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


def get_newProxy():
    response = requests.get('https://free-proxy-list.net/')
    ips = re.findall(r'\d+\.\d+\.\d+\.\d+:\d+', response.text)
    return ips


def check_proxy(ip, validips):
    try:
        _ = requests.get('https://api.ipify.org?format=json',
                         proxies={'http': ip, 'https': ip}, timeout=5)
        validips.append({'ip': ip})
    except:
        None


def save_result(validips, filename, mode):
    with open(filename, mode, encoding='utf-8') as file:
        for proxy in validips:
            proxy = proxy.get('ip', None)
            file.write(str(proxy) + '\n')


def thread(ips, filename, mode):
    validips = []
    threads = []

    for ip in ips:
        t = threading.Thread(target=check_proxy, args=(ip, validips))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    save_result(validips, filename, mode)


def main():
    if args.check:
        try:
            with open(args.check, 'r', encoding='utf-8') as file:
                ips = [lines.strip() for lines in file.readlines()]
                thread(ips, args.check, 'w')
        except:
            print("The file is not exist.")
    elif args.update:
        try:
            with open(args.update, 'r', encoding='utf-8') as file:
                ips = [lines.strip() for lines in file.readlines()]
                thread(ips, args.update, 'w')
            ips = get_newProxy()
            thread(ips, args.update, 'a')
        except:
            print("The file is not exist.")
    else:
        ips = get_newProxy()
        thread(ips, args.output, 'w')

    print("All threads have finished to get proxy.")


if __name__ == "__main__":
    main()
