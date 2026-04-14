# service/search/hpoi/scorer.py
"""
HPOI服务 - 评分模块
"""

from typing import List, Dict
from .utils import decompose_keyword


def score_items(items: List[Dict], keyword: str, debug: bool = False) -> List[Dict]:
    """
    对商品列表进行关键词评分
    基于搜索词的分解进行打分
    """
    
    # 分解搜索关键词
    search_terms = decompose_keyword(keyword)
    
    if debug:
        print(f"\n[score_items] 搜索词分解: {keyword} -> {search_terms}")
    
    scored_items = []
    
    for item in items:
        score = calculate_score(item, search_terms, debug)
        item['score'] = score
        scored_items.append(item)
        
        if debug:
            print(f"[score_items] {item['title'][:50]}... | 得分: {score}")
    
    return scored_items


def calculate_score(item: Dict, search_terms: List[str], debug: bool = False) -> int:
    """
    计算单个商品的关键词匹配得分
    
    计分规则：
    - 基础分：10分（商品存在且有价格）
    - 搜索词匹配：每个搜索词出现在标题中就加分（包含搜索词+20）
    - 如果没有匹配任何搜索词，大幅扣分
    """
    
    title = item.get('title', '').lower()
    score = 10  # 基础分
    
    # 1. 检查搜索词是否出现在标题中
    search_term_matched_count = 0
    for term in search_terms:
        term_lower = term.lower()
        if term_lower in title:
            score += 20  # 每个搜索词出现加20分
            search_term_matched_count += 1
    
    # 2. 有效价格的加分
    if item.get('price', 0) > 0:
        score += 5
    
    # 3. 有发售日期的加分（表示正版/官方发布）
    if item.get('release_date') and item.get('release_date') != '未知':
        score += 10
    
    # 4. 如果没有匹配任何搜索词，大幅扣分（表示这不是用户想要的商品）
    if search_term_matched_count == 0:
        score -= 50
    
    return max(score, 0)  # 确保最低分数为0
