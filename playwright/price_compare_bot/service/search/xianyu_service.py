# service/search/xianyu_service.py

from playwright.sync_api import sync_playwright
import time

from .parser import parse_xianyu_raw_items
from .filter import filter_items_by_keyword
from .sorter import sort_items_by_price


# ==============================
# 配置
# ==============================

USER_DATA_DIR = "user_data/xianyu"  # 👈 你的浏览器用户目录





# ==============================
# 主入口
# ==============================

def search_xianyu(keyword: str, max_items=50, debug=False, pages=1, context=None):
    """
    对外主函数：搜索商品并返回已解析信息（价格、运费、卖家、链接）。
    
    参数：
    - keyword: 搜索关键词
    - max_items: 最多返回商品数
    - debug: 是否打印调试信息
    - pages: 要翻页的页数（1表示第一页，2表示第一二页等）
    - context: 可选的已登录 Playwright context（如果提供则使用，否则创建新浏览器）
    """
    all_items = []
    
    for page_num in range(1, pages + 1):
        if debug:
            print(f"\n[search_xianyu] 正在加载第 {page_num} 页...")
        
        raw_data = _fetch_raw_data(keyword, debug=debug, page=page_num, context=context)
        items = parse_xianyu_raw_items(raw_data, debug=debug)
        all_items.extend(items)
        
        if debug:
            print(f"[search_xianyu] 第 {page_num} 页共获取 {len(items)} 个商品")

    # 2. 过滤无效或不匹配关键词项（使用 filter.py）
    # ⚠️ 暂时注释过滤，先调试是否能获取到商品数据
    # all_items = filter_items_by_keyword(all_items, blacklist=["不卖", "展示", "求购", "想要", "已出"])

    # 3. 根据总价排序（使用 sorter.py）
    all_items = sort_items_by_price(all_items, asc=True)

    if debug:
        print(f"[search_xianyu] 处理结果共 {len(all_items)} 条，取前 {max_items} 条")

    return all_items[:max_items]


# ==============================
# 1️⃣ 抓数据（Hook接口）
# ==============================

def _fetch_raw_data(keyword: str, debug=False, max_scroll=6, page=1, context=None):
    """
    抓取闲鱼搜索页商品数据
    
    参数：
    - keyword: 搜索关键词
    - debug: 是否打印调试信息
    - max_scroll: 单页内滚动次数
    - page: 页码（从1开始）
    - context: 可选的已创建 browser context（如果提供则使用现有的 page，否则创建新浏览器）
    """
    results = []

    # 如果提供了 context，直接使用
    if context:
        page_obj = context.new_page()
        should_close_browser = False
        browser = None
    else:
        # 创建新的浏览器实例
        p = sync_playwright().start()
        browser = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False
        )
        page_obj = browser.new_page()
        should_close_browser = True

    try:
        # ⚠️ 闲鱼翻页URL参数可能为 pageNo 或 page，根据实际调整
        current_url = f"https://www.goofish.com/search?q={keyword}&pageNo={page}"
        if debug:
            print(f"[_fetch_raw_data] 正在打开: {current_url}")
        
        page_obj.goto(current_url)

        page_obj.wait_for_load_state("networkidle")
        page_obj.wait_for_timeout(2500)

        # 滚动加载，触发更多数据
        for i in range(max_scroll):
            if debug:
                print(f"[scroll] {i+1}/{max_scroll}")
            page_obj.mouse.wheel(0, 2500)
            page_obj.wait_for_timeout(1500)

        page_obj.reload()
        page_obj.wait_for_load_state("networkidle")
        page_obj.wait_for_timeout(2000)

        # ⚠️ 需要结合实际闲鱼网页商品元素选择器调整：检查页面DOM，确认商品项的href属性
        item_locators = page_obj.locator('a[href*="goofish.com/item"]')

        # 在浏览器关闭前，直接提取所有数据
        for i in range(item_locators.count()):
            try:
                item = item_locators.nth(i)
                
                # 获取标题
                title = ""
                spans = item.locator('span')
                max_len = 0
                
                for j in range(spans.count()):
                    span_text = spans.nth(j).text_content().strip()
                    if len(span_text) > max_len and len(span_text) > 5:
                        max_len = len(span_text)
                        title = span_text
                
                if not title:
                    continue
                
                # 获取价格
                price_text = ""
                for j in range(spans.count()):
                    span_text = spans.nth(j).text_content().strip()
                    if span_text.isdigit() and len(span_text) >= 1:
                        price_text = span_text
                        break
                
                # 获取包邮图标
                has_post_icon = item.locator('img[src*="O1CN017BILHl1VNARooBnhe"]').count() > 0
                
                results.append({
                    'title': title,
                    'price': price_text,
                    'has_post_icon': has_post_icon
                })
                
            except Exception as e:
                if debug:
                    print(f"[_fetch_raw_data] 提取第{i+1}商品失败: {e}")
                continue

        if debug:
            print(f"[_fetch_raw_data] 采集到 {len(results)} 个商品数据")

    finally:
        # 只有在我们创建了浏览器时，才关闭它
        if should_close_browser and browser:
            browser.close()
        else:
            # 如果使用外部 context 提供的 page，则关闭这个 page，但不关闭 context
            page_obj.close()

    return results







# # ==============================
# # 4️⃣ 排序
# # ==============================

# def _sort_items(items):
#     return sorted(items, key=lambda x: x.get("total", float('inf')))


