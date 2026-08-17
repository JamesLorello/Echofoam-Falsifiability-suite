# Stress-Driven Blanket Fragmentation

A minimal computational assay for testing whether finite local update capacity and stress-driven rupture can generate smaller persistent statistical partitions in an adaptive network.

## Scientific status

**Current result:** the structural fragmentation transition occurs, but the
preferential-boundary claim has triggered its falsifier. Stress-selected rupture
did not outperform rupture-count- and rupture-time-matched random locations in
the original test or after anchoring the collective memory mode.

**Decision:** retire the v0 local stress-selection rule as a candidate mechanism
for preferentially discovering dynamically coherent boundaries.

This repository is a mechanism-level toy model. It does not claim a derivation of physical relativity, biological Markov blankets, or cosmological dynamics.

## Primitive model

Each observer carries a persistent, alterable memory vector `m_i`.

An interaction is considered committed when it changes that state and thereby constrains later dynamics.

Local coherent interaction is modeled through nearest-neighbor corrective currents:

```text
J_ij = K (m_j - m_i)
```

Observers have finite update bandwidth:

```text
|dm_i/dt| <= omega_max
```

A local shear proxy combines state mismatch and update-rate mismatch:

```text
S_ij = alpha |m_i - m_j| + beta |dm_i/dt - dm_j/dt|
```

Damage accumulates only above a critical stress. Links rupture when accumulated overload exceeds threshold.

No target cluster count, target blanket size, or preferred fragmentation scale is encoded.

## v0 hypothesis

If a large coherent structure exceeds its update/shear capacity while smaller local subsets remain viable, increasing drive should produce:

```text
one large component
-> several smaller components
-> many small components
-> near-singletons
```

The stronger claim is that stress-selected rupture should discover statistically better boundaries than equally many random ruptures.

## v0 result

The structural fragmentation transition appeared clearly around drive 1.3-1.4.

However, matched-random rupture produced essentially the same within-versus-across correlation separation:

- drive 1.3: stress 0.061, matched random 0.063
- drive 1.4: stress 0.225, matched random 0.239

Therefore v0 demonstrates a drive-dependent fragmentation transition with
statistical differentiation, but it does not demonstrate preferential discovery
of Markov blankets. The 64-seed anchored repair rerun strengthened this negative
result. At drive 1.4, the paired stress-minus-random separation was `-0.01847`
with a bootstrap 95% interval of `[-0.03506, -0.00218]`.

See `docs/anchored_collective_mode_result_2026-08-17.md` for the locked
discriminator, validity checks, full results, and retirement decision.

## Next falsifier

v1 should:

1. Allow broken links to reform.
2. Replace simple correlation with predictive shielding / conditional-dependence measures.
3. Test whether arbitrary cuts heal while persistently overloaded boundaries remain.
4. Preserve matched-random, shuffled-stress, reversed-stress, fixed-topology, and ablation controls.
5. Avoid any global coherence gate or hand-coded target partition.

A strong positive result would show that local dynamics select partitions that reduce cross-boundary update burden while preserving internal predictive information.

## Run

```bash
python src/blanket_fragmentation_v0.py
```

Dependencies:

```bash
pip install -r requirements.txt
```

## Repository layout

```text
src/
  blanket_fragmentation_v0.py
results/
  v0_transition_summary.csv
  v0_matched_random_control.csv
  blanket_fragmentation_transition.png
  blanket_statistical_separation.png
docs/
  v0_experiment_note.md
```

## Reproducibility note

The current script uses explicit seeds and fixed simulation parameters. Before treating future parameter sweeps as confirmatory, lock the parameter range, statistics, controls, and multiple-comparison procedure in advance.
