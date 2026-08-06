# Repository Map and Migration Plan

## Canonical

- `src/echofoam_falsifiability/`: maintained package code.
- `tests/`: behavioral, numerical, and scientific-regression tests.
- `docs/`: scientific status, assay definitions, and archived interpretations.
- `.github/workflows/`: reproducibility checks.

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
