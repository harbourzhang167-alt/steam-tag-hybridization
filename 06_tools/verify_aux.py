# -*- coding: utf-8 -*-
"""Verify whitespace contamination, centring denominator, dead dict keys, sample frame."""
import sys
from pathlib import Path
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
lines = []
def p(*a):
    s = " ".join(str(x) for x in a); lines.append(s); print(s)

df = pd.read_csv(ROOT / "01_data/processed/games_clustered_meta_export.csv")
exp = df.copy()

p("## 1. 中心化分母核对")
mean_all = df.Hybridization_Index.mean()
reg = df[df.Hybridization_Index > 0]
mean_reg = reg.Hybridization_Index.mean()
p(f"- 17,686 行均值 = {mean_all:.10f}")
p(f"- 17,670 行（回归样本）均值 = {mean_reg:.10f}")
p(f"- 差值 = {mean_reg - mean_all:+.6f}")
p(f"- 导出的 Hybrid_Centered 是否以 17,686 均值计算: "
  f"max|HC-(H-mean_all)| = {(df.Hybrid_Centered-(df.Hybridization_Index-mean_all)).abs().max():.2e}")
p(f"- 若改用回归样本均值，拐点变化 = {(-(-0.07606/(2*-0.01446))) - (-(-0.07606/(2*-0.01446))):.4f}（同斜率下仅截距/拐点平移 {mean_reg-mean_all:+.4f}）")

p("")
p("## 2. 标签空白污染（尾随/前导空格）")
raw = pd.read_csv(ROOT / "01_data/raw/steam_games_march2025_updated.csv",
                  usecols=["appid", "tags", "genres", "categories", "tags_counts",
                           "positive", "negative", "release_date", "estimated_owners"])
import ast, re
from collections import Counter
bad_games, bad_tags = [], Counter()
tag_dirty_pairs = Counter()
checked = 0
for appid, tg in zip(raw.appid.values, raw.tags.values):
    if not isinstance(tg, str):
        continue
    checked += 1
    try:
        d = ast.literal_eval(tg)
    except Exception:
        continue
    if not isinstance(d, dict):
        continue
    hits = [k for k in d if isinstance(k, str) and k != k.strip()]
    if hits:
        bad_games.append(appid)
        for h in hits:
            bad_tags[h] += 1
p(f"- 扫描原始数据 {checked:,} 行（含 tags 字典）")
p(f"- 含「首尾空白」标签的游戏数 = **{len(bad_games)}**（{100*len(bad_games)/checked:.2f}%）")
p(f"- 受影响的脏标签（共 {len(bad_tags)} 种），Top 15：")
for k, v in bad_tags.most_common(15):
    p(f"    - {k!r}: {v}")

p("")
p("## 3. Meta_Tags 中出现的异常取值")
meta = exp.Meta_Tags.fillna("").apply(lambda s: [t.strip() for t in str(s).split(";") if t.strip()])
c = Counter(t for l in meta for t in l)
odd = [k for k in c if k != k.strip() or k.lower() == "nan" or k.endswith(" ")]
p(f"- 含空白/nan 的元标签取值: {odd}")
p(f"- 'Dystopian' 次数 = {c.get('Dystopian',0)}；'Parody' = {c.get('Parody',0)}")
p(f"- 说明：`_csv_s()` 用 '; ' 连接，若原标签带尾随空格，导出后会出现 'Dystopian ; NextTag'，"
  f"split(';')+strip 会还原，故导出文件本身看不到空格，但管线内部 META_DICT.get('Dystopian ') 失败。")

p("")
p("## 4. META_DICT 死键检查（字典里指向自身但数据中不存在的标签）")
def parse_meta_dict(nb_path):
    import json
    nb = json.loads(nb_path.read_text(encoding="utf-8"))
    for cell in nb["cells"]:
        if cell["cell_type"] != "code":
            continue
        src = "".join(cell["source"])
        if "META_DICT = {" in src:
            start = src.index("META_DICT = {")
            depth = 0
            for i in range(start + len("META_DICT = "), len(src)):
                if src[i] == "{":
                    depth += 1
                elif src[i] == "}":
                    depth -= 1
                    if depth == 0:
                        end = i + 1
                        break
            literal = src[start + len("META_DICT = "):end]
            return eval(literal)
    return None

_nb = next(iter(ROOT.glob("**/4dissertation_gamespace_clustering_new.ipynb")), None)
if _nb is None:
    raise SystemExit("notebook not found under workspace root")
md = parse_meta_dict(_nb)
p(f"- 解析出 META_DICT 键数 = {len(md)}（含重复键）")
vals = sorted(set(v for v in md.values() if v != "IGNORE"))
p(f"- 映射目标类别（去重，含 IGNORE）= {len(vals)}；不含 IGNORE = {len([v for v in vals if v!='IGNORE'])}")
all_raw_tags = set()
for tg in raw.tags.dropna():
    try:
        d = ast.literal_eval(tg)
        if isinstance(d, dict):
            all_raw_tags.update(str(k) for k in d)
    except Exception:
        pass
p(f"- 原始 tags 中出现的不同标签数（全量口径）= **{len(all_raw_tags)}**")
dead = sorted(k for k in md if k not in all_raw_tags)
p(f"- 字典中在原始数据里**从未出现**的键（{len(dead)} 个）: {dead}")
missing = sorted(t for t in all_raw_tags if t not in md)
p(f"- 原始数据中出现但字典**未覆盖**的标签数 = **{len(missing)}**（占 {100*len(missing)/len(all_raw_tags):.1f}%）")
missing_freq = Counter()
for tg in raw.tags.dropna():
    try:
        d = ast.literal_eval(tg)
    except Exception:
        continue
    if isinstance(d, dict):
        for k in d:
            if str(k) not in md:
                missing_freq[str(k)] += 1
top_missing = pd.DataFrame(sorted(missing_freq.items(), key=lambda kv: -kv[1])[:25],
                           columns=["未覆盖标签", "出现游戏数"])
p("")
p("- 未覆盖标签 Top 25（全量原始数据口径）：")
p("")
p("| 未覆盖标签 | 出现游戏数 |")
p("|---|---|")
for r in top_missing.itertuples(index=False):
    p(f"| {r[0]} | {r[1]:,} |")

p("")
p("## 5. 样本框算术核对")
d0 = raw.copy()
d0["rd"] = pd.to_datetime(d0.release_date, errors="coerce")
d0["yr"] = d0.rd.dt.year
d0["tr"] = d0.positive + d0.negative
step = d0.dropna(subset=["genres", "categories", "tags_counts"])
p(f"- 载入 {len(d0):,} → dropna {len(step):,}")
s1 = step[(step.yr >= 2015) & (step.yr <= 2025)]
p(f"- 年份 2015–2025 后 = {len(s1):,}")
s2 = s1[s1.tr >= 100]
p(f"- 评论 ≥ 100 后 = {len(s2):,}（notebook: 17686，需再扣大厂与 priority 过滤）")
owners_excl = {"5000000-10000000", "10000000-20000000", "20000000-50000000",
               "50000000-100000000", "100000000-200000000", "200000000-500000000"}
def has_indie(g):
    return "Indie" in [x.strip() for x in str(g).split(",")]
own = s2.estimated_owners.astype(str).str.replace(r"\s+", "", regex=True)
mask_nonindie = (~s2.genres.apply(has_indie)) & own.isin(owners_excl)
p(f"- 非 Indie 且 owner ≥ 5,000,000 的样本 = **{int(mask_nonindie.sum())}** 个")
s3 = s2[~mask_nonindie]
p(f"- 剔除后 = {len(s3):,}")
p(f"- 与导出 17,686 的差额 = {len(s3) - 17686:,}（应为 priority ≥ 0.3 后标签为空 / tags 缺失的样本）")

p("")
p("## 6. 导出文件排序与年份抽样疑点核对")
p(f"- 事实表是否按 Total_Reviews 降序: {bool((exp.Total_Reviews.diff().dropna() <= 0).all())}")
y24 = int((exp.Release_Year == 2024).sum()); y25 = int((exp.Release_Year == 2025).sum())
y21 = int((exp.Release_Year == 2021).sum())
p(f"- 2021 年样本数 = {y21:,}；2024 = {y24:,}；2025 = {y25:,}（尾部 80 行抽样为 0 属抽样偏差）")
tail = exp.tail(80)
p(f"- 事实表末尾 80 行的年份分布: {tail.Release_Year.value_counts().sort_index().to_dict()}")
p(f"- 事实表末尾 80 行的杂交度均值 = {tail.Hybridization_Index.mean():.3f}"
  f"（全样本 {exp.Hybridization_Index.mean():.3f}）")

_out = Path(__file__).resolve().parent / "aux_report.md"
_out.write_text("\n".join(lines), encoding="utf-8")
print(f"\n[written] {_out}")
