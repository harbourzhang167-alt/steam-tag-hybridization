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

# 1. 载入 pipeline 导出数据 + 合并语言列
exp = pd.read_csv("01_data/processed/games_clustered_meta_export.csv")
raw = pd.read_csv(
    "01_data/raw/steam_games_march2025_updated.csv",
    usecols=["appid", "supported_languages", "supported_languages_counts"],
)
df = exp.merge(raw, on="appid", how="left")
df = df.dropna(subset=["supported_languages"]).copy()
df["lang_list"] = df["supported_languages"].apply(
    lambda x: [t.strip() for t in str(x).split(",") if t.strip()]
)
df["lang_set"] = df["lang_list"].apply(set)
df["n_langs"] = df["lang_list"].apply(len)

# 2. 定义大语种 / 中文
ZH = {"Simplified Chinese", "Traditional Chinese"}
BIG = {
    "German", "French", "Spanish - Spain", "Japanese", "Russian",
    "Italian", "Korean", "Portuguese - Brazil", "Polish", "Turkish",
    "Spanish - Latin America",
}

def classify(s):
    if s & ZH:
        return "A_有中文"
    if s == {"English"}:
        return "B_只有英语"
    if s - {"English"}:
        if s & BIG:
            return "C_有其它大语种"
        return "D_有其它小语种"
    return "B_只有英语"

df["lang_group"] = df["lang_set"].apply(classify)

# 3. 描述统计
print("=" * 70)
print("Step 1: 分组规模与商业表现描述统计")
print("=" * 70)
order = ["A_有中文", "B_只有英语", "C_有其它大语种", "D_有其它小语种"]
desc = df.groupby("lang_group").agg(
    N=("Log_Reviews", "size"),
    平均语言数=("n_langs", "mean"),
    Log均值=("Log_Reviews", "mean"),
    Log中位数=("Log_Reviews", "median"),
    评论均值=("Total_Reviews", "mean"),
    评论中位数=("Total_Reviews", "median"),
    平均价格=("price", "mean"),
    平均杂交度=("Hybridization_Index", "mean"),
).reindex(order)
print(desc.round(2).to_string())

# 4. 组间检验
print("\n" + "=" * 70)
print("Step 2: 组间差异检验 (DV = Log_Reviews)")
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
F, p_anova = stats.f_oneway(*groups)
print(f"\n单因素 ANOVA: F = {F:.2f}, p = {p_anova:.3e}")

# 5. 回归
print("\n" + "=" * 70)
print("Step 3: OLS — 控制价格/年份FE/杂交度后组别效应 (DV = Log_Reviews)")
print("=" * 70)
reg = df.dropna(subset=["Log_Reviews", "price", "Hybrid_Centered",
                        "Hybrid_Centered_Squared", "Release_Year"]).copy()
dummies = pd.get_dummies(reg["lang_group"], prefix="grp")
for g in order:
    col = f"grp_{g}"
    if col not in dummies:
        dummies[col] = 0
dummies = dummies[[f"grp_{g}" for g in order if g != "B_只有英语"]].astype(float)
year_dum = pd.get_dummies(reg["Release_Year"], prefix="Y", drop_first=True).astype(float)
X = pd.concat([dummies, reg[["Hybrid_Centered", "Hybrid_Centered_Squared", "price"]], year_dum], axis=1)
X = sm.add_constant(X)
model = sm.OLS(reg["Log_Reviews"], X).fit()
print(f"N = {int(model.nobs)}, R² = {model.rsquared:.4f}")
print("参照组: B_只有英语\n")
print(f"{'变量':<28}{'coef':>10}{'p':>13}")
for v in [f"grp_{g}" for g in order if g != "B_只有英语"]:
    print(f"{v:<28}{model.params[v]:>+10.4f}{model.pvalues[v]:>13.3e}")
print(f"{'Hybrid_Centered':<28}{model.params['Hybrid_Centered']:>+10.4f}{model.pvalues['Hybrid_Centered']:>13.3e}")
print(f"{'Hybrid_Centered_Squared':<28}{model.params['Hybrid_Centered_Squared']:>+10.4f}{model.pvalues['Hybrid_Centered_Squared']:>13.3e}")
print(f"{'price':<28}{model.params['price']:>+10.4f}{model.pvalues['price']:>13.3e}")
print("\n[注] 组别系数=相对「只有英语」组的 Log_Reviews 差异；正值=更好。")