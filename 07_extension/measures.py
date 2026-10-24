# -*- coding: utf-8 -*-
"""
Per-game hybridization measures derived from the tag space.

Three families are produced so that the count-based index and the
dispersion-based indices can be compared head to head:

  count          n_domains            number of distinct tag domains spanned
  coherence      Herfindahl over domain weight shares          in (0, 1]
                 entropy_coherence = 1 - H/ln K                in [0, 1]
  spanning       expected pairwise distance between the domains spanned,
                 under the priority weights                    in [0, max D]
                 tag_spanning = same idea but between individual tags in the
                 embedding, bypassing the community partition (breaks the
                 mechanical link with coherence)

Weights follow the pipeline's priority convention: w = votes / max(votes) for
the game, so the most-voted tag has weight 1 and marginal tags approach 0.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def _weights(game_tags, tag_to_domain, use_priority=True):
    """Restrict to tags present in the tag space; return (domains, weights, used_ids)."""
    if not game_tags:
        return np.array([], dtype=int), np.array([], dtype=float), []
    mx = max(game_tags.values()) if use_priority else 1.0
    if mx <= 0:
        return np.array([], dtype=int), np.array([], dtype=float), []
    dom, w, used = [], [], []
    for k, v in game_tags.items():
        d = tag_to_domain.get(k)
        if d is None:
            continue
        dom.append(int(d))
        w.append(float(v) / mx if use_priority else 1.0)
        used.append(k)
    return np.asarray(dom, dtype=int), np.asarray(w, dtype=float), used


def coherence(game_tags, tag_to_domain, K: int) -> float:
    """Herfindahl concentration of priority weight over tag domains."""
    dom, w, _ = _weights(game_tags, tag_to_domain)
    if len(dom) == 0 or w.sum() <= 0:
        return np.nan
    p = np.bincount(dom, weights=w, minlength=K)
    p = p / p.sum()
    return float((p ** 2).sum())


def entropy_coherence(game_tags, tag_to_domain, K: int) -> float:
    """1 - H/ln K, a concentration measure less dominated by the largest share."""
    dom, w, _ = _weights(game_tags, tag_to_domain)
    if len(dom) == 0 or w.sum() <= 0 or K < 2:
        return np.nan
    p = np.bincount(dom, weights=w, minlength=K)
    p = p / p.sum()
    nz = p[p > 0]
    H = -float((nz * np.log(nz)).sum())
    return float(1.0 - H / np.log(K))


def domain_shares(game_tags, tag_to_domain, K: int) -> np.ndarray:
    dom, w, _ = _weights(game_tags, tag_to_domain)
    if len(dom) == 0 or w.sum() <= 0:
        return np.full(K, np.nan)
    p = np.bincount(dom, weights=w, minlength=K).astype(float)
    return p / p.sum()


def spanning(game_tags, tag_to_domain, D: np.ndarray) -> float:
    """Expected cosine distance between two **distinct** domains the game spans.

    This is the priority-weighted mean of D over ordered distinct domain pairs::

        sum_{a != b} p_a p_b D_ab / sum_{a != b} p_a p_b
            = (p' D p) / (1 - sum_a p_a^2)

    Dividing by (1 - Herfindahl) is what makes this a pure *dispersion* measure:
    a game concentrated in one domain is not penalised twice, and the quantity no
    longer moves mechanically with `coherence`. The undivided quadratic form is
    kept separately as `spanning_diluted` for comparison.

    Single-domain games span nothing, so the value is defined as 0.0.
    """
    dom, w, _ = _weights(game_tags, tag_to_domain)
    if len(dom) == 0 or w.sum() <= 0:
        return np.nan
    K = D.shape[0]
    p = np.bincount(dom, weights=w, minlength=K).astype(float)
    p = p / p.sum()
    hhi = float((p ** 2).sum())
    if hhi >= 1.0 - 1e-12:          # only one domain present
        return 0.0
    return float((p @ D @ p) / (1.0 - hhi))


def spanning_diluted(game_tags, tag_to_domain, D: np.ndarray) -> float:
    """With-replacement version p' D p. Kept only for comparison: it is strongly
    (mechanically) negatively correlated with `coherence`."""
    dom, w, _ = _weights(game_tags, tag_to_domain)
    if len(dom) == 0 or w.sum() <= 0:
        return np.nan
    K = D.shape[0]
    p = np.bincount(dom, weights=w, minlength=K).astype(float)
    p = p / p.sum()
    return float(p @ D @ p)


def tag_spanning(game_tags, tag_index, emb: np.ndarray):
    """Priority-weighted mean pairwise cosine distance between the game's tags.

    Uses the same distinct-pair normalisation as `spanning`, but operates on
    individual tags rather than domains, so it varies *within* a fixed domain
    count and is not mechanically tied to the domain partition.

    Returns (value, n_tags_used).
    """
    if not game_tags:
        return np.nan, 0
    mx = max(game_tags.values())
    if mx <= 0:
        return np.nan, 0
    idx, w = [], []
    for k, v in game_tags.items():
        i = tag_index.get(k)
        if i is None:
            continue
        idx.append(i)
        w.append(float(v) / mx)
    if len(idx) == 0:
        return np.nan, 0
    if len(idx) == 1:
        return 0.0, 1
    E = emb[np.asarray(idx, dtype=int)]
    p = np.asarray(w, dtype=float)
    p = p / p.sum()
    S = E @ E.T
    Dm = np.clip(1.0 - S, 0.0, None)
    np.fill_diagonal(Dm, 0.0)
    hhi = float((p ** 2).sum())
    if hhi >= 1.0 - 1e-12:
        return 0.0, len(idx)
    return float((p @ Dm @ p) / (1.0 - hhi)), len(idx)


def n_domains_spanned(game_tags, tag_to_domain) -> int:
    dom, _, _ = _weights(game_tags, tag_to_domain)
    return int(len(np.unique(dom))) if len(dom) else 0


def score_games(tag_dicts, ts, appids=None, verbose=True) -> pd.DataFrame:
    """Score every game. Games with no scorable tag get NaN and are counted."""
    tag_index = {ts.vocab[int(g)]: i for i, g in enumerate(ts.keep)}
    rows = []
    for i, g in enumerate(tag_dicts):
        dom, w, used = _weights(g, ts.tag_to_domain)
        n_total = len(g)
        rec = {
            "row": i,
            "n_tags_total": n_total,
            "n_tags_used": len(used),
            "used_weight_share": float(w.sum() / n_total) if n_total else np.nan,
            "coherence": coherence(g, ts.tag_to_domain, ts.K),
            "entropy_coherence": entropy_coherence(g, ts.tag_to_domain, ts.K),
            "spanning": spanning(g, ts.tag_to_domain, ts.D),
            "spanning_diluted": spanning_diluted(g, ts.tag_to_domain, ts.D),
            "n_domains": n_domains_spanned(g, ts.tag_to_domain),
        }
        tsv, n_used = tag_spanning(g, tag_index, ts.emb)
        rec["tag_spanning"] = tsv
        rec["tag_spanning_n"] = n_used
        sh = domain_shares(g, ts.tag_to_domain, ts.K)
        for c in range(ts.K):
            rec[f"dom{c}"] = sh[c]
        rows.append(rec)

    out = pd.DataFrame(rows)
    if appids is not None:
        out.insert(0, "appid", np.asarray(appids))
    if verbose:
        bad = int(out["coherence"].isna().sum())
        print(f"[measures] scored {len(out):,} games; unscorable (no tag in space) = {bad:,} "
              f"({100*bad/len(out):.2f}%)")
    return out


def orthogonality_report(df: pd.DataFrame, cols=("coherence", "spanning", "n_domains",
                                                 "tag_spanning")) -> pd.DataFrame:
    """Pairwise correlation matrix of the candidate measures."""
    return df[list(cols)].corr()


def orthogonalise(df: pd.DataFrame, target: str, controls=("coherence",)) -> pd.Series:
    """Residual of `target` on `controls` (+ intercept), used to break collinearity.

    The main specification regresses spanning on coherence and keeps the residual,
    so that the spanning coefficient is identified from within-coherence variation.
    """
    d = df.dropna(subset=[target, *controls])
    A = np.column_stack([np.ones(len(d)), d[list(controls)].values])
    b = np.linalg.pinv(A.T @ A) @ (A.T @ d[target].values)
    resid = d[target].values - A @ b
    return pd.Series(resid, index=d.index, name=f"{target}_orth")
