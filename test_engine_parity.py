"""
test_engine_parity.py
=====================
The Python and Rust engines implement the same formulas but draw random numbers from
different generators, so with the same seed they simulate different series and niches.
Given the same inputs (series and niche samples), they must return the same numbers.

Skipped when the native module is not installed (build it with
`maturin build --release` and install the wheel); the CI builds and runs it.
"""

import unittest
import numpy as np

from thermodynamic_valence import simulate_neuromorphic_substrate_sde, calculate_thermodynamic_valence

try:
    import thermodynamic_valence_rust
except ImportError:
    thermodynamic_valence_rust = None

if thermodynamic_valence_rust is None:
    SKIP_REASON = "native module thermodynamic_valence_rust not installed"
elif not hasattr(thermodynamic_valence_rust, "calculate_valence_with_niche_rust"):
    SKIP_REASON = ("the installed thermodynamic_valence_rust predates v0.4.0; rebuild it with "
                   "`maturin build --release` and reinstall the wheel")
else:
    SKIP_REASON = None


@unittest.skipIf(SKIP_REASON is not None, SKIP_REASON or "")
class TestEngineParity(unittest.TestCase):

    def _compare(self, x, s_obs, s_pred, dt, niche):
        py = calculate_thermodynamic_valence(x, s_obs, s_pred, dt, niche_samples=niche)
        rs = thermodynamic_valence_rust.calculate_valence_with_niche_rust(
            list(x), list(s_obs), list(s_pred), dt, 1.0, 0.5, 0.8, list(niche))
        for key in ("sigma_ex", "sigma_hk", "d_kl_allostatic", "g_pred", "psi_valence"):
            self.assertAlmostEqual(py[key], getattr(rs, key), places=9, msg=key)

    def test_same_inputs_give_same_numbers(self):
        for seed in (1, 42):
            x, s_obs, s_pred, dt = simulate_neuromorphic_substrate_sde(n_steps=1500, seed=seed)
            niche = np.random.default_rng(seed).normal(0.0, 0.2, size=len(x))
            self._compare(x, s_obs, s_pred, dt, niche)

    def test_same_numbers_under_ablation(self):
        x, s_obs, s_pred, dt = simulate_neuromorphic_substrate_sde(n_steps=1500, seed=7)
        ablated = np.random.default_rng(2026).normal(0.0, 1.0, size=len(s_pred))
        niche = np.random.default_rng(8).normal(0.0, 0.2, size=len(x))
        self._compare(x, s_obs, ablated, dt, niche)

    def test_invalid_input_raises_value_error(self):
        with self.assertRaises(ValueError):
            thermodynamic_valence_rust.calculate_valence_with_niche_rust(
                [0.0] * 20, [0.0] * 19, [0.0] * 20, 0.001, 1.0, 0.5, 0.8, [0.0] * 20)


if __name__ == "__main__":
    unittest.main()
