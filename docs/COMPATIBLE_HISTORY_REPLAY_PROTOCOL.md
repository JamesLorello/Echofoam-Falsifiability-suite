# Compatible-History Replay Protocol

Status: first controlled pass of the deterministic toy kernel. This is an
implementation check, not a physical test.

## Question

Can two histories that end at the same present field generate different
retained memory, and does continuing the kernel from that shared present field
produce different futures?

## Matched histories

For each seed, make a positive periodic present field `F*` and a spatial mode
`H`. Construct two prescribed field tapes with the same start and endpoint:

```text
F_A(t) = F* + a sin(pi t / T) H
F_B(t) = F* - a sin(pi t / T) H
```

The excursion amplitude is `a = 0.03`. Both tapes begin and end at exactly
`F*`. `M` starts at zero and is advanced across each consecutive pair of tape
frames with `advance_memory`, the same signed write, transport, diffusion, and
relaxation update used by `step`. No memory field is manually seeded.

The tapes are controlled inputs. They are not autonomous solutions of the
field equation, and their construction does not show that a real system would
produce them. Because the kernel's material derivative can write memory even
for a grid-stationary field under nonzero background flow, a repeated-`F*`
stationary tape supplies a common baseline `M*`. The history-specific writes
`M_A - M*` and `M_B - M*` are amplitude-matched by construction.

At the endpoint, both continuations start from the exact same `F*`, retaining
their separately generated full `M_A` and `M_B` fields.

## Frozen run settings

- 24 paired phase seeds: `20260924` through `20260947`
- Grid: `32 x 32`
- History: 100 steps
- Continuation: 100 steps
- Excursion amplitude: `0.03`
- Kernel parameters: `Parameters()` defaults recorded in `summary.json`
- Uncertainty summary: 10,000 paired seed-bootstrap resamples, percentile 95%
  interval

Primary observable at the end of continuation:

```text
D_F = RMS(F_A - F_B) / RMS(F*)
```

Controls reset both memories to zero, set `kappa=0`, rotate each memory vector
by 90 degrees, and spatially shuffle vector pairs while preserving their
distribution. The same shuffle is applied to both members of each pair.

## Decision rule

The software-level check passes when all conditions hold:

1. The two endpoint fields match within `1e-12` maximum absolute error.
2. Their history-generated memory fields differ by more than `1e-12` RMS.
3. The lower endpoint of the paired seed-bootstrap interval for `D_F` exceeds
   `1e-12`.
4. The zero-memory and `kappa=0` controls have paired future separation no
   greater than `1e-12`.
5. The baseline-corrected history writes remain amplitude-matched within
   `1e-12` RMS.

These thresholds are numerical checks for this deterministic assay. They are
not empirical effect thresholds.

## First-pass result (2026-09-24)

The check passed. The mean RMS difference between the two retained memory
fields was `0.00101615`; their baseline-corrected history writes each had RMS
`0.000508073`. The mean final relative future-field separation was
`2.04649e-5` (paired seed-bootstrap 95% interval
`[2.04648696e-5, 2.04648696e-5]`). The zero-memory and feedback-off controls
both produced exactly zero separation.

The spatially shuffled control produced mean separation `7.02912e-6`, below
the history-matched result. The 90-degree-rotated control produced
`4.26554e-5`, above the unrotated result. This run therefore does not support
a claim that the unrotated memory direction is optimal. It shows that the
future response depends on the spatial and directional arrangement of the
explicit memory field in this kernel.

The intervals describe variability over the declared synthetic phase seeds.
The very narrow intervals reflect near-invariance across those phases; they
are not uncertainty bounds for a physical process.

## Reproduction

From the repository root:

```bash
python -m pip install -e ".[test]"
python -m echofoam_falsifiability.compatible_history_replay --pairs 24 --size 32 --history-steps 100 --future-steps 100 --seed 20260924 --bootstraps 10000 --output results/compatible_history_replay_2026-09-24
python -m pytest -q tests/test_local_dynamical_memory.py tests/test_compatible_history_replay.py
```

`summary.json` records parameters, decision checks, intervals, Git revision,
and source hashes. `runs.csv` records the per-seed outcomes.

## Interpretation limits

A pass shows that prescribed compatible field histories write different
memory through the implemented update and that this memory changes later
evolution in the deterministic toy kernel. The assay does not demonstrate
autonomous convergence of distinct histories, distinguish the law from
standard internal-variable or hysteresis models, or establish physical
validation.
