# Statistical analysis plan (Sec. 4.6)

`stats/analysis.py` implements the prespecified plan on `data/trial_log.csv` (schema: `docs/trial_log_schema.md`):
fixed effects controller × orientation, random intercept per circlip (`MixedLM`, REML), partial η² from the fixed-effects ANOVA,
binomial GLM with cluster-robust SEs for assembly success, contrasts C4 vs C3 (primary) and C4 vs C1, Tukey HSD post-hoc.

Limits to disclose: (i) Tukey HSD here uses fixed-effects residuals and does not propagate the circlip random effect; (ii) a single sleeve is a design constant
and cannot be a random effect; (iii) the `(1 | session)` term of the manuscript's illustrative formula is not included because `MixedLM` takes one grouping
factor by default — use R/lme4 (`tilt ~ controller * orientation + (1 | circlip_id) + (1 | session)`) for the final model if both are needed;
(iv) `--demo` data are arbitrary synthetic values for a pipeline check and carry no information about the study.
Run `stats/randomize_run_order.py --seed <fixed seed>` and time-stamp the seed and script before collecting data.
