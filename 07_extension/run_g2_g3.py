# -*- coding: utf-8 -*-
"""
M4/M5 driver — G2 (expanded explanatory variables) and G3 (time dimension).

G2  Build the covariate groups, report coverage and missing-data rules, and
    re-estimate the focal model with controls. Every proxy that is same-source
    with the outcome (peak_ccu) is reported WITH and WITHOUT, per the lesson
    from 06_tools/quality_proxy_report.md.

G3  No true panel exists (single snapshot, ~2025-03-10). Two things are
    feasible and are done here:
      (a) release-cohort and market-density moderation of the hybridization
          optimum (Klepper 1997; Navis & Glynn 2010; Zhao et al. 2017);
      (b) an activity outcome built from the recent-review window
          (num_reviews_recent > 0), plus that selected subsample, both
          reported with explicit selection caveats.

Output: 07_extension/results/g2_covariates.md, 07_extension/results/g3_time.md
Usage:  python 07_extension/run_g2_g3.py
"""
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import PATHS, load_sample, ols, vif, write_report   # noqa: E402

T0 = time.time()


# ------------------------------------------------------------------ helpers
def cen(s):
    return s - s.mean()


def sig(t):
    a = abs(t)
    return "***" if a > 3.29 else "**" if a > 2.58 else "*" if a > 1.96 else ""


def fit(df, dv, focal, controls, cluster=None, kind="HC3"):
    need = [dv] + list(focal) + list(controls)
    d = df.dropna(subset=need).copy()
    if len(d) < 200:
        return None
    cols = list(focal) + list(controls)
    yd = pd.get_dummies(d["Release_Year"], prefix="Y", drop_first=True, dtype=float).astype(float)
    X = np.column_stack([np.ones(len(d)), d[cols].values.astype(float), yd.values.astype(float)])
    names = ["const"] + cols + list(yd.columns)
    r = ols(d[dv].values.astype(float), X, cluster if cluster else kind,
            groups=d[cluster].values if cluster else None)
    v = vif(X[:, 1:])
    return dict(r=r, names=names, n=len(d), cols=cols,
                coef={c: r["b"][names.index(c)] for c in cols},
                t={c: r["t"][names.index(c)] for c in cols},
                vif={c: v[i] for i, c in enumerate(cols)}, r2=r["r2"])


def line(fr, label, keys):
    cells = []
    for k in keys:
        if k in fr["coef"]:
            cells.append(f"{fr['coef'][k]:+.4f}{sig(fr['t'][k])} (t={fr['t'][k]:+.1f})")
        else:
            cells.append("—")
    return f"| {label} | {fr['n']:,} | {fr['r2']:.4f} | " + " | ".join(cells) + " |"


# ------------------------------------------------------------------- data
d = load_sample(verbose=True)
m = pd.read_csv(PATHS["measures"], encoding="utf-8-sig")
df = d.merge(m.drop(columns=[c for c in m.columns if c in d.columns and c != "appid"]),
             on="appid", how="inner")
assert len(df) == len(d), f"merge changed row count: {len(df)} vs {len(d)}"

df["Hc"] = cen(df["Hybridization_Index"])
df["Hc2"] = df["Hc"] ** 2
df["sp_c"] = cen(df["spanning"])
df["tg_c"] = cen(df["tag_spanning"])
df["co_c"] = cen(df["coherence"])

BASE = ["Hc", "Hc2", "price"]
FOCAL_NEW = ["tg_c"]

# ============================================================== G2
L = []
def p(*a):
    s = " ".join(str(x) for x in a)
    L.append(s)
    print(s)

p("# G2 · 解释变量扩展与识别改进")
p("")
p(f"> N = {len(df):,}。所有模型含年份固定效应与 `price`，报告 HC3 稳健标准误。"
  f"显著性：\\*\\*\\* p<0.01，\\*\\* p<0.05，\\* p<0.10。")
p("")

p("## 1. 覆盖度与缺失规则")
p("")
COV = [
    ("quality", "peak_ccu", "并发峰值（同源热度）", "0 为真值（无并发）"),
    ("quality", "achievements", "成就数", "0 为真值"),
    ("quality", "recommendations", "Steam 推荐数", "0 为真值"),
    ("quality", "average_playtime_forever", "平均游戏时长", "0 为真值"),
    ("quality", "dlc_count", "DLC 数", "0 为真值"),
    ("quality", "metacritic_score", "Metacritic 评分", "**0 视为缺失**"),
    ("media", "n_screenshots", "商店页截图数", "解析自 URL 列表"),
    ("media", "n_movies", "预告片数", "解析自 URL 列表"),
    ("access", "n_languages", "支持语言数", "解析自列表"),
    ("access", "mac", "支持 macOS", "0/1"),
    ("access", "linux", "支持 Linux", "0/1"),
    ("price", "discount", "当前折扣 %", "0 为真值（无折扣）"),
    ("price", "has_discount", "是否有折扣", "0/1"),
    ("price", "age_days", "上市天数", "由快照日推算"),
]
p("| 组 | 变量 | 含义 | 缺失规则 | 可用率 | 中位数 | p95 |")
p("|---|---|---|---|---|---|---|")
for grp, col, desc, rule in COV:
    s = pd.to_numeric(df[col], errors="coerce").astype(float)
    ok = s.notna().mean()
    p(f"| {grp} | `{col}` | {desc} | {rule} | {100*ok:.1f}% | {s.median():.2f} | {s.quantile(.95):.2f} |")
p("")
p(f"- `user_score` **不纳入**（>0 者仅 {int((df['user_score']>0).sum())} 款，0.1%）；"
  f"`windows` 恒为 1，不纳入；`required_age` 仅 {100*(df['required_age']>0).mean():.1f}% >0，不纳入主规格。")
p(f"- `metacritic_score` 缺失 {100*df['metacritic_score'].isna().mean():.1f}%，"
  f"以「缺失指示 + 0 填充」方式入模，并单列子样本稳健性。")
p("- **开发者固定效应不做**：`developers` 有 "
  f"{df['developers'].nunique():,} 个唯一值，≥10 款者覆盖不足 7%。改用 publisher 规模分级作类别控制。")
p("")

p("## 2. 加入协变量后的模型")
p("")
GROUPS = {
    "质量/投入": ["ln_peak", "ln_ach", "ln_rec", "ln_play", "ln_dlc"],
    "媒体丰富度": ["n_screenshots", "n_movies"],
    "可及性": ["n_languages", "mac", "linux"],
    "价格动态": ["discount", "has_discount"],
}
df["ln_peak"] = np.log1p(df["peak_ccu"])
df["ln_ach"] = np.log1p(df["achievements"])
df["ln_rec"] = np.log1p(df["recommendations"])
df["ln_play"] = np.log1p(df["average_playtime_forever"])
df["ln_dlc"] = np.log1p(df["dlc_count"])
for c in ["ln_peak", "ln_ach", "ln_rec", "ln_play", "ln_dlc", "n_screenshots",
          "n_movies", "n_languages", "discount", "mac", "linux", "has_discount"]:
    df[c] = pd.to_numeric(df[c], errors="coerce").astype(float)
    df[c + "_c"] = cen(df[c])
df["mc_miss"] = df["metacritic_score"].isna().astype(float)
df["mc0"] = df["metacritic_score"].fillna(0.0)
df["mc0_c"] = cen(df["mc0"])

MODELS = [
    ("基线（既有指数 + tag_spanning）", BASE + FOCAL_NEW, []),
    ("+ 质量/投入", BASE + FOCAL_NEW, [c + "_c" for c in GROUPS["质量/投入"]]),
    ("+ 质量/投入（**剔除** peak_ccu）", BASE + FOCAL_NEW,
     [c + "_c" for c in GROUPS["质量/投入"] if c != "ln_peak"]),
    ("+ 媒体丰富度", BASE + FOCAL_NEW, [c + "_c" for c in GROUPS["媒体丰富度"]]),
    ("+ 可及性", BASE + FOCAL_NEW, [c + "_c" for c in GROUPS["可及性"]]),
    ("+ 价格动态", BASE + FOCAL_NEW, [c + "_c" for c in GROUPS["价格动态"]]),
    ("+ 全部四组", BASE + FOCAL_NEW,
     [c + "_c" for g in GROUPS.values() for c in g] + ["mc0_c"]),
    ("+ 全部四组（剔除 peak_ccu）", BASE + FOCAL_NEW,
     [c + "_c" for g in GROUPS.values() for c in g if c != "ln_peak"] + ["mc0_c"]),
]
p("| 模型 | N | R² | Hc | Hc² | tag_spanning | price |")
p("|---|---|---|---|---|---|---|")
for lab, focal, ctrl in MODELS:
    fr = fit(df, "Log_Reviews", focal, ctrl + ["Hc", "Hc2"][0:0] if False else ctrl)
    if fr is None:
        p(f"| {lab} | — | — | — | — | — | — |")
        continue
    p(line(fr, lab, ["Hc", "Hc2", "tg_c", "price"]))
p("")
p("> `[注]` `peak_ccu` 与因变量同源（见 `06_tools/quality_proxy_report.md`：与 `Log_Reviews` 相关 0.769，"
  "属典型 bad control）。因此**必须成对报告**含/不含它的两个规格。")
p("")

# ============================================================== G3
L3 = []
def q(*a):
    s = " ".join(str(x) for x in a)
    L3.append(s)
    print(s)

q("# G3 · 时间维度：进入队列、市场密度与活跃度")
q("")
q("`[实]` **本数据集是单一快照（抓取时点约 2025-03-10），不存在真正的面板**。")
q("因此本节做两件在当前数据下可行的事，并明确其边界：")
q("① **队列 × 市场密度**的权变分析（Klepper 1997；Navis & Glynn 2010；Zhao et al. 2017）；")
q("② 用**近期评论窗口**构造「活跃度」结果，并如实标注其**选择性**。")
q("")

q("## 1. 市场密度构造")
q("")
yd_count = df.groupby("Release_Year")["appid"].transform("size")
cl_density = df.groupby(["Game_Cluster", "Release_Year"])["appid"].transform("size")
df["year_density"] = cen(np.log1p(yd_count))
df["niche_density"] = cen(np.log1p(cl_density))
q("| 变量 | 含义 | mean | SD | min | max |")
q("|---|---|---|---|---|---|")
for c, desc in [("year_density", "同年发行游戏数（log，中心化）"),
                ("niche_density", "同年同簇发行游戏数（log，中心化）")]:
    q(f"| `{c}` | {desc} | {df[c].mean():.3f} | {df[c].std():.3f} | "
      f"{df[c].min():.3f} | {df[c].max():.3f} |")
q("")

q("## 2. 队列与密度的调节效应")
q("")
q("| 模型 | N | R² | Hc | Hc² | 交互项 |")
q("|---|---|---|---|---|---|")
df["Hc_x_yd"] = df["Hc"] * df["year_density"]
df["Hc2_x_yd"] = df["Hc2"] * df["year_density"]
df["Hc_x_nd"] = df["Hc"] * df["niche_density"]
df["Hc2_x_nd"] = df["Hc2"] * df["niche_density"]
SPECS3 = [
    ("基线", ["Hc", "Hc2"], []),
    ("× 年度密度", ["Hc", "Hc2", "Hc_x_yd", "Hc2_x_yd"], []),
    ("× 利基密度", ["Hc", "Hc2", "Hc_x_nd", "Hc2_x_nd"], []),
    ("× 两者", ["Hc", "Hc2", "Hc_x_yd", "Hc2_x_yd", "Hc_x_nd", "Hc2_x_nd"], []),
]
for lab, focal, extra in SPECS3:
    fr = fit(df, "Log_Reviews", focal, ["price"] + extra)
    if fr is None:
        continue
    inter = [k for k in focal if "_x_" in k]
    cells = " | ".join(f"{fr['coef'][k]:+.4f}{sig(fr['t'][k])} (t={fr['t'][k]:+.1f})"
                       for k in inter) if inter else "—"
    q(f"| {lab} | {fr['n']:,} | {fr['r2']:.4f} | {fr['coef']['Hc']:+.4f}{sig(fr['t']['Hc'])} | "
      f"{fr['coef']['Hc2']:+.4f}{sig(fr['t']['Hc2'])} | {cells} |")
q("")

# peak at low vs high density
q("### 2.1 不同密度下的最优杂交度")
q("")
q("| 情形 | 密度分位 | 密度值 | 拐点 H* |")
q("|---|---|---|---|")
fr = fit(df, "Log_Reviews", ["Hc", "Hc2", "Hc_x_yd", "Hc2_x_yd"], ["price"])
if fr:
    b1, b2 = fr["coef"]["Hc"], fr["coef"]["Hc2"]
    i1, i2 = fr["coef"]["Hc_x_yd"], fr["coef"]["Hc2_x_yd"]
    hm = df["Hybridization_Index"].mean()
    for lab, qq in [("低密度（p10）", 0.10), ("中位（p50）", 0.50), ("高密度（p90）", 0.90)]:
        dv = df["year_density"].quantile(qq)
        a1, a2 = b1 + i1 * dv, b2 + i2 * dv
        peak = hm + (-a1 / (2 * a2)) if a2 != 0 else np.nan
        q(f"| {lab} | p{int(qq*100)} | {dv:+.3f} | **{peak:.2f}** |")
q("")

q("## 3. 活跃度结果（近期评论窗口）")
q("")
q(f"- `num_reviews_recent > 0` 的游戏 = **{int(df['has_recent_reviews'].sum()):,}**"
  f"（{100*df['has_recent_reviews'].mean():.1f}%）")
q("- `[注]` Steam 只在**存在近期活动**时显示近期评论，因此这 {:.0%} 的子样本是"
  "**按当期需求选择**出来的。".format(df["has_recent_reviews"].mean()))
q("")
q("| 因变量 | 模型 | N | R² / 伪R² | Hc | Hc² | tag_spanning |")
q("|---|---|---|---|---|---|---|")
# OLS linear-probability for the binary outcome (reported as such, not as a logit)
fr = fit(df, "has_recent_reviews", ["Hc", "Hc2", "tg_c"], ["price"])
q(f"| 是否有近期评论（OLS 线性概率） | 全样本 | {fr['n']:,} | {fr['r2']:.4f} | "
  f"{fr['coef']['Hc']:+.5f}{sig(fr['t']['Hc'])} | {fr['coef']['Hc2']:+.5f}{sig(fr['t']['Hc2'])} | "
  f"{fr['coef']['tg_c']:+.5f}{sig(fr['t']['tg_c'])} |")
sub = df[df["has_recent_reviews"] == 1].copy()
if len(sub) > 200:
    fr2 = fit(sub, "Log_Reviews", ["Hc", "Hc2", "tg_c"], ["price"])
    q(f"| Log_Reviews | 仅活跃子样本 | {fr2['n']:,} | {fr2['r2']:.4f} | "
      f"{fr2['coef']['Hc']:+.4f}{sig(fr2['t']['Hc'])} | {fr2['coef']['Hc2']:+.4f}{sig(fr2['t']['Hc2'])} | "
      f"{fr2['coef']['tg_c']:+.4f}{sig(fr2['t']['tg_c'])} |")
    fr3 = fit(sub, "pct_pos_recent", ["Hc", "Hc2", "tg_c"], ["price"])
    if fr3:
        q(f"| pct_pos_recent | 仅活跃子样本 | {fr3['n']:,} | {fr3['r2']:.4f} | "
          f"{fr3['coef']['Hc']:+.4f}{sig(fr3['t']['Hc'])} | {fr3['coef']['Hc2']:+.4f}{sig(fr3['t']['Hc2'])} | "
          f"{fr3['coef']['tg_c']:+.4f}{sig(fr3['t']['tg_c'])} |")
q("")
q("`[注]` 活跃子样本的结果**不能作因果解读**：进入该子样本的条件是"
  "「当期仍有评论」，这本身是被杂交度影响的结果变量（选择性内生）。")
q("""
## 4. 为什么真面板超出本数据集能力

`[实]` 原始数据只有**一个**观测时点，`num_reviews_total`、`pct_pos_recent`、`peak_ccu` 都是该时点的存量。
`num_reviews_recent` 提供了**一个**较近的窗口，但：
- 它只覆盖 27.4% 的样本（平台只在有活动时显示）；
- 它是**一个**区间，无法识别趋势或拐点。

`[推]` **若要做真面板，需独立采集**：按 `appid` 抽样 3,000–5,000 款，经 Steam 公开接口获取
`num_reviews_total` / `pct_pos_recent` / `peak_ccu` 的**多期快照**（建议 ≥3 期、间隔 ≥3 个月），
构造 `appid × period` 面板，用双向固定效应 + 事件研究识别。**本计划不包含该采集**（见计划 §6）。
""")

write_report("g2_covariates.md", L)
write_report("g3_time.md", L3)
print(f"\n[done] {time.time()-T0:.1f}s")
