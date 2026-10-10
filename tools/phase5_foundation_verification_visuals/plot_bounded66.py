"""Render the reviewed foundation test outcome; this does not run project tests."""
import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--stdout", type=Path, required=True)
    parser.add_argument("--roster", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    review = json.loads(args.review.read_text())
    if review["decision"] != "PASS_FIXED66_FOUNDATION_RUNTIME_ONLY_NOT_PHASE_ACCEPTANCE":
        raise ValueError("This figure requires independent acceptance of the finite run")
    roster = json.loads(args.roster.read_text())
    ids = [row["id"] for row in roster["cases"]]
    expected = ("".join(f"PASS {case}\n" for case in ids) +
                "COMPLETE 66 foundation seam cases; no phase acceptance\n").encode("ascii")
    if len(ids) != 66 or len(set(ids)) != 66 or args.stdout.read_bytes() != expected:
        raise ValueError("Actual stdout does not match the original ordered roster")
    if digest(args.stdout) != review["actual_stdout_sha256"]:
        raise ValueError("Actual stdout identity differs from independent review")

    definitions = [
        ("Checked integer arithmetic", ("add_", "multiply_")),
        ("Decimal cycle parser", ("decimal_",)),
        ("Ordered cycle meshes", ("mesh_",)),
        ("Budget ownership and shared ledgers", ("ledger_",)),
    ]
    rows = [{"area": label, "passed_groups": sum(case.startswith(prefixes) for case in ids),
             "planned_groups": sum(case.startswith(prefixes) for case in ids)}
            for label, prefixes in definitions]
    if sum(row["passed_groups"] for row in rows) != 66:
        raise ValueError("Category definitions must partition the frozen roster")

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 14,
                         "svg.fonttype": "none", "axes.unicode_minus": False,
                         "svg.hashsalt": "phase5-foundation-bounded66-v1"})
    fig, ax = plt.subplots(figsize=(13, 7), dpi=180, facecolor="white")
    fig.subplots_adjust(left=.325, right=.945, top=.70, bottom=.31)
    color = "#2864B0"
    values = [row["passed_groups"] for row in rows]
    ax.barh(range(4), values, height=.54, color=color, zorder=3)
    ax.set_yticks(range(4), [row["area"] for row in rows])
    ax.invert_yaxis()
    ax.set_xlim(0, 30)
    ax.set_xticks(range(0, 31, 5))
    ax.set_xlabel("Case groups passing frozen checks (count)", labelpad=13)
    ax.grid(axis="x", color="#E3E7EC", linewidth=.8, zorder=0)
    ax.tick_params(axis="y", length=0, pad=12)
    ax.tick_params(axis="x", colors="#4E5661", length=4)
    for name in ["top", "right"]:
        ax.spines[name].set_visible(False)
    for name in ["left", "bottom"]:
        ax.spines[name].set_color("#68717E")
        ax.spines[name].set_linewidth(.8)
    for i, row in enumerate(rows):
        ax.text(row["passed_groups"]+.45, i,
                f'{row["passed_groups"]} / {row["planned_groups"]}',
                va="center", ha="left", fontsize=15, color="#233247", fontweight="bold")

    fig.text(.06, .905, "Foundation verification", fontsize=27,
             fontweight="bold", color="#172B46")
    fig.text(.06, .855, "66 fixed case groups · one bounded invocation", fontsize=16,
             color="#4E5661")
    fig.text(.06, .795, "Exact ordered stdout matched; stderr empty. Required refusals are included.",
             fontsize=13, color="#4E5661")
    fig.text(.06, .14, "Development verification only · Phase 5 NOT_ACCEPTED",
             fontsize=14, fontweight="bold", color="#172B46")
    fig.text(.06, .095, "No Model, controller or plant run. This is not a motion or performance result.",
             fontsize=12, color="#4E5661")
    fig.text(.06, .05,
             f'Binary SHA-256: {review["binary_sha256"][:16]}…   '
             f'Stdout SHA-256: {digest(args.stdout)[:16]}…',
             fontsize=10, color="#68717E")

    args.output_dir.mkdir(parents=True, exist_ok=False)
    names = ["foundation_bounded66_outcomes.png", "foundation_bounded66_outcomes.svg"]
    for name in names:
        metadata = {"Date": None} if name.endswith(".svg") else None
        fig.savefig(args.output_dir/name, dpi=180, facecolor="white", metadata=metadata)
    plt.close(fig)
    provenance = {
        "scope": "Finite foundation development verification; no phase acceptance",
        "grain": "One fixed test group; nested refusal assertions are not separate observations",
        "selection": "All 66 frozen groups, original source order; no curated subset",
        "rows": rows,
        "sources": {"review": {"file": args.review.name, "sha256": digest(args.review)},
                    "actual_stdout": {"file": args.stdout.name, "sha256": digest(args.stdout)},
                    "original_roster": {"file": args.roster.name, "sha256": digest(args.roster)}},
        "renderer": {"script": Path(__file__).name, "sha256": digest(Path(__file__)),
                     "matplotlib": matplotlib.__version__, "dpi": 180,
                     "figure_inches": [13, 7], "font": "DejaVu Sans", "bar_color": color},
        "outputs": [{"file": name, "bytes": (args.output_dir/name).stat().st_size,
                     "sha256": digest(args.output_dir/name)} for name in names],
        "phase5": "NOT_ACCEPTED", "phase6": "NOT_STARTED",
    }
    (args.output_dir/"provenance.json").write_text(json.dumps(provenance, indent=2)+"\n")
    print(json.dumps({"rows": rows, "outputs": provenance["outputs"]}))


if __name__ == "__main__":
    main()
