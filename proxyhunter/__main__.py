"""ProxyHunter command-line interface.

This module provides the main entry point when the package is executed directly
with `python -m proxyhunter`.

Supports both CLI operations and web dashboard launch.
"""

import sys
import argparse
from pathlib import Path

def main():
    """Main entry point for the ProxyHunter CLI."""
    parser = argparse.ArgumentParser(
        description="ProxyHunter - Professional proxy fetching and validation tool",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    # Add subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # CLI subcommand (default behavior)
    cli_parser = subparsers.add_parser('scan', help='Scan and validate proxies')
    cli_parser.add_argument("-o", "--output", default="proxies.txt",
                           help="Output file name")
    cli_parser.add_argument("-c", "--check", 
                           help="Check proxies from file")
    cli_parser.add_argument("-u", "--update",
                           help="Update proxies in file")
    cli_parser.add_argument("-t", "--threads", type=int, default=10,
                           help="Number of threads")
    cli_parser.add_argument("-f", "--format", choices=["txt", "json", "jsonl"], 
                           default="txt", help="Output format")
    cli_parser.add_argument("-a", "--anonymous-only", action="store_true",
                           help="Only anonymous proxies")
    cli_parser.add_argument("--timeout", type=int, default=5,
                           help="Timeout in seconds")
    cli_parser.add_argument("--db", help="Database path")
    cli_parser.add_argument("--stats", action="store_true",
                           help="Show statistics")
    cli_parser.add_argument("--limit", type=int,
                           help="Limit number of proxies")
    
    # Web dashboard subcommand
    web_parser = subparsers.add_parser('web', help='Launch web dashboard')
    web_parser.add_argument("--host", default="0.0.0.0",
                           help="Host to bind to (default: 0.0.0.0)")
    web_parser.add_argument("--port", type=int, default=5000,
                           help="Port to bind to (default: 5000)")
    web_parser.add_argument("--debug", action="store_true",
                           help="Enable debug mode")
    
    # Quick scan subcommand
    quick_parser = subparsers.add_parser('quick', help='Quick proxy scan')
    quick_parser.add_argument("-t", "--threads", type=int, default=10,
                             help="Number of threads")
    quick_parser.add_argument("-a", "--anonymous-only", action="store_true",
                             help="Only anonymous proxies")
    quick_parser.add_argument("--limit", type=int, default=50,
                             help="Limit number of proxies to test")
    
    # Parse arguments
    args = parser.parse_args()
    
    # If no command specified, default to scan
    if not args.command:
        args.command = 'scan'
        # Re-parse with scan defaults
        from .core import _cli
        _cli()
        return
    
    # Handle different commands
    if args.command == 'web':
        print(f"Starting ProxyHunter web dashboard on http://{args.host}:{args.port}")
        print("Press Ctrl+C to stop the server")
        
        from .web_app import app
        app.run(host=args.host, port=args.port, debug=args.debug)
        
    elif args.command == 'quick':
        from . import quick_scan
        
        print("Starting quick proxy scan...")
        working_proxies = quick_scan(
            threads=args.threads,
            anonymous_only=args.anonymous_only,
            limit=args.limit
        )
        
        print(f"\nFound {len(working_proxies)} working proxies:")
        for proxy in working_proxies[:10]:  # Show first 10
            print(f"  {proxy['proxy']} ({proxy.get('response_time', 'N/A')}s)")
        
        if len(working_proxies) > 10:
            print(f"  ... and {len(working_proxies) - 10} more")
        
    elif args.command == 'scan':
        # Use the existing CLI from core
        from .core import _cli
        
        # Modify sys.argv to work with the existing CLI
        original_argv = sys.argv[:]
        sys.argv = ['proxyhunter'] + sys.argv[2:]  # Remove 'scan' subcommand
        
        try:
            _cli()
        finally:
            sys.argv = original_argv

if __name__ == "__main__":
    main()
