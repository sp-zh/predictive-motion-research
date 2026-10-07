#!/usr/bin/env python3
"""Offline captured-QP feasibility and fresh frozen-wrapper precision audit; not original candidate recovery."""
import argparse,csv,hashlib,json
from pathlib import Path
SOURCE_SHA=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
import numpy as np
from scipy.optimize import linprog
import yaml

sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ['project','consumer','solves','output']:parser.add_argument('--'+key,type=Path,required=True)
    args=parser.parse_args();root=args.project;case=root/'results/phase5/development/servo-safe-reference-v2-validation'
    freeze=json.loads((case/'frozen.json').read_text());execution=json.loads((case/'execution.json').read_text());raw=Path(execution['argv'][-1]);inputs=[]
    for name,h in execution['raw_files'].items():assert sha(raw/name)==h;inputs.append(raw/name)
    inputs.extend(case/name for name in ['frozen.json','execution.json','materialized-identity.json'])
    installed=Path('/home/codextransfer/clean-audits/root-installed-v24')
    linked=[installed/'include/predictive_motion_control/reactive_qp.hpp',installed/'lib/libreactive_qp.a',root/'.vendor/osqp-1.0.0-install/lib/libosqpstatic.a']
    identity={}
    for p,suffix in zip(linked,['include/predictive_motion_control/reactive_qp.hpp','lib/libreactive_qp.a','lib/libosqpstatic.a']):
        matches={name:h for name,h in freeze['files'].items() if name.endswith(suffix)};assert len(matches)==1 and sha(p)==next(iter(matches.values()));identity[str(p)]={'sha256':sha(p),'frozen_original':matches};inputs.append(p)
    inputs.extend([args.consumer,args.consumer.with_name('consumer.cpp'),args.solves/'solves.csv'])
    a=np.loadtxt(raw/'first_rejected_A.csv',delimiter=',');l=np.loadtxt(raw/'first_rejected_lower.csv',delimiter=',');u=np.loadtxt(raw/'first_rejected_upper.csv',delimiter=',')
    assert a.shape==(34,7) and not np.any(l>u)
    lo=np.full(7,-np.inf);hi=np.full(7,np.inf)
    for i in range(21):
        nz=np.flatnonzero(a[i]);assert len(nz)==1;j=nz[0];v=a[i,j]
        lower,upper=(l[i]/v,u[i]/v) if v>0 else (u[i]/v,l[i]/v)
        lo[j]=max(lo[j],lower);hi[j]=min(hi[j],upper)
    assert np.all(lo<=hi)
    fl,fu=np.isfinite(l),np.isfinite(u)
    lp=linprog(np.zeros(7),A_ub=np.vstack((-a[fl],a[fu])),b_ub=np.r_[-l[fl],u[fu]],bounds=[(None,None)]*7,method='highs')
    assert lp.success
    violation=lambda x:float(max(0,np.max(l-a@x),np.max(a@x-u)))
    lpviolation=violation(lp.x);assert lpviolation<1e-7
    records=list(csv.DictReader((args.solves/'solves.csv').open()));assert len(records)==4
    numeric_keys=['tolerance','violation','primal_residual','dual_residual','setup_seconds','solve_seconds','wall_seconds','solver_absolute_tolerance','solver_relative_tolerance']
    integer_keys=['case','raw_status','api_error','iterations','maximum_violation_row','velocity_entries','workspace_reused']
    for k,r in enumerate(records):
        for key in numeric_keys:r[key]=float(r[key])
        for key in integer_keys:r[key]=int(r[key])
        assert r['tolerance']==[1e-9,1e-11,1e-12,1e-13][k] and r['solver_version']=='1.0.0'
        assert r['iterations']<=4000 and not r['workspace_reused']
        r['candidate_classification']='new offline fresh solve only; original failed candidate unavailable'
        point=args.solves/f'case{k}_solved_x.csv'
        if r['status']=='SOLVED':
            assert r['raw_status']==1 and r['velocity_entries']==7
            x=np.loadtxt(point,delimiter=',');v=violation(x);r['independent_original_SI_violation']=v;r['point']=x.tolist();r['point_sha256']=sha(point);inputs.append(point);assert v<=1e-7
        else:assert not point.exists() and r['velocity_entries']==0
        i=r['maximum_violation_row']
        if 7<=i<21:r['offline_violation_row_interpretation']=('command_acceleration' if (i-7)%2==0 else 'command_jerk')+'/'+str((i-7)//2)
    summary=yaml.safe_load((raw/'summary.yaml').read_text());assert summary['primary_failure']=='CONSTRAINT_VIOLATION' and summary['completed_stop']
    result={'scope':__doc__,'verdict':'CAPTURED_QP_FEASIBLE; OFFLINE_TIGHTER_PRECISION_NATIVE_SOLVED_ONLY_POINTS_PASS_ORIGINAL_SI',
            'source_sha256':SOURCE_SHA,'original_candidate_saved':False,'original_raw_status_saved':False,'original_maximum_violation_row_saved':False,
            'original_trial_primary_failure':summary['primary_failure'],'original_trial_completed_shared_stop':summary['completed_stop'],
            'box_bounds_rad_s':{'lower':lo.tolist(),'upper':hi.tolist(),'nonempty':True},
            'LP':{'method':'independent SciPy HiGHS pure feasibility, no geometry/model modification','status':int(lp.status),'success':bool(lp.success),'original_SI_violation':lpviolation,'feasible_point':lp.x.tolist()},
            'fixed_policy':{'max_iterations':4000,'time_limit_s':.05,'original_SI_acceptance':1e-7,'offline_state_age_s':0,'initial_rho':.1,'settings':'fresh solveQp for every setting; no primal seed or retained workspace'},
            'offline_solves':records,'baseline_status_reproduced_in_one_fresh_offline_call':records[0]['status']=='CONSTRAINT_VIOLATION',
            'linked_identity':identity,'effective_inputs':{str(p):{'sha256':sha(p),'bytes':p.stat().st_size} for p in inputs},
            'baseline_row_scope':'Even when the new baseline rejects row16, original row/candidate are unknown and are not reconstructed. Single snapshot/cold solves are not plant/horizon timing or performance distributions.'}
    assert sha(Path(__file__))==SOURCE_SHA
    args.output.mkdir(parents=True,exist_ok=False);(args.output/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
    lines=['# Safe-reference v2 offline QP precision audit','',
           'Scope: one actually captured34×7 QP, four fresh offline frozen-wrapper solves. No plant/fitting/model/geometry/guard changes. Original failure had no exported raw_status, maximumViolationRow or candidate; none is reconstructed here.',
           '',f'All seven command boxes are nonempty. Independent HiGHS finds full-QP feasibility with original SI violation{lpviolation:.3e}. The linked wrapper header, reactive-QP library and OSQP1.0.0 static library exactly match v2 frozen SHA identities; root-installed-v24 is reused only after that strict comparison.',
           '', '| Requested abs/rel tolerance | New offline status / rawStatus | Iterations | Wrapper SI violation | Independent Solved-only SI violation | Wall [s] |', '|---|---|---:|---:|---:|---:|']
    for r in records:lines.append(f"| {r['tolerance']:.0e} | {r['status']} / {r['raw_status']} | {r['iterations']} | {r['violation']:.4e} | {r.get('independent_original_SI_violation','unavailable; candidate cleared')} | {r['wall_seconds']:.6f} |")
    lines+=['','The new baseline1e-9 reports nativeSOLVED/rawStatus1 but wrapperCONSTRAINT_VIOLATION,1.1616e-7 at row16 (command jerk, index4); it exposes zero velocity entries. This is the new offline result only. Repeating the status does not identify the original failed point or its worst row.','',
            'Predetermined1e-11/1e-12/1e-13 stopping tolerances all return nativeSOLVED and wrapperSOLVED, with independent original-row validation below the unchanged1e-7 threshold. No Inaccurate/failed candidate is accepted. Max iterations4000, solver budget50ms, original bounds and acceptance are unchanged. Offline state age0 is a replay convention and does not relax the live50ms observation guard.','',
            'Original safe-reference-v2 primary failure remains retained even though its shared stop completed. These cold single-QP numerical records motivate a separately frozen prospective stricter-precision setting; they do not establish a full-run repair, arbitrary matrix convergence, online250Hz performance, model-domain extension, corrected servo contract, CTRL-001 closure or Phase5 acceptance. No authoritative configuration was edited.']
    (args.output/'AUDIT.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({'LP_original_SI':lpviolation,'offline_solves':records},indent=2))


if __name__=='__main__':main()
