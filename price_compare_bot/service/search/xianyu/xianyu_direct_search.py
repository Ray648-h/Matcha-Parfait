# -*- coding: utf-8 -*-
"""
闲鱼直接搜索商品功能
1. 直接搜索商品关键词
2. 爬取第一页全部商品
3. 筛选卖家名称在目标卖家列表中的商品
"""

import re
import random
import time
from typing import Dict, List, Optional
from urllib.parse import quote_plus

from config.context import BrowserManager
from config.settings import XIANYU_URL
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


def _load_target_sellers_from_file(file_path: str) -> Dict[str, str]:
    """
    从文件加载目标卖家列表
    格式：
    卖家名称
    卖家主页URL（可选）
    """
    target_sellers = {}
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        current_seller = None
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # 检查是否是URL
            if line.startswith('http'):
                if current_seller:
                    target_sellers[current_seller] = line
                current_seller = None
            else:
                # 这是卖家名称
                current_seller = line
        
        print(f"[_load_target_sellers_from_file] 加载了 {len(target_sellers)} 个目标卖家")
        return target_sellers
        
    except Exception as e:
        print(f"[_load_target_sellers_from_file] 加载卖家文件失败: {e}")
        # 返回空的卖家列表
        return {}


def _normalize_seller_name(seller_name: str) -> str:
    """标准化卖家名称，用于匹配"""
    # 移除特殊字符和空格，转换为小写
    seller_name = re.sub(r'[^\w\u4e00-\u9fff]', '', seller_name.lower())
    return seller_name


def _is_target_seller(seller_name: str, target_sellers: Dict[str, str]) -> bool:
    """检查卖家是否在目标卖家列表中"""
    if not seller_name:
        return False
    
    normalized_seller = _normalize_seller_name(seller_name)
    
    for target_seller in target_sellers.keys():
        normalized_target = _normalize_seller_name(target_seller)
        
        # 检查是否包含关系（部分匹配）
        if normalized_target in normalized_seller or normalized_seller in normalized_target:
            return True
    
    return False


def _search_xianyu_products_directly(page, keyword: str, debug: bool = False) -> List[Dict]:
    """
    直接搜索闲鱼商品
    返回：商品列表
    """
    items = []
    
    if debug:
        print(f"[_search_xianyu_products_directly] 搜索闲鱼商品: {keyword}")
    
    # 构建闲鱼搜索URL
    search_url = f"https://www.goofish.com/search?q={quote_plus(keyword)}"
    
    # 访问搜索页面
    if not _safe_goto(page, search_url, debug=debug):
        if debug:
            print(f"[_search_xianyu_products_directly] 无法访问闲鱼搜索页面: {search_url}")
        return items
    
    # 等待页面加载
    page.wait_for_timeout(3000)
    
    # 滚动加载更多商品
    if debug:
        print(f"[_search_xianyu_products_directly] 滚动加载商品...")
    
    for i in range(3):
        page.mouse.wheel(0, 2000)
        page.wait_for_timeout(1500)
    
    page.wait_for_timeout(2000)
    
    try:
        # 闲鱼搜索页面的商品选择器
        # 根据闲鱼页面结构
        item_selectors = [
            "a[href*='goofish.com/item']",  # 商品链接
            "div[class*='item']",  # 商品容器
            "div[class*='card']",  # 商品卡片
            "div[class*='product']",  # 商品
        ]
        
        for selector in item_selectors:
            item_elements = page.locator(selector)
            count = item_elements.count()
            
            if count > 0:
                if debug:
                    print(f"[_search_xianyu_products_directly] 找到 {count} 个商品元素，选择器: {selector}")
                
                for i in range(min(count, 50)):  # 闲鱼通常每页50个商品
                    try:
                        item = item_elements.nth(i)
                        
                        # 提取整个HTML元素
                        html_content = ""
                        try:
                            html_content = item.evaluate("element => element.outerHTML")
                        except:
                            pass
                        
                        # 提取标题
                        title = ""
                        # 方法1：从商品文本中提取
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
                        
                        # 方法2：使用选择器
                        if not title:
                            title_selectors = [
                                "span", "div", "p",
                                "div[class*='title']", "span[class*='title']"
                            ]
                            
                            for title_selector in title_selectors:
                                title_elem = item.locator(title_selector)
                                if title_elem.count() > 0:
                                    # 找到最长的文本作为标题
                                    max_len = 0
                                    for j in range(min(title_elem.count(), 10)):
                                        try:
                                            text = title_elem.nth(j).inner_text().strip()
                                            if len(text) > max_len and len(text) > 5:
                                                max_len = len(text)
                                                title = text
                                        except:
                                            pass
                                    if title:
                                        break
                        
                        if not title:
                            continue
                        
                        # 提取价格
                        price = ""
                        # 在商品文本中查找价格（通常是数字）
                        if item_text:
                            # 查找价格模式：¥数字 或 数字元
                            price_patterns = [
                                r'¥\s*(\d+(?:\.\d+)?)',
                                r'(\d+(?:\.\d+)?)\s*元',
                                r'价格\s*[:：]\s*(\d+(?:\.\d+)?)'
                            ]
                            
                            for pattern in price_patterns:
                                match = re.search(pattern, item_text)
                                if match:
                                    price = match.group(1)
                                    break
                        
                        # 如果没找到，尝试查找纯数字
                        if not price:
                            # 查找商品中的数字（可能是价格）
                            numbers = re.findall(r'\b\d{2,5}\b', item_text)
                            if numbers:
                                # 取第一个看起来像价格的数字（通常在100-10000之间）
                                for num in numbers:
                                    num_int = int(num)
                                    if 50 <= num_int <= 10000:
                                        price = num
                                        break
                        
                        # 提取卖家名称
                        seller = ""
                        # 在商品文本中查找卖家信息
                        if item_text:
                            # 卖家通常在标题后面或价格前面
                            lines = item_text.split('\n')
                            for line in lines:
                                line = line.strip()
                                # 排除标题和价格行
                                if line and line != title and not re.search(r'¥?\d+(?:\.\d+)?', line):
                                    # 可能是卖家信息
                                    seller = line
                                    break
                        
                        # 提取链接
                        link = ""
                        try:
                            link = item.get_attribute("href")
                            if link and not link.startswith("http"):
                                link = f"https:{link}" if link.startswith("//") else f"https://www.goofish.com{link}"
                        except:
                            pass
                        
                        # 提取图片
                        image = ""
                        img_elem = item.locator("img[src]")
                        if img_elem.count() > 0:
                            image = img_elem.first.get_attribute("src")
                        
                        items.append({
                            "title": title.strip(),
                            "seller": seller.strip() if seller else "未知卖家",
                            "price_text": price.strip() if price else "N/A",
                            "link": link,
                            "image": image,
                            "html_snippet": html_content[:300] + "..." if len(html_content) > 300 else html_content,
                            "index": i + 1
                        })
                        
                        if debug and len(items) <= 5:
                            print(f"[_search_xianyu_products_directly] 找到商品 {i+1}: {title[:40]}...")
                            if seller:
                                print(f"    卖家: {seller}")
                            if price:
                                print(f"    价格: {price}")
                            
                    except Exception as e:
                        if debug:
                            print(f"[_search_xianyu_products_directly] 提取商品 {i} 时出错: {e}")
                        continue
                
                break  # 找到商品后退出循环
        
        if debug:
            print(f"[_search_xianyu_products_directly] 共提取 {len(items)} 个商品")
        
    except Exception as e:
        if debug:
            print(f"[_search_xianyu_products_directly] 搜索商品时出错: {e}")
        import traceback
        traceback.print_exc()
    
    return items


def search_and_filter_xianyu_products(
    keyword: str,
    seller_file_path: str = "price_compare_bot/xianyu_sellers.txt",
    debug: bool = False,
    context=None,
) -> List[Dict]:
    """
    直接搜索闲鱼商品并筛选目标卖家
    流程：
    1. 登录闲鱼
    2. 直接搜索商品关键词
    3. 提取第一页全部商品
    4. 筛选卖家名称在目标卖家列表中的商品
    5. 返回筛选后的商品
    """
    all_items = []
    filtered_items = []
    own_context = context is None
    page = None
    
    try:
        # 加载目标卖家列表
        target_sellers = _load_target_sellers_from_file(seller_file_path)
        
        if debug:
            print(f"[search_and_filter_xianyu_products] 目标卖家数量: {len(target_sellers)}")
            for i, (seller, url) in enumerate(list(target_sellers.items())[:5], 1):
                print(f"   {i}. {seller}: {url[:50]}..." if url else f"   {i}. {seller}")
            if len(target_sellers) > 5:
                print(f"   ... 还有 {len(target_sellers) - 5} 个卖家")
        
        # 创建浏览器上下文
        if own_context:
            manager = BrowserManager()
            context = manager.launch_xianyu()
            login_service = LoginService(context)
            page = login_service.login(XIANYU_URL, "闲鱼")
        else:
            page = context.new_page()
        
        if not page or page.is_closed():
            if debug:
                print("[search_and_filter_xianyu_products] 页面创建失败")
            return filtered_items
        
        # 访问闲鱼首页
        if not _safe_goto(page, XIANYU_URL, debug=debug):
            if debug:
                print("[search_and_filter_xianyu_products] 无法访问闲鱼首页")
            return filtered_items
        
        # 直接搜索商品
        all_items = _search_xianyu_products_directly(page, keyword, debug=debug)
        
        if debug:
            print(f"[search_and_filter_xianyu_products] 搜索到 {len(all_items)} 个商品")
        
        # 筛选目标卖家的商品
        for item in all_items:
            seller_name = item.get('seller', '')
            if seller_name and _is_target_seller(seller_name, target_sellers):
                # 添加匹配的卖家URL
                for target_seller, seller_url in target_sellers.items():
                    if _normalize_seller_name(target_seller) in _normalize_seller_name(seller_name) or \
                       _normalize_seller_name(seller_name) in _normalize_seller_name(target_seller):
                        item['target_seller'] = target_seller
                        item['seller_url'] = seller_url
                        break
                
                filtered_items.append(item)
        
        if debug:
            print(f"[search_and_filter_xianyu_products] 筛选后剩余 {len(filtered_items)} 个商品")
        
        return filtered_items
        
    except Exception as e:
        if debug:
            print(f"[search_and_filter_xianyu_products] 搜索过程中出错: {e}")
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
def test_xianyu_direct_search():
    """测试闲鱼直接搜索商品功能"""
    print("=" * 80)
    print("测试闲鱼直接搜索商品功能")
    print("=" * 80)
    
    # 测试参数
    keyword = "初音未来粘土人"
    seller_file = "price_compare_bot/xianyu_sellers.txt"
    
    print(f"测试关键词: {keyword}")
    print(f"卖家文件: {seller_file}")
    print("-" * 80)
    
    start_time = time.time()
    
    try:
        items = search_and_filter_xianyu_products(
            keyword=keyword,
            seller_file_path=seller_file,
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
                print(f"   卖家: {item['seller']}")
                if item.get('target_seller'):
                    print(f"   匹配的目标卖家: {item['target_seller']}")
                print(f"   价格: {item['price_text']}")
                if item.get('link'):
                    link_preview = item['link'][:60] + "..." if len(item['link']) > 60 else item['link']
                    print(f"   链接: {link_preview}")
                print()
            
            if len(items) > 10:
                print(f"... 还有 {len(items) - 10} 个结果未显示")
        else:
            print("未找到目标卖家的商品")
            
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 80)


if __name__ == "__main__":
    test_xianyu_direct_search()