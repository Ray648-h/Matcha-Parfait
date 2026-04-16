#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
淘宝模块完整测试套件
包含单元测试、集成测试和端到端测试
"""

import sys
import os
import json
import tempfile
import unittest
from unittest.mock import Mock, patch, MagicMock
from dataclasses import dataclass
from typing import Dict, List, Optional

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestTaobaoScorer(unittest.TestCase):
    """测试淘宝评分模块"""
    
    def setUp(self):
        """测试前准备"""
        # 动态导入taobao_scorer模块
        scorer_path = os.path.join(
            os.path.dirname(__file__), 
            "..", "service", "search", "taobao_shop", "taobao_scorer.py"
        )
        
        import importlib.util
        spec = importlib.util.spec_from_file_location("taobao_scorer", scorer_path)
        self.taobao_scorer = importlib.util.module_from_spec(spec)
        
        # 添加必要的sys.path
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(scorer_path))))
        
        spec.loader.exec_module(self.taobao_scorer)
    
    def test_calculate_taobao_score_basic(self):
        """测试基本评分功能"""
        item = {
            'title': '初音未来 粘土人 3.0 全新正版',
            'shop': 'gsc官方旗舰店',
            'price_text': '¥299.00',
            'link': 'https://example.com',
            'image': 'https://example.com/image.jpg',
            'target_shop': 'gsc',
            'free_shipping': True
        }
        
        score, special = self.taobao_scorer.calculate_taobao_score(item, '初音未来粘土人3.0', debug=False)
        
        # 验证评分在合理范围内
        self.assertIsInstance(score, int)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)
        
        # 验证特殊关键词列表
        self.assertIsInstance(special, list)
    
    def test_calculate_taobao_score_target_shop(self):
        """测试目标店铺加分"""
        item_gsc = {
            'title': '测试商品',
            'shop': 'gsc官方旗舰店',
            'price_text': '¥100.00',
            'link': 'https://example.com',
            'image': 'https://example.com/image.jpg',
            'target_shop': 'gsc',
            'free_shipping': True
        }
        
        item_non_target = {
            'title': '测试商品',
            'shop': '其他店铺',
            'price_text': '¥100.00',
            'link': 'https://example.com',
            'image': 'https://example.com/image.jpg',
            'target_shop': None,
            'free_shipping': True
        }
        
        score_gsc, _ = self.taobao_scorer.calculate_taobao_score(item_gsc, '测试', debug=False)
        score_non_target, _ = self.taobao_scorer.calculate_taobao_score(item_non_target, '测试', debug=False)
        
        # 目标店铺应该得分更高
        self.assertGreater(score_gsc, score_non_target)
    
    def test_score_taobao_items(self):
        """测试批量评分"""
        items = [
            {
                'title': '初音未来 粘土人 3.0',
                'shop': 'gsc官方旗舰店',
                'price_text': '¥299.00',
                'link': 'https://example.com',
                'image': 'https://example.com/image.jpg',
                'target_shop': 'gsc',
                'free_shipping': True
            },
            {
                'title': '其他商品',
                'shop': '其他店铺',
                'price_text': '¥150.00',
                'link': 'https://example.com',
                'image': 'https://example.com/image.jpg',
                'target_shop': None,
                'free_shipping': False
            }
        ]
        
        scored_items = self.taobao_scorer.score_taobao_items(items, '初音未来粘土人3.0', debug=False)
        
        # 验证返回结果
        self.assertEqual(len(scored_items), len(items))
        
        # 验证每个商品都有score字段
        for item in scored_items:
            self.assertIn('score', item)
            self.assertIsInstance(item['score'], int)
        
        # 验证排序（得分高的在前）
        scores = [item['score'] for item in scored_items]
        self.assertEqual(scores, sorted(scores, reverse=True))
    
    def test_get_top_ranked_items_by_price(self):
        """测试获取前N名按价格排序"""
        items = [
            {
                'title': '商品A',
                'shop': '店铺A',
                'price_text': '¥100.00',
                'link': 'https://example.com',
                'image': 'https://example.com/image.jpg',
                'score': 80,
                'target_shop': 'gsc',
                'free_shipping': True
            },
            {
                'title': '商品B',
                'shop': '店铺B',
                'price_text': '¥200.00',
                'link': 'https://example.com',
                'image': 'https://example.com/image.jpg',
                'score': 80,
                'target_shop': None,
                'free_shipping': False
            },
            {
                'title': '商品C',
                'shop': '店铺C',
                'price_text': '¥150.00',
                'link': 'https://example.com',
                'image': 'https://example.com/image.jpg',
                'score': 60,
                'target_shop': None,
                'free_shipping': True
            }
        ]
        
        top_items = self.taobao_scorer.get_top_ranked_items_by_price(items, top_n=2)
        
        # 验证返回数量
        self.assertLessEqual(len(top_items), 2)
        
        # 验证价格排序（价格低的在前）
        if len(top_items) >= 2:
            price1 = float(top_items[0]['price_text'].replace('¥', '').replace(',', ''))
            price2 = float(top_items[1]['price_text'].replace('¥', '').replace(',', ''))
            self.assertLessEqual(price1, price2)
    
    def test_process_taobao_items_with_scoring(self):
        """测试完整评分流程"""
        items = [
            {
                'title': '初音未来 粘土人 3.0',
                'shop': 'gsc官方旗舰店',
                'price_text': '¥299.00',
                'link': 'https://example.com',
                'image': 'https://example.com/image.jpg',
                'target_shop': 'gsc',
                'free_shipping': True
            },
            {
                'title': '其他商品',
                'shop': '其他店铺',
                'price_text': '¥150.00',
                'link': 'https://example.com',
                'image': 'https://example.com/image.jpg',
                'target_shop': None,
                'free_shipping': False
            }
        ]
        
        scored_items, top_items = self.taobao_scorer.process_taobao_items_with_scoring(
            items, '初音未来粘土人3.0', debug=False
        )
        
        # 验证返回结果
        self.assertIsInstance(scored_items, list)
        self.assertIsInstance(top_items, list)
        
        # 验证评分后的商品都有score字段
        for item in scored_items:
            self.assertIn('score', item)
        
        # 验证top_items是scored_items的子集
        self.assertLessEqual(len(top_items), len(scored_items))


class TestTaobaoDataClasses(unittest.TestCase):
    """测试淘宝数据类"""
    
    def test_product_dataclass(self):
        """测试Product数据类"""
        from price_compare_bot.service.search.taobao_shop.taobao_main import Product
        
        # 创建Product实例
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
        self.assertEqual(product.target_shop, "gsc")
        self.assertEqual(product.index, 1)
        
        # 测试to_dict方法
        product_dict = product.to_dict()
        self.assertIsInstance(product_dict, dict)
        self.assertEqual(product_dict['title'], "测试商品")
        self.assertEqual(product_dict['score'], 85)
    
    def test_searchresult_dataclass(self):
        """测试SearchResult数据类"""
        from price_compare_bot.service.search.taobao_shop.taobao_main import Product, SearchResult
        
        # 创建Product实例
        product = Product(
            title="测试商品",
            shop="测试店铺",
            price_text="¥100.00",
            link="https://example.com",
            image="https://example.com/image.jpg"
        )
        
        # 创建SearchResult实例
        result = SearchResult(
            keyword="测试关键词",
            products=[product],
            total_count=10,
            filtered_count=1,
            search_time=1.5,
            success=True,
            error_message=""
        )
        
        # 验证属性
        self.assertEqual(result.keyword, "测试关键词")
        self.assertEqual(len(result.products), 1)
        self.assertEqual(result.total_count, 10)
        self.assertEqual(result.filtered_count, 1)
        self.assertEqual(result.search_time, 1.5)
        self.assertTrue(result.success)
        
        # 测试to_dict方法
        result_dict = result.to_dict()
        self.assertIsInstance(result_dict, dict)
        self.assertEqual(result_dict['keyword'], "测试关键词")
        self.assertEqual(len(result_dict['products']), 1)
        
        # 测试to_json方法
        result_json = result.to_json()
        self.assertIsInstance(result_json, str)
        self.assertIn("测试关键词", result_json)


class TestTaobaoSearchIntegration(unittest.TestCase):
    """测试淘宝搜索集成"""
    
    @patch('price_compare_bot.service.search.taobao_shop.taobao_main.TaobaoSearch._load_target_shops')
    def test_taobao_search_initialization(self, mock_load_shops):
        """测试TaobaoSearch初始化"""
        from price_compare_bot.service.search.taobao_shop.taobao_main import TaobaoSearch
        
        # 模拟加载店铺
        mock_load_shops.return_value = {
            'gsc': 'https://gsc.tmall.com',
            'hpoi': 'https://hpoi.tmall.com'
        }
        
        # 创建搜索器
        searcher = TaobaoSearch()
        
        # 验证初始化
        self.assertIsInstance(searcher, TaobaoSearch)
        self.assertIsInstance(searcher.target_shops, dict)
        
        # 验证方法调用
        mock_load_shops.assert_called_once()
    
    @patch('price_compare_bot.service.search.taobao_shop.taobao_main.TaobaoSearch._load_target_shops')
    def test_get_target_shops(self, mock_load_shops):
        """测试获取目标店铺"""
        from price_compare_bot.service.search.taobao_shop.taobao_main import TaobaoSearch
        
        # 模拟店铺数据
        mock_shops = {
            'gsc': 'https://gsc.tmall.com',
            'hpoi': 'https://hpoi.tmall.com',
            'amiami': 'https://amiami.tmall.com'
        }
        mock_load_shops.return_value = mock_shops
        
        # 创建搜索器
        searcher = TaobaoSearch()
        
        # 获取目标店铺
        target_shops = searcher.get_target_shops()
        
        # 验证返回结果
        self.assertIsInstance(target_shops, dict)
        self.assertEqual(len(target_shops), len(mock_shops))
        self.assertEqual(target_shops, mock_shops)


class TestTaobaoWorkflow(unittest.TestCase):
    """测试淘宝工作流程"""
    
    def test_workflow_file_exists(self):
        """测试工作流程文件存在"""
        workflow_file = os.path.join(
            os.path.dirname(__file__), "..", "taobao_workflow.py"
        )
        
        self.assertTrue(os.path.exists(workflow_file), f"工作流程文件不存在: {workflow_file}")
    
    def test_workflow_functions_exist(self):
        """测试工作流程函数存在"""
        workflow_file = os.path.join(
            os.path.dirname(__file__), "..", "taobao_workflow.py"
        )
        
        with open(workflow_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查关键函数
        required_functions = [
            "run_taobao_search_workflow",
            "batch_search",
            "save_results_to_file",
            "main"
        ]
        
        for func in required_functions:
            self.assertIn(func, content, f"函数 '{func}' 在工作流程文件中未找到")
    
    def test_workflow_command_line_args(self):
        """测试工作流程命令行参数"""
        workflow_file = os.path.join(
            os.path.dirname(__file__), "..", "taobao_workflow.py"
        )
        
        with open(workflow_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查argparse
        self.assertIn("argparse", content, "命令行参数解析未找到")
        self.assertIn("ArgumentParser", content, "ArgumentParser未找到")


class TestTaobaoTestData(unittest.TestCase):
    """测试淘宝测试数据"""
    
    def test_test_data_directory_exists(self):
        """测试测试数据目录存在"""
        test_data_dir = os.path.join(
            os.path.dirname(__file__), "test_data", "taobao"
        )
        
        self.assertTrue(os.path.exists(test_data_dir), f"测试数据目录不存在: {test_data_dir}")
    
    def test_sample_test_data(self):
        """测试示例测试数据"""
        test_data_dir = os.path.join(
            os.path.dirname(__file__), "test_data", "taobao"
        )
        
        # 创建示例测试数据文件
        sample_data = {
            "test_cases": [
                {
                    "keyword": "初音未来粘土人3.0",
                    "expected_min_score": 20,
                    "description": "测试初音未来相关商品评分"
                },
                {
                    "keyword": "Saber Alter 手办",
                    "expected_min_score": 15,
                    "description": "测试Saber相关商品评分"
                }
            ],
            "sample_items": [
                {
                    "title": "初音未来 粘土人 3.0 全新正版 包邮",
                    "shop": "gsc官方旗舰店",
                    "price_text": "¥299.00",
                    "link": "https://item.taobao.com/item.htm?id=1234567890",
                    "image": "https://example.com/image.jpg",
                    "target_shop": "gsc",
                    "free_shipping": True
                },
                {
                    "title": "Saber Alter 手办 1/7 比例",
                    "shop": "hpoi官方旗舰店",
                    "price_text": "¥899.00",
                    "link": "https://item.taobao.com/item.htm?id=2345678901",
                    "image": "https://example.com/image2.jpg",
                    "target_shop": "hpoi",
                    "free_shipping": True
                }
            ]
        }
        
        # 保存测试数据
        sample_file = os.path.join(test_data_dir, "sample_test_data.json")
        os.makedirs(test_data_dir, exist_ok=True)
        
        with open(sample_file, 'w', encoding='utf-8') as f:
            json.dump(sample_data, f, ensure_ascii=False, indent=2)
        
        # 验证文件创建
        self.assertTrue(os.path.exists(sample_file), f"示例测试数据文件未创建: {sample_file}")
        
        # 验证文件内容
        with open(sample_file, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        
        self.assertEqual(len(loaded_data["test_cases"]), 2)
        self.assertEqual(len(loaded_data["sample_items"]), 2)
        self.assertEqual(loaded_data["test_cases"][0]["keyword"], "初音未来粘土人3.0")


def create_test_results_summary():
    """创建测试结果摘要"""
    summary = {
        "test_suite": "淘宝模块完整测试套件",
        "timestamp": "2026-04-16T01:40:00",
        "tests": [
            {
                "name": "TestTaobaoScorer",
                "description": "测试淘宝评分模块",
                "test_cases": 5
            },
            {
                "name": "TestTaobaoDataClasses",
                "description": "测试淘宝数据类",
                "test_cases": 2
            },
            {
                "name": "TestTaobaoSearchIntegration",
                "description": "测试淘宝搜索集成",
                "test_cases": 2
            },
            {
                "name": "TestTaobaoWorkflow",
                "description": "测试淘宝工作流程",
                "test_cases": 3
            },
            {
                "name": "TestTaobao