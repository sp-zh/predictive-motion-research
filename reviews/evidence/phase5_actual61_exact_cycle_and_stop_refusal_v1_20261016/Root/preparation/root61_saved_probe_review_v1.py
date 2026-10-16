from pathlib import Path
import sys,os,json,struct,hashlib,re
import numpy as np
sys.dont_write_bytecode=True;sys.path.insert(0,'/private/tmp')
from bounded_derived_bytes53_v1 import bounded_write
P=Path('/private/tmp/phase5_exact_cycle_endpoint61_probe_v2_20261016');Q=P/'readback';O=Path('/private/tmp/root61_cycle_review_v1_20261016');O.mkdir(exist_ok=True);os.environ['P5_DERIVED53_ROOT']=str(O)
sha=lambda b:hashlib.sha256(b).hexdigest();receipt=json.loads((Q/'READBACK.json').read_text())
for e in receipt:
 b=(Q/e['name']).read_bytes();assert len(b)==e['bytes']and sha(b)==e['sha256']
result=json.loads((Q/'RESULT.json').read_text());assert len(result['records'])==2 and all(x['exit']==0 for x in result['records'])and result['input_before_after_equal']
b=(P/'actual60_current43_trial0.initialized.fixture').read_bytes();assert sha(b)=='e8b14e198bafc29885419f2a42d54681d172b4ba1bd7f80aeca79f1044e43254';at=0
def vec():
 global at
 n=struct.unpack_from('<Q',b,at)[0];at+=8;assert n<=20000;v=np.frombuffer(b,dtype='<f8',count=n,offset=at);at+=8*n;return v
def mat():
 global at
 m,n=struct.unpack_from('<2Q',b,at);at+=16;assert m<=20000 and n<=144;v=np.frombuffer(b,dtype='<f8',count=m*n,offset=at).reshape(m,n);at+=8*m*n;return v
H,g,A,lo,hi,seed=mat(),vec(),mat(),vec(),vec(),vec();assert at==len(b)and A.shape==(7344,144)
xy=(Q/'prototype.finalxy.bin').read_bytes();offset=0;values=[]
for _ in range(2):
 n=struct.unpack_from('<Q',xy,offset)[0];offset+=8;values.append(np.frombuffer(xy,dtype='<f8',count=n,offset=offset));offset+=8*n
assert offset==len(xy);x,y=values;assert x.shape==(144,)and y.shape==(7344,)and np.isfinite(x).all()and np.isfinite(y).all();v=max(0.,float(np.max(lo-A@x)),float(np.max(A@x-hi)));s=float(np.max(np.abs(H@x+g+A.T@y)));assert v<=1e-12 and s<=1e-10
faces=(Q/'prototype.faces16.bin').read_bytes();assert len(faces)%16==0 and len(faces)<=144*16;ff=[struct.unpack_from('<2q',faces,i)for i in range(0,len(faces),16)];assert len({e[0]for e in ff})==len(ff)and all(0<=row<7344 and side in[-1,1]for row,side in ff);mask=np.zeros(7344,dtype=bool)
for row,side in ff:mask[row]=True
mu=np.array([side*y[row]for row,side in ff]);assert np.all(y[~mask]==0)and float(np.min(mu))>=0
events=(Q/'prototype.states.bin').read_bytes();assert len(events)==284*56;actual=Path('/private/tmp/phase5_bland_cycle43_analysis61_v1_20261016/ACTUAL_EVENTS56.bin').read_bytes();assert sha(actual)=='68da27f2fd1bec1f4ae9d5eaf017330add186b01826beba79e2f19fc1eb0fd8b'and events[:220*56]==actual[:220*56]
for i in range(284):
 it,active,worst,*vals=struct.unpack_from('<3q4d',events,i*56);assert it==i and 0<=active<=144 and -1<=worst<7344 and np.isfinite(vals).all()and vals[-1]<=1e-10
endpoint=(Q/'prototype.retained64.bin').read_bytes();assert len(endpoint)==3397*64
for at in range(0,len(endpoint),64):
 it,row,start,travel,value,l,u,violation=struct.unpack_from('<2q6d',endpoint,at);assert 0<=it<512 and 0<=row<7344 and np.isfinite([start,travel,value,l,u,violation]).all()and l<=u and violation==max(0.,l-value,value-u)<=1e-12
boundary=(Q/'prototype.boundary48.bin').read_bytes();assert len(boundary)==943*48
for at in range(0,len(boundary),48):
 it,row,side,*values=struct.unpack_from('<3q3d',boundary,at);assert 0<=it<512 and 0<=row<7344 and side in[-1,1]and np.isfinite(values).all()
lines=(Q/'prototype.stderr').read_text().splitlines();assert len(lines)==6;rows=[];iterations=[]
for i,line in enumerate(lines):
 d=dict(re.findall(r'(\w+)=([^ ]+)',line));assert d['same_full_primal_bits']==d['same_full_ordered_faces']==d['same_mask']=='1'and int(d['promotions'])==i+1;rows.append(int(d['row']));iterations.append(int(d['iteration']))
assert rows==[7250,7251,7252,7253,7254,7277]and iterations==[219,223,227,231,235,239]
out=dict(schema='ROOT61_V2_SAVED43_PROBE_ORIGINAL_FULLROW_NUMPY_AND_PREFIX_REVIEW_V1',payload_hashes_verified=len(receipt),two_commands_exit0=True,fixture_sha256=sha(b),same_source60_failure_fixture=True,full_rows=7344,events=284,finalxy_sha256=sha(xy),final_primal_numpy=v,full_stationarity_numpy=s,final_face_dual_min=float(np.min(mu)),nonface_dual_exact_zero=True,first220events_byte_equal_actual60=True,endpoints=3397,all_recorded_endpoint_numeric_domain_recomputed=True,boundaries=943,eligibility_rows=rows,eligibility_iterations=iterations,eligibility_log_same_full_bits_faces_mask_reported=True,scope='Pure saved numerical hint only. Eligibility stderr is source-reported and does not independently prove every snapshot comparison; direct witness/targeted tests required. No production/nativeOSQP/Model/B/C/physical stopping/task/phase result. Earlier failedNNLS candidate is not used here; failure to find a dual certificate is not a proof none exists.')
bounded_write(O/'PROBE_V2_FULLROW_AND_PREFIX_REVIEW.json',json.dumps(out,indent=2)+'\n');print(json.dumps(out))
