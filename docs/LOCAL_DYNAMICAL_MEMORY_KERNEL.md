# Local Dynamical Memory Kernel

Status: toy-model mechanism kernel, not a validated physical theory.

## Purpose

This kernel isolates the smallest mechanism currently supported by the numerical assays: local field deformation writes a directional memory, that memory is transported and relaxed, and later field evolution depends on the memory's direction, location, and timing.

## Variables

Let `F(x,t)` be the evolving field and let `A=|F|` be its local amplitude. Let `M(x,t)` be a vector memory field.

## Memory write law

The memory source is the signed material derivative of the amplitude gradient:

`S_M = D(grad A)/Dt`

with

`D/Dt = partial_t + V dot grad`.

Memory evolves as

`partial_t M + V dot grad M = D_M Laplacian(M) - gamma_M M + alpha S_M`.

Interpretation: stable gradients do not continuously rewrite memory. Memory is deposited when the local gradient changes, and the signed direction of that change is retained.

Here "stable" means unchanged along the background flow `V`. A gradient that is stationary at fixed grid points can still have a nonzero material derivative when `V dot grad(grad A)` is nonzero.

## Feedback law

The retained memory acts directionally on later evolution:

`partial_t F + V dot grad F = D_F Laplacian(F) + R(F) - kappa (M dot grad) F`.

`R(F)` is the baseline local field dynamics. The memory term behaves as a history-dependent directional transport/drag contribution.

## Assay results supporting the kernel

### Directional specificity

Rotating the memory vector before feedback produced a smooth angular persistence law. In the retained sweep, persistence decreased from about 2.253 at 0 degrees to about 2.008 at 180 degrees, a decline of about 10.87%. A first-harmonic description fit the sweep with R^2 about 0.999984. This establishes only that the constructed coupling is strongly direction-sensitive.

### Spatial specificity

Keeping memory at the location where it was written increased persistence by about 5.08% relative to no memory. Scrambling the same vector pairs across the domain reduced the effect to about 0.003% above baseline. In this toy system, the effect therefore depends on local correspondence between memory and field history.

### Temporal specificity

Using increasingly delayed memory snapshots reduced persistence monotonically. In the retained assay:

- delay 0.00: persistence AUC about 2.05535
- delay 0.04: about 2.05066
- delay 0.10: about 2.04388
- delay 0.20: about 2.03323
- delay 0.40: about 2.01428
- delay 0.60: about 1.99827

Over this tested interval, the descriptive linear fit had R^2 about 0.996 and negative slope about -0.0953 AUC per time unit.

## What the kernel currently earns

Within the simulation class tested so far, future persistence depends on a transported variable that encodes where local deformation occurred, the direction of that deformation, and how recently it occurred.

A concise operational statement is:

`P(future | present, local history variable) != P(future | present)`

for the toy dynamics, with the history variable represented explicitly by `M`.

## What the kernel does not establish

This does not establish that nature contains this memory field, that the mechanism is fundamental, or that it explains gravity, spacetime, quantum mechanics, dark matter, dark energy, cosmology, identity, or consciousness.

The present behavior can still arise from ordinary nonlinear PDE structure because the memory variable and feedback operator are explicitly constructed into the equations.

## Required next tests

1. Compare against passive-vector transport with no write-feedback loop.
2. Match delayed-memory amplitude distributions to rule out trivial attenuation with delay.
3. Freeze a present `F` state and replay multiple compatible histories that converge to that same present state. Test whether different retained `M` fields produce different futures.
4. Search for a prediction of the kernel that differs from standard advection-diffusion-reaction models without explicit history state.
5. Sweep `alpha`, `kappa`, `gamma_M`, `D_M`, resolution, timestep, packet geometry, and noise level.
6. Check numerical convergence and CFL/stability margins.

## Current interpretation

The strongest defensible interpretation is a minimal local dynamical memory mechanism implemented as an advected, relaxing, directional history field sourced by gradient change.

## Minimal executable realization

`src/echofoam_falsifiability/local_dynamical_memory.py` implements a deliberately small specialization of the equations above:

- `F[ny, nx]` is a real scalar field, `A = abs(F)`, and `M[2, ny, nx]` contains `(Mx, My)`.
- The rectangular 2D grid is periodic, with equal spacing `dx` in both directions and a constant background velocity `(Vx, Vy)`.
- The local reaction is `R(F) = -gamma_F F`. Diffusion, relaxation, write strength `alpha`, and feedback strength `kappa` are nonnegative. All quantities are dimensionless toy variables.
- `step(F, M, Parameters(...))` returns new arrays without mutating its inputs. `simulate(..., steps=N)` returns the final arrays; there is no hidden history buffer or random forcing.

Let `G` be the centered gradient, `L` the five-point Laplacian, and `U_v` the first-order upwind approximation of `v dot grad`, applied componentwise to vectors. One explicit step is:

```text
g = G(abs(F))
F_new = F + dt * [-U_(V + kappa M)(F) + D_F L(F) - gamma_F F]
write = G(abs(F_new)) - g + dt * U_V(g)
M_new = M + dt * [-U_V(M) + D_M L(M) - gamma_M M] + alpha * write
```

`write` approximates `dt * D(grad A)/Dt`; its sign is retained. The convective source correction uses **V**, while field feedback uses **V + kappa M**. The new memory first affects the following step. Using the same constant-velocity transport operator cancels writing from pure numerical translation of a sign-definite profile up to roundoff. At zeros of `F`, the finite difference of `abs(F)` defines the discrete source; continuum differentiability is not assumed there.

Setting `kappa=0` keeps memory writing, transport, and relaxation active while removing every influence of `M` on `F`. Setting both `alpha=0` and `kappa=0` gives a passive transported vector control. These switches are available through `Parameters`.

Each step requires both conservative sufficient bounds below to be at most one:

```text
dt * [max_grid(|Vx + kappa Mx| + |Vy + kappa My|)/dx + 4 D_F/dx^2 + gamma_F]
dt * [(|Vx| + |Vy|)/dx + 4 D_M/dx^2 + gamma_M]
```

These guards make the homogeneous transport/diffusion/decay updates monotone. In particular, the field satisfies `max|F_new| <= (1 - dt gamma_F) max|F|`. They do not prove convergence or stability of the full sourced feedback loop for arbitrary parameters. Every accepted state is also checked for finite values and a configurable absolute magnitude limit, with errors on violations and no clipping. General mass or energy conservation is not asserted: variable-velocity directional feedback is not a conservative flux divergence.

From the repository root, install and run the deterministic paired demonstration and focused tests:

```bash
python -m pip install -e ".[test]"
python -m echofoam_falsifiability.local_dynamical_memory --size 32 --steps 500 --seed 20260914 --dt 0.02
python -m pytest -q tests/test_local_dynamical_memory.py
```

The demonstration uses identical seeded `F` and zero initial `M` in coupled and `kappa=0` runs. It prints parameters, final time, field RMS difference, and memory diagnostics as JSON. The focused tests check constant and stationary-gradient states, signed writing against an analytic decaying Fourier mode, rigid periodic transport, source-free sum conservation, translation and field-sign symmetries, deterministic trajectories, finite-horizon bounds, the no-feedback control, directional feedback, and invalid or unstable input rejection. The repository's existing `python -m pytest -q` command includes these tests.

This realization does not rerun or reproduce the historical persistence percentages above, which came from different assays. A coupled/control difference demonstrates the effect of the imposed feedback term inside this discrete toy model. It does not validate a physical memory field or close the six required next tests.
