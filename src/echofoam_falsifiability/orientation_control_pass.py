"""Prespecified, energy-matched orientation controls for the vector-field toy PDE.

See docs/ORIENTATION_CONTROL_PROTOCOL.md before interpreting a sweep. Relative
angle is a real-valued parameter; a finite numerical grid samples [0, 90] degrees.
No additional memory variable or physical interpretation is introduced here.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import subprocess
from concurrent.futures import ProcessPoolExecutor
from contextlib import nullcontext
from dataclasses import asdict, replace
from functools import partial
from pathlib import Path

import numpy as np

from .aligned_rotated_assay import Params, lap


CONDITIONS = ("coherent", "shuffled", "separated")
MATERIAL_FRACTION = 0.01
ENERGY_TOLERANCE = 1e-12
SEPARATION_TOLERANCE = 0.001
BOOTSTRAP_SEED = 20260913


def angle_grid(step: float) -> np.ndarray:
    """Include both endpoints, even when the positive real step does not divide 90."""
    if not np.isfinite(step) or not 0 < step <= 90:
        raise ValueError("angle step must be finite and in (0, 90]")
    angles = np.arange(0.0, 90.0, step)
    return np.append(angles[angles < 90.0 - 1e-10], 90.0)


def validate(p: Params) -> None:
    if not all(np.isfinite(v) for v in asdict(p).values()):
        raise ValueError("parameters must be finite")
    if p.N < 8 or p.steps < 1 or p.sample_every < 1:
        raise ValueError("N >= 8, steps >= 1, and sample_every >= 1 required")
    if min(p.L, p.dt, p.target_energy, p.interaction_radius) <= 0:
        raise ValueError("length, timestep, energy, and radius must be positive")
    if min(p.D, p.gamma, p.beta, p.delta) < 0:
        raise ValueError("this protocol requires nonnegative PDE coefficients")
    if p.interaction_radius >= p.L / 4:
        raise ValueError("observation windows must fit the separated geometry")
    if p.dt * (8 * p.D / (p.L / p.N)**2 + p.gamma) > 1:
        raise ValueError("timestep violates the nonnegative linear Fourier multiplier gate")


def sample_steps(p: Params) -> np.ndarray:
    return np.unique(np.append(np.arange(0, p.steps + 1, p.sample_every), p.steps))


def geometry(p: Params, separated: bool = False):
    x = np.linspace(-p.L / 2, p.L / 2, p.N, endpoint=False)
    X, Y = np.meshgrid(x, x, indexing="ij")
    offset = p.L / 4 if separated else 0.0

    def distance(z, center):
        return (z - center + p.L / 2) % p.L - p.L / 2

    X1, Y1 = distance(X, -offset), distance(Y, -offset)
    X2, Y2 = distance(X, offset), distance(Y, offset)
    a = np.exp(-((X1 / 4.0)**2 + (Y1 / 1.15)**2))
    b = np.exp(-((X2 / 1.15)**2 + (Y2 / 4.0)**2))
    mask = ((X1**2 + Y1**2) <= p.interaction_radius**2)
    mask |= ((X2**2 + Y2**2) <= p.interaction_radius**2)
    return a, b, mask


def initial_fields(angles, seed: int, condition: str, p: Params, noise: float = 0.003):
    """Return matched fields, their packet parts, mask, and common energy density.

    A common pointwise amplitude removes initial global AND local energy
    differences. Noise is attached to packet amplitudes so rotating an isolated
    packet cannot change its relation to an unrelated background-noise vector.
    """
    angles = np.asarray(angles, dtype=float)
    if angles.ndim != 1 or not len(angles) or not np.all(np.isfinite(angles)):
        raise ValueError("angles must be a nonempty finite one-dimensional array")
    if np.any((angles < 0) | (angles > 90)) or condition not in CONDITIONS:
        raise ValueError("unknown condition or angle outside [0, 90]")
    if not np.isfinite(noise) or noise < 0:
        raise ValueError("noise must be finite and nonnegative")
    a, b, mask = geometry(p, separated=condition == "separated")
    rng = np.random.default_rng(seed)
    a *= np.exp(noise * rng.standard_normal(a.shape) - 0.5 * noise**2)
    b *= np.exp(noise * rng.standard_normal(b.shape) - 0.5 * noise**2)
    density = a*a + b*b
    density *= p.target_energy / (np.sum(density) * (p.L / p.N)**2)
    theta = np.deg2rad(angles)[:, None, None]
    if condition == "shuffled":
        # Balanced full-circle orientation bank with a random common offset,
        # then a spatial permutation. Its law is invariant under theta shifts.
        shuffle_rng = np.random.default_rng(np.random.SeedSequence([seed, 731]))
        bank = 2 * np.pi * np.arange(p.N*p.N) / (p.N*p.N)
        bank += shuffle_rng.uniform(0, 2 * np.pi)
        theta = theta + shuffle_rng.permutation(bank).reshape(p.N, p.N)
    raw_u, raw_v = a + b * np.cos(theta), b * np.sin(theta)
    magnitude = np.hypot(raw_u, raw_v)
    if np.any(magnitude == 0):
        raise FloatingPointError("exact packet cancellation makes matched orientation undefined")
    scale = np.sqrt(density)[None, :, :] / magnitude
    u, v = scale * raw_u, scale * raw_v
    # Keep the decomposition for independent-packet evolution diagnostics.
    parts = (scale * a, np.zeros_like(u), scale * b * np.cos(theta), scale * raw_v)
    return u, v, parts, mask, density


def energy(u, v, mask, dx):
    return np.sum((u*u + v*v)[:, mask], axis=-1) * dx**2


def evolve(u, v, p: Params):
    """Explicit Euler, identical stencil and reaction to the original assay."""
    u, v = u.copy(), v.copy()
    dx = p.L / p.N
    for k in range(p.steps + 1):
        if k % p.sample_every == 0 or k == p.steps:
            if not np.isfinite(u).all() or not np.isfinite(v).all():
                raise FloatingPointError("nonfinite nonlinear trajectory")
            if max(np.max(np.abs(u)), np.max(np.abs(v))) > 1e6:
                raise FloatingPointError("nonlinear trajectory exceeded the boundedness guard")
            yield k, u, v
        if k == p.steps:
            break
        amp2 = u*u + v*v
        reaction = -p.gamma + p.beta * amp2 - p.delta * amp2*amp2
        new_u = u + p.dt * (p.D * lap(u, dx) + reaction*u)
        v = v + p.dt * (p.D * lap(v, dx) + reaction*v)
        u = new_u


def nonlinear_curves(u, v, mask, p: Params):
    e0 = energy(u, v, mask, p.L / p.N)
    return np.stack([
        energy(ut, vt, mask, p.L / p.N) / e0 for _, ut, vt in evolve(u, v, p)
    ], axis=-1)


def linear_curves(u, v, mask, p: Params):
    """Analytic solution of the SAME finite-difference Euler linear recurrence.

    Fourier mode multiplier = 1 + dt * (D * lambda_h - gamma).
    This avoids confounding baseline subtraction with a different integrator.
    """
    dx = p.L / p.N
    s = np.sin(np.pi * np.fft.fftfreq(p.N))**2
    eigenvalues = -4 * (s[:, None] + s[None, :]) / dx**2
    multiplier = 1 + p.dt * (p.D * eigenvalues - p.gamma)
    fu, fv = np.fft.fft2(u), np.fft.fft2(v)
    e0 = energy(u, v, mask, dx)
    values = []
    for k in sample_steps(p):
        uk = np.fft.ifft2(fu * multiplier**k).real
        vk = np.fft.ifft2(fv * multiplier**k).real
        values.append(energy(uk, vk, mask, dx) / e0)
    return np.stack(values, axis=-1)


def isolated_pair_curves(parts, mask, p: Params):
    """Evolve each endpoint packet independently and superpose only at readout."""
    u1, v1, u2, v2 = (a[[0, -1]] for a in parts)
    u, v = np.concatenate([u1, u2]), np.concatenate([v1, v2])
    e0 = energy(u1 + u2, v1 + v2, mask, p.L / p.N)
    values = []
    for _, uk, vk in evolve(u, v, p):
        values.append(energy(uk[:2] + uk[2:], vk[:2] + vk[2:], mask, p.L / p.N) / e0)
    return np.stack(values, axis=-1)


def auc(curves, p: Params):
    times = sample_steps(p) * p.dt
    return np.sum(0.5 * (curves[..., 1:] + curves[..., :-1]) * np.diff(times), axis=-1)


def simulate_seed(seed: int, angles, p: Params, noise: float):
    nonlinear, linear, rows = [], [], []
    max_energy_error, separation_leakage = 0.0, 0.0
    for condition in CONDITIONS:
        u, v, parts, mask, density = initial_fields(angles, seed, condition, p, noise)
        energy_error = float(np.max(np.abs(u*u + v*v - density)) / np.max(density))
        max_energy_error = max(max_energy_error, energy_error)
        nc, lc = nonlinear_curves(u, v, mask, p), linear_curves(u, v, mask, p)
        if condition == "separated":
            isolated = isolated_pair_curves(parts, mask, p)
            separation_leakage = float(np.max(np.abs(nc[[0, -1]] - isolated)))
        na, la = auc(nc, p), auc(lc, p)
        nonlinear.append(na)
        linear.append(la)
        initial_local = energy(u, v, mask, p.L / p.N)
        initial_global = np.sum(u*u + v*v, axis=(-2, -1)) * (p.L / p.N)**2
        for i, angle in enumerate(angles):
            rows.append({
                "seed": seed, "condition": condition, "angle_deg": float(angle),
                "initial_global_energy": float(initial_global[i]),
                "initial_local_energy": float(initial_local[i]),
                "nonlinear_auc": float(na[i]), "analytic_linear_auc": float(la[i]),
                "nonlinear_increment_auc": float(na[i] - la[i]),
            })
    return np.asarray(nonlinear), np.asarray(linear), rows, {
        "seed": seed, "max_pointwise_energy_relative_error": max_energy_error,
        "separated_max_normalized_curve_leakage": separation_leakage,
    }


def paired_statistics(values, indices):
    values = np.asarray(values, dtype=float)
    boot_samples = values[indices]
    boot = np.mean(boot_samples, axis=1)
    sd = float(np.std(values, ddof=1))
    boot_sd = np.std(boot_samples, axis=1, ddof=1)
    dz_ci = None
    # A constant paired contrast has no finite standardized effect size.
    if sd > 0 and np.all(boot_sd > 0):
        dz_ci = np.quantile(boot / boot_sd, [0.025, 0.975]).tolist()
    return {
        "mean": float(np.mean(values)), "ci95": np.quantile(boot, [0.025, 0.975]).tolist(),
        "paired_sd": sd, "paired_dz": float(np.mean(values) / sd) if sd > 0 else None,
        "paired_dz_ci95": dz_ci,
    }


def summarize(nonlinear, linear, angles, diagnostics, bootstraps=10000,
              bootstrap_seed=BOOTSTRAP_SEED, material_fraction=MATERIAL_FRACTION):
    """Resample entire paired seed blocks, including every angle and control."""
    if len(nonlinear) < 2 or bootstraps < 100:
        raise ValueError("at least two paired seeds and 100 bootstrap resamples required")
    delta = nonlinear - linear
    raw = delta - delta[:, :, -1:]
    reference = linear[:, 0, -1]
    if np.any(reference <= 0):
        raise FloatingPointError("nonpositive orthogonal linear reference AUC")
    fraction = raw / reference[:, None, None]
    rng = np.random.default_rng(bootstrap_seed)
    indices = rng.integers(0, len(delta), size=(bootstraps, len(delta)))
    means = np.mean(fraction, axis=0)
    se = np.std(fraction, axis=0, ddof=1) / np.sqrt(len(delta))
    bootstrap_means = np.empty((bootstraps, len(CONDITIONS), len(angles)))
    for c in range(len(CONDITIONS)):
        for a in range(len(angles)):
            bootstrap_means[:, c, a] = np.mean(fraction[:, c, a][indices], axis=1)
    active = se > 0
    if np.any(active):
        zmax = np.max(np.abs(bootstrap_means[:, active] - means[active]) / se[active], axis=1)
        critical = float(np.quantile(zmax, 0.95))
    else:
        critical = 0.0
    lower, upper = means - critical * se, means + critical * se
    curves = []
    for c, condition in enumerate(CONDITIONS):
        for a, angle in enumerate(angles):
            curves.append({
                "condition": condition, "angle_deg": float(angle),
                "nonlinear_auc_mean": float(np.mean(nonlinear[:, c, a])),
                "linear_auc_mean": float(np.mean(linear[:, c, a])),
                "paired_auc": paired_statistics(raw[:, c, a], indices),
                "paired_fraction": paired_statistics(fraction[:, c, a], indices),
                "simultaneous_fraction_ci95": [float(lower[c, a]), float(upper[c, a])],
            })
    primary = paired_statistics(fraction[:, 0, 0], indices)
    interactions = {
        name: paired_statistics(fraction[:, 0, 0] - fraction[:, c, 0], indices)
        for c, name in enumerate(CONDITIONS[1:], start=1)
    }
    gates = {
        "pointwise_energy_matched": all(
            d["max_pointwise_energy_relative_error"] <= ENERGY_TOLERANCE for d in diagnostics
        ),
        "separated_packets_effectively_noninteracting": all(
            d["separated_max_normalized_curve_leakage"] <= SEPARATION_TOLERANCE
            for d in diagnostics
        ),
        "primary_above_material_threshold": primary["ci95"][0] > material_fraction,
        "shuffled_equivalent_to_zero_across_sweep": bool(
            np.all(lower[1] > -material_fraction) and np.all(upper[1] < material_fraction)
        ),
        "separated_equivalent_to_zero_across_sweep": bool(
            np.all(lower[2] > -material_fraction) and np.all(upper[2] < material_fraction)
        ),
        "coherent_exceeds_each_control": all(
            v["ci95"][0] > material_fraction for v in interactions.values()
        ),
    }
    valid = gates["pointwise_energy_matched"] and gates["separated_packets_effectively_noninteracting"]
    if not valid:
        verdict = "INVALID_CONTROL_PASS"
    elif all(gates.values()):
        verdict = "PASS_MATERIAL_TOY_ORIENTATION_EFFECT"
    elif primary["ci95"][1] < material_fraction:
        verdict = "FAIL_PRESPECIFIED_MATERIAL_ADVANTAGE"
    else:
        verdict = "INCONCLUSIVE_OR_CONTROLS_FAIL"
    return {
        "verdict": verdict, "gates": gates, "material_fraction": material_fraction,
        "primary_paired_fraction": primary, "primary_minus_controls": interactions,
        "reference_linear_90_auc_mean": float(np.mean(reference)),
        "simultaneous_bootstrap_critical_value": critical, "curves": curves,
        "diagnostics": diagnostics,
        "scope": "Finite-grid nonlinear vector-field toy dynamics; no physical or memory claim.",
        "uncertainty_scope": "Seed variation conditional on this geometry, equation, grid, and timestep.",
    }


def revision_metadata():
    root = Path(__file__).resolve().parents[2]
    try:
        revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
        dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=root, text=True).strip())
    except (OSError, subprocess.CalledProcessError):
        revision, dirty = None, None
    paths = [Path(__file__), Path(__file__).with_name("aligned_rotated_assay.py"),
             root / "docs/ORIENTATION_CONTROL_PROTOCOL.md"]
    return {"git_revision": revision, "git_dirty": dirty, "sha256": {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in paths if path.exists()
    }}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=24)
    parser.add_argument("--seed", type=int, default=0, help="first initialization seed")
    parser.add_argument("--workers", type=int, default=1, help="independent seed processes; outputs retain seed order")
    parser.add_argument("--angle-step", type=float, default=5.0)
    parser.add_argument("--bootstrap-seed", type=int, default=BOOTSTRAP_SEED)
    parser.add_argument("--bootstraps", type=int, default=10000)
    parser.add_argument("--material-fraction", type=float, default=MATERIAL_FRACTION)
    parser.add_argument("--noise", type=float, default=0.003)
    parser.add_argument("--size", type=int, default=96)
    parser.add_argument("--dt", type=float, default=0.008)
    parser.add_argument("--steps", type=int, default=1500)
    parser.add_argument("--sample-every", type=int, default=10)
    parser.add_argument("--output", type=Path, default=Path("orientation_control_output"))
    args = parser.parse_args()
    if args.seeds < 2 or args.seed < 0 or args.bootstrap_seed < 0 or args.bootstraps < 100:
        parser.error("need >= 2 seeds, nonnegative seeds, and >= 100 bootstrap samples")
    if args.workers < 1:
        parser.error("workers must be positive")
    if not np.isfinite(args.material_fraction) or args.material_fraction <= 0:
        parser.error("material fraction must be finite and positive")
    if not np.isfinite(args.noise) or args.noise < 0:
        parser.error("noise must be finite and nonnegative")
    p = replace(Params(), N=args.size, dt=args.dt, steps=args.steps, sample_every=args.sample_every)
    validate(p)
    angles = angle_grid(args.angle_step)
    if args.output.exists():
        parser.error("output already exists; choose a new path to preserve the prior run")
    seeds = list(range(args.seed, args.seed + args.seeds))
    manifest = {
        "protocol": "docs/ORIENTATION_CONTROL_PROTOCOL.md", "params": asdict(p),
        "seeds": seeds, "angles_deg": angles.tolist(), "noise": args.noise,
        "workers": args.workers,
        "bootstrap_seed": args.bootstrap_seed, "bootstraps": args.bootstraps,
        "material_fraction": args.material_fraction,
        "energy_tolerance": ENERGY_TOLERANCE, "separation_tolerance": SEPARATION_TOLERANCE,
        "python": platform.python_version(), "numpy": np.__version__,
        "source": revision_metadata(),
        "threshold_rule": "Endpoint paired difference-of-differences / per-seed coherent linear 90 AUC",
        "time_samples_include_final_step": True,
    }
    args.output.mkdir(parents=True)
    # Write the immutable run specification BEFORE producing any outcomes.
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Material threshold fixed at {100*args.material_fraction:g}% before sweep", flush=True)
    nonlinear, linear, diagnostics = [], [], []
    pool = ProcessPoolExecutor(max_workers=args.workers) if args.workers > 1 else nullcontext()
    simulate = partial(simulate_seed, angles=angles, p=p, noise=args.noise)
    with pool as executor, (args.output / "runs.csv").open("w", newline="") as stream:
        results = executor.map(simulate, seeds) if executor else map(simulate, seeds)
        writer = None
        for seed, (n, l, rows, diagnostic) in zip(seeds, results):
            nonlinear.append(n)
            linear.append(l)
            diagnostics.append(diagnostic)
            if writer is None:
                writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
                writer.writeheader()
            writer.writerows(rows)
            stream.flush()
            print(f"Completed seed {seed} ({len(nonlinear)}/{len(seeds)})", flush=True)
    summary = summarize(np.asarray(nonlinear), np.asarray(linear), angles, diagnostics,
                        args.bootstraps, args.bootstrap_seed, args.material_fraction)
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n")
    with (args.output / "effects.csv").open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["condition", "angle_deg", "paired_auc", "auc_ci_low", "auc_ci_high",
                         "paired_fraction", "fraction_ci_low", "fraction_ci_high", "paired_dz",
                         "dz_ci_low", "dz_ci_high", "simultaneous_fraction_low", "simultaneous_fraction_high"])
        for row in summary["curves"]:
            a, f = row["paired_auc"], row["paired_fraction"]
            writer.writerow([row["condition"], row["angle_deg"], a["mean"], *a["ci95"],
                             f["mean"], *f["ci95"], f["paired_dz"],
                             *(f["paired_dz_ci95"] or [None, None]), *row["simultaneous_fraction_ci95"]])
    primary = summary["primary_paired_fraction"]
    print(summary["verdict"])
    print(f"Paired endpoint effect: {100*primary['mean']:.6f}% "
          f"(95% bootstrap CI {100*primary['ci95'][0]:.6f}%, {100*primary['ci95'][1]:.6f}%)")
    print(json.dumps(summary["gates"], indent=2))


if __name__ == "__main__":
    main()
