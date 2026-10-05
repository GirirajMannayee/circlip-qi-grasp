#!/usr/bin/env python3
"""Regenerate computed tables (12, 13, 14, 15, 20) and re-emit the designed tables (16-19) as CSV/Markdown/LaTeX.
Output: tables/generated/. Also writes tables/generated/COMPARISON.md (regenerated vs. manuscript)."""
import json, pathlib
import numpy as np, pandas as pd
from qi_grasp.noise import depolarizing_fit, predicted_noisy
from qi_grasp.montecarlo import binomial_ci_halfwidth

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "tables" / "generated"; OUT.mkdir(parents=True, exist_ok=True)
noise = json.loads((ROOT / "data/results/noise_runs.json").read_text())
runs = noise["runs"]

def emit(df, name, caption, note=None):
    df.to_csv(OUT / f"{name}.csv", index=False)
    (OUT / f"{name}.md").write_text(f"**{caption}**\n\n{df.to_markdown(index=False)}\n" + (f"\n*{note}*\n" if note else ""))
    (OUT / f"{name}.tex").write_text(df.to_latex(index=False, escape=True, caption=caption, label=f"tab:{name.lower()}"))

pm = lambda m, s: f"{m:.3f} ± {s:.3f}"
gate, diag, s2, s3 = runs
# Table 12 -----------------------------------------------------------------------------------------------
t12 = pd.DataFrame([
    ["Hard", 3, f'{gate["ideal_p"]:.3f}', gate["depth"], gate["two_qubit_gates"], pm(gate["noisy_p_mean"], gate["noisy_p_sd"]), pm(gate["hellinger_mean"], gate["hellinger_sd"])],
    ["Soft (γ = 6)", 2, f'{s2["ideal_p"]:.3f}', s2["depth"], s2["two_qubit_gates"], pm(s2["noisy_p_mean"], s2["noisy_p_sd"]), pm(s2["hellinger_mean"], s2["hellinger_sd"])],
    ["Soft (γ = 6)", 3, f'{s3["ideal_p"]:.3f}', s3["depth"], s3["two_qubit_gates"], pm(s3["noisy_p_mean"], s3["noisy_p_sd"]), pm(s3["hellinger_mean"], s3["hellinger_sd"])],
], columns=["Oracle", "K", "Ideal P_target (exact)", "Transp. depth", "2-qubit gates", "Noisy P_target", "Noisy fidelity"])
emit(t12, "Table12", "Table 12. Executed circuit results (ideal and FakeManilaV2 noise)",
     "Hard row: gate-level X–CCCZ–X circuit. Candidate set: synthetic, seed 42. Hellinger fidelity vs. ideal distribution.")
# Table 13 -----------------------------------------------------------------------------------------------
rows = []
for lab, r in (("Hard, K = 3", gate), ("Soft, K = 2", s2), ("Soft, K = 3", s3)):
    lam, f = depolarizing_fit(r["ideal_p"], r["noisy_p_mean"], r["two_qubit_gates"])
    rows.append([lab, r["two_qubit_gates"], f"{lam:.3f}", f"{f:.3f}",
                 f'{predicted_noisy(r["ideal_p"], r["two_qubit_gates"], 0.988):.3f}'])
t13 = pd.DataFrame(rows, columns=["Configuration", "2q gates g", "λ = (Pn − 1/N)/(Pi − 1/N)", "Effective f = λ^(1/g)", "Predicted Pn at f = 0.988"])
emit(t13, "Table13", "Table 13. Global-depolarizing fit of Eq. (13) to Table 12")
# Table 14 -----------------------------------------------------------------------------------------------
orig = {"Hard, 3": (277, "0.161±0.006", "0.328"), "Soft, 2": (187, "0.163±0.007", "0.619"), "Soft, 3": (280, "0.103±0.005", "0.930")}
t14 = pd.DataFrame([
    ["Hard, 3", f'{orig["Hard, 3"][0]} / {diag["depth"]}', diag["two_qubit_gates"], f'{diag["ideal_p"]:.3f}', f'{orig["Hard, 3"][1]} / {diag["noisy_p_mean"]:.3f}±{diag["noisy_p_sd"]:.3f}', f'{orig["Hard, 3"][2]} / {diag["hellinger_mean"]:.3f}', "Yes" if diag["modal_best_all_seeds"] else "No"],
    ["Soft, 2", f'{orig["Soft, 2"][0]} / {s2["depth"]}', s2["two_qubit_gates"], f'{s2["ideal_p"]:.3f}', f'{orig["Soft, 2"][1]} / {s2["noisy_p_mean"]:.3f}±{s2["noisy_p_sd"]:.3f}', f'{orig["Soft, 2"][2]} / {s2["hellinger_mean"]:.3f}', "Yes" if s2["modal_best_all_seeds"] else "No"],
    ["Soft, 3", f'{orig["Soft, 3"][0]} / {s3["depth"]}', s3["two_qubit_gates"], f'{s3["ideal_p"]:.3f}', f'{orig["Soft, 3"][1]} / {s3["noisy_p_mean"]:.3f}±{s3["noisy_p_sd"]:.3f}', f'{orig["Soft, 3"][2]} / {s3["hellinger_mean"]:.3f}', "Yes" if s3["modal_best_all_seeds"] else "No"],
], columns=["Oracle, K", "Depth (orig / re-run)", "2q gates", "Ideal P_target", "Noisy P (orig / re-run)", "Hellinger fid. (orig / re-run)", "Modal outcome = best?"])
emit(t14, "Table14", "Table 14. Independent re-run versus original values",
     "'orig' values are those printed in the manuscript; 're-run' values are produced by this repository.")
# Table 15 -----------------------------------------------------------------------------------------------
mc = pd.read_csv(ROOT / "data/results/montecarlo.csv")
t15 = mc.copy()
for c in ("Top-1 (%)", "Top-3 (%)"): t15[c] = t15[c].map("{:.1f}".format)
for c in ("Mean regret", "95th-pct regret"): t15[c] = t15[c].map("{:.4f}".format)
emit(t15, "Table15", "Table 15. Executed candidate-selection performance on 2,000 synthetic sets (seed 43, layout fixed in this repo)",
     "Regret = U(best) − U(selected). Binomial 95 % half-width on 2,000 sets ≈ ±2.2 pts at 50 %, ±1.0 at 95 %, ±0.4 at 99 %.")
# Tables 16-19 (designed) ---------------------------------------------------------------------------------
cap = {16: "Table 16. Controller-level DESIGNED benchmark (not measured)", 17: "Table 17. Initial-orientation sensitivity under C4 (DESIGNED benchmark)",
       18: "Table 18. DESIGNED optimizer benchmark (not executed)", 19: "Table 19. DESIGNED ablation benchmark"}
for n, c in cap.items():
    emit(pd.read_csv(ROOT / f"data/designed_benchmark/Table{n}.csv"), f"Table{n}", c, "Designed value from the manuscript; not a measurement.")
# Table 20 (derived, recomputed from Table 16) ---------------------------------------------------------------
t16 = pd.read_csv(ROOT / "data/designed_benchmark/Table16.csv").set_index("Controller")
c1, c4 = t16.loc["C1 Fixed"], t16.loc["C4 QI Vision+Force"]
rows = []
for col, interp_hi in [("Success (%)", True), ("Grasp error (mm)", False), ("Tilt (°)", False), ("Overshoot (%)", False),
                       ("Slip (mm)", False), ("Peak force (N)", False), ("Time (s)", False)]:
    rel = (c4[col] - c1[col]) / c1[col] * 100
    rows.append([col.replace("Time", "Cycle time"), c1[col], c4[col], f"{rel:+.1f}%", "Higher" if rel > 0 else "Lower"])
emit(pd.DataFrame(rows, columns=["Outcome", "C1", "C4", "Relative change", "Interpretation"]), "Table20",
     "Table 20. Derived relative changes of C4 versus C1 (computed from the designed Table 16)")
# Comparison against the manuscript --------------------------------------------------------------------------
man = lambda n: pd.read_csv(ROOT / f"tables/manuscript/Table{n:02d}.csv")
lines = ["# Regenerated vs. manuscript\n"]
m20 = man(20); g20 = pd.read_csv(OUT / "Table20.csv")
ok20 = all(str(a).replace("−", "-") == str(b) for a, b in zip(m20["Relative change"].str.replace("−", "-"), g20["Relative change"]))
lines.append(f"* **Table 20** (derived): relative changes identical to manuscript: **{ok20}**")
m12 = man(12); lines.append(f"* **Table 12**: depth / 2q gates / noisy P match to printed precision: **"
    + str(all([(int(m12.iloc[i]["Transp. depth"]) == int(t12.iloc[i]["Transp. depth"]) and int(m12.iloc[i]["2-qubit gates"]) == int(t12.iloc[i]["2-qubit gates"]) and m12.iloc[i]["Noisy Ptarget"] == t12.iloc[i]["Noisy P_target"] and m12.iloc[i]["Noisy fidelity"] == t12.iloc[i]["Noisy fidelity"]) for i in range(3)])) + "**")
m13 = man(13); lines.append("* **Table 13** (λ, f, predicted): manuscript vs regenerated\n")
lines.append("| Configuration | λ (ms / regen) | f (ms / regen) | Pred. Pn (ms / regen) |\n|---|---|---|---|")
for i in range(3):
    lines.append(f'| {t13.iloc[i,0]} | {m13.iloc[i,2]} / {t13.iloc[i,2]} | {m13.iloc[i,3]} / {t13.iloc[i,3]} | {m13.iloc[i,4]} / {t13.iloc[i,4]} |')
m15 = man(15); lines.append("\n* **Table 15**: manuscript vs. regenerated top-1 (%) — the manuscript notes its random-stream layout was not archived, so 1–2 point differences are expected\n")
lines.append("| Method | Top-1 ms | Top-1 regen | Top-3 ms | Top-3 regen | Mean regret ms | regen | Evals |\n|---|---|---|---|---|---|---|---|")
for i in range(len(m15)):
    lines.append(f'| {m15.iloc[i,0]} | {m15.iloc[i,1]} | {t15.iloc[i,1]} | {m15.iloc[i,2]} | {t15.iloc[i,2]} | {m15.iloc[i,3]} | {t15.iloc[i,3]} | {m15.iloc[i,5]} |')
(OUT / "COMPARISON.md").write_text("\n".join(lines) + "\n")
print("\n".join(lines))
