#!/usr/bin/env python3
"""
Cloudflare 优选IP提取器
从 https://api.uouin.com/cloudflare.html 下载并提取优选IP
"""

import json
import sys
from urllib.request import urlopen
from urllib.error import URLError
from bs4 import BeautifulSoup


def download_html(url: str) -> str:
    """下载HTML内容"""
    print(f"正在下载: {url}")
    try:
        with urlopen(url, timeout=30) as response:
            return response.read().decode('utf-8')
    except URLError as e:
        print(f"下载失败: {e}")
        sys.exit(1)


def extract_ips(html: str) -> list:
    """从HTML中提取IP地址"""
    soup = BeautifulSoup(html, 'html.parser')
    results = []

    table = soup.find('table')
    if not table:
        print("未找到表格")
        return results

    tbody = table.find('tbody')
    if not tbody:
        print("未找到tbody")
        return results

    rows = tbody.find_all('tr')
    valid_isps = ['电信', '联通', '移动', '多线', 'IPV6']

    for row in rows:
        cells = row.find_all(['td', 'th'])
        if len(cells) >= 3:
            isp = cells[1].get_text(strip=True)
            ip = cells[2].get_text(strip=True)

            if isp in valid_isps and ip:
                results.append({'isp': isp, 'ip': ip})

    return results


def print_summary(results: list):
    """打印提取摘要"""
    isps = {}
    for item in results:
        isp = item['isp']
        isps[isp] = isps.get(isp, 0) + 1

    print("\n=== 提取结果 ===")
    print(f"总计: {len(results)} 个IP")
    for isp, count in isps.items():
        print(f"  {isp}: {count}个")


def main():
    url = "https://api.uouin.com/cloudflare.html"

    # 下载HTML
    html = download_html(url)

    # 提取IP
    results = extract_ips(html)

    # 打印摘要
    print_summary(results)

    # 输出JSON
    json_output = json.dumps(results, ensure_ascii=False, indent=2)
    print("\n=== JSON输出 ===")
    print(json_output)

    # 保存到文件
    output_file = "cloudflare_ips.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(json_output)
    print(f"\n已保存到: {output_file}")


if __name__ == "__main__":
    main()
