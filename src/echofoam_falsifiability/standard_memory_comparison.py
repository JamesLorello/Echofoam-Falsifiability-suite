"""Held-out comparison with a conventional Maxwell internal-variable model.

The Echofoam write law generates synthetic target trajectories. A one-mode
Maxwell model is fitted only on the training seed set by selecting a frozen
relaxation-rate / equilibrium-gain pair. This is a toy model-class comparison,
not independent empirical evidence or physical validation.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import subprocess
from dataclasses import asdict
from pathlib import Path

import numpy as np

from .compatible_history_replay import _bootstrap_mean_ci
from .f_only_adr_comparison import (
    TRAIN_FAMILIES,
    TEST_FAMILIES,
    _trajectory_error,
    make_preparation_histories,
)
from .local_dynamical_memory import (
    Parameters,
)


DEFAULT_TRAIN_SEED_START = 26092400
DEFAULT_TEST_SEED_START = 26092424
DEFAULT_SEED_COUNT = 24
MATERIAL_ERROR = 0.001
NUMERICAL_TOLERANCE = 1e-12
RELAXATION_RATES = (0.05, 0.10, 0.20, 0.40)
EQUILIBRIUM_GAINS = (0.0, 0.01, 0.05)
EXTRA_TEST_FAMILY = "heldout_diagonal_mode"


def _validate_integer(name: str, value: int, minimum: int) -> None:
    if not isinstance(value, (int, np.integer)) or isinstance(value, bool):
        raise ValueError(f"{name} must be an integer")
    if value < minimum:
        raise ValueError(f"{name} must be >= {minimum}")


def _all_histories(
    *, seed: int, size: int, history_steps: int, excursion_amplitude: float,
) -> tuple[np.ndarray, dict[str, dict[str, np.ndarray]]]:
    present, histories = make_preparation_histories(
        seed=seed, size=size, history_steps=history_steps,
        excursion_amplitude=excursion_amplitude,
    )
    rng = np.random.default_rng(seed)
    phase_x, phase_y = rng.uniform(0.0, 2.0 * np.pi, size=2)
    x = 2.0 * np.pi * np.arange(size) / size + phase_x
    y = 2.0 * np.pi * np.arange(size) / size + phase_y
    mode = np.cos(x[None, :] + y[:, None])
    phase = np.arange(history_steps + 1, dtype=float) / history_steps
    envelope = np.sin(np.pi * phase)
    excursion = (
        excursion_amplitude * envelope[:, None, None] * mode[None, :, :]
    )
    histories[EXTRA_TEST_FAMILY] = {
        "plus": present[None, :, :] + excursion,
        "minus": present[None, :, :] - excursion,
    }
    return present, histories


def _maxwell_memory_from_history(
    history: np.ndarray,
    p: Parameters,
    *,
    relaxation_rate: float,
    equilibrium_gain: float,
) -> np.ndarray:
    """Integrate a vector Maxwell state relaxing toward grad(abs(F))."""
    memory = np.zeros((2, *history.shape[1:]), dtype=float)
    cfl = p.dt * (
        sum(abs(value) for value in p.velocity) / p.dx
        + 4.0 * p.D_M / p.dx**2
        + relaxation_rate
    )
    if cfl > 1.0:
        raise ValueError("Maxwell memory CFL guard exceeded")
    for field in history[1:]:
        target = equilibrium_gain * _gradient_abs(field, p.dx)
        memory = memory + p.dt * (
            -_advection(memory, p.velocity, p.dx)
            + p.D_M * _laplacian(memory, p.dx)
            + relaxation_rate * (target - memory)
        )
        if not np.isfinite(memory).all() or np.max(np.abs(memory)) > p.max_abs:
            raise FloatingPointError(
                "Maxwell memory became nonfinite or unbounded"
            )
    return memory


def _gradient_abs(field: np.ndarray, dx: float) -> np.ndarray:
    return np.stack([
        (np.roll(np.abs(field), -1, axis) - np.roll(np.abs(field), 1, axis))
        / (2.0 * dx)
        for axis in (-1, -2)
    ])


def _laplacian(array: np.ndarray, dx: float) -> np.ndarray:
    return sum(
        (np.roll(array, -1, axis) - 2.0 * array + np.roll(array, 1, axis))
        / dx**2
        for axis in (-1, -2)
    )


def _advection(array: np.ndarray, velocity, dx: float) -> np.ndarray:
    return sum(
        (
            np.maximum(component, 0.0) * (array - np.roll(array, 1, axis))
            + np.minimum(component, 0.0)
            * (np.roll(array, -1, axis) - array)
        ) / dx
        for component, axis in zip(velocity, (-1, -2))
    )


def _maxwell_step(
    field: np.ndarray,
    memory: np.ndarray,
    p: Parameters,
    *,
    relaxation_rate: float,
    equilibrium_gain: float,
) -> tuple[np.ndarray, np.ndarray]:
    velocity = (
        p.velocity[0] + p.kappa * memory[0],
        p.velocity[1] + p.kappa * memory[1],
    )
    field_cfl = p.dt * (
        float(np.max(np.abs(velocity[0]) + np.abs(velocity[1]))) / p.dx
        + 4.0 * p.D_F / p.dx**2 + p.gamma_F
    )
    if field_cfl > 1.0:
        raise ValueError("Maxwell field CFL guard exceeded")
    next_field = field + p.dt * (
        -_advection(field, velocity, p.dx)
        + p.D_F * _laplacian(field, p.dx)
        - p.gamma_F * field
    )
    next_memory = memory + p.dt * (
        -_advection(memory, p.velocity, p.dx)
        + p.D_M * _laplacian(memory, p.dx)
        + relaxation_rate * (
            equilibrium_gain * _gradient_abs(next_field, p.dx) - memory
        )
    )
    if (
        not np.isfinite(next_field).all()
        or not np.isfinite(next_memory).all()
        or max(
            np.max(np.abs(next_field)), np.max(np.abs(next_memory))
        ) > p.max_abs
    ):
        raise FloatingPointError(
            "Maxwell trajectory became nonfinite or unbounded"
        )
    return next_field, next_memory


def _predict_maxwell(
    present: np.ndarray,
    memory: np.ndarray,
    p: Parameters,
    *,
    steps: int,
    relaxation_rate: float,
    equilibrium_gain: float,
) -> np.ndarray:
    frames = [present.copy()]
    field, state = present.copy(), memory.copy()
    for _ in range(steps):
        field, state = _maxwell_step(
            field, state, p,
            relaxation_rate=relaxation_rate,
            equilibrium_gain=equilibrium_gain,
        )
        frames.append(field.copy())
    return np.stack(frames)


def _kernel_trajectory(
    present: np.ndarray, memory: np.ndarray, p: Parameters, steps: int,
) -> np.ndarray:
    from .local_dynamical_memory import step

    frames = [present.copy()]
    field, state = present.copy(), memory.copy()
    for _ in range(steps):
        field, state = step(field, state, p)
        frames.append(field.copy())
    return np.stack(frames)


def _cluster_mean(
    rows: list[dict[str, object]], value: str,
) -> dict[int, float]:
    grouped: dict[int, list[float]] = {}
    for row in rows:
        grouped.setdefault(int(row["seed"]), []).append(float(row[value]))
    return {seed: float(np.mean(values)) for seed, values in grouped.items()}


def _source_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_revision(root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root, check=True,
            capture_output=True, text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip()


def run_comparison(
    *,
    train_seed_start: int = DEFAULT_TRAIN_SEED_START,
    train_seeds: int = DEFAULT_SEED_COUNT,
    test_seed_start: int = DEFAULT_TEST_SEED_START,
    test_seeds: int = DEFAULT_SEED_COUNT,
    size: int = 32,
    history_steps: int = 100,
    future_steps: int = 100,
    bootstraps: int = 10000,
    bootstrap_seed: int = 20260924,
    excursion_amplitude: float = 0.03,
    relaxation_rates: tuple[float, ...] = RELAXATION_RATES,
    equilibrium_gains: tuple[float, ...] = EQUILIBRIUM_GAINS,
    output: str | Path | None = None,
    revision: str | None = None,
) -> dict[str, object]:
    """Select a Maxwell comparator on training data; score held-out seeds."""
    for name, value in (
        ("train_seed_start", train_seed_start), ("train_seeds", train_seeds),
        ("test_seed_start", test_seed_start), ("test_seeds", test_seeds),
        ("size", size), ("history_steps", history_steps),
        ("future_steps", future_steps), ("bootstraps", bootstraps),
        ("bootstrap_seed", bootstrap_seed),
    ):
        minimum = (
            0 if name.endswith("start") or name == "bootstrap_seed"
            else 1 if name == "future_steps"
            else 2
        )
        _validate_integer(name, value, minimum)
    if size < 4 or history_steps < 2 or future_steps < 1 or bootstraps < 100:
        raise ValueError(
            "size >= 4, history_steps >= 2, future_steps >= 1, "
            "bootstraps >= 100 required"
        )
    if train_seed_start + train_seeds > test_seed_start:
        raise ValueError("training and test seed ranges must not overlap")
    if (
        not np.isfinite(excursion_amplitude)
        or not 0.0 < excursion_amplitude < 0.1
    ):
        raise ValueError("excursion_amplitude must be finite and in (0, 0.1)")
    if (
        not relaxation_rates or not equilibrium_gains
        or any(not np.isfinite(x) or x <= 0 for x in relaxation_rates)
        or any(not np.isfinite(x) or x < 0 for x in equilibrium_gains)
        or 0.0 not in equilibrium_gains
    ):
        raise ValueError(
            "rates must be positive; gains must be nonnegative "
            "and include zero"
        )

    p = Parameters()
    candidates = list(itertools.product(relaxation_rates, equilibrium_gains))
    train_rows: list[dict[str, object]] = []
    train_seeds_list = list(
        range(train_seed_start, train_seed_start + train_seeds)
    )
    for seed in train_seeds_list:
        present, histories = _all_histories(
            seed=seed, size=size, history_steps=history_steps,
            excursion_amplitude=excursion_amplitude,
        )
        for family in TRAIN_FAMILIES:
            for direction, history in histories[family].items():
                kernel_memory = _kernel_memory(history, p)
                target = _kernel_trajectory(
                    present, kernel_memory, p, future_steps
                )
                for rate, gain in candidates:
                    memory = _maxwell_memory_from_history(
                        history, p, relaxation_rate=rate,
                        equilibrium_gain=gain,
                    )
                    prediction = _predict_maxwell(
                        present, memory, p, steps=future_steps,
                        relaxation_rate=rate, equilibrium_gain=gain,
                    )
                    error = _trajectory_error(prediction, target, present)
                    train_rows.append({
                        "model": "maxwell",
                        "seed": seed,
                        "family": family,
                        "direction": direction,
                        "relaxation_rate": rate,
                        "equilibrium_gain": gain,
                        "normalized_trajectory_l2_error": error,
                    })
    by_candidate: dict[tuple[float, float], dict[int, list[float]]] = {}
    for row in train_rows:
        pair = (float(row["relaxation_rate"]), float(row["equilibrium_gain"]))
        by_candidate.setdefault(pair, {}).setdefault(
            int(row["seed"]), []
        ).append(float(row["normalized_trajectory_l2_error"]))
    candidate_scores = []
    for rate, gain in candidates:
        per_seed = by_candidate[(rate, gain)]
        seed_scores = [
            float(np.mean(per_seed[seed])) for seed in sorted(per_seed)
        ]
        candidate_scores.append({
            "relaxation_rate": rate,
            "equilibrium_gain": gain,
            "mean_training_error": float(np.mean(seed_scores)),
            "training_seed_count": len(seed_scores),
        })
    selected = min(
        candidate_scores,
        key=lambda row: (
            float(row["mean_training_error"]),
            float(row["relaxation_rate"]),
            float(row["equilibrium_gain"]),
        ),
    )
    selected_rate = float(selected["relaxation_rate"])
    selected_gain = float(selected["equilibrium_gain"])
    zero_rate = float(relaxation_rates[0])

    test_rows: list[dict[str, object]] = []
    test_seed_ids = list(range(test_seed_start, test_seed_start + test_seeds))
    for seed in test_seed_ids:
        present, histories = _all_histories(
            seed=seed, size=size, history_steps=history_steps,
            excursion_amplitude=excursion_amplitude,
        )
        for family in (*TRAIN_FAMILIES, *TEST_FAMILIES, EXTRA_TEST_FAMILY):
            for direction, history in histories[family].items():
                kernel_memory = _kernel_memory(history, p)
                target = _kernel_trajectory(
                    present, kernel_memory, p, future_steps
                )
                f_only = _predict_maxwell(
                    present, np.zeros((2, size, size)), p, steps=future_steps,
                    relaxation_rate=zero_rate, equilibrium_gain=0.0,
                )
                maxwell_memory = _maxwell_memory_from_history(
                    history, p, relaxation_rate=selected_rate,
                    equilibrium_gain=selected_gain,
                )
                maxwell = _predict_maxwell(
                    present, maxwell_memory, p, steps=future_steps,
                    relaxation_rate=selected_rate,
                    equilibrium_gain=selected_gain,
                )
                test_rows.append({
                    "seed": seed,
                    "family": family,
                    "direction": direction,
                    "kernel_error": _trajectory_error(target, target, present),
                    "f_only_error": _trajectory_error(f_only, target, present),
                    "maxwell_error": _trajectory_error(
                        maxwell, target, present
                    ),
                    "present_match_max_abs": float(
                        np.max(np.abs(history[0] - history[-1]))
                    ),
                })
    maxwell_cluster = _cluster_mean(test_rows, "maxwell_error")
    f_only_cluster = _cluster_mean(test_rows, "f_only_error")
    kernel_cluster = _cluster_mean(test_rows, "kernel_error")
    delta_maxwell = np.asarray([
        maxwell_cluster[seed] - kernel_cluster[seed] for seed in test_seed_ids
    ])
    delta_memory_gain = np.asarray([
        f_only_cluster[seed] - maxwell_cluster[seed] for seed in test_seed_ids
    ])
    maxwell_mean, maxwell_low, maxwell_high = _bootstrap_mean_ci(
        delta_maxwell, replicates=bootstraps, seed=bootstrap_seed,
    )
    gain_mean, gain_low, gain_high = _bootstrap_mean_ci(
        delta_memory_gain, replicates=bootstraps, seed=bootstrap_seed + 1,
    )
    if maxwell_low > MATERIAL_ERROR:
        kernel_decision = "KERNEL_MATERIAL_ADVANTAGE"
    elif maxwell_high < -MATERIAL_ERROR:
        kernel_decision = "MAXWELL_MATERIAL_ADVANTAGE"
    elif maxwell_low >= -MATERIAL_ERROR and maxwell_high <= MATERIAL_ERROR:
        kernel_decision = "PRACTICAL_EQUIVALENCE"
    else:
        kernel_decision = "INCONCLUSIVE"
    if gain_low > MATERIAL_ERROR:
        memory_decision = "MAXWELL_MATERIAL_GAIN_OVER_F_ONLY"
    elif gain_high <= MATERIAL_ERROR:
        memory_decision = "NO_MATERIAL_MAXWELL_GAIN_DEMONSTRATED"
    else:
        memory_decision = "INCONCLUSIVE"

    source_dir = Path(__file__).resolve().parent
    root = source_dir.parent.parent
    summary: dict[str, object] = {
        "assay": "held-out conventional Maxwell internal-variable comparison",
        "status": kernel_decision,
        "interpretation": (
            "The standard Maxwell state is driven by the present amplitude "
            "gradient and relaxes toward it. Targets use the Echofoam "
            "gradient-change write law. "
            "This is a synthetic model-class comparison only."
        ),
        "limitations": [
            (
                "All targets are generated by the Echofoam toy kernel; its "
                "reference error is zero by construction."
            ),
            (
                "The prescribed field histories are controlled inputs, not "
                "autonomous solutions or physical data."
            ),
            (
                "Only one conventional Maxwell state with the declared "
                "shared transport and feedback was tested."
            ),
            (
                "Bootstrap intervals describe the declared synthetic seed "
                "ensemble, not physical uncertainty."
            ),
            "A result cannot establish or refute physical uniqueness.",
        ],
        "configuration": {
            "train_seed_ids": train_seeds_list,
            "test_seed_ids": test_seed_ids,
            "train_families": list(TRAIN_FAMILIES),
            "test_families": [
                *TRAIN_FAMILIES, *TEST_FAMILIES, EXTRA_TEST_FAMILY
            ],
            "histories_per_training_seed": 4,
            "histories_per_test_seed": 10,
            "size": size,
            "history_steps": history_steps,
            "future_steps": future_steps,
            "bootstraps": bootstraps,
            "bootstrap_seed": bootstrap_seed,
            "excursion_amplitude": excursion_amplitude,
            "shared_field_and_transport_parameters": asdict(p),
            "candidate_relaxation_rates": list(relaxation_rates),
            "candidate_equilibrium_gains": list(equilibrium_gains),
            "selected_maxwell": {
                "relaxation_rate": selected_rate,
                "equilibrium_gain": selected_gain,
            },
            "maxwell_equation": (
                "M_t + V.grad(M) = D_M lap(M) + lambda * "
                "(c * grad(abs(F)) - M)"
            ),
            "comparison_rule": (
                "Select lambda and c by mean seed-averaged training "
                "forecast error; held-out data do not enter selection."
            ),
        },
        "decision_rule": {
            "primary_metric": (
                "Mean future-frame L2 trajectory error normalized by "
                "||F*||2, then averaged within seed"
            ),
            "kernel_material_advantage_threshold": MATERIAL_ERROR,
            "maxwell_advantage_interval": [maxwell_low, maxwell_high],
            "maxwell_advantage_mean": maxwell_mean,
            "kernel_vs_maxwell_decision": kernel_decision,
            "maxwell_gain_over_f_only_interval": [gain_low, gain_high],
            "maxwell_gain_over_f_only_mean": gain_mean,
            "maxwell_gain_decision": memory_decision,
            "practical_equivalence_rule": (
                "95% interval wholly within [-0.001, +0.001]"
            ),
        },
        "candidate_training_scores": candidate_scores,
        "provenance": {
            "source_revision": revision or _git_revision(root),
            "protocol_sha256": _source_hash(
                root / "docs" / "STANDARD_MEMORY_COMPARISON_PROTOCOL.md"
            ),
            "standard_memory_comparison_sha256": _source_hash(Path(__file__)),
            "local_dynamical_memory_sha256": _source_hash(
                source_dir / "local_dynamical_memory.py"
            ),
            "f_only_adr_comparison_sha256": _source_hash(
                source_dir / "f_only_adr_comparison.py"
            ),
            "compatible_history_replay_sha256": _source_hash(
                source_dir / "compatible_history_replay.py"
            ),
        },
        "runs": test_rows,
    }
    if output is not None:
        out = Path(output)
        out.mkdir(parents=True, exist_ok=True)
        (out / "summary.json").write_text(
            json.dumps(summary, indent=2, allow_nan=False) + "\n",
            encoding="utf-8",
        )
        with (out / "runs.csv").open(
            "w", newline="", encoding="utf-8"
        ) as handle:
            writer = csv.DictWriter(handle, fieldnames=list(test_rows[0]))
            writer.writeheader()
            writer.writerows(test_rows)
        with (out / "training_candidate_scores.csv").open(
            "w", newline="", encoding="utf-8",
        ) as handle:
            writer = csv.DictWriter(handle, fieldnames=list(train_rows[0]))
            writer.writeheader()
            writer.writerows(train_rows)
        with (out / "candidate_summary.csv").open(
            "w", newline="", encoding="utf-8"
        ) as handle:
            writer = csv.DictWriter(
                handle, fieldnames=list(candidate_scores[0])
            )
            writer.writeheader()
            writer.writerows(candidate_scores)
    return summary


def _kernel_memory(history: np.ndarray, p: Parameters) -> np.ndarray:
    from .compatible_history_replay import memory_from_history

    return memory_from_history(history, p)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--train-seed-start", type=int, default=DEFAULT_TRAIN_SEED_START
    )
    parser.add_argument("--train-seeds", type=int, default=DEFAULT_SEED_COUNT)
    parser.add_argument(
        "--test-seed-start", type=int, default=DEFAULT_TEST_SEED_START
    )
    parser.add_argument("--test-seeds", type=int, default=DEFAULT_SEED_COUNT)
    parser.add_argument("--size", type=int, default=32)
    parser.add_argument("--history-steps", type=int, default=100)
    parser.add_argument("--future-steps", type=int, default=100)
    parser.add_argument("--bootstraps", type=int, default=10000)
    parser.add_argument("--bootstrap-seed", type=int, default=20260924)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--revision", type=str, default=None)
    args = parser.parse_args()
    summary = run_comparison(
        train_seed_start=args.train_seed_start,
        train_seeds=args.train_seeds,
        test_seed_start=args.test_seed_start,
        test_seeds=args.test_seeds,
        size=args.size,
        history_steps=args.history_steps,
        future_steps=args.future_steps,
        bootstraps=args.bootstraps,
        bootstrap_seed=args.bootstrap_seed,
        output=args.output,
        revision=args.revision,
    )
    print(json.dumps({
        "status": summary["status"],
        "selected_maxwell": summary["configuration"]["selected_maxwell"],
        "decision_rule": summary["decision_rule"],
        "output": str(args.output),
    }, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
