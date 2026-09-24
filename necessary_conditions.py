"""
necessary_conditions.py
=======================
Operational criteria for three of the five necessary physical conditions of the
programme (P1_Main.tex, section 3; Appendices B and D). The other two (homeostatic
reorganisation, autopoietic barrier) are tested experimentally (Test 3, Appendix C)
and have no counterpart here.

1. Local activity at the edge of chaos (Chua): the small-signal admittance has a band
   with Re Y(j omega) < 0 while the operating point is asymptotically stable.
2. Robust causal degeneracy (Appendix B): D_C = 1 - rank_delta(J_F) / M, its
   effective-rank version, and the robust degeneracy radius rho_deg, tested against
   the falsifiable prediction rho_deg / ||Delta W_therm|| > 1.
3. Critical scale-invariance (Appendix D): the critical exponents estimated at the three
   largest sizes are stable within a tolerance Delta_exp, and the protocol is feasible
   only if Delta_exp <= 30% (2D) or 50% (3D).

All functions take measured or estimated quantities as input. They replace the
functions of demarcation_tests.py (up to v0.2.1), which computed different quantities.
"""

import numpy as np


def _finite(values, name):
    arr = np.asarray(values)
    if arr.size == 0:
        raise ValueError(f"{name} is empty")
    if not np.all(np.isfinite(arr)):
        raise ValueError(f"{name} contains NaN or infinite values")
    return arr


# ---------------------------------------------------------------------------
# 1. Local activity at the edge of chaos
# ---------------------------------------------------------------------------

def edge_of_chaos(frequencies_hz, admittance, jacobian):
    """
    Edge of chaos in Chua's sense: locally active (Re Y(j omega) < 0 somewhere in the
    measured band) and asymptotically stable (all eigenvalues of the Jacobian at the
    operating point have negative real part).

    frequencies_hz -- frequencies at which the admittance was measured
    admittance     -- complex small-signal admittance Y(j omega) at those frequencies
    jacobian       -- Jacobian of the circuit dynamics at the operating point
    """
    freqs = _finite(frequencies_hz, "frequencies_hz").astype(float)
    y = _finite(admittance, "admittance").astype(complex)
    if freqs.shape != y.shape:
        raise ValueError(f"frequencies and admittance differ in shape: {freqs.shape} vs {y.shape}")
    jac = np.atleast_2d(_finite(jacobian, "jacobian").astype(float))
    if jac.shape[0] != jac.shape[1]:
        raise ValueError(f"jacobian must be square, got shape {jac.shape}")

    active = np.real(y) < 0.0
    eigenvalues = np.linalg.eigvals(jac)
    stable = bool(np.all(np.real(eigenvalues) < 0.0))
    return {
        "locally_active": bool(active.any()),
        "active_band_hz": freqs[active],
        "asymptotically_stable": stable,
        "eigenvalues": eigenvalues,
        "passes": bool(active.any()) and stable,
    }


def first_order_admittance(frequencies_hz, g0, gain, rate):
    """
    Small-signal admittance of a first-order memristive device,
        Y(s) = g0 + gain / (s + rate),   s = j * 2 * pi * f,
    with pole at -rate. Re Y(j omega) = g0 + gain * rate / (omega**2 + rate**2): the device
    is locally active at low frequencies when gain < -g0 * rate, and its internal state is
    stable when rate > 0. Used by the demonstration; measured admittances replace it.
    """
    omega = 2 * np.pi * np.asarray(frequencies_hz, dtype=float)
    return g0 + gain / (1j * omega + rate)


# ---------------------------------------------------------------------------
# 2. Robust causal degeneracy (Appendix B)
# ---------------------------------------------------------------------------

def causal_degeneracy(jacobian_f, delta):
    """
    Degeneracy of the map F from conductances to macroscopic configurations, from the
    singular values of its Jacobian J_F (M x N^2):

        D_C     = 1 - rank_delta(J_F) / M
        rank_eff = exp(-sum p_i ln p_i),  p_i = sigma_i / sum_j sigma_j
        D_C_eff = 1 - rank_eff / M
    """
    jac = _finite(jacobian_f, "jacobian_f").astype(float)
    if jac.ndim != 2:
        raise ValueError(f"jacobian_f must be 2-dimensional, got shape {jac.shape}")
    if delta < 0:
        raise ValueError(f"delta must be non-negative, got {delta}")
    m = jac.shape[0]
    sigma = np.linalg.svd(jac, compute_uv=False)
    rank_delta = int(np.sum(sigma > delta))
    total = sigma.sum()
    if total > 0:
        p = sigma[sigma > 0] / total
        rank_eff = float(np.exp(-np.sum(p * np.log(p))))
    else:
        rank_eff = 0.0
    return {"M": m, "singular_values": sigma, "rank_delta": rank_delta, "D_C": 1.0 - rank_delta / m,
            "effective_rank": rank_eff, "D_C_eff": 1.0 - rank_eff / m}


def degenerate_directions(jacobian_f, delta):
    """
    Orthonormal basis (columns) of K_delta: the right singular vectors of J_F whose
    singular value is <= delta, including the null directions beyond rank M.
    """
    jac = _finite(jacobian_f, "jacobian_f").astype(float)
    _, sigma, vt = np.linalg.svd(jac, full_matrices=True)
    padded = np.zeros(vt.shape[0])
    padded[:len(sigma)] = sigma
    return vt[padded <= delta].T


def degeneracy_radius(F, w0, attractor, epsilon, jacobian_f, delta,
                      n_directions=64, r_max=1.0, tol=1e-3, seed=0):
    """
    Estimate of the robust degeneracy radius
        rho_deg = sup{ r : for all dW in K_delta with ||dW|| <= r, F(w0 + dW) in U_eps(A) }.

    F         -- callable: flattened conductance vector (length N^2) -> macroscopic state
    w0        -- flattened operating conductances
    attractor -- macroscopic state A of the attractor; U_eps(A) = {y : ||y - A|| <= epsilon}
    For each of n_directions random unit directions in K_delta, the largest r <= r_max
    that keeps F inside U_eps(A) is found by bisection (assuming the exit is monotone
    along the ray); rho_deg is the minimum over directions. Sampling can miss the worst
    direction, so the estimate is an upper bound of the true supremum.
    """
    w0 = _finite(w0, "w0").astype(float).ravel()
    attractor = _finite(attractor, "attractor").astype(float)
    basis = degenerate_directions(jacobian_f, delta)
    if basis.shape[0] != w0.size:
        raise ValueError(f"jacobian_f has {basis.shape[0]} columns, w0 has {w0.size} entries")
    if basis.shape[1] == 0:
        return {"rho_deg": 0.0, "n_degenerate_directions": 0, "upper_bound": True}
    if epsilon <= 0 or r_max <= 0:
        raise ValueError("epsilon and r_max must be positive")

    inside = lambda w: np.linalg.norm(np.asarray(F(w), dtype=float) - attractor) <= epsilon
    if not inside(w0):
        raise ValueError("F(w0) is not within epsilon of the attractor")

    rng = np.random.default_rng(seed)
    radii = []
    for _ in range(n_directions):
        u = basis @ rng.normal(size=basis.shape[1])
        u /= np.linalg.norm(u)
        if inside(w0 + r_max * u):
            radii.append(r_max)
            continue
        lo, hi = 0.0, r_max
        while hi - lo > tol:
            mid = 0.5 * (lo + hi)
            lo, hi = (mid, hi) if inside(w0 + mid * u) else (lo, mid)
        radii.append(lo)
    return {"rho_deg": float(min(radii)), "n_degenerate_directions": int(basis.shape[1]), "upper_bound": True}


def degeneracy_prediction(rho_deg, thermal_perturbation_norm):
    """Falsifiable prediction (B.15): rho_deg / ||Delta W_therm(T_op)|| > 1."""
    if thermal_perturbation_norm <= 0:
        raise ValueError("thermal_perturbation_norm must be positive")
    ratio = rho_deg / thermal_perturbation_norm
    return {"ratio": float(ratio), "passes": ratio > 1.0}


# ---------------------------------------------------------------------------
# 3. Critical scale-invariance (Appendix D)
# ---------------------------------------------------------------------------

FEASIBILITY_LIMIT = {"2D": 0.30, "3D": 0.50}


def exponent_stability(sizes, exponents, delta_exp, lattice="2D"):
    """
    Operational criterion of Appendix D: the critical exponents estimated at the three
    largest system sizes are stable within the preregistered tolerance delta_exp,
    read here as max |e_i - mean| / |mean| <= delta_exp over those three sizes.
    If delta_exp exceeds the feasibility limit (30% for 2D, 50% for 3D crossbars), the
    protocol is infeasible for the device class and the criterion is not applied.
    Estimating the exponents and choosing delta_exp follow the technical companion.
    """
    if lattice not in FEASIBILITY_LIMIT:
        raise ValueError(f"lattice must be '2D' or '3D', got {lattice!r}")
    sizes = _finite(sizes, "sizes").astype(float)
    exponents = _finite(exponents, "exponents").astype(float)
    if sizes.shape != exponents.shape or sizes.ndim != 1:
        raise ValueError("sizes and exponents must be 1-dimensional and of equal length")
    if len(sizes) < 3:
        raise ValueError(f"need at least three sizes, got {len(sizes)}")
    if delta_exp <= 0:
        raise ValueError(f"delta_exp must be positive, got {delta_exp}")

    feasible = delta_exp <= FEASIBILITY_LIMIT[lattice]
    largest = np.argsort(sizes)[-3:]
    selected = exponents[largest]
    mean = selected.mean()
    if mean == 0:
        raise ValueError("the mean exponent of the three largest sizes is zero")
    spread = float(np.max(np.abs(selected - mean)) / abs(mean))
    return {"sizes_used": sizes[largest], "exponents_used": selected, "relative_spread": spread,
            "delta_exp": float(delta_exp), "feasible": feasible,
            "passes": bool(feasible and spread <= delta_exp)}
