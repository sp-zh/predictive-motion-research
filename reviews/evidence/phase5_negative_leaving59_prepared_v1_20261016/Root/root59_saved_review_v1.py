from pathlib import Path
import ast,sys,os,json,struct,hashlib,importlib.util
import numpy as np
sys.dont_write_bytecode=True;sys.path.insert(0,'/private/tmp')
from bounded_derived_bytes53_v1 import bounded_write
ROOT=Path('/Users/uot/Documents/ChatGPT/ros');P=Path('/private/tmp/phase5_negative_leaving59_source_v1_20261016');O=Path('/private/tmp/root59_saved_review_v1_20261016');O.mkdir(exist_ok=True);os.environ['P5_DERIVED53_ROOT']=str(O)
def sha(b):return hashlib.sha256(b).hexdigest()
spec=importlib.util.spec_from_file_location('strict',ROOT/'tools/cold_storage_verification_v1/strict_codec_reader.py');strict=importlib.util.module_from_spec(spec);spec.loader.exec_module(strict)
# Reuse only the already reviewed generic bounded binary Reader class, never its audit main.
tree=ast.parse(Path('/private/tmp/root58_selected_audit_v1.py').read_text());exec(compile(ast.Module(body=[x for x in tree.body if isinstance(x,ast.ClassDef)and x.name in ['R','RV4']],type_ignores=[]),'<Reader-only>','exec'))
A=next(Path('/private/tmp/phase5_controlled_stop_global_interval_terminal58_v1_20261016').glob('actual-dell/*/run-attempt1/artifacts/cycle-74/trial-0'))
r=R(A/'qp_equality_reduction.bin','ORIGINAL_AND_NUMERICAL_PLANNING_TERMINAL_REDUCTION_V2');r.text();r.text();r.u();r.mat();r.vec();r.mat();r.vec();r.vec()
for _ in range(2):
 for __ in range(r.u()):r.u()
H,g,AA,lo,hi,D,F,seed,sy,ry,rs,Hs,gs,As,ls,us,Fs,solver_seed=[fn()for fn in [r.mat,r.vec,r.mat,r.vec,r.vec,r.vec,r.mat,r.vec,r.vec,r.vec,r.vec,r.mat,r.vec,r.mat,r.vec,r.vec,r.mat,r.vec]]
r.text();wrapper,attempts,status,px,py=r.take('<5Q');r.vec();r.vec();r.u();r.take('<5d');r.end();assert wrapper==attempts==0
from initializer_codec58_v4 import initializer_v4
z=initializer_v4(strict.read_artifact_bytes(A/'numeric_feasible_initializer.bin'),RV4,len(ls));assert z['complete']and z['global_scope_entered']and len(z['corrections'])==1
assert z['seed'].tobytes()==solver_seed.tobytes()
fixture=b''
for v in [Hs,gs,As,ls,us,z['seed']]:fixture+=(struct.pack('<2Q',*v.shape)if v.ndim==2 else struct.pack('<Q',len(v)))+v.astype('<f8').tobytes()
F59=Path('/private/tmp/phase5_iteration74_analysis59_v1_20261016');assert fixture==(F59/'actual58_current74_trial0.initialized.fixture').read_bytes()and sha(fixture)=='ba0de80aaba82efd4cbac257bf89017a10494b322303a47dbffec04f03fdd5be'
r=R(A/'current_numeric_hint.bin','BOUNDED_CURRENT_MATRIX_OPTIMIZER_HINT_NOT_CANDIDATE');assert r.u()==1 and r.u()==0 and r.text()=='current numeric iteration cap512';x,y=r.vec(),r.vec();assert r.u()==512
events=bytes(r.b[r.i:r.i+512*56]);r.i+=512*56
for _ in range(r.u()):r.take('<2Q')
r.text();r.end()
baseline=F59/'readback';assert events==(baseline/'baseline.states.bin').read_bytes();actualxy=b''.join(struct.pack('<Q',len(v))+v.astype('<f8').tobytes()for v in [x,y]);assert actualxy==(baseline/'baseline.finalxy.bin').read_bytes()
v2=Path('/private/tmp/phase5_iteration74_bland59_prototype_v2_20261016/readback');b=(v2/'new.finalxy.bin').read_bytes();at=0;vectors=[]
for _ in range(2):
 n=struct.unpack_from('<Q',b,at)[0];at+=8;vectors.append(np.frombuffer(b,dtype='<f8',count=n,offset=at));at+=8*n
assert at==len(b);xx,yy=vectors;assert xx.shape==(144,)and yy.shape==(7391,)
v=max(0.,float(np.max(ls-As@xx)),float(np.max(As@xx-us)));stationarity=float(np.max(np.abs(Hs@xx+gs+As.T@yy)));assert v<=1e-12 and stationarity<=1e-10
states=(v2/'new.states.bin').read_bytes();assert len(states)==171*56
for it in range(171):
 iteration,active,worst,vv,ll,ss,rr=struct.unpack_from('<3q4d',states,it*56);assert iteration==it and 0<=active<=144 and -1<=worst<7391 and np.isfinite([vv,ll,ss,rr]).all()and rr<=1e-10
assert sha(b)=='57c61abe945cf2ee5093bc89a6ea6d4967665fdd6586973299b3a536bc77e95f'
manifest=json.loads((P/'src-final-v1/SOURCE_IDENTITIES.json').read_text());assert len(manifest['files'])==82
for name,e in manifest['files'].items():
 bb=(P/'src-final-v1'/name).read_bytes();assert len(bb)==e['bytes']and sha(bb)==e['sha256']
old=ROOT/'tools/phase5_controlled_stop_session_v11';changed=[name for name in manifest['files']if not (old/name).exists()or(old/name).read_bytes()!=(P/'src-final-v1'/name).read_bytes()]
assert set(changed)=={'README.md','active_first_cycle.cpp','current_numeric_guess.hpp','negative_leaving59.hpp','negative_leaving_codec59.hpp','negative_leaving59_tests.cpp'}
pold=json.loads((old/'profile/active_input.json').read_text());pnew=json.loads((P/'profile-version1/active_input.json').read_text());assert {k for k in set(pold)|set(pnew)if pold.get(k)!=pnew.get(k)}=={'session_id','negative_multiplier_leaving'}
report=dict(schema='ROOT59_SAVED74_BINDING_BASELINE_REPRODUCTION_AND_PURE_V2_GATE_REVIEW_V1',actual74_QP_initializer_seed_all6_fields_bitexact=True,fixture_sha256=sha(fixture),original_nominal_and_scale_separate=True,actual74_native_wrapper_attempts=attempts,baseline_actual512events_and_partialxy_bitexact=True,pure_v2_events=171,pure_v2_full_current_rows=7391,finalxy_sha256=sha(b),primal_numpy=v,stationarity_numpy=stationarity,all_events_finite_rank_residual_original_gate=True,source_manifest_files_verified=82,source_plus_manifest_files=83,changed_files=changed,profile_changed_keys=['session_id','negative_multiplier_leaving'],stop_inventory=744208,unchanged_stop_reservation=745000,codec_bound=28672,scope='Pure saved input only. Stop working-face leaving selection changes optimizer paths and low bits on old successes; do not claim stop byte compatibility. Activefalse unchanged by source; formal runtime regressions reviewed separately. No Model/nativeOSQP/B/C/actual stop/task/phase acceptance. Original budget/threshold/math/physical gates unchanged; smallest-row leaving alone is not a full anti-cycling proof.')
bounded_write(O/'SAVED74_AND_SOURCE_INITIAL_REVIEW.json',json.dumps(report,indent=2)+'\n');print(json.dumps(report))
