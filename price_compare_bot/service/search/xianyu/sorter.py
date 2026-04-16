
# ==============================
# 4️⃣ 排序
# ==============================

def sort_items_by_price(items, asc=True):
    def parse_price(p):
        try:
            return float(str(p).replace("¥", "").replace("元", "").strip())
        except:
            return float('inf')

    for item in items:
        item["price"] = parse_price(item.get("price", 0))

    sorted_items = sorted(
        items,
        key=lambda x: (
            0 if x.get('shipping') == '包邮' else 1,
            x.get('price', float('inf'))
        )
    )

    if asc:
        return sorted_items
    return list(reversed(sorted_items))


def _sort_items(items):
    return sort_items_by_price(items)

