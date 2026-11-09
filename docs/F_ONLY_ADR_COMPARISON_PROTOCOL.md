# Held-Out F-Only ADR Comparison

Status: completed deterministic toy-model comparison. It does not establish
physical validation.

## Question

Can a conventional F-only advection-diffusion-reaction (ADR) model, with shared
coefficients fitted only on training seeds, predict the held-out continuations
from the common present field as well as the explicit-memory toy kernel?

The “kernel reference” is the specified local-memory model that generates the
synthetic target trajectories. Its forecast error is zero by construction. The
comparison measures how far F-only models are from that known synthetic
generator; it is not an independent prediction contest.

## Controlled histories and split

Each seed has one common positive present field `F*` and four controlled
histories. Each history starts and ends at that exact `F*`; its memory field is
generated from the tape using the existing kernel write update. Two training
preparation families and two distinct test families each contribute a
plus/minus pair:

| Split | Seed IDs | Preparation families | Histories per seed |
| --- | --- | --- | ---: |
| Coefficient fitting and model selection | `26090400`–`26090423` | `calibration_mode_a`, `calibration_mode_b` | 4 |
| Held-out evaluation | `26090424`–`26090447` | `heldout_harmonic_mode`, `heldout_two_lobe_mode` | 4 |

For model selection, seeds `26090400`–`26090417` fit coefficients and
`26090418`–`26090423` select among four predeclared F-only candidates. The
selected candidate is refit on all 24 training seeds. Neither held-out test
seeds nor test preparation families enter coefficient fitting or selection.

The held-out profiles use new spatial modes; the `heldout_two_lobe_mode` also
uses a different temporal envelope. The continuation has zero future forcing
and no stochastic noise, identically across all histories.

## Models and prediction rule

The full F-only ADR model uses constant velocity, diffusion, and linear decay:

```text
F_next = F + dt * (-advection(F, V) + D_F * laplacian(F) - gamma_F * F)
```

Coefficients are fitted jointly across all training seeds and calibration
histories. Candidate models are full ADR, advection-diffusion, diffusion-reaction,
and diffusion-only. All use one shared coefficient set. They receive only the
common present `F*` when forecasting; they receive no history labels,
preparation inputs, branch-specific parameters, or future information. The
four predictions for a given seed are therefore identical for each F-only
candidate.

The explicit-memory reference generates `M` from each tape and continues the
declared toy kernel from `(F*, M)`. This reuses the same equations and parameter
values as the target generator.

## Observable and decision rule

For each held-out trajectory, the forecast error is the mean across future
frames of `||F_prediction - F_target||_2 / ||F*||_2`. Four histories remain in
one seed cluster. The primary contrast is:

```text
Delta_predict = mean(E_F-only_ADR - E_kernel_reference)
```

The material-advantage threshold is `0.001` normalized forecast error. A
kernel advantage requires the lower endpoint of the 95% held-out seed-cluster
bootstrap interval for `Delta_predict` to exceed `0.001`. A confidence interval
entirely within `[-0.001, +0.001]` is reported as practical equivalence for this
toy observable. An interval that crosses `+0.001` is inconclusive at the
predeclared threshold. These labels describe only this simulator and metric.

## Result (2026-09-24)

The training-selected model was full ADR. Its fitted coefficients were
`V = (0.20000154, -0.10000080)`, `D_F = 0.10011797`, and
`gamma_F = 0.04998160`, close to the generator values
`(0.2, -0.1, 0.1, 0.05)`.

On the 24 held-out seeds, the full ADR model's mean normalized trajectory
error was `2.26513568e-5`; the paired seed-cluster bootstrap 95% interval for
`Delta_predict` was `[2.26513568e-5, 2.26513568e-5]`. The kernel reference error
is zero by construction. The interval lies inside the `±0.001` band, so the
result is **practical equivalence at the predeclared material threshold**:
the memory kernel has no demonstrated material predictive advantage over the
best training-selected F-only candidate in this toy comparison.

The mean pairwise separation among the four kernel-generated held-out futures
was `1.83780781e-5` normalized trajectory L2. Thus the controlled histories
did produce different toy futures, but those differences were small on the
chosen forecast scale. The full ADR candidate was substantially better than
the reduced candidates, which omitted reaction or advection; its held-out mean
errors were `0.04861943` for advection-diffusion,
`0.00564361` for diffusion-reaction, and `0.04894604` for diffusion-only.

The bootstrap interval is extremely narrow because phase-seed results are
nearly invariant in this periodic deterministic setup. It describes variation
over the declared synthetic seed set, not uncertainty for a physical process.

## Reproduction

From the repository root:

```bash
python -m pip install -e ".[test]"
python -m echofoam_falsifiability.f_only_adr_comparison --train-seed-start 26090400 --train-seeds 24 --test-seed-start 26090424 --test-seeds 24 --size 32 --history-steps 100 --future-steps 100 --bootstraps 10000 --output results/f_only_adr_comparison_2026-09-24
python -m pytest -q tests/test_f_only_adr_comparison.py tests/test_compatible_history_replay.py
```

The output directory contains `summary.json`, per-seed `runs.csv`, and
per-history `branch_scores.csv`. The summary records coefficient fits,
selection scores, seed splits, source hashes, uncertainty intervals, and the
decision rule.

## Interpretation limits

The targets are simulated from the memory kernel being assessed, and the
kernel reference has access to the same generating equations. This check
shows that the current controlled history effect is small relative to the
predeclared normalized error band and can be predicted nearly as well by a
fitted F-only ADR model. It neither establishes the memory law as a distinct
physical mechanism nor rules out other memory models. Autonomous histories,
independent or noisy data, broader parameter regimes, and physical validation
remain untested.
