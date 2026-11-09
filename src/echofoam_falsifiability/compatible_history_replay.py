"""Controlled compatible-history replay for the local memory toy kernel.

Two prescribed field histories begin and end at the same F. The kernel's
memory update law generates M from each history, then both branches continue
from the shared present F with their retained memory. The history tapes are
controlled inputs; they are not autonomous solutions or physical data.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from dataclasses import asdict, replace
from pathlib import Path

import numpy as np

from .local_dynamical_memory import Parameters, advance_memory, simulate


DEFAULT_SEED = 20260924
NUMERICAL_TOLERANCE = 1e-12


def make_compatible_histories(
    *, seed: int, size: int = 32, history_steps: int = 100,
    excursion_amplitude: float = 0.03,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return common present F and two distinct closed field-history tapes.

    Both tapes start and finish at the exact same positive base field. Between
    endpoints they make equal-and-opposite smooth excursions along the same
    spatial mode, so their field amplitudes are paired while their write
    directions differ. The tapes are exogenous controls, not autonomous runs.
    """
    if not isinstance(seed, (int, np.integer)) or isinstance(seed, bool) or seed < 0:
        raise ValueError("seed must be a nonnegative integer")
    if not isinstance(size, (int, np.integer)) or isinstance(size, bool) or size < 4:
        raise ValueError("size must be an integer >= 4")
    if (not isinstance(history_steps, (int, np.integer))
            or isinstance(history_steps, bool) or history_steps < 2):
        raise ValueError("history_steps must be an integer >= 2")
    if not np.isfinite(excursion_amplitude) or excursion_amplitude <= 0:
        raise ValueError("excursion_amplitude must be finite and positive")

    rng = np.random.default_rng(seed)
    phase_x, phase_y = rng.uniform(0.0, 2.0 * np.pi, size=2)
    x = 2.0 * np.pi * np.arange(size) / size + phase_x
    y = 2.0 * np.pi * np.arange(size) / size + phase_y
    base = 1.0 + 0.1 * (np.cos(x)[None, :] + np.cos(y)[:, None])
    mode = np.cos(x)[None, :] - np.cos(y)[:, None]
    envelope = np.sin(np.pi * np.arange(history_steps + 1) / history_steps)
    excursion = excursion_amplitude * envelope[:, None, None] * mode[None, :, :]
    history_a = base[None, :, :] + excursion
    history_b = base[None, :, :] - excursion
    return base, history_a, history_b


def memory_from_history(field_history, p: Parameters = Parameters()) -> np.ndarray:
    """Compute M from a prescribed F tape, starting from zero memory."""
    if np.iscomplexobj(field_history):
        raise ValueError("field history must be real")
    fields = np.asarray(field_history, dtype=float)
    if fields.ndim != 3 or fields.shape[0] < 2:
        raise ValueError("field_history must have shape (time >= 2, ny, nx)")
    if min(fields.shape[1:]) < 3:
        raise ValueError("field grids must have ny/nx >= 3")
    if not np.isfinite(fields).all():
        raise FloatingPointError("field history contains nonfinite values")
    M = np.zeros((2, *fields.shape[1:]), dtype=float)
    for previous, current in zip(fields[:-1], fields[1:]):
        M = advance_memory(previous, current, M, p)
    return M


def rotate_memory(M: np.ndarray) -> np.ndarray:
    """Rotate each 2-vector by 90 degrees while preserving its local norm."""
    if M.ndim != 3 or M.shape[0] != 2:
        raise ValueError("M must have shape (2, ny, nx)")
    return np.stack((-M[1], M[0]))


def shuffle_memory(M: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Shuffle vector pairs across space, preserving the vector distribution."""
    if M.ndim != 3 or M.shape[0] != 2:
        raise ValueError("M must have shape (2, ny, nx)")
    ny, nx = M.shape[1:]
    pairs = np.moveaxis(M, 0, -1).reshape(-1, 2)
    return np.moveaxis(pairs[rng.permutation(pairs.shape[0])].reshape(ny, nx, 2), -1, 0)


def _rms(array: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(array))))


def _relative_separation(F_a: np.ndarray, F_b: np.ndarray, F_present: np.ndarray) -> float:
    scale = _rms(F_present)
    return _rms(F_a - F_b) / scale


def _endpoint(F: np.ndarray, M: np.ndarray, p: Parameters, steps: int) -> np.ndarray:
    return simulate(F, M, p, steps=steps)[0]


def _run_seed(
    seed: int, *, size: int, history_steps: int, future_steps: int,
    excursion_amplitude: float, p: Parameters,
) -> dict[str, float | int]:
    F_present, history_a, history_b = make_compatible_histories(
        seed=seed, size=size, history_steps=history_steps,
        excursion_amplitude=excursion_amplitude,
    )
    M_a = memory_from_history(history_a, p)
    M_b = memory_from_history(history_b, p)
    stationary_history = np.repeat(F_present[None, :, :], history_steps + 1, axis=0)
    M_stationary = memory_from_history(stationary_history, p)
    history_delta_a = M_a - M_stationary
    history_delta_b = M_b - M_stationary

    future_a = _endpoint(F_present, M_a, p, future_steps)
    future_b = _endpoint(F_present, M_b, p, future_steps)
    natural = _relative_separation(future_a, future_b, F_present)

    zero = np.zeros_like(M_a)
    zero_a = _endpoint(F_present, zero, p, future_steps)
    zero_b = _endpoint(F_present, zero, p, future_steps)
    reset_memory = _relative_separation(zero_a, zero_b, F_present)

    p_no_feedback = replace(p, kappa=0.0)
    no_feedback_a = _endpoint(F_present, M_a, p_no_feedback, future_steps)
    no_feedback_b = _endpoint(F_present, M_b, p_no_feedback, future_steps)
    feedback_off = _relative_separation(no_feedback_a, no_feedback_b, F_present)

    rotated_a = _endpoint(F_present, rotate_memory(M_a), p, future_steps)
    rotated_b = _endpoint(F_present, rotate_memory(M_b), p, future_steps)
    rotated = _relative_separation(rotated_a, rotated_b, F_present)

    shuffle_seed = seed + 0x5EED
    shuffled_a = _endpoint(
        F_present, shuffle_memory(M_a, np.random.default_rng(shuffle_seed)), p, future_steps,
    )
    shuffled_b = _endpoint(
        F_present, shuffle_memory(M_b, np.random.default_rng(shuffle_seed)), p, future_steps,
    )
    shuffled = _relative_separation(shuffled_a, shuffled_b, F_present)

    return {
        "seed": int(seed),
        "present_match_max_abs": float(np.max(np.abs(history_a[-1] - history_b[-1]))),
        "memory_a_rms": _rms(M_a),
        "memory_b_rms": _rms(M_b),
        "memory_difference_rms": _rms(M_a - M_b),
        "stationary_baseline_memory_rms": _rms(M_stationary),
        "history_delta_a_rms": _rms(history_delta_a),
        "history_delta_b_rms": _rms(history_delta_b),
        "history_delta_pair_mismatch_rms": _rms(history_delta_a + history_delta_b),
        "future_separation_relative": natural,
        "reset_memory_separation_relative": reset_memory,
        "feedback_off_separation_relative": feedback_off,
        "rotated_memory_separation_relative": rotated,
        "shuffled_memory_separation_relative": shuffled,
    }


def _bootstrap_mean_ci(
    values: np.ndarray, *, replicates: int, seed: int,
) -> tuple[float, float, float]:
    if values.ndim != 1 or values.size == 0:
        raise ValueError("bootstrap values must be a nonempty one-dimensional array")
    rng = np.random.default_rng(seed)
    draws = rng.integers(0, values.size, size=(replicates, values.size))
    means = values[draws].mean(axis=1)
    low, high = np.percentile(means, (2.5, 97.5))
    return float(values.mean()), float(low), float(high)


def _git_revision(repo_root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=repo_root, check=True,
            capture_output=True, text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_benchmark(
    *, pairs: int = 24, size: int = 32, history_steps: int = 100,
    future_steps: int = 100, seed: int = DEFAULT_SEED,
    bootstraps: int = 10000, excursion_amplitude: float = 0.03,
    output: str | Path | None = None, revision: str | None = None,
) -> dict[str, object]:
    """Run paired deterministic histories and a seed bootstrap summary."""
    integer_options = {
        "pairs": pairs, "size": size, "history_steps": history_steps,
        "future_steps": future_steps, "seed": seed, "bootstraps": bootstraps,
    }
    for name, value in integer_options.items():
        if not isinstance(value, (int, np.integer)) or isinstance(value, bool):
            raise ValueError(f"{name} must be an integer")
    if pairs < 2 or size < 4 or history_steps < 2 or future_steps < 1 or seed < 0:
        raise ValueError("pairs >= 2, size >= 4, history_steps >= 2, future_steps >= 1, seed >= 0 required")
    if bootstraps < 100:
        raise ValueError("bootstraps must be >= 100")
    if not np.isfinite(excursion_amplitude) or not 0 < excursion_amplitude < 0.1:
        raise ValueError("excursion_amplitude must be finite and in (0, 0.1)")

    p = Parameters()
    rows = [
        _run_seed(
            seed + index, size=size, history_steps=history_steps,
            future_steps=future_steps, excursion_amplitude=excursion_amplitude,
            p=p,
        )
        for index in range(pairs)
    ]
    metric_names = (
        "memory_difference_rms", "future_separation_relative",
        "rotated_memory_separation_relative", "shuffled_memory_separation_relative",
        "reset_memory_separation_relative", "feedback_off_separation_relative",
        "history_delta_a_rms", "history_delta_b_rms",
        "history_delta_pair_mismatch_rms",
    )
    values = {
        name: np.asarray([float(row[name]) for row in rows])
        for name in metric_names
    }
    intervals = {
        name: {
            "mean": mean, "bootstrap_95_percentile_ci": [low, high],
        }
        for offset, (name, sample) in enumerate(values.items())
        for mean, low, high in [_bootstrap_mean_ci(
            sample, replicates=bootstraps, seed=seed + 1000 + offset,
        )]
    }
    paired_deltas = {}
    for name in ("rotated_memory_separation_relative", "shuffled_memory_separation_relative"):
        delta = values["future_separation_relative"] - values[name]
        mean, low, high = _bootstrap_mean_ci(
            delta, replicates=bootstraps, seed=seed + 2000 + len(paired_deltas),
        )
        paired_deltas[f"natural_minus_{name}"] = {
            "mean": mean, "bootstrap_95_percentile_ci": [low, high],
        }

    max_present_mismatch = max(float(row["present_match_max_abs"]) for row in rows)
    max_history_delta_mismatch = max(
        float(row["history_delta_pair_mismatch_rms"]) for row in rows
    )
    max_reset_separation = max(float(row["reset_memory_separation_relative"]) for row in rows)
    max_feedback_off_separation = max(float(row["feedback_off_separation_relative"]) for row in rows)
    primary_ci_low = intervals["future_separation_relative"]["bootstrap_95_percentile_ci"][0]
    checks = {
        "identical_present_field": max_present_mismatch <= NUMERICAL_TOLERANCE,
        "history_wrote_different_memory": float(values["memory_difference_rms"].mean()) > NUMERICAL_TOLERANCE,
        "history_write_amplitudes_matched": max_history_delta_mismatch <= NUMERICAL_TOLERANCE,
        "natural_memory_changes_future": primary_ci_low > NUMERICAL_TOLERANCE,
        "memory_reset_null": max_reset_separation <= NUMERICAL_TOLERANCE,
        "feedback_off_null": max_feedback_off_separation <= NUMERICAL_TOLERANCE,
    }

    source_dir = Path(__file__).resolve().parent
    repo_root = source_dir.parent.parent
    summary: dict[str, object] = {
        "assay": "controlled compatible-history replay",
        "status": "TOY_MECHANISM_CHECK_PASS" if all(checks.values()) else "TOY_MECHANISM_CHECK_FAIL",
        "interpretation": (
            "A pass shows that the implemented write and feedback laws transmit "
            "differences between controlled field histories into later toy-model evolution."
        ),
        "limitations": [
            "History tapes are prescribed controls, not autonomous kernel solutions or physical data.",
            "The benchmark does not distinguish this memory law from standard internal-variable models.",
            "No physical validation is established.",
            "Bootstrap intervals describe variability over the declared synthetic phase seeds.",
        ],
        "configuration": {
            "pairs": pairs, "size": size, "history_steps": history_steps,
            "future_steps": future_steps, "first_seed": seed,
            "last_seed": seed + pairs - 1, "bootstraps": bootstraps,
            "bootstrap_seed": seed, "excursion_amplitude": excursion_amplitude,
            "parameters": asdict(p),
            "memory_initialization": "zero; M is advanced from each field tape by advance_memory",
        },
        "decision_rule": {
            "primary_observable": "mean final RMS(F_A - F_B) / RMS(F_present)",
            "numerical_tolerance": NUMERICAL_TOLERANCE,
            "pass_requires": checks,
            "controls": [
                "zero-memory reset", "kappa=0 feedback-off", "90-degree vector rotation",
                "spatial shuffle of vector pairs",
            ],
        },
        "checks": checks,
        "metrics": intervals,
        "paired_control_differences": paired_deltas,
        "provenance": {
            "git_revision": revision or _git_revision(repo_root),
            "compatible_history_replay_sha256": _sha256(Path(__file__)),
            "local_dynamical_memory_sha256": _sha256(source_dir / "local_dynamical_memory.py"),
        },
        "runs": rows,
    }
    if output is not None:
        output_dir = Path(output)
        output_dir.mkdir(parents=True, exist_ok=True)
        summary["output"] = str(output_dir)
        (output_dir / "summary.json").write_text(
            json.dumps(summary, indent=2, allow_nan=False) + "\n", encoding="utf-8",
        )
        with (output_dir / "runs.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pairs", type=int, default=24)
    parser.add_argument("--size", type=int, default=32)
    parser.add_argument("--history-steps", type=int, default=100)
    parser.add_argument("--future-steps", type=int, default=100)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--bootstraps", type=int, default=10000)
    parser.add_argument("--excursion-amplitude", type=float, default=0.03)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--revision")
    args = parser.parse_args()
    result = run_benchmark(
        pairs=args.pairs, size=args.size, history_steps=args.history_steps,
        future_steps=args.future_steps, seed=args.seed, bootstraps=args.bootstraps,
        excursion_amplitude=args.excursion_amplitude, output=args.output,
        revision=args.revision,
    )
    printable = {key: value for key, value in result.items() if key != "runs"}
    print(json.dumps(printable, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
