use pyo3::prelude::*;
use pyo3::wrap_pyfunction;

/// High-performance random number generator Xorshift128+
struct Xorshift128Plus {
    s: [u64; 2],
}

impl Xorshift128Plus {
    fn new(seed: u64) -> Self {
        let mut s0 = seed.wrapping_add(0x9E3779B97F4A7C15);
        let mut s1 = s0.wrapping_add(0x9E3779B97F4A7C15);
        if s0 == 0 && s1 == 0 {
            s0 = 1;
            s1 = 1;
        }
        Self { s: [s0, s1] }
    }

    fn next_u64(&mut self) -> u64 {
        let mut x = self.s[0];
        let y = self.s[1];
        self.s[0] = y;
        x ^= x << 23;
        self.s[1] = x ^ y ^ (x >> 17) ^ (y >> 26);
        self.s[1].wrapping_add(y)
    }

    fn next_f64(&mut self) -> f64 {
        (self.next_u64() >> 11) as f64 / (1u64 << 53) as f64
    }

    fn next_gaussian(&mut self) -> f64 {
        let u1 = f64::max(self.next_f64(), 1e-15);
        let u2 = self.next_f64();
        (-2.0 * u1.ln()).sqrt() * (2.0 * std::f64::consts::PI * u2).cos()
    }
}

#[pyclass]
#[derive(Clone, Debug)]
pub struct MetrologyResultsRust {
    #[pyo3(get)]
    pub sigma_ex: f64,
    #[pyo3(get)]
    pub sigma_hk: f64,
    #[pyo3(get)]
    pub d_kl_allostatic: f64,
    #[pyo3(get)]
    pub g_pred: f64,
    #[pyo3(get)]
    pub psi_valence: f64,
}

#[pymethods]
impl MetrologyResultsRust {
    fn __repr__(&self) -> String {
        format!(
            "<MetrologyResultsRust sigma_ex={:.4} sigma_hk={:.4} D_KL={:.4} G_pred={:.4} Psi={:.4}>",
            self.sigma_ex, self.sigma_hk, self.d_kl_allostatic, self.g_pred, self.psi_valence
        )
    }
}

#[pyfunction]
pub fn compute_thermodynamic_valence_rust(
    n_steps: usize,
    dt: f64,
    seed: u64,
    alpha: f64,
    beta: f64,
    gamma: f64,
) -> PyResult<MetrologyResultsRust> {
    let mut rng = Xorshift128Plus::new(seed);
    let a = -1.2;
    let b = 0.8;
    let sigma_noise = 0.15;

    let mut x_a1 = vec![0.0; n_steps];
    let mut s_obs = vec![0.0; n_steps];
    let mut s_pred = vec![0.0; n_steps];

    let mut x_val: f64 = 0.1;
    x_a1[0] = x_val;
    for t in 1..n_steps {
        let dw = rng.next_gaussian() * dt.sqrt();
        // Euler-Maruyama: with additive noise the Milstein correction vanishes (g' = 0).
        let dx = (a * x_val + b * x_val.tanh() + (t as f64 * dt * 2.0).sin()) * dt
            + sigma_noise * dw;
        x_val += dx;
        x_a1[t] = x_val;

        s_obs[t] = x_val + rng.next_gaussian() * 0.05;
        s_pred[t] = x_a1[t - 1] + (a * x_a1[t - 1] + b * x_a1[t - 1].tanh()) * dt;
    }

    // Heuristic dissipation proxies, NOT Hatano-Sasa quantities (see
    // thermodynamic_valence.py): sigma_hk ~ sigma_noise^2 / dt, so Psi changes with dt.
    let mut mean_x = 0.0;
    for &x in &x_a1 {
        mean_x += x;
    }
    mean_x /= n_steps as f64;

    let mut dx_vec = vec![0.0; n_steps - 1];
    for i in 0..n_steps - 1 {
        dx_vec[i] = (x_a1[i + 1] - x_a1[i]) / dt;
    }
    let mean_dx = dx_vec.iter().sum::<f64>() / (n_steps - 1) as f64;
    let sigma_hk = dx_vec.iter().map(|v| (v - mean_dx).powi(2)).sum::<f64>() / (n_steps - 1) as f64;

    let mut excess_sum = 0.0;
    for i in 0..n_steps - 1 {
        excess_sum += (dx_vec[i] * x_a1[i]).abs();
    }
    let sigma_ex = excess_sum / (n_steps - 1) as f64;

    // PLACEHOLDERS, not the k-NN estimators of thermodynamic_valence.py/.rs: D_KL is a
    // squared z-score of the mean, G_pred uses a single sample. Results from this
    // module are therefore not comparable with the Python or standalone Rust engines.
    let d_kl_allostatic = (mean_x.abs() / 0.2).powi(2);
    let g_pred = 0.05 * (1.0 - (s_obs[1] - s_pred[1]).abs());

    // PRACTICAL PROXY, not the formal Psi(t) of P1_Main.tex Appendix F -- see
    // thermodynamic_valence.py for the full rationale. Not algebraically equivalent.
    let psi = alpha * (1.0 + (sigma_ex / (sigma_hk + 1e-8))).ln() - beta * d_kl_allostatic + gamma * g_pred;

    Ok(MetrologyResultsRust {
        sigma_ex,
        sigma_hk,
        d_kl_allostatic,
        g_pred,
        psi_valence: psi,
    })
}

#[pymodule]
fn thermodynamic_valence_rust(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<MetrologyResultsRust>()?;
    m.add_function(wrap_pyfunction!(compute_thermodynamic_valence_rust, m)?)?;
    Ok(())
}
