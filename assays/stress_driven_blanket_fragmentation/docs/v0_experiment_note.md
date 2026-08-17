# v0 Experiment Note

## Research question

Can finite local update bandwidth plus stress-dependent rupture cause a coupled system of persistent state-bearing elements to reorganize into smaller statistically coherent structures?

## Operational definitions

**Observer**  
A persistent degree of freedom that carries an alterable internal state and whose future couplings depend on that state.

**Committed interaction**  
An interaction producing a persistent change in the carried state.

**Coherent interaction**  
An interaction whose required relational updates remain within the update/shear capacity of the interacting structure's boundary.

**Rupture**  
Local loss of coupling after accumulated overload exceeds a threshold.

## Model

N = 48 observers, each with a 2D memory vector.

Nearest-neighbor corrective coupling:
`J_ij = K(m_j - m_i)`

Finite update rate:
`|dm_i/dt| <= omega_max`

Shear proxy:
`S_ij = alpha |m_i-m_j| + beta |m_dot_i-m_dot_j|`

No partition target is specified.

## Pre-run predictions

Weak:
Increasing drive yields hierarchical fragmentation.

Strong:
Stress-selected rupture yields stronger statistical shielding than matched random rupture.

## Results

Weak prediction passed qualitatively.

Strong prediction did not pass the first discriminator. Stress-selected rupture did not outperform matched random rupture on within-versus-across correlation separation.

A small reduction in internal spread for stress-selected partitions was observed, but this is exploratory only.

## Interpretation

Connected-component separation is insufficient evidence for an emergent Markov blanket. Any cut in a locally coupled network can create statistical differentiation.

The next assay must measure predictive shielding or conditional independence and permit links to heal.

## v1 target

A convincing result would require:

- persistent internal predictive information,
- reduced conditional influence from exterior variables given an emergent boundary,
- stress-selected boundaries outperforming matched controls,
- arbitrary partitions preferentially healing,
- no global partition objective in the update rule.
