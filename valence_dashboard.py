"""
valence_dashboard.py
=====================
Metrology visualization dashboard generator (Digital Twin P0_Distilled v0.1)

Generates:
1. Time series of the valence functional Psi(t) and of the Ex/Hk dissipation proxies.
2. Phase-space trajectory (x(t) vs dx/dt) with the edge-of-chaos region.
3. Comparison diagram between the baseline condition and an efference-copy ablation
   (A2 decoupled). This is not Ablation/Control 4 of the papers, which is the
   hard-wired Braitenberg vehicle.
"""

import os
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

# BASE_DIR is only used for sys.path (importing thermodynamic_valence when the
# script runs standalone). If packaged with PyInstaller, __file__ points inside
# the app's internal folder (_internal): the output must NOT end up there, but
# in the user's current working directory, like for any other command-line
# executable.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.environ.get('OUTPUT_DIR', os.path.join(os.getcwd(), 'output'))
sys.path.append(BASE_DIR)
from thermodynamic_valence import simulate_neuromorphic_substrate_sde, calculate_thermodynamic_valence  # noqa: E402

def generate_metrology_dashboard():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    sns.set_theme(style='whitegrid', palette='colorblind', font='DejaVu Sans')

    # 1. Baseline simulation
    n_steps = 2000
    x_A1, s_obs, s_pred, dt = simulate_neuromorphic_substrate_sde(n_steps=n_steps, seed=42)
    time_vec = np.arange(n_steps) * dt

    # Valence computed on a moving window
    window = 100
    psi_series = []
    ex_series = []
    hk_series = []

    for i in range(window, n_steps, 20):
        sub_x = x_A1[i-window:i]
        sub_obs = s_obs[i-window:i]
        sub_pred = s_pred[i-window:i]
        res = calculate_thermodynamic_valence(sub_x, sub_obs, sub_pred, dt)
        psi_series.append(res['psi_valence'])
        ex_series.append(res['sigma_ex'])
        hk_series.append(res['sigma_hk'])

    t_sub = time_vec[window::20]

    # 2. Efference-copy ablation (A2 decoupled): the prediction is replaced by noise
    # Seeded, so that the comparison is reproducible between runs.
    s_pred_ablation = np.random.default_rng(2026).normal(0, 1.0, size=n_steps)
    res_base = calculate_thermodynamic_valence(x_A1, s_obs, s_pred, dt)
    res_abl = calculate_thermodynamic_valence(x_A1, s_obs, s_pred_ablation, dt)

    # --- BUILD THE GRAPHICAL DASHBOARD ---
    fig = plt.figure(figsize=(16, 10))
    gs = fig.add_gridspec(2, 2, hspace=0.35, wspace=0.25)

    fig.suptitle(r"Thermodynamic Valence $\Psi(t)$: Baseline vs Efference Ablation",
                 fontsize=16, fontweight='bold', y=0.98)

    # Plot 1: Time series of the valence Psi(t)
    ax1 = fig.add_subplot(gs[0, 0])
    sns.lineplot(x=t_sub, y=psi_series, ax=ax1, color='#0173B2', linewidth=2, label=r'$\Psi(t)$ Allostatic Valence')
    ax1.axhline(np.mean(psi_series), color='red', linestyle='--', label=f'Mean: {np.mean(psi_series):.2f}')
    ax1.set_title(r'Time Evolution of the Valence $\Psi(t)$', fontsize=12, fontweight='bold')
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel(r'Valence $\Psi(t)$ (a.u.)')
    ax1.legend(loc='lower right')

    # Plot 2: Phase space (edge of chaos)
    ax2 = fig.add_subplot(gs[0, 1])
    dx = np.gradient(x_A1, dt)
    ax2.plot(x_A1, dx, color='#DE8F05', alpha=0.6, linewidth=0.8)
    ax2.scatter([x_A1[0]], [dx[0]], color='green', s=50, label='Start')
    ax2.scatter([x_A1[-1]], [dx[-1]], color='red', s=50, label='End')
    ax2.set_title(r'Phase-Space Trajectory ($x$ vs $\dot{x}$)', fontsize=12, fontweight='bold')
    ax2.set_xlabel('Physical State $x(t)$ (Memristor)')
    ax2.set_ylabel('Derivative $dx/dt$')
    ax2.legend()

    # Plot 3: heuristic dissipation proxies (NOT Hatano-Sasa quantities; see thermodynamic_valence.py)
    ax3 = fig.add_subplot(gs[1, 0])
    sns.lineplot(x=t_sub, y=ex_series, ax=ax3, color='#029E73', label=r'$\sigma_{ex}$ proxy')
    sns.lineplot(x=t_sub, y=hk_series, ax=ax3, color='#D55E00', label=r'$\sigma_{hk}$ proxy ($dt$-dependent)')
    ax3.set_title('Heuristic Dissipation Proxies', fontsize=12, fontweight='bold')
    ax3.set_xlabel('Time (s)')
    ax3.set_ylabel('Proxy value (arb. units)')
    ax3.legend()

    # Plot 4: Negative control comparison (efference-copy ablation)
    ax4 = fig.add_subplot(gs[1, 1])
    categories = ['Baseline ($A_1+A_2$)', 'Efference ablation ($A_2$ decoupled)']
    values = [res_base['psi_valence'], res_abl['psi_valence']]
    colors = ['#0173B2', '#CC78BC']
    bars = ax4.bar(categories, values, color=colors, width=0.5)
    for bar in bars:
        yval = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2.0, yval / 2.0, f'{yval:.2f}',
                 ha='center', va='center', color='white', fontweight='bold', fontsize=12)
    ax4.set_title('Negative Control Verification (Efference Ablation)', fontsize=12, fontweight='bold')
    ax4.set_ylabel(r'Integrated Valence $\Psi(t)$')

    sns.despine(fig=fig)
    output_path = os.path.join(OUTPUT_DIR, 'valence_dashboard.png')
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Dashboard successfully generated at: {output_path}")

if __name__ == "__main__":
    generate_metrology_dashboard()
