# service/search/hpoi/scorer.py
"""
HPOI服务 - 评分模块
"""

from typing import List, Dict
import re
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
    - 部分匹配：如果搜索词的部分内容出现在标题中，也给予部分分数
    - 如果没有匹配任何搜索词，大幅扣分
    """
    
    title = item.get('title', '').lower()
    score = 10  # 基础分
    
    # 1. 检查搜索词是否出现在标题中
    search_term_matched_count = 0
    for term in search_terms:
        term_lower = term.lower()
        
        # 完全匹配
        if term_lower in title:
            score += 20  # 每个搜索词完全匹配加20分
            search_term_matched_count += 1
            if debug:
                print(f"[calculate_score] 完全匹配: '{term_lower}' in '{title[:50]}...'")
        
        # 部分匹配：如果搜索词包含多个部分，检查每个部分是否在标题中
        else:
            # 对于中文文本，尝试多种拆分方式
            # 1. 按空格、标点等拆分
            parts = re.split(r'[\s\-_]+', term_lower)
            
            # 2. 如果只有一个部分，尝试按字符拆分（针对中文）
            if len(parts) <= 1:
                # 将中文字符拆分为单个字符
                parts = list(term_lower)
            
            matched_parts = 0
            for part in parts:
                if part and len(part) > 1 and part in title:
                    matched_parts += 1
                # 对于单字符，检查是否在标题中（但权重较低）
                elif part and len(part) == 1 and part in title:
                    matched_parts += 0.5  # 单字符匹配权重减半
            
            # 如果大部分部分都匹配，给予部分分数
            if matched_parts > 0:
                # 计算匹配比例
                match_ratio = matched_parts / len(parts)
                # 根据匹配比例给予分数（最高15分）
                partial_score = int(15 * match_ratio)
                score += partial_score
                search_term_matched_count += 1
                if debug:
                    print(f"[calculate_score] 部分匹配: {matched_parts}/{len(parts)} parts of '{term_lower}' in '{title[:50]}...' (+{partial_score}分, ratio={match_ratio:.2f})")
    
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
