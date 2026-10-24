# 管线产物核查与主模型重估报告

生成时间: 2026-09-30 20:50:22

数据来源：`games_clustered_meta_export.csv`（管线导出的事实表）。
OLS 由 numpy 正规方程独立重估（无 statsmodels），同时给出经典标准误与 HC1 稳健标准误。

## A. 事实表总体审计

- 形状: **17686 行 × 15 列**
- 列名: ['appid', 'name', 'Release_Year', 'Clean_Priority_Tags', 'Meta_Tags', 'Game_Cluster', 'in_focus_cluster', 'Total_Reviews', 'positive', 'negative', 'price', 'Hybridization_Index', 'Log_Reviews', 'Hybrid_Centered', 'Hybrid_Centered_Squared']
- 重复 appid: **0** 个

| index | count | mean | std | min | 25% | 50% | 75% | max | median |
|---|---|---|---|---|---|---|---|---|---|
| price | 17,686 | 11.5961 | 11.9644 | 0 | 2.0900 | 9.5900 | 17.9900 | 269.9900 | 9.5900 |
| Total_Reviews | 17,686 | 3,928.8521 | 23,851.8168 | 100 | 179 | 396 | 1,364.7500 | 1,195,980 | 396 |
| Hybridization_Index | 17,686 | 9.3145 | 3.6682 | 0 | 7 | 10 | 12 | 20 | 10 |
| Log_Reviews | 17,686 | 6.3998 | 1.5292 | 4.6151 | 5.1930 | 5.9839 | 7.2195 | 13.9945 | 5.9839 |
| Hybrid_Centered | 17,686 | 0 | 3.6682 | -9.3145 | -2.3145 | 0.6855 | 2.6855 | 10.6855 | 0.6855 |
| Hybrid_Centered_Squared | 17,686 | 13.4550 | 15.2533 | 0.0989 | 1.7280 | 7.2117 | 21.9535 | 114.1790 | 7.2117 |

### A1. 口径与门槛
- 发行年份范围: 2015–2025
- `Total_Reviews` 最小值: 100（门槛 100 应为满足）
- 杂交度 = 0 的样本: **16** 个
- 杂交度 > 0 的样本: **17670** 个（应等于回归 N）
- `price` = 0 的样本: **2347** 个（13.27%）
- `price` ≥ 100 的样本: **1** 个；最大价格 269.99
- `price` 上四分位以上极值: [24.99, 33.25, 59.99, 69.99]
- `in_focus_cluster` 取值: [1]（恒为 1 说明该变量已退化）

### A2. 恒等式校验
- `Hybridization_Index` 全样本均值 = **9.314543**（notebook 打印 9.32）
- |Hybrid_Centered − (H − mean)| 最大偏差 = 8.882e-16（>1e-6 的行数: 0）
- |Hc² − Hc²| 最大偏差 = 1.421e-14（>1e-6 的行数: 0）
- |Log_Reviews − ln(1+Total_Reviews)| 最大偏差 = 1.776e-15（>1e-9 的行数: 0）
- |Total_Reviews − (positive+negative)| > 0 的行数: 0

### A3. 相关矩阵（Pearson）
| index | price | Hybridization_Index | Log_Reviews | Total_Reviews |
|---|---|---|---|---|
| price | 1 | 0.1644 | 0.3080 | 0.1203 |
| Hybridization_Index | 0.1644 | 1 | 0.2113 | 0.0506 |
| Log_Reviews | 0.3080 | 0.2113 | 1 | 0.4426 |
| Total_Reviews | 0.1203 | 0.0506 | 0.4426 | 1 |

### A4. 分簇概况
| Game_Cluster | N | share_pct | mean_hybrid | median_hybrid | min_hybrid | max_hybrid | mean_logrev | median_logrev | mean_price | n_free | mean_total_reviews |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 2,060 | 11.648 | 11.863 | 12 | 3 | 18 | 6.491 | 6.101 | 11.219 | 156 | 3443.382 |
| 1 | 3,238 | 18.308 | 8.603 | 9 | 1 | 18 | 6.455 | 5.964 | 11.431 | 533 | 4785.906 |
| 2 | 2,462 | 13.921 | 10.140 | 11 | 1 | 17 | 6.450 | 6.047 | 15.407 | 269 | 3374.097 |
| 3 | 1,605 | 9.075 | 11.368 | 12 | 3 | 20 | 6.133 | 5.740 | 8.006 | 161 | 1964.726 |
| 4 | 2,880 | 16.284 | 6.372 | 6 | 0 | 17 | 6.013 | 5.702 | 7.294 | 573 | 1576.085 |
| 5 | 1,542 | 8.719 | 11.228 | 11 | 4 | 17 | 6.996 | 6.644 | 15.007 | 123 | 10493.710 |
| 6 | 1,232 | 6.966 | 11.931 | 12 | 3 | 18 | 6.378 | 6.010 | 12.379 | 97 | 3577.814 |
| 7 | 2,667 | 15.080 | 7.076 | 7 | 1 | 17 | 6.461 | 6.061 | 13.042 | 435 | 3864.582 |

- ΣN = 17686；Σshare = 100.00%

### A5. 发行年份分布与年份均值
| Release_Year | N | share_pct | mean_logrev | mean_hybrid | mean_price |
|---|---|---|---|---|---|
| 2,015 | 1,473 | 8.329 | 6.429 | 7.628 | 8.318 |
| 2,016 | 1,922 | 10.867 | 6.335 | 7.415 | 8.121 |
| 2,017 | 1,904 | 10.766 | 6.296 | 7.836 | 8.770 |
| 2,018 | 1,850 | 10.460 | 6.362 | 7.986 | 9.529 |
| 2,019 | 1,526 | 8.628 | 6.492 | 8.463 | 11.095 |
| 2,020 | 1,901 | 10.749 | 6.489 | 9.794 | 10.344 |
| 2,021 | 1,628 | 9.205 | 6.519 | 10.895 | 13.188 |
| 2,022 | 1,395 | 7.888 | 6.477 | 11.030 | 15.590 |
| 2,023 | 1,650 | 9.329 | 6.442 | 11.062 | 15.594 |
| 2,024 | 2,129 | 12.038 | 6.269 | 10.924 | 15.132 |
| 2,025 | 308 | 1.741 | 6.220 | 11.003 | 16.684 |

## A6. Meta_Tags 词表（漏网标签的直接证据）

- `Meta_Tags` 中出现的**不同元标签取值数 = 192**
- 每款游戏元标签数（= 杂交度）: min 0, mean 9.315, max 20

完整词表（按出现游戏数降序）：

| meta_tag | n_games | share_pct |
|---|---|---|
| Perspective | 11,509 | 65.07 |
| Adventure/Narrative | 10,330 | 58.41 |
| Art Style | 8,800 | 49.76 |
| Action | 8,187 | 46.29 |
| Casual | 6,563 | 37.11 |
| Simulation | 6,288 | 35.55 |
| Mood (Positive) | 5,994 | 33.89 |
| Core System | 5,438 | 30.75 |
| Story-Driven | 5,351 | 30.26 |
| RPG | 5,120 | 28.95 |
| Strategy | 4,646 | 26.27 |
| Puzzle/Board | 4,458 | 25.21 |
| Atmospheric | 4,424 | 25.01 |
| Mood (Dark) | 4,258 | 24.08 |
| Fantasy/Magic | 3,485 | 19.70 |
| Exploration | 3,180 | 17.98 |
| Sci-Fi/Cyberpunk | 3,028 | 17.12 |
| Shooter | 2,700 | 15.27 |
| Platformer | 2,554 | 14.44 |
| Female Protagonist | 2,489 | 14.07 |
| Colorful | 2,450 | 13.85 |
| Adult | 1,964 | 11.10 |
| Difficult | 1,913 | 10.82 |
| Other Themes | 1,885 | 10.66 |
| Historical | 1,885 | 10.66 |
| Fighting/Brawler | 1,837 | 10.39 |
| Arcade | 1,756 | 9.93 |
| Roguelike | 1,641 | 9.28 |
| Sports/Racing | 1,571 | 8.88 |
| Violent | 1,562 | 8.83 |
| Military/Combat | 1,333 | 7.54 |
| Stylized | 1,327 | 7.50 |
| Character Customization | 1,270 | 7.18 |
| Combat | 1,199 | 6.78 |
| Arcade/Top-Down Shooter | 1,146 | 6.48 |
| Physics | 1,106 | 6.25 |
| Tactical | 1,010 | 5.71 |
| Cartoony | 1,003 | 5.67 |
| Side Scroller | 934 | 5.28 |
| Turn-Based | 917 | 5.18 |
| Turn-Based Combat | 897 | 5.07 |
| Immersive Sim | 857 | 4.85 |
| Emotional | 776 | 4.39 |
| Surreal | 734 | 4.15 |
| Old School | 647 | 3.66 |
| Short | 642 | 3.63 |
| Linear | 637 | 3.60 |
| Cartoon | 616 | 3.48 |
| Dark Humor | 571 | 3.23 |
| 1990's | 567 | 3.21 |
| Cinematic | 541 | 3.06 |
| Fast-Paced | 540 | 3.05 |
| Narration | 493 | 2.79 |
| Psychological | 461 | 2.61 |
| Nature | 440 | 2.49 |
| RPGMaker | 431 | 2.44 |
| Education | 426 | 2.41 |
| Clicker | 410 | 2.32 |
| Competitive | 380 | 2.15 |
| Conversation | 356 | 2.01 |
| Team-Based | 355 | 2.01 |
| Score Attack | 346 | 1.96 |
| Idler | 333 | 1.88 |
| Level Editor | 328 | 1.85 |
| 1980s | 319 | 1.80 |
| Psychedelic | 315 | 1.78 |
| Abstract | 315 | 1.78 |
| Destruction | 306 | 1.73 |
| Experimental | 304 | 1.72 |
| Comic Book | 297 | 1.68 |
| Flight | 297 | 1.68 |
| Nonlinear | 289 | 1.63 |
| Collectathon | 282 | 1.59 |
| Cats | 268 | 1.52 |
| Modern | 253 | 1.43 |
| Dark Comedy | 246 | 1.39 |
| Artificial Intelligence | 230 | 1.30 |
| Capitalism | 224 | 1.27 |
| Rhythm | 222 | 1.26 |
| Noir | 209 | 1.18 |
| Creature Collector | 205 | 1.16 |
| Trading | 198 | 1.12 |
| Philosophical | 198 | 1.12 |
| Split Screen | 197 | 1.11 |
| Science | 191 | 1.08 |
| Tutorial | 190 | 1.07 |
| Cooking | 189 | 1.07 |
| Political | 183 | 1.03 |
| Remake | 181 | 1.02 |
| Co-op Campaign | 179 | 1.01 |
| Parody | 171 | 0.97 |
| FMV | 170 | 0.96 |
| Narrative | 155 | 0.88 |
| Design & Illustration | 154 | 0.87 |
| Gun Customization | 150 | 0.85 |
| Class-Based | 150 | 0.85 |
| Real-Time | 148 | 0.84 |
| Fishing | 147 | 0.83 |
| Party | 146 | 0.83 |
| America | 145 | 0.82 |
| Grid-Based Movement | 145 | 0.82 |
| Hacking | 142 | 0.80 |
| Cult Classic | 142 | 0.80 |
| Politics | 141 | 0.80 |
| Hex Grid | 135 | 0.76 |
| Satire | 135 | 0.76 |
| Villain Protagonist | 132 | 0.75 |
| Mining | 131 | 0.74 |
| Illuminati | 130 | 0.74 |
| Real-Time with Pause | 129 | 0.73 |
| Diplomacy | 129 | 0.73 |
| Bullet Time | 129 | 0.73 |
| Battle Royale | 122 | 0.69 |
| Dog | 121 | 0.68 |
| Trains | 119 | 0.67 |
| Dinosaurs | 117 | 0.66 |
| Time Travel | 117 | 0.66 |
| Conspiracy | 115 | 0.65 |
| Faith | 114 | 0.64 |
| Programming | 114 | 0.64 |
| Hunting | 111 | 0.63 |
| Dynamic Narration | 108 | 0.61 |
| Underwater | 107 | 0.60 |
| Time Manipulation | 107 | 0.60 |
| Kickstarter | 101 | 0.57 |
| Immersive | 100 | 0.57 |
| 6DOF | 97 | 0.55 |
| Sequel | 90 | 0.51 |
| Action RTS | 85 | 0.48 |
| Underground | 84 | 0.47 |
| Superhero | 83 | 0.47 |
| Touch-Friendly | 81 | 0.46 |
| Minigames | 76 | 0.43 |
| Quick-Time Events | 75 | 0.42 |
| Typing | 73 | 0.41 |
| Episodic | 72 | 0.41 |
| Experience | 72 | 0.41 |
| Nostalgia | 72 | 0.41 |
| Foreign | 64 | 0.36 |
| Animation & Modeling | 64 | 0.36 |
| Time Attack | 63 | 0.36 |
| Gambling | 60 | 0.34 |
| Snow | 60 | 0.34 |
| Dwarf | 57 | 0.32 |
| Horses | 55 | 0.31 |
| Bikes | 54 | 0.31 |
| Social Deduction | 49 | 0.28 |
| Games Workshop | 49 | 0.28 |
| GameMaker | 49 | 0.28 |
| Mars | 49 | 0.28 |
| Archery | 45 | 0.25 |
| Music-Based Procedural Generation | 43 | 0.24 |
| Werewolves | 42 | 0.24 |
| Submarine | 38 | 0.21 |
| Unforgiving | 37 | 0.21 |
| Video Production | 36 | 0.20 |
| Jet | 34 | 0.19 |
| Silent Protagonist | 34 | 0.19 |
| Dungeons & Dragons | 32 | 0.18 |
| LEGO | 31 | 0.18 |
| Warhammer 40K | 30 | 0.17 |
| Jump Scare | 28 | 0.16 |
| Audio Production | 28 | 0.16 |
| Spaceships | 27 | 0.15 |
| Photo Editing | 26 | 0.15 |
| Software Training | 21 | 0.12 |
| Web Publishing | 21 | 0.12 |
| Intentionally Awkward Controls | 19 | 0.11 |
| Pool | 19 | 0.11 |
| Based On A Novel | 19 | 0.11 |
| Gaming | 17 | 0.10 |
| Well-Written | 17 | 0.10 |
| Electronic Music | 16 | 0.09 |
| nan | 16 | 0.09 |
| Shop Keeper | 15 | 0.08 |
| TrackIR | 11 | 0.06 |
| Voice Control | 11 | 0.06 |
| Hardware | 10 | 0.06 |
| Lemmings | 10 | 0.06 |
| Ambient | 9 | 0.05 |
| Fox | 9 | 0.05 |
| Rock Music | 8 | 0.05 |
| Instrumental Music | 8 | 0.05 |
| Electronic | 8 | 0.05 |
| Coding | 7 | 0.04 |
| Birds | 7 | 0.04 |
| Steam Machine | 6 | 0.03 |
| Lara Croft | 4 | 0.02 |
| Reboot | 3 | 0.02 |
| Feature Film | 3 | 0.02 |
| Elf | 2 | 0.01 |
| VR Only | 2 | 0.01 |

### A7. 兜底（未被 META_DICT 覆盖，原标签直接进入 Meta_Tags）的取值：**166 个**

| index | meta_tag | n_games | share_pct |
|---|---|---|---|
| 12 | Atmospheric | 4,424 | 25.01 |
| 15 | Exploration | 3,180 | 17.98 |
| 19 | Female Protagonist | 2,489 | 14.07 |
| 20 | Colorful | 2,450 | 13.85 |
| 22 | Difficult | 1,913 | 10.82 |
| 26 | Arcade | 1,756 | 9.93 |
| 29 | Violent | 1,562 | 8.83 |
| 31 | Stylized | 1,327 | 7.50 |
| 32 | Character Customization | 1,270 | 7.18 |
| 33 | Combat | 1,199 | 6.78 |
| 35 | Physics | 1,106 | 6.25 |
| 36 | Tactical | 1,010 | 5.71 |
| 37 | Cartoony | 1,003 | 5.67 |
| 38 | Side Scroller | 934 | 5.28 |
| 39 | Turn-Based | 917 | 5.18 |
| 40 | Turn-Based Combat | 897 | 5.07 |
| 41 | Immersive Sim | 857 | 4.85 |
| 42 | Emotional | 776 | 4.39 |
| 43 | Surreal | 734 | 4.15 |
| 44 | Old School | 647 | 3.66 |
| 45 | Short | 642 | 3.63 |
| 46 | Linear | 637 | 3.60 |
| 47 | Cartoon | 616 | 3.48 |
| 48 | Dark Humor | 571 | 3.23 |
| 49 | 1990's | 567 | 3.21 |
| 50 | Cinematic | 541 | 3.06 |
| 51 | Fast-Paced | 540 | 3.05 |
| 52 | Narration | 493 | 2.79 |
| 53 | Psychological | 461 | 2.61 |
| 54 | Nature | 440 | 2.49 |
| 55 | RPGMaker | 431 | 2.44 |
| 56 | Education | 426 | 2.41 |
| 57 | Clicker | 410 | 2.32 |
| 58 | Competitive | 380 | 2.15 |
| 59 | Conversation | 356 | 2.01 |
| 60 | Team-Based | 355 | 2.01 |
| 61 | Score Attack | 346 | 1.96 |
| 62 | Idler | 333 | 1.88 |
| 63 | Level Editor | 328 | 1.85 |
| 64 | 1980s | 319 | 1.80 |
| 65 | Psychedelic | 315 | 1.78 |
| 66 | Abstract | 315 | 1.78 |
| 67 | Destruction | 306 | 1.73 |
| 68 | Experimental | 304 | 1.72 |
| 69 | Comic Book | 297 | 1.68 |
| 70 | Flight | 297 | 1.68 |
| 71 | Nonlinear | 289 | 1.63 |
| 72 | Collectathon | 282 | 1.59 |
| 73 | Cats | 268 | 1.52 |
| 74 | Modern | 253 | 1.43 |
| 75 | Dark Comedy | 246 | 1.39 |
| 76 | Artificial Intelligence | 230 | 1.30 |
| 77 | Capitalism | 224 | 1.27 |
| 78 | Rhythm | 222 | 1.26 |
| 79 | Noir | 209 | 1.18 |
| 80 | Creature Collector | 205 | 1.16 |
| 81 | Trading | 198 | 1.12 |
| 82 | Philosophical | 198 | 1.12 |
| 83 | Split Screen | 197 | 1.11 |
| 84 | Science | 191 | 1.08 |
| 85 | Tutorial | 190 | 1.07 |
| 86 | Cooking | 189 | 1.07 |
| 87 | Political | 183 | 1.03 |
| 88 | Remake | 181 | 1.02 |
| 89 | Co-op Campaign | 179 | 1.01 |
| 90 | Parody | 171 | 0.97 |
| 91 | FMV | 170 | 0.96 |
| 92 | Narrative | 155 | 0.88 |
| 93 | Design & Illustration | 154 | 0.87 |
| 94 | Gun Customization | 150 | 0.85 |
| 95 | Class-Based | 150 | 0.85 |
| 96 | Real-Time | 148 | 0.84 |
| 97 | Fishing | 147 | 0.83 |
| 99 | America | 145 | 0.82 |
| 100 | Grid-Based Movement | 145 | 0.82 |
| 101 | Hacking | 142 | 0.80 |
| 102 | Cult Classic | 142 | 0.80 |
| 103 | Politics | 141 | 0.80 |
| 104 | Hex Grid | 135 | 0.76 |
| 105 | Satire | 135 | 0.76 |
| 106 | Villain Protagonist | 132 | 0.75 |
| 107 | Mining | 131 | 0.74 |
| 108 | Illuminati | 130 | 0.74 |
| 109 | Real-Time with Pause | 129 | 0.73 |
| 110 | Diplomacy | 129 | 0.73 |
| 111 | Bullet Time | 129 | 0.73 |
| 112 | Battle Royale | 122 | 0.69 |
| 113 | Dog | 121 | 0.68 |
| 114 | Trains | 119 | 0.67 |
| 115 | Dinosaurs | 117 | 0.66 |
| 116 | Time Travel | 117 | 0.66 |
| 117 | Conspiracy | 115 | 0.65 |
| 118 | Faith | 114 | 0.64 |
| 119 | Programming | 114 | 0.64 |
| 120 | Hunting | 111 | 0.63 |
| 121 | Dynamic Narration | 108 | 0.61 |
| 122 | Underwater | 107 | 0.60 |
| 123 | Time Manipulation | 107 | 0.60 |
| 124 | Kickstarter | 101 | 0.57 |
| 125 | Immersive | 100 | 0.57 |
| 126 | 6DOF | 97 | 0.55 |
| 127 | Sequel | 90 | 0.51 |
| 128 | Action RTS | 85 | 0.48 |
| 129 | Underground | 84 | 0.47 |
| 130 | Superhero | 83 | 0.47 |
| 131 | Touch-Friendly | 81 | 0.46 |
| 132 | Minigames | 76 | 0.43 |
| 133 | Quick-Time Events | 75 | 0.42 |
| 134 | Typing | 73 | 0.41 |
| 135 | Episodic | 72 | 0.41 |
| 136 | Experience | 72 | 0.41 |
| 137 | Nostalgia | 72 | 0.41 |
| 138 | Foreign | 64 | 0.36 |
| 139 | Animation & Modeling | 64 | 0.36 |
| 140 | Time Attack | 63 | 0.36 |
| 141 | Gambling | 60 | 0.34 |
| 142 | Snow | 60 | 0.34 |
| 143 | Dwarf | 57 | 0.32 |
| 144 | Horses | 55 | 0.31 |
| 145 | Bikes | 54 | 0.31 |
| 146 | Social Deduction | 49 | 0.28 |
| 147 | Games Workshop | 49 | 0.28 |
| 148 | GameMaker | 49 | 0.28 |
| 149 | Mars | 49 | 0.28 |
| 150 | Archery | 45 | 0.25 |
| 151 | Music-Based Procedural Generation | 43 | 0.24 |
| 152 | Werewolves | 42 | 0.24 |
| 153 | Submarine | 38 | 0.21 |
| 154 | Unforgiving | 37 | 0.21 |
| 155 | Video Production | 36 | 0.20 |
| 156 | Jet | 34 | 0.19 |
| 157 | Silent Protagonist | 34 | 0.19 |
| 158 | Dungeons & Dragons | 32 | 0.18 |
| 159 | LEGO | 31 | 0.18 |
| 160 | Warhammer 40K | 30 | 0.17 |
| 161 | Jump Scare | 28 | 0.16 |
| 162 | Audio Production | 28 | 0.16 |
| 163 | Spaceships | 27 | 0.15 |
| 164 | Photo Editing | 26 | 0.15 |
| 165 | Software Training | 21 | 0.12 |
| 166 | Web Publishing | 21 | 0.12 |
| 167 | Intentionally Awkward Controls | 19 | 0.11 |
| 168 | Pool | 19 | 0.11 |
| 169 | Based On A Novel | 19 | 0.11 |
| 170 | Gaming | 17 | 0.10 |
| 171 | Well-Written | 17 | 0.10 |
| 172 | Electronic Music | 16 | 0.09 |
| 173 | nan | 16 | 0.09 |
| 174 | Shop Keeper | 15 | 0.08 |
| 175 | TrackIR | 11 | 0.06 |
| 176 | Voice Control | 11 | 0.06 |
| 177 | Hardware | 10 | 0.06 |
| 178 | Lemmings | 10 | 0.06 |
| 179 | Ambient | 9 | 0.05 |
| 180 | Fox | 9 | 0.05 |
| 181 | Rock Music | 8 | 0.05 |
| 182 | Instrumental Music | 8 | 0.05 |
| 183 | Electronic | 8 | 0.05 |
| 184 | Coding | 7 | 0.04 |
| 185 | Birds | 7 | 0.04 |
| 186 | Steam Machine | 6 | 0.03 |
| 187 | Lara Croft | 4 | 0.02 |
| 188 | Reboot | 3 | 0.02 |
| 189 | Feature Film | 3 | 0.02 |
| 190 | Elf | 2 | 0.01 |
| 191 | VR Only | 2 | 0.01 |

- 这些兜底标签合计贡献 52636 次「元标签计数」
- 占全部元标签计数的 31.95%（总计数 164753）

## B. 小表核查

### B1. cluster_megatag_reference.csv
| cluster_id | n_games | share_pct | defining_meta_tags | mean_hybrid_index | median_hybrid_index | min_hybrid_index | max_hybrid_index |
|---|---|---|---|---|---|---|---|
| 0 | 2,060 | 11.6500 | Adventure/Narrative; Story-Driven; Mood (Dark); Perspective; Atmospheric | 11.8630 | 12 | 3 | 18 |
| 1 | 3,238 | 18.3100 | Action; Perspective; Shooter; Art Style; Adventure/Narrative | 8.6030 | 9 | 1 | 18 |
| 2 | 2,462 | 13.9200 | RPG; Adventure/Narrative; Perspective; Art Style; Strategy | 10.1400 | 11 | 1 | 17 |
| 3 | 1,605 | 9.0700 | Casual; Mood (Positive); Perspective; Puzzle/Board; Art Style | 11.3680 | 12 | 3 | 20 |
| 4 | 2,880 | 16.2800 | Adventure/Narrative; Casual; Art Style; Adult; Story-Driven | 6.3720 | 6 | 0 | 17 |
| 5 | 1,542 | 8.7200 | Simulation; Core System; Perspective; Adventure/Narrative; Action | 11.2280 | 11 | 4 | 17 |
| 6 | 1,232 | 6.9700 | Platformer; Action; Perspective; Adventure/Narrative; Art Style | 11.9310 | 12 | 3 | 18 |
| 7 | 2,667 | 15.0800 | Simulation; Strategy; Casual; Perspective; Sports/Racing | 7.0760 | 7 | 1 | 17 |

- Σ n_games = **17686**（应为 17686）
- Σ share_pct = **100.00**
- 与事实表分簇计数一致: True

### B2. cluster_cohens_h_tags.csv
| cluster_id | meta_tag | cohens_h | share_in_cluster | share_global |
|---|---|---|---|---|
| 0 | Story-Driven | 1.3204 | 0.8961 | 0.3026 |
| 0 | Mood (Dark) | 1.0709 | 0.7510 | 0.2408 |
| 0 | Adventure/Narrative | 1.0284 | 0.9655 | 0.5841 |
| 0 | Atmospheric | 1.0103 | 0.7340 | 0.2501 |
| 0 | Exploration | 0.7125 | 0.5087 | 0.1798 |
| 1 | Action | 1.4763 | 0.9929 | 0.4629 |
| 1 | Shooter | 0.7519 | 0.4920 | 0.1527 |
| 1 | Arcade/Top-Down Shooter | 0.5055 | 0.2384 | 0.0648 |
| 1 | Arcade | 0.4375 | 0.2637 | 0.0993 |
| 1 | Violent | 0.3280 | 0.2017 | 0.0883 |
| 2 | RPG | 1.8913 | 0.9968 | 0.2895 |
| 2 | Fantasy/Magic | 0.7094 | 0.5292 | 0.1970 |
| 2 | Turn-Based Combat | 0.6424 | 0.2717 | 0.0507 |
| 2 | Turn-Based | 0.5261 | 0.2238 | 0.0518 |
| 2 | Roguelike | 0.4685 | 0.2677 | 0.0928 |
| 3 | Casual | 1.3929 | 0.9526 | 0.3711 |
| 3 | Mood (Positive) | 1.2564 | 0.9003 | 0.3389 |
| 3 | Colorful | 0.7513 | 0.4717 | 0.1385 |
| 3 | Puzzle/Board | 0.7368 | 0.6081 | 0.2521 |
| 3 | Perspective | 0.4618 | 0.8474 | 0.6507 |
| 4 | Casual | 0.5257 | 0.6309 | 0.3711 |
| 4 | Adventure/Narrative | 0.4929 | 0.8073 | 0.5841 |
| 4 | Adult | 0.4593 | 0.2906 | 0.1110 |
| 4 | Female Protagonist | 0.1865 | 0.2115 | 0.1407 |
| 4 | Short | 0.1554 | 0.0708 | 0.0363 |
| 5 | Core System | 1.5036 | 0.9475 | 0.3075 |
| 5 | Simulation | 1.5018 | 0.9676 | 0.3555 |
| 5 | Exploration | 0.7261 | 0.5156 | 0.1798 |
| 5 | Immersive Sim | 0.4598 | 0.1907 | 0.0485 |
| 5 | Perspective | 0.4553 | 0.8450 | 0.6507 |
| 6 | Platformer | 1.8566 | 0.9375 | 0.1444 |
| 6 | Action | 1.1672 | 0.9440 | 0.4629 |
| 6 | Side Scroller | 0.8878 | 0.3912 | 0.0528 |
| 6 | Perspective | 0.7362 | 0.9318 | 0.6507 |
| 6 | Difficult | 0.6023 | 0.3531 | 0.1082 |
| 7 | Strategy | 0.9947 | 0.7398 | 0.2627 |
| 7 | Simulation | 0.9645 | 0.8110 | 0.3555 |
| 7 | Tactical | 0.3387 | 0.1594 | 0.0571 |
| 7 | Sports/Racing | 0.3310 | 0.2036 | 0.0888 |
| 7 | Military/Combat | 0.3132 | 0.1774 | 0.0754 |

Cohen's h ≥ 0.5 的强定义标签：
- 簇 0: Story-Driven (1.32), Mood (Dark) (1.07), Adventure/Narrative (1.03), Atmospheric (1.01), Exploration (0.71)
- 簇 1: Action (1.48), Shooter (0.75), Arcade/Top-Down Shooter (0.51)
- 簇 2: RPG (1.89), Fantasy/Magic (0.71), Turn-Based Combat (0.64), Turn-Based (0.53)
- 簇 3: Casual (1.39), Mood (Positive) (1.26), Colorful (0.75), Puzzle/Board (0.74)
- 簇 4: Casual (0.53)
- 簇 5: Core System (1.50), Simulation (1.50), Exploration (0.73)
- 簇 6: Platformer (1.86), Action (1.17), Side Scroller (0.89), Perspective (0.74), Difficult (0.60)
- 簇 7: Strategy (0.99), Simulation (0.96)

### B3. all_tags.txt
- 行数（非空）= **448**，唯一值 = **448**，重复 = 0
- `Meta_Tags` 词表中**不在** `all_tags.txt` 且不属于 META_DICT 类别的标签（2 个）：
  ['VR Only', 'nan']

## C. 主模型独立重估（numpy OLS）

- 回归样本 N = **17670**（事实表 17686 减去杂交度为 0 的 16 个）

- N = 17670, k = 14, R² = **0.1623**, Adj. R² = 0.1616, Durbin-Watson = **0.343**, sigma = 1.4003

核心系数（经典标准误与 HC1 稳健标准误并列）：

| 变量 | coef | SE(classic) | t(classic) | SE(HC1) | t(HC1) |  |
|---|---|---|---|---|---|---|
| const | 6.4898 | 0.0396 | 163.6947 | 0.0403 | 161.2112 | *** |
| Hybrid_Centered | 0.0761 | 0.0033 | 23.2209 | 0.0032 | 23.7948 | *** |
| Hybrid_Centered_Squared | -0.0145 | 0.0007 | -19.3990 | 0.0007 | -21.3039 | *** |
| price | 0.0381 | 0.0009 | 41.6816 | 0.0016 | 23.6174 | *** |

- 拐点（原尺度） = 9.3145 + (−0.07613/(2×-0.01454)) = **11.93**

年份固定效应（HC1）：

| 年份 | coef | SE(HC1) | t(HC1) |
|---|---|---|---|
| Y_2016 | -0.0450 | 0.0454 | -0.9920 |
| Y_2017 | -0.1608 | 0.0465 | -3.4581 |
| Y_2018 | -0.1501 | 0.0477 | -3.1443 |
| Y_2019 | -0.1521 | 0.0505 | -3.0134 |
| Y_2020 | -0.2774 | 0.0492 | -5.6325 |
| Y_2021 | -0.4487 | 0.0527 | -8.5111 |
| Y_2022 | -0.5918 | 0.0545 | -10.8552 |
| Y_2023 | -0.6331 | 0.0520 | -12.1787 |
| Y_2024 | -0.7830 | 0.0481 | -16.2762 |
| Y_2025 | -0.9151 | 0.0816 | -11.2155 |

## D. 追加：含题材簇固定效应的主模型（P0 改进预演）

- N = 17670, R² = **0.1757**（主模型 0.1623）

| 变量 | coef | SE(classic) | t(classic) | SE(HC1) | t(HC1) |  |
|---|---|---|---|---|---|---|
| const | 6.4682 | 0.0502 | 128.7722 | 0.0502 | 128.7893 | *** |
| Hybrid_Centered | 0.0866 | 0.0037 | 23.1139 | 0.0037 | 23.4460 | *** |
| Hybrid_Centered_Squared | -0.0141 | 0.0007 | -18.8913 | 0.0007 | -20.7924 | *** |
| price | 0.0365 | 0.0009 | 39.3574 | 0.0016 | 22.4366 | *** |

- 拐点 = **12.38**

### D1. 分簇单独估计倒 U（检验结论是否由题材构成驱动）
| cluster | N | R2 | beta1 | t1(HC1) | beta2 | t2(HC1) | peak | mean_hybrid |
|---|---|---|---|---|---|---|---|---|
| 0 | 2,060 | 0.1713 | 0.0883 | 4.5858 | -0.0147 | -3.9537 | 14.8762 | 11.8626 |
| 1 | 3,238 | 0.2336 | 0.1097 | 12.1534 | -0.0146 | -7.6779 | 12.3644 | 8.6028 |
| 2 | 2,462 | 0.1975 | 0.1174 | 13.7521 | -0.0115 | -5.1343 | 15.2571 | 10.1397 |
| 3 | 1,605 | 0.0504 | 0.0297 | 1.8714 | -0.0098 | -3.2493 | 12.8873 | 11.3682 |
| 4 | 2,864 | 0.1600 | 0.1135 | 9.0827 | -0.0063 | -3.4089 | 15.4225 | 6.4071 |
| 5 | 1,542 | 0.1824 | 0.0261 | 1.0149 | -0.0187 | -3.7720 | 11.9271 | 11.2283 |
| 6 | 1,232 | 0.1358 | 0.1031 | 6.7081 | -0.0163 | -4.9920 | 15.0986 | 11.9310 |
| 7 | 2,667 | 0.1625 | 0.0618 | 4.4644 | -0.0169 | -7.5089 | 8.9106 | 7.0757 |

## E. 追加：函数形式与稳健性对照

### E1. 二次项 vs 分箱均值（无参数证据）
| Hybridization_Index | N | mean_logrev | mean_hybrid |
|---|---|---|---|
| (0, 4] | 2,477 | 5.565 | 3.017 |
| (4, 7] | 2,803 | 6.082 | 6.027 |
| (7, 10] | 4,601 | 6.670 | 9.146 |
| (10, 12] | 4,139 | 6.701 | 11.505 |
| (12, 14] | 2,783 | 6.594 | 13.393 |
| (14, 16] | 795 | 6.301 | 15.293 |
| (16, 25] | 72 | 6.516 | 17.208 |

### E2. 用好评率替代因变量（需求 vs 合法性）
- 因变量 = 好评率（%），N = 17670, R² = 0.0672

| 变量 | coef | SE(classic) | t(classic) | SE(HC1) | t(HC1) |  |
|---|---|---|---|---|---|---|
| Hybrid_Centered | 0.8057 | 0.0383 | 21.0452 | 0.0396 | 20.3552 | *** |
| Hybrid_Centered_Squared | -0.0872 | 0.0088 | -9.9607 | 0.0102 | -8.5715 | *** |
| price | -0.0461 | 0.0107 | -4.3197 | 0.0139 | -3.3120 | *** |

### E3. 加入质量/投入代理变量（缓解遗漏变量）
- N = 17670, R² = 0.6940

| 变量 | coef | SE(classic) | t(classic) | SE(HC1) | t(HC1) |  |
|---|---|---|---|---|---|---|
| Hybrid_Centered | 0.0546 | 0.0020 | 27.1217 | 0.0020 | 26.6914 | *** |
| Hybrid_Centered_Squared | -0.0061 | 0.0005 | -13.2700 | 0.0005 | -13.3296 | *** |
| price | -0.0001 | 0.0006 | -0.1712 | 0.0008 | -0.1306 |  |
| ln_playtime | 0.0799 | 0.0026 | 30.8675 | 0.0029 | 27.7086 | *** |
| ln_achievements | 0.0213 | 0.0042 | 5.1382 | 0.0045 | 4.7235 | *** |
| ln_dlc | 0.1263 | 0.0103 | 12.2566 | 0.0122 | 10.3174 | *** |
| ln_peak_ccu | 0.5691 | 0.0040 | 141.4023 | 0.0050 | 113.0453 | *** |

- 拐点 = **13.83**

## F. 原始数据形状核对

- 原始 CSV 读入行数 = **89618**，列数（全表）= 48
- 其中 `genres/categories/tags_counts` 任一为空的行数: 1000
- dropna 后行数 = **88618**（notebook 打印 88618）
- 年份过滤后 = 85884
- 评论数 ≥ 100 后 = 17772（notebook 最终 17686，差异来自大厂剔除与 priority 过滤）