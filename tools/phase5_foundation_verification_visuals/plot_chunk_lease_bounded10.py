"""Render the reviewed chunk-lease test outcome; this does not run project tests."""
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
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    review = json.loads(args.review.read_text())
    if review["decision"] != "PASS_FIXED10_CHUNK_IO_LEASE_RUNTIME_ONLY_NOT_PHASE_ACCEPTANCE":
        raise ValueError("This figure requires independent acceptance of the finite run")
    roster = json.loads(args.roster.read_text())
    ids = [row["id"] for row in roster["groups"]]
    expected = ("".join(f"PASS {case}\n" for case in ids) +
                "COMPLETE 10 chunk IO lease groups; no phase acceptance\n").encode("ascii")
    if len(ids) != 10 or len(set(ids)) != 10 or args.stdout.read_bytes() != expected:
        raise ValueError("Actual stdout does not match the original ordered roster")
    if digest(args.stdout) != review["actual_stdout_sha256"]:
        raise ValueError("Actual stdout identity differs from independent review")

    results = json.loads(args.results.read_text())["groups"]
    if ([row["case_group_id"] for row in results] != ids or
            any(row["observed_status"] != "PASS" for row in results)):
        raise ValueError("Observed results must match all fixed groups")
    definitions = [
        ("Healthy open / reopen", ids[:1]),
        ("Reentry / poison / reset", ids[1:4]),
        ("Case / batch isolation", ids[4:6]),
        ("Move / lifetime checks", ids[6:]),
    ]
    rows = [{"area": label, "case_group_ids": group_ids,
             "passed_groups": len(group_ids), "planned_groups": len(group_ids)}
            for label, group_ids in definitions]
    if [row["passed_groups"] for row in rows] != [1, 3, 2, 4]:
        raise ValueError("Frozen outcomes must partition all ten groups")

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 14,
                         "svg.fonttype": "none", "axes.unicode_minus": False,
                         "svg.hashsalt": "phase5-chunk-lease-bounded10-v1"})
    fig, ax = plt.subplots(figsize=(13, 7), dpi=180, facecolor="white")
    fig.subplots_adjust(left=.38, right=.945, top=.70, bottom=.31)
    color = "#2864B0"
    values = [row["passed_groups"] for row in rows]
    ax.barh(range(4), values, height=.54, color=color, zorder=3)
    ax.set_yticks(range(4), [row["area"] for row in rows])
    ax.invert_yaxis()
    ax.set_xlim(0, 5)
    ax.set_xticks(range(0, 6, 1))
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
        ax.text(row["passed_groups"]+.12, i,
                f'{row["passed_groups"]} / {row["planned_groups"]}',
                va="center", ha="left", fontsize=15, color="#233247", fontweight="bold")

    fig.text(.06, .905, "Chunk IO lease verification", fontsize=27,
             fontweight="bold", color="#172B46")
    fig.text(.06, .855, "10 fixed groups · nested refusals checked · one invocation", fontsize=16,
             color="#4E5661")
    fig.text(.06, .795, "Every group matched its frozen checks; exact ordered stdout matched, stderr empty.",
             fontsize=13, color="#4E5661")
    fig.text(.06, .14, "Development verification only · Phase 5 NOT_ACCEPTED",
             fontsize=14, fontweight="bold", color="#172B46")
    fig.text(.06, .095, "Public lease behavior only. Actual IO, thread safety, private state and RSS remain outside scope.",
             fontsize=12, color="#4E5661")
    fig.text(.06, .05,
             f'Binary SHA-256: {review["binary_sha256"][:16]}…   '
             f'Stdout SHA-256: {digest(args.stdout)[:16]}…',
             fontsize=10, color="#68717E")

    args.output_dir.mkdir(parents=True, exist_ok=False)
    names = ["chunk_lease_bounded10_outcomes.png", "chunk_lease_bounded10_outcomes.svg"]
    for name in names:
        metadata = {"Date": None} if name.endswith(".svg") else None
        fig.savefig(args.output_dir/name, dpi=180, facecolor="white", metadata=metadata)
    plt.close(fig)
    provenance = {
        "scope": "Finite Chunk IO lease verification; no phase acceptance",
        "grain": "One fixed test group; nested refusal assertions are not separate observations",
        "selection": "All ten frozen groups, original source order; no curated subset",
        "rows": rows,
        "sources": {"review": {"file": args.review.name, "sha256": digest(args.review)},
                    "actual_stdout": {"file": args.stdout.name, "sha256": digest(args.stdout)},
                    "original_roster": {"file": args.roster.name, "sha256": digest(args.roster)},
                    "group_results": {"file": args.results.name, "sha256": digest(args.results)}},
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
