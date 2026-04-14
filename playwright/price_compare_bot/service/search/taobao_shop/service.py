import re
import random
from typing import Dict, List, Optional
from urllib.parse import quote_plus, urlencode, urlparse, urlunparse

from config.context import BrowserManager
from config.settings import TAOBAO_URL
from service.login_service import LoginService



REQUEST_RETRY = 4
REQUEST_TIMEOUT_MS = 45000
SHORT_DELAY_RANGE_MS = (1800, 3600)
LONG_DELAY_RANGE_MS = (6000, 12000)


def _normalize_text(text: str) -> str:
    return "".join(str(text).lower().split())


def _is_target_shop(shop_name: str, target_shops: List[str]) -> bool:
    if not shop_name:
        return False

    shop_n = _normalize_text(shop_name)
    for target in target_shops:
        target_n = _normalize_text(target)
        if target_n in shop_n or shop_n in target_n:
            return True
    return False


def _normalize_shop_url(url: str) -> str:
    if not url:
        return ""
    if url.startswith("//"):
        return f"https:{url}"
    if url.startswith("http"):
        return url
    return f"https://{url.lstrip('/')}"


def _build_shop_search_url(shop_url: str, keyword: str, page_index: int = 1) -> str:
    normalized_url = _normalize_shop_url(shop_url)
    parsed = urlparse(normalized_url)
    base_path = parsed.path.rstrip("/")
    search_path = f"{base_path}/search.htm" if base_path else "/search.htm"

    query = {"search": "y", "keyword": keyword}
    if page_index > 1:
        query["pageNo"] = str(page_index)

    return urlunparse((parsed.scheme or "https", parsed.netloc, search_path, "", urlencode(query), ""))


def _human_wait(page, delay_range_ms, reason: str = "", debug: bool = False) -> None:
    if not page or page.is_closed():
        return

    delay = random.randint(*delay_range_ms)
    if debug:
        message = f"[_human_wait] 等待 {delay}ms"
        if reason:
            message = f"{message}，原因: {reason}"
        print(message)
    try:
        page.wait_for_timeout(delay)
    except Exception:
        # 页面已关闭时无需再等待。
        return


def _is_target_closed_error(error: Exception) -> bool:
    error_text = str(error).lower()
    return "target page, context or browser has been closed" in error_text


def _is_anti_bot_page(page) -> bool:
    try:
        title = (page.title() or "").lower()
        if any(flag in title for flag in ["验证", "验证码", "异常流量", "访问受限", "安全验证"]):
            return True
    except Exception:
        pass

    try:
        body = (page.content() or "").lower()
        anti_bot_markers = [
            "验证码",
            "滑动",
            "异常流量",
            "访问受限",
            "captcha",
            "请完成验证",
            "拖动滑块",
        ]
        return any(marker in body for marker in anti_bot_markers)
    except Exception:
        return False


def _safe_goto(page, url: str, debug: bool = False, retry: int = REQUEST_RETRY) -> bool:
    for attempt in range(1, retry + 1):
        if not page or page.is_closed():
            if debug:
                print(f"[_safe_goto] 页面已关闭，停止访问: {url}")
            return False

        try:
            page.goto(url, wait_until="domcontentloaded", timeout=REQUEST_TIMEOUT_MS)
            try:
                page.wait_for_load_state("networkidle", timeout=8000)
            except Exception as e:
                if _is_target_closed_error(e):
                    if debug:
                        print(f"[_safe_goto] networkidle 阶段页面关闭: {url}")
                    return False
                if debug:
                    print(f"[_safe_goto] networkidle 超时，继续解析页面: {url}")

            if _is_anti_bot_page(page):
                if debug:
                    print(f"[_safe_goto] 命中反爬页面，第{attempt}次: {url}")
                _human_wait(page, LONG_DELAY_RANGE_MS, reason="反爬命中，长退避", debug=debug)
                continue

            _human_wait(page, SHORT_DELAY_RANGE_MS, reason="页面稳定等待", debug=debug)
            return True
        except Exception as e:
            if debug:
                print(f"[_safe_goto] 第{attempt}次访问失败: {e}")
            if _is_target_closed_error(e):
                return False
            _human_wait(page, LONG_DELAY_RANGE_MS, reason="访问失败退避", debug=debug)

    return False


def _extract_shop_url_from_search(page, shop_name: str, debug: bool = False) -> Optional[str]:
    shop_search_url = f"https://shopsearch.taobao.com/search?app=shopsearch&q={quote_plus(shop_name)}"

    if debug:
        print(f"[_extract_shop_url_from_search] 搜索店铺: {shop_name}")

    if not _safe_goto(page, shop_search_url, debug=debug):
        if debug:
            print(f"[_extract_shop_url_from_search] 打开店铺搜索页失败: {shop_name}")
        return None

    anchors = page.locator("a[href]")
    count = min(anchors.count(), 200)
    normalized_target = _normalize_text(shop_name)
    fallback_candidates: List[str] = []

    for index in range(count):
        try:
            anchor = anchors.nth(index)
            href = anchor.get_attribute("href") or ""
            text = (anchor.inner_text() or "").strip()
            normalized_text = _normalize_text(text)

            if not href or not normalized_text:
                continue

            if normalized_target in normalized_text or normalized_text in normalized_target:
                if any(domain in href for domain in ["taobao.com", "tmall.com"]):
                    shop_url = _normalize_shop_url(href)
                    if debug:
                        print(f"[_extract_shop_url_from_search] 命中店铺URL: {shop_name} -> {shop_url}")
                    return shop_url

            # 文本匹配失败时，记录候选店铺链接作为兜底。
            normalized_href = _normalize_shop_url(href)
            parsed_href = urlparse(normalized_href)
            host = (parsed_href.netloc or "").lower()
            if (
                host.endswith("tmall.com")
                or host.endswith("shop.taobao.com")
                or re.search(r"shop\d+\.taobao\.com", host)
            ):
                fallback_candidates.append(normalized_href)
        except Exception:
            continue

    for candidate in fallback_candidates:
        if candidate:
            if debug:
                print(f"[_extract_shop_url_from_search] 使用候选店铺URL: {shop_name} -> {candidate}")
            return candidate

    if debug:
        print(f"[_extract_shop_url_from_search] 未解析到店铺URL: {shop_name}")
    return None


def _extract_items_from_shop_page(page, shop_name: str, debug: bool = False) -> List[Dict]:
    items: List[Dict] = []

    card_selectors = [
        "div.item",
        "li.item",
        "div[class*='item']",
        "div[class*='product']",
    ]
    title_selectors = [
        "a[title]",
        "div[class*='title'] a",
        "a[class*='title']",
    ]
    price_selectors = [
        "strong",
        "em",
        "span[class*='price']",
        "div[class*='price']",
    ]
    link_selectors = [
        "a[href*='item.taobao.com']",
        "a[href*='detail.tmall.com']",
        "a[href]",
    ]

    cards = []
    for selector in card_selectors:
        locator = page.locator(selector)
        count = locator.count()
        if count > 0:
            cards = [locator.nth(i) for i in range(count)]
            if debug:
                print(f"[_extract_items_from_shop_page] 命中店铺商品卡片选择器 {selector}，数量={count}")
            break

    if not cards:
        if debug:
            print(f"[_extract_items_from_shop_page] 店铺 {shop_name} 未找到商品卡片")
        return items

    for index, card in enumerate(cards, 1):
        try:
            title = ""
            for selector in title_selectors:
                locator = card.locator(selector)
                if locator.count() > 0:
                    candidate = locator.first.get_attribute("title") or locator.first.inner_text().strip()
                    if candidate:
                        title = candidate.strip()
                        break

            if not title:
                continue

            price_text = ""
            for selector in price_selectors:
                locator = card.locator(selector)
                if locator.count() > 0:
                    candidate = locator.first.inner_text().strip()
                    if candidate:
                        price_text = candidate
                        break

            link = ""
            for selector in link_selectors:
                locator = card.locator(selector)
                if locator.count() > 0:
                    href = locator.first.get_attribute("href")
                    if href:
                        link = _normalize_shop_url(href)
                        break

            items.append({
                "title": title,
                "shop": shop_name,
                "price_text": price_text,
                "link": link,
            })

            if debug:
                print(f"[_extract_items_from_shop_page] 命中商品 {index}: {shop_name} | {title[:40]}")
        except Exception as e:
            if debug:
                print(f"[_extract_items_from_shop_page] 解析卡片失败: {e}")
            continue

    return items


def resolve_target_shop_urls(
    target_shops: Optional[List[str]] = None,
    debug: bool = False,
    context=None,
) -> Dict[str, str]:
    use_shops = target_shops or TARGET_SHOPS
    own_context = context is None
    page = None
    resolved: Dict[str, str] = {}

    try:
        if own_context:
            manager = BrowserManager()
            context = manager.launch_taobao()
            login_service = LoginService(context)
            page = login_service.login(TAOBAO_URL, "淘宝")
        else:
            page = context.new_page()

        for shop_name in use_shops:
            shop_url = _extract_shop_url_from_search(page, shop_name, debug=debug)
            if shop_url:
                resolved[shop_name] = shop_url
            _human_wait(page, SHORT_DELAY_RANGE_MS, reason=f"切换店铺: {shop_name}", debug=debug)

        if debug:
            print(f"[resolve_target_shop_urls] 共解析店铺URL {len(resolved)}/{len(use_shops)} 个")

        return resolved
    finally:
        if page:
            try:
                page.close()
            except Exception:
                pass

        if own_context and context:
            try:
                context.close()
            except Exception:
                pass


def search_taobao_target_shops(
    keyword: str,
    target_shops: Optional[List[str]] = None,
    pages: int = 1,
    debug: bool = False,
    context=None,
) -> List[Dict]:
    """
    在淘宝中先解析目标店铺URL，再进入每个店铺进行店内搜索。

    特点：
    - 不做关键词自动扩展，仅使用传入 keyword。
    - 只在目标店铺各自的店铺页内搜索。
    - 支持复用外部 context。
    """
    use_shops = target_shops or TARGET_SHOPS
    all_items: List[Dict] = []

    own_context = context is None
    page = None

    try:
        if own_context:
            manager = BrowserManager()
            context = manager.launch_taobao()
            login_service = LoginService(context)
            page = login_service.login(TAOBAO_URL, "淘宝")
        else:
            page = context.new_page()

        shop_urls: Dict[str, str] = {}
        for shop_name in use_shops:
            shop_url = _extract_shop_url_from_search(page, shop_name, debug=debug)
            if shop_url:
                shop_urls[shop_name] = shop_url
            _human_wait(page, SHORT_DELAY_RANGE_MS, reason=f"店铺URL解析间隔: {shop_name}", debug=debug)

        if debug:
            print(f"[search_taobao_target_shops] 已解析店铺URL {len(shop_urls)}/{len(use_shops)} 个")

        for shop_name, shop_url in shop_urls.items():
            for page_index in range(1, pages + 1):
                in_shop_url = _build_shop_search_url(shop_url, keyword, page_index)

                if debug:
                    print(f"[search_taobao_target_shops] 店内搜索 {shop_name}: {in_shop_url}")

                if not _safe_goto(page, in_shop_url, debug=debug):
                    if debug:
                        print(f"[search_taobao_target_shops] 跳过页面（访问失败）: {in_shop_url}")
                    continue

                page_items = _extract_items_from_shop_page(page, shop_name, debug=debug)
                all_items.extend(page_items)

                if debug:
                    print(f"[search_taobao_target_shops] {shop_name} 第{page_index}页命中 {len(page_items)} 条")

        if debug:
            print(f"[search_taobao_target_shops] 总命中 {len(all_items)} 条")

        return all_items
    finally:
        if page:
            try:
                page.close()
            except Exception:
                pass

        if own_context and context:
            try:
                context.close()
            except Exception:
                pass
