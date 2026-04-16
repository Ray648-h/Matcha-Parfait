# -*- coding: utf-8 -*-
"""
HPOI搜索功能简单测试脚本

快速测试HPOI搜索功能，不包含复杂的测试套件
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hpoi_search.hpoi_service import (
    test_hpoi_search,
    test_hpoi_search_top_6,
    parse_price,
    decompose_keyword
)


def quick_test():
    """快速测试HPOI搜索功能"""
    print("=" * 80)
    print("HPOI搜索功能快速测试")
    print("=" * 80)
    
    # 测试价格解析
    print("\n1. 测试价格解析:")
    test_prices = ["¥12,800", "12800日元", "无效价格"]
    for price in test_prices:
        result = parse_price(price)
        print(f"  '{price}' -> {result}")
    
    # 测试关键词分解
    print("\n2. 测试关键词分解:")
    test_keywords = ["满舰饰真子粘土人", "GSC户山香澄手办", "初音未来"]
    for keyword in test_keywords:
        result = decompose_keyword(keyword)
        print(f"  '{keyword}' -> {result}")
    
    # 测试搜索功能（使用内置测试函数）
    print("\n3. 测试搜索功能（演示模式）:")
    print("-" * 40)
    
    # 测试单个商品搜索
    print("\n测试单个最佳商品搜索:")
    print("搜索关键词: 'GSC户山香澄'")
    print("-" * 40)
    test_hpoi_search("GSC户山香澄")
    
    # 测试前6个商品搜索
    print("\n测试前6个商品搜索:")
    print("搜索关键词: '初音未来'")
    print("-" * 40)
    test_hpoi_search_top_6("初音未来")
    
    print("=" * 80)
    print("✅ 快速测试完成!")
    print("=" * 80)


def test_with_custom_keyword(keyword):
    """使用自定义关键词测试"""
    print("=" * 80)
    print(f"使用自定义关键词测试: '{keyword}'")
    print("=" * 80)
    
    # 测试关键词分解
    decomposed = decompose_keyword(keyword)
    print(f"关键词分解结果: {decomposed}")
    
    # 测试搜索
    print("\n搜索测试:")
    print("-" * 40)
    test_hpoi_search_top_6(keyword)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="HPOI搜索功能简单测试")
    parser.add_argument("--keyword", type=str, default="", 
                       help="自定义搜索关键词")
    
    args = parser.parse_args()
    
    if args.keyword:
        test_with_custom_keyword(args.keyword)
    else:
        quick_test()