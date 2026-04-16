# -*- coding: utf-8 -*-
"""
测试统一搜索结果数据结构的演示
展示如何创建、管理和排序搜索结果
"""

import sys
import os

# 添加路径以便导入模块
# test_unified_models.py 位于 d:\playwright\price_compare_bot\test_unified_models.py
# 我们需要添加 d:\playwright 到 sys.path，因为模块结构是 price_compare_bot.service.search.unified_models
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # d:\playwright
sys.path.insert(0, project_root)

from price_compare_bot.service.search.unified_models import (
    SearchResult, 
    HpoiResult, 
    UnifiedSearchResults,
    sort_results_by_shipping_and_price
)


def create_sample_data():
    """创建示例数据"""
    results = []
    
    # 淘宝示例数据
    results.append(SearchResult(
        platform="taobao",
        title="初音未来粘土人3.0 全新正品 包邮",
        price=450.0,
        shipping_fee=0.0,
        is_free_shipping=True,
        image_url="https://img.alicdn.com/xxxx.jpg",
        detail_url="https://item.taobao.com/item.htm?id=123",
        shop_name="动漫手办专营店",
        score=85
    ))
    
    results.append(SearchResult(
        platform="taobao",
        title="GSC Saber Alter 手办 现货",
        price=800.0,
        shipping_fee=15.0,
        is_free_shipping=False,
        image_url="https://img.alicdn.com/yyyy.jpg",
        detail_url="https://item.taobao.com/item.htm?id=456",
        shop_name="日本手办直邮店",
        score=90
    ))
    
    # 闲鱼示例数据
    results.append(SearchResult(
        platform="xianyu",
        title="二手 初音未来 雪未来 手办 包邮",
        price=350.0,
        shipping_fee=0.0,
        is_free_shipping=True,
        image_url="https://img.goofish.com/zzzz.jpg",
        detail_url="https://www.goofish.com/item/123",
        shop_name="手办爱好者",
        score=75
    ))
    
    results.append(SearchResult(
        platform="xianyu",
        title="GSC 樱初音 粘土人 二手",
        price=280.0,
        shipping_fee=10.0,
        is_free_shipping=False,
        image_url="https://img.goofish.com/aaaa.jpg",
        detail_url="https://www.goofish.com/item/456",
        shop_name="动漫收藏家",
        score=80
    ))
    
    # HPOI示例数据
    hpoi_result = HpoiResult(
        name="GSC 户山香澄 初回特典",
        price=1200.0,
        release_date="2024-12-31",
        image_url="https://hpoi.net/image/123.jpg",
        detail_url="https://hpoi.net/item/123",
        score=95
    )
    results.append(hpoi_result.to_search_result())
    
    # 万美集示例数据（假设）
    results.append(SearchResult(
        platform="wanmeiji",
        title="初音未来 十周年纪念版 包邮",
        price=950.0,
        shipping_fee=0.0,
        is_free_shipping=True,
        image_url="https://wanmeiji.com/image/123.jpg",
        detail_url="https://wanmeiji.com/item/123",
        shop_name="万美集官方店",
        score=88
    ))
    
    return results


def demo_basic_usage():
    """演示基础使用"""
    print("=" * 80)
    print("演示：统一搜索结果数据结构")
    print("=" * 80)
    
    # 创建示例数据
    sample_results = create_sample_data()
    
    print(f"创建了 {len(sample_results)} 个示例结果")
    print("\n原始数据（按添加顺序）：")
    for i, result in enumerate(sample_results, 1):
        print(f"{i}. 【{result.platform}】{result.title[:30]}...")
        print(f"   价格: ¥{result.price}, 运费: ¥{result.shipping_fee}, 总价: ¥{result.total_price()}")
        print(f"   包邮: {'是' if result.is_free_shipping else '否'}")
    
    return sample_results


def demo_sorting():
    """演示排序功能"""
    print("\n" + "=" * 80)
    print("演示：排序功能")
    print("=" * 80)
    
    sample_results = create_sample_data()
    
    # 使用工具函数排序（包邮优先）
    sorted_results = sort_results_by_shipping_and_price(sample_results, free_shipping_first=True)
    
    print("排序后（包邮优先，按总价升序）：")
    for i, result in enumerate(sorted_results, 1):
        free_shipping_marker = "✓" if result.is_free_shipping else " "
        print(f"{i}. [{free_shipping_marker}] 【{result.platform}】{result.title[:30]}...")
        print(f"   总价: ¥{result.total_price():.2f} (商品¥{result.price} + 运费¥{result.shipping_fee})")
    
    print("\n" + "=" * 80)
    print("分组统计：")
    
    # 使用UnifiedSearchResults进行分组
    manager = UnifiedSearchResults()
    manager.results = sample_results
    
    free_shipping = manager.get_free_shipping()
    not_free_shipping = manager.get_not_free_shipping()
    
    print(f"包邮商品: {len(free_shipping)} 个")
    print(f"不包邮商品: {len(not_free_shipping)} 个")
    
    print("\n包邮商品（按总价升序）：")
    free_shipping_sorted = sorted(free_shipping, key=lambda x: x.total_price())
    for i, result in enumerate(free_shipping_sorted, 1):
        print(f"{i}. 【{result.platform}】{result.title[:30]}...")
        print(f"   总价: ¥{result.total_price():.2f}")
    
    print("\n不包邮商品（按总价升序）：")
    not_free_sorted = sorted(not_free_shipping, key=lambda x: x.total_price())
    for i, result in enumerate(not_free_sorted, 1):
        print(f"{i}. 【{result.platform}】{result.title[:30]}...")
        print(f"   总价: ¥{result.total_price():.2f} (商品¥{result.price} + 运费¥{result.shipping_fee})")


def demo_unified_manager():
    """演示UnifiedSearchResults管理器"""
    print("\n" + "=" * 80)
    print("演示：UnifiedSearchResults管理器")
    print("=" * 80)
    
    manager = UnifiedSearchResults()
    
    # 添加原始数据（模拟从不同平台获取的数据）
    # 淘宝数据
    taobao_item = {
        'title': '初音未来 Project DIVA 手办 全新',
        'price_text': '¥680 包邮',
        'image': 'https://img.alicdn.com/taobao.jpg',
        'link': 'https://item.taobao.com/item?id=789',
        'shop': '动漫世界',
        'score': 92
    }
    manager.add_from_taobao(taobao_item)
    
    # 闲鱼数据
    xianyu_item = {
        'title': '二手 GSC 雪未来 粘土人',
        'price_text': '¥320',
        'image': 'https://img.goofish.com/xianyu.jpg',
        'link': 'https://goofish.com/item?id=321',
        'seller': '手办收藏家'
    }
    manager.add_from_xianyu(xianyu_item)
    
    # HPOI数据
    hpoi_item = {
        'title': 'GSC 樱初音 十周年纪念版',
        'price': 1500.0,
        'release_date': '2024-10-31',
        'image_url': 'https://hpoi.net/hpoi.jpg',
        'link': 'https://hpoi.net/item/555',
        'score': 96
    }
    manager.add_from_hpoi(hpoi_item)
    
    print(f"添加了 {len(manager)} 个商品")
    
    # 排序
    manager.sort_by_price(free_shipping_first=True)
    
    print("\n排序后结果：")
    for i, result in enumerate(manager.results, 1):
        free_shipping_marker = "✓" if result.is_free_shipping else " "
        print(f"{i}. [{free_shipping_marker}] 【{result.platform}】{result.title}")
        print(f"   价格: ¥{result.price:.2f}, 运费: ¥{result.shipping_fee:.2f}, 总价: ¥{result.total_price():.2f}")
        if result.shop_name:
            print(f"   店铺: {result.shop_name}")
    
    # 转换为字典列表
    print("\n转换为字典列表（前2个）：")
    dict_list = manager.to_list()[:2]
    for i, item in enumerate(dict_list, 1):
        print(f"{i}. {item}")


def demo_hpoi_compatibility():
    """演示HPOI兼容性"""
    print("\n" + "=" * 80)
    print("演示：HPOI兼容性")
    print("=" * 80)
    
    # 创建HPOI结果
    hpoi_result = HpoiResult(
        name="GSC 初音未来 16周年纪念版",
        price=1800.0,
        release_date="2024-08-31",
        image_url="https://hpoi.net/image/888.jpg",
        detail_url="https://hpoi.net/item/888",
        score=98
    )
    
    print("HPOI原始结果：")
    print(f"名称: {hpoi_result.name}")
    print(f"价格: ¥{hpoi_result.price}")
    print(f"发售日期: {hpoi_result.release_date}")
    
    # 转换为统一格式
    unified_result = hpoi_result.to_search_result()
    
    print("\n转换为统一格式：")
    print(f"平台: {unified_result.platform}")
    print(f"标题: {unified_result.title}")
    print(f"价格: ¥{unified_result.price}")
    print(f"是否包邮: {unified_result.is_free_shipping}")
    print(f"运费: ¥{unified_result.shipping_fee}")
    print(f"总价: ¥{unified_result.total_price()}")


def main():
    """主函数"""
    print("统一搜索结果数据结构演示")
    print("=" * 80)
    
    # 演示基础使用
    demo_basic_usage()
    
    # 演示排序功能
    demo_sorting()
    
    # 演示统一管理器
    demo_unified_manager()
    
    # 演示HPOI兼容性
    demo_hpoi_compatibility()
    
    print("\n" + "=" * 80)
    print("演示完成！")
    print("=" * 80)
    print("\n核心特性总结：")
    print("1. ✅ 统一SearchResult数据结构，支持xianyu/taobao/wanmeiji/hpoi平台")
    print("2. ✅ HPOI特殊结构（HpoiResult）兼容性")
    print("3. ✅ 支持包邮状态识别（is_free_shipping）")
    print("4. ✅ 按包邮状态和价格排序（包邮优先，按总价升序）")
    print("5. ✅ 统一管理器（UnifiedSearchResults）简化数据处理")
    print("6. ✅ 便捷的价格提取和总价计算")


if __name__ == "__main__":
    main()