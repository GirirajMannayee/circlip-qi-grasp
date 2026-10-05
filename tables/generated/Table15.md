**Table 15. Executed candidate-selection performance on 2,000 synthetic sets (seed 43, layout fixed in this repo)**

| Method                  |   Top-1 (%) |   Top-3 (%) |   Mean regret |   95th-pct regret |   Utility evals |
|:------------------------|------------:|------------:|--------------:|------------------:|----------------:|
| Exhaustive argmax       |       100   |       100   |        0      |            0      |              16 |
| Greedy (position only)  |        24.6 |        53.5 |        0.1066 |            0.2896 |              16 |
| Random subset (8 evals) |        50.7 |        88.6 |        0.0414 |            0.1651 |               8 |
| QI hard K = 3           |       100   |       100   |        0      |            0      |              16 |
| QI soft K = 2           |       100   |       100   |        0      |            0      |              16 |
| QI soft K = 3           |        94.8 |        97.3 |        0.002  |            0.0136 |              16 |

*Regret = U(best) − U(selected). Binomial 95 % half-width on 2,000 sets ≈ ±2.2 pts at 50 %, ±1.0 at 95 %, ±0.4 at 99 %.*
