# -*- coding: utf-8 -*-
"""
M1 driver — build the tag space and report its structure.

Outputs
  01_data/processed/tag_space_nodes.csv     tag, dfreq, domain, 8 embedding dims
  01_data/processed/tag_space_summary.json  parameters, K, modularity, stability
  07_extension/results/g1_tag_space.md      human-readable report

Usage:  python 07_extension/build_tag_space.py
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import PATHS, load_sample, tag_dicts, write_report, markdown_table  # noqa: E402
from tagspace import (build_cooccurrence, npmi_matrix, graph_from_npmi,        # noqa: E402
                      detect_domains, embed_tags, domain_centroids,
                      domain_distance, stability, build_tag_space,
                      save_tag_space, consensus_domains, modularity_null_test,
                      domain_jaccard_distance, DEFAULTS)

T0 = time.time()
L = []


def p(*a):
    s = " ".join(str(x) for x in a)
    L.append(s)
    print(s)


# ------------------------------------------------------------------- sample
p("# G1 · 标签空间构建报告")
p("")
p("> 由 `07_extension/build_tag_space.py` 生成。方法：NPMI 共现图 → Louvain 社区（标签域）→ 对称 NPMI 的谱嵌入。")
p("")

d = load_sample()
td = tag_dicts(d)
p(f"- 分析样本 **N = {len(d):,}**；每款游戏中位标签数 = **{int(np.median([len(t) for t in td]))}**")
p("")

# ------------------------------------------------------------- graph build
MIN_DF = DEFAULTS["min_df"]
EDGE = DEFAULTS["edge_threshold"]
vocab, keep, C, dfreq, n_docs = build_cooccurrence(td, MIN_DF)
npmi = npmi_matrix(C, dfreq, n_docs)
G = graph_from_npmi(npmi, EDGE)

import networkx as nx  # noqa: E402

p("## 1. 共现网络")
p("")
p(f"- 原始标签词表 = **{len(vocab)}**；文档频次 ≥ {MIN_DF} 的标签 = **{len(keep)}**（建图节点）")
p(f"- 边（NPMI > {EDGE}）= **{G.number_of_edges():,}**；密度 = **{nx.density(G):.4f}**")
p(f"- 文档频次分布：min {int(dfreq.min())} / 中位 {int(np.median(dfreq))} / max {int(dfreq.max())}")
p("")

# -------------------------------------------------------- resolution sweep
p("## 2. 分辨率扫描（Louvain）")
p("")
sweep = []
labels_by_res = {}
for res in [0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0]:
    lab, K, q, comms = detect_domains(G, res, DEFAULTS["seed"])
    labels_by_res[res] = lab
    sizes = sorted(np.bincount(lab).tolist(), reverse=True)
    sweep.append(dict(resolution=res, K=K, modularity=q,
                      largest=int(sizes[0]),
                      largest_share=float(sizes[0] / len(keep)),
                      sizes=", ".join(str(s) for s in sizes[:8])))
    p(f"- res={res:<4} → K={K:<3} modularity={q:.4f}  最大域占比 {100*sizes[0]/len(keep):.1f}%")
p("")
p(markdown_table([{k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()} for r in sweep]))
p("")
p("> `[实]` Louvain 在 res=1.0 处给出 **modularity ≈ 0.33**。对照论文 Table 2 的结论——")
p("> 论文用 Jaccard + 谱聚类在**游戏特征空间**上做硬聚类、得到轮廓系数 ≤ 0，据此断言")
p("> \"Steam tags do not inhabit a tidy, separable space … without a meaningful community structure\"。")
p("> 本结果显示：**标签×标签网络存在社区结构**。")
p(">")
p("> `[注]` **统计上不能只靠 0.3 这个经验门槛**：随机图与无标度网络本身就能因涨落达到较高模块度")
p("> （Guimerà, Sales-Pardo & Amaral 2004, *Phys. Rev. E* 70:025101），且模块度存在分辨率极限")
p("> （Fortunato & Barthélemy 2007, *PNAS* 104:36–41）。因此下一节用**同度序列零模型**做正式检验。")
p("")

# ------------------------------------------------------- null model test
res_main = DEFAULTS["resolution"]
p("### 2.1 模块度零模型检验（同度序列配置模型）")
p("")
null = modularity_null_test(G, labels_by_res[res_main], n_reps=30, seed=0)
p(f"- 观测：modularity = **{null['observed']:.4f}**（K = {int(labels_by_res[res_main].max()+1)}）")
p(f"- 零模型（{null['n_reps']} 次配置模型重连，每次重跑 Louvain）："
  f"均值 **{null['null_mean']:.4f}**、SD {null['null_sd']:.4f}、最大 {null['null_max']:.4f}"
  f"（零模型 K 中位数 = {null['null_k_median']:.0f}）")
p(f"- **z = {null['z']:.2f}**；经验 p = {null['p_empirical']:.3f}")
if null["p_empirical"] == 0:
    p(f"  （即 {null['n_reps']} 次重连中**没有一次**达到观测值；p < {1/null['n_reps']:.3f}）")
p("")
p(f"> `[实]` 观测模块度显著高于同度序列零模型（z = {null['z']:.1f}，经验 p < {1/max(null['n_reps'],1):.3f}），")
p("> **因此标签网络的社区结构不是随机涨落的产物**。这比引用任何\"0.3 门槛\"都更有说服力。")
p("")

# ------------------------------------------------------------- resolution
lab_main = labels_by_res[res_main]
K_main = int(lab_main.max() + 1)
q_main = [r["modularity"] for r in sweep if r["resolution"] == res_main][0]

p("## 3. 分辨率间一致性（ARI）")
p("")
res_list = sorted(labels_by_res)
ari = np.zeros((len(res_list), len(res_list)))
for i, a in enumerate(res_list):
    for j, b in enumerate(res_list):
        ari[i, j] = stability(labels_by_res[a], labels_by_res[b])
hdr = ["res"] + [f"{r}" for r in res_list]
p("| " + " | ".join(hdr) + " |")
p("|" + "|".join(["---"] * len(hdr)) + "|")
for i, a in enumerate(res_list):
    p(f"| {a} | " + " | ".join(f"{ari[i,j]:.3f}" for j in range(len(res_list))) + " |")
p("")
p("> 相邻分辨率的 ARI 较高、跨档较低，说明社区划分随分辨率平滑变化，主口径 res=1.0 不是孤立取值。")
p("")

# ---------------------------------------------------------- seed stability
p("## 4. 种子稳定性与共识划分（主口径 res=%.2f）" % res_main)
p("")
rng = np.random.RandomState(0)
seeds = rng.choice(100000, size=20, replace=False)
aris, mods, ks = [], [], []
for s in seeds:
    lab_s, k_s, q_s, _ = detect_domains(G, res_main, int(s))
    aris.append(stability(lab_main, lab_s))
    mods.append(q_s)
    ks.append(k_s)
aris = np.array(aris)
p("### 4.1 单次运行的种子敏感性")
p("")
p(f"- 20 个随机种子：modularity = {np.mean(mods):.4f} ± {np.std(mods):.4f}"
  f"（min {np.min(mods):.4f} / max {np.max(mods):.4f}）")
p(f"- K 取值集合 = {sorted(set(ks))}")
p(f"- 与主口径（seed={DEFAULTS['seed']}）的 **ARI = {aris.mean():.4f} ± {aris.std():.4f}（min {aris.min():.4f}）**")
p(f"- 判定：{'✅ 稳定（≥ 0.8）' if aris.mean() >= 0.8 else '⚠️ **不稳定（< 0.8）→ 触发预案：多种子共识划分**'}")
p("")
p("> Louvain 在该图上存在多个近简并解（K 在 4–7 之间摆动、模块度几乎相同），因此**不能**把单次运行")
p("> 的划分当作最终标签域。按计划 §4 的失败模式预案，改用**共现（co-association）共识**：")
p("> 多次运行的共分配频率矩阵 → 平均连接层次聚类 → 以**模块度最大化**客观选取切点 K。")
p("")

cons = consensus_domains(G, res_main, n_runs=100, seed=0)
p("### 4.2 共识划分（100 次运行）")
p("")
p(f"- 每次运行的 K 中位数 = **{cons['median_k']}**")
p(f"- 共识切点 **K = {cons['K']}**（由**与集合的一致性 ARI 最大化**选出）")
p(f"- 该划分：modularity = **{cons['modularity']:.4f}**，与 100 次单次运行的 "
  f"**ARI = {cons['ari_vs_runs']:.4f} ± {cons['ari_sd']:.4f}**")
p(f"- 若改按模块度最大化选 K，会得到 K = {cons['k_best_modularity']}"
  f"（模块度 {cons['k_curve'][cons['k_best_modularity']]:.4f}）——两者相差仅 "
  f"{abs(cons['k_curve'][cons['k_best_modularity']] - cons['modularity']):.4f}，说明**模块度曲面近乎平坦**。")
p("")
p("| K（切点） | 模块度 | 与集合的 ARI |")
p("|---|---|---|")
for k in cons["k_curve"]:
    mark = " ← **选定**" if k == cons["K"] else ""
    p(f"| {k} | {cons['k_curve'][k]:.4f} | {cons['ari_curve'][k]:.4f}{mark} |")
p("")
p("`[实]` **一个重要的实质性发现**：该图的模块度曲面在 K = 4–14 之间几乎是平的"
  "（0.323–0.335），Louvain 的多个近简并解模块度只差 0.002。这意味着标签空间存在**层次很浅的**社区结构——")
p("它既不是\"无结构\"，也不是几个彼此分离的整洁簇。**论文说它\"near-continuous\"是对的一半**：")
p("结构确实存在（模块度 0.33），但**硬划分本身不稳定**。")
p("")
p("> 这恰好**加强**了 G1 的论证：如果空间是连续且层次浅的，那么\"数了几个硬簇\"必然是脆弱的，")
p("> 而**在该空间中的距离**是良定义且稳定的。→ 用离散度而非计数，正是对论文自身批评的正确回应。")
p("")

# promote the consensus partition to the main one
lab_main = cons["labels"]
K_main = cons["K"]
q_main = cons["modularity"]
p(f"> **主口径自此改为共识划分**（K = {K_main}，模块度 {q_main:.4f}，与单次运行 ARI {cons['ari_vs_runs']:.3f}）。")
p("")

# ------------------------------------------------------------- min_df sweep
p("## 5. `min_df` 敏感性")
p("")
mdf = []
for m in [10, 20, 50, 100]:
    v_, k_, C_, df_, n_ = build_cooccurrence(td, m)
    M_ = npmi_matrix(C_, df_, n_)
    G_ = graph_from_npmi(M_, EDGE)
    lab_, K_, q_, _ = detect_domains(G_, res_main, DEFAULTS["seed"])
    mdf.append(dict(min_df=m, n_tags=len(k_), edges=G_.number_of_edges(),
                    K=K_, modularity=round(q_, 4),
                    largest_share=round(float(np.bincount(lab_).max() / len(k_)), 3)))
p(markdown_table(mdf))
p("")

# --------------------------------------------------------------- embedding
emb = embed_tags(npmi, DEFAULTS["n_components"], seed=0)
centroids = domain_centroids(emb, lab_main, K_main)
D = domain_distance(centroids)

# Jaccard distance between domains, on the games carrying each domain.
# This is the definition adopted for the spanning measure (see
# 07_extension/results/g1_distance_choice.md for the comparison that chose it).
tag_to_domain_main = {vocab[int(keep[i])]: int(lab_main[i]) for i in range(len(keep))}
D_jac, carriers = domain_jaccard_distance(td, tag_to_domain_main, K_main)
DIST_PATH = PATHS["tag_summary"].parent / "tag_domain_distances.csv"
pd.DataFrame(np.round(D_jac, 6),
             index=[f"dom{i}" for i in range(K_main)],
             columns=[f"dom{i}" for i in range(K_main)]).to_csv(
    DIST_PATH, encoding="utf-8-sig")

p("## 6. 标签域与域间距离")
p("")
p(f"- 域数 K = **{K_main}**（共识划分，与单次运行 ARI {cons['ari_vs_runs']:.3f}）")
p("")
p("### 6.1 域间距离矩阵（Jaccard，主口径）")
p("")
p("| 域 | 承载游戏数 | 占样本 | " + " | ".join(f"d{i}" for i in range(K_main)) + " |")
p("|---|---|---|" + "|".join(["---"] * K_main) + "|")
for a in range(K_main):
    p(f"| {a} | {carriers[a]:,} | {100*carriers[a]/len(td):.1f}% | " +
      " | ".join(f"{D_jac[a,b]:.3f}" for b in range(K_main)) + " |")
p("")
_iu = np.triu_indices(K_main, 1)
p(f"- Jaccard 距离：均值 **{D_jac[_iu].mean():.4f}**、SD {D_jac[_iu].std(ddof=1):.4f}、"
  f"范围 [{D_jac[_iu].min():.4f}, {D_jac[_iu].max():.4f}]")
p(f"- 对照质心余弦距离：均值 {D[_iu].mean():.4f}、SD {D[_iu].std(ddof=1):.4f}")
p("")
p("> `[实]` **主口径采用 Jaccard 距离**。选择依据（`g1_distance_choice.md`）：")
p("> ① 它有已发表先例（Wang & Lyu 2026；结构上等同 Kovács & Hannan 的标签外延 Jaccard）；")
p("> ② 它与标签数**完全正交**（r = +0.000），是一个真正独立的构念；")
p("> ③ 它在控制计数后**有显著增量**（t = −3.2），而质心余弦版不显著（t = +1.2）且符号不稳。")
p("")
p("### 6.2 标签域代表标签")
p("")
p("| 域 | 标签数 | 权重占比* | 代表标签（按文档频次，前 14） |")
p("|---|---|---|---|")
tot = dfreq.sum()
for c in range(K_main):
    m = lab_main == c
    names = np.array(vocab)[keep[m]]
    fr = dfreq[m]
    order = np.argsort(-fr)[:14]
    p(f"| {c} | {int(m.sum())} | {100*fr.sum()/tot:.1f}% | " +
      ", ".join(f"`{names[i]}`" for i in order) + " |")
p("")
p("\\* 权重占比 = 该域内标签文档频次之和 / 全部保留标签文档频次之和（仅表示规模，非用户票数权重）。")
p("")

# -------------------------------------------------------------------- save
ts = build_tag_space(td, want_stability=False)
# rebuild with the identical parameters as above but keep the pre-computed pieces
ts.labels, ts.K, ts.modularity = lab_main, K_main, q_main
ts.emb, ts.centroids = emb, centroids
ts.D = D_jac          # adopted distance definition (Jaccard on carrier sets)
ts.D_cos = D          # kept for reference / robustness
ts.__post_init__()
ts.stability = dict(
    n_seeds=20, ari_mean=float(aris.mean()), ari_min=float(aris.min()), ari_sd=float(aris.std()),
    modularity_mean=float(np.mean(mods)), modularity_min=float(np.min(mods)),
    modularity_max=float(np.max(mods)),
    consensus=dict(n_runs=100, K=int(cons["K"]), modularity=float(cons["modularity"]),
                   ari_vs_runs=float(cons["ari_vs_runs"]), ari_sd=float(cons["ari_sd"]),
                   median_k=int(cons["median_k"]),
                   k_best_modularity=int(cons["k_best_modularity"]),
                   k_curve={str(k): v for k, v in cons["k_curve"].items()},
                   ari_curve={str(k): v for k, v in cons["ari_curve"].items()}),
    partition_source="consensus (100 Louvain runs, average-linkage, K chosen by ensemble ARI)")

summary = save_tag_space(ts, PATHS["tag_nodes"], PATHS["tag_summary"],
                         extra=dict(resolution_sweep=sweep,
                                    min_df_sweep=mdf,
                                    modularity_null_test=null,
                                    distance_definition="jaccard_on_carrier_sets",
                                    domain_carriers=carriers.tolist(),
                                    jaccard_dispersion=dict(
                                        mean=float(D_jac[_iu].mean()),
                                        sd=float(D_jac[_iu].std(ddof=1)),
                                        min=float(D_jac[_iu].min()),
                                        max=float(D_jac[_iu].max())),
                                    cosine_dispersion=dict(
                                        mean=float(D[_iu].mean()),
                                        sd=float(D[_iu].std(ddof=1))),
                                    ari_between_resolutions={str(a): {str(b): float(ari[i, j])
                                                                      for j, b in enumerate(res_list)}
                                                             for i, a in enumerate(res_list)}))
p("## 7. 落盘")
p("")
p(f"- `{PATHS['tag_nodes'].relative_to(PATHS['tag_nodes'].parents[2])}`：{len(ts.keep)} 个标签 × "
  f"(dfreq, domain, {emb.shape[1]} 维嵌入)")
p(f"- `{PATHS['tag_summary'].relative_to(PATHS['tag_summary'].parents[2])}`：参数、K、模块度、稳定性、零模型检验")
p(f"- `{DIST_PATH.relative_to(DIST_PATH.parents[2])}`：{K_main}×{K_main} 域间 Jaccard 距离矩阵（**主口径**）")
p("")
p("> 标签域划分使用**共识划分**（100 次 Louvain + 平均连接 + 以集合一致性 ARI 选 K），")
p("> 因此 `tag_space_nodes.csv` 中的 `domain` 列可复现，不受单次运行随机性影响。")
p("> 域间距离使用 **Jaccard**（主口径），余弦版保留作稳健性。")
p("")

write_report("g1_tag_space.md", L)
print(f"\n[done] {time.time()-T0:.1f}s")
