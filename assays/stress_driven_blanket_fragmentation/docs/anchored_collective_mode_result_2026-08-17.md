# Anchored Collective-Mode Fragmentation Test

## Date

2026-08-17

## Question

Does removing the freely diffusing collective memory mode reveal a late-time dynamical-separation advantage for stress-selected rupture locations over rupture-count- and rupture-time-matched random locations?

## Locked discriminator

The original observable was retained:

`separation = mean absolute within-component update-rate correlation - mean absolute across-component update-rate correlation`

It was evaluated over the final 600 of 3000 steps. Drives 1.3 and 1.4, seeds 0 through 63, initial conditions, OU forcing, integration settings, rupture counts, rupture times, and sampling window were retained. The only intervention was projection of the actual update vector onto the zero-collective-motion subspace while preserving the original per-observer speed bound.

## Validity checks

- Zero-mode anchoring passed: maximum final collective mean norm was `4.30e-15`.
- Update bandwidth passed: maximum update speed was `3.000000000001` for a bound of `3.0` (floating-point tolerance).
- Exact determinism passed for repeated seed 17 at drive 1.4.
- Rupture counts matched within every stress/random pair.
- The unanchored branch reproduced the original v0 transition and matched-control behavior.
- Three direct implementation tests passed. The environment did not include pytest, so the test functions were invoked directly.

## Result

| Drive | Finite pairs | Stress mean separation | Random mean separation | Mean paired difference | Median paired difference | Standardized paired effect | Fraction stress > random | Bootstrap 95% interval |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1.3 | 61 | 0.04309 | 0.04927 | -0.00618 | -0.00147 | -0.230 | 0.475 | [-0.01289, 0.00049] |
| 1.4 | 64 | 0.18233 | 0.20080 | -0.01847 | -0.01360 | -0.273 | 0.406 | [-0.03506, -0.00218] |

The one-sided sign-flip probabilities for an effect at least as positive as observed were 0.961 at drive 1.3 and 0.984 at drive 1.4. These are not evidence for the preregistered positive direction. At drive 1.4, the bootstrap interval excludes zero in the negative direction.

## Decision

**FALSIFIER TRIGGERED: retire the v0 stress-selection rule as a candidate mechanism for preferentially discovering dynamically coherent boundaries.**

Anchoring repaired the finite-horizon collective-drift defect but did not rescue the target prediction. Generic matched partitioning performed at least as well, and at drive 1.4 performed better, on the locked separation observable.

This decision applies to the specific v0 rupture-location rule and observable. It does not establish that all local overload or adaptive-boundary mechanisms must fail. Any replacement mechanism must be independently motivated, preregistered, and tested against the same matched-control standard rather than added to rescue this result.

## Files

- `src/blanket_fragmentation_v0.py`: anchored zero-mode implementation
- `src/run_anchored_discriminator.py`: locked 64-seed paired sweep
- `tests/test_anchored_collective_mode.py`: invariants, determinism, and rupture matching
- `results/anchored_matched_random_control.csv`: pair-level results
- `results/anchored_discriminator_summary.csv`: aggregate results
