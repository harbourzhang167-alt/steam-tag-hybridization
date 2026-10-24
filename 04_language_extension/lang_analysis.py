# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
# --- workspace-root anchor (added during reorganisation) -------------------
from pathlib import Path as _Path
import os as _os
_ROOT = _Path(__file__).resolve().parent
while not (_ROOT / "01_data").exists() and _ROOT.parent != _ROOT:
    _ROOT = _ROOT.parent
_os.chdir(_ROOT)
# --------------------------------------------------------------------------
import sys
if sys.version_info >= (3, 7):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import pandas as pd
import numpy as np
from collections import Counter

# 1. 载入 pipeline 导出的游戏级数据（已含筛选/聚类/杂交度/商业表现）
exp = pd.read_csv("01_data/processed/games_clustered_meta_export.csv")

# 2. 从原始数据中取语言列，按 appid 合并回来
raw = pd.read_csv(
    "01_data/raw/steam_games_march2025_updated.csv",
    usecols=["appid", "supported_languages", "supported_languages_counts"],
)
df = exp.merge(raw, on="appid", how="left")

print("=" * 60)
print("样本概况")
print("=" * 60)
print(f"pipeline 游戏数: {len(df)}")
print(f"有语言信息: {df['supported_languages'].notna().sum()}")
print(f"缺语言信息: {df['supported_languages'].isna().sum()}")

# 3. 语言频次统计
c = Counter()
for x in df["supported_languages"].dropna():
    for lang in str(x).split(","):
        lang = lang.strip()
        if lang:
            c[lang] += 1

print("\n语言支持频次（前 50）:")
for lang, n in c.most_common(50):
    print(f"{n:7d}  {lang}")