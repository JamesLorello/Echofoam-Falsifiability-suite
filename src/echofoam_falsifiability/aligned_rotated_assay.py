"""Aligned-vs-rotated interaction assay.

Tests whether relative internal orientation changes interaction-region persistence
beyond a matched linear superposition baseline.

This is a toy nonlinear vector-field assay. It is not a model of gravity,
spacetime, dark matter, dark energy, or quantum measurement.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Params:
    N: int = 96
    L: float = 24.0
    dt: float = 0.008
    steps: int = 1500
    sample_every: int = 10
    D: float = 0.18
    gamma: float = 0.30
    beta: float = 1.10
    delta: float = 0.85
    target_energy: float = 1.0
    interaction_radius: float = 2.2


def lap(a: np.ndarray, dx: float) -> np.ndarray:
    return (
        np.roll(a, 1, 0) + np.roll(a, -1, 0)
        + np.roll(a, 1, 1) + np.roll(a, -1, 1)
        - 4 * a
    ) / dx**2


def build_geometry(p: Params):
    x = np.linspace(-p.L / 2, p.L / 2, p.N, endpoint=False)
    X, Y = np.meshgrid(x, x, indexing="ij")
    g1 = np.exp(-((X / 4.0) ** 2 + (Y / 1.15) ** 2))
    g2 = np.exp(-((X / 1.15) ** 2 + (Y / 4.0) ** 2))
    mask = (X**2 + Y**2) <= p.interaction_radius**2
    return g1, g2, mask


def init_field(condition: str, seed: int, p: Params, g1, g2):
    rng = np.random.default_rng(seed)
    noise_u = rng.normal(0.0, 0.003, size=(p.N, p.N))
    noise_v = rng.normal(0.0, 0.003, size=(p.N, p.N))

    if condition == "aligned":
        u, v = g1 + g2 + noise_u, noise_v
    elif condition == "rotated":
        u, v = g1 + noise_u, g2 + noise_v
    else:
        raise ValueError(condition)

    dx = p.L / p.N
    energy = np.sum(u * u + v * v) * dx * dx
    scale = np.sqrt(p.target_energy / energy)
    return u * scale, v * scale


def run_one(condition: str, seed: int, nonlinear: bool, p: Params):
    dx = p.L / p.N
    g1, g2, mask = build_geometry(p)
    u, v = init_field(condition, seed, p, g1, g2)
    initial_local = np.sum((u * u + v * v)[mask]) * dx * dx

    times = []
    local_fraction = []

    for k in range(p.steps + 1):
        if k % p.sample_every == 0:
            local = np.sum((u * u + v * v)[mask]) * dx * dx
            times.append(k * p.dt)
            local_fraction.append(local / initial_local)

        if k == p.steps:
            break

        amp2 = u * u + v * v
        if nonlinear:
            reaction = -p.gamma + p.beta * amp2 - p.delta * amp2 * amp2
        else:
            reaction = -p.gamma

        u = u + p.dt * (p.D * lap(u, dx) + reaction * u)
        v = v + p.dt * (p.D * lap(v, dx) + reaction * v)

    times = np.asarray(times)
    local_fraction = np.asarray(local_fraction)
    persistence = np.trapezoid(local_fraction, times)
    crossing = np.where(local_fraction <= 0.5)[0]
    half_life = times[crossing[0]] if len(crossing) else times[-1]
    return persistence, half_life


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=24)
    args = parser.parse_args()
    p = Params()

    results = {}
    for nonlinear, model in [(True, "nonlinear"), (False, "linear_ablation")]:
        for condition in ["aligned", "rotated"]:
            values = [run_one(condition, seed, nonlinear, p)[0] for seed in range(args.seeds)]
            results[(model, condition)] = np.asarray(values)
            print(model, condition, f"mean AUC={np.mean(values):.6f}")

    raw = np.mean(results[("nonlinear", "aligned")] - results[("nonlinear", "rotated")])
    linear = np.mean(results[("linear_ablation", "aligned")] - results[("linear_ablation", "rotated")])
    dod = raw - linear

    print(f"raw aligned-minus-rotated nonlinear AUC: {raw:.6f}")
    print(f"linear aligned-minus-rotated baseline AUC: {linear:.6f}")
    print(f"difference-of-differences: {dod:.6f}")


if __name__ == "__main__":
    main()
