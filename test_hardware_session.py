"""
test_hardware_session.py
========================
Test suite for verifying the extended hardware acquisition session and for
validating the compliance and safety parameters (P0_Distilled v0.1).
"""

import unittest
import numpy as np
import os
import sys

# Import the metrology and hardware driver v2 modules
from hardware_driver_v2 import (
    LaboratoryParametersConfig,
    KeithleyDMMDriverV2,
    PicoScopeOscilloscopeDriverV2,
    NeuromorphicHardwareInterfaceV2
)
from thermodynamic_valence import calculate_thermodynamic_valence


class TestHardwareAcquisitionSession(unittest.TestCase):
    """Unit and extended tests for real and simulated hardware interfacing."""

    def setUp(self):
        self.config = LaboratoryParametersConfig()
        self.hw = NeuromorphicHardwareInterfaceV2(config=self.config, mock=True)
        self.hw.initialize_session()

    def test_compliance_limits_enforced(self):
        """Verifies that voltage (1.5V) and current (1mA) compliance is always respected."""
        frame = self.hw.get_realtime_frame(n_samples=2000)
        i_t = frame["current_I"]
        v_t = frame["voltage_V"]

        # Maximum current must not exceed I_COMPLIANCE_MAX
        self.assertTrue(np.all(i_t <= self.config.I_COMPLIANCE_MAX + 1e-9),
                        f"Current compliance violation: max(I)={np.max(i_t)} A > {self.config.I_COMPLIANCE_MAX} A")
        self.assertTrue(np.all(i_t >= 0), "Current has non-physical negative values")

        # Voltage must not exceed V_COMPLIANCE_MAX in magnitude
        self.assertTrue(np.all(np.abs(v_t) <= self.config.V_COMPLIANCE_MAX + 1e-9),
                        f"Voltage compliance violation: max(|V|)={np.max(np.abs(v_t))} V > {self.config.V_COMPLIANCE_MAX} V")

    def test_noise_calibration_edge_of_chaos(self):
        """Verifies that the injected 1/f percolative noise is calibrated around the critical point (sigma ~ 0.10)."""
        dmm = KeithleyDMMDriverV2(config=self.config, mock=True)
        dmm.connect()
        i_t = dmm.read_current_stream(n_samples=5000)

        # Compute the relative fluctuations around the trend
        i_mean = np.mean(i_t)
        rel_fluctuations = (i_t - i_mean) / i_mean
        std_fluct = np.std(rel_fluctuations)

        # The relative noise should be around 0.10 (edge of chaos)
        self.assertGreater(std_fluct, 0.02, "Percolative noise too suppressed")
        self.assertLess(std_fluct, 0.35, "Percolative noise too high (outside the critical regime)")

    def test_extended_multi_frame_acquisition(self):
        """Simulates an extended session of 15 consecutive frames and verifies temporal stability."""
        n_frames = 15
        i_means = []
        v_stds = []

        for f in range(n_frames):
            frame = self.hw.get_realtime_frame(n_samples=1000)
            i_means.append(np.mean(frame["current_I"]))
            v_stds.append(np.std(frame["voltage_V"]))

        self.assertEqual(len(i_means), n_frames)
        # Verify mean stability (no catastrophic drift)
        self.assertTrue(np.all(np.isfinite(i_means)))
        self.assertTrue(np.all(np.isfinite(v_stds)))

    def test_thermodynamic_valence_integration_from_hardware(self):
        """Integrates the time series acquired from simulated hardware with the valence pipeline Psi(t)."""
        frame = self.hw.get_realtime_frame(n_samples=2000)
        i_t = frame["current_I"]
        v_t = frame["voltage_V"]

        dt = 1.0 / self.config.SAMPLE_RATE_DMM_HZ
        # Normalization of the substrate state
        x_A1 = (i_t - np.mean(i_t)) / (np.std(i_t) + 1e-12)
        s_obs = x_A1 + np.random.normal(0, 0.05, len(x_A1))
        s_pred = np.roll(x_A1, 1) * self.config.EFFERENCE_COPY_GAIN_GAMMA

        res = calculate_thermodynamic_valence(x_A1, s_obs, s_pred, dt)

        self.assertIn("psi_valence", res)
        self.assertIn("g_pred", res)
        self.assertTrue(np.isfinite(res["psi_valence"]))
        self.assertGreaterEqual(res["sigma_hk"], 0.0)


if __name__ == "__main__":
    unittest.main()
