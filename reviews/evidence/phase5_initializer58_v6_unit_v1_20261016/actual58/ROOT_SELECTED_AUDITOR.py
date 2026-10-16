from pathlib import Path
import sys,os,json,hashlib,struct,importlib.util
sys.dont_write_bytecode=True
import numpy as np
sys.path.insert(0,'/private/tmp')
from bounded_derived_bytes53_v1 import bounded_write
P=Path('/private/tmp/phase5_controlled_stop_global_interval_terminal58_v1_20261016')
O=Path('/private/tmp/root58_actual_selected_review_v1_20261016');O.mkdir(exist_ok=True)
os.environ['P5_DERIVED53_ROOT']=str(O)
spec=importlib.util.spec_from_file_location('strict', '/Users/uot/Documents/ChatGPT/ros/tools/cold_storage_verification_v1/strict_codec_reader.py');strict=importlib.util.module_from_spec(spec);spec.loader.exec_module(strict)
def sha(b):return hashlib.sha256(b).hexdigest()
ready=json.loads((P/'READY.json').read_text());assert sha((P/'READY.json').read_bytes())=='80afd6ecffd138417a78ea1fab50ccc19663e7f8e2d88c04132c4dfbe52cb7ba'
receipts=[]
for e in ready['payload']:
 p=P/e['path'];b=strict.bounded_read(p,256*1024**2);assert len(b)==e['bytes'] and sha(b)==e['sha256']
 if p.suffix=='.bin':receipts.append(strict.verify_artifact(p))
assert len(ready['payload'])==865 and sum(x['bytes']for x in ready['payload'])==93137772
assert len(receipts)==221 and all(x['source_complete']for x in receipts)
B=next(P.glob('actual-dell/*/run-attempt1'));A=B/'artifacts'
before=(B/'BEFORE_INPUT_IDENTITIES.json').read_bytes();assert before==(B/'AFTER_INPUT_IDENTITIES.json').read_bytes() and len(json.loads(before))==1720
class R:
 def __init__(self,path,role):
  self.b=strict.read_artifact_bytes(path);self.i=0
  assert self.text()=='P5_ACTIVE_SESSION_LOSSLESS_V1' and self.text()==role
 def take(self,fmt):
  n=struct.calcsize(fmt);assert self.i+n<=len(self.b);v=struct.unpack_from(fmt,self.b,self.i);self.i+=n;return v
 def u(self):return self.take('<Q')[0]
 def d(self):return self.take('<d')[0]
 def text(self):
  n=self.u();assert n<=1024**2 and self.i+n<=len(self.b);s=self.b[self.i:self.i+n].decode();self.i+=n;return s
 def arr(self,n):
  assert n<=4000000 and self.i+8*n<=len(self.b);a=np.frombuffer(self.b,dtype='<f8',count=n,offset=self.i).copy();self.i+=8*n;return a
 def vec(self):return self.arr(self.u())
 def mat(self):
  m,n=self.take('<2Q');return self.arr(m*n).reshape(m,n)
 def end(self):assert self.i==len(self.b)
r=R(A/'entry_completion.bin','ACTIVE_SESSION_FINAL_SCOPE_AND_TIMING')
entry=dict(stage=r.text(),error=r.text(),boundary_unchanged=r.u(),session_termination=r.u(),session_error=r.text(),native_termination=r.u(),native_error=r.text(),wall_seconds=r.d(),physical_step_attempts=r.u(),commits=r.u());r.end()
assert entry['error']=='current numeric iteration cap512' and entry['commits']==74 and entry['physical_step_attempts']==1148 and entry['session_termination']==entry['native_termination']==1
whole=[]
for i in range(75):
 r=R(A/f'cycle-{i}/whole_current_cycle.bin','ALL_REJECTED_TRIALS_THROUGH_ONE_ACTUAL_CYCLE_WALL_SCOPE_V1')
 w=dict(zip(['cycle','trials_entered','physical_complete'],r.take('<3Q')));w.update(wall=r.d(),deadline_miss=r.u(),last_B_error=r.text(),fatal_error=r.text());w.update(zip(['trials_total','forecasts','steps','commits'],r.take('<4Q')));w['scope']=r.text();r.end()
 assert w['cycle']==i and w['deadline_miss']==int(w['wall']>.004)==1 and w['commits']==min(i+1,74) and w['steps']==2*w['commits']
 assert w['physical_complete']==int(i<74);whole.append(w)
assert whole[-1]['trials_total']==152 and whole[-1]['forecasts']==303
r=R(A/'actual_stop_dwell.bin','ACTUAL_PHYSICAL_V_A_ACCEPTED_HISTORY_STOP_DWELL_V2');passed,failed,dwell,required,maximum=r.take('<5Q');limits=r.take('<8d');assert limits==(1e-4,1e-3,1e-6,1e-4,1e-6,1e-4,1e-6,1e-6)
count=r.u();assert count==84 and (passed,failed,dwell,required,maximum)==(0,0,0,50,178)
rows=[];anchor=None;consecutive=0
for i in range(count):
 half,t=r.take('<Qd');v,a,C,w,alpha=[r.arr(7)for _ in range(5)];s,rate,b=r.take('<3d');guards,below,hold,recorded=r.take('<4Q');Cd,sd=r.take('<2d')
 norms=[float(np.max(np.abs(x)))for x in [v,a,w,alpha]]+[rate,abs(b)];assert np.isfinite(norms).all() and min(norms)>=0
 independently_below=int(all(x<=lim for x,lim in zip(norms,limits[:6])))
 assert half==1065+i and abs(t-(2.13+.002*i))<1e-12 and guards==1 and below==independently_below
 if below:
  if anchor is None:anchor=(C.copy(),s)
  assert Cd==float(np.max(np.abs(C-anchor[0]))) and sd==abs(s-anchor[1]);consecutive=consecutive+1 if Cd<=limits[6]and sd<=limits[7]else 0
 else:anchor=None;consecutive=0;assert Cd==sd==0
 assert recorded==consecutive and hold==int(anchor is not None) and not below
 rows.append(dict(global_half=half,time_s=t,v=norms[0],a=norms[1],w=norms[2],alpha=norms[3],s=s,r=rate,b=b,below=below,hold=hold,consecutive=recorded,C_drift=Cd,s_drift=sd))
scope=r.text();r.end()
def hint(path):
 r=R(path,'BOUNDED_CURRENT_MATRIX_OPTIMIZER_HINT_NOT_CANDIDATE');assert r.u()==1;complete,error=r.u(),r.text();x,y=r.vec(),r.vec();n=r.u();events=[]
 for _ in range(n):events.append(r.take('<3Q4d'))
 faces=[r.take('<2Q')for _ in range(r.u())];s=r.text();r.end();return dict(complete=complete,error=error,x=x,y=y,events=events,faces=faces)
h54=hint(A/'cycle-54/trial-0/current_numeric_hint.bin');h74=hint(A/'cycle-74/trial-0/current_numeric_hint.bin')
assert h54['complete']==1 and len(h54['events'])==173 and h54['error']==''
assert h74['complete']==0 and h74['error']=='current numeric iteration cap512' and len(h74['events'])==512
xy=b''.join(struct.pack('<Q',len(x))+x.astype('<f8').tobytes()for x in [h54['x'],h54['y']]);assert sha(xy)=='aad3b819cd4eb17dc8c4745b2aef83135d1814ff94729d69a0dada12ce384936'
# Independently extract original nominal QP fields from fixed V2 order; skip no fields silently.
r=R(A/'cycle-54/trial-0/qp_equality_reduction.bin','ORIGINAL_AND_NUMERICAL_PLANNING_TERMINAL_REDUCTION_V2');r.text();r.text();r.u();r.mat();r.vec();r.mat();r.vec();r.vec();r.arr(0)
for _ in range(2):
 for __ in range(r.u()):r.u()
H,g,AA,lo,hi,D,F,seed,sy,ry,rs,Hs,gs,As,ls,us,Fs,solver_seed=[fn()for fn in [r.mat,r.vec,r.mat,r.vec,r.vec,r.vec,r.mat,r.vec,r.vec,r.vec,r.vec,r.mat,r.vec,r.mat,r.vec,r.vec,r.mat,r.vec]]
r.text();r.take('<5Q');r.vec();r.vec();r.u();r.take('<5d');r.end()
fixture=b''
for v in [Hs,gs,As,ls,us,seed/D,D]:fixture+=(struct.pack('<2Q',*v.shape)if v.ndim==2 else struct.pack('<Q',len(v)))+v.astype('<f8').tobytes()
assert sha(fixture)=='601f0a92e224e024a12e56a8aaaef037fe1106377fb3e354886ac4f749c7c2e9'
# On successful current solve solver_seed is overwritten with the completed hint.
assert h54['x'].tobytes()==solver_seed.tobytes()
vx=max(0.,float(np.max(ls-As@h54['x'])),float(np.max(As@h54['x']-us)));stationarity=float(np.max(np.abs(Hs@h54['x']+gs+As.T@h54['y'])));assert vx<=1e-12 and stationarity<=1e-10
# Previously audited data-only V4 schema parser; no controller calls.
from initializer_codec58_v4 import initializer_v4
class RV4(R):
 def __init__(self,raw,role):
  self.b=raw;self.i=0;assert self.text()=='P5_ACTIVE_SESSION_LOSSLESS_V1' and self.text()==role
 def signed(self):return self.take('<q')[0]
z=initializer_v4(strict.read_artifact_bytes(A/'cycle-54/trial-0/numeric_feasible_initializer.bin'),RV4,As.shape[0]);assert z['complete']and z['global_scope_entered']and len(z['corrections'])==1 and z['corrections'][0]['row']==7358
assert [s['limiting_upper_row']for s in z['global_scans']]==[7075,7075]
nominal=seed/D
mask=np.array([j%8!=7 for j in range(144)]);assert z['seed'][mask].tobytes()==nominal[mask].tobytes()
delta=float(np.max(np.abs(D*(z['seed']-nominal))));sv=max(0.,float(np.max(ls-As@z['seed'])),float(np.max(As@z['seed']-us)));assert delta<=1e-6 and sv<=1e-12
result=dict(schema='ROOT58_SELECTED_CODEC_COUNTS_STOP_AND_SAVED_BLOCKAGE_CROSSING_V1',payload_count=865,payload_bytes=93137772,complete_binary_files=len(receipts),raw_binary_bytes=sum(x['raw_bytes']for x in receipts),all_codec_CRC_singleEOF_stored_and_raw_SHA_passed=True,before_after_1720_input_records_byte_equal=True,entry=entry,whole_boundaries=75,whole_deadline_misses=75,task_halves=148,task_duration_ms=296,last_whole=whole[-1],stop=dict(records=84,passed=passed,failed=failed,consecutive=dwell,required=required,all_original_thresholds_and_anchor_drifts_independently_recomputed=True,first=rows[0],last=rows[-1]),crossing54=dict(original_seven_fields_fixture_sha256=sha(fixture),one_correction_row=7358,limiting_rows=[7075,7075],nonbeta_bits_equal=True,seed_delta_physical_inf=delta,seed_violation_numpy=sv,hint_iterations=173,finalxy_sha256=sha(xy),final_violation_numpy=vx,final_stationarity_numpy=stationarity),failure74=dict(hint_complete=False,error=h74['error'],retained_events=len(h74['events'])),scope='Selected packet independent review; not a full original B/C/SI audit. Full stored-evidence restoration separately verified on Mac and Dell; not standalone environment restoration or research acceptance. Stop/fulltask/realtime remain unmet.')
for name,obj in [('RESULT.json',result),('STOP_ROWS.json',rows),('CODEC_RECEIPTS.json',receipts),('WHOLE_CYCLES.json',whole)]:bounded_write(O/name,json.dumps(obj,indent=2)+'\n')
print(json.dumps(result))
