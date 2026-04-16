"""HPOI打分兼容层，统一转发到 hpoi 子包实现。"""

from .hpoi.scorer import score_items, calculate_score

__all__ = [
    'score_items',
    'calculate_score',
]
