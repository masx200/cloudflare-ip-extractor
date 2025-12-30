#!/usr/bin/env python3
"""
Cloudflare 优选IP提取器
从 https://api.uouin.com/cloudflare.html 下载并提取优选IP
使用无头浏览器(Pyppeteer)抓取数据
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from pyppeteer import launch
from bs4 import BeautifulSoup


SUCCESS_TEXT = 'CloudFlare优选IP仅对CDN节点IP进行优选，不提供任何CDN服务，严禁用户用于从事任何违法犯罪行为或帮助网络信息犯罪行为'


async def download_html(url: str) -> str:
    """使用无头浏览器下载HTML内容"""
    print(f"正在使用无头浏览器访问: {url}")

    browser = None
    try:
        # 查找本地 Chrome 路径
        possible_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            r"C:\Users\{}\AppData\Local\Google\Chrome\Application\chrome.exe".format(os.getenv('USERNAME', '')),
            os.path.join(os.getenv('LOCALAPPDATA', ''), r"Google\Chrome\Application\chrome.exe"),
            # 尝试 Edge 浏览器作为备选
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
        ]

        executable_path = None
        for path in possible_paths:
            if os.path.exists(path):
                executable_path = path
                break

        if executable_path:
            print(f"✓ 检测到本地浏览器: {executable_path}")
        else:
            print("⚠ 未检测到 Chrome/Edge，将尝试使用 Pyppeteer 默认下载（可能会失败）")
            print("提示: 如果报错，请安装 Google Chrome 或 Microsoft Edge")

        # 启动无头浏览器
        browser = await launch(
            headless=True,
            executablePath=executable_path,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        page = await browser.newPage()

        # 设置用户代理，模拟真实浏览器
        await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

        # 隐藏webdriver特征
        await page.evaluateOnNewDocument('''() => {
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN', 'zh', 'en']});
        }''')

        # 访问目标页面，等待网络空闲
        await page.goto(url, {
            'waitUntil': 'networkidle2',
            'timeout': 60000
        })

        # 等待页面完全加载
        await asyncio.sleep(3)

        # 检查是否成功加载
        page_content = await page.content()
        if SUCCESS_TEXT in page_content:
            print("✓ 数据加载成功!")
        else:
            print("⚠ 警告: 未检测到成功加载标识文本")

        return page_content

    except Exception as e:
        print(f"浏览器访问失败: {e}")
        sys.exit(1)
    finally:
        if browser:
            await browser.close()


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
        # 表格结构: #, 线路, 优选IP, 丢包, 延迟, 速度, 带宽, Colo, 时间
        if len(cells) >= 9:
            isp = cells[1].get_text(strip=True)
            ip = cells[2].get_text(strip=True)
            time = cells[8].get_text(strip=True)  # 最后一列是时间

            if isp in valid_isps and ip:
                results.append({
                    'isp': isp,
                    'ip': ip,
                    'time': time
                })

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


async def main():
    url = "https://api.uouin.com/cloudflare.html"

    # 下载HTML
    html = await download_html(url)

    # 提取IP
    results = extract_ips(html)

    # 打印摘要
    print_summary(results)

    # 添加时间戳
    output_data = {
        "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_count": len(results),
        "data": results
    }

    # 输出JSON
    json_output = json.dumps(output_data, ensure_ascii=False, indent=2)
    print("\n=== JSON输出 ===")
    print(json_output)

    # 保存到文件
    output_file = "cloudflare_ips.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(json_output)
    print(f"\n已保存到: {output_file}")


if __name__ == "__main__":
    # Windows系统下解决 asyncio 事件循环策略问题
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(main())
