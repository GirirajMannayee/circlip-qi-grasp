#!/usr/bin/env python3
"""Generate the randomised 360-trial run order (4 controllers x 3 orientations x 30 reps) and an empty trial log.
Randomisation is blocked by session (default 6 sessions of 60 trials, each containing every controller x orientation cell 5 times).
Usage: python stats/randomize_run_order.py --seed 20261005 --out data/trial_log_planned.csv
Fix and time-stamp the seed BEFORE data collection (Sec. 4.6)."""
import argparse, csv, itertools, random, datetime

ap = argparse.ArgumentParser(); ap.add_argument("--seed", type=int, required=True); ap.add_argument("--out", default="data/trial_log_planned.csv")
ap.add_argument("--sessions", type=int, default=6); a = ap.parse_args()
rng = random.Random(a.seed)
cells = list(itertools.product(["C1", "C2", "C3", "C4"], [0, 30, 60]))
reps_per_session = 30 // a.sessions
header = next(csv.reader(open("data/trial_log_template.csv")))
rows, order = [], 0
for s in range(1, a.sessions + 1):
    block = [c for c in cells for _ in range(reps_per_session)]; rng.shuffle(block)
    for ctl, ori in block:
        order += 1; rows.append({"trial_id": order, "run_order": order, "session": f"S{s}", "controller": ctl, "init_orientation_deg": ori})
with open(a.out, "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=header); w.writeheader(); [w.writerow(r) for r in rows]
print(f"{len(rows)} trials -> {a.out}  (seed {a.seed}, generated {datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')})")
