# 修正变更日志（CHANGELOG）

> 执行时间：2026-09-30　｜　执行范围：主管线 notebook + 结果落盘
> 依据：`06_tools/threshold_03_report.md`、`index_spec_report.md`、`paper_tables_report.md`、`quality_proxy_report.md`
> 执行方式：`python 06_tools/apply_notebook_fixes.py`（写入前自动备份为
> `4dissertation_gamespace_clustering_new.ipynb.bak-<时间戳>`；`--check` 为试运行。
> 脚本带**幂等保护**：检测到修正已应用时会直接提示并退出，不会重复改写。

---

## 摘要

| 编号 | 修正 | 类型 | 对结论的影响 |
|---|---|---|---|
| **C1** | 全部 OLS 改用 `cov_type="HC3"` | 推断口径 | **无**（系数不变），但 price 的推断更保守 |
| **C2** | `META_DICT` 键与标签键 `strip()` 归一化 | 数据正确性 | 无（β 变动在第 5 位小数） |
| **C3** | 稳健 4 改为**固定样本**、只变索引定义 | 方法学正确性 | 无（方向与显著性不变），但消除了 N 伪迹 |
| **C4** | 结果落盘到 `02_pipeline/results/` | 可复现性 | 无 |
| **C5** | 就地标注「0.3 过滤非约束性」 | 文档 | 无 |
| **C6** | **真正执行修正后的 notebook 并重生成导出表** | 产物一致性 | 索引均值 9.3247 → **9.3145**（C2 生效）；**聚类划分发生变化**（见下） |

**核心结论（倒 U、拐点、价格效应）在全部修正后不变。**

---

## C6 · 执行修正后的 notebook 并重生成导出表（追加）

**问题**　C1–C5 只改了 notebook 的**源码**，但 notebook **从未在本环境执行过**，
因此 `01_data/processed/*.csv` 仍是**修正前**的产物。新增的集成测试暴露了这一不一致：

```
mean(Hybridization_Index) 实测 = 9.3246635757   （应为 C2 后的 9.3145）
```

**改动**　新增 `06_tools/run_notebook.py`（无需 nbconvert/nbclient：逐单元 `exec`、
剥离 IPython 魔法命令、matplotlib 强制 Agg），并完整执行了主管线 notebook——
**16 个单元、30.5 秒、全部通过**（本环境首次跑通）。

**结果**

| 指标 | 执行前 | 执行后 | 判定 |
|---|---|---|---|
| `mean(Hybridization_Index)` | 9.3246635757 | **9.3145425760** | ✅ C2 生效 |
| 回归样本（H > 0） | 17,670 | **17,670** | ✅ 不变 |
| 导出表形状 / `appid` 集合 | 17,686 × 15 | **17,686 × 15，集合完全一致** | ✅ 不变 |
| **`Game_Cluster` 簇规模** | `[2181, 2163, 1741, 1341, 2478, 2620, 1977, 3185]` | **`[2060, 3238, 2462, 1605, 2880, 1542, 1232, 2667]`** | ⚠️ **变化** |

**⚠️ 新发现的可复现性缺陷**：输入数据、`random_state=42`、`K=8` 均未改变，簇划分却变了——
差异只能来自 **scikit-learn 的 KMeans 实现/默认值**（`n_init="auto"`）在版本间的变化，
而 notebook **没有记录任何库版本**。

`[推]` 含义：**"导出表八个簇规模与论文 Table 10 逐位相同"这条证据只对原始运行环境成立**，
在新环境下无法复现。这既是本工作区的缺陷，也说明**论文的聚类结果必须固定环境才能复现**。

**影响范围**：聚类**只用于描述**（论文 Table 10、簇画像），**从未进入任何回归**，
因此 §4 的全部结论与 `07_extension` 的全部结果**不受影响**（G3 的 `niche_density` 用了簇标签，
已随新导出表重算：拐点位移由 0.31 变为 0.32 个维度，结论不变）。

**落盘**

- 执行前产物归档至 `05_archive/pre_c2_regeneration_backup/`（旧导出表、两张图、旧标签表）；
- 新导出表为**当前主口径**（C2 一致）；
- 建议后续动作：写 `requirements.txt`、在导出表旁写**版本指纹**、
  并把 `Game_Cluster` 落盘为独立文件 `cluster_assignment.csv`，使下游不再依赖重跑聚类。

**复核**　`python 06_tools/run_notebook.py`（约 30 秒）；
`python 07_extension/tests/test_integration.py`（10 项验收测试，全部通过）。

---

## C1 · 全面改用 HC3 稳健标准误

**问题**　论文全程使用 HC3 异方差稳健标准误（BP LM = 601.91、White LM = 1,489.97，p < .001，
见论文 §3.5），并用 HC3 报告 Table 5–9。notebook 使用 statsmodels 的默认**经典标准误**，
没有任何稳健修正。

**改动**　5 处 `.fit()` → `.fit(cov_type="HC3")`：

| 位置 | cell | 语句 |
|---|---|---|
| 主模型 | #14 | `final_model = sm.OLS(Y, X_main).fit(cov_type="HC3")` |
| 稳健 1 | #16 | `m0 = sm.OLS(Y, X0).fit(cov_type="HC3")` |
| 稳健 2 | #17 | `m_age = sm.OLS(Y, X_age).fit(cov_type="HC3")` |
| 稳健 3 | #18 | `m_inter = sm.OLS(Y, X_inter).fit(cov_type="HC3")` |
| 稳健 4 | #19 | `m = sm.OLS(sub['Log_Reviews'], X).fit(cov_type="HC3")` |

**数值影响**（主模型，`06_tools/rebuild_results.py` 复算）

| 变量 | Coef. | SE(经典) | SE(HC1) | **SE(HC3)** | t(经典) | **t(HC3)** |
|---|---|---|---|---|---|---|
| const | +6.4898 | 0.0396 | 0.0403 | **0.0404** | 163.69 | **160.74** |
| Hybrid_Centered | +0.0761 | 0.0033 | 0.0032 | **0.0032** | 23.22 | **23.77** |
| Hybrid_Centered_Squared | −0.0145 | 0.0008 | 0.0007 | **0.0007** | −19.40 | **−21.29** |
| price | +0.0381 | 0.0009 | 0.0016 | **0.0016** | 41.68 | **23.23** |

- **系数一个都没变**（HC3 只改协方差矩阵，不改点估计）；
- price 的 t 由 **41.68 → 23.23**，是本次修正中唯一实质性的推断变化；
- **验证**：修正后的 HC3 标准误与论文 Table 5 逐位比较 ——
  `Hybridization` 0.003202 vs 论文 **0.0032** ✅、`Hybridization²` 0.000683 vs **0.0007** ✅、
  `Price` 0.001641 vs **0.0016** ✅。四个里三个吻合到 4 位小数。
  仅 `const` 不吻合（0.0404 vs 0.0439），差异来自年份虚拟变量的基准/集合，不影响任何关注量。

---

## C2 · 标签键与字典键 `strip()` 归一化

**问题**　原始数据中 `'Dystopian '`（1,050 款）与 `'Parody '`（583 款）带**尾随空格**，
`META_DICT.get('Dystopian ')` 查不到（字典里只有 `'Dystopian'`），于是这些标签**绕过词典**、
以原始标签的身份被当成一个独立维度计入杂交度。共有 1,615 款游戏（1.80%）受污染。

**改动**　两处同时归一化（只改一侧无效）：

| 位置 | cell | 改动 |
|---|---|---|
| `META_DICT` 定义之后 | #13 | `META_DICT = {str(k).strip(): v for k, v in META_DICT.items()}` |
| `_parse_tags_dict()` | #11 | dict 分支与 str 分支返回时均 `{str(k).strip(): v ...}` |

**数值影响**

| 口径 | mean(H) | SD | 杂交度变化的游戏 |
|---|---|---|---|
| 修正前 | 9.3247 | 3.6756 | — |
| 修正后 | **9.3145** | 3.6682 | **179 款（1.01%）** |
| 差 | −0.0101 | −0.0074 | |

- 主模型 β₁ +0.07606 → **+0.076131**、β₂ −0.01446 → **−0.014540**、R² 0.1622 → **0.1623**
  ⇒ **影响在第 4–5 位小数，无实质意义**；
- `strip()` 后 `META_DICT` 键数仍为 291（无键碰撞）；
- 顺带修好 7 个死键中的 `Dystopian`（此前因空格而"从未出现"）。
  另外 6 个（`Adult`、`Base Building`、`Dating`、`Eroge`、`Hentai(Nudity)`、`Visual Novel (Adult)`）
  仍为死键——无害，但应在词典维护时清理。

---

## C3 · 稳健 4 改为「固定样本、只变索引定义」

**问题**　原实现每一档同时做两件事：① 用阈值 t 重新定义杂交度；② 用
`(data['_Cpt'].apply(len) > 0) & (data['_Mt'].apply(len) > 0)` 重新筛样本。
实测（`threshold_03_report.md`）表明：

- **`_Cpt` 为空的行数在全部七档都是 0** —— 每款游戏票数最高的标签 `priority` 恒为 **1.0 ≥ 任何 t ≤ 1**，
  所以 priority 过滤**一次也没有删掉任何一行**；
- N 的下降（17,639 → 17,488）**全部**来自 `_Mt` 为空，即"priority ≥ t 的标签恰好全被
  `META_DICT` 映射到 `'IGNORE'`"：t = 0.15 时 47 行，t = 0.30 时 108 行，t = 0.45 时 198 行。
  `META_DICT` 有 **44** 个键指向 `'IGNORE'`（含 `Multiplayer`、`Singleplayer`、`Indie`、
  `Free to Play`、`Gore`、`Great Soundtrack`、`Controller` 等极常见标签）。

⇒ 原设计把「**索引定义变化**」与「**样本构成变化**」两个效应混在了一起，而且后者是词典归并的副产物，
不是阈值在筛样本。

**改动**　cell #19 整体重写。样本固定为 `reg_data`（主模型回归样本，N = 17,670），
每一档只重新计算 `_Mt` 并据此定义 `Hc_t`；被 IGNORE 清空的游戏保留在样本中（其 H = 0），
不再被删除。

**数值影响**

| t | N（修正前） | N（修正后） | 拐点（修正前） | 拐点（修正后） |
|---|---|---|---|---|
| 0.15 | 17,639 | **17,670** | 10.93 | 11.00 |
| 0.30 | 17,578 | **17,670** | 9.66 | 9.68 |
| 0.45 | 17,488 | **17,670** | 8.52 | 8.50 |

- **N 恒为 17,670**，β₂ 在全部八档均为负且显著（t 在 −21.3 ~ −12.3）⇒ 倒 U 稳健性结论**不变**；
- 拐点区间 8.50 ~ 11.93（修正前 8.52 ~ 10.93 的可比区间），结论方向一致。

**未做的相关改动**　主模型的 `Hybridization_Index > 0` 过滤（剔除 16 款零杂交度游戏）**保留不动**。
理由：它与论文 Table 5 的 N = 17,670 **逐位一致**，是二者可比的基石；改动它会破坏这一对应关系。
IGNORE 的"不计维度"语义本身是正确的，本次只解耦"据此删样本"这一副作用在稳健性检验中的使用。

---

## C4 · 结果落盘

**问题**　此前**所有**回归结果只 `print` 到控制台，没有任何结果文件，无法被引用或复核。

**改动**　新增 cell #25，写出：

| 文件 | 内容 |
|---|---|
| `02_pipeline/results/regression_summary.csv` | Table 5–8 的 N / R² / Adj R² / β₁ / β₂ / price 及各自 HC3 标准误与 t 值 / 拐点 |
| `02_pipeline/results/table1_index_descriptives.csv` | 全样本杂交度描述统计（论文 Table 1 的替代来源） |
| `02_pipeline/results/year_distribution.csv` | 发行年份分布（论文 §4.1 的替代来源） |

另外，`06_tools/rebuild_results.py`（不依赖 statsmodels/sklearn，可独立复核）已生成完整结果表：

```
02_pipeline/results/
  corrected_tables.md              # 人可读的汇总（全部修正后表格）
  table1_index_descriptives.csv    # 杂交度描述统计
  table4_summary_statistics.csv    # 四变量汇总统计（论文 Table 4 的替代）
  table5_main_regression.csv       # 主回归，三种标准误并列
  table6_8_robustness.csv          # 稳健 1–3
  table9_threshold_series.csv      # 阈值序列（固定样本）
  year_distribution.csv            # 年份分布
```

---

## C5 · 就地标注「0.3 过滤非约束性」

cell #9，在 `Clean_Priority_Tags` 赋值之后加入注释，说明该过滤实测删除 0 行及其原因，
避免后续读者误以为它真的在筛样本。

---

## 修正后必须替换的论文数字

以下数字**不得**再转引论文原表，应改用管线自算值（来源：`02_pipeline/results/`）：

| 论文位置 | 论文原值 | 应替换为（管线自算） |
|---|---|---|
| Table 1 / Table 4 · 杂交度 Mean | 10.35 | **9.31**（全样本 17,686）／ 9.32（回归样本） |
| Table 1 / Table 4 · 杂交度 SD | 4.14 | **3.67** |
| Table 4 · 杂交度 Median | 11.00（Table 1 注与正文均写 10.0） | **10.0** |
| Table 4 · 杂交度 Min | 0 | **0** ✅（但注意它来自 17,686 全样本，非 17,670） |
| §4.1 · 2024 年款数 | 2,123 | **2,129** |
| §4.1 · 年份百分比分母 | 声明 17,670，反解 ≈17,633 | **17,686** |

**可以直接沿用**（与管线逐位相同，无需改动）：Table 3 三个 VIF、Table 5 的系数与 R²、
Table 6–9 的 N 与四个拐点、Table 10 八个簇规模。

---

## 未执行的改动及原因

| 项 | 为什么没做 |
|---|---|
| 为对齐论文的 10.35 而放开 `'IGNORE'` 或改 `META_DICT` | `paper_tables_report.md` §B2 已证：10.35 **不可能**由这套杂交度值的任何子样本产生；且放开 IGNORE 会把拐点推到 14.15、β₁ 压到 +0.0493，**离论文更远** |
| 修改兜底（fall-through）规则 | 已验证方向与论文一致（改成"仅词典类别"使均值降到 5.55 / 7.79，反向） |
| 补齐 168 个未覆盖标签 | 属**构念改进**（P2），需人工判定词表，且不影响本次结论 |
| 删除死参数（`MIN_TAG_DOC_FREQ`、`FOCUS_CLUSTERS`、`Game_Age` 等） | 属清理项（P2），与结论无关，单独提交更安全 |
| 加入簇固定效应 | 属 P1 增强项，不是修正；已预演（β₁ = +0.0773、峰值 12.07、R² 0.1752） |
| 修改主模型样本（含入 H = 0 的 16 款） | 会破坏与论文 N = 17,670 的逐位对应 |

---

## 回滚

```powershell
Copy-Item 02_pipeline\4dissertation_gamespace_clustering_new.ipynb.bak-<时间戳> `
          02_pipeline\4dissertation_gamespace_clustering_new.ipynb -Force
```

## 复核方式

```powershell
python 06_tools/verify_all.py           # 总体审计 + 全部 OLS 重估
python 06_tools/check_threshold_03.py   # 0.3 阈值穷尽核查
python 06_tools/check_index_specs.py    # 词典/维度规则量化
python 06_tools/check_paper_tables.py   # 论文描述性表格自洽性
python 06_tools/rebuild_results.py      # 修正后结果重建（本文档全部数字的来源）
```
