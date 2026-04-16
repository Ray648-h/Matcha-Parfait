# -*- coding: utf-8 -*-
"""
淘宝店铺搜索测试脚本 - 增强版
支持多种测试场景
"""

import time
from service.search.taobao_shop import search_taobao_target_shops, load_shop_urls


def test_basic_search():
    """
    基础搜索测试 - 测试search_taobao_target_shops函数
    """
    print("=" * 80)
    print("测试场景1: 基础搜索测试")
    print("=" * 80)
    
    # 测试关键词
    keyword = "手办"
    
    # 目标店铺列表（从taobao_shop_urls.txt中获取）
    shop_urls = load_shop_urls()
    target_shops = list(shop_urls.keys())[:5]  # 只测试前5个店铺，加快测试速度
    
    print(f"测试关键词: {keyword}")
    print(f"测试店铺数量: {len(target_shops)}")
    print(f"测试店铺列表: {target_shops}")
    
    # 搜索页数
    pages = 1
    
    # 启用调试模式
    debug = True
    
    start_time = time.time()
    
    try:
        # 执行搜索
        items = search_taobao_target_shops(
            keyword=keyword,
            target_shops=target_shops,
            pages=pages,
            debug=debug
        )
        
        end_time = time.time()
        search_time = end_time - start_time
        
        print(f"\n搜索完成，耗时: {search_time:.2f}秒")
        print(f"共找到 {len(items)} 个商品")
        
        # 打印搜索结果摘要
        if items:
            print("\n搜索结果摘要:")
            for i, item in enumerate(items[:10], 1):  # 只显示前10个结果
                title_preview = item['title'][:50] + "..." if len(item['title']) > 50 else item['title']
                print(f"{i}. 店铺: {item['shop']}")
                print(f"   标题: {title_preview}")
                print(f"   价格: {item['price_text']}")
            
            if len(items) > 10:
                print(f"... 还有 {len(items) - 10} 个结果未显示")
        else:
            print("未找到商品")
            
    except Exception as e:
        print(f"搜索过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


def test_multiple_keywords():
    """
    多关键词测试
    """
    print("\n" + "=" * 80)
    print("测试场景2: 多关键词测试")
    print("=" * 80)
    
    # 多个测试关键词
    test_keywords = ["手办", "模型", "Figure"]
    
    # 使用少量店铺进行测试
    shop_urls = load_shop_urls()
    target_shops = list(shop_urls.keys())[:3]
    
    for keyword in test_keywords:
        print(f"\n测试关键词: '{keyword}'")
        print(f"测试店铺: {target_shops}")
        
        start_time = time.time()
        
        try:
            items = search_taobao_target_shops(
                keyword=keyword,
                target_shops=target_shops,
                pages=1,
                debug=False  # 关闭详细调试信息，只显示结果
            )
            
            end_time = time.time()
            search_time = end_time - start_time
            
            print(f"  找到 {len(items)} 个商品，耗时: {search_time:.2f}秒")
            
            # 显示每个店铺的结果数量
            shop_counts = {}
            for item in items:
                shop = item['shop']
                shop_counts[shop] = shop_counts.get(shop, 0) + 1
            
            for shop, count in shop_counts.items():
                print(f"    {shop}: {count} 个商品")
                
        except Exception as e:
            print(f"  搜索失败: {e}")


def test_performance():
    """
    性能测试 - 测试不同页数的搜索
    """
    print("\n" + "=" * 80)
    print("测试场景3: 性能测试（不同页数）")
    print("=" * 80)
    
    keyword = "手办"
    shop_urls = load_shop_urls()
    target_shops = list(shop_urls.keys())[:2]  # 只测试2个店铺
    
    print(f"测试关键词: {keyword}")
    print(f"测试店铺: {target_shops}")
    
    for pages in [1, 2, 3]:
        print(f"\n测试页数: {pages}")
        
        start_time = time.time()
        
        try:
            items = search_taobao_target_shops(
                keyword=keyword,
                target_shops=target_shops,
                pages=pages,
                debug=False
            )
            
            end_time = time.time()
            search_time = end_time - start_time
            
            print(f"  找到 {len(items)} 个商品")
            print(f"  总耗时: {search_time:.2f}秒")
            print(f"  平均每页耗时: {search_time/pages:.2f}秒")
            
        except Exception as e:
            print(f"  搜索失败: {e}")


def main():
    """
    主测试函数
    """
    print("淘宝店铺搜索功能测试")
    print("=" * 80)
    
    # 测试基础搜索功能
    test_basic_search()
    
    # 测试多关键词搜索
    test_multiple_keywords()
    
    # 测试性能
    test_performance()
    
    print("\n" + "=" * 80)
    print("所有测试完成！")
    print("=" * 80)


if __name__ == "__main__":
    main()
