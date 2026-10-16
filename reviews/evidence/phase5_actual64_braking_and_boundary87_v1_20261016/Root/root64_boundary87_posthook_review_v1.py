from pathlib import Path
import os,sys,ast,json,struct,hashlib
import numpy as np
sys.path.insert(0,'/private/tmp');from bounded_derived_bytes53_v1 import bounded_write
import root63_nominal_reader_v4 as n
strict=n.strict
T=ast.parse(Path('/private/tmp/root58_selected_audit_v1.py').read_text());exec(compile(ast.Module(body=[x for x in T.body if isinstance(x,ast.ClassDef)and x.name in['R','RV4']],type_ignores=[]),'<readers>','exec'))
T=ast.parse(Path('/private/tmp/root59_production_review_v1.py').read_text());exec(compile(ast.Module(body=[x for x in T.body if isinstance(x,ast.FunctionDef)and x.name in['fixture','xy']],type_ignores=[]),'<fixtures>','exec'))
O=Path('/private/tmp/root64_actual_review_v1_20261016');os.environ['P5_DERIVED53_ROOT']=str(O);P=Path('/private/tmp/phase5_saved64_boundary_diagnostic_v1_20261016');A=next(Path('/private/tmp/phase5_controlled_stop_roundoff_command_terminal64_v1_20261016').glob('actual-dell/*/run-attempt1/artifacts/cycle-87/trial-0'))
raw=(P/'current_numeric_guess.hpp').read_text();extra='P5_BOUNDARY64_DIAGNOSTIC(iteration,r,side,slack,positive_travel,slack/positive_travel,full_values(r),lower(r),upper(r));';assert raw.count(extra)==1 and raw.replace(extra,'')==Path('tools/phase5_controlled_stop_session_v17/current_numeric_guess.hpp').read_text()
r=R(A/'qp_equality_reduction.bin','ORIGINAL_AND_NUMERICAL_PLANNING_TERMINAL_REDUCTION_V2');r.text();r.text();r.u();r.mat();r.vec();r.mat();r.vec();r.vec()
for _ in range(2):r.take('<'+str(r.u())+'Q')
for fn in[r.mat,r.vec,r.mat,r.vec,r.vec,r.vec,r.mat,r.vec,r.vec,r.vec,r.vec]:fn()
H,g,AA,lo,hi=[fn()for fn in[r.mat,r.vec,r.mat,r.vec,r.vec]]
from initializer_codec58_v4 import initializer_v4
z=initializer_v4(strict.read_artifact_bytes(A/'numeric_feasible_initializer.bin'),RV4,len(lo));assert z['complete'];buf=b''
for a in[H,g,AA,lo,hi,z['seed']]:buf+=(struct.pack('<2Q',*a.shape)if a.ndim==2 else struct.pack('<Q',len(a)))+a.astype('<f8').tobytes()
assert buf==(P/'fixture.bin').read_bytes()
r=R(A/'current_numeric_hint.bin','BOUNDED_CURRENT_MATRIX_OPTIMIZER_HINT_NOT_CANDIDATE');assert r.u()==1 and r.u()==0;error=r.text();x,y=r.vec(),r.vec();count=r.u();events=[r.take('<3q4d')for _ in range(count)];sx,sy=xy(P/'readback/case.finalxy.bin');assert x.tobytes()==sx.tobytes()and y.tobytes()==sy.tobytes()and b''.join(struct.pack('<3q4d',*v)for v in events)==(P/'readback/case.states.bin').read_bytes()and count==111
rows=json.loads((O/'FAILURE87_ALL12288_BOUNDARY_RECORDS.json').read_text());b=(P/'readback/case.boundary80.bin').read_bytes();assert len(b)==12288*80;minimum=float('inf');maximum=0.;count=0
for i,row in enumerate(rows):
 p=b[i*80:(i+1)*80];assert p[:48]==struct.pack('<3q3d',*row);it,rid,side,slack,travel,fraction,endpoint,l,u,v=struct.unpack('<3q7d',p);assert struct.pack('<2d',l,u)==struct.pack('<2d',lo[rid],hi[rid])and v==max(0.,l-endpoint,endpoint-u)>1e-12;minimum=min(minimum,v);maximum=max(maximum,v);count+=1
report=dict(schema='ROOT64_SAVED87_POSTAPPEND_FULL_ENDPOINT_DOMAIN_AND_ORIGINAL_REPLAY_REVIEW_V1',fixture_sha256=hashlib.sha256(buf).hexdigest(),all6_scaled_inputs_byteexact_actual87=True,original_header_diff_exactly_one_readonly_postappend_macro=True,all_actual_final_x_y_111events_12288_boundary_fields_byteexact=True,all12288_stored_original_row_bounds_bitexact=True,full_endpoints_outside_original1e12_domain=count,inside_original_domain=0,minimum_endpoint_violation=minimum,maximum_endpoint_violation=maximum,scope='Independent original-matrix/replay/recorded scalar domain check. Current64 correctly refuses these full directions; no basis to bypass/relax original1e-12 or increase12288. Intermediate full direction vectors are not all serialized; this does not independently reconstruct each original native full row product. No new65 Model/native/source gate or physical stop acceptance.')
bounded_write(O/'FAILURE87_FULL_ENDPOINT_POSTHOOK_REVIEW.json',json.dumps(report,indent=2)+'\n');print(json.dumps(report))
