"""
demarcation.py
==============
The three operational demarcation conditions of the programme (P0_Distilled_v0.1.tex,
section 3; P1_Main.tex, section 2.1 and Appendix A). A substrate is a candidate if and
only if all three hold:

1. Causal non-separability: the numerical rank of the perturbational response matrix R
   exceeds the rank of a linear superposition model R_lin of the same size and bandwidth.
2. Non-Markovian memory: the information that the past carries about the future, beyond
   the most recent k states, stays positive for every Markov order k up to k_max and
   exceeds the distribution obtained from IAAFT surrogates.
3. State-dependent effective dynamics: the effective Jacobian estimated in three distinct
   regions of phase space differs by a relative norm above theta_state.

Interpretation choices, where the papers leave room (all declared in the docstrings):
- Condition 1 takes R_lin as input: fitting the linear time-invariant model to an impulse
  response is outside this module.
- Condition 2 measures, for each k, the conditional mutual information between the
  future and the past beyond order k, I(x[t+1]; x[t-k], ..., x[t-k-L+1] | x[t], ...,
  x[t-k+1]), with the k-nearest-neighbour estimator of Frenzel & Pompe (2007), k_NN = 4
  as in the papers. The "past beyond order k" is truncated to L lags (past_lags). The
  papers set k_max = 500, which a k-nearest-neighbour estimator cannot handle (it would
  work in 500+ dimensions); k_max is therefore a parameter. IAAFT surrogates preserve the amplitude distribution and the
  power spectrum, so they reproduce linear memory: as specified in the papers, the
  condition requires memory beyond that of a linear Gaussian process.
- Condition 3 splits the states into three regions by the terciles of their first
  principal component, fits a linear map in each region by least squares (the papers'
  randomised sketching is only a speed-up for large systems), and passes if the largest
  relative Frobenius difference between the Jacobians exceeds theta_state and the
  distribution of the same statistic on linear surrogates. The papers specify theta_state
  alone, which lets estimation noise pass with short records; the surrogate null is a
  declared deviation (see state_dependent_dynamics).
"""

import numpy as np
from scipy.spatial import cKDTree
from scipy.special import digamma


def _finite_array(values, name, ndim=None):
    arr = np.asarray(values, dtype=float)
    if ndim is not None and arr.ndim != ndim:
        raise ValueError(f"{name} must be {ndim}-dimensional, got shape {arr.shape}")
    if arr.size == 0:
        raise ValueError(f"{name} is empty")
    if not np.all(np.isfinite(arr)):
        raise ValueError(f"{name} contains NaN or infinite values")
    return arr


# ---------------------------------------------------------------------------
# Condition 1: causal non-separability
# ---------------------------------------------------------------------------

def numerical_rank(matrix, delta):
    """Number of singular values of `matrix` strictly above the noise floor `delta`."""
    matrix = _finite_array(matrix, "matrix", ndim=2)
    if delta < 0:
        raise ValueError(f"delta must be non-negative, got {delta}")
    return int(np.sum(np.linalg.svd(matrix, compute_uv=False) > delta))


def noise_floor_from_recordings(noise_matrix):
    """
    Noise floor delta for the numerical rank: the largest singular value of a response
    matrix recorded without stimulation (same shape as R). A singular value of R below it
    cannot be distinguished from measurement noise.
    """
    noise_matrix = _finite_array(noise_matrix, "noise_matrix", ndim=2)
    return float(np.linalg.svd(noise_matrix, compute_uv=False)[0])


def causal_non_separability(R, R_lin, delta):
    """
    Condition 1: rank_delta(R) > rank_delta(R_lin).

    R      -- K x K perturbational response matrix of the substrate
    R_lin  -- response matrix predicted by a linear superposition model of the same size
              and bandwidth
    delta  -- measurement noise floor (see noise_floor_from_recordings)
    """
    R = _finite_array(R, "R", ndim=2)
    R_lin = _finite_array(R_lin, "R_lin", ndim=2)
    if R.shape != R_lin.shape:
        raise ValueError(f"R and R_lin must have the same shape, got {R.shape} and {R_lin.shape}")
    rank_r = numerical_rank(R, delta)
    rank_lin = numerical_rank(R_lin, delta)
    return {"rank_R": rank_r, "rank_R_lin": rank_lin, "delta": float(delta), "passes": rank_r > rank_lin}


# ---------------------------------------------------------------------------
# Condition 2: non-Markovian memory
# ---------------------------------------------------------------------------

def dither(values, rng):
    """
    Break ties before a k-nearest-neighbour estimate (Kraskov et al. 2004 recommend adding
    low-amplitude noise). Each column with repeated values - quantized data, as from an
    ADC - gets uniform noise one quantization step wide (the step is the smallest gap
    between distinct values), which spreads each quantization level over its bin. Columns
    without repeats get Gaussian noise of 1e-10 times their standard deviation, which only
    breaks accidental ties.
    """
    values = np.array(values, dtype=float, copy=True)
    # Centre first: added noise must stay representable next to large offsets (at 1e15 the
    # spacing between doubles is 0.125, so noise of 1e-10 would be rounded away).
    values -= values.mean(axis=0)
    for col in range(values.shape[1]):
        column = values[:, col]
        levels = np.unique(column)
        if len(levels) < len(column) and len(levels) > 1:
            step = np.min(np.diff(levels))
            column += rng.uniform(-step / 2, step / 2, size=len(column))
        else:
            column += rng.normal(0.0, 1e-10 * (np.std(column) or 1.0), size=len(column))
    return values


def conditional_mutual_information(x, y, z=None, k=4, jitter=True, seed=0):
    """
    k-nearest-neighbour estimate of I(X; Y | Z) (Frenzel & Pompe 2007; with z=None, the
    mutual information estimator of Kraskov, Stoegbauer & Grassberger 2004), in nats.
    Uses the maximum norm. x, y, z are arrays of shape (n,) or (n, d).

    With jitter=True (default) the inputs are dithered first (see dither): on quantized
    data the estimator is otherwise strongly biased (two independent variables rounded to
    0.1 gave 0.19 nats instead of 0). The dither is seeded, so results are reproducible.
    """
    x = _finite_array(x, "x").reshape(len(x), -1)
    y = _finite_array(y, "y").reshape(len(y), -1)
    n = len(x)
    if len(y) != n:
        raise ValueError("x and y must have the same number of samples")
    if z is not None:
        z = _finite_array(z, "z").reshape(len(z), -1)
        if len(z) != n:
            raise ValueError("z must have the same number of samples as x and y")
    if n <= k + 1:
        raise ValueError(f"need more than k + 1 = {k + 1} samples, got {n}")
    if jitter:
        rng = np.random.default_rng(seed)
        x, y = dither(x, rng), dither(y, rng)
        z = dither(z, rng) if z is not None else None

    joint = np.hstack([x, y] if z is None else [x, y, z])
    # Distance to the k-th neighbour in the joint space (index 0 is the point itself)
    eps = cKDTree(joint).query(joint, k=k + 1, p=np.inf)[0][:, -1]
    # Count neighbours strictly closer than eps in the marginal spaces
    radius = np.nextafter(eps, 0)

    def counts(space):
        return cKDTree(space).query_ball_point(space, radius, p=np.inf, return_length=True) - 1

    if z is None:
        n_x, n_y = counts(x), counts(y)
        return float(digamma(k) + digamma(n) - np.mean(digamma(n_x + 1) + digamma(n_y + 1)))
    n_xz, n_yz, n_z = counts(np.hstack([x, z])), counts(np.hstack([y, z])), counts(z)
    return float(digamma(k) - np.mean(digamma(n_xz + 1) + digamma(n_yz + 1) - digamma(n_z + 1)))


def residual_memory(series, order, past_lags=5, k_nn=4):
    """
    Information that the past beyond the `order` most recent states carries about the
    future: I(x[t+1]; x[t-order], ..., x[t-order-past_lags+1] | x[t], ..., x[t-order+1]).
    For order = 0 it is the mutual information between x[t+1] and the last past_lags states.
    It vanishes (up to estimator bias) for a Markov process of order <= `order`.
    """
    series = _finite_array(series, "series", ndim=1)
    if order < 0:
        raise ValueError(f"order must be non-negative, got {order}")
    if past_lags < 1:
        raise ValueError(f"past_lags must be at least 1, got {past_lags}")
    span = order + past_lags  # number of lagged states used before x[t+1]
    n = len(series) - span
    if n <= 10 * (span + 1):
        raise ValueError(f"series too short ({len(series)} samples) for order {order} and {past_lags} past lags")

    def lagged(lag):  # x[t - lag] for t = span - 1, ..., len(series) - 2
        return series[span - 1 - lag: span - 1 - lag + n]

    future = series[span:]
    remote = np.column_stack([lagged(order + j) for j in range(past_lags)])
    recent = np.column_stack([lagged(j) for j in range(order)]) if order > 0 else None
    return conditional_mutual_information(future, remote, recent, k=k_nn)


def iaaft_surrogate(series, rng=None, n_iter=100):
    """
    Iterative amplitude-adjusted Fourier transform surrogate (Schreiber & Schmitz 1996):
    same amplitude distribution and approximately the same power spectrum as `series`,
    with nonlinear temporal structure destroyed.
    """
    series = _finite_array(series, "series", ndim=1)
    rng = np.random.default_rng() if rng is None else rng
    sorted_values = np.sort(series)
    target_amplitudes = np.abs(np.fft.rfft(series))
    surrogate = rng.permutation(series)
    for _ in range(n_iter):
        phases = np.angle(np.fft.rfft(surrogate))
        spectral = np.fft.irfft(target_amplitudes * np.exp(1j * phases), n=len(series))
        ranks = np.argsort(np.argsort(spectral))
        new = sorted_values[ranks]
        if np.array_equal(new, surrogate):
            break
        surrogate = new
    return surrogate


def non_markovian_memory(series, k_max=5, past_lags=5, n_surrogates=100, percentile=99.0, k_nn=4, seed=0):
    """
    Condition 2: for every Markov order k = 1..k_max, the residual memory of the series
    exceeds the `percentile` of the same quantity computed on IAAFT surrogates.

    Papers: k_NN = 4, k_max = 500, 99th percentile. k_max = 500 is not feasible with a
    k-nearest-neighbour estimator (see module docstring); the default here is 5.
    """
    series = _finite_array(series, "series", ndim=1)
    if k_max < 1:
        raise ValueError(f"k_max must be at least 1, got {k_max}")
    if n_surrogates < 1:
        raise ValueError(f"n_surrogates must be at least 1, got {n_surrogates}")
    rng = np.random.default_rng(seed)
    surrogates = [iaaft_surrogate(series, rng=rng) for _ in range(n_surrogates)]

    per_order = []
    for order in range(1, k_max + 1):
        observed = residual_memory(series, order, past_lags=past_lags, k_nn=k_nn)
        null = np.array([residual_memory(s, order, past_lags=past_lags, k_nn=k_nn) for s in surrogates])
        threshold = float(np.percentile(null, percentile))
        per_order.append({"order": order, "residual_memory": observed,
                          "surrogate_threshold": threshold, "exceeds": observed > threshold})
    return {"per_order": per_order, "k_max": k_max, "past_lags": past_lags, "n_surrogates": n_surrogates,
            "percentile": percentile, "passes": all(row["exceeds"] for row in per_order)}


# ---------------------------------------------------------------------------
# Condition 3: state-dependent effective dynamics
# ---------------------------------------------------------------------------

def phase_space_regions(states, n_regions=3):
    """
    Split the states (T x d) into `n_regions` disjoint regions of phase space by the
    quantiles of their first principal component. Returns a list of index arrays, each
    referring to states whose successor is also available (t < T - 1).
    """
    states = _finite_array(states, "states")
    states = states.reshape(len(states), -1)
    centred = states[:-1] - states[:-1].mean(axis=0)
    if centred.shape[1] == 1:
        score = centred[:, 0]
    else:
        score = centred @ np.linalg.svd(centred, full_matrices=False)[2][0]
    edges = np.quantile(score, np.linspace(0, 1, n_regions + 1))
    labels = np.clip(np.searchsorted(edges, score, side="right") - 1, 0, n_regions - 1)
    return [np.flatnonzero(labels == r) for r in range(n_regions)]


def local_jacobian(states, indices, dt=1.0):
    """
    Effective Jacobian of the flow in one region: least-squares fit of
    (x[t+1] - x[t]) / dt = J (x[t] - mean) + b over the given time indices.
    """
    states = _finite_array(states, "states").reshape(len(states), -1)
    indices = np.asarray(indices)
    d = states.shape[1]
    if len(indices) <= d + 1:
        raise ValueError(f"region has {len(indices)} points, need more than {d + 1}")
    x = states[indices]
    velocity = (states[indices + 1] - x) / dt
    design = np.hstack([x - x.mean(axis=0), np.ones((len(indices), 1))])
    coeffs = np.linalg.lstsq(design, velocity, rcond=None)[0]
    return coeffs[:d].T


def _jacobian_differences(states, regions, dt):
    jacobians = [local_jacobian(states, idx, dt=dt) for idx in regions]
    differences = []
    for i in range(len(jacobians)):
        for j in range(i + 1, len(jacobians)):
            scale = max(np.linalg.norm(jacobians[i]), np.linalg.norm(jacobians[j]), 1e-12)
            differences.append({"pair": (i, j),
                                "relative_difference": float(np.linalg.norm(jacobians[i] - jacobians[j]) / scale)})
    return jacobians, differences


def linear_surrogates(states, n_surrogates, rng):
    """
    Series of the same length generated by the best linear model of the data,
    x[t+1] = A x[t] + c + e[t], with the residuals e resampled with replacement
    (residual bootstrap). They share the data's linear dynamics and noise level, and
    their effective Jacobian is the same everywhere in phase space by construction.
    """
    states = _finite_array(states, "states").reshape(len(states), -1)
    x, y = states[:-1], states[1:]
    design = np.hstack([x, np.ones((len(x), 1))])
    coeffs = np.linalg.lstsq(design, y, rcond=None)[0]
    a, c = coeffs[:-1].T, coeffs[-1]
    residuals = y - design @ coeffs
    if np.max(np.abs(np.linalg.eigvals(a))) >= 1.0:
        raise ValueError("the fitted linear model is not stable; the linear null cannot be simulated")
    surrogates = []
    for _ in range(n_surrogates):
        noise = residuals[rng.integers(0, len(residuals), size=len(states) - 1)]
        s = np.empty_like(states)
        s[0] = states[0]
        for t in range(len(states) - 1):
            s[t + 1] = a @ s[t] + c + noise[t]
        surrogates.append(s)
    return surrogates


def state_dependent_dynamics(states, theta_state=0.25, dt=1.0, regions=None,
                             n_null=99, percentile=95.0, seed=0):
    """
    Condition 3: the effective Jacobians of three phase-space regions differ.

    Statistic: the largest pairwise relative difference
        ||J_i - J_j||_F / max(||J_i||_F, ||J_j||_F).
    Passes if the statistic exceeds both
      - theta_state, the minimum effect size of the papers (0.25), and
      - the `percentile` of the same statistic on n_null linear surrogates
        (linear_surrogates), which have the same Jacobian everywhere: the differences
        they show are estimation noise only.
    The papers specify theta_state alone. Without the null, estimation noise passes the
    threshold for short records: a linear system passed in 20 of 20 runs at 1000 samples.
    The null is a declared deviation from the papers; n_null = 0 reproduces their criterion.
    `regions` is a rule that partitions a series into regions: a callable taking the states
    and returning a list of index arrays, applied to the data and to each surrogate
    (default: phase_space_regions with three regions). A fixed list of index arrays is
    accepted only with n_null = 0, because indices of the observed series do not identify
    the same regions of phase space in a surrogate.
    """
    states = _finite_array(states, "states").reshape(len(states), -1)
    if isinstance(n_null, bool) or not isinstance(n_null, (int, np.integer)) or n_null < 0:
        raise ValueError(f"n_null must be a non-negative integer, got {n_null!r}")
    if regions is None:
        def partition(s):
            return phase_space_regions(s, 3)
    elif callable(regions):
        partition = regions
    elif n_null > 0:
        raise ValueError("with n_null > 0, regions must be a callable partition rule, "
                         "not fixed indices (they do not carry over to the surrogates)")
    else:
        fixed = list(regions)

        def partition(s):
            return fixed
    regions = partition(states)
    if len(regions) < 2:
        raise ValueError("need at least two regions")
    jacobians, differences = _jacobian_differences(states, regions, dt)
    statistic = max(d["relative_difference"] for d in differences)

    null_threshold = None
    if n_null > 0:
        rng = np.random.default_rng(seed)
        null = []
        for s in linear_surrogates(states, n_null, rng):
            null.append(max(d["relative_difference"] for d in _jacobian_differences(s, partition(s), dt)[1]))
        null_threshold = float(np.percentile(null, percentile))

    passes = statistic > theta_state and (null_threshold is None or statistic > null_threshold)
    return {"jacobians": jacobians, "differences": differences, "statistic": statistic,
            "theta_state": theta_state, "null_threshold": null_threshold, "n_null": n_null,
            "percentile": percentile, "passes": bool(passes)}


def is_candidate(condition_1, condition_2, condition_3):
    """A substrate is a candidate if and only if all three conditions pass."""
    return bool(condition_1["passes"] and condition_2["passes"] and condition_3["passes"])
