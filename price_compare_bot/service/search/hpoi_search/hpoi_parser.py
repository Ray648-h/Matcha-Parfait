"""HPOI解析兼容层，统一转发到 hpoi 子包实现。"""

from .hpoi.config import HPOI_SEARCH_URL
from .hpoi.fetcher import fetch_hpoi_items, parse_hpoi_item

__all__ = [
    'HPOI_SEARCH_URL',
    'fetch_hpoi_items',
    'parse_hpoi_item',
]
