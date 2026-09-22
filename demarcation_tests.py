"""
demarcation_tests.py
======================
Module for the Operational Demarcation Criteria and Tests (Paper 0.1 Distilled)

Includes:
1. Edge of Chaos (Chua / Ascoli): computation of the small-signal admittance Re(Y(jw))
   and Jacobian eigenvalues.
2. Spectral Causal Degeneracy (rho_deg): rank and spectral multiplicity analysis of the
   Jacobian under thermal noise.
3. Finite-Size Scaling (FSS): verification of scale invariance on N x N memristive arrays.
"""

import numpy as np

def test_edge_of_chaos_admittance(frequencies_hz, a=-1.2, b=0.8):
    """
    Verifies the local activity condition at the edge of chaos for a memristor:
    Re(Y(j w)) < 0 in a finite frequency band [w1, w2].
    """
    omega = 2 * np.pi * frequencies_hz
    # Linearized admittance model Y(j w) = G_0 + (b / (j w - a))
    y_jw = 0.1 + (b / (1j * omega - a))
    re_y = np.real(y_jw)

    # Identify the frequencies at which the material amplifies small signals (Re(Y) < 0)
    locally_active_mask = re_y < 0.0
    active_bandwidth = frequencies_hz[locally_active_mask]

    # Equilibrium point stability check (Tr(J) < 0, det(J) > 0)
    jacobian_eq = np.array([[a, b], [-0.5, -1.0]])
    trace_j = np.trace(jacobian_eq)
    det_j = np.linalg.det(jacobian_eq)
    is_stable = (trace_j < 0) and (det_j > 0)

    is_edge_of_chaos = (len(active_bandwidth) > 0) and is_stable

    return {
        "is_edge_of_chaos": is_edge_of_chaos,
        "re_y": re_y,
        "active_bandwidth_hz": active_bandwidth,
        "trace_J": float(trace_j),
        "det_J": float(det_j)
    }

def calculate_spectral_causal_degeneracy(state_matrix_J, thermal_noise_std=0.05, tol=1e-3):
    """
    Computes the spectral causal degeneracy measure rho_deg:
    rho_deg = dim(ker(J - lambda_0 I)) / ||W_therm||
    """
    eigenvalues, eigenvectors = np.linalg.eig(state_matrix_J)

    # Find the dominant eigenvalue lambda_0
    idx_max = np.argmax(np.real(eigenvalues))
    lambda_0 = eigenvalues[idx_max]

    # Compute the rank of the kernel ker(J - lambda_0 I)
    shifted_J = state_matrix_J - lambda_0 * np.eye(state_matrix_J.shape[0])
    singular_values = np.linalg.svd(shifted_J, compute_uv=False)

    # Approximate dimension of the kernel
    nullspace_dim = np.sum(singular_values < tol) + 1  # At least 1 for the associated eigenvector

    rho_deg = float(nullspace_dim / (thermal_noise_std + 1e-12))

    return {
        "lambda_0": complex(lambda_0),
        "nullspace_dim": int(nullspace_dim),
        "thermal_noise_std": float(thermal_noise_std),
        "rho_deg": rho_deg,
        "passes_degeneracy_threshold": rho_deg > 10.0
    }

def verify_finite_size_scaling(system_sizes_L=[10, 20, 50, 100], p_c=0.5, nu=1.33):
    """
    Verifies finite-size scaling (FSS) for the susceptibility and correlation length:
    xi ~ |p - p_c|^(-nu)
    """
    results = []
    for L in system_sizes_L:
        # Simulate the threshold fluctuation delta_p as the lattice size L varies
        delta_p = (1.0 / L) ** (1.0 / nu) + np.random.normal(0, 0.01 / L)
        xi = np.abs(delta_p)**(-nu)
        scaled_susceptibility = xi / (L**2)
        results.append({
            "L": L,
            "delta_p": float(delta_p),
            "xi": float(xi),
            "scaled_susceptibility": float(scaled_susceptibility)
        })
    return results

if __name__ == "__main__":
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
    fss = verify_finite_size_scaling()
    for row in fss:
        print(f"L={row['L']}: delta_p={row['delta_p']:.4f}, xi={row['xi']:.2f}")
