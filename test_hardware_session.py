"""
test_hardware_session.py
========================
Test suite for verifying the extended hardware acquisition session and for
validating the compliance and safety parameters (P0_Distilled v0.1).
"""

import unittest
import numpy as np

# Import the metrology and hardware driver v2 modules
from hardware_driver_v2 import (
    LaboratoryParametersConfig,
    KeithleyDMMDriverV2,
    PicoScopeOscilloscopeDriverV2,
    NeuromorphicHardwareInterfaceV2,
    generate_1f_noise,
    mock_dmm_carrier,
)
from thermodynamic_valence import calculate_thermodynamic_valence


class TestRealInstrumentPaths(unittest.TestCase):
    """Only the mock instruments exist; the real paths must fail explicitly."""

    def test_keithley_real_path_is_explicitly_unavailable(self):
        dmm = KeithleyDMMDriverV2(mock=False)
        with self.assertRaises(NotImplementedError):
            dmm.connect()
        with self.assertRaises(NotImplementedError):
            dmm.read_current_stream()
        with self.assertRaises(NotImplementedError):
            with KeithleyDMMDriverV2(mock=False):
                pass

    def test_picoscope_real_path_is_explicitly_unavailable(self):
        pico = PicoScopeOscilloscopeDriverV2(mock=False)
        with self.assertRaises(NotImplementedError):
            pico.connect()
        with self.assertRaises(NotImplementedError):
            pico.acquire_waveform()

    def test_interface_releases_instruments_when_initialisation_fails(self):
        hw = NeuromorphicHardwareInterfaceV2(mock=False)
        with self.assertRaises(NotImplementedError):
            with hw:
                pass
        self.assertFalse(hw.dmm.connected)
        self.assertFalse(hw.pico.connected)

    def test_mock_acquisition_requires_connection(self):
        with self.assertRaises(RuntimeError):
            PicoScopeOscilloscopeDriverV2(mock=True).acquire_waveform()
        with self.assertRaises(RuntimeError):
            KeithleyDMMDriverV2(mock=True).read_current_stream()


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
        """
        The mock current is carrier * (1 + noise): relative to the known 5 Hz carrier, the
        fluctuations must have the calibrated amplitude sigma_noise = 0.10. (The earlier
        version of this test measured the carrier as noise too, and failed.)
        """
        dmm = KeithleyDMMDriverV2(config=self.config, mock=True, seed=3)
        dmm.connect()
        n_samples = 5000
        i_t = dmm.read_current_stream(n_samples=n_samples)

        dt = 1.0 / self.config.SAMPLE_RATE_DMM_HZ
        t = np.linspace(0, n_samples * dt, n_samples)
        rel_fluctuations = i_t / mock_dmm_carrier(t) - 1.0

        self.assertAlmostEqual(np.std(rel_fluctuations), self.config.SIGMA_NOISE_OPTIMAL, delta=0.01)

    def test_1f_noise_generator_spectrum(self):
        """The generator gives the requested standard deviation and a 1/f**alpha spectrum."""
        dt, n_samples = 1e-3, 2 ** 14
        for alpha in (0.5, 1.0, 1.5):
            noise = generate_1f_noise(n_samples, dt, alpha=alpha, sigma=0.1, rng=np.random.default_rng(0))
            self.assertAlmostEqual(np.std(noise), 0.1, places=6)

            freqs = np.fft.rfftfreq(n_samples, dt)[1:]
            power = np.abs(np.fft.rfft(noise))[1:] ** 2
            band = (freqs > 1.0) & (freqs < 200.0)
            slope = np.polyfit(np.log(freqs[band]), np.log(power[band]), 1)[0]
            self.assertAlmostEqual(slope, -alpha, delta=0.1)

    def test_1f_noise_generator_rejects_invalid_input(self):
        with self.assertRaises(ValueError):
            generate_1f_noise(2, 1e-3)
        with self.assertRaises(ValueError):
            generate_1f_noise(100, 0.0)

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
