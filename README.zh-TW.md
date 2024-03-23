# Proxy Hunter

## 概覽

Proxy Hunter 是一款強大的 Python 工具，專為從[免費代理列表](https://free-proxy-list.net/)抓取和測試免費代理的可用性而設計。它使用正則表達式來收集 IP 地址列表並利用[ipify](https://www.ipify.org/)測試它們的有效性。對於需要快速且可靠地獲得免費且可工作代理服務器的開發者和安全分析師來說，它是一個必不可少的工具。

## 特性

- **抓取免費代理**：自動從免費代理列表抓取免費代理服務器。
- **代理驗證**：通過嘗試使用代理連接到互聯網來檢查每個代理服務器的有效性。
- **輸出自定義**：允許用戶指定有效代理列表的輸出文件。
- **基於文件的代理檢查**：支持檢查用戶指定文件中列出的代理的有效性。

## 先決條件

開始之前，請確保您已滿足以下要求：

- 您的機器上安裝了 Python 3.x
- 安裝了`requests`庫

## 安裝

### 克隆存儲庫或下載源代碼：

```bash
git clone https://your-repository-link.git
```

### 安裝所需的 Python 包

```bash
pip install -r requirements.txt
```

## 使用方式

### 獲取新 Proxy

運行腳本而不帶任何參數以抓取新代理並將它們保存到 proxy.txt（默認文件名）：

```bash
python proxy_hunter.py
```

### 自定義輸出文件名

使用 `-o` 或 `--output` 選項指定代理的不同輸出文件：

```bash
python proxy_hunter.py -o existing_proxies.txt
```

### 幫助

要獲取有關命令行選項的更多資訊，請使用 `-h` 或 `--help`選項：

```bash
python proxy_hunter.py -h
```

## License

根據 MIT 許可分發。有關更多資訊，請查看 LICENSE。
