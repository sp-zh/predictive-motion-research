#!/usr/bin/env python3
"""Plot retained failed Phase 5 data, never a controller acceptance figure."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("raw", type=Path)
    p.add_argument("output", type=Path)
    args = p.parse_args()
    rows = [r for r in csv.DictReader(args.raw.open())
            if r["phase"] == "path" and r["substep"] == "2"]
    assert len(rows) == 139, "This figure is scoped to retained v19-full only"
    t = [float(r["time_s"]) - 2 for r in rows]
    plt.rcParams.update({"font.size": 11, "font.family": "DejaVu Sans",
                         "axes.spines.top": False, "axes.spines.right": False})
    fig, ax = plt.subplots(3, 1, figsize=(10.5, 8.6), sharex=True,
                           gridspec_kw={"height_ratios": [1, 0.8, 1.4]})
    fig.suptitle("Phase 5 position-servo contract diagnostic", x=0.08, ha="left",
                 fontsize=19, fontweight="bold")
    fig.text(0.08, 0.915, "Retained failed Q=10000 development run · 139 predictive commands · paused simulation",
             color="#555555", fontsize=10)
    blue, orange, gray = "#286094", "#C46A2C", "#545454"
    ax[0].plot(t, [1000 * float(r["euclidean_position_m"]) for r in rows],
               color=blue, linewidth=2)
    ax[0].set_ylabel("Actual TCP error [mm]")
    ax[0].set_ylim(0, 3.5)
    ax[1].plot(t, [float(r["s"]) for r in rows], color=blue, linewidth=2)
    ax[1].set_ylabel("Actual path progress s")
    ax[1].set_ylim(0, 4.1e-8)
    ax[1].ticklabel_format(axis="y", style="sci", scilimits=(-8, -8))
    for prefix, label, color, style in [
            ("applied_model_acc", "Model input a", blue, "-"),
            ("command_acc", "Accepted command acceleration", orange, "--"),
            ("physical_acc", "Physical acceleration", gray, ":")]:
        values = [max(abs(float(r[f"{prefix}_{j}"])) for j in range(7)) for r in rows]
        ax[2].plot(t, values, label=label, color=color, linestyle=style, linewidth=2)
    ax[2].set_ylabel("Max joint magnitude [rad/s²]")
    ax[2].set_ylim(0, 1)
    ax[2].legend(loc="upper right", frameon=False, fontsize=10)
    ax[2].set_xlabel("Elapsed task time [s]")
    for a in ax:
        a.grid(axis="y", color="#DADADA", linewidth=0.6)
        a.set_xlim(t[0], t[-1])
    ax[2].set_xticks([t[0], .1, .2, .3, .4, .5, t[-1]])
    ax[2].set_xticklabels(["0.004", "0.1", "0.2", "0.3", "0.4", "0.5", "0.556"])
    fig.text(0.08, 0.03, "4 ms samples; lower panel shows maximum absolute value over seven joints. Physical acceleration uses\n"
             "the final 2 ms substep of each command. Error decreases during pose preparation; progress remains negligible.\n"
             "Run subsequently failed INACCURATE. Development diagnostic only; no accuracy, liveness or timing acceptance.",
             fontsize=9, color="#555555")
    fig.subplots_adjust(left=.14, right=.97, top=.87, bottom=.15, hspace=.35)
    args.output.mkdir(parents=True, exist_ok=False)
    for ext in ["png", "svg"]:
        fig.savefig(args.output / f"phase5_servo_contract_v19.{ext}", dpi=180,
                    facecolor="white")
    meta = {"scope": __doc__, "source": str(args.raw),
            "raw_sha256": hashlib.sha256(args.raw.read_bytes()).hexdigest(),
            "source_rows": len(rows), "task_time_s": [t[0], t[-1]],
            "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "outputs": {f.name: hashlib.sha256(f.read_bytes()).hexdigest()
                        for f in args.output.iterdir()}}
    (args.output / "phase5_servo_contract_v19.json").write_text(json.dumps(meta, indent=2) + "\n")


if __name__ == "__main__":
    main()
