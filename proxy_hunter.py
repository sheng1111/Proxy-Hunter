import threading
import requests
import re
from argparse import ArgumentParser, RawTextHelpFormatter

"""
抓取Free Proxy List (https://free-proxy-list.net/) 上的頁面，再利用正規表達法蒐集所有的IP 清單，最後再透過 ipify (https://www.ipify.org/) 做測試
添加 '-o' '--output' 參數，設定預設值為 'proxy.txt'
添加 '-u' '--update' 參數，更新你的 proxy list
添加 '-c' '--check' 參數，檢查指定文件中列出的代理是否有效。此選項需要一個文件名作為參數，該文件應包含欲檢查的代理列表。
"""

description_text = r"""

 ______                              _______                __
|   __ \.----..-----..--.--..--.--. |   |   |.--.--..-----.|  |_ .-----..----.
|    __/|   _||  _  ||_   _||  |  | |       ||  |  ||     ||   _||  -__||   _|
|___|   |__|  |_____||__.__||___  | |___|___||_____||__|__||____||_____||__|
                            |_____|

Get the proxy list from this tool and check the proxy is valid or not.
"""

parser = ArgumentParser(description=description_text,
                        formatter_class=RawTextHelpFormatter)
parser.add_argument(
    '-o', '--output', help='Set the output file name.', default='proxy.txt')
parser.add_argument(
    '-u', '--update', help='Update your proxies listed.')
parser.add_argument(
    '-c', '--check', help="Check if the proxies listed in the specified file are valid. This option requires a filename as an argument, which should contain the list of proxies to be checked.")

args = parser.parse_args()


def get_new_proxy():
    response = requests.get('https://free-proxy-list.net/')
    response.raise_for_status()
    ips = re.findall(r'\d+\.\d+\.\d+\.\d+:\d+', response.text)
    # remove duplicated entries while preserving order
    return list(dict.fromkeys(ips))


def check_proxy(ip, validips):
    try:
        _ = requests.get('https://api.ipify.org?format=json',
                         proxies={'http': ip, 'https': ip}, timeout=5)
        validips.append({'ip': ip})
    except requests.RequestException:
        pass


def save_result(validips, filename, mode):
    with open(filename, mode, encoding='utf-8') as file:
        for proxy in validips:
            proxy = proxy.get('ip', None)
            file.write(str(proxy) + '\n')


def check_proxy_thread(ips, filename, mode):
    validips = []
    threads = []

    for ip in ips:
        t = threading.Thread(target=check_proxy, args=(ip, validips))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    save_result(validips, filename, mode)


def read_ips_from_file(filename):
    try:
        with open(filename, 'r', encoding='utf8') as file:
            ips = [line.strip() for line in file if line.strip()]
        return list(dict.fromkeys(ips))
    except FileNotFoundError:
        print("The file does not exist.")
        return []


def main():
    if args.check:
        ips = read_ips_from_file(args.check)
        check_proxy_thread(ips, args.check, 'w')
    elif args.update:
        ips = read_ips_from_file(args.update)
        check_proxy_thread(ips, args.update, 'w')
    else:
        ips = get_new_proxy()
        check_proxy_thread(ips, args.output, 'w')

    print("All threads have finished to get proxy.")


if __name__ == "__main__":
    main()
