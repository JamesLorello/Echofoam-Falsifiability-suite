"""Minimal periodic 2D realization of LOCAL_DYNAMICAL_MEMORY_KERNEL.md.

F is a real scalar field with shape (ny, nx); M has shape (2, ny, nx),
with components (Mx, My). All quantities are dimensionless toy variables.
The local reaction is R(F) = -gamma_F * F. No physical identification is made.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, replace

import numpy as np


@dataclass(frozen=True)
class Parameters:
    dx: float = 0.5
    dt: float = 0.02
    velocity: tuple[float, float] = (0.2, -0.1)
    D_F: float = 0.1
    D_M: float = 0.05
    gamma_F: float = 0.05
    gamma_M: float = 0.1
    alpha: float = 0.5
    kappa: float = 0.5
    max_abs: float = 1e6

    def __post_init__(self) -> None:
        scalars = (self.dx, self.dt, self.D_F, self.D_M, self.gamma_F,
                   self.gamma_M, self.alpha, self.kappa, self.max_abs)
        if len(self.velocity) != 2 or not np.isfinite((*scalars, *self.velocity)).all():
            raise ValueError("parameters must be finite; velocity must contain (Vx, Vy)")
        if min(self.dx, self.dt, self.max_abs) <= 0:
            raise ValueError("dx, dt, and max_abs must be positive")
        if min(self.D_F, self.D_M, self.gamma_F, self.gamma_M, self.alpha, self.kappa) < 0:
            raise ValueError("diffusion, relaxation, write, and feedback rates must be nonnegative")


def gradient(a: np.ndarray, dx: float) -> np.ndarray:
    """Periodic centered (x, y) gradient of a scalar array."""
    return np.stack([
        (np.roll(a, -1, axis) - np.roll(a, 1, axis)) / (2 * dx)
        for axis in (-1, -2)
    ])


def laplacian(a: np.ndarray, dx: float) -> np.ndarray:
    """Periodic five-point Laplacian, componentwise for vector arrays."""
    return sum(
        (np.roll(a, -1, axis) - 2 * a + np.roll(a, 1, axis)) / dx**2
        for axis in (-1, -2)
    )


def advection(a: np.ndarray, velocity, dx: float) -> np.ndarray:
    """Upwind discretization of velocity dot grad(a), not a flux divergence."""
    return sum(
        (np.maximum(v, 0) * (a - np.roll(a, 1, axis))
         + np.minimum(v, 0) * (np.roll(a, -1, axis) - a)) / dx
        for v, axis in zip(velocity, (-1, -2))
    )


def _fields(F, M, p: Parameters) -> tuple[np.ndarray, np.ndarray]:
    if np.iscomplexobj(F) or np.iscomplexobj(M):
        raise ValueError("this minimal kernel accepts real fields only")
    F, M = np.asarray(F, dtype=float), np.asarray(M, dtype=float)
    if F.ndim != 2 or min(F.shape) < 3 or M.shape != (2, *F.shape):
        raise ValueError("F must be (ny, nx), ny/nx >= 3; M must be (2, ny, nx)")
    if not np.isfinite(F).all() or not np.isfinite(M).all():
        raise FloatingPointError("nonfinite field or memory")
    if max(np.max(np.abs(F)), np.max(np.abs(M))) > p.max_abs:
        raise FloatingPointError("field or memory exceeded max_abs; no clipping is applied")
    return F, M


def step(F, M, p: Parameters = Parameters()) -> tuple[np.ndarray, np.ndarray]:
    """Advance without mutating inputs; new memory first acts on the next step.

    F uses upwind transport at V + kappa*M and centered diffusion. The signed
    material write increment is grad|F_new| - grad|F| + dt * V.dot.grad(grad|F|).
    This uses the SAME constant-V upwind operator as field/memory transport.
    It cancels rigid numerical translation of a sign-definite profile up to
    roundoff. At zeros of F, the finite difference of |F| defines the write.

    The CFL guards enforce monotone homogeneous transport/diffusion/decay
    steps. They are not a convergence or stability proof for the sourced loop.
    """
    F, M = _fields(F, M, p)
    with np.errstate(over="raise", invalid="raise", divide="raise"):
        velocity = (p.velocity[0] + p.kappa * M[0],
                    p.velocity[1] + p.kappa * M[1])
        field_cfl = p.dt * (np.max(np.abs(velocity[0]) + np.abs(velocity[1])) / p.dx
                            + 4 * p.D_F / p.dx**2 + p.gamma_F)
        memory_cfl = p.dt * (sum(abs(v) for v in p.velocity) / p.dx
                             + 4 * p.D_M / p.dx**2 + p.gamma_M)
        if max(field_cfl, memory_cfl) > 1:
            raise ValueError("CFL guard exceeded: reduce dt (including feedback velocity)")

        F_new = F + p.dt * (-advection(F, velocity, p.dx)
                            + p.D_F * laplacian(F, p.dx) - p.gamma_F * F)
        g = gradient(np.abs(F), p.dx)
        write = (gradient(np.abs(F_new), p.dx) - g
                 + p.dt * advection(g, p.velocity, p.dx))
        M_new = M + p.dt * (-advection(M, p.velocity, p.dx)
                            + p.D_M * laplacian(M, p.dx) - p.gamma_M * M) + p.alpha * write
    return _fields(F_new, M_new, p)


def simulate(F, M, p: Parameters = Parameters(), *, steps: int = 500):
    """Return final (F, M). Fixed inputs give deterministic trajectories."""
    if not isinstance(steps, (int, np.integer)) or isinstance(steps, bool) or steps < 0:
        raise ValueError("steps must be a nonnegative integer")
    F, M = _fields(F, M, p)
    F, M = F.copy(), M.copy()
    for _ in range(steps):
        F, M = step(F, M, p)
    return F, M


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--size", type=int, default=32)
    parser.add_argument("--steps", type=int, default=500)
    parser.add_argument("--seed", type=int, default=20260914)
    parser.add_argument("--dt", type=float, default=0.02)
    args = parser.parse_args()
    if args.size < 3 or args.steps < 1 or args.seed < 0:
        parser.error("size >= 3, steps >= 1, and seed >= 0 required")
    p = Parameters(dt=args.dt)
    y, x = np.meshgrid(2 * np.pi * np.arange(args.size) / args.size,
                       2 * np.pi * np.arange(args.size) / args.size, indexing="ij")
    rng = np.random.default_rng(args.seed)
    F0 = 1 + 0.2 * np.sin(x) + 0.15 * np.cos(y) + 0.01 * rng.standard_normal(x.shape)
    M0 = np.zeros((2, *F0.shape))
    F, M = simulate(F0, M0, p, steps=args.steps)
    Fc, Mc = simulate(F0, M0, replace(p, kappa=0), steps=args.steps)
    print(json.dumps({
        "model": "local dynamical memory, periodic real scalar F / vector M",
        "parameters": asdict(p), "size": args.size, "steps": args.steps, "seed": args.seed,
        "final_time": args.steps * p.dt,
        "field_rms_difference_from_no_feedback": float(np.sqrt(np.mean((F - Fc)**2))),
        "coupled_final_memory_rms": float(np.sqrt(np.mean(M**2))),
        "no_feedback_final_memory_rms": float(np.sqrt(np.mean(Mc**2))),
        "coupled_final_max_abs_F": float(np.max(np.abs(F))),
        "coupled_final_max_abs_M": float(np.max(np.abs(M))),
        "interpretation": "Deterministic toy dynamics with explicitly imposed feedback; no physical validation.",
    }, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
