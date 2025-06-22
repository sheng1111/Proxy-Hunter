# Proxy Hunter

[中文版說明](README.zh-TW.md)

## Overview

Proxy Hunter is a powerful Python tool designed for scraping and testing the availability of free proxies from [Free Proxy List](https://free-proxy-list.net/). It employs regular expressions to collect a list of IP addresses and tests their validity using [ipify](https://www.ipify.org/). It's an essential tool for developers and security analysts who require a quick and reliable method of obtaining free and working proxy servers.

## Features

- **Scrape Free Proxies**: Automatically scrapes free proxy servers from Free Proxy List.
- **Proxy Validation**: Checks the validity of each proxy server by attempting to connect to the internet using the proxy.
- **Output Customization**: Allows users to specify the output file for the list of valid proxies.
- **File-Based Proxy Check**: Supports checking the validity of proxies listed in a user-specified file.
- **Thread Control**: Choose how many threads are used for proxy validation.
- **Anonymous Proxy Filter**: Optionally keep only proxies that hide your real IP.
- **Flexible Output Formats**: Save results in plain text or JSON format.

## Prerequisites

Before you begin, ensure you have met the following requirements:

- Python 3.x installed on your machine
- `requests` library installed

## Installation

### Clone the repository or download the source code:

```bash
git clone https://your-repository-link.git
```

#### Install the required Python packages:

```bash
pip install -r requirements.txt
```

## Usage

### Getting New Proxies

Run the script without any arguments to scrape new proxies and save them to `proxy.txt` (default filename):

```bash
python -m proxyhunter
```

### Custom Output Filename

To specify a different output file for the proxies, use the `-o` or `--output` option:

```bash
python -m proxyhunter -o existing_proxies.txt
```

### Advanced Options

Specify thread count, only keep anonymous proxies and save as JSON:

```bash
python -m proxyhunter -t 20 -a -f json -o proxies.json
```

### Web Dashboard

Launch a simple Flask dashboard to monitor proxies and see response-time charts:

```bash
python -m proxyhunter.web_app
```

### Using as a Library

You can also import :class:`ProxyHunter` in your own code:

```python
from proxyhunter import ProxyHunter

hunter = ProxyHunter()
proxies = hunter.fetch_proxies()
results = hunter.check_proxies(proxies)
```

### Help

For more information on the command-line options, use the `-h` or `--help` option:

```bash
python -m proxyhunter -h
```

## License

Distributed under the MIT License. See `LICENSE` for more information.
