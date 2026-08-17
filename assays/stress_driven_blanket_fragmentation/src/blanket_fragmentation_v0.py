
import numpy as np
import pandas as pd


def _anchored_bounded_update(dm, omega_max, max_iter=100, tol=1e-12):
    """Project updates onto zero collective motion and per-node speed bounds."""
    projected = dm.copy()
    for _ in range(max_iter):
        projected -= projected.mean(axis=0, keepdims=True)
        speed = np.linalg.norm(projected, axis=1)
        projected *= np.minimum(1.0, omega_max / (speed + 1e-15))[:, None]
        if np.linalg.norm(projected.mean(axis=0)) <= tol:
            break
    projected -= projected.mean(axis=0, keepdims=True)
    return projected

def simulate(
    drive,
    seed=0,
    N=48,
    K=3.0,
    dt=0.02,
    steps=3000,
    tau_force=0.8,
    omega_max=3.0,
    stress_c=1.1,
    damage_thresh=0.35,
    alpha_state=0.55,
    beta_rate=0.45,
    sample_last=600,
    mode="stress",
    forced_break_schedule=None,
    anchor_collective=False,
):
    """
    Minimal vector-memory blanket fragmentation assay.

    Primitive observer:
      m_i in R^2 = persistent, alterable memory state.

    Local coherent interaction:
      J_ij = K (m_j - m_i) across intact nearest-neighbor links.

    Attempted motion:
      independent OU drive f_i(t), scaled by `drive`.

    Finite update bandwidth:
      |dm_i/dt| <= omega_max.

    Local shear:
      weighted combination of memory mismatch and update-rate mismatch.

    Rupture:
      accumulated overload breaks only the overloaded local link.

    No cluster count, target blanket size, or preferred fragmentation scale
    is specified in the update rule.
    """
    rng_force = np.random.default_rng(seed)
    rng_break = np.random.default_rng(seed + 100000)

    m = 0.05 * rng_force.standard_normal((N, 2))
    if anchor_collective:
        m -= m.mean(axis=0, keepdims=True)
    f = 0.1 * rng_force.standard_normal((N, 2))
    intact = np.ones(N - 1, dtype=bool)
    damage = np.zeros(N - 1)
    break_events = []

    hist = np.empty((sample_last, N))
    dhist = np.empty((sample_last, N))
    h = 0
    max_update_speed = 0.0

    schedule = {}
    if forced_break_schedule:
        for t, count in forced_break_schedule:
            schedule[t] = schedule.get(t, 0) + count

    ou_noise = np.sqrt(2 / tau_force) * np.sqrt(dt)

    for t in range(steps):
        # Local attempted change ("motion demand")
        f += (-f / tau_force) * dt + ou_noise * rng_force.standard_normal((N, 2))

        # Shared flow / corrective current between coherent neighbors
        dm = drive * f.copy()
        diff = m[1:] - m[:-1]
        J = K * diff * intact[:, None]
        dm[:-1] += J
        dm[1:] -= J

        # Finite update bandwidth. The anchored branch removes only the
        # freely diffusing collective (zero-wavenumber) update mode.
        if anchor_collective:
            dm = _anchored_bounded_update(dm, omega_max)
        else:
            speed = np.linalg.norm(dm, axis=1)
            dm *= np.minimum(1.0, omega_max / (speed + 1e-12))[:, None]
        max_update_speed = max(max_update_speed, float(np.max(np.linalg.norm(dm, axis=1))))
        m += dt * dm

        if mode == "stress":
            state_mismatch = np.linalg.norm(m[1:] - m[:-1], axis=1)
            rate_mismatch = np.linalg.norm(dm[1:] - dm[:-1], axis=1)
            shear = alpha_state * state_mismatch + beta_rate * rate_mismatch

            overload = np.maximum(0.0, shear / stress_c - 1.0)
            damage += dt * overload * intact

            # weak recovery while safely below threshold
            damage -= (
                dt * 0.15
                * np.maximum(0.0, 1.0 - shear / stress_c)
                * damage
                * intact
            )
            np.maximum(damage, 0.0, out=damage)

            breaks = (damage > damage_thresh) & intact
            if np.any(breaks):
                n_breaks = int(np.sum(breaks))
                intact[breaks] = False
                break_events.append((t, n_breaks))

        elif mode == "random_matched":
            n_breaks = schedule.get(t, 0)
            if n_breaks:
                candidates = np.flatnonzero(intact)
                n_breaks = min(n_breaks, len(candidates))
                if n_breaks:
                    chosen = rng_break.choice(
                        candidates, size=n_breaks, replace=False
                    )
                    intact[chosen] = False

        if t >= steps - sample_last:
            hist[h] = m[:, 0]
            dhist[h] = dm[:, 0]
            h += 1

    # Connected components become candidate smaller blankets.
    clusters = []
    start = 0
    for edge, alive in enumerate(intact):
        if not alive:
            clusters.append(np.arange(start, edge + 1))
            start = edge + 1
    clusters.append(np.arange(start, N))

    membership = np.empty(N, dtype=int)
    for cidx, cluster in enumerate(clusters):
        membership[cluster] = cidx

    # Simple first-pass statistical proxy:
    # absolute correlation of memory-update rates.
    C = np.corrcoef(dhist.T)
    within, across = [], []

    for i in range(N - 1):
        vals = np.abs(C[i, i + 1:])
        finite = np.isfinite(vals)
        same = membership[i + 1:] == membership[i]
        within.extend(vals[finite & same].tolist())
        across.extend(vals[finite & ~same].tolist())

    sizes = [len(c) for c in clusters]
    wc = float(np.mean(within)) if within else np.nan
    ac = float(np.mean(across)) if across else np.nan

    # A spatial coherence measure independent of correlation.
    spreads = []
    for cluster in clusters:
        if len(cluster) > 1:
            centered = hist[:, cluster] - hist[:, cluster].mean(axis=1, keepdims=True)
            spreads.append(float(np.mean(centered**2)))

    return {
        "drive": drive,
        "seed": seed,
        "nclusters": len(clusters),
        "mean_size": float(np.mean(sizes)),
        "max_size": max(sizes),
        "broken": int(np.sum(~intact)),
        "within_corr": wc,
        "across_corr": ac,
        "separation": wc - ac if np.isfinite(wc) and np.isfinite(ac) else np.nan,
        "internal_spread": float(np.mean(spreads)) if spreads else np.nan,
        "break_events": break_events,
        "collective_mean_norm": float(np.linalg.norm(m.mean(axis=0))),
        "max_update_speed": max_update_speed,
    }


if __name__ == "__main__":
    drives = np.round(np.arange(0.8, 1.51, 0.1), 3)
    rows = []
    details = {}

    for drive in drives:
        for seed in range(8):
            r = simulate(float(drive), seed)
            details[(float(drive), seed)] = r
            rows.append({k: v for k, v in r.items() if k != "break_events"})

    df = pd.DataFrame(rows)
    print(df.groupby("drive").mean(numeric_only=True).round(3))

    # Matched-random fracture control at two transition points.
    controls = []
    for drive in (1.3, 1.4):
        for seed in range(8):
            stress = details[(drive, seed)]
            random_control = simulate(
                drive,
                seed,
                mode="random_matched",
                forced_break_schedule=stress["break_events"],
            )
            for label, result in (
                ("stress", stress),
                ("random_matched", random_control),
            ):
                controls.append({
                    "drive": drive,
                    "seed": seed,
                    "mode": label,
                    "within_corr": result["within_corr"],
                    "across_corr": result["across_corr"],
                    "separation": result["separation"],
                    "internal_spread": result["internal_spread"],
                    "broken": result["broken"],
                })

    controls = pd.DataFrame(controls)
    print("\nMatched-random control:")
    print(
        controls.groupby(["drive", "mode"])
        .mean(numeric_only=True)
        .round(3)
    )
