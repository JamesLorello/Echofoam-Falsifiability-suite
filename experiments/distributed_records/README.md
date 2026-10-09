# Distributed records and correction: exploratory controls

Status: **toy models / exploratory**. These scripts do not establish new physics or validate an independent memory field.

## Hypothesis under examination

An event changes present physical configurations. Later recoverability depends on distributed records and correlations, rather than a separate historical ledger. Correction may produce different patterns of reorganization depending on network structure and where the correction enters.

## Reproduce

```bash
python experiments/distributed_records/present_state_test.py
python experiments/distributed_records/distributed_memory_experiment.py
```

The second script requires NumPy. Both scripts use deterministic seeded or fixed controls.

## Interpretation boundaries

- The present-state experiment deliberately resets two different prior states to the same complete model state. Identical futures then follow by construction for deterministic Markovian dynamics; this is a sanity check, not an empirical test of the physical universe.
- Matching only position while omitting velocity, or omitting a trace variable that influences acceleration, produces divergent futures. The trace is a **present state variable**, not evidence of an independent historical field.
- The network experiment compares ring, hub, complete, and two-module graphs, with 12 nodes, a biased noisy scalar record, and a correction to a known truth value.
- Fidelity is represented by change in mean squared error relative to an uncorrected control.
- "Identity cost" is **not directly measured**: summed squared state change relative to an uncorrected baseline is merely a reorganization proxy, not physical energy, damage, or lost identity.
- The default correction is injected at node zero, which is the hub in the hub topology; comparisons are not degree-budget matched.
- The dynamics explicitly implement consensus diffusion, so topology-dependent effects are expected under conventional network theory.

## Next falsification-oriented iteration

1. Equalize total coupling budgets and compare node placements without privileging the hub.
2. Separate accurate correction from confidently incorrect interventions.
3. Generate distinct event histories and track joint information, not only scalar MSE.
4. Predeclare quantitative outcomes, margins, seed splits, null models, and stability-failure rules before interpreting a sweep.
5. Compare against conventional diffusion/consensus baselines; do not promote exploratory results into preregistered verdicts.

No existing assay verdict should be changed on the basis of these scripts.
