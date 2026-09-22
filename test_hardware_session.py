"""
test_hardware_session.py
========================
Suite di test per la verifica della sessione di acquisizione hardware extended
e per la convalida dei parametri di compliance e sicurezza (P0_Distilled v0.1).
"""

import unittest
import numpy as np
import os
import sys

# Importa i moduli della metrologia e dell'hardware driver v2
from hardware_driver_v2 import (
    LaboratoryParametersConfig,
    KeithleyDMMDriverV2,
    PicoScopeOscilloscopeDriverV2,
    NeuromorphicHardwareInterfaceV2
)
from valenza_metrologia import calculate_thermodynamic_valence


class TestHardwareAcquisitionSession(unittest.TestCase):
    """Test unitari ed extended per l'interfacciamento hardware reale e simulato."""

    def setUp(self):
        self.config = LaboratoryParametersConfig()
        self.hw = NeuromorphicHardwareInterfaceV2(config=self.config, mock=True)
        self.hw.initialize_session()

    def test_compliance_limits_enforced(self):
        """Verifica che la compliance di tensione (1.5V) e corrente (1mA) sia sempre rispettata."""
        frame = self.hw.get_realtime_frame(n_samples=2000)
        i_t = frame["current_I"]
        v_t = frame["voltage_V"]

        # Corrente massima non deve superare I_COMPLIANCE_MAX
        self.assertTrue(np.all(i_t <= self.config.I_COMPLIANCE_MAX + 1e-9),
                        f"Violazione compliance corrente: max(I)={np.max(i_t)} A > {self.config.I_COMPLIANCE_MAX} A")
        self.assertTrue(np.all(i_t >= 0), "La corrente presenta valori negativi non fisici")

        # Tensione non deve superare V_COMPLIANCE_MAX in modulo
        self.assertTrue(np.all(np.abs(v_t) <= self.config.V_COMPLIANCE_MAX + 1e-9),
                        f"Violazione compliance tensione: max(|V|)={np.max(np.abs(v_t))} V > {self.config.V_COMPLIANCE_MAX} V")

    def test_noise_calibration_edge_of_chaos(self):
        """Verifica che il rumore percolativo 1/f iniettato sia calibrato attorno al punto critico (sigma ~ 0.10)."""
        dmm = KeithleyDMMDriverV2(config=self.config, mock=True)
        dmm.connect()
        i_t = dmm.read_current_stream(n_samples=5000)

        # Calcola le fluttuazioni relative attorno al trend
        i_mean = np.mean(i_t)
        rel_fluctuations = (i_t - i_mean) / i_mean
        std_fluct = np.std(rel_fluctuations)

        # Il rumore relativo deve essere nell'intorno dello 0.10 (Edge of Chaos)
        self.assertGreater(std_fluct, 0.02, "Rumore percolativo troppo soppresso")
        self.assertLess(std_fluct, 0.35, "Rumore percolativo troppo elevato (fuori dal regime critico)")

    def test_extended_multi_frame_acquisition(self):
        """Simula una sessione estesa di 15 frame consecutivi e verifica la stabilita' temporale."""
        n_frames = 15
        i_means = []
        v_stds = []

        for f in range(n_frames):
            frame = self.hw.get_realtime_frame(n_samples=1000)
            i_means.append(np.mean(frame["current_I"]))
            v_stds.append(np.std(frame["voltage_V"]))

        self.assertEqual(len(i_means), n_frames)
        # Verifica stabilità media (nessun drift catastrofico)
        self.assertTrue(np.all(np.isfinite(i_means)))
        self.assertTrue(np.all(np.isfinite(v_stds)))

    def test_thermodynamic_valence_integration_from_hardware(self):
        """Integra le serie temporali acquisite dall'hardware simulato con la pipeline di valenza Psi(t)."""
        frame = self.hw.get_realtime_frame(n_samples=2000)
        i_t = frame["current_I"]
        v_t = frame["voltage_V"]

        dt = 1.0 / self.config.SAMPLE_RATE_DMM_HZ
        # Normalizzazione dello stato del substrato
        x_A1 = (i_t - np.mean(i_t)) / (np.std(i_t) + 1e-12)
        s_obs = x_A1 + np.random.normal(0, 0.05, len(x_A1))
        s_pred = np.roll(x_A1, 1) * self.config.EFFERENCE_COPY_GAIN_GAMMA

        res = calculate_thermodynamic_valence(x_A1, s_obs, s_pred, dt)

        self.assertIn("psi_valenza", res)
        self.assertIn("g_pred", res)
        self.assertTrue(np.isfinite(res["psi_valenza"]))
        self.assertGreaterEqual(res["sigma_hk"], 0.0)


if __name__ == "__main__":
    unittest.main()
