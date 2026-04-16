#!/usr/bin/env python3
"""
HPOI搜索功能新测试脚本
包含前5个商品功能和绝对链接
"""

import sys
import os
import json
from pathlib import Path

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

try:
    from hpoi_search.hpoi_service import (
        search_hpoi_top_5,
        test_hpoi_search_top_5,
        search_hpoi_top_n,
        test_hpoi_search_top_6,
        parse_price,
        decompose_keyword
    )
except ImportError:
    # 备选导入方式
    sys.path.insert(0, os.path.join(project_root, 'price_compare_bot'))
    from hpoi_search.hpoi_service import (
        search_hpoi_top_5,
        test_hpoi_search_top_5,
        search_hpoi_top_n,
        test_hpoi_search_top_6,
        parse_price,
        decompose_keyword
    )


def test_price_parsing():
    """测试价格解析功能"""
    print("=" * 80)
    print("测试价格解析功能")
    print("=" * 80)
    
    test_cases = [
        ('¥12,800', 12800.0),
        ('￥12,800', 12800.0),
        ('12800日元', 12800.0),
        ('12,800JPY', 12800.0),
        ('12800元', 12800.0),
        ('$128.00', 128.0),
        ('128.00', 128.0),
        ('12,800.50', 12800.5),
        ('无效价格', 0.0),
        ('', 0.0),
    ]
    
    for price_str, expected in test_cases:
        result = parse_price(price_str)
        status = '✓' if abs(result - expected) < 0.01 else '✗'
        print(f"{status} '{price_str}' -> {result} (期望: {expected})")
    
    print()


def test_keyword_decomposition():
    """测试关键词分解功能"""
    print("=" * 80)
    print("测试关键词分解功能")
    print("=" * 80)
    
    test_cases = [
        ('满舰饰真子粘土人', ['粘土人', '满舰饰真子']),
        ('GSC户山香澄手办', ['手办', 'gsc', 'GSC户山香澄']),
        ('初音未来', ['初音未来']),
        ('初音未来十面埋伏', ['初音未来十面埋伏']),
        ('GSC 户山香澄 粘土人', ['粘土人', 'gsc', 'GSC 户山香澄']),
    ]
    
    for keyword, expected in test_cases:
        result = decompose_keyword(keyword)
        status = '✓' if result == expected else '✗'
        print(f"{status} '{keyword}' -> {result} (期望: {expected})")
    
    print()


def test_search_top_5(keyword: str = "初音未来十面埋伏"):
    """测试前5个商品搜索功能"""
    print("=" * 80)
    print(f"测试前5个商品搜索: '{keyword}'")
    print("=" * 80)
    
    results = search_hpoi_top_5(keyword, debug=True)
    
    if results:
        print(f"\n✅ 搜索完成，共获得 {len(results)} 个商品")
        print("-" * 80)
        
        for idx, item in enumerate(results, 1):
            print(f"{idx}. 【{item['source']}】{item['title']}")
            print(f"   日元价格: ¥{item.get('price', '未知')}")
            print(f"   人民币价格: ¥{item.get('price_cny', '未知')}")
            print(f"   发售日期: {item.get('release_date', '未知')}")
            print(f"   得分: {item.get('score', 0)}")
            if item.get('link'):
                print(f"   链接: {item['link']}")
                # 验证链接是否为绝对链接
                if item['link'].startswith('http'):
                    print(f"   ✅ 绝对链接验证通过")
                else:
                    print(f"   ⚠️  链接不是绝对链接: {item['link']}")
            if item.get('image_url'):
                print(f"   图片: {item['image_url'][:80]}...")
            print()
    else:
        print("❌ 未找到匹配商品")
    
    print("=" * 80)
    return results


def create_test_data():
    """创建测试数据"""
    print("=" * 80)
    print("创建测试数据")
    print("=" * 80)
    
    # 创建测试数据目录
    test_data_dir = Path(__file__).parent / "test_data" / "hpoi_new"
    test_data_dir.mkdir(parents=True, exist_ok=True)
    
    # 测试商品数据
    test_products = [
        {
            "id": "hpoi_new_001",
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
            "id": "hpoi_new_002",
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
            "id": "hpoi_new_003",
            "title": "Alter 雪之下雪乃 1/7 比例手办",
            "price_jpy": 25800.0,
            "price_cny": 1320.96,
            "release_date": "2025年3月",
            "category": "比例手办",
            "brand": "Alter",
            "character": "雪之下雪乃",
            "series": "我的青春恋爱物语果然有问题",
            "source": "HPOI",
            "search_keywords": ["雪之下雪乃", "1/7", "比例手办", "Alter"]
        },
        {
            "id": "hpoi_new_004",
            "title": "Kotobukiya 雷姆 生日纪念版 手办",
            "price_jpy": 19800.0,
            "price_cny": 1013.76,
            "release_date": "2024年11月",
            "category": "生日纪念版",
            "brand": "Kotobukiya",
            "character": "雷姆",
            "series": "Re:从零开始的异世界生活",
            "source": "HPOI",
            "search_keywords": ["雷姆", "生日纪念", "手办", "Kotobukiya"]
        },
        {
            "id": "hpoi_new_005",
            "title": "FREEing  Saber 兔女郎 1/4 比例手办",
            "price_jpy": 39800.0,
            "price_cny": 2037.76,
            "release_date": "2025年1月",
            "category": "兔女郎手办",
            "brand": "FREEing",
            "character": "Saber",
            "series": "Fate/stay night",
            "source": "HPOI",
            "search_keywords": ["Saber", "兔女郎", "1/4", "比例手办", "FREEing"]
        }
    ]
    
    # 搜索测试用例
    test_search_cases = [
        {
            "keyword": "户山香澄粘土人",
            "expected_matches": ["hpoi_new_001"],
            "description": "精确匹配特定角色和产品类型"
        },
        {
            "keyword": "初音未来",
            "expected_matches": ["hpoi_new_002"],
            "description": "匹配角色名称"
        },
        {
            "keyword": "雪之下雪乃手办",
            "expected_matches": ["hpoi_new_003"],
            "description": "匹配角色和产品类型"
        },
        {
            "keyword": "雷姆生日纪念",
            "expected_matches": ["hpoi_new_004"],
            "description": "匹配角色和特殊版本"
        },
        {
            "keyword": "Saber兔女郎",
            "expected_matches": ["hpoi_new_005"],
            "description": "匹配角色和特殊造型"
        }
    ]
    
    # 保存测试数据
    products_file = test_data_dir / "test_products.json"
    with open(products_file, 'w', encoding='utf-8') as f:
        json.dump(test_products, f, ensure_ascii=False, indent=2)
    
    search_cases_file = test_data_dir / "test_search_cases.json"
    with open(search_cases_file, 'w', encoding='utf-8') as f:
        json.dump(test_search_cases, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 测试商品数据已保存到: {products_file}")
    print(f"   包含 {len(test_products)} 个测试商品")
    print(f"✅ 搜索测试用例已保存到: {search_cases_file}")
    print(f"   包含 {len(test_search_cases)} 个测试用例")
    print()


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='HPOI搜索功能新测试脚本')
    parser.add_argument('--test', choices=['price', 'keyword', 'search', 'data', 'all'], 
                       default='all', help='运行特定测试')
    parser.add_argument('--keyword', type=str, default='初音未来十面埋伏',
                       help='搜索关键词')
    parser.add_argument('--network', action='store_true',
                       help='启用网络测试（实际搜索）')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("HPOI搜索功能新测试套件")
    print("=" * 80)
    
    if args.test in ['price', 'all']:
        test_price_parsing()
    
    if args.test in ['keyword', 'all']:
        test_keyword_decomposition()
    
    if args.test in ['search', 'all']:
        if args.network:
            test_search_top_5(args.keyword)
        else:
            print("\n⚠️  网络测试已禁用，使用 --network 参数启用实际搜索测试")
            print("   使用模拟数据测试...")
            # 这里可以添加模拟数据测试
    
    if args.test in ['data', 'all']:
        create_test_data()
    
    print("=" * 80)
    print("✅ 测试完成!")
    print("=" * 80)


if __name__ == "__main__":
    main()