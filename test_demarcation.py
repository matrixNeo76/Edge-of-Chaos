"""
test_demarcation.py
===================
Tests of the three operational demarcation conditions (demarcation.py) on systems whose
answer is known in advance.
"""

import unittest
import numpy as np

from demarcation import (
    numerical_rank,
    noise_floor_from_recordings,
    causal_non_separability,
    conditional_mutual_information,
    residual_memory,
    iaaft_surrogate,
    non_markovian_memory,
    phase_space_regions,
    state_dependent_dynamics,
    is_candidate,
)
from synthetic_systems import ar1, nonlinear_lag5, linear_2d, double_well, response_matrices


class TestCausalNonSeparability(unittest.TestCase):

    def test_numerical_rank_counts_singular_values_above_delta(self):
        matrix = np.diag([3.0, 1.0, 0.1, 0.0])
        self.assertEqual(numerical_rank(matrix, 0.05), 3)
        self.assertEqual(numerical_rank(matrix, 0.5), 2)

    def test_extra_modes_beyond_linear_model_pass(self):
        r, r_lin, noise = response_matrices(seed=1)
        delta = noise_floor_from_recordings(noise)
        result = causal_non_separability(r, r_lin, delta)
        self.assertEqual((result["rank_R"], result["rank_R_lin"]), (5, 3))
        self.assertTrue(result["passes"])
        self.assertFalse(causal_non_separability(r_lin, r_lin, delta)["passes"])

    def test_invalid_input(self):
        with self.assertRaises(ValueError):
            causal_non_separability(np.eye(3), np.eye(4), 0.1)
        with self.assertRaises(ValueError):
            numerical_rank(np.array([[np.nan, 1.0], [0.0, 1.0]]), 0.1)
        with self.assertRaises(ValueError):
            numerical_rank(np.eye(2), -1.0)


class TestNonMarkovianMemory(unittest.TestCase):

    def test_mutual_information_matches_gaussian_value(self):
        rng = np.random.default_rng(2)
        x = rng.normal(size=3000)
        y = 0.8 * x + 0.6 * rng.normal(size=3000)
        expected = -0.5 * np.log(1 - 0.8 ** 2)
        self.assertAlmostEqual(conditional_mutual_information(x, y), expected, delta=0.06)
        self.assertAlmostEqual(conditional_mutual_information(x, rng.normal(size=3000)), 0.0, delta=0.03)

    def test_conditional_mutual_information_vanishes_given_the_common_cause(self):
        rng = np.random.default_rng(3)
        z = rng.normal(size=3000)
        x = z + 0.5 * rng.normal(size=3000)
        y = z + 0.5 * rng.normal(size=3000)
        self.assertGreater(conditional_mutual_information(x, y), 0.3)
        self.assertAlmostEqual(conditional_mutual_information(x, y, z), 0.0, delta=0.03)

    def test_quantized_data_do_not_bias_the_estimator(self):
        """
        ADC data are quantized. Without dithering, two independent variables rounded to
        0.1 gave 0.19 nats and rounded to 1.0 gave -3.8; with it they give about 0.
        """
        rng = np.random.default_rng(6)
        x, y = rng.normal(size=3000), rng.normal(size=3000)
        for step in (0.1, 0.5, 1.0):
            xq, yq = np.round(x / step) * step, np.round(y / step) * step
            self.assertAlmostEqual(conditional_mutual_information(xq, yq), 0.0, delta=0.03)
        self.assertGreater(abs(conditional_mutual_information(np.round(x, 1), np.round(y, 1), jitter=False)), 0.1)
        # Dependence survives quantization
        y_dep = 0.8 * x + 0.6 * rng.normal(size=3000)
        self.assertAlmostEqual(conditional_mutual_information(np.round(x, 1), np.round(y_dep, 1)),
                               -0.5 * np.log(1 - 0.8 ** 2), delta=0.06)

    def test_quantized_markov_process_has_no_spurious_memory(self):
        quantized = np.round(ar1(3000), 0)
        for order in (1, 2):
            self.assertAlmostEqual(residual_memory(quantized, order, past_lags=3), 0.0, delta=0.03)

    def test_dither_is_reproducible_and_leaves_continuous_data_unchanged(self):
        rng = np.random.default_rng(7)
        x, y = rng.normal(size=500), rng.normal(size=500)
        self.assertEqual(conditional_mutual_information(x, y), conditional_mutual_information(x, y))
        self.assertAlmostEqual(conditional_mutual_information(x, y), conditional_mutual_information(x, y, jitter=False), places=6)

    def test_residual_memory_identifies_markov_order(self):
        series = nonlinear_lag5(3000)
        for order in (1, 2, 3, 4):
            self.assertGreater(residual_memory(series, order, past_lags=5), 0.2)
        for order in (5, 6):
            self.assertAlmostEqual(residual_memory(series, order, past_lags=5), 0.0, delta=0.03)
        for order in (1, 2):
            self.assertAlmostEqual(residual_memory(ar1(3000), order, past_lags=5), 0.0, delta=0.03)

    def test_iaaft_preserves_amplitudes_and_spectrum(self):
        series = nonlinear_lag5(2048)
        surrogate = iaaft_surrogate(series, rng=np.random.default_rng(0))
        np.testing.assert_allclose(np.sort(surrogate), np.sort(series))
        spectrum = np.abs(np.fft.rfft(series))
        spectrum_s = np.abs(np.fft.rfft(surrogate))
        self.assertLess(np.linalg.norm(spectrum - spectrum_s) / np.linalg.norm(spectrum), 0.1)

    def test_condition_passes_for_nonlinear_memory_and_fails_for_markov(self):
        # Reduced surrogate count and percentile to keep the test fast.
        settings = dict(k_max=2, past_lags=5, n_surrogates=9, percentile=90.0)
        self.assertTrue(non_markovian_memory(nonlinear_lag5(1500), **settings)["passes"])
        self.assertFalse(non_markovian_memory(ar1(1500), **settings)["passes"])

    def test_invalid_input(self):
        with self.assertRaises(ValueError):
            residual_memory(np.arange(20.0), order=3)
        with self.assertRaises(ValueError):
            non_markovian_memory(ar1(500), k_max=0)
        with self.assertRaises(ValueError):
            conditional_mutual_information(np.zeros(10), np.zeros(9))


class TestStateDependentDynamics(unittest.TestCase):

    def test_regions_are_disjoint_and_cover_the_states(self):
        states = np.random.default_rng(4).normal(size=(900, 2))
        regions = phase_space_regions(states, 3)
        indices = np.concatenate(regions)
        self.assertEqual(len(indices), len(states) - 1)
        self.assertEqual(len(np.unique(indices)), len(indices))

    def test_linear_system_fails_nonlinear_system_passes(self):
        self.assertFalse(state_dependent_dynamics(linear_2d(20000, seed=5))["passes"])
        self.assertTrue(state_dependent_dynamics(double_well(20000, seed=5))["passes"])

    def test_null_controls_false_positives_on_short_records(self):
        """
        With theta_state alone, estimation noise passed a linear system in 20 of 20 runs at
        1000 samples. With the linear-surrogate null (95th percentile) the false positive
        rate stays near the nominal 5%.
        """
        runs = [state_dependent_dynamics(linear_2d(1000, seed=s), n_null=49) for s in range(10)]
        self.assertLessEqual(sum(r["passes"] for r in runs), 2)
        # The papers' criterion alone (n_null = 0) is fooled by the same data
        fooled = [state_dependent_dynamics(linear_2d(1000, seed=s), n_null=0) for s in range(10)]
        self.assertGreaterEqual(sum(r["passes"] for r in fooled), 8)

    def test_null_threshold_reported(self):
        result = state_dependent_dynamics(double_well(20000, seed=1), n_null=19)
        self.assertIsNotNone(result["null_threshold"])
        self.assertGreater(result["statistic"], result["null_threshold"])
        with self.assertRaises(ValueError):
            state_dependent_dynamics(linear_2d(500), n_null=-1)

    def test_candidate_requires_all_three(self):
        yes, no = {"passes": True}, {"passes": False}
        self.assertTrue(is_candidate(yes, yes, yes))
        self.assertFalse(is_candidate(yes, no, yes))


if __name__ == "__main__":
    unittest.main()
