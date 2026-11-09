import numpy as np
import pytest

from echofoam_falsifiability.compatible_history_replay import (
    make_compatible_histories,
    memory_from_history,
    rotate_memory,
    run_benchmark,
    shuffle_memory,
)
from echofoam_falsifiability.local_dynamical_memory import Parameters, advance_memory, step


def test_memory_replay_uses_the_same_update_as_an_autonomous_kernel_step():
    rng = np.random.default_rng(19)
    F = 1 + rng.uniform(-0.1, 0.1, (12, 14))
    M = np.zeros((2, *F.shape))
    p = Parameters()
    F_next, expected_M = step(F, M, p)

    replayed_M = advance_memory(F, F_next, M, p)

    np.testing.assert_array_equal(replayed_M, expected_M)


def test_controlled_histories_are_distinct_and_have_an_exact_common_endpoint():
    present, history_a, history_b = make_compatible_histories(
        seed=3, size=16, history_steps=20,
    )

    np.testing.assert_array_equal(history_a[0], present)
    np.testing.assert_array_equal(history_b[0], present)
    np.testing.assert_array_equal(history_a[-1], present)
    np.testing.assert_array_equal(history_b[-1], present)
    assert np.max(np.abs(history_a - history_b)) > 0
    assert np.min(history_a) > 0 and np.min(history_b) > 0


def test_compatible_histories_generate_opposite_amplitude_matched_memory():
    _, history_a, history_b = make_compatible_histories(
        seed=11, size=16, history_steps=40,
    )
    p = Parameters()

    memory_a = memory_from_history(history_a, p)
    memory_b = memory_from_history(history_b, p)
    stationary = np.repeat(history_a[:1], len(history_a), axis=0)
    memory_stationary = memory_from_history(stationary, p)
    delta_a = memory_a - memory_stationary
    delta_b = memory_b - memory_stationary

    np.testing.assert_allclose(delta_b, -delta_a, atol=1e-15, rtol=0)
    assert np.linalg.norm(delta_a) > 0
    assert np.linalg.norm(delta_b) == pytest.approx(np.linalg.norm(delta_a), rel=1e-14)


def test_rotated_and_shuffled_controls_preserve_memory_amplitudes():
    rng = np.random.default_rng(6)
    memory = rng.normal(size=(2, 8, 10))
    shuffled = shuffle_memory(memory, np.random.default_rng(37))
    rotated = rotate_memory(memory)

    np.testing.assert_allclose(np.sum(shuffled**2), np.sum(memory**2), atol=1e-14)
    np.testing.assert_allclose(np.sum(rotated**2), np.sum(memory**2), atol=1e-14)
    np.testing.assert_allclose(np.sqrt(np.sum(rotated**2, axis=0)),
                               np.sqrt(np.sum(memory**2, axis=0)), atol=1e-14)


def test_small_benchmark_passes_toy_mechanism_checks_and_is_deterministic():
    kwargs = {
        "pairs": 4, "size": 12, "history_steps": 30,
        "future_steps": 50, "seed": 71, "bootstraps": 500,
    }
    first = run_benchmark(**kwargs)
    second = run_benchmark(**kwargs)

    assert first["status"] == "TOY_MECHANISM_CHECK_PASS"
    assert first["checks"] == second["checks"]
    assert first["runs"] == second["runs"]
    assert first["metrics"] == second["metrics"]
    assert all(row["present_match_max_abs"] == 0 for row in first["runs"])
    assert all(row["reset_memory_separation_relative"] == 0 for row in first["runs"])
    assert all(row["feedback_off_separation_relative"] == 0 for row in first["runs"])


def test_benchmark_writes_reviewable_raw_rows_and_summary(tmp_path):
    result = run_benchmark(
        pairs=3, size=8, history_steps=12, future_steps=10,
        seed=81, bootstraps=100, output=tmp_path,
    )

    summary = (tmp_path / "summary.json").read_text(encoding="utf-8")
    rows = (tmp_path / "runs.csv").read_text(encoding="utf-8")
    assert '"assay": "controlled compatible-history replay"' in summary
    assert "future_separation_relative" in rows
    assert len(result["runs"]) == 3


@pytest.mark.parametrize("kwargs", [
    {"size": 3}, {"history_steps": 1}, {"seed": -1},
])
def test_history_generator_rejects_invalid_shape_parameters(kwargs):
    options = {"seed": 0, "size": 8, "history_steps": 8}
    options.update(kwargs)
    with pytest.raises(ValueError):
        make_compatible_histories(**options)


def test_history_memory_rejects_bad_tape_shape_and_nonfinite_values():
    with pytest.raises(ValueError, match="time"):
        memory_from_history(np.ones((1, 8, 8)))
    bad_history = np.ones((2, 8, 8))
    bad_history[1, 0, 0] = np.nan
    with pytest.raises(FloatingPointError, match="nonfinite"):
        memory_from_history(bad_history)
