# -*- coding: utf-8 -*-
"""
Apply the agreed corrections to the main pipeline notebook, in place.

Corrections (see 06_tools/CHANGELOG_corrections.md):
  C1  cov_type="HC3" on every OLS fit
  C2  .strip() normalisation of META_DICT keys and of the tags-dict keys
  C3  Robustness 4 holds the estimation sample FIXED and only varies the index
  C4  results are persisted to 02_pipeline/results/
  C5  verified facts annotated in-place (non-binding 0.3 filter)

The script verifies that every replacement matches the expected number of
times, and refuses to write if any replacement is ambiguous.

Usage:  python 06_tools/apply_notebook_fixes.py [--check]
"""
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
NB = ROOT / "02_pipeline" / "4dissertation_gamespace_clustering_new.ipynb"
CHECK_ONLY = "--check" in sys.argv

orig_text = NB.read_text(encoding="utf-8")
nb = json.loads(orig_text)
report = []

# --- idempotency guard -----------------------------------------------------
_ALL = "\n".join("".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code")
if 'cov_type="HC3"' in _ALL and "sub = reg_data.copy()" in _ALL:
    print("✅ C1–C5 修正**已经应用**（检测到 cov_type=\"HC3\" 与固定样本的稳健 4）。")
    print("   如需重新应用，请先回滚到备份：")
    baks = sorted(NB.parent.glob(NB.name + ".bak-*"))
    for b in baks[-3:]:
        print(f"     Copy-Item 02_pipeline\\{b.name} 02_pipeline\\{NB.name} -Force")
    raise SystemExit(0)
# ---------------------------------------------------------------------------


def cell_src(cell):
    return "".join(cell["source"])


def set_src(cell, text):
    cell["source"] = text.splitlines(keepends=True)


def replace_in_cell(idx, old, new, expected=1, label=""):
    src = cell_src(nb["cells"][idx])
    n = src.count(old)
    if n != expected:
        raise SystemExit(f"❌ [{label}] 期望 {expected} 处匹配，实际 {n} 处")
    set_src(nb["cells"][idx], src.replace(old, new))
    report.append(f"- [{label}] cell #{idx}：{n} 处替换 ✅")


def find_cell(pred, label):
    for i, c in enumerate(nb["cells"]):
        if c["cell_type"] == "code" and pred(cell_src(c)):
            return i
    raise SystemExit(f"❌ 找不到单元格：{label}")


# ---------------------------------------------------------------- C2: keys
i = find_cell(lambda s: "META_DICT = {" in s, "META_DICT 定义")
src = cell_src(nb["cells"][i])
start = src.index("META_DICT = {")
depth = 0
end = None
for j in range(start + len("META_DICT = "), len(src)):
    if src[j] == "{":
        depth += 1
    elif src[j] == "}":
        depth -= 1
        if depth == 0:
            end = j + 1
            break
if end is None:
    raise SystemExit("❌ 无法定位 META_DICT 字面量的结束位置")
insert = ('\n\n# --- C2 修正：字典键空白归一化 -------------------------------------\n'
          '# 原始数据里存在 \'Dystopian \' / \'Parody \' 这类带尾随空格的标签；\n'
          '# 对字典键与查询键同时 strip() 才能正确归并（实测影响 -0.010 个维度）。\n'
          'META_DICT = {str(k).strip(): v for k, v in META_DICT.items()}\n')
set_src(nb["cells"][i], src[:end] + insert + src[end:])
report.append(f"- [C2] cell #{i}：在 META_DICT 字面量之后插入键归一化 ✅")

i = find_cell(lambda s: "def _parse_tags_dict" in s, "_parse_tags_dict")
replace_in_cell(
    i,
    "    if isinstance(x, dict):\n        return x\n",
    "    if isinstance(x, dict):\n"
    "        return {str(k).strip(): v for k, v in x.items()}   # C2: 键空白归一化\n",
    label="C2 / _parse_tags_dict(dict 分支)")
replace_in_cell(
    i,
    "            return v if isinstance(v, dict) else {}\n",
    "            return ({str(k).strip(): v for k, v in v.items()}\n"
    "                    if isinstance(v, dict) else {})            # C2: 键空白归一化\n",
    label="C2 / _parse_tags_dict(str 分支)")

# ------------------------------------------- C5: non-binding 0.3 annotation
i = find_cell(lambda s: "Clean_Priority_Tags" in s and "priority_threshold" not in s,
              "Step 1 priority 过滤")
replace_in_cell(
    i,
    'data["Clean_Priority_Tags"] = data["tags"].apply(lambda x: parse_tags_counts_with_priority(x, 0.3))\n',
    'data["Clean_Priority_Tags"] = data["tags"].apply(lambda x: parse_tags_counts_with_priority(x, 0.3))\n'
    '# [实] 该过滤实测删除 0 行：每款游戏票数最高的标签 priority 恒为 1.0 >= 0.3。\n'
    '#      详见 06_tools/threshold_03_report.md（样本框逐级核对）。\n',
    label="C5 / 0.3 过滤非约束性注释")

# ------------------------------------------------------------- C1: HC3 fits
HC3_TARGETS = [
    ("final_model = sm.OLS(Y, X_main).fit()",
     'final_model = sm.OLS(Y, X_main).fit(cov_type="HC3")   # C1: 论文全程使用 HC3',
     "C1 / 主模型"),
    ("m0 = sm.OLS(Y, X0).fit()",
     'm0 = sm.OLS(Y, X0).fit(cov_type="HC3")   # C1',
     "C1 / 稳健 1"),
    ("m_age = sm.OLS(Y, X_age).fit()",
     'm_age = sm.OLS(Y, X_age).fit(cov_type="HC3")   # C1',
     "C1 / 稳健 2"),
    ("m_inter = sm.OLS(Y, X_inter).fit()",
     'm_inter = sm.OLS(Y, X_inter).fit(cov_type="HC3")   # C1',
     "C1 / 稳健 3"),
]
for old, new, label in HC3_TARGETS:
    i = find_cell(lambda s, o=old: o in s, label)
    replace_in_cell(i, old, new, label=label)

# ------------------------------------------------- C3: robustness-4 rewrite
i = find_cell(lambda s: "Tag-Priority 阈值序列" in s and "for t in" in s, "稳健 4")
NEW_R4 = '''print("\\n" + "=" * 60)
print("稳健4 | Tag-Priority 阈值序列 (固定样本, 只变索引定义)")
print("=" * 60)

def to_metatags(tag_list):
    """Map raw tags through the Meta-Tag dictionary, dropping IGNORE."""
    out = set()
    for tag in tag_list:
        key = str(tag).strip()
        mapped = META_DICT.get(key, key)
        if mapped != 'IGNORE':
            out.add(mapped)
    return list(out)

# --- C3 修正 -------------------------------------------------------------
# 原先该单元让样本随阈值 t 一起缩小（N 由 17,639 递减到 17,488）。实测（
# 06_tools/threshold_03_report.md）表明：priority >= t 的标签列表在全部七档
# 都是空的 0 行 —— 票数最高的标签 priority 恒为 1.0，阈值从不删行。N 的下降
# 全部来自 'IGNORE' 归并（阈值越高，幸存标签越少，越容易被 IGNORE 清空）。
# 因此那样会把「索引定义变化」与「样本构成变化」两个效应混在一起。
# 修正：样本固定为主模型回归样本 reg_data，每一档只重新定义杂交度。
# ------------------------------------------------------------------------
print(f"{'t':>6} {'N':>7} {'IndexMean':>10} {'H=0':>5} "
      f"{'beta1':>9} {'t':>7} {'beta2':>9} {'t':>7} {'Peak':>7} {'R2':>8}")
for t in [None, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45]:
    if t is None:
        data['_Cpt'] = data['tags'].apply(lambda x: list(_parse_tags_dict(x).keys()))
    else:
        data['_Cpt'] = data['tags'].apply(lambda x: parse_tags_counts_with_priority(x, t))
    data['_Mt'] = data['_Cpt'].apply(to_metatags)
    hm = data['_Mt'].apply(len).mean()

    sub = reg_data.copy()
    sub['Hc_t'] = data.loc[sub.index, '_Mt'].apply(len) - hm
    sub['Hc_t2'] = sub['Hc_t'] ** 2
    X = sm.add_constant(sub[['Hc_t', 'Hc_t2', 'price']].join(year_dum))
    m = sm.OLS(sub['Log_Reviews'], X).fit(cov_type="HC3")   # C1
    pk = hm + (-m.params['Hc_t'] / (2 * m.params['Hc_t2']))
    tag = ' none' if t is None else f"{t:.2f}"
    print(f"{tag:>6} {int(m.nobs):>7} {hm:>10.4f} {int((data['_Mt'].apply(len) == 0).sum()):>5} "
          f"{m.params['Hc_t']:>+9.4f} {m.tvalues['Hc_t']:>+7.2f} "
          f"{m.params['Hc_t2']:>+9.4f} {m.tvalues['Hc_t2']:>+7.2f} {pk:>7.2f} {m.rsquared:>8.4f}")
'''
set_src(nb["cells"][i], NEW_R4)
report.append(f"- [C3] cell #{i}：稳健 4 重写为「固定样本 + HC3」✅")

# ------------------------------------------------------- C4: persist results
PERSIST = '''# ============================================================
# C4 修正：结果落盘（原先全部回归结果只 print 到控制台，无法被引用/复核）
# ============================================================
from pathlib import Path as _Path

_RES_DIR = _Path("02_pipeline/results")
_RES_DIR.mkdir(parents=True, exist_ok=True)


def _row(name, mdl, b1, b2, pk):
    return {
        "table": name, "N": int(mdl.nobs), "R2": mdl.rsquared, "adj_R2": mdl.rsquared_adj,
        "beta1_Hc": b1, "se_HC3_Hc": mdl.bse["Hybrid_Centered"],
        "t_HC3_Hc": mdl.tvalues["Hybrid_Centered"],
        "beta2_Hc2": b2, "se_HC3_Hc2": mdl.bse["Hybrid_Centered_Squared"],
        "t_HC3_Hc2": mdl.tvalues["Hybrid_Centered_Squared"],
        "beta3_price": mdl.params["price"], "se_HC3_price": mdl.bse["price"],
        "t_HC3_price": mdl.tvalues["price"], "peak": pk,
    }


pd.DataFrame([
    _row("Table 5 主模型 (年份FE)", final_model, lin, quad, peak),
    _row("Table 6 稳健1 无时间控制", m0, lin0, quad0, peak0),
    _row("Table 7 稳健2 按天年龄控制", m_age, linA, quadA, peakA),
    _row("Table 8 稳健3 价格调制", m_inter, linI, quadI, peakI),
]).to_csv(_RES_DIR / "regression_summary.csv", index=False, encoding="utf-8-sig")

# 描述统计（论文 Table 1 / Table 4 的替代来源）
_idx = data["Hybridization_Index"]
pd.DataFrame([{
    "sample": "analysis (17,686)", "N": len(_idx), "mean": _idx.mean(),
    "median": _idx.median(), "sd": _idx.std(ddof=1), "min": _idx.min(), "max": _idx.max(),
}]).to_csv(_RES_DIR / "table1_index_descriptives.csv", index=False, encoding="utf-8-sig")

# 发行年份分布（论文 §4.1 的替代来源）
_vc = data["Release_Year"].value_counts().sort_index()
pd.DataFrame({
    "year": _vc.index.astype(int), "N": _vc.values,
    "share_pct": (100 * _vc.values / len(data)).round(2),
}).to_csv(_RES_DIR / "year_distribution.csv", index=False, encoding="utf-8-sig")

print(f"[written] {_RES_DIR / 'regression_summary.csv'}")
print(f"[written] {_RES_DIR / 'table1_index_descriptives.csv'}")
print(f"[written] {_RES_DIR / 'year_distribution.csv'}")
'''
new_cell = {
    "cell_type": "code",
    "execution_count": None,
    "id": "c4persist",
    "metadata": {},
    "outputs": [],
    "source": PERSIST.splitlines(keepends=True),
}
nb["cells"].append(new_cell)
report.append(f"- [C4] 追加结果落盘单元（cell #{len(nb['cells'])-1}）✅")

# ------------------------------------------------------------------- write
if CHECK_ONLY:
    print("\n".join(report))
    print("\n--check：未写入")
    raise SystemExit(0)

backup = NB.with_suffix(".ipynb.bak-" + datetime.now().strftime("%Y%m%d%H%M%S"))
shutil.copy2(NB, backup)
NB.write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding="utf-8")

# verify it still parses and that the round trip is stable
json.loads(NB.read_text(encoding="utf-8"))
print("\n".join(report))
print()
print(f"[backup]  {backup.name}")
print(f"[written] {NB.name}")
