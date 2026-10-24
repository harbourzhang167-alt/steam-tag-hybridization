<div align="center">

# Steam Tag Hybridization

**Measuring how *far apart* a game's genre tags sit — not just how many it has.**

A reproducible research codebase for quantifying "tag hybridization" in indie video games on Steam,
with a full reproducibility audit of an existing pipeline and a methodological extension that replaces
the count-based index with a **dispersion-based** one.

`Python 3.12` · `scikit-learn 1.9.0` · `statsmodels 0.14.6` · 27 passing tests · 17,686 games

</div>

---

## TL;DR — what this repo shows

| # | Finding | Evidence |
|---|---|---|
| 1 | **The Steam tag network *does* have community structure.** Modularity **0.3329** against a degree-preserving null of **0.0794 ± 0.0021** → **z = 118.5**, empirical *p* < 0.033. A prior claim that tags "have no meaningful community structure" is an artifact of testing the wrong object (game feature space) with the wrong statistic (silhouette on a hard partition). | [`results/g1_tag_space.md`](07_extension/results/g1_tag_space.md) |
| 2 | **But that structure is shallow and hard partitions are fragile.** The modularity surface is nearly flat over *K* = 4–14 (0.323–0.335); single-run Louvain reaches only **ARI = 0.635** across seeds; consensus lifts it to 0.766 — still short of 0.8. | [`results/g1_tag_space.md`](07_extension/results/g1_tag_space.md) |
| 3 | **Therefore the measure should live in a continuous space, not a partition.** A tag-level distance measure that *never uses the community partition* is **exactly invariant** to the resolution parameter, while the partition-dependent variant loses significance at higher resolution (*t*: −12.2 → −1.4). | [`results/g1_resolution_robustness.md`](07_extension/results/g1_resolution_robustness.md) |
| 4 | **Counting is doubly compromised here.** **54.78%** of games carry *exactly* 20 tags, and the least-voted of those still has a median of **75 votes** — so 20 is a **platform display cap**, not a property of the game. | [`results/g1_measures.md`](07_extension/results/g1_measures.md) |
| 5 | **Coherence replicates the literature; spanning distance does not.** Concentration raises both attention (+1.17\*\*\*) and evaluation (+10.12\*\*\*), matching the film-market finding. Spanning distance **lowers both** (−0.51\*\*\*, −13.73\*\*\*) — a pure category-spanning penalty, consistent with meta-analytic conditions for *bounded* vocabularies with *third-party* attribution at the *product* level. | [`results/g1_models.md`](07_extension/results/g1_models.md) |

The full argument is written up as a standalone manuscript: **[`07_extension/METHOD_PAPER.md`](07_extension/METHOD_PAPER.md)**.

---

## Why distance rather than count

Category-spanning research holds that the penalty for crossing categories depends on **how far apart**
the spanned categories are, not on how many there are (Kovács & Hannan 2015). A count also has a
practical defect on this data: the platform truncates each game's tag list at 20, so the count's
support is capped for the majority of the sample before any modelling begins.

The obstacle is that a prior co-occurrence route was abandoned after Jaccard + spectral clustering
returned silhouette ≈ 0. That test asks whether **games** separate into clean groups. It says nothing
about whether **tags** form communities. Re-posing the question on the correct object — the
tag × tag co-occurrence graph — and testing it against a null model rather than a rule-of-thumb
threshold recovers clear structure.

But recovering structure is only half the story. Because that structure is shallow, any measure built
on a *hard* partition inherits its fragility. The robust move is to define the measure on a
**continuous embedding** and skip the partition entirely.

---

## Method at a glance

```
tags {tag: votes}
    │
    ├─ co-occurrence  C = MᵀM          (405 tags with document frequency ≥ 20)
    ├─ NPMI weighting                  (down-weights ubiquitous hub tags analytically,
    │                                    so no node deletion is needed)
    ├─ Louvain × 100 → consensus       (co-association + average linkage; K = 7)
    ├─ TruncatedSVD on NPMI            (8-dim tag embedding)
    │
    ▼
per game (priority weights w = votes / max(votes), normalised to p)
    coherence       Σ_c p_c²                                  concentrated in few domains?
    spanning        (pᵀDp) / (1 − HHI)                        how far apart are the domains?
    tag_spanning    same, but D is tag-to-tag embedding distance
                    → uses NO partition at all                 ← primary measure
    │
    ▼
OLS:  log(1 + reviews)  or  positive-review share
      ~ measure + count index (+ count²) + price + release-year FE
      HC3 robust SEs; cluster-robust by KMeans cluster as a robustness check
```

Two measurement corrections turned out to matter and are documented as first-class results:

- **Distinct-pair normalisation.** Using `pᵀDp` directly collapses onto `1 − HHI` when inter-domain
  distances are homogeneous. Dividing by `1 − HHI` cuts the correlation with coherence from
  **−0.785 to −0.404**.
- **Jaccard, not centroid cosine.** The cosine variant is insignificant once the count is controlled
  (*t* = +1.2) and its sign is unstable; Jaccard on domain carrier sets is significant (*t* = −3.2)
  and is **orthogonal to the tag count** (*r* = +0.000).

---

## Repository layout

```
01_data/processed/          derived tables only — the 436 MB raw scrape is NOT included
  games_clustered_meta_export.csv     17,686 × 15  fact table
  game_measures_extension.csv         17,686 × 26  dispersion measures
  tag_space_nodes.csv, tag_space_summary.json, tag_domain_distances.csv
  all_tags.txt, cluster_*.csv
02_pipeline/                main notebook + figures
06_tools/                   reproducibility-audit scripts and their reports
07_extension/               the dispersion study (library + drivers + results)
  METHOD_PAPER.md                    ← the manuscript
  common.py  tagspace.py  measures.py
  build_tag_space.py  choose_distance.py  build_measures.py
  run_g1_models.py  run_g1_resolution_robustness.py  run_g2_g3.py
  tests/                             27 tests (unit + integration)
  results/                           every number in this README lives here
reference_pipeline_and_paper.md   full pipeline reference: data lineage, every model,
                                  the audit of the original count-based index, and the
                                  list of conflicts resolved
requirements.txt            pinned environment
```

> **Source materials not redistributed.** `03_literature/` (the reference dissertation and its
> extracted text) and `08_ref_txt/` (20 third-party papers) are deliberately excluded. Documents in
> `06_tools/` and `reference_pipeline_and_paper.md` therefore cite those paths, which will not
> resolve in a fresh clone; the citations themselves remain valid.

## Quickstart

```bash
python -m venv .venv && . .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python 06_tools/check_environment.py             # verify the pinned environment
python 07_extension/tests/test_measures.py       # 17 unit tests
python 07_extension/tests/test_integration.py    # 10 acceptance tests
```

To rebuild the analysis artefacts from scratch:

```bash
python 07_extension/build_tag_space.py      # → tag space + null-model test + consensus
python 07_extension/build_measures.py       # → per-game measures
python 07_extension/run_g1_models.py        # → main tests
python 07_extension/run_g1_resolution_robustness.py
python 07_extension/run_g2_g3.py
```

Rebuilding from the **raw** scrape additionally requires the public Steam dataset placed at
`01_data/raw/steam_games_march2025_updated.csv` (see *Data* below), then:

```bash
python 06_tools/run_notebook.py             # executes the main notebook (~30 s)
```

---

## Data

The 436 MB raw Steam scrape (89,618 games × 48 columns) is **not redistributed here** — it is a
third-party public dataset. Place it at the path above to rebuild from source.

The **derived** tables in `01_data/processed/` (11.5 MB) *are* included, so every result in this repo
can be re-derived and every test can run without the raw file. They are derived features rather than
the original scrape; check the upstream dataset's licence before reusing them commercially.

## Reproducibility notes

- **The environment is pinned and checked.** `06_tools/check_environment.py` compares
  `requirements.txt` against what is installed and writes
  `01_data/processed/environment_fingerprint.json` (versions + SHA-256 of key artefacts).
- **Clustering is version-fragile — deliberately documented.** Re-running KMeans under a different
  scikit-learn changes the cluster assignment even with the same data, `random_state=42` and `K=8`.
  This was discovered by actually re-executing the pipeline, and is recorded as a defect rather than
  hidden. Nothing in this repo's conclusions depends on the cluster labels; they are descriptive only.
- **No absolute local paths, no credentials, no personal identifiers** are present in this tree.
- Every reported figure is produced by a script and written to `07_extension/results/`.

## Status

Complete: dispersion measures, stability/null-model diagnostics, measure triangulation, main tests on
two outcomes, resolution robustness, covariate expansion, cohort/density analysis, manuscript.

Not done (deliberately out of scope): a genuine multi-period panel (the data is a single snapshot;
collection protocol is documented in `results/g3_time.md`), developer fixed effects (coverage < 7%),
and node2vec / text-embedding alternatives.

## Citation

If you use this code, please cite the manuscript in [`07_extension/METHOD_PAPER.md`](07_extension/METHOD_PAPER.md)
and see [`CITATION.cff`](CITATION.cff). The theoretical debts are to Kovács & Hannan (2015) on
conceptual-space distance, Wang & Lyu (2026) on coherence/spanning-distance measurement,
Li & Zhang (2020) on Steam tag networks, and Ahn, Vergne & Sharkey (2026) on the conditions under
which spanning helps or hurts.

## Licence

Code: MIT (see [`LICENSE`](LICENSE)). Derived data and third-party material: see [`NOTICE`](NOTICE).

---

<details>
<summary><b>中文摘要</b></summary>

本仓库把「标签杂交度」从**计数**（跨越了几个元标签维度）改为**离散度**（所跨维度有多远），
并附一份完整的可复现性审计。三项核心结论：

1. **标签网络确实有社区结构**：模块度 0.3329，对同度序列零模型的 z = 118.5（经验 p < 0.033）。
   此前「标签无社区结构」的判断，来自用错了对象（游戏特征空间）与统计量（硬划分的轮廓系数）。
2. **但划分很脆弱**：模块度曲面在 K = 4–14 之间近乎平坦，单次 Louvain 跨种子 ARI 仅 0.635。
   因此**依赖硬划分的测度必然脆弱**（域级跨越在分辨率升高时失去显著性），
   而**不依赖划分的标签级距离对分辨率完全不变**。
3. **实测结果是纯类别跨越惩罚**：内聚度同时提升关注度与评价（+1.17、+10.12），
   **跨越距离两处皆负**（−0.51、−13.73），与电影市场「提升评价、降低关注」的分裂结果不同——
   这与元分析指出的三个加重惩罚条件（有界词表 / 第三方主张 / 产品层测量）一致。

另发现一个独立的测量缺陷：**54.78% 的游戏恰好 20 个标签**，20 是平台的展示上限而非游戏属性，
因此计数型指数在数据层就被封顶。

完整论证见 [`07_extension/METHOD_PAPER.md`](07_extension/METHOD_PAPER.md)。

</details>
