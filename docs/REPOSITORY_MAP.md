# Repository Map and Migration Plan

## Canonical

- `src/echofoam_falsifiability/`: maintained package code.
- `tests/`: behavioral, numerical, and scientific-regression tests.
- `docs/`: scientific status, assay definitions, and archived interpretations.
- `.github/workflows/`: reproducibility checks.

## Orientation control pass

The September 13 pass tests energy-matched orientation-dependent persistence
in the nonlinear vector-field assay. Its scope is separate from the proposed
local dynamical memory kernel.

| Purpose | Entry point |
| --- | --- |
| Prospective controls and decision rules | [Control protocol](ORIENTATION_CONTROL_PROTOCOL.md) |
| Scientific result and limitations | [Result report](ORIENTATION_CONTROL_RESULTS_2026-09-13.md) |
| Supplementary timestep and grid specification | [Numerical checks](ORIENTATION_NUMERICAL_CHECKS.md) |
| Sweep implementation and command-line entry point | [orientation_control_pass.py](../src/echofoam_falsifiability/orientation_control_pass.py) |
| Numerical invariants and decision-gate tests | [test_orientation_control_pass.py](../tests/test_orientation_control_pass.py) |
| Raw data, manifests, uncertainty, and figures | [Retained run index](../results/orientation_control_2026-09-13/README.md) |
| Figure reproduction | [plot_orientation_control.py](../scripts/plot_orientation_control.py) |

The [original two-endpoint assay](../src/echofoam_falsifiability/aligned_rotated_assay.py)
and its earlier results remain available for historical comparison.

## Legacy and pending classification

The repository currently contains duplicate modules at:

- repository root,
- `src/`,
- `src/echofoam_falsifiability/`,
- a root compatibility package.

Game, weather, laser, teleportation, art, GUI, and blockchain prototypes are preserved because they are part of the development history. They are not presently part of the scientific evidence suite.

## Migration phases

1. Establish honest status documents and a canonical matched-control assay.
2. Inventory every legacy module by hash, dependency, output, and stated claim.
3. Move unique historical prototypes under `legacy/` without rewriting their content.
4. Delete only byte-identical duplicates after their commit history is recorded.
5. Replace animation-instantiation tests with invariant and discriminator tests.
6. Attach result manifests containing seed, parameters, environment, commit SHA, and preregistered observable.
7. Tag a new release only after CI reproduces the canonical assays.

No historical file should be silently erased because a failed version is evidence about the development path.

The inventory must record `old_path`, `retained_path`, content hash, import users, associated claim, and last historical commit. Before relocation, legacy imports receive either a compatibility wrapper with a deprecation notice or a documented breaking-change decision. A duplicate is eligible for deletion only after this mapping is committed and its retained copy is verified.
