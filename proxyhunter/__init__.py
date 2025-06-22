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
"""

from .core import (
    ProxyHunter,
    ProxyHunterError,
    ProxyValidationError,
    DatabaseError
)

# Version information
__version__ = "2.0.0"
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
    "run_web_dashboard",
    "quick_scan",
    "__version__"
]

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
from .core import ProxyHunter as Hunter  # Shorter alias
