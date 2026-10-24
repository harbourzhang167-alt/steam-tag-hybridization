# -*- coding: utf-8 -*-
# --- workspace-root anchor (added during reorganisation) -------------------
from pathlib import Path as _Path
import os as _os
_ROOT = _Path(__file__).resolve().parent
while not (_ROOT / "01_data").exists() and _ROOT.parent != _ROOT:
    _ROOT = _ROOT.parent
_os.chdir(_ROOT)
# --------------------------------------------------------------------------
"# -*- coding: utf-8 -*-
\"\"\"
基于当前 pipeline 筛选流程，比较不同语言支持组别的商业表现。
分组（互斥）：
  A. 有中文          —— 支持简体或繁体中文
  B. 只有英语        —— 语言集合 == {English}
  C. 有其它大语种    —— 无中文、非纯英语，且含至少一个大语种
  D. 有其它小语种    —— 无中文、无大语种（通常 English+小语种，或纯小语种）
商业表现：Log_Reviews (pipeline 的因变量) 以及 Total_Reviews 原始量级。
\"\"\"
import sys
if sys.version_info >= (3, 7):
    try:
        sys.stdout.reconfigure(encoding=\"utf-8\")
        sys.stderr.reconfigure(encoding=\"utf-8\")
    except Exception:
        pass

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

pd.set_option(\"display.unicode.east_asian_width\", True)

# ---------------------------------------------------------------------------
# 1. 载入 pipeline 导出数据 + 合并语言列
# ---------------------------------------------------------------------------
exp = pd.read_csv(\"games_clustered_meta_export.csv\")
raw = pd.read_csv(
    \"steam_games_march2025_updated.csv\",
    usecols=[\"appid\", \"supported_languages\", \"supported_languages_counts\"],
)
df = exp.merge(raw, on=\"appid\", how=\"left\")
df = df.dropna(subset=[\"supported_languages\"]).copy()
df[\"lang_list\"] = df[\"supported_languages\"].apply(
    lambda x: [t.strip() for t in str(x).split(\",\") if t.strip()]
)
df[\"lang_set\"] = df[\"lang_list\"].apply(set)
df[\"n_langs\"] = df[\"lang_list\"].apply(len)

# ---------------------------------------------------------------------------
# 2. 定义大语种 / 中文
# ---------------------------------------------------------------------------
ZH = {\"Simplified Chinese\", \"Traditional Chinese\"}
# 大语种：样本中出现频次较高(=2000 款以上)的非中文主力本地化语言
BIG = {
    \"German\", \"French\", \"Spanish - Spain\", \"Japanese\", \"Russian\",
    \"Italian\", \"Korean\", \"Portuguese - Brazil\", \"Polish\", \"Turkish\",
    \"Spanish - Latin America\",
}

def classify(s):
    has_zh = bool(s & ZH)
    if has_zh:
        return \"A_有中文\"
    if s == {\"English\"}:
        return \"B_只有英语\"
    if s - {\"English\"}:
        if s & BIG:
            return \"C_有其它大语种\"
        return \"D_有其它小语种\"
    # 仅 English 且无其它（上面已覆盖），兜底
    return \"B_只有英语\"

df[\"lang_group\"] = df[\"lang_set\"].apply(classify)

# ---------------------------------------------------------------------------
# 3. 描述性统计
# ---------------------------------------------------------------------------
print(\"=\" * 70)
print(\"Step 1: 分组规模与商业表现描述统计\")
print(\"=\" * 70)

order = [\"A_有中文\", \"B_只有英语\", \"C_有其它大语种\", \"D_有其它小语种\"]
desc = df.groupby(\"lang_group\").agg(
    N=(\"Log_Reviews\", \"size\"),
    平均支持语言数=(\"n_langs\", \"mean\"),
    Log_Reviews均值=(\"Log_Reviews\", \"mean\"),
    Log_Reviews中位数=(\"Log_Reviews\", \"median\"),
    评论数均值=(\"Total_Reviews\", \"mean\"),
    评论数中位数=(\"Total_Reviews\", \"median\"),
    平均价格=(\"price\", \"mean\"),
    平均杂交度=(\"Hybridization_Index\", \"mean\"),
).reindex(order)
print(desc.round(2).to_string())

# ---------------------------------------------------------------------------
# 4. 组间均值检验 (以「只有英语」为基准的 t 检验 + 总体 ANOVA)
# ---------------------------------------------------------------------------
print(\"\\n\" + \"=\" * 70)
print(\"Step 2: 组间差异检验 (DV = Log_Reviews)\")
print(\"=\" * 70)

base = df[df[\"lang_group\"] == \"B_只有英语\"][\"Log_Reviews\"]
print(f\"基准组 [只有英语] 均值 = {base.mean():.3f} (N={len(base)})\")
print(f\"{'组别':<16}{'均值':>9}{'差值':>9}{'t':>9}{'p':>12}\")
for g in order:
    if g == \"B_只有英语\":
        continue
    x = df[df[\"lang_group\"] == g][\"Log_Reviews\"]
    t, p = stats.ttest_ind(x, base, equal_var=False)
    print(f\"{g:<16}{x.mean():>9.3f}{x.mean()-base.mean():>+9.3f}{t:>9.3f}{p:>12.3e}\")

groups = [df[df[\"lang_group\"] == g][\"Log_Reviews\"].values for g in order]
F, p_anova = stats.f_oneway(*groups)
print(f\"\\n单因素 ANOVA: F = {F:.2f}, p = {p_anova:.3e}\")

# ---------------------------------------------------------------------------
# 5. 回归（吸收混杂）：组别虚拟变量 + 价格 + 年份FE + 杂交度
# ---------------------------------------------------------------------------
print(\"\\n\" + \"=\" * 70)
print(\"Step 3: OLS — 控制价格/年份FE/杂交度后组别效应 (DV = Log_Reviews)\")
print(\"=\" * 70)

reg = df.dropna(subset=[\"Log_Reviews\", \"price\", \"Hybrid_Centered\",
                        \"Hybrid_Centered_Squared\", \"Release_Year\"]).copy()
# 以「只有英语」为参照组
dummies = pd.get_dummies(reg[\"lang_group\"], prefix=\"grp\")
for g in order[1:]:  # 去掉基准
    col = f\"grp_{g}\"
    if col not in dummies:
        dummies[col] = 0
dummies = dummies[[f\"grp_{g}\" for g in order if g != \"B_只有英语\"]].astype(float)

year_dum = pd.get_dummies(reg[\"Release_Year\"], prefix=\"Y\", drop_first=True).astype(float)

X = pd.concat([
    dummies,
    reg[[\"Hybrid_Centered\", \"Hybrid_Centered_Squared\", \"price\"]],
    year_dum,
], axis=1)
X = sm.add_constant(X)
model = sm.OLS(reg[\"Log_Reviews\"], X).fit()

print(f\"N = {int(model.nobs)}, R² = {model.rsquared:.4f}\")
print(f\"参照组: B_只有英语\\n\")
print(f\"{'变量':<28}{'coef':>10}{'p':>12}\")
for v in [f\"grp_{g}\" for g in order if g != \"B_只有英语\"]:
    print(f\"{v:<28}{model.params[v]:>+10.4f}{model.pvalues[v]:>12.3e}\")
print(f\"{'Hybrid_Centered':<28}{model.params['Hybrid_Centered']:>+10.4f}{model.pvalues['Hybrid_Centered']:>12.3e}\")
print(f\"{'Hybrid_Centered_Squared':<28}{model.params['Hybrid_Centered_Squared']:>+10.4f}{model.pvalues['Hybrid_Centered_Squared']:>12.3e}\")
print(f\"{'price':<28}{model.params['price']:>+10.4f}{model.pvalues['price']:>12.3e}\")

print(\"\\n[注] 组别系数解释：相对「只有英语」组的 Log_Reviews 差异；\"+
      \"正值=商业表现更好。\")
"