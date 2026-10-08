#!/usr/bin/env python3
"""SOURCE ONLY until separately dispatched. Copies saved maps; never calls a model."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

SOURCE_SHA = "ce5731c49d4c4815d2e30d8079054310d1f73816d7906c607a1e76a4cf0c0a0c"
F1_SHA = "f1b7e6c7e4219fec2beb310540c725b448dcf021b3a95ddafc2922e8849bf1d6"
SOURCE_ARCHIVE_SHA = "e42af2a0ca5a85047e371660f9fc565cdc0a28ace450235a1f3d6acb13d9de83"
CERT = "COMMAND_PROGRESS_EXTENSION_JACOBIAN_STRICT_PHYSICAL_V1"
FLAGS = dict.fromkeys(["connecting_segment", "ball", "admissibility", "execution",
                      "safety", "uniform_error_bound", "controller_readiness"], False)
LIMITS = dict(max_cases=32, max_cells=16, max_samples=512, max_nx=64, max_nu=16,
              max_terms=32, max_factor_rows=256, max_matrix_elements=2000000,
              max_document_bytes=67108864, max_problem_numeric_elements=8000000,
              max_cli_numeric_elements=16000000, arithmetic_abs=2e-13, arithmetic_rel=2e-13)


def packed(z):
    return sum((z[k] for k in ("q", "v", "C", "w")), []) + [z["s"], z["r"]]


def terms(nx, nu, cells, samples):
    dy = nx * (cells + 1) + nu * cells
    result = []
    for ordinal, rows in enumerate((11, 7)):
        result.append(dict(
            name=f"declared_algebra_{ordinal}", units="explicit_test_coefficients",
            F=[[(((2*i+7*j+3*i*j+ordinal) % 23)-11)/170.0
                for j in range(dy)] for i in range(rows)],
            f0=[.002 * (-1)**(i+ordinal)*(i+1) for i in range(rows)],
            linear=[.0007 * (-1)**(j+ordinal)/(j+2) for j in range(dy)],
            constant=.13 + .02*ordinal,
            sample_additions=[]))
    if samples:
        for t, index in zip(result, (0, samples-1)):
            rows = len(t["F"])
            t["sample_additions"] = [dict(sample_index=index, coefficient=[
                [(((i+3*j) % 9)-4)/240.0 for j in range(nx)] for i in range(rows)])]
    return result


def controls(nu, cells):
    return [(.0015*(c+1) if j == nu-1 else .0002*(-1)**(c+j)*(j+1)/(c+2))
            for c in range(cells) for j in range(nu)]


def public_case(name, row, shifted=False, roster="complete"):
    x0 = packed(row["original_input"]["state"])
    if shifted:
        # Algebra shifts, never a new physical certificate or model forecast.
        for index, delta in ((2, .00012), (8, -.00003), (19, .00002),
                             (25, .00001), (28, .00006), (29, .00003)):
            x0[index] += delta
    n = len(row["original_input"]["cells"])
    samples = len(row["original_output"]["substep_maps"])
    return dict(name=name, source=dict(kind="public_saved_json", artifact_id="archived_f1_v1",
                roster=roster, row_name=row["name"]), actual_initial=x0,
                terms=terms(30, 8, n, samples), evaluate_controls=controls(8, n), scope=FLAGS.copy())


def generic_case():
    cells = [dict(cycles=1, A=[[1,.03,0,0],[0,.94,.02,0],[.01,0,1.04,.01],[0,.02,0,.91]],
                  B=[[.1,.02,-.01],[.03,-.08,.02],[.04,.01,.06],[-.02,.05,.03]],
                  defect=[.004,-.002,.001,.003]),
             dict(cycles=2, A=[[.93,0,.03,.01],[.02,1,0,0],[0,.03,.89,.02],[.01,0,.02,1.02]],
                  B=[[.07,-.01,.02],[-.02,.11,.01],[.03,.04,-.05],[.02,.01,.08]],
                  defect=[-.001,.003,.002,-.004])]
    samples = [dict(cell=0, cycle=1, half=1,
                    A=[[1,.015,0,0],[0,.97,.01,0],[.005,0,1.02,.005],[0,.01,0,.955]],
                    B=[[.05,.01,-.005],[.015,-.04,.01],[.02,.005,.03],[-.01,.025,.015]],
                    defect=[.002,-.001,.0005,.0015]),
               dict(cell=0, cycle=1, half=2, **{k:copy.deepcopy(cells[0][k]) for k in ("A","B","defect")}),
               dict(cell=1, cycle=2, half=2, **{k:copy.deepcopy(cells[1][k]) for k in ("A","B","defect")})]
    return dict(name="producer_generic_noncommuting", source=dict(kind="generic_synthetic", nx=4,nu=3,
                cells=cells,samples=samples), actual_initial=[.16,-.09,.07,.11],
                terms=terms(4,3,2,len(samples)),evaluate_controls=controls(3,2),scope=FLAGS.copy())


def write(path, obj):
    with path.open("x") as stream:
        json.dump(obj, stream, indent=2, allow_nan=False)
        stream.write("\n")


def main():
    parser=argparse.ArgumentParser();parser.add_argument("--source",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True);args=parser.parse_args()
    raw=args.source.read_bytes();assert hashlib.sha256(raw).hexdigest()==SOURCE_SHA
    bundle=json.loads(raw);args.output.mkdir(parents=True,exist_ok=False)
    ready={r["name"]:r for r in bundle["complete"]};refused={r["name"]:r for r in bundle["refused"]}
    policy=dict(schema_version=1,limits=LIMITS,scope=FLAGS,artifacts=[dict(id="archived_f1_v1",
                path=str(args.source.resolve()),sha256=SOURCE_SHA,source_binary_sha256=F1_SHA,
                certificate_name=CERT,archive_sha256=SOURCE_ARCHIVE_SHA)])
    good=[public_case("producer_public_startup",ready["root_trial_identity_start"]),
          public_case("producer_public_nonuniform_shifted",ready["root_trial_nonuniform_finite_state_controls"],True),
          generic_case()]
    zero=copy.deepcopy(good[-1]);zero["name"]="producer_generic_zero_terms";zero["terms"]=[];good.append(zero)
    bad=[public_case("producer_refused_"+name,row,roster="refused") for name,row in refused.items()]
    wrong=copy.deepcopy(good[-1]);wrong["name"]="producer_quoted_cycle_refused";wrong["source"]["cells"][0]["cycles"]="1";bad.append(wrong)
    wrong=copy.deepcopy(good[-1]);wrong["name"]="producer_false_safety_refused";wrong["scope"]["safety"]=True;bad.append(wrong)
    wrong=copy.deepcopy(good[-1]);wrong["name"]="producer_ragged_matrix_refused";wrong["source"]["cells"][0]["A"][0].pop();bad.append(wrong)
    wrong=copy.deepcopy(good[-1]);wrong["name"]="producer_overflow_refused";wrong["source"]["cells"][0]["A"][0][0]=1e308;wrong["actual_initial"][0]=1e308;bad.append(wrong)
    write(args.output/"policy.json",policy);write(args.output/"cases.json",dict(schema_version=1,cases=good+bad))
    write(args.output/"empty.json",dict(schema_version=1,cases=[]))
    write(args.output/"DECLARATION.json",dict(source_sha256=SOURCE_SHA,source_archive_sha256=SOURCE_ARCHIVE_SHA,
          names=[x["name"] for x in good+bad],expected_success={x["name"]:x in good for x in good+bad},
          half_square_convention=True, comparison_abs=2e-12,comparison_rel=2e-12,
          scope="General affine algebra diagnostic only; fixed bounded v1 envelope, no physical shift certificate",
          earlier_fd_failure="RETAINED_IMMUTABLE",phase5="NOT_ACCEPTED",scope_flags=FLAGS))
    # Malformed process controls are separate documents, not values JSON permits.
    for name,raw in (("duplicate_keys",'{"schema_version":1,"cases":[],"cases":[]}'),
                     ("yaml_refused","schema_version: 1\ncases: []\n"),
                     ("nonfinite_refused",'{"schema_version":1,"cases":[NaN]}')):
        (args.output/(name+".json")).write_text(raw+"\n")
    files={p.name:dict(sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size)
           for p in args.output.iterdir() if p.is_file()}
    write(args.output/"INPUT_MANIFEST.json",dict(files=files,script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          prepared_inputs_only=True,no_model_or_binary_call=True,requires_separate_full_dependency_freeze=True))


if __name__=="__main__":main()
