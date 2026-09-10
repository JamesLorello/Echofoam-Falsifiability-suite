# Mechanism-First Project Status — 2026-09-10

## Current scope

The project is being treated as a collection of falsifiable mechanism hypotheses about persistence, interaction, predictive mismatch, and history-dependent propagation. It is not currently established as a theory of gravity, spacetime, cosmology, consciousness, dark matter, or dark energy.

## Working conceptual chain

A compact working abstraction is:

`history -> predictive distribution -> interaction -> mismatch -> persistent modification -> changed future propagation`

"State" is used operationally as information sufficient to describe possible continuations, not as an assumed exact classical microstate.

## Evidence boundary

### Retained negative results

- Emergent propagation-speed test vCF-1.1 failed its prediction: measured speed about 0.3559 versus predicted 1.
- Stress-selected fragmentation did not outperform matched random rupture in the retained comparison. These negative results remain part of the evidence ledger.

### Unresolved or exploratory results

- BAO-like structure remains exploratory and is not evidence for a cosmological mechanism without recovered raw outputs, matched controls, and exclusion of numerical/statistical look-alikes.
- History-dependent / impedance-style propagation models are computational sandboxes. Their physical interpretation remains open.

## Current primary experiment: aligned vs rotated interaction

### Question

Do two otherwise matched coherent field packets persist differently at their interaction region when their internal field orientations are aligned versus rotated by 90 degrees?

### Preregisterable prediction

If alignment contributes to persistence, interaction-region persistence should be greater in the aligned condition than in the rotated condition, after accounting for ordinary linear superposition effects.

### Toy assay implemented

`src/echofoam_falsifiability/aligned_rotated_assay.py`

The assay evolves a two-component field F=(u,v) under

`dF/dt = D Laplacian(F) - gamma F + beta |F|^2 F - delta |F|^4 F`

Two anisotropic crossing packets have identical spatial geometry in both conditions. In the aligned condition both occupy the same internal component. In the rotated condition the second packet occupies the orthogonal component. Each realization is normalized to equal total initial L2 energy.

A matched linear ablation sets `beta=delta=0` while preserving damping, diffusion, initialization, geometry, and seeds.

Primary observable: area under the normalized interaction-region energy curve (persistence AUC).

### First run

Parameters:

- grid: 96 x 96
- domain length: 24
- dt: 0.008
- steps: 1500
- seeds: 24
- D: 0.18
- gamma: 0.30
- beta: 1.10
- delta: 0.85
- initial total L2 energy: 1.0

Observed mean persistence AUC:

| Model | Aligned | Rotated | Aligned - rotated |
| --- | ---: | ---: | ---: |
| Nonlinear | 1.406534 | 1.296040 | +0.110494 |
| Linear ablation | 1.263122 | 1.193251 | +0.069871 |

Raw nonlinear aligned advantage: about 8.53% relative to the rotated nonlinear mean.

However, the linear control already contains an aligned advantage of about 5.86%. Therefore the raw 8.53% result cannot be interpreted as evidence for a nonlinear memory mechanism.

The difference-of-differences was:

`(nonlinear aligned - nonlinear rotated) - (linear aligned - linear rotated) = +0.040623 AUC`

A paired bootstrap across 24 seeds gave an internal numerical 95% interval of approximately `0.040609 to 0.040638` for this exact toy implementation.

### Interpretation

This run supports only the narrow computational statement that the chosen nonlinear vector-field dynamics add an orientation-dependent persistence effect above the matched linear baseline.

It does not establish that nature contains the proposed fields, that the effect represents physical memory, or that the mechanism explains gravity, spacetime, quantum behavior, dark matter, dark energy, or cosmology.

The narrow positive result may still be conventional nonlinear dynamics. That ordinary explanation must be treated as the default until a discriminating prediction is found.

## Immediate next tests

1. Sweep relative internal angle continuously from 0 to 90 degrees rather than comparing only two points.
2. Match both global energy and initial interaction-region energy where possible, or use a baseline subtraction that removes the initialization geometry analytically.
3. Repeat across packet widths, amplitudes, diffusion, damping, and nonlinear coefficients.
4. Add shuffled/internal-orientation nulls and spatially separated noninteraction controls.
5. Test whether the effect survives alternative equations of motion that do not encode the same amplitude nonlinearity.
6. Define a material-effect threshold before the next confirmatory sweep.

## Research priority

For now, cosmological and gravitational interpretations remain downstream. The highest-value work is to determine whether history/alignment-dependent persistence survives strong controls and whether it produces a prediction not already expected from standard nonlinear field dynamics.
