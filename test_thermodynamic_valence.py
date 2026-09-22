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

if __name__ == "__main__":
    unittest.main()
