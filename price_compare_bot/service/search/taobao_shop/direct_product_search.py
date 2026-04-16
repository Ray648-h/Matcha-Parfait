# -*- coding: utf-8 -*-
"""
直接搜索商品功能
1. 直接搜索商品关键词
2. 爬取第一页全部商品
3. 筛选店铺名称在taobao_shop_urls.txt里的商品
"""

import re
import random
import time
from typing import Dict, List, Optional
from urllib.parse import quote_plus, urlparse

from config.context import BrowserManager
from config.settings import TAOBAO_URL
from service.login_service import LoginService


# 配置参数
REQUEST_RETRY = 3
REQUEST_TIMEOUT_MS = 30000
SHORT_DELAY_RANGE_MS = (2000, 4000)
LONG_DELAY_RANGE_MS = (5000, 10000)


def _human_wait(page, delay_range_ms, reason: str = "", debug: bool = False) -> None:
    """人类行为等待"""
    if not page or page.is_closed():
        return

    delay = random.randint(*delay_range_ms)
    if debug:
        message = f"[_human_wait] 等待 {delay}ms"
        if reason:
            message = f"{message}，原因: {reason}"
        print(message)
    try:
        page.wait_for_timeout(delay)
    except Exception:
        return


def _is_target_closed_error(error: Exception) -> bool:
    """检查是否是页面关闭错误"""
    error_text = str(error).lower()
    return "target page, context or browser has been closed" in error_text


def _safe_goto(page, url: str, debug: bool = False, retry: int = REQUEST_RETRY) -> bool:
    """安全访问页面"""
    for attempt in range(1, retry + 1):
        if not page or page.is_closed():
            if debug:
                print(f"[_safe_goto] 页面已关闭，停止访问: {url}")
            return False

        try:
            page.goto(url, wait_until="domcontentloaded", timeout=REQUEST_TIMEOUT_MS)
            page.wait_for_timeout(2000)  # 等待页面稳定
            
            if page.is_closed():
                if debug:
                    print(f"[_safe_goto] 页面被关闭，第{attempt}次: {url}")
                return False

            _human_wait(page, SHORT_DELAY_RANGE_MS, reason="页面稳定等待", debug=debug)
            return True
        except Exception as e:
            if debug:
                print(f"[_safe_goto] 第{attempt}次访问失败: {e}")
            if _is_target_closed_error(e):
                return False
            _human_wait(page, LONG_DELAY_RANGE_MS, reason="访问失败退避", debug=debug)

    return False


def _load_target_shops_from_file(file_path: str) -> Dict[str, str]:
    """
    从文件加载目标店铺列表
    格式：
    店铺名称
    店铺URL
    """
    target_shops = {}
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        current_shop = None
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # 检查是否是URL
            if line.startswith('http'):
                if current_shop:
                    target_shops[current_shop] = line
                current_shop = None
            else:
                # 这是店铺名称，可能包含编号如"1. 店铺名"
                # 移除编号前缀
                shop_name = re.sub(r'^\d+\.\s*', '', line)
                current_shop = shop_name
        
        print(f"[_load_target_shops_from_file] 加载了 {len(target_shops)} 个目标店铺")
        return target_shops
        
    except Exception as e:
        print(f"[_load_target_shops_from_file] 加载店铺文件失败: {e}")
        # 返回默认的店铺列表
        return {
            "gsc": "https://goodsmile.tmall.com/shop/view_shop.htm",
            "animate旗舰店": "https://shop69755565.taobao.com",
            "万代官方旗舰店": "https://shop70539661.taobao.com"
        }


def _normalize_shop_name(shop_name: str) -> str:
    """标准化店铺名称，用于匹配"""
    # 移除特殊字符和空格，转换为小写
    shop_name = re.sub(r'[^\w\u4e00-\u9fff]', '', shop_name.lower())
    return shop_name


def _is_target_shop(shop_name: str, target_shops: Dict[str, str]) -> bool:
    """检查店铺是否在目标店铺列表中"""
    if not shop_name:
        return False
    
    normalized_shop = _normalize_shop_name(shop_name)
    
    for target_shop in target_shops.keys():
        normalized_target = _normalize_shop_name(target_shop)
        
        # 检查是否包含关系（部分匹配）
        if normalized_target in normalized_shop or normalized_shop in normalized_target:
            return True
    
    return False


def _search_products_directly(page, keyword: str, debug: bool = False) -> List[Dict]:
    """
    直接搜索商品
    返回：商品列表
    """
    items = []
    
    if debug:
        print(f"[_search_products_directly] 搜索商品: {keyword}")
    
    # 构建商品搜索URL
    search_url = f"https://s.taobao.com/search?q={quote_plus(keyword)}"
    
    # 访问搜索页面
    if not _safe_goto(page, search_url, debug=debug):
        if debug:
            print(f"[_search_products_directly] 无法访问搜索页面: {search_url}")
        return items
    
    # 等待页面加载
    page.wait_for_timeout(3000)
    
    try:
        # 淘宝搜索页面的商品选择器
        # 根据用户提供的HTML结构
        item_selectors = [
            "div.mainPicAndDesc",  # 用户提供的类名（去掉动态后缀）
            "div[class*='mainPicAndDesc']",  # 包含mainPicAndDesc的类
            "div.item",  # 传统选择器
            "div[data-category*='auctions']",  # 数据属性选择器
            "div[class*='item']",  # 类名包含item
        ]
        
        for selector in item_selectors:
            item_elements = page.locator(selector)
            count = item_elements.count()
            
            if count > 0:
                if debug:
                    print(f"[_search_products_directly] 找到 {count} 个商品元素，选择器: {selector}")
                
                for i in range(min(count, 48)):  # 淘宝通常每页48个商品
                    try:
                        item = item_elements.nth(i)
                        
                        # 提取整个HTML元素
                        html_content = ""
                        try:
                            html_content = item.evaluate("element => element.outerHTML")
                        except:
                            pass
                        
                        # 提取标题 - 使用通用选择器，避免动态类名
                        title = ""
                        # 方法1：尝试获取商品容器的文本内容，然后提取标题
                        item_text = ""
                        try:
                            item_text = item.inner_text()
                        except:
                            pass
                        
                        if item_text:
                            # 从文本中提取标题（通常是第一行或最长的行）
                            lines = [line.strip() for line in item_text.split('\n') if line.strip()]
                            if lines:
                                # 找到最长的行作为标题
                                title = max(lines, key=len)
                        
                        # 方法2：使用通用选择器
                        if not title:
                            title_selectors = [
                                "div[class*='title']",  # 包含title的类
                                "div.title", "a.title", "span.title",
                                "h3", "h4", "div[class*='desc']"
                            ]
                            
                            for title_selector in title_selectors:
                                title_elem = item.locator(title_selector)
                                if title_elem.count() > 0:
                                    title = title_elem.first.inner_text().strip()
                                    if title:
                                        break
                        
                        if not title:
                            continue
                        
                        # 提取价格 - 使用通用选择器
                        price = ""
                        price_selectors = [
                            "div[class*='price']",  # 包含price的类
                            "div.price", "span.price", "strong.price",
                            "div[class*='priceWrapper']", "span[class*='price']"
                        ]
                        
                        for price_selector in price_selectors:
                            price_elem = item.locator(price_selector)
                            if price_elem.count() > 0:
                                price = price_elem.first.inner_text().strip()
                                if price:
                                    break
                        
                        # 如果价格包含"¥"符号，清理一下
                        if price and '¥' in price:
                            price = price.replace('¥', '').strip()
                        
                        # 提取店铺名称 - 使用通用选择器
                        shop = ""
                        shop_selectors = [
                            "span[class*='shopName']",  # 包含shopName的类
                            "div.shop", "a.shop", "span.shop",
                            "div[class*='shop']", "a[class*='shop']",
                            "span[class*='shopNameText']"
                        ]
                        
                        for shop_selector in shop_selectors:
                            shop_elem = item.locator(shop_selector)
                            if shop_elem.count() > 0:
                                shop = shop_elem.first.inner_text().strip()
                                if shop:
                                    break
                        
                        # 如果没找到店铺名称，尝试从商品容器外部查找
                        if not shop:
                            # 查找商品容器外部的店铺名称
                            parent_container = item.locator("xpath=..")
                            shop_selectors_outer = [
                                "span[class*='shopName']",
                                "div[class*='shop']",
                                "a[class*='shop']"
                            ]
                            for shop_selector in shop_selectors_outer:
                                shop_elem = parent_container.locator(shop_selector)
                                if shop_elem.count() > 0:
                                    shop = shop_elem.first.inner_text().strip()
                                    if shop:
                                        break
                        
                        # 如果还是没找到，尝试在整个页面中查找店铺名称
                        if not shop and debug:
                            print(f"[_search_products_directly] 商品 {i+1} 未找到店铺名称，尝试其他方法")
                        
                        # 提取链接
                        link = ""
                        link_elem = item.locator("a[href*='item.taobao.com'], a[href*='detail.tmall.com']")
                        if link_elem.count() > 0:
                            link = link_elem.first.get_attribute("href")
                            if link and not link.startswith("http"):
                                link = f"https:{link}" if link.startswith("//") else f"https://{link}"
                        
                        # 提取图片
                        image = ""
                        img_elem = item.locator("img[src]")
                        if img_elem.count() > 0:
                            image = img_elem.first.get_attribute("src")
                        
                        # 提取包邮信息
                        free_shipping = False
                        # 方法1：检查包含"包邮"文本的元素
                        for sel in [
                            "div[class*='SalesPoint--subIconWrapper']",
                            "div[class*='SalesPoint']",
                            "div[class*='subIconWrapper']",
                            "span[style*='color: rgb(255, 98, 0)']",
                        ]:
                            shipping_elem = item.locator(sel)
                            if shipping_elem.count() > 0:
                                text = shipping_elem.first.inner_text().strip()
                                if "包邮" in text:
                                    free_shipping = True
                                    break
                        
                        # 方法2：检查title属性
                        if not free_shipping:
                            for sel in [
                                "div[title*='包邮']",
                                "span[title*='包邮']",
                            ]:
                                shipping_elem = item.locator(sel)
                                if shipping_elem.count() > 0:
                                    free_shipping = True
                                    break
                        
                        items.append({
                            "title": title.strip(),
                            "shop": shop.strip() if shop else "未知店铺",
                            "price_text": price.strip() if price else "N/A",
                            "link": link,
                            "image": image,
                            "free_shipping": free_shipping,
                            "html_snippet": html_content[:300] + "..." if len(html_content) > 300 else html_content,
                            "index": i + 1
                        })
                        
                        if debug and len(items) <= 5:
                            print(f"[_search_products_directly] 找到商品 {i+1}: {title[:40]}...")
                            if shop:
                                print(f"    店铺: {shop}")
                            if price:
                                print(f"    价格: {price}")
                            
                    except Exception as e:
                        if debug:
                            print(f"[_search_products_directly] 提取商品 {i} 时出错: {e}")
                        continue
                
                break  # 找到商品后退出循环
        
        if debug:
            print(f"[_search_products_directly] 共提取 {len(items)} 个商品")
        
    except Exception as e:
        if debug:
            print(f"[_search_products_directly] 搜索商品时出错: {e}")
        import traceback
        traceback.print_exc()
    
    return items


def search_and_filter_products(
    keyword: str,
    shop_file_path: str = "price_compare_bot/taobao_shop_urls.txt",
    debug: bool = False,
    context=None,
    enable_scoring: bool = True,
) -> List[Dict]:
    """
    直接搜索商品并筛选目标店铺，支持评分功能
    流程：
    1. 登录淘宝
    2. 直接搜索商品关键词
    3. 提取第一页全部商品
    4. 筛选店铺名称在目标店铺列表中的商品
    5. 对商品进行评分（如果启用）
    6. 返回筛选后的商品（如果启用评分，则返回评分后的商品）
    """
    all_items = []
    filtered_items = []
    own_context = context is None
    page = None
    
    try:
        # 加载目标店铺列表
        target_shops = _load_target_shops_from_file(shop_file_path)
        
        if debug:
            print(f"[search_and_filter_products] 目标店铺数量: {len(target_shops)}")
            for i, (shop, url) in enumerate(list(target_shops.items())[:5], 1):
                print(f"   {i}. {shop}: {url[:50]}...")
            if len(target_shops) > 5:
                print(f"   ... 还有 {len(target_shops) - 5} 个店铺")
        
        # 创建浏览器上下文
        if own_context:
            manager = BrowserManager()
            context = manager.launch_taobao()
            login_service = LoginService(context)
            page = login_service.login(TAOBAO_URL, "淘宝")
        else:
            page = context.new_page()
        
        if not page or page.is_closed():
            if debug:
                print("[search_and_filter_products] 页面创建失败")
            return filtered_items
        
        # 访问淘宝首页
        if not _safe_goto(page, TAOBAO_URL, debug=debug):
            if debug:
                print("[search_and_filter_products] 无法访问淘宝首页")
            return filtered_items
        
        # 直接搜索商品
        all_items = _search_products_directly(page, keyword, debug=debug)
        
        if debug:
            print(f"[search_and_filter_products] 搜索到 {len(all_items)} 个商品")
        
        # 筛选目标店铺的商品
        for item in all_items:
            shop_name = item.get('shop', '')
            if shop_name and _is_target_shop(shop_name, target_shops):
                # 添加匹配的店铺URL
                for target_shop, shop_url in target_shops.items():
                    if _normalize_shop_name(target_shop) in _normalize_shop_name(shop_name) or \
                       _normalize_shop_name(shop_name) in _normalize_shop_name(target_shop):
                        item['target_shop'] = target_shop
                        item['shop_url'] = shop_url
                        break
                
                filtered_items.append(item)
        
        if debug:
            print(f"[search_and_filter_products] 筛选后剩余 {len(filtered_items)} 个商品")
        
        # 如果启用评分功能，对商品进行评分
        if enable_scoring and filtered_items:
            try:
                # 导入评分模块
                from .taobao_scorer import process_taobao_items_with_scoring
                
                if debug:
                    print(f"[search_and_filter_products] 开始对商品进行评分...")
                
                # 对商品进行评分并获取前2名按价格排序的商品
                scored_items, top_items = process_taobao_items_with_scoring(
                    filtered_items, keyword, debug=debug
                )
                
                if debug:
                    print(f"[search_and_filter_products] 评分完成")
                    print(f"  评分后商品数量: {len(scored_items)}")
                    print(f"  前2名按价格排序的商品数量: {len(top_items)}")
                
                # 返回评分后的商品和前2名商品
                # 在返回的商品中添加评分信息
                for item in scored_items:
                    item['scored'] = True
                
                # 只返回前2名按价格排序的商品
                return top_items
                
            except ImportError as e:
                if debug:
                    print(f"[search_and_filter_products] 无法导入评分模块: {e}")
                    print("  返回未评分的商品")
            except Exception as e:
                if debug:
                    print(f"[search_and_filter_products] 评分过程中出错: {e}")
                    print("  返回未评分的商品")
        
        return filtered_items
        
    except Exception as e:
        if debug:
            print(f"[search_and_filter_products] 搜索过程中出错: {e}")
        import traceback
        traceback.print_exc()
        return filtered_items
    
    finally:
        # 清理资源
        if page:
            try:
                page.close()
            except:
                pass
        
        if own_context and context:
            try:
                context.close()
            except:
                pass


# 测试函数
def test_direct_search():
    """测试直接搜索商品功能"""
    print("=" * 80)
    print("测试直接搜索商品功能")
    print("=" * 80)
    
    # 测试参数
    keyword = "初音未来粘土人3.0"
    shop_file = "price_compare_bot/taobao_shop_urls.txt"
    
    print(f"测试关键词: {keyword}")
    print(f"店铺文件: {shop_file}")
    print("-" * 80)
    
    start_time = time.time()
    
    try:
        items = search_and_filter_products(
            keyword=keyword,
            shop_file_path=shop_file,
            debug=True
        )
        
        end_time = time.time()
        search_time = end_time - start_time
        
        print("-" * 80)
        print(f"搜索完成!")
        print(f"总耗时: {search_time:.2f}秒")
        print(f"搜索到商品总数: 未知（需要从日志查看）")
        print(f"筛选后商品数量: {len(items)}")
        
        # 显示结果
        if items:
            print("\n筛选后的商品结果:")
            for i, item in enumerate(items[:10], 1):  # 只显示前10个结果
                title_preview = item['title'][:50] + "..." if len(item['title']) > 50 else item['title']
                print(f"{i}. 商品 {item.get('index', '?')}")
                print(f"   标题: {title_preview}")
                print(f"   店铺: {item['shop']}")
                if item.get('target_shop'):
                    print(f"   匹配的目标店铺: {item['target_shop']}")
                print(f"   价格: {item['price_text']}")
                if item.get('link'):
                    link_preview = item['link'][:60] + "..." if len(item['link']) > 60 else item['link']
                    print(f"   链接: {link_preview}")
                print()
            
            if len(items) > 10:
                print(f"... 还有 {len(items) - 10} 个结果未显示")
        else:
            print("未找到目标店铺的商品")
            
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 80)


if __name__ == "__main__":
    test_direct_search()