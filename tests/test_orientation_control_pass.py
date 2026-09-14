from dataclasses import replace

import numpy as np
import pytest

from echofoam_falsifiability.aligned_rotated_assay import Params, lap
from echofoam_falsifiability.orientation_control_pass import (
    CONDITIONS,
    angle_grid,
    auc,
    initial_fields,
    linear_curves,
    nonlinear_curves,
    sample_steps,
    simulate_seed,
    summarize,
    validate,
)


SMALL = replace(Params(), N=24, steps=23, sample_every=10)
ANGLES = np.array([0.0, 13.7, 45.0, 90.0])


def test_real_angle_grid_includes_both_endpoints_without_overshoot():
    np.testing.assert_allclose(angle_grid(22.5), [0, 22.5, 45, 67.5, 90])
    np.testing.assert_allclose(angle_grid(37.1), [0, 37.1, 74.2, 90])
    assert len(angle_grid(5)) == 19


@pytest.mark.parametrize("step", [0, -1, 91, float("nan"), float("inf")])
def test_invalid_angle_steps_rejected(step):
    with pytest.raises(ValueError):
        angle_grid(step)


def test_batched_stencil_conserves_spatial_sum_and_matches_original_2d_stencil():
    a = np.random.default_rng(2).normal(size=(3, 12, 12))
    np.testing.assert_allclose(lap(a, 0.5).sum(axis=(-2, -1)), 0, atol=1e-12)
    for i in range(len(a)):
        expected = (np.roll(a[i], 1, 0) + np.roll(a[i], -1, 0)
                    + np.roll(a[i], 1, 1) + np.roll(a[i], -1, 1) - 4*a[i]) / 0.5**2
        np.testing.assert_array_equal(lap(a, 0.5)[i], expected)


@pytest.mark.parametrize("condition", CONDITIONS)
def test_pointwise_global_and_local_energy_match_and_parts_reconstruct(condition):
    u, v, parts, mask, density = initial_fields(ANGLES, 7, condition, SMALL)
    np.testing.assert_allclose(u*u + v*v, np.broadcast_to(density, u.shape), rtol=2e-14)
    np.testing.assert_allclose(np.sum(u*u + v*v, axis=(-2, -1)) * (SMALL.L / SMALL.N)**2, 1)
    local = np.sum((u*u + v*v)[:, mask], axis=-1)
    np.testing.assert_allclose(local, local[0], rtol=2e-14)
    np.testing.assert_allclose(parts[0] + parts[2], u, rtol=1e-13, atol=1e-15)
    np.testing.assert_allclose(parts[1] + parts[3], v, rtol=1e-13, atol=1e-15)


def test_seed_pairing_and_angle_grid_do_not_change_realizations():
    for condition in CONDITIONS:
        u, v, _, _, density = initial_fields(ANGLES, 11, condition, SMALL)
        other_u, other_v, _, _, other_density = initial_fields(ANGLES[[2]], 11, condition, SMALL)
        np.testing.assert_array_equal(u[[2]], other_u)
        np.testing.assert_array_equal(v[[2]], other_v)
        np.testing.assert_array_equal(density, other_density)
    _, _, _, _, coherent = initial_fields(ANGLES, 11, "coherent", SMALL)
    _, _, _, _, shuffled = initial_fields(ANGLES, 11, "shuffled", SMALL)
    np.testing.assert_array_equal(coherent, shuffled)
    new_u = initial_fields(ANGLES, 12, "shuffled", SMALL)[0]
    assert not np.array_equal(new_u, u)


@pytest.mark.parametrize("condition", CONDITIONS)
def test_analytic_linear_recurrence_matches_direct_euler(condition):
    p = replace(SMALL, beta=0, delta=0)
    u, v, _, mask, _ = initial_fields(ANGLES, 1, condition, p)
    direct = nonlinear_curves(u, v, mask, p)
    analytic = linear_curves(u, v, mask, p)
    np.testing.assert_allclose(analytic, direct, atol=2e-13, rtol=2e-13)


def test_global_internal_rotation_preserves_nonlinear_and_linear_observables():
    u, v, _, mask, _ = initial_fields(ANGLES, 3, "coherent", SMALL)
    c, s = np.cos(0.713), np.sin(0.713)
    ru, rv = c*u - s*v, s*u + c*v
    for simulate in (nonlinear_curves, linear_curves):
        np.testing.assert_allclose(simulate(u, v, mask, SMALL), simulate(ru, rv, mask, SMALL), atol=1e-13)


def test_zero_diffusion_removes_orientation_dependence_with_matched_amplitudes():
    p = replace(SMALL, D=0, steps=100)
    curves = []
    for condition in ("coherent", "shuffled"):
        u, v, _, mask, _ = initial_fields(ANGLES, 4, condition, p)
        curves.append(nonlinear_curves(u, v, mask, p))
    expected = np.broadcast_to(curves[0][0], curves[0].shape)
    np.testing.assert_allclose(curves[0], expected, atol=2e-13)
    np.testing.assert_allclose(curves[1], expected, atol=2e-13)


def test_final_partial_sampling_interval_is_included_in_auc():
    assert sample_steps(SMALL).tolist() == [0, 10, 20, 23]
    assert auc(np.ones((2, 4)), SMALL).tolist() == pytest.approx([23 * SMALL.dt] * 2)


@pytest.mark.parametrize("params", [
    replace(SMALL, dt=10), replace(SMALL, D=-1), replace(SMALL, steps=0),
    replace(SMALL, target_energy=0), replace(SMALL, L=float("nan")),
])
def test_invalid_or_unstable_parameters_rejected(params):
    with pytest.raises(ValueError):
        validate(params)


def synthetic(effect=0.125):
    linear = np.full((12, 3, 3), 4.0)
    nonlinear = linear.copy()
    nonlinear[:, 0, 0] += effect
    nonlinear[:, 0, 1] += effect / 2
    diagnostics = [{"max_pointwise_energy_relative_error": 0.0,
                    "separated_max_normalized_curve_leakage": 0.0} for _ in range(12)]
    return nonlinear, linear, diagnostics


def test_paired_bootstrap_gates_and_degenerate_standardization():
    n, l, d = synthetic()
    summary = summarize(n, l, [0, 45, 90], d, bootstraps=200)
    assert summary == summarize(n, l, [0, 45, 90], d, bootstraps=200)
    assert summary["verdict"] == "PASS_MATERIAL_TOY_ORIENTATION_EFFECT"
    assert summary["primary_paired_fraction"]["mean"] == 0.03125
    assert summary["primary_paired_fraction"]["ci95"] == [0.03125, 0.03125]
    assert summary["primary_paired_fraction"]["paired_dz"] is None
    assert all(summary["gates"].values())


def test_below_threshold_is_failure_even_if_positive_and_precise():
    n, l, d = synthetic(effect=0.015625)
    result = summarize(n, l, [0, 45, 90], d, bootstraps=200)
    assert result["verdict"] == "FAIL_PRESPECIFIED_MATERIAL_ADVANTAGE"
    assert result["primary_paired_fraction"]["ci95"][0] > 0


def test_positive_primary_cannot_pass_when_shuffle_or_noninteraction_gates_fail():
    n, l, d = synthetic()
    n[:, 1, 1] += 0.125
    result = summarize(n, l, [0, 45, 90], d, bootstraps=200)
    assert result["verdict"] == "INCONCLUSIVE_OR_CONTROLS_FAIL"
    assert not result["gates"]["shuffled_equivalent_to_zero_across_sweep"]
    d[0]["separated_max_normalized_curve_leakage"] = 0.002
    assert summarize(n, l, [0, 45, 90], d, bootstraps=200)["verdict"] == "INVALID_CONTROL_PASS"


def test_paired_ratio_uses_each_seeds_reference_and_preserves_shared_nuisance():
    n, l, d = synthetic()
    nuisance = np.arange(12, dtype=float)[:, None, None]
    n += nuisance
    l += nuisance
    result = summarize(n, l, [0, 45, 90], d, bootstraps=200)
    expected = 0.125 / (4 + np.arange(12))
    assert result["primary_paired_fraction"]["mean"] == pytest.approx(expected.mean())
    assert result["curves"][0]["paired_auc"]["ci95"] == [0.125, 0.125]


def test_small_end_to_end_pass_has_all_paired_rows_and_valid_separation():
    n, l, rows, d = simulate_seed(2, ANGLES, SMALL, 0.003)
    assert n.shape == l.shape == (3, 4)
    assert len(rows) == 3 * 4
    assert all(row["seed"] == 2 for row in rows)
    assert np.isfinite(n).all() and np.isfinite(l).all()
    assert d["max_pointwise_energy_relative_error"] < 1e-12
    assert d["separated_max_normalized_curve_leakage"] < 0.001
