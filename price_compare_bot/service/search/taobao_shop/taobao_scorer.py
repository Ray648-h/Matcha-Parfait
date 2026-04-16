# service/search/taobao_shop/taobao_scorer.py
"""
淘宝商品评分模块
根据用户需求：
1. 与输入关键词一致就加分
2. 有别的关键词就扣分
3. 使得能够与输入完全匹配的商品得分最高
4. 最后将最高分前两个名次（重复分数算名次一样）的商品按照价格从低到高列出
"""

import re
from typing import List, Dict, Tuple


def calculate_taobao_score(item: Dict, keyword: str, debug: bool = False) -> Tuple[int, List[str]]:
    """
    计算淘宝商品的匹配得分，并提取特殊关键词
    
    计分规则：
    1. 基础分：10分
    2. 关键词匹配加分：
       - 完全匹配关键词：+200分
       - 关键词出现在标题中：每个出现+100分
       - 关键词分词后匹配：每个匹配的词+50分
    3. 无关关键词扣分：
       - 标题中包含与关键词无关的词汇：每个无关词-5分（减少扣分）
    4. 价格合理性加分：
       - 有价格：+10分 
    5. 店铺匹配加分（如果提供目标店铺）：
       - 店铺在目标列表中：+20分
    6. 匹配比例加分：
       - 匹配的关键词比例越高，额外加分越多
    7. 特殊关键词处理：
       - 如果标题中包含"补款"、"尾款"等字样，单独摘出来
    
    参数：
        item: 商品信息字典，包含title、price_text、shop等字段
        keyword: 用户输入的关键词
        debug: 是否输出调试信息
    
    返回：
        (匹配得分, 特殊关键词列表)
    """
    score = 10  # 基础分
    title = item.get('title', '').lower()
    keyword_lower = keyword.lower()
    
    # 特殊关键词列表
    special_keywords = []
    
    if debug:
        print(f"\n[calculate_taobao_score] 计算商品得分: '{item.get('title', '')[:50]}...'")
        print(f"  关键词: '{keyword}'")
    
    # 1. 检查特殊关键词
    special_terms = ['补款', '尾款']
    for term in special_terms:
        if term in title:
            special_keywords.append(term)
            if debug:
                print(f"  发现特殊关键词: '{term}'")
    
    # 2. 完全匹配检查
    if keyword_lower == title.strip():
        score += 200
        if debug:
            print(f"  完全匹配加分: +200")
    
    # 3. 关键词出现在标题中
    if keyword_lower in title:
        # 计算出现次数
        count = title.count(keyword_lower)
        score += count * 100
        if debug:
            print(f"  关键词出现{count}次加分: +{count * 100}")
    
    # 4. 关键词分词匹配
    search_terms = _split_keyword(keyword)
    matched_terms = []
    for term in search_terms:
        term_lower = term.lower()
        if term_lower in title:
            score += 50
            matched_terms.append(term)
            if debug:
                print(f"  分词匹配 '{term}' 加分: +50")
    
    # 5. 无关关键词扣分（减少扣分）
    # 提取标题中的所有中文词汇
    title_terms = _extract_chinese_terms(title)
    keyword_terms = set(_extract_chinese_terms(keyword_lower))
    
    unrelated_terms = []
    for term in title_terms:
        if term not in keyword_terms and len(term) >= 2:
            # 检查是否与关键词相关（简单实现：检查是否有重叠字符）
            related = False
            for k_term in keyword_terms:
                if len(k_term) >= 2 and (term in k_term or k_term in term):
                    related = True
                    break
            
            if not related:
                unrelated_terms.append(term)
                score -= 5  # 减少扣分
                if debug:
                    print(f"  无关关键词 '{term}' 扣分: -5")
    
    # 6. 价格合理性加分
    price_text = item.get('price_text', '')
    if price_text and price_text != 'N/A':
        score += 10
        if debug:
            print(f"  有价格加分: +10")
    
    # 7. 店铺匹配加分（如果商品有target_shop字段）
    if item.get('target_shop'):
        score += 30
        if debug:
            print(f"  目标店铺加分: +30")
    
    # 8. 匹配比例加分
    if search_terms:
        match_ratio = len(matched_terms) / len(search_terms)
        if match_ratio > 0:
            bonus = int(match_ratio * 50)  # 最高50分
            score += bonus
            if debug:
                print(f"  匹配比例 {match_ratio:.2f} 加分: +{bonus}")
    
    # 9. 特殊关键词额外处理
    # 如果有特殊关键词，可以给予额外加分或特殊标记
    if special_keywords:
        # 这里可以根据业务需求决定是否给予额外加分或扣分
        # 例如，如果是"补款"或"尾款"，可能表示这不是完整商品，可以适当扣分
        if any(term in ['补款', '尾款'] for term in special_keywords):
            score -= 10  # 轻微扣分，表示这不是完整商品
            if debug:
                print(f"  特殊关键词扣分: -10")
    
    # 确保分数不为负数
    final_score = max(score, 0)
    
    if debug:
        print(f"  最终得分: {final_score}")
        if matched_terms:
            print(f"  匹配的分词: {matched_terms}")
        if unrelated_terms:
            print(f"  无关词汇: {unrelated_terms}")
        if special_keywords:
            print(f"  特殊关键词: {special_keywords}")
    
    return final_score, special_keywords


def _split_keyword(keyword: str) -> List[str]:
    """
    将关键词拆分为有意义的词汇
    
    算法：
    1. 按空格、标点符号分割
    2. 过滤短词（长度<2）
    3. 保留中文词汇和数字
    """
    if not keyword:
        return []
    
    # 分割关键词
    terms = re.split(r'[,\s，。！？；：、]+', keyword)
    
    # 过滤和清理
    filtered_terms = []
    for term in terms:
        term = term.strip()
        if not term:
            continue
        
        # 保留长度>=2的词汇，或者包含数字的词汇
        if len(term) >= 2 or any(char.isdigit() for char in term):
            filtered_terms.append(term)
    
    return filtered_terms


def _extract_chinese_terms(text: str) -> List[str]:
    """
    从文本中提取中文词汇
    
    算法：
    1. 提取连续的中文字符
    2. 过滤短词（长度<2）
    """
    if not text:
        return []
    
    # 提取连续的中文字符
    chinese_terms = re.findall(r'[\u4e00-\u9fff]{2,}', text)
    
    return chinese_terms


def score_taobao_items(items: List[Dict], keyword: str, debug: bool = False) -> List[Dict]:
    """
    对淘宝商品列表进行评分
    
    参数：
        items: 商品列表
        keyword: 用户输入的关键词
        debug: 是否输出调试信息
    
    返回：
        评分后的商品列表，按得分降序排序
    """
    if debug:
        print(f"\n[score_taobao_items] 开始评分，关键词: '{keyword}'")
        print(f"  待评分商品数量: {len(items)}")
    
    scored_items = []
    
    for item in items:
        score, special_keywords = calculate_taobao_score(item, keyword, debug)
        item['score'] = score
        item['special_keywords'] = special_keywords  # 添加特殊关键词到商品信息中
        scored_items.append(item)
    
    # 按得分降序排序
    scored_items.sort(key=lambda x: x['score'], reverse=True)
    
    if debug:
        print(f"\n[score_taobao_items] 评分完成")
        print(f"  最高分: {scored_items[0]['score'] if scored_items else 0}")
        print(f"  最低分: {scored_items[-1]['score'] if scored_items else 0}")
    
    return scored_items


def get_top_ranked_items_by_price(scored_items: List[Dict], top_n: int = 2) -> List[Dict]:
    """
    获取最高分前两个名次（重复分数算名次一样）的商品，按照价格从低到高列出
    
    算法：
    1. 确定前N个名次的分数阈值
    2. 筛选出分数在前N个名次的商品
    3. 按价格从低到高排序
    
    参数：
        scored_items: 已评分的商品列表（按得分降序排序）
        top_n: 要获取的前几个名次
    
    返回：
        按价格从低到高排序的商品列表
    """
    if not scored_items:
        return []
    
    # 确定前N个名次的分数阈值
    unique_scores = []
    current_score = None
    
    for item in scored_items:
        score = item['score']
        if score != current_score:
            unique_scores.append(score)
            current_score = score
        
        if len(unique_scores) >= top_n:
            break
    
    # 如果没有足够的唯一分数，使用所有分数
    if len(unique_scores) < top_n:
        unique_scores = list(set(item['score'] for item in scored_items))
        unique_scores.sort(reverse=True)
        unique_scores = unique_scores[:top_n]
    
    # 获取分数阈值（前N个名次的最低分数）
    threshold_score = unique_scores[-1] if unique_scores else 0
    
    if len(unique_scores) > 0:
        print(f"\n[get_top_ranked_items_by_price] 前{top_n}个名次的分数阈值: {threshold_score}")
        print(f"  唯一分数列表: {unique_scores}")
    
    # 筛选出分数在前N个名次的商品
    top_items = [item for item in scored_items if item['score'] >= threshold_score]
    
    # 按价格从低到高排序
    def get_price(item):
        price_text = item.get('price_text', '')
        try:
            # 尝试提取价格数字
            price_str = re.sub(r'[^\d.]', '', price_text)
            return float(price_str) if price_str else float('inf')
        except (ValueError, TypeError):
            return float('inf')
    
    top_items_sorted_by_price = sorted(top_items, key=get_price)
    
    print(f"\n[get_top_ranked_items_by_price] 结果:")
    print(f"  筛选出 {len(top_items)} 个商品（分数 >= {threshold_score}）")
    print(f"  按价格排序后: {len(top_items_sorted_by_price)} 个商品")
    
    return top_items_sorted_by_price


def process_taobao_items_with_scoring(items: List[Dict], keyword: str, debug: bool = False) -> Tuple[List[Dict], List[Dict]]:
    """
    处理淘宝商品的完整流程：评分 + 获取前N名按价格排序
    
    参数：
        items: 原始商品列表
        keyword: 用户输入的关键词
        debug: 是否输出调试信息
    
    返回：
        (评分后的所有商品列表, 前2名按价格排序的商品列表)
    """
    # 1. 对商品进行评分
    scored_items = score_taobao_items(items, keyword, debug)
    
    # 2. 获取前2名按价格排序的商品
    top_items = get_top_ranked_items_by_price(scored_items, top_n=2)
    
    return scored_items, top_items


# 测试函数
def test_taobao_scorer():
    """测试淘宝评分模块"""
    print("=" * 80)
    print("测试淘宝商品评分模块（包含特殊关键词测试）")
    print("=" * 80)
    
    # 测试数据（包含特殊关键词的商品）
    test_items = [
        {
            'title': '初音未来 粘土人 3.0 全新正版 包邮',
            'price_text': '¥299.00',
            'shop': 'gsc官方旗舰店',
            'target_shop': 'gsc'
        },
        {
            'title': '初音未来 手办 模型 二手 补款',
            'price_text': '¥150.00',
            'shop': '二手玩具店',
            'target_shop': None
        },
        {
            'title': '初音未来 粘土人 尾款',
            'price_text': '¥280.00',
            'shop': '动漫周边店',
            'target_shop': None
        },
        {
            'title': '其他角色 粘土人 2.0 定金',
            'price_text': '¥250.00',
            'shop': '模型专卖店',
            'target_shop': None
        },
        {
            'title': '初音未来 预售',
            'price_text': '¥320.00',
            'shop': '高价店',
            'target_shop': None
        },
        {
            'title': '初音未来 粘土人 预订',
            'price_text': '¥350.00',
            'shop': '预订专店',
            'target_shop': None
        }
    ]
    
    # 测试不同的关键词
    test_keywords = [
        "初音未来粘土人3.0",
        "初音未来",
        "粘土人"
    ]
    
    for keyword in test_keywords:
        print(f"\n{'='*60}")
        print(f"测试关键词: '{keyword}'")
        print(f"{'='*60}")
        
        # 处理商品
        scored_items, top_items = process_taobao_items_with_scoring(
            test_items, keyword, debug=True
        )
        
        # 显示评分结果（包含特殊关键词）
        print(f"\n评分结果（按得分降序，显示特殊关键词）:")
        for i, item in enumerate(scored_items[:6], 1):
            title_preview = item['title'][:40] + "..." if len(item['title']) > 40 else item['title']
            special_keywords = item.get('special_keywords', [])
            special_str = f" [特殊: {', '.join(special_keywords)}]" if special_keywords else ""
            print(f"{i}. 得分: {item['score']:3d} | 价格: {item['price_text']:10s} | {title_preview}{special_str}")
        
        # 显示前2名按价格排序的结果
        print(f"\n前2名按价格从低到高排序:")
        if top_items:
            for i, item in enumerate(top_items, 1):
                title_preview = item['title'][:40] + "..." if len(item['title']) > 40 else item['title']
                special_keywords = item.get('special_keywords', [])
                special_str = f" [特殊: {', '.join(special_keywords)}]" if special_keywords else ""
                print(f"{i}. 价格: {item['price_text']:10s} | 得分: {item['score']:3d} | {title_preview}{special_str}")
        else:
            print("  无符合条件的商品")
        
        print(f"\n统计信息:")
        print(f"  总商品数: {len(scored_items)}")
        print(f"  前2名商品数: {len(top_items)}")
        if scored_items:
            scores = [item['score'] for item in scored_items]
            print(f"  得分范围: {min(scores)} - {max(scores)}")
            print(f"  平均得分: {sum(scores)/len(scores):.1f}")
            
            # 统计特殊关键词
            special_items = [item for item in scored_items if item.get('special_keywords')]
            print(f"  包含特殊关键词的商品数: {len(special_items)}")
            if special_items:
                all_special = []
                for item in special_items:
                    all_special.extend(item.get('special_keywords', []))
                special_counts = {}
                for term in all_special:
                    special_counts[term] = special_counts.get(term, 0) + 1
                print(f"  特殊关键词统计: {special_counts}")


if __name__ == "__main__":
    test_taobao_scorer()