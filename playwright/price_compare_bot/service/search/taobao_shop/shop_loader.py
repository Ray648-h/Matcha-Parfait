# service/search/taobao_shop/shop_loader.py
# 职责：从 taobao_shop_urls.txt 加载店铺名 → URL 映射

import re
from pathlib import Path
from typing import Dict

# taobao_shop_urls.txt 位于 price_compare_bot/ 根目录
_DEFAULT_TXT = Path(__file__).resolve().parents[3] / "taobao_shop_urls.txt"


def load_shop_urls(filepath=None) -> Dict[str, str]:
    """
    读取 taobao_shop_urls.txt，返回 {店铺名: URL} 字典。

    文件格式（两行一组）：
        1. 三月兽官方旗舰店          ← 店铺名（可带序号前缀）
        https://shop123.taobao.com  ← 对应 URL

    注释行（以 # 开头）和空行会被跳过。
    """
    path = Path(filepath) if filepath else _DEFAULT_TXT

    if not path.exists():
        raise FileNotFoundError(f"找不到店铺 URL 文件: {path}")

    result: Dict[str, str] = {}
    current_name: str | None = None

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()

        if not line or line.startswith("#"):
            current_name = None
            continue

        if line.startswith("http"):
            if current_name:
                result[current_name] = line
                current_name = None
        else:
            # 去掉 "1. " 这样的序号前缀
            name = re.sub(r"^\d+\.\s*", "", line).strip()
            if name:
                current_name = name

    return result


def get_all_shop_names(filepath=None) -> list:
    """返回所有可选店铺名列表（供前端展示用）。"""
    return list(load_shop_urls(filepath).keys())
