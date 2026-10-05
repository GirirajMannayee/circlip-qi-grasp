**Table 12. Executed circuit results (ideal and FakeManilaV2 noise)**

| Oracle       |   K |   Ideal P_target (exact) |   Transp. depth |   2-qubit gates | Noisy P_target   | Noisy fidelity   |
|:-------------|----:|-------------------------:|----------------:|----------------:|:-----------------|:-----------------|
| Hard         |   3 |                    0.961 |             277 |             189 | 0.161 ± 0.006    | 0.328 ± 0.008    |
| Soft (γ = 6) |   2 |                    0.506 |             187 |             125 | 0.163 ± 0.007    | 0.619 ± 0.011    |
| Soft (γ = 6) |   3 |                    0.28  |             280 |             189 | 0.103 ± 0.005    | 0.930 ± 0.004    |

*Hard row: gate-level X–CCCZ–X circuit. Candidate set: synthetic, seed 42. Hellinger fidelity vs. ideal distribution.*
