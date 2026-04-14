# service/search/hpoi/fetcher.py
"""
HPOI服务 - 数据获取模块
"""

from playwright.sync_api import sync_playwright
import time
import re
from typing import List, Dict, Optional
from urllib.parse import quote_plus, urljoin

import requests
from bs4 import BeautifulSoup

from .config import HPOI_URL, HPOI_SEARCH_URL, HPOI_SEARCH_QUERY_PARAM, PRODUCT_ITEM_SELECTOR, TITLE_SELECTOR, PRICE_SELECTOR, DATE_SELECTOR, LINK_SELECTOR, SOURCE_SELECTOR
from .utils import parse_price


def _build_hpoi_search_urls(keyword: str) -> List[str]:
    query = quote_plus(keyword)
    urls = [f"{HPOI_SEARCH_URL}?{HPOI_SEARCH_QUERY_PARAM}={query}"]
    if HPOI_SEARCH_QUERY_PARAM != 'q':
        urls.append(f"{HPOI_SEARCH_URL}?q={query}")
    return urls


def fetch_hpoi_items(keyword: str, max_items: int, debug: bool = False, 
                     context=None) -> List[Dict]:
    """
    从HPOI获取搜索结果商品列表
    """
    
    items = []
    
    try:
        # 创建浏览器上下文
        if context is None:
            playwright = sync_playwright().start()
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context()
        else:
            # 使用已有的context
            pass
        
        page = context.new_page()
        
        # 设置超时
        page.set_default_timeout(30000)
        
        try:
            # 打开HPOI搜索页面
            if debug:
                print(f"[fetch_hpoi_items] 打开HPOI搜索页...")
            
            # HPOI搜索URL格式（支持 keyword + 兼容 q）
            urls = _build_hpoi_search_urls(keyword)
            search_url = urls[0]
            if debug:
                print(f"[fetch_hpoi_items] 尝试搜索URL: {search_url}")

            try:
                page.goto(search_url, wait_until="networkidle")
            except Exception as e:
                if debug:
                    print(f"[fetch_hpoi_items] 连接HPOI失败（首选URL），尝试临时方案: {e}")
                # fallback 方案：换成 http 或者使用User-Agent模拟浏览器
                alt_url = search_url.replace("https://", "http://")
                page.set_extra_http_headers({
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
                })
                page.goto(alt_url, wait_until="networkidle")

            time.sleep(2)  # 等待页面完全加载

            # products 提取
            product_elements = page.query_selector_all(PRODUCT_ITEM_SELECTOR)
            if not product_elements and len(urls) > 1:
                # 兼容旧参数 q
                if debug:
                    print(f"[fetch_hpoi_items] 0个结果，尝试旧参数 URL: {urls[1]}")
                page.goto(urls[1], wait_until="networkidle")
                time.sleep(2)
                product_elements = page.query_selector_all(PRODUCT_ITEM_SELECTOR)

            # 解析每个商品
            for idx, elem in enumerate(product_elements[:max_items]):
                try:
                    item = parse_hpoi_item(elem, page, debug)
                    if item:
                        items.append(item)
                except Exception as e:
                    if debug:
                        print(f"[fetch_hpoi_items] 商品 {idx+1} 解析失败: {e}")
                    continue
            
            if debug:
                print(f"[fetch_hpoi_items] 共解析 {len(items)} 件商品")
        
        finally:
            page.close()
    
    except Exception as e:
        if debug:
            print(f"[fetch_hpoi_items] 错误: {e}")
    
    if not items:
        # playwright 失败时备选方案：requests+bs4
        if debug:
            print("[fetch_hpoi_items] Playwright 无结果，尝试 requests 备选方案")
        items = _fetch_hpoi_items_requests(keyword, max_items, debug)

    return items


def _fetch_hpoi_items_requests(keyword: str, max_items: int, debug: bool) -> List[Dict]:
    """
    requests+BeautifulSoup 备选抓取
    """
    items = []
    urls = _build_hpoi_search_urls(keyword)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }

    for url in urls:
        if debug:
            print(f"[_fetch_hpoi_items_requests] 尝试搜索URL: {url}")

        try:
            resp = requests.get(url, headers=headers, timeout=15)
            resp.raise_for_status()
            html = resp.text
            soup = BeautifulSoup(html, 'html.parser')

            elements = soup.select(PRODUCT_ITEM_SELECTOR)
            if debug:
                print(f"[_fetch_hpoi_items_requests] 解析到 {len(elements)} 个元素")

            if not elements:
                continue

            for idx, elem in enumerate(elements[:max_items]):
                title_tag = elem.select_one(TITLE_SELECTOR)
                title = title_tag.get_text(strip=True) if title_tag else ''

                price_tag = elem.select_one(PRICE_SELECTOR)
                price_text = price_tag.get_text(strip=True) if price_tag else '0'
                price = parse_price(price_text)

                date_tag = elem.select_one(DATE_SELECTOR)
                release_date = date_tag.get_text(strip=True) if date_tag else '未知'

                link_tag = elem.select_one(LINK_SELECTOR)
                link = link_tag['href'] if link_tag and link_tag.has_attr('href') else ''

                source_tag = elem.select_one(SOURCE_SELECTOR)
                source = source_tag.get_text(strip=True) if source_tag else 'HPOI'

                if not title:
                    continue

                items.append({
                    'title': title,
                    'price': price,
                    'release_date': release_date,
                    'link': link,
                    'source': source,
                    'raw_price_text': price_text
                })

            if debug:
                print(f"[_fetch_hpoi_items_requests] 共解析 {len(items)} 件商品")

            if items:
                break

        except Exception as e:
            if debug:
                print(f"[_fetch_hpoi_items_requests] 异常: {e}")
            continue

    return items


def _extract_price_from_text(text: str) -> Optional[float]:
    if not text:
        return None
    # 支持 ¥, ￥, 日元, JPY, 元 等格式
    matches = re.findall(r'([\d,\.]+)\s*(?:日元|JPY|円|元|¥|￥)', text, re.I)
    for m in matches:
        p = parse_price(m)
        if p > 0:
            return p
    return None


def _extract_release_date_from_text(text: str) -> Optional[str]:
    if not text:
        return None
    patterns = [
        r'\d{4}年\d{1,2}月\d{1,2}日',
        r'\d{4}年\d{1,2}月',
        r'\d{1,2}月\d{1,2}日',
        r'\d{4}-\d{1,2}-\d{1,2}',
        r'\d{4}/\d{1,2}/\d{1,2}'
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            return m.group(0)
    return None


def parse_hpoi_item(element, page, debug: bool = False) -> Optional[Dict]:
    """
    解析单个HPOI商品元素
    """
    
    try:
        # 提取标题
        title_elem = element.query_selector(TITLE_SELECTOR)
        title = title_elem.text_content().strip() if title_elem else ""
        
        # 提取价格
        price_elem = element.query_selector(PRICE_SELECTOR)
        price_str = price_elem.text_content().strip() if price_elem else ""
        price = parse_price(price_str) if price_str else 0.0

        # 如果 list 页面没有价格，则尝试从元素文本或详情页抓取
        if price <= 0:
            price_from_text = _extract_price_from_text(element.inner_text())
            if price_from_text:
                price = price_from_text
                price_str = str(price_from_text)

        # 提取发售日期
        date_elem = element.query_selector(DATE_SELECTOR)
        release_date = date_elem.text_content().strip() if date_elem else ""
        if not release_date:
            release_date = _extract_release_date_from_text(element.inner_text()) or "未知"

        # 提取商品链接
        link_elem = element.query_selector(LINK_SELECTOR)
        link = link_elem.get_attribute("href") if link_elem else ""

        # 如果仍没有价格，且有详情链接，尝试从详情页抓取
        if price <= 0 and link:
            try:
                detail_url = urljoin(HPOI_URL, link)
                resp = requests.get(detail_url, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
                }, timeout=15)
                resp.raise_for_status()
                price_detail = _extract_price_from_text(resp.text)
                if price_detail:
                    price = price_detail
                    price_str = str(price_detail)
                    if debug:
                        print(f"[parse_hpoi_item] 详情页价格回退: {price_str} (from {detail_url})")

                # 详情页也提取发售日期回退
                if release_date in ("未知", ""):
                    date_detail = _extract_release_date_from_text(resp.text)
                    if date_detail:
                        release_date = date_detail
                        if debug:
                            print(f"[parse_hpoi_item] 详情页发售日期回退: {release_date} (from {detail_url})")
            except Exception as e:
                if debug:
                    print(f"[parse_hpoi_item] 详情页价格抓取失败: {e}")

        # 提取来源/商家信息
        source_elem = element.query_selector(SOURCE_SELECTOR)
        source = source_elem.text_content().strip() if source_elem else "HPOI"
        
        if not title:
            return None
        
        item = {
            'title': title,
            'price': price,
            'release_date': release_date,
            'link': link,
            'source': source,
            'raw_price_text': price_str
        }
        
        if debug:
            print(f"  ✓ 解析商品: {title[:40]}... | ¥{price} | {release_date}")
        
        return item
    
    except Exception as e:
        if debug:
            print(f"[parse_hpoi_item] 解析异常: {e}")
        return None
