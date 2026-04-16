# service/search/search_service.py

class SearchService:
    def __init__(self, context):
        self.context = context

    def search_xianyu_items(self, product_name: str) -> list:
        """
        在闲鱼搜索商品，获取价格、运费、卖家信息
        假设已登录状态
        """
        page = self.context.new_page()
        search_url = f"https://www.goofish.com/search?q={product_name.replace(' ', '%20')}"
        page.goto(search_url)
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)  # 额外等待

        items = []

        # 假设商品项的selector是 '.item' 或类似，需要根据实际页面调整
        item_locators = page.locator('.item')  # 替换为实际selector

        for i in range(item_locators.count()):
            item = item_locators.nth(i)
            try:
                # 提取价格
                price_locator = item.locator('.price')  # 替换为实际价格selector
                price = price_locator.text_content().strip() if price_locator.count() > 0 else "未知"

                # 提取运费
                shipping_locator = item.locator('.shipping')  # 替换为实际运费selector
                shipping = shipping_locator.text_content().strip() if shipping_locator.count() > 0 else "未知"

                # 提取卖家
                seller_locator = item.locator('.seller')  # 替换为实际卖家selector
                seller = seller_locator.text_content().strip() if seller_locator.count() > 0 else "未知"

                items.append({
                    "price": price,
                    "shipping": shipping,
                    "seller": seller
                })
            except Exception as e:
                print(f"提取第{i+1}个商品信息失败: {e}")
                continue

        page.close()
        return items
