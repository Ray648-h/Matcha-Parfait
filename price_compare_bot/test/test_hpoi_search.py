# -*- coding: utf-8 -*-
"""
HPOI搜索功能测试脚本

测试HPOI（日本合伙人玩具价格信息）搜索功能，包括：
1. 基本搜索功能测试
2. 关键词分解测试
3. 评分逻辑测试
4. 价格解析测试
5. 实际网络搜索测试（可选）
"""

import sys
import os
import json
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hpoi_search.hpoi_service import (
    search_hpoi, 
    search_hpoi_top_n,
    test_hpoi_search,
    test_hpoi_search_top_6,
    parse_price,
    decompose_keyword,
    calculate_score,
    fetch_hpoi_items,
    score_items
)
from hpoi_search.hpoi.utils import convert_jpy_to_cny
from hpoi_search.hpoi.config import PRODUCT_TYPE_KEYWORDS


def test_price_parsing():
    """测试价格解析功能"""
    print("=" * 80)
    print("测试价格解析功能")
    print("=" * 80)
    
    test_cases = [
        ("¥12,800", 12800.0),
        ("￥12,800", 12800.0),
        ("12800日元", 12800.0),
        ("12,800JPY", 12800.0),
        ("12800元", 12800.0),
        ("$128.00", 128.0),
        ("128.00", 128.0),
        ("12,800.50", 12800.5),
        ("无效价格", 0.0),
        ("", 0.0),
    ]
    
    for price_text, expected in test_cases:
        result = parse_price(price_text)
        status = "✓" if abs(result - expected) < 0.01 else "✗"
        print(f"{status} '{price_text}' -> {result} (期望: {expected})")
    
    print()


def test_keyword_decomposition():
    """测试关键词分解功能"""
    print("=" * 80)
    print("测试关键词分解功能")
    print("=" * 80)
    
    test_cases = [
        ("满舰饰真子粘土人", ["粘土人", "满舰饰真子"]),
        ("GSC户山香澄手办", ["手办", "GSC户山香澄"]),
        ("初音未来手办粘土人", ["粘土人", "手办", "初音未来"]),
        ("figma Saber", ["figma", "Saber"]),
        ("普通商品", ["普通商品"]),
    ]
    
    for keyword, expected in test_cases:
        result = decompose_keyword(keyword)
        # 排序后比较，因为顺序不重要
        result_sorted = sorted(result)
        expected_sorted = sorted(expected)
        status = "✓" if result_sorted == expected_sorted else "✗"
        print(f"{status} '{keyword}' -> {result} (期望: {expected})")
    
    print(f"\n已知产品类型关键词: {PRODUCT_TYPE_KEYWORDS}")
    print()


def test_scoring_logic():
    """测试评分逻辑"""
    print("=" * 80)
    print("测试评分逻辑")
    print("=" * 80)
    
    # 创建测试商品数据
    test_items = [
        {
            'title': 'GSC 户山香澄 粘土人 手办',
            'price': 12800.0,
            'release_date': '2024年12月',
            'link': 'https://example.com/item1',
            'source': 'HPOI'
        },
        {
            'title': '初音未来 手办',
            'price': 15800.0,
            'release_date': '2024年10月',
            'link': 'https://example.com/item2',
            'source': 'HPOI'
        },
        {
            'title': 'Saber figma 模型',
            'price': 9800.0,
            'release_date': '未知',
            'link': 'https://example.com/item3',
            'source': 'HPOI'
        },
        {
            'title': '完全不相关的商品',
            'price': 5000.0,
            'release_date': '2024年1月',
            'link': 'https://example.com/item4',
            'source': 'HPOI'
        }
    ]
    
    # 测试不同关键词的评分
    test_keywords = [
        ("户山香澄粘土人", [0, 1, 2, 3]),  # 应该匹配第一个商品
        ("初音未来", [0, 1, 2, 3]),  # 应该匹配第二个商品
        ("figma", [0, 1, 2, 3]),  # 应该匹配第三个商品
    ]
    
    for keyword, item_indices in test_keywords:
        print(f"\n关键词: '{keyword}'")
        print("-" * 40)
        
        search_terms = decompose_keyword(keyword)
        print(f"分解后的搜索词: {search_terms}")
        
        for idx in item_indices:
            item = test_items[idx].copy()
            score = calculate_score(item, search_terms)
            item['score'] = score
            print(f"  {idx+1}. '{item['title'][:30]}...' -> 得分: {score}")
    
    print()


def test_currency_conversion():
    """测试货币转换功能"""
    print("=" * 80)
    print("测试货币转换功能")
    print("=" * 80)
    
    test_cases = [
        (12800, 0.0512, 655.36),
        (10000, 0.05, 500.0),
        (0, 0.0512, 0.0),
        (5000, 0.0512, 256.0),
    ]
    
    for jpy_amount, rate, expected in test_cases:
        result = convert_jpy_to_cny(jpy_amount, rate)
        status = "✓" if abs(result - expected) < 0.01 else "✗"
        print(f"{status} {jpy_amount} JPY × {rate} = {result} CNY (期望: {expected})")
    
    print()


def test_mock_search():
    """使用模拟数据进行搜索测试"""
    print("=" * 80)
    print("使用模拟数据进行搜索测试")
    print("=" * 80)
    
    # 模拟数据
    mock_items = [
        {
            'title': 'Good Smile Company 户山香澄 粘土人 手办',
            'price': 12800.0,
            'release_date': '2024年12月',
            'link': 'https://www.hpoi.net/item/12345',
            'source': 'HPOI',
            'raw_price_text': '¥12,800'
        },
        {
            'title': 'Max Factory 初音未来 figma 可动手办',
            'price': 15800.0,
            'release_date': '2024年10月',
            'link': 'https://www.hpoi.net/item/12346',
            'source': 'HPOI',
            'raw_price_text': '¥15,800'
        },
        {
            'title': 'GSC 满舰饰真子 粘土人 手办',
            'price': 13800.0,
            'release_date': '2024年11月',
            'link': 'https://www.hpoi.net/item/12347',
            'source': 'HPOI',
            'raw_price_text': '¥13,800'
        },
        {
            'title': 'Saber Alter 手办 模型',
            'price': 19800.0,
            'release_date': '2024年9月',
            'link': 'https://www.hpoi.net/item/12348',
            'source': 'HPOI',
            'raw_price_text': '¥19,800'
        }
    ]
    
    # 测试搜索函数（模拟版本）
    def mock_fetch_hpoi_items(keyword, max_items, debug=False, context=None):
        """模拟获取HPOI商品"""
        if debug:
            print(f"[mock_fetch_hpoi_items] 模拟搜索: {keyword}, 最多 {max_items} 个商品")
        
        # 简单过滤：如果关键词在标题中，则返回
        filtered_items = []
        for item in mock_items:
            if keyword.lower() in item['title'].lower():
                filtered_items.append(item.copy())
        
        return filtered_items[:max_items]
    
    # 测试不同关键词
    test_keywords = [
        "户山香澄",
        "初音未来",
        "粘土人",
        "手办",
    ]
    
    for keyword in test_keywords:
        print(f"\n搜索关键词: '{keyword}'")
        print("-" * 60)
        
        # 模拟获取商品
        items = mock_fetch_hpoi_items(keyword, 10, debug=True)
        
        if items:
            # 对商品进行评分
            scored_items = score_items(items, keyword, debug=True)
            
            # 按得分排序
            sorted_items = sorted(scored_items, key=lambda x: x['score'], reverse=True)
            
            print(f"找到 {len(sorted_items)} 个商品:")
            for idx, item in enumerate(sorted_items, 1):
                cny_price = convert_jpy_to_cny(item['price'])
                print(f"  {idx}. 【{item['source']}】{item['title'][:40]}...")
                print(f"     价格: ¥{item['price']} JPY (约¥{cny_price} CNY)")
                print(f"     发售日期: {item['release_date']}")
                print(f"     得分: {item['score']}")
                if item.get('link'):
                    print(f"     链接: {item['link'][:50]}...")
                print()
        else:
            print("未找到匹配商品")
    
    print()


def test_actual_search(use_network=False):
    """测试实际网络搜索（可选）"""
    print("=" * 80)
    print("测试实际网络搜索功能")
    print("=" * 80)
    
    if not use_network:
        print("注意：网络搜索已禁用，如需测试请设置 use_network=True")
        print("将使用内置的测试函数进行演示")
        print("-" * 80)
        
        # 使用内置的测试函数
        print("\n1. 测试单个最佳商品搜索:")
        print("-" * 40)
        test_hpoi_search("GSC户山香澄")
        
        print("\n2. 测试前6个商品搜索:")
        print("-" * 40)
        test_hpoi_search_top_6("初音未来")
        
        return
    
    # 实际网络搜索（需要网络连接）
    print("警告：这将进行实际的网络请求，需要网络连接")
    print("测试关键词: 'GSC户山香澄'")
    print("-" * 80)
    
    try:
        # 测试搜索单个最佳商品
        print("\n1. 搜索单个最佳商品:")
        result = search_hpoi("GSC户山香澄", max_items=10, debug=True)
        
        if result:
            print(f"\n✅ 找到最佳商品:")
            print(f"   标题: {result['title']}")
            print(f"   价格: ¥{result['price']} JPY")
            print(f"   发售日期: {result['release_date']}")
            print(f"   得分: {result['score']}")
            print(f"   来源: {result['source']}")
            if result.get('link'):
                print(f"   链接: {result['link']}")
        else:
            print("❌ 未找到匹配商品")
        
        # 测试搜索前6个商品
        print("\n2. 搜索前6个商品:")
        results = search_hpoi_top_n("初音未来", n=6, debug=True)
        
        if results:
            print(f"\n✅ 找到 {len(results)} 个商品:")
            for idx, item in enumerate(results, 1):
                print(f"   {idx}. 【{item['source']}】{item['title'][:50]}...")
                print(f"       价格: ¥{item['price']} JPY")
                print(f"       发售日期: {item['release_date']}")
                print(f"       得分: {item['score']}")
                print()
        else:
            print("❌ 未找到匹配商品")
            
    except Exception as e:
        print(f"❌ 网络搜索失败: {e}")
        print("建议检查网络连接或HPOI网站可访问性")
    
    print()


def create_test_data():
    """创建测试数据文件"""
    print("=" * 80)
    print("创建测试数据文件")
    print("=" * 80)
    
    test_data_dir = Path(__file__).parent / "test_data" / "hpoi"
    test_data_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建测试商品数据
    test_products = [
        {
            "id": "hpoi_001",
            "title": "Good Smile Company 户山香澄 粘土人 手办",
            "price_jpy": 12800.0,
            "price_cny": 655.36,
            "release_date": "2024年12月",
            "category": "粘土人",
            "brand": "GSC",
            "character": "户山香澄",
            "series": "BanG Dream!",
            "source": "HPOI",
            "search_keywords": ["户山香澄", "粘土人", "手办", "GSC", "Good Smile Company"]
        },
        {
            "id": "hpoi_002",
            "title": "Max Factory 初音未来 figma 可动手办",
            "price_jpy": 15800.0,
            "price_cny": 808.96,
            "release_date": "2024年10月",
            "category": "figma",
            "brand": "Max Factory",
            "character": "初音未来",
            "series": "VOCALOID",
            "source": "HPOI",
            "search_keywords": ["初音未来", "figma", "可动手办", "Max Factory"]
        },
        {
            "id": "hpoi_003",
            "title": "GSC 满舰饰真子 粘土人 手办",
            "price_jpy": 13800.0,
            "price_cny": 706.56,
            "release_date": "2024年11月",
            "category": "粘土人",
            "brand": "GSC",
            "character": "满舰饰真子",
            "series": "少女与战车",
            "source": "HPOI",
            "search_keywords": ["满舰饰真子", "粘土人", "手办", "GSC"]
        },
        {
            "id": "hpoi_004",
            "title": "Saber Alter 手办 模型",
            "price_jpy": 19800.0,
            "price_cny": 1013.76,
            "release_date": "2024年9月",
            "category": "手办",
            "brand": "Aniplex",
            "character": "Saber Alter",
            "series": "Fate/stay night",
            "source": "HPOI",
            "search_keywords": ["Saber", "Alter", "手办", "模型", "Fate"]
        },
        {
            "id": "hpoi_005",
            "title": "Nendoroid 雷姆 粘土人 手办",
            "price_jpy": 14800.0,
            "price_cny": 757.76,
            "release_date": "2024年8月",
            "category": "粘土人",
            "brand": "Good Smile Company",
            "character": "雷姆",
            "series": "Re:从零开始的异世界生活",
            "source": "HPOI",
            "search_keywords": ["雷姆", "粘土人", "Nendoroid", "手办", "GSC"]
        }
    ]
    
    # 保存为JSON文件
    test_data_file = test_data_dir / "test_products.json"
    with open(test_data_file, 'w', encoding='utf-8') as f:
        json.dump(test_products, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 测试数据已保存到: {test_data_file}")
    print(f"   包含 {len(test_products)} 个测试商品")
    
    # 创建搜索测试用例
    test_cases = [
        {
            "keyword": "户山香澄粘土人",
            "expected_matches": ["hpoi_001"],
            "description": "精确匹配特定角色和产品类型"
        },
        {
            "keyword": "初音未来",
            "expected_matches": ["hpoi_002"],
            "description": "匹配角色名称"
        },
        {
            "keyword": "粘土人",
            "expected_matches": ["hpoi_001", "hpoi_003", "hpoi_005"],
            "description": "匹配产品类型"
        },
        {
            "keyword": "GSC手办",
            "expected_matches": ["hpoi_001", "hpoi_003", "hpoi_005"],
            "description": "匹配品牌和产品类型"
        },
        {
            "keyword": "Saber",
            "expected_matches": ["hpoi_004"],
            "description": "匹配角色名称（英文）"
        }
    ]
    
    test_cases_file = test_data_dir / "test_search_cases.json"
    with open(test_cases_file, 'w', encoding='utf-8') as f:
        json.dump(test_cases, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 搜索测试用例已保存到: {test_cases_file}")
    print(f"   包含 {len(test_cases)} 个测试用例")
    
    # 创建配置文件测试数据
    config_test_data = {
        "hpoi_url": "https://www.hpoi.net",
        "hpoi_search_url": "https://www.hpoi.net/search",
        "product_type_keywords": PRODUCT_TYPE_KEYWORDS,
        "selectors": {
            "product_item": "div.product-item, li.item-list, div.goods-item, li.media.ibox-content",
            "title": "a.product-name, a.goods-name, span.name, h4.media-heading a",
            "price": "span.price, span.sale-price, em.price",
            "date": "span.date, span.release-date, em.date",
            "link": "a.product-link, a.goods-link, a",
            "source": "span.source, span.seller, em.shop"
        }
    }
    
    config_file = test_data_dir / "config_test.json"
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config_test_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 配置测试数据已保存到: {config_file}")
    print()


def run_all_tests(include_network_test=False):
    """运行所有测试"""
    print("=" * 80)
    print("HPOI搜索功能测试套件")
    print("=" * 80)
    
    # 1. 创建测试数据
    create_test_data()
    
    # 2. 测试价格解析
    test_price_parsing()
    
    # 3. 测试关键词分解
    test_keyword_decomposition()
    
    # 4. 测试评分逻辑
    test_scoring_logic()
    
    # 5. 测试货币转换
    test_currency_conversion()
    
    # 6. 测试模拟搜索
    test_mock_search()
    
    # 7. 测试实际搜索（可选）
    if include_network_test:
        test_actual_search(use_network=True)
    else:
        test_actual_search(use_network=False)
    
    print("=" * 80)
    print("✅ 所有测试完成!")
    print("=" * 80)


def run_specific_test(test_name):
    """运行特定的测试"""
    print("=" * 80)
    print(f"运行特定测试: {test_name}")
    print("=" * 80)
    
    test_functions = {
        "price": test_price_parsing,
        "keyword": test_keyword_decomposition,
        "scoring": test_scoring_logic,
        "currency": test_currency_conversion,
        "mock": test_mock_search,
        "network": lambda: test_actual_search(use_network=True),
        "data": create_test_data,
        "all": lambda: run_all_tests(include_network_test=False)
    }
    
    if test_name in test_functions:
        test_functions[test_name]()
    else:
        print(f"❌ 未知测试: {test_name}")
        print("可用测试: price, keyword, scoring, currency, mock, network, data, all")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="HPOI搜索功能测试")
    parser.add_argument("--test", type=str, default="all", 
                       help="运行特定测试: price, keyword, scoring, currency, mock, network, data, all")
    parser.add_argument("--network", action="store_true", 
                       help="包含网络测试（需要网络连接）")
    
    args = parser.parse_args()
    
    if args.test == "all":
        run_all_tests(include_network_test=args.network)
    else:
        run_specific_test(args.test)
