# Evidence status and known issues

* **Gates 1–3 are reproduced here** (Python reference, ideal statevector, FakeManilaV2 with the pinned Qiskit stack).
  Table 12 / 14 numbers reproduce exactly to the printed precision (depth 277/280, 189 two-qubit gates, noisy P = 0.161 ± 0.006 / 0.163 ± 0.008).
* **Gate 1 for the Rust build is now closed on the software side:** the crate compiles (stable, no dependencies), passes its unit/integration tests and
  agrees with the Python reference to max |ΔP| ≈ 5e-15 over 500 candidate sets with 0 selection mismatches (`make verify`).
  The manuscript sentence "The Rust listing has not yet been compiled or profiled" can be updated accordingly.
* **H5 (edge-hardware latency) stays open.** `data/results/rust_latency_dev_machine.txt` was measured on a 2-core cloud container, not the target
  hardware; use `make bench` on the device (median / p95 / p99.9 over ≥ 10⁵ calls, fallback rate). Note that on this CPU the amplitude search is *slower* than
  exhaustive argmax (≈ 0.4–0.7 µs vs. 0.14 µs), consistent with Proposition 3 / Sec. 6.2: no advantage.
* **Gate 4 (robot) is planned.** Tables 16–20 and Figs 19–24 are designed values. Nothing in this repository is a robot measurement.
* **Deviation from App. B.3 (documented):** the hard oracle marks the best *admissible* candidate (Eq. 2: argmax over 𝒜), so a collision mask cannot
  leave the oracle pointing at an excluded candidate. With an all-true mask the behaviour is identical to the manuscript.
* **Table 15:** the manuscript's random-stream layout was not archived. This repository fixes one (documented in `montecarlo.py`); the regenerated rates
  differ by up to ≈ 2.5 points (random-subset arm 50.7 % vs 48.2 %, within the ±2.2-point binomial interval), and the method ordering and the
  exactness of argmax / hard K = 3 are unchanged. The Rust PRNG is a different stream again, so its Table 15 numbers differ slightly too; cross-language parity is
  verified on exported vectors, not on random streams.
* **Table 19 inconsistency (flagged in the manuscript):** A1 carries C2's values and A3 ≠ C3. Kept as printed in `data/designed_benchmark/Table19.csv`.
* **Table 18 omits an exhaustive-argmax comparator** and is not an executed result. The executed comparison is Table 15.
* The soft oracle's K must be tuned (K = 2 here); `soft_phases` returns all-zero phases for constant utilities instead of dividing by zero.
