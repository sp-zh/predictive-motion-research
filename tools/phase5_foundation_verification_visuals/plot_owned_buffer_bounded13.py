"""Render the reviewed owned-buffer test outcome; this does not run project tests."""
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
    if review["decision"] != "PASS_FIXED13_OWNED_BUFFER_RUNTIME_ONLY_NOT_PHASE_ACCEPTANCE":
        raise ValueError("This figure requires independent acceptance of the finite run")
    roster = json.loads(args.roster.read_text())
    ids = [row["id"] for row in roster["groups"]]
    expected = ("".join(f"PASS {case}\n" for case in ids) +
                "COMPLETE 13 owned buffer groups; no phase acceptance\n").encode("ascii")
    if len(ids) != 13 or len(set(ids)) != 13 or args.stdout.read_bytes() != expected:
        raise ValueError("Actual stdout does not match the original ordered roster")
    if digest(args.stdout) != review["actual_stdout_sha256"]:
        raise ValueError("Actual stdout identity differs from independent review")

    results = json.loads(args.results.read_text())["groups"]
    if ([row["case_group_id"] for row in results] != ids or
            any(row["observed_status"] != "PASS" for row in results)):
        raise ValueError("Observed results must match all fixed groups")
    definitions = [
        ("Storage / value checks", ids[:3]),
        ("Move-operation checks", ids[3:10]),
        ("Lifetime / overlap checks", ids[10:12]),
        ("Required constructor refusal", ids[12:]),
    ]
    if any(row["first_refusal_reason"] is not None for row in roster["groups"][:12]):
        raise ValueError("First 12 groups must be positive checks")
    if roster["groups"][12]["first_refusal_reason"] != "moved-from case budget":
        raise ValueError("Final group must check the exact moved-case refusal")
    rows = [{"area": label, "case_group_ids": group_ids,
             "passed_groups": len(group_ids), "planned_groups": len(group_ids)}
            for label, group_ids in definitions]
    if [row["passed_groups"] for row in rows] != [3, 7, 2, 1]:
        raise ValueError("Frozen outcomes must partition all 13 groups")

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 14,
                         "svg.fonttype": "none", "axes.unicode_minus": False,
                         "svg.hashsalt": "phase5-owned-buffer-bounded13-v1"})
    fig, ax = plt.subplots(figsize=(13, 7), dpi=180, facecolor="white")
    fig.subplots_adjust(left=.38, right=.945, top=.70, bottom=.31)
    color = "#2864B0"
    values = [row["passed_groups"] for row in rows]
    ax.barh(range(4), values, height=.54, color=color, zorder=3)
    ax.set_yticks(range(4), [row["area"] for row in rows])
    ax.invert_yaxis()
    ax.set_xlim(0, 9)
    ax.set_xticks(range(0, 10, 1))
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

    fig.text(.06, .905, "Owned numeric buffer verification", fontsize=27,
             fontweight="bold", color="#172B46")
    fig.text(.06, .855, "13 fixed groups · 12 positive checks + 1 required refusal · one invocation", fontsize=16,
             color="#4E5661")
    fig.text(.06, .795, "Every group matched its frozen checks; exact ordered stdout matched, stderr empty.",
             fontsize=13, color="#4E5661")
    fig.text(.06, .14, "Development verification only · Phase 5 NOT_ACCEPTED",
             fontsize=14, fontweight="bold", color="#172B46")
    fig.text(.06, .095, "Values / moves / public ledgers only. Private allocator order, OOM and host-size failures remain deferred.",
             fontsize=12, color="#4E5661")
    fig.text(.06, .05,
             f'Binary SHA-256: {review["binary_sha256"][:16]}…   '
             f'Stdout SHA-256: {digest(args.stdout)[:16]}…',
             fontsize=10, color="#68717E")

    args.output_dir.mkdir(parents=True, exist_ok=False)
    names = ["owned_buffer_bounded13_outcomes.png", "owned_buffer_bounded13_outcomes.svg"]
    for name in names:
        metadata = {"Date": None} if name.endswith(".svg") else None
        fig.savefig(args.output_dir/name, dpi=180, facecolor="white", metadata=metadata)
    plt.close(fig)
    provenance = {
        "scope": "Finite Owned numeric buffer verification; no phase acceptance",
        "grain": "One fixed test group; nested refusal assertions are not separate observations",
        "selection": "All 13 frozen groups, original source order; no curated subset",
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
