# Held-Out Standard Relaxing-Memory Comparison

Status: prespecified synthetic model-class comparison. It does not establish
physical validation.

## Question

Can a conventional one-mode Maxwell internal variable, driven by the current
amplitude gradient and relaxing toward it, predict held-out trajectories from
the same field histories as well as the Echofoam gradient-change write law?

The Echofoam kernel generates all targets. Its reference forecast error is
zero by construction. This assay measures representational differences inside
the declared toy simulator; it is not independent evidence that either model
describes nature.

## Models

Both models share the same field equation, feedback coefficient, background
transport, diffusion, relaxation, numerical grid, and future update schedule.
The Echofoam reference evolves its memory with the committed kernel law:

```text
M_t + V.grad(M) = D_M lap(M) - gamma_M M + alpha D_t grad(abs(F))
F_t + V.grad(F) = D_F lap(F) - gamma_F F - kappa (M.grad) F
```

The comparator is a one-mode vector Maxwell state:

```text
M_t + V.grad(M) = D_M lap(M) + lambda * (c grad(abs(F)) - M)
F_t + V.grad(F) = D_F lap(F) - gamma_F F - kappa (M.grad) F
```

The Maxwell state starts at zero and is advanced along the same supplied
preparation tape. At release it continues to relax toward the instantaneous
amplitude gradient. The model therefore has access to the same observable
field history, but does not use the Echofoam increment-of-gradient source.

## Frozen design

- Training seed IDs: `26092400`–`26092423`.
- Held-out seed IDs: `26092424`–`26092447`; complete seeds remain bootstrap
  clusters.
- Grid: `32 x 32`; history and future each use 100 steps at the shared kernel
  defaults. The source, test families, and output schema are frozen before the
  full run.
- Training uses plus/minus tapes from `calibration_mode_a` and
  `calibration_mode_b` only.
- Held-out evaluation uses all four existing families, plus the excluded
  closed-envelope diagonal pattern `+/-cos(x+y)`.
- The sole fitted comparator is selected from the Cartesian product
  `lambda in {0.05, 0.10, 0.20, 0.40}` and
  `c in {0, 0.01, 0.05}` by lowest mean training trajectory error. The zero
  gain is the nested F-only control. Ties select the lower relaxation rate,
  then the lower gain.
- No held-out seed or preparation family enters selection. Other field and
  transport coefficients are held at the generator's declared values to
  isolate the memory source law.
- 10,000 whole-seed percentile bootstrap replicates use seed `20260924`.
  Seed clusters, not individual histories or time frames, are the sampling
  units.

## Metrics and decisions

For each forecast, `E` is the mean over future frames of
`||F_prediction - F_target||_2 / ||F*||_2`. Errors are averaged across all
held-out families and directions within a seed before uncertainty estimation.

The primary contrast is `E_Maxwell - E_Echofoam`; a positive value is an
Echofoam advantage on this synthetic target. The predeclared material margin
is `0.001`. A lower 95% interval above `0.001` is a material Echofoam advantage;
an interval wholly inside `[-0.001,+0.001]` is practical equivalence for this
observable. The secondary contrast `E_F-only - E_Maxwell` asks whether the
selected relaxing state adds material predictive accuracy beyond zero memory.

NaN/Inf values or numerical-stability guard failures terminate the run and are
retained as failures; no seed is dropped. The full results include candidate
training scores, per-seed and per-history forecast errors, model settings,
source hashes, and the decision intervals.

## Interpretation limits

This is one standard linear relaxing-vector comparator. It does not cover
multi-mode Prony models, nonlinear fatigue, passive-vector controls, noisy
observations, autonomous preparation convergence, or physical data. A positive
Echofoam result would only show better representation of these synthetic
targets under this split and metric. A practical-equivalence result would mean
that the write-law distinction did not yield a material held-out forecast
benefit here.

## Reproduction

After installing the package test dependencies, run:

```bash
python -m echofoam_falsifiability.standard_memory_comparison \
  --train-seed-start 26092400 --train-seeds 24 \
  --test-seed-start 26092424 --test-seeds 24 \
  --size 32 --history-steps 100 --future-steps 100 \
  --bootstraps 10000 --bootstrap-seed 20260924 \
  --output results/standard_memory_comparison_2026-09-24
```

The output directory contains `summary.json`, `runs.csv`,
`training_candidate_scores.csv`, and `candidate_summary.csv`.
