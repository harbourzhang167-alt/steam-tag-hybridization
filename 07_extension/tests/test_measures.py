# -*- coding: utf-8 -*-
"""
Unit tests for the tag-space measures.

Run:  python -m unittest discover -s 07_extension/tests -v
 or:  python 07_extension/tests/test_measures.py
"""
import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from measures import (coherence, entropy_coherence, spanning, spanning_diluted,  # noqa: E402
                      tag_spanning, n_domains_spanned, domain_shares)
from tagspace import npmi_matrix, embed_tags, build_cooccurrence  # noqa: E402


class TestCoherenceSpanning(unittest.TestCase):
    """Hand-built cases with known answers."""

    def setUp(self):
        # three domains; D has 0-1 far apart, 2 close to 0
        self.K = 3
        self.t2d = {"a": 0, "b": 1, "c": 2}
        self.D = np.array([[0.0, 1.0, 0.2],
                           [1.0, 0.0, 0.9],
                           [0.2, 0.9, 0.0]])

    def test_single_tag(self):
        g = {"a": 10}
        self.assertAlmostEqual(coherence(g, self.t2d, self.K), 1.0, places=12)
        self.assertAlmostEqual(spanning(g, self.t2d, self.D), 0.0, places=12)
        self.assertAlmostEqual(entropy_coherence(g, self.t2d, self.K), 1.0, places=12)
        self.assertEqual(n_domains_spanned(g, self.t2d), 1)

    def test_same_domain_is_zero_spanning(self):
        g = {"a": 10, "c": 5}          # both domain 0? no: c is domain 2
        self.assertEqual(n_domains_spanned({"a": 10}, self.t2d), 1)
        # three tags mapped into one domain
        t2d = {"a": 0, "a2": 0, "a3": 0}
        g = {"a": 10, "a2": 8, "a3": 3}
        self.assertAlmostEqual(spanning(g, t2d, self.D), 0.0, places=12)
        self.assertAlmostEqual(coherence(g, t2d, self.K), 1.0, places=12)

    def test_two_equal_far_domains_hits_max_distance(self):
        g = {"a": 10, "b": 10}          # equal weight, distance 1.0
        self.assertAlmostEqual(spanning(g, self.t2d, self.D), 1.0, places=12)
        self.assertAlmostEqual(coherence(g, self.t2d, self.K), 0.5, places=12)
        # the diluted (with-replacement) version is halved by self-pairs
        self.assertAlmostEqual(spanning_diluted(g, self.t2d, self.D), 0.5, places=12)

    def test_priority_weighting_matters(self):
        # same tag set, different vote ratios -> different results
        g1 = {"a": 100, "b": 100}
        g2 = {"a": 100, "b": 10}
        self.assertGreater(coherence(g2, self.t2d, self.K), coherence(g1, self.t2d, self.K))
        self.assertLess(spanning(g2, self.t2d, self.D), spanning(g1, self.t2d, self.D))

    def test_monotonicity(self):
        base = {"a": 100, "b": 100}
        cohs, spans = [], []
        for wb in [100, 80, 60, 40, 20, 1]:
            g = {"a": 100, "b": wb}
            cohs.append(coherence(g, self.t2d, self.K))
            spans.append(spanning(g, self.t2d, self.D))
        self.assertTrue(all(x <= y + 1e-12 for x, y in zip(cohs, cohs[1:])),
                        f"coherence not monotone: {cohs}")
        self.assertTrue(all(x >= y - 1e-12 for x, y in zip(spans, spans[1:])),
                        f"spanning not monotone: {spans}")

    def test_bounds(self):
        rng = np.random.RandomState(0)
        for _ in range(200):
            tagset = {k: int(rng.randint(1, 100)) for k in rng.choice(["a", "b", "c"], size=rng.randint(1, 4), replace=False)}
            co = coherence(tagset, self.t2d, self.K)
            sp = spanning(tagset, self.t2d, self.D)
            spd = spanning_diluted(tagset, self.t2d, self.D)
            ec = entropy_coherence(tagset, self.t2d, self.K)
            self.assertTrue(0.0 < co <= 1.0 + 1e-12, co)
            self.assertTrue(-1e-12 <= sp <= self.D.max() + 1e-12, sp)
            self.assertTrue(-1e-12 <= spd <= sp + 1e-12, (spd, sp))
            self.assertTrue(-1e-12 <= ec <= 1.0 + 1e-12, ec)

    def test_distinct_pair_definition_reduces_collinearity(self):
        """The normalised version must correlate less with coherence than the diluted one."""
        rng = np.random.RandomState(7)
        cols = np.array(["a", "b", "c"])
        rows_co, rows_sp, rows_spd = [], [], []
        for _ in range(600):
            n = rng.randint(1, 4)
            tagset = {k: int(rng.randint(1, 100)) for k in rng.choice(cols, size=n, replace=False)}
            rows_co.append(coherence(tagset, self.t2d, self.K))
            rows_sp.append(spanning(tagset, self.t2d, self.D))
            rows_spd.append(spanning_diluted(tagset, self.t2d, self.D))
        c_sp = abs(np.corrcoef(rows_co, rows_sp)[0, 1])
        c_spd = abs(np.corrcoef(rows_co, rows_spd)[0, 1])
        self.assertLess(c_sp, c_spd, f"normalised |r|={c_sp:.3f} not better than diluted {c_spd:.3f}")

    def test_shares_sum_to_one(self):
        g = {"a": 5, "b": 3, "c": 2}
        self.assertAlmostEqual(domain_shares(g, self.t2d, self.K).sum(), 1.0, places=12)

    def test_unknown_tags_ignored(self):
        g = {"a": 10, "zzz": 10}
        self.assertAlmostEqual(coherence(g, self.t2d, self.K), 1.0, places=12)
        self.assertAlmostEqual(spanning(g, self.t2d, self.D), 0.0, places=12)

    def test_empty_game_is_nan(self):
        self.assertTrue(np.isnan(coherence({}, self.t2d, self.K)))
        self.assertTrue(np.isnan(spanning({}, self.t2d, self.D)))


class TestTagSpanning(unittest.TestCase):
    def setUp(self):
        # two orthogonal unit vectors -> cosine distance 1; identical -> 0
        self.emb = np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 0.0]])
        self.idx = {"x": 0, "y": 1, "z": 2}

    def test_identical_tags_zero(self):
        v, n = tag_spanning({"x": 1, "z": 1}, self.idx, self.emb)
        self.assertAlmostEqual(v, 0.0, places=12)
        self.assertEqual(n, 2)

    def test_orthogonal_tags_one(self):
        v, n = tag_spanning({"x": 1, "y": 1}, self.idx, self.emb)
        self.assertAlmostEqual(v, 1.0, places=12)

    def test_single_tag_zero(self):
        v, n = tag_spanning({"x": 5}, self.idx, self.emb)
        self.assertEqual(v, 0.0)
        self.assertEqual(n, 1)

    def test_no_known_tag(self):
        v, n = tag_spanning({"q": 1}, self.idx, self.emb)
        self.assertTrue(np.isnan(v))
        self.assertEqual(n, 0)


class TestTagSpacePrimitives(unittest.TestCase):
    def test_npmi_symmetric_zero_diagonal(self):
        tag_dicts = [{"a": 1, "b": 1}, {"a": 1}, {"b": 1}, {"a": 1, "b": 1}, {"a": 1, "c": 1}]
        vocab, keep, C, dfreq, n = build_cooccurrence(tag_dicts, min_df=1)
        M = npmi_matrix(C, dfreq, n)
        self.assertTrue(np.allclose(M, M.T, atol=1e-12))
        self.assertTrue(np.allclose(np.diag(M), 0.0, atol=1e-12))
        self.assertTrue(np.all(np.isfinite(M)))
        self.assertLessEqual(np.abs(M).max(), 1.0 + 1e-9)

    def test_min_df_filters(self):
        tag_dicts = [{"a": 1, "rare": 1}, {"a": 1}, {"a": 1}]
        vocab, keep, C, dfreq, n = build_cooccurrence(tag_dicts, min_df=2)
        kept_names = {vocab[int(g)] for g in keep}
        self.assertIn("a", kept_names)
        self.assertNotIn("rare", kept_names)

    def test_embedding_rows_normalised(self):
        rng = np.random.RandomState(0)
        M = rng.rand(30, 30)
        M = (M + M.T) / 2
        np.fill_diagonal(M, 0.0)
        E = embed_tags(M, n_components=5)
        norms = np.linalg.norm(E, axis=1)
        self.assertTrue(np.allclose(norms, 1.0, atol=1e-9), norms[:5])


if __name__ == "__main__":
    unittest.main(verbosity=2)
