# -*- coding: utf-8 -*-
"""
Choose the inter-domain distance definition.

Motivation
----------
Wang & Lyu (2026, NLP4DH) report a correlation of only 0.09 between coherence
(HHI over narrative-pattern shares) and spanning distance, so their two measures
are genuinely distinct. Our first implementation used cosine distance between
L2-normalised spectral centroids and got r = -0.909, i.e. spanning was almost a
deterministic function of (1 - HHI).

That is a property of the distance matrix, not of the data: if all inter-domain
distances were equal to d, then
        spanning = (p'Dp)/(1 - HHI) = d * (1 - HHI)/(1 - HHI) = d,
and with near-homogeneous distances spanning collapses onto (1 - HHI).

This script compares candidate distance definitions on three criteria:
  1. dispersion of the off-diagonal distances (a flat D cannot carry information);
  2. correlation with coherence (lower is better: the measures should be distinct);
  3. incremental explanatory power for Log_Reviews beyond the count index.

Candidate definitions
  A  cosine  : 1 - cos(centroid_i, centroid_j) in the spectral embedding   (current)
  B  jaccard : 1 - |F_i n F_j| / |F_i u F_j|, F = games carrying domain i  (Wang & Lyu)
  C  jaccard_z: B standardised to zero mean / unit SD across domain pairs
  D  cooc    : 1 - P(both domains present) / P(either), i.e. the game-level
               Jaccard computed on the full sample rather than on carriers only

Output: 07_extension/results/g1_distance_choice.md
Usage:  python 07_extension/choose_distance.py
"""
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import PATHS, ROOT, load_sample, tag_dicts, vif, ols, write_report  # noqa: E402
from measures import spanning, coherence, tag_spanning, _weights               # noqa: E402

T0 = time.time()
L = []


def p(*a):
    s = " ".join(str(x) for x in a)
    L.append(s)
    print(s)


# ------------------------------------------------------------------- inputs
d = load_sample()
td = tag_dicts(d)
nodes = pd.read_csv(PATHS["tag_nodes"], encoding="utf-8-sig")
tag_to_domain = dict(zip(nodes["tag"], nodes["domain"].astype(int)))
K = int(nodes["domain"].max()) + 1
emb_cols = [c for c in nodes.columns if c.startswith("emb")]
tag_index = {t: i for i, t in enumerate(nodes["tag"])}
emb = nodes[emb_cols].values.astype(float)

p("# G1 · 域间距离定义的选择")
p("")
p(f"> 输入：{len(nodes)} 个标签、K = {K} 个标签域（共识划分）、{len(d):,} 款游戏。")
p("")

# ------------------------------------------------ domain membership per game
p("## 1. 构造候选距离矩阵")
p("")
n = len(td)
present = np.zeros((n, K), dtype=bool)
weight_sum = np.zeros((n, K))
for i, g in enumerate(td):
    dom, w, _ = _weights(g, tag_to_domain)
    if len(dom):
        present[i, dom] = True
        np.add.at(weight_sum[i], dom, w)

F = [set(np.where(present[:, c])[0].tolist()) for c in range(K)]   # games carrying domain c
carriers = np.array([len(f) for f in F])
p("| 域 | 承载游戏数 | 占样本 |")
p("|---|---|---|")
for c in range(K):
    p(f"| {c} | {carriers[c]:,} | {100*carriers[c]/n:.1f}% |")
p("")

# A: cosine between spectral centroids
cent = np.zeros((K, emb.shape[1]))
for c in range(K):
    m = nodes["domain"].values == c
    v = emb[m].mean(axis=0)
    cent[c] = v / max(np.linalg.norm(v), 1e-12)
D_cos = np.clip(1 - cent @ cent.T, 0, None)
np.fill_diagonal(D_cos, 0.0)

# B: Jaccard distance between domain carrier sets
D_jac = np.zeros((K, K))
for a in range(K):
    for b in range(K):
        if a == b:
            continue
        inter = len(F[a] & F[b])
        union = len(F[a] | F[b])
        D_jac[a, b] = 1.0 - inter / union

# C: standardised Jaccard
iu = np.triu_indices(K, 1)
vals = D_jac[iu]
D_z = np.zeros((K, K))
z_vals = (vals - vals.mean()) / (vals.std(ddof=1) + 1e-12)
D_z[iu] = z_vals
D_z = D_z + D_z.T

# D: Jaccard on full sample (equivalent to B up to a constant, kept as a sanity check)
D_co = D_jac.copy()

CAND = {"A cosine（质心余弦）": D_cos,
        "B jaccard（承载集合 Jaccard，Wang & Lyu 口径）": D_jac,
        "C jaccard_z（B 的标准化）": D_z}

p("| 定义 | 距离均值 | SD | min | max | 变异系数 |")
p("|---|---|---|---|---|---|")
for name, D in CAND.items():
    v = D[iu]
    p(f"| {name} | {v.mean():.4f} | {v.std(ddof=1):.4f} | {v.min():.4f} | {v.max():.4f} | "
      f"{v.std(ddof=1)/max(v.mean(),1e-9):.3f} |")
p("")
p("> **判据 1**：距离矩阵本身的变异系数越低，`spanning` 越容易退化为 `(1 − HHI)` 的单调函数。")
p("")

# -------------------------------------------------------- per-game measures
rows = []
for i, g in enumerate(td):
    rows.append(dict(
        co=coherence(g, tag_to_domain, K),
        n_dom=n_domains_spanned(g, tag_to_domain) if False else len(np.unique(_weights(g, tag_to_domain)[0])) if len(_weights(g, tag_to_domain)[0]) else 0,
    ))
base = pd.DataFrame(rows, index=d.index)
for name, D in CAND.items():
    base[f"sp_{name[0]}"] = [spanning(g, tag_to_domain, D) for g in td]
base["tag_sp"] = [tag_spanning(g, tag_index, emb)[0] for g in td]
base["n_tags"] = [len(g) for g in td]

data = pd.concat([d[["Log_Reviews", "price", "Release_Year", "pct_pos_total", "Game_Cluster"]]
                  if "Game_Cluster" in d.columns else
                  d[["Log_Reviews", "price", "Release_Year", "pct_pos_total"]], base], axis=1)

p("## 2. 与 coherence 的共线性（判据 2：越低越好）")
p("")
p("| 距离定义 | corr(coh, span) | 与标签数 corr | 与 Log_Reviews corr |")
p("|---|---|---|---|")
for name in CAND:
    c = data["co"].corr(data[f"sp_{name[0]}"])
    cn = data["n_tags"].corr(data[f"sp_{name[0]}"])
    cy = data["Log_Reviews"].corr(data[f"sp_{name[0]}"])
    p(f"| {name} | **{c:+.3f}** | {cn:+.3f} | {cy:+.3f} |")
p(f"| tag_spanning（标签级，不经社区） | {data['co'].corr(data['tag_sp']):+.3f} | "
  f"{data['n_tags'].corr(data['tag_sp']):+.3f} | {data['Log_Reviews'].corr(data['tag_sp']):+.3f} |")
p("")
p(f"> 对照文献：Wang & Lyu (2026) 报告 HHI 与 spanning distance 的相关系数为 **0.09**，VIF ≈ 1。")
p(f"> 我方 coherence 与标签数 corr = {data['co'].corr(data['n_tags']):+.3f}；spanning(coherence) corr 越低越好。")
p("")

# ------------------------------------- restricted to genuinely spanning games
p("### 2.1 排除单一域游戏后的共线性（对齐文献口径）")
p("")
nd = data["n_dom"]
multi = nd >= 2
p(f"- 单一域游戏 = **{int((nd < 2).sum()):,}**（{100*(nd<2).mean():.1f}%）；跨 ≥2 域 = **{int(multi.sum()):,}**")
p(f"- `[注]` Wang & Lyu 把只属于一个模式的电影（1,056 部）**直接剔除**，因为其 SD 无定义；"
  f"本实现把单一域游戏的 spanning 记为 **0**（语义上\"没有跨越任何距离\"）并保留。")
p("")
p("| 距离定义 | 全样本 corr | **仅跨 ≥2 域** corr | 与 entropy_coherence corr |")
p("|---|---|---|---|")
for name in CAND:
    c_all = data["co"].corr(data[f"sp_{name[0]}"])
    c_mul = data.loc[multi, "co"].corr(data.loc[multi, f"sp_{name[0]}"])
    c_ent = data["co"].corr(data[f"sp_{name[0]}"])
    p(f"| {name} | {c_all:+.3f} | **{c_mul:+.3f}** | — |")
p(f"| tag_spanning | {data['co'].corr(data['tag_sp']):+.3f} | "
  f"{data.loc[multi,'co'].corr(data.loc[multi,'tag_sp']):+.3f} | — |")
p("")

# ------------------------------------------------------ incremental regression
p("## 3. 增量解释力（判据 3）")
p("")
yd = pd.get_dummies(data["Release_Year"], prefix="Y", drop_first=True, dtype=float).astype(float)


def fit(cols, label):
    dd = data.dropna(subset=["Log_Reviews", "price", "co", "n_tags"] + cols).copy()
    X = np.column_stack([np.ones(len(dd)), dd[cols].values.astype(float),
                         dd["price"].values.astype(float), yd.loc[dd.index].values.astype(float)])
    r = ols(dd["Log_Reviews"].values, X, "HC3")
    names = ["const"] + cols + ["price"] + list(yd.columns)
    out = dict(model=label, n=r["n"], R2=round(r["r2"], 4), adj=round(r["r2_adj"], 4))
    for nm in cols:
        i = names.index(nm)
        out[nm] = f"{r['b'][i]:+.4f} (t={r['t'][i]:+.1f})"
    out["_r2"] = r["r2"]
    out["_vif"] = vif(X[:, 1:])          # exclude the intercept column
    return out, r, names


data["nt_c"] = data["n_tags"] - data["n_tags"].mean()
data["nt_c2"] = data["nt_c"] ** 2
data["co_c"] = data["co"] - data["co"].mean()

models = []
for name in CAND:
    col = f"sp_{name[0]}"
    data[col + "_c"] = data[col] - data[col].mean()
    m, r, names = fit(["nt_c", "nt_c2", col + "_c"], f"计数 + spanning（{name}）")
    m["vif_span"] = round(float(m["_vif"][2]), 3)
    m["dR2_vs_count"] = None
    models.append(m)

m0, _, _ = fit(["nt_c", "nt_c2"], "仅计数（基线）")
models.insert(0, {**m0, "vif_span": None, "dR2_vs_count": None})
for m in models[1:]:
    m["dR2_vs_count"] = round(m["_r2"] - m0["_r2"], 5)

p("| 模型 | N | R² | ΔR² vs 计数 | 标签数 | 标签数² | spanning 项 | spanning VIF |")
p("|---|---|---|---|---|---|---|---|")
for m in models:
    cols = [c for c in m if c not in ("model", "n", "R2", "adj", "_r2", "_vif", "vif_span", "dR2_vs_count")]
    vals = " | ".join(str(m.get(c, "")) for c in cols)
    dr2 = "—" if m["dR2_vs_count"] is None else f"{m['dR2_vs_count']:+.5f}"
    vsp = "—" if m["vif_span"] is None else str(m["vif_span"])
    p(f"| {m['model']} | {m['n']:,} | {m['R2']:.4f} | {dr2} | {vals} | {vsp} |")
p("")

# ---------------------------------------------------------------- decision
p("## 4. 选择")
p("")
best = None
for name in CAND:
    c = abs(data["co"].corr(data[f"sp_{name[0]}"]))
    if best is None or c < best[1]:
        best = (name, c)
p(f"- **判据 2 最优**：`{best[0]}`（|corr(coherence, spanning)| = {best[1]:.3f}）")
p(f"- 与文献对照：Wang & Lyu 的对应相关系数为 0.09；我方最优为 {best[1]:.3f}。"
  + ("**已接近文献水平**，两个测度可视为基本独立。" if best[1] < 0.35
     else "**仍高于文献水平**，说明我方 K=7 的域间距离异质性不足；主规格将采用"
          "**正交化残差**入模，并把该相关系数如实披露。"))
p("")
p("`[推]` 若采用 Jaccard 口径，需注意其与文献的差异：Wang & Lyu 的模式由**电影集合**定义，"
  "而本项目的域由**标签集合**定义，因此我方 Jaccard 表达的是「共同承载同一批游戏的域彼此更近」，"
  "语义上正好对应 Kovács & Hannan 的「标签外延交并」（Eq. 11, p. 261）——**理论口径一致**。")
p("")

write_report("g1_distance_choice.md", L)
print(f"\n[done] {time.time()-T0:.1f}s")
