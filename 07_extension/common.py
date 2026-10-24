# -*- coding: utf-8 -*-
"""
Shared infrastructure for the hybridization-extension study (07_extension/).

Provides
  ROOT            workspace root (anchored by walking up to the folder with 01_data)
  PATHS           input / output paths
  SAMPLE          pipeline constants, kept identical to the main notebook
  parse_meta_dict()   read META_DICT out of the main notebook
  load_sample()       rebuild the 17,686-game analysis frame (+ disk cache)
  tag_dicts()         parse the raw `tags` column once
  ols()               numpy OLS with classical / HC1 / HC3 / cluster SEs
  vif()               variance inflation factors
  markdown_table()    tiny formatter (tabulate is not installed)

IMPORTANT: load_sample() must reproduce the main pipeline's frame exactly
(17,686 games; 17,670 in the regression sample). It asserts this and fails loudly.
"""
from __future__ import annotations

import ast
import json
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# --------------------------------------------------------------------- paths
_here = Path(__file__).resolve()
ROOT = _here.parent
while not (ROOT / "01_data").exists() and ROOT.parent != ROOT:
    ROOT = ROOT.parent

PATHS = {
    "raw": ROOT / "01_data/raw/steam_games_march2025_updated.csv",
    "export": ROOT / "01_data/processed/games_clustered_meta_export.csv",
    "tag_nodes": ROOT / "01_data/processed/tag_space_nodes.csv",
    "tag_summary": ROOT / "01_data/processed/tag_space_summary.json",
    "measures": ROOT / "01_data/processed/game_measures_extension.csv",
    "cache": ROOT / "01_data/processed/extension_sample.pkl",
    "results": ROOT / "07_extension/results",
    "notebook": None,  # filled lazily
}

# ------------------------------------------------------------------ constants
SAMPLE = dict(
    year_min=2015,
    year_max=2025,
    min_reviews=100,
    owners_exclude=[
        "5000000-10000000", "10000000-20000000", "20000000-50000000",
        "50000000-100000000", "100000000-200000000", "200000000-500000000",
    ],
    expected_n=17686,
    expected_reg_n=17670,
    expected_mean_meta_h=9.3145,   # after the C2 strip() correction
)

RAW_USECOLS = [
    "appid", "name", "release_date", "price", "positive", "negative",
    "estimated_owners", "genres", "categories", "tags", "tags_counts",
    "pct_pos_total", "pct_pos_recent", "num_reviews_total", "num_reviews_recent",
    "peak_ccu", "achievements", "dlc_count", "recommendations", "discount",
    "metacritic_score", "required_age", "average_playtime_forever",
    "median_playtime_forever", "average_playtime_2weeks", "median_playtime_2weeks",
    "screenshots", "movies", "supported_languages", "developers", "publishers",
    "windows", "mac", "linux", "user_score",
]


# ------------------------------------------------------------------- notebook
def find_notebook() -> Path:
    if PATHS["notebook"] is None:
        nb = next(iter(ROOT.glob("**/4dissertation_gamespace_clustering_new.ipynb")), None)
        if nb is None:
            raise FileNotFoundError("main pipeline notebook not found")
        PATHS["notebook"] = nb
    return PATHS["notebook"]


def parse_meta_dict(strip=True) -> dict:
    """Read the META_DICT literal out of the main notebook.

    strip=True mirrors the C2 correction applied to the notebook itself.
    """
    nb = json.loads(find_notebook().read_text(encoding="utf-8"))
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
                        md = eval(src[start + len("META_DICT = "):i + 1])
                        return ({str(k).strip(): v for k, v in md.items()}
                                if strip else md)
    raise ValueError("META_DICT not found in notebook")


# -------------------------------------------------------------------- parsing
def parse_list_field(x) -> list:
    """Verbatim behaviour of the notebook's parse_list_field()."""
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


def parse_box(x) -> dict:
    """Steam 'tags' column -> {tag: votes}; keys stripped (C2)."""
    if isinstance(x, dict):
        return {str(k).strip(): v for k, v in x.items()}
    if isinstance(x, str):
        try:
            v = ast.literal_eval(x)
            return {str(k).strip(): val for k, val in v.items()} if isinstance(v, dict) else {}
        except Exception:
            return {}
    return {}


def _count_list(x) -> int:
    """Count entries of a serialised list field ('screenshots', 'movies', ...)."""
    if not isinstance(x, str) or not x.strip().startswith("["):
        return 0
    try:
        v = ast.literal_eval(x)
        return len(v) if isinstance(v, (list, tuple, set)) else 0
    except Exception:
        return 0


# --------------------------------------------------------------- sample frame
def _build_sample() -> pd.DataFrame:
    raw = pd.read_csv(PATHS["raw"], usecols=RAW_USECOLS)

    d = raw.copy()
    d = d.dropna(subset=["genres", "categories", "tags_counts"])

    d["release_date"] = pd.to_datetime(d["release_date"], errors="coerce")
    d["Release_Year"] = d["release_date"].dt.year
    d["Total_Reviews"] = d["positive"] + d["negative"]

    d = d[(d["Release_Year"] >= SAMPLE["year_min"]) & (d["Release_Year"] <= SAMPLE["year_max"])]
    d = d[d["Total_Reviews"] >= SAMPLE["min_reviews"]]

    genres_list = d["genres"].apply(parse_list_field)
    owners_norm = d["estimated_owners"].astype(str).str.replace(r"\s+", "", regex=True)
    non_indie_large = (~genres_list.apply(lambda g: "Indie" in g)) & owners_norm.isin(SAMPLE["owners_exclude"])
    d = d[~non_indie_large].reset_index(drop=True)

    # --- derived columns used downstream ------------------------------------
    d["Log_Reviews"] = np.log1p(d["Total_Reviews"])
    d["age_days"] = (pd.Timestamp("2025-03-10") - d["release_date"]).dt.days
    d["n_screenshots"] = d["screenshots"].apply(_count_list)
    d["n_movies"] = d["movies"].apply(_count_list)
    d["n_languages"] = d["supported_languages"].apply(
        lambda s: len(parse_list_field(s)) if isinstance(s, str) else 0)

    # --- missing-value rules (see plan section 4) ---------------------------
    # Steam writes -1 as a "not available" sentinel in these columns.
    for c in ["pct_pos_total", "pct_pos_recent", "num_reviews_total", "num_reviews_recent"]:
        d[c] = pd.to_numeric(d[c], errors="coerce").where(lambda s: s > 0)
    # A zero Metacritic / user score means "no score", not "score of zero".
    for c in ["metacritic_score", "user_score"]:
        d[c] = pd.to_numeric(d[c], errors="coerce").where(lambda s: s > 0)
    # peak_ccu and discount legitimately take the value 0.
    d["has_recent_reviews"] = (pd.to_numeric(d["num_reviews_recent"], errors="coerce") > 0).astype(int)
    d["has_metacritic"] = d["metacritic_score"].notna().astype(int)
    d["has_discount"] = (pd.to_numeric(d["discount"], errors="coerce") > 0).astype(int)

    return d


def load_sample(force: bool = False, verbose: bool = True) -> pd.DataFrame:
    """Analysis frame, cached to disk. Asserts the pipeline's frame size."""
    if PATHS["cache"].exists() and not force:
        d = pd.read_pickle(PATHS["cache"])
    else:
        d = _build_sample()
        d.to_pickle(PATHS["cache"])

    n = len(d)
    if n != SAMPLE["expected_n"]:
        raise AssertionError(
            f"sample frame mismatch: got {n}, expected {SAMPLE['expected_n']}. "
            "The extension must reuse the main pipeline's frame exactly.")

    if verbose:
        print(f"[sample] N = {n:,}  (regression subset = {int((d['Total_Reviews'] > 0).sum()):,})")
    return d


def tag_dicts(d: pd.DataFrame) -> list:
    return [parse_box(s) for s in d["tags"].values]


# ----------------------------------------------------------------------- OLS
def ols(y, X, kind: str = "HC3", groups=None):
    """OLS with classical / HC1 / HC3 / cluster-robust standard errors."""
    y = np.asarray(y, dtype=float)
    X = np.asarray(X, dtype=float)
    XtXi = np.linalg.pinv(X.T @ X)
    b = XtXi @ (X.T @ y)
    e = y - X @ b
    n, k = X.shape

    if kind == "classical":
        cov = (float(e @ e) / (n - k)) * XtXi
    elif kind == "HC1":
        Xw = X * e[:, None]
        cov = (XtXi @ (Xw.T @ Xw) @ XtXi) * (n / (n - k))
    elif kind == "HC3":
        h = np.einsum("ij,jk,ik->i", X, XtXi, X)
        w = e / np.clip(1.0 - h, 1e-12, None)
        Xw = X * w[:, None]
        cov = XtXi @ (Xw.T @ Xw) @ XtXi
    elif kind == "cluster":
        if groups is None:
            raise ValueError("cluster SEs need `groups`")
        g = pd.factorize(np.asarray(groups))[0]
        meat = np.zeros((k, k))
        for gg in np.unique(g):
            m = g == gg
            Xg = X[m]
            eg = e[m]
            s = Xg.T @ eg
            meat += np.outer(s, s)
        G = len(np.unique(g))
        cov = XtXi @ meat @ XtXi * (G / (G - 1)) * ((n - 1) / (n - k))
    else:
        raise ValueError(kind)

    se = np.sqrt(np.diag(cov))
    ss = float(((y - y.mean()) ** 2).sum())
    r2 = 1 - float(e @ e) / ss
    return dict(b=b, se=se, t=b / se, n=n, k=k, r2=r2,
                r2_adj=1 - (1 - r2) * (n - 1) / (n - k), resid=e, cov=cov)


def vif(X) -> np.ndarray:
    """VIF per column of X, including an intercept in each auxiliary regression.

    Constant columns (e.g. an intercept passed in by mistake) return NaN rather
    than dividing by zero.
    """
    X = np.asarray(X, dtype=float)
    k = X.shape[1]
    out = np.empty(k)
    for j in range(k):
        xj = X[:, j]
        ss = float(((xj - xj.mean()) ** 2).sum())
        if ss <= 1e-12:
            out[j] = np.nan
            continue
        others = np.delete(X, j, axis=1)
        A = np.column_stack([np.ones(len(others)), others])
        b = np.linalg.pinv(A.T @ A) @ (A.T @ xj)
        e = xj - A @ b
        r2 = 1 - float(e @ e) / ss
        out[j] = np.inf if r2 >= 1 else 1.0 / (1.0 - r2)
    return out


# ----------------------------------------------------------------- formatting
def markdown_table(rows, headers=None, floatfmt="{:+.4f}") -> str:
    if not rows:
        return "_(empty)_"
    if headers is None:
        headers = list(rows[0].keys()) if isinstance(rows[0], dict) else None
    if isinstance(rows[0], dict):
        body = [[r.get(h, "") for h in headers] for r in rows]
    else:
        body = [list(r) for r in rows]
    out = ["| " + " | ".join(str(h) for h in headers) + " |",
           "|" + "|".join(["---"] * len(headers)) + "|"]
    for b in body:
        cells = []
        for v in b:
            if isinstance(v, float):
                cells.append("—" if not np.isfinite(v) else floatfmt.format(v))
            else:
                cells.append(str(v))
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out)


def write_report(name: str, lines) -> Path:
    """Write a results markdown file under 07_extension/results/."""
    PATHS["results"].mkdir(parents=True, exist_ok=True)
    p = PATHS["results"] / name
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("[written]", p)
    return p


def load_tag_space():
    """Reconstruct a lightweight tag space from the artifacts written by build_tag_space.py.

    Returns an object exposing the attributes `measures.py` needs:
    vocab, keep, labels, K, emb, D, tag_to_domain.
    """
    from types import SimpleNamespace

    nodes = pd.read_csv(PATHS["tag_nodes"], encoding="utf-8-sig")
    emb_cols = [c for c in nodes.columns if c.startswith("emb")]
    dist_path = PATHS["tag_nodes"].parent / "tag_domain_distances.csv"
    D = pd.read_csv(dist_path, index_col=0, encoding="utf-8-sig").values.astype(float)

    ts = SimpleNamespace(
        vocab=nodes["tag"].tolist(),
        keep=np.arange(len(nodes)),
        labels=nodes["domain"].values.astype(int),
        K=int(nodes["domain"].max()) + 1,
        emb=nodes[emb_cols].values.astype(float),
        D=D,
        dfreq=nodes["dfreq"].values.astype(float),
    )
    ts.tag_to_domain = {t: int(d) for t, d in zip(nodes["tag"], nodes["domain"])}
    return ts
