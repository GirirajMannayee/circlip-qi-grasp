# Manuscript → repository map

Evidence type: **E** executed here · **D** designed benchmark (not measured) · **S** schematic / static · **P** planned (Gate 4).

## Figures
| Fig | Content | Evidence | Where |
|---|---|---|---|
| 1 | Hybrid architecture | S | `figures/manuscript_originals/Fig01_original.png` |
| 2 | 16-candidate model + utility | E | `figures/generated/Fig02_candidates.*` (`make_figures.py`) |
| 3 | Seating geometry / tilt | S | original (`Fig03_original.png`); maths in `python/qi_grasp/force.py::tilt_deg`, `rust/src/tilt.rs` |
| 4 | Two-stage formulation | S | original |
| 5 | Force loop (a block diagram, b step response) | S / E | 5b: `Fig05b_force_step.*`; 5a: original; Rust: `qi-grasp step-response` |
| 6 | Operator sequence + probability insets | E | `Fig06_operator_sequence.*` |
| 7 | 4-qubit circuit (a block, b gates) | S / E | 7b: `Fig07b_circuit_gate_level_K1.*`; 7a: original |
| 8 | Noisy P vs. 2-qubit gate count | E | `Fig08_noise_attenuation.*` |
| 9 | Experimental configuration | S | original |
| 10 | Evidence gates | S | `Fig10_evidence_gates.*` |
| 11 | Quirk circuit K = 3 | E | `Fig11_quirk_style_circuit_K3.*`, `circuits/qio_quirk_circuit_K3.json`, `circuits/qio_quirk_url.txt` |
| 12 | FakeManilaV2 + transpiled cost | E | `Fig12_device_and_cost.*` (device values read live from the backend snapshot) |
| 13 | QIO-Rust architecture | S | original; implementation = `rust/` |
| 14 | 360-trial study design | S / P | `Fig14_study_design.*`, `stats/` |
| 15 | Probabilities K = 0–3 | E | `Fig15_probabilities_K0-3.*` |
| 16 | P(best) vs. K | E | `Fig16_probability_vs_K.*` |
| 17 | FakeManilaV2 noise test | E | `Fig17_noise_test.*` |
| 18 | Monte-Carlo comparison | E | `Fig18_montecarlo.*` |
| 19–24 | Controller, heat map, orientation, optimizer, ablation, relative change | **D** | `Fig19`…`Fig24` (each labelled "DESIGNED – not measured") |

All generated figures: PNG (300 dpi), PDF and SVG (Table 21 asks for vector formats).

## Tables
| Table | Evidence | Where |
|---|---|---|
| 1–11, 21 | S | verbatim in `tables/manuscript/TableNN.csv` |
| 5, 6, 7, 9, 10 | S | same; machine-readable versions of the settings are in `config/controller.yaml`, `docs/trial_log_schema.md` |
| 12 | E | `tables/generated/Table12.*` ← `data/results/noise_runs.json` |
| 13 | E | `Table13.*` (global-depolarizing fit, Eq. 13) |
| 14 | E | `Table14.*` (original vs. re-run) |
| 15 | E | `Table15.*` ← `data/results/montecarlo.csv` (Python) and `data/results/rust_montecarlo.txt` (Rust) |
| 16–19 | **D** | `data/designed_benchmark/` and `tables/generated/Table16–19.*` |
| 20 | derived from D | `Table20.*`, recomputed from Table 16 (matches the manuscript) |
| – | E | `tables/generated/weight_sensitivity.csv` (the ±20 % check recommended in Sec. 3.1) |
| – | | `tables/generated/COMPARISON.md`: regenerated vs. printed numbers |

## Equations → code
| Eq. | Python (`python/qi_grasp/`) | Rust (`rust/src/`) |
|---|---|---|
| (1)–(2) | `core.cost`, `core.utility` | `cost::cost_of`, `cost::utilities` |
| (3) | `force.tilt_deg` | `tilt::tilt_rad` |
| (6) admissible set | `core.select(valid=…)` | `select::Request::valid` |
| (9) PI law | `force.simulate_pi` | `force::Pi` |
| (10)–(12) | `core.amplitude_search`, `soft_phases`, `hard_phases` | `amplitude::{evolve, probabilities, soft_phases, hard_phases}` |
| (11) | `core.grover_p` | `amplitude::grover_p` |
| (13) | `noise.depolarizing_fit`, `predicted_noisy`, `g_max_for_threshold` | – |
| App. B.1 / B.2 / B.3 / B.4 / B.5 | `core`, `circuits.build_circuit/build_gate_level`, – , `circuits.quirk_json`, `circuits.gate_level_qasm2` | `amplitude::select_grasp` |
