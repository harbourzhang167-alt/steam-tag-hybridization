# 质量代理回归（verify_all.py §E3）施加方式与稳健性拆解

生成时间: 2026-09-30 20:50:49

本报告回答一个问题：**「加入质量代理后 price 不显著」这一步到底是怎么做的、结论有多稳。** 所有数字由 numpy 正规方程独立重估（HC1 稳健标准误）。

## 1. 样本与合并路径（代理变量是怎么进来的）

- 事实表 `games_clustered_meta_export.csv`：**17686 行 × 15 列**
- 事实表列名：['appid', 'name', 'Release_Year', 'Clean_Priority_Tags', 'Meta_Tags', 'Game_Cluster', 'in_focus_cluster', 'Total_Reviews', 'positive', 'negative', 'price', 'Hybridization_Index', 'Log_Reviews', 'Hybrid_Centered', 'Hybrid_Centered_Squared']

- 四个代理变量中**存在于事实表**的：无
- 因此需要从原始 CSV 回并的列：**['average_playtime_forever', 'achievements', 'dlc_count', 'peak_ccu']**

合并语句（与 verify_all.py 完全一致）：

```python
raw = pd.read_csv(RAW, usecols=["appid", "pct_pos_total", "average_playtime_forever",
                                "metacritic_score", "achievements", "dlc_count", "peak_ccu"])
m = reg.merge(raw, on="appid", how="left")          # 左连接，回并到回归样本上
```

- 关键点：代理变量**不是**主管线算出来的，而是**按 `appid` 从原始 CSV 左连接回并**；所以这一步不改变任何已有变量，只追加列。

回归样本构造（与主管线一致）：

```python
reg = df[df.Hybridization_Index > 0].dropna(
    subset=["Log_Reviews", "Hybrid_Centered", "Hybrid_Centered_Squared", "price"])
```

- 事实表 17686 行 → 回归样本 **N = 17670** 行（剔除杂交度为 0 的 16 行）
- 左连接后行数 = **17670**（未发生行扩张 ⇒ `appid` 在原始表中唯一）

| 列 | 缺失行数 | 缺失率% | 是否进入回归 |
|---|---|---|---|
| average_playtime_forever | 0 | 0.00 | 是 |
| achievements | 0 | 0.00 | 是 |
| dlc_count | 0 | 0.00 | 是 |
| peak_ccu | 0 | 0.00 | 是 |
| metacritic_score | 0 | 0.00 | 否（仅读入未使用） |

- 四个代理变量缺失行数全为 **0** ⇒ `dropna` 一行都没删，E3 的样本与主模型**完全同一批 17670 款游戏**（这是可比性的前提）。
- `metacritic_score` **被读入但未进入回归**（独立游戏缺失太多），是本检验的一个已知缺口。

## 2. 变换方式：逐列 log1p

实际进入回归的是 **`np.log1p(x)`（自然对数，ln(1+x)）**，直接用原始量纲会严重右偏：

| 变量 | min | 中位数 | 均值 | max | ln后均值 | 偏度(原始) | 偏度(ln1p) |
|---|---|---|---|---|---|---|---|
| average_playtime_forever | 0.000 | 0.000 | 507.592 | 1462997.000 | 1.787 | 74.039 | 1.075 |
| achievements | 0.000 | 20.000 | 51.098 | 9821.000 | 2.522 | 14.786 | -0.297 |
| dlc_count | 0.000 | 0.000 | 1.802 | 3427.000 | 0.426 | 88.568 | 2.393 |
| peak_ccu | 0.000 | 1.000 | 236.575 | 703236.000 | 1.605 | 90.995 | 1.506 |

对应代码：

```python
ctrl = np.column_stack([
    np.log1p(m3.average_playtime_forever.values),
    np.log1p(m3.achievements.values),
    np.log1p(m3.dlc_count.values),
    np.log1p(m3.peak_ccu.values),
])
```

含义对照：`ln_playtime` = 单局时长/留存（投入深度）；`ln_achievements` = 内容体量；`ln_dlc` = 后续运营投入；`ln_peak_ccu` = 并发峰值（**需求侧热度**，与因变量同源，见 §6）。

## 3. 规格：与主模型只差追加的 4 列

主模型（baseline）：

```python
X_main = [1, Hybrid_Centered, Hybrid_Centered_Squared, price, 年份哑变量]
```

E3（质量代理版）= baseline **原封不动** + 4 列 log 代理，无交互项、无标准化、无样本变动：

```python
Xq = [1, Hybrid_Centered, Hybrid_Centered_Squared, price, 年份哑变量,
      ln_playtime, ln_achievements, ln_dlc, ln_peak_ccu]
```

| 模型 | N | k | R² | Adj.R² | β1 | β2 | price coef | price t(HC1) | 拐点 |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 17670 | 14 | 0.1623 | 0.1616 | 0.0761 | -0.0145 | 0.0381 | 23.6174 | 11.9409 |
| +质量代理 | 17670 | 18 | 0.6940 | 0.6937 | 0.0546 | -0.0061 | -0.0001 | -0.1306 | 13.8312 |

完整系数（质量代理版，只显示核心项与代理项）：

| 变量 | coef | SE(HC1) | t(HC1) |  |
|---|---|---|---|---|
| Hybrid_Centered | 0.0546 | 0.0020 | 26.6914 | *** |
| Hybrid_Centered_Squared | -0.0061 | 0.0005 | -13.3296 | *** |
| price | -0.0001 | 0.0008 | -0.1306 |  |
| ln_playtime | 0.0799 | 0.0029 | 27.7086 | *** |
| ln_achievements | 0.0213 | 0.0045 | 4.7235 | *** |
| ln_dlc | 0.1263 | 0.0122 | 10.3174 | *** |
| ln_peak_ccu | 0.5691 | 0.0050 | 113.0453 | *** |

**复现确认**：baseline 的 price 系数 +0.03812 / t(HC1)≈23.6，质量代理版 −0.0001 / t=−0.13，R² 0.1622 → 0.6940，与 §E3 报告一致。

## 4. 相关性：四个代理是不是在抢同一块方差

|  | ln_playtime | ln_achievements | ln_dlc | ln_peak_ccu | price | Hybridization_Index | Log_Reviews |
|---|---|---|---|---|---|---|---|
| ln_playtime | 1.000 | 0.130 | 0.191 | 0.365 | 0.157 | 0.055 | 0.451 |
| ln_achievements | 0.130 | 1.000 | 0.251 | 0.196 | 0.208 | 0.202 | 0.215 |
| ln_dlc | 0.191 | 0.251 | 1.000 | 0.338 | 0.313 | 0.116 | 0.358 |
| ln_peak_ccu | 0.365 | 0.196 | 0.338 | 1.000 | 0.397 | 0.176 | 0.769 |
| price | 0.157 | 0.208 | 0.313 | 0.397 | 1.000 | 0.164 | 0.308 |
| Hybridization_Index | 0.055 | 0.202 | 0.116 | 0.176 | 0.164 | 1.000 | 0.212 |
| Log_Reviews | 0.451 | 0.215 | 0.358 | 0.769 | 0.308 | 0.212 | 1.000 |

读法（以下均为实测值）：

- 四个代理**两两相关只有 0.130–0.365**（最高的一对是 ln_playtime–ln_peak_ccu），属中等相关，**够不上「互相抵消」的共线性**；所以代理入模后系数怎么变，必须看 §6 的逐个加入，而不能归因于共线性；
- `ln_peak_ccu` 与因变量 `Log_Reviews` 相关 **0.769**，而 `ln_playtime` 只有 0.451、`ln_achievements` 只有 0.215 —— peak_ccu 本质上**与因变量同源**（都是热度/规模的同期表现），不是外生质量指标；
- 四个代理与 `Hybridization_Index` 的相关只有 0.055–0.202 ⇒ 它们**几乎不吸收杂交度的方差**，这正是二次项在加入代理后仍然存活的原因。

## 5. 共线性诊断：代理能不能替 price「背锅」

| 变量 | R²(对其他解释变量) | VIF |
|---|---|---|
| Hybrid_Centered | 0.149 | 1.176 |
| Hybrid_Centered_Squared | 0.133 | 1.154 |
| price | 0.209 | 1.265 |
| ln_playtime | 0.141 | 1.164 |
| ln_achievements | 0.113 | 1.127 |
| ln_dlc | 0.182 | 1.223 |
| ln_peak_ccu | 0.300 | 1.428 |

- 核心变量 VIF 落在 1.13–1.43，**全部远低于 5** ⇒ 不存在灾难性共线性，price 归零**不能**用方差膨胀解释；

更有信息量的诊断：四个代理各自能解释多少 `price` 和多少 `Hybridization_Index`。

- `price` 对四个代理回归：R² = **0.2028** ⇒ 价格里约 20.3% 的方差可由开发体量/热度代理解释，这就是主模型 price 系数「不干净」的来源；
- `Hybridization_Index` 对四个代理回归：R² = **0.0612** ⇒ 杂交度与这组代理**近乎正交**，倒 U 不可能被它们吸收掉。

## 6. 逐个加入（ablation）：到底是谁杀死了 price

| 只加入 | R² | price coef | price t(HC1) | 该代理 coef | 该代理 t | β1 | β2 | 拐点 |
|---|---|---|---|---|---|---|---|---|
| ln_playtime | 0.3072 | 0.0294 | 21.4906 | 0.2204 | 51.1121 | 0.0659 | -0.0121 | 12.0433 |
| ln_achievements | 0.1759 | 0.0353 | 22.5419 | 0.1138 | 15.8232 | 0.0669 | -0.0139 | 11.7314 |
| ln_dlc | 0.2219 | 0.0277 | 18.7611 | 0.5755 | 27.6459 | 0.0677 | -0.0128 | 11.9606 |
| ln_peak_ccu | 0.6730 | 0.0026 | 3.0277 | 0.6270 | 138.9999 | 0.0604 | -0.0067 | 13.8282 |
| （四个一起，= E3） | 0.6940 | -0.0001 | -0.1306 |  |  | 0.0546 | -0.0061 | 13.8312 |

- baseline 的 price 系数是 **+0.0381**；单独加入 playtime / achievements / dlc 时，price 仍在 +0.0277 ~ +0.0353、t = 18.8~22.5，**照样显著**；
- 但单独加入 **`ln_peak_ccu`** 就把 price 压到 +0.0026（t = 3.03，相对 baseline 衰减 93%），且它一个变量就贡献了 R² 增量 0.5318 中的 96%；
- 四个一起进入才让 price 归零 ⇒ **主因是 `peak_ccu` 这个与因变量同源的热度变量**，而不是四个代理组成的「共同质量因子」。

## 7. 两个更干净的替代规格

### 7.1 剔除 `ln_peak_ccu`（去掉热度内生项）

- N = 17670, R² = **0.3474**

| 变量 | coef | SE(HC1) | t(HC1) |  |
|---|---|---|---|---|
| Hybrid_Centered | 0.0563 | 0.0029 | 19.6355 | *** |
| Hybrid_Centered_Squared | -0.0107 | 0.0006 | -17.5535 | *** |
| price | 0.0209 | 0.0013 | 16.7529 | *** |
| ln_playtime | 0.2030 | 0.0042 | 48.4051 | *** |
| ln_achievements | 0.0497 | 0.0063 | 7.9281 | *** |
| ln_dlc | 0.4404 | 0.0188 | 23.4479 | *** |

- 拐点 = **11.95**

### 7.2 用单一标准化合成指标代替四个相关代理

```python
z = (ln_proxy - ln_proxy.mean()) / ln_proxy.std()   # 逐列 z 分数（ddof=1）
composite = mean(z_playtime, z_achievements, z_dlc, z_peak_ccu)   # 等权质量指数
```

- `quality_z`：均值 0.000，SD 0.659，与 H 相关 0.208
- N = 17670, R² = **0.4905**

| 变量 | coef | SE(HC1) | t(HC1) |  |
|---|---|---|---|---|
| Hybrid_Centered | 0.0387 | 0.0026 | 15.1286 | *** |
| Hybrid_Centered_Squared | -0.0078 | 0.0006 | -13.8490 | *** |
| price | 0.0065 | 0.0010 | 6.7805 | *** |
| quality_z | 1.4886 | 0.0164 | 90.9808 | *** |

- 拐点 = **11.82**

合成指标把四个代理压成 1 个自由度，避免四个变量争夺同一块共享方差，是这一组检验里**最可信的一版**：它同时回答了「price 还剩多少」和「二次项还站不站得住」。

## 8. 结论：这一步能支持什么、不能支持什么

**能支持**

- 倒 U 型**不是质量/投入代理的伪装**：从 baseline 到四种代理规格，β2 始终为负且 |t| 很大；`quality_z` 合成版 β2 = -0.0078、拐点 11.82，与主模型（β2 = −0.0145、峰值 11.96）同向同量级 ⇒ 结论加固；
- 四个代理与杂交度的解释力只有 R² = 0.0612 ⇒ 倒 U 与质量是**两块近乎正交的方差**，不存在「控制质量后倒 U 消失」的风险；
- 原主模型里 `price` 的正系数**不稳健**：price 有 20.3% 的方差能被开发体量/热度解释，加入代理后从 +0.0381 掉到 0 附近；

**不能支持（比对上面几点同样重要）**

- **不能**说「price 的效应完全由质量吸收」：逐个加入时 price 依然显著（§6），剔除同源的 `ln_peak_ccu` 后 price 回升到 +0.0209（t = 16.8，≈ baseline 的 55%），合成指标版也有 +0.0065（t = 6.8）。**正确表述是「价格效应大幅缩水、识别不干净」，而不是「价格无效应」**；
- 拐点 11.96 → 13.91 的位移**完全由 `ln_peak_ccu` 造成**：剔除它以后拐点回到 **11.95**，合成版 11.82 ⇒ 峰值应报 ≈11.8–12.0，13.91 是同源控制变量带来的假位移（这一点反而**加固**了基准拐点，并与 §E1 分箱均值在 (10,12] 见顶一致）；
- **不是因果识别**：没有工具变量、没有面板/时间变动、没有断点。`peak_ccu` 与因变量同源（并发热度），属「坏控制」；playtime 也是成功的结果而非原因。因此这只是**遗漏变量敏感性检验**，不能替代识别策略；
- `metacritic_score` 未使用（独立游戏缺失严重），是**唯一可直接补的缺口** —— 若要用外部质量评分，需先报告其缺失率与选择性问题。

## 9. 审计更正记录（本报告相对 verify_report.md 旧版 §E3 的差异）


`verify_all.py` 旧版 §E3 的 `ols()` 只传了 8 个变量名，而设计矩阵有 18 列（含 10 个年份哑变量）。`coef_table()` 按下标取名字，于是**标着 `ln_playtime`/`ln_achievements`/`ln_dlc`/`ln_peak_ccu` 的四行其实是 `Y_2016`~`Y_2019` 的年份哑变量系数**（−0.044 / −0.180 / −0.177 / −0.115）。

- 受影响的只有**这四行的标签**；同一回归里的 N、R²、`price`、`Hybrid_Centered`、`Hybrid_Centered_Squared`、拐点都是前 4 列，**未被污染**；
- 四个代理的**真实**系数是 `ln_playtime` +0.0799、`ln_achievements` +0.0213、`ln_dlc` +0.1263、`ln_peak_ccu` +0.5691（全部为正、高度显著，符合经济直觉）；
- 已修复 `verify_all.py`（补全名字列表并重新生成 `verify_report.md`），并同步更正 `reference_pipeline_and_paper.md` 中引用该表的一行。**教训**：OLS 封装函数应按列数校验名字列表长度，`assert len(names) == X.shape[1]`。