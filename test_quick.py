#!/usr/bin/env python3
"""Quick test script for ProxyHunter."""

import time
from pathlib import Path
from proxyhunter.core import ProxyHunter

def main():
    print("🚀 ProxyHunter 快速測試")
    print("=" * 50)
    
    # 創建 ProxyHunter 實例
    db_path = Path('db/proxy_dashboard.db')
    hunter = ProxyHunter(threads=3, timeout=8, db_path=str(db_path))
    
    # 1. 添加一些測試數據
    print("📊 添加測試數據...")
    test_data = [
        {
            'proxy': '127.0.0.1:8080', 
            'host': '127.0.0.1', 
            'port': 8080, 
            'status': 'ok', 
            'response_time': 0.123, 
            'data_size': 1024
        },
        {
            'proxy': '192.168.1.100:3128', 
            'host': '192.168.1.100', 
            'port': 3128, 
            'status': 'ok', 
            'response_time': 0.456, 
            'data_size': 2048
        },
        {
            'proxy': '8.8.8.8:80', 
            'host': '8.8.8.8', 
            'port': 80, 
            'status': 'ok', 
            'response_time': 0.789, 
            'data_size': 512
        },
        {
            'proxy': '1.1.1.1:8080', 
            'host': '1.1.1.1', 
            'port': 8080, 
            'status': 'failed', 
            'response_time': None, 
            'data_size': 0
        },
        {
            'proxy': '10.0.0.1:3128', 
            'host': '10.0.0.1', 
            'port': 3128, 
            'status': 'failed', 
            'response_time': None, 
            'data_size': 0
        }
    ]
    
    hunter.save_to_database(test_data)
    print(f"✅ 已添加 {len(test_data)} 筆測試數據")
    
    # 2. 獲取一些真實代理進行測試
    print("\n🌐 獲取真實代理...")
    try:
        proxies = hunter.fetch_proxies()
        print(f"📥 獲取到 {len(proxies)} 個代理")
        
        if proxies:
            # 只測試前5個代理
            test_proxies = proxies[:5]
            print(f"🔍 測試前 {len(test_proxies)} 個代理...")
            
            # 顯示要測試的代理
            for i, proxy in enumerate(test_proxies, 1):
                print(f"  {i}. {proxy}")
            
            # 驗證代理
            print("\n⏳ 開始驗證...")
            results = hunter.validate_proxies(test_proxies, show_progress=True)
            
            # 保存結果
            if results:
                hunter.save_to_database(results)
                print(f"💾 已保存 {len(results)} 個驗證結果")
                
                # 顯示結果摘要
                success_count = sum(1 for r in results if r['status'] == 'ok')
                print(f"✅ 成功: {success_count}/{len(results)}")
            
    except Exception as e:
        print(f"❌ 獲取代理時出錯: {e}")
    
    # 3. 顯示統計信息
    print("\n📈 資料庫統計:")
    try:
        stats = hunter.get_statistics()
        print(f"  總代理數: {stats.get('total_proxies', 0)}")
        print(f"  工作代理: {stats.get('working_proxies', 0)}")
        print(f"  失敗代理: {stats.get('failed_proxies', 0)}")
        
        response_stats = stats.get('response_time_stats', {})
        avg_time = response_stats.get('avg_response_time', 0)
        if avg_time:
            print(f"  平均回應時間: {avg_time:.3f}s")
        
    except Exception as e:
        print(f"❌ 獲取統計時出錯: {e}")
    
    # 4. 清理
    hunter.close()
    
    print("\n🎉 測試完成！")
    print("現在可以啟動 web 應用程式:")
    print("  python -m proxyhunter.web_app")
    print("  然後訪問: http://localhost:5000")

if __name__ == "__main__":
    main() 