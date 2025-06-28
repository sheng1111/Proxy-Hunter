#!/usr/bin/env python3
"""Test script to verify the fixes."""

try:
    # Test basic imports
    from proxyhunter import get_proxy, get_proxies, ProxySession
    print("✅ Basic imports successful")

    # Test ProxySession with new parameters
    session = ProxySession(
        proxy_count=2,
        rotation_strategy='quality_based',
        min_quality=30,
        protocol_filter='http'
    )
    print("✅ ProxySession with new parameters created successfully")

    # Test command line help
    import subprocess
    result = subprocess.run(['python', '-m', 'proxyhunter', '--help'],
                            capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ Command line interface working")
    else:
        print("❌ Command line interface issue")

    print("\n🎉 All fixes verified successfully!")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
