#!/usr/bin/env python3
"""Fill the 360-trial log with SIMULATED values drawn around the manuscript's DESIGNED benchmark (Tables 16-17).

Outputs
  data/trial_log_planned.csv               design-only columns filled (order, session, ring, expansion cycle, frame id); measurements stay empty
  data/trial_log_designed_simulation.csv   every column filled; notes = 'SIMULATED ...'. NOT measurements - never merge with real trial data.

Model: controller means = Table 16; orientation multipliers = Table 17 (C4 row / its mean) applied to every controller;
gamma noise (CV 0.35) for positive skewed endpoints; success ~ Bernoulli with failure probability scaled by orientation.
Fixed seed => reproducible. Used by `stats/analysis.py --demo` as a realistic pipeline check.
"""
import numpy as np, pandas as pd, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
plan = pd.read_csv(ROOT / "data/trial_log_planned.csv", keep_default_na=False)
t16 = pd.read_csv(ROOT / "data/designed_benchmark/Table16.csv").set_index("Controller")
t17 = pd.read_csv(ROOT / "data/designed_benchmark/Table17.csv").set_index("Initial orientation")
key = {"C1": "C1 Fixed", "C2": "C2 Vision", "C3": "C3 Vision+Force", "C4": "C4 QI Vision+Force"}
ori_idx = {0: "0°", 30: "30°", 60: "60°"}
rng = np.random.default_rng(20261005)
mult = {c: t17[col] / t17[col].mean() for c, col in [("tilt", "Tilt (°)"), ("grasp", "Grasp error (mm)"), ("over", "Overshoot (%)"), ("slip", "Slip (mm)")]}
fail_o = (100 - t17["Success (%)"]); fail_mult = fail_o / fail_o.mean()
gam = lambda mean, cv=0.35: rng.gamma(1 / cv**2, mean * cv**2)

plan = plan.sort_values("run_order").reset_index(drop=True)
n = len(plan); cyc_cap = 10
plan["circlip_id"] = [f"R{(i // cyc_cap) + 1:03d}" for i in range(n)]
plan["expansion_cycle_no"] = [(i % cyc_cap) + 1 for i in range(n)]
plan["rgbd_frame_id"] = [f"F{i + 1:06d}" for i in range(n)]
plan.to_csv(ROOT / "data/trial_log_planned.csv", index=False)

ring_eff = {r: float(np.exp(rng.normal(0, 0.12))) for r in plan["circlip_id"].unique()}   # ring-to-ring random effect (multiplicative)
ring_dreq = {r: rng.normal(20.10, 0.02) for r in plan["circlip_id"].unique()}        # smallest clearing inner diameter, sleeve OD = 20 mm
openloop_cmd = {"C1": 20.0, "C2": 18.0}                                              # preset grip command without force regulation (N)
modes_open = ["slip", "excessive_tilt", "mis_seat_or_ejection", "grasp_point", "contact_force", "over_expansion"]
modes_ctrl = ["excessive_tilt", "mis_seat_or_ejection", "slip", "over_expansion"]
rows = []
for _, r in plan.iterrows():
    c, o = r["controller"], int(r["init_orientation_deg"]); d = t16.loc[key[c]]; oi = ori_idx[o]
    p_fail = (100 - d["Success (%)"]) / 100 * fail_mult[oi]
    ok = rng.random() >= p_fail
    mode = "none" if ok else str(rng.choice(modes_open if c in ("C1", "C2") else modes_ctrl))
    tilt = gam(d["Tilt (°)"] * mult["tilt"][oi] * ring_eff[r["circlip_id"]]) * (2.2 if mode == "excessive_tilt" else 1.0)
    over = gam(d["Overshoot (%)"] * mult["over"][oi]) * (2.0 if mode == "over_expansion" else 1.0)
    slip = gam(d["Slip (mm)"] * mult["slip"][oi] * ring_eff[r["circlip_id"]]) * (2.5 if mode == "slip" else 1.0)
    dreq = ring_dreq[r["circlip_id"]]
    cyc = max(rng.normal(d["Time (s)"], 0.35), 4.0)
    rows.append({**r.to_dict(),
        "selected_candidate": -1 if c == "C1" else int(rng.integers(0, 16)),   # -1 = fixed grasp point, no selection
        "grasp_error_mm": round(gam(d["Grasp error (mm)"] * mult["grasp"][oi]), 3),
        "force_cmd_N": 14.0 if c in ("C3", "C4") else openloop_cmd[c],
        "force_peak_N": round(max(rng.normal(d["Peak force (N)"], 1.0 if c in ("C1", "C2") else 0.8), 5.0), 2),
        "expansion_Dreq_mm": round(dreq, 3), "expansion_Dpk_mm": round(dreq * (1 + over / 100), 3), "overshoot_pct": round(over, 3),
        "slip_mm": round(slip, 3), "seating_tilt_deg": round(tilt, 3), "assembly_success": int(ok),
        "release_time_s": round(cyc - 3.0, 2), "cycle_time_s": round(cyc, 2), "failure_mode": mode, "exclusion_flag": 0,
        "notes": "SIMULATED from designed benchmark (Tables 16-17); not a measurement"})
out = pd.DataFrame(rows)[list(pd.read_csv(ROOT / "data/trial_log_template.csv").columns)]
out.to_csv(ROOT / "data/trial_log_designed_simulation.csv", index=False)
s = out.groupby("controller").agg(success=("assembly_success", "mean"), tilt=("seating_tilt_deg", "mean"), grasp=("grasp_error_mm", "mean"),
    over=("overshoot_pct", "mean"), slip=("slip_mm", "mean"), peak=("force_peak_N", "mean"), time=("cycle_time_s", "mean")).round(2)
print(s.to_string()); print("rows", len(out), "blank cells", int((out.astype(str).apply(lambda c: c.str.strip() == "")).values.sum()))
