# -*- coding: utf-8 -*-
"""
简化版淘宝店铺搜索测试
专注于测试search_taobao_target_shops函数，确保测试后自动关闭浏览器
"""

import time
import traceback
from service.search.taobao_shop import search_taobao_target_shops, load_shop_urls


def test_simple_search():
    """
    简化搜索测试
    """
    print("=" * 80)
    print("简化版淘宝店铺搜索测试")
    print("=" * 80)
    
    # 测试关键词
    keyword = "初音未来小鸟手办"
    
    # 从taobao_shop_urls.txt中获取店铺列表
    try:
        shop_urls = load_shop_urls()
        print(f"成功加载店铺列表，共 {len(shop_urls)} 个店铺")
        
        # 只测试前3个店铺，加快测试速度
        target_shops = list(shop_urls.keys())[:3]
        print(f"测试店铺: {target_shops}")
    except Exception as e:
        print(f"加载店铺列表失败: {e}")
        # 使用硬编码的店铺列表作为备选
        target_shops = ["gsc", "hpoi正版手办店", "万代官方旗舰店"]
        print(f"使用备选店铺列表: {target_shops}")
    
    # 搜索页数
    pages = 1
    
    # 启用调试模式
    debug = True
    
    print(f"\n开始搜索，关键词: '{keyword}'")
    print(f"搜索页数: {pages}")
    print(f"调试模式: {debug}")
    print("-" * 80)
    
    start_time = time.time()
    
    try:
        # 执行搜索
        print("调用 search_taobao_target_shops 函数...")
        items = search_taobao_target_shops(
            keyword=keyword,
            target_shops=target_shops,
            pages=pages,
            debug=debug
        )
        
        end_time = time.time()
        search_time = end_time - start_time
        
        print("-" * 80)
        print(f"搜索完成!")
        print(f"总耗时: {search_time:.2f}秒")
        print(f"找到商品数量: {len(items)}")
        
        # 打印搜索结果
        if items:
            print("\n搜索结果:")
            for i, item in enumerate(items, 1):
                title_preview = item['title'][:60] + "..." if len(item['title']) > 60 else item['title']
                print(f"{i}. 店铺: {item['shop']}")
                print(f"   标题: {title_preview}")
                print(f"   价格: {item['price_text']}")
                print(f"   链接: {item['link'][:80]}..." if len(item['link']) > 80 else f"   链接: {item['link']}")
                print()
        else:
            print("未找到商品")
            
    except Exception as e:
        print(f"搜索过程中出现错误: {e}")
        traceback.print_exc()
    
    finally:
        print("-" * 80)
        print("测试完成，浏览器应该已经自动关闭")
        print("=" * 80)


if __name__ == "__main__":
    test_simple_search()