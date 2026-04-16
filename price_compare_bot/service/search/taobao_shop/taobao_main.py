# -*- coding: utf-8 -*-
"""
淘宝搜索主模块 - 整合所有功能
直接使用现有文件中的函数，提供统一的接口
"""

import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json

# 导入现有模块的函数
from .service import (
    resolve_target_shop_urls,
    search_taobao_target_shops,
    _normalize_text,
    _normalize_shop_url,
    _build_shop_search_url
)

from .direct_product_search import (
    search_and_filter_products as direct_search,
    _load_target_shops_from_file,
    _is_target_shop as is_target_shop_func
)

from .new_search import (
    search_shops_directly
)

from .taobao_scorer import (
    calculate_taobao_score,
    score_taobao_items,
    process_taobao_items_with_scoring
)

from .shop_loader import (
    load_shop_urls,
    get_all_shop_names
)

from .parser import parse_shop_items
from .sorter import sort_by_price


# ============================================================================
# 数据类定义
# ============================================================================

@dataclass
class Product:
    """商品数据类"""
    title: str
    shop: str
    price_text: str
    link: str
    image: str
    score: int = 0
    target_shop: str = ""
    shop_url: str = ""
    index: int = 0
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "title": self.title,
            "shop": self.shop,
            "price_text": self.price_text,
            "link": self.link,
            "image": self.image,
            "score": self.score,
            "target_shop": self.target_shop,
            "shop_url": self.shop_url,
            "index": self.index
        }


@dataclass
class SearchResult:
    """搜索结果数据类"""
    keyword: str
    products: List[Product]
    total_count: int
    filtered_count: int
    search_time: float
    success: bool
    error_message: str = ""
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "keyword": self.keyword,
            "products": [p.to_dict() for p in self.products],
            "total_count": self.total_count,
            "filtered_count": self.filtered_count,
            "search_time": self.search_time,
            "success": self.success,
            "error_message": self.error_message
        }
    
    def to_json(self, indent: int = 2) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


# ============================================================================
# 统一搜索接口
# ============================================================================

class TaobaoSearch:
    """淘宝搜索统一接口"""
    
    def __init__(self, shop_file_path: str = "price_compare_bot/taobao_shop_urls.txt"):
        self.shop_file_path = shop_file_path
        self.target_shops = {}
        self._load_target_shops()
    
    def _load_target_shops(self):
        """加载目标店铺"""
        self.target_shops = _load_target_shops_from_file(self.shop_file_path)
    
    def search_direct(self, keyword: str, debug: bool = False, context=None) -> SearchResult:
        """
        直接搜索商品（推荐使用）
        流程：直接搜索商品 -> 提取所有商品 -> 筛选目标店铺 -> 评分排序
        """
        start_time = time.time()
        
        try:
            # 使用direct_product_search模块
            items = direct_search(
                keyword=keyword,
                shop_file_path=self.shop_file_path,
                debug=debug,
                context=context
            )
            
            # 转换为Product对象
            products = []
            for item in items:
                product = Product(
                    title=item.get('title', ''),
                    shop=item.get('shop', '未知店铺'),
                    price_text=item.get('price_text', 'N/A'),
                    link=item.get('link', ''),
                    image=item.get('image', ''),
                    score=item.get('score', 0),
                    target_shop=item.get('target_shop', ''),
                    shop_url=item.get('shop_url', ''),
                    index=item.get('index', 0)
                )
                products.append(product)
            
            # 按得分排序
            products.sort(key=lambda x: x.score, reverse=True)
            
            search_time = time.time() - start_time
            
            return SearchResult(
                keyword=keyword,
                products=products,
                total_count=len(items),  # 注意：direct_search返回的是筛选后的结果
                filtered_count=len(products),
                search_time=search_time,
                success=True
            )
            
        except Exception as e:
            search_time = time.time() - start_time
            return SearchResult(
                keyword=keyword,
                products=[],
                total_count=0,
                filtered_count=0,
                search_time=search_time,
                success=False,
                error_message=str(e)
            )
    
    def search_in_shops(self, keyword: str, debug: bool = False, context=None) -> SearchResult:
        """
        在目标店铺内搜索商品
        流程：遍历目标店铺 -> 在每个店铺内搜索商品 -> 合并结果 -> 评分排序
        """
        start_time = time.time()
        
        try:
            # 使用new_search模块
            items = search_shops_directly(
                keyword=keyword,
                shop_file_path=self.shop_file_path,
                debug=debug,
                context=context
            )
            
            # 转换为Product对象
            products = []
            for item in items:
                product = Product(
                    title=item.get('title', ''),
                    shop=item.get('shop', '未知店铺'),
                    price_text=item.get('price_text', 'N/A'),
                    link=item.get('link', ''),
                    image=item.get('image', ''),
                    score=item.get('score', 0),
                    target_shop=item.get('target_shop', ''),
                    shop_url=item.get('shop_url', ''),
                    index=item.get('index', 0)
                )
                products.append(product)
            
            # 按得分排序
            products.sort(key=lambda x: x.score, reverse=True)
            
            search_time = time.time() - start_time
            
            return SearchResult(
                keyword=keyword,
                products=products,
                total_count=len(items),
                filtered_count=len(products),
                search_time=search_time,
                success=True
            )
            
        except Exception as e:
            search_time = time.time() - start_time
            return SearchResult(
                keyword=keyword,
                products=[],
                total_count=0,
                filtered_count=0,
                search_time=search_time,
                success=False,
                error_message=str(e)
            )
    
    def search_comprehensive(self, keyword: str, debug: bool = False, context=None) -> SearchResult:
        """
        综合搜索（推荐使用）
        流程：直接搜索 + 店铺内搜索 -> 合并去重 -> 评分排序
        """
        start_time = time.time()
        
        try:
            # 同时进行两种搜索
            direct_result = self.search_direct(keyword, debug, context)
            shop_result = self.search_in_shops(keyword, debug, context)
            
            # 合并结果，去重（基于标题和店铺）
            all_products = {}
            for product in direct_result.products + shop_result.products:
                key = f"{product.title}_{product.shop}"
                if key not in all_products or product.score > all_products[key].score:
                    all_products[key] = product
            
            products = list(all_products.values())
            
            # 按得分排序
            products.sort(key=lambda x: x.score, reverse=True)
            
            search_time = time.time() - start_time
            
            return SearchResult(
                keyword=keyword,
                products=products,
                total_count=direct_result.total_count + shop_result.total_count,
                filtered_count=len(products),
                search_time=search_time,
                success=True
            )
            
        except Exception as e:
            search_time = time.time() - start_time
            return SearchResult(
                keyword=keyword,
                products=[],
                total_count=0,
                filtered_count=0,
                search_time=search_time,
                success=False,
                error_message=str(e)
            )
    
    def get_target_shops(self) -> Dict[str, str]:
        """获取目标店铺列表"""
        return self.target_shops
    
    def add_target_shop(self, shop_name: str, shop_url: str = ""):
        """添加目标店铺"""
        self.target_shops[shop_name] = shop_url
    
    def remove_target_shop(self, shop_name: str):
        """移除目标店铺"""
        if shop_name in self.target_shops:
            del self.target_shops[shop_name]


# ============================================================================
# 工具函数
# ============================================================================

def create_search_result(keyword: str, items: List[Dict], search_time: float) -> SearchResult:
    """从原始商品列表创建SearchResult"""
    products = []
    for item in items:
        product = Product(
            title=item.get('title', ''),
            shop=item.get('shop', '未知店铺'),
            price_text=item.get('price_text', 'N/A'),
            link=item.get('link', ''),
            image=item.get('image', ''),
            score=item.get('score', 0),
            target_shop=item.get('target_shop', ''),
            shop_url=item.get('shop_url', ''),
            index=item.get('index', 0)
        )
        products.append(product)
    
    # 按得分排序
    products.sort(key=lambda x: x.score, reverse=True)
    
    return SearchResult(
        keyword=keyword,
        products=products,
        total_count=len(items),
        filtered_count=len(products),
        search_time=search_time,
        success=True
    )


def print_search_result(result: SearchResult, max_display: int = 10):
    """打印搜索结果"""
    print("=" * 80)
    print(f"搜索关键词: {result.keyword}")
    print(f"搜索状态: {'成功' if result.success else '失败'}")
    if not result.success:
        print(f"错误信息: {result.error_message}")
        return
    
    print(f"搜索耗时: {result.search_time:.2f}秒")
    print(f"找到商品总数: {result.total_count}")
    print(f"筛选后商品数量: {result.filtered_count}")
    print("-" * 80)
    
    if result.products:
        print(f"\n前 {min(max_display, len(result.products))} 个商品结果:")
        for i, product in enumerate(result.products[:max_display], 1):
            title_preview = product.title[:50] + "..." if len(product.title) > 50 else product.title
            print(f"{i}. [{product.score}分] {title_preview}")
            print(f"   店铺: {product.shop}", end="")
            if product.target_shop:
                print(f" (匹配: {product.target_shop})")
            else:
                print()
            print(f"   价格: {product.price_text}")
            if product.link:
                link_preview = product.link[:60] + "..." if len(product.link) > 60 else product.link
                print(f"   链接: {link_preview}")
            print()
        
        if len(result.products) > max_display:
            print(f"... 还有 {len(result.products) - max_display} 个结果未显示")
    else:
        print("未找到符合条件的商品")
    
    print("=" * 80)


# ============================================================================
# 主函数（用于测试）
# ============================================================================

def main():
    """主函数 - 测试淘宝搜索功能"""
    print("淘宝搜索整合模块测试")
    print("=" * 80)
    
    # 创建搜索器
    searcher = TaobaoSearch()
    
    # 显示目标店铺
    target_shops = searcher.get_target_shops()
    print(f"加载了 {len(target_shops)} 个目标店铺:")
    for i, (shop, url) in enumerate(list(target_shops.items())[:5], 1):
        print(f"  {i}. {shop}: {url[:50]}..." if url else f"  {i}. {shop}")
    if len(target_shops) > 5:
        print(f"  ... 还有 {len(target_shops) - 5} 个店铺")
    
    print("\n" + "-" * 80)
    
    # 测试搜索
    test_keywords = [
        "初音未来粘土人3.0",
        "GSC户山香澄",
        "手办 初音未来"
    ]
    
    for keyword in test_keywords[:1]:  # 只测试第一个关键词
        print(f"\n测试搜索: {keyword}")
        print("-" * 40)
        
        # 测试直接搜索
        print("1. 直接搜索:")
        result = searcher.search_direct(keyword, debug=True)
        print_search_result(result, max_display=3)
        
        # 测试店铺内搜索
        print("\n2. 店铺内搜索:")
        result = searcher.search_in_shops(keyword, debug=True)
        print_search_result(result, max_display=3)
        
        # 测试综合搜索
        print("\n3. 综合搜索:")
        result = searcher.search_comprehensive(keyword, debug=True)
        print_search_result(result, max_display=5)
    
    print("\n测试完成!")


if __name__ == "__main__":
    main()