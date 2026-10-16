from pathlib import Path
import sys,os,json,struct,hashlib,ast,importlib.util
import numpy as np
sys.dont_write_bytecode=True;sys.path.insert(0,'/private/tmp')
from bounded_derived_bytes53_v1 import bounded_write
ROOT=Path('/Users/uot/Documents/ChatGPT/ros');BASE=Path('/private/tmp/phase5_negative_leaving59_source_v1_20261016');P=BASE/'production_math_pure_v1/readback';OLD=Path('/private/tmp/phase5_global_interval_initializer58_source_v1_20261016/production_math_pure_v1');O=Path('/private/tmp/root59_saved_review_v1_20261016');os.environ['P5_DERIVED53_ROOT']=str(O)
spec=importlib.util.spec_from_file_location('strict',ROOT/'tools/cold_storage_verification_v1/strict_codec_reader.py');strict=importlib.util.module_from_spec(spec);spec.loader.exec_module(strict)
tree=ast.parse(Path('/private/tmp/root58_selected_audit_v1.py').read_text());exec(compile(ast.Module(body=[x for x in tree.body if isinstance(x,ast.ClassDef)and x.name in ['R','RV4']],type_ignores=[]),'<Reader-only>','exec'))
def sha(b):return hashlib.sha256(b).hexdigest()
receipt=json.loads((P/'PRODUCER_RECEIPT.json').read_text())
for e in receipt:
 b=(P/e['path']).read_bytes();assert len(b)==e['bytes']and sha(b)==e['sha256']
j=json.loads((P/'RESULT.json').read_text());assert len(j['records'])==17 and all(x['exit']==0 for x in j['records'])and j['input_before_after_equal']
def fixture(path):
 r=object.__new__(R);r.b=path.read_bytes();r.i=0;v=[fn()for fn in [r.mat,r.vec,r.mat,r.vec,r.vec,r.vec]];r.end();return v,r.b
def xy(path):
 r=object.__new__(R);r.b=path.read_bytes();r.i=0;x,y=r.vec(),r.vec();r.end();return x,y
def actualfixture(cycle):
 p=next(Path('/private/tmp/phase5_controlled_stop_global_interval_terminal58_v1_20261016').glob(f'actual-dell/*/run-attempt1/artifacts/cycle-{cycle}/trial-0'))
 r=R(p/'qp_equality_reduction.bin','ORIGINAL_AND_NUMERICAL_PLANNING_TERMINAL_REDUCTION_V2');r.text();r.text();r.u();r.mat();r.vec();r.mat();r.vec();r.vec()
 for _ in range(2):
  for __ in range(r.u()):r.u()
 for fn in [r.mat,r.vec,r.mat,r.vec,r.vec,r.vec,r.mat,r.vec,r.vec,r.vec,r.vec]:fn()
 H,g,A,lo,hi=[fn()for fn in [r.mat,r.vec,r.mat,r.vec,r.vec]]
 from initializer_codec58_v4 import initializer_v4
 z=initializer_v4(strict.read_artifact_bytes(p/'numeric_feasible_initializer.bin'),RV4,len(lo));assert z['complete']
 b=b''
 for v in [H,g,A,lo,hi,z['seed']]:b+=(struct.pack('<2Q',*v.shape)if v.ndim==2 else struct.pack('<Q',len(v)))+v.astype('<f8').tobytes()
 return b
cases=['actual56_48_1','old52_40_0','old53_40_1','old54_43_0','old55_40_2','actual58_54_0','actual58_74_0'];out=[]
for case in cases:
 if case=='actual58_54_0':f=BASE/'production_math_pure_v1/actual58_54_0.initialized.fixture'
 elif case=='actual58_74_0':f=Path('/private/tmp/phase5_iteration74_analysis59_v1_20261016/actual58_current74_trial0.initialized.fixture')
 else:f=OLD/(case+'.fixture')
 (H,g,A,lo,hi,seed),raw=fixture(f);pin=next(v for k,v in j['input_pins'].items()if k.endswith('/'+f.name));assert pin['sha256']==sha(raw)and pin['bytes']==len(raw)
 if case.startswith('actual58_'):assert raw==actualfixture(int(case.split('_')[1]))
 prefix=P/('stop_'+case);x,y=xy(Path(str(prefix)+'.finalxy.bin'));assert x.shape==g.shape and y.shape==lo.shape and np.isfinite(x).all()and np.isfinite(y).all()
 v=max(0.,float(np.max(lo-A@x)),float(np.max(A@x-hi)));s=float(np.max(np.abs(H@x+g+A.T@y)));assert v<=1e-12 and s<=1e-10
 states=Path(str(prefix)+'.states.bin').read_bytes();assert len(states)%56==0 and len(states)<=512*56;events=[struct.unpack_from('<3q4d',states,i)for i in range(0,len(states),56)]
 for i,e in enumerate(events):assert e[0]==i and 0<=e[1]<=144 and -1<=e[2]<len(lo)and np.isfinite(e[3:]).all()and e[6]<=1e-10
 r=R(Path(str(prefix)+'.leaving/hint_negative_leaving_events.bin'),'STOP_ONLY_SMALLEST_CURRENT_ROW_NEGATIVE_MULTIPLIER_LEAVING_DIAGNOSTICS_V1');c,t,h,stop,policy,count=r.take('<6Q');assert (h,stop,policy)==(1,1,1)and count<=512
 chosen=[];last=-1
 for _ in range(count):
  it,row,side,pos,selected,minimum=r.take('<4q2d');assert last<it<len(events)and 0<=row<len(lo)and side in [-1,1]and 0<=pos<events[it][1]and np.isfinite([selected,minimum]).all()and minimum<=selected<-1e-12 and events[it][2]==-1 and minimum==events[it][4];last=it;chosen.append((it,row,side,pos,selected,minimum))
 r.text();r.end()
 boundary=Path(str(prefix)+'.boundary48.bin').read_bytes();assert len(boundary)%48==0 and len(boundary)<=12288*48
 for at in range(0,len(boundary),48):
  it,row,side,*values=struct.unpack_from('<3q3d',boundary,at);assert 0<=it<512 and 0<=row<len(lo)and side in [-1,1]and np.isfinite(values).all()
 endpoint=Path(str(prefix)+'.retained64.bin').read_bytes();assert len(endpoint)%64==0 and len(endpoint)<=16384*64
 for at in range(0,len(endpoint),64):
  it,row,*values=struct.unpack_from('<2q6d',endpoint,at);assert 0<=it<512 and 0<=row<len(lo)and np.isfinite(values).all()and values[3]<=values[4]and 0<=values[5]<=1e-12
 assert 'complete=1 error=""' in Path(str(prefix)+'.stdout').read_text()
 compare={}
 if case in cases[:5]:
  for ext in ['finalxy.bin','states.bin','boundary48.bin','retained64.bin','refinement120.bin']:compare[ext]=Path(str(prefix)+'.'+ext).read_bytes()==(OLD/'readback'/('new_stop_'+case+'.'+ext)).read_bytes()
 if case=='actual58_74_0':assert sha(Path(str(prefix)+'.finalxy.bin').read_bytes())=='57c61abe945cf2ee5093bc89a6ea6d4967665fdd6586973299b3a536bc77e95f'
 out.append(dict(case=case,fixture_sha256=sha(raw),events=len(events),full_rows=len(lo),final_primal_numpy=v,final_stationarity_numpy=s,chosen_records=count,chosen_globalmin_bound_to_old_event=True,boundary_count=len(boundary)//48,endpoint_count=len(endpoint)//64,old58_byte_comparison=compare,finalxy_sha256=sha(Path(str(prefix)+'.finalxy.bin').read_bytes())))
active=[]
for case in ['old52_40_0','old53_40_1','old54_43_0','ACTIVE_constrained','ACTIVE_interior','ACTIVE_zero']:
 b=(P/('active_'+case+'.core.bin')).read_bytes();assert b==(OLD/'readback'/('new_active_'+case+'.core.bin')).read_bytes();active.append(dict(case=case,bytes=len(b),sha256=sha(b),entire_core_byte_equal_old58=True))
report=dict(schema='ROOT59_FROZEN_PRODUCTION_SEVEN_STOP_SIX_ACTIVE_AND_CHOSEN_CODEC_REVIEW_V1',payload_hashes_verified=len(receipt),all17_production_driver_commands_exit0=True,before_after_inputs_equal_report=True,seven_stop=out,six_activefalse=active,scope='Saved numerical optimization only; independently checked full row primal/stationarity, event domains, boundary/endpoint prefixes and new chosen/global-min fields. Scalar chosen records do not reconstruct all eligible sets; no new nativeOSQP/Model/B/C/task/stop/phase acceptance. Old stop byte differences are explicit; activefalse entire old core identical.')
bounded_write(O/'FORMAL_PRODUCTION_REGRESSION_REVIEW.json',json.dumps(report,indent=2)+'\n');print(json.dumps(dict(payloads=len(receipt),stop=[(x['case'],x['events'],x['chosen_records'])for x in out],active_equal=len(active))))
