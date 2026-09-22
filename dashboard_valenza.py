"""
dashboard_valenza.py
=====================
Script per la Generazione della Dashboard di Visualizzazione Metrologica (Digital Twin P0_Distilled v0.1)

Genera:
1. Serie temporale del Funzionale di Valenza Psi(t) e della Dissipazione Ex/Hk.
2. Traiettoria nello Spazio delle Fasi (x(t) vs dx/dt) con regione di Edge of Chaos.
3. Diagramma di Confronto tra Condizione Baseline e Ablazione 4 (Disaccoppiamento Efferenza).
"""

import os
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

# BASE_DIR serve solo per sys.path (import di valenza_metrologia quando lo
# script gira standalone). Se impacchettato con PyInstaller, __file__ punta
# dentro la cartella interna dell'app (_internal): l'output NON deve finire
# li', ma nella directory di lavoro corrente dell'utente, come per qualsiasi
# altro eseguibile a riga di comando.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.environ.get('OUTPUT_DIR', os.path.join(os.getcwd(), 'output'))
sys.path.append(BASE_DIR)
from valenza_metrologia import simulate_neuromorphic_substrate_sde, calculate_thermodynamic_valence

def generate_metrology_dashboard():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    sns.set_theme(style='whitegrid', palette='colorblind', font='DejaVu Sans')
    
    # 1. Simulazione Baseline
    n_steps = 2000
    x_A1, s_obs, s_pred, dt = simulate_neuromorphic_substrate_sde(n_steps=n_steps, seed=42)
    time_vec = np.arange(n_steps) * dt
    
    # Calcolo valenza su finestra mobile
    window = 100
    psi_series = []
    ex_series = []
    hk_series = []
    
    for i in range(window, n_steps, 20):
        sub_x = x_A1[i-window:i]
        sub_obs = s_obs[i-window:i]
        sub_pred = s_pred[i-window:i]
        res = calculate_thermodynamic_valence(sub_x, sub_obs, sub_pred, dt)
        psi_series.append(res['psi_valenza'])
        ex_series.append(res['sigma_ex'])
        hk_series.append(res['sigma_hk'])
        
    t_sub = time_vec[window::20]
    
    # 2. Simulazione Ablazione 4 (Copia Efferente Distorta / Rumore)
    s_pred_ablation = np.random.normal(0, 1.0, size=n_steps)
    res_base = calculate_thermodynamic_valence(x_A1, s_obs, s_pred, dt)
    res_abl = calculate_thermodynamic_valence(x_A1, s_obs, s_pred_ablation, dt)
    
    # --- CREAZIONE DASHBOARD GRAFICA ---
    fig = plt.figure(figsize=(16, 10))
    gs = fig.add_gridspec(2, 2, hspace=0.35, wspace=0.25)
    
    fig.suptitle(r"La Valenza Termodinamica $\Psi(t)$ Crolla sotto Ablazione dell'Efferenza",
                 fontsize=16, fontweight='bold', y=0.98)
    
    # Plot 1: Serie Temporale della Valenza Psi(t)
    ax1 = fig.add_subplot(gs[0, 0])
    sns.lineplot(x=t_sub, y=psi_series, ax=ax1, color='#0173B2', linewidth=2, label=r'$\Psi(t)$ Valenza Allostasica')
    ax1.axhline(np.mean(psi_series), color='red', linestyle='--', label=f'Media: {np.mean(psi_series):.2f}')
    ax1.set_title(r'Evoluzione Temporale della Valenza $\Psi(t)$', fontsize=12, fontweight='bold')
    ax1.set_xlabel('Tempo (s)')
    ax1.set_ylabel(r'Valenza $\Psi(t)$ (u.a.)')
    ax1.legend(loc='lower right')
    
    # Plot 2: Spazio delle Fasi (Edge of Chaos)
    ax2 = fig.add_subplot(gs[0, 1])
    dx = np.gradient(x_A1, dt)
    ax2.plot(x_A1, dx, color='#DE8F05', alpha=0.6, linewidth=0.8)
    ax2.scatter([x_A1[0]], [dx[0]], color='green', s=50, label='Inizio')
    ax2.scatter([x_A1[-1]], [dx[-1]], color='red', s=50, label='Fine')
    ax2.set_title(r'Traiettoria nello Spazio delle Fasi ($x$ vs $\dot{x}$)', fontsize=12, fontweight='bold')
    ax2.set_xlabel('Stato Fisico $x(t)$ (Memristore)')
    ax2.set_ylabel('Derivata $dx/dt$')
    ax2.legend()
    
    # Plot 3: Dissipazione Hatano-Sasa (Housekeeping vs Excess)
    ax3 = fig.add_subplot(gs[1, 0])
    sns.lineplot(x=t_sub, y=ex_series, ax=ax3, color='#029E73', label=r'$\sigma_{ex}$ (Dissipazione in Eccesso)')
    sns.lineplot(x=t_sub, y=hk_series, ax=ax3, color='#D55E00', label=r'$\sigma_{hk}$ (Housekeeping Entropy)')
    ax3.set_title('Decomposizione Termodinamica NESS', fontsize=12, fontweight='bold')
    ax3.set_xlabel('Tempo (s)')
    ax3.set_ylabel('Produzione di Entropia')
    ax3.legend()
    
    # Plot 4: Confronto Controllo Negativo (Ablazione 4)
    ax4 = fig.add_subplot(gs[1, 1])
    categories = ['Baseline ($A_1+A_2$)', 'Ablazione 4 (No Efferenza)']
    values = [res_base['psi_valenza'], res_abl['psi_valenza']]
    colors = ['#0173B2', '#CC78BC']
    bars = ax4.bar(categories, values, color=colors, width=0.5)
    for bar in bars:
        yval = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2.0, yval / 2.0, f'{yval:.2f}',
                 ha='center', va='center', color='white', fontweight='bold', fontsize=12)
    ax4.set_title('Verifica Controllo Negativo (Ablazione Efferenza)', fontsize=12, fontweight='bold')
    ax4.set_ylabel(r'Valenza Integrata $\Psi(t)$')
    
    sns.despine(fig=fig)
    output_path = os.path.join(OUTPUT_DIR, 'dashboard_valenza.png')
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Dashboard generata con successo in: {output_path}")

if __name__ == "__main__":
    generate_metrology_dashboard()
