## 1. 中心化分母核对
- 17,686 行均值 = 9.3145425760
- 17,670 行（回归样本）均值 = 9.3229767968
- 差值 = +0.008434
- 导出的 Hybrid_Centered 是否以 17,686 均值计算: max|HC-(H-mean_all)| = 8.88e-16
- 若改用回归样本均值，拐点变化 = 0.0000（同斜率下仅截距/拐点平移 +0.0084）

## 2. 标签空白污染（尾随/前导空格）
- 扫描原始数据 89,618 行（含 tags 字典）
- 含「首尾空白」标签的游戏数 = **1615**（1.80%）
- 受影响的脏标签（共 2 种），Top 15：
    - 'Dystopian ': 1050
    - 'Parody ': 583

## 3. Meta_Tags 中出现的异常取值
- 含空白/nan 的元标签取值: []
- 'Dystopian' 次数 = 0；'Parody' = 171
- 说明：`_csv_s()` 用 '; ' 连接，若原标签带尾随空格，导出后会出现 'Dystopian ; NextTag'，split(';')+strip 会还原，故导出文件本身看不到空格，但管线内部 META_DICT.get('Dystopian ') 失败。

## 4. META_DICT 死键检查（字典里指向自身但数据中不存在的标签）
- 解析出 META_DICT 键数 = 291（含重复键）
- 映射目标类别（去重，含 IGNORE）= 26；不含 IGNORE = 26
- 原始 tags 中出现的不同标签数（全量口径）= **452**
- 字典中在原始数据里**从未出现**的键（7 个）: ['Adult', 'Base Building', 'Dating', 'Dystopian', 'Eroge', 'Hentai(Nudity)', 'Visual Novel (Adult)']
- 原始数据中出现但字典**未覆盖**的标签数 = **168**（占 37.2%）

- 未覆盖标签 Top 25（全量原始数据口径）：

| 未覆盖标签 | 出现游戏数 |
|---|---|
| Atmospheric | 13,780 |
| Colorful | 11,833 |
| Exploration | 11,053 |
| Arcade | 9,866 |
| Female Protagonist | 6,474 |
| Combat | 6,259 |
| Stylized | 5,997 |
| Difficult | 5,580 |
| Cartoony | 5,127 |
| Linear | 5,039 |
| Physics | 4,825 |
| Violent | 4,346 |
| Side Scroller | 3,776 |
| Old School | 3,716 |
| Character Customization | 3,591 |
| Tactical | 3,422 |
| Cartoon | 3,076 |
| Turn-Based Combat | 2,850 |
| Immersive Sim | 2,768 |
| 1990's | 2,620 |
| Score Attack | 2,531 |
| Surreal | 2,501 |
| Emotional | 2,423 |
| Nature | 2,367 |
| Education | 2,268 |

## 5. 样本框算术核对
- 载入 89,618 → dropna 88,618
- 年份 2015–2025 后 = 85,884
- 评论 ≥ 100 后 = 17,772（notebook: 17686，需再扣大厂与 priority 过滤）
- 非 Indie 且 owner ≥ 5,000,000 的样本 = **86** 个
- 剔除后 = 17,686
- 与导出 17,686 的差额 = 0（应为 priority ≥ 0.3 后标签为空 / tags 缺失的样本）

## 6. 导出文件排序与年份抽样疑点核对
- 事实表是否按 Total_Reviews 降序: False
- 2021 年样本数 = 1,628；2024 = 2,129；2025 = 308（尾部 80 行抽样为 0 属抽样偏差）
- 事实表末尾 80 行的年份分布: {2015: 3, 2016: 13, 2017: 8, 2018: 11, 2019: 14, 2020: 7, 2021: 2, 2022: 3, 2023: 7, 2024: 12}
- 事实表末尾 80 行的杂交度均值 = 5.287（全样本 9.315）