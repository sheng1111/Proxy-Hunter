# ProxyHunter 🚀

<div align="center">

![ProxyHunter Logo](https://img.shields.io/badge/ProxyHunter-2.3.0-blue.svg)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/sheng1111/Proxy-Hunter.svg)](https://github.com/sheng1111/Proxy-Hunter/stargazers)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/sheng1111/Proxy-Hunter)

**🔥 Professional proxy management with SOCKS support, geographic targeting, and AI-powered validation**

[English](#english) | [繁體中文](#繁體中文) | [日本語](#日本語)

</div>

---

## English

ProxyHunter is the ultimate proxy management solution for red team operators, web scrapers, and security professionals who demand enterprise-grade proxy capabilities with cutting-edge features.

### 🔥 Revolutionary Features

- 🚀 **15+ Premium Proxy Sources** - GitHub, ProxyScrape, SOCKS proxy lists, and specialized sources
- 🛡️ **SOCKS4/SOCKS5 Support** - Complete SOCKS proxy detection, validation, and management
- 🌍 **Geographic Intelligence** - Real-time IP geolocation with country/city/ISP detection
- 🎯 **AI-Powered Quality Scoring** - Dynamic proxy ranking based on performance metrics
- ⚡ **Enhanced Validation Engine** - Socket + HTTP dual-layer testing with 7 endpoints
- 🔒 **Advanced Anonymity Detection** - Elite, Anonymous, Transparent with header leak analysis
- 🚫 **Smart Blacklist System** - Automatic failed proxy filtering and performance tracking
- 💾 **Enhanced Database Analytics** - SQLite with geographic distribution and quality metrics
- 🌐 **Modern Web Dashboard** - Real-time monitoring with advanced filtering and search
- 📊 **Interactive Analytics** - Protocol distribution, geographic insights, performance graphs
- 🛠️ **Comprehensive RESTful API** - Full programmatic control with enhanced endpoints
- 🐍 **Professional Python Library** - One-line access with intelligent caching and rotation
- 🔄 **Intelligent Pool Management** - Auto-refresh, quality-based selection, and warming
- ⚡ **Lightning-Fast Performance** - 50 concurrent threads, sub-second proxy access

### 🎯 Red Team & Penetration Testing

- **🌍 Geographic Operations** - Target-specific country/region proxy filtering
- **🔒 Elite SOCKS Proxies** - High-anonymity SOCKS4/SOCKS5 for advanced operations
- **⚡ Speed Optimization** - Sub-1-second response time filtering with quality scoring
- **🛡️ Stealth Validation** - Socket-level testing before HTTP to avoid detection
- **🔄 Advanced Rotation** - Performance-based proxy selection with auto-failover
- **📡 Tool Integration** - Native export for Burp Suite, Metasploit, curl, Python
- **🚫 Anti-Blacklist** - Automatic failed proxy removal and fresh pool management
- **📊 Operation Analytics** - Success rates, geographic distribution, performance metrics

### 🕷️ Web Scraping & Enterprise Automation

- **🚀 High-Volume Processing** - 50 concurrent threads, 1000+ proxies per minute
- **🌐 Global Proxy Network** - Access proxies from 50+ countries worldwide
- **📈 Performance Intelligence** - Real-time quality scoring and response analytics
- **💾 Enterprise Database** - SQLite with advanced indexing and query optimization
- **🔄 Smart Rotation** - AI-powered proxy selection based on success patterns
- **📊 Real-Time Dashboard** - Live monitoring with WebSocket updates and filtering
- **🛠️ API Integration** - RESTful API for enterprise automation and integration

### 🚀 Quick Start

#### Installation

```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or venv\Scripts\activate  # Windows

# Install from PyPI
pip install proxy-meshx

# Or install from source for latest features
git clone https://github.com/sheng1111/Proxy-Hunter.git
cd Proxy-Hunter
pip install -e .
```

**Note:** Package name is `proxy-meshx`, import as `proxyhunter`:

```python
from proxyhunter import ProxyHunter, get_proxy
```

#### Command Line Usage

```bash
# Quick proxy scan with enhanced validation
proxyhunter scan --threads 30 --limit 100 --anonymous-only

# Launch modern web dashboard
proxyhunter web --port 8080

# Or using Python module
python -m proxyhunter.web_app
```

#### One-Line Proxy Access 🔥

```python
from proxyhunter import get_proxy, get_proxies, get_socks_proxies, get_elite_proxies
import requests

# Get any working proxy instantly
proxy_url = get_proxy()
response = requests.get('https://httpbin.org/ip',
                       proxies={'http': proxy_url, 'https': proxy_url})
print(f"Your IP: {response.json()['origin']}")

# Get high-quality US proxies with minimum quality score
us_proxies = get_proxies(count=5, country='US', min_quality=70, max_response_time=2.0)
print(f"Found {len(us_proxies)} high-quality US proxies")

# Get SOCKS proxies for advanced operations
socks_proxies = get_socks_proxies(count=3, protocol='socks5')
print(f"SOCKS5 proxies: {socks_proxies}")

# Get elite anonymity proxies for red team operations
elite_proxies = get_elite_proxies(count=5)
print(f"Elite proxies: {elite_proxies}")

# Geographic filtering with quality constraints
uk_proxies = get_proxies(count=3, country='UK', min_quality=60, anonymous_only=True)
```

#### Advanced Usage with Enhanced Features

```python
from proxyhunter import ProxyHunter, ProxySession

# Professional ProxyHunter with SOCKS and geolocation support
hunter = ProxyHunter(
    threads=50,                    # Maximum concurrent validation
    enable_socks=True,             # Include SOCKS4/SOCKS5 proxies
    enable_geolocation=True,       # Geographic IP detection
    auto_blacklist=True,           # Automatic failed proxy filtering
    quality_threshold=50.0,        # Minimum quality score
    anonymous_only=False,          # Allow all proxy types
    validate_on_fetch=True         # Immediate validation
)

# Fetch from all sources including SOCKS
proxies = hunter.fetch_proxies()
print(f"Fetched {len(proxies)} unique proxies from 15+ sources")

# Enhanced filtering and analytics
socks_proxies = hunter.get_socks_proxies(limit=10)
quality_proxies = hunter.get_proxies_by_quality(min_quality_score=80, limit=5)
us_proxies = hunter.get_proxies_by_geolocation(country_code='US', limit=10)
elite_proxies = hunter.get_elite_proxies_enhanced(limit=5)

# Comprehensive analytics
analytics = hunter.get_proxy_analytics()
print(f"Protocol distribution: {analytics['protocol_distribution']}")
print(f"Geographic distribution: {analytics['geographic_distribution']}")
print(f"Quality distribution: {analytics['quality_distribution']}")

# Search proxies by criteria
london_proxies = hunter.search_proxies("London", limit=5)
aws_proxies = hunter.search_proxies("Amazon", limit=3)

# ProxySession with enhanced rotation
session = ProxySession(
    proxy_count=20,
    rotation_strategy='quality_based',  # Use highest quality proxies
    country_filter='US',
    protocol_filter='http',
    min_quality=60
)

response = session.get('https://httpbin.org/ip')
print(f"Response via quality proxy: {response.json()}")
```

### 🔥 Enhanced Quick Scan with SOCKS Support

```python
from proxyhunter import quick_scan, get_proxy_stats, search_proxies

# Professional scan with SOCKS and geolocation
working_proxies = quick_scan(
    threads=50,           # Maximum performance
    include_socks=True,   # Include SOCKS4/SOCKS5
    limit=200,
    anonymous_only=False
)
print(f"Found {len(working_proxies)} working proxies")

# Scan specific sources including SOCKS
socks_sources = ['github-socks5', 'proxyscrape-socks', 'socks-proxy-list']
socks_proxies = quick_scan(
    sources=socks_sources,
    include_socks=True,
    threads=30
)

# Get elite anonymous proxies with enhanced filtering
elite_proxies = quick_scan(
    anonymous_only=True,
    include_socks=True,
    threads=40,
    limit=100
)

# Comprehensive proxy analytics
stats = get_proxy_stats()
print(f"Protocol distribution: {stats['protocol_distribution']}")
print(f"Total working proxies: {stats['performance_metrics']['total_working']}")

# Search for specific geographic proxies
us_proxies = search_proxies("United States", limit=10)
tokyo_proxies = search_proxies("Tokyo", limit=5)
```

### 🎯 Red Team Use Cases with Enhanced Capabilities

#### Advanced Multi-Protocol Reconnaissance

```python
from proxyhunter import get_proxies, get_socks_proxies, get_elite_proxies
import requests
import random

# Multi-protocol reconnaissance with geographic distribution
countries = ['US', 'UK', 'DE', 'JP', 'CA', 'AU', 'NL', 'FR']
reconnaissance_proxies = {}

for country in countries:
    # Get high-quality HTTP/HTTPS proxies
    http_proxies = get_proxies(count=2, country=country, min_quality=60, max_response_time=3.0)
    # Get SOCKS proxies for advanced operations
    socks_proxies = get_socks_proxies(count=1, protocol='socks5')

    reconnaissance_proxies[country] = {
        'http': http_proxies,
        'socks': socks_proxies
    }
    print(f"📍 {country}: {len(http_proxies)} HTTP + {len(socks_proxies)} SOCKS proxies")

# Elite proxy pool for sensitive operations
elite_ops_proxies = get_elite_proxies(count=10)
print(f"🔒 Elite proxy pool: {len(elite_ops_proxies)} proxies")

# Target enumeration with proxy rotation and anonymity levels
targets = ["example.com", "test.com", "demo.org"]
user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
]

for target in targets:
    for country, proxy_sets in reconnaissance_proxies.items():
        for proxy_url in proxy_sets['http'][:1]:  # Use first proxy from each country
            try:
                headers = {
                    'User-Agent': random.choice(user_agents),
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
                }
                response = requests.get(
                    f"https://{target}",
                    proxies={'http': proxy_url, 'https': proxy_url},
                    headers=headers,
                    timeout=10,
                    verify=False
                )
                print(f"✅ {country} -> {target}: {response.status_code} ({len(response.content)} bytes)")
            except Exception as e:
                print(f"❌ {country} -> {target}: {str(e)[:50]}")
```

#### SOCKS Tunnel Operations

```python
from proxyhunter import get_socks_proxies, search_proxies

# Establish SOCKS tunnels for advanced operations
socks5_proxies = get_socks_proxies(count=5, protocol='socks5')
socks4_proxies = get_socks_proxies(count=3, protocol='socks4')

print("🔧 SOCKS5 Tunnels:")
for proxy in socks5_proxies:
    print(f"   socks5://{proxy.split('://')[-1]}")

print("🔧 SOCKS4 Tunnels:")
for proxy in socks4_proxies:
    print(f"   socks4://{proxy.split('://')[-1]}")

# Search for specific ISP or cloud provider proxies
aws_proxies = search_proxies("Amazon", limit=5)
azure_proxies = search_proxies("Microsoft", limit=3)
print(f"☁️ Cloud proxies: {len(aws_proxies)} AWS + {len(azure_proxies)} Azure")
```

#### OSINT with Enhanced Geographic Intelligence

```python
from proxyhunter import ProxySession, get_proxy_stats

# Create region-specific sessions with quality thresholds
sessions = {
    'North_America': ProxySession(
        proxy_count=8,
        country_filter='US',
        min_quality=70,
        anonymous_only=True
    ),
    'Europe': ProxySession(
        proxy_count=6,
        country_filter='UK',
        min_quality=65,
        protocol_filter='http'
    ),
    'Asia_Pacific': ProxySession(
        proxy_count=5,
        country_filter='JP',
        min_quality=60,
        rotation_strategy='quality_based'
    )
}

# Perform enhanced OSINT from different geographic locations
targets = ["linkedin.com", "twitter.com", "facebook.com", "github.com"]
for region, session in sessions.items():
    print(f"\n🌍 Starting OSINT from {region}")
    for target in targets:
        try:
            response = session.get(f"https://{target}", timeout=15)
            print(f"✅ [{region}] {target}: {response.status_code} ({response.headers.get('server', 'Unknown')})")
        except Exception as e:
            print(f"❌ [{region}] {target}: {str(e)[:50]}")

# Display comprehensive analytics
analytics = get_proxy_stats()
print(f"\n📊 Global Proxy Analytics:")
print(f"   Active Proxies: {analytics['performance_metrics']['total_working']}")
print(f"   Geographic Distribution: {analytics['geographic_distribution']}")
```

### 🌐 Enhanced Web Dashboard

Launch the professional web interface:

```bash
python -m proxyhunter.web_app
# Visit http://localhost:5000
```

**New Dashboard Features:**

- 📊 **Real-Time Analytics** - Live proxy statistics with WebSocket updates
- 📈 **Performance Charts** - Response time trends and success rate analysis
- 🌍 **Geographic Distribution** - World map showing proxy locations
- 🔄 **One-Click Operations** - Instant proxy refresh and validation
- 📋 **Smart Copy** - Copy proxies in various formats (curl, requests, etc.)
- 🌍 **Multi-Language UI** - Full interface in 3 languages
- 📱 **Mobile Responsive** - Works perfectly on all devices
- 🎨 **Modern Design** - Clean, professional interface

### 🚦 Traffic Monitoring Dashboard

Access advanced monitoring at `/traffic`:

```bash
# Start dashboard and visit http://localhost:5000/traffic
python -m proxyhunter.web_app
```

**Traffic Monitor Features:**

- 📈 **Real-Time Request Tracking** - Live monitoring of all proxy requests
- 📊 **Success/Failure Analytics** - Visual success rate analysis
- 🌍 **Geographic Usage Stats** - Proxy usage by country and region
- ⏱️ **Response Time Analysis** - Detailed latency statistics
- 📊 **Data Transfer Monitoring** - Track bandwidth usage per proxy
- 🔄 **Active Session Management** - Monitor all active proxy sessions
- 📝 **Detailed Request Logs** - Complete request/response logging
- 🚦 **Live Updates** - WebSocket-powered real-time updates

---

## 繁體中文

ProxyHunter 是終極代理管理解決方案，專為紅隊操作員、網頁爬蟲開發者和資安專業人員打造，提供企業級代理功能和尖端特色。

### 🔥 革新功能

- 🚀 **15+個頂級代理源** - GitHub、ProxyScrape、SOCKS 代理清單和專業來源
- 🛡️ **SOCKS4/SOCKS5 支援** - 完整的 SOCKS 代理檢測、驗證和管理
- 🌍 **地理智能** - 即時 IP 地理定位，支援國家/城市/ISP 檢測
- 🎯 **AI 驅動品質評分** - 基於效能指標的動態代理排名
- ⚡ **增強驗證引擎** - Socket + HTTP 雙層測試，支援 7 個端點
- 🔒 **進階匿名性檢測** - Elite、Anonymous、Transparent 與標頭洩漏分析
- 🚫 **智能黑名單系統** - 自動失效代理過濾和效能追蹤
- 💾 **增強資料庫分析** - SQLite 搭配地理分佈和品質指標
- 🌐 **現代化 Web 儀表板** - 即時監控與進階過濾和搜尋
- 📊 **互動式分析** - 協定分佈、地理洞察、效能圖表
- 🛠️ **完整 RESTful API** - 全面程式化控制與增強端點
- 🐍 **專業 Python 函式庫** - 一行存取，智能快取和輪換
- 🔄 **智能池管理** - 自動刷新、基於品質選擇和預熱
- ⚡ **閃電般效能** - 50 個併發執行緒，亞秒級代理存取

### 🎯 紅隊 & 滲透測試

- **🌍 地理操作** - 目標特定國家/地區代理過濾
- **🔒 Elite SOCKS 代理** - 進階操作的高匿名 SOCKS4/SOCKS5
- **⚡ 速度最佳化** - 亞秒級回應時間過濾與品質評分
- **🛡️ 隱蔽驗證** - HTTP 前 Socket 層級測試避免偵測
- **🔄 進階輪換** - 基於效能的代理選擇與自動故障轉移
- **📡 工具整合** - 原生匯出至 Burp Suite、Metasploit、curl、Python
- **🚫 反黑名單** - 自動移除失效代理和新池管理
- **📊 操作分析** - 成功率、地理分佈、效能指標

### 🕷️ 網頁爬蟲 & 企業自動化

- **🚀 大量處理** - 50 個併發執行緒，每分鐘 1000+個代理
- **🌐 全球代理網路** - 存取來自 50+個國家的代理
- **📈 效能智能** - 即時品質評分和回應分析
- **💾 企業資料庫** - SQLite 搭配進階索引和查詢最佳化
- **🔄 智能輪換** - AI 驅動的代理選擇基於成功模式
- **📊 即時儀表板** - WebSocket 更新和過濾的即時監控
- **🛠️ API 整合** - 企業自動化和整合的 RESTful API

### 🚀 快速開始

#### 安裝

```bash
# 建立虛擬環境（建議）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 從 PyPI 安裝
pip install proxy-meshx

# 或從原始碼安裝以獲得最新功能
git clone https://github.com/sheng1111/Proxy-Hunter.git
cd Proxy-Hunter
pip install -e .
```

**注意：** 套件名稱為 `proxy-meshx`，匯入時使用 `proxyhunter`：

```python
from proxyhunter import ProxyHunter, get_proxy
```

#### 指令列使用

```bash
# 快速代理掃描，增強驗證
proxyhunter scan --threads 30 --limit 100 --anonymous-only

# 啟動現代化 Web 儀表板
proxyhunter web --port 8080

# 或使用 Python 模組
python -m proxyhunter.web_app
```

#### 一行代碼取得代理 🔥

```python
from proxyhunter import get_proxy, get_proxies, get_socks_proxies, get_elite_proxies
import requests

# 立即取得任何可用代理
proxy_url = get_proxy()
response = requests.get('https://httpbin.org/ip',
                       proxies={'http': proxy_url, 'https': proxy_url})
print(f"您的 IP：{response.json()['origin']}")

# 取得高品質美國代理，最低品質評分要求
us_proxies = get_proxies(count=5, country='US', min_quality=70, max_response_time=2.0)
print(f"找到 {len(us_proxies)} 個高品質美國代理")

# 取得進階操作用的 SOCKS 代理
socks_proxies = get_socks_proxies(count=3, protocol='socks5')
print(f"SOCKS5 代理：{socks_proxies}")

# 取得紅隊操作用的 Elite 匿名代理
elite_proxies = get_elite_proxies(count=5)
print(f"Elite 代理：{elite_proxies}")

# 地理過濾搭配品質限制
uk_proxies = get_proxies(count=3, country='UK', min_quality=60, anonymous_only=True)
```

#### 進階使用

```python
from proxyhunter import ProxyHunter, ProxySession

# 具備 15+個源的增強版 ProxyHunter
hunter = ProxyHunter(
    threads=30,              # 高速驗證
    anonymous_only=True,     # 僅 Elite 代理
    timeout=8,              # 合理超時
    validate_on_fetch=True   # 立即驗證
)

# 從所有 15+個源獲取代理
proxies = hunter.fetch_proxies()
print(f"{len(proxies)}個的唯一代理")

# 取得獲取統計
stats = hunter.get_fetch_statistics()
print(f"成功率：{stats['sources_successful']}/{stats['sources_attempted']}")

# 進階篩選
us_elite_proxies = hunter.get_proxies_by_country('US', limit=10)
fast_proxies = hunter.get_fast_proxies(max_response_time=2.0, limit=20)

# 具有自動輪換的 ProxySession
session = ProxySession(
    proxy_count=15,
    rotation_strategy='performance',
    country_filter='US'
)

response = session.get('https://httpbin.org/ip')
print(f"回應：{response.json()}")

# 監控會話效能
stats = session.get_traffic_stats()
print(f"成功率: {stats['successful_requests']}/{stats['total_requests']}")
```

### 🔥 增強快速掃描

```python
from proxyhunter import quick_scan

# 掃描所有 15+個源，高速驗證
working_proxies = quick_scan(threads=30, limit=100)
print(f"{len(working_proxies)}個的動作代理")

# 僅掃描特定源
github_proxies = quick_scan(
    sources=['github-proxy-list', 'github-free-proxies', 'github-proxy-daily'],
    threads=20
)

# 僅取得 Elite 匿名代理
elite_proxies = quick_scan(anonymous_only=True, threads=25, limit=50)
```

### 🎯 紅隊實戰案例

#### 分散偵察

```python
from proxyhunter import get_proxies
import requests

# 分散偵察的異國代理
countries = ['US', 'UK', 'DE', 'CA', 'AU']
all_proxies = []

for country in countries:
    proxies = get_proxies(count=3, country=country, max_response_time=3.0)
    all_proxies.extend(proxies)
    print(f"{country}從{len(proxies)}個代理")

# 分散目標列舉使用
target = "example.com"
for i, proxy in enumerate(all_proxies):
    try:
        response = requests.get(f"http://{target}",
                              proxies={'http': proxy, 'https': proxy},
                              timeout=10, headers={'User-Agent': 'Mozilla/5.0...'})
        print(f"代理 {i+1}: {response.status_code}")
    except:
        continue
```

#### 地理分散 OSINT

```python
from proxyhunter import ProxySession
import requests

# 為不同地區建立多個會話
sessions = {}
for region in ['US', 'EU', 'AS']:
    sessions[region] = ProxySession(
        proxy_count=5,
        country_filter=region,
        anonymous_only=True
    )

# 異地理位置執行OSINT
targets = ["linkedin.com", "twitter.com", "facebook.com"]
for region, session in sessions.items():
    for target in targets:
        try:
            response = session.get(f"https://{target}")
            print(f"[{region}] {target}: {response.status_code}")
        except:
            print(f"[{region}] {target}: 失敗")
```

### 🌐 強化 Web 儀表板

專業 Web 介面啟動：

```bash
python -m proxyhunter.web_app
# http://localhost:5000 訪問
```

**新儀表板功能：**

- 📊 **即時分析** - WebSocket 即時代理統計
- 📈 **效能圖表** - 回應時間趨勢和成功率分析
- 🌍 **地理分布** - 顯示代理位置的世界地圖
- 🔄 **一鍵操作** - 即時代理刷新和驗證
- 📋 **智能複製** - 各種格式代理複製（curl、requests 等）
- 🌍 **多語言 UI** - 3 語言完整的介面
- 📱 **行動響應式** - 所有裝置完美運作
- 🎨 **現代設計** - 簡潔、專業介面

### 🚦 流量監控儀表板

`/traffic` 高度監控存取：

```bash
# 啟動儀表板並訪問 http://localhost:5000/traffic
python -m proxyhunter.web_app
```

**流量監控功能：**

- �� **即時請求追蹤** - 所有代理請求的即時監控
- 📊 **成功/失敗分析** - 視覺的成功的分析
- 🌍 **地理的使用統計** - 國家/地區代理使用情況
- ⏱️ **回應時間分析** - 詳細的延遲統計
- 📊 **資料傳輸監控** - 每個代理的帶寬使用量追蹤
- 🔄 **活躍會話管理** - 監控所有活躍代理會話
- 📝 **詳細請求記錄** - 完整的請求/回應記錄
- 🚦 **即時更新** - WebSocket 驅動的即時更新

---

## 日本語

ProxyHunter は、レッドチーム操作、ウェブスクレイピング、セキュリティ専門家向けの究極のプロキシ管理ソリューションで、最先端機能を備えたエンタープライズグレードのプロキシ機能を提供します。

### 🔥 革新的機能

- 🚀 **15+のプレミアムプロキシソース** - GitHub、ProxyScrape、SOCKS プロキシリスト、専門ソース
- 🛡️ **SOCKS4/SOCKS5 対応** - 完全な SOCKS プロキシ検出、検証、管理
- 🌍 **地理的インテリジェンス** - リアルタイム IP ジオロケーション（国/都市/ISP 検出）
- 🎯 **AI 駆動品質スコアリング** - パフォーマンス指標に基づく動的プロキシランキング
- ⚡ **強化検証エンジン** - Socket + HTTP デュアルレイヤーテスト（7 つのエンドポイント）
- 🔒 **高度匿名性検出** - Elite、Anonymous、Transparent でヘッダーリーク分析
- 🚫 **スマートブラックリストシステム** - 自動失敗プロキシフィルタリングとパフォーマンス追跡
- 💾 **強化データベース分析** - 地理的分布と品質指標を含む SQLite
- 🌐 **モダン Web ダッシュボード** - 高度フィルタリングと検索によるリアルタイム監視
- 📊 **インタラクティブ分析** - プロトコル分布、地理的洞察、パフォーマンスグラフ
- 🛠️ **包括的 RESTful API** - 強化エンドポイントによる完全プログラム制御
- 🐍 **プロフェッショナル Python ライブラリ** - インテリジェントキャッシュとローテーションによる 1 行アクセス
- 🔄 **インテリジェントプール管理** - 自動更新、品質ベース選択、ウォーミング
- ⚡ **超高速パフォーマンス** - 50 同期スレッド、サブ秒プロキシアクセス

### 🎯 レッドチーム & ペネトレーションテスト

- **🌍 地理的操作** - ターゲット固有の国/地域プロキシフィルタリング
- **🔒 Elite SOCKS プロキシ** - 高度操作用の高匿名 SOCKS4/SOCKS5
- **⚡ 速度最適化** - 品質スコアリングによるサブ 1 秒応答時間フィルタリング
- **🛡️ ステルス検証** - 検出回避のための HTTP 前 Socket レベルテスト
- **🔄 高度ローテーション** - 自動フェイルオーバーによるパフォーマンスベースプロキシ選択
- **📡 ツール統合** - Burp Suite、Metasploit、curl、Python へのネイティブエクスポート
- **🚫 アンチブラックリスト** - 自動失敗プロキシ削除と新プール管理
- **📊 操作分析** - 成功率、地理的分布、パフォーマンス指標

### 🕷️ ウェブスクレイピング & エンタープライズ自動化

- **🚀 大量処理** - 50 同期スレッド、毎分 1000+プロキシ
- **🌐 グローバルプロキシネットワーク** - 世界 50+カ国からのプロキシアクセス
- **📈 パフォーマンスインテリジェンス** - リアルタイム品質スコアリングと応答分析
- **💾 エンタープライズデータベース** - 高度インデックスとクエリ最適化を備えた SQLite
- **🔄 スマートローテーション** - 成功パターンに基づく AI 駆動プロキシ選択
- **📊 リアルタイムダッシュボード** - WebSocket 更新とフィルタリングによるライブ監視
- **🛠️ API 統合** - エンタープライズ自動化と統合のための RESTful API

### 🚀 クイックスタート

#### インストール

```bash
# 仮想環境の作成（推奨）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# または venv\Scripts\activate  # Windows

# PyPIからインストール
pip install proxy-meshx

# または最新機能のためにソースからインストール
git clone https://github.com/sheng1111/Proxy-Hunter.git
cd Proxy-Hunter
pip install -e .
```

**注意:** パッケージ名は `proxy-meshx`、インポート時は `proxyhunter`：

```python
from proxyhunter import ProxyHunter, get_proxy
```

#### コマンドライン使用

```bash
# 強化検証による高速プロキシスキャン
proxyhunter scan --threads 30 --limit 100 --anonymous-only

# モダンWebダッシュボードの起動
proxyhunter web --port 8080

# またはPythonモジュールを使用
python -m proxyhunter.web_app
```

#### 1 行プロキシアクセス 🔥

```python
from proxyhunter import get_proxy, get_proxies, get_socks_proxies, get_elite_proxies
import requests

# 作動するプロキシを即座に取得
proxy_url = get_proxy()
response = requests.get('https://httpbin.org/ip',
                       proxies={'http': proxy_url, 'https': proxy_url})
print(f"あなたのIP: {response.json()['origin']}")

# 最小品質スコア要件を持つ高品質USプロキシを取得
us_proxies = get_proxies(count=5, country='US', min_quality=70, max_response_time=2.0)
print(f"{len(us_proxies)}個の高品質USプロキシを発見")

# 高度操作用SOCKSプロキシを取得
socks_proxies = get_socks_proxies(count=3, protocol='socks5')
print(f"SOCKS5プロキシ: {socks_proxies}")

# レッドチーム操作用Elite匿名プロキシを取得
elite_proxies = get_elite_proxies(count=5)
print(f"Eliteプロキシ: {elite_proxies}")

# 品質制約による地理フィルタリング
uk_proxies = get_proxies(count=3, country='UK', min_quality=60, anonymous_only=True)
```

### 🌐 強化 Web ダッシュボード

プロフェッショナル Web インターフェイスの起動：

```bash
python -m proxyhunter.web_app
# http://localhost:5000 にアクセス
```

**新ダッシュボード機能：**

- 📊 **リアルタイム分析** - WebSocket によるライブプロキシ統計
- 📈 **パフォーマンスチャート** - 応答時間トレンドと成功率分析
- 🌍 **地理的分布** - プロキシ位置を示す世界地図
- 🔄 **ワンクリック操作** - 即座のプロキシ更新と検証
- 📋 **スマートコピー** - 様々な形式でのプロキシコピー（curl、requests 等）
- 🌍 **多言語 UI** - 3 言語での完全インターフェイス
- 📱 **モバイル対応** - 全デバイスで完璧動作
- 🎨 **モダンデザイン** - クリーンでプロフェッショナルなインターフェイス

### 🚦 トラフィック監視ダッシュボード

`/traffic`での高度監視アクセス：

```bash
# ダッシュボードを起動し http://localhost:5000/traffic にアクセス
python -m proxyhunter.web_app
```

**トラフィック監視機能：**

- 📈 **リアルタイムリクエスト追跡** - 全プロキシリクエストのライブ監視
- 📊 **成功/失敗分析** - 視覚的成功率分析
- 🌍 **地理的使用統計** - 国/地域別プロキシ使用状況
- ⏱️ **応答時間分析** - 詳細レイテンシー統計
- 📊 **データ転送監視** - プロキシごとの帯域幅使用量追跡
- 🔄 **アクティブセッション管理** - 全アクティブプロキシセッションの監視
- 📝 **詳細リクエストログ** - 完全なリクエスト/レスポンスログ
- 🚦 **ライブ更新** - WebSocket 駆動のリアルタイム更新

---

### 📋 System Requirements

**Python**: 3.8+
**Memory**: 512MB minimum, 2GB+ recommended for heavy workloads
**Storage**: 100MB minimum
**Network**: Stable internet connection for proxy fetching

### 📁 Enhanced Project Structure

```
Proxy-Hunter/
├── proxyhunter/                    # Main package directory
│   ├── __init__.py                # Enhanced quick access functions
│   ├── __main__.py                # Command-line interface
│   ├── core.py                    # Enhanced ProxyHunter with 15+ sources
│   ├── proxy_session.py           # Smart ProxySession with rotation
│   ├── web_app.py                 # Modern Flask dashboard
│   ├── i18n.py                    # Internationalization support
│   ├── i18n/                      # Translation files
│   │   ├── en.json                # English translations
│   │   ├── zh.json                # Traditional Chinese translations
│   │   └── ja.json                # Japanese translations
│   └── public/                    # Enhanced web templates
│       ├── index.html             # Main dashboard with analytics
│       └── traffic.html           # Traffic monitoring interface
├── db/                            # Database directory (auto-created)
├── tests/                         # Comprehensive test suite
├── requirements.txt               # Python dependencies
├── pyproject.toml                 # Python project configuration
├── setup.py                      # Package installation script
├── MANIFEST.in                    # Package manifest
├── LICENSE                        # MIT License
└── README.md                      # This enhanced documentation
```

### 🚀 Performance Benchmarks

- **Fetching Speed**: 15+ sources in parallel, ~500-2000 proxies in 10-30 seconds
- **Validation Speed**: 50 concurrent threads, ~100 proxies validated in 30-60 seconds
- **Success Rate**: Typically 10-30% working proxies depending on source quality
- **Memory Usage**: ~50-200MB depending on proxy count and concurrent operations
- **Database Performance**: SQLite with optimized indexes for sub-second queries

### 🔧 Development & Contribution

```bash
git clone https://github.com/sheng1111/Proxy-Hunter.git
cd Proxy-Hunter
python -m venv venv
source venv/bin/activate  # Linux/Mac or venv\Scripts\activate on Windows
pip install -r requirements.txt
pip install -e .
```

### 📚 API Documentation

Complete API documentation with examples:

- **English & 繁體中文**: [API Documentation](wiki/API-Documentation.md)

<div align="center">

### 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### ⚠️ Disclaimer

This tool is for educational and authorized security testing purposes only. Users are responsible for complying with applicable laws and regulations. The authors are not responsible for any misuse of this software.

**⭐ Star this repository if you find it helpful!**

Made with ❤️ for the security community

</div>
