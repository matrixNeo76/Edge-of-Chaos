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

/// Estimate of the Kullback-Leibler divergence D_KL(P || Q) via k-nearest neighbours (k-NN)
pub fn estimate_kl_divergence_knn_1d(p_samples: &[f64], q_samples: &[f64], k: usize) -> f64 {
    let n = p_samples.len();
    let m = q_samples.len();

    if n <= k || m <= k {
        return 0.0;
    }

    let mut sorted_q = q_samples.to_vec();
    sorted_q.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));

    let mut kl_sum = 0.0;

    for &p_i in p_samples.iter() {
        // Distance to the k-th nearest neighbour in P
        let mut p_dists: Vec<f64> = p_samples.iter().map(|&x| (x - p_i).abs()).collect();
        p_dists.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
        let r_k_p = p_dists[k].max(1e-12);

        // Distance to the k-th nearest neighbour in Q
        let mut q_dists: Vec<f64> = sorted_q.iter().map(|&x| (x - p_i).abs()).collect();
        q_dists.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
        let r_k_q = q_dists[k - 1].max(1e-12);

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

    for p_i in p_samples.iter() {
        // Distance to the k-th nearest neighbour in P (index 0 is the point itself)
        let mut p_dists: Vec<f64> = p_samples.iter().map(|x| dist(x, p_i)).collect();
        p_dists.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
        let r_k_p = p_dists[k].max(1e-12);

        // Distance to the k-th nearest neighbour in Q
        let mut q_dists: Vec<f64> = q_samples.iter().map(|x| dist(x, p_i)).collect();
        q_dists.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
        let r_k_q = q_dists[k - 1].max(1e-12);

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
    let tau_steps = 10;
    let n = x_a1.len();
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

    // Target distribution for the allostatic niche
    let mut rng = FastRng::new(12345);
    let target_samples: Vec<f64> = (0..n).map(|_| rng.next_gaussian() * 0.2).collect();

    let d_kl_allostatic = estimate_kl_divergence_knn_1d(x_a1, &target_samples, 5);

    // G_pred scores the prediction against the observations, not against the niche.
    let p_ref = delay_embed(&target_samples, tau_steps);
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
