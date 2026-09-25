//! thermodynamic_valence.rs
//! ==========================
//! High-Performance Metrology Module in Rust for Neuromorphic Substrates & Digital Twin (P0_Distilled v0.1)
//!
//! Author: Lakatosian Research Programme (P0_Distilled v0.1)
//! Description:
//!   High-performance metrology module written in Rust for real-time processing
//!   of physical time series extracted from analog neuromorphic substrates.
//!
//! Implements:
//!   1. Euler-Maruyama SDE integration (additive noise) for a two-level A1/A2 architecture.
//!   2. Heuristic dissipation proxies sigma_hk / sigma_ex. These are NOT Hatano-Sasa
//!      housekeeping/excess entropy production rates: sigma_hk scales as
//!      sigma_noise^2 / dt, and the true housekeeping rate of this one-variable
//!      model is identically zero. See thermodynamic_valence.py for details.
//!   3. Non-parametric k-NN estimate of the Kullback-Leibler divergence (D_KL).
//!   4. Predictive gain of the efference copy (G_pred), as defined in
//!      P2_SelfAgency.tex §5.4, on delay-embedded densities.
//!   5. Integrated thermodynamic and allostatic valence functional Psi(t).

use std::f64::consts::PI;

/// Data structure for the metrology metric results
#[derive(Debug, Clone)]
pub struct MetrologyResult {
    pub sigma_ex: f64,
    pub sigma_hk: f64,
    pub d_kl_allostatic: f64,
    pub g_pred: f64,
    pub psi_valence: f64,
}

/// High-performance random number generator (Xorshift128+) with zero external dependencies
pub struct FastRng {
    s: [u64; 2],
}

impl FastRng {
    pub fn new(seed: u64) -> Self {
        let s0 = seed ^ 0x9E3779B97F4A7C15;
        let s1 = (seed.wrapping_add(0xBF58476D1CE4E5B9)) ^ 0x94D049BB133111EB;
        let (s0, s1) = if s0 == 0 && s1 == 0 { (1, s1) } else { (s0, s1) };
        Self { s: [s0, s1] }
    }

    pub fn next_u64(&mut self) -> u64 {
        let mut x = self.s[0];
        let y = self.s[1];
        self.s[0] = y;
        x ^= x << 23;
        self.s[1] = x ^ y ^ (x >> 17) ^ (y >> 26);
        self.s[1].wrapping_add(y)
    }

    pub fn next_f64(&mut self) -> f64 {
        (self.next_u64() >> 11) as f64 * (1.0 / (1u64 << 53) as f64)
    }

    /// Box-Muller transform for Gaussian random variables
    pub fn next_gaussian(&mut self) -> f64 {
        let u1 = self.next_f64().max(1e-15);
        let u2 = self.next_f64();
        (-2.0 * u1.ln()).sqrt() * (2.0 * PI * u2).cos()
    }
}

/// Simulates the A1/A2 neuromorphic substrate via Euler-Maruyama SDE integration (additive noise)
pub fn simulate_neuromorphic_substrate_sde(
    n_steps: usize,
    dt: f64,
    seed: u64,
) -> (Vec<f64>, Vec<f64>, Vec<f64>) {
    assert!(n_steps >= 2, "n_steps must be at least 2, got {}", n_steps);
    assert!(dt.is_finite() && dt > 0.0, "dt must be positive and finite, got {}", dt);
    let mut rng = FastRng::new(seed);
    let a = -1.2;
    let b = 0.8;
    let sigma_noise = 0.15; // additive white Gaussian noise, not 1/f

    let mut x_a1 = vec![0.0; n_steps];
    let mut s_obs = vec![0.0; n_steps];
    let mut s_pred = vec![0.0; n_steps];

    let mut x_val: f64 = 0.1;
    x_a1[0] = x_val;
    // No noise draw at t = 0, so the random stream of the loop is unchanged.
    s_obs[0] = x_val;
    s_pred[0] = x_val;
    let sqrt_dt = dt.sqrt();

    for t in 1..n_steps {
        let dw = rng.next_gaussian() * sqrt_dt;
        let time_val = t as f64 * dt;

        // With additive noise the Milstein correction 0.5*g*g'*(dw^2 - dt) vanishes
        // (g' = 0), so Milstein reduces to Euler-Maruyama (Higham 2001).
        let dx = (a * x_val + b * x_val.tanh() + (time_val * 2.0).sin()) * dt
            + sigma_noise * dw;

        x_val += dx;
        x_a1[t] = x_val;

        // Real sensory reafference
        s_obs[t] = x_val + rng.next_gaussian() * 0.05;

        // Predictive efference copy (level A2)
        let prev_x = x_a1[t - 1];
        s_pred[t] = prev_x + (a * prev_x + b * prev_x.tanh()) * dt;
    }

    (x_a1, s_obs, s_pred)
}

/// Value at position `index` of the sorted slice, by partial selection (reorders `values`)
fn kth_smallest(values: &mut [f64], index: usize) -> f64 {
    *values
        .select_nth_unstable_by(index, |a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal))
        .1
}

/// Estimate of the Kullback-Leibler divergence D_KL(P || Q) via k-nearest neighbours (k-NN).
/// Negative estimates (possible from sampling noise when P and Q are close) are clipped
/// to 0, as in the Python engine; G_pred, a difference of two estimates, inherits this.
pub fn estimate_kl_divergence_knn_1d(p_samples: &[f64], q_samples: &[f64], k: usize) -> f64 {
    let n = p_samples.len();
    let m = q_samples.len();

    if n <= k || m <= k {
        return 0.0;
    }

    let mut kl_sum = 0.0;
    let mut p_dists = vec![0.0; n];
    let mut q_dists = vec![0.0; m];

    for &p_i in p_samples.iter() {
        // Distance to the k-th nearest neighbour in P (index 0 is the point itself)
        for (d, &x) in p_dists.iter_mut().zip(p_samples) {
            *d = (x - p_i).abs();
        }
        let r_k_p = kth_smallest(&mut p_dists, k).max(1e-12);

        // Distance to the k-th nearest neighbour in Q
        for (d, &x) in q_dists.iter_mut().zip(q_samples) {
            *d = (x - p_i).abs();
        }
        let r_k_q = kth_smallest(&mut q_dists, k - 1).max(1e-12);

        kl_sum += (r_k_q / r_k_p).ln();
    }

    let kl_est = (1.0 / n as f64) * kl_sum + (m as f64 / (n - 1) as f64).ln();
    kl_est.max(0.0)
}

/// Two-dimensional delay embedding (s(t), s(t - tau)) of a one-dimensional signal
pub fn delay_embed(signal: &[f64], tau_steps: usize) -> Vec<[f64; 2]> {
    (tau_steps..signal.len())
        .map(|t| [signal[t], signal[t - tau_steps]])
        .collect()
}

/// Estimate of D_KL(P || Q) via k-nearest neighbours for two-dimensional samples
/// (Euclidean distance), matching estimate_kl_divergence_knn in thermodynamic_valence.py
pub fn estimate_kl_divergence_knn_2d(p_samples: &[[f64; 2]], q_samples: &[[f64; 2]], k: usize) -> f64 {
    let n = p_samples.len();
    let m = q_samples.len();

    if n <= k || m <= k {
        return 0.0;
    }

    let dist = |a: &[f64; 2], b: &[f64; 2]| ((a[0] - b[0]).powi(2) + (a[1] - b[1]).powi(2)).sqrt();
    let mut kl_sum = 0.0;
    let mut p_dists = vec![0.0; n];
    let mut q_dists = vec![0.0; m];

    for p_i in p_samples.iter() {
        // Distance to the k-th nearest neighbour in P (index 0 is the point itself)
        for (d, x) in p_dists.iter_mut().zip(p_samples) {
            *d = dist(x, p_i);
        }
        let r_k_p = kth_smallest(&mut p_dists, k).max(1e-12);

        // Distance to the k-th nearest neighbour in Q
        for (d, x) in q_dists.iter_mut().zip(q_samples) {
            *d = dist(x, p_i);
        }
        let r_k_q = kth_smallest(&mut q_dists, k - 1).max(1e-12);

        kl_sum += (r_k_q / r_k_p).ln();
    }

    let kl_est = (2.0 / n as f64) * kl_sum + (m as f64 / (n - 1) as f64).ln();
    kl_est.max(0.0)
}

/// Computes the integrated valence functional Psi(t).
///
/// G_pred follows P2_SelfAgency.tex (§5.4): D_KL(p_obs || p_ref) - D_KL(p_obs || p_pred),
/// on delay-embedded densities. The target niche stands in for the free-running
/// reference p_ref, because the digital twin has no actuation.
pub fn calculate_thermodynamic_valence(
    x_a1: &[f64],
    s_obs: &[f64],
    s_pred: &[f64],
    dt: f64,
    alpha: f64,
    beta: f64,
    gamma: f64,
) -> MetrologyResult {
    // Target distribution for the allostatic niche, N(0, 0.2), from a fixed seed
    let mut rng = FastRng::new(12345);
    let niche: Vec<f64> = (0..x_a1.len()).map(|_| rng.next_gaussian() * 0.2).collect();
    calculate_thermodynamic_valence_with_niche(x_a1, s_obs, s_pred, dt, alpha, beta, gamma, &niche)
}

/// As calculate_thermodynamic_valence, with the niche samples given explicitly. With the
/// same niche, the Python engine returns the same numbers (tested in test_engine_parity.py).
#[allow(clippy::too_many_arguments)]
pub fn calculate_thermodynamic_valence_with_niche(
    x_a1: &[f64],
    s_obs: &[f64],
    s_pred: &[f64],
    dt: f64,
    alpha: f64,
    beta: f64,
    gamma: f64,
    target_samples: &[f64],
) -> MetrologyResult {
    let tau_steps = 10;
    let n = x_a1.len();
    assert!(
        target_samples.len() == n,
        "the niche must have as many samples as the series, got {} and {}",
        target_samples.len(), n
    );
    assert!(
        s_obs.len() == n && s_pred.len() == n,
        "x_a1, s_obs and s_pred must have equal length, got {}, {}, {}",
        n, s_obs.len(), s_pred.len()
    );
    assert!(dt.is_finite() && dt > 0.0, "dt must be positive and finite, got {}", dt);
    assert!(n >= tau_steps + 7, "series too short: {} samples, need at least {}", n, tau_steps + 7);
    assert!(
        x_a1.iter().chain(s_obs).chain(s_pred).chain(target_samples).all(|v| v.is_finite()),
        "x_a1, s_obs, s_pred and the niche must not contain NaN or infinite values"
    );
    let mut dx = Vec::with_capacity(n - 1);
    for i in 0..n - 1 {
        dx.push((x_a1[i + 1] - x_a1[i]) / dt);
    }

    // Heuristic proxies, NOT Hatano-Sasa quantities; their ratio (and Psi) changes with dt.
    // sigma_hk proxy: variance of the finite-difference velocity (~ sigma_noise^2 / dt)
    let mean_dx = dx.iter().sum::<f64>() / dx.len() as f64;
    let sigma_hk = dx.iter().map(|v| (v - mean_dx).powi(2)).sum::<f64>() / dx.len() as f64;

    // sigma_ex proxy: mean |velocity * state|
    let mut excess_sum = 0.0;
    for i in 0..dx.len() {
        excess_sum += (dx[i] * x_a1[i]).abs();
    }
    let sigma_ex = excess_sum / dx.len() as f64;

    let d_kl_allostatic = estimate_kl_divergence_knn_1d(x_a1, target_samples, 5);

    // G_pred scores the prediction against the observations, not against the niche.
    let p_ref = delay_embed(target_samples, tau_steps);
    let obs_embedded = delay_embed(s_obs, tau_steps);
    let pred_embedded = delay_embed(s_pred, tau_steps);
    let d_kl_reference = estimate_kl_divergence_knn_2d(&obs_embedded, &p_ref, 5);
    let d_kl_prediction = estimate_kl_divergence_knn_2d(&obs_embedded, &pred_embedded, 5);

    let g_pred = d_kl_reference - d_kl_prediction;

    // PRACTICAL PROXY, not the formal Psi(t) of P1_Main.tex Appendix F (which uses
    // normalized entropy-production rates against a hardware-calibrated S_crit_dot).
    // The two forms are NOT algebraically equivalent -- see Appendix F before
    // treating this as ground truth.
    let psi = alpha * (1.0 + (sigma_ex / (sigma_hk + 1e-8))).ln() - beta * d_kl_allostatic + gamma * g_pred;

    MetrologyResult {
        sigma_ex,
        sigma_hk,
        d_kl_allostatic,
        g_pred,
        psi_valence: psi,
    }
}

fn main() {
    println!("=== RUNNING RUST DIGITAL TWIN METROLOGY (P0_Distilled v0.1) ===");
    let n_steps = 10000;
    let dt = 0.001;
    let (x_a1, s_obs, s_pred) = simulate_neuromorphic_substrate_sde(n_steps, dt, 42);

    let res = calculate_thermodynamic_valence(&x_a1, &s_obs, &s_pred, dt, 1.0, 0.5, 0.8);

    println!("Time points processed: {}", n_steps);
    println!("Mean state of substrate A1 x(t): {:.4}", x_a1.iter().sum::<f64>() / n_steps as f64);
    println!("Excess-dissipation proxy sigma_ex: {:.4}", res.sigma_ex);
    println!("Housekeeping-dissipation proxy sigma_hk (dt-dependent): {:.4}", res.sigma_hk);
    println!("Allostatic divergence D_KL(P||P_target): {:.4}", res.d_kl_allostatic);
    println!("Predictive gain of the efference copy G_pred: {:.4}", res.g_pred);
    println!("-> INTEGRATED VALENCE FUNCTIONAL Psi(t): {:.4}", res.psi_valence);
    println!("=========================================================================");
}

#[cfg(test)]
mod tests {
    use super::*;

    fn gaussian(rng: &mut FastRng, n: usize, mean: f64, sd: f64) -> Vec<f64> {
        (0..n).map(|_| mean + sd * rng.next_gaussian()).collect()
    }

    fn gaussian_kl(m1: f64, s1: f64, m2: f64, s2: f64) -> f64 {
        (s2 / s1).ln() + (s1 * s1 + (m1 - m2).powi(2)) / (2.0 * s2 * s2) - 0.5
    }

    #[test]
    fn kl_1d_matches_closed_form_gaussian_values() {
        let mut rng = FastRng::new(1);
        for &(m1, s1, m2, s2) in &[(0.0, 1.0, 1.0, 1.0), (0.0, 1.0, 0.0, 2.0), (0.5, 0.3, 0.0, 1.0)] {
            let p = gaussian(&mut rng, 3000, m1, s1);
            let q = gaussian(&mut rng, 3000, m2, s2);
            let estimate = estimate_kl_divergence_knn_1d(&p, &q, 5);
            let expected = gaussian_kl(m1, s1, m2, s2);
            assert!((estimate - expected).abs() < 0.08, "estimate {} vs {}", estimate, expected);
        }
    }

    #[test]
    fn kl_2d_matches_closed_form_value() {
        let mut rng = FastRng::new(2);
        let p: Vec<[f64; 2]> = (0..3000).map(|_| [rng.next_gaussian(), rng.next_gaussian()]).collect();
        let q: Vec<[f64; 2]> = (0..3000).map(|_| [1.0 + rng.next_gaussian(), 1.0 + rng.next_gaussian()]).collect();
        let estimate = estimate_kl_divergence_knn_2d(&p, &q, 5);
        assert!((estimate - 1.0).abs() < 0.1, "estimate {}", estimate);
    }

    #[test]
    fn delay_embedding_pairs_each_sample_with_its_past() {
        let embedded = delay_embed(&[0.0, 1.0, 2.0, 3.0, 4.0], 2);
        assert_eq!(embedded, vec![[2.0, 0.0], [3.0, 1.0], [4.0, 2.0]]);
    }

    #[test]
    fn default_niche_equals_explicit_seeded_niche() {
        let (x, s_obs, s_pred) = simulate_neuromorphic_substrate_sde(300, 0.001, 3);
        let mut rng = FastRng::new(12345);
        let niche: Vec<f64> = (0..x.len()).map(|_| rng.next_gaussian() * 0.2).collect();
        let a = calculate_thermodynamic_valence(&x, &s_obs, &s_pred, 0.001, 1.0, 0.5, 0.8);
        let b = calculate_thermodynamic_valence_with_niche(&x, &s_obs, &s_pred, 0.001, 1.0, 0.5, 0.8, &niche);
        assert_eq!(a.psi_valence, b.psi_valence);
    }

    #[test]
    fn efference_ablation_lowers_the_predictive_gain() {
        let (x, s_obs, s_pred) = simulate_neuromorphic_substrate_sde(1500, 0.001, 42);
        let mut rng = FastRng::new(2026);
        let ablated = gaussian(&mut rng, s_pred.len(), 0.0, 1.0);
        let base = calculate_thermodynamic_valence(&x, &s_obs, &s_pred, 0.001, 1.0, 0.5, 0.8);
        let abl = calculate_thermodynamic_valence(&x, &s_obs, &ablated, 0.001, 1.0, 0.5, 0.8);
        assert!(abl.g_pred < base.g_pred);
        assert!(abl.psi_valence < base.psi_valence);
    }

    #[test]
    #[should_panic(expected = "equal length")]
    fn unequal_lengths_panic() {
        let (x, s_obs, s_pred) = simulate_neuromorphic_substrate_sde(100, 0.001, 1);
        calculate_thermodynamic_valence(&x, &s_obs[..90], &s_pred, 0.001, 1.0, 0.5, 0.8);
    }

    #[test]
    #[should_panic(expected = "too short")]
    fn short_series_panic() {
        let (x, s_obs, s_pred) = simulate_neuromorphic_substrate_sde(12, 0.001, 1);
        calculate_thermodynamic_valence(&x, &s_obs, &s_pred, 0.001, 1.0, 0.5, 0.8);
    }

    #[test]
    #[should_panic(expected = "must not contain NaN")]
    fn non_finite_niche_panics() {
        let (x, s_obs, s_pred) = simulate_neuromorphic_substrate_sde(100, 0.001, 1);
        let mut niche = vec![0.0; x.len()];
        niche[3] = f64::INFINITY;
        calculate_thermodynamic_valence_with_niche(&x, &s_obs, &s_pred, 0.001, 1.0, 0.5, 0.8, &niche);
    }

    #[test]
    #[should_panic(expected = "dt must be positive")]
    fn zero_dt_panics() {
        simulate_neuromorphic_substrate_sde(100, 0.0, 1);
    }
}
