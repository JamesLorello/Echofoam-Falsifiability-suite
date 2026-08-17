import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from blanket_fragmentation_v0 import _anchored_bounded_update, simulate


def test_anchored_update_has_zero_mean_and_respects_bandwidth():
    rng = np.random.default_rng(12)
    dm = 8.0 * rng.standard_normal((48, 2))
    projected = _anchored_bounded_update(dm, omega_max=3.0)
    assert np.linalg.norm(projected.mean(axis=0)) < 1e-10
    assert np.max(np.linalg.norm(projected, axis=1)) <= 3.0 + 1e-10


def test_anchored_simulation_is_deterministic_and_bounded():
    first = simulate(1.4, 17, anchor_collective=True)
    second = simulate(1.4, 17, anchor_collective=True)
    assert first == second
    assert first["collective_mean_norm"] < 1e-10
    assert first["max_update_speed"] <= 3.0 + 1e-10


def test_matched_control_preserves_break_count():
    stress = simulate(1.4, 3, anchor_collective=True)
    control = simulate(
        1.4,
        3,
        mode="random_matched",
        forced_break_schedule=stress["break_events"],
        anchor_collective=True,
    )
    assert stress["broken"] == control["broken"]
