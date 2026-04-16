# service/search/hpoi_service.py
"""
HPOI (日本合伙人玩具价格信息) 搜索和筛选服务

已重构：HPOI模块现已挪至 service/search/hpoi/ 文件夹
本文件包含顶层服务接口和测试调试入口。
"""

from .hpoi.main import search_hpoi, search_hpoi_top_n
from .hpoi.config import HPOI_URL, HPOI_SEARCH_URL
from .hpoi.fetcher import fetch_hpoi_items, parse_hpoi_item
from .hpoi.scorer import score_items, calculate_score
from .hpoi.utils import parse_price, decompose_keyword
from urllib.parse import urljoin


def test_hpoi_search(keyword: str = "GSC户山香澄"):
    """测试HPOI搜索功能，返回单个最佳商品。"""
    print("=" * 60)
    print(f"🚀 开始HPOI搜索测试: {keyword}")
    print("=" * 60)

    result = search_hpoi(keyword, max_items=20, debug=True)

    if result:
        print("\n" + "=" * 60)
        print("✅ 搜索完成")
        print("=" * 60)
        print(f"商品: {result['title']}")
        print(f"价格: ¥{result['price']}")
        print(f"发售日期: {result['release_date']}")
        print(f"得分: {result['score']}")
        print(f"来源: {result['source']}")
        if result.get('link'):
            print(f"链接: {result['link']}")
    else:
        print("❌ 未找到匹配商品")

    print("=" * 60)


def test_hpoi_search_top_6(keyword: str = "GSC户山香澄"):
    """测试HPOI搜索功能，返回前6个商品。"""
    print("=" * 80)
    print(f"开始HPOI爬取前6个商品: {keyword}")
    print("=" * 80)

    results = search_hpoi_top_n(keyword, n=6, debug=True)

    if results:
        print("\n" + "=" * 80)
        print(f"✅ 爬取完成，共获得 {len(results)} 个商品")
        print("=" * 80 + "\n")

        for idx, item in enumerate(results, 1):
            print(f"{idx}. 【{item['source']}】{item['title']}")
            print(f"   💰 价格: ¥{item.get('price', '未知')}")
            print(f"   📅 发售日期: {item.get('release_date', '未知')}")
            print(f"   ⭐ 得分: {item.get('score', 0)}")
            if item.get('link'):
                print(f"   🔗 链接: {item['link']}")
            print()
    else:
        print("❌ 未找到匹配商品")

    print("=" * 80)


def search_hpoi_top_5(keyword: str, debug: bool = False):
    """
    搜索HPOI并返回前5个商品，链接转换为绝对链接
    
    参数:
        keyword: 搜索关键词
        debug: 是否打印调试信息
        
    返回:
        前5个商品列表，已按得分排序，链接为绝对链接
    """
    # 获取前6个商品（多取一个以防有无效商品）
    results = search_hpoi_top_n(keyword, n=6, debug=debug)
    
    # 只保留前5个
    top_5 = results[:5] if results else []
    
    # 将相对链接转换为绝对链接
    for item in top_5:
        if item.get('link') and not item['link'].startswith('http'):
            item['link'] = urljoin(HPOI_URL, item['link'])
    
    return top_5


def test_hpoi_search_top_5(keyword: str = "GSC户山香澄"):
    """测试HPOI搜索功能，返回前5个商品（绝对链接）。"""
    print("=" * 80)
    print(f"开始HPOI爬取前5个商品: {keyword}")
    print("=" * 80)

    results = search_hpoi_top_5(keyword, debug=True)

    if results:
        print("\n" + "=" * 80)
        print(f"✅ 爬取完成，共获得 {len(results)} 个商品（前5名）")
        print("=" * 80 + "\n")

        for idx, item in enumerate(results, 1):
            print(f"{idx}. 【{item['source']}】{item['title']}")
            print(f"   💰 价格: ¥{item.get('price', '未知')}")
            print(f"   📅 发售日期: {item.get('release_date', '未知')}")
            print(f"   ⭐ 得分: {item.get('score', 0)}")
            if item.get('link'):
                print(f"   🔗 链接: {item['link']}")
            print()
    else:
        print("❌ 未找到匹配商品")

    print("=" * 80)

__all__ = [
    'search_hpoi',
    'search_hpoi_top_n',
    'search_hpoi_top_5',
    'HPOI_URL',
    'HPOI_SEARCH_URL',
    'fetch_hpoi_items',
    'parse_hpoi_item',
    'score_items',
    'calculate_score',
    'parse_price',
    'decompose_keyword',
    'test_hpoi_search',
    'test_hpoi_search_top_6',
    'test_hpoi_search_top_5',
]


if __name__ == "__main__":
    test_hpoi_search_top_6()



