import numpy as np
import pytest

from echofoam_falsifiability.memory_coupling_audit import (
    BRANCHES,
    Parameters,
    laplacian,
    radial_metrics,
    run_assay,
    simulate,
)


def test_periodic_laplacian_conserves_sum():
    rng = np.random.default_rng(1)
    field = rng.normal(size=(16, 16))
    assert np.sum(laplacian(field, 1.0)) == pytest.approx(0.0, abs=1e-12)


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
