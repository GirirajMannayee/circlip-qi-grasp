"""Candidate-selection Monte-Carlo (Sec. 5.3, Table 15, Fig. 18).

2,000 sets of 16 candidates x 5 uniform features (NumPy default_rng(43)).
The manuscript states the original random-stream layout was not archived and that regenerated
rates move by ~1-2 points while the method ordering is preserved; this module fixes the layout
(one `rng.random((n_sets, 16, 5))` draw, then one `rng.permuted` call for the random-subset arm)
so that results are bit-for-bit reproducible from here on.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from .core import N, WEIGHTS, soft_phases, hard_phases, amplitude_search

METHODS = ["Exhaustive argmax", "Greedy (position only)", "Random subset (8 evals)",
           "QI hard K = 3", "QI soft K = 2", "QI soft K = 3"]
EVALS = [16, 16, 8, 16, 16, 16]


def generate_sets(n_sets: int = 2000, seed: int = 43) -> np.ndarray:
    return np.random.default_rng(seed).random((n_sets, N, 5))


def run(n_sets: int = 2000, seed: int = 43) -> pd.DataFrame:
    F = generate_sets(n_sets, seed)
    rng = np.random.default_rng(seed + 1000)
    U = 1.0 - F @ WEIGHTS
    best = U.max(axis=1)
    top3 = np.sort(U, axis=1)[:, -3]
    sel = {m: np.empty(n_sets, int) for m in METHODS}
    for i in range(n_sets):
        u = U[i]
        sel[METHODS[0]][i] = np.argmax(u)
        sel[METHODS[1]][i] = np.argmin(F[i, :, 0])                      # lowest position error
        sub = rng.choice(N, size=8, replace=False)
        sel[METHODS[2]][i] = sub[np.argmax(u[sub])]
        sel[METHODS[3]][i] = np.argmax(amplitude_search(hard_phases(u), 3))
        sel[METHODS[4]][i] = np.argmax(amplitude_search(soft_phases(u), 2))
        sel[METHODS[5]][i] = np.argmax(amplitude_search(soft_phases(u), 3))
    rows = []
    for m, ev in zip(METHODS, EVALS):
        s = sel[m]; u_sel = U[np.arange(n_sets), s]; reg = best - u_sel
        rows.append({"Method": m, "Top-1 (%)": 100 * np.mean(u_sel >= best - 1e-12),
                     "Top-3 (%)": 100 * np.mean(u_sel >= top3 - 1e-12),
                     "Mean regret": reg.mean(), "95th-pct regret": np.percentile(reg, 95),
                     "Utility evals": ev})
    return pd.DataFrame(rows)


def binomial_ci_halfwidth(p_pct: float, n: int = 2000) -> float:
    p = p_pct / 100
    return 196 * np.sqrt(p * (1 - p) / n)
