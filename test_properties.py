"""
Property-based tests of the estimators: invariances that must hold for every input, checked on
many generated cases instead of a few hand-picked ones. Generation is derandomized, so every run
explores the same cases (as the fixed seeds of the other tests do).
"""

import unittest

import numpy as np
from hypothesis import given, settings
from hypothesis import strategies as st

from demarcation import numerical_rank
from thermodynamic_valence import estimate_kl_divergence_knn

SETTINGS = settings(max_examples=40, deadline=None, derandomize=True)


def gaussian_samples(seed, n, d, shift):
    rng = np.random.default_rng(seed)
    return rng.normal(0.0, 1.0, size=(n, d)), rng.normal(shift, 1.0, size=(n, d))


class KLDivergenceProperties(unittest.TestCase):
    @SETTINGS
    @given(seed=st.integers(0, 2**32 - 1), n=st.integers(40, 200), d=st.integers(1, 3),
           shift=st.floats(-2.0, 2.0), offset=st.floats(-1e3, 1e3), scale=st.floats(1e-2, 1e2))
    def test_invariant_under_a_common_translation_and_scaling(self, seed, n, d, shift, offset, scale):
        # k-NN distances change by the same factor in P and Q, so their log-ratio does not change
        p, q = gaussian_samples(seed, n, d, shift)
        base = estimate_kl_divergence_knn(p, q, k=5)
        moved = estimate_kl_divergence_knn(p * scale + offset, q * scale + offset, k=5)
        self.assertAlmostEqual(base, moved, delta=1e-6 * max(1.0, abs(base)))

    @SETTINGS
    @given(seed=st.integers(0, 2**32 - 1), n=st.integers(40, 200), shift=st.floats(-3.0, 3.0))
    def test_is_never_negative(self, seed, n, shift):
        p, q = gaussian_samples(seed, n, 1, shift)
        self.assertGreaterEqual(estimate_kl_divergence_knn(p, q, k=5), 0.0)


class NumericalRankProperties(unittest.TestCase):
    @SETTINGS
    @given(seed=st.integers(0, 2**32 - 1), rows=st.integers(1, 8), cols=st.integers(1, 8),
           rank=st.integers(1, 8), delta=st.floats(1e-9, 1e-3))
    def test_bounded_and_invariant_under_permutation_and_transposition(self, seed, rows, cols, rank, delta):
        rng = np.random.default_rng(seed)
        r = min(rank, rows, cols)
        matrix = rng.normal(size=(rows, r)) @ rng.normal(size=(r, cols))  # rank r by construction
        value = numerical_rank(matrix, delta)
        self.assertLessEqual(value, min(rows, cols))
        self.assertEqual(value, numerical_rank(matrix[rng.permutation(rows)], delta))
        self.assertEqual(value, numerical_rank(matrix.T, delta))
        self.assertEqual(value, r)


if __name__ == "__main__":
    unittest.main()
