# -*- coding: utf-8 -*-
"""
Follow-up quantification of the META_DICT coverage problem and a
dictionary-only hybridisation index re-estimation.

Run:  python 06_tools/verify_coverage.py
Out:  06_tools/coverage_report.md
"""
# -*- coding: utf-8 -*-
# --- workspace-root anchor (added during reorganisation) -------------------
from pathlib import Path as _Path
import os as _os
_ROOT = _Path(__file__).resolve().parent
while not (_ROOT / "01_data").exists() and _ROOT.parent != _ROOT:
    _ROOT = _ROOT.parent
_os.chdir(_ROOT)
# --------------------------------------------------------------------------
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent / "coverage_report.md"

DICT_VALUES = {
    'RPG', 'Shooter', 'Simulation', 'Roguelike', 'Strategy', 'Fighting/Brawler', 'Platformer',
    'Sports/Racing', 'Puzzle/Board', 'Adventure/Narrative', 'Core System', 'Sci-Fi/Cyberpunk',
    'Fantasy/Magic', 'Historical', 'Military/Combat', 'Other Themes', 'Story-Driven',
    'Mood (Positive)', 'Mood (Dark)', 'Perspective', 'Art Style', 'Action', 'Casual', 'Party',
    'Adult', 'Arcade/Top-Down Shooter',
}

lines = []
def p(*a):
    s = " ".join(str(x) for x in a)
    lines.append(s)
    print(s)

def _fmt(v, ff):
    if isinstance(v, str):
        return v
    if isinstance(v, (int, np.integer)):
        return f"{int(v):,}"
    if isinstance(v, (float, np.floating)):
        if float(v).is_integer() and abs(v) < 1e15:
            return f"{int(v):,}"
        return ff.format(float(v))
    return str(v)

def table(df, ff="{:.4f}"):
    df = df.reset_index() if (df.index.name or not isinstance(df.index, pd.RangeIndex)) else df
    cols = [str(c) for c in df.columns]
    p("| " + " | ".join(cols) + " |")
    p("|" + "|".join(["---"] * len(cols)) + "|")
    for rec in df.itertuples(index=False):
        p("| " + " | ".join(_fmt(v, ff) for v in rec) + " |")

def ols(y, X, names):
    X = np.asarray(X, float); y = np.asarray(y, float).reshape(-1, 1)
    n, k = X.shape
    XtX_inv = np.linalg.pinv(X.T @ X)
    beta = (XtX_inv @ (X.T @ y)).ravel()
    resid = (y - (X @ beta).reshape(-1, 1))
    ssr = float((resid ** 2).sum()); sst = float(((y - y.mean()) ** 2).sum())
    r2 = 1 - ssr / sst
    sigma2 = ssr / (n - k)
    se_c = np.sqrt(np.diag(sigma2 * XtX_inv))
    e = resid.ravel()
    meat = (X * (e ** 2)[:, None]).T @ X
    se_h = np.sqrt(np.diag((n / (n - k)) * (XtX_inv @ meat @ XtX_inv)))
    dw = float((np.diff(e) ** 2).sum() / (e ** 2).sum())
    return dict(beta=beta, se_h=se_h, t=beta / se_h, r2=r2, n=n, dw=dw)

df = pd.read_csv(ROOT / "01_data/processed/games_clustered_meta_export.csv")
meta = df.Meta_Tags.fillna("").apply(lambda s: [t.strip() for t in str(s).split(";") if t.strip()])

# --- per-game composition -------------------------------------------------
n_total, n_dict = [], []
for lst in meta:
    n_total.append(len(lst))
    n_dict.append(sum(1 for t in lst if t in DICT_VALUES))
df["H_total"] = n_total
df["H_dict"] = n_dict
df["H_fall"] = df.H_total - df.H_dict

p("# META_DICT 覆盖度量化报告")
p("")
p("对每个游戏的 `Meta_Tags` 逐项判定：是否属于 META_DICT 的类别值（26 个）还是原标签兜底（fall-through）。")
p("")
p("## 1. 覆盖度总览")
p("")
tot = int(df.H_total.sum()); dic = int(df.H_dict.sum()); fal = int(df.H_fall.sum())
p(f"- 全部「元标签计数」总数 = **{tot:,}**")
p(f"- 其中属于 META_DICT 类别 = **{dic:,}**（{100*dic/tot:.2f}%）")
p(f"- 其中为兜底原标签 = **{fal:,}**（{100*fal/tot:.2f}%）")
p(f"- 不同兜底标签种类 = **{len(set(t for l in meta for t in l if t not in DICT_VALUES))}**")
p("")
p("## 2. 每款游戏的杂交度：总口径 vs 仅字典口径")
p("")
d = df[["H_total", "H_dict", "H_fall"]].describe().T
d["median"] = df[["H_total", "H_dict", "H_fall"]].median()
table(d.round(3), "{:.3f}")
p("")
p(f"- 相关性 corr(H_total, H_dict) = **{df.H_total.corr(df.H_dict):.4f}**")
p(f"- 完全由兜底标签构成的游戏（H_dict = 0）：**{int((df.H_dict == 0).sum())}** 款")
p("")
p("### 2.1 兜底占比分布")
q = df.H_fall.div(df.H_total.where(df.H_total > 0)).dropna()
table(pd.DataFrame({"兜底占比分位": ["min", "p25", "median", "p75", "p90", "max"],
                    "值": [q.min(), q.quantile(.25), q.median(), q.quantile(.75),
                           q.quantile(.90), q.max()]}).round(3).set_index("兜底占比分位").T, "{:.3f}")

# --- top fall-through tags ------------------------------------------------
from collections import Counter
c = Counter(t for l in meta for t in l if t not in DICT_VALUES)
top = pd.DataFrame(sorted(c.items(), key=lambda kv: -kv[1])[:30], columns=["fall_through_tag", "n_games"])
top["share_pct"] = (100 * top.n_games / len(df)).round(2)
p("")
p("## 3. 兜底标签 Top 30（按出现游戏数）")
p("")
table(top, "{:.2f}")

# --- cluster composition --------------------------------------------------
p("")
p("## 4. 分簇的字典纯度")
p("")
g = df.groupby("Game_Cluster").agg(N=("appid", "size"),
                                   H_total_mean=("H_total", "mean"),
                                   H_dict_mean=("H_dict", "mean"),
                                   H_fall_mean=("H_fall", "mean"))
g["dict_share_pct"] = (100 * g.H_dict_mean / g.H_total_mean).round(2)
table(g.round(3).reset_index(), "{:.3f}")

# --- re-estimation with dictionary-only index -----------------------------
p("")
p("## 5. 用「仅字典口径」的杂交度重估倒 U 模型")
p("")
p("H_dict = 仅计入 META_DICT 类别的数量（0–13 左右）。其余设定与主模型一致：Log_Reviews、price、年份 FE。")
p("")

reg = df.dropna(subset=["Log_Reviews", "price", "Release_Year"]).copy()
for label, col in [("总口径 H_total（= 现状）", "H_total"), ("仅字典口径 H_dict", "H_dict")]:
    sub = reg[reg[col] > 0].copy()
    m = sub[col].mean()
    sub["Hc"] = sub[col] - m
    sub["Hc2"] = sub.Hc ** 2
    yd = pd.get_dummies(sub.Release_Year, prefix="Y", drop_first=True).astype(float)
    X = np.column_stack([np.ones(len(sub)), sub.Hc.values, sub.Hc2.values, sub.price.values, yd.values])
    r = ols(sub.Log_Reviews.values, X, None)
    b1, b2 = r["beta"][1], r["beta"][2]
    peak = m + (-b1 / (2 * b2))
    p(f"**{label}**")
    p("")
    p(f"- N = {r['n']:,}，均值 = {m:.3f}，R² = {r['r2']:.4f}，DW = {r['dw']:.3f}")
    p(f"- β1 = {b1:+.5f} (t_HC1 = {r['t'][1]:+.2f})，β2 = {b2:+.5f} (t_HC1 = {r['t'][2]:+.2f})")
    p(f"- 拐点 = **{peak:.2f}**")
    p("")

# --- how many games change cluster/quantile ------------------------------
p("## 6. 结论稳健性的直接检验：字典纯度是否驱动倒 U")
p("")
corr = df[["H_dict", "H_fall", "Log_Reviews", "price"]].corr().round(4)
table(corr, "{:.4f}")
p("")
p("把 `H_fall`（兜底标签个数）作为额外控制变量加入主模型，看二次项是否幸存：")
p("")
sub = df[df.H_total > 0].copy()
m = sub.H_total.mean()
sub["Hc"] = sub.H_total - m
sub["Hc2"] = sub.Hc ** 2
yd = pd.get_dummies(sub.Release_Year, prefix="Y", drop_first=True).astype(float)
X = np.column_stack([np.ones(len(sub)), sub.Hc.values, sub.Hc2.values, sub.price.values,
                     sub.H_fall.values, yd.values])
r = ols(sub.Log_Reviews.values, X, None)
p(f"- N = {r['n']:,}，R² = {r['r2']:.4f}")
p(f"- β1(Hc) = {r['beta'][1]:+.5f} (t={r['t'][1]:+.2f})")
p(f"- β2(Hc²) = {r['beta'][2]:+.5f} (t={r['t'][2]:+.2f})")
p(f"- β(H_fall) = {r['beta'][4]:+.5f} (t={r['t'][4]:+.2f})")
p(f"- 拐点 = **{m + (-r['beta'][1]/(2*r['beta'][2])):.2f}**")

OUT.write_text("\n".join(lines), encoding="utf-8")
print(f"\n[written] {OUT}")
