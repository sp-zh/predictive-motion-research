from pathlib import Path
import os,sys,ast,json,math,struct
import numpy as np
sys.path.insert(0,'/private/tmp');sys.path.insert(0,'/private/tmp/root65_codec_independent_review_v1_20261016')
from bounded_derived_bytes53_v1 import bounded_write
import reader as nominal
strict=nominal.old.strict
T=ast.parse(Path('/private/tmp/root58_selected_audit_v1.py').read_text());exec(compile(ast.Module(body=[x for x in T.body if isinstance(x,ast.ClassDef)and x.name=='R'],type_ignores=[]),'<file-reader>','exec'))
O=Path('/private/tmp/root65_actual_review_v1_20261016');os.environ['P5_DERIVED53_ROOT']=str(O);P=O/'selected/native65/run-attempt1/artifacts/cycle-50/trial-0'
m=nominal.parse(P/'stop_objective_mode.bin')
r=R(P/'candidate.bin','SOLVER_RESULT_AND_DATA_ONLY_PREVIEW');reason=r.text();permission,attempts,wrappers,status,rawstatus,api,it,vr=r.take('<8Q');U=r.vec();diag=r.take('<14d');r.take('<4Q');r.text();r.take('<4Q');viol=r.arr(r.u());r.u();r.take('<4d');r.take('<2Q');assert r.take('<3Q')==(0,0,0);r.end();assert(permission,attempts,wrappers,status,rawstatus,api,it)==(0,1,1,0,1,0,1)and len(U)==160 and max(viol)<=1e-7
r=R(P/'planning_guard.bin','EXPLICIT_ALPHA_PROGRESS_JERK_CURRENT_FIRST_COMMAND_AND_FIRST_PROGRESS_BAND_V7');solver,stricta,pjerk,sjerk,prevb,terminal=r.take('<6d');base=r.u();r.take('<'+str(r.u())+'Q');r.vec();r.text();center=r.vec();r.u();r.take('<'+str(r.u())+'Q');r.mat();margin=r.d();assert r.u()==1 and r.take('<3d')==(.5,.75,1e-6);n=r.u();assert n==7 and np.array_equal(center,m['controls'].reshape(-1));guards=[]
for _ in range(7):
 j=r.u();ww,a,nw,sb,tb,lower,upper=r.take('<7d');assert ww==m['w'][j]and a==center[j]
 rawsolver=max(.5*abs(ww),abs(ww+.004*a),.5e-6);rawstrict=max(.75*abs(ww),abs(ww+.004*a),.75e-6);strictB=math.nextafter(rawstrict*(1+16*sys.float_info.epsilon),math.inf)
 lo=min(max(max(-1.,a-solver),math.nextafter((-rawsolver-ww)/.004,-math.inf)),a);hi=max(min(min(1.,a+solver),math.nextafter((rawsolver-ww)/.004,math.inf)),a)
 assert(nw,sb,tb,lower,upper)==(ww+.004*a,rawsolver,strictB,lo,hi)
 guards.append({'joint0':j,'w':ww,'nominal_alpha':a,'native_alpha':float(U[j]),'strict_bound':tb,'lower':lo,'upper':hi,'native_next_w':ww+.004*float(U[j]),'native_strict_gap':math.nextafter(abs(ww+.004*float(U[j])),math.inf)-tb})
assert r.u()==1 and r.take('<2d')==(1e-7,.75e-7);r.text();r.end()
r=R(P/'qp_equality_reduction.bin','ORIGINAL_AND_NUMERICAL_PLANNING_TERMINAL_REDUCTION_V2');r.text();stage=r.text();valid=r.u();Z,p=r.mat(),r.vec();r.mat();r.vec();r.vec()
for _ in range(2):r.take('<'+str(r.u())+'Q')
r.mat();r.vec();r.mat();r.vec();r.vec();D=r.vec();r.mat();r.vec();r.vec();r.vec();r.vec();H,g,A,lo,hi=r.mat(),r.vec(),r.mat(),r.vec(),r.vec();r.mat();seed=r.vec();r.text();flags=r.take('<5Q');nx,ny=r.vec(),r.vec();r.u();r.take('<5d');r.end()
T=ast.parse(Path('/private/tmp/root_independent_controlled_stop52_review_20261012/reference_source/audit_geometry_qp_actual.py').read_text());cl=next(x for x in T.body if isinstance(x,ast.ClassDef)and x.name=='R');cl.name='WireR';fn=next(x for x in T.body if isinstance(x,ast.FunctionDef)and x.name=='parse_current_hint')
for n in ast.walk(fn):
 if isinstance(n,ast.Name)and n.id=='R':n.id='WireR'
exec(compile(ast.Module(body=[cl,fn],type_ignores=[]),'<hint-wire>','exec'))
hint=parse_current_hint(strict.read_artifact_bytes(P/'current_numeric_hint.bin'));assert hint['complete']==1 and not hint['error']and hint['x'].tobytes()==seed.tobytes();assert np.array_equal(Z[:144],np.eye(144))and np.array_equal(p[:144],np.zeros(144));assert flags==(1,1,1,1,1)and A.shape==(7337,144)
for row in guards:
 j=row['joint0'];ha=float(D[j])*float(hint['x'][j]);na=float(D[j])*float(nx[j]);assert na==U[j]
 row.update(hint_alpha=ha,native_minus_hint_alpha=na-ha,hint_strict_gap=math.nextafter(abs(row['w']+.004*ha),math.inf)-row['strict_bound'],native_gap_ULPs=row['native_strict_gap']/math.ulp(row['strict_bound']))
assert all(q['hint_strict_gap']<=0 for q in guards)and[q['joint0']for q in guards if q['native_strict_gap']>0]==[4]
res={}
for name,x,y in [('hint',hint['x'],hint['y']),('native',nx,ny)]:
 ax=A@x;res[name]={'primal':max(0.,float(np.max(lo-ax)),float(np.max(ax-hi))),'stationarity':float(np.max(np.abs(H@x+g+A.T@y)))}
out={'schema':'ROOT65_FAILED50_NATIVE_PERTURBATION_EXACT_GUARD_REVIEW_V1','sourcecomplete_archive_bound_before_decode':True,'native_Solved_raw1_enum0_iterations1':True,'original_SI14756_reported_max':float(max(viol)),'candidate_preview_tail_request_absent':True,'all_first7_guard_bounds_rederived_from_new_nominal_and_history':True,'hint_last_seed_bitexact':True,'current_scaled_rows':len(lo),'raw_native_flags':flags,'rows':guards,'independent_scaled_residuals':res,'failed_joint0':4,'cause':'Hint satisfies all seven existing strict-first-command checks. One native iteration moves joint5 alpha negatively by ~8.78e-14; its nextw exceeds the unchanged outward strict bound by ~3.48e-16 (3207ULPs). Existing gate correctly refuses before forward/B/C; no clipping, tolerance relaxation, solver/Model rerun or new66.','scope':'Exact retained binary64 reconstruction and matrix residuals, not a new solver experiment or physical stop/full-task/phase acceptance.'}
bounded_write(O/'FAILED50_NATIVE_PERTURBATION_INDEPENDENT_REVIEW.json',json.dumps(out,indent=2)+'\n');print(json.dumps({'failed_joint0':4,'joint5':guards[4],'residuals':res}))
