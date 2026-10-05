#!/usr/bin/env python3
"""Pre-specified statistical analysis of the 360-trial study (Sec. 4.6, Table 9, Appendix A).

    python stats/analysis.py --data data/trial_log.csv --out stats/output
    python stats/analysis.py --demo                     # PIPELINE CHECK on synthetic placeholder data (NOT results)

Models
  continuous endpoints : endpoint ~ controller * orientation + (1 | circlip_id)   (statsmodels MixedLM, REML)
                         + partial eta^2 from the fixed-effects OLS ANOVA (Type II)
  assembly success     : binomial GLM  success ~ controller * orientation, cluster-robust SE by circlip_id
  primary contrast     : C4 vs C3 (selection + orientation correction), overall effect C4 vs C1
  post-hoc             : Tukey HSD on controller (fixed-effects; random effect not propagated - see docs/statistics.md)
Freeze and time-stamp this script BEFORE data collection.
"""
import argparse, pathlib, sys, hashlib, datetime, warnings
import numpy as np, pandas as pd
import statsmodels.api as sm, statsmodels.formula.api as smf
from statsmodels.stats.anova import anova_lm
from statsmodels.stats.multicomp import pairwise_tukeyhsd

CONT = ["seating_tilt_deg", "grasp_error_mm", "overshoot_pct", "slip_mm", "force_peak_N", "cycle_time_s"]

def demo_data(seed=0):
    """Arbitrary synthetic data with effects unrelated to the manuscript's designed values. NOT results."""
    r = np.random.default_rng(seed); rows = []
    ring = 0
    for c, mu in zip(["C1", "C2", "C3", "C4"], [5.0, 4.0, 3.0, 2.0]):
        for o in (0, 30, 60):
            for k in range(30):
                if k % 3 == 0: ring += 1
                t = max(0.05, r.normal(mu + o / 60, 1.0) + r.normal(0, .3))
                rows.append(dict(controller=c, init_orientation_deg=o, circlip_id=f"R{ring}", seating_tilt_deg=t,
                                 grasp_error_mm=abs(r.normal(mu / 2, .5)), overshoot_pct=abs(r.normal(mu, 1)), slip_mm=abs(r.normal(mu / 4, .2)),
                                 force_peak_N=r.normal(10 + 3 * mu, 2), cycle_time_s=r.normal(6 + .3 * mu, .5),
                                 assembly_success=int(r.random() < 1 - .03 * mu), failure_mode="none", exclusion_flag=0))
    return pd.DataFrame(rows)

def main():
    warnings.filterwarnings("ignore", message=".*(converge|boundary|Retrying|optimizer|Gradient).*")   # boundary fits (ring variance ~ 0) are reported in the text, not as warnings
    ap = argparse.ArgumentParser(); ap.add_argument("--data"); ap.add_argument("--out", default="stats/output"); ap.add_argument("--demo", action="store_true"); a = ap.parse_args()
    out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
    if a.demo:
        sim = pathlib.Path(__file__).resolve().parents[1] / "data" / "trial_log_designed_simulation.csv"
        df = pd.read_csv(sim) if sim.exists() else demo_data()
        banner = "*** DEMO / PIPELINE CHECK ON SIMULATED DATA (drawn around the DESIGNED benchmark) - NOT RESULTS ***"
    elif a.data: df = pd.read_csv(a.data); banner = f"data: {a.data} sha256={hashlib.sha256(open(a.data,'rb').read()).hexdigest()[:16]}"
    else: sys.exit("give --data or --demo")
    df = df[df.get("exclusion_flag", 0) == 0].copy()          # acquisition failures only; all other failed trials retained
    df["controller"] = pd.Categorical(df["controller"], ["C1", "C2", "C3", "C4"]); df["ori"] = df["init_orientation_deg"].astype(str)
    L = [banner, f"script run {datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')}  n={len(df)}\n"]
    for y in CONT:
        if y not in df or df[y].isna().all(): continue
        d = df.dropna(subset=[y])
        m = smf.mixedlm(f"{y} ~ C(controller) * C(ori)", d, groups=d["circlip_id"]).fit(reml=True)
        ols = smf.ols(f"{y} ~ C(controller) * C(ori)", d).fit(); an = anova_lm(ols, typ=2)
        an["partial_eta2"] = an["sum_sq"] / (an["sum_sq"] + an.loc["Residual", "sum_sq"])
        L += [f"## {y}{'  (PRIMARY ENDPOINT)' if y == 'seating_tilt_deg' else ''}", d.groupby("controller", observed=True)[y].agg(["mean", "std", "count"]).round(3).to_string(),
              "\nMixedLM fixed effects (95% CI):", pd.concat([m.params, m.conf_int()], axis=1).iloc[:12].round(3).to_string(), "\nANOVA (Type II, fixed effects) + partial eta^2:", an.round(4).to_string()]
        tk = pairwise_tukeyhsd(d[y], d["controller"].astype(str)); L += ["\nTukey HSD (controller):", str(tk.summary())]
        for a_, b_ in (("C4", "C3"), ("C4", "C1")):
            x, z = d[d.controller == a_][y], d[d.controller == b_][y]; sp = np.sqrt((x.var() + z.var()) / 2)
            L.append(f"contrast {a_} - {b_}: mean diff {x.mean() - z.mean():+.3f}, Cohen d {(x.mean() - z.mean()) / sp:+.2f}")
        L.append("")
    if "assembly_success" in df:
        g = smf.glm("assembly_success ~ C(controller) * C(ori)", df, family=sm.families.Binomial()).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(df["circlip_id"])[0]})
        L += ["## assembly_success (binomial GLM, cluster-robust SE by circlip)", df.groupby("controller", observed=True)["assembly_success"].agg(["sum", "count", "mean"]).round(3).to_string(),
              "\nodds ratios (95% CI):", pd.concat([np.exp(g.params), np.exp(g.conf_int())], axis=1).round(3).to_string()]
    (out / ("DEMO_report.txt" if a.demo else "report.txt")).write_text("\n".join(L)); print("\n".join(L[:6]), "...\nreport written to", out)

if __name__ == "__main__": main()
