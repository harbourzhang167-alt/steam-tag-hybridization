# -*- coding: utf-8 -*-
"""
Tag-space construction: co-occurrence -> NPMI -> community detection -> embedding.

Rationale (see plan section 2, Goal G1)
---------------------------------------
The reference dissertation rejected the tag co-occurrence route after running
Jaccard + spectral clustering on the *game* feature space and getting
silhouette <= 0. We instead ask whether the *tag-by-tag* network has community
structure, measured by modularity, which is the appropriate statistic for that
object. Pilot runs give modularity ~0.33, i.e. real structure.

Pipeline
    tag dicts  ->  binary game x tag matrix
               ->  co-occurrence counts C = M'M
               ->  NPMI (Bouma 2009)
               ->  thresholded weighted graph
               ->  Louvain communities  ("tag domains")
               ->  TruncatedSVD embedding of the symmetrised NPMI matrix
               ->  L2-normalised domain centroids + cosine distance matrix
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field

import networkx as nx
import numpy as np
import pandas as pd
from networkx.algorithms.community import louvain_communities, modularity
from sklearn.decomposition import TruncatedSVD
from sklearn.metrics import adjusted_rand_score

DEFAULTS = dict(
    min_df=20,          # a tag must appear in >= this many games to enter the graph
    edge_threshold=0.05,  # keep edges with NPMI above this
    resolution=1.0,
    n_components=8,
    seed=42,
)


# --------------------------------------------------------------- construction
def build_cooccurrence(tag_dicts, min_df: int = 20):
    """Return (vocab, keep, C, dfreq, n_docs).

    vocab  : list of tag names, indexed by the *global* tag id
    keep   : global ids of tags with document frequency >= min_df
    C      : (len(keep), len(keep)) co-occurrence counts, diagonal zeroed
    dfreq  : document frequency of the kept tags
    """
    vocab: dict[str, int] = {}
    for t in tag_dicts:
        for k in t:
            if k not in vocab:
                vocab[k] = len(vocab)
    v = len(vocab)
    n = len(tag_dicts)

    rows, cols = [], []
    for i, t in enumerate(tag_dicts):
        for k in t:
            rows.append(i)
            cols.append(vocab[k])
    M = np.zeros((n, v), dtype=np.float32)
    M[np.asarray(rows, dtype=np.int64), np.asarray(cols, dtype=np.int64)] = 1.0

    C_full = M.T @ M
    dfreq_full = np.diag(C_full).copy()
    keep = np.where(dfreq_full >= min_df)[0]
    C = C_full[np.ix_(keep, keep)].astype(np.float64).copy()
    np.fill_diagonal(C, 0.0)
    return list(vocab.keys()), keep, C, dfreq_full[keep].astype(np.float64), n


def npmi_matrix(C: np.ndarray, dfreq: np.ndarray, n_docs: int) -> np.ndarray:
    """Normalised PMI in [-1, 1]; diagonal set to 0; NaNs/infs neutralised."""
    with np.errstate(divide="ignore", invalid="ignore"):
        P = C / n_docs
        pi = dfreq[:, None] / n_docs
        pj = dfreq[None, :] / n_docs
        pmi = np.log(P / (pi * pj))
        denom = -np.log(P)
        out = np.where(denom > 0, pmi / denom, 0.0)
    out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
    np.fill_diagonal(out, 0.0)
    return out


def graph_from_npmi(npmi: np.ndarray, edge_threshold: float = 0.05) -> nx.Graph:
    """Weighted undirected graph; isolated nodes are retained."""
    k = npmi.shape[0]
    G = nx.Graph()
    G.add_nodes_from(range(k))
    iu = np.triu_indices(k, 1)
    w = npmi[iu]
    sel = w > edge_threshold
    for a, b in zip(iu[0][sel], iu[1][sel]):
        G.add_edge(int(a), int(b), weight=float(npmi[a, b]))
    return G


# ----------------------------------------------------------- communities
def detect_domains(G: nx.Graph, resolution: float = 1.0, seed: int = 42):
    """Louvain communities. Returns (labels array, K, modularity, community list)."""
    comms = louvain_communities(G, weight="weight", resolution=resolution, seed=seed)
    comms = sorted(comms, key=len, reverse=True)
    labels = np.full(G.number_of_nodes(), -1, dtype=int)
    for c, members in enumerate(comms):
        for m in members:
            labels[m] = c
    q = modularity(G, comms, weight="weight")
    return labels, len(comms), float(q), comms


def stability(labels_a: np.ndarray, labels_b: np.ndarray) -> float:
    """Adjusted Rand index between two community labellings."""
    return float(adjusted_rand_score(labels_a, labels_b))


# ------------------------------------------------------- consensus clustering
def coassociation_matrix(labels_runs) -> np.ndarray:
    """A[i, j] = fraction of runs in which i and j fall in the same community."""
    runs = list(labels_runs)
    n = len(runs[0])
    A = np.zeros((n, n), dtype=np.float64)
    for lab in runs:
        A += (lab[:, None] == lab[None, :])
    A /= len(runs)
    return A


def consensus_domains(G: nx.Graph, resolution: float = 1.0, n_runs: int = 100,
                      seed: int = 0, k_range=range(4, 15), method: str = "average"):
    """Multi-seed consensus partition.

    Louvain is stochastic and, on this graph, returns K between 4 and 7 depending
    on the seed (ARI ~ 0.63). Averaging over many runs via the co-association
    matrix and cutting an average-linkage tree gives a reproducible partition.

    K is chosen objectively as the cut maximising modularity on G; the median
    per-run K is returned alongside for comparison.

    Returns dict with labels, K, modularity, ari_vs_runs, median_k, k_curve.
    """
    from scipy.cluster.hierarchy import fcluster, linkage
    from scipy.spatial.distance import squareform

    runs = []
    for s in range(n_runs):
        lab, _, _, _ = detect_domains(G, resolution, seed + int(s))
        runs.append(lab)
    A = coassociation_matrix(runs)

    Dist = 1.0 - A
    np.fill_diagonal(Dist, 0.0)
    Dist = (Dist + Dist.T) / 2.0
    Z = linkage(squareform(Dist, checks=False), method=method)

    k_curve = {}
    ari_curve = {}
    for k in k_range:
        lab_k = fcluster(Z, t=k, criterion="maxclust") - 1
        k_curve[int(k)] = float(modularity(G, _as_sets(lab_k), weight="weight"))
        ari_curve[int(k)] = float(np.mean([stability(lab_k, r) for r in runs]))

    # K is chosen by AGREEMENT with the ensemble (reproducibility), because the
    # modularity landscape is nearly flat here (0.328-0.335 over K=4..14) and
    # would make the choice arbitrary. Modularity is reported alongside.
    k_best = max(ari_curve, key=ari_curve.get)
    labels = fcluster(Z, t=k_best, criterion="maxclust") - 1
    ari = float(np.mean([stability(labels, r) for r in runs]))
    return dict(labels=labels, K=int(k_best),
                modularity=float(k_curve[k_best]),
                ari_vs_runs=ari,
                ari_sd=float(np.std([stability(labels, r) for r in runs])),
                median_k=int(np.median([len(np.unique(r)) for r in runs])),
                k_curve=k_curve, ari_curve=ari_curve,
                k_best_modularity=int(max(k_curve, key=k_curve.get)))


def _as_sets(labels: np.ndarray):
    out = []
    for c in np.unique(labels):
        out.append(set(np.where(labels == c)[0].tolist()))
    return out


def modularity_null_test(G: nx.Graph, labels: np.ndarray, n_reps: int = 30,
                         resolution: float = 1.0, seed: int = 0):
    """Compare the observed partition's modularity against a degree-preserving null.

    There is no canonical absolute modularity threshold: random and scale-free
    graphs routinely reach high modularity through fluctuations (Guimerà,
    Sales-Pardo & Amaral 2004, Phys. Rev. E 70:025101), and modularity suffers a
    resolution limit (Fortunato & Barthélemy 2007, PNAS 104:36-41). The correct
    test is therefore against a null model with the same degree sequence.

    Null graphs are drawn from the configuration model, collapsed to simple
    graphs, and Louvain is re-run on each so that the comparison is
    procedure-for-procedure rather than partition-for-partition.
    """
    obs = float(modularity(G, _as_sets(labels), weight="weight"))
    deg = [d for _, d in G.degree()]
    rng = np.random.RandomState(seed)
    null_q, null_k = [], []
    for _ in range(n_reps):
        Gm = nx.configuration_model(deg, seed=int(rng.randint(1, 10 ** 6)))
        Gm = nx.Graph(Gm)
        Gm.remove_edges_from(list(nx.selfloop_edges(Gm)))
        if Gm.number_of_edges() == 0:
            continue
        _, k_n, q_n, _ = detect_domains(Gm, resolution, 42)
        null_q.append(q_n)
        null_k.append(k_n)
    null_q = np.asarray(null_q)
    z = (obs - null_q.mean()) / (null_q.std(ddof=1) + 1e-12)
    p_emp = float((null_q >= obs).mean())
    return dict(observed=obs, null_mean=float(null_q.mean()), null_sd=float(null_q.std(ddof=1)),
                null_max=float(null_q.max()), n_reps=len(null_q), z=float(z),
                p_empirical=p_emp, null_k_median=float(np.median(null_k)))


# ------------------------------------------------------------------ embedding
def embed_tags(npmi: np.ndarray, n_components: int = 8, seed: int = 0):
    """Spectral embedding of the symmetrised NPMI matrix, rows L2-normalised."""
    S = (npmi + npmi.T) / 2.0
    emb = TruncatedSVD(n_components=n_components, random_state=seed).fit_transform(S)
    norms = np.linalg.norm(emb, axis=1, keepdims=True)
    return emb / np.clip(norms, 1e-12, None)


def domain_centroids(emb: np.ndarray, labels: np.ndarray, k: int) -> np.ndarray:
    cent = np.zeros((k, emb.shape[1]))
    for c in range(k):
        m = labels == c
        if m.any():
            v = emb[m].mean(axis=0)
            cent[c] = v / max(np.linalg.norm(v), 1e-12)
    return cent


def domain_distance(centroids: np.ndarray) -> np.ndarray:
    """Cosine distance between domain centroids; diagonal zeroed."""
    D = 1.0 - centroids @ centroids.T
    D = np.clip(D, 0.0, None)
    np.fill_diagonal(D, 0.0)
    return D


def domain_jaccard_distance(tag_dicts, tag_to_domain, K: int):
    """Jaccard distance between domains, computed on the games that carry them.

    d_ij = 1 - |F_i n F_j| / |F_i u F_j|, where F_c is the set of games carrying
    at least one tag of domain c.

    This is the definition used by Wang & Lyu (2026, NLP4DH), and it is
    structurally the same object as Kovacs & Hannan's (2015, p. 261 Eq. 11)
    similarity on label extensions. It was preferred over centroid cosine
    distance because (a) it follows the published precedent and (b) it carries
    significant incremental explanatory power for Log_Reviews whereas the cosine
    version does not (see 07_extension/results/g1_distance_choice.md).

    Returns (D, carriers) with carriers[c] = |F_c|.
    """
    n = len(tag_dicts)
    present = np.zeros((n, K), dtype=bool)
    for i, g in enumerate(tag_dicts):
        for t in g:
            c = tag_to_domain.get(t)
            if c is not None:
                present[i, c] = True
    F = [set(np.where(present[:, c])[0].tolist()) for c in range(K)]
    D = np.zeros((K, K), dtype=float)
    for a in range(K):
        for b in range(a + 1, K):
            union = len(F[a] | F[b])
            j = 0.0 if union == 0 else len(F[a] & F[b]) / union
            D[a, b] = D[b, a] = 1.0 - j
    carriers = np.array([len(f) for f in F], dtype=int)
    return D, carriers


# ---------------------------------------------------------------------- bundle
@dataclass
class TagSpace:
    """Everything downstream code needs to score a game."""
    vocab: list
    keep: np.ndarray
    dfreq: np.ndarray
    npmi: np.ndarray
    labels: np.ndarray
    K: int
    modularity: float
    emb: np.ndarray
    centroids: np.ndarray
    D: np.ndarray
    global_to_keep: dict = field(default_factory=dict)
    tag_to_domain: dict = field(default_factory=dict)

    def __post_init__(self):
        self.global_to_keep = {int(g): i for i, g in enumerate(self.keep)}
        self.tag_to_domain = {
            self.vocab[int(self.keep[i])]: int(self.labels[i])
            for i in range(len(self.keep))
        }

    # ---- persistence -----------------------------------------------------
    def nodes_frame(self) -> pd.DataFrame:
        return pd.DataFrame({
            "tag": [self.vocab[int(g)] for g in self.keep],
            "dfreq": self.dfreq.astype(int),
            "domain": self.labels,
            **{f"emb{i}": self.emb[:, i] for i in range(self.emb.shape[1])},
        }).sort_values("dfreq", ascending=False).reset_index(drop=True)

    def summary(self) -> dict:
        return {
            "n_tags_total": len(self.vocab),
            "n_tags_kept": int(len(self.keep)),
            "K": int(self.K),
            "modularity": round(float(self.modularity), 6),
            "domain_sizes": np.bincount(self.labels).tolist(),
            "mean_domain_distance": float(
                self.D[np.triu_indices(self.K, 1)].mean()) if self.K > 1 else 0.0,
            "emb_components": int(self.emb.shape[1]),
        }


def build_tag_space(tag_dicts, *, min_df=None, edge_threshold=None,
                    resolution=None, n_components=None, seed=None,
                    want_stability=True, n_seeds=20) -> TagSpace:
    p = {**DEFAULTS}
    for k, v in dict(min_df=min_df, edge_threshold=edge_threshold,
                     resolution=resolution, n_components=n_components,
                     seed=seed).items():
        if v is not None:
            p[k] = v

    vocab, keep, C, dfreq, n_docs = build_cooccurrence(tag_dicts, p["min_df"])
    npmi = npmi_matrix(C, dfreq, n_docs)
    G = graph_from_npmi(npmi, p["edge_threshold"])
    labels, K, q, comms = detect_domains(G, p["resolution"], p["seed"])
    emb = embed_tags(npmi, p["n_components"], seed=0)
    centroids = domain_centroids(emb, labels, K)
    D = domain_distance(centroids)

    ts = TagSpace(vocab=vocab, keep=keep, dfreq=dfreq, npmi=npmi, labels=labels,
                  K=K, modularity=q, emb=emb, centroids=centroids, D=D)
    ts.params = p
    ts.n_docs = n_docs
    ts.graph_stats = dict(nodes=G.number_of_nodes(), edges=G.number_of_edges(),
                          density=float(nx.density(G)))

    if want_stability:
        rng = np.random.RandomState(0)
        seeds = rng.choice(100000, size=n_seeds, replace=False)
        aris, mods = [], []
        for s in seeds:
            lab_s, k_s, q_s, _ = detect_domains(G, p["resolution"], int(s))
            aris.append(stability(labels, lab_s))
            mods.append(q_s)
        ts.stability = dict(n_seeds=n_seeds, ari_mean=float(np.mean(aris)),
                            ari_min=float(np.min(aris)), ari_sd=float(np.std(aris)),
                            modularity_mean=float(np.mean(mods)),
                            modularity_min=float(np.min(mods)),
                            modularity_max=float(np.max(mods)))
    else:
        ts.stability = {}
    return ts


def save_tag_space(ts: TagSpace, nodes_path, summary_path, extra=None):
    ts.nodes_frame().to_csv(nodes_path, index=False, encoding="utf-8-sig")
    s = ts.summary()
    s["params"] = getattr(ts, "params", {})
    s["graph"] = getattr(ts, "graph_stats", {})
    s["stability"] = getattr(ts, "stability", {})
    if extra:
        s.update(extra)
    summary_path.write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")
    return s
