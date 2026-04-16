# service/search/taobao_shop/parser.py
# 职责：解析淘宝/天猫店铺搜索结果页 DOM，提取商品信息

import re
from typing import List, Dict


def parse_shop_items(page, shop_name: str, debug: bool = False) -> List[Dict]:
    """
    从当前店铺搜索结果页提取商品列表。

    返回每条商品格式：
    {
        "title":      str,   # 商品名
        "price":      str,   # 原始价格文本，如 "199.00"
        "link":       str,   # 商品详情页 URL
        "shop":       str,   # 店铺名
        "image":      str,   # 商品图片URL
        "free_shipping": bool, # 是否包邮
    }
    """
    items: List[Dict] = []

    # ── 1. 尝试多种商品卡片选择器 ──
    card_locator = None
    for selector in [
        "div[class*='ItemCard']",
        "div[class*='item-card']",
        "div[class*='Card--']",
        "li[class*='item']",
        "div[class*='item']",
        "div[class*='product']",
    ]:
        loc = page.locator(selector)
        if loc.count() > 0:
            card_locator = loc
            if debug:
                print(f"[parser] 命中卡片选择器: {selector}，数量={loc.count()}")
            break

    if card_locator is None:
        if debug:
            print(f"[parser] {shop_name} 未找到商品卡片，跳过")
        return items

    for i in range(card_locator.count()):
        try:
            card = card_locator.nth(i)
            title = _extract_title(card)
            if not title:
                continue

            price = _extract_price(card)
            link = _extract_link(card)
            image = _extract_image(card)
            free_shipping = _extract_free_shipping(card)

            items.append({
                "title": title,
                "price": price,
                "link":  link,
                "shop":  shop_name,
                "image": image,
                "free_shipping": free_shipping,
            })

            if debug:
                print(f"[parser] {shop_name} 商品{i+1}: {title[:40]} | {price} | 图片: {'有' if image else '无'} | 包邮: {free_shipping}")

        except Exception as e:
            if debug:
                print(f"[parser] {shop_name} 商品{i+1} 解析失败: {e}")
            continue

    if debug:
        print(f"[parser] {shop_name} 共解析 {len(items)} 条商品")

    return items


# ── 私有辅助 ──────────────────────────────────────

def _extract_title(card) -> str:
    for sel in [
        "a[title]",
        "div[class*='title'] a",
        "span[class*='title']",
        "a[class*='title']",
        "h3",
    ]:
        loc = card.locator(sel)
        if loc.count() > 0:
            candidate = (
                loc.first.get_attribute("title")
                or loc.first.inner_text()
                or ""
            ).strip()
            if candidate:
                return candidate
    return ""


def _extract_price(card) -> str:
    for sel in [
        "span[class*='price']",
        "div[class*='price']",
        "strong",
        "em",
    ]:
        loc = card.locator(sel)
        if loc.count() > 0:
            text = loc.first.inner_text().strip()
            # 只保留数字与小数点
            cleaned = re.sub(r"[^\d.]", "", text)
            if cleaned:
                return cleaned
    return "0"


def _normalize_url(href: str) -> str:
    if not href:
        return ""
    if href.startswith("//"):
        return f"https:{href}"
    if href.startswith("http"):
        return href
    return f"https://{href.lstrip('/')}"


def _extract_link(card) -> str:
    for sel in [
        "a[href*='item.taobao.com']",
        "a[href*='detail.tmall.com']",
        "a[href]",
    ]:
        loc = card.locator(sel)
        if loc.count() > 0:
            href = loc.first.get_attribute("href") or ""
            if href:
                return _normalize_url(href)
    return ""


def _extract_image(card) -> str:
    """
    提取商品图片URL
    根据用户提供的HTML结构：
    <div class="MainPic--mainPicWrapper--varchHg">
        <img src="http://img.alicdn.com/img/O1CN01n8cPFM1YqQt2QdtpM_!!4611686018427383878-0-item_pic.jpg">
    </div>
    """
    # 尝试多种图片选择器
    for sel in [
        "div[class*='MainPic--mainPicWrapper'] img",
        "div[class*='mainPicWrapper'] img",
        "div[class*='MainPic'] img",
        "img[src*='alicdn.com']",
        "img[src*='item_pic']",
        "img[src]",
    ]:
        loc = card.locator(sel)
        if loc.count() > 0:
            src = loc.first.get_attribute("src") or ""
            if src:
                return _normalize_url(src)
    return ""


def _extract_free_shipping(card) -> bool:
    """
    提取是否包邮信息
    根据用户提供的HTML结构：
    <div class="SalesPoint--subIconWrapper--qJH48u6 " title="包邮 酷动城">
        <div><span style="color: rgb(255, 98, 0);">包邮</span></div>
    </div>
    """
    # 方法1：检查包含"包邮"文本的元素
    for sel in [
        "div[class*='SalesPoint--subIconWrapper']",
        "div[class*='SalesPoint']",
        "div[class*='subIconWrapper']",
        "span[style*='color: rgb(255, 98, 0)']",
    ]:
        loc = card.locator(sel)
        if loc.count() > 0:
            # 检查元素文本是否包含"包邮"
            text = loc.first.inner_text().strip()
            if "包邮" in text:
                return True
    
    # 方法2：检查title属性
    for sel in [
        "div[title*='包邮']",
        "span[title*='包邮']",
    ]:
        loc = card.locator(sel)
        if loc.count() > 0:
            return True
    
    return False
