def parse_xianyu_raw_items(raw_items, debug=False):
    """
    处理从_fetch_raw_data返回的商品字典列表。
    输入: 已提取的商品字典 [{'title': '', 'price': '', 'has_post_icon': bool}, ...]
    输出: 格式化的商品数据 [{'title': '', 'price': float, 'shipping': '包邮/不包邮'}, ...]
    ⚠️ 数据已在浏览器打开时完全提取，避免事件循环关闭问题
    """
    parsed = []

    for idx, raw in enumerate(raw_items):
        try:
            title = raw.get('title', '').strip()
            price_str = raw.get('price', '').strip()
            has_post_icon = raw.get('has_post_icon', False)
            
            if not title:
                if debug:
                    print(f"[解析] 商品{idx+1}: 缺少标题，跳过")
                continue

            # 转换价格为float
            price = _parse_price(price_str)
            
            if debug:
                print(f"[解析] 商品{idx+1}: 标题='{title[:30]}...', 价格={price}")

            # 判断包邮状态（双重判断：图标 + 关键词）
            has_baoyou_keyword = any(k in title for k in ["包邮", "全国包邮", "顺丰包邮"])
            shipping = '包邮' if (has_post_icon or has_baoyou_keyword) else '不包邮'

            parsed.append({
                'title': title,
                'price': price,
                'shipping': shipping
            })

        except Exception as e:
            if debug:
                print(f"[解析] 商品{idx+1}: 异常 - {e}")
            continue

    if debug:
        print(f"[parse_xianyu_raw_items] 共解析 {len(parsed)}/{len(raw_items)} 个商品")
    
    return parsed


# ======================
# 工具函数
# ======================

def _parse_price(text):
    try:
        p = ''.join(ch for ch in str(text) if ch.isdigit() or ch == '.')
        return float(p) if p else 0.0
    except:
        return 0.0