# ==============================
# 3️⃣ 过滤
# ==============================

def _filter_items(items, keyword):
    if not keyword:
        return items

    keyword_lower = keyword.lower()
    out = []

    for item in items:
        title = item.get("title", "").lower()

        if keyword_lower not in title:
            continue

        if any(w in title for w in ["不卖", "展示", "求购", "想要", "已出"]):
            continue

        out.append(item)

    return out

def filter_items_by_keyword(items, keyword):
    """过滤商品列表，保留包含关键词且非无效状态的商品"""
    return _filter_items(items, keyword)
