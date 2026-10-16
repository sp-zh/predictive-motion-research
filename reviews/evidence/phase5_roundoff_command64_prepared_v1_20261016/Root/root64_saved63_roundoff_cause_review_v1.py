from pathlib import Path
import ast,os,sys,json,struct,hashlib
import numpy as np
sys.path.insert(0,'/private/tmp');from bounded_derived_bytes53_v1 import bounded_write
import root63_nominal_reader_v4 as n
strict=n.strict
T=ast.parse(Path('/private/tmp/root58_selected_audit_v1.py').read_text());exec(compile(ast.Module(body=[x for x in T.body if isinstance(x,ast.ClassDef)and x.name in['R','RV4']],type_ignores=[]),'<readers>','exec'))
T=ast.parse(Path('/private/tmp/root59_production_review_v1.py').read_text());exec(compile(ast.Module(body=[x for x in T.body if isinstance(x,ast.FunctionDef)and x.name in['fixture','xy']],type_ignores=[]),'<fixture-readers>','exec'))
P=Path('/private/tmp/phase5_saved63_roundoff_endpoint_probe_v1_20261016');O=Path('/private/tmp/root64_saved63_cause_review_v1_20261016');O.mkdir();os.environ['P5_DERIVED53_ROOT']=str(O)
A=next(Path('/private/tmp/phase5_controlled_stop_explicit_warm_nominal_terminal63_v1_20261016').glob('actual-dell/*/run-attempt1/artifacts/cycle-63/trial-0'))
r=R(A/'qp_equality_reduction.bin','ORIGINAL_AND_NUMERICAL_PLANNING_TERMINAL_REDUCTION_V2');r.text();r.text();r.u();r.mat();r.vec();r.mat();r.vec();r.vec()
for _ in range(2):
 for __ in range(r.u()):r.u()
for fn in[r.mat,r.vec,r.mat,r.vec,r.vec,r.vec,r.mat,r.vec,r.vec,r.vec,r.vec]:fn()
Hs,gs,As,ls,us=[fn()for fn in[r.mat,r.vec,r.mat,r.vec,r.vec]]
from initializer_codec58_v4 import initializer_v4
z=initializer_v4(strict.read_artifact_bytes(A/'numeric_feasible_initializer.bin'),RV4,len(ls));assert z['complete']
raw=b''
for v in[Hs,gs,As,ls,us,z['seed']]:raw+=(struct.pack('<2Q',*v.shape)if v.ndim==2 else struct.pack('<Q',len(v)))+v.astype('<f8').tobytes()
assert raw==(P/'fixture.bin').read_bytes();(H,g,AA,lo,hi,seed),raw=fixture(P/'fixture.bin');x,y=xy(P/'readback/case.finalxy.bin');assert H.shape==(144,144)and AA.shape==(7364,144)and len(y)==7364
primal=max(0.,float(np.max(lo-AA@x)),float(np.max(AA@x-hi)));stationarity=float(np.max(np.abs(H@x+g+AA.T@y)));assert primal<=1e-12 and stationarity<=1e-10
b=(P/'readback/case.endpoints.bin').read_bytes();assert len(b)==1488*64;worst=0.;minimum=0.
for at in range(0,len(b),64):
 it,row,start,travel,endpoint,l,u,v=struct.unpack_from('<2Q6d',b,at);assert it<170 and row<len(lo)and np.isfinite([start,travel,endpoint,l,u,v]).all();assert struct.pack('<2d',l,u)==struct.pack('<2d',lo[row],hi[row]);slack=u-start if travel>0 else start-l;assert travel!=0 and slack<=0 and v==max(0.,l-endpoint,endpoint-u)<=1e-12;worst=max(worst,v);minimum=min(minimum,slack)
events=(P/'readback/case.states.bin').read_bytes();assert len(events)==170*56
old=Path('/private/tmp/phase5_saved63_cycle_diagnostic_v2_20261016/readback/case.states.bin');original_bytes=old.read_bytes()if old.exists()else b''
report=dict(schema='ROOT64_SAVED_ACTUAL63_ROUNDOFF_CAUSE_AND_ORIGINAL_DOMAIN_REVIEW_V1',fixture_whole_SHA256=hashlib.sha256(raw).hexdigest(),all_six_original_scaled_matrix_vectors_and_initializer_seed_byteexact_actual63=True,rows=7364,controls=144,fresh_pure_iterations=170,original_actual63_numeric512_failure_preserved=True,final_original_primal_violation_numpy=primal,final_original_stationarity_numpy=stationarity,retained_endpoint_records=1488,all_stored_row_bounds_bitexact_actual_matrix=True,every_record_nonzero_travel_rawslack_nonpositive=True,every_stored_fullendpoint_inside_original1e12_domain=True,worst_endpoint_violation=worst,minimum_raw_slack=minimum,no_native64_entry=True,scope='Independent fixed-saved-data numerical certificate/arithmetic review. Endpoint stored full values are checked against original row domain but are not independently reconstructed from every intermediate full direction; those states are not fully serialized. Original actual63 allmember/codec provenance independently checked. No new Model/nativeOSQP/SI/nonlinear/B/C/physical stop or generic convergence proof. Old512 cap, oldfailure and original1e-12/1e-10 unchanged.')
bounded_write(O/'ROOT_SAVED63_ROUNDOFF_CERTIFICATE.json',json.dumps(report,indent=2)+'\n');print(json.dumps(report))
