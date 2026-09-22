"""
paper0_cli.py
=============
Single subcommand entry point for the P0_Distilled v0.1 metrology platform.

Does not duplicate the logic of the existing scripts: it imports their functions
and calls them. Each script (`thermodynamic_valence.py`, `valence_dashboard.py`,
`demarcation_tests.py`, `hardware_driver_v2.py`) remains runnable standalone
exactly as before — this file is purely additive, designed mainly as a single
entry point for PyInstaller packaging.

Usage:
    python paper0_cli.py metrology
    python paper0_cli.py dashboard
    python paper0_cli.py demarcation
    python paper0_cli.py hardware
    python paper0_cli.py test [--suite metrology|hardware|all]
"""

import argparse
import sys
import unittest


def cmd_metrology(_args):
    from thermodynamic_valence import simulate_neuromorphic_substrate_sde, calculate_thermodynamic_valence
    import numpy as np

    print("=== RUNNING ADVANCED DIGITAL TWIN METROLOGY (P0_Distilled v0.1) ===")
    x_A1, s_obs, s_pred, dt = simulate_neuromorphic_substrate_sde(n_steps=10000)
    res = calculate_thermodynamic_valence(x_A1, s_obs, s_pred, dt)
    print(f"Time points processed: {len(x_A1)}")
    print(f"Mean state of substrate A1 x(t): {np.mean(x_A1):.4f}")
    print(f"Excess dissipation sigma_ex: {res['sigma_ex']:.4f}")
    print(f"Housekeeping dissipation sigma_hk: {res['sigma_hk']:.4f}")
    print(f"Allostatic divergence D_KL(P||P_target): {res['d_kl_allostatic']:.4f}")
    print(f"Predictive gain of the efference copy G_pred: {res['g_pred']:.4f}")
    print(f"-> INTEGRATED VALENCE FUNCTIONAL Psi(t): {res['psi_valence']:.4f}")
    return 0


def cmd_dashboard(_args):
    from valence_dashboard import generate_metrology_dashboard
    generate_metrology_dashboard()
    return 0


def cmd_demarcation(_args):
    import numpy as np
    from demarcation_tests import (
        test_edge_of_chaos_admittance,
        calculate_spectral_causal_degeneracy,
        verify_finite_size_scaling,
    )

    freqs = np.linspace(0.1, 100.0, 500)
    eoc = test_edge_of_chaos_admittance(freqs)
    print("=== DEMARCATION TEST 1: EDGE OF CHAOS ===")
    print(f"Edge of Chaos Verified: {eoc['is_edge_of_chaos']}")
    print(f"Jacobian Trace: {eoc['trace_J']:.2f}, Determinant: {eoc['det_J']:.2f}")

    print("\n=== DEMARCATION TEST 2: SPECTRAL CAUSAL DEGENERACY ===")
    J_mock = np.array([[-1.0, 0.5, 0.0], [0.5, -1.0, 0.0], [0.0, 0.0, -1.0]])
    deg = calculate_spectral_causal_degeneracy(J_mock)
    print(f"Kernel Dimension: {deg['nullspace_dim']}, Degeneracy Rho: {deg['rho_deg']:.2f}")
    print(f"Degeneracy Threshold Exceeded: {deg['passes_degeneracy_threshold']}")

    print("\n=== DEMARCATION TEST 3: FINITE-SIZE SCALING (FSS) ===")
    for row in verify_finite_size_scaling():
        print(f"L={row['L']}: delta_p={row['delta_p']:.4f}, xi={row['xi']:.2f}")
    return 0


def cmd_hardware(_args):
    from hardware_driver_v2 import NeuromorphicHardwareInterfaceV2
    import numpy as np

    hw = NeuromorphicHardwareInterfaceV2(mock=True)
    print(hw.initialize_session())
    frame = hw.get_realtime_frame(n_samples=1000)
    print(f"Frame acquired: {len(frame['current_I'])} I(t) points "
          f"[Mean I = {np.mean(frame['current_I'])*1e6:.2f} uA], "
          f"{len(frame['voltage_V'])} V(t) points.")
    return 0


def cmd_test(args):
    suite_map = {
        "metrology": ["test_thermodynamic_valence"],
        "hardware": ["test_hardware_session"],
        "all": ["test_thermodynamic_valence", "test_hardware_session"],
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
        description="Metrology Platform for Neuromorphic Substrates (P0_Distilled v0.1)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("metrology", help="Runs the digital twin and computes Psi(t)")
    sub.add_parser("dashboard", help="Generates the 4-quadrant graphical dashboard")
    sub.add_parser("demarcation", help="Runs the 3 operational demarcation tests")
    sub.add_parser("hardware", help="Initializes a mock hardware session and acquires a frame")

    p_test = sub.add_parser("test", help="Runs the test suites")
    p_test.add_argument(
        "--suite", choices=["metrology", "hardware", "all"], default="all",
        help="Which suite to run (default: all)",
    )

    args = parser.parse_args(argv)
    dispatch = {
        "metrology": cmd_metrology,
        "dashboard": cmd_dashboard,
        "demarcation": cmd_demarcation,
        "hardware": cmd_hardware,
        "test": cmd_test,
    }
    return dispatch[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
