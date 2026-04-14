# service/search/hpoi/config.py
"""
HPOI (日本合伙人玩具价格信息) 配置文件
"""

# HPOI网址配置
HPOI_URL = "https://www.hpoi.net"
HPOI_SEARCH_URL = "https://www.hpoi.net/search"
HPOI_SEARCH_QUERY_PARAM = "keyword"  # 关键字查询参数, 兼容 q 旧参数

# 常见的产品类型词列表
PRODUCT_TYPE_KEYWORDS = [
    "粘土人", "手办粘土人", "手办", "模型", "玩偶", "人偶",
    "雕像", "公仔", "黏土人", "nendoroid", "figma",
    "max factory", "good smile", "gsc",
    "手办盲盒", "盲盒手办",
]

# 页面元素选择器
# 兼容历史旧结构与当前新版结构（如：li.media.ibox-content）
PRODUCT_ITEM_SELECTOR = "div.product-item, li.item-list, div.goods-item, li.media.ibox-content"
TITLE_SELECTOR = "a.product-name, a.goods-name, span.name, h4.media-heading a"
PRICE_SELECTOR = "span.price, span.sale-price, em.price"
DATE_SELECTOR = "span.date, span.release-date, em.date"
LINK_SELECTOR = "a.product-link, a.goods-link, a"
SOURCE_SELECTOR = "span.source, span.seller, em.shop"
