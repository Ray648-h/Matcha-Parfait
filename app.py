#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手办价格比较机器人 - Web应用入口

前端文件位置：price_compare_bot/testfront/
后端API服务：集成登录服务和搜索服务
"""

import os
import sys
import json
import time
import traceback
from typing import Dict, List, Optional, Any
from pathlib import Path

# 添加项目路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS

# 导入项目模块 - 使用相对导入避免路径问题
try:
    # 尝试直接导入，如果失败则使用备用方案
    import importlib
    import sys
    import os
    
    # 添加price_compare_bot到路径
    price_bot_path = os.path.join(current_dir, 'price_compare_bot')
    if price_bot_path not in sys.path:
        sys.path.insert(0, price_bot_path)
    
    # 动态导入模块
    def try_import(module_path, module_name=None):
        try:
            module = importlib.import_module(module_path)
            if module_name:
                globals()[module_name] = module
            return module
        except ImportError:
            return None
    
    # 尝试导入各个模块
    login_service_module = try_import('service.login_service')
    if login_service_module:
        from service.login_service import LoginService
        print("成功导入LoginService")
    else:
        LoginService = None
        print("警告: 无法导入LoginService")
    
    hpoi_service_module = try_import('service.search.hpoi_search.hpoi_service')
    if hpoi_service_module:
        from service.search.hpoi_search.hpoi_service import search_hpoi_top_5
        print("成功导入HPOI服务")
    else:
        search_hpoi_top_5 = None
        print("警告: 无法导入HPOI服务")
    
    unified_models_module = try_import('service.search.unified_models')
    if unified_models_module:
        from service.search.unified_models import (
            UnifiedSearchResults, 
            SearchResult,
            create_unified_result,
            sort_results_by_shipping_and_price
        )
        print("成功导入统一模型")
    else:
        # 创建替代实现
        class SearchResult:
            def __init__(self, **kwargs):
                self.__dict__.update(kwargs)
            def to_dict(self):
                return self.__dict__
        
        def create_unified_result(**kwargs):
            return SearchResult(**kwargs)
        
        def sort_results_by_shipping_and_price(results, free_shipping_first=True):
            return sorted(results, key=lambda x: getattr(x, 'price', 0))
        
        print("警告: 使用简化版统一模型")
    
    # 尝试导入配置
    config_module = try_import('config.settings')
    if config_module:
        from config.settings import TAOBAO_URL, XIANYU_URL, WAJUEJI_URL
        print("成功导入配置")
    else:
        # 使用默认配置
        TAOBAO_URL = "https://www.taobao.com"
        XIANYU_URL = "https://www.goofish.com"
        WAJUEJI_URL = "https://www.meruki.cn/"
        print("使用默认配置")
    
    # 尝试导入淘宝搜索
    try:
        taobao_shop_module = try_import('service.search.taobao_shop.service')
        if taobao_shop_module:
            from service.search.taobao_shop.service import search_taobao_target_shops
            TAOBAO_AVAILABLE = True
            print("成功导入淘宝搜索")
        else:
            TAOBAO_AVAILABLE = False
            print("警告: 淘宝搜索模块导入失败")
    except Exception:
        TAOBAO_AVAILABLE = False
        print("警告: 淘宝搜索模块导入失败")
        
    # 尝试导入闲鱼搜索
    try:
        xianyu_module = try_import('service.search.xianyu.xianyu_service')
        if xianyu_module:
            from service.search.xianyu.xianyu_service import search_xianyu
            XIANYU_AVAILABLE = True
            print("成功导入闲鱼搜索")
        else:
            XIANYU_AVAILABLE = False
            print("警告: 闲鱼搜索模块导入失败")
    except Exception:
        XIANYU_AVAILABLE = False
        print("警告: 闲鱼搜索模块导入失败")
        
    # 尝试导入挖煤姬搜索
    WAJUEJI_AVAILABLE = False  # 暂时标记为不可用
    print("提示: 挖煤姬搜索暂未实现")
    
    # 设置BrowserManager占位符
    class BrowserManager:
        def launch_taobao(self):
            return None
    
except ImportError as e:
    print(f"导入项目模块失败: {e}")
    print("部分功能可能不可用")
    traceback.print_exc()
    # 设置默认值
    TAOBAO_AVAILABLE = False
    XIANYU_AVAILABLE = False
    WAJUEJI_AVAILABLE = False
    # 创建占位符类
    class LoginService:
        def __init__(self, context):
            pass
        def login(self, url, name):
            return None
    class BrowserManager:
        def launch_taobao(self):
            return None
    # 默认配置
    TAOBAO_URL = "https://www.taobao.com"
    XIANYU_URL = "https://www.goofish.com"
    WAJUEJI_URL = "https://www.meruki.cn/"
    search_hpoi_top_5 = None

# 初始化Flask应用
app = Flask(__name__, 
            static_folder=os.path.join(current_dir, 'price_compare_bot', 'testfront'),
            static_url_path='')
CORS(app)

# 全局状态
app_state = {
    'login_status': {
        'taobao': False,
        'xianyu': False,
        'wajueji': False,
        'hpoi': True  # HPOI不需要登录
    },
    'browser_manager': None,
    'login_service': None,
    'last_search_results': {}
}

# 配置
class Config:
    SECRET_KEY = 'price_compare_bot_secret_key_2024'
    FRONTEND_FOLDER = os.path.join(current_dir, 'price_compare_bot', 'testfront')
    DEBUG = True

app.config.from_object(Config)

# 确保前端目录存在
os.makedirs(Config.FRONTEND_FOLDER, exist_ok=True)

# ========== 工具函数 ==========

def get_browser_manager():
    """获取浏览器管理器（单例）"""
    if app_state['browser_manager'] is None:
        try:
            app_state['browser_manager'] = BrowserManager()
        except Exception as e:
            print(f"初始化浏览器管理器失败: {e}")
            return None
    return app_state['browser_manager']

def get_login_service():
    """获取登录服务"""
    if app_state['login_service'] is None:
        browser_manager = get_browser_manager()
        if browser_manager:
            try:
                app_state['login_service'] = LoginService(browser_manager.launch_taobao())
            except Exception as e:
                print(f"初始化登录服务失败: {e}")
                return None
    return app_state['login_service']

def check_platform_availability(platforms: List[str]) -> Dict[str, bool]:
    """检查平台可用性"""
    availability = {
        'taobao': TAOBAO_AVAILABLE,
        'xianyu': XIANYU_AVAILABLE,
        'wajueji': WAJUEJI_AVAILABLE,
        'hpoi': True  # HPOI总是可用
    }
    
    result = {}
    for platform in platforms:
        result[platform] = availability.get(platform, False)
    
    return result

def search_taobao_items(keyword: str, debug: bool = False) -> List[Dict]:
    """搜索淘宝商品"""
    if not TAOBAO_AVAILABLE:
        return []
    
    try:
        # 加载店铺URL
        from price_compare_bot.service.search.taobao_shop.shop_loader import load_shop_urls
        shop_urls = load_shop_urls()
        target_shops = list(shop_urls.keys())[:5]  # 限制店铺数量提高性能
        
        # 执行搜索
        items = search_taobao_target_shops(
            keyword=keyword,
            target_shops=target_shops,
            pages=1,  # 只搜索第一页
            debug=debug
        )
        
        return items
    except Exception as e:
        print(f"淘宝搜索失败: {e}")
        traceback.print_exc()
        return []

def search_xianyu_items(keyword: str, debug: bool = False) -> List[Dict]:
    """搜索闲鱼商品"""
    if not XIANYU_AVAILABLE:
        return []
    
    try:
        items = search_xianyu(keyword, max_results=20)
        return items
    except Exception as e:
        print(f"闲鱼搜索失败: {e}")
        traceback.print_exc()
        return []

def search_hpoi_items(keyword: str, debug: bool = False) -> Dict[str, Any]:
    """搜索HPOI商品"""
    try:
        # 获取前5个商品
        results = search_hpoi_top_5(keyword, debug=debug)
        
        if not results:
            return {
                'best': None,
                'recommendations': []
            }
        
        # 第一个作为最佳商品
        best_result = results[0] if results else None
        
        # 剩余4个作为推荐商品
        recommendations = results[1:5] if len(results) > 1 else []
        
        return {
            'best': best_result,
            'recommendations': recommendations
        }
    except Exception as e:
        print(f"HPOI搜索失败: {e}")
        traceback.print_exc()
        return {
            'best': None,
            'recommendations': []
        }

def sort_results(results: List[Dict], order: str = 'desc', free_shipping_first: bool = True) -> List[Dict]:
    """排序搜索结果"""
    if not results:
        return []
    
    # 转换为SearchResult对象
    search_results = []
    for item in results:
        try:
            # 根据平台处理数据
            if isinstance(item, SearchResult):
                search_results.append(item)
            else:
                # 创建统一的SearchResult
                result = create_unified_result(
                    platform=item.get('platform', 'unknown'),
                    title=item.get('title', ''),
                    price=float(item.get('price', 0)),
                    shipping_fee=float(item.get('shipping_fee', 0)),
                    is_free_shipping=item.get('is_free_shipping', False),
                    image_url=item.get('image_url', ''),
                    detail_url=item.get('detail_url', ''),
                    shop_name=item.get('shop_name', ''),
                    release_date=item.get('release_date', ''),
                    score=item.get('score', 0),
                    raw_data=item
                )
                search_results.append(result)
        except Exception as e:
            print(f"转换搜索结果失败: {e}")
            continue
    
    # 排序
    sorted_results = sort_results_by_shipping_and_price(
        search_results, 
        free_shipping_first=free_shipping_first
    )
    
    # 按升降序调整
    if order == 'desc':
        sorted_results = list(reversed(sorted_results))
    
    # 转换回字典
    return [r.to_dict() for r in sorted_results]

# ========== 路由 ==========

@app.route('/')
def index():
    """主页"""
    return send_from_directory(app.config['FRONTEND_FOLDER'], 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    """静态文件服务"""
    return send_from_directory(app.config['FRONTEND_FOLDER'], path)

# ========== API路由 ==========

@app.route('/api/check-login', methods=['GET'])
def api_check_login():
    """检查登录状态"""
    try:
        # 这里可以添加实际的登录状态检查逻辑
        # 目前返回默认状态
        return jsonify({
            'success': True,
            'status': app_state['login_status'],
            'message': '登录状态获取成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'检查登录状态失败: {str(e)}'
        }), 500

@app.route('/api/login', methods=['POST'])
def api_login():
    """登录平台"""
    try:
        data = request.get_json()
        platforms = data.get('platforms', ['taobao', 'xianyu', 'wajueji'])
        
        # 这里应该调用实际的登录服务
        # 目前模拟登录过程
        print(f"开始登录平台: {platforms}")
        
        # 模拟登录成功
        for platform in platforms:
            if platform in app_state['login_status']:
                app_state['login_status'][platform] = True
        
        return jsonify({
            'success': True,
            'message': '登录流程已启动，请按照浏览器提示完成登录',
            'status': app_state['login_status']
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'登录失败: {str(e)}'
        }), 500

@app.route('/api/search', methods=['POST'])
def api_search():
    """搜索商品"""
    start_time = time.time()
    
    try:
        data = request.get_json()
        keyword = data.get('keyword', '').strip()
        platforms = data.get('platforms', ['hpoi'])
        sort_options = data.get('sort', {
            'order': 'desc',
            'freeShippingFirst': True
        })
        
        if not keyword:
            return jsonify({
                'success': False,
                'message': '请输入搜索关键词'
            }), 400
        
        print(f"搜索请求: 关键词='{keyword}', 平台={platforms}, 排序={sort_options}")
        
        # 检查平台可用性
        availability = check_platform_availability(platforms)
        unavailable_platforms = [p for p, avail in availability.items() if not avail]
        
        if unavailable_platforms:
            print(f"平台不可用: {unavailable_platforms}")
        
        # 收集所有搜索结果
        all_results = []
        hpoi_results = None
        
        # HPOI搜索（总是执行）
        print(f"开始HPOI搜索: {keyword}")
        hpoi_data = search_hpoi_items(keyword, debug=False)
        hpoi_results = hpoi_data
        
        # 转换HPOI结果为统一格式
        if hpoi_data.get('best'):
            best_item = hpoi_data['best']
            all_results.append({
                'platform': 'hpoi',
                'title': best_item.get('title', ''),
                'price': float(best_item.get('price', 0)),
                'shipping_fee': 0.0,
                'is_free_shipping': True,
                'image_url': best_item.get('image_url', ''),
                'detail_url': best_item.get('link', ''),
                'release_date': best_item.get('release_date', ''),
                'score': best_item.get('score', 0),
                'shop_name': 'HPOI'
            })
        
        # 其他平台搜索
        for platform in platforms:
            if platform == 'hpoi':
                # HPOI已经处理过了
                continue
                
            if not availability.get(platform, False):
                continue
                
            print(f"开始{platform}搜索: {keyword}")
            
            try:
                if platform == 'taobao':
                    items = search_taobao_items(keyword, debug=False)
                    # 转换为统一格式
                    for item in items:
                        all_results.append({
                            'platform': 'taobao',
                            'title': item.get('title', ''),
                            'price': float(item.get('price', 0) if item.get('price') else 0),
                            'shipping_fee': 0.0,  # 需要从实际数据中提取
                            'is_free_shipping': '包邮' in item.get('title', '') or '包邮' in item.get('price_text', ''),
                            'image_url': item.get('image', ''),
                            'detail_url': item.get('link', ''),
                            'shop_name': item.get('shop', ''),
                            'score': item.get('score', 0),
                            'raw_data': item
                        })
                        
                elif platform == 'xianyu':
                    items = search_xianyu_items(keyword, debug=False)
                    # 转换为统一格式
                    for item in items:
                        all_results.append({
                            'platform': 'xianyu',
                            'title': item.get('title', ''),
                            'price': float(item.get('price', 0) if item.get('price') else 0),
                            'shipping_fee': 0.0,  # 需要从实际数据中提取
                            'is_free_shipping': '包邮' in item.get('title', '') or '包邮' in item.get('price_text', ''),
                            'image_url': item.get('image', ''),
                            'detail_url': item.get('link', ''),
                            'shop_name': item.get('seller', ''),
                            'raw_data': item
                        })
                        
                elif platform == 'wajueji':
                    # 挖煤姬搜索暂未实现
                    print(f"平台 {platform} 搜索暂未实现")
                    continue
                    
            except Exception as e:
                print(f"{platform}搜索出错: {e}")
                traceback.print_exc()
                continue
        
        # 排序结果
        sorted_results = sort_results(
            all_results,
            order=sort_options.get('order', 'desc'),
            free_shipping_first=sort_options.get('freeShippingFirst', True)
        )
        
        # 准备HPOI数据
        hpoi_best = None
        hpoi_recommendations = []
        
        if hpoi_results:
            if hpoi_results.get('best'):
                best = hpoi_results['best']
                hpoi_best = {
                    'title': best.get('title', ''),
                    'price': float(best.get('price', 0)),
                    'release_date': best.get('release_date', ''),
                    'image_url': best.get('image_url', ''),
                    'link': best.get('link', ''),
                    'score': best.get('score', 0)
                }
            
            if hpoi_results.get('recommendations'):
                for rec in hpoi_results['recommendations']:
                    hpoi_recommendations.append({
                        'title': rec.get('title', ''),
                        'price': float(rec.get('price', 0)),
                        'image_url': rec.get('image_url', ''),
                        'link': rec.get('link', ''),
                        'score': rec.get('score', 0)
                    })
        
        elapsed_time = time.time() - start_time
        
        print(f"搜索完成: 找到 {len(sorted_results)} 个结果，耗时 {elapsed_time:.2f} 秒")
        
        # 保存到全局状态（用于调试）
        app_state['last_search_results'][keyword] = {
            'results': sorted_results,
            'hpoi_best': hpoi_best,
            'hpoi_recommendations': hpoi_recommendations,
            'timestamp': time.time()
        }
        
        return jsonify({
            'success': True,
            'results': sorted_results,
            'hpoiBest': hpoi_best,
            'hpoiRecommendations': hpoi_recommendations,
            'stats': {
                'total': len(sorted_results),
                'platform_counts': {},
                'time': elapsed_time
            },
            'message': f'找到 {len(sorted_results)} 个结果'
        })
        
    except Exception as e:
        print(f"搜索API出错: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'搜索失败: {str(e)}'
        }), 500

@app.route('/api/status', methods=['GET'])
def api_status():
    """获取服务状态"""
    return jsonify({
        'success': True,
        'status': {
            'server': 'running',
            'timestamp': time.time(),
            'frontend': os.path.exists(app.config['FRONTEND_FOLDER']),
            'modules': {
                'taobao': TAOBAO_AVAILABLE,
                'xianyu': XIANYU_AVAILABLE,
                'wajueji': WAJUEJI_AVAILABLE,
                'hpoi': True
            },
            'login_status': app_state['login_status']
        }
    })

@app.route('/api/debug/search', methods=['GET'])
def api_debug_search():
    """调试搜索 - 返回示例数据"""
    # 生成示例数据用于测试
    import random
    
    keyword = request.args.get('keyword', '示例手办')
    platforms = request.args.get('platforms', 'taobao,xianyu,hpoi').split(',')
    
    example_results = []
    
    # HPOI示例
    if 'hpoi' in platforms:
        example_results.append({
            'platform': 'hpoi',
            'title': f'Good Smile Company {keyword} 1/7 比例手办',
            'price': 899.00,
            'shipping_fee': 0.0,
            'is_free_shipping': True,
            'image_url': 'https://via.placeholder.com/300x200/FFD700/000000?text=HPOI+Best',
            'detail_url': 'https://example.com/hpoi/item123',
            'release_date': '2024-12-31',
            'score': 95,
            'shop_name': 'HPOI官方'
        })
    
    # 淘宝示例
    if 'taobao' in platforms:
        for i in range(1, 4):
            price = random.randint(500, 1200)
            example_results.append({
                'platform': 'taobao',
                'title': f'{keyword} 正版手办 1/7比例 全新未拆 {i}',
                'price': float(price),
                'shipping_fee': 0.0 if random.random() > 0.5 else 15.0,
                'is_free_shipping': random.random() > 0.5,
                'image_url': f'https://via.placeholder.com/300x200/FF6B6B/FFFFFF?text=淘宝+{i}',
                'detail_url': f'https://item.taobao.com/item{i}.html',
                'shop_name': f'手办专卖店{i}',
                'score': random.randint(70, 90)
            })
    
    # 闲鱼示例
    if 'xianyu' in platforms:
        for i in range(1, 3):
            price = random.randint(400, 1000)
            example_results.append({
                'platform': 'xianyu',
                'title': f'【二手】{keyword} 手办 9成新 盒子完好 {i}',
                'price': float(price),
                'shipping_fee': 0.0 if random.random() > 0.3 else 12.0,
                'is_free_shipping': random.random() > 0.3,
                'image_url': f'https://via.placeholder.com/300x200/4ECDC4/FFFFFF?text=闲鱼+{i}',
                'detail_url': f'https://2.taobao.com/item{i}.html',
                'shop_name': f'个人卖家{i}',
                'score': random.randint(60, 85)
            })
    
    # HPOI最佳商品示例
    hpoi_best = {
        'title': f'Good Smile Company {keyword} 限定版 1/7 比例手办',
        'price': 1299.00,
        'release_date': '2024-12-25',
        'image_url': 'https://via.placeholder.com/400x300/FFD700/000000?text=HPOI+限定版',
        'link': 'https://example.com/hpoi/best123',
        'score': 98
    }
    
    # HPOI推荐商品示例
    hpoi_recommendations = []
    for i in range(1, 5):
        hpoi_recommendations.append({
            'title': f'{keyword} 相关手办 {i} 特别版',
            'price': float(random.randint(800, 1500)),
            'image_url': f'https://via.placeholder.com/250x150/FAD961/000000?text=推荐+{i}',
            'link': f'https://example.com/hpoi/rec{i}',
            'score': random.randint(80, 95)
        })
    
    return jsonify({
        'success': True,
        'results': example_results,
        'hpoiBest': hpoi_best,
        'hpoiRecommendations': hpoi_recommendations,
        'stats': {
            'total': len(example_results),
            'time': 1.5
        },
        'message': f'示例数据: {len(example_results)} 个结果'
    })

# ========== 启动应用 ==========

if __name__ == '__main__':
    print("=" * 60)
    print("手办价格比较机器人 Web应用")
    print("=" * 60)
    print(f"前端目录: {app.config['FRONTEND_FOLDER']}")
    print(f"模块状态: 淘宝={TAOBAO_AVAILABLE}, 闲鱼={XIANYU_AVAILABLE}, HPOI=可用")
    print("=" * 60)
    print("启动服务器...")
    
    # 检查前端文件
    index_path = os.path.join(app.config['FRONTEND_FOLDER'], 'index.html')
    if not os.path.exists(index_path):
        print(f"警告: 前端文件不存在: {index_path}")
        print("前端文件将在 price_compare_bot/testfront/ 目录下生成")
    
    # 启动Flask应用
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)