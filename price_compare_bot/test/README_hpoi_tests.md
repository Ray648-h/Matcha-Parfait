# HPOI搜索功能测试

本目录包含HPOI（日本合伙人玩具价格信息）搜索功能的测试脚本和测试数据。

## 测试文件说明

### 1. `test_hpoi_simple.py` - 简单测试脚本
快速测试HPOI搜索功能，适合快速验证和演示。

**使用方法：**
```bash
# 快速测试（默认）
python test_hpoi_simple.py

# 使用自定义关键词测试
python test_hpoi_simple.py --keyword "初音未来粘土人"

# 显示帮助
python test_hpoi_simple.py --help
```

**功能：**
- 测试价格解析功能
- 测试关键词分解功能
- 测试搜索功能（演示模式）

### 2. `test_hpoi_search.py` - 完整测试套件
全面的HPOI搜索功能测试，包含所有测试用例。

**使用方法：**
```bash
# 运行所有测试（不包含网络测试）
python test_hpoi_search.py

# 运行所有测试（包含网络测试）
python test_hpoi_search.py --network

# 运行特定测试
python test_hpoi_search.py --test price      # 价格解析测试
python test_hpoi_search.py --test keyword    # 关键词分解测试
python test_hpoi_search.py --test scoring    # 评分逻辑测试
python test_hpoi_search.py --test currency   # 货币转换测试
python test_hpoi_search.py --test mock       # 模拟搜索测试
python test_hpoi_search.py --test network    # 网络搜索测试
python test_hpoi_search.py --test data       # 创建测试数据
python test_hpoi_search.py --test all        # 所有测试（默认）

# 显示帮助
python test_hpoi_search.py --help
```

**功能：**
- 价格解析功能测试
- 关键词分解功能测试
- 评分逻辑测试
- 货币转换功能测试
- 模拟搜索测试
- 实际网络搜索测试（可选）
- 测试数据创建

## 测试数据

测试数据保存在 `test_data/hpoi/` 目录下：

### 1. `test_products.json` - 测试商品数据
包含5个模拟的HPOI商品数据，用于测试搜索和评分功能。

**数据结构：**
```json
{
  "id": "hpoi_001",
  "title": "Good Smile Company 户山香澄 粘土人 手办",
  "price_jpy": 12800.0,
  "price_cny": 655.36,
  "release_date": "2024年12月",
  "category": "粘土人",
  "brand": "GSC",
  "character": "户山香澄",
  "series": "BanG Dream!",
  "source": "HPOI",
  "search_keywords": ["户山香澄", "粘土人", "手办", "GSC", "Good Smile Company"]
}
```

### 2. `test_search_cases.json` - 搜索测试用例
包含5个搜索测试用例，用于验证搜索功能。

**数据结构：**
```json
{
  "keyword": "户山香澄粘土人",
  "expected_matches": ["hpoi_001"],
  "description": "精确匹配特定角色和产品类型"
}
```

### 3. `config_test.json` - 配置测试数据
包含HPOI配置信息的测试数据。

## HPOI搜索功能概述

### 主要组件
1. **数据获取模块** (`hpoi/fetcher.py`)
   - 使用Playwright和requests获取HPOI商品数据
   - 支持网络请求失败时的备选方案

2. **评分模块** (`hpoi/scorer.py`)
   - 基于关键词匹配进行商品评分
   - 计分规则：
     - 基础分：10分
     - 搜索词匹配：每个搜索词+20分
     - 有效价格：+5分
     - 有发售日期：+10分
     - 无匹配搜索词：-50分

3. **工具模块** (`hpoi/utils.py`)
   - 价格解析：支持多种货币格式
   - 关键词分解：识别产品类型词
   - 货币转换：日元转人民币

4. **配置模块** (`hpoi/config.py`)
   - HPOI网址配置
   - 产品类型关键词列表
   - 页面元素选择器

### 主要API函数
- `search_hpoi(keyword, max_items=20, debug=False)` - 搜索单个最佳商品
- `search_hpoi_top_n(keyword, n=6, debug=False)` - 搜索前N个商品
- `test_hpoi_search(keyword)` - 测试单个商品搜索
- `test_hpoi_search_top_6(keyword)` - 测试前6个商品搜索

## 依赖安装

运行测试前需要安装以下依赖：

```bash
pip install requests beautifulsoup4
```

如果使用Playwright进行网络测试，还需要安装Playwright：

```bash
pip install playwright
playwright install chromium
```

## 测试结果验证

### 成功标准
1. 价格解析功能正确解析各种货币格式
2. 关键词分解功能正确识别产品类型词
3. 评分逻辑根据关键词匹配正确计算分数
4. 货币转换功能正确转换日元到人民币
5. 搜索功能能够获取并评分商品

### 已知问题
1. Playwright同步API在异步环境中可能有问题（使用requests备选方案）
2. 网络测试需要稳定的网络连接
3. HPOI网站结构可能变化，需要更新选择器

## 扩展测试

要添加新的测试用例，可以：

1. 在 `test_products.json` 中添加新的测试商品
2. 在 `test_search_cases.json` 中添加新的搜索测试用例
3. 在测试脚本中添加新的测试函数

## 故障排除

### 常见问题
1. **ModuleNotFoundError: No module named 'requests'**
   ```bash
   pip install requests beautifulsoup4
   ```

2. **网络连接失败**
   - 检查网络连接
   - 使用 `--network` 参数禁用网络测试
   - 使用模拟数据测试

3. **Playwright错误**
   ```bash
   pip install playwright
   playwright install chromium
   ```

4. **HPOI网站不可访问**
   - 使用requests备选方案
   - 检查防火墙设置
   - 尝试使用代理