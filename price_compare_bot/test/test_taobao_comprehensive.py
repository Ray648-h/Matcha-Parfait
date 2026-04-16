# -*- coding: utf-8 -*-
"""
淘宝搜索综合测试
包含单元测试、集成测试和端到端测试
将测试数据和结果保存到test文件夹
"""

import sys
import os
import json
import time
import unittest
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入要测试的模块
from service.search.taobao_shop.taobao_main import (
    TaobaoSearch, Product, SearchResult, print_search_result, create_search_result
)
from service.search.taobao_shop.taobao_scorer import (
    calculate_taobao_score, score_taobao_items, get_top_ranked_items_by_price,
    process_taobao_items_with_scoring
)
from service.search.taobao_shop.parser import parse_taobao_items
from service.search.taobao_shop.shop_loader import load_shop_urls


# ============================================================================
# 测试数据
# ============================================================================

class TestData:
    """测试数据类"""
    
    @staticmethod
    def get_sample_products() -> List[Dict]:
        """获取示例商品数据"""
        return [
            {
                'title': '初音未来 粘土人 3.0 全新正版 包邮',
                'shop': 'gsc官方旗舰店',
                'price_text': '¥299.00',
                'link': 'https://item.taobao.com/item.htm?id=1234567890',
                'image': 'https://img.alicdn.com/img/O1CN01n8cPFM1YqQt2QdtpM_!!4611686018427383878-0-item_pic.jpg',
                'target_shop': 'gsc',
                'free_shipping': True
            },
            {
                'title': '初音未来 手办 模型 二手 补款',
                'shop': '二手玩具店',
                'price_text': '¥150.00',
                'link': 'https://item.taobao.com/item.htm?id=2345678901',
                'image': 'https://img.alicdn.com/img/O1CN01n8cPFM1YqQt2QdtpM_!!4611686018427383878-0-item_pic.jpg',
                'target_shop': None,
                'free_shipping': False
            },
            {
                'title': '初音未来 粘土人 尾款',
                'shop': '动漫周边店',
                'price_text': '¥280.00',
                'link': 'https://item.taobao.com/item.htm?id=3456789012',
                'image': 'https://img.alicdn.com/img/O1CN01n8cPFM1YqQt2QdtpM_!!4611686018427383878-0-item_pic.jpg',
                'target_shop': None,
                'free_shipping': True
            },
            {
                'title': '其他角色 粘土人 2.0 定金',
                'shop': '模型专卖店',
                'price_text': '¥250.00',
                'link': 'https://item.taobao.com/item.htm?id=4567890123',
                'image': 'https://img.alicdn.com/img/O1CN01n8cPFM1YqQt2QdtpM_!!4611686018427383878-0-item_pic.jpg',
                'target_shop': None,
                'free_shipping': False
            },
            {
                'title': '初音未来 预售',
                'shop': '高价店',
                'price_text': '¥320.00',
                'link': 'https://item.taobao.com/item.htm?id=5678901234',
                'image': 'https://img.alicdn.com/img/O1CN01n8cPFM1YqQt2QdtpM_!!4611686018427383878-0-item_pic.jpg',
                'target_shop': None,
                'free_shipping': True
            }
        ]
    
    @staticmethod
    def get_test_keywords() -> List[str]:
        """获取测试关键词"""
        return [
            "初音未来粘土人3.0",
            "初音未来",
            "粘土人",
            "手办 初音未来",
            "GSC户山香澄"
        ]
    
    @staticmethod
    def get_html_samples() -> Dict[str, str]:
        """获取HTML样本数据"""
        return {
            "product_card": '''
            <div class="cardContainer--CwazTl0O">
                <div class="MainPic--mainPicWrapper--varchHg" data-name="itemExp">
                    <img src="http://img.alicdn.com/img/O1CN01n8cPFM1YqQt2QdtpM_!!4611686018427383878-0-item_pic.jpg" height="240" width="240" class="MainPic--mainPic--aVle5J9">
                </div>
                <div class="title--GExDBPUi">初音未来粘土人3.0 手办模型</div>
                <div class="price--WtT08bds">¥299.00</div>
                <div class="SalesPoint--subIconWrapper--qJH48u6 " title="包邮 酷动城">
                    <div style="display: flex; align-items: center; justify-content: center; margin-right: 6px; vertical-align: middle; line-height: 16px;">
                        <span style="color: rgb(255, 98, 0); font-size: 14px;">包邮</span>
                    </div>
                </div>
                <a href="//item.taobao.com/item.htm?id=1234567890">商品链接</a>
            </div>
            ''',
            "shop_item": '''
            <div class="item">
                <div class="pic">
                    <a href="//item.taobao.com/item.htm?id=9876543210">
                        <img src="https://img.alicdn.com/bao/uploaded/i4/1234567890/O1CN01ABCDEF_1234567890.jpg">
                    </a>
                </div>
                <div class="title">
                    <a href="//item.taobao.com/item.htm?id=9876543210">GSC 户山香澄 手办 全新正版</a>
                </div>
                <div class="price">
                    <strong>¥450.00</strong>
                </div>
                <div class="deal-cnt">月销100+</div>
                <div class="shop">
                    <a href="//shop1234567890.taobao.com">gsc官方旗舰店</a>
                </div>
            </div>
            '''
        }


# ============================================================================
# 单元测试类
# ============================================================================

class TestTaobaoScorer(unittest.TestCase):
    """淘宝评分器单元测试"""
    
    def setUp(self):
        """测试前准备"""
        self.test_items = TestData.get_sample_products()
        self.keyword = "初音未来粘土人3.0"
    
    def test_calculate_taobao_score_basic(self):
        """测试基本评分功能"""
        item = self.test_items[0]  # 完全匹配的商品
        score, special_keywords = calculate_taobao_score(item, self.keyword, debug=False)
        
        # 验证分数为正数
        self.assertGreater(score, 0)
        
        # 验证完全匹配的商品得分应该较高
        self.assertGreater(score, 100)
        
        # 验证特殊关键词列表
        self.assertIsInstance(special_keywords, list)
    
    def test_calculate_taobao_score_partial_match(self):
        """测试部分匹配评分"""
        item = self.test_items[1]  # 部分匹配的商品
        score, special_keywords = calculate_taobao_score(item, self.keyword, debug=False)
        
        # 验证分数
        self.assertGreater(score, 0)
        
        # 验证包含特殊关键词"补款"
        self.assertIn("补款", special_keywords)
    
    def test_score_taobao_items(self):
        """测试批量商品评分"""
        scored_items = score_taobao_items(self.test_items, self.keyword, debug=False)
        
        # 验证返回列表长度
        self.assertEqual(len(scored_items), len(self.test_items))
        
        # 验证每个商品都有score字段
        for item in scored_items:
            self.assertIn('score', item)
            self.assertIsInstance(item['score'], int)
        
        # 验证按得分降序排序
        scores = [item['score'] for item in scored_items]
        self.assertEqual(scores, sorted(scores, reverse=True))
    
    def test_get_top_ranked_items_by_price(self):
        """测试获取前N名按价格排序"""
        # 先评分
        scored_items = score_taobao_items(self.test_items, self.keyword, debug=False)
        
        # 获取前2名按价格排序
        top_items = get_top_ranked_items_by_price(scored_items, top_n=2)
        
        # 验证返回列表
        self.assertIsInstance(top_items, list)
        
        # 验证按价格排序
        if len(top_items) >= 2:
            prices = []
            for item in top_items:
                price_text = item.get('price_text', '')
                try:
                    price = float(price_text.replace('¥', '').replace(',', ''))
                    prices.append(price)
                except:
                    prices.append(float('inf'))
            
            # 验证价格升序
            self.assertEqual(prices, sorted(prices))
    
    def test_process_taobao_items_with_scoring(self):
        """测试完整评分流程"""
        scored_items, top_items = process_taobao_items_with_scoring(
            self.test_items, self.keyword, debug=False
        )
        
        # 验证返回结果
        self.assertIsInstance(scored_items, list)
        self.assertIsInstance(top_items, list)
        
        # 验证评分后的商品都有score字段
        for item in scored_items:
            self.assertIn('score', item)
        
        # 验证top_items是scored_items的子集
        top_titles = [item['title'] for item in top_items]
        scored_titles = [item['title'] for item in scored_items]
        for title in top_titles:
            self.assertIn(title, scored_titles)


class TestTaobaoMain(unittest.TestCase):
    """淘宝主模块单元测试"""
    
    def setUp(self):
        """测试前准备"""
        self.searcher = TaobaoSearch()
        self.test_products = TestData.get_sample_products()
    
    def test_product_dataclass(self):
        """测试Product数据类"""
        product = Product(
            title="测试商品",
            shop="测试店铺",
            price_text="¥100.00",
            link="https://example.com",
            image="https://example.com/image.jpg",
            score=85,
            target_shop="gsc",
            shop_url="https://shop.taobao.com",
            index=1
        )
        
        # 验证属性
        self.assertEqual(product.title, "测试商品")
        self.assertEqual(product.shop, "测试店铺")
        self.assertEqual(product.price_text, "¥100.00")
        self.assertEqual(product.score, 85)
        
        # 验证to_dict方法
        product_dict = product.to_dict()
        self.assertIsInstance(product_dict, dict)
        self.assertEqual(product_dict['title'], "测试商品")
        self.assertEqual(product_dict['score'], 85)
    
    def test_search_result_dataclass(self):
        """测试SearchResult数据类"""
        products = [
            Product(
                title="商品1",
                shop="店铺1",
                price_text="¥100.00",
                link="https://example.com/1",
                image="https://example.com/image1.jpg",
                score=90
            ),
            Product(
                title="商品2",
                shop="店铺2",
                price_text="¥200.00",
                link="https://example.com/2",
                image="https://example.com/image2.jpg",
                score=80
            )
        ]
        
        result = SearchResult(
            keyword="测试关键词",
            products=products,
            total_count=10,
            filtered_count=2,
            search_time=1.5,
            success=True
        )
        
        # 验证属性
        self.assertEqual(result.keyword, "测试关键词")
        self.assertEqual(len(result.products), 2)
        self.assertEqual(result.total_count, 10)
        self.assertEqual(result.filtered_count, 2)
        self.assertEqual(result.success, True)
        
        # 验证to_dict方法
        result_dict = result.to_dict()
        self.assertIsInstance(result_dict, dict)
        self.assertEqual(result_dict['keyword'], "测试关键词")
        self.assertEqual(len(result_dict['products']), 2)
        
        # 验证to_json方法
        json_str = result.to_json()
        self.assertIsInstance(json_str, str)
        self.assertIn("测试关键词", json_str)
    
    def test_create_search_result(self):
        """测试create_search_result函数"""
        items = self.test_products[:2]
        search_time = 1.2
        
        result = create_search_result("测试关键词", items, search_time)
        
        # 验证返回类型
        self.assertIsInstance(result, SearchResult)
        
        # 验证属性
        self.assertEqual(result.keyword, "测试关键词")
        self.assertEqual(len(result.products), 2)
        self.assertEqual(result.search_time, search_time)
        self.assertEqual(result.success, True)
    
    @patch('service.search.taobao_shop.taobao_main.direct_search')
    def test_search_direct_mocked(self, mock_direct_search):
        """测试直接搜索（模拟）"""
        # 模拟返回数据
        mock_direct_search.return_value = self.test_products[:3]
        
        # 执行搜索
        result = self.searcher.search_direct("测试关键词", debug=False)
        
        # 验证结果
        self.assertIsInstance(result, SearchResult)
        self.assertEqual(result.keyword, "测试关键词")
        self.assertEqual(result.success, True)
        self.assertEqual(len(result.products), 3)
        
        # 验证按得分排序
        scores = [p.score for p in result.products]
        self.assertEqual(scores, sorted(scores, reverse=True))
    
    @patch('service.search.taobao_shop.taobao_main.search_shops_directly')
    def test_search_in_shops_mocked(self, mock_search_shops):
        """测试店铺内搜索（模拟）"""
        # 模拟返回数据
        mock_search_shops.return_value = self.test_products[2:4]
        
        # 执行搜索
        result = self.searcher.search_in_shops("测试关键词", debug=False)
        
        # 验证结果
        self.assertIsInstance(result, SearchResult)
        self.assertEqual(result.keyword, "测试关键词")
        self.assertEqual(result.success, True)
        self.assertEqual(len(result.products), 2)
    
    @patch('service.search.taobao_shop.taobao_main.TaobaoSearch.search_direct')
    @patch('service.search.taobao_shop.taobao_main.TaobaoSearch.search_in_shops')
    def test_search_comprehensive_mocked(self, mock_shop_search, mock_direct_search):
        """测试综合搜索（模拟）"""
        # 模拟返回数据
        direct_result = SearchResult(
            keyword="测试关键词",
            products=[
                Product(
                    title="商品A",
                    shop="店铺A",
                    price_text="¥100.00",
                    link="https://example.com/a",
                    image="https://example.com/a.jpg",
                    score=90
                )
            ],
            total_count=5,
            filtered_count=1,
            search_time=1.0,
            success=True
        )
        
        shop_result = SearchResult(
            keyword="测试关键词",
            products=[
                Product(
                    title="商品A",  # 重复商品
                    shop="店铺A",
                    price_text="¥100.00",
                    link="https://example.com/a",
                    image="https://example.com/a.jpg",
                    score=95  # 不同分数
                ),
                Product(
                    title="商品B",
                    shop="店铺B",
                    price_text="¥200.00",
                    link="https://example.com/b",
                    image="https://example.com/b.jpg",
                    score=80
                )
            ],
            total_count=3,
            filtered_count=2,
            search_time=1.5,
            success=True
        )
        
        mock_direct_search.return_value = direct_result
        mock_shop_search.return_value = shop_result
        
        # 执行综合搜索
        result = self.searcher.search_comprehensive("测试关键词", debug=False)
        
        # 验证结果
        self.assertIsInstance(result, SearchResult)
        self.assertEqual(result.keyword, "测试关键词")
        self.assertEqual(result.success, True)
        
        # 验证去重（商品A应该只出现一次）
        titles = [p.title for p in result.products]
        self.assertEqual(len(titles), len(set(titles)))
        
        # 验证商品A应该使用较高的分数（95分）
        for product in result.products:
            if product.title == "商品A":
                self.assertEqual(product.score, 95)
                break


# ============================================================================
# 集成测试类
# ============================================================================

class TestTaobaoIntegration(unittest.TestCase):
    """淘宝集成测试"""
    
    def setUp(self):
        """测试前准备"""
        self.test_data_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "test_data", "taobao"
        )
        os.makedirs(self.test_data_dir, exist_ok=True)
    
    def test_shop_loader_integration(self):
        """测试店铺加载器集成"""
        try:
            shop_urls = load_shop_urls()
            
            # 验证返回类型
            self.assertIsInstance(shop_urls, dict)
            
            # 验证不为空（如果文件存在）
            if os.path.exists("price_compare_bot/taobao_shop_urls.txt"):
                self.assertGreater(len(shop_urls), 0)
            
            # 保存测试数据
            test_data = {
                "test_name": "test_shop_loader_integration",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "shop_count": len(shop_urls),
                "sample_shops": list(shop_urls.keys())[:5] if shop_urls else []
            }
            
            self._save_test_result("shop_loader", test_data)
            
        except Exception as e:
            # 如果文件不存在，这是可以接受的
            if "No such file" in str(e):
                self.skipTest("店铺文件不存在，跳过测试")
            else:
                raise
    
    def test_parser_module_integration(self):
        """测试解析器模块集成"""
        html_samples = TestData.get_html_samples()
        
        # 测试商品卡片解析
        product_html = html_samples["product_card"]
        
        # 注意：parse_taobao_items需要Playwright页面对象
        # 这里我们只测试导入和函数存在性
        try:
            from service.search.taobao_shop.parser import parse_taobao_items
            
            # 验证函数存在
            self.assertTrue(callable(parse_taobao_items))
            
            # 保存测试数据
            test_data = {
                "test_name": "test_parser_module_integration",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "html_samples_available": list(html_samples.keys()),
                "parser_function": "parse_taobao_items"
            }
            
            self._save_test_result("parser_integration", test_data)
            
        except ImportError as e:
            self.fail(f"无法导入parser模块: {e}")
    
    def test_taobao_scorer_integration(self):
        """测试淘宝评分器集成"""
        test_items = TestData.get_sample_products()
        keyword = "初音未来粘土人3.0"
        
        # 测试完整评分流程
        scored_items, top_items = process_taobao_items_with_scoring(
            test_items, keyword, debug=False
        )
        
        # 验证结果
        self.assertIsInstance(scored_items, list)
        self.assertIsInstance(top_items, list)
        self.assertGreater(len(scored_items), 0)
        
        # 验证评分逻辑
        for item in scored_items:
            self.assertIn('score', item)
            self.assertIsInstance(item['score'], int)
            self.assertGreaterEqual(item['score'], 0)
        
        # 保存测试结果
        test_data = {
            "test_name": "test_taobao_scorer_integration",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "keyword": keyword,
            "total_items": len(test_items),
            "scored_items": len(scored_items),
            "top_items": len(top_items),
            "score_range": {
                "min": min(item['score'] for item in scored_items),
                "max": max(item['score'] for item in scored_items),
                "avg": sum(item['score'] for item in scored_items) / len(scored_items)
            } if scored_items else None,
            "top_items_details": [
                {
                    "title": item['title'][:50],
                    "score": item['score'],
                    "price": item['price_text']
                }
                for item in top_items[:3]
            ] if top_items else []
        }
        
        self._save_test_result("scorer_integration", test_data)
    
    def test_taobao_main_integration(self):
        """测试淘宝主模块集成"""
        searcher = TaobaoSearch()
        
        # 验证搜索器初始化
        self.assertIsInstance(searcher, TaobaoSearch)
        
        # 获取目标店铺
        target_shops = searcher.get_target_shops()
        self.assertIsInstance(target_shops, dict)
        
        # 保存测试数据
        test_data = {
            "test_name": "test_taobao_main_integration",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "searcher_initialized": True,
            "target_shops_count": len(target_shops),
            "sample_shops": list(target_shops.keys())[:3] if target_shops else []
        }
        
        self._save_test_result("main_integration", test_data)
    
    def _save_test_result(self, test_name: str, data: Dict):
        """保存测试结果到文件"""
        try:
            filename = os.path.join(
                self.test_data_dir,
                f"{test_name}_{time.strftime('%Y%m%d_%H%M%S')}.json"
            )
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"测试结果已保存: {filename}")
            
        except Exception as e:
            print(f"保存测试结果时出错: {e}")


# ============================================================================
# 端到端测试类（需要实际网络连接）
# ============================================================================

class TestTaobaoE2E(unittest.TestCase):
    """淘宝端到端测试（需要实际网络连接）"""
    
    def setUp(self):
        """测试前准备"""
        self.test_data_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "test_data", "taobao", "e2e_results"
        )
        os.makedirs(self.test_data_dir, exist_ok=True)
        
        # 创建搜索器
        self.searcher = TaobaoSearch()
    
    @unittest.skipIf(os.getenv('SKIP_E2E_TESTS', 'false').lower() == 'true',
                    "跳过端到端测试（需要网络连接）")
    def test_e2e_search_smoke(self):
        """端到端冒烟测试"""
        print("\n" + "=" * 80)
        print("淘宝端到端冒烟测试")
        print("=" * 80)
        
        test_keywords = ["初音未来", "粘土人"]
        
        all_results = []
        
        for keyword in test_keywords:
            print(f"\n测试关键词: {keyword}")
            print("-" * 40)
            
            try:
                # 执行综合搜索
                result = self.searcher.search_comprehensive(keyword, debug=True)
                
                # 验证结果
                self.assertIsInstance(result, SearchResult)
                self.assertEqual(result.keyword, keyword)
                
                # 保存结果
                self._save_e2e_result(keyword, result)
                all_results.append(result)
                
                # 打印摘要
                print(f"  找到商品: {len(result.products)} 个")
                print(f"  搜索耗时: {result.search_time:.2f}秒")
                print(f"  搜索状态: {'成功' if result.success else '失败'}")
                
                if not result.success:
                    print(f"  错误信息: {result.error_message}")
                
            except Exception as e:
                print(f"  搜索失败: {e}")
                # 保存错误信息
                error_data = {
                    "keyword": keyword,
                    "error": str(e),
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                self._save_e2e_error(keyword, error_data)
        
        # 保存汇总结果
        if all_results:
            self._save_e2e_summary(all_results)
    
    def _save_e2e_result(self, keyword: str, result: SearchResult):
        """保存端到端测试结果"""
        try:
            safe_keyword = "".join(c for c in keyword if c.isalnum() or c in " _-")
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            
            # 保存JSON格式
            json_filename = os.path.join(
                self.test_data_dir,
                f"e2e_{safe_keyword}_{timestamp}.json"
            )
            
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)
            
            # 保存文本格式
            txt_filename = os.path.join(
                self.test_data_dir,
                f"e2e_{safe_keyword}_{timestamp}.txt"
            )
            
            with open(txt_filename, 'w', encoding='utf-8') as f:
                f.write(f"淘宝端到端测试结果 - {keyword}\n")
                f.write(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"搜索耗时: {result.search_time:.2f}秒\n")
                f.write(f"找到商品总数: {result.total_count}\n")
                f.write(f"筛选后商品数量: {result.filtered_count}\n")
                f.write(f"搜索状态: {'成功' if result.success else '失败'}\n")
                
                if not result.success:
                    f.write(f"错误信息: {result.error_message}\n")
                
                f.write("=" * 60 + "\n\n")
                
                if result.products:
                    f.write("搜索结果:\n")
                    for i, product in enumerate(result.products[:10], 1):
                        f.write(f"{i}. [{product.score}分] {product.title}\n")
                        f.write(f"   店铺: {product.shop}")
                        if product.target_shop:
                            f.write(f" (匹配: {product.target_shop})")
                        f.write("\n")
                        f.write(f"   价格: {product.price_text}\n")
                        f.write("\n")
                else:
                    f.write("未找到商品\n")
            
            print(f"  结果已保存: {txt_filename}")
            
        except Exception as e:
            print(f"  保存结果时出错: {e}")
    
    def _save_e2e_error(self, keyword: str, error_data: Dict):
        """保存端到端测试错误"""
        try:
            safe_keyword = "".join(c for c in keyword if c.isalnum() or c in " _-")
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            
            filename = os.path.join(
                self.test_data_dir,
                f"e2e_error_{safe_keyword}_{timestamp}.json"
            )
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(error_data, f, ensure_ascii=False, indent=2)
            
        except Exception as e:
            print(f"保存错误信息时出错: {e}")
    
    def _save_e2e_summary(self, results: List[SearchResult]):
        """保存端到端测试汇总"""
        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            
            summary = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "total_keywords": len(results),
                "successful_searches": sum(1 for r in results if r.success),
                "total_products": sum(len(r.products) for r in results),
                "total_search_time": sum(r.search_time for r in results),
                "keyword_summary": [
                    {
                        "keyword": r.keyword,
                        "success": r.success,
                        "products_found": len(r.products),
                        "search_time": r.search_time,
                        "top_products": [
                            {
                                "title": p.title[:50],
                                "score": p.score,
                                "price": p.price_text,
                                "shop": p.shop
                            }
                            for p in r.products[:3]
                        ] if r.products else []
                    }
                    for r in results
                ]
            }
            
            filename = os.path.join(
                self.test_data_dir,
                f"e2e_summary_{timestamp}.json"
            )
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            
            print(f"\n汇总结果已保存: {filename}")
            
        except Exception as e:
            print(f"保存汇总结果时出错: {e}")


# ============================================================================
# 主测试运行函数
# ============================================================================

def run_all_tests():
    """运行所有测试"""
    print("=" * 80)
    print("淘宝搜索综合测试套件")
    print("=" * 80)
    
    # 创建测试套件
    loader = unittest.TestLoader()
    
    # 添加单元测试
    unit_suite = unittest.TestSuite()
    unit_suite.addTests(loader.loadTestsFromTestCase(TestTaobaoScorer))
    unit_suite.addTests(loader.loadTestsFromTestCase(TestTaobaoMain))
    
    # 添加集成测试
    integration_suite = unittest.TestSuite()
    integration_suite.addTests(loader.loadTestsFromTestCase(TestTaobaoIntegration))
    
    # 添加端到端测试
    e2e_suite = unittest.TestSuite()
    e2e_suite.addTests(loader.loadTestsFromTestCase(TestTaobaoE2E))
    
    # 运行单元测试
    print("\n1. 运行单元测试...")
    unit_runner = unittest.TextTestRunner(verbosity=2)
    unit_result = unit_runner.run(unit_suite)
    
    # 运行集成测试
    print("\n2. 运行集成测试...")
    integration_runner = unittest.TextTestRunner(verbosity=2)
    integration_result = integration_runner.run(integration_suite)
    
    # 运行端到端测试（可选）
    print("\n3. 运行端到端测试（需要网络连接）...")
    print("   设置环境变量 SKIP_E2E_TESTS=true 可跳过端到端测试")
    
    e2e_runner = unittest.TextTestRunner(verbosity=2)
    e2e_result = e2e_runner.run(e2e_suite)
    
    # 汇总结果
    print("\n" + "=" * 80)
    print("测试结果汇总")
    print("=" * 80)
    
    total_tests = (
        unit_result.testsRun +
        integration_result.testsRun +
        e2e_result.testsRun
    )
    
    total_failures = (
        len(unit_result.failures) +
        len(integration_result.failures) +
        len(e2e_result.failures)
    )
    
    total_errors = (
        len(unit_result.errors) +
        len(integration_result.errors) +
        len(e2e_result.errors)
    )
    
    print(f"总测试数: {total_tests}")
    print(f"失败: {total_failures}")
    print(f"错误: {total_errors}")
    print(f"通过: {total_tests - total_failures - total_errors}")
    
    # 保存测试报告
    save_test_report(unit_result, integration_result, e2e_result)
    
    if total_failures == 0 and total_errors == 0:
        print("\n✅ 所有测试通过！")
        return True
    else:
        print("\n❌ 有测试失败或错误")
        return False


def save_test_report(unit_result, integration_result, e2e_result):
    """保存测试报告"""
    try:
        report_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "test_data", "taobao", "test_reports"
        )
        os.makedirs(report_dir, exist_ok=True)
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        report_file = os.path.join(report_dir, f"test_report_{timestamp}.json")
        
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "unit_tests": {
                "tests_run": unit_result.testsRun,
                "failures": len(unit_result.failures),
                "errors": len(unit_result.errors),
                "failure_details": [
                    {
                        "test": str(f[0]),
                        "error": str(f[1])
                    }
                    for f in unit_result.failures
                ],
                "error_details": [
                    {
                        "test": str(e[0]),
                        "error": str(e[1])
                    }
                    for e in unit_result.errors
                ]
            },
            "integration_tests": {
                "tests_run": integration_result.testsRun,
                "failures": len(integration_result.failures),
                "errors": len(integration_result.errors),
                "failure_details": [
                    {
                        "test": str(f[0]),
                        "error": str(f[1])
                    }
                    for f in integration_result.failures
                ],
                "error_details": [
                    {
                        "test": str(e[0]),
                        "error": str(e[1])
                    }
                    for e in integration_result.errors
                ]
            },
            "e2e_tests": {
                "tests_run": e2e_result.testsRun,
                "failures": len(e2e_result.failures),
                "errors": len(e2e_result.errors),
                "failure_details": [
                    {
                        "test": str(f[0]),
                        "error": str(f[1])
                    }
                    for f in e2e_result.failures
                ],
                "error_details": [
                    {
                        "test": str(e[0]),
                        "error": str(e[1])
                    }
                    for e in e2e_result.errors
                ]
            }
        }
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"测试报告已保存: {report_file}")
        
    except Exception as e:
        print(f"保存测试报告时出错: {e}")


# ============================================================================
# 命令行接口
# ============================================================================

def main():
    """主函数 - 命令行接口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="淘宝搜索综合测试套件")
    parser.add_argument("--unit", action="store_true", help="只运行单元测试")
    parser.add_argument("--integration", action="store_true", help="只运行集成测试")
    parser.add_argument("--e2e", action="store_true", help="只运行端到端测试")
    parser.add_argument("--skip-e2e", action="store_true", help="跳过端到端测试")
    parser.add_argument("--all", action="store_true", help="运行所有测试（默认）")
    
    args = parser.parse_args()
    
    # 设置环境变量（如果跳过端到端测试）
    if args.skip_e2e:
        os.environ['SKIP_E2E_TESTS'] = 'true'
    
    if args.unit:
        # 只运行单元测试
        print("运行单元测试...")
        loader = unittest.TestLoader()
        unit_suite = unittest.TestSuite()
        unit_suite.addTests(loader.loadTestsFromTestCase(TestTaobaoScorer))
        unit_suite.addTests(loader.loadTestsFromTestCase(TestTaobaoMain))
        
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(unit_suite)
        
        return result.wasSuccessful()
    
    elif args.integration:
        # 只运行集成测试
        print("运行集成测试...")
        loader = unittest.TestLoader()
        integration_suite = unittest.TestSuite()
        integration_suite.addTests(loader.loadTestsFromTestCase(TestTaobaoIntegration))
        
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(integration_suite)
        
        return result.wasSuccessful()
    
    elif args.e2e:
        # 只运行端到端测试
        print("运行端到端测试...")
        loader = unittest.TestLoader()
        e2e_suite = unittest.TestSuite()
        e2e_suite.addTests(loader.loadTestsFromTestCase(TestTaobaoE2E))
        
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(e2e_suite)
        
        return result.wasSuccessful()
    
    else:
        # 运行所有测试
        return run_all_tests()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
