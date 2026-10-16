from pathlib import Path
import os,sys,ast,json,struct,hashlib
import numpy as np
sys.path.insert(0,'/private/tmp');from bounded_derived_bytes53_v1 import bounded_write
import root63_nominal_reader_v4 as nominal
import root64_merged_reader_v4 as merged
strict=nominal.strict
T=ast.parse(Path('/private/tmp/root58_selected_audit_v1.py').read_text());exec(compile(ast.Module(body=[x for x in T.body if isinstance(x,ast.ClassDef)and x.name=='R'],type_ignores=[]),'<reader>','exec'))
T=ast.parse(Path('/private/tmp/root59_production_review_v1.py').read_text());exec(compile(ast.Module(body=[x for x in T.body if isinstance(x,ast.FunctionDef)and x.name in['fixture','xy']],type_ignores=[]),'<fixture>','exec'))
O=Path('/private/tmp/root65_saved_design_review_v1_20261016');os.environ['P5_DERIVED53_ROOT']=str(O);P=Path('/private/tmp/phase5_saved64_progress_band_probe_v1_20261016');A=next(Path('/private/tmp/phase5_controlled_stop_roundoff_command_terminal64_v1_20261016').glob('actual-dell/*/run-attempt1/artifacts/cycle-87/trial-0'))
a,_=fixture(Path('/private/tmp/phase5_saved64_boundary_diagnostic_v1_20261016/fixture.bin'));b,raw=fixture(P/'fixture.bin');H,g,AA,lo,hi,seed=a;HH,gg,AAA,ll,uu,newseed=b
for x,y in[(H,HH),(g,gg),(AA,AAA),(hi,uu)]:assert x.tobytes()==y.tobytes()
assert np.flatnonzero(lo!=ll).tolist()==[7106]and ll[7106]>lo[7106]
r=R(A/'qp_equality_reduction.bin','ORIGINAL_AND_NUMERICAL_PLANNING_TERMINAL_REDUCTION_V2');r.text();r.text();r.u();Z,p=r.mat(),r.vec();r.mat();r.vec();r.vec()
for _ in range(2):r.take('<'+str(r.u())+'Q')
r.mat();r.vec();r.mat();r.vec();r.vec();D=r.vec()
m=nominal.parse(A/'stop_objective_mode.bin');u,pulse=nominal.family(m['r'],m['b'],2e-7,0);pr=nominal.check(u,m['r'],m['b'],m['s'],True,0,0,2e-7);assert pr[0]==0 and m['r']+.004*u[0]>=1e-7
ids=[8*k+7 for k in range(18)];other=[k for k in range(144)if k not in ids];assert seed[other].tobytes()==newseed[other].tobytes()and np.array_equal(newseed[ids],np.array(u[:18])/D[ids]);mult=1/max(1.,float(np.max(np.abs((Z[7]/.004)*D))));expected=max(lo[7106],mult*((1e-7-m['r'])/(.004*.004)-m['b']/.004));assert expected==ll[7106]
vseed=max(0.,float(np.max(ll-AA@newseed)),float(np.max(AA@newseed-uu)));assert vseed<=1e-12
x,y=xy(O/'band_readback/case.finalxy.bin');v=max(0.,float(np.max(ll-AA@x)),float(np.max(AA@x-uu)));s=float(np.max(np.abs(H@x+g+AA.T@y)));assert v<=1e-12 and s<=1e-10
h=merged.parse(O/'band_readback/case.leaving/hint_kkt_rank_events.bin',len(lo));ep=(O/'band_readback/case.retained64.bin').read_bytes();assert len(ep)%64==0 and len(ep)//64==3145 and h['admissions']<=3145
for at in range(0,len(ep),64):
 it,row,start,travel,value,l,u,v0=struct.unpack_from('<2Q6d',ep,at);assert it<512 and row<len(ll)and struct.pack('<2d',l,u)==struct.pack('<2d',ll[row],uu[row])and v0==max(0.,l-value,value-u)<=1e-12
result=json.loads((O/'band_readback/RESULT.json').read_text());assert result['exit']==0 and result['inputs_before_after_equal']and 'complete=1 error=""'in result['stdout'];events=(O/'band_readback/case.states.bin').read_bytes();assert len(events)==117*56;U=p+Z@(D*x);rfirst=m['r']+.004*U[7];assert rfirst>=.75e-7
report=dict(schema='ROOT65_SAVED64_CURRENT87_INTERIOR_FIRST_PROGRESS_RESTRICTION_REVIEW_V1',fixture_sha256=hashlib.sha256(raw).hexdigest(),old_fixture_bound_to_original_actual87=True,original_H_g_A_upper_byteexact=True,one_existing_lower_row_tightened=7106,all_other_lower_rows_bitexact=True,current_actual_r_and_history_unchanged=True,new_seed_only18_free_progress_controls_from_original_scalar_family_target2e7=True,new_seed_full7390_rows_violation=vseed,original264_floor1e9_and_QPterminal1e13_retained=True,new_nominal_target2e7_not_original_terminal_E0_feasibility_claim=True,complete_numeric_events=117,boundary_events=902,rank_events=len(h['ranks']),retained_endpoints=3145,final_primal_numpy=v,final_stationarity_numpy=s,reconstructed_first_actual_progress_rate=rfirst,original_caps_512_10s_12288_16384_and_domains_unchanged=True,scope='Independent one stricter planning-bound/fresh scalar-derived seed and saved numerical certificate. Original matrix/cost/other bounds preserved, no actualr/control projection or relabelled oldseed. No nativeOSQP/65 Model/B/C/physical stop/task/phase proof; future baseline/current-history/strict margin/source/hotguard/backup protocol still require review.')
bounded_write(O/'FIRST_PROGRESS_BAND_REAL87_MATRIX_AND_CERTIFICATE.json',json.dumps(report,indent=2)+'\n');print(json.dumps(report))
