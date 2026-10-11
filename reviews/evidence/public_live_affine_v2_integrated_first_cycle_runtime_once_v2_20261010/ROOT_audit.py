"""Independent actual file-algebra audit. No production predictor/kernel imports."""
import hashlib,json,struct,csv
from pathlib import Path
import numpy as np

BASE=Path('/private/tmp/public_live_affine_v2_integrated_first_cycle_runtime_once_v2_20261010/actual-dell-runtime/attempt/artifacts')
PROFILE=Path('/private/tmp/public_live_affine_v2_integrated_first_cycle_canonical_protocol_repair_v2_20261010/proposed-files')
OUT=Path(__file__).resolve().parent
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
SOURCE_SHA=sha(Path(__file__))
schema_sources=[Path('/Users/uot/Documents/ChatGPT/ros/tools/phase5_first_cycle_v1')/n for n in ['lossless_evidence.cpp','core/integrated_horizon_qp.cpp','core/integrated_horizon_qp.hpp','standalone_first_cycle.cpp','include/predictive_motion_control/reactive_qp.hpp']]
schema_hashes={str(p):sha(p) for p in schema_sources}
profile_hashes={n:sha(PROFILE/n) for n in ['runner_profile.json','inputs/public_constants.json','inputs/inspection_curve.json']}
manifest_bytes=(BASE/'MANIFEST.yaml').read_bytes()
# Strict parser for this known emitted flat manifest and file-receipt list.
# Reject every other layout rather than accept a general YAML interpretation.
manifest={};receipts=[];current=None
def scalar(s):
 if s in ('true','false'):return s=='true'
 if s.isdecimal():return int(s)
 if s.startswith('"'):return json.loads(s)
 assert ':' not in s and '\n' not in s
 return s
for line in manifest_bytes.decode().splitlines():
 if line=='files:':manifest['files']=receipts;continue
 if line.startswith('  - file: '):
  current={'file':scalar(line[len('  - file: '):])};receipts.append(current);continue
 if line.startswith('    '):
  key,value=line[4:].split(': ',1);assert current is not None and key not in current;current[key]=scalar(value)
 else:
  assert not line.startswith(' ');key,value=line.split(': ',1);assert key not in manifest;manifest[key]=scalar(value)
assert manifest['schema']=='FIRST_CYCLE_EVIDENCE_MANIFEST_V1'
ids={}
for r in manifest['files']:
 p=BASE/r['file']; assert r['created'] and r['complete'] and r['hash_valid'] and not r['error']
 assert p.stat().st_size==r['bytes'] and sha(p)==r['sha256'];ids[r['file']]=r['sha256']
assert len(ids)==7 and sum(r['bytes'] for r in manifest['files'])==manifest['output_bytes']
class Reader:
 def __init__(self,name,role):
  self.data=(BASE/name).read_bytes();self.pos=0
  assert self.text()=='P5_FIRST_CYCLE_LOSSLESS_V1' and self.text()==role
 def u(self):
  n=struct.unpack_from('<Q',self.data,self.pos)[0];self.pos+=8;return n
 def signed(self):
  n=self.u();return n if n<2**63 else n-2**64
 def d(self):
  x=struct.unpack_from('<d',self.data,self.pos)[0];self.pos+=8;return x
 def text(self):
  n=self.u();b=self.data[self.pos:self.pos+n];assert len(b)==n;self.pos+=n;return b.decode()
 def nums(self,n):
  a=np.frombuffer(self.data,dtype='<f8',count=n,offset=self.pos).copy();self.pos+=8*n;return a
 def vec(self):return self.nums(self.u())
 def mat(self):
  r,c=self.u(),self.u();return self.nums(r*c).reshape(r,c)
 def state(self):return np.r_[self.vec(),self.vec(),self.vec(),self.vec(),self.d(),self.d()]
 def fixedstate(self):return self.nums(30)
 def identity(self):return {'path':self.text(),'sha256':self.text(),'bytes':self.u()}
 def metadata(self):
  m={'version':self.text(),'nq':self.u(),'nv':self.u()}
  for k in ['joint_names','frame_names']:m[k]=[self.text() for _ in range(self.u())]
  for k in ['idx_q','idx_v','joint_nq','joint_nv']:m[k]=[self.signed() for _ in range(self.u())]
  for k in ['masses','armature','gravity','R','B','damping']:m[k]=self.vec().tolist()
  return m
 def done(self):assert self.pos==len(self.data),(self.pos,len(self.data))

r=Reader('original_nominal.bin','ORIGINAL_GENUINE_NOMINAL_BEFORE_ADAPTER')
raw={k:r.text() for k in ['transport','structural','invocation_sha','units','certificate']}
raw['identities']=[r.identity() for _ in range(3)]
raw['files']=[r.identity() for _ in range(r.u())];raw['libraries']=[r.identity() for _ in range(r.u())];raw['metadata']=r.metadata()
x0=r.fixedstate();previous_alpha=r.nums(7);previous_b=r.d();raw['attempts']=[r.u() for _ in range(6)]
mesh=[r.u() for _ in range(r.u())];controls=[]
for _ in range(r.u()):
 cycles=r.u();a=r.vec();b=r.d();controls.append((cycles,np.r_[a,b]))
assert r.u()==1
raw['value_success']=r.u();raw['has_final']=r.u();raw['value_error']=r.text();rawfinal=r.state()
raw['extension_success']=r.u();raw['first_uncertified']=r.signed();raw['error']=r.text()
points=[]
for _ in range(r.u()):
 p={'cell':r.u(),'cycle':r.u(),'half':r.u(),'time':r.d(),'s':r.d(),'r':r.d()}
 for k in ['q','v','C','w','force']:p[k]=r.vec()
 p['branches']=[r.signed() for _ in range(r.u())];p['iterations']=r.u();p['kkt']=r.d();p['ctrlclips']=r.u();p['forceclips']=r.u();points.append(p)
cycles=[r.state() for _ in range(r.u())];cells=[r.state() for _ in range(r.u())]
def readmap():
 m={k:r.u() for k in ['cell','cycle','half']}
 for k in ['origin','state','cell_origin']:m[k]=r.state()
 m['u']=r.vec()
 for k in ['A','B','cell_A','cell_B']:m[k]=r.mat()
 m['d']=r.vec();m['cell_d']=r.vec();return m
maps={k:[readmap() for _ in range(r.u())] for k in ['half','cycle','cell']};r.done()
assert not raw['transport'] and not raw['structural'] and raw['value_success'] and raw['has_final'] and raw['extension_success']
assert not raw['value_error'] and not raw['error'] and raw['first_uncertified']==-1
assert mesh==[1,1,2,2,3,3,4,4,5,5,6,6,8,10,12,16,20,24,28,40]
assert [len(points),len(cycles),len(cells),len(maps['half']),len(maps['cycle']),len(maps['cell'])]==[400,200,20,400,200,20]
r=Reader('inline_qp.bin','INLINE_QP_COMPLETE_OR_RETAINED_PREFIX')
trace={'stage':r.text(),'error':r.text()}
for k in ['complete','refused','factor_rows','rows','task_nodes','slots','age_bound']:trace[k]=r.u()
trace['observation_source']=r.text();trace['timingmode']=r.u()
for k in ['observer_age','upstream','connection']:trace[k]=r.d()
trace['geometry']=r.u();H,g,A,lower,upper=r.mat(),r.vec(),r.mat(),r.vec(),r.vec();state_age=r.d()
F,f,seed=r.mat(),r.vec(),r.vec();constant=r.d();labels=[(r.text(),r.text()) for _ in range(r.u())]
terms=[(r.text(),r.u(),r.u()) for _ in range(r.u())];task=[]
for _ in range(r.u()):task.append({'id':r.text(),'residual':r.vec(),'Js':r.vec(),'Jq':r.mat()})
fr,fc,fn=r.u(),r.u(),r.u();sparse=np.zeros((fr,fc))
for _ in range(fn):i,j,v=r.u(),r.u(),r.d();sparse[i,j]=v
r.done();assert trace['complete'] and not trace['refused'] and not trace['error']
assert H.shape==(160,160) and F.shape==(741,160) and A.shape==(13156,160) and len(labels)==13156 and len(task)==21
assert len(set(x[0] for x in labels))==13156 and not trace['geometry']
r=Reader('candidate.bin','SOLVER_RESULT_AND_DATA_ONLY_PREVIEW')
candidate={'reason':r.text()}
for k in ['execution','solve_attempts','wrapper_entries','status','raw_status','api_error','iterations']:candidate[k]=r.u()
candidate['max_violation_row']=r.signed();candidate['velocity']=r.vec().tolist()
for k in ['violation','primal_residual','dual_residual','setup_seconds','solve_seconds','minrowscale','maxrowscale','minvarscale','maxvarscale','eps_abs','eps_rel','rho0','rho_estimate','update_seconds']:candidate[k]=r.d()
for k in ['workspace_reused','matrix_updated','dual_reused','dual_mapped_rows']:candidate[k]=r.u()
candidate['reset_reason']=r.text()
for k in ['Hnnz','Annz','rho_updates','polish_status']:candidate[k]=r.u()
candidate['row_violations_count']=len(r.vec());candidate['timingmode']=r.u()
for k in ['observer_age','upstream','connection_solver','wall_age']:candidate[k]=r.d()
candidate['within_age']=r.u();candidate['complete_online_timing']=r.u()
# This actual failure has no preview/tail/request. Do not synthesize absent fields.
candidate['preview_present']=r.u();candidate['tail_present']=r.u();candidate['request_present']=r.u()
assert not candidate['preview_present'] and not candidate['tail_present'] and not candidate['request_present'];r.done()
def observation(name):
 r=Reader(name,'ACTUAL_NATIVE_BOOTSTRAP_SNAPSHOT');o={k:r.text() for k in ['epoch','source','stage','error']}
 for k in ['complete','joints_read','contacts']:o[k]=r.u()
 o['time']=r.d();o['state']=r.fixedstate();o['before_written']=r.u();o['before']=r.vec();o['after_written']=r.u();o['after']=r.vec();r.done();return o
before,after=observation('observation_before.bin'),observation('observation_after.bin')
assert before['complete'] and after['complete'] and before['contacts']==after['contacts']==0 and before['time']==after['time']==0
assert np.array_equal(before['before'],before['after']) and np.array_equal(before['before'],after['before']) and np.array_equal(before['state'],after['state']) and np.array_equal(x0,before['state'])
r=Reader('model_open.bin','ORIGINAL_MODEL_OPEN_RESULT');model_open={k:r.u() for k in ['has_model','constructor_attempted','metadata_attempted']};model_open['error']=r.text();model_open['metadata_present']=r.u();model_open['metadata']=r.metadata();r.done()
assert model_open['has_model']==model_open['constructor_attempted']==model_open['metadata_attempted']==model_open['metadata_present']==1 and not model_open['error'] and model_open['metadata']==raw['metadata']
r=Reader('bootstrap.bin','ACTUAL_DIRECT_BOOTSTRAP_API_ENTRIES');bootstrap={k:r.u() for k in ['load_xml','make_data','reset_keyframe','forward','copy_data','state_size','get_state','joint_name_queries','key_name_queries','initialized']};bootstrap['error']=r.text();r.done()
assert not bootstrap['error'] and bootstrap['initialized']==1
profile=json.loads((PROFILE/'runner_profile.json').read_text()); consts=json.loads((PROFILE/'inputs/public_constants.json').read_text())
assert sha(PROFILE/'inputs/public_constants.json')==profile['constants']['sha256']
assert any(i['sha256']==profile['constants']['sha256'] for i in raw['files'])
assert any(i['sha256']==profile['task_reference']['sha256'] for i in raw['files']) or sha(PROFILE/'inputs/inspection_curve.json')==profile['task_reference']['sha256']
checks={}
def check(name,a,b,abs_gate=1e-11,rel_gate=1e-10):
 aa,bb=np.asarray(a),np.asarray(b);assert aa.shape==bb.shape,(name,aa.shape,bb.shape)
 assert np.isfinite(aa).all() and np.isfinite(bb).all(),name
 error=np.abs(aa-bb);threshold=abs_gate+rel_gate*np.maximum(np.abs(aa),np.abs(bb))
 assert np.all(error<=threshold),(name,float(error.max()),float(np.max(error/threshold)))
 ratios=np.divide(error,threshold,out=np.zeros_like(error,dtype=float),where=threshold>0)
 checks[name]={'max_abs':float(np.max(error,initial=0)),'max_gate_ratio':float(np.max(ratios,initial=0))}
# Independent lifted elimination, not production recurrence/helper import.
L=np.eye(630);E=np.zeros((630,160));d=np.zeros(630);G=np.zeros((630,30));G[:30]=np.eye(30)
for k,m in enumerate(maps['cell']):
 rr=slice((k+1)*30,(k+2)*30);L[rr,k*30:(k+1)*30]=-m['cell_A'];E[rr,k*8:(k+1)*8]=m['cell_B'];d[rr]=m['cell_d']
solution=np.linalg.solve(L,np.c_[E,d,G]);M=solution[:,:160].reshape(21,30,160);o=solution[:,160].reshape(21,30);P=solution[:,161:].reshape(21,30,30)
check('lifted_equations',L@solution,np.c_[E,d,G]);c=o+np.einsum('kij,j->ki',P,x0)
U=np.concatenate([u for _,u in controls]);check('seed_original_controls',seed,U,0,0)
check('nominal_boundaries',np.einsum('kij,j->ki',M,U)+c,np.array([x0]+cells))
Sm=[];Sc=[];defect_errors=[];compose_errors=[];value_errors=[]
for group in ['half','cycle','cell']:
 for m in maps[group]:
  defect_errors.extend([np.max(np.abs(m['state']-m['A']@m['origin']-m['B']@m['u']-m['d'])),np.max(np.abs(m['state']-m['cell_A']@m['cell_origin']-m['cell_B']@m['u']-m['cell_d']))])
for i,m in enumerate(maps['half']):
 k=m['cell'];t=(m['cycle']-1)*.004+m['half']*.002
 assert (m['cell'],m['cycle'],m['half'])==(points[i]['cell'],points[i]['cycle'],points[i]['half']) and points[i]['time']==.002*(i+1)
 nominal=np.r_[points[i]['q'],points[i]['v'],points[i]['C'],points[i]['w'],points[i]['s'],points[i]['r']];check(f'half_value_{i}',m['state'],nominal,0,0)
 S=m['cell_A']@M[k];S[:,k*8:(k+1)*8]+=m['cell_B'];sc=m['cell_A']@c[k]+m['cell_d'];Sm.append(S);Sc.append(sc)
 value_errors.append(np.max(np.abs(S@U+sc-m['state'])))
 prior=None if m['cycle']==1 else maps['cycle'][sum(mesh[:k])+m['cycle']-2]
 pa=np.eye(30) if prior is None else prior['cell_A'];pb=np.zeros((30,8)) if prior is None else prior['cell_B']
 compose_errors.extend([np.max(np.abs(m['cell_A']-m['A']@pa)),np.max(np.abs(m['cell_B']-(m['A']@pb+m['B'])))])
checks['raw_defects']={'max_abs':float(max(defect_errors))};checks['raw_cumulative_composition']={'max_abs':float(max(compose_errors))};checks['sample_nominal_reproduction']={'max_abs':float(max(value_errors))}
assert max(defect_errors)<1e-10 and max(compose_errors)<1e-10 and max(value_errors)<1e-10
# Rectangular factor independently assembled from saved task local values.
FF=[];ff=[];tt=[]
def factor(m,v,weight,name):
 m=np.atleast_2d(m);v=np.atleast_1d(v);tt.append((name,sum(len(x) for x in ff),len(v)));FF.append(np.sqrt(2*weight)*m);ff.append(np.sqrt(2*weight)*v)
for k,t in enumerate(task):
 nominal=x0 if k==0 else cells[k-1];T=t['Jq']@M[k,:7]+np.outer(t['Js'],M[k,28]);v=t['residual']+t['Jq']@(c[k,:7]-nominal[:7])+t['Js']*(c[k,28]-nominal[28]);T[3:]*=.3;v[3:]*=.3
 duration=.5*.004*((0 if k==0 else mesh[k-1])+(0 if k==20 else mesh[k]))
 factor(T,v,100*duration,f'tracking/node/{k}');factor(M[k,7:14],c[k,7:14],.01*duration,f'physical_velocity/node/{k}');factor(M[k,:7],c[k,:7]-x0[:7],.001*duration,f'posture/node/{k}')
for k in range(20):
 u=np.zeros((8,160));u[:,k*8:k*8+8]=np.eye(8);j=u.copy();jc=np.zeros(8)
 if k==0:jc=-np.r_[previous_alpha,previous_b]
 else:j[:,(k-1)*8:k*8]-=np.eye(8)
 j/=.004;jc/=.004
 factor(u[:7],np.zeros(7),.001*.004*mesh[k],f'command_alpha/cell/{k}');factor(j[:7],jc[:7],.00001*.004,f'command_jerk/cell/{k}');factor(u[7],np.zeros(1),.001*.004*mesh[k],f'progress_b/cell/{k}');factor(j[7],jc[7:],.00001*.004,f'progress_jerk/cell/{k}')
factor(M[-1,28],np.array([c[-1,28]-1]),.1,'terminal_progress');FF=np.vstack(FF);ff=np.concatenate(ff)
assert terms==tt;check('F',F,FF);check('f',f,ff);check('sparse_factor',sparse,F,0,0)
HH=FF.T@FF;gg=FF.T@ff-.1*M[-1,28];cc=.5*float(ff@ff)-.1*c[-1,28]
check('H',H,HH);check('g',g,gg);check('constant',constant,cc)
direct=.5*float((FF@U+ff)@(FF@U+ff))-.1*(M[-1,28]@U+c[-1,28]);quadratic=.5*float(U@H@U)+g@U+constant
check('objective_at_seed',direct,quadratic);check('raw_H_symmetry',H,H.T,1e-12,0)
check('gradient_at_seed',FF.T@(FF@U+ff)-.1*M[-1,28],H@U+g)
eigenvalues=np.linalg.eigvalsh(.5*(H+H.T));assert eigenvalues.min()>0
# Exact semantic original-unit row recreation; command maps use closed sums.
rows=[];bounds=[];roster=[]
def row(m,v,lo,hi,label,units):rows.append(np.asarray(m).copy());bounds.append((lo-v,hi-v));roster.append((label,units))
cr=np.array(consts['control_range']).reshape(7,2);qr=np.array(consts['joint_range']).reshape(7,2)
cm=np.zeros((7,160));wm=cm.copy();co=x0[14:21].copy();wo=x0[21:28].copy();sm=np.zeros(160);rm=sm.copy();so=x0[28];ro=x0[29];sample_index=0
for k,m in enumerate(mesh):
 bm=np.zeros(160);bm[k*8+7]=1
 for j in range(8):
  u=np.zeros(160);u[k*8+j]=1;acc=1 if j<7 else .5;jerkcap=20 if j<7 else 5
  row(u,0,-acc,acc,f'input/{k}/{j}','rad/s^2' if j<7 else '1/s^2');jm=u/.004;prior=0
  if k==0:prior=previous_alpha[j] if j<7 else previous_b
  else:jm[(k-1)*8+j]-=250
  row(jm,-prior/.004,-jerkcap,jerkcap,f'feedback_jerk/{k}/{j}','rad/s^3' if j<7 else '1/s^3')
 os,orr=sm.copy(),rm.copy();oss,orr0=so,ro;duration=.004*m
 row(os+.5*duration*orr,oss+.5*duration*orr0,0,1,f'progress/bernstein/cell/{k}','dimensionless')
 for t in range(1,m+1):
  wm[:,k*8:k*8+7]+=.004*np.eye(7);cm+=.004*wm;co+=.004*wo
  prev=rm.copy();sm+=.004*prev+.5*.004**2*bm;so+=.004*ro;rm+=.004*bm;tick=sample_index//2+1
  for j in range(7):
   row(cm[j],co[j],cr[j,0]+.005,cr[j,1]-.005,f'command/C/tick/{tick}/{j}','rad');row(wm[j],wo[j],-.0625,.0625,f'command/w/tick/{tick}/{j}','rad/s')
  row(sm,so,0,1,f'progress/s/tick/{tick}','dimensionless');row(rm,ro,0,.2,f'progress/r/tick/{tick}','1/s')
  for half in [1,2]:
   dt=.004*(t-1)+.002*half;row(os+dt*orr+.5*dt**2*bm,oss+dt*orr0,0,1,f'progress/s/half/{sample_index}','dimensionless');row(orr+dt*bm,orr0,0,.2,f'progress/r/half/{sample_index}','1/s');sample_index+=1
for j in range(7):
 row(wm[j],wo[j],0,0,f'terminal/command_w/{j}','rad/s');u=np.zeros(160);u[19*8+j]=1;row(u,0,0,0,f'terminal/alpha/{j}','rad/s^2')
row(rm,ro,0,0,'terminal/progress_r','1/s');u=np.zeros(160);u[-1]=1;row(u,0,0,0,'terminal/b','1/s^2')
for i in range(400):
 m,sc,nom=Sm[i],Sc[i],maps['half'][i]['state']
 for j in range(7):
  suffix=f'{i}/{j}';row(m[j],sc[j],qr[j,0]+.005,qr[j,1]-.005,f'physical/q/half/{suffix}','rad');row(m[7+j],sc[7+j],-profile['physical_speed'][j],profile['physical_speed'][j],f'physical/v/half/{suffix}','rad/s');row(m[j],sc[j],nom[j]-.002,nom[j]+.002,f'trust/q/half/{suffix}','rad')
 row(m[28],sc[28],nom[28]-.02,nom[28]+.02,f'trust/s/half/{i}','dimensionless')
assert roster==labels and len(rows)==13156;AA=np.vstack(rows);bb=np.array(bounds);check('A',A,AA);check('lower',lower,bb[:,0]);check('upper',upper,bb[:,1])
seed_violation=np.maximum.reduce([np.zeros(13156),lower-A@seed,A@seed-upper]);idx=int(np.argmax(seed_violation))
candidate['status_name']='TIME_LIMIT' if candidate['status']==7 else 'OTHER';candidate['raw_status_name']='OSQP_TIME_LIMIT_REACHED' if candidate['raw_status']==8 else 'OTHER'
for k,v in list(candidate.items()):
 if isinstance(v,float) and not np.isfinite(v):candidate[k]='Infinity' if v>0 else '-Infinity'
report={'scope':'ACTUAL_FILE_ALGEBRA_ONLY_NO_MODEL_NATIVE_COMPILER_PLANT','input_hashes':ids,'manifest_sha256':hashlib.sha256(manifest_bytes).hexdigest(),'audit_source_sha256':SOURCE_SHA,'schema_readset_sha256':schema_hashes,'profile_readset_sha256':profile_hashes,'profile_sha256':sha(PROFILE/'runner_profile.json'),'source_binary':raw['identities'][0],'model_open':model_open,'bootstrap':bootstrap,'raw_flags':{k:raw[k] for k in ['transport','structural','units','certificate','attempts','value_success','has_final','extension_success','first_uncertified','error']},'raw_physical_diagnostics':{'max_saved_friction_kkt':max(p['kkt'] for p in points),'max_control_clips':max(p['ctrlclips'] for p in points),'max_force_clips':max(p['forceclips'] for p in points)},'trace':trace,'checks':checks,'candidate':candidate,'H_eigenvalues':{'minimum':float(eigenvalues.min()),'maximum':float(eigenvalues.max())},'arithmetic_gate':{'absolute':1e-11,'relative':1e-10,'scope':'file algebra not model accuracy'},'state_age_seconds':state_age,'seed_max_violation':{'value':float(seed_violation[idx]),'row':idx,'label':labels[idx]},'geometry_rows':0,'candidate_available':bool(candidate['velocity']),'before_after_byte_identical':ids['observation_before.bin']==ids['observation_after.bin'],'phase5':'NOT_ACCEPTED'}
assert sha(Path(__file__))==SOURCE_SHA and (BASE/'MANIFEST.yaml').read_bytes()==manifest_bytes
for n,s in ids.items():assert sha(BASE/n)==s
for n,s in profile_hashes.items():assert sha(PROFILE/n)==s
for n,s in schema_hashes.items():assert sha(Path(n))==s
(OUT/'report.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
columns=['cell','cycle','half','elapsed_seconds']+[f'{v}{j}' for v in ['q','v','C','w'] for j in range(7)]+['s','r']
with (OUT/'actual_produced_nominal_halves.csv').open('w',newline='') as file:
 writer=csv.writer(file);writer.writerow(columns)
 for p in points:writer.writerow([p['cell'],p['cycle'],p['half'],p['time']]+[float(x) for v in ['q','v','C','w'] for x in p[v]]+[p['s'],p['r']])
node_times=np.r_[0,np.cumsum(mesh)*.004]
export={'scope':'ACTUAL_PRODUCED_MODEL_NOMINAL_NO_PLANT_MOTION_NO_CANDIDATE','source_binary':raw['identities'][0],'raw_nominal_sha256':ids['original_nominal.bin'],'audit_source_sha256':SOURCE_SHA,'points':[{'cell':p['cell'],'cycle':p['cycle'],'half':p['half'],'elapsed_seconds':p['time'],**{v:p[v].tolist() for v in ['q','v','C','w']},'s':p['s'],'r':p['r']} for p in points],'task_nodes':[{'node':i,'elapsed_seconds':float(node_times[i]),'actual_produced_nominal_state':(x0 if i==0 else cells[i-1]).tolist(),'source_id':t['id'],'residual_unscaled_translation_m_rotation_rad':t['residual'].tolist()} for i,t in enumerate(task)]}
(OUT/'actual_produced_nominal_export.json').write_text(json.dumps(export,indent=2,allow_nan=False)+'\n')
print(json.dumps({'candidate':candidate,'trace':trace,'checks':{k:v for k,v in checks.items() if not k.startswith('half_value_')},'seed_max_violation':report['seed_max_violation']},indent=2))
