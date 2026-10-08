#!/usr/bin/env python3
"""Independent producer NumPy algebra checker. SOURCE ONLY before dispatch."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import numpy as np

ATOL=2e-12
RTOL=2e-12
FLAGS=dict.fromkeys(["connecting_segment","ball","admissibility","execution","safety",
                     "uniform_error_bound","controller_readiness"],False)


def load(path):
    def pairs(items):
        out={}
        for k,v in items:
            if k in out:raise ValueError("duplicate key "+k)
            out[k]=v
        return out
    def bad(x):raise ValueError("nonfinite JSON "+x)
    return json.loads(Path(path).read_text(),object_pairs_hook=pairs,parse_constant=bad)


def packed(z):
    return np.array(sum((z[k] for k in ("q","v","C","w")),[])+[z["s"],z["r"]],dtype=float)


def view(offset,control,initial):
    return dict(offset=offset.tolist(),control=control.tolist(),initial=initial.tolist())


def compare(expected,actual,path="root"):
    if isinstance(expected,dict):
        assert type(actual) is dict and set(expected)==set(actual),(path,"keys",set(expected),set(actual))
        for k in expected:compare(expected[k],actual[k],path+"."+k)
    elif isinstance(expected,list):
        assert type(actual) is list and len(expected)==len(actual),(path,"length")
        for i,(a,b) in enumerate(zip(expected,actual)):compare(a,b,path+f"[{i}]")
    elif isinstance(expected,bool):assert type(actual) is bool and expected==actual,(path,"boolean")
    elif isinstance(expected,str):assert type(actual) is str and expected==actual,(path,"string")
    elif isinstance(expected,int):assert type(actual) is int and expected==actual,(path,"integer")
    else:
        assert type(actual) in (float,int) and math.isfinite(actual),(path,"finite numeric type")
        assert abs(expected-actual)<=ATOL+RTOL*max(abs(expected),abs(actual)),(path,expected,actual)


def reference(case,policy):
    src=case["source"];public=src["kind"]=="public_saved_json"
    if public:
        artifact=next(a for a in policy["artifacts"] if a["id"]==src["artifact_id"])
        raw=Path(artifact["path"]).read_bytes();assert hashlib.sha256(raw).hexdigest()==artifact["sha256"]
        bundle=load(artifact["path"]);row=next(r for r in bundle[src["roster"]] if r["name"]==src["row_name"])
        original=row["original_output"];descriptor=row["original_input"]
        assert original["value"]["success"] and original["extension_jacobian_success"]
        nx,nu=30,8;cells=original["cell_maps"];cycles=[c["cycles"] for c in descriptor["cells"]]
        samples=[dict(cell=s["cell"],cycle=s["cycle"],half=s["half"],A=s["cell_A"],B=s["cell_B"],defect=s["cell_defect"])
                 for s in original["substep_maps"]]
        ident=dict(kind="public_saved_json",artifact_id=artifact["id"],file_sha256=artifact["sha256"],
                   row_name=row["name"],source_binary_sha256=artifact["source_binary_sha256"],
                   certificate_name=artifact["certificate_name"],full_nominal_source_certified=True,
                   actual_initial_shifted=not np.array_equal(np.array(case["actual_initial"]),packed(descriptor["state"])))
        distinct=False;last=0
        for c,m in zip(cells,cycles):
            last+=m;local=original["cycle_maps"][last-1]
            if m>1 and any(not np.array_equal(np.array(c[k]),np.array(local[k])) for k in ("A","B","defect")):distinct=True
        bridge=dict(used_native_normalization=True,matched_json_cumulative_fields=True,
                    multicycle_local_cumulative_distinct=distinct,source_file_sha256=artifact["sha256"],
                    source_binary_sha256=artifact["source_binary_sha256"],cell_count=len(cells),sample_count=len(samples))
    else:
        nx,nu=src["nx"],src["nu"];cells=src["cells"];cycles=[c["cycles"] for c in cells];samples=src.get("samples",[])
        ident=dict(kind="generic_synthetic",artifact_id="",file_sha256="",row_name="",source_binary_sha256="",
                   certificate_name="",full_nominal_source_certified=False,actual_initial_shifted=False)
        bridge=dict(used_native_normalization=False,matched_json_cumulative_fields=False,
                    multicycle_local_cumulative_distinct=False,source_file_sha256="",source_binary_sha256="",
                    cell_count=0,sample_count=0)
    N=len(cells);dx=nx*(N+1);du=nu*N;dy=dx+du
    L=np.eye(dx);E=np.zeros((dx,du));f=np.zeros(dx);f[:nx]=case["actual_initial"]
    initial_selector=np.zeros((dx,nx));initial_selector[:nx]=np.eye(nx)
    offsets=[np.array(case["actual_initial"],float)];controls=[np.zeros((nx,du))];initials=[np.eye(nx)]
    for c,cell in enumerate(cells):
        A=np.array(cell["A"],float);B=np.array(cell["B"],float);d=np.array(cell["defect"],float)
        L[(c+1)*nx:(c+2)*nx,c*nx:(c+1)*nx]=-A;E[(c+1)*nx:(c+2)*nx,c*nu:(c+1)*nu]=B;f[(c+1)*nx:(c+2)*nx]=d
        o=A@offsets[-1]+d;M=A@controls[-1];M[:,c*nu:(c+1)*nu]+=B;P=A@initials[-1]
        offsets.append(o);controls.append(M);initials.append(P)
    # Independent dense solve, not copied from the recursive construction.
    XC=np.linalg.solve(L,E);XO=np.linalg.solve(L,f);XP=np.linalg.solve(L,initial_selector)
    T=np.vstack((XC,np.eye(du)));t=np.concatenate((XO,np.zeros(du)));PI=np.vstack((XP,np.zeros((du,nx))))
    sample_out=[];cell_errors=[];sample_errors=[]
    if public:
        for c in cells:
            err=np.array(c["A"])@packed(c["origin"])+np.array(c["B"])@np.array(c["input"])+np.array(c["defect"])-packed(c["state"])
            cell_errors.append(float(np.max(np.abs(err))))
    for j,s in enumerate(samples):
        c=s["cell"];A=np.array(s["A"],float);B=np.array(s["B"],float);d=np.array(s["defect"],float)
        S=np.zeros((nx,dy));S[:,c*nx:(c+1)*nx]=A;S[:,dx+c*nu:dx+(c+1)*nu]=B
        M=A@controls[c];M[:,c*nu:(c+1)*nu]+=B
        sample_out.append(dict(cell=c,cycle=s["cycle"],half=s["half"],
             recursive=view(A@offsets[c]+d,M,A@initials[c]),lifted_factor=S.tolist(),lifted_offset=d.tolist(),
             eliminated=view(S@t+d,S@T,S@PI)))
        if public:
            sm=original["substep_maps"][j];err=A@packed(sm["cell_origin"])+B@np.array(sm["input"])+d-packed(sm["state"])
            sample_errors.append(float(np.max(np.abs(err))))
    assembly=dict(nx=nx,nu=nu,N=N,cycles=cycles,recursive_states=[view(o,M,P) for o,M,P in zip(offsets,controls,initials)],
                  lifted=dict(L=L.tolist(),E=E.tolist(),f=f.tolist(),initial_selector=initial_selector.tolist(),
                  X_control=XC.tolist(),X_offset=XO.tolist(),X_initial=XP.tolist(),T=T.tolist(),t=t.tolist()),
                  samples=sample_out,nominal_cell_defect_residual_max=cell_errors,nominal_sample_defect_residual_max=sample_errors)
    ts=[]
    for term in case["terms"]:
        F=np.array(term["F"],float);f0=np.array(term["f0"],float);ell=np.array(term["linear"],float);k=float(term["constant"])
        for addition in term["sample_additions"]:
            s=sample_out[addition["sample_index"]];C=np.array(addition["coefficient"],float)
            F=F+C@np.array(s["lifted_factor"]);f0=f0+C@np.array(s["lifted_offset"])
        Fc=F@T;fc=F@t+f0;H=Fc.T@Fc;g=Fc.T@fc+T.T@ell;constant=.5*float(fc@fc)+float(ell@t)+k
        ts.append(dict(name=term["name"],units=term["units"],used_F=F.tolist(),used_f0=f0.tolist(),
                  used_linear=ell.tolist(),used_constant=k,factor=Fc.tolist(),offset=fc.tolist(),H=H.tolist(),g=g.tolist(),constant=constant))
    total=dict(name="sum",units="declared_terms",used_F=[],used_f0=[],used_linear=np.zeros(dy).tolist(),used_constant=0.0,
               factor=[],offset=[],H=np.zeros((du,du)).tolist(),g=np.zeros(du).tolist(),constant=0.0)
    # Canonical sum uses explicit input term order, not concatenated factor recomputation.
    for term in ts:
        for key in ("used_F","used_f0","factor","offset"):total[key]+=term[key]
        for key in ("used_linear","H","g"):total[key]=(np.array(total[key])+np.array(term[key])).tolist()
        for key in ("used_constant","constant"):total[key]+=term[key]
    U=np.array(case["evaluate_controls"],float);y=T@U+t
    def evaluate(term):
        F=np.array(term["used_F"],float).reshape((-1,dy));f0=np.array(term["used_f0"]);ell=np.array(term["used_linear"])
        H=np.array(term["H"]);g=np.array(term["g"]);Hs=.5*(H+H.T);r=F@y+f0
        return dict(name=term["name"],lifted_value=.5*float(r@r)+float(ell@y)+term["used_constant"],
                    condensed_value=.5*float(U@H@U)+float(g@U)+term["constant"],
                    lifted_chain_gradient=(T.T@(F.T@r+ell)).tolist(),condensed_gradient=(Hs@U+g).tolist(),
                    lifted_chain_hessian=(((T.T@F.T)@F)@T).tolist(),condensed_hessian=Hs.tolist())
    return dict(name=case["name"],success=True,error="",source=ident,scope=FLAGS,native_bridge=bridge,
                assembly=assembly,objective=dict(terms=ts,sum=total),
                evaluation=dict(controls=U.tolist(),terms=[evaluate(t) for t in ts],sum=evaluate(total)))


def verify(inputs,policy,declaration,output):
    assert set(output)=={"schema_version","metadata","cases"} and type(output["schema_version"]) is int and output["schema_version"]==1
    assert output["metadata"]["namespace"]=="phase5_public_affine_horizon"
    compare(policy["limits"],output["metadata"]["limits"]);compare(FLAGS,output["metadata"]["scope"])
    assert len(inputs["cases"])==len(output["cases"])
    for case,result in zip(inputs["cases"],output["cases"]):
        assert result["name"]==case["name"] and type(result["success"]) is bool
        expected=declaration["expected_success"][case["name"]];assert result["success"] is expected
        if expected:compare(reference(case,policy),result,case["name"])
        else:
            assert set(result)=={"name","success","error","refusal_code","scope","source","source_diagnostic"}
            assert type(result["error"]) is str and result["error"] and type(result["refusal_code"]) is str
            compare(FLAGS,result["scope"]);assert result["source"]==case["source"]
            if case["source"]["kind"]=="public_saved_json":
                a=next(a for a in policy["artifacts"] if a["id"]==case["source"]["artifact_id"])
                row=next(r for r in load(a["path"])[case["source"]["roster"]] if r["name"]==case["source"]["row_name"])
                assert result["source_diagnostic"]==row["original_output"]
            else:assert result["source_diagnostic"]=={}


def main():
    parser=argparse.ArgumentParser()
    for k in ("inputs","policy","declaration","output","report"):parser.add_argument("--"+k,type=Path,required=True)
    args=parser.parse_args();assert not args.report.exists()
    inputs,policy,declaration,output=(load(p) for p in (args.inputs,args.policy,args.declaration,args.output))
    policy_sha=hashlib.sha256(args.policy.read_bytes()).hexdigest();assert output["metadata"]["policy_sha256"]==policy_sha
    verify(inputs,policy,declaration,output)
    positives=[i for i,r in enumerate(output["cases"]) if r["success"]];first=positives[0]
    controls=[]
    def control(name,mutate):
        altered=copy.deepcopy(output);mutate(altered)
        try:verify(inputs,policy,declaration,altered)
        except (AssertionError,KeyError,ValueError,TypeError,IndexError):controls.append(dict(name=name,rejected=True));return
        raise AssertionError("negative output accepted: "+name)
    control("omitted_case",lambda d:d["cases"].pop())
    control("false_safety",lambda d:d["cases"][first]["scope"].__setitem__("safety",True))
    control("unused_native_bridge",lambda d:d["cases"][first]["native_bridge"].__setitem__("used_native_normalization",False))
    control("changed_source_hash",lambda d:d["cases"][first]["source"].__setitem__("file_sha256","0"*64))
    control("dropped_constant",lambda d:d["cases"][first]["objective"]["sum"].__setitem__("constant",0.0))
    control("missing_sum_used_F",lambda d:d["cases"][first]["objective"]["sum"].pop("used_F"))
    control("missing_initial_P",lambda d:d["cases"][first]["assembly"]["recursive_states"][0]["initial"][0].__setitem__(0,0.0))
    control("missing_sample_P",lambda d:d["cases"][first]["assembly"]["samples"][0]["recursive"]["initial"][0].__setitem__(0,0.0))
    control("lost_linear_gradient",lambda d:d["cases"][first]["objective"]["sum"]["g"].__setitem__(0,0.0))
    control("nominal_state_reset",lambda d:d["cases"][first]["assembly"]["recursive_states"][1]["offset"].__setitem__(0,0.0))
    control("nonfinite_coefficient",lambda d:d["cases"][first]["objective"]["sum"]["H"][0].__setitem__(0,float("nan")))
    refusals=[i for i,r in enumerate(output["cases"]) if not r["success"]]
    control("tied_cell_input_columns",lambda d:d["cases"][1]["assembly"]["recursive_states"][-1]["control"][0].__setitem__(8,d["cases"][1]["assembly"]["recursive_states"][-1]["control"][0][0]))
    def local_substitution(d):
        case=inputs["cases"][1];src=case["source"];artifact=next(a for a in policy["artifacts"] if a["id"]==src["artifact_id"])
        row=next(r for r in load(artifact["path"])[src["roster"]] if r["name"]==src["row_name"])
        local=row["original_output"]["cycle_maps"][3]["A"]
        # N4 cell1 cycles3: substitute lastcycle local block for fullcell block.
        for i in range(30):
            for j in range(30):d["cases"][1]["assembly"]["lifted"]["L"][60+i][30+j]=-local[i][j]
    control("native_lastcycle_substitution",local_substitution)
    control("fabricated_failed_tail",lambda d:d["cases"][refusals[0]].__setitem__("assembly",{}))
    report=dict(first_attempt_verification="PASS",cases=len(output["cases"]),negative_controls=controls,
                comparison_abs=ATOL,comparison_rel=RTOL,source_model_calls=0,scope_flags=FLAGS,
                earlier_fd_failure="RETAINED_IMMUTABLE",phase5="NOT_ACCEPTED",
                files={k:hashlib.sha256(getattr(args,k).read_bytes()).hexdigest() for k in ("inputs","policy","declaration","output")})
    with args.report.open("x") as f:json.dump(report,f,indent=2,allow_nan=False);f.write("\n")


if __name__=="__main__":main()
