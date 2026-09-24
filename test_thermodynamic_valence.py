"""
test_thermodynamic_valence.py
===============================
Unit and E2E test suite for the metrology script (P0_Distilled v0.1)

Author: Lakatosian Research Programme
Description:
  Verifies the mathematical correctness, numerical stability, and metrology
  constraints of the `thermodynamic_valence.py` script.
"""

import unittest
import numpy as np
import sys
import os

# Import the functions from the thermodynamic_valence script
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from thermodynamic_valence import (
    simulate_neuromorphic_substrate_sde,
    estimate_kl_divergence_knn,
    calculate_thermodynamic_valence
)

class TestThermodynamicValence(unittest.TestCase):

    def test_sde_simulation_integrity(self):
        """Verifies that the SDE simulation produces correctly sized arrays, with no NaN or Inf."""
        n_steps = 1000
        x_A1, s_obs, s_pred, dt = simulate_neuromorphic_substrate_sde(n_steps=n_steps, seed=123)

        self.assertEqual(len(x_A1), n_steps)
        self.assertEqual(len(s_obs), n_steps)
        self.assertEqual(len(s_pred), n_steps)
        self.assertGreater(dt, 0.0)

        # Absence of non-numeric values
        self.assertFalse(np.isnan(x_A1).any(), "x_A1 contains NaN values")
        self.assertFalse(np.isinf(x_A1).any(), "x_A1 contains Inf values")
        self.assertFalse(np.isnan(s_obs).any(), "s_obs contains NaN values")
        self.assertFalse(np.isnan(s_pred).any(), "s_pred contains NaN values")

    def test_kl_divergence_knn_properties(self):
        """Verifies the fundamental properties of the k-NN Kullback-Leibler divergence estimate."""
        np.random.seed(42)

        # 1. D_KL between two samples of the same distribution N(0, 1) should be close to 0
        p_samples = np.random.normal(0, 1, size=1000)
        q_identical = np.random.normal(0, 1, size=1000)
        d_kl_zero = estimate_kl_divergence_knn(p_samples, q_identical, k=5)

        self.assertGreaterEqual(d_kl_zero, 0.0)
        self.assertLess(d_kl_zero, 0.2, f"D_KL between identical distributions should be close to 0, got {d_kl_zero}")

        # 2. D_KL between two different distributions N(0, 1) and N(2, 1) should be clearly > 0
        q_shifted = np.random.normal(2, 1, size=1000)
        d_kl_positive = estimate_kl_divergence_knn(p_samples, q_shifted, k=5)

        self.assertGreater(d_kl_positive, 1.0, f"D_KL between shifted distributions should be significantly positive, got {d_kl_positive}")

    def test_kl_estimator_matches_analytic_gaussian_values(self):
        """k-NN estimate against the closed-form KL divergence of two Gaussians."""
        rng = np.random.default_rng(0)

        def gaussian_kl(m1, s1, m2, s2):
            return np.log(s2 / s1) + (s1 ** 2 + (m1 - m2) ** 2) / (2 * s2 ** 2) - 0.5

        for m1, s1, m2, s2 in [(0, 1, 1, 1), (0, 1, 0, 2), (0.5, 0.3, 0, 1)]:
            p = rng.normal(m1, s1, size=(4000, 1))
            q = rng.normal(m2, s2, size=(4000, 1))
            self.assertAlmostEqual(estimate_kl_divergence_knn(p, q, k=5), gaussian_kl(m1, s1, m2, s2), delta=0.08)

        # Two dimensions: unit shift in each coordinate gives KL = 1
        p = rng.normal(0, 1, size=(4000, 2))
        q = rng.normal(1, 1, size=(4000, 2))
        self.assertAlmostEqual(estimate_kl_divergence_knn(p, q, k=5), 1.0, delta=0.1)

    def test_thermodynamic_valence_keys_and_bounds(self):
        """Verifies that the valence computation returns the expected keys and finite values."""
        x_A1, s_obs, s_pred, dt = simulate_neuromorphic_substrate_sde(n_steps=2000, seed=42)
        res = calculate_thermodynamic_valence(x_A1, s_obs, s_pred, dt)

        expected_keys = {"sigma_ex", "sigma_hk", "d_kl_allostatic", "g_pred", "psi_valence"}
        self.assertEqual(set(res.keys()), expected_keys)

        for key, val in res.items():
            self.assertTrue(np.isfinite(val), f"Metric {key} is not a finite value: {val}")

        self.assertGreaterEqual(res["sigma_hk"], 0.0, "Housekeeping dissipation must be non-negative")
        self.assertGreaterEqual(res["sigma_ex"], 0.0, "Excess dissipation must be non-negative")
        self.assertGreaterEqual(res["d_kl_allostatic"], 0.0, "Allostatic D_KL must be non-negative")

    def test_ablation_efference_copy_degradation(self):
        """
        Verifies the system's sensitivity: a completely random efference copy (white noise)
        should degrade or nullify the predictive gain G_pred relative to an informed copy.
        """
        np.random.seed(99)
        x_A1, s_obs, s_pred, dt = simulate_neuromorphic_substrate_sde(n_steps=3000, seed=99)

        # Valence with a normal efference copy
        res_normal = calculate_thermodynamic_valence(x_A1, s_obs, s_pred, dt)

        # Valence with an ablated efference copy (disconnected random noise)
        s_pred_ablated = np.random.normal(5.0, 2.0, size=len(s_pred))
        res_ablated = calculate_thermodynamic_valence(x_A1, s_obs, s_pred_ablated, dt)

        # The predictive gain with the random copy should be lower
        self.assertLess(
            res_ablated["g_pred"],
            res_normal["g_pred"] + 1e-3,
            "Ablating the efference copy should reduce the predictive gain G_pred"
        )

    def test_ablation_centred_on_niche_reduces_gain(self):
        """
        Regression test: before v0.2.1, G_pred compared the prediction with the target
        niche instead of with the observations, so noise centred on the niche (as in
        valence_dashboard.py) raised G_pred and Psi instead of lowering them.
        """
        x_A1, s_obs, s_pred, dt = simulate_neuromorphic_substrate_sde(n_steps=2000, seed=42)
        s_pred_ablated = np.random.default_rng(2026).normal(0.0, 1.0, size=len(s_pred))

        res_normal = calculate_thermodynamic_valence(x_A1, s_obs, s_pred, dt)
        res_ablated = calculate_thermodynamic_valence(x_A1, s_obs, s_pred_ablated, dt)

        self.assertLess(res_ablated["g_pred"], res_normal["g_pred"])
        self.assertLess(res_ablated["psi_valence"], res_normal["psi_valence"])

    def test_valence_is_deterministic(self):
        """Equal inputs give equal outputs: the target niche is drawn from a fixed seed."""
        x_A1, s_obs, s_pred, dt = simulate_neuromorphic_substrate_sde(n_steps=1000, seed=5)
        first = calculate_thermodynamic_valence(x_A1, s_obs, s_pred, dt)
        second = calculate_thermodynamic_valence(x_A1, s_obs, s_pred, dt)
        self.assertEqual(first, second)

    def test_invalid_input_raises(self):
        """Invalid input raises ValueError instead of returning silently wrong numbers."""
        x_A1, s_obs, s_pred, dt = simulate_neuromorphic_substrate_sde(n_steps=200, seed=1)
        cases = {
            "unequal lengths": (x_A1, s_obs[:-5], s_pred, dt),
            "NaN": (np.r_[x_A1[:-1], np.nan], s_obs, s_pred, dt),
            "too short for tau": (x_A1[:12], s_obs[:12], s_pred[:12], dt),
            "zero dt": (x_A1, s_obs, s_pred, 0.0),
        }
        for name, args in cases.items():
            with self.subTest(name), self.assertRaises(ValueError):
                calculate_thermodynamic_valence(*args)
        with self.assertRaises(ValueError):
            estimate_kl_divergence_knn(np.array([]), np.ones(10))
        with self.assertRaises(ValueError):
            estimate_kl_divergence_knn(np.ones((20, 2)), np.ones((20, 1)))
        with self.assertRaises(ValueError):
            simulate_neuromorphic_substrate_sde(n_steps=1)

if __name__ == "__main__":
    unittest.main()
