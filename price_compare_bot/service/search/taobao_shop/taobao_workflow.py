# -*- coding: utf-8 -*-
"""
淘宝搜索综合运行流程脚本
整合所有环节，提供完整的搜索流程
"""

import sys
import os
import time
import argparse
from typing import List, Dict

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from service.search.taobao_shop.taobao_main import TaobaoSearch, print_search_result


def run_taobao_search_workflow(keyword: str, search_type: str = "comprehensive", debug: bool = False):
    """
    运行淘宝搜索工作流程
    
    参数:
        keyword: 搜索关键词
        search_type: 搜索类型 (direct, shop, comprehensive)
        debug: 是否显示调试信息
    """
    print("=" * 80)
    print("淘宝搜索综合工作流程")
    print("=" * 80)
    
    # 1. 初始化搜索器
    print("1. 初始化淘宝搜索器...")
    searcher = TaobaoSearch()
    
    # 显示目标店铺信息
    target_shops = searcher.get_target_shops()
    print(f"   加载了 {len(target_shops)} 个目标店铺")
    if debug and target_shops:
        print("   目标店铺列表:")
        for i, (shop, url) in enumerate(list(target_shops.items())[:3], 1):
            print(f"     {i}. {shop}")
        if len(target_shops) > 3:
            print(f"     ... 还有 {len(target_shops) - 3} 个店铺")
    
    print(f"\n2. 开始搜索: {keyword}")
    print(f"   搜索类型: {search_type}")
    print("-" * 80)
    
    # 2. 执行搜索
    start_time = time.time()
    
    try:
        if search_type == "direct":
            result = searcher.search_direct(keyword, debug=debug)
        elif search_type == "shop":
            result = searcher.search_in_shops(keyword, debug=debug)
        else:  # comprehensive
            result = searcher.search_comprehensive(keyword, debug=debug)
        
        search_time = time.time() - start_time
        
        # 3. 显示结果
        print("\n3. 搜索结果:")
        print_search_result(result)
        
        # 4. 保存结果到文件
        if result.success and result.products:
            save_results_to_file(result, keyword, search_type)
        
        return result
        
    except Exception as e:
        search_time = time.time() - start_time
        print(f"\n搜索过程中出错: {e}")
        print(f"搜索耗时: {search_time:.2f}秒")
        return None


def save_results_to_file(result, keyword: str, search_type: str):
    """保存搜索结果到文件"""
    try:
        # 创建结果目录
        results_dir = "search_results"
        os.makedirs(results_dir, exist_ok=True)
        
        # 生成文件名
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        safe_keyword = "".join(c for c in keyword if c.isalnum() or c in " _-")
        filename = f"{results_dir}/taobao_{safe_keyword}_{search_type}_{timestamp}.json"
        
        # 保存为JSON
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(result.to_json(indent=2))
        
        print(f"\n4. 结果已保存到: {filename}")
        
        # 同时保存简化的文本版本
        txt_filename = f"{results_dir}/taobao_{safe_keyword}_{search_type}_{timestamp}.txt"
        with open(txt_filename, 'w', encoding='utf-8') as f:
            f.write(f"淘宝搜索结果 - {keyword}\n")
            f.write(f"搜索类型: {search_type}\n")
            f.write(f"搜索时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"搜索耗时: {result.search_time:.2f}秒\n")
            f.write(f"找到商品总数: {result.total_count}\n")
            f.write(f"筛选后商品数量: {result.filtered_count}\n")
            f.write("=" * 60 + "\n\n")
            
            for i, product in enumerate(result.products[:20], 1):
                f.write(f"{i}. [{product.score}分] {product.title}\n")
                f.write(f"   店铺: {product.shop}")
                if product.target_shop:
                    f.write(f" (匹配: {product.target_shop})")
                f.write("\n")
                f.write(f"   价格: {product.price_text}\n")
                if product.link:
                    f.write(f"   链接: {product.link}\n")
                f.write("\n")
        
        print(f"   文本版本已保存到: {txt_filename}")
        
    except Exception as e:
        print(f"保存结果时出错: {e}")


def batch_search(keywords: List[str], search_type: str = "comprehensive", debug: bool = False):
    """批量搜索多个关键词"""
    print("=" * 80)
    print("淘宝批量搜索")
    print("=" * 80)
    
    all_results = []
    
    for i, keyword in enumerate(keywords, 1):
        print(f"\n[{i}/{len(keywords)}] 搜索关键词: {keyword}")
        print("-" * 40)
        
        result = run_taobao_search_workflow(keyword, search_type, debug)
        if result:
            all_results.append(result)
        
        # 避免频繁搜索，添加延迟
        if i < len(keywords):
            print(f"\n等待3秒后继续下一个搜索...")
            time.sleep(3)
    
    # 汇总结果
    if all_results:
        print("\n" + "=" * 80)
        print("批量搜索完成!")
        print("=" * 80)
        
        total_products = sum(len(r.products) for r in all_results)
        total_time = sum(r.search_time for r in all_results)
        
        print(f"共搜索 {len(all_results)} 个关键词")
        print(f"总共找到 {total_products} 个商品")
        print(f"总搜索耗时: {total_time:.2f}秒")
        
        # 保存汇总结果
        save_batch_results(all_results)
    
    return all_results


def save_batch_results(results: List):
    """保存批量搜索结果"""
    try:
        results_dir = "search_results"
        os.makedirs(results_dir, exist_ok=True)
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"{results_dir}/taobao_batch_{timestamp}.json"
        
        # 保存所有结果
        all_data = {
            "search_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_keywords": len(results),
            "total_products": sum(len(r.products) for r in results),
            "total_search_time": sum(r.search_time for r in results),
            "results": [r.to_dict() for r in results]
        }
        
        import json
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n批量搜索结果已保存到: {filename}")
        
    except Exception as e:
        print(f"保存批量结果时出错: {e}")


def main():
    """主函数 - 命令行接口"""
    parser = argparse.ArgumentParser(description="淘宝搜索综合工作流程")
    parser.add_argument("keyword", nargs="?", help="搜索关键词")
    parser.add_argument("--type", choices=["direct", "shop", "comprehensive"], 
                       default="comprehensive", help="搜索类型 (默认: comprehensive)")
    parser.add_argument("--debug", action="store_true", help="显示调试信息")
    parser.add_argument("--batch", help="批量搜索文件路径（每行一个关键词）")
    parser.add_argument("--keywords", nargs="+", help="多个搜索关键词")
    
    args = parser.parse_args()
    
    if args.batch:
        # 从文件读取批量关键词
        try:
            with open(args.batch, 'r', encoding='utf-8') as f:
                keywords = [line.strip() for line in f if line.strip()]
            
            if not keywords:
                print("错误: 批量文件为空")
                return
            
            print(f"从文件读取 {len(keywords)} 个关键词")
            batch_search(keywords, args.type, args.debug)
            
        except Exception as e:
            print(f"读取批量文件时出错: {e}")
    
    elif args.keywords:
        # 命令行指定的多个关键词
        batch_search(args.keywords, args.type, args.debug)
    
    elif args.keyword:
        # 单个关键词搜索
        run_taobao_search_workflow(args.keyword, args.type, args.debug)
    
    else:
        # 交互式模式
        print("淘宝搜索综合工作流程 - 交互模式")
        print("-" * 40)
        
        keyword = input("请输入搜索关键词: ").strip()
        if not keyword:
            print("错误: 关键词不能为空")
            return
        
        print("\n搜索类型选项:")
        print("  1. 直接搜索 (direct)")
        print("  2. 店铺内搜索 (shop)")
        print("  3. 综合搜索 (comprehensive)")
        
        type_choice = input("请选择搜索类型 (1-3, 默认3): ").strip()
        if type_choice == "1":
            search_type = "direct"
        elif type_choice == "2":
            search_type = "shop"
        else:
            search_type = "comprehensive"
        
        debug_choice = input("是否显示调试信息? (y/N): ").strip().lower()
        debug = debug_choice == "y"
        
        print("\n" + "=" * 40)
        run_taobao_search_workflow(keyword, search_type, debug)


if __name__ == "__main__":
    main()