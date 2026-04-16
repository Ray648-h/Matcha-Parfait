# -*- coding: utf-8 -*-
"""
统一搜索数据结构定义
用于跨平台（闲鱼、淘宝、万美集、HPOI）的搜索结果统一化
"""

from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime


@dataclass
class SearchResult:
    """统一搜索结果数据结构"""
    platform: str          # 平台：xianyu / taobao / wanmeiji / hpoi
    title: str             # 商品名称
    price: float           # 商品价格
    shipping_fee: float    # 运费（0=包邮）
    is_free_shipping: bool # 是否包邮
    image_url: str         # 图片
    detail_url: str        # 跳转链接
    # 可选字段
    shop_name: str = ""    # 店铺/卖家名称
    release_date: str = "" # 发售日期（HPOI专用）
    score: int = 0         # 匹配得分
    raw_data: dict = None  # 原始数据
    
    def __post_init__(self):
        """初始化后处理"""
        if self.raw_data is None:
            self.raw_data = {}
        
        # 确保is_free_shipping与shipping_fee一致
        if self.shipping_fee == 0:
            self.is_free_shipping = True
        else:
            self.is_free_shipping = False
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "platform": self.platform,
            "title": self.title,
            "price": self.price,
            "shipping_fee": self.shipping_fee,
            "is_free_shipping": self.is_free_shipping,
            "image_url": self.image_url,
            "detail_url": self.detail_url,
            "shop_name": self.shop_name,
            "release_date": self.release_date,
            "score": self.score
        }
    
    def total_price(self) -> float:
        """计算总价（商品价格+运费）"""
        return self.price + self.shipping_fee


@dataclass
class HpoiResult:
    """HPOI特殊结构（兼容性）"""
    name: str              # 商品名称
    price: float           # 商品价格
    release_date: str      # 发售日期
    image_url: str         # 图片
    detail_url: str = ""   # 跳转链接
    score: int = 0         # 匹配得分
    source: str = "hpoi"   # 来源
    
    def to_search_result(self) -> SearchResult:
        """转换为统一的SearchResult"""
        return SearchResult(
            platform="hpoi",
            title=self.name,
            price=self.price,
            shipping_fee=0.0,      # HPOI通常不涉及运费
            is_free_shipping=True,
            image_url=self.image_url,
            detail_url=self.detail_url,
            release_date=self.release_date,
            score=self.score,
            raw_data=self.__dict__
        )


class UnifiedSearchResults:
    """统一搜索结果管理器"""
    
    def __init__(self):
        self.results: List[SearchResult] = []
    
    def add_result(self, result: SearchResult):
        """添加搜索结果"""
        self.results.append(result)
    
    def add_from_taobao(self, item: dict):
        """从淘宝原始数据添加"""
        # 尝试提取价格和运费
        price_text = item.get('price_text', '0')
        price = self._extract_price(price_text)
        
        # 淘宝通常显示包邮信息在标题或价格中
        shipping_fee = 0.0
        is_free_shipping = "包邮" in item.get('title', '') or "包邮" in price_text
        
        result = SearchResult(
            platform="taobao",
            title=item.get('title', ''),
            price=price,
            shipping_fee=shipping_fee,
            is_free_shipping=is_free_shipping,
            image_url=item.get('image', ''),
            detail_url=item.get('link', ''),
            shop_name=item.get('shop', ''),
            score=item.get('score', 0),
            raw_data=item
        )
        self.results.append(result)
    
    def add_from_xianyu(self, item: dict):
        """从闲鱼原始数据添加"""
        # 闲鱼通常价格文本中可能包含运费信息
        price_text = item.get('price_text', '0')
        price = self._extract_price(price_text)
        
        # 闲鱼通常显示运费信息
        shipping_fee = 0.0  # 默认运费，需要根据实际情况提取
        is_free_shipping = "包邮" in item.get('title', '') or "包邮" in price_text
        
        result = SearchResult(
            platform="xianyu",
            title=item.get('title', ''),
            price=price,
            shipping_fee=shipping_fee,
            is_free_shipping=is_free_shipping,
            image_url=item.get('image', ''),
            detail_url=item.get('link', ''),
            shop_name=item.get('seller', ''),
            raw_data=item
        )
        self.results.append(result)
    
    def add_from_hpoi(self, item: dict):
        """从HPOI原始数据添加"""
        hpoi_result = HpoiResult(
            name=item.get('title', ''),
            price=item.get('price', 0.0),
            release_date=item.get('release_date', ''),
            image_url=item.get('image_url', ''),
            detail_url=item.get('link', ''),
            score=item.get('score', 0)
        )
        self.results.append(hpoi_result.to_search_result())
    
    def _extract_price(self, price_text: str) -> float:
        """从价格文本中提取数值"""
        import re
        
        if not price_text or price_text == "N/A":
            return 0.0
        
        # 移除非数字字符（除了小数点和逗号）
        price_text = str(price_text)
        # 移除¥、元、,等字符
        price_text = re.sub(r'[¥元,，]', '', price_text)
        
        # 提取数字（包括小数）
        match = re.search(r'(\d+(?:\.\d+)?)', price_text)
        if match:
            try:
                return float(match.group(1))
            except (ValueError, TypeError):
                return 0.0
        
        return 0.0
    
    def sort_by_price(self, free_shipping_first: bool = True):
        """
        按价格排序
        free_shipping_first: True表示包邮商品优先，False表示统一排序
        """
        if free_shipping_first:
            # 先按是否包邮分组，再分别按总价排序
            free_shipping = [r for r in self.results if r.is_free_shipping]
            not_free_shipping = [r for r in self.results if not r.is_free_shipping]
            
            # 按总价升序排序
            free_shipping.sort(key=lambda x: x.total_price())
            not_free_shipping.sort(key=lambda x: x.total_price())
            
            self.results = free_shipping + not_free_shipping
        else:
            # 统一按总价升序排序
            self.results.sort(key=lambda x: x.total_price())
    
    def get_free_shipping(self) -> List[SearchResult]:
        """获取包邮商品"""
        return [r for r in self.results if r.is_free_shipping]
    
    def get_not_free_shipping(self) -> List[SearchResult]:
        """获取不包邮商品"""
        return [r for r in self.results if not r.is_free_shipping]
    
    def to_list(self) -> List[dict]:
        """转换为字典列表"""
        return [r.to_dict() for r in self.results]
    
    def __len__(self) -> int:
        return len(self.results)
    
    def __getitem__(self, index) -> SearchResult:
        return self.results[index]


# 工具函数
def create_unified_result(platform: str, **kwargs) -> SearchResult:
    """创建统一搜索结果"""
    return SearchResult(platform=platform, **kwargs)


def sort_results_by_shipping_and_price(results: List[SearchResult], free_shipping_first: bool = True) -> List[SearchResult]:
    """按包邮状态和价格排序"""
    manager = UnifiedSearchResults()
    manager.results = results
    manager.sort_by_price(free_shipping_first)
    return manager.results