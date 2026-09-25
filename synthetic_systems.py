"""
synthetic_systems.py
====================
Synthetic systems with a known answer, used by the tests, the command-line demonstrations
and the notebook to show that each criterion separates the cases it should. They are
illustrations, not models of any real substrate.
"""

import numpy as np


def ar1(n, phi=0.8, seed=0):
    """Linear Gaussian Markov process of order 1: fails the non-Markovian memory condition."""
    rng = np.random.default_rng(seed)
    x = np.zeros(n)
    for t in range(1, n):
        x[t] = phi * x[t - 1] + rng.normal()
    return x


def nonlinear_lag5(n, seed=0):
    """
    Nonlinear process whose next state depends on x[t] and, through a cosine, on x[t-4]:
    Markov order 5, with memory that IAAFT surrogates do not reproduce.
    """
    rng = np.random.default_rng(seed)
    x = np.zeros(n)
    for t in range(5, n):
        x[t] = 0.4 * x[t - 1] + 0.8 * np.cos(2 * x[t - 5]) + 0.3 * rng.normal()
    return x


def linear_2d(n, seed=0):
    """Linear two-dimensional system: the same Jacobian everywhere in phase space."""
    rng = np.random.default_rng(seed)
    a = np.array([[0.8, 0.1], [-0.1, 0.8]])
    x = np.zeros((n, 2))
    for t in range(1, n):
        x[t] = a @ x[t - 1] + 0.1 * rng.normal(size=2)
    return x


def double_well(n, seed=0):
    """Noisy double-well dynamics x' = x - x^3: the local Jacobian changes sign across wells."""
    rng = np.random.default_rng(seed)
    x = np.zeros(n)
    for t in range(1, n):
        x[t] = x[t - 1] + 0.05 * (x[t - 1] - x[t - 1] ** 3) + 0.3 * rng.normal()
    return x


def response_matrices(size=8, noise=0.05, seed=0):
    """
    Perturbational response matrices with noise: a linear model R_lin with three modes, a
    substrate response R with two further modes, and a noise-only recording of the same
    shape (for the noise floor). Returns (R, R_lin, noise_recording).
    """
    rng = np.random.default_rng(seed)
    basis = np.linalg.qr(rng.normal(size=(size, size)))[0]
    r_lin = basis[:, :3] @ np.diag([3.0, 2.0, 1.0]) @ basis[:, :3].T
    r = r_lin + basis[:, 3:5] @ np.diag([0.8, 0.5]) @ basis[:, 3:5].T

    def noisy(m):
        return m + noise * rng.normal(size=m.shape)

    return noisy(r), noisy(r_lin), noise * rng.normal(size=(size, size))
