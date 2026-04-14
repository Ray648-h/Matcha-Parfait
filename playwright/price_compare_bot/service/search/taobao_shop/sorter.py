# service/search/taobao_shop/sorter.py
# 职责：对商品列表按价格排序

from typing import List, Dict


def sort_by_price(items: List[Dict], asc: bool = True) -> List[Dict]:
    """
    按 price 字段升序/降序排列商品。
    price 字段为字符串，内部自动转 float；无法解析时排到最末。
    """
    def _to_float(item: Dict) -> float:
        try:
            return float(str(item.get("price", 0)).replace("¥", "").strip())
        except (ValueError, TypeError):
            return float("inf")

    return sorted(items, key=_to_float, reverse=not asc)
