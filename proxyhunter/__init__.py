"""ProxyHunter - Professional proxy fetching and validation tool.

This package provides comprehensive proxy management for red team operations,
web scraping, and security testing with support for 15+ proxy sources.

Enhanced Features:
- HTTP/HTTPS and SOCKS4/SOCKS5 proxy support
- Geographic location detection and filtering
- Dynamic quality scoring and ranking
- Advanced anonymity detection with header leak protection
- Blacklist/whitelist management
- Real-time performance monitoring
- Intelligent proxy pool warming

Quick Start Examples:
    # Get a single working proxy instantly
    >>> from proxyhunter import get_proxy
    >>> proxy_url = get_proxy()
    >>> print(proxy_url)  # http://1.2.3.4:8080

    # Get high-quality proxies by country
    >>> from proxyhunter import get_proxies
    >>> us_proxies = get_proxies(count=5, country='US', min_quality=70)

    # Get SOCKS proxies for advanced operations
    >>> socks_proxies = get_socks_proxies(count=3)

    # Get elite anonymity proxies for red team ops
    >>> elite_proxies = get_elite_proxies(count=5)

    # Advanced usage with ProxyHunter class
    >>> from proxyhunter import ProxyHunter
    >>> hunter = ProxyHunter(threads=30, enable_geolocation=True, enable_socks=True)
    >>> proxies = hunter.fetch_proxies()
    >>> results = hunter.validate_proxies(proxies)
"""

from .core import ProxyHunter, ProxyHunterError, ProxyValidationError, DatabaseError
from .proxy_session import ProxySession, TrafficMonitor

# Package version
__version__ = "2.3.0"

# Global hunter instance for quick access functions
_global_hunter = None
_hunter_lock = None


def _get_global_hunter():
    """Get or create the global ProxyHunter instance with enhanced settings."""
    global _global_hunter, _hunter_lock

    if _hunter_lock is None:
        import threading
        _hunter_lock = threading.Lock()

    if _global_hunter is None:
        with _hunter_lock:
            if _global_hunter is None:
                # Create enhanced hunter for quick access
                _global_hunter = ProxyHunter(
                    threads=30,  # Higher thread count for faster validation
                    timeout=8,   # Reasonable timeout
                    socket_timeout=2,  # Fast socket testing
                    anonymous_only=False,  # Allow all proxies for better availability
                    validate_on_fetch=True,  # Immediate validation
                    max_retries=2,  # Quick retries
                    enable_geolocation=True,  # Geographic detection
                    enable_socks=True,  # SOCKS proxy support
                    auto_blacklist=True,  # Automatic blacklisting
                    quality_threshold=20.0  # Low threshold for quick access
                )

    return _global_hunter


def get_proxy(prefer_country: str = None, max_response_time: float = None,
              min_quality: float = None, protocol: str = None,
              force_refresh: bool = False) -> str:
    """Get a single working proxy URL with enhanced filtering options.

    Args:
        prefer_country: Preferred country code (e.g., 'US', 'UK', 'DE') (default: None)
        max_response_time: Maximum response time in seconds (default: None)
        min_quality: Minimum quality score 0-100 (default: None)
        protocol: Preferred protocol ('http', 'https', 'socks4', 'socks5') (default: None)
        force_refresh: Force refresh of proxy pool (default: False)

    Returns:
        Single proxy URL in format 'http://host:port' or 'socks4://host:port'

    Raises:
        ProxyHunterError: If no working proxy is found

    Example:
        >>> from proxyhunter import get_proxy
        >>> import requests
        >>>
        >>> # Get any working proxy
        >>> proxy_url = get_proxy()
        >>> proxies = {'http': proxy_url, 'https': proxy_url}
        >>> response = requests.get('https://httpbin.org/ip', proxies=proxies)
        >>> print(f"Your IP: {response.json()['origin']}")
        >>>
        >>> # Get high-quality US proxy
        >>> us_proxy = get_proxy(prefer_country='US', min_quality=70)
        >>> print(f"US Proxy: {us_proxy}")
        >>>
        >>> # Get SOCKS5 proxy
        >>> socks_proxy = get_proxy(protocol='socks5')
        >>> print(f"SOCKS5 Proxy: {socks_proxy}")
    """
    hunter = _get_global_hunter()

    try:
        # Apply filters based on preferences
        if protocol and protocol.startswith('socks'):
            working_proxies = hunter.get_socks_proxies(limit=50)
            # Filter by specific SOCKS protocol
            if protocol in ['socks4', 'socks5']:
                working_proxies = [
                    p for p in working_proxies if p.get('protocol') == protocol]
        elif prefer_country:
            working_proxies = hunter.get_proxies_by_geolocation(
                country_code=prefer_country, limit=50)
        elif min_quality:
            working_proxies = hunter.get_proxies_by_quality(
                min_quality_score=min_quality, limit=50)
        else:
            working_proxies = hunter.get_working_proxies(limit=50)

        # Apply additional filters
        if max_response_time and working_proxies:
            working_proxies = [p for p in working_proxies
                               if p.get('response_time', 999) <= max_response_time]

        if not working_proxies or len(working_proxies) < 5 or force_refresh:
            # Need fresh proxies
            print("🔍 Getting fresh proxy data...")
            fresh_proxies = hunter.fetch_proxies()
            results = hunter.validate_proxies(fresh_proxies[:100])
            hunter.save_to_database(results)

            # Re-apply filters
            if protocol and protocol.startswith('socks'):
                working_proxies = hunter.get_socks_proxies(limit=50)
                if protocol in ['socks4', 'socks5']:
                    working_proxies = [
                        p for p in working_proxies if p.get('protocol') == protocol]
            elif prefer_country:
                working_proxies = hunter.get_proxies_by_geolocation(
                    country_code=prefer_country, limit=50)
            elif min_quality:
                working_proxies = hunter.get_proxies_by_quality(
                    min_quality_score=min_quality, limit=50)
            else:
                working_proxies = hunter.get_working_proxies(limit=50)

            if max_response_time and working_proxies:
                working_proxies = [p for p in working_proxies
                                   if p.get('response_time', 999) <= max_response_time]

        if not working_proxies:
            raise ProxyHunterError(
                f"No working proxies found matching criteria: "
                f"country={prefer_country}, protocol={protocol}, "
                f"max_time={max_response_time}, min_quality={min_quality}")

        # Get the best proxy (highest quality score, lowest response time)
        best_proxy = working_proxies[0]
        proxy_protocol = best_proxy.get('protocol', 'http')

        if proxy_protocol.startswith('socks'):
            proxy_url = f"{proxy_protocol}://{best_proxy['proxy']}"
        else:
            proxy_url = f"http://{best_proxy['proxy']}"

        # Display proxy info
        quality = best_proxy.get('quality_score', 0)
        country = best_proxy.get('country', 'Unknown')
        response_time = best_proxy.get('response_time', 0)

        print(f"✅ Selected {proxy_protocol.upper()} proxy: {proxy_url}")
        print(
            f"   📍 Location: {country} | ⚡ Speed: {response_time:.2f}s | 🎯 Quality: {quality:.1f}/100")

        return proxy_url

    except Exception as e:
        raise ProxyHunterError(f"Unable to get working proxy: {e}")


def get_proxies(count: int = 10, country: str = None, max_response_time: float = None,
                min_quality: float = None, protocol: str = None, anonymous_only: bool = False,
                force_refresh: bool = False) -> list:
    """Get multiple working proxy URLs with advanced filtering.

    Args:
        count: Number of proxies to return (default: 10, max: 100)
        country: Filter by country code (e.g., 'US', 'UK', 'DE') (default: None)
        max_response_time: Maximum response time in seconds (default: None)
        min_quality: Minimum quality score 0-100 (default: None)
        protocol: Filter by protocol ('http', 'https', 'socks4', 'socks5') (default: None)
        anonymous_only: Only return anonymous/elite proxies (default: False)
        force_refresh: Force refresh of proxy pool (default: False)

    Returns:
        List of proxy URLs in format 'http://host:port' or 'socks4://host:port'

    Example:
        >>> from proxyhunter import get_proxies
        >>> import requests
        >>>
        >>> # Get 5 high-quality US proxies
        >>> us_proxies = get_proxies(count=5, country='US', min_quality=60)
        >>>
        >>> # Get elite anonymous proxies
        >>> elite_proxies = get_proxies(count=3, anonymous_only=True)
        >>>
        >>> # Get fast SOCKS5 proxies
        >>> socks_proxies = get_proxies(count=5, protocol='socks5', max_response_time=3.0)
        >>>
        >>> # Test the proxies
        >>> for proxy_url in us_proxies:
        >>>     proxies = {'http': proxy_url, 'https': proxy_url}
        >>>     try:
        >>>         response = requests.get('https://httpbin.org/ip', proxies=proxies, timeout=10)
        >>>         print(f"✅ {proxy_url}: {response.json()['origin']}")
        >>>     except:
        >>>         print(f"❌ {proxy_url}: Failed")
    """
    hunter = _get_global_hunter()
    count = min(count, 100)  # Limit to reasonable number

    try:
        # Apply filters based on preferences
        working_proxies = []

        if protocol and protocol.startswith('socks'):
            working_proxies = hunter.get_socks_proxies(limit=count * 3)
            if protocol in ['socks4', 'socks5']:
                working_proxies = [
                    p for p in working_proxies if p.get('protocol') == protocol]
        elif country:
            working_proxies = hunter.get_proxies_by_geolocation(
                country_code=country, limit=count * 3)
        elif min_quality:
            working_proxies = hunter.get_proxies_by_quality(
                min_quality_score=min_quality, limit=count * 3)
        else:
            working_proxies = hunter.get_working_proxies(limit=count * 3)

        # Apply additional filters
        if anonymous_only and working_proxies:
            working_proxies = [p for p in working_proxies
                               if p.get('anonymity') in ['elite', 'anonymous']]

        if max_response_time and working_proxies:
            working_proxies = [p for p in working_proxies
                               if p.get('response_time', 999) <= max_response_time]

        if not working_proxies or len(working_proxies) < count or force_refresh:
            # Need more proxies, fetch fresh ones
            print(f"🔍 Need {count} proxies, fetching from 15+ sources...")
            fresh_proxies = hunter.fetch_proxies()
            print(
                f"✅ Found {len(fresh_proxies)} unique proxies, validating up to {min(200, len(fresh_proxies))}...")

            # Validate more proxies to get enough results
            results = hunter.validate_proxies(fresh_proxies[:200])
            hunter.save_to_database(results)

            # Re-apply all filters
            if protocol and protocol.startswith('socks'):
                working_proxies = hunter.get_socks_proxies(limit=count * 3)
                if protocol in ['socks4', 'socks5']:
                    working_proxies = [
                        p for p in working_proxies if p.get('protocol') == protocol]
            elif country:
                working_proxies = hunter.get_proxies_by_geolocation(
                    country_code=country, limit=count * 3)
            elif min_quality:
                working_proxies = hunter.get_proxies_by_quality(
                    min_quality_score=min_quality, limit=count * 3)
            else:
                working_proxies = hunter.get_working_proxies(limit=count * 3)

            if anonymous_only and working_proxies:
                working_proxies = [p for p in working_proxies
                                   if p.get('anonymity') in ['elite', 'anonymous']]

            if max_response_time and working_proxies:
                working_proxies = [p for p in working_proxies
                                   if p.get('response_time', 999) <= max_response_time]

        if not working_proxies:
            raise ProxyHunterError(
                f"No working proxies found matching criteria: "
                f"count={count}, country={country}, protocol={protocol}, "
                f"max_time={max_response_time}, min_quality={min_quality}, "
                f"anonymous_only={anonymous_only}")

        # Sort by quality score and response time
        working_proxies.sort(
            key=lambda x: (-x.get('quality_score', 0), x.get('response_time', 999)))

        # Convert to proxy URLs and return requested count
        proxy_urls = []
        for proxy_info in working_proxies[:count]:
            proxy_protocol = proxy_info.get('protocol', 'http')
            if proxy_protocol.startswith('socks'):
                proxy_url = f"{proxy_protocol}://{proxy_info['proxy']}"
            else:
                proxy_url = f"http://{proxy_info['proxy']}"
            proxy_urls.append(proxy_url)

        # Display summary
        protocols = {}
        countries = {}
        avg_quality = 0

        for proxy_info in working_proxies[:count]:
            proto = proxy_info.get('protocol', 'http')
            protocols[proto] = protocols.get(proto, 0) + 1
            country_code = proxy_info.get('country_code', 'XX')
            countries[country_code] = countries.get(country_code, 0) + 1
            avg_quality += proxy_info.get('quality_score', 0)

        avg_quality /= len(proxy_urls) if proxy_urls else 1

        print(f"🎯 Returning {len(proxy_urls)} high-quality proxies")
        print(f"   📊 Protocols: {dict(protocols)}")
        print(f"   🌍 Countries: {dict(countries)}")
        print(f"   ⭐ Avg Quality: {avg_quality:.1f}/100")

        return proxy_urls

    except Exception as e:
        raise ProxyHunterError(f"Unable to get working proxies: {e}")


def get_socks_proxies(count: int = 10, protocol: str = None) -> list:
    """Get SOCKS proxies specifically (SOCKS4 and SOCKS5).

    Args:
        count: Number of SOCKS proxies to return (default: 10)
        protocol: Specific SOCKS protocol ('socks4' or 'socks5') (default: both)

    Returns:
        List of SOCKS proxy URLs

    Example:
        >>> from proxyhunter import get_socks_proxies
        >>> # Get any SOCKS proxies
        >>> socks_proxies = get_socks_proxies(count=5)
        >>> # Get only SOCKS5 proxies
        >>> socks5_proxies = get_socks_proxies(count=3, protocol='socks5')
    """
    return get_proxies(count=count, protocol=protocol or 'socks4')


def get_elite_proxies(count: int = 10) -> list:
    """Get elite anonymity proxies with no header leaks.

    Args:
        count: Number of elite proxies to return (default: 10)

    Returns:
        List of elite proxy URLs

    Example:
        >>> from proxyhunter import get_elite_proxies
        >>> elite_proxies = get_elite_proxies(count=5)
        >>> print(f"Got {len(elite_proxies)} elite proxies")
    """
    hunter = _get_global_hunter()
    elite_proxies = hunter.get_elite_proxies_enhanced(limit=count * 2)

    if len(elite_proxies) < count:
        # Fetch more proxies
        fresh_proxies = hunter.fetch_proxies()
        results = hunter.validate_proxies(fresh_proxies[:100])
        hunter.save_to_database(results)
        elite_proxies = hunter.get_elite_proxies_enhanced(limit=count * 2)

    proxy_urls = []
    for proxy_info in elite_proxies[:count]:
        proxy_protocol = proxy_info.get('protocol', 'http')
        if proxy_protocol.startswith('socks'):
            proxy_url = f"{proxy_protocol}://{proxy_info['proxy']}"
        else:
            proxy_url = f"http://{proxy_info['proxy']}"
        proxy_urls.append(proxy_url)

    print(f"🔒 Returning {len(proxy_urls)} elite anonymity proxies")
    return proxy_urls


def quick_scan(threads: int = 30, anonymous_only: bool = False,
               limit: int = None, sources: list = None,
               include_socks: bool = True) -> list:
    """Enhanced quick proxy scan and validation with SOCKS support.

    Args:
        threads: Number of concurrent threads (default: 30, max: 50)
        anonymous_only: Only return anonymous proxies (default: False)
        limit: Limit number of proxies to test (default: None)
        sources: Specific sources to fetch from (default: all sources)
        include_socks: Include SOCKS proxy sources (default: True)

    Returns:
        List of working proxy dictionaries with detailed information

    Example:
        >>> from proxyhunter import quick_scan
        >>>
        >>> # Enhanced quick scan with SOCKS support
        >>> working_proxies = quick_scan(include_socks=True)
        >>> print(f"Found {len(working_proxies)} working proxies")
        >>>
        >>> # Scan specific sources only
        >>> github_proxies = quick_scan(sources=['github-proxy-list', 'github-socks5'])
        >>>
        >>> # Get only elite anonymous proxies with SOCKS
        >>> elite_proxies = quick_scan(anonymous_only=True, include_socks=True, limit=50)
    """
    threads = min(threads, 50)  # Limit to reasonable number
    hunter = ProxyHunter(
        threads=threads,
        anonymous_only=anonymous_only,
        validate_on_fetch=False,  # We'll validate manually
        enable_socks=include_socks,
        enable_geolocation=True,
        auto_blacklist=True
    )

    try:
        print("🚀 Starting enhanced proxy scan with SOCKS support...")

        # Fetch proxies from specified or all sources
        if sources:
            print(f"📡 Fetching from {len(sources)} specified sources...")
            proxies = hunter.fetch_proxies(sources=sources)
        else:
            print("📡 Fetching from all 15+ proxy sources (HTTP/HTTPS/SOCKS)...")
            proxies = hunter.fetch_proxies()

        print(f"🔍 Found {len(proxies)} unique proxies")

        # Limit if specified
        if limit:
            proxies = proxies[:limit]
            print(f"🎯 Testing first {len(proxies)} proxies")

        # Validate proxies with progress tracking
        print("⚡ Starting high-speed validation with enhanced features...")
        results = hunter.validate_proxies(proxies, show_progress=True)

        # Save to database for future use
        hunter.save_to_database(results)

        # Return only working proxies with enhanced info
        working_proxies = [r for r in results if r['status'] == 'ok']

        # Sort by quality score (highest first), then response time
        working_proxies.sort(
            key=lambda x: (-x.get('quality_score', 0), x.get('response_time', 999)))

        # Enhanced completion statistics
        protocols = {}
        countries = {}
        anonymity_levels = {}

        for proxy in working_proxies:
            proto = proxy.get('protocol', 'http')
            protocols[proto] = protocols.get(proto, 0) + 1

            country = proxy.get('country', 'Unknown')
            countries[country] = countries.get(country, 0) + 1

            anon = proxy.get('anonymity', 'transparent')
            anonymity_levels[anon] = anonymity_levels.get(anon, 0) + 1

        print(
            f"✅ Enhanced scan complete! Found {len(working_proxies)} working proxies")
        print(
            f"📊 Success rate: {len(working_proxies)}/{len(results)} ({len(working_proxies)/len(results)*100:.1f}%)")
        print(f"🌐 Protocols: {dict(protocols)}")
        print(f"🌍 Top countries: {dict(list(countries.items())[:5])}")
        print(f"🔒 Anonymity: {dict(anonymity_levels)}")

        return working_proxies

    except Exception as e:
        raise ProxyHunterError(f"Enhanced quick scan failed: {e}")
    finally:
        hunter.close()


def get_proxy_stats() -> dict:
    """Get comprehensive proxy pool statistics and analytics.

    Returns:
        Dictionary with detailed proxy statistics

    Example:
        >>> from proxyhunter import get_proxy_stats
        >>> stats = get_proxy_stats()
        >>> print(f"Total working proxies: {stats['performance_metrics']['total_working']}")
        >>> print(f"Geographic distribution: {stats['geographic_distribution']}")
    """
    hunter = _get_global_hunter()
    return hunter.get_proxy_analytics()


def search_proxies(query: str, limit: int = 20) -> list:
    """Search for proxies by country, city, ISP, or IP.

    Args:
        query: Search term (country, city, ISP, IP address)
        limit: Maximum number of results (default: 20)

    Returns:
        List of matching proxy dictionaries

    Example:
        >>> from proxyhunter import search_proxies
        >>> # Search by country
        >>> us_proxies = search_proxies("United States")
        >>> # Search by city
        >>> london_proxies = search_proxies("London")
        >>> # Search by ISP
        >>> aws_proxies = search_proxies("Amazon")
    """
    hunter = _get_global_hunter()
    return hunter.search_proxies(query, limit=limit)


def clear_proxy_cache() -> None:
    """Clear the global proxy cache to force fresh data."""
    global _global_hunter
    if _global_hunter:
        _global_hunter._warmed_proxies = None
        _global_hunter._warm_cache_time = None
        print("🧹 Proxy cache cleared")


def refresh_proxy_pool(force: bool = True) -> dict:
    """Manually refresh the proxy pool with fresh data.

    Args:
        force: Force refresh even if cache is still valid (default: True)

    Returns:
        Refresh statistics

    Example:
        >>> from proxyhunter import refresh_proxy_pool
        >>> stats = refresh_proxy_pool()
        >>> print(f"Refreshed pool: {stats['working']} working proxies")
    """
    hunter = _get_global_hunter()
    return hunter.refresh_proxy_pool(force=force)


# Export all public functions and classes
__all__ = [
    'ProxyHunter', 'ProxySession', 'TrafficMonitor',
    'ProxyHunterError', 'ProxyValidationError', 'DatabaseError',
    'get_proxy', 'get_proxies', 'get_socks_proxies', 'get_elite_proxies',
    'quick_scan', 'get_proxy_stats', 'search_proxies',
    'clear_proxy_cache', 'refresh_proxy_pool'
]
