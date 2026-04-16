# service/search/taobao_shop/searcher.py
# 职责：接收关键词 + 用户选中的店铺列表 + 已登录 page，
#        依次进入店铺搜索并返回排序后的商品列表。

from typing import List, Dict
from urllib.parse import urlencode, urlparse, urlunparse

from .shop_loader import load_shop_urls
from .parser import parse_shop_items
from .sorter import sort_by_price
from .service import _safe_goto, _human_wait, SHORT_DELAY_RANGE_MS


def search_shops(
    keyword: str,
    selected_shops: List[str],
    page,
    debug: bool = False,
) -> List[Dict]:
    """
    在用户选中的店铺内搜索关键词，返回按价格升序排列的商品列表。

    Args:
        keyword:        搜索关键词（用户输入）
        selected_shops: 用户选中的店铺名列表，必须与 taobao_shop_urls.txt 中的名称一致
        page:           已登录的 Playwright page 对象
        debug:          是否输出调试日志

    Returns:
        List[Dict]，每条格式为 {title, price, link, shop}
    """
    shop_urls = load_shop_urls()
    all_items: List[Dict] = []

    for shop_name in selected_shops:
        url = shop_urls.get(shop_name)
        if not url:
            if debug:
                print(f"[searcher] ⚠️ 未找到店铺 URL，跳过: {shop_name}")
            continue

        search_url = _build_shop_search_url(url, keyword)

        if debug:
            print(f"[searcher] 🔍 {shop_name} -> {search_url}")

        ok = _safe_goto(page, search_url, debug=debug)
        if not ok:
            if debug:
                print(f"[searcher] ❌ 访问失败，跳过: {shop_name}")
            continue

        items = parse_shop_items(page, shop_name, debug=debug)
        all_items.extend(items)

        if debug:
            print(f"[searcher] ✅ {shop_name} 命中 {len(items)} 条")

        # 每家店搜索完之后间隔 1.8~3.6 秒，降低反爬风险
        _human_wait(page, SHORT_DELAY_RANGE_MS, reason=f"店铺切换: {shop_name}", debug=debug)

    sorted_items = sort_by_price(all_items)

    if debug:
        print(f"[searcher] 全部完成，共 {len(sorted_items)} 条商品")

    return sorted_items


# ── 私有工具 ─────────────────────────────────────

def _build_shop_search_url(shop_url: str, keyword: str) -> str:
    """
    在店铺 URL 基础上拼接 /search.htm?search=y&keyword=xxx
    兼容 taobao.com 和 tmall.com 两种域名格式。
    """
    parsed = urlparse(shop_url)
    base_path = parsed.path.rstrip("/")
    search_path = f"{base_path}/search.htm" if base_path else "/search.htm"
    query = urlencode({"search": "y", "keyword": keyword})
    return urlunparse((parsed.scheme or "https", parsed.netloc, search_path, "", query, ""))
