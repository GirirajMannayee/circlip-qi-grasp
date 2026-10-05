#!/usr/bin/env python3
"""Regenerate every data-driven or circuit figure of the manuscript (PNG 300 dpi + PDF + SVG) into figures/generated/.

Schematic-only figures (1, 3, 4, 9, 13 and the block diagram 5a, 7a) are NOT redrawn; the manuscript originals are kept in
figures/manuscript_originals/. Figures that show designed (non-measured) values carry an on-figure label.
"""
import json, pathlib
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle, FancyArrowPatch
from qi_grasp.core import (N, utility, candidate_set_seed42, soft_phases, hard_phases, amplitude_search, grover_p)
from qi_grasp.force import step_response, overshoot_pct
from qi_grasp.noise import predicted_noisy, g_max_for_threshold, depolarizing_fit
from qi_grasp.circuits import build_gate_level

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "figures" / "generated"; OUT.mkdir(parents=True, exist_ok=True)
noise = json.loads((ROOT / "data/results/noise_runs.json").read_text())["runs"]
mc = pd.read_csv(ROOT / "data/results/montecarlo.csv")
D = lambda n: pd.read_csv(ROOT / f"data/designed_benchmark/Table{n}.csv")

# Okabe-Ito colour-blind-safe palette
BLUE, ORANGE, GREEN, RED, PURPLE, GREY, SKY, YEL = "#0072B2", "#E69F00", "#009E73", "#D55E00", "#CC79A7", "#6b6b6b", "#56B4E9", "#F0E442"
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "axes.titlesize": 9.5,
                     "axes.labelsize": 9, "legend.frameon": False, "figure.dpi": 100, "savefig.bbox": "tight"})
DESIGNED = "DESIGNED benchmark – not measured"

def save(fig, name):
    for ext in ("png", "pdf", "svg"):
        fig.savefig(OUT / f"{name}.{ext}", dpi=300)
    plt.close(fig); print("  ", name)

def tag(ax_or_fig, text=DESIGNED):
    (ax_or_fig.text if hasattr(ax_or_fig, "text") else ax_or_fig.text)(0.995, 1.02, text, ha="right", va="bottom", fontsize=7.5,
        color=RED, style="italic", transform=ax_or_fig.transAxes if hasattr(ax_or_fig, "transAxes") else ax_or_fig.transFigure)

U = utility(candidate_set_seed42()); BEST = int(np.argmax(U)); PH, PS = hard_phases(U), soft_phases(U)
labels = [format(i, "04b") for i in range(N)]
ideal = lambda K, ph=PH: amplitude_search(ph, K)

# ---- Fig 2 ------------------------------------------------------------------------------------------------
fig, (a, b) = plt.subplots(1, 2, figsize=(8.6, 3.5), gridspec_kw={"width_ratios": [1, 1.5], "wspace": 0.45})
gap = np.radians(60); ang = np.linspace(gap / 2 + 0.12, 2 * np.pi - gap / 2 - 0.12, N)
th = np.linspace(gap / 2, 2 * np.pi - gap / 2, 300)
a.plot(np.cos(th), np.sin(th), color=GREY, lw=5, solid_capstyle="round", alpha=.35)
sc = a.scatter(np.cos(ang), np.sin(ang), c=U, cmap="viridis", s=90, zorder=3, edgecolor="white")
for i, t in enumerate(ang): a.text(1.2 * np.cos(t), 1.2 * np.sin(t), str(i), ha="center", va="center", fontsize=7)
bx, by = np.cos(ang[BEST]), np.sin(ang[BEST])
a.scatter([bx], [by], s=260, facecolor="none", edgecolor=RED, lw=1.8, zorder=4)
a.annotate("", xy=(bx + .05, by - .65), xytext=(bx + .05, by - .05), arrowprops=dict(arrowstyle="->", color=RED, lw=1.5))
a.text(bx + .12, by - .4, "F", color=RED); a.text(.0, 0, "open ring\n(gap at right)", ha="center", va="center", fontsize=8, color=GREY)
a.set_aspect("equal"); a.axis("off"); a.set_title("(a) 16 contour candidates, colour = utility\n(M = r × F at the best contact, red)")
plt.colorbar(sc, ax=a, shrink=.7, label="U(p)")
b.bar(range(N), U, color=[RED if i == BEST else BLUE for i in range(N)])
b.set_xticks(range(N)); b.set_xticklabels(labels, rotation=90, fontsize=7); b.set_ylabel("Utility U(p)"); b.set_xlabel("Basis state |q3 q2 q1 q0>")
b.set_title(f"(b) Utility landscape; best p = {BEST} (U = {U[BEST]:.3f})"); b.set_title(f"(b) Utility, best p = {BEST} (U = {U[BEST]:.3f}); synthetic seed 42, not robot data", fontsize=8.5)
save(fig, "Fig02_candidates")

# ---- Fig 5b -----------------------------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(5.2, 3.2))
for z, c in zip((0.5, 0.7, 1.0, 1.5), (RED, ORANGE, BLUE, GREEN)):
    t, y = step_response(z, 1.0); ax.plot(t, y, color=c, label=f"ζ = {z}  (overshoot {overshoot_pct(z):.0f} %)")
ax.axhspan(.95, 1.05, color=GREY, alpha=.2); ax.axhline(1, color="k", lw=.6, ls=":")
ax.set_xlabel("Time × ω_n"); ax.set_ylabel("F_m / F_d"); ax.set_title("Normalised force step response (computed from transfer function)"); ax.legend(loc="lower right")
save(fig, "Fig05b_force_step")

# ---- Fig 6 operator sequence ---------------------------------------------------------------------------------
fig = plt.figure(figsize=(10, 3.4))
gs = fig.add_gridspec(2, 4, height_ratios=[1, 1.5], hspace=.55)
axb = fig.add_subplot(gs[0, :]); axb.axis("off"); axb.set_xlim(0, 10); axb.set_ylim(0, 1)
boxes = [("|0⟩⊗4", 0.1), ("H⊗4", 1.9), ("O_φ  (phase oracle)", 3.7), ("R_s  (diffusion)", 5.7), ("measure", 7.6), ("argmax over\nvalid indices", 8.8)]
w = [1.2, 1.2, 1.6, 1.6, 1.0, 1.1]
for (txt, x0), ww in zip(boxes, w):
    axb.add_patch(FancyBboxPatch((x0, .25), ww, .5, boxstyle="round,pad=.02", fc="#eef3f8", ec=BLUE)); axb.text(x0 + ww / 2, .5, txt, ha="center", va="center", fontsize=8)
for i in range(len(boxes) - 1):
    axb.annotate("", xy=(boxes[i + 1][1], .5), xytext=(boxes[i][1] + w[i], .5), arrowprops=dict(arrowstyle="->", color=GREY))
axb.text(5.2, .93, "repeat K times", ha="center", fontsize=8, color=RED)
axb.plot([3.6, 7.4], [.85, .85], color=RED, lw=1)
for k in range(4):
    ax = fig.add_subplot(gs[1, k]); p = ideal(k)
    ax.bar(range(N), p, color=[RED if i == BEST else BLUE for i in range(N)]); ax.set_ylim(0, 1); ax.set_title(f"after K = {k}:  P(p={BEST}) = {p[BEST]:.3f}", fontsize=8)
    ax.set_xticks([0, 5, 10, 15]); ax.set_xlabel("candidate p")
    if k == 0: ax.set_ylabel("probability")
save(fig, "Fig06_operator_sequence")

# ---- Fig 7b / 11: circuit drawings --------------------------------------------------------------------------
for K, name, w_ in ((1, "Fig07b_circuit_gate_level_K1", 14), (3, "Fig11_quirk_style_circuit_K3", 26)):
    qc = build_gate_level(K, measure=True)
    f = qc.draw("mpl", fold=-1, style={"fontsize": 9}); f.set_size_inches(w_ * .6, 2.6); save(f, name)

# ---- Fig 8 --------------------------------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(5.4, 3.3)); g = np.arange(0, 800)
for f_, c in ((0.988, RED), (0.995, ORANGE), (0.999, GREEN)):
    ax.plot(g, predicted_noisy(0.961, g, f_), color=c, label=f"f = {f_}" + ("" if f_ == .988 else " (projection)"))
gm = g_max_for_threshold(0.988); ax.plot([gm], [.5], "s", color=RED, ms=7); ax.annotate(f"g_max ≈ {gm:.0f}", (gm, .5), (gm + 40, .62), arrowprops=dict(arrowstyle="-", color=GREY))
ax.plot([189], [noise[0]["noisy_p_mean"]], "o", color="k", ms=7); ax.annotate("executed hard oracle\n(189 gates, 0.161)", (189, .161), (260, .3), arrowprops=dict(arrowstyle="-", color=GREY))
ax.axhline(1 / 16, color=GREY, ls="--", lw=.8); ax.text(790, .015, "uniform 1/16", ha="right", fontsize=7.5, color=GREY); ax.axhline(.5, color=GREY, ls=":", lw=.6)
ax.set_xlabel("Two-qubit gate count g"); ax.set_ylabel("Noisy target probability"); ax.set_title("Eq. (13), P_ideal = 0.961"); ax.legend(); ax.set_ylim(0, 1)
save(fig, "Fig08_noise_attenuation")

# ---- Fig 12 -------------------------------------------------------------------------------------------------
from qiskit_ibm_runtime.fake_provider import FakeManilaV2
bk = FakeManilaV2(); tg = bk.target
fig, (a, b) = plt.subplots(1, 2, figsize=(9.2, 3.3), gridspec_kw={"width_ratios": [1.5, 1]})
for q in range(5):
    a.add_patch(Circle((q, 0), .27, fc="#eef3f8", ec=BLUE)); a.text(q, 0, f"Q{q}", ha="center", va="center", fontweight="bold")
    qp = bk.qubit_properties(q); a.text(q, -.55, f"RO {tg['measure'][(q,)].error*100:.1f}%\nT1 {qp.t1*1e6:.0f} µs", ha="center", va="top", fontsize=7.5)
for q in range(4):
    a.plot([q + .27, q + .73], [0, 0], color=GREY); a.text(q + .5, .12, f"CX\n{tg['cx'][(q, q+1)].error*100:.2f}%", ha="center", fontsize=7, color=RED)
a.set_xlim(-.6, 4.6); a.set_ylim(-1.2, .8); a.set_aspect("equal"); a.axis("off"); a.set_title("(a) FakeManilaV2 linear coupling map (backend snapshot)")
nm = ["Hard K=3\n(gate-level)", "Soft K=2", "Soft K=3"]; rr = [noise[0], noise[2], noise[3]]; x = np.arange(3)
b.bar(x - .2, [r["two_qubit_gates"] for r in rr], .4, color=BLUE, label="2-qubit (CX) gates"); b.bar(x + .2, [r["depth"] for r in rr], .4, color=ORANGE, label="transpiled depth")
for i, r in enumerate(rr): b.text(i - .2, r["two_qubit_gates"] + 4, r["two_qubit_gates"], ha="center", fontsize=7.5); b.text(i + .2, r["depth"] + 4, r["depth"], ha="center", fontsize=7.5)
b.set_xticks(x); b.set_xticklabels(nm, fontsize=8); b.set_ylim(0, 380); b.legend(loc="upper left", fontsize=8, ncol=2); b.set_title("(b) Transpiled cost, opt. level 1")
save(fig, "Fig12_device_and_cost")

# ---- Fig 15 -------------------------------------------------------------------------------------------------
fig, axs = plt.subplots(1, 4, figsize=(10, 2.4), sharey=True)
for k, ax in enumerate(axs):
    p = ideal(k); ax.bar(range(N), p, color=[RED if i == BEST else BLUE for i in range(N)]); ax.set_title(f"K = {k}   P = {p[BEST]:.3f}"); ax.set_xlabel("candidate p"); ax.set_xticks([0, 5, 10, 15])
axs[0].set_ylabel("probability"); save(fig, "Fig15_probabilities_K0-3")

# ---- Fig 16 -------------------------------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(4.8, 3.4)); Ks = np.arange(0, 7); kk = np.linspace(0, 6, 300)
ax.plot(kk, grover_p(kk), color=GREY, lw=1, label="Grover law (continuous)")
ax.plot(Ks, [ideal(k)[BEST] for k in Ks], "o-", color=BLUE, label="hard oracle")
ax.plot(Ks, [ideal(k, PS)[BEST] for k in Ks], "s-", color=ORANGE, label="soft oracle (γ = 6)")
ax.axhline(1 / 16, color=GREY, ls=":"); ax.set_xlabel("Iterations K"); ax.set_ylabel(f"P(best candidate p = {BEST})"); ax.legend(); ax.set_title("Best-candidate probability vs. K")
save(fig, "Fig16_probability_vs_K")

# ---- Fig 17 -------------------------------------------------------------------------------------------------
fig, (a, b, c) = plt.subplots(1, 3, figsize=(11, 3.1), gridspec_kw={"width_ratios": [1.4, 1, 1.1]})
w_ = .4; a.bar(np.arange(N) - w_ / 2, noise[0]["ideal_dist"], w_, color=BLUE, label="ideal"); a.bar(np.arange(N) + w_ / 2, noise[0]["mean_dist"], w_, color=ORANGE, label="noisy (mean of 10 seeds)")
a.set_xticks(range(N)); a.set_xticklabels(labels, rotation=90, fontsize=6.5); a.legend(); a.set_ylabel("probability"); a.set_title("(a) Hard oracle K = 3")
cfg = [("Hard K=3", noise[0]), ("Soft K=2", noise[2]), ("Soft K=3", noise[3])]; x = np.arange(3)
b.bar(x - .2, [r["ideal_p"] for _, r in cfg], .4, color=BLUE, label="ideal"); b.bar(x + .2, [r["noisy_p_mean"] for _, r in cfg], .4, yerr=[r["noisy_p_sd"] for _, r in cfg], color=ORANGE, capsize=3, label="noisy ±1 SD")
b.axhline(1 / 16, color=GREY, ls=":"); b.set_xticks(x); b.set_xticklabels([n for n, _ in cfg], fontsize=8); b.legend(); b.set_title("(b) Target-state probability")
gg = np.arange(1, 260); c.plot(gg, .988 ** gg, color=RED, label="f = 0.988")
for (n, r), mk in zip(cfg, ("o", "s", "^")):
    lam, _ = depolarizing_fit(r["ideal_p"], r["noisy_p_mean"], r["two_qubit_gates"]); c.plot(r["two_qubit_gates"], lam, mk, color="k", label=n)
c.set_xlabel("Two-qubit gates g"); c.set_ylabel("λ = f^g"); c.legend(fontsize=7.5); c.set_title("(c) Attenuation factor")
save(fig, "Fig17_noise_test")

# ---- Fig 18 -------------------------------------------------------------------------------------------------
fig, (a, b) = plt.subplots(1, 2, figsize=(9.4, 3.3)); y = np.arange(len(mc))[::-1]
a.barh(y + .2, mc["Top-1 (%)"], .4, color=BLUE, label="top-1"); a.barh(y - .2, mc["Top-3 (%)"], .4, color=SKY, label="top-3")
a.set_yticks(y); a.set_yticklabels([f"{m}  [{e} evals]" for m, e in zip(mc["Method"], mc["Utility evals"])], fontsize=7.5); a.set_xlabel("selection rate (%)"); a.legend(loc="upper center", bbox_to_anchor=(0.5, -0.18), ncol=2); a.set_title("(a) Selection rate, 2,000 sets")
b.barh(y, mc["Mean regret"], color=ORANGE); b.set_yticks(y); b.set_yticklabels([]); b.set_xlabel("mean utility regret U(best) − U(selected)"); b.set_title("(b) Mean regret")
save(fig, "Fig18_montecarlo")

# ---- Designed benchmark figures 19-24 -------------------------------------------------------------------------
t16, t17, t18, t19 = D(16), D(17), D(18), D(19); ctl = ["C1", "C2", "C3", "C4"]; cc = [GREY, SKY, BLUE, RED]
fig, (a, b) = plt.subplots(1, 2, figsize=(7.4, 3)); a.bar(ctl, t16["Success (%)"], color=cc); a.set_ylim(80, 100); a.set_ylabel("Assembly success (%)"); a.set_title("(a) Success")
b.bar(ctl, t16["Tilt (°)"], color=cc); b.set_ylabel("Seating tilt (°)"); b.set_title("(b) Tilt"); fig.text(.99, .98, DESIGNED, ha="right", color=RED, fontsize=7.5, style="italic"); save(fig, "Fig19_controller_benchmark")

metrics = ["Success (%)", "Grasp error (mm)", "Tilt (°)", "Overshoot (%)", "Slip (mm)", "Peak force (N)", "Time (s)"]
M = t16[metrics].to_numpy(float); hib = [True] + [False] * 6
rank = np.array([(-M[:, j] if hib[j] else M[:, j]).argsort().argsort() for j in range(7)]).T   # 0 = best
fig, ax = plt.subplots(figsize=(6.2, 3)); ax.imshow(rank, cmap="Blues_r", vmin=-1, vmax=4.5, aspect="auto")
ax.set_xticks(range(7)); ax.set_xticklabels(metrics, rotation=30, ha="right", fontsize=8); ax.set_yticks(range(4)); ax.set_yticklabels(t16["Controller"], fontsize=8)
for i in range(4):
    for j in range(7): ax.text(j, i, f"{M[i, j]:g}", ha="center", va="center", fontsize=8, color="white" if rank[i, j] == 0 else "black")
ax.set_title("Colour = within-metric rank (darker = better)  –  " + DESIGNED, fontsize=8); save(fig, "Fig20_heatmap")

fig, axs = plt.subplots(1, 3, figsize=(9.4, 2.9)); ori = ["0°", "30°", "60°"]
for ax, col, yl in zip(axs, ("Tilt (°)", "Grasp error (mm)", "Success (%)"), ("Seating tilt (°)", "Grasp error (mm)", "Success (%)")):
    ax.plot(ori, t17[col], "o-", color=RED); ax.set_xlabel("Initial orientation"); ax.set_ylabel(yl)
axs[0].set_title("(a)"); axs[1].set_title("(b)"); axs[2].set_title("(c)"); fig.text(.99, 1.0, DESIGNED, ha="right", color=RED, fontsize=7.5, style="italic"); save(fig, "Fig21_orientation")

fig, axs = plt.subplots(1, 3, figsize=(9.4, 2.9)); nms = ["Greedy", "PSO", "QI", "QI+F/T"]
for ax, col, yl in zip(axs, ("Normalized score", "Candidate evals", "Latency (ms)"), ("Normalised grasp score", "Candidate evaluations", "Latency (ms)")):
    ax.bar(nms, t18[col], color=[GREY, SKY, BLUE, RED]); ax.set_ylabel(yl); ax.tick_params(axis="x", labelsize=8)
fig.text(.99, 1.0, DESIGNED.replace("benchmark – not measured", "benchmark – not executed"), ha="right", color=RED, fontsize=7.5, style="italic"); save(fig, "Fig22_optimizer_benchmark")

fig, a = plt.subplots(figsize=(4.8, 3)); a.bar(t19["Configuration"], t19["Tilt (°)"], color=BLUE); a.set_ylabel("Seating tilt (°)"); a2 = a.twinx(); a2.plot(t19["Configuration"], t19["Success (%)"], "o-", color=RED); a2.set_ylabel("Success (%)", color=RED); a2.spines["right"].set_visible(True)
a.set_title(DESIGNED + "\n(A1 carries C2 values – see manuscript Sec. 5.4)", fontsize=7.5, color=RED); save(fig, "Fig23_ablation")

t20 = pd.read_csv(ROOT / "tables/generated/Table20.csv"); rel = t20["Relative change"].str.replace("%", "").astype(float)
fig, a = plt.subplots(figsize=(5.2, 3)); a.barh(t20["Outcome"][::-1], rel[::-1], color=[BLUE if v > 0 else RED for v in rel[::-1]]); a.axvline(0, color="k", lw=.6); a.set_xlabel("Relative change C4 vs C1 (%)")
for i, v in enumerate(rel[::-1]): a.text(v + (2 if v > 0 else -2), i, f"{v:+.1f}%", va="center", ha="left" if v > 0 else "right", fontsize=7.5)
a.set_xlim(-100, 30); a.set_title(DESIGNED, fontsize=7.5, color=RED); save(fig, "Fig24_relative_change")

# ---- Fig 10 evidence gates / Fig 14 study design ---------------------------------------------------------------
def flow(names, sub, fname, w=11, fc=("#eef3f8",) * 9, title=None):
    fig, ax = plt.subplots(figsize=(w, 1.9)); ax.axis("off"); n = len(names); ax.set_xlim(0, n * 2.2); ax.set_ylim(0, 1.6)
    for i, (t, s) in enumerate(zip(names, sub)):
        ax.add_patch(FancyBboxPatch((i * 2.2 + .05, .3), 1.9, 1.0, boxstyle="round,pad=.03", fc=fc[i], ec=BLUE)); ax.text(i * 2.2 + 1.0, .95, t, ha="center", va="center", fontweight="bold", fontsize=8.5)
        ax.text(i * 2.2 + 1.0, .6, s, ha="center", va="center", fontsize=7.2)
        if i < n - 1: ax.annotate("", xy=((i + 1) * 2.2 + .05, .8), xytext=(i * 2.2 + 1.95, .8), arrowprops=dict(arrowstyle="->", color=GREY))
    if title: ax.set_title(title, fontsize=9)
    save(fig, fname)
flow(["Gate 1", "Gate 2", "Gate 3", "Gate 4"], ["reference optimizer\n(candidates, ranking)", "ideal circuit\nsimulation", "FakeManilaV2\nnoise model", "physical robot\n360 trials"],
     "Fig10_evidence_gates", fc=("#d9f0e6", "#d9f0e6", "#d9f0e6", "#fbe3d4"), title="Executed: Gates 1–3 (computational).  Planned: Gate 4 (measured).")
flow(["Design", "Randomise", "Run trials", "Log", "Analyse"], ["4 controllers × 3 orient.\n× 30 reps = 360", "order randomised;\ncirclip ID logged", "capped expansion\ncycles per circlip", "one row per trial;\nfailures retained", "mixed model / GLMM;\ntilt = primary"],
     "Fig14_study_design", w=12, fc=("#fbe3d4",) * 5, title="Planned 360-trial factorial study (no data yet)")
print("done")
