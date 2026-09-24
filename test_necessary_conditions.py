"""
test_necessary_conditions.py
============================
Tests of the operational criteria for the necessary conditions (necessary_conditions.py)
on cases whose answer is known in advance.
"""

import unittest
import numpy as np

from necessary_conditions import (
    edge_of_chaos,
    first_order_admittance,
    causal_degeneracy,
    degenerate_directions,
    degeneracy_radius,
    degeneracy_prediction,
    exponent_stability,
)


class TestEdgeOfChaos(unittest.TestCase):

    def setUp(self):
        self.freqs = np.linspace(0.1, 100.0, 500)

    def test_locally_active_and_stable_device_passes(self):
        # Re Y(0) = g0 + gain / rate = 0.1 - 2.0 < 0; pole at -1 (stable)
        y = first_order_admittance(self.freqs, g0=0.1, gain=-2.0, rate=1.0)
        result = edge_of_chaos(self.freqs, y, jacobian=[[-1.0]])
        self.assertTrue(result["locally_active"])
        self.assertTrue(result["passes"])
        # Band ends where Re Y crosses zero: omega^2 = -gain*rate/g0 - rate^2 = 19
        f_cross = np.sqrt(19.0) / (2 * np.pi)
        self.assertLess(abs(result["active_band_hz"].max() - f_cross), self.freqs[1] - self.freqs[0])

    def test_passive_device_fails(self):
        y = first_order_admittance(self.freqs, g0=0.1, gain=0.8, rate=1.2)
        result = edge_of_chaos(self.freqs, y, jacobian=[[-1.2]])
        self.assertFalse(result["locally_active"])
        self.assertFalse(result["passes"])

    def test_active_but_unstable_device_fails(self):
        y = first_order_admittance(self.freqs, g0=0.1, gain=-2.0, rate=1.0)
        result = edge_of_chaos(self.freqs, y, jacobian=[[0.5, 0.0], [0.0, -1.0]])
        self.assertTrue(result["locally_active"])
        self.assertFalse(result["asymptotically_stable"])
        self.assertFalse(result["passes"])

    def test_invalid_input(self):
        with self.assertRaises(ValueError):
            edge_of_chaos(self.freqs, np.ones(3), [[-1.0]])
        with self.assertRaises(ValueError):
            edge_of_chaos(self.freqs, np.ones(500), [[-1.0, 0.0]])


class TestCausalDegeneracy(unittest.TestCase):

    def test_rank_and_effective_rank(self):
        # M = 4 macroscopic variables, N^2 = 9 conductances, two singular values above delta
        u = np.linalg.qr(np.random.default_rng(0).normal(size=(4, 4)))[0]
        v = np.linalg.qr(np.random.default_rng(1).normal(size=(9, 9)))[0]
        sigma = np.zeros((4, 9))
        sigma[0, 0], sigma[1, 1], sigma[2, 2] = 2.0, 1.0, 1e-6
        result = causal_degeneracy(u @ sigma @ v.T, delta=1e-3)
        self.assertEqual(result["rank_delta"], 2)
        self.assertAlmostEqual(result["D_C"], 0.5)
        self.assertLessEqual(result["effective_rank"], 2.0 + 1e-3)
        self.assertGreater(result["D_C_eff"], 0.45)

        equal = causal_degeneracy(np.eye(3), delta=1e-3)
        self.assertAlmostEqual(equal["effective_rank"], 3.0)
        self.assertAlmostEqual(equal["D_C_eff"], 0.0)

    def test_degenerate_directions_are_orthonormal_null_space(self):
        jac = np.array([[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0]])
        basis = degenerate_directions(jac, delta=1e-9)
        self.assertEqual(basis.shape, (4, 2))
        np.testing.assert_allclose(jac @ basis, 0.0, atol=1e-12)
        np.testing.assert_allclose(basis.T @ basis, np.eye(2), atol=1e-12)

    def test_radius_of_a_known_map(self):
        # F(w) = (w0, w1, |w2|^2 + |w3|^2): J_F at w=0 has null directions w2, w3, and
        # F stays within epsilon of the attractor (0, 0, 0) along them for r <= sqrt(epsilon).
        F = lambda w: np.array([w[0], w[1], w[2] ** 2 + w[3] ** 2])
        jac = np.array([[1.0, 0, 0, 0], [0, 1.0, 0, 0], [0, 0, 0, 0]])
        result = degeneracy_radius(F, np.zeros(4), np.zeros(3), epsilon=0.04, jacobian_f=jac, delta=1e-9)
        self.assertAlmostEqual(result["rho_deg"], 0.2, delta=2e-3)
        self.assertEqual(result["n_degenerate_directions"], 2)

    def test_prediction_b15(self):
        self.assertTrue(degeneracy_prediction(0.2, 0.1)["passes"])
        self.assertFalse(degeneracy_prediction(0.05, 0.1)["passes"])
        with self.assertRaises(ValueError):
            degeneracy_prediction(0.2, 0.0)


class TestExponentStability(unittest.TestCase):

    def test_stable_exponents_pass(self):
        result = exponent_stability([16, 32, 64, 128], [1.9, 1.52, 1.50, 1.48], delta_exp=0.05)
        np.testing.assert_array_equal(np.sort(result["sizes_used"]), [32, 64, 128])
        self.assertTrue(result["passes"])

    def test_drifting_exponents_fail(self):
        self.assertFalse(exponent_stability([32, 64, 128], [1.2, 1.5, 1.9], delta_exp=0.1)["passes"])

    def test_infeasible_tolerance(self):
        result = exponent_stability([32, 64, 128], [1.5, 1.5, 1.5], delta_exp=0.4, lattice="2D")
        self.assertFalse(result["feasible"])
        self.assertFalse(result["passes"])
        self.assertTrue(exponent_stability([32, 64, 128], [1.5, 1.5, 1.5], delta_exp=0.4, lattice="3D")["passes"])

    def test_invalid_input(self):
        with self.assertRaises(ValueError):
            exponent_stability([32, 64], [1.5, 1.5], delta_exp=0.1)
        with self.assertRaises(ValueError):
            exponent_stability([32, 64, 128], [1.5, 1.5, 1.5], delta_exp=0.1, lattice="1D")


if __name__ == "__main__":
    unittest.main()
