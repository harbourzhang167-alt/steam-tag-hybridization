# -*- coding: utf-8 -*-
"""
Integration / acceptance tests for the extension.

These enforce the criteria from the approved plan (section 5) that the pure
unit tests cannot cover:

  T7  tag-space reproducibility: rebuilding the consensus partition from the
      same seed reproduces the stored tag -> domain mapping exactly (ARI = 1.0)
  T9  data consistency: the extension sample reproduces the main pipeline frame
      (N = 17,686), the regression sample (N = 17,670) and
      mean(Hybridization_Index) = 9.3145
  T10 join integrity: game_measures_extension.csv x export joins on appid with
      no duplicate keys and no row inflation
  T11 model acceptance: the main model re-estimated here reproduces the C1-C5
      corrected pipeline table (02_pipeline/results/table5_main_regression.csv)
      coefficient for coefficient and HC3 standard error for HC3 standard error

Run:  python 07_extension/tests/test_integration.py
      (takes ~1 min because it rebuilds the 100-run consensus partition)
"""
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "07_extension"))

from common import PATHS, SAMPLE, load_sample, tag_dicts, ols, parse_meta_dict  # noqa: E402
from tagspace import (build_cooccurrence, npmi_matrix, graph_from_npmi,        # noqa: E402
                      consensus_domains, DEFAULTS)


class TestDataConsistency(unittest.TestCase):
    """T9 — the sample chain must reproduce the pipeline's frame."""

    @classmethod
    def setUpClass(cls):
        cls.d = load_sample(verbose=False)
        cls.exp = pd.read_csv(PATHS["export"], encoding="utf-8-sig")

    def test_sample_size(self):
        self.assertEqual(len(self.d), SAMPLE["expected_n"],
                         f"extension sample is {len(self.d)}, expected {SAMPLE['expected_n']}")

    def test_appid_set_matches_export(self):
        a = set(self.d["appid"].tolist())
        b = set(self.exp["appid"].tolist())
        self.assertEqual(a, b, f"appid sets differ: only-ext {len(a-b)}, only-export {len(b-a)}")

    def test_regression_sample_size(self):
        n_reg = int((self.exp["Hybridization_Index"] > 0).sum())
        self.assertEqual(n_reg, SAMPLE["expected_reg_n"],
                         f"regression sample is {n_reg}, expected {SAMPLE['expected_reg_n']}")

    def test_index_mean_matches_pipeline(self):
        m = float(self.exp["Hybridization_Index"].mean())
        self.assertAlmostEqual(m, SAMPLE["expected_mean_meta_h"], delta=5e-4,
                               msg=f"mean(Hybridization_Index) = {m}, expected "
                                   f"{SAMPLE['expected_mean_meta_h']}")


class TestJoinIntegrity(unittest.TestCase):
    """T10 — the measures file must join cleanly."""

    @classmethod
    def setUpClass(cls):
        cls.d = load_sample(verbose=False)
        cls.m = pd.read_csv(PATHS["measures"], encoding="utf-8-sig")
        cls.exp = pd.read_csv(PATHS["export"], encoding="utf-8-sig")

    def test_no_duplicate_appid(self):
        self.assertEqual(self.m["appid"].duplicated().sum(), 0, "duplicate appid in measures")
        self.assertEqual(self.exp["appid"].duplicated().sum(), 0, "duplicate appid in export")

    def test_join_does_not_inflate(self):
        j = self.d.merge(self.m, on="appid", how="inner")
        self.assertEqual(len(j), SAMPLE["expected_n"],
                         f"join produced {len(j)} rows, expected {SAMPLE['expected_n']}")

    def test_measures_cover_all_games(self):
        self.assertEqual(self.m["appid"].nunique(), SAMPLE["expected_n"])
        self.assertEqual(int(self.m["coherence"].isna().sum()), 0,
                         "some games could not be scored")


class TestTagSpaceReproducibility(unittest.TestCase):
    """T7 — same seed must reproduce the stored partition exactly."""

    def test_consensus_reproduces_stored_domains(self):
        saved = pd.read_csv(PATHS["tag_nodes"], encoding="utf-8-sig")
        d = load_sample(verbose=False)
        td = tag_dicts(d)

        vocab, keep, C, dfreq, n_docs = build_cooccurrence(td, DEFAULTS["min_df"])
        npmi = npmi_matrix(C, dfreq, n_docs)
        G = graph_from_npmi(npmi, DEFAULTS["edge_threshold"])
        cons = consensus_domains(G, 1.0, n_runs=100, seed=0)

        rebuilt = pd.DataFrame({
            "tag": [vocab[int(g)] for g in keep],
            "domain": cons["labels"],
        })
        merged = saved[["tag", "domain"]].merge(rebuilt, on="tag",
                                                suffixes=("_saved", "_rebuilt"))
        self.assertEqual(len(merged), len(saved), "tag sets differ between saved and rebuilt")

        from sklearn.metrics import adjusted_rand_score
        ari = adjusted_rand_score(merged["domain_saved"], merged["domain_rebuilt"])
        self.assertEqual(round(ari, 10), 1.0,
                         f"rebuilt partition differs from stored (ARI = {ari:.6f})")
        self.assertEqual(int(cons["K"]), int(saved["domain"].max()) + 1,
                         "K differs from the stored partition")

    def test_domain_distance_matrix_saved(self):
        p = PATHS["tag_nodes"].parent / "tag_domain_distances.csv"
        D = pd.read_csv(p, index_col=0, encoding="utf-8-sig").values
        self.assertEqual(D.shape[0], D.shape[1])
        self.assertTrue(np.allclose(D, D.T, atol=1e-9), "distance matrix not symmetric")
        self.assertTrue(np.allclose(np.diag(D), 0.0, atol=1e-12), "diagonal not zero")
        self.assertTrue(np.all((D >= -1e-12) & (D <= 1 + 1e-12)), "Jaccard distance out of [0,1]")


class TestModelAcceptance(unittest.TestCase):
    """T11 — re-estimate the main model and compare with the corrected pipeline table."""

    @classmethod
    def setUpClass(cls):
        cls.m = pd.read_csv(PATHS["measures"], encoding="utf-8-sig")
        cls.ref = pd.read_csv(PATHS["results"].parent.parent / "02_pipeline/results"
                              / "table5_main_regression.csv", encoding="utf-8-sig")

    def test_main_model_reproduces_pipeline(self):
        df = self.m[self.m["Hybridization_Index"] > 0].dropna(
            subset=["Log_Reviews", "price", "Hybridization_Index", "Release_Year"]).copy()
        hm = self.m["Hybridization_Index"].mean()          # full-sample centring, as in the notebook
        df["Hc"] = df["Hybridization_Index"] - hm
        df["Hc2"] = df["Hc"] ** 2
        yd = pd.get_dummies(df["Release_Year"], prefix="Y", drop_first=True,
                            dtype=float).astype(float)
        X = np.column_stack([np.ones(len(df)), df[["Hc", "Hc2", "price"]].values,
                             yd.values.astype(float)])
        names = ["const", "Hybrid_Centered", "Hybrid_Centered_Squared", "price"] + list(yd.columns)
        r = ols(df["Log_Reviews"].values, X, "HC3")

        self.assertEqual(r["n"], 17670, f"N = {r['n']}, expected 17670")
        for _, row in self.ref.iterrows():
            v = row["variable"]
            i = names.index(v)
            self.assertAlmostEqual(r["b"][i], row["coef"], delta=1e-6,
                                   msg=f"{v}: coef {r['b'][i]} vs pipeline {row['coef']}")
            self.assertAlmostEqual(r["se"][i], row["se_hc3"], delta=1e-6,
                                   msg=f"{v}: HC3 SE {r['se'][i]} vs pipeline {row['se_hc3']}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
