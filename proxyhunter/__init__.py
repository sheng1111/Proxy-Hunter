"""ProxyHunter - Professional proxy fetching and validation tool.

A comprehensive solution for fetching, validating, and managing free proxies
for red team operations, web scraping, and security testing.

Features:
- Fetch proxies from multiple sources
- Validate proxy connectivity and anonymity
- Store results in SQLite database
- Export results in multiple formats
- Thread-safe operations
- Modern web dashboard
- Multi-language support

Example:
    >>> from proxyhunter import ProxyHunter
    >>> hunter = ProxyHunter(threads=20, anonymous_only=True)
    >>> proxies = hunter.fetch_proxies()
    >>> results = hunter.validate_proxies(proxies)
    >>> hunter.save_to_database(results)
    >>> working_proxies = hunter.get_working_proxies(limit=10)

    # Quick proxy usage for requests
    >>> from proxyhunter import get_proxy, ProxySession
    >>> proxy_url = get_proxy()  # Get a working proxy URL
    >>>
    >>> # Use with requests
    >>> import requests
    >>> response = requests.get('https://httpbin.org/ip', proxies={'http': proxy_url, 'https': proxy_url})
    >>>
    >>> # Or use ProxySession for automatic proxy management
    >>> session = ProxySession()
    >>> response = session.get('https://httpbin.org/ip')
"""

from .core import ProxyHunter as Hunter  # Shorter alias
from .core import (
    ProxyHunter,
    ProxyHunterError,
    ProxyValidationError,
    DatabaseError
)

# Import new proxy session functionality
from .proxy_session import ProxySession

# Version information
__version__ = "2.0.5"
__author__ = "Terry Wang"
__github__ = "https://github.com/sheng1111/Proxy-Hunter"
__license__ = "MIT"
__description__ = "Professional proxy fetching and validation tool for red team operations and web scraping"
__url__ = "https://github.com/sheng1111/Proxy-Hunter"

# Main exports
__all__ = [
    "ProxyHunter",
    "ProxyHunterError",
    "ProxyValidationError",
    "DatabaseError",
    "ProxySession",
    "get_proxy",
    "get_proxies",
    "run_web_dashboard",
    "quick_scan",
    "__version__"
]

# Global hunter instance for quick access
_global_hunter = None


def _get_global_hunter():
    """Get or create a global ProxyHunter instance."""
    global _global_hunter
    if _global_hunter is None:
        _global_hunter = ProxyHunter(threads=20, timeout=10)
        # Try to get fresh proxies if database is empty
        try:
            stats = _global_hunter.get_statistics()
            if stats.get('working_proxies', 0) == 0:
                proxies = _global_hunter.fetch_proxies()
                results = _global_hunter.validate_proxies(
                    proxies[:50])  # Validate first 50 for quick start
                _global_hunter.save_to_database(results)
        except Exception:
            pass  # Continue even if initial fetch fails
    return _global_hunter


def get_proxy() -> str:
    """Get a single working proxy URL for immediate use.

    Returns:
        A proxy URL in format 'http://host:port' ready to use with requests

    Example:
        >>> import requests
        >>> from proxyhunter import get_proxy
        >>>
        >>> proxy_url = get_proxy()
        >>> proxies = {'http': proxy_url, 'https': proxy_url}
        >>> response = requests.get('https://httpbin.org/ip', proxies=proxies)
        >>> print(response.json())
    """
    hunter = _get_global_hunter()
    working_proxies = hunter.get_working_proxies(limit=1)

    if not working_proxies:
        # No proxies available, try to fetch and validate new ones
        try:
            proxies = hunter.fetch_proxies()
            results = hunter.validate_proxies(proxies[:20])  # Quick validation
            hunter.save_to_database(results)
            working_proxies = hunter.get_working_proxies(limit=1)
        except Exception as e:
            raise ProxyHunterError(f"Unable to get working proxy: {e}")

    if not working_proxies:
        raise ProxyHunterError("No working proxies available")

    proxy_info = working_proxies[0]
    return f"http://{proxy_info['proxy']}"


def get_proxies(count: int = 10, country: str = None, max_response_time: float = None) -> list:
    """Get multiple working proxy URLs.

    Args:
        count: Number of proxies to return (default: 10)
        country: Filter by country code (e.g., 'US', 'UK') (default: None)
        max_response_time: Maximum response time in seconds (default: None)

    Returns:
        List of proxy URLs in format 'http://host:port'

    Example:
        >>> from proxyhunter import get_proxies
        >>>
        >>> # Get 5 US proxies with fast response time
        >>> proxy_urls = get_proxies(count=5, country='US', max_response_time=2.0)
        >>>
        >>> # Use with requests
        >>> import requests
        >>> for proxy_url in proxy_urls:
        >>>     proxies = {'http': proxy_url, 'https': proxy_url}
        >>>     try:
        >>>         response = requests.get('https://httpbin.org/ip', proxies=proxies, timeout=10)
        >>>         print(f"Using {proxy_url}: {response.json()}")
        >>>         break
        >>>     except:
        >>>         continue
    """
    hunter = _get_global_hunter()

    # Get proxies based on filters
    if country:
        working_proxies = hunter.get_proxies_by_country(
            country, limit=count * 2)
    elif max_response_time:
        working_proxies = hunter.get_fast_proxies(
            max_response_time=max_response_time, limit=count * 2)
    else:
        working_proxies = hunter.get_working_proxies(limit=count * 2)

    if not working_proxies:
        # Try to fetch new proxies
        try:
            proxies = hunter.fetch_proxies()
            results = hunter.validate_proxies(proxies[:50])
            hunter.save_to_database(results)
            working_proxies = hunter.get_working_proxies(limit=count * 2)
        except Exception as e:
            raise ProxyHunterError(f"Unable to get working proxies: {e}")

    # Convert to proxy URLs and return requested count
    proxy_urls = []
    for proxy_info in working_proxies[:count]:
        proxy_urls.append(f"http://{proxy_info['proxy']}")

    return proxy_urls


def run_web_dashboard(host: str = "0.0.0.0", port: int = 5000, debug: bool = False):
    """Launch the web dashboard.

    Args:
        host: Host to bind to (default: "0.0.0.0")
        port: Port to bind to (default: 5000)
        debug: Enable debug mode (default: False)

    Example:
        >>> from proxyhunter import run_web_dashboard
        >>> run_web_dashboard(port=8080)
    """
    from .web_app import app
    app.run(host=host, port=port, debug=debug)


def quick_scan(threads: int = 10, anonymous_only: bool = False, limit: int = None) -> list:
    """Quick proxy scan and validation.

    Args:
        threads: Number of concurrent threads (default: 10)
        anonymous_only: Only return anonymous proxies (default: False)
        limit: Limit number of proxies to test (default: None)

    Returns:
        List of working proxy dictionaries

    Example:
        >>> from proxyhunter import quick_scan
        >>> working_proxies = quick_scan(threads=20, limit=50)
        >>> print(f"Found {len(working_proxies)} working proxies")
    """
    hunter = ProxyHunter(threads=threads, anonymous_only=anonymous_only)

    try:
        # Fetch proxies
        proxies = hunter.fetch_proxies()

        # Limit if specified
        if limit:
            proxies = proxies[:limit]

        # Validate proxies
        results = hunter.validate_proxies(proxies)

        # Save to database
        hunter.save_to_database(results)

        # Return only working proxies
        return [r for r in results if r['status'] == 'ok']

    finally:
        hunter.close()


# Convenience imports for common use cases
