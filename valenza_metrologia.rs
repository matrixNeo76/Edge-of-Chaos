//! valenza_metrologia.rs
//! ======================
//! High-Performance Metrology Module in Rust for Neuromorphic Substrates & Digital Twin (P0_Distilled v0.1)
//!
//! Autore: Programma di Ricerca Lakatosiano (P0_Distilled v0.1)
//! Descrizione:
//!   Modulo metrologico ad alte prestazioni scritto in Rust per l'elaborazione in tempo reale
//!   di serie temporali fisiche estratte da substrati neuromorfici analogici.
//!   
//! Implementa:
//!   1. Integrazione SDE stocastica di Itô-Milstein per architettura a due livelli A1/A2.
//!   2. Decomposizione termodinamica di NESS (Housekeeping vs Excess entropy production).
//!   3. Stima non-parametrica k-NN della Divergenza di Kullback-Leibler (D_KL).
//!   4. Guadagno predittivo della copia efferente (G_pred).
//!   5. Funzionale di Valenza Termodinamica e Allostasica integrato Psi(t).

use std::f64::consts::PI;

/// Struttura dati per i risultati delle metriche metrologiche
#[derive(Debug, Clone)]
pub struct MetrologyResult {
    pub sigma_ex: f64,
    pub sigma_hk: f64,
    pub d_kl_allostasica: f64,
    pub g_pred: f64,
    pub psi_valenza: f64,
}

/// Generatore di numeri casuali ad alte prestazioni (Xorshift128+) per zero dipendenze esterne
pub struct FastRng {
    s: [u64; 2],
}

impl FastRng {
    pub fn new(seed: u64) -> Self {
        let mut s0 = seed ^ 0x9E3779B97F4A7C15;
        let mut s1 = (seed.wrapping_add(0xBF58476D1CE4E5B9)) ^ 0x94D049BB133111EB;
        if s0 == 0 && s1 == 0 {
            s0 = 1;
        }
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

    /// Trasformata di Box-Muller per variabili casuali gaussiane
    pub fn next_gaussian(&mut self) -> f64 {
        let u1 = self.next_f64().max(1e-15);
        let u2 = self.next_f64();
        (-2.0 * u1.ln()).sqrt() * (2.0 * PI * u2).cos()
    }
}

/// Simula il substrato neuromorfico A1/A2 tramite integrazione SDE di Itô-Milstein
pub fn simulate_neuromorphic_substrate_sde(
    n_steps: usize,
    dt: f64,
    seed: u64,
) -> (Vec<f64>, Vec<f64>, Vec<f64>) {
    let mut rng = FastRng::new(seed);
    let a = -1.2;
    let b = 0.8;
    let sigma_noise = 0.15;

    let mut x_a1 = vec![0.0; n_steps];
    let mut s_obs = vec![0.0; n_steps];
    let mut s_pred = vec![0.0; n_steps];

    let mut x_val: f64 = 0.1;
    let sqrt_dt = dt.sqrt();

    for t in 1..n_steps {
        let dw = rng.next_gaussian() * sqrt_dt;
        let time_val = t as f64 * dt;

        // Step SDE Itô-Milstein per il substrato A1
        let mut dx = (a * x_val + b * x_val.tanh() + (time_val * 2.0).sin()) * dt
            + sigma_noise * dw;
        dx += 0.5 * sigma_noise * sigma_noise * (dw * dw - dt);

        x_val += dx;
        x_a1[t] = x_val;

        // Riafferenza sensoriale reale
        s_obs[t] = x_val + rng.next_gaussian() * 0.05;

        // Copia efferente predittiva (Livello A2)
        let prev_x = x_a1[t - 1];
        s_pred[t] = prev_x + (a * prev_x + b * prev_x.tanh()) * dt;
    }

    (x_a1, s_obs, s_pred)
}

/// Stima della Divergenza di Kullback-Leibler D_KL(P || Q) tramite vicini più prossimi (k-NN)
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
        // Distanza dal k-esimo vicino in P
        let mut p_dists: Vec<f64> = p_samples.iter().map(|&x| (x - p_i).abs()).collect();
        p_dists.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
        let r_k_p = p_dists[k].max(1e-12);

        // Distanza dal k-esimo vicino in Q
        let mut q_dists: Vec<f64> = sorted_q.iter().map(|&x| (x - p_i).abs()).collect();
        q_dists.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
        let r_k_q = q_dists[k - 1].max(1e-12);

        kl_sum += (r_k_q / r_k_p).ln();
    }

    let kl_est = (1.0 / n as f64) * kl_sum + (m as f64 / (n - 1) as f64).ln();
    kl_est.max(0.0)
}

/// Calcola il funzionale di valenza integrato Psi(t)
pub fn calculate_thermodynamic_valence(
    x_a1: &[f64],
    s_obs: &[f64],
    s_pred: &[f64],
    dt: f64,
    alpha: f64,
    beta: f64,
    gamma: f64,
) -> MetrologyResult {
    let n = x_a1.len();
    let mut dx = Vec::with_capacity(n - 1);
    for i in 0..n - 1 {
        dx.push((x_a1[i + 1] - x_a1[i]) / dt);
    }

    // Dissipazione di housekeeping (varianza di dx)
    let mean_dx = dx.iter().sum::<f64>() / dx.len() as f64;
    let sigma_hk = dx.iter().map(|v| (v - mean_dx).powi(2)).sum::<f64>() / dx.len() as f64;

    // Dissipazione in eccesso per riorganizzazione
    let mut excess_sum = 0.0;
    for i in 0..dx.len() {
        excess_sum += (dx[i] * x_a1[i]).abs();
    }
    let sigma_ex = excess_sum / dx.len() as f64;

    // Distribuzione target per la nicchia allostasica
    let mut rng = FastRng::new(12345);
    let target_samples: Vec<f64> = (0..n).map(|_| rng.next_gaussian() * 0.2).collect();

    let d_kl_allostasica = estimate_kl_divergence_knn_1d(x_a1, &target_samples, 5);
    let d_kl_baseline = estimate_kl_divergence_knn_1d(s_obs, &target_samples, 5);
    let d_kl_predicted = estimate_kl_divergence_knn_1d(s_pred, &target_samples, 5);

    let g_pred = d_kl_baseline - d_kl_predicted;

    let psi = alpha * (1.0 + (sigma_ex / (sigma_hk + 1e-8))).ln() - beta * d_kl_allostasica + gamma * g_pred;

    MetrologyResult {
        sigma_ex,
        sigma_hk,
        d_kl_allostasica,
        g_pred,
        psi_valenza: psi,
    }
}

fn main() {
    println!("=== ESECUZIONE METROLOGIA RUST DIGITAL TWIN (P0_Distilled v0.1) ===");
    let n_steps = 10000;
    let dt = 0.001;
    let (x_a1, s_obs, s_pred) = simulate_neuromorphic_substrate_sde(n_steps, dt, 42);

    let res = calculate_thermodynamic_valence(&x_a1, &s_obs, &s_pred, dt, 1.0, 0.5, 0.8);

    println!("Punti temporali processati: {}", n_steps);
    println!("Stato medio substrato A1 x(t): {:.4}", x_a1.iter().sum::<f64>() / n_steps as f64);
    println!("Dissipazione in eccesso sigma_ex: {:.4}", res.sigma_ex);
    println!("Dissipazione housekeeping sigma_hk: {:.4}", res.sigma_hk);
    println!("Divergenza Allostasica D_KL(P||P_target): {:.4}", res.d_kl_allostasica);
    println!("Guadagno Predittivo dell'Efference Copy G_pred: {:.4}", res.g_pred);
    println!("-> FUNZIONALE DI VALENZA INTEGRATO Psi(t): {:.4}", res.psi_valenza);
    println!("=========================================================================");
}
