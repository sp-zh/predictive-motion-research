"""Render actual attempt62 stop observations; no controller or simulator calls."""
import argparse
import csv
import gzip
import hashlib
import io
import json
import math
import os
from pathlib import Path
import struct


def render(source):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    stored = source.read_bytes()
    raw = gzip.decompress(stored) if stored[:2] == b"\x1f\x8b" else stored
    at = 0

    def take(fmt):
        nonlocal at
        value = struct.unpack_from(fmt, raw, at)
        at += struct.calcsize(fmt)
        return value

    def text():
        nonlocal at
        size, = take("<Q")
        result = raw[at:at+size].decode()
        at += size
        return result

    assert text() == "P5_ACTIVE_SESSION_LOSSLESS_V1"
    assert text() == "ACTUAL_PHYSICAL_V_A_ACCEPTED_HISTORY_STOP_DWELL_V2"
    passed, failed, consecutive, required, maximum = take("<5Q")
    limits = take("<8d")
    assert limits == (1e-4, 1e-3, 1e-6, 1e-4, 1e-6, 1e-4, 1e-6, 1e-6)
    count, = take("<Q")
    rows = []
    for index in range(count):
        half, time = take("<Qd")
        vectors = [take("<7d") for _ in range(5)]
        progress, rate, acceleration = take("<3d")
        guards, below, hold, dwell = take("<4Q")
        C_drift, s_drift = take("<2d")
        values = [max(map(abs, vectors[j])) for j in (0, 1, 3, 4)]
        values += [rate, abs(acceleration)]
        assert all(math.isfinite(x) and x >= 0 for x in values)
        assert half == 1065 + index and guards == 1
        assert below == int(all(x <= y for x, y in zip(values, limits[:6])))
        assert not below and not hold and not dwell and C_drift == s_drift == 0
        rows.append([half, time, *values])
    scope = text()
    assert at == len(raw) and count == 42 and not (passed or failed or consecutive)
    assert required == 50 and maximum == 178
    fields = ["global_half", "simulation_time_s", "actual_v_inf_rad_s",
              "actual_a_inf_rad_s2", "accepted_w_inf_rad_s", "accepted_alpha_inf_rad_s2",
              "progress_r_s_inv", "progress_abs_b_s_inv2"]
    csv_buffer = io.StringIO()
    writer = csv.writer(csv_buffer)
    writer.writerow(fields)
    writer.writerows(rows)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "axes.spines.top": False, "axes.spines.right": False})
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.8), sharex=True)
    times = [(r[1] - rows[0][1]) * 1000 for r in rows]
    labels = [("Actual velocity / 1e-4 rad/s", "Actual acceleration / 1e-3 rad/s²"),
              ("Accepted w / 1e-6 rad/s", "Accepted alpha / 1e-4 rad/s²"),
              ("Progress r / (1e-6 s⁻¹)", "Absolute b / (1e-4 s⁻²)")]
    titles = ["Measured physical state", "Accepted command history", "Accepted progress history"]
    for panel, ax in enumerate(axes):
        for j, (color, marker) in enumerate((("#2463A6", "o"), ("#C46B20", "s"))):
            k = 2 * panel + j
            ax.plot(times, [r[k+2] / limits[k] for r in rows], color=color,
                    marker=marker, markersize=3, linewidth=1.6, label=labels[panel][j])
        ax.axhline(1, color="#454545", linestyle="--", linewidth=1)
        ax.set_yscale("symlog", linthresh=1)
        ax.set_ylim(bottom=0)
        ax.set_title(titles[panel], loc="left", fontsize=11, y=1.25)
        ax.set_xlabel("Time after first braking observation (ms)")
        ax.set_xticks([0, 20, 40, 60, 82])
        ax.grid(axis="y", alpha=.2)
        ax.legend(loc="lower left", bbox_to_anchor=(0, 1.01), fontsize=8, frameon=False)
    axes[0].set_ylabel("Magnitude / original stop threshold (linear 0–1; log above 1)")
    fig.suptitle("Attempt 62: actual braking observations", x=.06, ha="left", fontsize=16)
    fig.text(.06, .87, "53 committed commands · 106 task half-steps × 2 ms · 42 braking observations", fontsize=10)
    fig.text(.06, .045, "Dashed line = original stop threshold. Dwell 0/50. Run ended at current53: finite nominal families exhausted before Model.\n"
             "Observed21-command braking prefix; full task incomplete. Hold-anchor drift is unavailable while thresholds fail.", fontsize=9)
    fig.subplots_adjust(left=.07, right=.985, top=.69, bottom=.23, wspace=.32)
    outputs = {"csv": csv_buffer.getvalue().encode()}
    for extension in ("png", "svg"):
        buffer = io.BytesIO()
        fig.savefig(buffer, format=extension, dpi=180, facecolor="white")
        outputs[extension] = buffer.getvalue()
    plt.close(fig)
    provenance = {"schema": "ACTUAL_STOP62_STATIC_FIGURE_V1", "source_stored_sha256": hashlib.sha256(stored).hexdigest(),
                  "source_raw_sha256": hashlib.sha256(raw).hexdigest(), "source_role": "ACTUAL_PHYSICAL_V_A_ACCEPTED_HISTORY_STOP_DWELL_V2",
                  "source_packet": "phase5_controlled_stop_current_braking_nominal_terminal62_v3_20261016",
                  "records": count, "original_thresholds": limits, "stop_dwell": 0, "required_dwell": required,
                  "renderer": {"script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                               "matplotlib": matplotlib.__version__, "font": "DejaVu Sans", "dpi": 180,
                               "figure_inches": [13, 4.8]},
                  "selection": "Every actual braking observation in attempt62, with no omitted failures or extrapolation",
                  "scope": scope, "outputs": {k: {"bytes": len(v), "sha256": hashlib.sha256(v).hexdigest()} for k, v in outputs.items()}}
    outputs["json"] = (json.dumps(provenance, indent=2) + "\n").encode()
    return outputs


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output_prefix", type=Path)
    args = parser.parse_args()
    outputs = render(args.source)
    assert sum(map(len, outputs.values())) <= 2 * 1024 * 1024
    if os.environ.get("P5_DERIVED53_ROOT"):
        import sys
        sys.path.insert(0, "/private/tmp")
        from bounded_derived_bytes53_v1 import bounded_write_bytes
        write = bounded_write_bytes
    else:
        def write(path, payload):
            with open(path, "xb") as target:
                target.write(payload)
    for extension, payload in outputs.items():
        write(Path(str(args.output_prefix) + "." + extension), payload)
