"""ProxySession - Enhanced requests session with automatic proxy rotation and traffic monitoring.

This module provides a high-level interface for making HTTP requests through proxies
with automatic rotation, failure handling, and traffic monitoring capabilities.
"""

import json
import logging
import random
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .core import ProxyHunter, ProxyHunterError

logger = logging.getLogger(__name__)


class TrafficMonitor:
    """Monitor and record proxy traffic for analysis."""

    def __init__(self):
        self.traffic_log = []
        self.lock = threading.Lock()
        self.session_start = datetime.now()

    def log_request(self, proxy: str, url: str, method: str,
                    response_code: Optional[int] = None,
                    response_time: Optional[float] = None,
                    data_size: int = 0, error: Optional[str] = None):
        """Log a request made through proxy."""
        with self.lock:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'proxy': proxy,
                'url': url,
                'method': method.upper(),
                'status_code': response_code,
                'response_time': response_time,
                'data_size': data_size,
                'error': error
            }
            self.traffic_log.append(log_entry)

            # Keep only last 1000 entries to prevent memory issues
            if len(self.traffic_log) > 1000:
                self.traffic_log = self.traffic_log[-1000:]

    def get_stats(self) -> Dict[str, Any]:
        """Get traffic statistics."""
        with self.lock:
            if not self.traffic_log:
                return {
                    'total_requests': 0,
                    'successful_requests': 0,
                    'failed_requests': 0,
                    'unique_proxies': 0,
                    'avg_response_time': 0,
                    'total_data': 0,
                    'session_duration': 0
                }

            total_requests = len(self.traffic_log)
            successful_requests = len(
                [log for log in self.traffic_log if log['status_code'] and 200 <= log['status_code'] < 400])
            failed_requests = total_requests - successful_requests
            unique_proxies = len(set(log['proxy'] for log in self.traffic_log))

            response_times = [log['response_time']
                              for log in self.traffic_log if log['response_time']]
            avg_response_time = sum(response_times) / \
                len(response_times) if response_times else 0

            total_data = sum(log['data_size'] for log in self.traffic_log)
            session_duration = (
                datetime.now() - self.session_start).total_seconds()

            return {
                'total_requests': total_requests,
                'successful_requests': successful_requests,
                'failed_requests': failed_requests,
                'unique_proxies': unique_proxies,
                'avg_response_time': round(avg_response_time, 3),
                'total_data': total_data,
                'session_duration': round(session_duration, 2)
            }

    def get_recent_traffic(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent traffic logs."""
        with self.lock:
            return self.traffic_log[-limit:] if self.traffic_log else []

    def clear_logs(self):
        """Clear traffic logs."""
        with self.lock:
            self.traffic_log.clear()


class ProxySession(requests.Session):
    """Enhanced requests session with automatic proxy rotation and monitoring.

    This class extends requests.Session to provide:
    - Automatic proxy rotation on failures
    - Traffic monitoring and logging
    - Proxy health tracking
    - Fallback mechanisms

    Example:
        >>> session = ProxySession(proxy_count=10)
        >>> response = session.get('https://httpbin.org/ip')
        >>> print(session.get_traffic_stats())
    """

    def __init__(self, proxy_count: int = 10, rotation_strategy: str = 'round_robin',
                 max_retries: int = 3, timeout: int = 10,
                 country_filter: Optional[str] = None,
                 anonymous_only: bool = True):
        """Initialize ProxySession.

        Args:
            proxy_count: Number of proxies to maintain in rotation pool
            rotation_strategy: 'round_robin', 'random', or 'performance'
            max_retries: Maximum retries per proxy
            timeout: Request timeout in seconds
            country_filter: Filter proxies by country code (e.g., 'US')
            anonymous_only: Only use anonymous proxies
        """
        super().__init__()

        self.proxy_count = proxy_count
        self.rotation_strategy = rotation_strategy
        self.max_retries = max_retries
        self.timeout = timeout
        self.country_filter = country_filter
        self.anonymous_only = anonymous_only

        # Initialize proxy hunter
        self.hunter = ProxyHunter(
            threads=20, anonymous_only=anonymous_only, timeout=timeout)

        # Proxy management
        self.proxy_pool = []
        self.current_proxy_index = 0
        self.proxy_performance = {}  # Track proxy performance
        self.failed_proxies = set()
        self.lock = threading.Lock()

        # Traffic monitoring
        self.traffic_monitor = TrafficMonitor()

        # Session configuration
        self.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

        # Initialize proxy pool
        self._refresh_proxy_pool()

        # Setup retry strategy
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )

        try:
            retry_strategy = Retry(allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE", "OPTIONS"],
                                   **retry_strategy.__dict__)
        except TypeError:
            # Fallback for older urllib3 versions
            retry_strategy = Retry(method_whitelist=["HEAD", "GET", "POST", "PUT", "DELETE", "OPTIONS"],
                                   **retry_strategy.__dict__)

        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.mount("http://", adapter)
        self.mount("https://", adapter)

    def _refresh_proxy_pool(self):
        """Refresh the proxy pool with working proxies."""
        try:
            if self.country_filter:
                proxies = self.hunter.get_proxies_by_country(
                    self.country_filter,
                    limit=self.proxy_count * 2
                )
            else:
                proxies = self.hunter.get_working_proxies(
                    limit=self.proxy_count * 2)

            # If not enough proxies, try to fetch more
            if len(proxies) < self.proxy_count:
                logger.info("Not enough cached proxies, fetching new ones...")
                fresh_proxies = self.hunter.fetch_proxies()
                results = self.hunter.validate_proxies(fresh_proxies[:50])
                self.hunter.save_to_database(results)

                # Get working proxies again
                if self.country_filter:
                    proxies = self.hunter.get_proxies_by_country(
                        self.country_filter,
                        limit=self.proxy_count * 2
                    )
                else:
                    proxies = self.hunter.get_working_proxies(
                        limit=self.proxy_count * 2)

            with self.lock:
                self.proxy_pool = []
                for proxy_info in proxies[:self.proxy_count]:
                    proxy_url = f"http://{proxy_info['proxy']}"
                    self.proxy_pool.append(proxy_url)

                    # Initialize performance tracking
                    if proxy_url not in self.proxy_performance:
                        self.proxy_performance[proxy_url] = {
                            'success_count': 0,
                            'failure_count': 0,
                            'avg_response_time': proxy_info.get('response_time', 5.0)
                        }

                logger.info(
                    f"Refreshed proxy pool with {len(self.proxy_pool)} proxies")

        except Exception as e:
            logger.error(f"Failed to refresh proxy pool: {e}")
            if not self.proxy_pool:
                raise ProxyHunterError(f"Unable to initialize proxy pool: {e}")

    def _get_next_proxy(self) -> Optional[str]:
        """Get the next proxy based on rotation strategy."""
        with self.lock:
            if not self.proxy_pool:
                return None

            available_proxies = [
                p for p in self.proxy_pool if p not in self.failed_proxies]

            if not available_proxies:
                # All proxies failed, reset failed set and refresh pool
                self.failed_proxies.clear()
                self._refresh_proxy_pool()
                available_proxies = self.proxy_pool

            if not available_proxies:
                return None

            if self.rotation_strategy == 'random':
                return random.choice(available_proxies)
            elif self.rotation_strategy == 'performance':
                # Sort by performance (success rate and response time)
                def performance_score(proxy):
                    perf = self.proxy_performance.get(
                        proxy, {'success_count': 0, 'failure_count': 0, 'avg_response_time': 5.0})
                    total_requests = perf['success_count'] + \
                        perf['failure_count']
                    if total_requests == 0:
                        return 0.5  # Default score for unused proxies
                    success_rate = perf['success_count'] / total_requests
                    # Higher success rate and lower response time = higher score
                    return success_rate / (1 + perf['avg_response_time'])

                available_proxies.sort(key=performance_score, reverse=True)
                return available_proxies[0]
            else:  # round_robin
                # Find next available proxy in round-robin order
                for i in range(len(self.proxy_pool)):
                    proxy_index = (self.current_proxy_index +
                                   i) % len(self.proxy_pool)
                    proxy = self.proxy_pool[proxy_index]
                    if proxy in available_proxies:
                        self.current_proxy_index = (
                            proxy_index + 1) % len(self.proxy_pool)
                        return proxy
                return available_proxies[0] if available_proxies else None

    def _update_proxy_performance(self, proxy: str, success: bool, response_time: Optional[float] = None):
        """Update proxy performance metrics."""
        with self.lock:
            if proxy not in self.proxy_performance:
                self.proxy_performance[proxy] = {
                    'success_count': 0,
                    'failure_count': 0,
                    'avg_response_time': 5.0
                }

            perf = self.proxy_performance[proxy]

            if success:
                perf['success_count'] += 1
                if response_time is not None:
                    # Update average response time
                    total_requests = perf['success_count'] + \
                        perf['failure_count']
                    perf['avg_response_time'] = (
                        (perf['avg_response_time'] * (total_requests -
                         1) + response_time) / total_requests
                    )
            else:
                perf['failure_count'] += 1

                # Mark proxy as failed if too many failures
                total_requests = perf['success_count'] + perf['failure_count']
                if total_requests >= 5 and perf['failure_count'] / total_requests > 0.8:
                    self.failed_proxies.add(proxy)

    def request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Make HTTP request through proxy with automatic rotation and monitoring."""
        start_time = time.time()
        proxy = None
        last_exception = None

        # Try up to 3 different proxies
        for attempt in range(3):
            proxy = self._get_next_proxy()
            if not proxy:
                if attempt == 0:
                    # Try to refresh proxy pool
                    self._refresh_proxy_pool()
                    proxy = self._get_next_proxy()

                if not proxy:
                    break

            # Set proxy for this request
            kwargs['proxies'] = {'http': proxy, 'https': proxy}
            kwargs.setdefault('timeout', self.timeout)

            try:
                response = super().request(method, url, **kwargs)

                # Calculate response time and data size
                response_time = time.time() - start_time
                data_size = len(response.content) if response.content else 0

                # Update performance tracking
                self._update_proxy_performance(proxy, True, response_time)

                # Log successful request
                self.traffic_monitor.log_request(
                    proxy=proxy,
                    url=url,
                    method=method,
                    response_code=response.status_code,
                    response_time=response_time,
                    data_size=data_size
                )

                return response

            except Exception as e:
                last_exception = e
                response_time = time.time() - start_time

                # Update performance tracking
                self._update_proxy_performance(proxy, False, response_time)

                # Log failed request
                self.traffic_monitor.log_request(
                    proxy=proxy,
                    url=url,
                    method=method,
                    error=str(e),
                    response_time=response_time
                )

                logger.warning(f"Request failed with proxy {proxy}: {e}")
                start_time = time.time()  # Reset timer for next attempt

        # All proxies failed
        if last_exception:
            raise last_exception
        else:
            raise ProxyHunterError("No working proxies available")

    def get_traffic_stats(self) -> Dict[str, Any]:
        """Get current traffic statistics."""
        return self.traffic_monitor.get_stats()

    def get_recent_traffic(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent traffic logs."""
        return self.traffic_monitor.get_recent_traffic(limit)

    def get_proxy_status(self) -> Dict[str, Any]:
        """Get current proxy pool status."""
        with self.lock:
            return {
                'total_proxies': len(self.proxy_pool),
                'active_proxies': len([p for p in self.proxy_pool if p not in self.failed_proxies]),
                'failed_proxies': len(self.failed_proxies),
                'current_proxy': self._get_next_proxy(),
                'performance_data': self.proxy_performance.copy()
            }

    def refresh_proxies(self):
        """Manually refresh the proxy pool."""
        self.failed_proxies.clear()
        self._refresh_proxy_pool()

    def clear_traffic_logs(self):
        """Clear traffic monitoring logs."""
        self.traffic_monitor.clear_logs()

    def close(self):
        """Close the session and cleanup resources."""
        super().close()
        if hasattr(self, 'hunter'):
            self.hunter.close()
