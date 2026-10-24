## A. 管线中字面量 `0.3` 的全部出现位置

| cell | 源码行（去缩进） | 角色 |
|---|---|---|
| 7 | `def parse_tags_counts_with_priority(x, priority_threshold=0.3):` | **功能性**：函数默认参数（Step 1 与稳健 4 共用） |
| 9 | `data["Clean_Priority_Tags"] = data["tags"].apply(lambda x: parse_tags_counts_wit…` | **功能性**：样本纳入过滤（priority ≥ 0.3） |
| 9 | `# [实] 该过滤实测删除 0 行：每款游戏票数最高的标签 priority 恒为 1.0 >= 0.3。` | 无关 / 数值输出中的小数 |
| 11 | `+ Meta_Tags_Priority(priority 归一化)。在完整 tags 字典上做，不先砍 0.3 阈值。"""` | 无关 / 数值输出中的小数 |
| 19 | `for t in [None, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45]:` | 无关 / 数值输出中的小数 |
| 24 | `scatter_kws={"alpha": 0.3, "color": "gray"},` | 无关 / 数值输出中的小数 |
| 24 | `axes[1].axvline(0.3, color="orange", linestyle="--", label="Medium (0.3)")` | 纯视觉：图中标注线，不参与任何计算 |

源码中含 `0.3` 的行共 **7** 行（另有若干出现在已保存输出的数值里，非源码）。

- `META_DICT` 键数 = 291；映射到 `'IGNORE'` 的键数 = **44**
- 这些 IGNORE 键为：['360 Video', '3D Vision', '4 Player Local', '8-bit Music', 'Addictive', 'Asymmetric VR', 'Asynchronous Multiplayer', 'Beautiful', 'Benchmark', 'Blood', 'Classic', 'Co-op', 'Controller', 'Crowdfunded', 'Documentary', 'Early Access', 'Family Friendly', 'Free to Play', 'Game Development', 'Gore', 'Great Soundtrack', 'Indie', 'Local Co-Op', 'Local Multiplayer', 'Massively Multiplayer', 'Masterpiece', 'Mature', 'Memes', 'Mod', 'Moddable', 'Mouse only', 'Movie', 'Multiplayer', 'Music', 'Online Co-Op', 'PvE', 'PvP', 'Replay Value', 'Singleplayer', 'Software']

## B. Step 1 逐级复现：0.3 过滤到底删掉了多少行？

- 载入 = 89,618
- `dropna(genres, categories, tags_counts)` 后 = 88,618
- 年份 2015–2025 后 = 85,884
- `Total_Reviews >= 100` 后 = 17,772
- 「非 Indie 且 owner ≥ 5,000,000」标记 = **86** 行
- 剔除非 Indie 大厂后 = 17,686

**在 17,686 行的样本上施加 `parse_tags_counts_with_priority(x, 0.3)`：**
- priority ≥ 0.3 的标签列表**为空**的行数 = **0**
- 即该过滤实际删除 = **0** 行
- 过滤后 = 17,686  （notebook 打印：17,686）

| 阶段 | N | 本阶段删除 |
|---|---|---|
| 载入 | 89,618 | — |
| dropna | 88,618 | 1,000 |
| 年份窗口 | 85,884 | 2,734 |
| 评论 ≥ 100 | 17,772 | 68,112 |
| 剔除非 Indie 大厂 | 17,686 | 86 |
| **priority ≥ 0.3** | 17,686 | **0** |

## C. 稳健 4 复现：t = 0.30 时到底删了谁？

### C0. 主模型口径（完整 tags 字典，**不砍阈值**）
- N = 17,686
- mean(H) = **9.3247**  （notebook 打印：9.32）
- H = 0 的游戏数 = **16**
- 回归样本（H > 0）N = 17,670  （notebook 打印：17,670）

### C1. 七挡阈值序列（复现 notebook 稳健 4 的输出）

| t | _Cpt 空 | _Mt 空 | price/Log_Reviews 缺失 | 最终 N | IndexMean（本文复现） | notebook 打印 |
|---|---|---|---|---|---|---|
| 0.15 | 0 | 47 | 0 | **17,639** | 8.92 | 17,639 / 8.92 |
| 0.20 | 0 | 56 | 0 | **17,630** | 8.67 | 17,630 / 8.67 |
| 0.25 | 0 | 82 | 0 | **17,604** | 8.39 | 17,604 / 8.39 |
| 0.30 | 0 | 108 | 0 | **17,578** | 8.06 | 17,578 / 8.06 |
| 0.35 | 0 | 138 | 0 | **17,548** | 7.70 | 17,548 / 7.70 |
| 0.40 | 0 | 171 | 0 | **17,515** | 7.33 | 17,515 / 7.33 |
| 0.45 | 0 | 198 | 0 | **17,488** | 6.96 | 17,488 / 6.96 |

### C2. 关键对照：0.3 在两条路径上的作用
- 稳健 4 在 t = 0.30 时，`_Cpt` 为空的行数 = **0**
- 而 Step 1 的同一个 0.3 过滤，在它自己的位置上删除的行数 = **0**

## D. 主模型的杂交度用哪一列？

| 列 | 生成方式 | 是否砍 0.3 | 去向 |
|---|---|---|---|
| `Clean_Priority_Tags` | `parse_tags_counts_with_priority(tags, 0.3)` | **是** | 仅用于样本纳入过滤；另派生 `Clean_Meta_Tags` → `all_tags.txt` |
| `Clean_Meta_Tags` | `Clean_Priority_Tags` 去重 | **是** | 仅写入 `01_data/processed/all_tags.txt`（448 个标签），**未进入回归** |
| `Meta_Tags` | `build_meta_fields()` 读 **完整 `tags` 字典** | **否** | `Hybridization_Index = len(Meta_Tags)` → 主模型自变量 |

- `Clean_Meta_Tags` 口径的唯一标签数（= `all_tags.txt`）= **448**
- 完整 `tags` 字典口径的唯一标签数 = **452**
- 两者相差 4 个标签；回归用的是**后者**（452 口径经 META_DICT 映射后的元标签）

## 结论

1. **0.3 在管线中确实存在，且是功能性的**——出现在 Step 1 的样本纳入过滤（cell 9）与稳健 4 的七挡阈值序列（cell 19）中；另有 2 处纯视觉（散点 alpha、图上 0.3 参考线）和 1 处文档字符串说明。
2. **它不参与主模型杂交度的构造**：`build_meta_fields()` 明确读完整 `tags` 字典（cell 11 的 docstring 自述「不先砍 0.3 阈值」），cell 623 的注释也写明「不再从 Clean_Priority_Tags 重建」。主模型 mean(H) = 9.3247。

3. **作为「标签过滤」，0.3 一次也没有删掉任何样本**：Step 1 删 **0** 行，稳健 4 在 t = 0.30 时 `_Cpt` 为空的行数也是 **0**——因为每款游戏的票数最高标签 priority 恒为 1.0 ≥ 0.3，所以 `_Cpt` 永远非空。
4. **稳健 4 的样本随 t 缩小，是 `'IGNORE'` 映射造成的，不是阈值直接删行**：t = 0.30 时 `_Mt` 为空（priority ≥ 0.3 的标签全被映射到 `'IGNORE'`）的行数 = **108**，这才是 17,686 → 17,578 的真正来源。`META_DICT` 有 44 个键指向 `'IGNORE'`，其中 `Multiplayer` / `Singleplayer` / `Indie` / `Free to Play` / `Gore` 等是极常见标签，所以阈值越高、幸存标签越少，就越容易被 IGNORE 清空。
5. 由此，论文「指数在 0.30 阈值之后计算」的说法对**指数**不成立；对**样本**也不成立，因为该阈值在样本纳入上是**非约束性（non-binding）**的。0.3 唯一产生实质影响的场合是稳健 4，而那里的机制是 IGNORE 归并的副产物，不宜表述为「按 priority 阈值筛选」。
