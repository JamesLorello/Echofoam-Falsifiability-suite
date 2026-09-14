"""Plot the retained sweep and its simultaneous seed-bootstrap uncertainty."""

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result_dir", type=Path)
    args = parser.parse_args()
    summary = json.loads((args.result_dir / "summary.json").read_text())
    manifest = json.loads((args.result_dir / "manifest.json").read_text())
    palette = {
        "coherent": ("Coherent crossing", "#126d82"),
        "shuffled": ("Shuffled orientations", "#b16924"),
        "separated": ("Separated packets", "#71538d"),
    }
    with plt.rc_context({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False}):
        fig, ax = plt.subplots(figsize=(9, 5.8))
        threshold = 100 * summary["material_fraction"]
        ax.axhspan(-threshold, threshold, color="#e8ecf0", alpha=0.65, zorder=0)
        ax.axhline(threshold, color="#374151", linestyle="--", linewidth=1)
        ax.axhline(-threshold, color="#374151", linestyle="--", linewidth=1)
        ax.axhline(0, color="#b4bcc5", linewidth=0.8)
        for condition, (label, color) in palette.items():
            rows = [r for r in summary["curves"] if r["condition"] == condition]
            angles = np.array([r["angle_deg"] for r in rows])
            means = 100 * np.array([r["paired_fraction"]["mean"] for r in rows])
            bands = 100 * np.array([r["simultaneous_fraction_ci95"] for r in rows])
            ax.fill_between(angles, bands[:, 0], bands[:, 1], color=color, alpha=0.20)
            ax.plot(angles, means, "o-", color=color, markersize=3.3, linewidth=1.8, label=label)
        ax.set(xlim=(0, 90), xticks=np.arange(0, 91, 15),
               xlabel="Relative internal angle (degrees)",
               ylabel="Baseline-adjusted angle contrast (%)")
        ax.set_title("Orientation after pointwise energy matching", loc="left", fontsize=16, pad=17)
        ax.legend(loc="lower left", bbox_to_anchor=(0.008, 0.09), borderaxespad=0, frameon=False)
        ax.text(0.98, threshold, f"  +{threshold:g}% material threshold", ha="right", va="bottom",
                transform=ax.get_yaxis_transform(), fontsize=10, color="#374151")
        ax.grid(axis="y", alpha=0.2)
        count = len(manifest["seeds"])
        fig.text(0.13, 0.055,
                 f"{count} paired seeds; 95% simultaneous bootstrap bands. Every contrast is relative to 90 degrees.\n"
                 "Nonlinear minus analytic-linear AUC, scaled by the coherent orthogonal linear AUC.\n"
                 "Gray shading marks the declared control-equivalence region. Toy model only.",
                 fontsize=9.3, color="#4b5563", linespacing=1.5)
        fig.subplots_adjust(left=0.13, bottom=0.23, top=0.89, right=0.97)
        fig.savefig(args.result_dir / "angle_sweep.png", dpi=180)
        fig.savefig(args.result_dir / "angle_sweep.svg")
        plt.close(fig)


if __name__ == "__main__":
    main()
