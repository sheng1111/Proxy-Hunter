"""Proxy Hunter - Professional proxy fetching and validation tool.

This module provides a comprehensive solution for fetching, validating, and managing
free proxies for red team operations, web scraping, and security testing.

Features:
- Fetch proxies from multiple sources
- Validate proxy connectivity and anonymity
- Store results in SQLite database
- Export results in multiple formats
- Thread-safe operations
- Comprehensive logging
"""

from __future__ import annotations

import json
import logging
import re
import sqlite3
import time
from argparse import ArgumentParser, RawTextHelpFormatter
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Union, Tuple, Any
from urllib.parse import urlparse

try:
    import requests
    from requests.adapters import HTTPAdapter
    from requests.exceptions import RequestException, ConnectionError, Timeout
    from urllib3.util.retry import Retry
except ImportError as e:
    print(f"Error importing required packages: {e}")
    print("Please install required packages: pip install requests")
    raise

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ProxyHunterError(Exception):
    """Base exception for ProxyHunter operations."""
    pass


class ProxyValidationError(ProxyHunterError):
    """Exception raised when proxy validation fails."""
    pass


class DatabaseError(ProxyHunterError):
    """Exception raised when database operations fail."""
    pass


class ProxyHunter:
    """Professional proxy fetching and validation tool.
    
    This class provides comprehensive proxy management capabilities including:
    - Fetching from multiple sources
    - Validation with timeout and retry logic
    - SQLite database storage
    - Statistics and reporting
    - Thread-safe operations
    
    Args:
        threads: Number of concurrent threads for validation (default: 10)
        anonymous_only: Only keep proxies that hide your real IP (default: False)
        timeout: Timeout in seconds for each proxy check (default: 5)
        max_retries: Maximum number of retries for failed requests (default: 3)
        db_path: Path to SQLite database file
        
    Example:
        >>> hunter = ProxyHunter(threads=20, anonymous_only=True)
        >>> proxies = hunter.fetch_proxies()
        >>> results = hunter.validate_proxies(proxies)
        >>> hunter.save_to_database(results)
    """

    # Default proxy sources - Enhanced for red team operations
    PROXY_SOURCES = {
        'free-proxy-list': 'https://free-proxy-list.net/',
        'proxylist-geonode': 'https://proxylist.geonode.com/api/proxy-list?limit=500&page=1&sort_by=lastChecked&sort_type=desc',
        'proxy-list-org': 'https://www.proxy-list.download/api/v1/get?type=http',
        'proxyrotator': 'https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all',
        'hidemyname': 'https://hidemy.name/en/proxy-list/',
        'freeproxylist': 'https://freeproxylist.co/',
        'spys-one': 'http://spys.one/en/free-proxy-list/',
        'cool-proxy': 'https://www.cool-proxy.net/proxies/http_proxy_list/sort:score/direction:desc',
    }
    
    # Test URLs for validation (more reliable and diverse)
    TEST_URLS = {
        'httpbin': 'http://httpbin.org/ip',  # Use HTTP instead of HTTPS for better proxy compatibility
        'ipinfo': 'http://ipinfo.io/ip',     # Alternative IP service
        'ipapi': 'http://ip-api.com/json',   # Another reliable service
        'myip': 'http://whatismyipaddress.com/api/ip.php',  # Backup service
    }

    def __init__(
        self,
        threads: int = 10,
        anonymous_only: bool = False,
        timeout: int = 5,
        max_retries: int = 3,
        db_path: Optional[str] = None,
        user_agent: Optional[str] = None,
        geo_filter: Optional[List[str]] = None,
        protocol_filter: Optional[List[str]] = None,
        elite_only: bool = False
    ) -> None:
        self.threads = max(1, min(threads, 100))  # Limit threads to reasonable range
        self.anonymous_only = anonymous_only
        self.timeout = timeout
        self.max_retries = max_retries
        self.elite_only = elite_only
        self.geo_filter = geo_filter or []
        self.protocol_filter = protocol_filter or ['http', 'https']
        
        # Red team specific user agents
        self.user_agents = [
            user_agent if user_agent else 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0'
        ]
        
        # Database setup
        if db_path is None:
            db_path = Path(__file__).parent.parent / 'db' / 'proxy_data.db'
        self.db_path = Path(db_path)
        self._init_database()
        
        # Setup session with retry logic
        self.session = self._create_session()
        
        # Cache for public IP
        self._public_ip: Optional[str] = None
        self._ip_cache_time: Optional[float] = None
        self._ip_cache_duration = 300  # 5 minutes

    def _create_session(self) -> requests.Session:
        """Create a requests session with retry logic."""
        session = requests.Session()
        
        # Handle urllib3 version compatibility
        retry_kwargs = {
            'total': self.max_retries,
            'backoff_factor': 1,
            'status_forcelist': [429, 500, 502, 503, 504],
        }
        
        # Try new parameter name first, fallback to old one for compatibility
        try:
            retry_strategy = Retry(allowed_methods=["HEAD", "GET", "OPTIONS"], **retry_kwargs)
        except TypeError:
            # Fallback for older urllib3 versions
            retry_strategy = Retry(method_whitelist=["HEAD", "GET", "OPTIONS"], **retry_kwargs)
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session

    def _init_database(self) -> None:
        """Initialize SQLite database with required tables."""
        try:
            with self._get_db_connection() as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS proxies (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        proxy TEXT NOT NULL,
                        host TEXT NOT NULL,
                        port INTEGER NOT NULL,
                        protocol TEXT DEFAULT 'http',
                        country TEXT,
                        anonymity TEXT,
                        status TEXT NOT NULL,
                        response_time REAL,
                        data_size INTEGER DEFAULT 0,
                        last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        success_count INTEGER DEFAULT 0,
                        failure_count INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(proxy)
                    )
                ''')
                
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS proxy_stats (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        total_proxies INTEGER,
                        successful_proxies INTEGER,
                        failed_proxies INTEGER,
                        average_response_time REAL,
                        scan_duration REAL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create indexes for better performance
                conn.execute('CREATE INDEX IF NOT EXISTS idx_proxy_status ON proxies(status)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_proxy_last_checked ON proxies(last_checked)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_proxy_response_time ON proxies(response_time)')
                
                conn.commit()
                logger.info(f"Database initialized at {self.db_path}")
                
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to initialize database: {e}")

    @contextmanager
    def _get_db_connection(self):
        """Context manager for database connections."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            yield conn
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            raise DatabaseError(f"Database error: {e}")
        finally:
            if conn:
                conn.close()

    def fetch_proxies(self, sources: Optional[List[str]] = None) -> List[str]:
        """Fetch proxies from multiple sources.
        
        Args:
            sources: List of source names to fetch from. If None, use all sources.
            
        Returns:
            List of proxy strings in format 'host:port'
            
        Raises:
            ProxyHunterError: If fetching fails from all sources
        """
        if sources is None:
            sources = list(self.PROXY_SOURCES.keys())
        
        all_proxies = []
        successful_sources = 0
        
        for source in sources:
            try:
                if source == 'free-proxy-list':
                    proxies = self._fetch_from_free_proxy_list()
                elif source == 'proxylist-geonode':
                    proxies = self._fetch_from_geonode()
                else:
                    logger.warning(f"Unknown source: {source}")
                    continue
                
                all_proxies.extend(proxies)
                successful_sources += 1
                logger.info(f"Fetched {len(proxies)} proxies from {source}")
                
            except Exception as e:
                logger.error(f"Failed to fetch from {source}: {e}")
                continue
        
        if successful_sources == 0:
            raise ProxyHunterError("Failed to fetch proxies from any source")
        
        # Remove duplicates while preserving order
        unique_proxies = list(dict.fromkeys(all_proxies))
        logger.info(f"Total unique proxies fetched: {len(unique_proxies)}")
        
        return unique_proxies

    def _fetch_from_free_proxy_list(self) -> List[str]:
        """Fetch proxies from free-proxy-list.net."""
        try:
            response = self.session.get(self.PROXY_SOURCES['free-proxy-list'], timeout=self.timeout)
            response.raise_for_status()
            
            # Extract IP:PORT patterns
            ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}:\d{2,5}\b'
            proxies = re.findall(ip_pattern, response.text)
            
            return proxies
            
        except RequestException as e:
            raise ProxyHunterError(f"Failed to fetch from free-proxy-list: {e}")

    def _fetch_from_geonode(self) -> List[str]:
        """Fetch proxies from proxylist.geonode.com API."""
        try:
            response = self.session.get(self.PROXY_SOURCES['proxylist-geonode'], timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            proxies = []
            
            for item in data.get('data', []):
                if item.get('ip') and item.get('port'):
                    proxies.append(f"{item['ip']}:{item['port']}")
            
            return proxies
            
        except (RequestException, json.JSONDecodeError) as e:
            raise ProxyHunterError(f"Failed to fetch from geonode: {e}")

    def _get_public_ip(self) -> Optional[str]:
        """Get current public IP address with caching."""
        current_time = time.time()
        
        # Return cached IP if still valid
        if (self._public_ip and self._ip_cache_time and 
            current_time - self._ip_cache_time < self._ip_cache_duration):
            return self._public_ip
        
        # Try multiple services
        for service_name, url in self.TEST_URLS.items():
            try:
                response = self.session.get(url, timeout=self.timeout, verify=False)
                
                if response.status_code == 200:
                    try:
                        if service_name == 'httpbin':
                            data = response.json()
                            ip = data.get('origin', '').split(',')[0].strip()
                        elif service_name == 'ipapi':
                            data = response.json()
                            ip = data.get('query', '')
                        else:
                            ip = response.text.strip()
                    except:
                        ip = response.text.strip()
                    
                    if ip and self._is_valid_ip(ip.split(',')[0].strip()):
                        ip = ip.split(',')[0].strip()
                        self._public_ip = ip
                        self._ip_cache_time = current_time
                        logger.info(f"Public IP: {ip}")
                        return ip
                        
            except Exception as e:
                logger.debug(f"Failed to get IP from {service_name}: {e}")
                continue
        
        logger.warning("Could not determine public IP address")
        return None

    def _is_valid_ip(self, ip: str) -> bool:
        """Validate IP address format."""
        try:
            parts = ip.split('.')
            return len(parts) == 4 and all(0 <= int(part) <= 255 for part in parts)
        except (ValueError, AttributeError):
            return False

    def _parse_proxy(self, proxy: str) -> Tuple[str, int]:
        """Parse proxy string into host and port."""
        try:
            if '://' in proxy:
                parsed = urlparse(proxy)
                return parsed.hostname, parsed.port
            else:
                host, port = proxy.split(':')
                return host, int(port)
        except (ValueError, AttributeError) as e:
            raise ProxyValidationError(f"Invalid proxy format: {proxy}")

    def _validate_single_proxy(self, proxy: str, public_ip: Optional[str]) -> Dict[str, Any]:
        """Validate a single proxy."""
        start_time = time.time()
        
        try:
            host, port = self._parse_proxy(proxy)
            
            # Test proxy connectivity
            proxy_dict = {
                'http': f'http://{host}:{port}',
                'https': f'http://{host}:{port}',
            }
            
            # Try multiple test URLs (simplified and more reliable)
            for test_name, test_url in self.TEST_URLS.items():
                try:
                    response = self.session.get(
                        test_url,
                        proxies=proxy_dict,
                        timeout=self.timeout,
                        allow_redirects=True,
                        verify=False  # Disable SSL verification for better compatibility
                    )
                    
                    # Check if we got a valid response
                    if response.status_code == 200 and response.content:
                        # Parse response to get proxy IP
                        try:
                            if test_name == 'httpbin':
                                data = response.json()
                                proxy_ip = data.get('origin', '').split(',')[0].strip()
                            elif test_name == 'ipapi':
                                data = response.json()
                                proxy_ip = data.get('query', '')
                            else:
                                proxy_ip = response.text.strip()
                        except:
                            proxy_ip = response.text.strip()
                        
                        # Basic validation of IP format
                        if proxy_ip and self._is_valid_ip(proxy_ip.split(',')[0].strip()):
                            proxy_ip = proxy_ip.split(',')[0].strip()
                            
                            # Check anonymity
                            is_anonymous = public_ip is None or proxy_ip != public_ip
                            
                            if self.anonymous_only and not is_anonymous:
                                return {
                                    'proxy': proxy,
                                    'host': host,
                                    'port': port,
                                    'status': 'not_anonymous',
                                    'response_time': None,
                                    'data_size': 0,
                                    'proxy_ip': proxy_ip,
                                    'is_anonymous': False
                                }
                            
                            elapsed = time.time() - start_time
                            
                            return {
                                'proxy': proxy,
                                'host': host,
                                'port': port,
                                'status': 'ok',
                                'response_time': round(elapsed, 3),
                                'data_size': len(response.content),
                                'proxy_ip': proxy_ip,
                                'is_anonymous': is_anonymous,
                                'test_url': test_url
                            }
                    
                except Exception as e:
                    # Log debug info for first URL only to reduce noise
                    if test_name == 'httpbin':
                        logger.debug(f"Proxy {proxy} failed test {test_name}: {e}")
                    continue  # Try next test URL
            
            # If all test URLs failed
            return {
                'proxy': proxy,
                'host': host,
                'port': port,
                'status': 'failed',
                'response_time': None,
                'data_size': 0,
                'proxy_ip': None,
                'is_anonymous': False
            }
            
        except ProxyValidationError as e:
            return {
                'proxy': proxy,
                'host': '',
                'port': 0,
                'status': 'invalid',
                'response_time': None,
                'data_size': 0,
                'proxy_ip': None,
                'is_anonymous': False,
                'error': str(e)
            }
        except Exception as e:
            return {
                'proxy': proxy,
                'host': '',
                'port': 0,
                'status': 'error',
                'response_time': None,
                'data_size': 0,
                'proxy_ip': None,
                'is_anonymous': False,
                'error': str(e)
            }

    def validate_proxies(self, proxies: List[str], show_progress: bool = True) -> List[Dict[str, Any]]:
        """Validate a list of proxies using multi-threading.
        
        Args:
            proxies: List of proxy strings to validate
            show_progress: Whether to show progress information
            
        Returns:
            List of validation results
        """
        if not proxies:
            return []
        
        public_ip = self._get_public_ip() if self.anonymous_only else None
        results = []
        
        logger.info(f"Starting validation of {len(proxies)} proxies using {self.threads} threads")
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            # Submit all tasks
            future_to_proxy = {
                executor.submit(self._validate_single_proxy, proxy, public_ip): proxy
                for proxy in proxies
            }
            
            # Collect results
            completed = 0
            for future in as_completed(future_to_proxy):
                try:
                    result = future.result()
                    results.append(result)
                    completed += 1
                    
                    if show_progress and completed % 10 == 0:
                        logger.info(f"Validated {completed}/{len(proxies)} proxies")
                        
                except Exception as e:
                    proxy = future_to_proxy[future]
                    logger.error(f"Error validating {proxy}: {e}")
                    results.append({
                        'proxy': proxy,
                        'status': 'error',
                        'error': str(e)
                    })
        
        elapsed = time.time() - start_time
        successful = sum(1 for r in results if r['status'] == 'ok')
        
        logger.info(f"Validation completed in {elapsed:.2f}s: {successful}/{len(results)} successful")
        
        return results

    def save_to_database(self, results: List[Dict[str, Any]]) -> None:
        """Save validation results to SQLite database."""
        if not results:
            return
        
        try:
            with self._get_db_connection() as conn:
                for result in results:
                    # Update or insert proxy record
                    conn.execute('''
                        INSERT OR REPLACE INTO proxies (
                            proxy, host, port, status, response_time, data_size,
                            last_checked, anonymity, success_count, failure_count
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 
                                 COALESCE((SELECT success_count FROM proxies WHERE proxy = ?), 0) + 
                                 CASE WHEN ? = 'ok' THEN 1 ELSE 0 END,
                                 COALESCE((SELECT failure_count FROM proxies WHERE proxy = ?), 0) + 
                                 CASE WHEN ? != 'ok' THEN 1 ELSE 0 END)
                    ''', (
                        result['proxy'],
                        result.get('host', ''),
                        result.get('port', 0),
                        result['status'],
                        result.get('response_time'),
                        result.get('data_size', 0),
                        datetime.now().isoformat(),
                        'anonymous' if result.get('is_anonymous') else 'transparent',
                        result['proxy'],  # for success_count calculation
                        result['status'],
                        result['proxy'],  # for failure_count calculation
                        result['status']
                    ))
                
                # Save scan statistics
                successful = sum(1 for r in results if r['status'] == 'ok')
                failed = len(results) - successful
                avg_response_time = (
                    sum(r.get('response_time', 0) for r in results if r.get('response_time')) / successful
                    if successful > 0 else 0
                )
                
                conn.execute('''
                    INSERT INTO proxy_stats (
                        total_proxies, successful_proxies, failed_proxies,
                        average_response_time, scan_duration
                    ) VALUES (?, ?, ?, ?, ?)
                ''', (len(results), successful, failed, avg_response_time, time.time()))
                
                conn.commit()
                logger.info(f"Saved {len(results)} results to database")
                
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to save results to database: {e}")

    def get_working_proxies(self, limit: Optional[int] = None, min_response_time: Optional[float] = None) -> List[Dict[str, Any]]:
        """Get working proxies from database.
        
        Args:
            limit: Maximum number of proxies to return
            min_response_time: Minimum response time threshold
            
        Returns:
            List of working proxy records
        """
        try:
            with self._get_db_connection() as conn:
                query = '''
                    SELECT * FROM proxies 
                    WHERE status = 'ok'
                '''
                params = []
                
                if min_response_time is not None:
                    query += ' AND response_time >= ?'
                    params.append(min_response_time)
                
                query += ' ORDER BY response_time ASC'
                
                if limit is not None:
                    query += ' LIMIT ?'
                    params.append(limit)
                
                cursor = conn.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
                
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to fetch working proxies: {e}")

    def get_statistics(self) -> Dict[str, Any]:
        """Get proxy statistics from database."""
        try:
            with self._get_db_connection() as conn:
                # Current proxy status
                cursor = conn.execute('''
                    SELECT status, COUNT(*) as count
                    FROM proxies
                    GROUP BY status
                ''')
                status_counts = dict(cursor.fetchall())
                
                # Response time statistics
                cursor = conn.execute('''
                    SELECT 
                        AVG(response_time) as avg_response_time,
                        MIN(response_time) as min_response_time,
                        MAX(response_time) as max_response_time
                    FROM proxies
                    WHERE status = 'ok' AND response_time IS NOT NULL
                ''')
                response_stats = dict(cursor.fetchone() or {})
                
                # Recent scan statistics
                cursor = conn.execute('''
                    SELECT *
                    FROM proxy_stats
                    ORDER BY timestamp DESC
                    LIMIT 1
                ''')
                recent_scan = dict(cursor.fetchone() or {})
                
                return {
                    'status_counts': status_counts,
                    'response_time_stats': response_stats,
                    'recent_scan': recent_scan,
                    'total_proxies': sum(status_counts.values()),
                    'working_proxies': status_counts.get('ok', 0),
                    'failed_proxies': sum(v for k, v in status_counts.items() if k != 'ok')
                }
                
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to get statistics: {e}")

    # Legacy methods for backward compatibility
    def fetch_proxies_legacy(self) -> List[str]:
        """Legacy method name for backward compatibility."""
        return self.fetch_proxies()

    def check_proxies(self, proxies: List[str]) -> List[Dict[str, Any]]:
        """Legacy method name for backward compatibility."""
        return self.validate_proxies(proxies)

    def save(self, results: List[Dict[str, Any]], filename: str, fmt: str = "txt", mode: str = "w") -> None:
        """Save proxy results to file in various formats."""
        with open(filename, mode, encoding="utf-8") as fh:
            if fmt == "json":
                json.dump([r for r in results if r["status"] == "ok"], fh,
                          ensure_ascii=False, indent=2)
            elif fmt == "jsonl":
                for r in results:
                    if r["status"] == "ok":
                        fh.write(json.dumps(r, ensure_ascii=False) + "\n")
            else:
                for r in results:
                    if r["status"] == "ok":
                        fh.write(f"{r['proxy']}\n")

    def load(self, filename: str, fmt: str = "txt") -> List[Dict[str, Any]]:
        """Load proxy results from file."""
        results = []
        try:
            with open(filename, "r", encoding="utf-8") as fh:
                if fmt == "json":
                    results = json.load(fh)
                elif fmt == "jsonl":
                    for line in fh:
                        results.append(json.loads(line))
                else:
                    for line in fh:
                        ip = line.strip()
                        if ip:
                            results.append({"proxy": ip, "status": "ok"})
        except FileNotFoundError:
            pass
        return results

    def get_proxies_by_country(self, country: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get working proxies filtered by country."""
        try:
            with self._get_db_connection() as conn:
                query = '''
                    SELECT * FROM proxies 
                    WHERE status = 'ok' AND LOWER(country) LIKE LOWER(?)
                    ORDER BY response_time ASC
                '''
                params = [f'%{country}%']
                
                if limit is not None:
                    query += ' LIMIT ?'
                    params.append(limit)
                
                cursor = conn.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to fetch proxies by country: {e}")

    def get_elite_proxies(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get elite/high anonymity proxies only."""
        try:
            with self._get_db_connection() as conn:
                query = '''
                    SELECT * FROM proxies 
                    WHERE status = 'ok' AND anonymity = 'anonymous'
                    ORDER BY response_time ASC
                '''
                params = []
                
                if limit is not None:
                    query += ' LIMIT ?'
                    params.append(limit)
                
                cursor = conn.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to fetch elite proxies: {e}")

    def get_fast_proxies(self, max_response_time: float = 2.0, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get fast proxies with response time under threshold."""
        try:
            with self._get_db_connection() as conn:
                query = '''
                    SELECT * FROM proxies 
                    WHERE status = 'ok' AND response_time <= ?
                    ORDER BY response_time ASC
                '''
                params = [max_response_time]
                
                if limit is not None:
                    query += ' LIMIT ?'
                    params.append(limit)
                
                cursor = conn.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to fetch fast proxies: {e}")

    def test_proxy_with_target(self, proxy: str, target_url: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Test a specific proxy against a target URL - useful for red team operations."""
        try:
            host, port = self._parse_proxy(proxy)
            
            proxy_dict = {
                'http': f'http://{host}:{port}',
                'https': f'http://{host}:{port}',
            }
            
            # Use random user agent for stealth
            test_headers = {
                'User-Agent': self.user_agents[0],
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            if headers:
                test_headers.update(headers)
            
            start_time = time.time()
            response = self.session.get(
                target_url,
                proxies=proxy_dict,
                headers=test_headers,
                timeout=self.timeout,
                allow_redirects=True
            )
            elapsed = time.time() - start_time
            
            return {
                'proxy': proxy,
                'target_url': target_url,
                'status_code': response.status_code,
                'response_time': round(elapsed, 3),
                'content_length': len(response.content),
                'headers': dict(response.headers),
                'success': response.status_code == 200
            }
            
        except Exception as e:
            return {
                'proxy': proxy,
                'target_url': target_url,
                'success': False,
                'error': str(e)
            }

    def get_proxy_rotation_list(self, count: int = 10, max_response_time: float = 5.0) -> List[str]:
        """Get a list of proxies for rotation - useful for web scraping."""
        proxies = self.get_fast_proxies(max_response_time=max_response_time, limit=count)
        return [proxy['proxy'] for proxy in proxies]

    def export_proxies_for_tools(self, format_type: str = 'burp', output_file: Optional[str] = None) -> str:
        """Export proxies in formats suitable for security tools."""
        working_proxies = self.get_working_proxies()
        
        if format_type == 'burp':
            # Burp Suite format
            output = []
            for proxy in working_proxies:
                host, port = proxy['proxy'].split(':')
                output.append(f"{host}:{port}")
            result = '\n'.join(output)
            
        elif format_type == 'curl':
            # curl format
            output = []
            for proxy in working_proxies:
                output.append(f"--proxy {proxy['proxy']}")
            result = '\n'.join(output)
            
        elif format_type == 'requests':
            # Python requests format
            proxies_list = [f"'{proxy['proxy']}'" for proxy in working_proxies]
            result = f"proxies = [{', '.join(proxies_list)}]"
            
        else:
            # Default text format
            result = '\n'.join([proxy['proxy'] for proxy in working_proxies])
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(result)
        
        return result

    def close(self) -> None:
        """Clean up resources."""
        if hasattr(self, 'session'):
            self.session.close()


def _read_ips_from_file(filename: str) -> List[str]:
    """Read IP addresses from a file."""
    try:
        with open(filename, "r", encoding="utf8") as file:
            ips = [line.strip() for line in file if line.strip()]
        return list(dict.fromkeys(ips))
    except FileNotFoundError:
        print("The file does not exist.")
        return []


def _cli() -> None:
    """Command-line interface for ProxyHunter."""
    parser = ArgumentParser(
        description="Professional proxy fetching and validation tool for red team operations and web scraping.",
        formatter_class=RawTextHelpFormatter,
    )
    parser.add_argument("-o", "--output", default="proxy.txt",
                        help="Set the output file name.")
    parser.add_argument("-u", "--update", help="Update your proxies listed.")
    parser.add_argument(
        "-c",
        "--check",
        help=(
            "Check if the proxies listed in the specified file are valid. "
            "This option requires a filename as an argument."
        ),
    )
    parser.add_argument("-t", "--threads", type=int, default=10,
                        help="Number of threads for proxy validation.")
    parser.add_argument("-f", "--format", choices=["txt", "json", "jsonl"], default="txt",
                        help="Output file format.")
    parser.add_argument("-a", "--anonymous-only", action="store_true",
                        help="Only keep proxies that hide your real IP.")
    parser.add_argument("--timeout", type=int, default=5,
                        help="Timeout in seconds for each proxy check.")
    parser.add_argument("--db", help="SQLite database path for storing results.")
    parser.add_argument("--stats", action="store_true",
                        help="Show proxy statistics from database.")
    parser.add_argument("--limit", type=int,
                        help="Limit number of proxies to process.")

    args = parser.parse_args()

    hunter = ProxyHunter(
        threads=args.threads,
        anonymous_only=args.anonymous_only,
        timeout=args.timeout,
        db_path=args.db
    )

    try:
        if args.stats:
            stats = hunter.get_statistics()
            print(f"Proxy Statistics:")
            print(f"Total proxies: {stats.get('total_proxies', 0)}")
            print(f"Working proxies: {stats.get('working_proxies', 0)}")
            print(f"Failed proxies: {stats.get('failed_proxies', 0)}")
            return

        if args.check:
            ips = _read_ips_from_file(args.check)
            if args.limit:
                ips = ips[:args.limit]
            results = hunter.validate_proxies(ips)
            hunter.save_to_database(results)
            hunter.save(results, args.check, fmt=args.format, mode="w")
        elif args.update:
            ips = _read_ips_from_file(args.update)
            if args.limit:
                ips = ips[:args.limit]
            results = hunter.validate_proxies(ips)
            hunter.save_to_database(results)
            hunter.save(results, args.update, fmt=args.format, mode="w")
        else:
            ips = hunter.fetch_proxies()
            if args.limit:
                ips = ips[:args.limit]
            results = hunter.validate_proxies(ips)
            hunter.save_to_database(results)
            hunter.save(results, args.output, fmt=args.format, mode="w")

        print("Proxy validation completed successfully.")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        exit(1)
    finally:
        hunter.close()


# CLI entry point for direct execution
if __name__ == "__main__":
    _cli()


