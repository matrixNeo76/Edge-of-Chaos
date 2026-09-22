"""
paper0_cli.py
=============
Entry-point unico a sottocomandi per la piattaforma di metrologia P0_Distilled v0.1.

Non duplica la logica degli script esistenti: importa le loro funzioni e le richiama.
Ogni script (`valenza_metrologia.py`, `dashboard_valenza.py`, `demarcation_tests.py`,
`hardware_driver_v2.py`) resta eseguibile standalone esattamente come prima — questo
file è puramente additivo, pensato principalmente come punto di ingresso singolo per
il packaging PyInstaller (vedi docs_v0.2/05_PACKAGING_PYINSTALLER.md).

Uso:
    python paper0_cli.py metrologia
    python paper0_cli.py dashboard
    python paper0_cli.py demarcazione
    python paper0_cli.py hardware
    python paper0_cli.py test [--suite metrologia|hardware|tutti]
"""

import argparse
import sys
import unittest


def cmd_metrologia(_args):
    from valenza_metrologia import simulate_neuromorphic_substrate_sde, calculate_thermodynamic_valence
    import numpy as np

    print("=== ESECUZIONE METROLOGIA AVANZATA DIGITAL TWIN (P0_Distilled v0.1) ===")
    x_A1, s_obs, s_pred, dt = simulate_neuromorphic_substrate_sde(n_steps=10000)
    res = calculate_thermodynamic_valence(x_A1, s_obs, s_pred, dt)
    print(f"Punti temporali processati: {len(x_A1)}")
    print(f"Stato medio substrato A1 x(t): {np.mean(x_A1):.4f}")
    print(f"Dissipazione in eccesso sigma_ex: {res['sigma_ex']:.4f}")
    print(f"Dissipazione housekeeping sigma_hk: {res['sigma_hk']:.4f}")
    print(f"Divergenza Allostasica D_KL(P||P_target): {res['d_kl_allostasica']:.4f}")
    print(f"Guadagno Predittivo dell'Efference Copy G_pred: {res['g_pred']:.4f}")
    print(f"-> FUNZIONALE DI VALENZA INTEGRATO Psi(t): {res['psi_valenza']:.4f}")
    return 0


def cmd_dashboard(_args):
    from dashboard_valenza import generate_metrology_dashboard
    generate_metrology_dashboard()
    return 0


def cmd_demarcazione(_args):
    import numpy as np
    from demarcation_tests import (
        test_edge_of_chaos_admittance,
        calculate_spectral_causal_degeneracy,
        verify_finite_size_scaling,
    )

    freqs = np.linspace(0.1, 100.0, 500)
    eoc = test_edge_of_chaos_admittance(freqs)
    print("=== TEST DEMARCAZIONE 1: EDGE OF CHAOS ===")
    print(f"Edge of Chaos Verificato: {eoc['is_edge_of_chaos']}")
    print(f"Traccia Jacobiano: {eoc['trace_J']:.2f}, Determinante: {eoc['det_J']:.2f}")

    print("\n=== TEST DEMARCAZIONE 2: DEGENERAZIONE CAUSALE SPETTRALE ===")
    J_mock = np.array([[-1.0, 0.5, 0.0], [0.5, -1.0, 0.0], [0.0, 0.0, -1.0]])
    deg = calculate_spectral_causal_degeneracy(J_mock)
    print(f"Dimensione Nucleo: {deg['nullspace_dim']}, Rho Degenerazione: {deg['rho_deg']:.2f}")
    print(f"Soglia Degenerazione Superata: {deg['passes_degeneracy_threshold']}")

    print("\n=== TEST DEMARCAZIONE 3: FINITE-SIZE SCALING (FSS) ===")
    for row in verify_finite_size_scaling():
        print(f"L={row['L']}: delta_p={row['delta_p']:.4f}, xi={row['xi']:.2f}")
    return 0


def cmd_hardware(_args):
    from hardware_driver_v2 import NeuromorphicHardwareInterfaceV2
    import numpy as np

    hw = NeuromorphicHardwareInterfaceV2(mock=True)
    print(hw.initialize_session())
    frame = hw.get_realtime_frame(n_samples=1000)
    print(f"Frame acquisito: {len(frame['current_I'])} punti I(t) "
          f"[Mean I = {np.mean(frame['current_I'])*1e6:.2f} uA], "
          f"{len(frame['voltage_V'])} punti V(t).")
    return 0


def cmd_test(args):
    suite_map = {
        "metrologia": ["test_valenza_metrologia"],
        "hardware": ["test_hardware_session"],
        "tutti": ["test_valenza_metrologia", "test_hardware_session"],
    }
    modules = suite_map[args.suite]
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for mod_name in modules:
        suite.addTests(loader.loadTestsFromName(mod_name))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="paper0",
        description="Piattaforma di Metrologia per Substrati Neuromorfici (P0_Distilled v0.1)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("metrologia", help="Esegue il digital twin e calcola Psi(t)")
    sub.add_parser("dashboard", help="Genera la dashboard grafica a 4 quadranti")
    sub.add_parser("demarcazione", help="Esegue i 3 test di demarcazione operativa")
    sub.add_parser("hardware", help="Inizializza una sessione hardware mock e acquisisce un frame")

    p_test = sub.add_parser("test", help="Esegue le suite di test")
    p_test.add_argument(
        "--suite", choices=["metrologia", "hardware", "tutti"], default="tutti",
        help="Quale suite eseguire (default: tutti)",
    )

    args = parser.parse_args(argv)
    dispatch = {
        "metrologia": cmd_metrologia,
        "dashboard": cmd_dashboard,
        "demarcazione": cmd_demarcazione,
        "hardware": cmd_hardware,
        "test": cmd_test,
    }
    return dispatch[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
