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
