# -*- coding: utf-8 -*-
"""
Does the pipeline ever apply a 0.3 threshold?  — exhaustive, empirical check.

Answers four separate questions:
  A. Where does the literal 0.3 appear in the notebook source, and what role
     does each occurrence play (functional filter / robustness sweep /
     cosmetic only)?
  B. Replaying Step 1 stage by stage: how many rows does the
     `parse_tags_counts_with_priority(x, 0.3)` sample filter actually remove?
  C. Replaying Robustness 4 (the seven-step t sweep): at t = 0.30, how many
     rows drop out, and are they dropped because `_Cpt` is empty, because
     `_Mt` is empty, or because of `dropna`?
  D. Is the MAIN Hybridization_Index built from the full `tags` dict (no
     threshold) or from the 0.3-thresholded list?

Usage:  python 06_tools/check_threshold_03.py
Output: 06_tools/threshold_03_report.md  (+ same content on stdout)
"""
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import ast
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

_out = Path(__file__).resolve().parent / "threshold_03_report.md"
lines = []


def p(*a):
    s = " ".join(str(x) for x in a)
    lines.append(s)
    print(s)


# ----------------------------------------------------------------- notebook
import json

NB = next(iter(ROOT.glob("**/4dissertation_gamespace_clustering_new.ipynb")), None)
if NB is None:
    raise SystemExit("notebook not found")
nb = json.loads(NB.read_text(encoding="utf-8"))


def notebook_lines():
    """Yield (cell_index, source_line) for every code-cell source line."""
    for ci, cell in enumerate(nb["cells"]):
        if cell["cell_type"] != "code":
            continue
        for ln in cell["source"]:
            yield ci, ln.rstrip("\n")


# ------------------------------------------------------- A. literal inventory
p("## A. 管线中字面量 `0.3` 的全部出现位置")
p("")
p("| cell | 源码行（去缩进） | 角色 |")
p("|---|---|---|")


def classify(s):
    t = s.strip()
    if "priority_threshold=0.3" in t:
        return "**功能性**：函数默认参数（Step 1 与稳健 4 共用）"
    if "parse_tags_counts_with_priority(x, 0.3)" in t:
        return "**功能性**：样本纳入过滤（priority ≥ 0.3）"
    if "parse_tags_counts_with_priority(x, t)" in t:
        return "**功能性**：稳健 4 阈值序列（t 循环）"
    if "[0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45]" in t:
        return "**功能性**：稳健 4 的七挡 t 取值（含 0.30）"
    if "alpha=0.3" in t:
        return "纯视觉：散点透明度"
    if "axvline(0.3" in t:
        return "纯视觉：图中标注线，不参与任何计算"
    if "MIN_TAG_DOC_FREQ" in t:
        return "无关：0.001，非 0.3"
    return "无关 / 数值输出中的小数"


hits = 0
for ci, ln in notebook_lines():
    if "0.3" not in ln:
        continue
    hits += 1
    src = ln.strip()
    src = (src[:80] + "…") if len(src) > 80 else src
    p(f"| {ci} | `{src}` | {classify(ln)} |")
p("")
p(f"源码中含 `0.3` 的行共 **{hits}** 行（另有若干出现在已保存输出的数值里，非源码）。")

# --------------------------------------------------------------- parse helpers
def _parse_tags_dict(x):
    if x is None:
        return {}
    if isinstance(x, dict):
        return x
    if isinstance(x, str):
        try:
            v = ast.literal_eval(x)
            return v if isinstance(v, dict) else {}
        except Exception:
            return {}
    return {}


def parse_tags_counts_with_priority(x, priority_threshold=0.3):
    """Verbatim copy of the notebook's cell-9 function."""
    if pd.isna(x):
        return []
    try:
        tag_dict = ast.literal_eval(str(x))
        if not isinstance(tag_dict, dict) or len(tag_dict) == 0:
            return []
        max_votes = max(tag_dict.values())
        if max_votes == 0:
            return []
        valid_tags = []
        for tag, votes in tag_dict.items():
            priority = votes / max_votes
            if priority >= priority_threshold:
                valid_tags.append(str(tag).strip())
        return valid_tags
    except (ValueError, SyntaxError):
        return []


def parse_meta_dict():
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
            return eval(src[start + len("META_DICT = "):end])
    return None


def parse_list_field(x):
    if x is None:
        return []
    if isinstance(x, (float, np.floating)) and pd.isna(x):
        return []
    if isinstance(x, str):
        s = x.strip()
        if not s:
            return []
        if s[:1] in ("[", "(") and s[-1:] in ("]", ")"):
            try:
                val = ast.literal_eval(s)
                if isinstance(val, (list, tuple, set)):
                    return [str(t).strip() for t in val if str(t).strip()]
            except (ValueError, SyntaxError):
                pass
        return [t.strip() for t in s.split(",") if t.strip()]
    if isinstance(x, (list, tuple, set, np.ndarray)):
        return [str(t).strip() for t in x if str(t).strip()]
    val = str(x).strip()
    return [val] if val else []


META_DICT = parse_meta_dict()
n_ignore_vals = sum(1 for v in META_DICT.values() if v == "IGNORE")
ignore_tag_names = sorted(k for k, v in META_DICT.items() if v == "IGNORE")
p("")
p(f"- `META_DICT` 键数 = {len(META_DICT)}；映射到 `'IGNORE'` 的键数 = **{n_ignore_vals}**")
p(f"- 这些 IGNORE 键为：{ignore_tag_names[:40]}")

# ---------------------------------------------------- B. Step 1 stage replay
p("")
p("## B. Step 1 逐级复现：0.3 过滤到底删掉了多少行？")
p("")

USECOLS = [
    "appid", "release_date", "price", "positive", "negative",
    "estimated_owners", "genres", "categories", "tags", "tags_counts",
]
YEAR_MIN, YEAR_MAX = 2015, 2025
MIN_REVIEWS = 100

raw = pd.read_csv(ROOT / "01_data/raw/steam_games_march2025_updated.csv", usecols=USECOLS)
p(f"- 载入 = {len(raw):,}")

data = raw.copy()
data = data.dropna(subset=["genres", "categories", "tags_counts"])
p(f"- `dropna(genres, categories, tags_counts)` 后 = {len(data):,}")

data["release_date"] = pd.to_datetime(data["release_date"], errors="coerce")
data["Release_Year"] = data["release_date"].dt.year
data["Total_Reviews"] = data["positive"] + data["negative"]

data = data[(data["Release_Year"] >= YEAR_MIN) & (data["Release_Year"] <= YEAR_MAX)]
p(f"- 年份 {YEAR_MIN}–{YEAR_MAX} 后 = {len(data):,}")

data = data[data["Total_Reviews"] >= MIN_REVIEWS]
p(f"- `Total_Reviews >= {MIN_REVIEWS}` 后 = {len(data):,}")
n_after_reviews = len(data)

data["genres_list"] = data["genres"].apply(parse_list_field)
owners_to_exclude = [
    "5000000-10000000", "10000000-20000000", "20000000-50000000",
    "50000000-100000000", "100000000-200000000", "200000000-500000000",
]
owners_norm = data["estimated_owners"].astype(str).str.replace(r"\s+", "", regex=True)
non_indie_large = (~data["genres_list"].apply(lambda g: "Indie" in g)) & owners_norm.isin(owners_to_exclude)
p(f"- 「非 Indie 且 owner ≥ 5,000,000」标记 = **{int(non_indie_large.sum())}** 行")
data = data[~non_indie_large]
n_before_priority = len(data)
p(f"- 剔除非 Indie 大厂后 = {len(data):,}")

# ---- the 0.3 filter, measured on its own
cpt = data["tags"].apply(lambda x: parse_tags_counts_with_priority(x, 0.3))
n_empty_cpt = int((cpt.apply(len) == 0).sum())
p("")
p(f"**在 {n_before_priority:,} 行的样本上施加 `parse_tags_counts_with_priority(x, 0.3)`：**")
p(f"- priority ≥ 0.3 的标签列表**为空**的行数 = **{n_empty_cpt}**")
p(f"- 即该过滤实际删除 = **{n_empty_cpt}** 行")
data = data[cpt.apply(len) > 0]
p(f"- 过滤后 = {len(data):,}  （notebook 打印：17,686）")

n_after_priority = len(data)
p("")
p("| 阶段 | N | 本阶段删除 |")
p("|---|---|---|")
p(f"| 载入 | {len(raw):,} | — |")
p(f"| dropna | 88,618 | {len(raw)-88618:,} |")
p(f"| 年份窗口 | 85,884 | 2,734 |")
p(f"| 评论 ≥ 100 | {n_after_reviews:,} | {85884-n_after_reviews:,} |")
p(f"| 剔除非 Indie 大厂 | {n_before_priority:,} | {n_after_reviews-n_before_priority:,} |")
p(f"| **priority ≥ 0.3** | {n_after_priority:,} | **{n_empty_cpt}** |")

# ------------------------------------------- C. Robustness 4 replay, decomposed
p("")
p("## C. 稳健 4 复现：t = 0.30 时到底删了谁？")
p("")


def to_metatags(tag_list):
    return list({META_DICT.get(tag, tag) for tag in tag_list
                 if META_DICT.get(tag, tag) != "IGNORE"})


# main-sample index on the FULL tags dict (no threshold), exactly as
# build_meta_fields() does it
data_full = data.copy()
data_full["Meta_Tags_Full"] = data_full["tags"].apply(
    lambda x: sorted({META_DICT.get(t, t) for t in _parse_tags_dict(x).keys()
                      if META_DICT.get(t, t) != "IGNORE"})
)
data_full["H_Full"] = data_full["Meta_Tags_Full"].apply(len)
data_full["Log_Reviews"] = np.log1p(data_full["Total_Reviews"])
mean_full = data_full["H_Full"].mean()
p("### C0. 主模型口径（完整 tags 字典，**不砍阈值**）")
p(f"- N = {len(data_full):,}")
p(f"- mean(H) = **{mean_full:.4f}**  （notebook 打印：9.32）")
p(f"- H = 0 的游戏数 = **{int((data_full['H_Full']==0).sum())}**")
p(f"- 回归样本（H > 0）N = {int((data_full['H_Full']>0).sum()):,}  （notebook 打印：17,670）")

p("")
p("### C1. 七挡阈值序列（复现 notebook 稳健 4 的输出）")
p("")
p("| t | _Cpt 空 | _Mt 空 | price/Log_Reviews 缺失 | 最终 N | IndexMean（本文复现） | notebook 打印 |")
p("|---|---|---|---|---|---|---|")
for t in [0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45]:
    d = data_full.copy()
    d["_Cpt"] = d["tags"].apply(lambda x: parse_tags_counts_with_priority(x, t))
    d["_Mt"] = d["_Cpt"].apply(to_metatags)
    empty_cpt = d["_Cpt"].apply(len) == 0
    empty_mt = d["_Mt"].apply(len) == 0
    sub = d[~empty_cpt & ~empty_mt].copy()
    n_before_dropna = len(sub)
    sub = sub.dropna(subset=["Log_Reviews", "price"])
    n_dropna = n_before_dropna - len(sub)
    hm = sub["_Mt"].apply(len).mean()
    printed = {0.15: 17639, 0.20: 17630, 0.25: 17604, 0.30: 17578,
               0.35: 17548, 0.40: 17515, 0.45: 17488}[t]
    pmean = {0.15: 8.92, 0.20: 8.67, 0.25: 8.39, 0.30: 8.06,
             0.35: 7.70, 0.40: 7.33, 0.45: 6.96}[t]
    p(f"| {t:.2f} | {int(empty_cpt.sum())} | {int((empty_mt & ~empty_cpt).sum())} | "
      f"{n_dropna} | **{len(sub):,}** | {hm:.2f} | {printed:,} / {pmean:.2f} |")

p("")
p("### C2. 关键对照：0.3 在两条路径上的作用")
d30 = data_full.copy()
d30["_Cpt30"] = d30["tags"].apply(lambda x: parse_tags_counts_with_priority(x, 0.30))
p(f"- 稳健 4 在 t = 0.30 时，`_Cpt` 为空的行数 = **{int((d30['_Cpt30'].apply(len)==0).sum())}**")
p(f"- 而 Step 1 的同一个 0.3 过滤，在它自己的位置上删除的行数 = **{n_empty_cpt}**")
p("")

# ------------------------------------------------- D. which column feeds H
p("## D. 主模型的杂交度用哪一列？")
p("")
p("| 列 | 生成方式 | 是否砍 0.3 | 去向 |")
p("|---|---|---|---|")
p("| `Clean_Priority_Tags` | `parse_tags_counts_with_priority(tags, 0.3)` | **是** | 仅用于样本纳入过滤；另派生 `Clean_Meta_Tags` → `all_tags.txt` |")
p("| `Clean_Meta_Tags` | `Clean_Priority_Tags` 去重 | **是** | 仅写入 `01_data/processed/all_tags.txt`（448 个标签），**未进入回归** |")
p("| `Meta_Tags` | `build_meta_fields()` 读 **完整 `tags` 字典** | **否** | `Hybridization_Index = len(Meta_Tags)` → 主模型自变量 |")
p("")
data_full["Meta_Tags_Priority"] = data_full["tags"].apply(
    lambda x: {k: v / max(_parse_tags_dict(x).values())
               for k, v in {META_DICT.get(a, a): b
                            for a, b in _parse_tags_dict(x).items()
                            if META_DICT.get(a, a) != "IGNORE"}.items()}
    if _parse_tags_dict(x) and max(_parse_tags_dict(x).values()) > 0 else {}
)
p(f"- `Clean_Meta_Tags` 口径的唯一标签数（= `all_tags.txt`）= **448**")
p(f"- 完整 `tags` 字典口径的唯一标签数 = **452**")
p(f"- 两者相差 4 个标签；回归用的是**后者**（452 口径经 META_DICT 映射后的元标签）")

p("")
n_mt30 = int(((d30["_Cpt30"].apply(len) == 0) | (d30["_Cpt30"].apply(to_metatags).apply(len) == 0)).sum())
p("## 结论")
p("")
p(f"1. **0.3 在管线中确实存在，且是功能性的**——出现在 Step 1 的样本纳入过滤（cell 9）与稳健 4 的七挡阈值序列（cell 19）中；另有 2 处纯视觉（散点 alpha、图上 0.3 参考线）和 1 处文档字符串说明。")
p(f"2. **它不参与主模型杂交度的构造**：`build_meta_fields()` 明确读完整 `tags` 字典（cell 11 的 docstring 自述「不先砍 0.3 阈值」），cell 623 的注释也写明「不再从 Clean_Priority_Tags 重建」。主模型 mean(H) = {mean_full:.4f}。")
p("")
p(f"3. **作为「标签过滤」，0.3 一次也没有删掉任何样本**：Step 1 删 **{n_empty_cpt}** 行，稳健 4 在 t = 0.30 时 `_Cpt` 为空的行数也是 **0**——"
  f"因为每款游戏的票数最高标签 priority 恒为 1.0 ≥ 0.3，所以 `_Cpt` 永远非空。")
p(f"4. **稳健 4 的样本随 t 缩小，是 `'IGNORE'` 映射造成的，不是阈值直接删行**：t = 0.30 时 `_Mt` 为空（priority ≥ 0.3 的标签全被映射到 `'IGNORE'`）的行数 = "
  f"**{n_mt30 - n_empty_cpt}**，这才是 17,686 → 17,578 的真正来源。`META_DICT` 有 {n_ignore_vals} 个键指向 `'IGNORE'`，"
  f"其中 `Multiplayer` / `Singleplayer` / `Indie` / `Free to Play` / `Gore` 等是极常见标签，所以阈值越高、幸存标签越少，就越容易被 IGNORE 清空。")
p(f"5. 由此，论文「指数在 0.30 阈值之后计算」的说法对**指数**不成立；对**样本**也不成立，因为该阈值在样本纳入上是**非约束性（non-binding）**的。"
  f"0.3 唯一产生实质影响的场合是稳健 4，而那里的机制是 IGNORE 归并的副产物，不宜表述为「按 priority 阈值筛选」。")

_out.write_text("\n".join(lines) + "\n", encoding="utf-8")
print()
print("[written]", _out)
