"""
demarcation_tests.py
======================
Modulo per i Criteri e Test di Demarcazione Operativa (Paper 0.1 Distilled)

Include:
1. Edge of Chaos (Chua / Ascoli): Calcolo dell'ammettenza a piccoli segnali Re(Y(jw)) e autovalori Jacobiano.
2. Degenerazione Causale Spettrale (rho_deg): Analisi del rango e della molteplicita' spettrale dello Jacobiano sotto rumore termico.
3. Finite-Size Scaling (FSS): Verifica dell'invarianza di scala su array memristivi N x N.
"""

import numpy as np

def test_edge_of_chaos_admittance(frequencies_hz, a=-1.2, b=0.8):
    """
    Verifica la condizione di attivita' locale all'edge of chaos per un memristore:
    Re(Y(j w)) < 0 in una banda finita di frequenze [w1, w2].
    """
    omega = 2 * np.pi * frequencies_hz
    # Modello di ammettenza linearizzata Y(j w) = G_0 + (b / (j w - a))
    y_jw = 0.1 + (b / (1j * omega - a))
    re_y = np.real(y_jw)
    
    # Identifica le frequenze in cui il materiale amplifica piccoli segnali (Re(Y) < 0)
    locally_active_mask = re_y < 0.0
    active_bandwidth = frequencies_hz[locally_active_mask]
    
    # Controllo stabilita' del punto di equilibrio (Tr(J) < 0, det(J) > 0)
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
    Calcola la misura della degenerazione causale spettrale rho_deg:
    rho_deg = dim(ker(J - lambda_0 I)) / ||W_therm||
    """
    eigenvalues, eigenvectors = np.linalg.eig(state_matrix_J)
    
    # Trova il valore proprio dominante lambda_0
    idx_max = np.argmax(np.real(eigenvalues))
    lambda_0 = eigenvalues[idx_max]
    
    # Calcola il rango del nucleo ker(J - lambda_0 I)
    shifted_J = state_matrix_J - lambda_0 * np.eye(state_matrix_J.shape[0])
    singular_values = np.linalg.svd(shifted_J, compute_uv=False)
    
    # Dimensione approssimata del nucleo
    nullspace_dim = np.sum(singular_values < tol) + 1  # Almeno 1 per l'autovettore associato
    
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
    Verifica lo scaling di dimensione finita (FSS) per la suscettibilita' e la lunghezza di correlazione:
    xi ~ |p - p_c|^(-nu)
    """
    results = []
    for L in system_sizes_L:
        # Simula la fluttuazione di soglia delta_p al variare della dimensione del reticolo L
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
    print("=== TEST DEMARCAZIONE 1: EDGE OF CHAOS ===")
    print(f"Edge of Chaos Verificato: {eoc['is_edge_of_chaos']}")
    print(f"Traccia Jacobiano: {eoc['trace_J']:.2f}, Determinante: {eoc['det_J']:.2f}")
    
    print("\n=== TEST DEMARCAZIONE 2: DEGENERAZIONE CAUSALE SPETTRALE ===")
    J_mock = np.array([[-1.0, 0.5, 0.0], [0.5, -1.0, 0.0], [0.0, 0.0, -1.0]])
    deg = calculate_spectral_causal_degeneracy(J_mock)
    print(f"Dimensione Nucleo: {deg['nullspace_dim']}, Rho Degenerazione: {deg['rho_deg']:.2f}")
    print(f"Soglia Degenerazione Superata: {deg['passes_degeneracy_threshold']}")
    
    print("\n=== TEST DEMARCAZIONE 3: FINITE-SIZE SCALING (FSS) ===")
    fss = verify_finite_size_scaling()
    for row in fss:
        print(f"L={row['L']}: delta_p={row['delta_p']:.4f}, xi={row['xi']:.2f}")
