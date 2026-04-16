from .service import resolve_target_shop_urls, search_taobao_target_shops
from .searcher import search_shops
from .shop_loader import load_shop_urls, get_all_shop_names
from .direct_product_search import search_and_filter_products
from .new_search import search_shops_directly
from .taobao_scorer import (
    calculate_taobao_score, 
    score_taobao_items, 
    get_top_ranked_items_by_price,
    process_taobao_items_with_scoring
)
from .taobao_main import TaobaoSearch, Product, SearchResult, print_search_result

__all__ = [
    # 原有
    "resolve_target_shop_urls",
    "search_taobao_target_shops",
    # 新功能
    "search_shops",
    "load_shop_urls",
    "get_all_shop_names",
    # 直接搜索
    "search_and_filter_products",
    # 新搜索逻辑
    "search_shops_directly",
    # 评分功能
    "calculate_taobao_score",
    "score_taobao_items",
    "get_top_ranked_items_by_price",
    "process_taobao_items_with_scoring",
    # 整合模块
    "TaobaoSearch",
    "Product",
    "SearchResult",
    "print_search_result",
]
