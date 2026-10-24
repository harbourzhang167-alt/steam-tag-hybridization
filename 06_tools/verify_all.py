# -*- coding: utf-8 -*-
"""
Full audit + independent re-estimation of the dissertation pipeline outputs.

Environment: no sklearn / statsmodels / scipy available, so:
  - the audit is pure pandas/numpy;
  - OLS with year fixed effects is re-estimated via numpy (normal equations),
    with both classical and HC1 heteroskedasticity-robust standard errors.

Usage:
    python 06_tools/verify_all.py
Outputs:
    06_tools/verify_report.md   (markdown report)
    stdout                      (same content)
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
import sys, json, math
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "01_data/processed/games_clustered_meta_export.csv"
RAW = ROOT / "01_data/raw/steam_games_march2025_updated.csv"
OUT = Path(__file__).resolve().parent / "verify_report.md"

lines = []
def p(*a):
    s = " ".join(str(x) for x in a)
    lines.append(s)
    print(s)

def head(t):
    p("")
    p("## " + t)
    p("")

def _fmt(v, floatfmt):
    if isinstance(v, str):
        return v
    if isinstance(v, (int, np.integer)):
        return f"{int(v):,}"
    if isinstance(v, (float, np.floating)):
        if float(v).is_integer() and abs(v) < 1e15:
            return f"{int(v):,}"
        return floatfmt.format(float(v))
    return str(v)

def table(df, floatfmt="{:,.4f}"):
    """Markdown table without the tabulate dependency."""
    df = df.reset_index() if df.index.name or not isinstance(df.index, pd.RangeIndex) else df
    cols = [str(c) for c in df.columns]
    rows = [[_fmt(v, floatfmt) for v in rec] for rec in df.itertuples(index=False)]
    p("| " + " | ".join(cols) + " |")
    p("|" + "|".join(["---"] * len(cols)) + "|")
    for r in rows:
        p("| " + " | ".join(r) + " |")

# ----------------------------------------------------------------------------
# OLS helpers (numpy only)
# ----------------------------------------------------------------------------
def ols(y, X, names):
    """Return dict with params, classical SE, HC1 SE, t, p (normal approx), R2, N."""
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
    var_classic = sigma2 * XtX_inv
    # HC1
    meat = (X * (resid ** 2)).T @ X
    var_hc1 = (n / (n - k)) * (XtX_inv @ meat @ XtX_inv)
    se_c = np.sqrt(np.diag(var_classic))
    se_h = np.sqrt(np.diag(var_hc1))
    t_c = beta.ravel() / se_c
    t_h = beta.ravel() / se_h
    # Durbin-Watson
    e = resid.ravel()
    dw = float((np.diff(e) ** 2).sum() / (e ** 2).sum())
    return dict(names=names, beta=beta.ravel(), se_c=se_c, se_h=se_h,
                t_c=t_c, t_h=t_h, r2=r2, adj_r2=adj_r2, n=n, k=k, dw=dw,
                sigma=math.sqrt(sigma2), resid=e)

def stars(t):
    at = abs(t)
    return "***" if at > 3.29 else "**" if at > 2.58 else "*" if at > 1.96 else ""

def coef_table(res, show=("Hybrid_Centered", "Hybrid_Centered_Squared", "price", "const")):
    rows = []
    for i, nm in enumerate(res["names"]):
        if show is not None and nm not in show:
            continue
        rows.append({
            "变量": nm,
            "coef": res["beta"][i],
            "SE(classic)": res["se_c"][i],
            "t(classic)": res["t_c"][i],
            "SE(HC1)": res["se_h"][i],
            "t(HC1)": res["t_h"][i],
            "": stars(res["t_h"][i]),
        })
    return pd.DataFrame(rows)

def peak(mean_h, b1, b2):
    return mean_h + (-b1 / (2 * b2))

# ----------------------------------------------------------------------------
p("# 管线产物核查与主模型重估报告")
p("")
p(f"生成时间: {pd.Timestamp.now():%Y-%m-%d %H:%M:%S}")
p("")
p("数据来源：`games_clustered_meta_export.csv`（管线导出的事实表）。")
p("OLS 由 numpy 正规方程独立重估（无 statsmodels），同时给出经典标准误与 HC1 稳健标准误。")

# ============================ A. 总体审计 ==================================
df = pd.read_csv(DATA)
head("A. 事实表总体审计")
p(f"- 形状: **{df.shape[0]} 行 × {df.shape[1]} 列**")
p(f"- 列名: {list(df.columns)}")
p(f"- 重复 appid: **{int(df['appid'].duplicated().sum())}** 个")
p("")
d = df[["price", "Total_Reviews", "Hybridization_Index", "Log_Reviews",
        "Hybrid_Centered", "Hybrid_Centered_Squared"]].describe().T
d["median"] = df[["price", "Total_Reviews", "Hybridization_Index", "Log_Reviews",
                  "Hybrid_Centered", "Hybrid_Centered_Squared"]].median()
table(d.round(4))

p("")
p("### A1. 口径与门槛")
p(f"- 发行年份范围: {int(df.Release_Year.min())}–{int(df.Release_Year.max())}")
p(f"- `Total_Reviews` 最小值: {int(df.Total_Reviews.min())}（门槛 100 应为满足）")
p(f"- 杂交度 = 0 的样本: **{int((df.Hybridization_Index == 0).sum())}** 个")
p(f"- 杂交度 > 0 的样本: **{int((df.Hybridization_Index > 0).sum())}** 个（应等于回归 N）")
p(f"- `price` = 0 的样本: **{int((df.price == 0).sum())}** 个（{100*(df.price==0).mean():.2f}%）")
p(f"- `price` ≥ 100 的样本: **{int((df.price >= 100).sum())}** 个；最大价格 {df.price.max()}")
p(f"- `price` 上四分位以上极值: {np.round(np.percentile(df.price, [90,95,99,99.9]), 2).tolist()}")
p(f"- `in_focus_cluster` 取值: {sorted(df.in_focus_cluster.unique().tolist())}（恒为 1 说明该变量已退化）")

p("")
p("### A2. 恒等式校验")
mean_h = df.Hybridization_Index.mean()
p(f"- `Hybridization_Index` 全样本均值 = **{mean_h:.6f}**（notebook 打印 9.32）")
d1 = (df.Hybrid_Centered - (df.Hybridization_Index - mean_h)).abs()
d2 = (df.Hybrid_Centered_Squared - df.Hybrid_Centered ** 2).abs()
d3 = (df.Log_Reviews - np.log1p(df.Total_Reviews)).abs()
p(f"- |Hybrid_Centered − (H − mean)| 最大偏差 = {d1.max():.3e}（>1e-6 的行数: {int((d1>1e-6).sum())}）")
p(f"- |Hc² − Hc²| 最大偏差 = {d2.max():.3e}（>1e-6 的行数: {int((d2>1e-6).sum())}）")
p(f"- |Log_Reviews − ln(1+Total_Reviews)| 最大偏差 = {d3.max():.3e}（>1e-9 的行数: {int((d3>1e-9).sum())}）")
p(f"- |Total_Reviews − (positive+negative)| > 0 的行数: "
  f"{int(((df.Total_Reviews - df.positive - df.negative).abs() > 0).sum())}")

p("")
p("### A3. 相关矩阵（Pearson）")
cm = df[["price", "Hybridization_Index", "Log_Reviews", "Total_Reviews"]].corr().round(4)
table(cm, floatfmt="{:.4f}")

p("")
p("### A4. 分簇概况")
g = df.groupby("Game_Cluster").agg(
    N=("appid", "size"),
    share_pct=("appid", lambda s: 100 * len(s) / len(df)),
    mean_hybrid=("Hybridization_Index", "mean"),
    median_hybrid=("Hybridization_Index", "median"),
    min_hybrid=("Hybridization_Index", "min"),
    max_hybrid=("Hybridization_Index", "max"),
    mean_logrev=("Log_Reviews", "mean"),
    median_logrev=("Log_Reviews", "median"),
    mean_price=("price", "mean"),
    n_free=("price", lambda s: int((s == 0).sum())),
    mean_total_reviews=("Total_Reviews", "mean"),
).round(3)
table(g.reset_index(), floatfmt="{:.3f}")
p("")
p(f"- ΣN = {int(g.N.sum())}；Σshare = {g.share_pct.sum():.2f}%")

p("")
p("### A5. 发行年份分布与年份均值")
gy = df.groupby("Release_Year").agg(
    N=("appid", "size"),
    share_pct=("appid", lambda s: 100 * len(s) / len(df)),
    mean_logrev=("Log_Reviews", "mean"),
    mean_hybrid=("Hybridization_Index", "mean"),
    mean_price=("price", "mean"),
).round(3)
table(gy.reset_index(), floatfmt="{:.3f}")

# Meta tag vocabulary
head("A6. Meta_Tags 词表（漏网标签的直接证据）")
def split_meta(s):
    return [t.strip() for t in str(s).split(";") if t.strip()]
mt = df.Meta_Tags.apply(split_meta)
from collections import Counter
c = Counter(t for lst in mt for t in lst)
vocab = pd.DataFrame(sorted(c.items(), key=lambda kv: -kv[1]), columns=["meta_tag", "n_games"])
vocab["share_pct"] = (100 * vocab.n_games / len(df)).round(2)
p(f"- `Meta_Tags` 中出现的**不同元标签取值数 = {len(vocab)}**")
p(f"- 每款游戏元标签数（= 杂交度）: min {df.Hybridization_Index.min()}, "
  f"mean {df.Hybridization_Index.mean():.3f}, max {df.Hybridization_Index.max()}")
p("")
p("完整词表（按出现游戏数降序）：")
p("")
table(vocab, floatfmt="{:.2f}")

# Known META_DICT values (from notebook) to identify fall-through tags
DICT_VALUES = {
    'RPG','Shooter','Simulation','Roguelike','Strategy','Fighting/Brawler','Platformer',
    'Sports/Racing','Puzzle/Board','Adventure/Narrative','Core System','Sci-Fi/Cyberpunk',
    'Fantasy/Magic','Historical','Military/Combat','Other Themes','Story-Driven',
    'Mood (Positive)','Mood (Dark)','Perspective','Art Style','Action','Casual','Party',
    'Adult','Arcade/Top-Down Shooter',
}
fallthrough = vocab[~vocab.meta_tag.isin(DICT_VALUES)]
p("")
p(f"### A7. 兜底（未被 META_DICT 覆盖，原标签直接进入 Meta_Tags）的取值：**{len(fallthrough)} 个**")
p("")
table(fallthrough, floatfmt="{:.2f}")
p("")
p(f"- 这些兜底标签合计贡献 {(fallthrough.n_games.sum())} 次「元标签计数」")
tot = int(vocab.n_games.sum())
p(f"- 占全部元标签计数的 {100*fallthrough.n_games.sum()/tot:.2f}%（总计数 {tot}）")

# ============================ B. 小表核查 =================================
head("B. 小表核查")
cm_ref = pd.read_csv(ROOT / "01_data/processed/cluster_megatag_reference.csv")
p("### B1. cluster_megatag_reference.csv")
table(cm_ref)
p("")
p(f"- Σ n_games = **{int(cm_ref.n_games.sum())}**（应为 17686）")
p(f"- Σ share_pct = **{cm_ref.share_pct.sum():.2f}**")
p(f"- 与事实表分簇计数一致: "
  f"{bool((cm_ref.set_index('cluster_id').n_games.sort_index() == g.N.sort_index()).all())}")

coh = pd.read_csv(ROOT / "01_data/processed/cluster_cohens_h_tags.csv")
p("")
p("### B2. cluster_cohens_h_tags.csv")
table(coh, floatfmt="{:.4f}")
p("")
strong = coh[coh.cohens_h >= 0.5]
p("Cohen's h ≥ 0.5 的强定义标签：")
for cid, grp in strong.groupby("cluster_id"):
    p(f"- 簇 {cid}: " + ", ".join(f"{r.meta_tag} ({r.cohens_h:.2f})" for r in grp.itertuples()))

tags_txt = [l.strip() for l in (ROOT / "01_data/processed/all_tags.txt").read_text(encoding="utf-8").splitlines() if l.strip()]
p("")
p("### B3. all_tags.txt")
p(f"- 行数（非空）= **{len(tags_txt)}**，唯一值 = **{len(set(tags_txt))}**，"
  f"重复 = {len(tags_txt)-len(set(tags_txt))}")
missing = sorted(set(vocab.meta_tag) - set(tags_txt) - DICT_VALUES)
p(f"- `Meta_Tags` 词表中**不在** `all_tags.txt` 且不属于 META_DICT 类别的标签（{len(missing)} 个）：")
p(f"  {missing}")

# ============================ C. 主模型重估 ===============================
head("C. 主模型独立重估（numpy OLS）")
reg = df[df.Hybridization_Index > 0].dropna(
    subset=["Log_Reviews", "Hybrid_Centered", "Hybrid_Centered_Squared", "price"]).copy()
p(f"- 回归样本 N = **{len(reg)}**（事实表 {len(df)} 减去杂交度为 0 的 {len(df)-len(reg)} 个）")

yd = pd.get_dummies(reg.Release_Year, prefix="Y", drop_first=True).astype(float)
ycols = list(yd.columns)
X_main = np.column_stack([
    np.ones(len(reg)),
    reg.Hybrid_Centered.values,
    reg.Hybrid_Centered_Squared.values,
    reg.price.values,
    yd.values,
])
names = ["const", "Hybrid_Centered", "Hybrid_Centered_Squared", "price"] + ycols
res = ols(reg.Log_Reviews.values, X_main, names)
p("")
p(f"- N = {res['n']}, k = {res['k']}, R² = **{res['r2']:.4f}**, Adj. R² = {res['adj_r2']:.4f}, "
  f"Durbin-Watson = **{res['dw']:.3f}**, sigma = {res['sigma']:.4f}")
p("")
p("核心系数（经典标准误与 HC1 稳健标准误并列）：")
p("")
table(coef_table(res), floatfmt="{:.4f}")
b1, b2 = res["beta"][1], res["beta"][2]
pk = peak(mean_h, b1, b2)
p("")
p(f"- 拐点（原尺度） = {mean_h:.4f} + (−{b1:.5f}/(2×{b2:.5f})) = **{pk:.2f}**")

p("")
p("年份固定效应（HC1）：")
p("")
yr_rows = [{"年份": nm, "coef": res["beta"][i], "SE(HC1)": res["se_h"][i], "t(HC1)": res["t_h"][i]}
           for i, nm in enumerate(names) if nm.startswith("Y_")]
table(pd.DataFrame(yr_rows), floatfmt="{:.4f}")

# ---- cluster fixed effects version (the P0 improvement) ----
head("D. 追加：含题材簇固定效应的主模型（P0 改进预演）")
Xd = pd.get_dummies(reg.Game_Cluster, prefix="C", drop_first=True).astype(float)
X_cl = np.column_stack([
    np.ones(len(reg)),
    reg.Hybrid_Centered.values,
    reg.Hybrid_Centered_Squared.values,
    reg.price.values,
    yd.values,
    Xd.values,
])
res_cl = ols(reg.Log_Reviews.values, X_cl, ["const", "Hybrid_Centered", "Hybrid_Centered_Squared",
                                            "price"] + ycols + list(Xd.columns))
p(f"- N = {res_cl['n']}, R² = **{res_cl['r2']:.4f}**（主模型 {res['r2']:.4f}）")
p("")
table(coef_table(res_cl), floatfmt="{:.4f}")
b1c, b2c = res_cl["beta"][1], res_cl["beta"][2]
p("")
p(f"- 拐点 = **{peak(mean_h, b1c, b2c):.2f}**")

# ---- within-cluster estimates ----
p("")
p("### D1. 分簇单独估计倒 U（检验结论是否由题材构成驱动）")
rows = []
for cid, sub in reg.groupby("Game_Cluster"):
    if len(sub) < 300:
        continue
    ydd = pd.get_dummies(sub.Release_Year, prefix="Y", drop_first=True).astype(float)
    Xc = np.column_stack([np.ones(len(sub)), sub.Hybrid_Centered.values,
                          sub.Hybrid_Centered_Squared.values, sub.price.values, ydd.values])
    r = ols(sub.Log_Reviews.values, Xc, ["const", "Hybrid_Centered", "Hybrid_Centered_Squared", "price"] + list(ydd.columns))
    rows.append({
        "cluster": int(cid), "N": r["n"], "R2": r["r2"],
        "beta1": r["beta"][1], "t1(HC1)": r["t_h"][1],
        "beta2": r["beta"][2], "t2(HC1)": r["t_h"][2],
        "peak": peak(sub.Hybridization_Index.mean(), r["beta"][1], r["beta"][2]),
        "mean_hybrid": sub.Hybridization_Index.mean(),
    })
table(pd.DataFrame(rows).round(4), floatfmt="{:.4f}")

# ---- alternative functional forms ----
head("E. 追加：函数形式与稳健性对照")
p("### E1. 二次项 vs 分箱均值（无参数证据）")
bins = pd.cut(reg.Hybridization_Index, bins=[0, 4, 7, 10, 12, 14, 16, 25])
bt = reg.groupby(bins, observed=True).agg(N=("appid", "size"), mean_logrev=("Log_Reviews", "mean"),
                                          mean_hybrid=("Hybridization_Index", "mean")).round(3)
table(bt, floatfmt="{:.3f}")

p("")
p("### E2. 用好评率替代因变量（需求 vs 合法性）")
raw_cols = pd.read_csv(RAW, nrows=0).columns.tolist()
if "pct_pos_total" in raw_cols:
    raw = pd.read_csv(RAW, usecols=["appid", "pct_pos_total", "average_playtime_forever",
                                    "metacritic_score", "achievements", "dlc_count", "peak_ccu"])
    m = reg.merge(raw, on="appid", how="left")
    m2 = m.dropna(subset=["pct_pos_total"])
    yd2 = pd.get_dummies(m2.Release_Year, prefix="Y", drop_first=True).astype(float)
    Xp = np.column_stack([np.ones(len(m2)), m2.Hybrid_Centered.values, m2.Hybrid_Centered_Squared.values,
                          m2.price.values,
                          yd2.values])
    rp = ols(m2.pct_pos_total.values, Xp,
             ["const", "Hybrid_Centered", "Hybrid_Centered_Squared", "price"] + list(yd2.columns))
    p(f"- 因变量 = 好评率（%），N = {rp['n']}, R² = {rp['r2']:.4f}")
    p("")
    table(coef_table(rp, show=("Hybrid_Centered", "Hybrid_Centered_Squared", "price")), floatfmt="{:.4f}")
    p("")
    p("### E3. 加入质量/投入代理变量（缓解遗漏变量）")
    m3 = m.dropna(subset=["average_playtime_forever", "achievements", "dlc_count", "peak_ccu"]).copy()
    ctrl = np.column_stack([
        np.log1p(m3.average_playtime_forever.values),
        np.log1p(m3.achievements.values),
        np.log1p(m3.dlc_count.values),
        np.log1p(m3.peak_ccu.values),
    ])
    yd3 = pd.get_dummies(m3.Release_Year, prefix="Y", drop_first=True).astype(float)
    Xq = np.column_stack([np.ones(len(m3)), m3.Hybrid_Centered.values, m3.Hybrid_Centered_Squared.values,
                          m3.price.values,
                          yd3.values,
                          ctrl])
    # NOTE: name list must cover *every* column of Xq, otherwise the labels slide
    # onto the year dummies.  (Bug fixed during the quality-proxy audit.)
    rq = ols(m3.Log_Reviews.values, Xq,
             ["const", "Hybrid_Centered", "Hybrid_Centered_Squared", "price"]
             + list(yd3.columns)
             + ["ln_playtime", "ln_achievements", "ln_dlc", "ln_peak_ccu"])
    p(f"- N = {rq['n']}, R² = {rq['r2']:.4f}")
    p("")
    table(coef_table(rq, show=("Hybrid_Centered", "Hybrid_Centered_Squared", "price",
                               "ln_playtime", "ln_achievements", "ln_dlc", "ln_peak_ccu")), floatfmt="{:.4f}")
    p("")
    p(f"- 拐点 = **{peak(m3.Hybridization_Index.mean(), rq['beta'][1], rq['beta'][2]):.2f}**")
else:
    p("- 原始数据缺少 pct_pos_total 列，跳过。")

# ---- raw data shape reconciliation ----
head("F. 原始数据形状核对")
raw_shape = pd.read_csv(RAW, usecols=["appid", "genres", "categories", "tags_counts",
                                      "positive", "negative", "release_date", "estimated_owners"])
p(f"- 原始 CSV 读入行数 = **{len(raw_shape)}**，列数（全表）= {len(raw_cols)}")
d0 = raw_shape.copy()
d0["rd"] = pd.to_datetime(d0.release_date, errors="coerce")
d0["yr"] = d0.rd.dt.year
d0["tr"] = d0.positive + d0.negative
p(f"- 其中 `genres/categories/tags_counts` 任一为空的行数: "
  f"{int(d0[['genres','categories','tags_counts']].isna().any(axis=1).sum())}")
step = d0.dropna(subset=["genres", "categories", "tags_counts"])
p(f"- dropna 后行数 = **{len(step)}**（notebook 打印 88618）")
step = step[(step.yr >= 2015) & (step.yr <= 2025)]
p(f"- 年份过滤后 = {len(step)}")
step = step[step.tr >= 100]
p(f"- 评论数 ≥ 100 后 = {len(step)}（notebook 最终 17686，差异来自大厂剔除与 priority 过滤）")

# write report
OUT.write_text("\n".join(lines), encoding="utf-8")
print(f"\n[written] {OUT}")
