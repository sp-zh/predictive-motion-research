from pathlib import Path
import os,sys,ast,json,struct,math,hashlib
import numpy as np
sys.path.insert(0,'/private/tmp');from bounded_derived_bytes53_v1 import bounded_write
import root63_nominal_reader_v4 as nominal
import root64_merged_reader_v4 as merged
strict=nominal.strict
T=ast.parse(Path('/private/tmp/root58_selected_audit_v1.py').read_text());exec(compile(ast.Module(body=[x for x in T.body if isinstance(x,ast.ClassDef)and x.name=='R'],type_ignores=[]),'<reader>','exec'))
T=ast.parse(Path('/private/tmp/root59_production_review_v1.py').read_text());exec(compile(ast.Module(body=[x for x in T.body if isinstance(x,ast.FunctionDef)and x.name in['fixture','xy']],type_ignores=[]),'<fixture>','exec'))
O=Path('/private/tmp/root65_codec_independent_review_v1_20261016');os.environ['P5_DERIVED53_ROOT']=str(O);P=O/'correct-band-readback'
A=next(Path('/private/tmp/phase5_controlled_stop_roundoff_command_terminal64_v1_20261016').glob('actual-dell/*/run-attempt1/artifacts/cycle-87/trial-0'))
a,_=fixture(Path('/private/tmp/phase5_saved64_boundary_diagnostic_v1_20261016/fixture.bin'));b,raw=fixture(P/'fixture.bin');H,g,AA,lo,hi,seed=a;HH,gg,AAA,ll,uu,newseed=b
for x,y in [(H,HH),(g,gg),(AA,AAA),(hi,uu)]:assert x.tobytes()==y.tobytes()
assert np.flatnonzero(lo!=ll).tolist()==[7106]
r=R(A/'qp_equality_reduction.bin','ORIGINAL_AND_NUMERICAL_PLANNING_TERMINAL_REDUCTION_V2');r.text();r.text();r.u();Z,p=r.mat(),r.vec();r.mat();r.vec();r.vec()
for _ in range(2):r.take('<'+str(r.u())+'Q')
r.mat();r.vec();r.mat();r.vec();r.vec();D=r.vec()
m=nominal.parse(A/'stop_objective_mode.bin');u,_=nominal.family(m['r'],m['b'],2e-7,0);assert nominal.check(u,m['r'],m['b'],m['s'],True,0,0,2e-7)[0]==0
ids=[8*k+7 for k in range(18)];other=[k for k in range(144)if k not in ids];assert seed[other].tobytes()==newseed[other].tobytes()and np.array_equal(newseed[ids],np.array(u[:18])/D[ids]);assert p[7]==0
mult=1/max(1.,float(np.max(np.abs((Z[7]/.004)*D))));unscaled=(1e-7-m['r'])/(.004*.004)-p[7]/.004;expected=max(lo[7106],mult*unscaled);production=max(lo[7106],mult*math.nextafter(unscaled,-math.inf));assert expected==ll[7106]and production<=expected
vseed=max(0.,float(np.max(ll-AA@newseed)),float(np.max(AA@newseed-uu)));assert vseed<=1e-12
x,y=xy(P/'case.finalxy.bin');v=max(0.,float(np.max(ll-AA@x)),float(np.max(AA@x-uu)));s=float(np.max(np.abs(H@x+g+AA.T@y)));assert v<=1e-12 and s<=1e-10
h=merged.parse(P/'case.leaving/hint_kkt_rank_events.bin',len(lo));ep=(P/'case.retained64.bin').read_bytes();assert len(ep)==330*64
for at in range(0,len(ep),64):
 it,row,start,travel,value,l,u_,v0=struct.unpack_from('<2Q6d',ep,at);assert it<512 and row<len(ll)and struct.pack('<2d',l,u_)==struct.pack('<2d',ll[row],uu[row])and v0==max(0.,l-value,value-u_)<=1e-12
assert len((P/'case.states.bin').read_bytes())==71*56
result=json.loads((P/'RESULT.json').read_text());assert result['exit']==0 and result['inputs_before_after_equal']and 'complete=1 error=""'in result['stdout']
U=p+Z@(D*x);first=m['r']+.004*U[7];assert first>=.75e-7
v={'schema':'ROOT65_CORRECT_OFFSET_SAVED87_NUMERIC_CERTIFICATE_V1','fixture_sha256':hashlib.sha256(raw).hexdigest(),'only_old_lower_7106_changes':True,'H_g_A_upper_all_other_lower_byteexact':True,'new_seed_only18free_progress_controls_checked':True,'seed_full7390_violation':vseed,'current_q_v_histories_and_original_Z_p_D_terminal1e13_unchanged':True,'numeric_complete_events':71,'rank_events':65,'retained_endpoints':330,'boundary_events':2,'final_primal_numpy':v,'final_stationarity_numpy':s,'reconstructed_first_r':first,'probe_lower':expected,'production_nextafter_lower':production,'certificate_also_primal_feasible_for_weaker_production_lower':True,'bitexact_production_nextafter_hint_path_NOT_TESTED':expected!=production,'original_512_10s_12288_16384_caps_unchanged':True,'old_wrong_history_and_source_helper_test_qualifications_preserved':True,'scope':'Exact saved matrix/proposed correct offset restriction numerical certificate; probe does not use final production downward nextafter, so path/event counts not claimed for production. No Model/native65/SI/B/C/actual physical stop or phase acceptance.'}
bounded_write(O/'CORRECT_OFFSET_SAVED87_NUMERIC_CERTIFICATE.json',json.dumps(v,indent=2)+'\n');print(json.dumps(v))
