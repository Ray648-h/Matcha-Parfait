# -*- coding: utf-8 -*-
"""
新的搜索逻辑：先搜索店铺，然后点进去店铺，再搜索商品
"""

import re
import random
import time
from typing import Dict, List, Optional
from urllib.parse import quote_plus, urlencode, urlparse, urlunparse

from config.context import BrowserManager
from config.settings import TAOBAO_URL
from service.login_service import LoginService


# 配置参数
REQUEST_RETRY = 4
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


def _search_and_click_shop(page, shop_name: str, debug: bool = False) -> bool:
    """
    搜索店铺并点击进入
    返回：是否成功进入店铺页面
    """
    # 构建店铺搜索URL
    search_url = f"https://shopsearch.taobao.com/search?app=shopsearch&q={quote_plus(shop_name)}"
    
    if debug:
        print(f"[_search_and_click_shop] 搜索店铺: {shop_name}")
    
    # 访问店铺搜索页面
    if not _safe_goto(page, search_url, debug=debug):
        if debug:
            print(f"[_search_and_click_shop] 无法访问店铺搜索页: {shop_name}")
        return False
    
    # 等待页面加载
    page.wait_for_timeout(4000)
    
    # 查找店铺链接 - 尝试多种方法
    try:
        # 方法1：查找包含店铺名的链接
        shop_links = page.locator(f"a:has-text('{shop_name}')")
        count = shop_links.count()
        
        if count == 0:
            # 方法2：尝试部分匹配
            if len(shop_name) > 4:
                for i in range(4, len(shop_name)):
                    partial_name = shop_name[:i]
                    shop_links = page.locator(f"a:has-text('{partial_name}')")
                    count = shop_links.count()
                    if count > 0:
                        break
        
        if count == 0:
            # 方法3：查找店铺卡片或列表项
            shop_selectors = [
                "div.shop-item", "li.shop-item", "div[class*='shop']",
                "div[class*='store']", "a[href*='shop']", "a[href*='store']"
            ]
            
            for selector in shop_selectors:
                elements = page.locator(selector)
                if elements.count() > 0:
                    # 点击第一个找到的元素
                    elements.first.click()
                    page.wait_for_timeout(3000)
                    if debug:
                        print(f"[_search_and_click_shop] 通过选择器 {selector} 进入店铺: {shop_name}")
                    return True
        
        if count > 0:
            # 点击第一个匹配的链接
            shop_links.first.click()
            page.wait_for_timeout(3000)  # 等待店铺页面加载
            
            if debug:
                print(f"[_search_and_click_shop] 成功进入店铺: {shop_name}")
            return True
        else:
            if debug:
                print(f"[_search_and_click_shop] 未找到店铺链接: {shop_name}")
                # 尝试获取页面内容帮助调试
                try:
                    content = page.content()[:2000]
                    print(f"[_search_and_click_shop] 页面内容片段: {content}")
                except:
                    pass
            return False
    except Exception as e:
        if debug:
            print(f"[_search_and_click_shop] 点击店铺时出错: {e}")
        return False


def _search_in_shop(page, shop_name: str, keyword: str, debug: bool = False) -> List[Dict]:
    """
    在店铺内搜索商品
    返回：商品列表
    """
    items = []
    
    if debug:
        print(f"[_search_in_shop] 在店铺 {shop_name} 中搜索: {keyword}")
    
    try:
        # 根据用户提供的HTML结构查找搜索框
        # 尝试多种选择器
        search_selectors = [
            "input[name='q']",  # 根据用户提供的 name='q'
            "input#mq",  # 根据用户提供的 id='mq'
            "input[title*='搜索']",
            "input[placeholder*='搜索']",
            "input[aria-label*='搜索']",
            ".s-combobox-input",  # 根据用户提供的 class
            "input[type='text'][name*='search']"
        ]
        
        search_input = None
        for selector in search_selectors:
            locator = page.locator(selector)
            if locator.count() > 0:
                search_input = locator.first
                if debug:
                    print(f"[_search_in_shop] 找到搜索框，选择器: {selector}")
                break
        
        if search_input:
            if debug:
                print(f"[_search_in_shop] 找到搜索框，准备输入关键词: {keyword}")
            
            # 输入关键词
            search_input.fill(keyword)
            page.wait_for_timeout(2000)
            
            # 查找搜索按钮
            # 根据用户提供的HTML：<button id="J_CurrShopBtn" class="currShopBtn">搜本店</button>
            btn_selectors = [
                "button#J_CurrShopBtn",  # 精确匹配用户提供的ID
                "button.currShopBtn",  # 精确匹配用户提供的class
                "button:has-text('搜本店')",  # 精确匹配按钮文本
                "button:has-text('搜索')",
                "button:has-text('Search')",
                "button[type='submit']",
                "#J_SearchBtn"  # 用户提供的另一个按钮ID
            ]
            
            search_btn = None
            for selector in btn_selectors:
                locator = page.locator(selector)
                if locator.count() > 0:
                    search_btn = locator.first
                    if debug:
                        print(f"[_search_in_shop] 找到搜索按钮，选择器: {selector}")
                    break
            
            if search_btn:
                # 点击搜索按钮
                if debug:
                    print(f"[_search_in_shop] 点击搜索按钮")
                search_btn.click()
                page.wait_for_timeout(5000)  # 等待搜索结果加载
                
                # 提取商品信息
                items = _extract_shop_items(page, shop_name, debug)
            else:
                if debug:
                    print(f"[_search_in_shop] 未找到搜索按钮，尝试按回车键")
                # 按回车键搜索
                search_input.press("Enter")
                page.wait_for_timeout(5000)
                items = _extract_shop_items(page, shop_name, debug)
        else:
            if debug:
                print(f"[_search_in_shop] 未找到搜索框: {shop_name}")
                # 打印页面HTML片段帮助调试
                try:
                    content = page.content()[:3000]
                    print(f"[_search_in_shop] 页面内容片段 (前3000字符):")
                    print(content)
                    
                    # 检查所有输入元素
                    all_inputs = page.locator("input")
                    input_count = all_inputs.count()
                    print(f"[_search_in_shop] 页面共有 {input_count} 个input元素")
                    
                    for i in range(min(input_count, 10)):
                        try:
                            input_elem = all_inputs.nth(i)
                            input_id = input_elem.get_attribute("id") or ""
                            input_name = input_elem.get_attribute("name") or ""
                            input_type = input_elem.get_attribute("type") or ""
                            input_placeholder = input_elem.get_attribute("placeholder") or ""
                            print(f"  Input {i}: id={input_id}, name={input_name}, type={input_type}, placeholder={input_placeholder}")
                        except:
                            pass
                except Exception as e:
                    print(f"[_search_in_shop] 调试时出错: {e}")
    except Exception as e:
        if debug:
            print(f"[_search_in_shop] 搜索商品时出错: {e}")
        import traceback
        traceback.print_exc()
    
    return items


def _extract_shop_items(page, shop_name: str, debug: bool = False) -> List[Dict]:
    """提取店铺商品信息"""
    items = []
    
    try:
        # 根据用户提供的HTML结构，使用更精确的选择器
        # 用户提供的HTML结构：<div class="cardContainer--CwazTl0O">
        item_selectors = [
            "div.cardContainer",  # 通用选择器
            "div[class*='cardContainer']",  # 包含cardContainer的类
            "div[class*='item']", 
            "div[class*='product']", 
            "div[class*='goods']",
            "li.item"
        ]
        
        for selector in item_selectors:
            item_elements = page.locator(selector)
            count = item_elements.count()
            
            if count > 0:
                if debug:
                    print(f"[_extract_shop_items] 找到 {count} 个商品元素，选择器: {selector}")
                
                for i in range(min(count, 20)):  # 最多处理20个商品
                    try:
                        item = item_elements.nth(i)
                        
                        # 提取整个HTML元素（用户要求）
                        html_content = ""
                        try:
                            html_content = item.evaluate("element => element.outerHTML")
                        except:
                            pass
                        
                        # 提取标题 - 根据用户提供的HTML：<div class="title--GExDBPUi">
                        title = ""
                        title_selectors = [
                            "div[class*='title']",  # 包含title的类
                            ".title--GExDBPUi",  # 用户提供的精确类名
                            "a[title]",
                            "div[class*='desc']",
                            "span[class*='title']"
                        ]
                        
                        for title_selector in title_selectors:
                            title_elem = item.locator(title_selector)
                            if title_elem.count() > 0:
                                title = title_elem.first.inner_text().strip()
                                if title:
                                    break
                        
                        if not title:
                            continue
                        
                        # 提取价格 - 根据用户提供的HTML：<div class="price--WtT08bds">
                        price = ""
                        price_selectors = [
                            "div[class*='price']",  # 包含price的类
                            ".price--WtT08bds",  # 用户提供的精确类名
                            "span[class*='price']",
                            "strong",
                            "em"
                        ]
                        
                        for price_selector in price_selectors:
                            price_elem = item.locator(price_selector)
                            if price_elem.count() > 0:
                                price = price_elem.first.inner_text().strip()
                                if price:
                                    break
                        
                        # 提取链接
                        link = ""
                        link_elem = item.locator("a[href]")
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
                            "shop": shop_name,
                            "price_text": price.strip() if price else "N/A",
                            "link": link,
                            "image": image,
                            "free_shipping": free_shipping,
                            "html_snippet": html_content[:500] + "..." if len(html_content) > 500 else html_content  # 限制长度
                        })
                        
                        if debug and len(items) <= 5:
                            print(f"[_extract_shop_items] 找到商品: {title[:40]}...")
                            if price:
                                print(f"    价格: {price}")
                            if html_content:
                                print(f"    HTML片段长度: {len(html_content)} 字符")
                            
                    except Exception as e:
                        if debug:
                            print(f"[_extract_shop_items] 提取商品 {i} 时出错: {e}")
                        continue
                
                break  # 找到商品后退出循环
    except Exception as e:
        if debug:
            print(f"[_extract_shop_items] 提取商品时出错: {e}")
    
    return items


def search_shops_directly(
    keyword: str,
    target_shops: List[str],
    pages: int = 1,
    debug: bool = False,
    context=None,
) -> List[Dict]:
    """
    直接搜索店铺并在店铺内搜索商品
    流程：
    1. 登录淘宝
    2. 对每个目标店铺：
        a. 搜索店铺
        b. 点击进入店铺
        c. 在店铺内搜索关键词
        d. 提取商品信息
    3. 返回所有商品
    """
    all_items = []
    own_context = context is None
    page = None
    
    try:
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
                print("[search_shops_directly] 页面创建失败")
            return all_items
        
        # 访问淘宝首页
        if not _safe_goto(page, TAOBAO_URL, debug=debug):
            if debug:
                print("[search_shops_directly] 无法访问淘宝首页")
            return all_items
        
        # 对每个店铺进行搜索
        for shop_index, shop_name in enumerate(target_shops):
            if debug:
                print(f"\n[search_shops_directly] 处理店铺 {shop_index+1}/{len(target_shops)}: {shop_name}")
            
            # 搜索并点击进入店铺
            if not _search_and_click_shop(page, shop_name, debug=debug):
                if debug:
                    print(f"[search_shops_directly] 无法进入店铺: {shop_name}")
                continue
            
            # 在店铺内搜索商品
            shop_items = _search_in_shop(page, shop_name, keyword, debug=debug)
            all_items.extend(shop_items)
            
            if debug:
                print(f"[search_shops_directly] 在店铺 {shop_name} 中找到 {len(shop_items)} 个商品")
            
            # 返回淘宝首页，准备搜索下一个店铺
            if shop_index < len(target_shops) - 1:
                if not _safe_goto(page, TAOBAO_URL, debug=debug):
                    if debug:
                        print("[search_shops_directly] 无法返回淘宝首页")
                    break
                
                _human_wait(page, SHORT_DELAY_RANGE_MS, reason="切换店铺间隔", debug=debug)
        
        if debug:
            print(f"\n[search_shops_directly] 搜索完成，共找到 {len(all_items)} 个商品")
        
        return all_items
        
    except Exception as e:
        if debug:
            print(f"[search_shops_directly] 搜索过程中出错: {e}")
        return all_items
    
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
def test_new_search():
    """测试新的搜索逻辑"""
    print("=" * 80)
    print("测试新的搜索逻辑：先搜索店铺，再在店铺内搜索商品")
    print("=" * 80)
    
    # 测试参数 - 使用用户指定的关键词
    keyword = "初音未来粘土人3.0"
    target_shops = ["gsc", "animate旗舰店"]  # 只测试2个店铺
    
    print(f"测试关键词: {keyword}")
    print(f"测试店铺: {target_shops}")
    print("-" * 80)
    
    start_time = time.time()
    
    try:
        items = search_shops_directly(
            keyword=keyword,
            target_shops=target_shops,
            pages=1,
            debug=True
        )
        
        end_time = time.time()
        search_time = end_time - start_time
        
        print("-" * 80)
        print(f"搜索完成!")
        print(f"总耗时: {search_time:.2f}秒")
        print(f"找到商品数量: {len(items)}")
        
        # 显示结果 - 包含HTML片段
        if items:
            print("\n搜索结果:")
            for i, item in enumerate(items[:5], 1):  # 只显示前5个结果
                title_preview = item['title'][:60] + "..." if len(item['title']) > 60 else item['title']
                print(f"{i}. 店铺: {item['shop']}")
                print(f"   标题: {title_preview}")
                print(f"   价格: {item['price_text']}")
                if item['image']:
                    print(f"   图片: {item['image'][:80]}...")
                if item['link']:
                    link_preview = item['link'][:70] + "..." if len(item['link']) > 70 else item['link']
                    print(f"   链接: {link_preview}")
                if item.get('html_snippet'):
                    print(f"   HTML片段预览: {item['html_snippet'][:100]}...")
                print()
            
            if len(items) > 5:
                print(f"... 还有 {len(items) - 5} 个结果未显示")
        else:
            print("未找到商品")
            
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 80)


if __name__ == "__main__":
    test_new_search()