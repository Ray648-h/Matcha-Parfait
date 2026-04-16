#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运行淘宝测试的简单脚本
"""

import sys
import os
import subprocess

def run_tests():
    """运行淘宝测试"""
    print("=" * 80)
    print("运行淘宝搜索功能测试")
    print("=" * 80)
    
    # 确保在正确的目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    # 1. 运行单元测试
    print("\n1. 运行单元测试...")
    print("-" * 40)
    
    unit_result = subprocess.run(
        [sys.executable, "-m", "pytest", 
         os.path.join(script_dir, "test_taobao_comprehensive.py::TestTaobaoScorer"),
         "-v", "--tb=short"],
        cwd=project_root,
        capture_output=True,
        text=True,
        encoding='utf-8'
    )
    
    print(unit_result.stdout)
    if unit_result.stderr:
        print("STDERR:", unit_result.stderr)
    
    # 2. 运行主模块测试
    print("\n2. 运行主模块测试...")
    print("-" * 40)
    
    main_result = subprocess.run(
        [sys.executable, "-m", "pytest",
         os.path.join(script_dir, "test_taobao_comprehensive.py::TestTaobaoMain"),
         "-v", "--tb=short"],
        cwd=project_root,
        capture_output=True,
        text=True,
        encoding='utf-8'
    )
    
    print(main_result.stdout)
    if main_result.stderr:
        print("STDERR:", main_result.stderr)
    
    # 3. 运行集成测试（跳过需要网络的部分）
    print("\n3. 运行集成测试...")
    print("-" * 40)
    
    integration_result = subprocess.run(
        [sys.executable, "-m", "pytest",
         os.path.join(script_dir, "test_taobao_comprehensive.py::TestTaobaoIntegration"),
         "-v", "--tb=short"],
        cwd=project_root,
        capture_output=True,
        text=True,
        encoding='utf-8'
    )
    
    print(integration_result.stdout)
    if integration_result.stderr:
        print("STDERR:", integration_result.stderr)
    
    # 4. 运行综合测试套件
    print("\n4. 运行综合测试套件...")
    print("-" * 40)
    
    # 设置环境变量跳过端到端测试
    env = os.environ.copy()
    env['SKIP_E2E_TESTS'] = 'true'
    
    comprehensive_result = subprocess.run(
        [sys.executable, os.path.join(script_dir, "test_taobao_comprehensive.py"),
         "--skip-e2e"],
        cwd=project_root,
        env=env,
        capture_output=True,
        text=True,
        encoding='utf-8'
    )
    
    print(comprehensive_result.stdout)
    if comprehensive_result.stderr:
        print("STDERR:", comprehensive_result.stderr)
    
    # 5. 检查测试数据目录
    print("\n5. 检查测试数据...")
    print("-" * 40)
    
    test_data_dir = os.path.join(script_dir, "test_data", "taobao")
    if os.path.exists(test_data_dir):
        print(f"测试数据目录: {test_data_dir}")
        
        # 列出文件
        for root, dirs, files in os.walk(test_data_dir):
            level = root.replace(test_data_dir, '').count(os.sep)
            indent = ' ' * 2 * level
            print(f"{indent}{os.path.basename(root)}/")
            subindent = ' ' * 2 * (level + 1)
            for file in files:
                if file.endswith('.json') or file.endswith('.txt'):
                    print(f"{subindent}{file}")
    else:
        print(f"测试数据目录不存在: {test_data_dir}")
    
    # 汇总结果
    print("\n" + "=" * 80)
    print("测试结果汇总")
    print("=" * 80)
    
    results = [
        ("单元测试", unit_result.returncode == 0),
        ("主模块测试", main_result.returncode == 0),
        ("集成测试", integration_result.returncode == 0),
        ("综合测试", comprehensive_result.returncode == 0)
    ]
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{test_name:20} {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 80)
    if all_passed:
        print("✅ 所有测试通过！淘宝搜索功能正常。")
        print("\n测试数据已保存到:")
        print(f"  {test_data_dir}")
        print("\n可以查看以下文件:")
        print("  - test_data/taobao/*.json - JSON格式的测试结果")
        print("  - test_data/taobao/test_reports/*.json - 测试报告")
    else:
        print("❌ 有测试失败，请检查上面的输出。")
    
    return all_passed


def test_simple_search():
    """简单的功能测试"""
    print("\n" + "=" * 80)
    print("简单功能测试")
    print("=" * 80)
    
    try:
        # 导入模块
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        from service.search.taobao_shop.taobao_scorer import (
            calculate_taobao_score, score_taobao_items
        )
        
        # 测试数据
        test_items = [
            {
                'title': '初音未来 粘土人 3.0',
                'shop': '测试店铺',
                'price_text': '¥299.00',
                'link': 'https://example.com',
                'image': 'https://example.com/image.jpg',
                'target_shop': 'gsc'
            },
            {
                'title': '其他商品',
                'shop': '其他店铺',
                'price_text': '¥150.00',
                'link': 'https://example.com/other',
                'image': 'https://example.com/other.jpg',
                'target_shop': None
            }
        ]
        
        keyword = "初音未来粘土人3.0"
        
        # 测试评分
        print(f"测试关键词: {keyword}")
        print(f"测试商品数: {len(test_items)}")
        
        # 单个商品评分
        score1, special1 = calculate_taobao_score(test_items[0], keyword, debug=True)
        print(f"\n商品1评分: {score1}分")
        print(f"特殊关键词: {special1}")
        
        score2, special2 = calculate_taobao_score(test_items[1], keyword, debug=True)
        print(f"\n商品2评分: {score2}分")
        print(f"特殊关键词: {special2}")
        
        # 批量评分
        scored_items = score_taobao_items(test_items, keyword, debug=True)
        print(f"\n批量评分结果:")
        for i, item in enumerate(scored_items, 1):
            print(f"{i}. {item['title'][:30]}... - {item['score']}分")
        
        return True
        
    except Exception as e:
        print(f"功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("淘宝搜索功能测试套件")
    print("=" * 80)
    
    # 运行测试
    tests_passed = run_tests()
    
    # 运行简单功能测试
    print("\n" + "=" * 80)
    print("运行简单功能测试...")
    print("=" * 80)
    
    func_test_passed = test_simple_search()
    
    # 最终结果
    print("\n" + "=" * 80)
    print("最终结果")
    print("=" * 80)
    
    if tests_passed and func_test_passed:
        print("✅ 所有测试和功能验证通过！")
        print("\n淘宝搜索功能完整，可以正常使用。")
        print("\n使用建议:")
        print("1. 运行端到端测试: python test_taobao_comprehensive.py --e2e")
        print("2. 查看测试报告: 查看 test_data/taobao/test_reports/ 目录")
        print("3. 使用淘宝工作流程: python taobao_workflow.py '关键词'")
        return 0
    else:
        print("❌ 测试或功能验证失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())