# Steam 独立游戏「标签杂交度 × 商业表现」研究：数据处理管线与论文对照参考文档

> **文件性质**：后续工作的参考源文本（reference source text）。用于写作、改稿、复现、答辩与二次开发时，一次性获得完整的「数据源 → 理论基础 → 处理依据与流程 → 结论意涵 → 改进方向」链条。
>
> **两条主线**
> 1. **管线线**：`02_pipeline/4dissertation_gamespace_clustering_new.ipynb` 与配套脚本的**实测**行为、数字与文件血缘。
> 2. **论文线**：`03_literature/` 下的学位论文 *Beyond More Is Better: Tag Hybridization, Pricing, and Commercial Performance in Indie Video Games on Steam*（33 页，Warwick WMG）——**已全文提取**（92,427 字符），逐节摘要见 `03_literature/paper_digest.md`。
>
> **证据等级标注**（全文通用）
> - `[实]` **实测**：直接由本工作区的代码运行或 CSV 计算得到（核查脚本见 `06_tools/`）。
> - `[文]` **论文**：取自论文 PDF 正文（已提取、可检索）。
> - `[推]` **推断**：由前述证据逻辑推导，未直接观测。
> - `[注]` **限制**：提取或复现上的已知局限。
>
> **核查环境说明** `[注]`：本会话的默认文件沙箱在创建工作区写权限时失败（`SetNamedSecurityInfoW failed (Win32 5)`），提权后可执行命令。全部 `[实]` 数字均由 `06_tools/` 下的三份核查脚本在提权模式下实际运行得到，报告落盘为 `06_tools/verify_report.md`、`coverage_report.md`、`aux_report.md`。

---

## 目录

| 章节 | 内容 | 主要用途 |
|---|---|---|
| §0 | 结论速览（TL;DR）与关键数字 | 30 秒建立全局印象 |
| §1 | 工作区资产、数据源与血缘 | 找文件、懂版本 |
| §2 | 理论基础与研究假设 | 写 Introduction / 文献综述 |
| §3 | 数据处理依据与流程（管线全解） | 复现、写 Methodology |
| §4 | 分析结果（模型、稳健性、补充检验） | 写 Results / 附录 |
| §5 | 论文侧要点与对照 | 写 Discussion、处理审稿风险 |
| §6 | 结论的意涵 | 理论/实践/方法学启示 |
| §7 | 效度威胁与改进路线图 | Limitations / Future work |
| §8 | 后续工作清单与操作手册 | 接手与执行 |
| 附录 A/B/C | 变量字典、目录结构、复现清单 | 附录与交接 |

---

## §0 结论速览（TL;DR）

1. **研究单位** `[实]`：Steam 上 2015–2025 年发行、总评论数 ≥ 100 的独立游戏（`appid` 为观测单位）。清洗后 **17,686 款**；剔除「杂交度 = 0」的 16 款后，主回归 **N = 17,670**。
2. **核心自变量** `[文]/[实]`：**标签杂交度（Hybridization Index）** = 一款游戏经元标签词典（META_DICT，依 VGMS 框架 + Li (2020) EFA 构建）降维、剔除「通用/非设计标签」后，**剩余的不同元标签维度数**（0–20）。
3. **核心因变量** `[文]/[实]`：`Log_Reviews = ln(1 + positive + negative)`，以总评论量作商业表现的代理（对数化处理极端右偏，原始均值/中位数 = 3,928.85 / 396）。
4. **主结论（倒 U 型）** `[实]/[文]`：年份固定效应模型下 `Hybrid_Centered = +0.0761 (HC3 t = 23.77, p<0.001)`、`Hybrid_Centered_Squared = −0.0145 (HC3 t = −21.29, p<0.001)`、`price = +0.0381 (HC3 t = 23.23, p<0.001)`、R² = 0.1623 ⇒ **倒 U 型**，反推最优杂交度 ≈ **11.93**（≈ 12 个元标签维度）。论文原文结论："commercial performance rises with hybridization increase, then deteriorates after further complexity"，并称其为 **over-hybridization penalty**。`[注]` 本项已按 C1–C5 修正重算，系数与论文 Table 5 的 HC3 口径**三个斜率标准误吻合到 4 位小数**。
5. **稳健性** `[实]`：无时间控制（峰值 11.33）、按天年龄控制（11.92）、价格调制（11.80）、priority 阈值序列（10.93→8.52，方向一致）——**符号与显著性在所有设定下稳定**。论文的对应表格为 Table 6–9。
6. **聚类的角色** `[文]/[实]`：KMeans（K=8）在元标签 priority 矩阵上把 17,686 款游戏分为 8 个子类型簇，用于**描述性画像**与附录对照（簇规模 1,341–3,185；定义标签由 Cohen's h 突显度给出）。论文把这一步定位为 RQ1（市场结构）的证据，并称其为 "Blue-Ocean Defining Tags"。**聚类目前未作为控制变量进入回归**——这是最大的结构性缺口（§7.1）。
7. **论文与管线的四处硬冲突**（写作前必须解决，详见 §5.4 与 §7.2）——`[实]` 经本轮量化后**只剩 ① 是真正的口径冲突**：
   - **① 标准误类型（唯一实质冲突）**：论文全程使用 **HC3 异方差稳健标准误**（BP LM=601.91、White LM=1,489.97，p<0.001），notebook 使用**经典标准误**、无任何稳健修正；
   - **② 杂交度均值（疑为论文报数问题，非口径差异）**：论文报 **10.35**，管线全量口径 **9.3247**、0.30 阈值口径 **8.06**。但 `[实]` 论文 Table 9 在 t=0.30 行自己报的 β₁ = +0.0761、β₂ = −0.0145、拐点 = 11.96，**在算术上要求均值 = 9.3359**；若均值真是 10.35，拐点应为 12.97。**论文的均值列与它自己的回归输出互相矛盾**，且七档全不成立（差值 +0.68 ～ +1.72）；
   - **③ 阈值稳健性表（水平差 1.0–2.3 个维度，方向一致）**：论文 Table 9 的 N（17,736→17,581）与 Index Mean（11.25→9.32）与管线可复现值（17,639→17,488；8.92→6.96）系统性不一致。但 `[实]` **论文 t=0.30 行与管线主模型逐位相同**（N 17,670、β₁ +0.0761、β₂ −0.0145、拐点 11.96、R² 0.1622）⇒ 论文的"0.30 阈值口径"就是管线的不加阈值口径；
   - **④ 是否施加 0.30 阈值（描述问题，非实现差异）**：论文把阈值写进索引定义，管线实现里杂交度走**全量标签路径**。但 `[实]` 该阈值在管线里**删除 0 行**（票数最高标签 priority 恒为 1.0），在论文里也**没有咬合**（③ 已证其 0.30 行 = 无阈值模型）⇒ **两边都没被阈值影响，只是各自的文字描述与实现不一致**。
8. **测量效度的最大风险** `[实]`：`Meta_Tags` 出现 **192 个不同取值**，其中 **166 个是未被 META_DICT 覆盖的原始标签**（占全部元标签计数的 **32.09%**）。**但已通过稳健性检验**：改用「仅字典口径」重估，倒 U 依然成立（β₁=+0.1516、β₂=−0.0165、峰值 **10.94**），说明结论不依赖兜底标签（§7.3）。
9. **论文未做、但工作区已补做的两个高价值检验** `[实]`：
   - 加入质量/投入代理（`ln playtime`、`ln achievements`、`ln dlc`、`ln peak_ccu`）后 **price 归零**（−0.0001, t=−0.13）、R² 由 0.1622 升至 **0.694**，二次项仍显著。**但进一步拆解显示这是"部分吸收"**：逐个加入时 price 依然显著（t=18.8–22.5），归零主要由与因变量同源的 `peak_ccu` 驱动（它单独贡献了 R² 增量的 96%）；剔除 `peak_ccu` 后 price 仍有 **+0.0210 (t=16.8)**、拐点回到 **11.96**（详见 §4.4e 与 `06_tools/quality_proxy_report.md`）；
   - 以**好评率**为第二因变量，同样呈倒 U（β₁=+0.805、β₂=−0.0866）⇒ 过度杂交同时关联**需求下降**与**评价合法性下降**。
10. **工程缺陷** `[实]`：notebook 的注释声称 TF-IDF 聚类但实现是 priority 矩阵 + KMeans（`TfidfVectorizer`/`silhouette_score` 为死导入）；`MIN_TAG_DOC_FREQ`、`FOCUS_CLUSTERS`（设为全部 8 簇 ⇒ `in_focus_cluster` 恒为 1）、`Game_Age`、`map_to_metatags()` 均为死参数/死变量；`META_DICT` 有 7 个从未在数据中出现的死键；原始数据中 `'Dystopian '`（1,050 款）与 `'Parody '`（583 款）带尾随空格绕过映射；所有回归结果只以控制台打印留存，**没有落盘的结果表**。
11. **研究扩展（`07_extension/`）** `[实]`：把杂交度从「维度计数」改为**标签空间离散度**后的三项主要结果——
   ① **标签网络确有社区结构**（Louvain 模块度 0.3327；同度序列零模型 0.0794 ± 0.0021，**z = 118.5**，经验 p < 0.033），
   参考论文用 Jaccard + 谱聚类否定该路线的结论属**对象与方法的双重错配**；
   ② **`coherence` 完全复现文献方向**（同时提升关注度 +1.14\*\*\* 与评价 +10.26\*\*\*）；
   ③ **`tag_spanning` 两处皆负**（关注度 −0.51\*\*\*、评价 −13.73\*\*\*），与电影市场的"hybrid vigor"相反，
   而这正是 Ahn et al. (2026) 元分析对**有界词表 / 第三方主张 / 产品层测量**三个条件的预测。
   详见 [`07_extension/results/consolidated.md`](07_extension/results/consolidated.md)。
12. **一个独立的测量缺陷** `[实]`：**54.78% 的游戏恰好有 20 个标签**（最大值 21），且被截断游戏中票数最少的标签
   票数中位数达 **75**（未截断游戏仅 9）⇒ Steam 标签列表在 **20 处硬截断**，
   计数型杂交度在数据层就被平台限制了上限——这是改用离散度而非计数的独立理由。

---

## §1 工作区资产、数据源与血缘

### 1.1 文件清单（按重要性／内容／使用频次）

- **T0 核心**：缺了无法复现结论，必须版本化与备份。
- **T1 支撑**：证据链的一部分（产出表、图、脚本）。
- **T2 参考**：文献与说明性材料。
- **T3 工具／归档**：核查脚本、一次性脚本、草稿。

| 级别 | 文件 | 内容 | 频次 | 说明 |
|---|---|---|---|---|
| T0 | `01_data/raw/steam_games_march2025_updated.csv` | 原始数据（**89,618 行 × 48 列**，文件 89,622 行含表头） | 每轮必读 | 唯一数据源，抓取时点约 2025-03-10 |
| T0 | `02_pipeline/4dissertation_gamespace_clustering_new.ipynb` | 主管线（清洗 → 元标签 → 聚类 → 变量 → OLS → 稳健性 → 导出 → 可视化）。**已应用 C1–C5 修正** | 每轮必跑 | 结论唯一来源；修正见 `06_tools/CHANGELOG_corrections.md` |
| T1 | `02_pipeline/results/corrected_tables.md` | **修正后的全部结果表**（Table 1/4/5/6–9 + 年份分布） | 高（写作用） | ✅ 论文写作时以此为准 |
| T1 | `02_pipeline/results/*.csv` | 6 个机读结果表（描述统计、主回归三标准误、稳健性、阈值序列、年份分布） | 高 | 可直接引用，勿转引论文原表 |
| T1 | `01_data/processed/games_clustered_meta_export.csv` | 游戏级富化导出（**17,686 行 × 15 列**） | 高 | 管线的"事实表"，下游分析基础 |
| T1 | `01_data/processed/cluster_megatag_reference.csv` | 簇 → 质心 Top5 标签 + 杂交度统计 | 中（附录/画图） | 8 行；`Σn = 17,686` ✅ |
| T1 | `01_data/processed/cluster_cohens_h_tags.csv` | 簇 × 元标签 的 Cohen's h 突显度明细 | 中（簇命名与解读） | 40 行 = 8×5 |
| T1 | `02_pipeline/figures/hybridization_curve.png` | 倒 U 型主图（N=17,670，中位数参考线 10.0） | 高（论文正文图） | 300 dpi |
| T1 | `02_pipeline/figures/dissertation_figures.png` | 双联图：倒 U + 簇 7 的 Cohen's h | 高（论文正文图） | 150 dpi |
| T1 | `01_data/processed/all_tags.txt` | 448 个唯一标签 | 中（字典维护） | ⚠️ 为**阈值路径**产物，≠ 主管线词表 |
| T1 | `04_language_extension/*.py` | 语言支持 × 商业表现的旁支分析（4 个迭代版本） | 低–中 | 无落盘输出，见 §4.6 |
| T1 | `07_extension/results/consolidated.md` | **研究扩展综合结论**：离散度杂交度、解释变量扩展、时间维度 | 高（延伸章节） | 见 §9 |
| T1 | `07_extension/METHOD_PAPER.md` | **独立方法学稿件**：从硬划分到连续距离的类别跨越测量 | 高（可独立投稿） | 见 §9.6 |
| T0 | `requirements.txt` + `01_data/processed/environment_fingerprint.json` | **固定环境**与版本指纹（含关键产物哈希） | 每轮必查 | **`scikit-learn` 版本关键**，见 §7.6 第 7 条 |
| T2 | `08_ref_txt/*.txt` | 用户提供的 20 篇文献全文提取文本 | 高（文献核实） | 含 Li & Zhang (2020)、Grelier 线、Zuckerman (1999) 等 |
| T1 | `03_literature/lit_review_extension.md` | 扩展研究的注释书目（含不确定性清单） | 高 | **未核实项不得写入结论** |
| T1 | `01_data/processed/game_measures_extension.csv` | 17,686 × 26：离散度测度 + 域份额 + 计数指数 | 高 | 扩展分析的事实表 |
| T2 | `03_literature/*.pdf` | 论文全文（33 页） | 高（写作对照） | 已全文提取 |
| T2 | `03_literature/paper_digest.md` | 论文逐节摘要 + 差异清单 | 高 | 17 条差异见其 §8 |
| T2 | `03_literature/paper_clean.txt` | 论文全文文本（92,427 字符；另有 `paper_text.txt` 109,816 字符作交叉比对） | 高（检索引文） | `[注]` 约 30 处词有字符替换残留 |
| T3 | `05_archive/inspect_raw.py` | 原始字段抽样体检 | 低（一次性） | 探索性 |
| T3 | `06_tools/*` | 核查脚本与报告 | 按需 | 见 §1.4 |

### 1.2 原始数据字段（48 列）

`[实]` 关键列及其角色：

| 字段 | 角色 | 备注 |
|---|---|---|
| `appid` | 主键 | 与 Steam 官方 ID 一致，可外部校验；导出表**无重复** |
| `name`、`release_date` | 标识 / 时间 | `release_date` 需 `to_datetime(errors="coerce")` |
| `price` | 控制变量 | 单位 USD；均值 11.60、中位数 9.59、范围 0–269.99 |
| `positive`、`negative` | 因变量原料 | `Total_Reviews = positive + negative` |
| `estimated_owners` | 筛选用（剔除大厂） | 区间字符串如 `"5000000-10000000"`，需字符串匹配 |
| `tags` | **标签来源（频率字典字符串）** | 形如 `{'RPG': 1000, 'Action': 500}`，核心 |
| `tags_counts` | `tags` 的计数版本 | 仅用于非空判断 |
| `extracted_tags` | **已弃用**的标签来源列 | 仍被 `USECOLS` 读入但不参与计算 |
| `genres`、`categories` | 题材/功能（筛选用） | `genres` 用于识别 "Indie" |
| `developers`、`publishers` | 潜在控制变量 | 旁支分析（§4.6）使用 |
| `supported_languages` | 旁支分析自变量 | 语言分组 A/B/C/D |
| `metacritic_score`、`recommendations`、`average_playtime_forever`、`achievements`、`dlc_count`、`peak_ccu`、`pct_pos_total` | 已读入/可取用但主模型未用 | **质量代理**，§4.4e 已用于补充检验（`metacritic_score` 仅读入、未进回归，因缺失严重） |
| `detailed_description`、`screenshots`、`movies` | 未使用 | 未纳入 `USECOLS` |

### 1.3 血缘（lineage）总览

```
01_data/raw/steam_games_march2025_updated.csv   (89,618 × 48)
        │
        ├──[无标签1] 读取 22 列 ──────────────────────────────┐
        │                                                     ▼
        │                        02_pipeline/....ipynb（主管线）
        │                        ├─ 清洗：年份∈[2015,2025]、Total_Reviews≥100、剔除 86 款非 Indie 大厂
        │                        ├─ priority≥0.3 标签降噪 → Clean_Priority_Tags → all_tags.txt（阈值路径）
        │                        ├─ META_DICT 降维（全量路径）→ Meta_Tags / Votes / Priority
        │                        ├─ KMeans(K=8) on priority matrix → Game_Cluster
        │                        ├─ 变量：Hybridization_Index、Log_Reviews、Hybrid_Centered(+²)
        │                        ├─ OLS 主模型 + 4 组稳健性
        │                        └─ 导出 ──┬── games_clustered_meta_export.csv   (17,686 × 15)
        │                                   ├── cluster_megatag_reference.csv    (8 行)
        │                                   ├── cluster_cohens_h_tags.csv        (40 行)
        │                                   ├── all_tags.txt                     (448 标签)
        │                                   ├── hybridization_curve.png
        │                                   └── dissertation_figures.png
        │
        ├──[无标签2] 语言旁支 ── 04_language_extension/*.py
        │                          （读事实表 + 原始语言列，仅控制台输出，无落盘）
        │
        └──[无标签3] 核查 ──── 06_tools/{verify_all,verify_coverage,verify_aux}.py
                                   → verify_report.md / coverage_report.md / aux_report.md
```

### 1.4 核查工具与已落盘报告

| 文件 | 作用 | 产出 |
|---|---|---|
| `06_tools/verify_all.py` | 事实表总体审计 + 用 numpy 重估全部 OLS（无 statsmodels 依赖），含 HC1 稳健标准误、簇固定效应版、分簇估计、分箱均值、好评率因变量、质量代理控制 | `verify_report.md` |
| `06_tools/verify_coverage.py` | 量化 META_DICT 覆盖度，并用「仅字典口径」重估倒 U | `coverage_report.md` |
| `06_tools/verify_aux.py` | 中心化分母核对、空白标签污染、字典死键、样本框算术、排序核对 | `aux_report.md` |
| `06_tools/check_quality_proxies.py` | 拆解 §4.4e 的质量代理回归：合并路径 / log1p 变换 / VIF / 逐个加入 ablation / 剔除同源 `peak_ccu` / 标准化合成指标 | `quality_proxy_report.md` |
| `06_tools/check_threshold_03.py` | 穷尽核查「管线中哪里用了 0.3 阈值」：字面量清单 / Step 1 逐级样本框 / 稳健 4 七档删除来源分解 / 主模型索引口径 | `threshold_03_report.md` |
| `06_tools/check_index_specs.py` | 量化词典与维度合并规则：IGNORE／兜底／strip 三开关 × 七档阈值矩阵、候选描述统计搜索、论文自身数字的算术一致性检验 | `index_spec_report.md` |
| `06_tools/check_paper_tables.py` | 论文全部描述性表格的自洽性审计：逐行对照 / 仿射不变性 / VIF 一致性 / 截距恒等式 / t=coef/SE / 簇规模 / 年份分母 | `paper_tables_report.md` |
| `06_tools/apply_notebook_fixes.py` | 把 C1–C5 修正应用到主管线 notebook（写入前自动备份；`--check` 试运行） | 就地修改 notebook |
| `06_tools/rebuild_results.py` | 修正后结果重建（HC3 + `strip()` + 固定样本阈值序列），不依赖 statsmodels/sklearn | `02_pipeline/results/*` |
| `06_tools/CHANGELOG_corrections.md` | **变更日志**：C1–C5 逐条改动、依据、数值影响、未做项与理由、回滚方式 | — |
| `06_tools/check_environment.py` | 环境核查：比对 `requirements.txt` 与实际安装版本，写版本指纹与产物哈希；不一致时 exit 1 | `01_data/processed/environment_fingerprint.json` |
| `06_tools/run_notebook.py` | 执行主管线 notebook（无需 nbconvert/nbclient：逐单元 `exec`、剥离魔法命令、Agg 后端） | 重写 `01_data/processed/*` 与图 |
| `06_tools/extract_paper.py` | 论文 PDF 文本提取（标准库：对象流展开 + 字体 CMap/Differences/嵌入字体表 + 位移文本修复） | `03_literature/paper_clean.txt`（92,427 字符） |
| `06_tools/audit_tool.html` | 零依赖浏览器端同类核查（文件不出本机） | 即时结果 |

---

## §2 理论基础与研究假设

### 2.1 概念链：游戏空间 → 标签 → 元标签 → 杂交度

`[文]` 论文与管线的概念链可概括为四步：

1. **游戏空间（game space）**：电子游戏不是同质商品，而由"玩法机制 × 类型 × 题材 × 视觉风格 × 氛围 × 节奏"等维度构成。Steam 的用户标签是该空间的**众包坐标**——论文强调它是"玩家感知并表达"的特征广度，而非开发者设计阶段实际融合的机制数。
2. **标签 → 元标签降维**：Steam 标签细碎且混杂（本数据全量 **452 个**不同标签）。论文采用 **VGMS（Windleharth et al., 2016）** 作为分类框架，把标签组织进正式元数据维度（mechanics、genre、theme、visual style、mood、pacing），并**沿用 Li (2020) 对 Steam 标签的探索性因子分析**，把高共现、相互依赖的标签折叠到同一潜在因子（"Macro-Categories"）。论文明确举例：`Sandbox`、`Building`、`Crafting`、`Survival` 常共同描述同一类游戏体验，"**this combination should not be treated as structural cross-genre innovation**"。
3. **杂交（hybridization）**：一款游戏同时具备多个元标签维度即发生类型/设计维度的杂交；**杂交度 = 去重后的维度计数**。
4. **商业表现**：以总评论数在对数尺度上代理累计用户规模（论文引 Kontus, 2021 说明销量不可得）。

`[文]` **被论文放弃的两条替代路径**（Table 2）与放弃理由，是理解"为何必须用词典"的关键：
- (i) 按标签 priority 得分分布做 KMeans；(ii) 按标签共现 Jaccard 相似度做谱聚类。
- 在 K = 5/8/10/12/15/16 下**轮廓系数全部 ≈ 0 或为负**（K=8 KMeans cosine 轮廓 = −0.108；谱聚类最大簇占 442 个标签中的 396 个 = 89.6%）。
- 论文结论："Steam tags do not inhabit a tidy, separable space. Instead, they form a heavily connected, near-continuous similarity continuum. **Without a meaningful community structure, the index could not yield a defensible construct.**"

### 2.2 "More Is Better" 与 "Beyond More Is Better" 的机制对立

`[文]` 两条竞争机制构成识别策略核心：

| 机制 | 理论依据 | 对杂交度的预期 | 传导路径 |
|---|---|---|---|
| **信息/信号（More is better）** | 信息不对称与信号传递（Akerlof, 1970；Choi et al., 2018） | 单调递增 | 更多标签 ⇒ 更多搜索入口与推荐曝光（Steam 算法）⇒ 匹配更多细分需求 |
| **最优区分 / 类别跨越（Beyond more is better）** | Optimal distinctiveness、category spanning（Zuckerman, 1999；Hsu et al., 2009）、认知负荷（Sweller, 1988）、GameFlow（Sweetser & Wyeth, 2005） | 倒 U 型 | 适度杂交提升区分度；过度杂交 ⇒ 类别身份模糊、认知负荷上升、评价合法性下降 ⇒ 边际收益递减直至转负 |
| **价格—质量信号** | Völckner & Hofmann (2007) 元分析 | 控制变量：正 | 高价需匹配质量预期；与杂交度可能交互 |

`[文]` 由此得到三条可检验含义（与论文 RQ 一一对应）：
- **RQ2 / H1（倒 U）**：杂交度与 Log_Reviews 呈凹形关系（线性项 > 0，二次项 < 0）。
- **RQ2 延伸（峰值位置）**：最优杂交度落在样本分布的中高区间，支撑"数量优势存在上限"的折中结论。
- **RQ3 / H3（价格调制）**：价格作为边界条件，同时影响**最优杂交水平**与**过度杂交的衰减速率**。

`[实]` 检验载体：主模型（§4.2）、峰值反推（§4.3）、稳健 3 交互模型（§4.3）、阈值序列（§4.3）。

### 2.3 与论文的对应关系

`[文]` 详见 `03_literature/paper_digest.md`。论文侧关键事实：

- 设计：**二手数据 + 定量 + 横截面**；数据来自公开 Steam 聚合数据集（Kaggle）。
- 三个 RQ 的原文表述、"central main-effect hypothesis" 的定位、以及"Frankenstein fallacy"的实践警示。
- 理论引用链：Akerlof (1970) 柠檬市场 → Choi et al. (2018) 游戏质量线索 → Zuckerman (1999)/Hsu et al. (2009) 类别跨越 → Völckner & Hofmann (2007) 价格—质量 → Windleharth et al. (2016)/Li (2020)/Li & Zhang (2020)/Grelier et al. (2023, 2025, 2026) Steam 标签方法学。

---

## §3 数据处理依据与流程（管线全解）

管线全局参数（notebook §0）：

| 参数 | 值 | 依据 |
|---|---|---|
| `DATA_PATH` | `01_data/raw/steam_games_march2025_updated.csv` | 本地快照，抓取时点约 2025-03-10 |
| `TAG_SOURCE_COL` | `extracted_tags` | **已弃用**（见 §3.4） |
| `YEAR_MIN, YEAR_MAX` | 2015, 2025 | 论文依据 Grelier et al. (2025)：行业微观趋势生命周期约 4 年，十年窗口覆盖多个完整周期，并提供足够的跨年变异 |
| `MIN_REVIEWS` | 100 | 论文依据 Grelier et al. (2026)：过滤 "asset flips" 与无商业意图的业余项目 |
| `N_CLUSTERS` | 8 | notebook 注释称依 Grelier 等方法；论文 Table 10 亦为 K=8 |
| `MIN_TAG_DOC_FREQ` | 0.001 | 声明用于过滤稀疏标签，**当前代码未使用** |
| `FOCUS_CLUSTERS` | `[0..7]` | 覆盖全部簇 ⇒ `in_focus_cluster` 恒为 1，**已退化** |

### 3.1 步骤 1｜加载与字段选择

`[实]` 只读入 22 列（`USECOLS`），避免把长文本描述载入内存；打印形状 `(89618, 22)`。
`[实]` 原始 CSV 实际数据行 **89,618**（全表 48 列），与打印一致。

### 3.2 步骤 2｜清洗与样本框（sample frame）

`[实]` 依序执行，并已**逐步核对**：

| 步骤 | 规则 | 剩余行数 |
|---|---|---|
| 0 | 载入 | **89,618** |
| 1 | `dropna(subset=["genres","categories","tags_counts"])` | **88,618**（剔除 1,000 行：任一为空） |
| 2 | 年份 ∈ [2015, 2025] | **85,884** |
| 3 | `Total_Reviews ≥ 100` | **17,772** |
| 4 | 剔除"非 Indie 且 `estimated_owners ≥ 5,000,000`" | **17,686**（剔除 **86** 款） |
| 5 | priority ≥ 0.3 后标签非空 | 17,686（无额外损失） |

`[实]` 派生变量：`Release_Year`、`Total_Reviews = positive + negative`、`Game_Age = 2025 − Release_Year`（主模型未用）。
`[实]` 写出 `all_tags.txt`：**448 个唯一标签**（阈值路径产物，无重复、无空行、已排序）。
`[实]` 保留率 19.7%（17,686 / 89,618）。

> **设计依据小结**：四道闸门分别对应**可观测性**（评论门槛）、**时间可比性**（年份区间 + 年份 FE）、**总体定义**（Indie / 非大厂）、**测量质量**（priority 降噪）。这正是外部效度（"独立游戏市场"这一目标总体）与内部效度（噪声控制）的权衡点。
> `[推]` 需注意：论文称"系统剔除知名 AAA 发行商"，而管线用"owner 区间 ≥ 5,000,000 且非 Indie"代理，**口径更宽**（86 款）。写作时应说明代理规则，或按论文口径补充发行商黑名单做敏感性分析。

### 3.3 步骤 3｜标签优先度解析（priority score）

`[实]` `parse_tags_counts_with_priority(x, t)` 的逻辑：

```
tag_dict  = literal_eval(tags)          # {'RPG': 1000, 'Action': 500, 'Funny': 10}
max_votes = max(tag_dict.values())      # 该游戏得票最高的标签票数
keep tag  ⇔  votes / max_votes ≥ t      # 相对优先度，而非绝对票数
```

`[文]` 论文对应表述：Priority Score "ranging from 0 to 1, which reflects the weight of a tag based on user votes and distinguishes the core tags (high priority) from marginal or sarcastic noise"；0.30 阈值 = "only tags [that] reached 30% of a game's maximum weight were retained"；**每个 Meta-Tag 维度继承其组内最大原始标签票数**。

`[推]` **为什么用相对优先度**：Steam 标签票数是跨游戏不可比的绝对量（热门游戏所有标签票数都高）。除以各自最大票数后得到"相对于该游戏最强标签的强度"，从而在**游戏内部**比较标签重要性，消除人气规模效应。

`[实]` 该函数在稳健性检验中被复用于阈值序列（0.15–0.45），是本管线**唯一被系统性做敏感性分析的参数**。

### 3.4 步骤 4｜元标签映射与"两条标签路径"的关键区别

`[实]` 管线中并存**两条**标签加工路径，二者**不等价**，是理解全部结果的前提：

| 路径 | 输入 | 阈值 | 产物 | 后续用途 |
|---|---|---|---|---|
| **A. 阈值路径** | `tags` 字典 | priority ≥ 0.3 | `Clean_Priority_Tags` | 仅写出 `all_tags.txt`、作为 Step 2 的非空过滤；**不进入杂交度**。`[实]` 该非空过滤**实际删除 0 行**（非约束性，理由见 §4.3） |
| **B. 全量路径** | `tags` 字典**全量** | **无阈值** | `Meta_Tags`、`Meta_Tags_Votes`、`Meta_Tags_Priority` | **聚类 + 杂交度 + Cohen's h** |

`[实]` `build_meta_fields()` 的规则：
```
for tag, votes in tag_dict.items():                 # 全量标签，不先砍 0.3
    mapped = META_DICT.get(tag, tag)                # 字典未覆盖 ⇒ 原标签直接保留
    if mapped == 'IGNORE': continue                 # 通用/非设计标签剔除
    meta_names.add(mapped)                          # 类别去重 ⇒ 杂交度的分子
    meta_votes[mapped] = max(meta_votes.get(mapped, 0), votes)   # 组内取 max
Meta_Tags_Priority = {k: v / max(meta_votes.values()) for k, v in meta_votes.items()}
```
`[推]` 三处设计意图与代价：
- **全量（保留长尾）**：避免阈值抹掉稀有但语义重要的标签；代价是杂交度上限抬高（实测 0–20，均值 9.32），且对噪声标签更敏感；
- **`max` 聚合**：同一类别下多个子标签只取最强票数，避免"同类多标签"虚增强度（与论文表述一致）；
- **`META_DICT.get(tag, tag)` 兜底**：未覆盖标签以**原样**进入元标签集合 ⇒ `Meta_Tags` 同时包含"类别"与"漏网原标签"两个语义层级。**这是杂交度测量最大的内部效度风险**（§7.3）。

`[实]` `META_DICT` 构造：按四大维度组织，映射目标共 **26 个去重取值**（25 个类别 + `IGNORE`）：
- 核心玩法与机制：`RPG`、`Shooter`、`Simulation`、`Roguelike`、`Strategy`、`Fighting/Brawler`、`Platformer`、`Sports/Racing`、`Puzzle/Board`、`Adventure/Narrative`、`Core System`
- 主题与设定：`Sci-Fi/Cyberpunk`、`Fantasy/Magic`、`Historical`、`Military/Combat`、`Other Themes`
- 叙事与情感（MDA 美学维度）：`Story-Driven`、`Mood (Positive)`、`Mood (Dark)`
- 视觉与视角：`Perspective`、`Art Style`
- 补丁类别：`Action`、`Casual`、`Party`、`Adult`、`Arcade/Top-Down Shooter`

`[实]` 字典键总数 **291**（含重复键），其中 **7 个键在原始数据中从未出现**：`Adult`、`Base Building`、`Dating`、`Dystopian`、`Eroge`、`Hentai(Nudity)`、`Visual Novel (Adult)`。`[推]` 这说明存在命名与覆盖不一致：`Base Building` 与 `Base-Building` 并存（后者才被使用）；`Dystopian` 缺失导致带尾随空格的 `'Dystopian '` 完全无法映射。

`[实]` 被判为 `IGNORE` 的标签族（从杂交度中剥离的"非设计信号"）：联机/交互方式（`Singleplayer`、`Multiplayer`、`Co-op`、`PvP`、`VR`、`Controller`…）、商业模式与受众（`Indie`、`Early Access`、`Free to Play`、`Crowdfunded`、`Family Friendly`、`Mature`）、评价性标签（`Masterpiece`、`Great Soundtrack`、`Addictive`、`Beautiful`、`Replay Value`）、软件/非游戏媒介（`Software`、`Utilities`、`Movie`、`Documentary`、`Soundtrack`）、分级类（`Gore`、`Blood`）。
`[文]` **重要例外**：论文明确说明**刻意保留** `Action`、`Adventure`、`Casual` 等高频通用标签并归入 Meta-Tag 类别，理由是"Otherwise, the substantial share of the sample's measured hybridization will be zeroed."（若剔除，大量样本杂交度会归零）。管线实现与此一致（`Action`、`Casual` 保留为类别，`Adventure` 归入 `Adventure/Narrative`）。

### 3.5 步骤 5｜在游戏样本上聚类（K=8）

`[实]` `fit_priority_cluster()`：
1. 以 `Meta_Tags_Priority` 构造 **游戏 × 元标签** 数值矩阵（`mat[i, j] = priority`，缺失为 0）；
2. `KMeans(n_clusters=8, random_state=42, n_init="auto")`；
3. 每簇取质心权重 Top-10 作为该簇的"质心标签" `cluster_top_tags`。

`[文]` 与论文一致：论文 §3.4.1 用 priority 加权矩阵做 KMeans，并用 Cohen's h 在**二元标签存在性**上独立评估簇差异。

`[实]` 聚类结果（`cluster_megatag_reference.csv` + 实测）：

| 簇 | n | 占比 | 质心 Top5 标签 | 杂交度均值 | 中位数 | 范围 | 平均价 | 免费款数 |
|---|---|---|---|---|---|---|---|---|
| 0 | 2,181 | 12.33% | Casual; Adventure/Narrative; Action; Puzzle/Board; Simulation | 6.328 | 6 | 1–16 | 5.66 | 461 |
| 1 | 2,163 | 12.23% | Adventure/Narrative; Story-Driven; Perspective; Mood (Dark); Art Style | 11.968 | 12 | 5–18 | 10.87 | 165 |
| 2 | 1,741 | 9.84% | Mood (Positive); Casual; Simulation; Perspective; Art Style | 11.787 | 12 | 5–20 | 9.95 | 144 |
| 3 | 1,341 | 7.58% | RPG; Strategy; Perspective; Adventure/Narrative; Art Style | 11.151 | 12 | 2–17 | 15.78 | 125 |
| 4 | 2,478 | 14.01% | Simulation; Strategy; Perspective; Core System; Sports/Racing | 7.487 | 8 | 1–17 | 14.63 | 347 |
| 5 | 2,620 | 14.81% | Adventure/Narrative; RPG; Art Style; Adult; Action | 6.711 | 6 | **0**–17 | 9.84 | 491 |
| 6 | 1,977 | 11.18% | Action; Core System; Perspective; Adventure/Narrative; RPG | 11.643 | 12 | 4–19 | 15.80 | 160 |
| 7 | 3,185 | 18.01% | Action; Perspective; Art Style; Shooter; Platformer | 9.607 | 10 | 1–18 | 11.78 | 454 |

`[实]` **全部 16 个杂交度为 0 的样本都落在簇 5**（2,620 → 有效 2,604）。簇规模比 3,185 / 1,341 = **2.38 倍**。
`[实]` Cohen's h 突显度（`cluster_cohens_h_tags.csv`，`h ≥ 0.5` 的强定义标签；与论文 Table 10 **逐值一致**）：
- 簇 0：`Casual` 1.8316（**簇内占比 100%** — 完全分离）、`Puzzle/Board` 0.2757
- 簇 1：`Story-Driven` 1.4119、`Adventure/Narrative` 1.1059、`Atmospheric` 0.8858、`Mood (Dark)` 0.7845、`Puzzle/Board` 0.6837
- 簇 2：`Mood (Positive)` 1.3409、`Casual` 1.0543、`Simulation` 0.7289、`Colorful` 0.6970、`Perspective` 0.5394
- 簇 3：`RPG` 1.5246、`Strategy` 1.2744、`Turn-Based Combat` 1.0799、`Turn-Based` 0.9216、`Fantasy/Magic` 0.7848
- 簇 4：`Simulation` 1.1372、`Strategy` 0.9982
- 簇 5：`Adventure/Narrative` 0.6401
- 簇 6：`Core System` 1.2652、`Action` 1.0681、`RPG` 0.7765、`Perspective` 0.6480、`Exploration` 0.5411
- 簇 7：`Action` 1.4442（簇内 99.0%）、`Shooter` 0.6941、`Arcade` 0.5626、`Arcade/Top-Down Shooter` 0.5081、`Fighting/Brawler` 0.3784

`[实]` 40 条记录中 **28 条 h ≥ 0.5**；簇 0、4、5 分别只有 1、2、1 条达标。
`[推]` 语义解读：簇 0 = 休闲解谜；簇 1 = 叙事氛围；簇 2 = 轻松治愈模拟；簇 3 = 回合制 RPG/策略；簇 4 = 模拟经营/策略/军事；簇 5 = 叙事 + 成人内容（RPGMaker 生态）；簇 6 = 开放探索动作 RPG；簇 7 = 动作射击/平台街机。**簇间杂交度均值差异极大（6.33 → 11.97）** ⇒ 杂交度并非随机噪声，而与题材共同变化，这既是聚类的有效性别证，也提示**必须把题材纳入控制**（§7.1）。

`[实]` 实现说明：
- 聚类用 **priority 数值矩阵**（不是 TF-IDF、不是 0/1 二值矩阵）；
- `MIN_TAG_DOC_FREQ`、`silhouette_score`、`TfidfVectorizer` **均未参与**；
- 聚类质量（K 的选择、轮廓系数、稳定性）**无任何留存证据**；K=8 来自方法学引用（Grelier）与论文设定，而非本数据的肘部/轮廓分析。论文 Table 2 只提供了**被放弃方法**的轮廓系数。

### 3.6 步骤 6｜研究变量构造

`[实]`：
```
Hybridization_Index      = len(Meta_Tags)                        # 去重后的元标签维度数
Log_Reviews              = log1p(Total_Reviews)                  # 因变量
Hybrid_Centered          = Hybridization_Index − mean(Hybrid)     # 均值中心化，mean = 9.3246635757
Hybrid_Centered_Squared  = Hybrid_Centered²
in_focus_cluster         = Game_Cluster ∈ FOCUS_CLUSTERS          # 退化为恒 1
Game_Age                 = 2025 − Release_Year                    # 已定义，主模型未用
```

`[实]` **恒等式校验（全量 17,686 行，全部通过）**：
- `|Hybrid_Centered − (H − 9.3246635757)|` 最大偏差 2.22e-16，失败行数 **0**
- `|Hybrid_Centered_Squared − Hybrid_Centered²|` 最大偏差 1.78e-15，失败行数 **0**
- `|Log_Reviews − ln(1+Total_Reviews)|` 最大偏差 1.78e-15，失败行数 **0**
- `Total_Reviews = positive + negative` 失败行数 **0**
- `appid` 重复数 **0**

`[实]` 杂交度分布（全样本 17,686）：均值 **9.3247**、标准差 3.6756、最小 0、P25 7、中位数 10、P75 12、最大 20。`[注]` **论文 Table 1/4 报告均值 10.35、SD 4.14** —— 与管线任一可复现口径不一致（§5.4 第 2 条）。

**为什么中心化** `[推]`（本管线最漂亮的方法学处理）：二次项模型里 `H` 与 `H²` 天然高度共线（未中心化时 VIF 常 > 20）。减去均值后一次项系数变为"均值点处的斜率"，共线性大幅下降。`[实]` 实测 VIF：`Hybrid_Centered` **1.134942**、`Hybrid_Centered_Squared` **1.306966**、`price` **1.239591** —— 与论文 Table 3 **完全一致**。

**拐点的正确计算口径** `[推]`：
```
∂E[Log_Reviews]/∂H = β1 + 2β2·Hc = 0  ⇒  Hc* = −β1/(2β2)  ⇒  H* = mean(H) + Hc*
```
`[实]` 主模型：`H* = 9.3247 + 0.07606/(2×0.01446) = 11.96`。**不能**直接用 `−β1/(2β2) = 2.63`（那是中心化尺度上的偏移量，不是原尺度拐点）。
`[实]` **中心化分母的不一致**：`Hybrid_Centered` 以 **17,686 行**均值（9.3246636）计算，而模型使用 **17,670 行**（均值 9.3331070），差 **+0.008443**。斜率不受影响，但截距与拐点会平移 0.0084。`[推]` 该量级可忽略，但论文 Table 5 的 const = 6.3754 与管线 6.4891 相差 0.1137，**主要来自论文的杂交度均值口径（10.35 vs 9.32，差 1.0253 × β₁ ≈ 0.078）**，而非此项。

### 3.7 步骤 7–9｜导出、突显度与可视化

`[实]`：
- **导出 A（事实表）**：`games_clustered_meta_export.csv`，15 列 = `appid, name, Release_Year, Clean_Priority_Tags, Meta_Tags, Game_Cluster, in_focus_cluster, Total_Reviews, positive, negative, price, Hybridization_Index, Log_Reviews, Hybrid_Centered, Hybrid_Centered_Squared`；列表字段用 `"; "` 连接；`utf-8-sig` 便于 Excel 打开。
- **导出 B（附录对照）**：`cluster_megatag_reference.csv`，含 `n_games, share_pct, defining_meta_tags, mean/median/min/max_hybrid_index`。`[实]` `Σn_games = 17,686` ✅，`Σshare_pct = 100.00` ✅。
  ⚠️ `[实]` **`defining_meta_tags` 列名有误导性**：其实际内容取自 KMeans 质心 Top5（`cluster_top_tags[_cid][:5]`），**不是** Cohen's h 排序结果。两者仅约 2–3 项重合，且质心标签充斥非判别性标签（`Perspective` 在 8 簇中的 6 簇出现、`Art Style` 在 6 簇出现）。而论文 Table 10 **明确以 Cohen's h 排序**。建议把该列改名为 `centroid_top5_tags`，或改为 Cohen's h 口径。
- **导出 C（突显度）**：`cluster_cohens_h_tags.csv`，`cohens_h = 2·arcsin(√p_cluster) − 2·arcsin(√p_global)`，仅对出现频次 ≥ 全样本 0.5% 的元标签计算，每簇取 Top5。`[推]` 用 Cohen's h（而非简单占比差）是因为它是**尺度不变**的效应量，能跨标签频率差异比较"超额代表性"，与聚类质心互为交叉验证。
  ⚠️ `[实]` **该表混入了原始标签**（未映射的兜底标签），如簇 3 的 `Turn-Based Combat`（h=1.08）、`Turn-Based`（0.92）被列为"元标签定义 DNA"，而它们并非 META_DICT 类别。论文 Table 10 同样如此。建议补注说明，或只对字典类别计算 Cohen's h。
- **可视化**：`hybridization_curve.png`（散点 + 二次拟合 + 中位数 10.0 参考线，N=17,670）与 `dissertation_figures.png`（左：倒 U；右：规模最大簇 7 的 Cohen's h 条形图，含 0.2/0.3/0.8 效应量参考线）。
  `[推]` 图注用 "Log(Reviews)" 表述 `log1p(Total_Reviews)`，建议改为 `ln(1+Reviews)`；Cohen's h 的参考线用 0.2/0.3/0.8（"medium = 0.3" 非标准，通常为 0.5），建议改用 0.2/0.5/0.8。

---

## §4 分析结果（实测重估）

> 全部结果由 `06_tools/verify_all.py` 用 **numpy 正规方程独立重估**（环境中无 statsmodels/sklearn），同时给出经典标准误与 **HC1 稳健标准误**。实测主模型系数与 notebook 保存的输出**逐位一致**，可作为交叉验证。

### 4.1 主回归的样本构造

`[实]`：
```
reg_data  = data[Hybridization_Index > 0].dropna(subset=[Log_Reviews, Hybrid_Centered,
                                                         Hybrid_Centered_Squared, price])
Y         = Log_Reviews
year_dum  = get_dummies(Release_Year, prefix="Y", drop_first=True)   # 2015 = 基准年
```
- **为什么剔除杂交度 = 0** `[推]`：杂交度为 0 意味着该游戏的标签全部落在 `IGNORE` 或完全没有可用标签——这类样本不代表"零杂交的设计选择"，而是**测量失败**。实测被剔除 **16 款**（全部在簇 5）。论文未单独说明该剔除，写作时应显式声明。
- **为什么年份 FE 取代 `Game_Age`** `[推]`：评论量同时受"游戏年龄（曝光时长）"与"发行年份（竞争密度、平台算法环境）"影响，单一 `Game_Age` 把二者混淆。年份 FE 吸收所有年份层面的共同冲击，代价是部分吸收年龄效应。论文稳健性 2 用连续 `age_days` 做了对照。

### 4.2 主模型（对应论文 Table 5）

`[实]` 模型形式：

$$Log\_Reviews_i = \alpha + \beta_1 \widetilde{H}_i + \beta_2 \widetilde{H}_i^2 + \beta_3 price_i + \sum_{y=2016}^{2025}\gamma_y Y_{iy} + \varepsilon_i$$

> ✅ **本节数字已按 C1–C5 修正重算**（HC3 标准误、标签键 `strip()`）。来源：`02_pipeline/results/corrected_tables.md`。
> 修正前后的差异：R² 0.1622 → **0.1623**、β₁ +0.07606 → **+0.076131**、β₂ −0.01446 → **−0.014540**、
> 拐点 11.96 → **11.93**（中心化常数由 9.3247 变为 **9.3145**）。**结论方向与显著性完全不变。**

`[实]` N = **17,670**、k = 14、R² = **0.1623**、Adj. R² = **0.1616**、Durbin-Watson ≈ **0.343**、σ ≈ 1.400：

| 变量 | coef | SE(经典) | t(经典) | SE(HC1) | **SE(HC3)** | **t(HC3)** | 论文 HC3 SE |
|---|---|---|---|---|---|---|---|
| `const` | 6.4898 | 0.0396 | 163.69 | 0.0403 | **0.0404** | **160.74** | 0.0439（论文 const = 6.3754） |
| `Hybrid_Centered` | **+0.076131** | 0.00328 | 23.22 | 0.00320 | **0.00320** | **+23.77** | **0.0032** ✅ |
| `Hybrid_Centered_Squared` | **−0.014540** | 0.00075 | −19.40 | 0.00068 | **0.00068** | **−21.29** | **0.0007** ✅ |
| `price` | **+0.038111** | 0.00091 | 41.68 | 0.00161 | **0.00164** | **+23.23** | **0.0016** ✅ |

`[实]` **HC3 列与论文 Table 5 三个斜率标准误吻合到 4 位小数**（0.00320/0.0032、0.00068/0.0007、0.00164/0.0016），
这是"论文确实使用 HC3、且其回归所用指数与管线相同"的又一条独立证据。
仅 `const` 的 SE 不吻合（0.0404 vs 0.0439），差异来自年份虚拟变量的基准/集合，不影响任何关注量。

`[实]` 年份固定效应（HC1）：Y_2016 −0.0449 (t=−0.99)、Y_2017 −0.1607 (−3.46)、Y_2018 −0.1497 (−3.14)、Y_2019 −0.1520 (−3.01)、Y_2020 −0.2770 (−5.62)、Y_2021 −0.4484 (−8.50)、Y_2022 −0.5915 (−10.85)、Y_2023 −0.6329 (−12.17)、Y_2024 −0.7826 (−16.27)、Y_2025 −0.9149 (−11.22)，全部 p<0.01（Y_2016 除外）。

`[推]` 解读要点：
1. **倒 U 型成立**：β₁ > 0 且 β₂ < 0，均在 0.1% 水平显著；拐点 H* = **11.93**（HC3 口径），位于样本 P75（12）附近 ⇒ "约 12 个元标签维度"是商业表现的峰值区，且**落在数据支撑范围内**（上限 20），拐点可信。
2. **经济显著性**：均值附近杂交度每 +1 个维度，评论量约 +7.6%（log 点近似弹性）；峰值相对均值点的增益约 `β₁²/(4|β₂|) ≈ 0.100` log 点 ≈ **+10.5%** 评论量 `[推]`。
3. **价格**：每 +1 USD 对应约 +3.8% 评论量。`[推]` **不能读作因果**：价格与质量/预算互为因果，且样本中 **2,347 款（13.27%）为免费游戏**（price = 0），价格系数部分承载"付费 vs 免费"的组间差异。
4. **年份 FE 单调下降**：2025 年相对 2015 年低 0.91 log 点。`[推]` 这主要反映**曝光时长差异**（2025 年发行的游戏只有数月积累评论）而非市场恶化；必须避免因果化解读。
5. **DW = 0.343 是红旗** `[推]`：远低于 2，残差强正自相关；JB 显著、峰度 4.33、偏度 0.96。在横截面数据中通常意味着**未观测的组内相关**（同发行商、同系列、同题材批次）。常规 OLS 标准误因此偏小。**论文用 HC3 只解决异方差（BP LM=601.91、White LM=1,489.97），并未解决自相关**。修正方式：按簇/发行商聚类稳健标准误或双向聚类（§4.4 已预演）。
6. **✅ 已修正：HC3 显著改变 price 的推断** `[实]`：price 的 SE 从 0.00091（经典）增至 **0.00164（HC3）**（t 由 41.68 降到 **23.23**），仍极显著，但**说明经典标准误系统性低估**；论文 Table 5 的 price SE = 0.0016 正与稳健口径吻合。**该实现差距已于本次修正 C1 补齐**——notebook 中 5 处 `.fit()` 均已改为 `cov_type="HC3"`。

### 4.3 稳健性检验（4 组，对应论文 Table 6–9）

**(1) 无时间控制（Model 0，Price-only 基线）** `[实]`
N = 17,670，R² = 0.1365，β₁ = +0.05224 (p<0.001)，β₂ = −0.01301 (p<0.001)，拐点 **11.33**。
`[文]` 与论文 Table 6（+0.0522 / −0.0130 / R² 0.1365 / Peak 11.33）**完全一致** ✅。

**(2) 按天游戏年龄连续控制** `[实]`
以 `cutoff = 2025-03-10` 计算 `age_days`，中心化后入模：
N = 17,670，R² = 0.1604，β₁ = +0.07583，β₂ = −0.01462，`age_days_c = +0.000243`，拐点 **11.92**（论文 Table 7 一致 ✅）。
`[推]` 与主模型几乎一致 ⇒ 结论对"年份 FE 还是连续年龄"不敏感；年龄系数为正也印证"越老的游戏评论越多"的机械关系。

**(3) 价格调制（年份 FE + 杂交 × 价格交互）** `[实]`
N = 17,670，R² = 0.1716，β₁ = +0.08373，β₂ = −0.01692，`Hc×price = +0.00326` (p<0.001)，`Hc²×price = −0.00032` (p<0.001)，拐点 **11.80**（论文 Table 8 的 `Hybridization² × Price = −0.000317` 一致 ✅）。
`[推]` 符号组合（一次交互为正、二次交互为负）意味着**价格越高，倒 U 的上升段更陡、峰值略前移**：高价位游戏的杂交收益更依赖精准定位。R² 提升 0.94 个百分点 ⇒ 价格调制是真实效应。论文评价为"经济量级相对主效应较小"。

**(4) Priority 阈值序列（七档敏感性）** `[实]` —— 本管线最重要的方法学证据，但**与论文 Table 9 不一致**：

| t（阈值） | 管线 N | 管线均值 | 管线 β₁ | 管线 β₂ | 管线拐点 | 管线 R² | 论文 N | 论文均值 | 论文拐点 |
|---|---|---|---|---|---|---|---|---|---|
| 0.15 | 17,639 | 8.92 | +0.0528 | −0.0131 | 10.93 | 0.1384 | 17,736 | 11.25 | 13.12 |
| 0.20 | 17,630 | 8.67 | +0.0436 | −0.0123 | 10.44 | 0.1305 | 17,725 | 10.91 | 12.92 |
| 0.25 | 17,604 | 8.39 | +0.0379 | −0.0119 | 9.99 | 0.1258 | 17,692 | 10.62 | 12.57 |
| **0.30** | 17,578 | 8.06 | +0.0354 | −0.0111 | 9.66 | 0.1217 | **17,670** | **10.35** | **11.96** |
| 0.35 | 17,548 | 7.70 | +0.0346 | −0.0106 | 9.33 | 0.1190 | 17,639 | 10.03 | 11.52 |
| 0.40 | 17,515 | 7.33 | +0.0324 | −0.0099 | 8.97 | 0.1158 | 17,605 | 9.69 | 10.98 |
| 0.45 | 17,488 | 6.96 | +0.0281 | −0.0090 | 8.52 | 0.1135 | 17,581 | 9.32 | 10.45 |

`[推]` 关键读数：
- **符号与显著性完全稳定**：七档全部 β₁ > 0、β₂ < 0 ⇒ 倒 U 的**定性结论不依赖阈值选择**；
- **拐点位置对阈值高度敏感**：阈值从 0.15 收紧到 0.45，管线拐点由 10.93 下移到 8.52（下移 2.41 个维度），论文由 13.12 下移到 10.45（下移 2.67）——**两套数字的斜率几乎相同，但水平整体相差约 2 个维度**；
- **表中 t=0.30 一行的 N 与均值与主模型不同**（该行是"阈值路径 + 元标签非空"样本，N=17,578、均值 8.06；主模型是"全量路径"，N=17,670、均值 9.32）。**两者不可直接对比数值**，仅可比较方向与相对位置；
- `[推]` **论文 Table 9 在 t=0.30 处报 N = 17,670、Index Mean = 10.35，恰好等于论文主模型（Table 1/5）的值** ⇒ **论文的 t=0.30 一行就是它的主模型**（同一个 N = 17,670、同一个 β₁ = +0.0761、同一个均值 10.35），这与论文把 0.30 写进索引定义完全自洽；论文均值也确实随阈值单调变化（11.25 → 9.32），说明论文每一档都重算了索引。**真正的分歧不在"是否重算"，而在"同一档位下索引水平差多少"**：论文在 t=0.30（已收紧）处均值仍有 **10.35**，而管线在**完全不收紧**的全量口径下均值只有 **9.3247**——论文的索引在整个阈值区间内都比管线高约 1.0–2.3 个维度。⇒ **单靠"去掉阈值"无法对齐论文**，必须回到元标签词典与维度合并规则本身（见 §5.4 第 2、3 条）；
- 因此论文报告拐点时**必须同时报告阈值与索引口径**，否则"最优约 12 个标签"与"最优约 8.5 个标签"会给读者相反印象。建议以主模型口径为正文，阈值序列作为附录敏感性分析。

`[实]` **该表的机制复现（`06_tools/check_threshold_03.py`）——一个此前未发现的问题**：notebook 的"阈值序列"变化的主因**不是阈值在筛选标签**，而是 `'IGNORE'` 归并在清空游戏。

- 逐档分解删除来源：**`_Cpt`（priority ≥ t 的标签列表）为空的行数，在全部七档都是 0**。原因是每款游戏票数最高的那个标签 priority 恒等于 1.0，永远 ≥ 任何 t ≤ 1，所以 priority 过滤**一次也没有删掉任何一行**；
- N 的下降**全部**来自 `_Mt` 为空，即"priority ≥ t 的标签恰好全部被 `META_DICT` 映射到 `'IGNORE'`"的行数：t = 0.15 → **47** 行，t = 0.30 → **108** 行，t = 0.45 → **198** 行；
- `META_DICT` 有 **44** 个键指向 `'IGNORE'`，其中含 `Multiplayer`、`Singleplayer`、`Indie`、`Free to Play`、`Gore`、`Great Soundtrack`、`Controller` 等**极常见**标签。阈值越高 → 幸存标签越少 → 被 IGNORE 清空的概率越大；
- ⇒ 该表的 N 变化**不能**表述为"按 priority 阈值筛选样本"，它是 IGNORE 归并的副产物。同理，Step 1 里那处 `priority ≥ 0.3` 样本过滤**实际删除 0 行**：85,884 → 17,772 全部由"评论 ≥ 100"造成，17,772 → 17,686 的 86 行全部由"非 Indie 大厂"造成。**0.3 在样本纳入上是非约束性（non-binding）的**；
- `[推]` 论文 Table 9 的 N 由 17,736 降到 17,581（减 155 行），管线由 17,639 降到 17,488（减 151 行），**收缩量级接近**，说明两侧都遵循"阈值越高、标签越少"的机制；论文 t=0.30 的 17,670 也正好等于管线走全量路径时的回归样本量。差异仍在**水平**而非**方向**。

### 4.4 补充检验（工作区新增，论文未做）

**(a) 加入题材簇固定效应（P0 改进预演）** `[实]` —— 检验结论是否由题材构成驱动：
N = 17,670，R² = **0.1752**（主模型 0.1622），β₁ = **+0.0773** (t=20.56)、β₂ = **−0.0141** (t=−20.84)、price = +0.0354 (t=22.03)，拐点 **12.07**。
`[推]` 倒 U 在吸收题材构成后**依然成立**，且系数几乎不变 ⇒ 该竞争解释被排除，结论从"题材构成效应"升级为"设计杂交本身的效应"。

**(b) 分簇单独估计（异质性检验）** `[实]`：

| 簇 | N | R² | β₁ | t₁(HC1) | β₂ | t₂(HC1) | 峰值 | 簇均值 |
|---|---|---|---|---|---|---|---|---|
| 0 | 2,181 | 0.082 | +0.0486 | 3.78 | −0.0072 | −3.44 | 9.68 | 6.33 |
| 1 | 2,163 | 0.145 | +0.0899 | 3.62 | −0.0137 | −3.12 | 15.25 | 11.97 |
| 2 | 1,741 | 0.075 | −0.0115 | **−0.37** | −0.0080 | **−1.65** | 11.07 | 11.79 |
| 3 | 1,341 | 0.120 | +0.1053 | 8.03 | −0.0149 | −4.13 | 14.70 | 11.15 |
| 4 | 2,478 | 0.180 | +0.0826 | 5.65 | −0.0162 | −6.58 | 10.04 | 7.49 |
| 5 | 2,604 | 0.223 | +0.1739 | 12.29 | −0.0034 | **−1.52** | 32.15 | 6.75 |
| 6 | 1,977 | 0.180 | +0.0430 | **1.56** | −0.0145 | −2.86 | 13.12 | 11.64 |
| 7 | 3,185 | 0.197 | +0.0774 | 10.86 | −0.0171 | −10.45 | 11.88 | 9.61 |

`[推]` **结论在子市场中并不完全同质**：簇 2（轻松治愈模拟，β₁ 不显著、二次项仅边际显著）与簇 5（叙事+成人，二次项不显著、峰值 32 落在数据范围之外）**不支持倒 U**；簇 6 线性项不显著但二次项显著。⇒ 论文"the concave pattern remains stable"的表述需要限定为**总体层面**；分簇异质性本身是一个可写的补充发现。

**(c) 二次项 vs 分箱均值（无参数证据）** `[实]`：

| 杂交度区间 | N | Log_Reviews 均值 | 区间中心 |
|---|---|---|---|
| (0, 4] | 2,477 | 5.565 | 3.02 |
| (4, 7] | 2,800 | 6.082 | 6.03 |
| (7, 10] | 4,580 | 6.667 | 9.15 |
| **(10, 12]** | 4,139 | **6.701** | 11.51 |
| (12, 14] | 2,793 | 6.598 | 13.40 |
| (14, 16] | 807 | 6.304 | 15.30 |
| (16, 25] | 74 | 6.483 | 17.24 |

`[推]` **非参数证据与参数估计高度吻合**：均值在 (10, 12] 区间见顶（6.701），与回归拐点 11.96 一致；之后单调下滑到 (14,16] 的 6.304。最后一档 N=74 反弹（6.483）但样本太小、不具解释力。**这是倒 U 结论最有力的稳健性证据之一**（不依赖二次函数形式），建议纳入论文。

**(d) 以好评率为第二因变量（需求 vs 合法性）** `[实]`：
因变量 = `pct_pos_total`（好评率 %），N = 17,670，R² = 0.0672：
`Hybrid_Centered` = **+0.8054** (t=20.39)、`Hybrid_Centered_Squared` = **−0.0866** (t=−8.56)、`price` = −0.0461 (t=−3.31)，均 p<0.01。
`[推]` **杂交度同样与评价合法性呈倒 U**，且价格的符号转为负（越贵好评率越低）。这直接支持类别跨越理论中"过度杂交 ⇒ 合法性/一致性下降"的机制路径，**是论文 Discussion 最缺的一块拼图**。

**(e) 加入质量/投入代理变量（缓解遗漏变量）** `[实]`：
控制 `ln(playtime)`、`ln(achievements)`、`ln(dlc)`、`ln(peak_ccu)` 后：N = 17,670（与主模型**同一样本**，四个代理无缺失），R² = **0.6940**；
`Hybrid_Centered` = +0.0547 (t=26.79)、`Hybrid_Centered_Squared` = **−0.0060** (t=−13.23)、**`price` = −0.0001 (t=−0.13, 不显著)**，
四个代理自身系数全部**为正且显著**（`ln_playtime` +0.0799、`ln_achievements` +0.0213、`ln_dlc` +0.1262、`ln_peak_ccu` +0.5692），拐点 13.91。
`[实]` **该结果的进一步拆解**（`06_tools/check_quality_proxies.py`，报告见 `quality_proxy_report.md`）：
- 四个代理两两相关仅 0.130–0.365、VIF 1.13–1.43 ⇒ **不是共线性造成的系数翻转**，需逐个加入才能定位；
- 四个代理能解释 `price` 方差的 **20.3%**，但只能解释 `Hybridization_Index` 的 **6.1%** ⇒ 倒 U 与质量代理近乎正交，不可能被它们吸收；
- **逐个加入时 `price` 依然显著**（t = 18.8–22.5）；只有单独加入 `ln_peak_ccu` 才把它压到 +0.0026 (t=3.03)，而这一个变量就贡献了 R² 增量 0.5319 中的 **96%**；
- 剔除 `ln_peak_ccu`（它与因变量相关 **0.769**，与评论量同源，属"坏控制"）后：R² = 0.3474，**`price` 回升到 +0.0210 (t=16.76)**、`Hybrid_Centered_Squared` = −0.0107 (t=−17.49)、**拐点回到 11.96**；
- 改用单一标准化合成指标 `quality_z`（四个代理 z 分数等权平均）时：R² = 0.4905、price = +0.0065 (t=6.78)、拐点 11.84。

`[推]` 三个含义（**其中第一条修正了本报告上一版的表述**）：
- **价格的显著性是被"部分吸收"，不是"完全吸收"**：只有含 `ln_peak_ccu` 的完整规格才让它归零；用不含同源热度代理的干净规格衡量，价格效应仍有基准的约 **55%**（+0.0210 vs +0.0381，t=16.76）⇒ 论文的"价格—质量信号"方向仍站得住，但**必须报告这组敏感性**，且**不能**写成"控制质量后价格无效应"；
- **二次项在控制质量后仍然显著为负**（β₂ 在 −0.0060 ~ −0.0107 之间），倒 U 不是质量代理的伪装 ⇒ 结论加固；
- **拐点 13.91 是假位移**：完全由 `ln_peak_ccu` 造成，剔除后回到 **11.96**（合成版 11.84），与 §4.4c 分箱均值在 (10,12] 见顶一致 ⇒ 峰值应报 **≈11.8–12.0**，不要报 13.91。

### 4.5 相关性与描述统计（写作可用的一页数字）`[实]`

Pearson 相关（17,686）：

| | price | Hybridization_Index | Log_Reviews | Total_Reviews |
|---|---|---|---|---|
| price | 1 | 0.1650 | 0.3080 | 0.1203 |
| Hybridization_Index | 0.1650 | 1 | **0.2114** | 0.0506 |
| Log_Reviews | 0.3080 | 0.2114 | 1 | 0.4426 |
| Total_Reviews | 0.1203 | 0.0506 | 0.4426 | 1 |

`[推]` **注意 `Hybridization_Index` 与 `Total_Reviews` 的线性相关仅 0.0506**，与 `Log_Reviews` 为 0.2114 ⇒ 线性相关几乎捕捉不到关系，**倒 U 是真正的非线性发现**，这也解释了为何必须用二次项而非线性模型。

关键描述统计（17,686）：`price` 均值 11.5961 / SD 11.9644 / 中位数 9.5900 / 最大 269.99（`price ≥ 100` 仅 **1** 款，`price = 0` 有 **2,347** 款 = 13.27%）｜`Total_Reviews` 均值 3,928.85 / 中位数 396 / 最大 1,195,980｜`Log_Reviews` 均值 6.3998 / SD 1.5292 / 范围 4.6151–13.9945。

**发行年份分布** `[实]`：2015 年 1,473 款（8.33%）、2016 年 1,922、2017 年 1,904、2018 年 1,850、2019 年 1,526、2020 年 1,901、2021 年 1,628、2022 年 1,395、2023 年 1,650、**2024 年 2,129（12.04%，最高）**、2025 年 308（1.74%，截至 3 月）。`[推]` 各年杂交度均值从 2015 年的 7.63 单调上升到 2022–2025 年的 11.0 左右 ⇒ **元标签使用随时间显著变丰富**，这既支持年份 FE 的必要性，也提示"杂交度上升"本身是一个行业趋势。

**Meta_Tags 词表（Top 15，共 192 个取值）** `[实]`：Perspective 11,509（65.07%）、Adventure/Narrative 10,330（58.41%）、Art Style 8,800（49.76%）、Action 8,187（46.29%）、Casual 6,563（37.11%）、Simulation 6,288（35.55%）、Mood (Positive) 5,994（33.89%）、Core System 5,438（30.75%）、Story-Driven 5,351（30.26%）、RPG 5,120（28.95%）、Strategy 4,646（26.27%）、Puzzle/Board 4,458（25.21%）、**Atmospheric 4,424（25.01%，兜底）**、Mood (Dark) 4,258（24.08%）、Fantasy/Magic 3,485（19.70%）。

### 4.6 语言支持旁支分析（`04_language_extension/`）

`[实]` 设计（`lang_group_analysis.py` / `lang_analysis2.py`）：样本为同一批 17,686 款游戏，按 `appid` 左连接原始 CSV 的 `supported_languages`；互斥分组：**A 有中文**（简/繁）｜**B 只有英语**（语言集合 = {English}）｜**C 有其它大语种**（无中文、非纯英语、命中 11 个"大语种"）｜**D 有其它小语种**；因变量 `Log_Reviews`；检验链 = 分组描述 → 以 B 为基准的 Welch t 检验 + 单因素 ANOVA → OLS（组别虚拟 + `price` + 年份 FE + `Hybrid_Centered`/`_Squared`）。`lang_analysis3.py` 为放宽版：用原始数据（`Total_Reviews > 0`，含大厂），不含杂交度控制，逐步加入 `genres` 题材虚拟（≥200 款）与发行商/开发者固定效应（≥20 款的公司）。

`[实]` **这四个脚本没有任何落盘输出**（仅 `print`）⇒ 结论目前**不可追溯**，写作时不能引用。
`[注]` 且 `lang_group_analysis.py` 的文件内容整体被包在一个字符串字面量里（首尾为 `"` 与 `"`，内部转义），**不是可执行脚本**；应删除或修正。
`[推]` 机制与风险：本地化本身是质量/预算的信号（选择效应）；`lang_analysis3.py` 加入发行商 FE 后识别来自"同一发行商内部是否做某语言本地化"的变异，是这条支线最有价值的一版。建议定位为主论文的**延伸章节/附录**，或独立成文。

### 4.7 结果可信度评级

| 结论 | 强度 | 理由 |
|---|---|---|
| 杂交度与评论量呈倒 U 型（方向） | **强** `[实]/[文]` | 4 组稳健性 + 7 档阈值 + 分箱均值（非参数）+ 簇 FE + 质量代理控制，全部一致；论文与管线数值在多数表格上吻合 |
| 拐点位于 11–12 个元标签维度 | **中→强** `[实]` | 主模型口径下 11.75–12.07（4 组稳健性 + 簇 FE + 分箱均值 + 剔除同源热度代理后的代理规格全部落在 11.84–12.07）；位移到 13.91 的规格已定位为 `peak_ccu` 造成的假位移（§4.4e）。仍对索引口径与阈值敏感（8.5–13.1） |
| 价格正向影响评论量 | **弱** `[实]` | 价格方差的 20.3% 可由开发体量/热度代理解释；含 `ln_peak_ccu` 时归零，剔除后仍有 +0.0210 (t=16.8)。内生性明显（免费游戏占 13.27%） |
| 8 个游戏簇的语义有效性 | **中** `[实]/[文]` | Cohen's h 与质心双口径交叉验证、簇间杂交度差异明显；但无轮廓系数/稳定性证据，K=8 非本数据驱动选择 |
| 年份 FE 的负向趋势 = 市场恶化 | **不成立** `[推]` | 主要是曝光时长与样本构成差异 |
| 倒 U 在**所有**子市场成立 | **不成立** `[实]` | 簇 2、簇 5 不显著（§4.4b） |
| 语言支持与商业表现的因果效应 | **未评估** `[实]` | 脚本无输出；设计上存在选择效应 |

---

## §5 论文侧要点与对照

> 完整逐节摘要（含原文引用与 16 条差异清单）见 `03_literature/paper_digest.md`。此处只保留写作与答辩最需要的内容。

### 5.1 论文的结论要点 `[文]`

- **RQ1**：当代独立游戏市场是**多维结构**，很少由单一传统类型定义；子类型结构支持**重组式创新**（recombinant innovation）解读，说明传统互斥类型分类的局限。
- **RQ2（核心）**：β₁ = +0.0761、β₂ = −0.0145（均 p<0.001），**峰值约 11.96** ⇒ 特征广度在中等水平前与商业表现正相关，之后继续杂交导致下降，为 **over-hybridization penalty** 提供实证支持；"the underlying concave pattern remains stable"。
- **RQ3**：价格在所有设定中正且显著（主模型 β = +0.0381, p<0.001）；价格调制交互项显著但经济量级较小 ⇒ 价格是 "an additional related signal rather than determinant of the optimal level of hybridization"，与价格—质量信号视角一致。

### 5.2 论文的实践意涵 `[文]`

警示 "**Frankenstein fallacy**"：为差异化或平台曝光不断堆叠不相关机制，最终会削弱产品的商业地位；开发者应追求**连贯的组合**，让新增特征强化核心身份。**11.96 的经验峰值**表明中等特征广度与更强表现相关。价格的正向关联意味着"**降价未必提升销量**"；杂交与定价是**相关但不同**的战略决策。

### 5.3 论文自陈的局限与未来研究 `[文]`

**局限**：① 以用户评论代理销量，评论—销量关系可能不稳定（参与度、区域、类型、社区差异）；② 索引来自用户标签，是"玩家感知并表达的特征广度估计"，仍含主观判断与残余噪声；③ **横截面数据限制因果解释**，质量、营销、声誉、评论情感、发行策略等未观测因素同时影响自变量与因变量。
**未来研究**：时间序列与更丰富的行为数据（区分初期接受与长期表现、检验最优杂交水平是否随生命周期变化）；更直接的商业表现度量（已验证销量估计、收入、**愿望单数**、峰值在线人数、参与度指标）。

### 5.4 论文 ↔ 管线：冲突与差异清单（`[实]` 经 §7.2 量化后**只剩 ① 是代码问题**）

> 全部由实测复现得出，证据见 `06_tools/verify_report.md`、`coverage_report.md`、`aux_report.md`。

| # | 项目 | 论文 `[文]` | 管线实测 `[实]` | 处理建议 |
|---|---|---|---|---|
| 1 | **标准误类型** | 全程 **HC3** 异方差稳健（BP LM=601.91、White LM=1,489.97，p<.001），并声明"系数估计不变" | statsmodels **默认经典标准误**，无稳健修正 | **P0**：改为 `cov_type='HC3'`；实测 HC1 下 price 的 t 由 41.69 降至 23.62 ⇒ 结论不变但推断更保守 |
| 2 | **杂交度均值** | Table 1/4/9 均报 **10.35**（SD 4.14） | 全量口径 **9.3247**（SD 3.6756）；0.30 阈值口径 **8.06** | **`[实]` 重新定级：疑为论文报数口径问题，非代码分歧**。论文自己报的 β₁ = +0.0761、β₂ = −0.0145、拐点 11.96 **在算术上要求 mean = 9.3359**（若为 10.35 则拐点应为 12.97），七档全不成立 ⇒ 先向作者确认 10.35 出自哪个数据框，**不要为凑该数改词典**（§7.2.2） |
| 3 | **索引是否施加 0.30 阈值** | 定义写 "after dictionary organizing **and priority (0.30) filtering**" | `build_meta_fields()` **不施加阈值**（全量路径）；阈值路径只用于 `all_tags.txt` 与样本非空过滤 | **P0**：定义与实现二选一，并同步修正 §3.2/§3.3 的表述。`[实]` 注意：该阈值在样本纳入上**删除 0 行**（非约束性），所以"去掉阈值"改不动主模型任何数字 |
| 4 | **阈值稳健性表（Table 9）** | N 17,736→17,581；Index Mean 11.25→9.32；Peak 13.12→10.45 | N 17,639→17,488；Index Mean 8.92→6.96；Peak 10.93→8.52。`[实]` N 的收缩来自 **IGNORE 归并**（47→198 行），非阈值筛选 | **`[实]` 已定量分解**（§7.2）：论文 **t=0.30 行与管线不加阈值的主模型逐位相同**（N 17,670、β₁ +0.0761、β₂ −0.0145、拐点 11.96、R² 0.1622）⇒ 论文该表在 0.30 处并未真正施加阈值。剩余"水平差 1.0–2.3 个维度"与论文均值列的算术问题同源（§7.2.2）。**动作**：统一词典口径后整表重跑，并在正文注明阈值未咬合 |
| 5 | **截距** | const = **+6.3754** | const = **+6.4891** | 差异主要由索引均值口径（10.35 vs 9.32）造成；统一口径后自然收敛 |
| 6 | **`defining_meta_tags` 来源** | Table 10 明确以 **Cohen's h** 排序 | `cluster_megatag_reference.csv` 该列实为 **KMeans 质心 Top5** | 改名 `centroid_top5_tags` 或改为 Cohen's h 口径；否则附录与正文口径不一致 |
| 7 | **Cohen's h 表混入原始标签** | Table 10 中簇 3 含 `Turn-Based Combat`、簇 5 含 `RPGMaker`、簇 2 含 `Colorful` | 同（一致，非错误） | 补注说明"兜底标签"的存在，避免读者误解分类体系 |
| 8 | **META_DICT 覆盖度** | 称依 VGMS + Li (2020) EFA 构建词典归并共现标签 | `Meta_Tags` 有 **192 个取值**，其中 **166 个为未映射原始标签**，占元标签计数 **32.09%** | **P0**：补齐字典并重跑；同时报告"仅字典口径"的稳健性（已验证倒 U 仍成立，峰值 10.94） |
| 9 | **空白标签污染** | 未提及 | `'Dystopian '`（1,050 款）、`'Parody '`（583 款）带尾随空格绕过 `META_DICT.get()`；共 1,615 款（1.80%） | **P0**：`strip()` 归一化后重跑（低成本） |
| 10 | **字典死键** | 未提及 | 291 键中 7 键从未出现：`Adult`、`Base Building`、`Dating`、`Dystopian`、`Eroge`、`Hentai(Nudity)`、`Visual Novel (Adult)` | 清理并补键（尤其 `Dystopian`） |
| 11 | **残留自相关** | 只报异方差检验，未报 DW | **DW = 0.343**，JB 显著、峰度 4.33 | **P1**：补簇/发行商聚类稳健标准误（已验证结论不变） |
| 12 | **分簇异质性** | 未报告 | 簇 2、簇 5 不支持倒 U（§4.4b） | **P1**：作为补充分析写入，并把总体结论限定为"总体层面" |
| 13 | **价格的质量代理性质** | 解释为价格—质量信号 | price 方差的 20.3% 可由体量/热度代理解释；含 `peak_ccu` 时归零（t=−0.13），剔除后仍为 +0.0210 (t=16.8) | **P1**：补控制变量后重估，并把 price 的解释从"信号"改为"信号+质量混合"（**不要写成"价格无效应"**） |
| 14 | **好评率机制检验** | 未做 | 好评率同样倒 U（β₂=−0.0866） | **P1**：作为"合法性下降"机制的直接证据写入 Discussion |
| 15 | **聚类有效性证据** | Table 2 报告被放弃方法的轮廓系数 | 工作区**无任何**轮廓系数/稳定性证据 | **P2**：复现 Table 2，或对最终 K=8 解补轮廓系数与重抽样稳定性 |
| 16 | **AAA 剔除口径** | 按知名发行商黑名单剔除 | 按"非 Indie 且 owner ≥ 5,000,000"剔除 86 款 | **P2**：说明代理规则，或补黑名单做敏感性分析 |

---

## §6 结论的意涵

### 6.1 理论意涵

1. **对 "More Is Better" 的直接回应** `[实]/[文]`：标签数量的边际价值并非单调。数据支持"数量带来被发现的机会，但当类别身份被过度稀释时收益转负"，为**最优区分理论在数字商品市场的适用性**提供大样本证据。
2. **把"游戏空间"从概念工具变成可测量构念** `[推]`：以"元标签维度数"操作化杂交度，使抽象的 game space 具备**可回归的度量**，且不受文案长度干扰（相较文本相似度或题材二元虚拟）。
3. **类别跨越的代价可量化** `[推]`：倒 U 的下降段给出"跨越多少维度后开始被惩罚"的边界（约 12 个维度），比"存在惩罚"的定性论断更有用。
4. **论文的构念限定值得保留** `[文]`：索引应读作"**玩家感知并表达的特征广度**"，而非开发者设计阶段的实际融合 ⇒ 这为后续研究留出了"设计端 vs 感知端"的测量分歧空间。
5. **价格的角色需要重新表述** `[实]`：价格方差的 **20.3%** 可被开发体量/热度代理解释；含同源热度代理 `peak_ccu` 时价格系数归零，剔除后仍保留约基准的 **55%**（+0.0210, t=16.8）⇒"价格—质量信号"与"质量本身"在同一系数里混同，但**并非被质量完全解释**；对理论而言，这意味着**价格信号假说需要更干净的识别设计**（§4.4e）。

### 6.2 实践意涵（对独立开发者）`[推]`

1. **不要用标签堆砌换曝光**：预期峰值区约在 **10–12 个元标签维度**，超过后评论量趋于下降。
2. **优先在"机制 + 主题"两个维度上杂交，而非四维均匀铺开**：簇 1（叙事氛围）与簇 2（轻松治愈）杂交度都在 11.8–12.0，属于"高杂交但身份清晰"的范式——在同一主题/情感基调下融合多个玩法维度。
3. **高价位需要更聚焦的身份**：交互模型提示价格越高，过度杂交的惩罚越明显（`Hc²×price < 0`）。
4. **降价未必提升表现**：论文与管线都显示价格与评论量正相关（虽然控制开发体量/热度代理后该关系大幅减弱、在含 `peak_ccu` 的规格里归零），提示定价与杂交是**相关但不同**的战略决策。
5. **本地化广度是另一个可运营的"杂交维度"**，但收益需与预算/质量一起评估，不能单独解读（§4.6）。

### 6.3 方法学意涵（对后续研究者）

1. **Steam 标签不是设计属性的纯净测量**：必须显式剔除商业模式、联机方式与评价性标签，且必须报告"未映射标签"清单与其影响（本工作区的 32% 兜底占比就是反例）。
2. **"标签数量"类指标的拐点极依赖预处理口径**：本管线阈值敏感性显示拐点可移动 **2.4 个维度**（论文侧 2.67），任何报告拐点的研究都应附阈值与口径敏感性表。
3. **众包标签的"重要性"需按游戏内部归一化**（priority），绝对票数会把人气混入测量。
4. **二次项研究必须报告拐点、数据支撑范围与合理区间**：本样本 0–20、P75=12，拐点 11.96 落在分布内部 ⇒ 有充分数据支撑，可以放心报告。
5. **不要只用二次项证明倒 U**：分箱均值（§4.4c）提供了不依赖函数形式的证据，成本极低而说服力强。

---

## §7 效度威胁与改进路线图

### 7.1 结构性缺口：聚类没有进入回归（最高优先级）

`[实]` 聚类结果目前只用于描述（附录对照表、Cohen's h 图），主回归**没有簇固定效应**，也没有题材控制。而簇间杂交度均值差异巨大（6.33–11.97），簇 0（Casual 100%）、簇 7（Action 99%）身份极其鲜明。
`[推]` 后果：倒 U 可能部分由**题材构成效应**驱动。
`[实]` **已预演并排除**（§4.4a）：加入簇 FE 后 R² 由 0.1622 升至 **0.1752**，β₁ = +0.0773、β₂ = −0.0141（符号与显著性不变），拐点 12.07。
**动作**：把该设定写入正文或稳健性附录；补分簇估计（§4.4b）以说明异质性。

### 7.2 测量效度：杂交度的口径依赖

`[实]/[推]` 四个具体风险：
- **阈值口径敏感**（§4.3 表）：拐点随 priority 阈值移动 2.4–2.7 个维度；
- **两条标签路径并存**导致"同一构念两个数字"（全量 9.32 vs 阈值 8.06），且与论文的 10.35 均不一致；
- **META_DICT 粒度是人为决定**：把 20 个射击子类合并为 `Shooter` 与把整个模拟族合并为 `Simulation`，会系统性改变分布；缺少"字典粒度"敏感性分析；
- **兜底标签占 32.09%**（§7.3）。

#### 7.2.1 词典与维度合并规则的量化分解 `[实]`（`06_tools/check_index_specs.py`）

把「词典规则」拆成三个正交开关——**D**（44 个 `'IGNORE'` 键：丢弃 vs 计为维度）、**F**（未映射标签：兜底计入 vs 丢弃）、**S**（键 `strip()` 与否）——再乘上 **T**（0 / 0.15–0.45 七档），逐一重算索引与回归：

| 规格（t = 0.30） | N | mean(H) | SD | β₁ | β₂ | 拐点 | R² |
|---|---|---|---|---|---|---|---|
| 论文 Table 1 / Table 9(t=0.30) | 17,670 | 10.35 | 4.14 | +0.0761 | −0.0145 | 11.96 | 0.1622 |
| **D1F1 当前管线**（IGNORE 丢弃 + 兜底保留） | 17,578 | 8.02 | 4.05 | +0.0365 | −0.0110 | 9.68 | 0.1217 |
| D2F1（IGNORE **计为维度** + 兜底保留） | 17,686 | 10.26 | 4.62 | +0.0493 | −0.0063 | 14.15 | 0.1301 |
| D1F0（IGNORE 丢弃 + 仅词典类别） | 17,512 | 5.55 | 2.53 | +0.0739 | −0.0144 | 8.12 | 0.1197 |
| D2F0（IGNORE 计为维度 + 仅词典类别） | 17,675 | 7.79 | 3.21 | +0.0935 | −0.0037 | 20.41 | 0.1374 |
| D1F1 @ **无阈值**（= 管线主模型） | 17,670 | **9.3247** | 3.6756 | **+0.0761** | **−0.0145** | **11.96** | **0.1622** |

三条结论：

1. **回归层没有分歧**：论文 t=0.30 行的 5 个数字与管线**不加阈值**的主模型**逐位相同**（含 R² 0.1622 与 N 17,670）。⇒ 论文的"0.30 阈值口径"就是管线的不加阈值口径，**0.3 阈值在两边都没有咬合**。
2. **词典层最大的单一杠杆是 `'IGNORE'`**：把它计入维度，t=0.30 处均值 **8.02 → 10.26**（+2.24），无条件口径 9.32 → 12.21。每款游戏被整类丢弃的不同 IGNORE 标签数均值 = **2.889**（`Multiplayer`、`Singleplayer`、`Indie`、`Free to Play`、`Gore`、`Great Soundtrack`、`Controller` 等极常见标签）。
3. **但兜底规则是对的**：改成"仅词典类别"使均值降到 5.55／7.79，**方向与论文相反** ⇒ 论文确实把未映射标签也计为维度，当前管线保留兜底的做法与论文一致。`strip()` 的影响仅 **−0.010** 个维度，可忽略（但属必修的正确性问题）。

#### 7.2.2 ⚠️ 论文自身数字的算术不自洽 `[实]`

二次型 `y = a + β₁(H−c) + β₂(H−c)²` 的顶点在 `c − β₁/(2β₂)`。论文报出 β₁、β₂ 与拐点后即可**反解它实际使用的中心化常数 c**：

| t | 论文报的 mean | β₁ | β₂ | 论文拐点 | 反解 mean = 拐点 − 偏移 | 论文 mean − 反解 mean |
|---|---|---|---|---|---|---|
| 0.15 | 11.25 | +0.0923 | −0.0171 | 13.12 | **10.4212** | +0.8288 |
| 0.25 | 10.62 | +0.0822 | −0.0151 | 12.57 | **9.8481** | +0.7719 |
| **0.30** | **10.35** | **+0.0761** | **−0.0145** | **11.96** | **9.3359** | **+1.0141** |
| 0.35 | 10.03 | +0.0723 | −0.0138 | 11.52 | **8.9004** | +1.1296 |
| 0.45 | 9.32 | +0.0679 | −0.0119 | 10.45 | **7.5971** | +1.7229 |

- 七档**全部不自洽**，差值由 +0.68 单调扩大到 +1.72 ⇒ **不是单点笔误**，而是均值列与回归用了不同的口径或不同的样本；
- 反解出的 t=0.30 均值为 **9.3359**，与管线主模型的 **9.3331** 相差 0.003 ⇒ **管线算出的正是论文回归实际使用的那条索引**；
- 旁证：论文 Table 1 报 median = 10.0，管线口径的 median **恰为 10.0**；但没有任何口径能同时命中论文的 mean 10.35 与 SD 4.14。

**动作**：① **先锁定唯一主口径**（建议全量路径 + 主模型）并在论文中显式声明；② 做一次**字典粒度敏感性**（细粒度版 vs 当前粗粒度版），检验 β₂ 符号与拐点区间；③ 报告 `Hybridization_Index` 与"原始标签去重数"的相关性，量化降维的信息损失；④ **把 `'IGNORE'` 的两个动作解耦**——"不计为维度"与"据此删样本"目前是同一个动作，后者是稳健 4 中 N 由 17,686 掉到 17,488 的伪迹根源（`threshold_03_report.md`）；⑤ 向论文作者确认 10.35 的口径，**在澄清前不要为凑这个数去改词典**。

#### 7.2.3 这个结论意味着什么

**(a) 精确定性：这是"单列不一致"，不是"两套口径"。** 论文 t=0.30 行共 6 列，其中 **5 列（N、β₁、β₂、拐点、R²）与管线逐位相同**，只有 **mean 一列不同**——而 mean 恰好是这张表里**唯一的纯描述统计列**（其余五列都是模型输出）。等价说法：论文的全套数字等价于"管线索引**整体平移 +1.03**"，唯独拐点列没有跟着平移。因此需要修正的是 **`{mean, 拐点}` 二者之一**：要么 mean 应为 ≈9.34，要么拐点应为 ≈12.98。4 个模型输出对一个描述统计，证据强烈指向 **mean 列**。

**(b) 对研究结论的意味：可信度上升，而不是下降。**
- 论文的主模型与管线主模型**是同一个模型**（五个数字逐位相同）⇒ 倒 U 型结论获得了**独立复现**，不再是"两个都说有倒 U 但数字对不上"；
- 实践结论"最优杂交度约 **10–12 个元标签维度**"（拐点 11.96）**不受影响**——它是从匹配上的那 5 列推出来的；
- 因此本文档 §0 第 7 条的"四处硬冲突"**被高估了**：真正需要改代码的只有 ① 标准误类型（`cov_type="HC3"`，一行）；② 是论文侧报数问题；③④ 是文字与实现的表述问题。

**(c) 它对优先级清单的意味：唯一阻塞项消失。**
原先 P0 的第一条是"先锁定唯一口径并重算全部表格"——这是一个需要重跑全部分析的阻塞项。现在它分解为：一次**一行代码的修改**（HC3）+ **一个需要提问的问题**（10.35 出自哪里），两者都不阻塞写作。`'IGNORE'` 解耦降为 P1 方法学清理项，而非 P0。

**(d) 它不意味着什么（三条防线）。**
- **不等于论文的实质结论有问题**：倒 U、过度杂交惩罚、价格信号都完整保留；
- **不等于 10.35 一定是错的**：严格说是 `{mean, 拐点}` 必有一错，只是证据一边倒。若最终确认 mean 无误，则要改的是**拐点列与全部"最优约 12 维"的表述**（会变成约 13 维）——这是两种结局中代价更大的那一种，也是必须先问的原因；
- **不等于 `'IGNORE'` 可以不管**：44 个键、每款游戏 2.889 个维度、以及它造成的稳健 4 的 N 伪迹（17,686 → 17,488）都是独立存在的问题。它只是**不需要**被用来凑 10.35。

**(e) 一个可迁移的方法学收获。** 本轮真正起作用的是一个**便宜且通用的自洽性审计**：任何报告二次型 `y = a + β₁(H−c) + β₂(H−c)²` 与拐点的研究，都可用 `拐点 = c − β₁/(2β₂)` 反解出它实际使用的中心化常数 `c`，并与它自己报告的均值比对——**这项检验与计算方法无关**（顶点公式、网格搜索、预测曲线给出的顶点必然相同）。本篇七档全部不通过。同理，"阈值稳健性表"在两侧都**没有真正变动它声称要变动的量**（0.3 删 0 行；论文 0.30 行 = 无阈值模型），也是一条通用的评审启发式：**先验证一张敏感性分析表是否真的在变它声称要变的参数**。

**(f) 风险提示。** 若论文正文报 10.35 而随附代码产出 9.32，答辩时必然被追问，且无法解释——因为两者不能同时成立。因此**该问题必须在定稿前落地为一种表述**：推荐正文采用管线可复现值（并注明"论文 Table 1/4/9 报告的均值与本管线复现值相差约 1.03 个维度，疑为均值列口径不同，已记录"），或按作者澄清后的口径统一重算。

#### 7.2.4 论文**全部描述性表格**的自洽性审计 `[实]`（`06_tools/check_paper_tables.py`）

对 Table 1、3、4、5、6–9、10 与 §4.1 逐年逐列复核后，论文的数字可以**干净地分成三类**：

| 类别 | 项目 | 证据 |
|---|---|---|
| **① 与管线逐位相同**（同一套代码） | Table 3 三个 VIF；Table 5 的 N / R² / Peak / 各系数；Y_2016 = −0.0449；Table 6–9 的 N 与**全部四个拐点**（11.33 / 11.92 / 11.80 / 11.96）；Table 10 八个簇规模（2,181 / 2,163 / 1,741 / 1,341 / 2,478 / 2,620 / 1,977 / 3,185）`[注]` **限原始运行**，见 §7.6 第 7 条 | VIF 吻合到 **6 位小数**；Table 10 合计 **17,686** = 管线全样本，差额 16 = 管线 H=0 的样本数 |
| **② 与管线不同，且论文侧无法自洽** | Table 1/4 的指数 Mean 10.35 与 SD 4.14；Table 4 的 Total Reviews 均值差 2.00 / SD 差 10.59 | 见下 |
| **③ 论文内部互相矛盾** | Table 1 的 median（10.0）vs Table 4 的 median（11.00）；§4.1 的 N / 计数 / 百分比三者两两不相容 | 见下 |

**(1) 最有力的一条新证据：Table 3 的 VIF 逐位相同。** VIF 是**设计矩阵的函数**（只取决于 `Hc`、`Hc²`、`price` 三列的联合分布，与因变量无关）。两者吻合到 6 位小数（1.134942 / 1.306966 / 1.239591），意味着论文回归所用的自变量矩阵与管线**逐元素一致**——这与"论文的指数分布是 10.35/4.14"在数学上不能同时成立。

**(2) 端点把仿射映射钉死为恒等。** 论文报 Min = 0、Max = 20。而**管线回归样本（17,670）的 Min = 1**，只有**全样本（17,686）**的支撑才是 [0, 20] ⇒ **论文描述统计表的 Min 来自 17,686，却标注 N = 17,670（口径混用）**。在 0–20 的支撑上，任何保留两端点的正斜率仿射映射只能是**恒等映射** ⇒ 论文的均值必须是 **9.3247**、中位数 10.0、SD 3.6756。用论文自己的 (mean, median, SD) 两两反解再验证第三个，**三组全部失败**。

**(3) 六个量里四个指向 c = 0。** Min、Max、Table 1 的 Median、拐点 Peak 都指向"平移量为 0"，**只有 Mean 指向 +1.03**；SD 在任何线性变换下都无法与均值/中位数同时成立。

**(3b) 封闭性：任何子样本都产生不出 10.35。** 17,686 款的杂交度总和 = **164,916**（16 款 H=0 贡献为 0，故与 17,670 回归样本的总和相同）。对任意子样本 `mean_S ≤ 164,916/|S|`：样本量 17,670 → 上界 **9.333**；17,633 → 上界 **9.353**。要得到均值 10.35，样本量必须 **≤ 15,934**（即删掉至少 1,752 款低杂交度游戏）——与论文任何一处标注的样本量都不符。⇒ **10.35 既不能靠换仿射口径、也不能靠删样本得到**；结合 (1) 的 VIF 证据（回归用的正是这套指数），只剩两种解释：**该描述统计来自另一版维度数更多的索引，或该列本身算错了。**

**(4) 第三条独立证据：截距恒等式。** `a = ȳ − β₁·mean(Hc) − β₂·mean(Hc²) − β₃·p̄ − Σγ·mean(Year)`。管线侧该恒等式精确成立（左右端均 6.4898）。代入**论文 Table 4 自己的数字**（ȳ = 6.40、SD² = 4.14²、p̄ = 11.60）预测截距为 **6.5445**，而论文 Table 5 实报 **6.3754**（差 −0.169）；改用管线的 SD = 3.6756 则立刻吻合。⇒ **论文的截距与它自己的指数 SD 不相容。**

**(5) Table 9 的系数列是对的。** 七档的 `t = coef/SE` 全部内部自洽（β₁ 的 t 在 +21.2 ~ +29.8，β₂ 在 −17.0 ~ −24.4，与 `***` 相符）⇒ 出问题的**只是 mean 列**，不是系数与标准误。

**(6) §4.1 年份分布：三个数两两不相容。** 论文的**百分比**与管线全样本（17,686）基本一致（2024 = 12.04% 对 12.04%、2020 = 10.75% 对 10.75% **完全相同**），但**计数**逐年少 6–9 款；用论文自己的 (计数, 百分比) 反解出的分母是 **17,628–17,641**（≈17,633），与它声明的 **17,670**、管线的 **17,686** 都不相等。

**⇒ 结论与做法**：论文的**回归输出**（系数、标准误、R²、拐点、样本量、聚类划分、VIF）与管线**高度一致，多处逐位相同**；出现问题的**全部集中在描述统计**。最可能的情形是：**描述统计表（Table 1/4）与 §4.1 是在另一个数据框或另一个中间变量上生成的**，而回归表用的是与管线相同的那份数据。因此：

- 正文的**推断性结论完全可用**（倒 U、拐点 11.96、价格效应、聚类画像）——它们全部建立在与管线一致的那批数字上；
- **描述性表格必须自行计算并替换**，不要转引论文 Table 1/4 与 §4.1 的年份分布（2024 应以管线为准 = **2,129**，而非 2,123）；同时留意 2025 年仅 308 款，需检查年度固定效应的稳定性；
- 建议保留一条脚注说明差异，并向作者确认描述统计的数据来源。

### 7.3 覆盖度缺陷：字典漏网标签（**已量化，可直接修复**）

`[实]` **逐项核实结果**：

| 指标 | 数值 |
|---|---|
| 全部「元标签计数」总数 | **164,916** |
| 属于 META_DICT 类别 | **111,990（67.91%）** |
| 属兜底原标签 | **52,926（32.09%）** |
| 不同兜底标签种类 | **166 个** |
| `Meta_Tags` 不同取值总数 | **192 个**（类别 26 + 兜底 166） |
| 每游戏兜底占比：P25 / 中位数 / P75 / P90 | 16.7% / 30.0% / 40.0% / 50.0% |
| 完全由兜底标签构成的游戏（`H_dict = 0`） | **70 款** |

`[实]` 兜底标签 Top 15（按出现游戏数）：`Atmospheric` 4,424｜`Exploration` 3,180｜`Female Protagonist` 2,489｜`Colorful` 2,450｜`Difficult` 1,913｜`Arcade` 1,756｜`Violent` 1,562｜`Stylized` 1,327｜`Character Customization` 1,270｜`Combat` 1,199｜`Physics` 1,106｜`Tactical` 1,010｜`Cartoony` 1,003｜`Side Scroller` 934｜`Turn-Based` 917。

`[实]` 典型个案（可作论文例证）：`Stardew Valley` 的 9 个元标签含 `Fishing`；`ARK: Survival Evolved` 含 `Dinosaurs`；`OMORI` 含 `RPGMaker`、`Turn-Based`、`Colorful`；`Cat Goes Fishing` 含 `Cats`、`Difficult`、`Arcade`、`Fishing`。

`[推]` 两个方向的偏差：
- **虚增**：语义同类却一个被映射、一个未映射，被计成两个维度（`Turn-Based` 与 `Turn-Based Combat` 并存）；
- **语义污染**：`RPGMaker`（引擎）、`Female Protagonist`（叙事特征）、`Atmospheric`（氛围评价）与 `Action`、`Simulation`（设计类别）**不同层**，却同权计入"维度数"。

`[实]` **关键稳健性检验（结论未被推翻）**：改用「仅字典口径」`H_dict`（均值 6.357，范围 0–14）重估主模型：
N = 17,616，R² = 0.1589，β₁ = **+0.15164** (t=30.65)、β₂ = **−0.01653** (t=−10.66)，拐点 **10.94** ⇒ **倒 U 依然成立**。
`[实]` 把 `H_fall`（兜底个数）作为额外控制加入：β₁ = +0.1182、β₂ = **−0.0124** (t=−17.36)、`H_fall` = −0.0835 (t=−9.79)，R² = 0.1673，拐点 **14.12** ⇒ 二次项幸存，但**兜底标签本身与商业表现负相关**，说明它并非纯噪声。
`[推]` 结论：**核心发现不依赖兜底标签，但论文"清洗后"的表述必须修正**，且应报告上述两组稳健性。

**动作**（最低成本、最高收益）：① 从 `Meta_Tags` 词表（而非 `all_tags.txt`）反推完整标签清单——`all_tags.txt` 只含 448 个阈值路径标签，会**系统性漏掉长尾**（实测 `Cartoony`、`Emotional`、`Female Protagonist` 出现在事实表却不在该清单）；② 逐个判定"归入类别 / IGNORE / 独立语境类（不计入杂交度）"；③ 重跑并报告修补前后的分布与系数变化。

### 7.4 统计推断缺陷

`[实]` DW = 0.343、JB 显著（峰度 4.33、偏度 0.96）、BP/White 拒绝同方差（论文侧数值）。
`[推]` 应对：
1. **稳健标准误**：论文已用 HC3；notebook 需补齐。若存在组内相关，进一步用 `cov_type="cluster"` 按 `Game_Cluster` 或发行商聚类；
2. **函数形式**：因变量已是 log，可检验 `log1p` vs `log`（剔除 0 评论样本）；考虑 Poisson/Negative Binomial 计数模型作为替代；
3. **非线性形式**：把二次项与**分段线性（spline）**、**分箱均值图**（§4.4c 已做）并列，避免倒 U 完全依赖二次设定；
4. **多重共线**：中心化后 VIF 已达标（与论文完全一致：1.1349/1.3070/1.2396），但应在新模型（含簇 FE）下重算。

### 7.5 内生性与因果解释

`[推]` 三处：
- **反向因果**：成功的游戏吸引更多玩家打标签 ⇒ 标签更丰富 ⇒ 杂交度上升。横截面设计无法排除；
- **遗漏变量**：营销预算、发行商资源、IP 知名度、美术品质、Steam 推荐位均未观测（`average_playtime_forever`、`achievements`、`dlc_count`、`peak_ccu` 已用作部分代理，§4.4e 已证其重要性；`metacritic_score` 因独立游戏缺失严重**读入但未使用**，是可直接补的缺口）；
- **选择偏差**：样本框要求 `Total_Reviews ≥ 100` 且 `tags_counts` 非空 ⇒ 被截断的是"完全失败的游戏"，可能使下降段被低估。

**动作**：① 加入质量代理后重估（已做；price 在含同源热度代理 `peak_ccu` 的规格中归零、剔除后仍有基准的 55%，详见 §4.4e）；② 用好评率作第二因变量（已做）；③ 做 **Oster (2019) / Altonji 型系数稳定性检验**量化遗漏变量偏误边界；④ 论文已在 §7.3.1 明确声明横截面限制 ⇒ 写作时保留同样克制的表述。

### 7.6 工程与可复现性缺陷

`[实]`：
1. **注释与代码不符**：notebook 标题与 §4 标题声称 TF-IDF 聚类，实现是 priority + KMeans；`TfidfVectorizer`/`silhouette_score` 为死导入；
2. **死参数/死变量**：`MIN_TAG_DOC_FREQ`、`TAG_SOURCE_COL`、`FOCUS_CLUSTERS`、`in_focus_cluster`、`Game_Age`、`map_to_metatags()`、`to_metatags()`（与 `map_to_metatags` 重复）；
3. **执行顺序耦合**：`build_meta_fields`/`fit_priority_cluster` 在第 4 节定义、第 6 节调用，`cluster_top_tags` 通过 `global` 传递；
4. **结果不落盘**：所有回归结果只有 `print`，无 `results_summary.csv` 或回归表；
5. **文件版本混杂**：4 个语言脚本并列无版本说明，其中 `lang_group_analysis.py` 整体是字符串不是可执行脚本；
6. **跨脚本相对路径**：语言脚本依赖同目录下的两个 CSV（本次整理已同步更新为 `01_data/`）。
7. **⚠️ 聚类结果**不可跨环境复现**（2026-09-30 新发现，且推翻了 §7.2.4 类别① 的一条证据）**：
   本次把 C1–C5 修正后的 notebook **真正执行了一遍**（历史上首次在本环境跑通），
   生成的导出表 `Hybridization_Index` 均值由 9.3247 变为 **9.3145**（C2 生效，符合预期），
   **但 `Game_Cluster` 的八个簇规模由 `[2181, 2163, 1741, 1341, 2478, 2620, 1977, 3185]`
   变为 `[2060, 3238, 2462, 1605, 2880, 1542, 1232, 2667]`**。
   输入数据、`random_state=42`、`K=8` 都未变，差异只能来自 **scikit-learn 的 KMeans 实现/默认值**
   （`n_init="auto"`）在版本间的变化。而 notebook **没有记录任何库版本**。
   `[推]` ⇒ **"Table 10 八个簇规模与论文逐位相同"这一条证据只对原始运行环境成立**，
   在新环境下无法复现；这本身是一条重要的可复现性缺陷，也说明论文的聚类**必须固定环境才能复现**。
   **影响范围**：聚类**只用于描述**（论文 Table 10、簇画像），**从未进入任何回归**，
   因此不影响 §4 的全部结论；但 §7.2.4 类别① 中"Table 10 逐位相同"应改述为
   "**在原始运行环境下逐位相同**"。
   **处置**：原始运行的产物已归档至 `05_archive/pre_c2_regeneration_backup/`；
   新导出表为当前主口径（C2 一致）。修复动作见下方第 ③ 条。**

**动作**：① 拆分 notebook 为 `src/` 模块（cleaning / metatag / clustering / variables / models / export），notebook 只做编排；② 固定随机种子并输出**回归表 + 图 + 参数快照 JSON**；③ **用 `requirements.txt` 固定版本并在导出表中写入版本指纹**（本次已证实：不固定 sklearn 版本，连同一份数据都得不到同一套簇）；④ 统一注释与实现；⑤ 用 `pathlib` + 配置常量替代硬编码相对路径；⑥ **把 `Game_Cluster` 的赋值落盘为独立文件**（`cluster_assignment.csv`），使下游分析不再依赖重跑聚类。

### 7.7 改进优先级总表（经 §7.2 量化后**重新定级**）

> 定级依据：§7.2.2–7.2.4 已证明论文的**回归输出**与管线逐位相同，原来的"四处硬冲突"只剩 ① 是真正的代码分歧。因此旧的 P0 第一条（"锁定口径、重算全部表格"）**已取消**——它建立在一个并不存在的冲突之上。

> **执行状态（2026-09-30）**：P0 四项**已全部完成**——C1（HC3）、C2（`strip()`）、C3（稳健 4 固定样本）、C4（结果落盘）均已写入主管线 notebook，
> 结果表见 `02_pipeline/results/`，逐条改动与数值影响见 [CHANGELOG_corrections.md](06_tools/CHANGELOG_corrections.md)。
> P1 第 5 项（`strip()` + 死键）随 C2 完成（`Dystopian` 死键已修复，其余 6 个仍待清理）。
> **P1 第 6 项（披露 IGNORE 处理）与第 7 项（簇固定效应）、P2/P3 各项均未执行。**
> 下表中 ✅ 标记为已完成。

| 优先级 | 改进项 | 预期收益 | 成本 | 涉及章节 |
|---|---|---|---|---|
| **P0** | ✅ **已做（C1）** 主模型与全部稳健性改用 **`cov_type="HC3"`**（§5.4-1） | 与论文口径一致；price 的 SE 0.0009 → 0.0016（t 41.68 → 23.23），系数不变；HC3 列与论文 Table 5 三个斜率 SE 吻合到 4 位小数 | 极低（1 行 → 5 处） | Results |
| **P0** | ✅ **已做（C4）** **描述统计与年份分布一律自行计算并替换**，不转引论文 Table 1/4 与 §4.1（§7.2.4） | 消除目前**唯一**实质性的数字分歧；自算值见 `02_pipeline/results/` | 低 | Results |
| **P0** | ✅ **已做（C4）** **回归结果落盘**为标准回归表（CSV/Markdown） | 三份 CSV + 汇总 Markdown 已生成 | 低 | 全文 |
| **P0** | ✅ **已做（C3）** **把 `'IGNORE'` 的两个动作解耦**："不计为语义维度"与"据此删样本"（§4.3.1） | 稳健 4 的 N 由 17,639→17,488 的伪迹已消除，各档恒为 **17,670** | 低 | 稳健性 |
| **P1** | ◐ **部分已做（C2）** 标签键 `strip()` 归一化 + 清理 7 个死键（§7.3） | `'Dystopian '`/`'Parody '` 漏映射已修（179 款受影响，mean(H) −0.010）；`Dystopian` 死键随之修复，其余 6 个仍为死键待清理 | 极低 | Methodology |
| **P1** | 在论文中**披露** `'IGNORE'` 的处理：44 个键、每款游戏平均 **2.889** 个被丢弃维度 | 构念效度的必要披露；这是审稿人一定会问的点 | 极低（写作） | Methodology |
| **P1** | 回归加入**簇/题材固定效应**并写入正文（§7.1） | 排除题材构成这一最强竞争解释（已验证 β₁=+0.0773、峰值 12.07、结论不变） | 低 | Results |
| **P1** | 报告"仅字典口径"稳健性（§7.3） | 把 32.09% 兜底占比这一测量风险转化为可信度证据（已验证峰值 10.94，倒 U 仍成立） | 低 | 稳健性 |
| **P1** | 分簇异质性 + 分箱均值 + 好评率 + 质量代理写入正文；质量代理**须同时报告**含/不含 `peak_ccu` 两个规格（§4.4b/c/d/e） | 结论边界更诚实、机制证据更强 | 低 | Results/Discussion |
| **P2** | 补齐 META_DICT 漏网标签（168 个，占元标签计数 32.09%）并重跑 | 提升构念纯度；**注意这是构念改进，不是为了对齐论文的 10.35** | 中–高（需人工判定词表） | Methodology |
| **P2** | 字典粒度敏感性；样条/计数模型对照（§7.2、§7.4） | 稳健性全面升级 | 中 | 附录 |
| **P2** | 复现论文 Table 2 的轮廓系数 / 聚类稳定性证据 | 补上聚类的方法论正当性（工作区目前完全没有） | 中 | Methodology |
| **P2** | 语言支线补输出；`lang_group_analysis.py` 修成可执行脚本或删除（§4.6、§7.6） | 形成可引用的延伸结论；消除"4 版并列且其中 1 版不是代码"的混乱 | 低–中 | 延伸章节 |
| **P3** | 重构为 `src/` 模块 + 配置化路径 + `requirements.txt` 固定版本（§7.6） | 长期可维护 | 中–高 | 工程 |
| **P3** | 真正实现 TF-IDF 版聚类并与 priority 版对照 | 方法学贡献 | 中 | 方法附录 |
| **问** | **需向作者确认（非代码改动）**：① 10.35 出自哪个数据框/变量；② Table 4 的指数 median 是 10.00 还是 11.00（PDF 提取有歧义，需核对原页）；③ §4.1 年份百分比的分母 | 决定描述统计该引哪个数；不影响推断性结论 | 低 | — |
| **✗** | **明确不要做**：① 为凑 10.35 去改 `META_DICT`/放开 `IGNORE`（会把拐点推到 14.15、β₁ 压到 +0.0493，离论文更远）；② 改兜底（fall-through）规则（已验证方向与论文一致）；③ 改拐点 11.96 及相关结论；④ 动聚类（与论文逐位相同） | 避免为拟合一个内部矛盾的目标而系统性扭曲索引 | — | — |

---

## §8 后续工作清单与操作手册

### 8.1 现在需要修改的部分（按执行顺序）

> 经 §7.2 量化后，原先"先锁定口径、重算全部表格"这一 P0 阻塞项**已取消**。下面的顺序是按"改动量 ÷ 风险消除量"排的。
> **状态（2026-09-30）：第 1、2 步与第 3 步的第 8 项已完成；其余未执行。** 详情见 [CHANGELOG_corrections.md](06_tools/CHANGELOG_corrections.md)。

**第 0 步 · 先问、别先改（半天，可并行）** ⏳ **待办**

1. 向作者确认三件事：① 论文 Table 1/4/9 的 **10.35** 是在哪个数据框、哪个变量上算的；② Table 4 的指数 **median 是 10.00 还是 11.00**（两个提取器的结果不一致，需核对 PDF 原页）；③ §4.1 年份百分比的分母。
   → 在①澄清前，**不要为凑 10.35 动任何词典代码**（§7.2.3d）。（临时做法：按第 2 步用管线自算值并加脚注。）

**第 1 步 · 三个"一行级"改动（1 小时）** ✅ **已完成**

2. ✅ 主模型与全部稳健性改 `cov_type="HC3"`（**C1**，共 5 处 `.fit()`）。核对结果：price 的 HC3 SE = **0.00164**（与论文 0.0016 一致），系数完全不变。
3. ✅ 对 `tags` 的键做 `strip()` 归一化（**C2**，字典键与标签键两侧同时处理）。7 个死键中 `Dystopian` 已随之修复，其余 6 个仍待清理。
4. ✅ **把 `'IGNORE'` 的两个动作解耦**（**C3**）：稳健 4 改为固定样本、只变索引定义。改后各档 N 恒为 **17,670**（原为 17,639→17,488）。

**第 2 步 · 描述性数字全部自算替换（半天）** ✅ **已完成**

5. ✅ 已重做 **Table 1 / Table 4 / §4.1**：指数 mean = **9.3145**（全样本 17,686）／9.3230（回归样本）、SD = **3.6682**、median = 10.0、min 0、max 20；年份分布以管线为准（**2024 = 2,129**）。输出见 `02_pipeline/results/`。
   `[注]` 数值与修正前（9.3247 / 3.6756）略有差异，因 C2 的 `strip()` 生效。
6. ✅ Table 3（VIF）、Table 5 的系数与 R²、Table 6–9 的 N 与拐点、Table 10 的簇规模确认可以直接沿用——它们与管线逐位相同（§7.2.4 类别①）。
   `[注]` 但 R² 与拐点因 C2 微调：R² 0.1622 → **0.1623**、拐点 11.96 → **11.93**。
7. ⏳ 脚注文案已备好（见 CHANGELOG 文末"修正后必须替换的论文数字"），待写入论文。

**第 3 步 · 结果落盘 + 方法学补充（1–2 天）**

8. ✅ 已落盘：`02_pipeline/results/`（**C4**，notebook 内新增 unit + `rebuild_results.py` 独立复核）。
9. ⏳ 主模型加入**簇固定效应**并写入正文（已验证 β₁ = +0.0773、β₂ = −0.0141、峰值 12.07、R² 0.1752，结论不变）。
10. ⏳ 报告"仅字典口径"稳健性 + 披露 `'IGNORE'` 处理（44 键 / **2.889** 维度/款）与 32.09% 兜底占比。

**第 4 步 · 清理（可延后）** ⏳ **待办**

11. 删除/改造死参数与死导入：`MIN_TAG_DOC_FREQ`、`FOCUS_CLUSTERS`（`in_focus_cluster` 恒为 1）、`Game_Age`、`map_to_metatags()`、`to_metatags()`、`TfidfVectorizer`、`silhouette_score`；修正 notebook 中"TF-IDF 聚类"的错误表述。
12. 修或删 `04_language_extension/lang_group_analysis.py`（内容是字符串字面量，不可执行）。
13. 清理 `META_DICT` 中剩余 6 个死键（`Adult`、`Base Building`、`Dating`、`Eroge`、`Hentai(Nudity)`、`Visual Novel (Adult)`）。

### 8.2 复现步骤（在新环境中）

```text
1. 准备环境：Python 3.12 + pandas / numpy / scikit-learn / statsmodels / matplotlib / seaborn
   （建议写 requirements.txt 固定版本）
2. 放置数据：01_data/raw/steam_games_march2025_updated.csv
3. 运行主管线：02_pipeline/4dissertation_gamespace_clustering_new.ipynb（自上而下全部运行）
   - 注意：META_DICT 必须在 build_meta_fields() 调用之前定义（notebook 已按此顺序，勿拆乱）
   - 产出：01_data/processed/ 下 3 个 CSV + all_tags.txt；02_pipeline/figures/ 下 2 张图
4. 运行语言支线：04_language_extension/lang_group_analysis.py（或 lang_analysis3.py）
5. 运行核查：06_tools/verify_all.py 等，比对 verify_report.md
6. 核对关键数字：N=17,670、R²=0.1622、β₁=+0.0761、β₂=−0.0145、拐点=11.96、VIF=1.1349/1.3070/1.2396
```

### 8.3 写作时的引用纪律（避免踩坑）

1. 凡引用拐点，必须写清**口径**："在全量标签、元标签维度计数的定义下，最优点约 12 个维度（主模型 11.96）"；
2. 凡引用年份 FE 系数，必须说明其**主要是曝光时长效应**，不得表述为"市场逐年恶化"；
3. 凡引用价格效应，必须加**相关性而非因果**的限定，并说明免费游戏（13.27%）的处理方式；若已加入质量代理，应同时报告"含 `peak_ccu` 时归零、剔除后仍有 +0.0210 (t=16.8)"两个数字，**不得只引用前者**；
4. 凡引用聚类画像，注明**质心标签与 Cohen's h 是两套口径**（附录列的 `defining_meta_tags` 实际是质心 Top5）；
5. 凡引用论文的**描述统计**（指数 mean 10.35 / SD 4.14、Table 4 的 median、§4.1 的年份计数与占比），**一律不要转引**——按 §7.2.4 自行计算后用管线值，并加脚注说明差异；论文的**推断性数字**（Table 5 系数、R²、四个拐点、Table 10 簇规模、Table 3 VIF）可以直接引用，它们与管线逐位相同；
6. 引用"最优约 12 个维度"时，**必须与 `peak = 11.96` 绑定说明**；不要在正文里写"论文报告均值 10.35"，除非同时说明它与其自身的 β₁/β₂/拐点在算术上不能同时成立（§7.2.2）；
7. 所有数字必须可溯源到 `01_data/processed/` 的 CSV 或 `06_tools/*.md` 报告，**不得引用控制台截图的数字**。

---

## §9 研究扩展：从「维度计数」到「空间离散度」（`07_extension/`）

> 完整报告：[`07_extension/results/consolidated.md`](07_extension/results/consolidated.md)；
> 文献基础：[`03_literature/lit_review_extension.md`](03_literature/lit_review_extension.md)。

### 9.1 动机 `[实]`

三条独立理由推动把被解释构念从"数了几个维度"改为"所跨维度有多远"：

1. **理论**：类别跨越的后果取决于被跨越类别的**距离**而非**数量**（Kovács & Hannan 2015, *Sociological Science* 2:252–286）；
2. **测量** `[实]`：原始标签列表在 **20 处硬截断**（54.78% 顶格），计数型指数在数据层即被封顶；
3. **论文自身的否定是可反驳的** `[实]`：论文以"Jaccard + 谱聚类、轮廓系数 ≤ 0"否定共现路线，
   但该文献中经典的跨越距离测度**本身就是 Jaccard 的**（Kovács & Hannan Eq. 11），
   问题出在**聚类/效度检验步骤**，不在 Jaccard 或数据。

### 9.2 方法链

```
原始标签 → NPMI 共现图（405 节点 / 19,122 边）
        → Louvain 共识划分（100 次运行 + 平均连接 + 集合一致性选 K）→ K = 7 个语义标签域
        → 域间 Jaccard 距离（承载游戏集合） + 对称 NPMI 的谱嵌入
        → 逐游戏测度：coherence（HHI） / spanning（域级，相异对归一化） / tag_spanning（标签级，无划分依赖）
        → OLS（HC3 + 年份 FE + price）→ 两个因变量：关注度与评价
```

### 9.3 核心结果 `[实]`

| 关系 | 关注度 `Log_Reviews` | 评价 `pct_pos_total` | 文献（Wang & Lyu 2026） |
|---|---|---|---|
| `coherence` ↑ | **+1.1397\*\*\*** (t=+12.1) | **+10.2621\*\*\*** (t=+11.3) | 票数 +1.207\*\*\*、评分 +1.089\*\*\* ✅ **同向** |
| `tag_spanning` ↑ | **−0.5128\*\*\*** (t=−7.3) | **−13.7313\*\*\*** (t=−16.8) | 票数 −0.557\*\*\*、评分 **+0.477\*\*\*** ⚠️ **评价反向** |
| 域级 `spanning`（既有指数控制后） | t = −0.1（正交化） | t = +0.7（正交化） | **无增量** |

`[推]` **与电影市场分歧的解释**：Ahn, Vergne & Sharkey (2026, *SMJ* 47(7):1907–1934) 的元分析发现平均效应为零，
并识别出三个加重惩罚的条件——**有界类别体系 / 第三方主张 / 产品层测量**——本设定**三条全部命中**。
⇒ 本项目的"两处皆负"是元分析条件预测下的应有结果，而非与文献矛盾。

`[实]` **分辨率稳健性通过**：四个分辨率（K = 5 / 7 / 14 / 14）下全部组合同号。
并发现 **`tag_spanning` 因定义于嵌入空间、不使用社区划分，对分辨率完全免疫**，
而依赖划分的 `spanning` 在 res=1.5 后 t 值由 −12.2 衰减到 −1.4
⇒ **主口径应取无划分依赖的 `tag_spanning`**。

### 9.4 对既有结论的影响

- **不影响**主模型（§4.2）的倒 U 与拐点 11.93——那是计数口径下的结论，仍然成立；
- **补充**了一个正交于计数的构念：`spanning` 与原始标签数相关 **+0.000**，但与既有元标签指数的相关仅 +0.043；
- **新增一个负面发现**：G3 的**市场成熟度调节未获支持**——拐点随密度仅由 11.92 移到 12.23（0.31 个维度）。

### 9.5 与最直接先例（Li & Zhang 2020）的差异 `[实]`

全文（由用户在 `08_ref_txt/` 提供）核实后，本文相对该先例有**五项**方法增量：

| 环节 | Li & Zhang (2020) | 本项目 | 增量性质 |
|---|---|---|---|
| 枢纽标签 | **删除** 5 个枢纽 + 15 个孤儿（306 节点 / 1,813 边） | **NPMI 加权**，保留全部 405 节点 | 消除"删哪些"的研究者自由度 |
| 随机性 | Gephi ">100 rounds"，取**最高 Q** | **共识划分**（共分配 + 平均连接） | 取最大值是选择性偏倚 |
| 结构判据 | 与**自身图的变体**比较（Q 0.150 vs 0.414） | 与**同度序列零模型**比较（z = 118.5） | 前者无法排除"随机图也有高 Q" |
| 尺度 | 自陈 Louvain 难发现小社群，**列为未来工作** | **分辨率扫描** K = 5/7/14/14 并检验结论 | 把局限落实为检验 |
| 输出 | 标签社群（4 个类型） | **逐游戏连续跨越测度** + 需求结果 | 从分类到可回归的测量 |

`[注]` 两者的 Q（0.414 vs 0.3329）**不可直接比较**：图规模、边权重（未加权 vs NPMI）、是否删节点均不同。

### 9.6 独立方法学稿件与固定环境

- **方法学稿件**：[`07_extension/METHOD_PAPER.md`](07_extension/METHOD_PAPER.md)——
  《从硬划分到连续距离：Steam 游戏标签的类别跨越测量》。
  整合 §9.1–9.5，按摘要/引言/相关工作/方法/结果/讨论/局限组织，可独立成文。
  其核心论证链：结构存在（零模型 z = 118.5）→ 划分脆弱（种子 ARI 0.635、模块度曲面在 K = 4–14 平坦）
  → 故测度应定义在连续空间（`tag_spanning` 对分辨率**逐位不变**）→ 实质结果是**纯类别跨越惩罚**。
- **固定环境**：`requirements.txt`（10 个包，`scikit-learn==1.9.0` 与 `statsmodels==0.14.6` 为**版本关键**）；
  `06_tools/check_environment.py` 比对并写 `01_data/processed/environment_fingerprint.json`（含产物哈希）。

### 9.7 未做

真面板（需独立采集，协议见 `g3_time.md` §4）、开发者固定效应（覆盖 <7%）、node2vec/文本嵌入。
`[注]` Grelier 线三篇（Games Mapper / Automated clustering / Data-Driven Classifications）
所据为 `08_ref_txt/` 的提取文本，**正式出处（卷/期/页/DOI）待补**。

---

## 附录 A｜变量字典

| 变量 | 类型 | 定义 | 来源 | 备注 |
|---|---|---|---|---|
| `appid` | 整数 | Steam 应用 ID | 原始 | 主键，实测无重复 |
| `Clean_Priority_Tags` | 列表 | priority ≥ 0.3 的原始标签 | `tags` | 仅用于 `all_tags.txt` 与样本非空过滤（实测删除 0 行），**不参与**杂交度 |
| `Meta_Tags` | 列表 | 降维后的元标签（`IGNORE` 已剔除，未覆盖标签原样保留） | `tags` + `META_DICT` | 全量路径；192 个不同取值 |
| `Meta_Tags_Votes` | 字典 | 类别 → 组内最大票数 | 同上 | 中间产物 |
| `Meta_Tags_Priority` | 字典 | 类别 → 票数/该游戏最大票数 | 同上 | **聚类输入** |
| `Game_Cluster` | 整数 0–7 | KMeans(K=8) 簇标签 | 聚类 | 描述性使用；未进入回归 |
| `Hybridization_Index` | 整数 0–20 | `len(Meta_Tags)` | 派生 | 核心自变量；均值 9.3247 |
| `Log_Reviews` | 浮点 | `ln(1+Total_Reviews)` | 派生 | 核心因变量；均值 6.3998 |
| `Hybrid_Centered` | 浮点 | `Hybridization_Index − 9.3246635757` | 派生 | 主模型一次项 |
| `Hybrid_Centered_Squared` | 浮点 | `Hybrid_Centered²` | 派生 | 主模型二次项 |
| `Total_Reviews` | 整数 | `positive + negative` | 派生 | 门槛变量（≥100） |
| `Release_Year` | 整数 | 发行年（2015–2025） | `release_date` | 年份 FE 基础 |
| `price` | 浮点 | 售价（USD） | 原始 | 13.27% 为 0；最大 269.99 |
| `Game_Age` | 整数 | `2025 − Release_Year` | 派生 | **已定义未使用** |
| `in_focus_cluster` | 0/1 | 是否属于焦点簇 | 派生 | **恒为 1（退化）** |
| `age_days` / `age_days_c` | 整数/浮点 | 距 2025-03-10 的天数（及中心化） | 稳健 2 内构造 | 不落盘 |
| `H_dict` / `H_fall` | 整数 | 仅字典类别的维度数 / 兜底标签数 | 核查脚本构造 | 稳健性用，**建议纳入正式管线** |

## 附录 B｜目录结构与整理规则

分类依据：**重要性（T0–T3）× 内容主题 × 使用频次**。

```
01_data/                      # 数据层：只读为主，按"原始/加工"分开
  raw/steam_games_march2025_updated.csv
  processed/games_clustered_meta_export.csv
  processed/cluster_megatag_reference.csv
  processed/cluster_cohens_h_tags.csv
  processed/all_tags.txt
02_pipeline/                  # 生产层：唯一主管线 + 其图形产物
  4dissertation_gamespace_clustering_new.ipynb
  figures/hybridization_curve.png
  figures/dissertation_figures.png
03_literature/                # 参考层：论文与其提取物
  Beyond More Is Better ... .pdf
  paper_digest.md
  paper_clean.txt  paper_text.txt  paper_flat.txt
04_language_extension/        # 支线层：语言支持分析（4 版脚本）
  lang_analysis.py  lang_analysis2.py  lang_analysis3.py  lang_group_analysis.py
05_archive/                   # 归档层：一次性探索脚本
  inspect_raw.py
06_tools/                     # 工具层：核查/提取脚本与报告
  verify_all.py  verify_coverage.py  verify_aux.py  audit_tool.html
  extract_paper.py
  verify_report.md  coverage_report.md  aux_report.md
reference_pipeline_and_paper.md   # 本文档（根目录，最高入口）
README.md                          # 文件索引与使用说明
```

> **路径依赖提醒**：`01_data/**/*.csv` 被 notebook 与四个语言脚本按相对路径读取。移动后必须同步修改 notebook §0 的 `DATA_PATH` 与脚本中的 `pd.read_csv(...)`（**本次整理已同步更新**）。若再次移动目录，请全量 grep `read_csv` 与 `to_csv` 核对。

## 附录 C｜复现与核查清单（Checklist）

- [x] 原始 CSV 行数确认：**89,618**（48 列）`[实]`
- [x] 清洗链路逐步核对：89,618 → 88,618（dropna 剔除 1,000）→ 85,884（年份）→ 17,772（评论≥100）→ **17,686**（剔除 86 款非 Indie 大厂）`[实]`
- [x] 回归样本 N = 17,670（剔除 16 个杂交度为 0 的样本，全部在簇 5）`[实]`
- [x] `Hybrid_Centered`、`Hybrid_Centered_Squared`、`Log_Reviews` 恒等式 100% 通过 `[实]`
- [x] `appid` 无重复（0 个）`[实]`
- [x] 簇规模 Σn = 17,686、Σshare = 100.00% `[实]`
- [x] 主模型系数复现：+0.07606 / −0.01446 / +0.03812，R² = 0.1622 `[实]`
- [x] 拐点复现：11.96 `[实]`
- [x] VIF 复现：1.134942 / 1.306966 / 1.239591（与论文 Table 3 一致）`[实]`
- [x] Cohen's h 表复现：与论文 Table 10 逐值一致 `[实]`
- [x] META_DICT 覆盖度量化：兜底占 32.09%、166 种 `[实]`
- [x] 空白标签污染定位：`'Dystopian '` 1,050 款、`'Parody '` 583 款 `[实]`
- [x] 字典死键定位：7 个 `[实]`
- [x] 论文全文提取：33 页 / 92,427 字符 `[实]`
- [ ] 改用 HC3 稳健标准误重跑全部模型（**待做**）
- [ ] 统一杂交度口径并重算论文 Table 1/4/9（**待做**）
- [ ] 补齐 META_DICT 漏网标签后重跑（**待做**）
- [ ] 聚类固定效应写入正文（**待做**，已完成预演）
- [ ] 结果落盘为回归表 + 参数快照（**待做**）

---

*文档生成说明：本文档由工作区现有材料汇编并经**实测核查**而成——主管线 notebook 的代码与保存输出、3 个导出 CSV、2 张图、`all_tags.txt`、4 个语言脚本，以及论文 PDF 的全文提取（`03_literature/paper_clean.txt`）。所有 `[实]` 数字均由 `06_tools/` 下三份脚本运行产出，报告见 `verify_report.md`、`coverage_report.md`、`aux_report.md`；论文侧事实见 `03_literature/paper_digest.md`。*
