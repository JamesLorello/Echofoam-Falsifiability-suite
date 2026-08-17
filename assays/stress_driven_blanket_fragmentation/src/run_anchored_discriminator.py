"""Preregistered zero-mode repair and matched-location rerun."""

from pathlib import Path

import numpy as np
import pandas as pd

from blanket_fragmentation_v0 import simulate


DRIVES = (1.3, 1.4)
SEEDS = tuple(range(64))


def paired_summary(frame):
    rows = []
    for drive, group in frame.groupby("drive"):
        wide = group.pivot(index="seed", columns="mode", values="separation")
        diff = (wide["stress"] - wide["random_matched"]).dropna().to_numpy()
        n = len(diff)
        sd = float(np.std(diff, ddof=1)) if n > 1 else np.nan
        se = sd / np.sqrt(n) if n > 1 else np.nan
        rows.append({
            "drive": drive,
            "finite_pairs": n,
            "mean_paired_difference": float(np.mean(diff)),
            "median_paired_difference": float(np.median(diff)),
            "paired_standardized_effect": float(np.mean(diff) / sd) if sd > 0 else np.nan,
            "fraction_stress_gt_random": float(np.mean(diff > 0)),
            "mean_difference_ci95_low": float(np.mean(diff) - 1.96 * se),
            "mean_difference_ci95_high": float(np.mean(diff) + 1.96 * se),
        })
    return pd.DataFrame(rows)


def run():
    records = []
    for drive in DRIVES:
        for seed in SEEDS:
            stress = simulate(drive, seed, anchor_collective=True)
            random_control = simulate(
                drive,
                seed,
                mode="random_matched",
                forced_break_schedule=stress["break_events"],
                anchor_collective=True,
            )
            assert stress["broken"] == random_control["broken"]
            for label, result in (("stress", stress), ("random_matched", random_control)):
                records.append({
                    "drive": drive,
                    "seed": seed,
                    "mode": label,
                    "separation": result["separation"],
                    "within_corr": result["within_corr"],
                    "across_corr": result["across_corr"],
                    "internal_spread": result["internal_spread"],
                    "broken": result["broken"],
                    "collective_mean_norm": result["collective_mean_norm"],
                    "max_update_speed": result["max_update_speed"],
                })

    frame = pd.DataFrame(records)
    summary = paired_summary(frame)
    output = Path(__file__).resolve().parents[1] / "results"
    output.mkdir(exist_ok=True)
    frame.to_csv(output / "anchored_matched_random_control.csv", index=False)
    summary.to_csv(output / "anchored_discriminator_summary.csv", index=False)
    print(summary.to_string(index=False))
    print("max collective mean norm:", frame["collective_mean_norm"].max())
    print("max update speed:", frame["max_update_speed"].max())


if __name__ == "__main__":
    run()
