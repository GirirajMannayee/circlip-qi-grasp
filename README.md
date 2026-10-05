# Circlip-to-sleeve QI grasp selection — reproducibility package

Code, data, tables and figures for **"Quantum-Inspired Multi-Objective Grasp Optimization for Vision–Force Adaptive Circlip-to-Sleeve Assembly"**
(manuscript: `manuscript/Circlip_Sleeve_QI_Grasp.docx`). It implements the artifacts listed in the manuscript's Appendix C / Table 21.

> **Evidence status.** Gates 1–3 (reference optimizer, ideal circuit, FakeManilaV2 noise) are executed and reproduced here.
> Gate 4 (the 360-trial robot study) has **not** been run: Tables 16–20 and Figs 19–24 are *designed benchmarks*, labelled as such everywhere, and are not results.
> Rust latency for hypothesis H5 has only been measured on a development container, not on edge hardware. See [`docs/evidence_and_limits.md`](docs/evidence_and_limits.md).

## What reproduces (checked by `make all`)
| Claim in the manuscript | Reproduced value |
|---|---|
| Best candidate on the seed-42 set | p = 5, U = 0.725 |
| Hard oracle P(best), K = 0…6 | 0.062, 0.473, 0.908, **0.961**, 0.582, 0.125, 0.020 (= Grover law, max abs diff 1e-12) |
| Soft oracle (γ = 6) | 0.506 at K = 2, 0.280 at K = 3 |
| FakeManilaV2, hard oracle K = 3 (gate-level) | depth 277, 189 two-qubit gates, P = 0.161 ± 0.006, Hellinger 0.328 |
| FakeManilaV2, DiagonalGate / soft K = 2 / soft K = 3 | 280 / 187 / 280 depth; P = 0.163±0.008 / 0.163±0.007 / 0.103±0.005 |
| Global-depolarizing fit | f ≈ 0.988, 0.988, 0.991; g_max ≈ 60 at f = 0.988 |
| Force-loop overshoot at ζ = 0.5 / 0.7 / 1.0 / 1.5 | 29.8 / 21.0 / 13.5 / 7.6 % (manuscript: ≈ 30 / 21 / 14 / 8 %) |
| Table 15 ordering; argmax and hard K = 3 exact | yes (rates within ≈ 2.5 pts; see limits) |
| Rust core vs Python reference | max abs ΔP 5e-15 over 500 sets, 0 selection mismatches |

Full side-by-side: [`tables/generated/COMPARISON.md`](tables/generated/COMPARISON.md).

## Layout
```
manuscript/            the .docx this package accompanies
rust/                  QIO-Rust core (no dependencies): lib + `qi-grasp` CLI, 22 tests
python/qi_grasp/       reference implementation, Qiskit circuits, noise study, Monte-Carlo, force loop, sensitivity
python/tests/          12 tests (2 need the pinned Qiskit stack)
scripts/               one script per table/figure/export; `make` calls them
circuits/              Quirk JSON + URL, OpenQASM 2.0 (App. B.4, B.5)
data/reference/        seed-42 matrix and 500 Python reference vectors for the Rust cross-check
data/results/          executed results (JSON/CSV/TXT)
data/designed_benchmark/  Tables 16–20 — DESIGNED values, not measurements
data/trial_log_*.csv    template, planned run order (design columns filled) and a fully filled SIMULATED log (pipeline check only)
tables/manuscript/     all 21 tables transcribed verbatim from the .docx
tables/generated/      regenerated tables (CSV / Markdown / LaTeX) + COMPARISON.md + weight sensitivity
figures/generated/     regenerated figures (PNG 300 dpi, PDF, SVG)
figures/manuscript_originals/  the 24 figures as embedded in the manuscript (schematics are kept, not redrawn)
stats/                 pre-specified analysis (mixed model, binomial GLM, Tukey) + run-order randomiser
config/                controller and camera/F-T configs (design / nominal starting values, labelled as such)
docs/                  manuscript map, evidence & limits, statistics plan, trial-log schema
```

## Quick start
```bash
make setup      # pinned: qiskit 2.5.2, qiskit-aer 0.17.2, qiskit-ibm-runtime 0.50.0 (Python ≥ 3.10); Rust ≥ 1.74
make all        # reference vectors → noise runs → Monte-Carlo → circuits → tables → figures → Rust tests → cross-check
make test       # Python + Rust tests
make bench      # Rust latency on THIS machine
```
Rust CLI (after `cd rust && cargo build --release`):
```bash
./target/release/qi-grasp demo                                   # utilities, P(K), selection in every mode
./target/release/qi-grasp select --features ../data/reference/seed42_features.csv --mode soft --k 2 --valid 1111111111111111
./target/release/qi-grasp montecarlo --sets 2000 --seed 43
./target/release/qi-grasp bench --mode soft --k 2 --calls 100000 --watchdog-us 500
./target/release/qi-grasp verify --ref ../data/reference/reference_vectors.csv
```
Library use:
```rust
use qi_grasp::{select::{select, Mode, Request}, Features, N};
let resp = select(&Request { features: &features, valid: &[true; N], mode: Mode::SOFT_DEFAULT,
                             watchdog: Some(std::time::Duration::from_micros(500)) })?;
// resp.selected, resp.utility, resp.probability, resp.iterations, resp.elapsed_ns, resp.fallback
```

## Running the planned robot study
1. The randomised run order is already generated (seed 20261005, `data/trial_log_planned.csv`); regenerate with another seed if needed: `python stats/randomize_run_order.py --seed <seed>`.
2. Calibrate (replace the nominal values in `config/`), measure force window and ring opening force, replace the nominal Table 5 dimensions.
3. Record trials into `data/trial_log.csv` (start from `data/trial_log_planned.csv`; `trial_log_designed_simulation.csv` shows a fully filled example) (`docs/trial_log_schema.md`), failed trials included.
4. `python stats/analysis.py --data data/trial_log.csv` — then replace the designed values in Tables 16–20.

## Reproducibility notes
Seeds: candidate set `default_rng(42)`; Monte-Carlo `default_rng(43)`; transpiler seed 42, simulator seeds 42–51, 4096 shots, optimization level 1; Rust PRNG is xoshiro256** (different stream, so only exported vectors are compared across languages).
Before deposit: add co-authors, the repository URL and a DOI to `CITATION.cff` (they do not exist yet), and complete the manuscript's reference list as noted in its Sec. 7.
License: MIT (code); the manuscript text is not covered by this licence.
