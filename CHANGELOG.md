# Changelog

All notable changes to this project are documented in this file. The format
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project
adheres to [Semantic Versioning](https://semver.org/) as far as applicable to
continuously evolving research software.

## [Unreleased]

## [0.4.0] - 2026-09-25

A second review of the code, with every finding verified by running it, and the
first change made through a pull request reviewed by CI and CodeRabbit.

### Changed
- **Condition 3 (state-dependent dynamics) is calibrated against a null.** With
  the fixed threshold theta_state = 0.25 alone, estimation noise made a linear
  system pass in 20 of 20 runs at 1000 samples, 14/20 at 3000 and 7/20 at 6000.
  The statistic must now also exceed the chosen percentile of its distribution on
  linear surrogates (residual bootstrap of the best linear model). Measured false
  positives: 2/20, 1/20, 1/20; detection of a double well: 0/20, 9/20, 19/20 at
  1000, 3000, 6000 samples. This is a declared deviation from the papers, which
  specify theta_state alone; `n_null=0` reproduces their criterion. Short records
  cannot support the condition, whatever the threshold.
- **The k-NN information estimates dither quantized data** (Kraskov et al. 2004).
  On data with repeated values, as from an ADC, independent variables rounded to
  0.1 gave 0.19 nats (-3.8 when rounded to 1.0), and a rounded AR(1) process
  showed 1.5-2.4 nats of spurious memory. With the seeded dither they give about
  0, while dependence and nonlinear memory are still detected. `jitter=False`
  disables it.
- `calculate_thermodynamic_valence` (Python and Rust) accepts explicit niche
  samples; the PyO3 module exposes `calculate_valence_with_niche_rust`.
- The Rust k-NN estimators use partial selection instead of full sorts: same
  results, binary run time from 21 s to 3 s.
- `simulate_neuromorphic_substrate_sde` uses a local generator: identical output,
  the caller's global NumPy state is no longer changed.
- The mock instruments use seeded generators.

### Added
- Unit tests for the Rust engine (there were none): k-NN KL estimates against
  closed-form values, delay embedding, ablation, input checks.
- `test_engine_parity.py`: the Python and Rust engines return the same numbers
  (9 decimal places) for the same inputs. The two engines draw random numbers from
  different generators, so they simulate different series for the same seed;
  "same engine" in the documentation meant same formulas.
- Tests that the real-instrument paths fail explicitly and release the instruments.
- CI: ruff, a coverage report, `cargo test`, the parity test against a freshly
  built wheel, and a Docker build. `.coderabbit.yaml` for automated review.

### Fixed
- `docker-compose.yml` ran `dashboard_valenza.py`, renamed in v0.2.0.
- PicoScope with `mock=False` answered "MOCK_PICOSCOPE" and returned None; it now
  raises NotImplementedError.
- **The real Keithley path now raises NotImplementedError too.** It had never run
  against an instrument, and review (CodeRabbit, PR #1) found it wrong: the voltage
  limit was set with the overvoltage-protection command, which on the 2400 cannot
  be 1.5 V; `:TRACE:DATA?` was parsed as currents while the default format
  interleaves five quantities; no acquisition was configured or started; and the
  instrument stayed open when connect() failed. The class docstring lists what a
  real driver must do. The interface releases the instruments when initialisation
  fails.
- Input checks: infinite `dt`, niche samples of the wrong shape (Python) or not
  finite (Rust), and non-integer or NaN `n_null` are rejected; fixed region indices
  are rejected with a surrogate null (they do not carry over to the surrogates;
  pass a partition rule instead). The dither centres the data first, so it also
  breaks ties next to large offsets.
- CI fails if the parity test would be skipped; `build_exe.ps1` stops if
  PyInstaller fails instead of reporting an older executable as a new build.
- `paper0 test` in the standalone executable could not find the test modules,
  which PyInstaller does not detect; `build_exe.ps1` could package a stale wheel
  left in `dist_wheel`.

## [0.3.0] - 2026-09-25

This release follows a conformance review of the code against the papers
(formula by formula). The review found that the operational demarcation of the
programme was not implemented, and that the three functions presented as the
"demarcation tests" computed quantities different from those the papers define.

### Added
- `demarcation.py`: the three operational demarcation conditions of P0 section 3
  and P1 section 2.1 — causal non-separability (numerical rank of the response
  matrix against a linear superposition model), non-Markovian memory (conditional
  mutual information beyond Markov order k, Frenzel-Pompe k-NN estimator with
  k_NN = 4, against IAAFT surrogates) and state-dependent effective dynamics
  (least-squares Jacobians in three phase-space regions, theta_state = 0.25).
  Interpretation choices where the papers leave room are stated in the docstrings.
- `necessary_conditions.py`: criteria for three of the necessary conditions, as
  P1 defines them — edge of chaos (Re Y(j omega) < 0 in the band and a stable
  operating point), causal degeneracy (D_C with rank_delta and effective rank, the
  robust radius rho_deg and prediction B.15; Appendix B) and exponent stability at
  the three largest sizes with the 30%/50% feasibility limits (Appendix D).
- `synthetic_systems.py`: systems with a known answer (AR(1), nonlinear lag-5
  process, linear system, double well, response matrices), shared by tests, CLI
  and notebook.
- Tests on known-answer cases: `test_demarcation.py`, `test_necessary_conditions.py`;
  the k-NN KL estimator against closed-form Gaussian values; the 1/f noise
  generator (standard deviation and spectral slope); input validation.
- CLI: `paper0_cli.py demarcation` now runs the three demarcation conditions;
  new `paper0_cli.py conditions` runs the necessary-condition criteria. The
  surrogate settings are reduced by default and configurable to the protocol's
  100 surrogates and 99th percentile.
- Continuous integration (GitHub Actions): tests on Python 3.11 and 3.12, the CLI
  demonstrations, and the Rust build.
- `notebooks/demo.ipynb`, runnable on Binder.

### Changed
- `demarcation_tests.py` is now a compatibility module that re-exports the new
  functions and emits a DeprecationWarning. **Breaking:** its former functions
  `test_edge_of_chaos_admittance`, `calculate_spectral_causal_degeneracy` and
  `verify_finite_size_scaling` are removed (see Fixed).
- `lib.rs` (PyO3 module) calls the engine of `thermodynamic_valence.rs` instead of
  its own simulation and placeholder estimators; it returns the same numbers as
  the binary.
- The 1/f noise generator and the mock carrier are extracted from the mock DMM
  (`generate_1f_noise`, `mock_dmm_carrier`), and the mock is seedable.

### Fixed
- The former edge-of-chaos test could never pass with its default parameters
  (Re Y > 0 for every frequency), and its stability Jacobian was a hard-coded
  constant unrelated to the model: the CLI always printed "Edge of Chaos
  Verified: False".
- The former "spectral causal degeneracy" used eigenvalues of a square matrix,
  counted the kernel with a spurious +1 and applied a threshold not in the papers.
- The former finite-size scaling check generated its data from the scaling law it
  was meant to verify.
- `calculate_thermodynamic_valence` returned numbers without error for series of
  unequal length, series too short for the delay embedding, and dt = 0 (NaN); the
  KL estimator divided by zero on empty input. They now raise ValueError (Python)
  or panic with a message (Rust).
- `test_noise_calibration_edge_of_chaos` measured the deterministic carrier as
  noise and failed deterministically; it now measures the fluctuations relative to
  the known carrier. The whole test suite passes.
- The READMEs, `CITATION.cff` and `PROJECT_STRUCTURE.md` called three necessary
  conditions "the operational demarcation tests".

## [0.2.1] - 2026-09-24

### Fixed
- `G_pred` did not follow its definition in the self-agency paper
  (P2_SelfAgency.tex, section 5.4), `D_KL(p_obs || p_ref) - D_KL(p_obs || p_pred)`.
  The code computed `D_KL(p_obs || p_target) - D_KL(p_pred || p_target)`, which
  scores the efference-copy prediction by its closeness to the target niche instead
  of to the observations. Because the niche is centred on 0 and the simulated state
  is not, noise centred on 0 looked "closer to the niche" than the correct
  prediction: this is why the dashboard's ablated condition scored higher than
  baseline (about -0.9 vs -2.1). With the P2 definition the ablation lowers `G_pred`
  and `Psi` (dashboard: 1.95 baseline vs -0.18 ablated), in both
  `thermodynamic_valence.py` and `thermodynamic_valence.rs`. The fix follows the
  specification; it was not tuned to obtain the predicted direction.
- The target niche was redrawn without a seed at every call in the Python engine,
  adding run-to-run noise to `d_kl_allostatic` and `G_pred`. It is now drawn from a
  fixed seed (`niche_seed=12345`, as the Rust engine already did), so equal inputs
  give equal outputs.
- The dashboard ablation drew unseeded random numbers; it is now seeded.
- The dashboard labelled the efference-copy ablation "Ablation 4", but in the papers
  Ablation (Control) 4 is the hard-wired Braitenberg vehicle. It is now labelled
  "Efference ablation (A2 decoupled)".
- `s_obs[0]` and `s_pred[0]` were left at 0 while the state started at 0.1; they
  now hold the initial state.

### Changed
- `G_pred` is estimated on two-dimensional delay-embedded densities
  `(s(t), s(t - tau))`, `tau_steps=10` by default, matching the "phase-space
  densities" of P2 section 5.4. New helpers: `delay_embed` (Python and Rust) and
  `estimate_kl_divergence_knn_2d` (Rust). Numerical values of `G_pred` and `Psi`
  change accordingly and are not comparable with v0.2.0.

### Added
- Regression tests: an ablation centred on the niche must lower `G_pred` and `Psi`;
  the valence computation must be deterministic.

## [0.2.0] - 2026-09-24

### Added
- Multilingual READMEs: `README.md` (English, now the default), `README.it.md`
  (Italian), `README.zh.md` (Chinese), cross-linked at the top of each.

### Changed
- Translated the entire codebase and repository documentation to English
  (previously Italian): filenames, docstrings, comments, CLI output strings,
  argparse help text, and CLI subcommand names
  (`metrologia`→`metrology`, `demarcazione`→`demarcation`, `tutti`→`all`).
- Renamed `valenza_metrologia.py` → `thermodynamic_valence.py`,
  `valenza_metrologia.rs` → `thermodynamic_valence.rs`,
  `dashboard_valenza.py` → `valence_dashboard.py`,
  `dashboard_valenza.png` → `valence_dashboard.png`,
  `test_valenza_metrologia.py` → `test_thermodynamic_valence.py`.
- Renamed the Rust package/binary/PyO3 module accordingly in `Cargo.toml`
  (`valenza_metrologia` → `thermodynamic_valence`,
  `valenza_metrologia_rust` → `thermodynamic_valence_rust`).
- Renamed the result dictionary keys `d_kl_allostasica`→`d_kl_allostatic` and
  `psi_valenza`→`psi_valence` across all Python/Rust implementations and their
  consumers, for consistency with the English codebase.

### Removed
- `hardware_driver.py` (v1): dead code, never imported by any script in the
  repository — fully superseded by `hardware_driver_v2.py`.

### Fixed
- Spurious Milstein correction in the SDE integrators (`thermodynamic_valence.py`,
  `thermodynamic_valence.rs`, `lib.rs`): with additive noise the correction
  `0.5*g*g'*(dW**2 - dt)` vanishes because `g' = 0`, but the code added
  `0.5*sigma**2*(dW**2 - dt)`. The integrators are now Euler-Maruyama, as they
  should be for additive noise (Higham 2001).
- `lib.rs` computed the variance of the finite-difference velocity around the mean
  of the *state* instead of the mean of the velocity.
- The stored initial state `x_A1[0]` was 0 while the integration started from 0.1,
  producing a spurious first derivative of 0.1/dt (the spike at the start of the
  dashboard's phase-space and `sigma_hk` panels). All three engines now store the
  actual initial state.
- The dashboard title claimed that `Psi` "collapses under efference ablation", but
  the dashboard's own bar chart shows the ablated condition with a *higher* `Psi`
  than baseline (about -0.9 vs -2.1), both before and after the fixes above. The
  title now just names the comparison; the discrepancy is listed below.
- The SDE noise was labelled "1/f percolative noise" but is white Gaussian noise.
  The genuine 1/f generator is the one in `hardware_driver_v2.py`.
- Documentation overclaim: README (all three languages), docstrings, CLI output and
  dashboard labels presented `sigma_hk` / `sigma_ex` as Hatano-Sasa housekeeping /
  excess entropy production. They are heuristic proxies: `sigma_hk` scales as
  `sigma_noise**2/dt`, so `Psi` depends on the integration step, and the true
  housekeeping rate of the one-variable model is identically zero. The labels now
  say so; the numerical definitions of the proxies are unchanged.
- Terminology typo "sentienza" → "senzienza" (correct Italian) in `README.it.md`
  and (previously) `AGENTS.md`.
- Broken README references to files excluded from the public repository
  (`docs_v0.2/...`, `report_campagna_rumore_p0.pdf`).

## [0.1.0] - 2026-09-22

### Added
- Python metrology digital twin (`valenza_metrologia.py`, later renamed) and its
  Rust counterpart (`valenza_metrologia.rs`, `lib.rs` via PyO3).
- Operational demarcation tests (`demarcation_tests.py`): edge of chaos, spectral
  causal degeneracy, finite-size scaling.
- Mock hardware drivers for Keithley DMM / PicoScope (`hardware_driver.py`,
  `hardware_driver_v2.py`).
- 4-quadrant visualization dashboard (`dashboard_valenza.py`, later renamed).
- Test suite (`test_valenza_metrologia.py`, `test_hardware_session.py`).
- Containerization (`Dockerfile`, `docker-compose.yml`) and installers
  (`install.sh`, `install.ps1`).
- Single CLI entry point (`paper0_cli.py`) and standalone PyInstaller build
  (`build_exe.ps1`), as an alternative to Docker for lab use.
- Dual MIT/Apache-2.0 license, `CITATION.cff`, packaging documentation.

### Fixed
- Broken import in `test_hardware_session.py` (renamed `hardware_driver-v2.py` →
  `hardware_driver_v2.py`).
- Ambiguous Rust type in `valenza_metrologia.rs`/`lib.rs` (`x_val` without an
  annotation).
- `Cargo.toml` did not wire `lib.rs` into the PyO3 build (missing `[lib]` +
  `pyo3` dependency).
- Missing dependencies (`matplotlib`, `seaborn`) in the installation scripts.
- Hardcoded `/workspace/...` paths in `dashboard_valenza.py` and
  `test_valenza_metrologia.py`, replaced with relative/`cwd`-based paths.
- 1/f noise generator in `hardware_driver_v2.py` that amplified the DC
  component, producing degenerate signals (zero mean/NaN).

### Known, unresolved
- No thermodynamically meaningful estimator of the housekeeping / excess entropy
  production is implemented yet. A candidate for linear Langevin systems with at
  least two coupled state variables is Sekizawa, Ito & Oizumi, Phys. Rev. X 14,
  041003 (2024). More generally, additive-noise Langevin models of nonlinear
  electronic circuits are thermodynamically inconsistent beyond the Gaussian
  (small-fluctuation) level (Falasco & Esposito, Rev. Mod. Phys. 97, 015002, 2025).
- ~~`lib.rs` uses placeholder estimators~~: resolved in 0.3.0.
- The papers set the highest Markov order of the non-Markovian memory condition to
  k_max = 500. A k-nearest-neighbour estimator cannot work in that many
  dimensions; `non_markovian_memory` takes k_max as a parameter (default 5) and
  truncates the past beyond order k to `past_lags` lags. The same limit applies to
  the protocol, not only to the software.
- Condition 1 of the demarcation takes the linear superposition model R_lin as
  input; fitting it to an impulse response is not implemented.
- `degeneracy_radius` samples directions in K_delta, so it returns an upper bound
  of the supremum that defines rho_deg.
- ~~The digital twin does not reproduce the predicted drop of `Psi` under efference
  ablation~~: resolved in 0.2.1 (wrong `G_pred` formula, see above).
- `G_pred` compares densities estimated separately for observations and
  predictions, so it cannot detect whether a prediction is aligned in time with the
  observations: a prediction shifted by 200 steps scores the same as the correct
  one, and a shuffled prediction only slightly lower, for any tested `tau_steps`
  (1-200). The same holds for the definition in P2 section 5.4, where temporal
  alignment is covered only by the joint requirement on transfer entropy, which the
  digital twin does not implement.
- In the simulation, level A2 does not feed back into A1: the efference-copy
  prediction never enters the dynamics. Ablating it changes the measurement, not
  the behaviour of the simulated substrate, so the digital twin cannot test the
  closed-loop prediction of the protocol.
- ~~`test_noise_calibration_edge_of_chaos` fails deterministically~~: resolved
  in 0.3.0.
- No real-instrument driver is implemented (Keithley, PicoScope): only the mocks.
