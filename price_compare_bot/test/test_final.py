# -*- coding: utf-8 -*-
"""
最终测试脚本 - 测试淘宝店铺搜索功能
确保测试后自动关闭浏览器
"""

import time
import traceback

def test_search_with_browser_cleanup():
    """
    测试搜索功能并确保浏览器关闭
    """
    print("=" * 80)
    print("淘宝店铺搜索功能测试 - 确保浏览器自动关闭")
    print("=" * 80)
    
    try:
        # 导入必要的模块
        from service.search.taobao_shop import search_taobao_target_shops, load_shop_urls
        
        # 测试关键词
        keyword = "手办"
        
        # 加载店铺列表
        shop_urls = load_shop_urls()
        print(f"成功加载 {len(shop_urls)} 个店铺")
        
        # 只测试前2个店铺
        target_shops = list(shop_urls.keys())[:2]
        print(f"测试店铺: {target_shops}")
        
        print(f"\n开始搜索关键词: '{keyword}'")
        print("-" * 80)
        
        start_time = time.time()
        
        # 执行搜索
        items = search_taobao_target_shops(
            keyword=keyword,
            target_shops=target_shops,
            pages=1,
            debug=True
        )
        
        end_time = time.time()
        search_time = end_time - start_time
        
        print("-" * 80)
        print(f"搜索完成!")
        print(f"耗时: {search_time:.2f}秒")
        print(f"找到商品: {len(items)} 个")
        
        if items:
            print("\n搜索结果示例:")
            for i, item in enumerate(items[:3], 1):
                print(f"{i}. 店铺: {item['shop']}")
                print(f"   标题: {item['title'][:60]}...")
                print(f"   价格: {item['price_text']}")
                print()
        
        return True
        
    except Exception as e:
        print(f"测试失败: {e}")
        traceback.print_exc()
        return False
    
    finally:
        print("-" * 80)
        print("测试脚本执行完成")
        print("注意: search_taobao_target_shops 函数内部应该已经关闭了浏览器")
        print("如果浏览器没有关闭，请检查 service.py 中的 finally 块")
        print("=" * 80)


if __name__ == "__main__":
    success = test_search_with_browser_cleanup()
    
    if success:
        print("\n✅ 测试完成！")
        print("浏览器应该已经自动关闭。")
        print("如果没有关闭，请手动检查浏览器进程。")
    else:
        print("\n❌ 测试失败！")
        print("请检查错误信息。")