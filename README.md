<div align="center">

# Steam Tag Hybridization

**Measuring how *far apart* a game's genre tags sit 鈥?not just how many it has.**

A reproducible research codebase for quantifying "tag hybridization" in indie video games on Steam,
with a full reproducibility audit of an existing pipeline and a methodological extension that replaces
the count-based index with a **dispersion-based** one.

`Python 3.12` 路 `scikit-learn 1.9.0` 路 `statsmodels 0.14.6` 路 27 passing tests 路 17,686 games

</div>

---

## TL;DR 鈥?what this repo shows

| # | Finding | Evidence |
|---|---|---|
| 1 | **The Steam tag network *does* have community structure.** Modularity **0.3329** against a degree-preserving null of **0.0794 卤 0.0021** 鈫?**z = 118.5**, empirical *p* < 0.033. A prior claim that tags "have no meaningful community structure" is an artifact of testing the wrong object (game feature space) with the wrong statistic (silhouette on a hard partition). | [`results/g1_tag_space.md`](07_extension/results/g1_tag_space.md) |
| 2 | **But that structure is shallow and hard partitions are fragile.** The modularity surface is nearly flat over *K* = 4鈥?4 (0.323鈥?.335); single-run Louvain reaches only **ARI = 0.635** across seeds; consensus lifts it to 0.766 鈥?still short of 0.8. | [`results/g1_tag_space.md`](07_extension/results/g1_tag_space.md) |
| 3 | **Therefore the measure should live in a continuous space, not a partition.** A tag-level distance measure that *never uses the community partition* is **exactly invariant** to the resolution parameter, while the partition-dependent variant loses significance at higher resolution (*t*: 鈭?2.2 鈫?鈭?.4). | [`results/g1_resolution_robustness.md`](07_extension/results/g1_resolution_robustness.md) |
| 4 | **Counting is doubly compromised here.** **54.78%** of games carry *exactly* 20 tags, and the least-voted of those still has a median of **75 votes** 鈥?so 20 is a **platform display cap**, not a property of the game. | [`results/g1_measures.md`](07_extension/results/g1_measures.md) |
| 5 | **Coherence replicates the literature; spanning distance does not.** Concentration raises both attention (+1.17\*\*\*) and evaluation (+10.12\*\*\*), matching the film-market finding. Spanning distance **lowers both** (鈭?.51\*\*\*, 鈭?3.73\*\*\*) 鈥?a pure category-spanning penalty, consistent with meta-analytic conditions for *bounded* vocabularies with *third-party* attribution at the *product* level. | [`results/g1_models.md`](07_extension/results/g1_models.md) |

The full argument is written up as a standalone manuscript: **[`07_extension/METHOD_PAPER.md`](07_extension/METHOD_PAPER.md)**.

---

## Why distance rather than count

Category-spanning research holds that the penalty for crossing categories depends on **how far apart**
the spanned categories are, not on how many there are (Kov谩cs & Hannan 2015). A count also has a
practical defect on this data: the platform truncates each game's tag list at 20, so the count's
support is capped for the majority of the sample before any modelling begins.

The obstacle is that a prior co-occurrence route was abandoned after Jaccard + spectral clustering
returned silhouette 鈮?0. That test asks whether **games** separate into clean groups. It says nothing
about whether **tags** form communities. Re-posing the question on the correct object 鈥?the
tag 脳 tag co-occurrence graph 鈥?and testing it against a null model rather than a rule-of-thumb
threshold recovers clear structure.

But recovering structure is only half the story. Because that structure is shallow, any measure built
on a *hard* partition inherits its fragility. The robust move is to define the measure on a
**continuous embedding** and skip the partition entirely.

---

## Method at a glance

```
tags {tag: votes}
    鈹?    鈹溾攢 co-occurrence  C = M岬€M          (405 tags with document frequency 鈮?20)
    鈹溾攢 NPMI weighting                  (down-weights ubiquitous hub tags analytically,
    鈹?                                   so no node deletion is needed)
    鈹溾攢 Louvain 脳 100 鈫?consensus       (co-association + average linkage; K = 7)
    鈹溾攢 TruncatedSVD on NPMI            (8-dim tag embedding)
    鈹?    鈻?per game (priority weights w = votes / max(votes), normalised to p)
    coherence       危_c p_c虏                                  concentrated in few domains?
    spanning        (p岬€Dp) / (1 鈭?HHI)                        how far apart are the domains?
    tag_spanning    same, but D is tag-to-tag embedding distance
                    鈫?uses NO partition at all                 鈫?primary measure
    鈹?    鈻?OLS:  log(1 + reviews)  or  positive-review share
      ~ measure + count index (+ count虏) + price + release-year FE
      HC3 robust SEs; cluster-robust by KMeans cluster as a robustness check
```

Two measurement corrections turned out to matter and are documented as first-class results:

- **Distinct-pair normalisation.** Using `p岬€Dp` directly collapses onto `1 鈭?HHI` when inter-domain
  distances are homogeneous. Dividing by `1 鈭?HHI` cuts the correlation with coherence from
  **鈭?.785 to 鈭?.404**.
- **Jaccard, not centroid cosine.** The cosine variant is insignificant once the count is controlled
  (*t* = +1.2) and its sign is unstable; Jaccard on domain carrier sets is significant (*t* = 鈭?.2)
  and is **orthogonal to the tag count** (*r* = +0.000).

---

## Repository layout

```
01_data/processed/          derived tables only 鈥?the 436 MB raw scrape is NOT included
  games_clustered_meta_export.csv     17,686 脳 15  fact table
  game_measures_extension.csv         17,686 脳 26  dispersion measures
  tag_space_nodes.csv, tag_space_summary.json, tag_domain_distances.csv
  all_tags.txt, cluster_*.csv
02_pipeline/                main notebook + figures
06_tools/                   reproducibility-audit scripts and their reports
07_extension/               the dispersion study (library + drivers + results)
  METHOD_PAPER.md                    鈫?the manuscript
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
python 07_extension/build_tag_space.py      # 鈫?tag space + null-model test + consensus
python 07_extension/build_measures.py       # 鈫?per-game measures
python 07_extension/run_g1_models.py        # 鈫?main tests
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

The 436 MB raw Steam scrape (89,618 games 脳 48 columns) is **not redistributed here** 鈥?it is a
third-party public dataset. Place it at the path above to rebuild from source.

The **derived** tables in `01_data/processed/` (11.5 MB) *are* included, so every result in this repo
can be re-derived and every test can run without the raw file. They are derived features rather than
the original scrape; check the upstream dataset's licence before reusing them commercially.

## Reproducibility notes

- **The environment is pinned and checked.** `06_tools/check_environment.py` compares
  `requirements.txt` against what is installed and writes
  `01_data/processed/environment_fingerprint.json` (versions + SHA-256 of key artefacts).
- **Clustering is version-fragile 鈥?deliberately documented.** Re-running KMeans under a different
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
and see [`CITATION.cff`](CITATION.cff). The theoretical debts are to Kov谩cs & Hannan (2015) on
conceptual-space distance, Wang & Lyu (2026) on coherence/spanning-distance measurement,
Li & Zhang (2020) on Steam tag networks, and Ahn, Vergne & Sharkey (2026) on the conditions under
which spanning helps or hurts.

## Licence

Code: MIT (see [`LICENSE`](LICENSE)). Derived data and third-party material: see [`NOTICE`](NOTICE).

---

<details>
<summary><b>涓枃鎽樿</b></summary>

鏈粨搴撴妸"鏍囩鏉備氦搴?浠?*璁℃暟**锛堣法瓒婁簡鍑犱釜鍏冩爣绛剧淮搴︼級鏀逛负**绂绘暎搴?*锛堟墍璺ㄧ淮搴︽湁澶氳繙锛夛紝
骞堕檮涓€浠藉畬鏁寸殑鍙鐜版€у璁°€備笁椤规牳蹇冪粨璁猴細

1. **鏍囩缃戠粶纭疄鏈夌ぞ鍖虹粨鏋?*锛氭ā鍧楀害 0.3329锛屽鍚屽害搴忓垪闆舵ā鍨嬬殑 z = 118.5锛堢粡楠?p < 0.033锛夈€?   姝ゅ墠"鏍囩鏃犵ぞ鍖虹粨鏋?鐨勫垽鏂紝鏉ヨ嚜鐢ㄩ敊浜嗗璞★紙娓告垙鐗瑰緛绌洪棿锛変笌缁熻閲忥紙纭垝鍒嗙殑杞粨绯绘暟锛夈€?2. **浣嗗垝鍒嗗緢鑴嗗急**锛氭ā鍧楀害鏇查潰鍦?K = 4鈥?4 涔嬮棿杩戜箮骞冲潶锛屽崟娆?Louvain 璺ㄧ瀛?ARI 浠?0.635銆?   鍥犳**渚濊禆纭垝鍒嗙殑娴嬪害蹇呯劧鑴嗗急**锛堝煙绾ц法瓒婂湪鍒嗚鲸鐜囧崌楂樻椂澶卞幓鏄捐憲鎬э級锛?   鑰?*涓嶄緷璧栧垝鍒嗙殑鏍囩绾ц窛绂诲鍒嗚鲸鐜囧畬鍏ㄤ笉鍙?*銆?3. **瀹炴祴缁撴灉鏄函绫诲埆璺ㄨ秺鎯╃綒**锛氬唴鑱氬害鍚屾椂鎻愬崌鍏虫敞搴︿笌璇勪环锛?1.17銆?10.12锛夛紝
   **璺ㄨ秺璺濈涓ゅ鐨嗚礋**锛堚垝0.51銆佲垝13.73锛夛紝涓庣數褰卞競鍦?鎻愬崌璇勪环銆侀檷浣庡叧娉?鐨勫垎瑁傜粨鏋滀笉鍚屸€斺€?   杩欎笌鍏冨垎鏋愭寚鍑虹殑涓変釜鍔犻噸鎯╃綒鏉′欢锛堟湁鐣岃瘝琛?/ 绗笁鏂逛富寮?/ 浜у搧灞傛祴閲忥級涓€鑷淬€?
鍙﹀彂鐜颁竴涓嫭绔嬬殑娴嬮噺缂洪櫡锛?*54.78% 鐨勬父鎴忔伆濂?20 涓爣绛?*锛?0 鏄钩鍙扮殑灞曠ず涓婇檺鑰岄潪娓告垙灞炴€э紝
鍥犳璁℃暟鍨嬫寚鏁板湪鏁版嵁灞傚氨琚皝椤躲€?
瀹屾暣璁鸿瘉瑙?[`07_extension/METHOD_PAPER.md`](07_extension/METHOD_PAPER.md)銆?
</details>
