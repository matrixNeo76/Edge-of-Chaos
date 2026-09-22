"""
test_valenza_metrologia.py
===========================
Suite di Test Unitari ed E2E per lo Script di Metrologia (P0_Distilled v0.1)

Autore: Programma di Ricerca Lakatosiano
Descrizione:
  Verifica la correttezza matematica, la stabilità numerica e i vincoli di metrologia
  dello script `valenza_metrologia.py`.
"""

import unittest
import numpy as np
import sys
import os

# Importa le funzioni dallo script valenza_metrologia
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from valenza_metrologia import (
    simulate_neuromorphic_substrate_sde,
    estimate_kl_divergence_knn,
    calculate_thermodynamic_valence
)

class TestValenzaMetrologia(unittest.TestCase):

    def test_sde_simulation_integrity(self):
        """Verifica che la simulazione SDE produca array di dimensione corretta, senza NaN o Inf."""
        n_steps = 1000
        x_A1, s_obs, s_pred, dt = simulate_neuromorphic_substrate_sde(n_steps=n_steps, seed=123)
        
        self.assertEqual(len(x_A1), n_steps)
        self.assertEqual(len(s_obs), n_steps)
        self.assertEqual(len(s_pred), n_steps)
        self.assertGreater(dt, 0.0)
        
        # Assenza di valori non numerici
        self.assertFalse(np.isnan(x_A1).any(), "x_A1 contiene valori NaN")
        self.assertFalse(np.isinf(x_A1).any(), "x_A1 contiene valori Inf")
        self.assertFalse(np.isnan(s_obs).any(), "s_obs contiene valori NaN")
        self.assertFalse(np.isnan(s_pred).any(), "s_pred contiene valori NaN")

    def test_kl_divergence_knn_properties(self):
        """Verifica le proprietà fondamentali della stima k-NN della divergenza di Kullback-Leibler."""
        np.random.seed(42)
        
        # 1. D_KL tra due campioni della stessa distribuzione N(0, 1) deve essere prossima a 0
        p_samples = np.random.normal(0, 1, size=1000)
        q_identical = np.random.normal(0, 1, size=1000)
        d_kl_zero = estimate_kl_divergence_knn(p_samples, q_identical, k=5)
        
        self.assertGreaterEqual(d_kl_zero, 0.0)
        self.assertLess(d_kl_zero, 0.2, f"D_KL tra distribuzioni identiche deve essere vicina a 0, ottenuto {d_kl_zero}")
        
        # 2. D_KL tra due distribuzioni diverse N(0, 1) e N(2, 1) deve essere nettamente > 0
        q_shifted = np.random.normal(2, 1, size=1000)
        d_kl_positive = estimate_kl_divergence_knn(p_samples, q_shifted, k=5)
        
        self.assertGreater(d_kl_positive, 1.0, f"D_KL tra distribuzioni traslate deve essere significativamente positiva, ottenuto {d_kl_positive}")

    def test_thermodynamic_valence_keys_and_bounds(self):
        """Verifica che il calcolo della valenza restituisca le chiavi attese e valori finiti."""
        x_A1, s_obs, s_pred, dt = simulate_neuromorphic_substrate_sde(n_steps=2000, seed=42)
        res = calculate_thermodynamic_valence(x_A1, s_obs, s_pred, dt)
        
        expected_keys = {"sigma_ex", "sigma_hk", "d_kl_allostasica", "g_pred", "psi_valenza"}
        self.assertEqual(set(res.keys()), expected_keys)
        
        for key, val in res.items():
            self.assertTrue(np.isfinite(val), f"La metrica {key} non è un valore finito: {val}")
        
        self.assertGreaterEqual(res["sigma_hk"], 0.0, "La dissipazione di housekeeping deve essere non-negativa")
        self.assertGreaterEqual(res["sigma_ex"], 0.0, "La dissipazione in eccesso deve essere non-negativa")
        self.assertGreaterEqual(res["d_kl_allostasica"], 0.0, "D_KL allostasica deve essere non-negativa")

    def test_ablation_efference_copy_degradation(self):
        """
        Verifica la sensibilità del sistema: una copia efferente completamente casuale (rumore bianco)
        deve degradare o annullare il guadagno predittivo G_pred rispetto a una copia informata.
        """
        np.random.seed(99)
        x_A1, s_obs, s_pred, dt = simulate_neuromorphic_substrate_sde(n_steps=3000, seed=99)
        
        # Valenza con copia efferente normale
        res_normal = calculate_thermodynamic_valence(x_A1, s_obs, s_pred, dt)
        
        # Valenza con copia efferente ablasta (rumore casuale scollegato)
        s_pred_ablated = np.random.normal(5.0, 2.0, size=len(s_pred))
        res_ablated = calculate_thermodynamic_valence(x_A1, s_obs, s_pred_ablated, dt)
        
        # Il guadagno predittivo con la copia casuale deve essere inferiore
        self.assertLess(
            res_ablated["g_pred"],
            res_normal["g_pred"] + 1e-3,
            "L'ablazione della copia efferente dovrebbe ridurre il guadagno predittivo G_pred"
        )

if __name__ == "__main__":
    unittest.main()
