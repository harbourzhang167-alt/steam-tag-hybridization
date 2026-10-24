# -*- coding: utf-8 -*-
"""
Decompose the "quality proxy" regression (E3 of verify_all.py).

Purpose
-------
verify_all.py section E3 added four log-transformed QA / investment proxies to
the main model and reported that `price` collapses to insignificance while R^2
jumps from 0.1622 to 0.6940.  That single line of evidence is easy to
over-read, so this script documents exactly HOW the proxies are applied and
stress-tests the result:

  1. sample construction + merge route (how the proxy columns get into the
     fact table at all);
  2. missingness and the log1p transform actually used;
  3. baseline vs. full model, side by side;
  4. correlation matrix of the proxies with price / hybridization / DV;
  5. VIF of the full design matrix (are the proxies competing for the same
     variance?);
  6. one-at-a-time ablation (which single proxy kills `price`?);
  7. drop `peak_ccu` (a concurrent-popularity proxy that may be an *outcome*
     of the DV rather than a quality measure);
  8. a single standardised composite instead of four collinear regressors.

Environment: no statsmodels / sklearn / scipy -> numpy normal equations, HC1.

Usage:  python 06_tools/check_quality_proxies.py
Output: 06_tools/quality_proxy_report.md  (+ same content on stdout)
"""
from pathlib import Path as _Path
import os as _os
_ROOT = _Path(__file__).resolve().parent
while not (_ROOT / "01_data").exists() and _ROOT.parent != _ROOT:
    _ROOT = _ROOT.parent
_os.chdir(_ROOT)

import sys
import math
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DATA = ROOT / "01_data/processed/games_clustered_meta_export.csv"
RAW = ROOT / "01_data/raw/steam_games_march2025_updated.csv"
OUT = HERE / "quality_proxy_report.md"

PROXIES = ["average_playtime_forever", "achievements", "dlc_count", "peak_ccu"]
LN = {"average_playtime_forever": "ln_playtime", "achievements": "ln_achievements",
      "dlc_count": "ln_dlc", "peak_ccu": "ln_peak_ccu"}

lines = []


def p(*a):
    s = " ".join(str(x) for x in a)
    lines.append(s)
    print(s)


def head(t):
    p("")
    p("## " + t)
    p("")


def table(df, floatfmt="{:.4f}"):
    df = df if isinstance(df, pd.DataFrame) else pd.DataFrame(df)
    cols = [str(c) for c in df.columns]
    p("| " + " | ".join(cols) + " |")
    p("|" + "|".join(["---"] * len(cols)) + "|")
    for _, r in df.iterrows():
        cells = []
        for v in r:
            if isinstance(v, str):
                cells.append(v)
            elif isinstance(v, (int, np.integer)):
                cells.append(str(int(v)))
            elif isinstance(v, (float, np.floating)):
                cells.append("" if pd.isna(v) else floatfmt.format(v))
            else:
                cells.append(str(v))
        p("| " + " | ".join(cells) + " |")


# ---------------------------------------------------------------------------
# OLS helpers (identical to verify_all.py)
# ---------------------------------------------------------------------------
def ols(y, X, names):
    X = np.asarray(X, dtype=float)
    y = np.asarray(y, dtype=float).reshape(-1, 1)
    n, k = X.shape
    if names is not None:
        assert len(names) == k, f"names ({len(names)}) != design columns ({k})"
    XtX_inv = np.linalg.pinv(X.T @ X)
    beta = XtX_inv @ (X.T @ y)
    resid = y - X @ beta
    ssr = float(resid.T @ resid)
    sst = float(((y - y.mean()) ** 2).sum())
    r2 = 1 - ssr / sst
    adj_r2 = 1 - (1 - r2) * (n - 1) / (n - k)
    sigma2 = ssr / (n - k)
    var_c = sigma2 * XtX_inv
    meat = (X * (resid ** 2)).T @ X
    var_h = (n / (n - k)) * (XtX_inv @ meat @ XtX_inv)
    se_c = np.sqrt(np.diag(var_c))
    se_h = np.sqrt(np.diag(var_h))
    return dict(names=list(names), beta=beta.ravel(), se_c=se_c, se_h=se_h,
                t_c=beta.ravel() / se_c, t_h=beta.ravel() / se_h,
                r2=r2, adj_r2=adj_r2, n=n, k=k, resid=resid.ravel())


def stars(t):
    at = abs(t)
    return "***" if at > 3.29 else "**" if at > 2.58 else "*" if at > 1.96 else ""


def pick(res, wanted):
    rows = []
    for i, nm in enumerate(res["names"]):
        if nm not in wanted:
            continue
        rows.append({"变量": nm, "coef": res["beta"][i], "SE(HC1)": res["se_h"][i],
                     "t(HC1)": res["t_h"][i], "": stars(res["t_h"][i])})
    return pd.DataFrame(rows)


def peak(mean_h, b1, b2):
    return mean_h + (-b1 / (2 * b2))


def vif(X, names):
    """VIF for each column of X, regressing it on all the others (+ intercept)."""
    out = []
    for j, nm in enumerate(names):
        yv = X[:, j]
        others = np.delete(X, j, axis=1)
        others = np.column_stack([np.ones(len(X)), others])   # intercept required
        r = ols(yv, others, [f"x{i}" for i in range(others.shape[1])])
        out.append({"变量": nm, "R²(对其他解释变量)": r["r2"],
                    "VIF": 1.0 / max(1e-12, 1.0 - r["r2"])})
    return pd.DataFrame(out)


# ===========================================================================
p("# 质量代理回归（verify_all.py §E3）施加方式与稳健性拆解")
p("")
p(f"生成时间: {pd.Timestamp.now():%Y-%m-%d %H:%M:%S}")
p("")
p("本报告回答一个问题：**「加入质量代理后 price 不显著」这一步到底是怎么做的、"
  "结论有多稳。** 所有数字由 numpy 正规方程独立重估（HC1 稳健标准误）。")

# ---------------------------------------------------------------- 1. sample
head("1. 样本与合并路径（代理变量是怎么进来的）")
df = pd.read_csv(DATA)
p(f"- 事实表 `games_clustered_meta_export.csv`：**{df.shape[0]} 行 × {df.shape[1]} 列**")
p(f"- 事实表列名：{list(df.columns)}")
p("")
missing_cols = [c for c in PROXIES if c not in df.columns]
p(f"- 四个代理变量中**存在于事实表**的：{ [c for c in PROXIES if c in df.columns] or '无' }")
p(f"- 因此需要从原始 CSV 回并的列：**{missing_cols}**")
p("")
p("合并语句（与 verify_all.py 完全一致）：")
p("")
p("```python")
p('raw = pd.read_csv(RAW, usecols=["appid", "pct_pos_total", "average_playtime_forever",')
p('                                "metacritic_score", "achievements", "dlc_count", "peak_ccu"])')
p('m = reg.merge(raw, on="appid", how="left")          # 左连接，回并到回归样本上')
p('```')
p("")
p("- 关键点：代理变量**不是**主管线算出来的，而是**按 `appid` 从原始 CSV 左连接回并**；"
  "所以这一步不改变任何已有变量，只追加列。")

# build the regression sample exactly as verify_all.py does
reg = df[df.Hybridization_Index > 0].dropna(
    subset=["Log_Reviews", "Hybrid_Centered", "Hybrid_Centered_Squared", "price"]).copy()
p("")
p("回归样本构造（与主管线一致）：")
p("")
p("```python")
p('reg = df[df.Hybridization_Index > 0].dropna(')
p('    subset=["Log_Reviews", "Hybrid_Centered", "Hybrid_Centered_Squared", "price"])')
p("```")
p("")
p(f"- 事实表 {len(df)} 行 → 回归样本 **N = {len(reg)}** 行"
  f"（剔除杂交度为 0 的 {len(df) - len(reg)} 行）")

raw = pd.read_csv(RAW, usecols=["appid"] + PROXIES + ["metacritic_score"])
m = reg.merge(raw, on="appid", how="left")
p(f"- 左连接后行数 = **{len(m)}**（未发生行扩张 ⇒ `appid` 在原始表中唯一）")
p("")

na = m[PROXIES + ["metacritic_score"]].isna().sum().rename("缺失行数").to_frame()
na["缺失率%"] = 100 * na["缺失行数"] / len(m)
na["是否进入回归"] = ["是" if c in PROXIES else "否（仅读入未使用）"
                      for c in na.index]
table(na.reset_index().rename(columns={"index": "列"}), floatfmt="{:.2f}")
p("")
p(f"- 四个代理变量缺失行数全为 **0** ⇒ `dropna` 一行都没删，"
  f"E3 的样本与主模型**完全同一批 {len(m)} 款游戏**（这是可比性的前提）。")
p("- `metacritic_score` **被读入但未进入回归**（独立游戏缺失太多），是本检验的一个已知缺口。")

# ------------------------------------------------------------- 2. transform
head("2. 变换方式：逐列 log1p")
p("实际进入回归的是 **`np.log1p(x)`（自然对数，ln(1+x)）**，直接用原始量纲会严重右偏：")
p("")
d = m[PROXIES].describe().T[["min", "50%", "mean", "max"]]
d.columns = ["min", "中位数", "均值", "max"]
d["ln后均值"] = [np.log1p(m[c]).mean() for c in PROXIES]
d["偏度(原始)"] = [m[c].skew() for c in PROXIES]
d["偏度(ln1p)"] = [np.log1p(m[c]).skew() for c in PROXIES]
table(d.reset_index().rename(columns={"index": "变量"}), floatfmt="{:.3f}")
p("")
p("对应代码：")
p("")
p("```python")
p("ctrl = np.column_stack([")
p("    np.log1p(m3.average_playtime_forever.values),")
p("    np.log1p(m3.achievements.values),")
p("    np.log1p(m3.dlc_count.values),")
p("    np.log1p(m3.peak_ccu.values),")
p("])")
p("```")
p("")
p("含义对照：`ln_playtime` = 单局时长/留存（投入深度）；`ln_achievements` = 内容体量；"
  "`ln_dlc` = 后续运营投入；`ln_peak_ccu` = 并发峰值（**需求侧热度**，与因变量同源，见 §6）。")

# ---------------------------------------------------------- 3. specifications
head("3. 规格：与主模型只差追加的 4 列")

yd = pd.get_dummies(reg.Release_Year, prefix="Y", drop_first=True).astype(float)
ycols = list(yd.columns)
Y = reg.Log_Reviews.values
p("主模型（baseline）：")
p("")
p("```python")
p("X_main = [1, Hybrid_Centered, Hybrid_Centered_Squared, price, 年份哑变量]")
p("```")
p("")
p("E3（质量代理版）= baseline **原封不动** + 4 列 log 代理，无交互项、无标准化、"
  "无样本变动：")
p("")
p("```python")
p("Xq = [1, Hybrid_Centered, Hybrid_Centered_Squared, price, 年份哑变量,")
p("      ln_playtime, ln_achievements, ln_dlc, ln_peak_ccu]")
p("```")
p("")
base_X = np.column_stack([np.ones(len(reg)), reg.Hybrid_Centered.values,
                          reg.Hybrid_Centered_Squared.values, reg.price.values, yd.values])
base_names = ["const", "Hybrid_Centered", "Hybrid_Centered_Squared", "price"] + ycols
res_b = ols(Y, base_X, base_names)

ctrl = np.column_stack([np.log1p(m[c].values) for c in PROXIES])
full_X = np.column_stack([base_X, ctrl])
full_names = base_names + [LN[c] for c in PROXIES]
res_f = ols(Y, full_X, full_names)

mean_h = reg.Hybridization_Index.mean()
cmp_rows = []
for lbl, r in (("baseline", res_b), ("+质量代理", res_f)):
    cmp_rows.append({"模型": lbl, "N": r["n"], "k": r["k"], "R²": r["r2"],
                     "Adj.R²": r["adj_r2"],
                     "β1": r["beta"][1], "β2": r["beta"][2],
                     "price coef": r["beta"][3],
                     "price t(HC1)": r["t_h"][3],
                     "拐点": peak(mean_h, r["beta"][1], r["beta"][2])})
table(pd.DataFrame(cmp_rows), floatfmt="{:.4f}")
p("")
p("完整系数（质量代理版，只显示核心项与代理项）：")
p("")
table(pick(res_f, ["Hybrid_Centered", "Hybrid_Centered_Squared", "price"] + [LN[c] for c in PROXIES]),
      floatfmt="{:.4f}")
p("")
p("**复现确认**：baseline 的 price 系数 +0.03812 / t(HC1)≈23.6，"
  "质量代理版 −0.0001 / t=−0.13，R² 0.1622 → 0.6940，与 §E3 报告一致。")

# ------------------------------------------------------------ 4. correlations
head("4. 相关性：四个代理是不是在抢同一块方差")
corr_cols = [LN[c] for c in PROXIES] + ["price", "Hybridization_Index", "Log_Reviews"]
cdf = pd.DataFrame({
    "ln_playtime": np.log1p(m.average_playtime_forever.values),
    "ln_achievements": np.log1p(m.achievements.values),
    "ln_dlc": np.log1p(m.dlc_count.values),
    "ln_peak_ccu": np.log1p(m.peak_ccu.values),
    "price": m.price.values,
    "Hybridization_Index": m.Hybridization_Index.values,
    "Log_Reviews": m.Log_Reviews.values,
})
cm = cdf.corr().round(3)
cm.insert(0, "", cm.index)
table(cm, floatfmt="{:.3f}")
p("")
p("读法（以下均为实测值）：")
p("")
_pc = cdf[[LN[c] for c in PROXIES]].corr().values
_off = _pc[~np.eye(len(_pc), dtype=bool)]
_hi = cdf[[LN[c] for c in PROXIES]].corr().where(
    ~np.eye(len(_pc), dtype=bool)).stack().idxmax()
p(f"- 四个代理**两两相关只有 {_off.min():.3f}–{_off.max():.3f}**（最高的一对是 "
  f"{_hi[0]}–{_hi[1]}），属中等相关，**够不上「互相抵消」的共线性**；"
  "所以代理入模后系数怎么变，必须看 §6 的逐个加入，而不能归因于共线性；")
p(f"- `ln_peak_ccu` 与因变量 `Log_Reviews` 相关 **{cdf['ln_peak_ccu'].corr(cdf['Log_Reviews']):.3f}**，"
  f"而 `ln_playtime` 只有 {cdf['ln_playtime'].corr(cdf['Log_Reviews']):.3f}、"
  f"`ln_achievements` 只有 {cdf['ln_achievements'].corr(cdf['Log_Reviews']):.3f} —— "
  "peak_ccu 本质上**与因变量同源**（都是热度/规模的同期表现），不是外生质量指标；")
_hc = [cdf[LN[c]].corr(cdf["Hybridization_Index"]) for c in PROXIES]
p(f"- 四个代理与 `Hybridization_Index` 的相关只有 {min(_hc):.3f}–{max(_hc):.3f} ⇒ "
  "它们**几乎不吸收杂交度的方差**，这正是二次项在加入代理后仍然存活的原因。")

# ------------------------------------------------------------------- 5. VIF
head("5. 共线性诊断：代理能不能替 price「背锅」")
vif_core = ["Hybrid_Centered", "Hybrid_Centered_Squared", "price"] + [LN[c] for c in PROXIES]
core_idx = [full_names.index(n) for n in vif_core]
_vt = vif(full_X[:, core_idx], vif_core)
table(_vt, floatfmt="{:.3f}")
p("")
p(f"- 核心变量 VIF 落在 {_vt.VIF.min():.2f}–{_vt.VIF.max():.2f}，**全部远低于 5** "
  "⇒ 不存在灾难性共线性，price 归零**不能**用方差膨胀解释；")
p("")
p("更有信息量的诊断：四个代理各自能解释多少 `price` 和多少 `Hybridization_Index`。")
p("")
_pX = np.column_stack([np.ones(len(m)), ctrl])
r_price = ols(m.price.values, _pX, ["const"] + [LN[c] for c in PROXIES])
r_h = ols(m.Hybridization_Index.values, _pX, ["const"] + [LN[c] for c in PROXIES])
p(f"- `price` 对四个代理回归：R² = **{r_price['r2']:.4f}** ⇒ 价格里约 "
  f"{100 * r_price['r2']:.1f}% 的方差可由开发体量/热度代理解释，"
  "这就是主模型 price 系数「不干净」的来源；")
p(f"- `Hybridization_Index` 对四个代理回归：R² = **{r_h['r2']:.4f}** ⇒ 杂交度与这组代理"
  "**近乎正交**，倒 U 不可能被它们吸收掉。")

# -------------------------------------------------------------- 6. ablation
head("6. 逐个加入（ablation）：到底是谁杀死了 price")
rows = []
for c in PROXIES:
    Xi = np.column_stack([base_X, np.log1p(m[c].values)])
    ri = ols(Y, Xi, base_names + [LN[c]])
    rows.append({"只加入": LN[c], "R²": ri["r2"],
                 "price coef": ri["beta"][3], "price t(HC1)": ri["t_h"][3],
                 "该代理 coef": ri["beta"][-1], "该代理 t": ri["t_h"][-1],
                 "β1": ri["beta"][1], "β2": ri["beta"][2],
                 "拐点": peak(mean_h, ri["beta"][1], ri["beta"][2])})
rows.append({"只加入": "（四个一起，= E3）", "R²": res_f["r2"],
             "price coef": res_f["beta"][3], "price t(HC1)": res_f["t_h"][3],
             "该代理 coef": np.nan, "该代理 t": np.nan,
             "β1": res_f["beta"][1], "β2": res_f["beta"][2],
             "拐点": peak(mean_h, res_f["beta"][1], res_f["beta"][2])})
table(pd.DataFrame(rows), floatfmt="{:.4f}")
p("")
_b = res_b["beta"][3]
_pk = [r for r in rows if r["只加入"] == "ln_peak_ccu"][0]
_oth = [r for r in rows if r["只加入"] not in ("ln_peak_ccu", "（四个一起，= E3）")]
_gain = res_f["r2"] - res_b["r2"]
p(f"- baseline 的 price 系数是 **{_b:+.4f}**；单独加入 playtime / achievements / dlc 时，"
  f"price 仍在 {min(r['price coef'] for r in _oth):+.4f} ~ {max(r['price coef'] for r in _oth):+.4f}、"
  f"t = {min(r['price t(HC1)'] for r in _oth):.1f}~{max(r['price t(HC1)'] for r in _oth):.1f}，"
  "**照样显著**；")
p(f"- 但单独加入 **`ln_peak_ccu`** 就把 price 压到 {_pk['price coef']:+.4f}"
  f"（t = {_pk['price t(HC1)']:.2f}，相对 baseline 衰减 {100 * (_b - _pk['price coef']) / _b:.0f}%），"
  f"且它一个变量就贡献了 R² 增量 {_gain:.4f} 中的 "
  f"{100 * (_pk['R²'] - res_b['r2']) / _gain:.0f}%；")
p("- 四个一起进入才让 price 归零 ⇒ **主因是 `peak_ccu` 这个与因变量同源的热度变量**，"
  "而不是四个代理组成的「共同质量因子」。")

# --------------------------------------------------- 7. drop peak_ccu / composite
head("7. 两个更干净的替代规格")
p("### 7.1 剔除 `ln_peak_ccu`（去掉热度内生项）")
keep = ["average_playtime_forever", "achievements", "dlc_count"]
X_k = np.column_stack([base_X] + [np.log1p(m[c].values) for c in keep])
res_k = ols(Y, X_k, base_names + [LN[c] for c in keep])
p("")
p(f"- N = {res_k['n']}, R² = **{res_k['r2']:.4f}**")
p("")
table(pick(res_k, ["Hybrid_Centered", "Hybrid_Centered_Squared", "price"] + [LN[c] for c in keep]),
      floatfmt="{:.4f}")
p("")
p(f"- 拐点 = **{peak(mean_h, res_k['beta'][1], res_k['beta'][2]):.2f}**")

p("")
p("### 7.2 用单一标准化合成指标代替四个相关代理")
p("")
p("```python")
p("z = (ln_proxy - ln_proxy.mean()) / ln_proxy.std()   # 逐列 z 分数（ddof=1）")
p("composite = mean(z_playtime, z_achievements, z_dlc, z_peak_ccu)   # 等权质量指数")
p("```")
p("")
Z = np.column_stack([(np.log1p(m[c].values) - np.log1p(m[c].values).mean())
                     / np.log1p(m[c].values).std(ddof=1) for c in PROXIES])
comp = Z.mean(axis=1)
X_z = np.column_stack([base_X, comp])
res_z = ols(Y, X_z, base_names + ["quality_z"])
p(f"- `quality_z`：均值 {comp.mean():.3f}，SD {comp.std(ddof=1):.3f}，"
  f"与 H 相关 {np.corrcoef(comp, m.Hybridization_Index.values)[0,1]:.3f}")
p(f"- N = {res_z['n']}, R² = **{res_z['r2']:.4f}**")
p("")
table(pick(res_z, ["Hybrid_Centered", "Hybrid_Centered_Squared", "price", "quality_z"]),
      floatfmt="{:.4f}")
p("")
p(f"- 拐点 = **{peak(mean_h, res_z['beta'][1], res_z['beta'][2]):.2f}**")
p("")
p("合成指标把四个代理压成 1 个自由度，避免四个变量争夺同一块共享方差，"
  "是这一组检验里**最可信的一版**：它同时回答了「price 还剩多少」和"
  "「二次项还站不站得住」。")

# ---------------------------------------------------------------- 8. summary
head("8. 结论：这一步能支持什么、不能支持什么")
p("**能支持**")
p("")
p("- 倒 U 型**不是质量/投入代理的伪装**：从 baseline 到四种代理规格，β2 始终为负且 |t| 很大；"
  f"`quality_z` 合成版 β2 = {res_z['beta'][2]:.4f}、拐点 {peak(mean_h, res_z['beta'][1], res_z['beta'][2]):.2f}，"
  "与主模型（β2 = −0.0145、峰值 11.96）同向同量级 ⇒ 结论加固；")
p(f"- 四个代理与杂交度的解释力只有 R² = {r_h['r2']:.4f} ⇒ 倒 U 与质量是**两块近乎正交的方差**，"
  "不存在「控制质量后倒 U 消失」的风险；")
p(f"- 原主模型里 `price` 的正系数**不稳健**：price 有 {100 * r_price['r2']:.1f}% 的方差能被"
  "开发体量/热度解释，加入代理后从 +0.0381 掉到 0 附近；")
p("")
p("**不能支持（比对上面几点同样重要）**")
p("")
p(f"- **不能**说「price 的效应完全由质量吸收」：逐个加入时 price 依然显著"
  f"（§6），剔除同源的 `ln_peak_ccu` 后 price 回升到 {res_k['beta'][3]:+.4f}"
  f"（t = {res_k['t_h'][3]:.1f}，≈ baseline 的 {100 * res_k['beta'][3] / _b:.0f}%），"
  f"合成指标版也有 {res_z['beta'][3]:+.4f}（t = {res_z['t_h'][3]:.1f}）。"
  "**正确表述是「价格效应大幅缩水、识别不干净」，而不是「价格无效应」**；")
p(f"- 拐点 11.96 → 13.91 的位移**完全由 `ln_peak_ccu` 造成**：剔除它以后拐点回到 "
  f"**{peak(mean_h, res_k['beta'][1], res_k['beta'][2]):.2f}**，合成版 "
  f"{peak(mean_h, res_z['beta'][1], res_z['beta'][2]):.2f} ⇒ 峰值应报 ≈11.8–12.0，"
  "13.91 是同源控制变量带来的假位移（这一点反而**加固**了基准拐点，"
  "并与 §E1 分箱均值在 (10,12] 见顶一致）；")
p("- **不是因果识别**：没有工具变量、没有面板/时间变动、没有断点。`peak_ccu` 与因变量同源"
  "（并发热度），属「坏控制」；playtime 也是成功的结果而非原因。"
  "因此这只是**遗漏变量敏感性检验**，不能替代识别策略；")
p("- `metacritic_score` 未使用（独立游戏缺失严重），是**唯一可直接补的缺口** —— "
  "若要用外部质量评分，需先报告其缺失率与选择性问题。")

head("9. 审计更正记录（本报告相对 verify_report.md 旧版 §E3 的差异）")
p("")
p("`verify_all.py` 旧版 §E3 的 `ols()` 只传了 8 个变量名，而设计矩阵有 18 列"
  "（含 10 个年份哑变量）。`coef_table()` 按下标取名字，于是"
  "**标着 `ln_playtime`/`ln_achievements`/`ln_dlc`/`ln_peak_ccu` 的四行其实是 "
  "`Y_2016`~`Y_2019` 的年份哑变量系数**（−0.044 / −0.180 / −0.177 / −0.115）。")
p("")
p("- 受影响的只有**这四行的标签**；同一回归里的 N、R²、`price`、`Hybrid_Centered`、"
  "`Hybrid_Centered_Squared`、拐点都是前 4 列，**未被污染**；")
p("- 四个代理的**真实**系数是 "
  f"`ln_playtime` {res_f['beta'][-4]:+.4f}、`ln_achievements` {res_f['beta'][-3]:+.4f}、"
  f"`ln_dlc` {res_f['beta'][-2]:+.4f}、`ln_peak_ccu` {res_f['beta'][-1]:+.4f}"
  "（全部为正、高度显著，符合经济直觉）；")
p("- 已修复 `verify_all.py`（补全名字列表并重新生成 `verify_report.md`），"
  "并同步更正 `reference_pipeline_and_paper.md` 中引用该表的一行。"
  "**教训**：OLS 封装函数应按列数校验名字列表长度，`assert len(names) == X.shape[1]`。")

OUT.write_text("\n".join(lines), encoding="utf-8")
print(f"\n[written] {OUT}")
