# Energy-matched orientation control protocol

Declared 2026-09-13, before the control sweep. Baseline main commit:
`40d23dfb5e73447a13d915c8633fd6430969ede0`.

## Question and scope

Does coherent relative orientation produce a **material** increase in local
persistence above the matched linear dynamics after removing initial amplitude
differences? Does that advantage disappear when relative orientations are
shuffled and when the packets do not appreciably interact?

This is a test of the existing isotropic nonlinear vector-field toy equation,
not the separate local-memory kernel. It contains no retained memory field.
Ordinary amplitude-dependent reaction and orientation-dependent diffusion are
the default explanations for any surviving effect.

## Fixed confirmatory specification

| Item | Prespecified value |
| --- | --- |
| Equation | `dF/dt = D Lap(F) - gamma F + beta |F|^2 F - delta |F|^4 F` |
| Grid and boundary | 96 by 96, length 24, periodic finite differences |
| Integration | Explicit Euler, dt 0.008, 1500 steps, horizon 12 |
| Measurements | Every 10 steps and always the final step; trapezoidal AUC |
| Coefficients | D 0.18, gamma 0.30, beta 1.10, delta 0.85 |
| Global initial L2 energy | 1.0 |
| Observation radius | 2.2 |
| Continuous angle parameter | theta in [0, 90] degrees |
| Numerical sweep grid | 0, 5, 10, ..., 90 degrees, 19 points |
| Initialization seeds | 0 through 23, paired across all angles and controls |
| Noise | Packet-attached lognormal amplitude noise, sigma 0.003 |
| Bootstrap | 10,000 whole-seed resamples, RNG seed 20260913 |
| Primary contrast | Baseline-adjusted coherent 0-degree minus 90-degree AUC |
| Material threshold | Positive 0.01 of the per-seed coherent linear 90-degree AUC |
| Energy-matching tolerance | Maximum pointwise error / maximum common density <= 1e-12 |
| Noninteraction gate | Maximum sampled normalized-energy discrepancy from independent packet evolution <= 0.001 |

One percent is a declared practical discrimination criterion for this assay,
not a physical scale, an estimated noise floor, or a threshold chosen from this
sweep's results. Changing it, the angle grid, or other parameters creates a new
run specification. The original two-endpoint run was already known when this
protocol was written. This is prospective to this new control pass, not a claim
of independent external preregistration or a blind replication.

The implementation accepts arbitrary real angle increments and includes both
endpoints even when the increment does not divide 90. A finite grid cannot test
every real angle or exclude features between sampled angles.

## Initialization and exact energy control

Start with the existing crossing anisotropic Gaussian envelopes. Their widths
remain (4, 1.15) and (1.15, 4). Replace the original spatially uniform additive
vector noise with positive, packet-attached amplitude perturbations:

`a = g1 exp(sigma z1 - sigma^2/2)`

`b = g2 exp(sigma z2 - sigma^2/2)`.

The same two standard-normal arrays are drawn from `default_rng(seed)` for every
angle and condition. This prevents an isolated rotated packet from changing its
relationship to an independent background-noise vector. It is an explicit
initialization change, so absolute AUCs are not a direct replication of the
September 10 run.

Define a common energy density `rho^2 = c^2 (a^2 + b^2)`, where c makes its
global integral 1. For each relative orientation phi, construct

`G = (a + b cos(phi), b sin(phi))`, then `F = rho G / |G|`.

Thus `|F(x,0)|^2` is identical **at every grid point** for all angles, coherent
and shuffled fields with the same geometry and seed. This also matches every
initial energy moment, global energy, and energy inside any fixed observation
mask. At 90 degrees the coherent condition is the normalized orthogonal packet
pair. At other angles the common spatial amplitude is imposed while retaining
the internal direction of the packet sum. This rescaling changes the individual
packet amplitudes; that intervention is part of this strengthened control.
Exact cancellation, if encountered in a shuffled field, is rejected instead of
assigning an arbitrary direction.

Spatial direction gradients intentionally differ. Matching amplitude does not
make the initial vector fields, gradient energies, or subsequent linear
diffusion identical. These are precisely why the matched baseline is retained.

## Controls

1. **Coherent crossing:** phi is the same theta throughout the second packet;
   the observation window is the central radius-2.2 disk.
2. **Shuffled relative orientation:** build a balanced full-circle phase bank,
   add a uniform random global phase, and randomly permute it over grid cells.
   Use `SeedSequence([seed, 731])` for this independent stream. Set
   `phi(x) = theta + shuffled_phase(x)`, preserving this same realization across
   angles. This physically destroys coherent relative orientation while
   preserving the common pointwise energy map. The distribution is invariant
   under a theta shift, so the population angle contrast is zero. Individual
   seeds need not be zero. Shuffling adds small-scale direction gradients, so
   absolute shuffled persistence need not equal coherent persistence.
3. **Spatially separated:** translate the first packet to (-6, -6) and the
   second to (6, 6), using periodic distances. The readout is the union of
   radius-2.2 disks at their centers. The global energy budget remains 1, and
   the full initial energy map is matched across angles within this geometry.
   The mask has two windows; its absolute AUC is not directly compared to the
   single-window crossing AUC. Only paired angle contrasts are compared.

Gaussian tails and diffusion preclude declaring exact noninteraction from
separation alone. At 0 and 90 degrees, evolve the two actual normalized packet
parts independently under the nonlinear equation, superpose only at readout,
and compare against their jointly evolved field. The maximum absolute
difference in sampled local energy, normalized by the joint initial local
energy, must be <= 0.001 for **every seed**. This is a direct endpoint
noninteraction diagnostic. It does not prove absence of every possible
interaction at unsampled times or angles. The full separated-angle contrast
must additionally pass the statistical equivalence gate below.

## Analytic linear baseline

For every actual initialized field, set beta=delta=0. Compute its trajectory
analytically for the same spatial discretization **and the same Euler timestep**:

`Fhat_k(t_n) = [1 + dt (D lambda_h(k) - gamma)]^n Fhat_k(0)`

`lambda_h(k) = -4/dx^2 [sin^2(pi kx/N) + sin^2(pi ky/N)]`.

The mode numbers k in this expression are integers. The code uses FFT
frequencies in cycles per grid cell. This is an exact solution of the linear
discrete recurrence up to floating-point error. It is not the continuous-time
heat equation. Its local normalized-energy AUC uses the same masks and sample
times as the nonlinear trajectory. A regression test compares it with direct
Euler evolution under zero nonlinear coefficients.

## Paired estimand, uncertainty, and decisions

Let `A_N(s,c,theta)` and `A_L(s,c,theta)` be nonlinear and analytic-linear AUCs,
each integrating `E_region(t) / E_region(0)`. Define

`B = A_N - A_L`

`d(s,c,theta) = B(s,c,theta) - B(s,c,90)`

`e(s,c,theta) = d(s,c,theta) / A_L(s,coherent,90)`.

The primary is the mean of `e(s,coherent,0)`. A common per-seed denominator is
used for all control contrasts; this is the mean of paired ratios, not a ratio
of group means. Report raw paired AUC differences, fractions, paired standard
deviations, and Cohen's paired `d_z = mean / sd`. A zero-variance standardized
effect is undefined and represented as JSON null. Very large d_z values under
tiny initialization noise are not measures of physical importance.

Resample the **entire seed block**, keeping both dynamics, all angles, and all
conditions together. Report percentile 95% intervals for paired raw and
normalized means and d_z. The planned endpoint does not depend on selecting an
angle after viewing the curve. Also report approximate simultaneous 95% bands
over all three angle-contrast curves, using the bootstrap maximum absolute
centered deviation divided by each contrast's observed standard error.
The exact 90-degree zero contrasts are excluded from standardization.

The material-effect claim passes only if all of these hold:

- Energy and direct noninteraction numerical gates pass.
- The primary endpoint's 95% interval lies entirely above +0.01.
- The simultaneous bands for **every sampled angle** of both the shuffled and
  separated controls lie entirely inside [-0.01, +0.01]. A nonsignificant null
  alone is insufficient; this is an equivalence requirement.
- The paired coherent-minus-shuffled and coherent-minus-separated endpoint
  intervals each lie entirely above +0.01.

Verdicts:

- `PASS_MATERIAL_TOY_ORIENTATION_EFFECT`: all gates pass.
- `INVALID_CONTROL_PASS`: energy matching or direct noninteraction fails.
- `FAIL_PRESPECIFIED_MATERIAL_ADVANTAGE`: valid numerical controls and the upper
  primary interval is below +0.01. Report any statistical control failures too.
- `INCONCLUSIVE_OR_CONTROLS_FAIL`: remaining cases, including an interval that
  straddles the threshold or a material primary with inadequate null controls.

Small positive effects may be estimated precisely and still fail the declared
material threshold. A failure does not establish an identically zero effect.
Bootstrap uncertainty describes initialization and orientation-shuffle
variation under this numerical setup. It excludes discretization, model-form,
parameter, and physical uncertainty. A material positive claim requires a
subsequent timestep/resolution check; the present gate alone is not numerical
convergence or physical validation.

## Reproduction and retained record

From the repository root:

```bash
python -m pip install -e ".[test]"
python -m echofoam_falsifiability.orientation_control_pass --seeds 24 --seed 0 --workers 4 --angle-step 5 --bootstraps 10000 --bootstrap-seed 20260913 --material-fraction 0.01 --output orientation_control_output
pytest
```

The run writes `manifest.json` before generating outcomes, including seeds,
parameters, threshold, software versions, source revision, and SHA-256 hashes
of both implementation files and this protocol. `runs.csv` retains each
seed/condition/angle measurement; `effects.csv` and `summary.json` retain paired
statistics, simultaneous bands, numerical diagnostics, and all decision gates.
Existing output directories are rejected to preserve previous runs.

`--workers` changes only independent seed scheduling. Random generators are
local to each seed; output rows and bootstrap inputs retain seed order. The
default is one process, and the retained complete run uses four. An initial
serial invocation was interrupted for runtime reasons before a complete
summary; no scientific settings or decision criteria changed on restarting.

Do not pool angle samples or bootstrap resamples as independent realizations.
There are 24 independent seed blocks in the confirmatory sweep.
