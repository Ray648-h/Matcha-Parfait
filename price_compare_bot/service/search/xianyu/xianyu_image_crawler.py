# -*- coding: utf-8 -*-
"""
闲鱼商品图片爬取功能
1. 搜索指定关键词的商品
2. 提取商品图片（使用特定的图片元素选择器）
3. 检查商品标题是否包含所有关键词
4. 分页逻辑：
   - 第一页如果有10个以上匹配所有关键词的商品，按价格排序取前5个
   - 否则爬取第二页，合并结果后结束
"""

import re
import random
import time
from typing import Dict, List, Optional, Tuple
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


def _extract_price_from_text(price_text: str) -> float:
    """从价格文本中提取数值"""
    if not price_text:
        return 0.0
    
    # 移除非数字字符（保留小数点）
    price_clean = re.sub(r'[^\d.]', '', price_text)
    try:
        return float(price_clean) if price_clean else 0.0
    except ValueError:
        return 0.0


def _matches_all_keywords(title: str, keywords: List[str]) -> bool:
    """检查标题是否包含所有关键词"""
    if not title or not keywords:
        return False
    
    title_lower = title.lower()
    for keyword in keywords:
        if keyword.lower() not in title_lower:
            return False
    return True


def _crawl_xianyu_page(page, keyword: str, page_num: int, debug: bool = False) -> List[Dict]:
    """
    爬取单页闲鱼商品
    返回：商品列表，每个商品包含 title, price, price_value, image_url, link
    """
    items = []
    
    if debug:
        print(f"[_crawl_xianyu_page] 爬取第 {page_num} 页，关键词: {keyword}")
    
    # 构建闲鱼搜索URL（翻页参数）
    search_url = f"https://www.goofish.com/search?q={quote_plus(keyword)}&pageNo={page_num}"
    
    # 访问搜索页面
    if not _safe_goto(page, search_url, debug=debug):
        if debug:
            print(f"[_crawl_xianyu_page] 无法访问闲鱼搜索页面: {search_url}")
        return items
    
    # 等待页面加载
    page.wait_for_timeout(3000)
    
    # 滚动加载更多商品
    if debug:
        print(f"[_crawl_xianyu_page] 滚动加载商品...")
    
    for i in range(3):
        page.mouse.wheel(0, 2000)
        page.wait_for_timeout(1500)
    
    page.wait_for_timeout(2000)
    
    try:
        # 闲鱼搜索页面的商品选择器
        # 使用更通用的选择器来定位商品卡片
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
                    print(f"[_crawl_xianyu_page] 找到 {count} 个商品元素，选择器: {selector}")
                
                for i in range(min(count, 50)):  # 闲鱼通常每页50个商品
                    try:
                        item = item_elements.nth(i)
                        
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
                        price_text = ""
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
                                    price_text = match.group(1)
                                    break
                        
                        # 如果没找到，尝试查找纯数字
                        if not price_text:
                            # 查找商品中的数字（可能是价格）
                            numbers = re.findall(r'\b\d{2,5}\b', item_text)
                            if numbers:
                                # 取第一个看起来像价格的数字（通常在100-10000之间）
                                for num in numbers:
                                    num_int = int(num)
                                    if 50 <= num_int <= 10000:
                                        price_text = num
                                        break
                        
                        # 提取链接
                        link = ""
                        try:
                            link = item.get_attribute("href")
                            if link and not link.startswith("http"):
                                link = f"https:{link}" if link.startswith("//") else f"https://www.goofish.com{link}"
                        except:
                            pass
                        
                        # 提取图片 - 使用特定的图片元素选择器
                        image_url = ""
                        # 尝试多种图片选择器，优先使用用户提供的结构
                        img_selectors = [
                            "div[class*='feeds-image-container'] img[class*='feeds-image']",  # 用户提供的结构
                            "div[class*='image-container'] img",  # 更通用的选择器
                            "div[class*='feeds-image'] img",  # 可能的变化
                            "img[class*='feeds-image']",  # 直接图片类
                            "img[src*='alicdn.com']",  # 淘宝图片
                            "img[src]",  # 任何图片
                        ]
                        
                        for img_selector in img_selectors:
                            img_elem = item.locator(img_selector)
                            if img_elem.count() > 0:
                                try:
                                    image_url = img_elem.first.get_attribute("src")
                                    if image_url:
                                        # 确保URL完整
                                        if image_url.startswith("//"):
                                            image_url = f"https:{image_url}"
                                        elif not image_url.startswith("http"):
                                            # 可能是相对路径，尝试构建完整URL
                                            image_url = f"https:{image_url}" if image_url.startswith("//") else f"https://{image_url}"
                                        break
                                except:
                                    continue
                        
                        # 如果还没找到图片，尝试在商品元素内查找任何图片
                        if not image_url:
                            img_elem = item.locator("img[src]")
                            if img_elem.count() > 0:
                                image_url = img_elem.first.get_attribute("src")
                                if image_url and image_url.startswith("//"):
                                    image_url = f"https:{image_url}"
                        
                        # 计算价格数值
                        price_value = _extract_price_from_text(price_text)
                        
                        items.append({
                            "title": title.strip(),
                            "price_text": price_text.strip() if price_text else "N/A",
                            "price_value": price_value,
                            "link": link,
                            "image_url": image_url,
                            "page_num": page_num,
                            "index": i + 1
                        })
                        
                        if debug and len(items) <= 5:
                            print(f"[_crawl_xianyu_page] 找到商品 {i+1}: {title[:40]}...")
                            if price_text:
                                print(f"    价格: {price_text}")
                            if image_url:
                                print(f"    图片: {image_url[:80]}...")
                            
                    except Exception as e:
                        if debug:
                            print(f"[_crawl_xianyu_page] 提取商品 {i} 时出错: {e}")
                        continue
                
                break  # 找到商品后退出循环
        
        if debug:
            print(f"[_crawl_xianyu_page] 共提取 {len(items)} 个商品")
        
    except Exception as e:
        if debug:
            print(f"[_crawl_xianyu_page] 爬取商品时出错: {e}")
        import traceback
        traceback.print_exc()
    
    return items


def search_xianyu_images_with_keywords(
    keyword: str,
    required_keywords: List[str] = None,
    debug: bool = False,
    context=None,
) -> List[Dict]:
    """
    搜索闲鱼商品图片，根据关键词匹配逻辑处理分页
    
    参数:
    - keyword: 搜索关键词（用于闲鱼搜索）
    - required_keywords: 必须全部出现在标题中的关键词列表（用于筛选）
    - debug: 是否打印调试信息
    - context: 可选的浏览器上下文
    
    返回:
    - 商品列表，每个商品包含 title, price_text, price_value, image_url, link
    """
    if required_keywords is None:
        required_keywords = []
    
    all_items = []
    own_context = context is None
    page = None
    
    try:
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
                print("[search_xianyu_images_with_keywords] 页面创建失败")
            return []
        
        # 访问闲鱼首页
        if not _safe_goto(page, XIANYU_URL, debug=debug):
            if debug:
                print("[search_xianyu_images_with_keywords] 无法访问闲鱼首页")
            return []
        
        # 爬取第一页
        page1_items = _crawl_xianyu_page(page, keyword, page_num=1, debug=debug)
        
        # 筛选匹配所有关键词的商品
        matched_items = []
        for item in page1_items:
            if _matches_all_keywords(item["title"], required_keywords):
                matched_items.append(item)
        
        if debug:
            print(f"[search_xianyu_images_with_keywords] 第一页共 {len(page1_items)} 个商品，其中 {len(matched_items)} 个匹配所有关键词")
        
        # 决策逻辑
        if len(matched_items) >= 10:
            if debug:
                print(f"[search_xianyu_images_with_keywords] 第一页有 {len(matched_items)} 个匹配商品，>=10，只处理第一页")
            # 只使用第一页的匹配商品
            all_matched = matched_items
            # 按价格排序（从低到高）
            all_matched.sort(key=lambda x: x["price_value"])
            # 取前5个
            result = all_matched[:5]
        else:
            if debug:
                print(f"[search_xianyu_images_with_keywords] 第一页只有 {len(matched_items)} 个匹配商品，<10，爬取第二页")
            # 爬取第二页
            page2_items = _crawl_xianyu_page(page, keyword, page_num=2, debug=debug)
            
            # 筛选第二页匹配的商品
            page2_matched = []
            for item in page2_items:
                if _matches_all_keywords(item["title"], required_keywords):
                    page2_matched.append(item)
            
            if debug:
                print(f"[search_xianyu_images_with_keywords] 第二页共 {len(page2_items)} 个商品，其中 {len(page2_matched)} 个匹配所有关键词")
            
            # 合并第一页和第二页的匹配商品
            all_matched = matched_items + page2_matched
            # 按价格排序（从低到高）
            all_matched.sort(key=lambda x: x["price_value"])
            # 取前5个（如果用户想要所有商品，可以注释掉这行）
            result = all_matched[:5] if len(all_matched) > 5 else all_matched
        
        if debug:
            print(f"[search_xianyu_images_with_keywords] 最终返回 {len(result)} 个商品")
        
        return result
            
    except Exception as e:
        if debug:
            print(f"[search_xianyu_images_with_keywords] 搜索过程中出错: {e}")
        import traceback
        traceback.print_exc()
        return []
    
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


def test_xianyu_image_crawler():
    """测试闲鱼图片爬取功能"""
    print("=" * 80)
    print("测试闲鱼图片爬取功能")
    print("=" * 80)
    
    # 测试参数
    keyword = "初音未来粘土人"
    required_keywords = ["初音未来", "粘土人"]  # 标题必须同时包含这些关键词
    
    print(f"搜索关键词: {keyword}")
    print(f"必须包含的关键词: {required_keywords}")
    print("-" * 80)
    
    start_time = time.time()
    
    try:
        items = search_xianyu_images_with_keywords(
            keyword=keyword,
            required_keywords=required_keywords,
            debug=True
        )
        
        end_time = time.time()
        search_time = end_time - start_time
        
        print("-" * 80)
        print(f"搜索完成!")
        print(f"总耗时: {search_time:.2f}秒")
        print(f"找到商品数量: {len(items)}")
        
        # 显示结果
        if items:
            print("\n找到的商品结果:")
            for i, item in enumerate(items, 1):
                title_preview = item['title'][:50] + "..." if len(item['title']) > 50 else item['title']
                print(f"{i}. 商品")
                print(f"   标题: {title_preview}")
                print(f"   价格: {item['price_text']} (数值: {item['price_value']})")
                if item.get('link'):
                    link_preview = item['link'][:60] + "..." if len(item['link']) > 60 else item['link']
                    print(f"   链接: {link_preview}")
                if item.get('image_url'):
                    img_preview = item['image_url'][:80] + "..." if len(item['image_url']) > 80 else item['image_url']
                    print(f"   图片: {img_preview}")
                print()
        else:
            print("未找到符合条件的商品")
            
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 80)


if __name__ == "__main__":
    test_xianyu_image_crawler()