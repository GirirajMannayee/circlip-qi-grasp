#!/usr/bin/env python3
"""Gate 1: candidate-selection study on 2,000 synthetic sets (Table 15, Fig. 18)."""
import pathlib
from qi_grasp.montecarlo import run
ROOT = pathlib.Path(__file__).resolve().parents[1]
df = run()
df.to_csv(ROOT / "data" / "results" / "montecarlo.csv", index=False)
print(df.round(4).to_string(index=False))
