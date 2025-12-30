# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Cloudflare IP extractor that fetches optimized Cloudflare CDN node IPs from https://api.uouin.com/cloudflare.html. The tool uses a headless browser (Pyppeteer) to handle dynamic content loading and extracts IP addresses along with ISP information and timestamps.

## Key Architecture

### Core Components

**cf_ip_extractor.py** - Main script with async/await pattern:
- `download_html()` - Async function that uses Pyppeteer to fetch pages with dynamic content
- `extract_ips()` - Parses HTML tables to extract ISP, IP, and timestamp data
- `main()` - Orchestrates the extraction pipeline and outputs JSON

### Browser Automation Strategy

The script uses **Pyppeteer** (Python port of Puppeteer) instead of simple HTTP requests because:
- Target page uses dynamic content loading
- Anti-bot detection requires realistic browser behavior
- Must verify successful page load by checking for specific text

**Key anti-detection features in download_html():**
- Automatically detects local Chrome/Edge browser paths
- Hides webdriver properties (`navigator.webdriver`)
- Sets realistic user agent and language preferences
- Waits for network idle before scraping

### Data Structure

Input HTML table structure (column indices):
```
[0]序号 [1]线路 [2]优选IP [3]丢包 [4]延迟 [5]速度 [6]带宽 [7]Colo [8]时间
```

Output JSON format:
```json
{
  "update_time": "2025-12-30 15:30:45",
  "total_count": 150,
  "data": [
    {
      "isp": "电信",
      "ip": "162.159.27.211",
      "time": "2025/12/30 10:02:27"
    }
  ]
}
```

## Running the Tool

### Installation
```bash
pip install -r requirements.txt
```

### Execute
```bash
python cf_ip_extractor.py
```

The script will:
1. Launch headless browser
2. Navigate to target URL and wait for dynamic content
3. Verify successful load by checking for disclaimer text
4. Extract IPs from HTML table (filters for valid ISPs: 电信, 联通, 移动, 多线, IPV6)
5. Save results to `cloudflare_ips.json`

## Development Notes

### Browser Path Detection
The `possible_paths` list in `download_html()` checks multiple Chrome/Edge installation locations. If modifying for different OS, update paths accordingly.

### Windows Event Loop Policy
The script sets `asyncio.WindowsSelectorEventLoopPolicy()` on Windows to avoid event loop issues with Pyppeteer. Do not remove this.

### Success Validation
The `SUCCESS_TEXT` constant contains Chinese disclaimer text that must be present in the loaded page to verify successful data loading. If the target website changes this text, updates will be needed.

### ISP Filtering
Only rows where ISP column matches one of the valid ISPs (电信, 联通, 移动, 多线, IPV6) are extracted. Modify `valid_isps` list to change filtering behavior.

### Table Column Dependencies
The extraction logic expects at least 9 columns in the table. Column indices are hardcoded:
- Column 1: ISP type
- Column 2: IP address
- Column 8: Timestamp

If the website changes table structure, these indices must be updated in `extract_ips()`.
