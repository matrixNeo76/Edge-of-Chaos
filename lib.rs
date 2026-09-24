//! Python extension (PyO3) exposing the Rust metrology engine of
//! thermodynamic_valence.rs. Up to v0.2.1 this module had its own simulation and
//! placeholder estimators for D_KL and G_pred, whose results were not comparable with
//! the Python and standalone Rust engines; it now calls the same engine as the binary.

use pyo3::prelude::*;
use pyo3::wrap_pyfunction;

// The binary's source file doubles as the engine module; its main() is unused here.
#[allow(dead_code)]
#[path = "thermodynamic_valence.rs"]
mod engine;

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

/// Simulates the substrate and computes the valence proxy with the Rust engine.
/// Same numbers as the standalone binary for the same arguments.
#[pyfunction]
pub fn compute_thermodynamic_valence_rust(
    n_steps: usize,
    dt: f64,
    seed: u64,
    alpha: f64,
    beta: f64,
    gamma: f64,
) -> PyResult<MetrologyResultsRust> {
    if n_steps < 17 {
        return Err(pyo3::exceptions::PyValueError::new_err(format!(
            "n_steps must be at least 17, got {}",
            n_steps
        )));
    }
    if !(dt > 0.0) {
        return Err(pyo3::exceptions::PyValueError::new_err(format!(
            "dt must be positive, got {}",
            dt
        )));
    }
    let (x_a1, s_obs, s_pred) = engine::simulate_neuromorphic_substrate_sde(n_steps, dt, seed);
    let res = engine::calculate_thermodynamic_valence(&x_a1, &s_obs, &s_pred, dt, alpha, beta, gamma);
    Ok(MetrologyResultsRust {
        sigma_ex: res.sigma_ex,
        sigma_hk: res.sigma_hk,
        d_kl_allostatic: res.d_kl_allostatic,
        g_pred: res.g_pred,
        psi_valence: res.psi_valence,
    })
}

#[pymodule]
fn thermodynamic_valence_rust(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<MetrologyResultsRust>()?;
    m.add_function(wrap_pyfunction!(compute_thermodynamic_valence_rust, m)?)?;
    Ok(())
}
