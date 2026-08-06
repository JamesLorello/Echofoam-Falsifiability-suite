# Falsifiable Coherence and Memory Assays

[![DOI](https://zenodo.org/badge/961712182.svg)](https://doi.org/10.5281/zenodo.15505391)

This repository preserves the historical **Echofoam Falsifiability Suite** while rebuilding it as a mechanism-first collection of reproducible numerical assays.

## Scientific status

This codebase is a sandbox for testing explicit dynamical mechanisms. It is not a validated theory of cosmology, gravity, consciousness, dark matter, or dark energy.

| Item | Current status |
| --- | --- |
| Legacy animation suite | Demonstration code; does not discriminate physical hypotheses |
| Emergent propagation speed vCF-1.1 | Falsified: measured speed about 0.3559 versus prediction 1 |
| Legacy BAO-like visual outputs | Unverified until raw outputs and matched controls are recovered |
| Delayed-memory pattern claim | Retired by matched controls; behavior is consistent with diffusion and box-scale coarsening |
| Ledger/fatigue separation | Toy-model behavior, internally testable, physical interpretation unresolved |
| Present-gated history effect | Open; counts only if the gate emerges from local dynamics |

See [Scientific Status](docs/SCIENTIFIC_STATUS.md) for the evidence boundary and [Repository Map](docs/REPOSITORY_MAP.md) for the migration plan.

## Canonical assay

The first canonical assay compares delayed memory against:

- no memory,
- shuffled memory,
- instantaneous feedback.

It reports boundedness, variance survival, dominant spectral scale, spectral entropy, and paired branch differences. A memory-field correlation is never treated by itself as evidence that memory generated structure.

```bash
python -m pip install -e ".[test]"
python -m echofoam_falsifiability.memory_coupling_audit --runs 24 --steps 1200
pytest
```

Outputs are written to `audit_output/runs.csv` and `audit_output/summary.json`.

## Repository policy

- `src/echofoam_falsifiability/` is the only canonical Python package.
- Root-level scripts and duplicate modules are retained temporarily as legacy material.
- Tests must evaluate observables or invariants, not merely whether a visualization opens.
- Every claimed mechanism needs matched null, shuffled, ablated, or instantaneous controls.
- Raw results, parameters, seeds, code revision, and analysis criteria must travel together.
- Negative results and falsified versions remain part of the record.

## Historical citation

Lorello, James. *Echofoam Falsifiability Suite v1.0*. Zenodo.  
DOI: [10.5281/zenodo.15505391](https://doi.org/10.5281/zenodo.15505391)

The DOI refers to the historical release. Claims in that release should be read with the status qualifications in this repository.
