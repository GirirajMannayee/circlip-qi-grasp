#!/usr/bin/env python3
"""Weight-sensitivity analysis recommended in Sec. 3.1 (+/-20 % per weight). Not part of the manuscript's reported results."""
import pathlib, pandas as pd
from qi_grasp.sensitivity import run
ROOT = pathlib.Path(__file__).resolve().parents[1]
df = pd.DataFrame(run()).drop(columns="renormalised")  # renormalising rescales all weights equally and cannot change argmax
df.to_csv(ROOT / "tables/generated/weight_sensitivity.csv", index=False); print(df.round(2).to_string(index=False))
