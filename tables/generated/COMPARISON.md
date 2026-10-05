# Regenerated vs. manuscript

* **Table 20** (derived): relative changes identical to manuscript: **True**
* **Table 12**: depth / 2q gates / noisy P match to printed precision: **True**
* **Table 13** (λ, f, predicted): manuscript vs regenerated

| Configuration | λ (ms / regen) | f (ms / regen) | Pred. Pn (ms / regen) |
|---|---|---|---|
| Hard, K = 3 | 0.11 / 0.109 | 0.988 / 0.988 | 0.154 / 0.154 |
| Soft, K = 2 | 0.227 / 0.226 | 0.988 / 0.988 | 0.161 / 0.161 |
| Soft, K = 3 | 0.186 / 0.187 | 0.991 / 0.991 | 0.085 / 0.085 |

* **Table 15**: manuscript vs. regenerated top-1 (%) — the manuscript notes its random-stream layout was not archived, so 1–2 point differences are expected

| Method | Top-1 ms | Top-1 regen | Top-3 ms | Top-3 regen | Mean regret ms | regen | Evals |
|---|---|---|---|---|---|---|---|
| Exhaustive argmax | 100.0 | 100.0 | 100.0 | 100.0 | 0.0 | 0.0000 | 16 |
| Greedy (position only) | 24.3 | 24.6 | 54.0 | 53.5 | 0.1077 | 0.1066 | 16 |
| Random subset (8 evals) | 48.2 | 50.7 | 90.5 | 88.6 | 0.0445 | 0.0414 | 8 |
| QI hard K = 3 | 100.0 | 100.0 | 100.0 | 100.0 | 0.0 | 0.0000 | 16 |
| QI soft K = 2 | 99.9 | 100.0 | 99.9 | 100.0 | 0.0 | 0.0000 | 16 |
| QI soft K = 3 | 95.0 | 94.8 | 97.2 | 97.3 | 0.002 | 0.0020 | 16 |
