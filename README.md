# ProxyHunter 🛡️

<div align="center">

![ProxyHunter Logo](https://img.shields.io/badge/ProxyHunter-2.0.1-blue.svg)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/sheng1111/Proxy-Hunter.svg)](https://github.com/sheng1111/Proxy-Hunter/stargazers)

**Professional proxy management with traffic monitoring for red team operations and web scraping**

[English](#english) | [繁體中文](#繁體中文) | [日本語](#日本語)

</div>

---

## English

ProxyHunter is a comprehensive proxy server management solution designed for security professionals, red team operators, and developers who need reliable proxy management capabilities.

### ✨ Features

- 🚀 **Multi-source proxy fetching** from 8+ quality sources
- ⚡ **High-performance validation** with concurrent threading (100+ threads)
- 💾 **SQLite database storage** for persistent data management and analytics
- 🌐 **Modern web dashboard** with real-time monitoring via WebSocket
- 📊 **Interactive charts** powered by Chart.js
- 🔒 **Anonymity detection** with automatic proxy level classification
- 🌍 **Multi-language support** - English, Traditional Chinese, Japanese
- 📤 **Multiple export formats** - TXT, JSON, CSV, JSONL, Burp Suite
- 🛠️ **RESTful API** with comprehensive endpoints
- 🐍 **Python library** for programmatic integration
- 🚦 **Traffic monitoring** with real-time request tracking and analytics
- 🔄 **Automatic proxy rotation** with intelligent session management
- ⚡ **Quick proxy access** - One-line proxy retrieval for immediate use

### 🎯 Red Team & Penetration Testing Features

- **Geolocation filtering** - Select proxies by target country
- **High anonymity proxies** - Elite-level anonymous proxy filtering
- **Fast proxy selection** - Filter by response time for speed
- **Target testing** - Test proxy availability against specific URLs
- **Security tool integration** - Export formats for Burp Suite, curl, Python requests
- **User-Agent rotation** - Built-in browser User-Agent pool
- **Anti-detection mechanisms** - Simulate real browser behavior

### 🕷️ Web Scraping Features

- **Proxy rotation pools** - Automated proxy rotation lists
- **Latency statistics** - Detailed response time analysis
- **Reliability scoring** - Historical success rate based scoring
- **Batch testing** - Bulk validation of proxy lists
- **Real-time monitoring** - Live proxy status via web dashboard

### 🚀 Quick Start

#### Installation

```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or venv\Scripts\activate  # Windows

# Install from PyPI
pip install proxy-hunter

# Or install from source
git clone https://github.com/sheng1111/Proxy-Hunter.git
cd Proxy-Hunter
pip install -e .
```

**Note:** The package name is `proxy-hunter`, but you still import it as `proxyhunter`:

```python
from proxyhunter import ProxyHunter, get_proxy
```

#### Command Line Usage

```bash
# Basic proxy scanning
python -m proxyhunter

# Launch web dashboard
python -m proxyhunter.web_app

# Or if installed as package
proxyhunter scan --limit 50 --threads 20
proxyhunter web --port 8080
```

#### Python Library Usage

```python
from proxyhunter import ProxyHunter

# Basic usage
hunter = ProxyHunter(threads=20, anonymous_only=True, timeout=10)
proxies = hunter.fetch_proxies()
results = hunter.validate_proxies(proxies)
hunter.save_to_database(results)

# Red team specific features
us_proxies = hunter.get_proxies_by_country('US', limit=10)
elite_proxies = hunter.get_elite_proxies(limit=20)
fast_proxies = hunter.get_fast_proxies(max_response_time=2.0, limit=15)

# Test proxy against target
target_url = "https://target-domain.com"
test_result = hunter.test_proxy_with_target('1.2.3.4:8080', target_url)

# Export for security tools
burp_format = hunter.export_proxies_for_tools('burp', 'burp_proxies.txt')
```

#### 🔥 Quick Proxy Access - NEW!

```python
import requests
from proxyhunter import get_proxy, get_proxies, ProxySession

# Get a single working proxy instantly
proxy_url = get_proxy()
response = requests.get('https://httpbin.org/ip',
                       proxies={'http': proxy_url, 'https': proxy_url})
print(f"My IP through proxy: {response.json()['origin']}")

# Get multiple proxies with filters
us_proxies = get_proxies(count=5, country='US', max_response_time=2.0)
for proxy_url in us_proxies:
    try:
        response = requests.get('https://httpbin.org/ip',
                              proxies={'http': proxy_url, 'https': proxy_url},
                              timeout=10)
        print(f"US proxy {proxy_url}: {response.json()['origin']}")
        break
    except:
        continue

# Advanced: ProxySession with automatic rotation and monitoring
session = ProxySession(proxy_count=10, rotation_strategy='performance')
response = session.get('https://httpbin.org/ip')
print(f"Response via rotated proxy: {response.json()}")

# Get traffic statistics
stats = session.get_traffic_stats()
print(f"Session made {stats['total_requests']} requests")
print(f"Success rate: {stats['successful_requests']}/{stats['total_requests']}")
print(f"Average response time: {stats['avg_response_time']}s")
```

### 🎯 Red Team Use Cases

#### Distributed Port Scanning

```python
def distributed_port_scan():
    hunter = ProxyHunter(threads=30, anonymous_only=True)
    us_proxies = hunter.get_proxies_by_country('US', limit=20)

    target_ports = [22, 80, 443, 3389, 5432]
    target_host = "target-server.com"

    for i, port in enumerate(target_ports):
        proxy = us_proxies[i % len(us_proxies)]
        proxy_dict = {
            'http': f'http://{proxy["proxy"]}',
            'https': f'http://{proxy["proxy"]}'
        }
        # Implement scanning logic here
```

#### OSINT Intelligence Gathering

```python
def social_media_osint():
    hunter = ProxyHunter(threads=20, anonymous_only=True)

    # Get proxies from different countries
    all_proxies = []
    for country in ['US', 'UK', 'DE', 'CA']:
        proxies = hunter.get_proxies_by_country(country, limit=5)
        all_proxies.extend(proxies)

    # Rotate through proxies for API requests
    # Implementation here
```

### 🌐 Web Dashboard

Launch the modern web interface:

```bash
python -m proxyhunter.web_app
```

**Dashboard Features:**

- 📊 Real-time proxy statistics with WebSocket updates
- 📈 Interactive charts and graphs
- 🔄 One-click proxy refresh
- 📋 Copy proxies to clipboard
- 🌍 Multi-language interface
- 📱 Responsive design
- 📤 Multi-format export

### 🚦 Traffic Monitoring Dashboard - NEW!

Access the traffic monitoring interface at `/traffic`:

```bash
# Start web dashboard and visit http://localhost:5000/traffic
python -m proxyhunter.web_app
```

**Traffic Monitor Features:**

- 📈 Real-time request tracking and analytics
- 📊 Success/failure rate visualization
- 🌍 Proxy usage statistics by country
- ⏱️ Response time analysis
- 📊 Data transfer monitoring
- 🔄 Active session management
- 📝 Detailed request logs with filtering
- 🚦 WebSocket real-time updates

---

## 繁體中文

ProxyHunter 是一個綜合性的代理伺服器管理解決方案，專為資安專業人員、紅隊操作員和開發者設計。

### ✨ 核心功能

- 🚀 **多源代理獲取** - 從 8+個優質來源獲取代理
- ⚡ **高效能驗證** - 支援 100+併發執行緒
- 💾 **SQLite 資料庫** - 持久化資料管理與統計分析
- 🌐 **現代化儀表板** - WebSocket 即時監控
- 📊 **互動式圖表** - Chart.js 驅動的數據可視化
- 🔒 **匿名性檢測** - 自動檢測代理匿名等級
- 🌍 **多語言支援** - 英文、繁體中文、日文
- 📤 **多種匯出格式** - TXT、JSON、CSV、JSONL、Burp Suite
- 🛠️ **RESTful API** - 完整的 API 介面
- 🐍 **Python 函式庫** - 可編程整合
- 🚦 **流量監控** - 即時請求追蹤與統計分析
- 🔄 **自動代理輪換** - 智能會話管理
- ⚡ **快速代理取得** - 一行代碼即可獲取可用代理

### 🎯 紅隊 & 滲透測試功能

- **地理位置過濾** - 根據目標國家選擇代理
- **高匿名代理** - Elite 級別匿名代理篩選
- **快速代理篩選** - 按回應時間篩選高速代理
- **目標測試功能** - 針對特定 URL 測試代理可用性
- **安全工具整合** - 支援 Burp Suite、curl、Python requests 格式
- **User-Agent 輪換** - 內建多種瀏覽器 User-Agent
- **反偵測機制** - 模擬真實瀏覽器行為

### 🕷️ 爬蟲開發功能

- **代理輪換池** - 自動建立代理輪換列表
- **延遲統計** - 詳細的回應時間分析
- **可靠性評分** - 基於歷史成功率的評分
- **批量測試** - 大量代理列表驗證
- **實時監控** - Web 儀表板即時監控

### 🚀 快速開始

#### 安裝

```bash
# 建立虛擬環境（建議）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 從 PyPI 安裝
pip install proxy-hunter

# 或從原始碼安裝
git clone https://github.com/sheng1111/Proxy-Hunter.git
cd Proxy-Hunter
pip install -e .
```

**注意：** 套件名稱為 `proxy-hunter`，但導入時仍使用 `proxyhunter`：

```python
from proxyhunter import ProxyHunter, get_proxy
```

#### 指令列使用

```bash
# 基本代理掃描
python -m proxyhunter

# 啟動Web儀表板
python -m proxyhunter.web_app

# 或如果已安裝為套件
proxyhunter scan --limit 50 --threads 20
proxyhunter web --port 8080
```

#### Python 函式庫使用

```python
from proxyhunter import ProxyHunter

# 基本使用
hunter = ProxyHunter(threads=20, anonymous_only=True, timeout=10)
proxies = hunter.fetch_proxies()
results = hunter.validate_proxies(proxies)
hunter.save_to_database(results)

# 紅隊專用功能
us_proxies = hunter.get_proxies_by_country('US', limit=10)
elite_proxies = hunter.get_elite_proxies(limit=20)
fast_proxies = hunter.get_fast_proxies(max_response_time=2.0, limit=15)

# 針對目標測試代理
target_url = "https://target-domain.com"
test_result = hunter.test_proxy_with_target('1.2.3.4:8080', target_url)

# 匯出為安全工具格式
burp_format = hunter.export_proxies_for_tools('burp', 'burp_proxies.txt')
```

#### 🔥 快速代理存取 - 新功能！

```python
import requests
from proxyhunter import get_proxy, get_proxies, ProxySession

# 立即獲取一個可用代理
proxy_url = get_proxy()
response = requests.get('https://httpbin.org/ip',
                       proxies={'http': proxy_url, 'https': proxy_url})
print(f"透過代理的IP: {response.json()['origin']}")

# 獲取多個有篩選條件的代理
us_proxies = get_proxies(count=5, country='US', max_response_time=2.0)
for proxy_url in us_proxies:
    try:
        response = requests.get('https://httpbin.org/ip',
                              proxies={'http': proxy_url, 'https': proxy_url},
                              timeout=10)
        print(f"美國代理 {proxy_url}: {response.json()['origin']}")
        break
    except:
        continue

# 進階：ProxySession 自動輪換與監控
session = ProxySession(proxy_count=10, rotation_strategy='performance')
response = session.get('https://httpbin.org/ip')
print(f"透過輪換代理的回應: {response.json()}")

# 獲取流量統計
stats = session.get_traffic_stats()
print(f"會話共發送 {stats['total_requests']} 個請求")
print(f"成功率: {stats['successful_requests']}/{stats['total_requests']}")
print(f"平均回應時間: {stats['avg_response_time']}秒")
```

### 🎯 紅隊演練實戰案例

#### 分散式端口掃描

```python
def distributed_port_scan():
    hunter = ProxyHunter(threads=30, anonymous_only=True)
    us_proxies = hunter.get_proxies_by_country('US', limit=20)

    target_ports = [22, 80, 443, 3389, 5432]
    target_host = "target-server.com"

    for i, port in enumerate(target_ports):
        proxy = us_proxies[i % len(us_proxies)]
        proxy_dict = {
            'http': f'http://{proxy["proxy"]}',
            'https': f'http://{proxy["proxy"]}'
        }
        # 在此實現掃描邏輯
```

#### 社交媒體情報收集

```python
def social_media_osint():
    hunter = ProxyHunter(threads=20, anonymous_only=True)

    # 獲取不同國家的代理
    all_proxies = []
    for country in ['US', 'UK', 'DE', 'CA']:
        proxies = hunter.get_proxies_by_country(country, limit=5)
        all_proxies.extend(proxies)

    # 輪換代理進行API請求
    # 在此實現邏輯
```

### 🌐 Web 儀表板

啟動現代化網頁介面：

```bash
python -m proxyhunter.web_app
```

**儀表板特色：**

- 📊 WebSocket 即時代理統計更新
- 📈 互動式圖表和圖形
- 🔄 一鍵代理刷新
- 📋 複製代理到剪貼板
- 🌍 多語言介面
- 📱 響應式設計
- 📤 多格式匯出

### 🚦 流量監控儀表板 - 新功能！

訪問流量監控介面於 `/traffic`：

```bash
# 啟動網頁儀表板並訪問 http://localhost:5000/traffic
python -m proxyhunter.web_app
```

**流量監控特色：**

- 📈 即時請求追蹤與統計分析
- 📊 成功/失敗率視覺化圖表
- 🌍 按國家分類的代理使用統計
- ⏱️ 回應時間分析
- 📊 數據傳輸監控
- 🔄 活躍會話管理
- 📝 詳細請求日誌與篩選功能
- 🚦 WebSocket 即時更新

---

## 日本語

ProxyHunter は、セキュリティ専門家、レッドチーム運用者、開発者向けの包括的なプロキシサーバー管理ソリューションです。

### ✨ 主な機能

- 🚀 **マルチソースプロキシ取得** - 8 つ以上の高品質ソースから取得
- ⚡ **高性能検証** - 100 以上の並行スレッドサポート
- 💾 **SQLite データベース** - 永続的なデータ管理と分析
- 🌐 **モダンな Web ダッシュボード** - WebSocket によるリアルタイム監視
- 📊 **インタラクティブチャート** - Chart.js によるデータ可視化
- 🔒 **匿名性検出** - プロキシ匿名レベルの自動分類
- 🌍 **多言語サポート** - 英語、繁体字中国語、日本語
- 📤 **複数のエクスポート形式** - TXT、JSON、CSV、JSONL、Burp Suite
- 🛠️ **RESTful API** - 包括的な API エンドポイント
- 🐍 **Python ライブラリ** - プログラム統合用
- 🚦 **トラフィック監視** - リアルタイムリクエスト追跡と分析
- 🔄 **自動プロキシローテーション** - インテリジェントセッション管理
- ⚡ **クイックプロキシアクセス** - 一行でプロキシを即座に取得

### 🎯 レッドチーム & ペネトレーションテスト機能

- **地理位置フィルタリング** - 対象国別プロキシ選択
- **高匿名プロキシ** - エリートレベル匿名プロキシフィルタリング
- **高速プロキシ選択** - 応答時間による高速フィルタリング
- **ターゲットテスト** - 特定 URL に対するプロキシ可用性テスト
- **セキュリティツール統合** - Burp Suite、curl、Python requests 形式
- **User-Agent ローテーション** - 内蔵ブラウザ User-Agent プール
- **検出回避メカニズム** - 実ブラウザ動作のシミュレーション

### 🕷️ Web スクレイピング機能

- **プロキシローテーションプール** - 自動プロキシローテーションリスト
- **レイテンシ統計** - 詳細な応答時間分析
- **信頼性スコアリング** - 履歴成功率ベースのスコアリング
- **バッチテスト** - 大量プロキシリストの検証
- **リアルタイム監視** - Web ダッシュボードによるライブ監視

### 🚀 クイックスタート

#### インストール

```bash
# 仮想環境の作成（推奨）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# または venv\Scripts\activate  # Windows

# PyPIからインストール
pip install proxy-hunter

# またはソースからインストール
git clone https://github.com/sheng1111/Proxy-Hunter.git
cd Proxy-Hunter
pip install -e .
```

**注意：** パッケージ名は `proxy-hunter` ですが、インポート時は `proxyhunter` を使用します：

```python
from proxyhunter import ProxyHunter, get_proxy
```

#### コマンドライン使用

```bash
# 基本的なプロキシスキャン
python -m proxyhunter

# Webダッシュボード起動
python -m proxyhunter.web_app

# またはパッケージとしてインストール済みの場合
proxyhunter scan --limit 50 --threads 20
proxyhunter web --port 8080
```

#### Python ライブラリ使用

```python
from proxyhunter import ProxyHunter

# 基本使用
hunter = ProxyHunter(threads=20, anonymous_only=True, timeout=10)
proxies = hunter.fetch_proxies()
results = hunter.validate_proxies(proxies)
hunter.save_to_database(results)

# レッドチーム専用機能
us_proxies = hunter.get_proxies_by_country('US', limit=10)
elite_proxies = hunter.get_elite_proxies(limit=20)
fast_proxies = hunter.get_fast_proxies(max_response_time=2.0, limit=15)

# ターゲットに対するプロキシテスト
target_url = "https://target-domain.com"
test_result = hunter.test_proxy_with_target('1.2.3.4:8080', target_url)

# セキュリティツール形式でエクスポート
burp_format = hunter.export_proxies_for_tools('burp', 'burp_proxies.txt')
```

#### 🔥 クイックプロキシアクセス - 新機能！

```python
import requests
from proxyhunter import get_proxy, get_proxies, ProxySession

# 即座に使用可能なプロキシを取得
proxy_url = get_proxy()
response = requests.get('https://httpbin.org/ip',
                       proxies={'http': proxy_url, 'https': proxy_url})
print(f"プロキシ経由のIP: {response.json()['origin']}")

# フィルタ条件付きで複数のプロキシを取得
us_proxies = get_proxies(count=5, country='US', max_response_time=2.0)
for proxy_url in us_proxies:
    try:
        response = requests.get('https://httpbin.org/ip',
                              proxies={'http': proxy_url, 'https': proxy_url},
                              timeout=10)
        print(f"USプロキシ {proxy_url}: {response.json()['origin']}")
        break
    except:
        continue

# 高度：ProxySession 自動ローテーションと監視
session = ProxySession(proxy_count=10, rotation_strategy='performance')
response = session.get('https://httpbin.org/ip')
print(f"ローテーションプロキシ経由のレスポンス: {response.json()}")

# トラフィック統計を取得
stats = session.get_traffic_stats()
print(f"セッションで {stats['total_requests']} リクエストを送信")
print(f"成功率: {stats['successful_requests']}/{stats['total_requests']}")
print(f"平均レスポンス時間: {stats['avg_response_time']}秒")
```

### 🎯 レッドチーム実戦事例

#### 分散ポートスキャン

```python
def distributed_port_scan():
    hunter = ProxyHunter(threads=30, anonymous_only=True)
    us_proxies = hunter.get_proxies_by_country('US', limit=20)

    target_ports = [22, 80, 443, 3389, 5432]
    target_host = "target-server.com"

    for i, port in enumerate(target_ports):
        proxy = us_proxies[i % len(us_proxies)]
        proxy_dict = {
            'http': f'http://{proxy["proxy"]}',
            'https': f'http://{proxy["proxy"]}'
        }
        # ここにスキャンロジックを実装
```

#### ソーシャルメディア情報収集

```python
def social_media_osint():
    hunter = ProxyHunter(threads=20, anonymous_only=True)

    # 異なる国のプロキシを取得
    all_proxies = []
    for country in ['US', 'UK', 'DE', 'CA']:
        proxies = hunter.get_proxies_by_country(country, limit=5)
        all_proxies.extend(proxies)

    # APIリクエストのためのプロキシローテーション
    # ここにロジックを実装
```

### 🌐 Web ダッシュボード

モダン Web インターフェースを起動：

```bash
python -m proxyhunter.web_app
```

**ダッシュボード機能：**

- 📊 WebSocket によるリアルタイムプロキシ統計更新
- 📈 インタラクティブチャートとグラフ
- 🔄 ワンクリックプロキシ更新
- 📋 クリップボードへのプロキシコピー
- 🌍 多言語インターフェース
- 📱 レスポンシブデザイン
- 📤 マルチフォーマットエクスポート

### 🚦 トラフィック監視ダッシュボード - 新機能！

`/traffic` でトラフィック監視インターフェースにアクセス：

```bash
# Web ダッシュボードを起動し、http://localhost:5000/traffic にアクセス
python -m proxyhunter.web_app
```

**トラフィック監視機能：**

- 📈 リアルタイムリクエスト追跡と分析
- 📊 成功/失敗率の可視化
- 🌍 国別プロキシ使用統計
- ⏱️ レスポンス時間分析
- 📊 データ転送監視
- 🔄 アクティブセッション管理
- 📝 詳細なリクエストログとフィルタリング
- 🚦 WebSocket リアルタイム更新

---

<div align="center">

### 📋 System Requirements

- **Python**: 3.8+
- **Memory**: 256MB minimum, 1GB+ recommended
- **Storage**: 50MB minimum
- **Network**: Stable internet connection

### 📁 Project Structure

```
Proxy-Hunter/
├── proxyhunter/                    # Main package directory
│   ├── __init__.py                # Package initialization and quick access functions
│   ├── __main__.py                # Command-line interface entry point
│   ├── core.py                    # Core ProxyHunter class and functionality
│   ├── proxy_session.py           # ProxySession class for automatic rotation
│   ├── web_app.py                 # Flask web dashboard application
│   ├── i18n.py                    # Internationalization support
│   ├── i18n/                      # Translation files
│   │   ├── en.json                # English translations
│   │   ├── zh.json                # Traditional Chinese translations
│   │   └── ja.json                # Japanese translations
│   └── public/                    # Web dashboard templates and assets
│       ├── index.html             # Main dashboard page
│       └── traffic.html           # Traffic monitoring page
├── db/                            # Database directory (auto-created)
├── tests/                         # Test files
│   └── test_proxy_hunter.py       # Unit tests
├── requirements.txt               # Python dependencies
├── pyproject.toml                 # Python project configuration
├── setup.py                      # Package installation script
├── MANIFEST.in                    # Package manifest
├── LICENSE                        # MIT License
└── README.md                      # This file
```

### 🔧 Development Setup

```bash
git clone https://github.com/sheng1111/Proxy-Hunter.git
cd Proxy-Hunter
python -m venv venv
source venv/bin/activate  # Linux/Mac or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### ⚠️ Disclaimer

This tool is for educational and authorized security testing purposes only. Users are responsible for complying with applicable laws and regulations.

**⭐ Star this repository if you find it helpful!**

Made with ❤️ for the security community

</div>
