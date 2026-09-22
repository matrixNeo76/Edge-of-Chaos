"""
valenza_metrologia.py
======================
Script di Metrologia per Substrati Neuromorfici e Digital Twin (P0_Distilled v0.1)

Autore: Programma di Ricerca Lakatosiano (P0_Distilled v0.1)
Descrizione:
  Questo script funge da "righello metrologico" per elaborare le serie temporali fisiche
  misurate da substrati analogici (o simulate via SDE in un Digital Twin).
  
  Calcola:
  1. Decomposizione termodinamica di Hatano-Sasa (Housekeeping vs Excess entropy production).
  2. Stima non-parametrica k-NN della Divergenza di Kullback-Leibler (D_KL) per la nicchia allostasica.
  3. Guadagno predittivo dell'Efference Copy (G_pred) generata dal livello A2.
  4. Funzionale di Valenza Termodinamica e Allostasica integrato Psi(t).
"""

import numpy as np
from scipy.spatial import KDTree

def simulate_neuromorphic_substrate_sde(n_steps=10000, dt=0.001, seed=42):
    """
    Simula le dinamiche stocastiche di un substrato neuromorfico a due livelli (A1/A2)
    tramite integrazione SDE di Itô-Milstein.
    """
    np.random.seed(seed)
    
    # Parametri del materiale (Mott / Diffusive Memristor)
    a, b = -1.2, 0.8  # Parametri di attivazione locale (Edge of Chaos)
    sigma_noise = 0.15 # Ampiezza del rumore percolativo 1/f
    
    x_A1 = np.zeros(n_steps)
    s_obs = np.zeros(n_steps)
    s_pred = np.zeros(n_steps)
    
    x_val = 0.1
    for t in range(1, n_steps):
        # SDE per il livello primario A1
        dW = np.random.normal(0, np.sqrt(dt))
        dx = (a * x_val + b * np.tanh(x_val) + np.sin(t * dt * 2.0)) * dt + sigma_noise * dW
        # Correzione di Milstein
        dx += 0.5 * sigma_noise * sigma_noise * (dW**2 - dt)
        x_val += dx
        x_A1[t] = x_val
        
        # Riafferenza sensoriale reale
        s_obs[t] = x_val + np.random.normal(0, 0.05)
        
        # Copia efferente (livello A2) - predizione allostasica
        s_pred[t] = x_A1[t-1] + (a * x_A1[t-1] + b * np.tanh(x_A1[t-1])) * dt

    return x_A1, s_obs, s_pred, dt

def estimate_kl_divergence_knn(p_samples, q_samples, k=5):
    """
    Stima non-parametrica k-NN della divergenza di Kullback-Leibler D_KL(P || Q)
    basata sugli albori KDTree (Kraskov et al. / Perez-Cruz).
    """
    p_samples = np.atleast_2d(p_samples).T if p_samples.ndim == 1 else p_samples
    q_samples = np.atleast_2d(q_samples).T if q_samples.ndim == 1 else q_samples
    
    n, d = p_samples.shape
    m, _ = q_samples.shape
    
    tree_p = KDTree(p_samples)
    tree_q = KDTree(q_samples)
    
    # Distanze dai k-esimi vicini in P
    r_p, _ = tree_p.query(p_samples, k=k+1)
    r_k_p = r_p[:, -1]
    
    # Distanze dai k-esimi vicini in Q
    r_q, _ = tree_q.query(p_samples, k=k)
    r_k_q = r_q[:, -1]
    
    # Evita divisioni per zero
    r_k_p = np.maximum(r_k_p, 1e-12)
    r_k_q = np.maximum(r_k_q, 1e-12)
    
    kl_est = (d / n) * np.sum(np.log(r_k_q / r_k_p)) + np.log(m / (n - 1.0))
    return max(0.0, float(kl_est))

def calculate_thermodynamic_valence(x_A1, s_obs, s_pred, dt, alpha=1.0, beta=0.5, gamma=0.8):
    """
    Calcola il funzionale di valenza Psi(t) integrando la produzione di entropia NESS,
    la divergenza allostasica e il guadagno predittivo dell'efferenza.
    """
    # 1. Stima delle componenti dissipative NESS (Hatano-Sasa)
    dx = np.diff(x_A1) / dt
    sigma_hk = np.var(dx) # Dissipazione di housekeeping stazionaria
    sigma_ex = np.mean(np.abs(dx * x_A1[:-1])) # Dissipazione in eccesso per riorganizzazione
    
    # 2. Nicchia allostasica target p_target ~ N(0, 0.2)
    p_target = np.random.normal(0.0, 0.2, size=(len(x_A1), 1))
    x_samples = np.atleast_2d(x_A1).T
    
    d_kl_allostasica = estimate_kl_divergence_knn(x_samples, p_target, k=5)
    
    # 3. Guadagno Predittivo dell'Efference Copy (G_pred)
    s_obs_samples = np.atleast_2d(s_obs).T
    s_pred_samples = np.atleast_2d(s_pred).T
    
    d_kl_baseline = estimate_kl_divergence_knn(s_obs_samples, p_target, k=5)
    d_kl_predicted = estimate_kl_divergence_knn(s_pred_samples, p_target, k=5)
    
    g_pred = d_kl_baseline - d_kl_predicted
    
    # 4. Funzionale di Valenza Integrato Psi(t)
    psi = alpha * np.log(1.0 + (sigma_ex / (sigma_hk + 1e-8))) - beta * d_kl_allostasica + gamma * g_pred
    
    return {
        "sigma_ex": float(sigma_ex),
        "sigma_hk": float(sigma_hk),
        "d_kl_allostasica": float(d_kl_allostasica),
        "g_pred": float(g_pred),
        "psi_valenza": float(psi)
    }

if __name__ == "__main__":
    print("=== ESECUZIONE METROLOGIA AVANZATA DIGITAL TWIN (P0_Distilled v0.1) ===")
    x_A1, s_obs, s_pred, dt = simulate_neuromorphic_substrate_sde(n_steps=10000)
    res = calculate_thermodynamic_valence(x_A1, s_obs, s_pred, dt)
    
    print(f"Punti temporali processati: {len(x_A1)}")
    print(f"Stato medio substrato A1 x(t): {np.mean(x_A1):.4f}")
    print(f"Dissipazione in eccesso sigma_ex: {res['sigma_ex']:.4f}")
    print(f"Dissipazione housekeeping sigma_hk: {res['sigma_hk']:.4f}")
    print(f"Divergenza Allostasica D_KL(P||P_target): {res['d_kl_allostasica']:.4f}")
    print(f"Guadagno Predittivo dell'Efference Copy G_pred: {res['g_pred']:.4f}")
    print(f"-> FUNZIONALE DI VALENZA INTEGRATO Psi(t): {res['psi_valenza']:.4f}")
    print("=========================================================================")
