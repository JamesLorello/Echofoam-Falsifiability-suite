import numpy as np
import pytest

from echofoam_falsifiability.memory_coupling_audit import (
    BRANCHES,
    Parameters,
    div_psi_grad_tau,
    laplacian,
    radial_metrics,
    run_assay,
    simulate,
)


def test_periodic_laplacian_conserves_sum():
    rng = np.random.default_rng(1)
    field = rng.normal(size=(16, 16))
    assert np.sum(laplacian(field, 1.0)) == pytest.approx(0.0, abs=1e-12)


def test_periodic_divergence_conserves_sum():
    rng = np.random.default_rng(2)
    psi = rng.normal(size=(16, 16))
    tau = rng.normal(size=(16, 16))
    assert np.sum(div_psi_grad_tau(psi, tau, 1.0)) == pytest.approx(0.0, abs=1e-12)


def test_radial_metrics_identify_lowest_box_mode():
    n = 32
    x = np.arange(n)
    field = np.sin(2 * np.pi * x / n)[None, :] * np.ones((n, 1))
    metrics = radial_metrics(field, 1.0)
    assert metrics["k_star"] == pytest.approx(1.0 / n)


@pytest.mark.parametrize("branch", BRANCHES)
def test_every_branch_runs_and_reports_finite_metrics(branch):
    rng = np.random.default_rng(4)
    params = Parameters(0.2, 0.1, 0.2, 0.4, 20.0, 0.1, 0.5)
    psi0 = rng.normal(0.0, 0.1, (16, 16))
    tau0 = rng.normal(0.0, 0.1, (16, 16))
    result = simulate(params, branch, psi0, tau0, rng, steps=20, dt=0.01, dx=1.0)
    assert result["bounded"]
    assert np.isfinite(result["variance_ratio"])
    assert np.isfinite(result["prominence"])


def test_assay_is_deterministic_and_paired():
    rows_a, summary_a = run_assay(runs=2, steps=20, size=16, seed=7)
    rows_b, summary_b = run_assay(runs=2, steps=20, size=16, seed=7)
    assert rows_a == rows_b
    assert summary_a == summary_b
    assert len(rows_a) == 2 * len(BRANCHES)
    assert set(summary_a["paired_comparisons"]) == set(BRANCHES[1:])
    assert summary_a["assay_manifest"]["seed"] == 7


def test_zero_memory_coupling_makes_memory_branches_equivalent():
    rng = np.random.default_rng(8)
    params = Parameters(0.2, 0.1, 0.2, 0.0, 20.0, 0.1, 0.5)
    psi0 = rng.normal(0.0, 0.1, (16, 16))
    tau0 = rng.normal(0.0, 0.1, (16, 16))
    results = [
        simulate(
            params, branch, psi0, tau0, np.random.default_rng(9),
            steps=20, dt=0.01, dx=1.0,
        )
        for branch in BRANCHES
    ]
    for result in results[1:]:
        assert result["final_variance"] == pytest.approx(results[0]["final_variance"])
        assert result["psi_tau_corr"] == pytest.approx(results[0]["psi_tau_corr"])


@pytest.mark.parametrize(
    "kwargs",
    [
        {"runs": 0},
        {"steps": 0},
        {"size": 3},
        {"dt": 0.0},
        {"dx": 0.0},
    ],
)
def test_assay_rejects_invalid_domain(kwargs):
    with pytest.raises(ValueError):
        run_assay(**kwargs)


def test_boundedness_guard_detects_unstable_integration():
    params = Parameters(1.0, 1.0, 1.0, 1.0, 10.0, -100.0, 0.1)
    psi0 = np.full((8, 8), 100.0)
    tau0 = np.zeros((8, 8))
    result = simulate(
        params, "full_memory", psi0, tau0, np.random.default_rng(10),
        steps=10, dt=10.0, dx=1.0,
    )
    assert not result["bounded"]


def test_radial_metrics_reject_non_square_fields():
    with pytest.raises(ValueError):
        radial_metrics(np.zeros((8, 4)), 1.0)
