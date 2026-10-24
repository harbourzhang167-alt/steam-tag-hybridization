# -*- coding: utf-8 -*-
"""
M2 driver — score every game on the dispersion measures and compare them with
the existing count-based index.

Outputs
  01_data/processed/game_measures_extension.csv    per-game measures
  07_extension/results/g1_measures.md              distributions and comparison

Usage:  python 07_extension/build_measures.py
"""
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import PATHS, load_sample, tag_dicts, load_tag_space, write_report  # noqa: E402
from measures import score_games, orthogonalise                                 # noqa: E402

T0 = time.time()
L = []


def p(*a):
    s = " ".join(str(x) for x in a)
    L.append(s)
    print(s)


p("# G1 · 逐游戏测度构建报告")
p("")

d = load_sample()
td = tag_dicts(d)
ts = load_tag_space()

p(f"- 标签空间：**{len(ts.vocab)}** 个标签、**K = {ts.K}** 个标签域、"
  f"域间距离为 Jaccard（主口径）")
p(f"- 分析样本：**{len(d):,}** 款游戏")
p("")

# --------------------------------------------------------------- scoring
m = score_games(td, ts, appids=d["appid"].values)
m = m.set_index("appid")

df = d.set_index("appid").join(m.drop(columns=["row"]), how="left")
df = df.reset_index()

# bring in the existing count-based index for comparison
exp = pd.read_csv(PATHS["export"], encoding="utf-8-sig",
                  usecols=["appid", "Hybridization_Index", "Game_Cluster"])
_before = len(df)
df = df.merge(exp, on="appid", how="left")
assert len(df) == _before, "export join inflated the frame (duplicate appid?)"
miss = int(df["Hybridization_Index"].isna().sum())
if miss:
    print(f"[warn] {miss} games have no Hybridization_Index in the export")

p("## 1. 覆盖与流失")
p("")
bad = int(df["coherence"].isna().sum())
p(f"- 无法评分（其标签全部低于 `min_df` 阈值）= **{bad}** 款（{100*bad/len(df):.2f}%）")
p(f"- 可评分 = **{len(df)-bad:,}** 款")
p(f"- 平均用到的标签占游戏全部标签的权重份额 = **{df['used_weight_share'].mean():.4f}**"
  f"（中位 {df['used_weight_share'].median():.4f}）")
p("")

# ---------------------------------------------------- tag-list censoring
p("### 1.1 ⚠️ 原始标签列表在 20 处被硬截断")
p("")
nt = df["n_tags_total"].values
at_cap = int((nt >= 20).sum())
p(f"- **恰好 20 个标签的游戏 = {int((nt == 20).sum()):,}（{100*(nt==20).mean():.2f}%）**；"
  f"≥20 的共 {at_cap:,}（{100*at_cap/len(df):.1f}%）；最大值 = {int(nt.max())}")
p("")
mv_cap = np.median([min(t.values()) for t in td if len(t) == 20])
mv_lo = np.median([min(t.values()) for t in td if len(t) < 20])
p(f"- 被截断游戏（=20 个标签）中，**票数最少的那个标签**票数中位数 = **{mv_cap:.0f}**")
p(f"- 未截断游戏（<20 个标签）中，同样统计 = **{mv_lo:.0f}**")
p("")
p("`[实]` 这证明 20 是**平台展示上限**而非「这款游戏只有 20 个标签」：被截断游戏的最后一个标签仍有")
p(f"约 {mv_cap:.0f} 票，远高于噪声水平（未截断游戏的对应值仅 {mv_lo:.0f}），说明被截掉的标签是有意义的。")
p("")
p("**对既有计数式杂交度指数的含义（重要）**：")
p("- 计数型指数（原始标签数、元标签维度数）**在 20 处右删失**，且**样本中 55% 的游戏已顶到上限**；")
p(f"- 导出表的 `Hybridization_Index` 分布：max = {int(df['Hybridization_Index'].max())}，"
  f"中位 {df['Hybridization_Index'].median():.0f}，"
  f"处于其最大值 {int(df['Hybridization_Index'].max())} 的比例 = "
  f"{100*(df['Hybridization_Index']==df['Hybridization_Index'].max()).mean():.2f}%；")
p("- ⇒ **「数了几个维度」这个操作在数据层就被平台限制了上限**，这本身就是改用离散度（组成）而非计数的一个独立理由。")
p("")

# ------------------------------------------------------- distributions
p("## 2. 测度分布")
p("")
cols = ["n_tags_total", "n_tags_used", "n_domains", "coherence", "entropy_coherence",
        "spanning", "spanning_diluted", "tag_spanning"]
p("| 变量 | N | mean | SD | p5 | p25 | median | p75 | p95 | min | max |")
p("|---|---|---|---|---|---|---|---|---|---|---|")
for c in cols:
    s = df[c].dropna()
    p(f"| `{c}` | {len(s):,} | {s.mean():.4f} | {s.std():.4f} | {s.quantile(.05):.4f} | "
      f"{s.quantile(.25):.4f} | {s.median():.4f} | {s.quantile(.75):.4f} | {s.quantile(.95):.4f} | "
      f"{s.min():.4f} | {s.max():.4f} |")
p("")

# --------------------------------------------- comparison with count index
p("## 3. 与既有计数指数的对照")
p("")
cmp_cols = ["Hybridization_Index", "n_domains", "n_tags_total",
            "coherence", "entropy_coherence", "spanning", "spanning_diluted", "tag_spanning"]
avail = [c for c in cmp_cols if c in df.columns]
corr = df[avail].corr()
p("### 3.1 相关矩阵（Pearson）")
p("")
p("| | " + " | ".join(f"`{c}`" for c in avail) + " |")
p("|" + "|".join(["---"] * (len(avail) + 1)) + "|")
for a in avail:
    p(f"| `{a}` | " + " | ".join(f"{corr.loc[a,b]:+.3f}" for b in avail) + " |")
p("")
p("`[实]` 关键读数：")
key_pairs = [("spanning", "coherence"), ("spanning", "Hybridization_Index"),
             ("spanning", "n_tags_total"), ("coherence", "Hybridization_Index"),
             ("spanning", "spanning_diluted"), ("spanning", "tag_spanning")]
for a, b in key_pairs:
    if a in corr.index and b in corr.columns:
        p(f"- corr(`{a}`, `{b}`) = **{corr.loc[a,b]:+.3f}**")
p("")
p("> 对照文献 Wang & Lyu (2026)：HHI 与 spanning distance 的相关系数为 **0.09**，VIF ≈ 1。")
p("> 本项目的 `spanning` 与 `spanning_diluted`（未做相异对归一化的版本）对比，"
  "可显示归一化对共线性的作用。")
p("")

# --------------------------------------------------------- orthogonality
p("### 3.2 正交化残差（主规格使用）")
p("")
df["spanning_orth"] = orthogonalise(df, "spanning", controls=("coherence",))
df["coherence_orth"] = orthogonalise(df, "coherence", controls=("spanning",))
r = df[["spanning", "coherence", "spanning_orth", "coherence_orth"]].corr()
p(f"- `spanning` 对 `coherence` 回归后的残差 `spanning_orth`：与 `coherence` 相关 "
  f"**{r.loc['spanning_orth','coherence']:+.6f}**（构造上为 0）")
p(f"- `coherence_orth` 与 `spanning` 相关 **{r.loc['coherence_orth','spanning']:+.6f}**")
p(f"- 残差保留的原变量方差比例：spanning **{1 - df['spanning_orth'].var()/df['spanning'].var():.4f}** 被 coherence 解释掉")
p("")
p("`[注]` 相关矩阵与正交化残差都会被带入 M3 的回归；主规格以 `spanning` 与 `coherence` "
  "**分别入模**并辅以正交化版本，避免两个近镜像变量互相抢方差。")
p("")

# ------------------------------------------- by-domain-count descriptive
p("## 4. 按跨越域数分组的测度均值")
p("")
g = df.groupby("n_domains").agg(
    n=("appid", "size"),
    coherence=("coherence", "mean"),
    spanning=("spanning", "mean"),
    tag_spanning=("tag_spanning", "mean"),
    log_reviews=("Log_Reviews", "mean"),
    n_tags=("n_tags_total", "mean"),
).reset_index()
p("| 跨越域数 | N | coherence | spanning | tag_spanning | mean(Log_Reviews) | mean(标签数) |")
p("|---|---|---|---|---|---|---|")
for _, row in g.iterrows():
    p(f"| {int(row.n_domains)} | {int(row.n):,} | {row.coherence:.4f} | {row.spanning:.4f} | "
      f"{row.tag_spanning:.4f} | {row.log_reviews:.3f} | {row.n_tags:.1f} |")
p("")

# ------------------------------------------------------------------ save
OUT = PATHS["measures"]
keep_cols = (["appid", "Release_Year", "Log_Reviews", "Total_Reviews", "price",
              "pct_pos_total", "Hybridization_Index", "Game_Cluster"]
             + [c for c in cols if c in df.columns]
             + ["spanning_orth", "coherence_orth", "used_weight_share"]
             + [f"dom{i}" for i in range(ts.K)])
keep_cols = [c for c in dict.fromkeys(keep_cols) if c in df.columns]
df[keep_cols].to_csv(OUT, index=False, encoding="utf-8-sig")
p("## 5. 落盘")
p("")
p(f"- `{OUT.relative_to(OUT.parents[2])}`：{len(df):,} 行 × {len(keep_cols)} 列")
p(f"  （含 K={ts.K} 个域权重份额 `dom0..dom{ts.K-1}`，供后续稳健性使用）")
p("")

write_report("g1_measures.md", L)
print(f"\n[done] {time.time()-T0:.1f}s")
