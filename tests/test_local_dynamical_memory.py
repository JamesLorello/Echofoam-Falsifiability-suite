from dataclasses import replace

import numpy as np
import pytest

from echofoam_falsifiability.local_dynamical_memory import Parameters, simulate, step


QUIET = Parameters(dx=1, dt=0.1, velocity=(0, 0), D_F=0, D_M=0,
                   gamma_F=0, gamma_M=0, alpha=0.5, kappa=0)


def initial_fields(seed=4, shape=(12, 16)):
    rng = np.random.default_rng(seed)
    F = 1 + rng.uniform(-0.2, 0.2, shape)
    M = rng.uniform(-0.1, 0.1, (2, *shape))
    return F, M


def test_uniform_field_is_invariant_and_memory_relaxes_analytically():
    F = np.full((8, 10), 2.0)
    M = np.full((2, 8, 10), 0.3)
    p = replace(Parameters(), gamma_F=0)
    final_F, final_M = simulate(F, M, p, steps=40)
    np.testing.assert_array_equal(final_F, F)
    np.testing.assert_allclose(final_M, M * (1 - p.dt * p.gamma_M)**40, rtol=1e-13)


def test_stationary_nonuniform_gradient_does_not_rewrite_memory():
    F, M = initial_fields()
    M.fill(0)
    final_F, final_M = simulate(F, M, replace(QUIET, kappa=0.5), steps=20)
    np.testing.assert_array_equal(final_F, F)
    np.testing.assert_array_equal(final_M, M)


@pytest.mark.parametrize("velocity,axis,shift", [
    ((1, 0), 1, 1), ((-1, 0), 1, -1), ((0, 1), 0, 1), ((0, -1), 0, -1),
])
def test_rigid_transport_shifts_both_fields_without_writing(velocity, axis, shift):
    F, M = initial_fields()
    p = replace(QUIET, dt=1, velocity=velocity)
    final_F, final_M = step(F, M, p)
    np.testing.assert_allclose(final_F, np.roll(F, shift, axis), atol=1e-15, rtol=0)
    np.testing.assert_allclose(final_M, np.roll(M, shift, axis + 1), atol=1e-15, rtol=0)


def test_signed_material_write_matches_decaying_fourier_mode():
    n, amplitude, decay = 16, 0.2, 0.3
    theta = 2 * np.pi * np.arange(n) / n
    F = np.broadcast_to(1 + amplitude * np.sin(theta), (8, n)).copy()
    M = np.zeros((2, *F.shape))
    p = replace(QUIET, gamma_F=decay)
    final_F, final_M = step(F, M, p)
    # Analytic centered derivative of this sampled sine, then its decay increment.
    expected_x = -p.alpha * p.dt * decay * amplitude * np.sin(2 * np.pi / n) * np.cos(theta)
    np.testing.assert_allclose(final_F, F * (1 - p.dt * decay), atol=1e-15, rtol=0)
    np.testing.assert_allclose(final_M[0], np.broadcast_to(expected_x, F.shape), atol=1e-15, rtol=0)
    np.testing.assert_array_equal(final_M[1], 0)
    assert final_M[0].min() < 0 < final_M[0].max()


def test_transport_and_diffusion_conserve_sums_when_sources_are_disabled():
    F, M = initial_fields()
    p = replace(Parameters(), alpha=0, kappa=0, gamma_F=0, gamma_M=0)
    final_F, final_M = simulate(F, M, p, steps=100)
    assert final_F.sum() == pytest.approx(F.sum(), abs=1e-12, rel=0)
    np.testing.assert_allclose(final_M.sum(axis=(1, 2)), M.sum(axis=(1, 2)), atol=1e-12, rtol=0)


def test_diffusion_damps_scalar_and_vector_fourier_modes():
    ny, nx = 8, 16
    F = np.broadcast_to(np.cos(2 * np.pi * np.arange(nx) / nx), (ny, nx)).copy()
    M = np.stack([F, np.broadcast_to(np.sin(2 * np.pi * np.arange(ny) / ny)[:, None], F.shape)])
    p = replace(QUIET, dx=0.5, D_F=0.2, D_M=0.15, alpha=0)
    final_F, final_M = step(F, M, p)
    eigen_x = -4 * np.sin(np.pi / nx)**2 / p.dx**2
    eigen_y = -4 * np.sin(np.pi / ny)**2 / p.dx**2
    np.testing.assert_allclose(final_F, F * (1 + p.dt * p.D_F * eigen_x), atol=1e-15, rtol=0)
    np.testing.assert_allclose(final_M[0], M[0] * (1 + p.dt * p.D_M * eigen_x), atol=1e-15, rtol=0)
    np.testing.assert_allclose(final_M[1], M[1] * (1 + p.dt * p.D_M * eigen_y), atol=1e-15, rtol=0)


def test_translation_equivariance_and_amplitude_sign_symmetry():
    F, M = initial_fields()
    final_F, final_M = simulate(F, M, steps=20)
    shifted_F, shifted_M = simulate(
        np.roll(F, (2, 3), (0, 1)), np.roll(M, (2, 3), (1, 2)), steps=20,
    )
    np.testing.assert_array_equal(shifted_F, np.roll(final_F, (2, 3), (0, 1)))
    np.testing.assert_array_equal(shifted_M, np.roll(final_M, (2, 3), (1, 2)))
    negative_F, negative_M = simulate(-F, M, steps=20)
    np.testing.assert_array_equal(negative_F, -final_F)
    np.testing.assert_array_equal(negative_M, final_M)


def test_determinism_and_no_input_mutation_or_output_aliasing():
    F, M = initial_fields()
    F_copy, M_copy = F.copy(), M.copy()
    first = simulate(F, M, steps=30)
    second = simulate(*initial_fields(), steps=30)
    for a, b in zip(first, second):
        np.testing.assert_array_equal(a, b)
    np.testing.assert_array_equal(F, F_copy)
    np.testing.assert_array_equal(M, M_copy)
    for output, source in zip(simulate(F, M, steps=0), (F, M)):
        assert not np.shares_memory(output, source)


@pytest.mark.parametrize("seed", [0, 7, 20260914])
def test_coupled_trajectory_is_finite_and_field_obeys_maximum_bound(seed):
    F, M = initial_fields(seed)
    p = Parameters()
    initial_max = np.max(np.abs(F))
    for k in range(500):
        F, M = step(F, M, p)
        assert np.isfinite(F).all() and np.isfinite(M).all()
        assert np.max(np.abs(F)) <= initial_max * (1 - p.dt * p.gamma_F)**(k + 1) + 1e-12
        assert F.min() >= 0
        # A finite-horizon regression bound for these stated initial conditions.
        assert np.max(np.abs(M)) < 0.2


def test_no_feedback_removes_all_memory_dependence_but_keeps_writing():
    F, M = initial_fields()
    p = replace(Parameters(), kappa=0)
    with_memory, _ = simulate(F, M, p, steps=50)
    zero_memory, written = simulate(F, np.zeros_like(M), p, steps=50)
    baseline, unwritten = simulate(F, np.zeros_like(M), replace(p, alpha=0), steps=50)
    np.testing.assert_array_equal(with_memory, zero_memory)
    np.testing.assert_array_equal(zero_memory, baseline)
    np.testing.assert_array_equal(unwritten, 0)
    assert np.linalg.norm(written) > 0


def test_newly_written_memory_first_changes_the_following_field_step():
    F, M = initial_fields()
    M.fill(0)
    p = Parameters()
    F1, M1 = step(F, M, p)
    control_F1, control_M1 = step(F, M, replace(p, kappa=0))
    np.testing.assert_array_equal(F1, control_F1)
    np.testing.assert_array_equal(M1, control_M1)
    assert np.linalg.norm(M1) > 0
    F2, _ = step(F1, M1, p)
    control_F2, _ = step(control_F1, control_M1, replace(p, kappa=0))
    assert np.linalg.norm(F2 - control_F2) > 1e-8


def test_feedback_is_directional_for_identical_present_field():
    n = 16
    F = np.broadcast_to(1 + 0.2 * np.sin(2 * np.pi * np.arange(n) / n), (8, n)).copy()
    M = np.zeros((2, *F.shape))
    M[0] = 0.5
    p = replace(QUIET, alpha=0, kappa=1, dt=1)
    right, _ = step(F, M, p)
    left, _ = step(F, -M, p)
    perpendicular, _ = step(F, M[::-1], p)
    np.testing.assert_allclose(right, 0.5 * (F + np.roll(F, 1, 1)), atol=1e-15, rtol=0)
    np.testing.assert_allclose(left, 0.5 * (F + np.roll(F, -1, 1)), atol=1e-15, rtol=0)
    np.testing.assert_array_equal(perpendicular, F)
    assert np.linalg.norm(right - left) > 0.1


@pytest.mark.parametrize("kwargs", [{"dx": 0}, {"dt": -1}, {"D_F": -1}, {"D_M": -1},
                                    {"gamma_M": -1}, {"alpha": float("nan")},
                                    {"kappa": float("inf")}, {"velocity": (0,)},
                                    {"velocity": (0, float("nan"))}, {"max_abs": 0}])
def test_invalid_parameters_rejected(kwargs):
    with pytest.raises(ValueError):
        Parameters(**kwargs)


@pytest.mark.parametrize("kwargs", [{"dt": 10}, {"D_M": 100}, {"kappa": 1000}])
def test_cfl_guard_includes_memory_transport_and_feedback_velocity(kwargs):
    F, M = initial_fields()
    with pytest.raises(ValueError, match="CFL"):
        step(F, M, replace(Parameters(), **kwargs))


def test_boundedness_guard_rejects_excessive_writing_without_clipping():
    F, M = initial_fields()
    with pytest.raises(FloatingPointError, match="max_abs"):
        step(F, M, replace(Parameters(), alpha=1e6, max_abs=10))


def test_nonfinite_complex_and_mismatched_fields_are_rejected():
    F, M = initial_fields()
    with pytest.raises(ValueError, match="real"):
        step(F.astype(complex), M)
    with pytest.raises(ValueError, match="ny"):
        step(F, M[0])
    F[0, 0] = np.nan
    with pytest.raises(FloatingPointError, match="nonfinite"):
        step(F, M)


@pytest.mark.parametrize("steps", [-1, 0.5, True])
def test_invalid_step_count_rejected(steps):
    with pytest.raises(ValueError, match="steps"):
        simulate(*initial_fields(), steps=steps)
