"""
paper0_cli.py
=============
Single subcommand entry point for the P0_Distilled v0.1 metrology platform.

Does not duplicate the logic of the existing scripts: it imports their functions
and calls them. Each script (`thermodynamic_valence.py`, `valence_dashboard.py`,
`demarcation.py`, `necessary_conditions.py`, `hardware_driver_v2.py`) remains usable standalone
exactly as before — this file is purely additive, designed mainly as a single
entry point for PyInstaller packaging.

Usage:
    python paper0_cli.py metrology
    python paper0_cli.py dashboard
    python paper0_cli.py demarcation [--k-max 3 --surrogates 19 --percentile 95]
    python paper0_cli.py conditions
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
    print(f"Excess-dissipation proxy sigma_ex: {res['sigma_ex']:.4f}")
    print(f"Housekeeping-dissipation proxy sigma_hk (dt-dependent): {res['sigma_hk']:.4f}")
    print(f"Allostatic divergence D_KL(P||P_target): {res['d_kl_allostatic']:.4f}")
    print(f"Predictive gain of the efference copy G_pred: {res['g_pred']:.4f}")
    print(f"-> INTEGRATED VALENCE FUNCTIONAL Psi(t): {res['psi_valence']:.4f}")
    return 0


def cmd_dashboard(_args):
    from valence_dashboard import generate_metrology_dashboard
    generate_metrology_dashboard()
    return 0


def _verdict(passes):
    return "PASS" if passes else "fail"


def cmd_demarcation(args):
    """
    The three operational demarcation conditions (P0 section 3, P1 section 2.1), each run
    on a synthetic system that should pass and one that should fail. The surrogate test
    uses reduced settings for speed; the protocol uses 100 surrogates and the 99th
    percentile (--surrogates 100 --percentile 99).
    """
    from demarcation import (causal_non_separability, noise_floor_from_recordings,
                             non_markovian_memory, state_dependent_dynamics)
    from synthetic_systems import ar1, nonlinear_lag5, linear_2d, double_well, response_matrices

    print("=== OPERATIONAL DEMARCATION (synthetic illustration, not a substrate) ===")

    r, r_lin, noise = response_matrices()
    delta = noise_floor_from_recordings(noise)
    print("\n[1] Causal non-separability: rank_delta(R) > rank_delta(R_lin)")
    for name, matrix in (("response with extra modes", r), ("linear superposition only", r_lin)):
        res = causal_non_separability(matrix, r_lin, delta)
        print(f"    {name:28s} rank {res['rank_R']} vs {res['rank_R_lin']} -> {_verdict(res['passes'])}")

    print(f"\n[2] Non-Markovian memory: orders 1..{args.k_max}, {args.surrogates} IAAFT surrogates, "
          f"{args.percentile:g}th percentile")
    for name, series in (("nonlinear, lag-5 memory", nonlinear_lag5(1500)), ("AR(1), Markov", ar1(1500))):
        res = non_markovian_memory(series, k_max=args.k_max, n_surrogates=args.surrogates,
                                   percentile=args.percentile)
        detail = ", ".join(f"k={row['order']}: {row['residual_memory']:.3f}/{row['surrogate_threshold']:.3f}"
                           for row in res["per_order"])
        print(f"    {name:28s} {detail} -> {_verdict(res['passes'])}")

    print("\n[3] State-dependent dynamics: Jacobian difference > 0.25 and > 95th percentile of linear surrogates")
    for name, states in (("double well", double_well(20000)), ("linear system", linear_2d(20000))):
        res = state_dependent_dynamics(states)
        print(f"    {name:28s} difference {res['statistic']:.3f}, null {res['null_threshold']:.3f} "
              f"-> {_verdict(res['passes'])}")
    return 0


def cmd_conditions(_args):
    """Criteria for three of the necessary conditions (P1 section 3, Appendices B and D)."""
    import numpy as np
    from necessary_conditions import (edge_of_chaos, first_order_admittance, causal_degeneracy,
                                      degeneracy_radius, degeneracy_prediction, exponent_stability)

    print("=== NECESSARY CONDITIONS (synthetic illustration, not a substrate) ===")

    freqs = np.linspace(0.1, 100.0, 500)
    print("\n[1] Edge of chaos: Re Y(jw) < 0 in the band and a stable operating point")
    for name, gain in (("locally active device", -2.0), ("passive device", 0.8)):
        res = edge_of_chaos(freqs, first_order_admittance(freqs, g0=0.1, gain=gain, rate=1.0), [[-1.0]])
        band = f"{res['active_band_hz'].min():.2f}-{res['active_band_hz'].max():.2f} Hz" if res["locally_active"] else "none"
        print(f"    {name:24s} active band {band:>16s} -> {_verdict(res['passes'])}")

    print("\n[2] Causal degeneracy (Appendix B) for F(w) = (w0, w1, w2^2 + w3^2) at w = 0")
    jacobian_f = np.array([[1.0, 0, 0, 0], [0, 1.0, 0, 0], [0, 0, 0, 0]])
    deg = causal_degeneracy(jacobian_f, delta=1e-9)
    radius = degeneracy_radius(lambda w: np.array([w[0], w[1], w[2] ** 2 + w[3] ** 2]),
                               np.zeros(4), np.zeros(3), epsilon=0.04, jacobian_f=jacobian_f, delta=1e-9)
    print(f"    D_C = {deg['D_C']:.3f}, D_C_eff = {deg['D_C_eff']:.3f}, rho_deg <= {radius['rho_deg']:.3f}")
    for norm in (0.1, 0.5):
        pred = degeneracy_prediction(radius["rho_deg"], norm)
        print(f"    (B.15) with ||dW_therm|| = {norm}: ratio {pred['ratio']:.2f} -> {_verdict(pred['passes'])}")

    print("\n[3] Exponent stability at the three largest sizes (Appendix D, 2D, Delta_exp = 10%)")
    for name, exponents in (("stable exponents", [1.90, 1.52, 1.50, 1.48]), ("drifting exponents", [1.0, 1.2, 1.5, 1.9])):
        res = exponent_stability([16, 32, 64, 128], exponents, delta_exp=0.10)
        print(f"    {name:24s} spread {res['relative_spread']:.3f} -> {_verdict(res['passes'])}")
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
        "demarcation": ["test_demarcation"],
        "conditions": ["test_necessary_conditions"],
        "all": ["test_thermodynamic_valence", "test_hardware_session",
                "test_demarcation", "test_necessary_conditions"],
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
    p_dem = sub.add_parser("demarcation", help="Runs the 3 operational demarcation conditions on synthetic systems")
    p_dem.add_argument("--k-max", type=int, default=3, help="Highest Markov order tested (default: 3)")
    p_dem.add_argument("--surrogates", type=int, default=19, help="Number of IAAFT surrogates (protocol: 100)")
    p_dem.add_argument("--percentile", type=float, default=95.0, help="Surrogate percentile (protocol: 99)")
    sub.add_parser("conditions", help="Runs the necessary-condition criteria on synthetic systems")
    sub.add_parser("hardware", help="Initializes a mock hardware session and acquires a frame")

    p_test = sub.add_parser("test", help="Runs the test suites")
    p_test.add_argument(
        "--suite", choices=["metrology", "hardware", "demarcation", "conditions", "all"], default="all",
        help="Which suite to run (default: all)",
    )

    args = parser.parse_args(argv)
    dispatch = {
        "metrology": cmd_metrology,
        "dashboard": cmd_dashboard,
        "demarcation": cmd_demarcation,
        "conditions": cmd_conditions,
        "hardware": cmd_hardware,
        "test": cmd_test,
    }
    return dispatch[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
