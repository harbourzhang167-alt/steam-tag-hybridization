# -*- coding: utf-8 -*-
"""
语言支持 vs 商业表现 —— 基于原始数据 steam_games_march2025_updated（含大厂游戏）。
沿用管线的时间/评论门槛筛选，但不去除大 owner 游戏、不控制杂交度。

因变量: Log_Reviews = log1p(positive+negative)
自变量: 语言分组 A/B/C/D
控制: price, 年份FE；进阶: +开发者/发行商 + 题材(genres)
"""
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

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

pd.set_option("display.unicode.east_asian_width", True)

# =====================================================================
# 1. 载入原始数据 + 管线筛选流程（时间 + 评论门槛）
# =====================================================================
USECOLS = ["appid", "name", "release_date", "price", "genres", "categories",
           "developers", "publishers", "positive", "negative", "supported_languages"]
raw = pd.read_csv("01_data/raw/steam_games_march2025_updated.csv", usecols=USECOLS)
print(f"原始行数: {len(raw)}")

df = raw.copy()
df = df.dropna(subset=["genres", "categories", "supported_languages"])
df["release_date"] = pd.to_datetime(df["release_date"], errors="coerce")
df["Release_Year"] = df["release_date"].dt.year
df["Total_Reviews"] = df["positive"] + df["negative"]

# 管线门槛：年份区间 + 评论数门槛
df = df[(df["Release_Year"] >= 2015) & (df["Release_Year"] <= 2025)]
df = df[df["Total_Reviews"] >= 0]
df = df[df["Total_Reviews"] > 0].copy()
df["Log_Reviews"] = np.log1p(df["Total_Reviews"])

print(f"筛选后行数 (2015-2025, 评论>=0): {len(df)}")

# =====================================================================
# 2. 语言分组
# =====================================================================
ZH = {"Simplified Chinese", "Traditional Chinese"}
BIG = {"German", "French", "Spanish - Spain", "Japanese", "Russian",
       "Italian", "Korean", "Portuguese - Brazil", "Polish", "Turkish",
       "Spanish - Latin America"}

def to_set(x):
    return {t.strip() for t in str(x).split(",") if t.strip()}

df["lang_set"] = df["supported_languages"].apply(to_set)
df["n_langs"] = df["lang_set"].apply(len)
df["has_zh"] = df["lang_set"].apply(lambda s: bool(s & ZH))
df["only_en"] = df["lang_set"].apply(lambda s: s == {"English"})
df["has_big"] = df["lang_set"].apply(lambda s: bool((s - {"English"}) & BIG))
df["has_other_nonEN"] = df["lang_set"].apply(lambda s: bool(s - {"English"}))

def classify(r):
    if r["has_zh"]:
        return "A_有中文"
    if r["only_en"]:
        return "B_只有英语"
    if r["has_other_nonEN"]:
        return "C_有其它大语种" if r["has_big"] else "D_有其它小语种"
    return "B_只有英语"

df["lang_group"] = df.apply(classify, axis=1)

order = ["A_有中文", "B_只有英语", "C_有其它大语种", "D_有其它小语种"]

# =====================================================================
# 3. 描述统计
# =====================================================================
print("\n" + "=" * 70)
print("Step 1: 分组描述统计 (含大厂游戏)")
print("=" * 70)
desc = df.groupby("lang_group").agg(
    N=("Log_Reviews", "size"),
    平均语言数=("n_langs", "mean"),
    Log均值=("Log_Reviews", "mean"),
    Log中位数=("Log_Reviews", "median"),
    评论均值=("Total_Reviews", "mean"),
    评论中位数=("Total_Reviews", "median"),
    平均价格=("price", "mean"),
).reindex(order)
print(desc.round(2).to_string())

# =====================================================================
# 4. 组间检验
# =====================================================================
print("\n" + "=" * 70)
print("Step 2: 组间差异检验 (DV = Log_Reviews, 基准=只有英语)")
print("=" * 70)
base = df[df["lang_group"] == "B_只有英语"]["Log_Reviews"]
print(f"基准组 [只有英语] 均值 = {base.mean():.3f} (N={len(base)})")
print(f"{'组别':<16}{'均值':>9}{'差值':>9}{'t':>9}{'p':>13}")
for g in order:
    if g == "B_只有英语":
        continue
    x = df[df["lang_group"] == g]["Log_Reviews"]
    t, p = stats.ttest_ind(x, base, equal_var=False)
    print(f"{g:<16}{x.mean():>9.3f}{x.mean()-base.mean():>+9.3f}{t:>9.3f}{p:>13.3e}")
groups = [df[df["lang_group"] == g]["Log_Reviews"].values for g in order]
F, pa = stats.f_oneway(*groups)
print(f"\nANOVA: F = {F:.2f}, p = {pa:.3e}")

# =====================================================================
# 5. 回归（不含杂交度）
# =====================================================================
print("\n" + "=" * 70)
print("Step 3: OLS 控制与效应 (DV = Log_Reviews, 参照=只有英语)")
print("=" * 70)

reg = df.dropna(subset=["Log_Reviews", "price", "Release_Year"]).copy()

def grp_dummies(frame):
    d = pd.get_dummies(frame["lang_group"], prefix="grp")
    return d[[f"grp_{g}" for g in order if g != "B_只有英语"]].astype(float)

def run_ols(frame, extra=None, label=""):
    parts = [grp_dummies(frame), frame[["price"]]]
    yd = pd.get_dummies(frame["Release_Year"], prefix="Y", drop_first=True).astype(float)
    parts.append(yd)
    if extra is not None:
        parts.append(extra)
    X = sm.add_constant(pd.concat(parts, axis=1))
    m = sm.OLS(frame["Log_Reviews"], X).fit()
    print(f"--- {label}: N={int(m.nobs)}, R²={m.rsquared:.4f}")
    for g in [x for x in order if x != "B_只有英语"]:
        print(f"    grp_{g:<14} {m.params[f'grp_{g}']:>+9.4f}  p={m.pvalues[f'grp_{g}']:.2e}")
    print(f"    price              {m.params['price']:>+9.4f}  p={m.pvalues['price']:.2e}")
    return m

# 模型1: price + 年份FE
m1 = run_ols(reg, None, "Model1: 仅价格+年份FE")

# =====================================================================
# 6. 增加 题材(genres) 控制
# =====================================================================
print("\n" + "=" * 70)
print("Step 4: 加入题材(genres)控制")
print("=" * 70)

def parse_genres(x):
    return [g.strip() for g in str(x).split(",") if g.strip()]

reg["genres_list"] = reg["genres"].apply(parse_genres)
genre_all = pd.Series([g for gl in reg["genres_list"] for g in gl]).value_counts()
# 只保留出现次数 >= 200 的主要题材做虚拟变量
major_genres = genre_all[genre_all >= 200].index.tolist()
print("主要题材 (>=200款):", major_genres)
genre_dum = pd.DataFrame(
    {f"G_{g}": reg["genres_list"].apply(lambda gl: int(g in gl)) for g in major_genres},
    index=reg.index,
).astype(float)

gd = genre_dum.copy()
m2 = run_ols(reg, gd, "Model2: 价格+年份FE + 题材")

# =====================================================================
# 7. 增加 发行商/开发者 控制（固定效应：出现>=X款的公司）
# =====================================================================
print("\n" + "=" * 70)
print("Step 5: 加入发行商固定效应")
print("=" * 70)

def parse_listcol(x):
    s = str(x).strip()
    if s.startswith("["):
        import ast
        try:
            v = ast.literal_eval(s)
            return [str(t).strip() for t in v]
        except Exception:
            return []
    return [t.strip() for t in s.split(",") if t.strip()]

reg["pub_list"] = reg["publishers"].apply(parse_listcol)
reg["dev_list"] = reg["developers"].apply(parse_listcol)
reg["pub_main"] = reg["pub_list"].apply(lambda l: l[0] if l else "UNKNOWN")
reg["dev_main"] = reg["dev_list"].apply(lambda l: l[0] if l else "UNKNOWN")

for col, name in [("pub_main", "发行商"), ("dev_main", "开发者")]:
    vc = reg[col].value_counts()
    keep = vc[vc >= 20].index.tolist()   # 出现>=20款的公司
    print(f"{name} 固定效应保留 {len(keep)} 个（>=20款），覆盖 {reg[col].isin(keep).sum()} 行")
    d = pd.get_dummies(reg[col].where(reg[col].isin(keep), "OTHER"), prefix=name)
    # 去掉一个作为基准
    d = d.drop(columns=d.columns[0]).astype(float)
    reg[f"_{name}_dum"] = d.values.tolist()
    globals()[f"dum_{name}"] = d
    run_ols(reg, pd.concat([gd, d], axis=1), f"Model: 价格+年份+题材+{name}FE")

print("\n[说明] 组别系数=相对「只有英语」组的 Log_Reviews 差异（log 点）；正值=更好。")