# Trial-log schema (Sec. 4.7, Table 10, Table 21)

One row per trial; **failed trials are retained** (set `failure_mode`; use `exclusion_flag = 1` only for acquisition failures).

| column | type | meaning |
|---|---|---|
| trial_id | int | 1…360 |
| run_order | int | position in the randomised order (see `stats/randomize_run_order.py`) |
| session | str | session label (random effect) |
| circlip_id | str | individual ring (random effect); expansion cycles per ring are capped and logged |
| expansion_cycle_no | int | how many times this ring has been expanded so far |
| controller | {C1,C2,C3,C4} | Table 6 |
| init_orientation_deg | {0,30,60} | gap rotation about the ring axis |
| rgbd_frame_id | str | frame used for candidate generation |
| selected_candidate | 0–15 / blank for C1 | candidate index p |
| grasp_error_mm | float | E_g, Euclidean distance measured–desired grasp point |
| force_cmd_N / force_peak_N | float | commanded setpoint F_d / max F(t) |
| expansion_Dreq_mm / _Dpk_mm | float | smallest clearing inner diameter / peak inner diameter |
| overshoot_pct | float | D_o = (D_pk − D_req)/D_req × 100 |
| slip_mm | float | S_d = abs(P_t − P_0) |
| seating_tilt_deg | float | **primary endpoint** Θ_s = abs(θ_m − θ_d), θ_d = 0, fixed world reference |
| assembly_success | 0/1 | prespecified axial-position + residual-tilt criterion at end of 3 s hold |
| release_time_s / cycle_time_s | float | t_seated − t_grasp |
| failure_mode | enum | none, perception, grasp_point, contact_force, slip, excessive_tilt, over_expansion, mis_seat_or_ejection, acquisition |
| exclusion_flag | 0/1 | acquisition failures only |

## Conventions used in the filled files
* `selected_candidate = -1` means the fixed grasp point of C1 (no candidate selection).
* `force_cmd_N`: 14 N setpoint for C3/C4 (force-regulated); preset open-loop grip command for C1 (20 N) and C2 (18 N).
* `expansion_Dreq_mm`: smallest inner diameter that clears the 20 mm sleeve (≈ 20.1 mm, per ring); `expansion_Dpk_mm = Dreq·(1 + overshoot_pct/100)`.
* `release_time_s = cycle_time_s − 3.0` (the 3 s seating hold follows the release).
* Each ring is used for 10 expansion cycles (`expansion_cycle_no` 1–10), then replaced (cap from `config/controller.yaml`).

## Which file is which
| file | content |
|---|---|
| `data/trial_log_template.csv` | header only |
| `data/trial_log_planned.csv` | randomised run order, sessions, ring/cycle assignment, frame ids; measurement columns empty until the robot runs |
| `data/trial_log_designed_simulation.csv` | **all columns filled with SIMULATED values** around the designed benchmark (Tables 16–17), every row flagged in `notes`. For testing the analysis pipeline and layout only; never merge with real data, never cite as results |
