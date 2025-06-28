"""Proxy Hunter - Professional proxy fetching and validation tool.

This module provides a comprehensive solution for fetching, validating, and managing
free proxies for red team operations, web scraping, and security testing.

Enhanced Features:
- Fetch proxies from multiple sources (15+ high-quality sources)
- SOCKS4/SOCKS5 proxy support with validation
- Geographic IP detection and filtering
- Advanced proxy validation with smart retry logic
- Real-time availability testing and anonymity detection
- Dynamic quality scoring and ranking system
- Blacklist/whitelist management for proxy filtering
- SQLite database with performance analytics
- Thread-safe operations with optimized concurrency
- Comprehensive logging and monitoring
- Intelligent proxy pool warming and auto-refresh
"""

from __future__ import annotations

import json
import logging
import re
import sqlite3
import time
import random
import socket
import struct
import hashlib
from argparse import ArgumentParser, RawTextHelpFormatter
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Union, Tuple, Any, Set
from urllib.parse import urlparse

try:
    import requests
    from requests.adapters import HTTPAdapter
    from requests.exceptions import RequestException, ConnectionError, Timeout
    from urllib3.util.retry import Retry
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
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


class ProxyQualityScorer:
    """Dynamic proxy quality scoring system for intelligent ranking."""

    def __init__(self):
        self.weight_response_time = 0.3
        self.weight_success_rate = 0.4
        self.weight_anonymity = 0.2
        self.weight_source_reliability = 0.1

    def calculate_score(self, proxy_data: Dict[str, Any]) -> float:
        """Calculate quality score for a proxy (0-100).

        Args:
            proxy_data: Dictionary containing proxy metrics

        Returns:
            Quality score between 0-100
        """
        score = 0.0

        # Response time score (faster = better, max 10 seconds)
        response_time = proxy_data.get('response_time', 10.0)
        time_score = max(0, 100 - (response_time * 10))
        score += time_score * self.weight_response_time

        # Success rate score
        success_count = proxy_data.get('success_count', 0)
        failure_count = proxy_data.get('failure_count', 0)
        total_attempts = success_count + failure_count

        if total_attempts > 0:
            success_rate = success_count / total_attempts
            success_score = success_rate * 100
        else:
            success_score = 50  # Neutral score for untested proxies

        score += success_score * self.weight_success_rate

        # Anonymity score
        anonymity = proxy_data.get('anonymity', 'transparent')
        if anonymity == 'elite':
            anonymity_score = 100
        elif anonymity == 'anonymous':
            anonymity_score = 80
        elif anonymity == 'transparent':
            anonymity_score = 60
        else:
            anonymity_score = 40

        score += anonymity_score * self.weight_anonymity

        # Source reliability score
        source = proxy_data.get('source', '')
        source_scores = {
            'github-proxy-list': 90,
            'github-free-proxies': 85,
            'github-proxy-daily': 85,
            'proxylist-geonode': 80,
            'proxyscrape-http': 75,
            'proxyscrape-https': 75,
            'pubproxy': 70,
            'free-proxy-list': 65,
        }
        source_score = source_scores.get(source, 50)
        score += source_score * self.weight_source_reliability

        return min(100, max(0, score))


class GeoLocationDetector:
    """Geographic location detection for proxies using multiple APIs."""

    def __init__(self):
        # Free geolocation APIs (no API key required)
        self.geo_apis = [
            'http://ip-api.com/json/{ip}?fields=status,country,countryCode,region,regionName,city,lat,lon,timezone,isp',
            'https://ipapi.co/{ip}/json/',
            'http://www.geoplugin.net/json.gp?ip={ip}',
            'https://freegeoip.app/json/{ip}',
        ]
        self.cache = {}  # Simple caching to avoid repeated lookups

    def get_location(self, ip: str) -> Dict[str, str]:
        """Get geographic location information for an IP address.

        Args:
            ip: IP address to lookup

        Returns:
            Dictionary with location info (country, region, city, etc.)
        """
        if ip in self.cache:
            return self.cache[ip]

        for api_url in self.geo_apis:
            try:
                url = api_url.format(ip=ip)
                response = requests.get(url, timeout=5)

                if response.status_code == 200:
                    data = response.json()

                    # Standardize response format
                    location = self._standardize_location_data(data, api_url)
                    if location.get('country'):
                        self.cache[ip] = location
                        return location

            except Exception as e:
                logger.debug(f"Geo API {api_url} failed: {e}")
                continue

        # Return default if all APIs fail
        default_location = {
            'country': 'Unknown',
            'country_code': '',
            'region': 'Unknown',
            'city': 'Unknown',
            'latitude': 0.0,
            'longitude': 0.0,
            'timezone': '',
            'isp': 'Unknown'
        }
        self.cache[ip] = default_location
        return default_location

    def _standardize_location_data(self, data: Dict, api_url: str) -> Dict[str, str]:
        """Standardize location data from different APIs."""
        location = {}

        if 'ip-api.com' in api_url:
            location = {
                'country': data.get('country', ''),
                'country_code': data.get('countryCode', ''),
                'region': data.get('regionName', ''),
                'city': data.get('city', ''),
                'latitude': data.get('lat', 0.0),
                'longitude': data.get('lon', 0.0),
                'timezone': data.get('timezone', ''),
                'isp': data.get('isp', '')
            }
        elif 'ipapi.co' in api_url:
            location = {
                'country': data.get('country_name', ''),
                'country_code': data.get('country_code', ''),
                'region': data.get('region', ''),
                'city': data.get('city', ''),
                'latitude': data.get('latitude', 0.0),
                'longitude': data.get('longitude', 0.0),
                'timezone': data.get('timezone', ''),
                'isp': data.get('org', '')
            }
        elif 'geoplugin.net' in api_url:
            location = {
                'country': data.get('geoplugin_countryName', ''),
                'country_code': data.get('geoplugin_countryCode', ''),
                'region': data.get('geoplugin_regionName', ''),
                'city': data.get('geoplugin_city', ''),
                'latitude': float(data.get('geoplugin_latitude', 0) or 0),
                'longitude': float(data.get('geoplugin_longitude', 0) or 0),
                'timezone': data.get('geoplugin_timezone', ''),
                'isp': ''
            }
        elif 'freegeoip.app' in api_url:
            location = {
                'country': data.get('country_name', ''),
                'country_code': data.get('country_code', ''),
                'region': data.get('region_name', ''),
                'city': data.get('city', ''),
                'latitude': data.get('latitude', 0.0),
                'longitude': data.get('longitude', 0.0),
                'timezone': data.get('time_zone', ''),
                'isp': ''
            }

        return location


class ProxyBlacklist:
    """Blacklist management for filtering out bad proxies."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_blacklist_db()

    def _init_blacklist_db(self):
        """Initialize blacklist database table."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS proxy_blacklist (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    proxy TEXT NOT NULL UNIQUE,
                    reason TEXT,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    auto_added BOOLEAN DEFAULT 0
                )
            ''')
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            logger.error(f"Failed to initialize blacklist database: {e}")

    def add_to_blacklist(self, proxy: str, reason: str = "Manual", auto_added: bool = False):
        """Add proxy to blacklist."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute('''
                INSERT OR REPLACE INTO proxy_blacklist (proxy, reason, auto_added)
                VALUES (?, ?, ?)
            ''', (proxy, reason, auto_added))
            conn.commit()
            conn.close()
            logger.info(f"Added {proxy} to blacklist: {reason}")
        except sqlite3.Error as e:
            logger.error(f"Failed to add {proxy} to blacklist: {e}")

    def is_blacklisted(self, proxy: str) -> bool:
        """Check if proxy is in blacklist."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute(
                'SELECT 1 FROM proxy_blacklist WHERE proxy = ?', (proxy,))
            result = cursor.fetchone() is not None
            conn.close()
            return result
        except sqlite3.Error:
            return False

    def get_blacklisted_proxies(self) -> List[Dict[str, Any]]:
        """Get all blacklisted proxies."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute(
                'SELECT * FROM proxy_blacklist ORDER BY added_at DESC')
            results = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return results
        except sqlite3.Error:
            return []

    def remove_from_blacklist(self, proxy: str):
        """Remove proxy from blacklist."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute(
                'DELETE FROM proxy_blacklist WHERE proxy = ?', (proxy,))
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            logger.error(f"Failed to remove {proxy} from blacklist: {e}")

    def auto_blacklist_failed_proxy(self, proxy: str, failure_count: int, total_attempts: int):
        """Automatically blacklist proxies with high failure rates."""
        if total_attempts >= 5 and failure_count / total_attempts >= 0.9:
            reason = f"Auto-blacklisted: {failure_count}/{total_attempts} failures"
            self.add_to_blacklist(proxy, reason, auto_added=True)


class ProxyHunter:
    """Professional proxy fetching and validation tool with enhanced capabilities.

    This class provides comprehensive proxy management capabilities including:
    - Fetching from 15+ high-quality sources with smart fallback
    - SOCKS4/SOCKS5 proxy support and validation
    - Advanced validation with multi-endpoint testing
    - Geographic location detection and filtering
    - Dynamic quality scoring and ranking
    - Blacklist/whitelist management
    - Intelligent retry logic and error handling
    - SQLite database storage with analytics
    - Performance optimization and caching
    - Thread-safe operations with progress tracking

    Args:
        threads: Number of concurrent threads for validation (default: 20)
        anonymous_only: Only keep proxies that hide your real IP (default: False)
        timeout: Timeout in seconds for each proxy check (default: 5)
        max_retries: Maximum number of retries for failed requests (default: 3)
        db_path: Path to SQLite database file
        validate_on_fetch: Validate proxies immediately after fetching (default: True)
        enable_geolocation: Enable geographic location detection (default: True)
        quality_threshold: Minimum quality score for proxies (0-100, default: 30)
        auto_blacklist: Automatically blacklist bad proxies (default: True)

    Example:
        >>> hunter = ProxyHunter(threads=30, anonymous_only=True, enable_geolocation=True)
        >>> proxies = hunter.fetch_proxies()
        >>> results = hunter.validate_proxies(proxies)
        >>> hunter.save_to_database(results)
    """

    # Enhanced proxy sources - 15+ high-quality free proxy sources
    PROXY_SOURCES = {
        'free-proxy-list': 'https://free-proxy-list.net/',
        'proxylist-geonode': 'https://proxylist.geonode.com/api/proxy-list?limit=500&page=1&sort_by=lastChecked&sort_type=desc',
        'proxy-list-org': 'https://www.proxy-list.download/api/v1/get?type=http',
        'proxyscrape-http': 'https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all',
        'proxyscrape-https': 'https://api.proxyscrape.com/v2/?request=getproxies&protocol=https&timeout=10000&country=all&ssl=all&anonymity=all',
        'proxyscrape-socks4': 'https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks4&timeout=10000&country=all',
        'proxyscrape-socks5': 'https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks5&timeout=10000&country=all',
        'pubproxy': 'http://pubproxy.com/api/proxy?limit=20&format=json&type=http',
        'proxyspace': 'https://api.proxyspace.pro/proxy?format=json&limit=100',
        'proxydb': 'http://proxydb.net/?limit=100',
        'github-proxy-list': 'https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt',
        'github-free-proxies': 'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt',
        'github-proxy-daily': 'https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt',
        'github-socks4': 'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt',
        'github-socks5': 'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt',
        'spys-one': 'http://spys.one/en/free-proxy-list/',
        'cool-proxy': 'https://www.cool-proxy.net/proxies/http_proxy_list/sort:score/direction:desc',
        'hidemyname': 'https://hidemy.name/en/proxy-list/',
        'freeproxylist': 'https://freeproxylist.co/',
    }

    # Enhanced test URLs for validation with multiple fallbacks
    TEST_URLS = {
        'httpbin': 'http://httpbin.org/ip',
        'ipify': 'https://api.ipify.org?format=json',
        'ipinfo': 'http://ipinfo.io/ip',
        'ipapi': 'http://ip-api.com/json?fields=query',
        'myip': 'http://whatismyipaddress.com/api/ip.php',
        'checkip': 'http://checkip.amazonaws.com/',
        'ipecho': 'http://ipecho.net/plain',
        'ifconfig': 'http://ifconfig.me/ip',
    }

    # Headers leak test URLs for advanced anonymity detection
    ANONYMITY_TEST_URLS = {
        'httpbin_headers': 'http://httpbin.org/headers',
        'httpbin_forwarded': 'http://httpbin.org/get',
    }

    # Common user agents for better success rate
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/119.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0',
    ]

    def __init__(
        self,
        threads: int = 20,
        anonymous_only: bool = False,
        timeout: int = 5,
        max_retries: int = 3,
        db_path: Optional[str] = None,
        user_agent: Optional[str] = None,
        geo_filter: Optional[List[str]] = None,
        protocol_filter: Optional[List[str]] = None,
        elite_only: bool = False,
        validate_on_fetch: bool = True,
        enable_geolocation: bool = True,
        quality_threshold: float = 30.0,
        auto_blacklist: bool = True,
        socket_timeout: int = 2,
        enable_socks: bool = True
    ) -> None:
        # Enhanced configuration with more options
        self.threads = max(1, min(threads, 100))
        self.anonymous_only = anonymous_only
        self.timeout = timeout
        self.socket_timeout = socket_timeout
        self.max_retries = max_retries
        self.elite_only = elite_only
        self.geo_filter = geo_filter or []
        self.protocol_filter = protocol_filter or [
            'http', 'https', 'socks4', 'socks5'] if enable_socks else ['http', 'https']
        self.validate_on_fetch = validate_on_fetch
        self.enable_geolocation = enable_geolocation
        self.quality_threshold = quality_threshold
        self.auto_blacklist = auto_blacklist
        self.enable_socks = enable_socks

        # Enhanced user agent rotation
        self.user_agent = user_agent or random.choice(self.USER_AGENTS)

        # Database setup
        if db_path is None:
            db_path = Path(__file__).parent.parent / 'db' / 'proxy_data.db'
        self.db_path = Path(db_path)
        self._init_database()

        # Initialize enhanced components
        self.quality_scorer = ProxyQualityScorer()
        self.geo_detector = GeoLocationDetector() if enable_geolocation else None
        self.blacklist = ProxyBlacklist(
            self.db_path) if auto_blacklist else None

        # Setup session with enhanced retry logic
        self.session = self._create_session()

        # Cache for public IP with better management
        self._public_ip: Optional[str] = None
        self._ip_cache_time: Optional[float] = None
        self._ip_cache_duration = 300  # 5 minutes

        # Enhanced performance tracking
        self._fetch_stats = {
            'sources_attempted': 0,
            'sources_successful': 0,
            'proxies_fetched': 0,
            'socks_proxies_found': 0,
            'http_proxies_found': 0,
            'fetch_errors': [],
            'fetch_duration': 0,
            'geographical_distribution': {}
        }

        # Proxy pool warming cache
        self._warmed_proxies: Optional[List[Dict[str, Any]]] = None
        self._warm_cache_time: Optional[float] = None
        self._warm_cache_duration = 1800  # 30 minutes

    def _create_session(self) -> requests.Session:
        """Create a requests session with enhanced retry logic and configuration."""
        session = requests.Session()

        # Enhanced retry strategy
        retry_kwargs = {
            'total': self.max_retries,
            'backoff_factor': 0.5,
            'status_forcelist': [429, 500, 502, 503, 504, 520, 521, 522, 523, 524],
            'raise_on_status': False,
            'raise_on_redirect': False,
        }

        # Handle urllib3 version compatibility
        try:
            retry_strategy = Retry(
                allowed_methods=["HEAD", "GET", "OPTIONS"], **retry_kwargs)
        except TypeError:
            # Fallback for older urllib3 versions
            retry_strategy = Retry(
                method_whitelist=["HEAD", "GET", "OPTIONS"], **retry_kwargs)

        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=20,
            pool_maxsize=20
        )
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Set headers for better success rate
        session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
        })

        return session

    def _init_database(self) -> None:
        """Initialize SQLite database with enhanced tables for new features."""
        try:
            with self._get_db_connection() as conn:
                # Enhanced proxies table with geographic and quality data
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS proxies (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        proxy TEXT NOT NULL,
                        host TEXT NOT NULL,
                        port INTEGER NOT NULL,
                        protocol TEXT DEFAULT 'http',
                        country TEXT,
                        country_code TEXT,
                        region TEXT,
                        city TEXT,
                        latitude REAL DEFAULT 0.0,
                        longitude REAL DEFAULT 0.0,
                        isp TEXT,
                        anonymity TEXT,
                        status TEXT NOT NULL,
                        response_time REAL,
                        data_size INTEGER DEFAULT 0,
                        quality_score REAL DEFAULT 0.0,
                        source TEXT,
                        last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        success_count INTEGER DEFAULT 0,
                        failure_count INTEGER DEFAULT 0,
                        headers_leaked BOOLEAN DEFAULT 0,
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
                        socks_proxies INTEGER DEFAULT 0,
                        http_proxies INTEGER DEFAULT 0,
                        geographic_distribution TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # Create enhanced indexes for better performance
                conn.execute(
                    'CREATE INDEX IF NOT EXISTS idx_proxy_status ON proxies(status)')
                conn.execute(
                    'CREATE INDEX IF NOT EXISTS idx_proxy_last_checked ON proxies(last_checked)')
                conn.execute(
                    'CREATE INDEX IF NOT EXISTS idx_proxy_response_time ON proxies(response_time)')
                conn.execute(
                    'CREATE INDEX IF NOT EXISTS idx_proxy_quality_score ON proxies(quality_score)')
                conn.execute(
                    'CREATE INDEX IF NOT EXISTS idx_proxy_country ON proxies(country_code)')
                conn.execute(
                    'CREATE INDEX IF NOT EXISTS idx_proxy_protocol ON proxies(protocol)')
                conn.execute(
                    'CREATE INDEX IF NOT EXISTS idx_proxy_anonymity ON proxies(anonymity)')

                conn.commit()
                logger.info(f"Enhanced database initialized at {self.db_path}")

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
        """Fetch proxies from multiple sources with enhanced error handling.

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
        self._fetch_stats = {
            'sources_attempted': len(sources),
            'sources_successful': 0,
            'proxies_fetched': 0,
            'socks_proxies_found': 0,
            'http_proxies_found': 0,
            'fetch_errors': [],
            'fetch_duration': 0,
            'geographical_distribution': {}
        }

        # Mapping of source names to their fetch methods
        fetch_methods = {
            'free-proxy-list': self._fetch_from_free_proxy_list,
            'proxylist-geonode': self._fetch_from_geonode,
            'proxy-list-org': self._fetch_from_proxy_list_org,
            'proxyscrape-http': self._fetch_from_proxyscrape_http,
            'proxyscrape-https': self._fetch_from_proxyscrape_https,
            'proxyscrape-socks4': self._fetch_from_proxyscrape_socks4,
            'proxyscrape-socks5': self._fetch_from_proxyscrape_socks5,
            'pubproxy': self._fetch_from_pubproxy,
            'proxyspace': self._fetch_from_proxyspace,
            'proxydb': self._fetch_from_proxydb,
            'github-proxy-list': self._fetch_from_github_proxy_list,
            'github-free-proxies': self._fetch_from_github_free_proxies,
            'github-proxy-daily': self._fetch_from_github_proxy_daily,
            'github-socks4': self._fetch_from_github_socks4,
            'github-socks5': self._fetch_from_github_socks5,
            'spys-one': self._fetch_from_spys_one,
            'cool-proxy': self._fetch_from_cool_proxy,
            'hidemyname': self._fetch_from_hidemyname,
            'freeproxylist': self._fetch_from_freeproxylist,
        }

        for source in sources:
            try:
                if source not in fetch_methods:
                    logger.warning(f"Unknown source: {source}")
                    continue

                logger.info(f"Fetching proxies from {source}...")
                proxies = fetch_methods[source]()

                if proxies:
                    # Tag proxies with source information
                    tagged_proxies = []
                    for proxy in proxies:
                        if isinstance(proxy, str):
                            tagged_proxies.append(
                                {'proxy': proxy, 'source': source})
                        else:
                            tagged_proxies.append(proxy)

                    all_proxies.extend(tagged_proxies)
                    self._fetch_stats['sources_successful'] += 1

                    # Count by protocol type
                    if 'socks' in source.lower():
                        self._fetch_stats['socks_proxies_found'] += len(
                            proxies)
                    else:
                        self._fetch_stats['http_proxies_found'] += len(proxies)

                    logger.info(
                        f"Successfully fetched {len(proxies)} proxies from {source}")
                else:
                    logger.warning(f"No proxies found from {source}")

            except Exception as e:
                error_msg = f"Failed to fetch from {source}: {e}"
                logger.error(error_msg)
                self._fetch_stats['fetch_errors'].append(error_msg)
                continue

        if self._fetch_stats['sources_successful'] == 0:
            raise ProxyHunterError(
                f"Failed to fetch proxies from any source. Errors: {self._fetch_stats['fetch_errors']}")

        # Remove duplicates while preserving order and filter invalid proxies
        unique_proxies = []
        seen = set()

        for proxy_data in all_proxies:
            if isinstance(proxy_data, dict):
                proxy = proxy_data['proxy']
                source = proxy_data['source']
            else:
                proxy = proxy_data
                source = 'unknown'

            if proxy and proxy not in seen and self._is_valid_proxy_format(proxy):
                unique_proxies.append({'proxy': proxy, 'source': source})
                seen.add(proxy)

        self._fetch_stats['proxies_fetched'] = len(unique_proxies)
        logger.info(
            f"Total unique proxies fetched: {len(unique_proxies)} from {self._fetch_stats['sources_successful']}/{self._fetch_stats['sources_attempted']} sources")

        # Track geographic distribution during fetching
        if self.enable_geolocation and unique_proxies:
            sample_size = min(20, len(unique_proxies))
            sample_proxies = random.sample(unique_proxies, sample_size)
            geo_distribution = {}

            for proxy_data in sample_proxies:
                try:
                    host, _ = self._parse_proxy(proxy_data['proxy'])
                    location = self.geo_detector.get_location(host)
                    country = location.get('country', 'Unknown')
                    geo_distribution[country] = geo_distribution.get(
                        country, 0) + 1
                except:
                    continue

            self._fetch_stats['geographical_distribution'] = geo_distribution

        # Optional: Validate proxies immediately after fetching
        if self.validate_on_fetch and unique_proxies:
            logger.info("Starting immediate validation of fetched proxies...")
            # Quick validation of first 50
            validation_sample = unique_proxies[:50]
            results = self.validate_proxies(validation_sample)
            self.save_to_database(results)
            working_proxies = [r['proxy']
                               for r in results if r['status'] == 'ok']
            logger.info(
                f"Quick validation: {len(working_proxies)} working proxies found")

        # Return just proxy strings for compatibility
        return [proxy_data['proxy'] for proxy_data in unique_proxies]

    def _fetch_from_free_proxy_list(self) -> List[str]:
        """Fetch proxies from free-proxy-list.net."""
        try:
            response = self.session.get(
                self.PROXY_SOURCES['free-proxy-list'], timeout=self.timeout)
            response.raise_for_status()

            # Extract IP:PORT patterns
            ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}:\d{2,5}\b'
            proxies = re.findall(ip_pattern, response.text)

            return proxies

        except RequestException as e:
            raise ProxyHunterError(
                f"Failed to fetch from free-proxy-list: {e}")

    def _fetch_from_geonode(self) -> List[str]:
        """Fetch proxies from proxylist.geonode.com API."""
        try:
            response = self.session.get(
                self.PROXY_SOURCES['proxylist-geonode'], timeout=self.timeout)
            response.raise_for_status()

            data = response.json()
            proxies = []

            for item in data.get('data', []):
                if item.get('ip') and item.get('port'):
                    proxies.append(f"{item['ip']}:{item['port']}")

            return proxies

        except (RequestException, json.JSONDecodeError) as e:
            raise ProxyHunterError(f"Failed to fetch from geonode: {e}")

    def _fetch_from_proxy_list_org(self) -> List[str]:
        """Fetch proxies from proxy-list.download API."""
        try:
            response = self.session.get(
                self.PROXY_SOURCES['proxy-list-org'], timeout=self.timeout)
            response.raise_for_status()

            # Response is plain text with one proxy per line
            proxies = []
            for line in response.text.strip().split('\n'):
                line = line.strip()
                if line and self._is_valid_proxy_format(line):
                    proxies.append(line)

            return proxies

        except RequestException as e:
            raise ProxyHunterError(f"Failed to fetch from proxy-list-org: {e}")

    def _fetch_from_proxyscrape_http(self) -> List[str]:
        """Fetch HTTP proxies from proxyscrape API."""
        try:
            response = self.session.get(
                self.PROXY_SOURCES['proxyscrape-http'], timeout=self.timeout)
            response.raise_for_status()

            # Response is plain text with one proxy per line
            proxies = []
            for line in response.text.strip().split('\n'):
                line = line.strip()
                if line and self._is_valid_proxy_format(line):
                    proxies.append(line)

            return proxies

        except RequestException as e:
            raise ProxyHunterError(
                f"Failed to fetch from proxyscrape-http: {e}")

    def _fetch_from_proxyscrape_https(self) -> List[str]:
        """Fetch HTTPS proxies from proxyscrape API."""
        try:
            response = self.session.get(
                self.PROXY_SOURCES['proxyscrape-https'], timeout=self.timeout)
            response.raise_for_status()

            # Response is plain text with one proxy per line
            proxies = []
            for line in response.text.strip().split('\n'):
                line = line.strip()
                if line and self._is_valid_proxy_format(line):
                    proxies.append(line)

            return proxies

        except RequestException as e:
            raise ProxyHunterError(
                f"Failed to fetch from proxyscrape-https: {e}")

    def _fetch_from_proxyscrape_socks4(self) -> List[str]:
        """Fetch SOCKS4 proxies from proxyscrape API."""
        try:
            response = self.session.get(
                self.PROXY_SOURCES['proxyscrape-socks4'], timeout=self.timeout)
            response.raise_for_status()

            # Response is plain text with one proxy per line
            proxies = []
            for line in response.text.strip().split('\n'):
                line = line.strip()
                if line and self._is_valid_proxy_format(line):
                    proxies.append(line)

            return proxies

        except RequestException as e:
            raise ProxyHunterError(
                f"Failed to fetch from proxyscrape-socks4: {e}")

    def _fetch_from_proxyscrape_socks5(self) -> List[str]:
        """Fetch SOCKS5 proxies from proxyscrape API."""
        try:
            response = self.session.get(
                self.PROXY_SOURCES['proxyscrape-socks5'], timeout=self.timeout)
            response.raise_for_status()

            # Response is plain text with one proxy per line
            proxies = []
            for line in response.text.strip().split('\n'):
                line = line.strip()
                if line and self._is_valid_proxy_format(line):
                    proxies.append(line)

            return proxies

        except RequestException as e:
            raise ProxyHunterError(
                f"Failed to fetch from proxyscrape-socks5: {e}")

    def _fetch_from_pubproxy(self) -> List[str]:
        """Fetch proxies from pubproxy API."""
        try:
            response = self.session.get(
                self.PROXY_SOURCES['pubproxy'], timeout=self.timeout)
            response.raise_for_status()

            data = response.json()
            proxies = []

            for item in data.get('data', []):
                if item.get('ipPort'):
                    proxies.append(item['ipPort'])
                elif item.get('ip') and item.get('port'):
                    proxies.append(f"{item['ip']}:{item['port']}")

            return proxies

        except (RequestException, json.JSONDecodeError) as e:
            raise ProxyHunterError(f"Failed to fetch from pubproxy: {e}")

    def _fetch_from_proxyspace(self) -> List[str]:
        """Fetch proxies from proxyspace API."""
        try:
            response = self.session.get(
                self.PROXY_SOURCES['proxyspace'], timeout=self.timeout)
            response.raise_for_status()

            # Try to parse as JSON, fallback to text
            try:
                data = response.json()
                proxies = []
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and item.get('ip') and item.get('port'):
                            proxies.append(f"{item['ip']}:{item['port']}")
                return proxies
            except json.JSONDecodeError:
                # Fallback to text parsing
                proxies = []
                for line in response.text.strip().split('\n'):
                    line = line.strip()
                    if line and self._is_valid_proxy_format(line):
                        proxies.append(line)
                return proxies

        except RequestException as e:
            raise ProxyHunterError(f"Failed to fetch from proxyspace: {e}")

    def _fetch_from_proxydb(self) -> List[str]:
        """Fetch proxies from proxydb.net."""
        try:
            response = self.session.get(
                self.PROXY_SOURCES['proxydb'], timeout=self.timeout)
            response.raise_for_status()

            # Extract IP:PORT patterns from HTML
            ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}:\d{2,5}\b'
            proxies = re.findall(ip_pattern, response.text)

            return proxies

        except RequestException as e:
            raise ProxyHunterError(f"Failed to fetch from proxydb: {e}")

    def _fetch_from_github_proxy_list(self) -> List[str]:
        """Fetch proxies from GitHub proxy-list repository."""
        try:
            response = self.session.get(
                self.PROXY_SOURCES['github-proxy-list'], timeout=self.timeout)
            response.raise_for_status()

            proxies = []
            for line in response.text.strip().split('\n'):
                line = line.strip()
                if line and self._is_valid_proxy_format(line):
                    proxies.append(line)

            return proxies

        except RequestException as e:
            raise ProxyHunterError(
                f"Failed to fetch from github-proxy-list: {e}")

    def _fetch_from_github_free_proxies(self) -> List[str]:
        """Fetch proxies from GitHub free proxies repository."""
        try:
            response = self.session.get(
                self.PROXY_SOURCES['github-free-proxies'], timeout=self.timeout)
            response.raise_for_status()

            proxies = []
            for line in response.text.strip().split('\n'):
                line = line.strip()
                if line and self._is_valid_proxy_format(line):
                    proxies.append(line)

            return proxies

        except RequestException as e:
            raise ProxyHunterError(
                f"Failed to fetch from github-free-proxies: {e}")

    def _fetch_from_github_proxy_daily(self) -> List[str]:
        """Fetch proxies from GitHub daily proxy repository."""
        try:
            response = self.session.get(
                self.PROXY_SOURCES['github-proxy-daily'], timeout=self.timeout)
            response.raise_for_status()

            proxies = []
            for line in response.text.strip().split('\n'):
                line = line.strip()
                if line and self._is_valid_proxy_format(line):
                    proxies.append(line)

            return proxies

        except RequestException as e:
            raise ProxyHunterError(
                f"Failed to fetch from github-proxy-daily: {e}")

    def _fetch_from_github_socks4(self) -> List[str]:
        """Fetch SOCKS4 proxies from GitHub repository."""
        try:
            response = self.session.get(
                self.PROXY_SOURCES['github-socks4'], timeout=self.timeout)
            response.raise_for_status()

            proxies = []
            for line in response.text.strip().split('\n'):
                line = line.strip()
                if line and self._is_valid_proxy_format(line):
                    proxies.append(line)

            return proxies

        except RequestException as e:
            raise ProxyHunterError(
                f"Failed to fetch from github-socks4: {e}")

    def _fetch_from_github_socks5(self) -> List[str]:
        """Fetch SOCKS5 proxies from GitHub repository."""
        try:
            response = self.session.get(
                self.PROXY_SOURCES['github-socks5'], timeout=self.timeout)
            response.raise_for_status()

            proxies = []
            for line in response.text.strip().split('\n'):
                line = line.strip()
                if line and self._is_valid_proxy_format(line):
                    proxies.append(line)

            return proxies

        except RequestException as e:
            raise ProxyHunterError(
                f"Failed to fetch from github-socks5: {e}")

    def _fetch_from_spys_one(self) -> List[str]:
        """Fetch proxies from spys.one (web scraping)."""
        try:
            response = self.session.get(
                self.PROXY_SOURCES['spys-one'], timeout=self.timeout)
            response.raise_for_status()

            # Extract IP:PORT patterns from HTML
            ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}:\d{2,5}\b'
            proxies = re.findall(ip_pattern, response.text)

            return proxies

        except RequestException as e:
            raise ProxyHunterError(f"Failed to fetch from spys-one: {e}")

    def _fetch_from_cool_proxy(self) -> List[str]:
        """Fetch proxies from cool-proxy.net (web scraping)."""
        try:
            response = self.session.get(
                self.PROXY_SOURCES['cool-proxy'], timeout=self.timeout)
            response.raise_for_status()

            # Extract IP:PORT patterns from HTML
            ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}:\d{2,5}\b'
            proxies = re.findall(ip_pattern, response.text)

            return proxies

        except RequestException as e:
            raise ProxyHunterError(f"Failed to fetch from cool-proxy: {e}")

    def _fetch_from_hidemyname(self) -> List[str]:
        """Fetch proxies from hidemy.name (web scraping)."""
        try:
            response = self.session.get(
                self.PROXY_SOURCES['hidemyname'], timeout=self.timeout)
            response.raise_for_status()

            # Extract IP:PORT patterns from HTML
            ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}:\d{2,5}\b'
            proxies = re.findall(ip_pattern, response.text)

            return proxies

        except RequestException as e:
            raise ProxyHunterError(f"Failed to fetch from hidemyname: {e}")

    def _fetch_from_freeproxylist(self) -> List[str]:
        """Fetch proxies from freeproxylist.co (web scraping)."""
        try:
            response = self.session.get(
                self.PROXY_SOURCES['freeproxylist'], timeout=self.timeout)
            response.raise_for_status()

            # Extract IP:PORT patterns from HTML
            ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}:\d{2,5}\b'
            proxies = re.findall(ip_pattern, response.text)

            return proxies

        except RequestException as e:
            raise ProxyHunterError(f"Failed to fetch from freeproxylist: {e}")

    def get_fetch_statistics(self) -> Dict[str, Any]:
        """Get statistics about the last fetch operation."""
        return self._fetch_stats.copy()

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
                response = self.session.get(
                    url, timeout=self.timeout, verify=False)

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

    def _validate_single_proxy(self, proxy: str, public_ip: Optional[str], source: str = '') -> Dict[str, Any]:
        """Validate a single proxy with enhanced testing and comprehensive analysis."""
        start_time = time.time()

        try:
            host, port = self._parse_proxy(proxy)

            # Check blacklist first to avoid wasting time on known bad proxies
            if self.blacklist and self.blacklist.is_blacklisted(proxy):
                return {
                    'proxy': proxy,
                    'host': host,
                    'port': port,
                    'status': 'blacklisted',
                    'response_time': None,
                    'data_size': 0,
                    'proxy_ip': None,
                    'is_anonymous': False,
                    'error': 'Proxy is blacklisted'
                }

            # First, check if proxy is reachable with socket connection
            if not self._test_proxy_connection(host, port):
                return {
                    'proxy': proxy,
                    'host': host,
                    'port': port,
                    'status': 'unreachable',
                    'response_time': None,
                    'data_size': 0,
                    'proxy_ip': None,
                    'is_anonymous': False,
                    'error': 'Connection failed'
                }

            # Detect proxy protocol automatically
            detected_protocol = self._detect_proxy_protocol(proxy)

            # For SOCKS proxies, we only validate connectivity
            if detected_protocol in ['socks4', 'socks5']:
                elapsed = time.time() - start_time
                return {
                    'proxy': proxy,
                    'host': host,
                    'port': port,
                    'protocol': detected_protocol,
                    'status': 'ok',
                    'response_time': round(elapsed, 3),
                    'data_size': 0,
                    'proxy_ip': 'N/A',  # Cannot determine IP for SOCKS without HTTP request
                    'is_anonymous': True,  # SOCKS proxies are generally anonymous
                    'anonymity': 'anonymous',
                    'source': source
                }

            # For HTTP/HTTPS proxies, perform comprehensive testing
            proxy_dict = {
                'http': f'http://{host}:{port}',
                'https': f'http://{host}:{port}',
            }

            # Use a prioritized list of test URLs (fastest and most reliable first)
            test_urls = ['httpbin', 'ipecho', 'checkip',
                         'ipinfo', 'ipapi', 'ifconfig']

            for test_name in test_urls:
                if test_name not in self.TEST_URLS:
                    continue

                test_url = self.TEST_URLS[test_name]

                try:
                    # Use random user agent for each test
                    headers = {
                        'User-Agent': random.choice(self.USER_AGENTS),
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.5',
                        'Connection': 'close',  # Avoid connection pooling issues
                    }

                    response = self.session.get(
                        test_url,
                        proxies=proxy_dict,
                        headers=headers,
                        timeout=self.timeout,
                        allow_redirects=True,
                        verify=False,
                        stream=False  # Don't stream to avoid hanging connections
                    )

                    # Check if we got a valid response
                    if response.status_code == 200 and response.content:
                        proxy_ip = self._extract_ip_from_response(
                            test_name, response)

                        if proxy_ip and self._is_valid_ip(proxy_ip):
                            # Basic anonymity check
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

                            # Perform advanced anonymity testing
                            anonymity_info = self._check_advanced_anonymity(
                                proxy, proxy_ip)

                            # Get geographic location
                            geo_info = self._get_proxy_geolocation(proxy_ip)

                            # Calculate quality score
                            proxy_data = {
                                'response_time': elapsed,
                                'anonymity': anonymity_info['level'],
                                'source': source,
                                'success_count': 1,
                                'failure_count': 0
                            }
                            quality_score = self.quality_scorer.calculate_score(
                                proxy_data)

                            # Comprehensive result with all enhanced data
                            result = {
                                'proxy': proxy,
                                'host': host,
                                'port': port,
                                'protocol': detected_protocol,
                                'status': 'ok',
                                'response_time': round(elapsed, 3),
                                'data_size': len(response.content),
                                'proxy_ip': proxy_ip,
                                'is_anonymous': is_anonymous,
                                'anonymity': anonymity_info['level'],
                                'headers_leaked': anonymity_info['headers_leaked'],
                                'leaked_headers': anonymity_info['leaked_headers'],
                                'quality_score': quality_score,
                                'source': source,
                                'test_url': test_url,
                                'test_service': test_name,
                                # Geographic information
                                'country': geo_info.get('country', 'Unknown'),
                                'country_code': geo_info.get('country_code', ''),
                                'region': geo_info.get('region', 'Unknown'),
                                'city': geo_info.get('city', 'Unknown'),
                                'latitude': geo_info.get('latitude', 0.0),
                                'longitude': geo_info.get('longitude', 0.0),
                                'isp': geo_info.get('isp', 'Unknown')
                            }

                            return result

                except (ConnectionError, Timeout) as e:
                    # These are expected for bad proxies, try next URL
                    logger.debug(
                        f"Proxy {proxy} failed connectivity test with {test_name}: {e}")
                    continue
                except Exception as e:
                    # Unexpected errors, log but continue
                    logger.debug(
                        f"Proxy {proxy} unexpected error with {test_name}: {e}")
                    continue

            # If all test URLs failed
            return {
                'proxy': proxy,
                'host': host,
                'port': port,
                'protocol': detected_protocol,
                'status': 'failed',
                'response_time': None,
                'data_size': 0,
                'proxy_ip': None,
                'is_anonymous': False,
                'anonymity': 'unknown',
                'error': 'All test URLs failed',
                'source': source
            }

        except ProxyValidationError as e:
            return {
                'proxy': proxy,
                'host': '',
                'port': 0,
                'protocol': 'unknown',
                'status': 'invalid',
                'response_time': None,
                'data_size': 0,
                'proxy_ip': None,
                'is_anonymous': False,
                'anonymity': 'unknown',
                'error': str(e),
                'source': source
            }
        except Exception as e:
            return {
                'proxy': proxy,
                'host': '',
                'port': 0,
                'protocol': 'unknown',
                'status': 'error',
                'response_time': None,
                'data_size': 0,
                'proxy_ip': None,
                'is_anonymous': False,
                'anonymity': 'unknown',
                'error': str(e),
                'source': source
            }

    def _test_proxy_connection(self, host: str, port: int) -> bool:
        """Test basic TCP connection to proxy server."""
        try:
            # Quick socket connection test with optimized timeout
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.socket_timeout)  # Configurable timeout
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except Exception:
            return False

    def _test_socks4_proxy(self, host: str, port: int) -> bool:
        """Test SOCKS4 proxy connectivity."""
        try:
            # Create socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.socket_timeout)

            # Connect to proxy
            sock.connect((host, port))

            # SOCKS4 request to connect to a test server (httpbin.org:80)
            # SOCKS4 format: VER | CMD | DSTPORT | DSTIP | USERID | NULL
            test_host = '127.0.0.1'  # Use localhost for quick test
            test_port = 80

            # Pack SOCKS4 request
            # VER=4, CMD=1 (CONNECT), DSTPORT
            request = struct.pack('>BBH', 4, 1, test_port)
            request += socket.inet_aton(test_host)  # DSTIP
            request += b'\x00'  # NULL terminator for USERID

            # Send request
            sock.send(request)

            # Read response (8 bytes)
            response = sock.recv(8)
            sock.close()

            # Check if response indicates success (second byte should be 0x5A)
            return len(response) >= 2 and response[1] == 0x5A

        except Exception:
            return False

    def _test_socks5_proxy(self, host: str, port: int) -> bool:
        """Test SOCKS5 proxy connectivity."""
        try:
            # Create socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.socket_timeout)

            # Connect to proxy
            sock.connect((host, port))

            # SOCKS5 greeting: VER | NMETHODS | METHODS
            greeting = b'\x05\x01\x00'  # VER=5, NMETHODS=1, METHOD=0 (no auth)
            sock.send(greeting)

            # Read greeting response
            response = sock.recv(2)
            if len(response) != 2 or response[0] != 5:
                sock.close()
                return False

            # SOCKS5 connect request to test server
            # VER | CMD | RSV | ATYP | DST.ADDR | DST.PORT
            test_host = '127.0.0.1'
            test_port = 80

            # VER=5, CMD=1 (CONNECT), RSV=0
            request = struct.pack('>BBB', 5, 1, 0)
            request += b'\x01'  # ATYP=1 (IPv4)
            request += socket.inet_aton(test_host)  # DST.ADDR
            request += struct.pack('>H', test_port)  # DST.PORT

            sock.send(request)

            # Read response (at least 4 bytes)
            response = sock.recv(10)
            sock.close()

            # Check if response indicates success (second byte should be 0x00)
            return len(response) >= 2 and response[1] == 0x00

        except Exception:
            return False

    def _detect_proxy_protocol(self, proxy: str) -> str:
        """Detect proxy protocol automatically."""
        host, port = self._parse_proxy(proxy)

        # Test different protocols in order of likelihood
        if self._test_proxy_connection(host, port):
            # Try HTTP first (most common)
            if self._test_http_proxy(host, port):
                return 'http'
            # Try SOCKS5
            elif self.enable_socks and self._test_socks5_proxy(host, port):
                return 'socks5'
            # Try SOCKS4
            elif self.enable_socks and self._test_socks4_proxy(host, port):
                return 'socks4'

        return 'unknown'

    def _test_http_proxy(self, host: str, port: int) -> bool:
        """Test HTTP proxy with a simple request."""
        try:
            proxy_dict = {
                'http': f'http://{host}:{port}',
                'https': f'http://{host}:{port}',
            }

            response = self.session.get(
                'http://httpbin.org/ip',
                proxies=proxy_dict,
                timeout=self.socket_timeout,
                verify=False
            )

            return response.status_code == 200
        except Exception:
            return False

    def _check_advanced_anonymity(self, proxy: str, proxy_ip: str) -> Dict[str, Any]:
        """Perform advanced anonymity testing to detect header leaks."""
        anonymity_result = {
            'level': 'transparent',
            'headers_leaked': False,
            'leaked_headers': [],
            'real_ip_leaked': False
        }

        try:
            host, port = self._parse_proxy(proxy)
            proxy_dict = {
                'http': f'http://{host}:{port}',
                'https': f'http://{host}:{port}',
            }

            # Test with headers endpoint
            headers = {
                'User-Agent': random.choice(self.USER_AGENTS),
                'X-Real-IP': self._public_ip,  # This should be hidden
                'X-Forwarded-For': self._public_ip,
                'Via': 'test-client',
            }

            response = self.session.get(
                self.ANONYMITY_TEST_URLS['httpbin_headers'],
                proxies=proxy_dict,
                headers=headers,
                timeout=self.timeout,
                verify=False
            )

            if response.status_code == 200:
                data = response.json()
                received_headers = data.get('headers', {})

                # Check for leaked headers
                leaked_headers = []
                for header_name in ['X-Real-IP', 'X-Forwarded-For', 'Via']:
                    if header_name in received_headers:
                        leaked_headers.append(header_name)
                        if self._public_ip and self._public_ip in received_headers[header_name]:
                            anonymity_result['real_ip_leaked'] = True

                anonymity_result['leaked_headers'] = leaked_headers
                anonymity_result['headers_leaked'] = len(leaked_headers) > 0

                # Determine anonymity level
                if not leaked_headers and not anonymity_result['real_ip_leaked']:
                    anonymity_result['level'] = 'elite'
                elif len(leaked_headers) <= 1 and not anonymity_result['real_ip_leaked']:
                    anonymity_result['level'] = 'anonymous'
                else:
                    anonymity_result['level'] = 'transparent'

        except Exception as e:
            logger.debug(f"Advanced anonymity test failed for {proxy}: {e}")

        return anonymity_result

    def _get_proxy_geolocation(self, proxy_ip: str) -> Dict[str, Any]:
        """Get geographic location for proxy IP."""
        if not self.geo_detector:
            return {}

        try:
            location = self.geo_detector.get_location(proxy_ip)
            return location
        except Exception as e:
            logger.debug(f"Geolocation failed for {proxy_ip}: {e}")
            return {}

    def _warm_proxy_pool(self) -> List[Dict[str, Any]]:
        """Pre-warm proxy pool with validated proxies for faster access."""
        current_time = time.time()

        # Return cached warmed proxies if still valid
        if (self._warmed_proxies and self._warm_cache_time and
                current_time - self._warm_cache_time < self._warm_cache_duration):
            return self._warmed_proxies

        logger.info("🔥 Warming proxy pool for faster access...")

        try:
            # Get recent working proxies from database
            working_proxies = self.get_working_proxies(limit=50)

            if len(working_proxies) < 20:
                # Not enough cached proxies, fetch and validate new ones
                logger.info(
                    "Insufficient cached proxies, fetching fresh batch...")
                fresh_proxies = self.fetch_proxies()

                # Quick validation of a subset
                results = self.validate_proxies(
                    fresh_proxies[:100], show_progress=False)
                self.save_to_database(results)

                # Update working proxies
                working_proxies = self.get_working_proxies(limit=50)

            # Update cache
            self._warmed_proxies = working_proxies
            self._warm_cache_time = current_time

            logger.info(
                f"✅ Proxy pool warmed with {len(working_proxies)} working proxies")
            return working_proxies

        except Exception as e:
            logger.error(f"Failed to warm proxy pool: {e}")
            return []

    def _extract_ip_from_response(self, service_name: str, response: requests.Response) -> Optional[str]:
        """Extract IP address from service response."""
        try:
            content = response.text.strip()

            if service_name == 'httpbin':
                data = response.json()
                return data.get('origin', '').split(',')[0].strip()
            elif service_name == 'ipapi':
                data = response.json()
                return data.get('query', '')
            elif service_name == 'ipify':
                data = response.json()
                return data.get('ip', '')
            elif service_name in ['ipecho', 'checkip', 'myip']:
                # Plain text response
                return content.split('\n')[0].strip()
            elif service_name == 'ipinfo':
                # Plain text IP
                return content
            else:
                # Try to extract IP from any format
                ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
                matches = re.findall(ip_pattern, content)
                return matches[0] if matches else None

        except (json.JSONDecodeError, KeyError, IndexError):
            # Fallback: try to extract IP with regex
            ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
            matches = re.findall(ip_pattern, response.text)
            return matches[0] if matches else None
        except Exception:
            return None

    def validate_proxies(self, proxies: Union[List[str], List[Dict[str, Any]]], show_progress: bool = True) -> List[Dict[str, Any]]:
        """Validate a list of proxies using enhanced multi-threading.

        Args:
            proxies: List of proxy strings or proxy dictionaries with source info
            show_progress: Whether to show progress information

        Returns:
            List of validation results with comprehensive data
        """
        if not proxies:
            return []

        # Get public IP for anonymity testing
        public_ip = self._get_public_ip(
        ) if self.anonymous_only or self.enable_geolocation else None
        results = []

        # Normalize proxy input format
        proxy_tasks = []
        for proxy_item in proxies:
            if isinstance(proxy_item, dict):
                proxy = proxy_item['proxy']
                source = proxy_item.get('source', 'unknown')
            else:
                proxy = proxy_item
                source = 'unknown'
            proxy_tasks.append((proxy, source))

        logger.info(
            f"Starting enhanced validation of {len(proxy_tasks)} proxies using {self.threads} threads")
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            # Submit all tasks with source information
            future_to_proxy = {}
            for proxy, source in proxy_tasks:
                future = executor.submit(
                    self._validate_single_proxy, proxy, public_ip, source)
                future_to_proxy[future] = (proxy, source)

            # Collect results with enhanced progress tracking
            completed = 0
            successful = 0
            socks_found = 0
            http_found = 0

            for future in as_completed(future_to_proxy):
                try:
                    result = future.result()
                    results.append(result)
                    completed += 1

                    # Track success and protocol statistics
                    if result['status'] == 'ok':
                        successful += 1
                        protocol = result.get('protocol', 'http')
                        if 'socks' in protocol:
                            socks_found += 1
                        else:
                            http_found += 1

                    # Update blacklist for failed proxies
                    if self.blacklist and result['status'] in ['failed', 'error', 'unreachable']:
                        proxy, source = future_to_proxy[future]
                        # Auto-blacklist after multiple failures (this would be tracked in database)
                        # For now, we'll let the blacklist system handle it through database updates

                    if show_progress and completed % 10 == 0:
                        success_rate = successful / completed * 100
                        logger.info(
                            f"Validated {completed}/{len(proxy_tasks)} proxies - {successful} working ({success_rate:.1f}%)")

                except Exception as e:
                    proxy, source = future_to_proxy[future]
                    logger.error(f"Error validating {proxy}: {e}")
                    results.append({
                        'proxy': proxy,
                        'status': 'error',
                        'error': str(e),
                        'source': source
                    })
                    completed += 1

        elapsed = time.time() - start_time

        # Enhanced completion statistics
        logger.info(f"✅ Validation completed in {elapsed:.2f}s:")
        logger.info(
            f"   Total: {len(results)} | Working: {successful} | Failed: {len(results) - successful}")
        logger.info(f"   HTTP/HTTPS: {http_found} | SOCKS: {socks_found}")
        logger.info(f"   Success rate: {successful/len(results)*100:.1f}%")
        logger.info(f"   Speed: {len(results)/elapsed:.1f} proxies/second")

        return results

    def save_to_database(self, results: List[Dict[str, Any]]) -> None:
        """Save enhanced validation results to SQLite database."""
        if not results:
            return

        try:
            with self._get_db_connection() as conn:
                for result in results:
                    # Enhanced database record with all new fields
                    conn.execute('''
                        INSERT OR REPLACE INTO proxies (
                            proxy, host, port, protocol, status, response_time, data_size,
                            country, country_code, region, city, latitude, longitude, isp,
                            anonymity, headers_leaked, quality_score, source,
                            last_checked, success_count, failure_count
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                                 COALESCE((SELECT success_count FROM proxies WHERE proxy = ?), 0) +
                                 CASE WHEN ? = 'ok' THEN 1 ELSE 0 END,
                                 COALESCE((SELECT failure_count FROM proxies WHERE proxy = ?), 0) +
                                 CASE WHEN ? != 'ok' THEN 1 ELSE 0 END)
                    ''', (
                        result['proxy'],
                        result.get('host', ''),
                        result.get('port', 0),
                        result.get('protocol', 'http'),
                        result['status'],
                        result.get('response_time'),
                        result.get('data_size', 0),
                        result.get('country', 'Unknown'),
                        result.get('country_code', ''),
                        result.get('region', 'Unknown'),
                        result.get('city', 'Unknown'),
                        result.get('latitude', 0.0),
                        result.get('longitude', 0.0),
                        result.get('isp', 'Unknown'),
                        result.get('anonymity', 'transparent'),
                        result.get('headers_leaked', False),
                        result.get('quality_score', 0.0),
                        result.get('source', 'unknown'),
                        datetime.now().isoformat(),
                        result['proxy'],  # for success_count calculation
                        result['status'],
                        result['proxy'],  # for failure_count calculation
                        result['status']
                    ))

                    # Auto-blacklist failed proxies if enabled
                    if (self.blacklist and result['status'] in ['failed', 'error', 'unreachable']):
                        # Get current failure stats
                        cursor = conn.execute('''
                            SELECT success_count, failure_count FROM proxies
                            WHERE proxy = ?
                        ''', (result['proxy'],))
                        stats = cursor.fetchone()
                        if stats:
                            success_count, failure_count = stats
                            self.blacklist.auto_blacklist_failed_proxy(
                                result['proxy'], failure_count, success_count + failure_count)

                # Enhanced scan statistics
                successful = sum(1 for r in results if r['status'] == 'ok')
                failed = len(results) - successful
                socks_proxies = sum(1 for r in results if r.get(
                    'protocol', '').startswith('socks'))
                http_proxies = successful - socks_proxies

                avg_response_time = (
                    sum(r.get('response_time', 0)
                        for r in results if r.get('response_time')) / successful
                    if successful > 0 else 0
                )

                # Collect geographic distribution
                geo_distribution = {}
                for r in results:
                    if r['status'] == 'ok' and r.get('country'):
                        country = r['country']
                        geo_distribution[country] = geo_distribution.get(
                            country, 0) + 1

                conn.execute('''
                    INSERT INTO proxy_stats (
                        total_proxies, successful_proxies, failed_proxies,
                        average_response_time, scan_duration, socks_proxies,
                        http_proxies, geographic_distribution
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    len(results), successful, failed, avg_response_time,
                    time.time(), socks_proxies, http_proxies,
                    json.dumps(geo_distribution)
                ))

                conn.commit()
                logger.info(
                    f"💾 Saved {len(results)} enhanced results to database")
                logger.info(f"   Working: {successful} | Failed: {failed}")
                logger.info(
                    f"   HTTP: {http_proxies} | SOCKS: {socks_proxies}")

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
                'User-Agent': self.user_agent,
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
        proxies = self.get_fast_proxies(
            max_response_time=max_response_time, limit=count)
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

    def get_proxies_by_quality(self, min_quality_score: float = 50.0, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get working proxies filtered by quality score.

        Args:
            min_quality_score: Minimum quality score (0-100)
            limit: Maximum number of proxies to return

        Returns:
            List of high-quality proxy records
        """
        try:
            with self._get_db_connection() as conn:
                query = '''
                    SELECT * FROM proxies
                    WHERE status = 'ok' AND quality_score >= ?
                    ORDER BY quality_score DESC, response_time ASC
                '''
                params = [min_quality_score]

                if limit is not None:
                    query += ' LIMIT ?'
                    params.append(limit)

                cursor = conn.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to fetch proxies by quality: {e}")

    def get_proxies_by_protocol(self, protocol: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get working proxies filtered by protocol.

        Args:
            protocol: Protocol type ('http', 'https', 'socks4', 'socks5')
            limit: Maximum number of proxies to return

        Returns:
            List of proxy records matching the protocol
        """
        try:
            with self._get_db_connection() as conn:
                query = '''
                    SELECT * FROM proxies
                    WHERE status = 'ok' AND protocol = ?
                    ORDER BY quality_score DESC, response_time ASC
                '''
                params = [protocol]

                if limit is not None:
                    query += ' LIMIT ?'
                    params.append(limit)

                cursor = conn.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to fetch proxies by protocol: {e}")

    def get_elite_proxies_enhanced(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get elite anonymity proxies with enhanced filtering.

        Args:
            limit: Maximum number of proxies to return

        Returns:
            List of elite proxy records
        """
        try:
            with self._get_db_connection() as conn:
                query = '''
                    SELECT * FROM proxies
                    WHERE status = 'ok' AND anonymity = 'elite' AND headers_leaked = 0
                    ORDER BY quality_score DESC, response_time ASC
                '''
                params = []

                if limit is not None:
                    query += ' LIMIT ?'
                    params.append(limit)

                cursor = conn.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to fetch elite proxies: {e}")

    def get_proxies_by_geolocation(self, country_code: str = None, region: str = None,
                                   city: str = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get working proxies filtered by geographic location.

        Args:
            country_code: Country code filter (e.g., 'US', 'UK')
            region: Region/state filter
            city: City filter
            limit: Maximum number of proxies to return

        Returns:
            List of proxy records matching location criteria
        """
        try:
            with self._get_db_connection() as conn:
                conditions = ["status = 'ok'"]
                params = []

                if country_code:
                    conditions.append("UPPER(country_code) = UPPER(?)")
                    params.append(country_code)

                if region:
                    conditions.append("LOWER(region) LIKE LOWER(?)")
                    params.append(f"%{region}%")

                if city:
                    conditions.append("LOWER(city) LIKE LOWER(?)")
                    params.append(f"%{city}%")

                query = f'''
                    SELECT * FROM proxies
                    WHERE {" AND ".join(conditions)}
                    ORDER BY quality_score DESC, response_time ASC
                '''

                if limit is not None:
                    query += ' LIMIT ?'
                    params.append(limit)

                cursor = conn.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to fetch proxies by geolocation: {e}")

    def get_socks_proxies(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get working SOCKS proxies (SOCKS4 and SOCKS5).

        Args:
            limit: Maximum number of proxies to return

        Returns:
            List of SOCKS proxy records
        """
        try:
            with self._get_db_connection() as conn:
                query = '''
                    SELECT * FROM proxies
                    WHERE status = 'ok' AND (protocol = 'socks4' OR protocol = 'socks5')
                    ORDER BY protocol, quality_score DESC, response_time ASC
                '''
                params = []

                if limit is not None:
                    query += ' LIMIT ?'
                    params.append(limit)

                cursor = conn.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to fetch SOCKS proxies: {e}")

    def get_proxy_analytics(self) -> Dict[str, Any]:
        """Get comprehensive proxy analytics and insights.

        Returns:
            Dictionary with detailed analytics
        """
        try:
            with self._get_db_connection() as conn:
                analytics = {}

                # Basic statistics
                cursor = conn.execute('''
                    SELECT status, COUNT(*) as count, AVG(quality_score) as avg_quality
                    FROM proxies
                    GROUP BY status
                ''')
                status_stats = {row[0]: {
                    'count': row[1], 'avg_quality': row[2] or 0} for row in cursor.fetchall()}
                analytics['status_distribution'] = status_stats

                # Protocol distribution
                cursor = conn.execute('''
                    SELECT protocol, COUNT(*) as count
                    FROM proxies
                    WHERE status = 'ok'
                    GROUP BY protocol
                ''')
                protocol_stats = dict(cursor.fetchall())
                analytics['protocol_distribution'] = protocol_stats

                # Anonymity distribution
                cursor = conn.execute('''
                    SELECT anonymity, COUNT(*) as count
                    FROM proxies
                    WHERE status = 'ok'
                    GROUP BY anonymity
                ''')
                anonymity_stats = dict(cursor.fetchall())
                analytics['anonymity_distribution'] = anonymity_stats

                # Geographic distribution (top 10 countries)
                cursor = conn.execute('''
                    SELECT country, COUNT(*) as count
                    FROM proxies
                    WHERE status = 'ok' AND country != 'Unknown'
                    GROUP BY country
                    ORDER BY count DESC
                    LIMIT 10
                ''')
                geo_stats = dict(cursor.fetchall())
                analytics['geographic_distribution'] = geo_stats

                # Quality score distribution
                cursor = conn.execute('''
                    SELECT
                        CASE
                            WHEN quality_score >= 80 THEN 'Excellent (80-100)'
                            WHEN quality_score >= 60 THEN 'Good (60-79)'
                            WHEN quality_score >= 40 THEN 'Fair (40-59)'
                            WHEN quality_score >= 20 THEN 'Poor (20-39)'
                            ELSE 'Very Poor (0-19)'
                        END as quality_range,
                        COUNT(*) as count
                    FROM proxies
                    WHERE status = 'ok'
                    GROUP BY quality_range
                ''')
                quality_stats = dict(cursor.fetchall())
                analytics['quality_distribution'] = quality_stats

                # Source reliability
                cursor = conn.execute('''
                    SELECT source, COUNT(*) as total,
                           SUM(CASE WHEN status = 'ok' THEN 1 ELSE 0 END) as working,
                           AVG(quality_score) as avg_quality
                    FROM proxies
                    GROUP BY source
                    HAVING total > 5
                    ORDER BY working DESC
                ''')
                source_stats = {}
                for row in cursor.fetchall():
                    source, total, working, avg_quality = row
                    source_stats[source] = {
                        'total': total,
                        'working': working,
                        'success_rate': working / total * 100,
                        'avg_quality': avg_quality or 0
                    }
                analytics['source_reliability'] = source_stats

                # Performance metrics
                cursor = conn.execute('''
                    SELECT
                        AVG(response_time) as avg_response_time,
                        MIN(response_time) as min_response_time,
                        MAX(response_time) as max_response_time,
                        COUNT(*) as total_working
                    FROM proxies
                    WHERE status = 'ok' AND response_time IS NOT NULL
                ''')
                perf_stats = dict(cursor.fetchone())
                analytics['performance_metrics'] = perf_stats

                return analytics

        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to get proxy analytics: {e}")

    def search_proxies(self, query: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search proxies by various criteria.

        Args:
            query: Search query (can match IP, country, city, ISP)
            limit: Maximum number of results

        Returns:
            List of matching proxy records
        """
        try:
            with self._get_db_connection() as conn:
                sql_query = '''
                    SELECT * FROM proxies
                    WHERE status = 'ok' AND (
                        proxy LIKE ? OR
                        country LIKE ? OR
                        city LIKE ? OR
                        isp LIKE ? OR
                        host LIKE ?
                    )
                    ORDER BY quality_score DESC, response_time ASC
                '''
                search_term = f"%{query}%"
                params = [search_term] * 5

                if limit is not None:
                    sql_query += ' LIMIT ?'
                    params.append(limit)

                cursor = conn.execute(sql_query, params)
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to search proxies: {e}")

    def cleanup_old_proxies(self, days: int = 7) -> int:
        """Remove old proxy records from database.

        Args:
            days: Number of days to keep records

        Returns:
            Number of records deleted
        """
        try:
            with self._get_db_connection() as conn:
                cutoff_date = datetime.now() - timedelta(days=days)
                cursor = conn.execute('''
                    DELETE FROM proxies
                    WHERE last_checked < ? AND status != 'ok'
                ''', (cutoff_date.isoformat(),))

                deleted_count = cursor.rowcount
                conn.commit()

                logger.info(f"🧹 Cleaned up {deleted_count} old proxy records")
                return deleted_count

        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to cleanup old proxies: {e}")

    def get_warmed_proxies(self) -> List[Dict[str, Any]]:
        """Get pre-warmed proxy pool for instant access.

        Returns:
            List of warmed proxy records
        """
        return self._warm_proxy_pool()

    def refresh_proxy_pool(self, force: bool = False) -> Dict[str, Any]:
        """Manually refresh the proxy pool with fresh data.

        Args:
            force: Force refresh even if cache is still valid

        Returns:
            Refresh statistics
        """
        if force:
            self._warmed_proxies = None
            self._warm_cache_time = None

        fresh_proxies = self.fetch_proxies()
        # Limit for reasonable refresh time
        results = self.validate_proxies(fresh_proxies[:200])
        self.save_to_database(results)

        # Update warmed cache
        self._warm_proxy_pool()

        working_count = sum(1 for r in results if r['status'] == 'ok')

        return {
            'total_fetched': len(fresh_proxies),
            'validated': len(results),
            'working': working_count,
            'success_rate': working_count / len(results) * 100 if results else 0,
            'timestamp': datetime.now().isoformat()
        }

    def close(self) -> None:
        """Clean up resources."""
        if hasattr(self, 'session'):
            self.session.close()

    def _is_valid_proxy_format(self, proxy: str) -> bool:
        """Validate basic proxy format (host:port)."""
        try:
            if not proxy or ':' not in proxy:
                return False
            host, port = proxy.split(':', 1)
            return bool(host.strip() and port.strip().isdigit() and 1 <= int(port) <= 65535)
        except (ValueError, AttributeError):
            return False


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
    parser.add_argument(
        "--db", help="SQLite database path for storing results.")
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
