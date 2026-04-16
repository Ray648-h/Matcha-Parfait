# -*- coding: utf-8 -*-
"""
直接测试淘宝店铺搜索功能
绕过登录检测，直接测试搜索功能
"""

import time
import traceback
from config.context import BrowserManager
from service.login_service import LoginService
from config.settings import TAOBAO_URL
from service.search.taobao_shop.searcher import search_shops
from service.search.taobao_shop.shop_loader import load_shop_urls


def test_direct_search():
    """
    直接测试搜索功能
    """
    print("=" * 80)
    print("直接测试淘宝店铺搜索功能")
    print("=" * 80)
    
    # 测试关键词
    keyword = "初音未来小鸟手办"
    
    # 加载店铺列表
    try:
        shop_urls = load_shop_urls()
        print(f"成功加载店铺列表，共 {len(shop_urls)} 个店铺")
        
        # 只测试前2个店铺
        selected_shops = list(shop_urls.keys())[:2]
        print(f"测试店铺: {selected_shops}")
    except Exception as e:
        print(f"加载店铺列表失败: {e}")
        selected_shops = ["gsc", "animate旗舰店"]
        print(f"使用默认店铺: {selected_shops}")
    
    print(f"\n测试关键词: '{keyword}'")
    print("-" * 80)
    
    # 启动浏览器
    print("启动浏览器...")
    manager = BrowserManager()
    context = None
    page = None
    
    try:
        # 启动淘宝浏览器上下文
        context = manager.launch_taobao()
        print("浏览器启动成功")
        
        # 创建登录服务（但跳过登录检测）
        login_service = LoginService(context)
        
        print("\n访问淘宝首页...")
        # 直接访问淘宝，不进行登录检测
        page = login_service.login(TAOBAO_URL, "淘宝")
        print("页面加载完成")
        
        # 等待页面稳定
        page.wait_for_timeout(2000)
        
        print("\n开始搜索...")
        start_time = time.time()
        
        # 直接调用搜索函数
        items = search_shops(
            keyword=keyword,
            selected_shops=selected_shops,
            page=page,
            debug=True
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
            for i, item in enumerate(items[:5], 1):  # 只显示前5个结果
                title_preview = item['title'][:50] + "..." if len(item['title']) > 50 else item['title']
                print(f"{i}. 店铺: {item['shop']}")
                print(f"   标题: {title_preview}")
                print(f"   价格: {item.get('price', item.get('price_text', 'N/A'))}")
                if 'link' in item:
                    link_preview = item['link'][:70] + "..." if len(item['link']) > 70 else item['link']
                    print(f"   链接: {link_preview}")
                print()
            
            if len(items) > 5:
                print(f"... 还有 {len(items) - 5} 个结果未显示")
        else:
            print("未找到商品")
            
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        traceback.print_exc()
    
    finally:
        print("-" * 80)
        print("清理资源...")
        
        # 确保关闭页面
        if page:
            try:
                page.close()
                print("页面已关闭")
            except:
                pass
        
        # 确保关闭浏览器上下文
        if context:
            try:
                context.close()
                print("浏览器上下文已关闭")
            except:
                pass
        
        print("测试完成，浏览器已关闭")
        print("=" * 80)


if __name__ == "__main__":
    test_direct_search()