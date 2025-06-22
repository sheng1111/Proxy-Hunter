"""Proxy Hunter module.

This module exposes a :class:`ProxyHunter` class that can fetch free proxies
and validate them. The module can also be executed directly as a CLI tool for
obtaining and checking proxies.
"""

from __future__ import annotations

import json
import re
from argparse import ArgumentParser, RawTextHelpFormatter
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict

import requests


class ProxyHunter:
    """Fetch and validate free proxies."""

    SOURCE_URL = "https://free-proxy-list.net/"
    IPIFY_URL = "https://api.ipify.org?format=json"

    def __init__(self, threads: int = 10, anonymous_only: bool = False,
                 timeout: int = 5) -> None:
        self.threads = threads
        self.anonymous_only = anonymous_only
        self.timeout = timeout

    # ------------------------------------------------------------------
    # fetching
    def fetch_proxies(self) -> List[str]:
        """Scrape a list of proxies from ``free-proxy-list.net``."""
        response = requests.get(self.SOURCE_URL)
        response.raise_for_status()
        ips = re.findall(r"\d+\.\d+\.\d+\.\d+:\d+", response.text)
        return list(dict.fromkeys(ips))

    def _get_public_ip(self) -> str | None:
        """Return the current public IP address."""
        try:
            resp = requests.get(self.IPIFY_URL, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json().get("ip")
        except requests.RequestException:
            return None

    # ------------------------------------------------------------------
    # validation helpers
    def _check_proxy(self, ip: str, results: List[Dict[str, str | float]], my_ip: str | None) -> None:
        start = requests.utils.default_timer()
        try:
            resp = requests.get(
                self.IPIFY_URL,
                proxies={"http": ip, "https": ip},
                timeout=self.timeout,
            )
            resp.raise_for_status()
            proxy_ip = resp.json().get("ip")
            if self.anonymous_only and proxy_ip == my_ip:
                return
            elapsed = requests.utils.default_timer() - start
            size = len(resp.content)
            results.append({
                "proxy": ip,
                "status": "ok",
                "response_time": round(elapsed, 2),
                "data_size": size,
            })
        except requests.RequestException:
            results.append({
                "proxy": ip,
                "status": "failed",
                "response_time": None,
                "data_size": 0,
            })

    def check_proxies(self, ips: List[str]) -> List[Dict[str, str | float]]:
        """Validate a list of proxy IP strings."""
        results: List[Dict[str, str | float]] = []
        my_ip = self._get_public_ip() if self.anonymous_only else None

        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            for ip in ips:
                executor.submit(self._check_proxy, ip, results, my_ip)

        return results

    # ------------------------------------------------------------------
    # convenience helpers
    def save(self, results: List[Dict[str, str | float]], filename: str,
             fmt: str = "txt", mode: str = "w") -> None:
        """Save proxy results to ``filename`` in the given format."""
        with open(filename, mode, encoding="utf-8") as fh:
            if fmt == "json":
                json.dump([r["proxy"] for r in results if r["status"] == "ok"], fh,
                          ensure_ascii=False, indent=2)
            else:
                for r in results:
                    if r["status"] == "ok":
                        fh.write(f"{r['proxy']}\n")


def _read_ips_from_file(filename: str) -> List[str]:
    try:
        with open(filename, "r", encoding="utf8") as file:
            ips = [line.strip() for line in file if line.strip()]
        return list(dict.fromkeys(ips))
    except FileNotFoundError:
        print("The file does not exist.")
        return []


def _cli() -> None:
    parser = ArgumentParser(
        description="Get the proxy list from this tool and check the proxy is valid or not.",
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
    parser.add_argument("-f", "--format", choices=["txt", "json"], default="txt",
                        help="Output file format.")
    parser.add_argument("-a", "--anonymous-only", action="store_true",
                        help="Only keep proxies that hide your real IP.")
    parser.add_argument("--timeout", type=int, default=5,
                        help="Timeout in seconds for each proxy check.")

    args = parser.parse_args()

    hunter = ProxyHunter(
        threads=args.threads,
        anonymous_only=args.anonymous_only,
        timeout=args.timeout,
    )

    if args.check:
        ips = _read_ips_from_file(args.check)
        results = hunter.check_proxies(ips)
        hunter.save(results, args.check, fmt=args.format, mode="w")
    elif args.update:
        ips = _read_ips_from_file(args.update)
        results = hunter.check_proxies(ips)
        hunter.save(results, args.update, fmt=args.format, mode="w")
    else:
        ips = hunter.fetch_proxies()
        results = hunter.check_proxies(ips)
        hunter.save(results, args.output, fmt=args.format, mode="w")

    print("All threads have finished to get proxy.")


if __name__ == "__main__":
    _cli()

