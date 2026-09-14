# Supplementary orientation numerical checks

Specified after the first four full-parameter seed blocks indicated a positive
endpoint residual near 1.37%, and before running these supplementary checks.
The confirmatory protocol and its decision threshold remain unchanged.

Purpose: determine whether a possible material positive result is sensitive to
the integration timestep or spatial grid. Bootstrap intervals over tiny
initialization noise cannot answer this question.

Use seeds 0 through 3 and the planned endpoints 0 and 90 degrees. Keep all three
conditions, energy matching, analytic baseline, and noninteraction diagnostics.
These are supplementary numerical comparisons, not extra independent samples
for the primary 24-seed inference.

| Check | N | dt | Steps | Sampling interval |
| --- | ---: | ---: | ---: | ---: |
| Reference subset from primary sweep | 96 | 0.008 | 1500 | 0.08 |
| Timestep halved | 96 | 0.004 | 3000 | 0.08 |
| Finer grid and halved timestep | 128 | 0.004 | 3000 | 0.08 |

Before these runs, define an agreement tolerance of **0.001 in normalized
effect**, or 0.1 percentage point. This is one tenth of the primary material
threshold. Report each difference from the matched four-seed reference mean;
both refinements must remain above 1% and inside the agreement tolerance to
describe the primary effect as stable under these checks. Failure would qualify
the primary finite-grid result as numerically sensitive and prevent a stronger
claim. Do not substitute the supplementary verdicts for the primary verdict.

All runs have physical horizon 12 and identical readout times. Common seed IDs
at different N do not mean the noise fields are identical continuum functions;
the generator draws a new-sized array. Thus this is a finite numerical
sensitivity check, not a fitted convergence order or continuum extrapolation.

```bash
python -m echofoam_falsifiability.orientation_control_pass --seeds 4 --seed 0 --workers 2 --angle-step 90 --dt 0.004 --steps 3000 --sample-every 20 --output orientation_dt_check
python -m echofoam_falsifiability.orientation_control_pass --seeds 4 --seed 0 --workers 2 --angle-step 90 --size 128 --dt 0.004 --steps 3000 --sample-every 20 --output orientation_grid_check
```
