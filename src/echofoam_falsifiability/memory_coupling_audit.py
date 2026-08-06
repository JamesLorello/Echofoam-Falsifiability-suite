"""Matched-control assay for delayed memory and spatial pattern claims."""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

BRANCHES = ("full_memory", "no_memory", "shuffled_memory", "instant_feedback")


@dataclass(frozen=True)
class Parameters:
    diffusion_psi: float
    beta: float
    diffusion_tau: float
    memory_strength: float
    memory_half_life: float
    a: float
    b: float


def sample_parameters(rng: np.random.Generator) -> Parameters:
    return Parameters(
        diffusion_psi=float(rng.uniform(0.1, 1.0)),
        beta=float(rng.uniform(0.0, 1.0)),
        diffusion_tau=float(rng.uniform(0.1, 1.0)),
        memory_strength=float(rng.uniform(0.1, 1.0)),
        memory_half_life=float(rng.uniform(10.0, 50.0)),
        a=float(rng.uniform(-1.0, 1.0)),
        b=float(rng.uniform(0.1, 1.0)),
    )


def laplacian(field: np.ndarray, dx: float) -> np.ndarray:
    return (
        np.roll(field, 1, 0) + np.roll(field, -1, 0)
        + np.roll(field, 1, 1) + np.roll(field, -1, 1)
        - 4.0 * field
    ) / dx**2


def div_psi_grad_tau(psi: np.ndarray, tau: np.ndarray, dx: float) -> np.ndarray:
    grad_x = (np.roll(tau, -1, 1) - np.roll(tau, 1, 1)) / (2.0 * dx)
    grad_y = (np.roll(tau, -1, 0) - np.roll(tau, 1, 0)) / (2.0 * dx)
    flux_x, flux_y = psi * grad_x, psi * grad_y
    return (
        np.roll(flux_x, -1, 1) - np.roll(flux_x, 1, 1)
        + np.roll(flux_y, -1, 0) - np.roll(flux_y, 1, 0)
    ) / (2.0 * dx)


def radial_metrics(field: np.ndarray, dx: float) -> dict[str, float]:
    centered = field - np.mean(field)
    power = np.abs(np.fft.fft2(centered)) ** 2
    n = field.shape[0]
    freq = np.fft.fftfreq(n, d=dx)
    kx, ky = np.meshgrid(freq, freq)
    bins = np.floor(np.sqrt(kx**2 + ky**2) / (1.0 / (n * dx))).astype(int)
    sums = np.bincount(bins.ravel(), weights=power.ravel())
    counts = np.bincount(bins.ravel())
    radial = np.divide(sums, counts, out=np.zeros_like(sums), where=counts > 0)
    nonzero = radial[1:]
    if nonzero.size < 2 or np.sum(nonzero) <= 0:
        return {"k_star": 0.0, "prominence": 0.0, "spectral_entropy": 0.0}
    peak = int(np.argmax(nonzero)) + 1
    probabilities = nonzero / np.sum(nonzero)
    entropy = -np.sum(probabilities * np.log(probabilities + 1e-30))
    entropy /= np.log(len(probabilities))
    return {
        "k_star": float(peak / (n * dx)),
        "prominence": float(radial[peak] / (np.mean(nonzero) + 1e-30)),
        "spectral_entropy": float(entropy),
    }


def simulate(
    params: Parameters,
    branch: str,
    psi0: np.ndarray,
    tau0: np.ndarray,
    rng: np.random.Generator,
    *,
    steps: int,
    dt: float,
    dx: float,
) -> dict[str, float | bool | str]:
    psi, tau = psi0.copy(), tau0.copy()
    memory = np.zeros_like(psi)
    shuffled = rng.permutation(psi0.ravel()).reshape(psi0.shape)
    decay = np.log(2.0) / params.memory_half_life
    initial_variance = float(np.var(psi))
    bounded = True

    for _ in range(steps):
        if branch == "full_memory":
            memory += dt * decay * (psi - memory)
            target, coupling = memory, params.memory_strength
        elif branch == "shuffled_memory":
            shuffled += dt * decay * (psi - shuffled)
            target = rng.permutation(shuffled.ravel()).reshape(psi.shape)
            coupling = params.memory_strength
        elif branch == "instant_feedback":
            target, coupling = psi, params.memory_strength
        elif branch == "no_memory":
            target, coupling = tau, 0.0
        else:
            raise ValueError(f"unknown branch: {branch}")

        psi_dot = (
            params.diffusion_psi * laplacian(psi, dx)
            - (params.a * psi + params.b * psi**3)
            + params.beta * div_psi_grad_tau(psi, tau, dx)
        )
        tau_dot = params.diffusion_tau * laplacian(tau, dx) + coupling * (target - tau)
        psi += dt * psi_dot
        tau += dt * tau_dot

        if not (np.all(np.isfinite(psi)) and np.all(np.isfinite(tau))):
            bounded = False
            break
        if max(float(np.max(np.abs(psi))), float(np.max(np.abs(tau)))) > 1e4:
            bounded = False
            break

    metrics = radial_metrics(psi, dx) if bounded else {
        "k_star": float("nan"),
        "prominence": float("nan"),
        "spectral_entropy": float("nan"),
    }
    final_variance = float(np.var(psi)) if bounded else float("nan")
    correlation = 0.0
    if bounded and np.std(psi) > 0 and np.std(tau) > 0:
        correlation = float(np.corrcoef(psi.ravel(), tau.ravel())[0, 1])
    return {
        "branch": branch,
        "bounded": bounded,
        "initial_variance": initial_variance,
        "final_variance": final_variance,
        "variance_ratio": final_variance / (initial_variance + 1e-30),
        "psi_tau_corr": correlation,
        **metrics,
    }


def run_assay(
    *,
    runs: int = 24,
    steps: int = 1200,
    size: int = 64,
    dt: float = 0.02,
    dx: float = 1.0,
    seed: int = 50,
) -> tuple[list[dict], dict]:
    rows: list[dict] = []
    for run in range(runs):
        parameter_seed = seed + run
        rng = np.random.default_rng(parameter_seed)
        params = sample_parameters(rng)
        psi0 = rng.normal(0.0, 0.1, (size, size))
        tau0 = rng.normal(0.0, 0.1, (size, size))
        for branch_index, branch in enumerate(BRANCHES):
            branch_rng = np.random.default_rng(parameter_seed * 100 + branch_index)
            rows.append({
                "run": run,
                "parameter_seed": parameter_seed,
                **asdict(params),
                **simulate(params, branch, psi0, tau0, branch_rng, steps=steps, dt=dt, dx=dx),
            })

    summary: dict[str, dict] = {}
    for branch in BRANCHES:
        selected = [row for row in rows if row["branch"] == branch and row["bounded"]]
        summary[branch] = {"runs": runs, "bounded_fraction": len(selected) / runs}
        for metric in ("prominence", "k_star", "spectral_entropy", "variance_ratio", "psi_tau_corr"):
            values = np.asarray([row[metric] for row in selected], dtype=float)
            summary[branch][f"median_{metric}"] = (
                float(np.nanmedian(values)) if values.size else None
            )

    full = {row["run"]: row for row in rows if row["branch"] == "full_memory"}
    paired = {}
    for control in BRANCHES[1:]:
        control_rows = {row["run"]: row for row in rows if row["branch"] == control}
        paired[control] = {}
        for metric in ("prominence", "k_star", "spectral_entropy", "variance_ratio"):
            deltas = [full[i][metric] - control_rows[i][metric] for i in full]
            paired[control][f"median_full_minus_control_{metric}"] = float(np.nanmedian(deltas))
    summary["paired_comparisons"] = paired

    box_mode = 1.0 / (size * dx)
    summary["audit_diagnostics"] = {
        "lowest_nonzero_box_mode": box_mode,
        "full_branch_peak_is_box_mode": bool(
            np.isclose(summary["full_memory"]["median_k_star"], box_mode)
        ),
        "interpretation_guard": (
            "A memory-specific effect requires paired separation from controls. "
            "Correlation alone establishes tracking inside the toy model."
        ),
    }
    return rows, summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=24)
    parser.add_argument("--steps", type=int, default=1200)
    parser.add_argument("--size", type=int, default=64)
    parser.add_argument("--dt", type=float, default=0.02)
    parser.add_argument("--dx", type=float, default=1.0)
    parser.add_argument("--seed", type=int, default=50)
    parser.add_argument("--output", type=Path, default=Path("audit_output"))
    args = parser.parse_args()

    rows, summary = run_assay(
        runs=args.runs, steps=args.steps, size=args.size,
        dt=args.dt, dx=args.dx, seed=args.seed,
    )
    args.output.mkdir(parents=True, exist_ok=True)
    with (args.output / "runs.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    with (args.output / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
