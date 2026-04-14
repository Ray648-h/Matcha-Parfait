# service/search/hpoi/utils.py
"""
HPOI服务 - 工具函数
"""

import re
from typing import List
from .config import PRODUCT_TYPE_KEYWORDS


def parse_price(text: str) -> float:
    """
    从文本中提取价格数值
    支持格式: $100, ¥100, 100元, 100JPY等
    """
    try:
        # 移除货币符号和文字，只保留数字和小数点
        price_str = re.sub(r'[^\d.]', '', text)
        
        # 处理多个小数点的情况
        parts = price_str.split('.')
        if len(parts) > 2:
            price_str = '.'.join([parts[0], parts[-1]])
        
        price = float(price_str) if price_str else 0.0
        return price
    
    except Exception:
        return 0.0


def decompose_keyword(keyword: str) -> List[str]:
    """
    分解搜索关键词为多个词组
    例如: "满舰饰真子粘土人" -> ["满舰饰真子", "粘土人"]
    
    使用简单的启发式算法：
    1. 尝试识别常见的产品类型词（如"粘土人"、"手办"等）
    2. 将剩余部分作为一个词组
    """
    keyword = keyword.strip()
    
    decomposed = []
    remaining = keyword
    
    # 从搜索词中提取已知的产品类型词
    for prod_type in PRODUCT_TYPE_KEYWORDS:
        if prod_type.lower() in keyword.lower():
            decomposed.append(prod_type)
            # 移除已识别的词
            remaining = remaining.replace(prod_type, "").replace(prod_type.lower(), "")
    
    # 如果还有剩余的词，添加为一个词组
    remaining = remaining.strip()
    if remaining:
        decomposed.append(remaining)
    
    # 如果没有识别出任何词，直接返回原关键词
    if not decomposed:
        decomposed = [keyword]
    
    return decomposed


def convert_jpy_to_cny(jpy_amount: float, exchange_rate: float = 0.0512) -> float:
    """将日元金额转换成人民币金额。

    参数:
        jpy_amount: 日元金额
        exchange_rate: 日元->人民币汇率，默认 0.0512
    返回:
        四舍五入到2位小数的人民币金额
    """
    try:
        cny_amount = float(jpy_amount) * float(exchange_rate)
        return round(cny_amount, 2)
    except Exception:
        return 0.0
