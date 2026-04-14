# -*- coding: utf-8 -*-
"""
淘宝店铺搜索测试脚本
"""

import time
from service.search.taobao_shop import search_taobao_target_shops


def test_taobao_search():
    """
    测试淘宝店铺搜索功能
    """
    # 测试关键词
    keyword = "手办"
    
    # 目标店铺列表
    target_shops = [
        "gsc",
        "animate旗舰店",
        "万代官方旗舰店",
        "塑唐玩具",
        "三月兽官方旗舰店",
        "bilibiligoods官方旗舰店",
        "猫受屋",
        "Aniplex 官方店",
        "52TOYS 旗舰店",
        "Hpoi 正版手办店",
        "模玩熊",
        "鹤屋通贩"
    ]
    
    # 搜索页数
    pages = 1
    
    # 启用调试模式
    debug = True
    
    print("\n开始搜索淘宝店铺商品，关键词: {}".format(keyword))
    print("目标店铺数量: {}".format(len(target_shops)))
    print("搜索页数: {}".format(pages))
    print("=" * 80)
    
    start_time = time.time()
    
    # 执行搜索
    items = search_taobao_target_shops(
        keyword=keyword,
        target_shops=target_shops,
        pages=pages,
        debug=debug
    )
    
    end_time = time.time()
    search_time = end_time - start_time
    
    print("=" * 80)
    print("搜索完成，耗时: {:.2f}秒".format(search_time))
    print("共找到 {} 个商品".format(len(items)))
    print("=" * 80)
    
    # 打印搜索结果
    if items:
        print("搜索结果:")
        for i, item in enumerate(items, 1):
            print("\n{}. 店铺: {}".format(i, item['shop']))
            print("   标题: {}".format(item['title']))
            print("   价格: {}".format(item['price_text']))
            print("   链接: {}".format(item['link']))
    else:
        print("未找到商品")


if __name__ == "__main__":
    test_taobao_search()