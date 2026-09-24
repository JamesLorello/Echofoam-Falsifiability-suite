import numpy as np
import pytest

from echofoam_falsifiability.f_only_adr_comparison import (
    TEST_FAMILIES,
    TRAIN_FAMILIES,
    make_preparation_histories,
    run_comparison,
)


def test_calibration_and_heldout_families_have_four_matched_histories():
    present, families = make_preparation_histories(
        seed=17,
        size=12,
        history_steps=20,
    )

    assert set(families) == set(TRAIN_FAMILIES + TEST_FAMILIES)
    for family in families.values():
        for tape in family.values():
            np.testing.assert_array_equal(tape[0], present)
            np.testing.assert_array_equal(tape[-1], present)
            assert np.min(tape) > 0
    assert not set(TRAIN_FAMILIES) & set(TEST_FAMILIES)


def test_heldout_comparison_uses_disjoint_seeds_and_selects_only_on_training(
    tmp_path,
):
    result = run_comparison(
        train_seed_start=26090400,
        train_seeds=8,
        test_seed_start=26090408,
        test_seeds=4,
        size=8,
        history_steps=12,
        future_steps=10,
        bootstraps=100,
        output=tmp_path,
    )

    assert result["checks"]["training_and_test_seeds_disjoint"]
    assert result["checks"]["preparation_families_held_out"]
    assert result["checks"][
        "four_histories_per_test_seed_share_exact_present"
    ]
    assert result["checks"]["memory_generated_from_each_history"]
    assert result["checks"][
        "heldout_histories_produce_distinct_kernel_futures"
    ]
    assert result["training_selected_model"] == min(
        result["training_validation_mean_error"],
        key=result["training_validation_mean_error"].get,
    )
    assert (
        result["status"]
        == "NO_MATERIAL_F_ONLY_ADR_ADVANTAGE_PRACTICAL_EQUIVALENCE"
    )
    assert set(result["test_metrics_by_model"]) == {
        "adr",
        "advection_diffusion",
        "diffusion_reaction",
        "diffusion_only",
    }
    assert (tmp_path / "summary.json").is_file()
    assert (tmp_path / "runs.csv").is_file()
    assert (tmp_path / "branch_scores.csv").is_file()


def test_comparison_rejects_overlapping_training_and_test_seeds():
    with pytest.raises(ValueError, match="disjoint"):
        run_comparison(
            train_seed_start=20,
            train_seeds=8,
            test_seed_start=27,
            test_seeds=4,
            size=8,
            history_steps=10,
            future_steps=5,
            bootstraps=100,
        )
