# service/search/hpoi/main.py
"""
HPOI服务 - 主要搜索函数
"""

from typing import List, Dict, Optional
from .fetcher import fetch_hpoi_items
from .scorer import score_items


def search_hpoi(keyword: str, max_items: int = 20, debug: bool = False, 
                context=None) -> Optional[Dict]:
    """
    在HPOI中搜索商品，基于关键词打分筛选，返回最佳商品的详细信息。
    
    参数：
    - keyword: 搜索关键词（支持日文/中文）
    - max_items: 最多搜索的商品数
    - debug: 是否打印调试信息
    - context: 可选的Playwright context
    
    返回：
    - 最佳匹配商品的dict，包含:
        {
            'title': '商品名称',
            'price': 发售价格,
            'release_date': '发售日期',
            'score': 关键词匹配分数,
            'link': '商品链接',
            'source': '来源信息'
        }
    """
    
    # 1. 获取搜索结果
    if debug:
        print(f"\n[search_hpoi] 正在HPOI中搜索: {keyword}")
    
    items = fetch_hpoi_items(keyword, max_items, debug, context)
    
    if not items:
        if debug:
            print(f"[search_hpoi] 未找到相关商品")
        return None
    
    if debug:
        print(f"[search_hpoi] 共获取 {len(items)} 个商品")
    
    # 2. 对每个商品进行关键词评分
    scored_items = score_items(items, keyword, debug)
    
    if not scored_items:
        if debug:
            print(f"[search_hpoi] 评分后无有效商品")
        return None
    
    # 3. 选择得分最高的商品
    best_item = max(scored_items, key=lambda x: x['score'])
    
    if debug:
        print(f"\n[search_hpoi] 最佳商品:")
        print(f"  标题: {best_item['title']}")
        print(f"  价格: ¥{best_item['price']}")
        print(f"  发售日期: {best_item['release_date']}")
        print(f"  得分: {best_item['score']}")
    
    return best_item


def search_hpoi_top_n(keyword: str, n: int = 6, 
                      debug: bool = False, context=None) -> List[Dict]:
    """
    搜索HPOI并返回前N个商品的打分结果（按得分排序）
    
    参数：
    - keyword: 搜索关键词
    - n: 获取多少个商品（默认6个）
    - debug: 是否打印调试信息
    - context: 可选的Playwright context
    
    返回：
    - 按得分排序的商品列表，每个商品包含title、price、release_date、score等信息
    """
    
    if debug:
        print(f"\n[search_hpoi_top_n] 正在HPOI中搜索: {keyword}")
    
    # 获取前N个商品的原始数据
    items = fetch_hpoi_items(keyword, n, debug, context)
    
    if not items:
        if debug:
            print(f"[search_hpoi_top_n] 未找到相关商品")
        return []
    
    if debug:
        print(f"[search_hpoi_top_n] 共获取 {len(items)} 个商品")
    
    # 对获取的商品进行关键词评分
    scored_items = score_items(items, keyword, debug)
    
    if not scored_items:
        if debug:
            print(f"[search_hpoi_top_n] 评分后无有效商品")
        return []
    
    # 按得分排序（降序）
    sorted_items = sorted(scored_items, key=lambda x: x['score'], reverse=True)
    
    if debug:
        print(f"\n[search_hpoi_top_n] 返回 {len(sorted_items)} 个商品（已按得分排序）")
    
    return sorted_items


def _run_demo(keyword: str = "GSC户山香澄") -> None:
    """命令行调试入口：默认打印前6个商品。"""
    print("=" * 80)
    print(f"开始HPOI爬取前6个商品: {keyword}")
    print("=" * 80)

    results = search_hpoi_top_n(keyword, n=6, debug=True)

    if results:
        print("\n" + "=" * 80)
        print(f"✅ 爬取完成，共获得 {len(results)} 个商品")
        print("=" * 80 + "\n")

        for idx, item in enumerate(results, 1):
            print(f"{idx}. 【{item.get('source', 'HPOI')}】{item.get('title', '')}")
            print(f"   💰 价格: ¥{item.get('price', '未知')}")
            print(f"   📅 发售日期: {item.get('release_date', '未知')}")
            print(f"   ⭐ 得分: {item.get('score', 0)}")
            if item.get('link'):
                print(f"   🔗 链接: {item['link']}")
            print()
    else:
        print("❌ 未找到匹配商品")

    print("=" * 80)


if __name__ == "__main__":
    _run_demo()
