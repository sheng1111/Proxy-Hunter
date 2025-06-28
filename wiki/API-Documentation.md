# ProxyHunter API Documentation

[English](#english) | [繁體中文](#繁體中文)

---

## English

### Quick Start Functions

#### get_proxy()

Get a single working proxy URL with enhanced filtering options.

```python
from proxyhunter import get_proxy

def get_proxy(prefer_country: str = None,
              max_response_time: float = None,
              min_quality: float = None,
              protocol: str = None,
              force_refresh: bool = False) -> str:
```

**Parameters:**

- `prefer_country`: Preferred country code (e.g., 'US', 'UK', 'DE') (default: None)
- `max_response_time`: Maximum response time in seconds (default: None)
- `min_quality`: Minimum quality score 0-100 (default: None)
- `protocol`: Preferred protocol ('http', 'https', 'socks4', 'socks5') (default: None)
- `force_refresh`: Force refresh of proxy pool (default: False)

**Returns:** Single proxy URL in format 'http://host:port' or 'socks4://host:port'

**Example:**

```python
# Get any working proxy
proxy_url = get_proxy()

# Get high-quality US proxy
us_proxy = get_proxy(prefer_country='US', min_quality=70)

# Get SOCKS5 proxy
socks_proxy = get_proxy(protocol='socks5')
```

#### get_proxies()

Get multiple working proxy URLs with advanced filtering.

```python
def get_proxies(count: int = 10,
                country: str = None,
                max_response_time: float = None,
                min_quality: float = None,
                protocol: str = None,
                anonymous_only: bool = False,
                force_refresh: bool = False) -> list:
```

**Parameters:**

- `count`: Number of proxies to return (default: 10, max: 100)
- `country`: Filter by country code (e.g., 'US', 'UK', 'DE') (default: None)
- `max_response_time`: Maximum response time in seconds (default: None)
- `min_quality`: Minimum quality score 0-100 (default: None)
- `protocol`: Preferred protocol ('http', 'https', 'socks4', 'socks5') (default: None)
- `anonymous_only`: Only return anonymous proxies (default: False)
- `force_refresh`: Force refresh of proxy pool (default: False)

**Returns:** List of proxy dictionaries with detailed information

#### get_socks_proxies()

Get SOCKS proxies for advanced operations.

```python
def get_socks_proxies(count: int = 10, protocol: str = None) -> list:
```

**Parameters:**

- `count`: Number of SOCKS proxies to return (default: 10)
- `protocol`: SOCKS protocol ('socks4' or 'socks5') (default: None)

#### get_elite_proxies()

Get elite anonymity proxies for red team operations.

```python
def get_elite_proxies(count: int = 10) -> list:
```

**Parameters:**

- `count`: Number of elite proxies to return (default: 10)

### ProxyHunter Class

Main class for comprehensive proxy management with enhanced capabilities.

```python
class ProxyHunter:
    def __init__(self,
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
                 enable_socks: bool = True):
```

#### Core Methods

##### fetch_proxies()

Fetch proxies from all available sources.

```python
def fetch_proxies(self, sources: Optional[List[str]] = None) -> List[str]:
```

##### validate_proxies()

Validate a list of proxies with advanced testing.

```python
def validate_proxies(self, proxies: Union[List[str], List[Dict[str, Any]]],
                    show_progress: bool = True) -> List[Dict[str, Any]]:
```

##### save_to_database()

Save validated proxies to SQLite database.

```python
def save_to_database(self, results: List[Dict[str, Any]]) -> None:
```

##### get_working_proxies()

Get working proxies from database.

```python
def get_working_proxies(self, limit: Optional[int] = None,
                       min_response_time: Optional[float] = None) -> List[Dict[str, Any]]:
```

#### Advanced Filtering Methods

##### get_proxies_by_country()

Get proxies filtered by country.

```python
def get_proxies_by_country(self, country: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
```

##### get_proxies_by_quality()

Get proxies filtered by quality score.

```python
def get_proxies_by_quality(self, min_quality_score: float = 50.0,
                          limit: Optional[int] = None) -> List[Dict[str, Any]]:
```

##### get_proxies_by_protocol()

Get proxies filtered by protocol.

```python
def get_proxies_by_protocol(self, protocol: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
```

##### get_proxies_by_geolocation()

Get proxies filtered by geographic location.

```python
def get_proxies_by_geolocation(self, country_code: str = None, region: str = None,
                              city: str = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
```

##### get_socks_proxies()

Get SOCKS proxies.

```python
def get_socks_proxies(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
```

##### get_elite_proxies_enhanced()

Get elite anonymity proxies with enhanced filtering.

```python
def get_elite_proxies_enhanced(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
```

#### Analytics Methods

##### get_proxy_analytics()

Get comprehensive proxy analytics.

```python
def get_proxy_analytics(self) -> Dict[str, Any]:
```

##### search_proxies()

Search proxies by query string.

```python
def search_proxies(self, query: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
```

##### get_statistics()

Get detailed statistics about proxy operations.

```python
def get_statistics(self) -> Dict[str, Any]:
```

#### Utility Methods

##### test_proxy_with_target()

Test a proxy against a specific target URL.

```python
def test_proxy_with_target(self, proxy: str, target_url: str,
                          headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
```

##### export_proxies_for_tools()

Export proxies in formats for various tools (Burp Suite, curl, etc.).

```python
def export_proxies_for_tools(self, format_type: str = 'burp',
                            output_file: Optional[str] = None) -> str:
```

##### cleanup_old_proxies()

Clean up old proxies from database.

```python
def cleanup_old_proxies(self, days: int = 7) -> int:
```

### ProxySession Class

Enhanced requests session with automatic proxy rotation and monitoring.

```python
class ProxySession(requests.Session):
    def __init__(self, proxy_count: int = 10,
                 rotation_strategy: str = 'round_robin',
                 max_retries: int = 3,
                 timeout: int = 10,
                 country_filter: Optional[str] = None,
                 anonymous_only: bool = True,
                 min_quality: float = 0.0,
                 protocol_filter: Optional[str] = None):
```

#### Methods

##### request()

Make HTTP request with automatic proxy rotation.

```python
def request(self, method: str, url: str, **kwargs) -> requests.Response:
```

##### get_traffic_stats()

Get traffic statistics.

```python
def get_traffic_stats(self) -> Dict[str, Any]:
```

##### get_proxy_status()

Get current proxy pool status.

```python
def get_proxy_status(self) -> Dict[str, Any]:
```

##### refresh_proxies()

Refresh the proxy pool.

```python
def refresh_proxies(self):
```

### Web API Endpoints

The ProxyHunter web interface provides RESTful API endpoints:

#### GET /api/proxies

Get list of working proxies with optional filtering.

**Query Parameters:**

- `limit`: Number of proxies to return (default: 50)
- `country`: Filter by country code
- `protocol`: Filter by protocol
- `min_quality`: Minimum quality score

#### GET /api/proxies/stats

Get proxy statistics and analytics.

#### POST /api/proxies/validate

Validate a list of proxies.

**Request Body:**

```json
{
  "proxies": ["proxy1:port1", "proxy2:port2"]
}
```

#### GET /api/proxies/refresh

Refresh proxy pool and get fresh proxies.

#### GET /api/traffic/stats

Get traffic monitoring statistics.

#### GET /api/traffic/logs

Get recent traffic logs.

---

## 繁體中文

### 快速開始函數

#### get_proxy()

取得單一可用代理伺服器 URL，支援進階篩選選項。

```python
從 proxyhunter 匯入 get_proxy

def get_proxy(prefer_country: str = None,
              max_response_time: float = None,
              min_quality: float = None,
              protocol: str = None,
              force_refresh: bool = False) -> str:
```

**參數：**

- `prefer_country`: 偏好的國家代碼（例如：'US', 'UK', 'DE'）（預設：None）
- `max_response_time`: 最大回應時間（秒）（預設：None）
- `min_quality`: 最低品質分數 0-100（預設：None）
- `protocol`: 偏好的協定（'http', 'https', 'socks4', 'socks5'）（預設：None）
- `force_refresh`: 強制重新整理代理伺服器池（預設：False）

**回傳值：** 格式為 'http://host:port' 或 'socks4://host:port' 的單一代理伺服器 URL

**範例：**

```python
# 取得任何可用的代理伺服器
proxy_url = get_proxy()

# 取得高品質的美國代理伺服器
us_proxy = get_proxy(prefer_country='US', min_quality=70)

# 取得 SOCKS5 代理伺服器
socks_proxy = get_proxy(protocol='socks5')
```

#### get_proxies()

取得多個可用代理伺服器 URL，支援進階篩選。

```python
def get_proxies(count: int = 10,
                country: str = None,
                max_response_time: float = None,
                min_quality: float = None,
                protocol: str = None,
                anonymous_only: bool = False,
                force_refresh: bool = False) -> list:
```

**參數：**

- `count`: 要回傳的代理伺服器數量（預設：10，最大：100）
- `country`: 依國家代碼篩選（例如：'US', 'UK', 'DE'）（預設：None）
- `max_response_time`: 最大回應時間（秒）（預設：None）
- `min_quality`: 最低品質分數 0-100（預設：None）
- `protocol`: 偏好的協定（'http', 'https', 'socks4', 'socks5'）（預設：None）
- `anonymous_only`: 僅回傳匿名代理伺服器（預設：False）
- `force_refresh`: 強制重新整理代理伺服器池（預設：False）

**回傳值：** 包含詳細資訊的代理伺服器字典清單

#### get_socks_proxies()

取得用於進階操作的 SOCKS 代理伺服器。

```python
def get_socks_proxies(count: int = 10, protocol: str = None) -> list:
```

**參數：**

- `count`: 要回傳的 SOCKS 代理伺服器數量（預設：10）
- `protocol`: SOCKS 協定（'socks4' 或 'socks5'）（預設：None）

#### get_elite_proxies()

取得用於紅隊操作的菁英匿名代理伺服器。

```python
def get_elite_proxies(count: int = 10) -> list:
```

**參數：**

- `count`: 要回傳的菁英代理伺服器數量（預設：10）

### ProxyHunter 類別

提供增強功能的綜合代理伺服器管理主類別。

```python
class ProxyHunter:
    def __init__(self,
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
                 enable_socks: bool = True):
```

#### 核心方法

##### fetch_proxies()

從所有可用來源獲取代理伺服器。

```python
def fetch_proxies(self, sources: Optional[List[str]] = None) -> List[str]:
```

##### validate_proxies()

使用進階測試驗證代理伺服器清單。

```python
def validate_proxies(self, proxies: Union[List[str], List[Dict[str, Any]]],
                    show_progress: bool = True) -> List[Dict[str, Any]]:
```

##### save_to_database()

將已驗證的代理伺服器儲存到 SQLite 資料庫。

```python
def save_to_database(self, results: List[Dict[str, Any]]) -> None:
```

##### get_working_proxies()

從資料庫取得可用的代理伺服器。

```python
def get_working_proxies(self, limit: Optional[int] = None,
                       min_response_time: Optional[float] = None) -> List[Dict[str, Any]]:
```

#### 進階篩選方法

##### get_proxies_by_country()

依國家篩選代理伺服器。

```python
def get_proxies_by_country(self, country: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
```

##### get_proxies_by_quality()

依品質分數篩選代理伺服器。

```python
def get_proxies_by_quality(self, min_quality_score: float = 50.0,
                          limit: Optional[int] = None) -> List[Dict[str, Any]]:
```

##### get_proxies_by_protocol()

依協定篩選代理伺服器。

```python
def get_proxies_by_protocol(self, protocol: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
```

##### get_proxies_by_geolocation()

依地理位置篩選代理伺服器。

```python
def get_proxies_by_geolocation(self, country_code: str = None, region: str = None,
                              city: str = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
```

##### get_socks_proxies()

取得 SOCKS 代理伺服器。

```python
def get_socks_proxies(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
```

##### get_elite_proxies_enhanced()

使用增強篩選取得菁英匿名代理伺服器。

```python
def get_elite_proxies_enhanced(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
```

#### 分析方法

##### get_proxy_analytics()

取得綜合代理伺服器分析資料。

```python
def get_proxy_analytics(self) -> Dict[str, Any]:
```

##### search_proxies()

依查詢字串搜尋代理伺服器。

```python
def search_proxies(self, query: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
```

##### get_statistics()

取得代理伺服器操作的詳細統計資料。

```python
def get_statistics(self) -> Dict[str, Any]:
```

#### 實用方法

##### test_proxy_with_target()

針對特定目標 URL 測試代理伺服器。

```python
def test_proxy_with_target(self, proxy: str, target_url: str,
                          headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
```

##### export_proxies_for_tools()

將代理伺服器匯出為各種工具的格式（Burp Suite、curl 等）。

```python
def export_proxies_for_tools(self, format_type: str = 'burp',
                            output_file: Optional[str] = None) -> str:
```

##### cleanup_old_proxies()

從資料庫清理舊的代理伺服器。

```python
def cleanup_old_proxies(self, days: int = 7) -> int:
```

### ProxySession 類別

具有自動代理伺服器輪換和監控功能的增強 requests 會話。

```python
class ProxySession(requests.Session):
    def __init__(self, proxy_count: int = 10,
                 rotation_strategy: str = 'round_robin',
                 max_retries: int = 3,
                 timeout: int = 10,
                 country_filter: Optional[str] = None,
                 anonymous_only: bool = True,
                 min_quality: float = 0.0,
                 protocol_filter: Optional[str] = None):
```

#### 方法

##### request()

使用自動代理伺服器輪換進行 HTTP 請求。

```python
def request(self, method: str, url: str, **kwargs) -> requests.Response:
```

##### get_traffic_stats()

取得流量統計資料。

```python
def get_traffic_stats(self) -> Dict[str, Any]:
```

##### get_proxy_status()

取得目前代理伺服器池狀態。

```python
def get_proxy_status(self) -> Dict[str, Any]:
```

##### refresh_proxies()

重新整理代理伺服器池。

```python
def refresh_proxies(self):
```

### Web API 端點

ProxyHunter 網頁介面提供 RESTful API 端點：

#### GET /api/proxies

取得可用代理伺服器清單，支援選擇性篩選。

**查詢參數：**

- `limit`: 要回傳的代理伺服器數量（預設：50）
- `country`: 依國家代碼篩選
- `protocol`: 依協定篩選
- `min_quality`: 最低品質分數

#### GET /api/proxies/stats

取得代理伺服器統計資料和分析。

#### POST /api/proxies/validate

驗證代理伺服器清單。

**請求主體：**

```json
{
  "proxies": ["proxy1:port1", "proxy2:port2"]
}
```

#### GET /api/proxies/refresh

重新整理代理伺服器池並取得新的代理伺服器。

#### GET /api/traffic/stats

取得流量監控統計資料。

#### GET /api/traffic/logs

取得最近的流量日誌。

---

## License | 授權

This API documentation is part of ProxyHunter, which is licensed under the MIT License.

本 API 文檔是 ProxyHunter 的一部分，根據 MIT 授權條款授權。
