import numpy as np

from echofoam_falsifiability.local_dynamical_memory import Parameters
from echofoam_falsifiability.standard_memory_comparison import (
    EXTRA_TEST_FAMILY,
    _all_histories,
    _maxwell_memory_from_history,
    _predict_maxwell,
    run_comparison,
)


def test_declared_histories_share_exact_release_and_hold_out_diagonal_family():
    present, histories = _all_histories(
        seed=11, size=8, history_steps=12, excursion_amplitude=0.03,
    )

    assert EXTRA_TEST_FAMILY in histories
    assert len(histories) == 5
    for directions in histories.values():
        for tape in directions.values():
            np.testing.assert_array_equal(tape[0], present)
            np.testing.assert_array_equal(tape[-1], present)


def test_zero_gain_maxwell_is_f_only_and_has_no_history_dependence():
    p = Parameters()
    present, histories = _all_histories(
        seed=12, size=8, history_steps=12, excursion_amplitude=0.03,
    )
    first = histories["calibration_mode_a"]["plus"]
    second = histories["calibration_mode_a"]["minus"]
    memory_first = _maxwell_memory_from_history(
        first, p, relaxation_rate=0.1, equilibrium_gain=0.0,
    )
    memory_second = _maxwell_memory_from_history(
        second, p, relaxation_rate=0.1, equilibrium_gain=0.0,
    )
    assert np.max(np.abs(memory_first)) == 0.0
    assert np.max(np.abs(memory_second)) == 0.0
    pred_first = _predict_maxwell(
        present, memory_first, p, steps=8,
        relaxation_rate=0.1, equilibrium_gain=0.0,
    )
    pred_second = _predict_maxwell(
        present, memory_second, p, steps=8,
        relaxation_rate=0.1, equilibrium_gain=0.0,
    )
    np.testing.assert_array_equal(pred_first, pred_second)


def test_training_selection_and_heldout_outputs_are_seed_clustered(tmp_path):
    result = run_comparison(
        train_seed_start=900,
        train_seeds=2,
        test_seed_start=902,
        test_seeds=2,
        size=8,
        history_steps=12,
        future_steps=10,
        bootstraps=100,
        relaxation_rates=(0.1, 0.2),
        equilibrium_gains=(0.0, 0.05),
        output=tmp_path,
        revision="frozen-test-revision",
    )

    assert result["configuration"]["train_seed_ids"] == [900, 901]
    assert result["configuration"]["test_seed_ids"] == [902, 903]
    assert len(result["runs"]) == 20
    assert len(result["candidate_training_scores"]) == 4
    assert result["provenance"]["source_revision"] == "frozen-test-revision"
    assert (tmp_path / "summary.json").exists()
    assert (tmp_path / "runs.csv").exists()
    assert (tmp_path / "training_candidate_scores.csv").exists()
    assert (tmp_path / "candidate_summary.csv").exists()
    assert all(row["kernel_error"] == 0.0 for row in result["runs"])
