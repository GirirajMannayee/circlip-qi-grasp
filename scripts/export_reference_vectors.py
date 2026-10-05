#!/usr/bin/env python3
"""Export reference vectors for the Rust cross-check (data/reference/*.csv).

reference_vectors.csv: 80 features | P(hard,K=3)x16 | P(soft,K=2)x16 | P(soft,K=3)x16 | idx argmax, hard3, soft2, soft3
First record = the seed-42 candidate set of the manuscript; remaining 499 from default_rng(7).
"""
import pathlib, numpy as np
from qi_grasp import *

ROOT = pathlib.Path(__file__).resolve().parents[1] / "data" / "reference"; ROOT.mkdir(parents=True, exist_ok=True)
sets = [candidate_set_seed42()] + list(np.random.default_rng(7).random((499, N, 5)))
np.savetxt(ROOT / "seed42_features.csv", sets[0], delimiter=",", fmt="%.17g")
rows = []
for f in sets:
    U = utility(f)
    ph, ps = hard_phases(U), soft_phases(U)
    rows.append(np.concatenate([f.ravel(), amplitude_search(ph, 3), amplitude_search(ps, 2), amplitude_search(ps, 3),
                                [select(U, "argmax"), select(U, "hard", 3), select(U, "soft", 2), select(U, "soft", 3)]]))
np.savetxt(ROOT / "reference_vectors.csv", np.array(rows), delimiter=",", fmt="%.17g")
print("wrote", len(rows), "reference records")
