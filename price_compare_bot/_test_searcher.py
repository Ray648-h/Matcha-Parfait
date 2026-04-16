import sys
from config.context import BrowserManager
from config.settings import TAOBAO_URL
from service.login_service import LoginService
from service.search.taobao_shop.searcher import search_shops

context = None
page = None
try:
    manager = BrowserManager()
    context = manager.launch_taobao()
    login_service = LoginService(context)
    page = login_service.login(TAOBAO_URL, "淘宝")

    results = search_shops(
        keyword="GSC",
        selected_shops=["猫受屋", "鹤屋通贩"],
        page=page,
        debug=True,
    )

    print()
    print("=" * 50)
    print(f"共命中 {len(results)} 条商品")
    print("=" * 50)
    for i, item in enumerate(results[:10], 1):
        print(f"{i}. [{item['shop']}] {item['title'][:40]}")
        print(f"   价格: {item['price']}  链接: {item['link'][:60]}")

finally:
    if page:
        try:
            page.close()
        except Exception:
            pass
    if context:
        try:
            context.close()
        except Exception:
            pass
    print("\n浏览器已关闭")
    sys.exit(0)
