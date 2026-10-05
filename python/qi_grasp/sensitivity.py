"""Weight-sensitivity analysis recommended in Sec. 3.1 (+/-20 % per weight, record changes in p-hat).

Not part of the manuscript's reported results; provided so the recommended check can be attached
to the final submission.
"""
from __future__ import annotations
import numpy as np
from .core import WEIGHTS


def run(n_sets: int = 2000, seed: int = 43, delta: float = 0.20, renormalise: bool = False):
    F = np.random.default_rng(seed).random((n_sets, 16, 5))
    base = np.argmax(-(F @ WEIGHTS), axis=1)
    names = ["position", "orientation", "expansion", "force", "slip"]
    rows = []
    for j, nm in enumerate(names):
        for sgn in (-1, +1):
            w = WEIGHTS.copy(); w[j] *= 1 + sgn * delta
            if renormalise: w = w / w.sum()
            alt = np.argmax(-(F @ w), axis=1)
            rows.append({"weight": nm, "perturbation": f"{sgn*delta:+.0%}",
                         "renormalised": renormalise, "p_hat_changed_pct": 100 * float(np.mean(alt != base))})
    return rows
