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

            items.append({
                "title": title,
                "price": price,
                "link":  link,
                "shop":  shop_name,
            })

            if debug:
                print(f"[parser] {shop_name} 商品{i+1}: {title[:40]} | {price}")

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
