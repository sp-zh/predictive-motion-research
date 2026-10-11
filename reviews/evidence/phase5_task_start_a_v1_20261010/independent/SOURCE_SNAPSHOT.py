"""Independent task-start saved-file algebra; no native/model/SciPy solve."""
import hashlib,json,struct,csv,math,time
from pathlib import Path
import numpy as np
import xml.etree.ElementTree as ET
OUT=Path(__file__).resolve().parent;PACK=Path('/private/tmp/phase5_task_start_a_checkpoint_v1_20261010');ORACLE=Path('/private/tmp/phase5_task_start_oracle_checkpoint_v2_20261010')
SS=hashlib.sha256(Path(__file__).read_bytes()).hexdigest();pins={};start_time=time.monotonic()
def pin(path,expected=None):
 b=path.read_bytes();h=hashlib.sha256(b).hexdigest()
 if expected:assert h==expected,(str(path),h,expected)
 pins[str(path)]={'bytes':len(b),'sha256':h};return b
rb=pin(PACK/'READY.json','17d59d457b1ba039141883a211e5259717a012f6dd8a48c5b81f892e5dbef3b6');manifest=json.loads(rb)['files'];assert len(manifest)==223 and sum(x['bytes'] for x in manifest.values())==77710253
for name,v in manifest.items():b=pin(PACK/name,v['sha256']);assert len(b)==v['bytes']
ob=pin(ORACLE/'READY.json','337fb7eb6d282b9e6a4c33b4bbed9be8ee1b259de18e19ddd333abe39dc60fc7');om=json.loads(ob)['files'];assert len(om)==26
for name,v in om.items():b=pin(ORACLE/name,v['sha256']);assert len(b)==v['bytes']
sm=json.loads(pin(OUT/'SOURCE_READ_MANIFEST.json'))
for name,v in sm.items():pin(OUT/'source-read-snapshot'/name,v['sha256'])
BASE=PACK/'actual-dell/repair2/run-attempt1/artifacts'
profile=json.loads((PACK/'actual-dell/repair2/profile-version1/active_input.json').read_text())
class Reader:
 def __init__(self,b,role):
  self.b=b;self.i=0;assert self.text()=='P5_ACTIVE_SESSION_LOSSLESS_V1';assert self.text()==role
 def u(self):
  assert self.i+8<=len(self.b);v=struct.unpack_from('<Q',self.b,self.i)[0];self.i+=8;return v
 def signed(self):
  v=self.u();return v-(1<<64) if v>=(1<<63) else v
 def d(self):
  assert self.i+8<=len(self.b);v=struct.unpack_from('<d',self.b,self.i)[0];self.i+=8;return v
 def text(self):
  n=self.u();assert n<=len(self.b)-self.i;v=self.b[self.i:self.i+n].decode();self.i+=n;return v
 def nums(self,n):
  assert n<=10_000_000 and self.i+8*n<=len(self.b)
  v=np.frombuffer(self.b,dtype='<f8',count=n,offset=self.i).copy();self.i+=8*n;return v
 def vec(self):return self.nums(self.u())
 def mat(self):r,c=self.u(),self.u();return self.nums(r*c).reshape(r,c)
 def ids(self):return [self.u() for _ in range(self.u())]
 def end(self):assert self.i==len(self.b),(self.i,len(self.b))
def scalar(s):
 if s in ('true','false'):return s=='true'
 if s.isdecimal():return int(s)
 if s.startswith('"'):return json.loads(s)
 return s
receipts={};fields={};current=None
for line in pin(BASE/'MANIFEST.yaml').decode().splitlines():
 if line=='files:':continue
 if line.startswith('  - file: '):name=scalar(line[len('  - file: '):]);assert name not in receipts;current={};receipts[name]=current
 elif line.startswith('    '):key,value=line[4:].split(': ',1);assert key not in current;current[key]=scalar(value)
 else:key,value=line.split(': ',1);assert key not in fields;fields[key]=scalar(value)
for name,v in receipts.items():
 b=pin(BASE/name,v['sha256']);assert len(b)==v['bytes'] and v['created'] and v['complete'] and v['hash_valid'] and not v['error'];Reader(b,v['role'])
assert sum(v['bytes'] for v in receipts.values())==fields['output_bytes'] and fields['execution_permission'] is False
def inline(b):
 r=Reader(b,'INLINE_QP_COMPLETE_OR_RETAINED_PREFIX');stage,error=r.text(),r.text();info=[r.u() for _ in range(7)];r.text();r.u()
 for _ in range(3):r.d()
 r.u();H,g,A,l,u=r.mat(),r.vec(),r.mat(),r.vec(),r.vec();r.d();F,f,seed=r.mat(),r.vec(),r.vec();k=r.d();labels=[(r.text(),r.text()) for _ in range(r.u())]
 assert H.shape==(160,160) and A.shape==(13156,160) and F.shape==(741,160) and len(labels)==13156
 assert all(np.isfinite(x).all() for x in [H,g,A,l,u,F,f,seed]) and np.isfinite(k)
 return H,g,A,l,u,F,f,seed,k,labels,info
H,g,A,lower,upper,F,f,seed,constant,labels,info=inline(pin(BASE/'inline_qp.bin'))
r=Reader(pin(BASE/'qp_equality_reduction.bin'),'STRUCTURED_ORIGINAL_TERMINAL_EQUALITY_REDUCTION')
policy,stage=r.text(),r.text();valid=r.u();Z,p,E,rhs=r.mat(),r.vec(),r.mat(),r.vec();eq,rows=r.ids(),r.ids()
Hr,gr,Ar,lr,ur,D,Fr,seedr,usablex,usabley,R,Hs,gs,As,ls,us,Fs,seeds=(r.mat(),r.vec(),r.mat(),r.vec(),r.vec(),r.vec(),r.mat(),r.vec(),r.vec(),r.vec(),r.vec(),r.mat(),r.vec(),r.mat(),r.vec(),r.vec(),r.mat(),r.vec())
tag=r.text();wrapper,native,rawstatus,presentx,presenty=[r.u() for _ in range(5)];rawx,rawy=r.vec(),r.vec();slots=r.u();kr,eorigin,emap,efactor,esfactor=[r.d() for _ in range(5)];r.end()
assert valid==wrapper==native==presentx==presenty==1 and rawstatus==7 and rawx.shape==(144,) and rawy.shape==(len(rows),) and usablex.size==usabley.size==0
expected_eq=[next(i for i,x in enumerate(labels) if x[0]==('terminal/alpha/'+str(j) if j<7 else 'terminal/b')) for j in range(8)]+[next(i for i,x in enumerate(labels) if x[0]==('terminal/command_w/'+str(j) if j<7 else 'terminal/progress_r')) for j in range(8)]
assert eq==expected_eq and np.array_equal(E,A[eq]) and np.array_equal(rhs,lower[eq]) and np.array_equal(lower[eq],upper[eq])
Zref=np.zeros((160,144));Zref[:144]=np.eye(144);pref=np.zeros(160)
for j in range(8):
 assert E[j,152+j]==1 and np.count_nonzero(E[j])==1 and rhs[j]==0
 assert E[8+j,144+j]!=0 and np.all(E[8+j,np.arange(160)%8!=j]==0)
 pref[144+j]=rhs[8+j]/E[8+j,144+j];Zref[144+j]=-E[8+j,:144]/E[8+j,144+j]
assert np.array_equal(p,pref) and np.array_equal(Z,Zref)
checks={}
def check(name,a,b,abs_gate=1e-11,rel_gate=1e-10):
 a,b=np.asarray(a),np.asarray(b);assert a.shape==b.shape and np.isfinite(a).all() and np.isfinite(b).all(),name
 e=np.abs(a-b);assert np.all(e<=abs_gate+rel_gate*np.maximum(np.abs(a),np.abs(b))),(name,float(e.max()));checks[name]=float(e.max()) if e.size else 0.
check('Hr',Hr,Z.T@H@Z);check('gr',gr,Z.T@(g+H@p));check('Ar',Ar,A[rows]@Z);check('lr',lr,lower[rows]-A[rows]@p);check('ur',ur,upper[rows]-A[rows]@p);check('Fr',Fr,F@Z);check('D',D,1/np.sqrt(np.diag(Hr)));check('R',R,1/np.maximum(1,np.max(np.abs(Ar*D),axis=1)));check('Hs',Hs,D[:,None]*Hr*D);check('gs',gs,D*gr);check('As',As,R[:,None]*Ar*D);check('ls',ls,R*lr);check('us',us,R*ur);check('Fs',Fs,Fr*D);check('seeds',seeds,seedr/D);check('kr',kr,constant+g@p+.5*p@H@p)
def snapshot(name):
 r=Reader(pin(BASE/name),'ACTUAL_NATIVE_SESSION_SNAPSHOT');identities=[r.text(),r.text()];boundary=[r.u(),r.u()];complete=r.u();stage,error=r.text(),r.text();counts=[r.u() for _ in range(3)];t,age=r.d(),r.d();contact=r.u();state=r.nums(30);alpha=r.nums(7);b=r.d();available=r.u();v,a=r.nums(7),r.nums(7);physicalsteps=r.u();source=r.text();before,after=r.vec(),r.vec();r.end()
 assert complete==contact==available==1 and not error and boundary==[0,0] and physicalsteps==1000 and abs(t-2)<1e-10 and np.array_equal(before,after)
 return {'state':state,'alpha':alpha,'b':b,'physicalsteps':physicalsteps,'t':t,'age':age,'v':v,'a':a,'source':source,'integration':before}
obs=snapshot('observation_before.bin');obsafter=snapshot('observation_after.bin');assert np.array_equal(obs['state'],obsafter['state']) and np.array_equal(obs['integration'],obsafter['integration'])
x0=obs['state'];previous_alpha=obs['alpha'];previous_b=obs['b'];mesh=[1,1,2,2,3,3,4,4,5,5,6,6,8,10,12,16,20,24,28,40]
odp=ORACLE/'actual-dell/task-start-linear-oracle-v2-20261010-attempt1/oracle-artifacts-attempt1'
inp=np.load(odp/'ACTUAL_ORACLE_INPUTS.npz',allow_pickle=False);ref=np.load(odp/'FOR_NUMERICAL_REFERENCE_ONLY.npz',allow_pickle=False)
for key,array in {'H':Hs,'g':gs,'A':As,'l':ls,'u':us,'recorded_seed':seeds,'zero_seed':np.zeros(144),'Z':Z,'p':p,'D':D,'R':R,'constant':kr}.items():assert np.array_equal(inp[key],array),(key,'NPZ not exact actual binary value')
xref=ref['solver_x'];Uref=p+Z@(D*xref);check('reference_reduced_product',ref['reduced_z'],D*xref);check('reference_U_product',ref['reconstructed_original_U'],Uref)
guess=json.loads((ORACLE/'actual-dell/task-start-numeric-guess-v1-20261010/guess.json').read_text());assert np.array_equal(np.asarray(guess['solver_coordinates']),xref)
for key,start,end in [('q',0,7),('v',7,14),('C',14,21),('w',21,28)]:assert struct.pack('<7d',*guess[key])==x0[start:end].astype('<f8').tobytes()
assert guess['s']==x0[28] and guess['r']==x0[29] and struct.pack('<7d',*guess['previous_alpha'])==previous_alpha.astype('<f8').tobytes() and guess['previous_b']==previous_b
def diagnostics(U):
 ax=A@U;v=np.maximum(np.maximum(lower-ax,ax-upper),0);worst=int(v.argmax());C=x0[14:21].copy();w=x0[21:28].copy();s,pr=x0[28:];previous=previous_alpha.copy();pb=previous_b;h=.004;events=[];maxjerk=0.;clock=0
 for cell,m in enumerate(mesh):
  os,orr=s,pr;a=U[cell*8:cell*8+7];b=U[cell*8+7]
  for t in range(m):
   clock+=1;nw=w+h*a;nC=C+h*nw;implied=(nw-w)/h;jerk=(implied-previous)/h;maxjerk=max(maxjerk,float(np.max(np.abs(jerk))))
   for j in range(7):
    for label,value,cap in [('alpha',abs(a[j]),1),('implied_alpha',abs(implied[j]),1),('command_jerk',abs(jerk[j]),20),('command_speed',abs(nw[j]),.0625)]:
     if value>cap:events.append({'kind':label,'cell':cell,'tick':clock,'joint':j,'excess':float(value-cap)})
    rowid=next(i for i,z in enumerate(labels) if z[0]==f'command/C/tick/{clock}/{j}');offset=x0[14+j]+clock*h*x0[21+j]
    if nC[j]<lower[rowid]+offset or nC[j]>upper[rowid]+offset:events.append({'kind':'command_position','cell':cell,'tick':clock,'joint':j})
   if abs(b)>.5 or abs((b-pb)/h)>5:events.append({'kind':'b_or_progress_jerk','cell':cell,'tick':clock,'b':float(b),'previous_b':float(pb),'progress_jerk':float((b-pb)/h),'cap':5.})
   for half in [1,2]:
    dt=h*t+.002*half;ss=os+dt*orr+.5*dt*dt*b;rr=orr+dt*b
    if not(0<=ss<=1 and 0<=rr<=.2):events.append({'kind':'half_progress_domain','cell':cell,'tick':clock,'half':half,'s':float(ss),'r':float(rr)})
   ns=s+h*pr+.5*h*h*b;nr=pr+h*b
   if not(0<=ns<=1 and 0<=nr<=.2):events.append({'kind':'recursive_progress_domain','cell':cell,'tick':clock,'s':float(ns),'r':float(nr)})
   C,w,s,pr,previous,pb=nC,nw,ns,nr,implied,b
 return {'maximum_original_SI_violation':float(v[worst]),'worst_row':worst,'worst_label':labels[worst][0],'worst_units':labels[worst][1],'rows_above_1e_7':int(np.sum(v>1e-7)),'terminal_affine_residual':float(np.max(np.abs(E@U-rhs))),'literal_history_failures':events,'literal_max_command_jerk':maxjerk,'literal_final_w':w.tolist(),'literal_final_r':float(pr),'last_alpha':U[-8:-1].tolist(),'last_b':float(U[-1]),'exact_zero_tail':bool(np.all(w==0) and pr==0 and np.all(U[-8:]==0)),'cycles':clock,'literal_C':C.tolist()}
forensicdiag=diagnostics(p+Z@(D*rawx));refdiag=diagnostics(Uref)
quick={'scope':'EXTERNAL_SLSQP_REFERENCE_ONLY_NOT_NATIVE_SOLVED_OR_CANDIDATE','forensic':forensicdiag,'external_reference':refdiag,'guess_state_history_bitwise_match_actual_A2':True,'oracle_inputs_exact_actual_A2':True}
(OUT/'quick_oracle_postgate.json').write_text(json.dumps(quick,indent=2,allow_nan=False)+'\n')
print('quick_reference',json.dumps({k:v for k,v in refdiag.items() if k!='literal_history_failures'}));print('reference_history_failure_count',len(refdiag['literal_history_failures']));print('reference_first_history_failure',refdiag['literal_history_failures'][:1])

def identity(r):return {'path':r.text(),'sha256':r.text(),'bytes':r.u()}
def metadata(r):
 m={'pinocchio_version':r.text(),'nq':r.u(),'nv':r.u()}
 for k in ['joint_names','frame_names']:m[k]=[r.text() for _ in range(r.u())]
 for k in ['idx_q','idx_v','joint_nq','joint_nv']:m[k]=[r.signed() for _ in range(r.u())]
 for k in ['masses','armature','gravity','R','B','damping']:m[k]=r.vec().tolist()
 return m
def state(r):return np.r_[r.vec(),r.vec(),r.vec(),r.vec(),r.d(),r.d()]
readback=Path('/Users/uot/Documents/ChatGPT/ros/results/phase5-reference/task-start-a-v1-20261010/root-input-readback1')
for name,key in [('scene.xml','native_xml'),('inspection_fr3.xml','xml'),('expected_metadata.json','expected_metadata')]:pin(readback/name,profile[key]['sha256'])
tree=ET.fromstring((readback/'scene.xml').read_bytes());includes=tree.findall('include');assert len(includes)==1 and includes[0].attrib['file']=='inspection_fr3.xml'
constpath=Path('/private/tmp/public_live_affine_v2_integrated_first_cycle_canonical_protocol_repair_v2_20261010/proposed-files/inputs/public_constants.json');consts=json.loads(pin(constpath,profile['constants']['sha256']))
r=Reader(pin(BASE/'model_open.bin'),'SESSION_STARTUP_VERIFIED_METADATA');model_metadata=metadata(r);r.end();expected=json.loads((readback/'expected_metadata.json').read_text())
assert len(expected)==16
for key,value in model_metadata.items():assert expected[key]==value,key
r=Reader(pin(BASE/'original_nominal.bin'),'ORIGINAL_GENUINE_NOMINAL_BEFORE_ADAPTER');rawtags=[r.text() for _ in range(5)];identities=[identity(r) for _ in range(4)];session_id=r.text();dependencies=[identity(r) for _ in range(r.u())];libraries=[identity(r) for _ in range(r.u())];raw_metadata=metadata(r);initial=r.nums(30);alpha0=r.nums(7);b0=r.d();binding=r.u();rawmesh=[r.u() for _ in range(r.u())];controls=[]
for _ in range(r.u()):cyclescount=r.u();a=r.vec();b=r.d();controls.append((cyclescount,np.r_[a,b]))
assert r.u()==1;value_success,has_final=r.u(),r.u();value_error=r.text();rawfinal=state(r);extension_success=r.u();first_uncertified=r.signed();extension_error=r.text();points=[]
for _ in range(r.u()):
 z={'cell':r.u(),'cycle':r.u(),'half':r.u(),'time':r.d(),'s':r.d(),'r':r.d()}
 for key in ['q','v','C','w','force']:z[key]=r.vec()
 z['branches']=[r.signed() for _ in range(r.u())];z['iterations']=r.u();z['kkt']=r.d();z['ctrlclips']=r.u();z['forceclips']=r.u();points.append(z)
cycles=[state(r) for _ in range(r.u())];cells=[state(r) for _ in range(r.u())]
def readmap():
 m={key:r.u() for key in ['cell','cycle','half']}
 for key in ['origin','state','cell_origin']:m[key]=state(r)
 m['u']=r.vec()
 for key in ['A','B','cell_A','cell_B']:m[key]=r.mat()
 m['d']=r.vec();m['cell_d']=r.vec();return m
maps={key:[readmap() for _ in range(r.u())] for key in ['half','cycle','cell']};r.end()
assert not rawtags[0] and not rawtags[1] and binding==value_success==has_final==extension_success==1 and first_uncertified==-1 and not value_error and not extension_error
assert np.array_equal(initial,x0) and np.array_equal(alpha0,previous_alpha) and b0==previous_b and raw_metadata==model_metadata and rawmesh==mesh
assert [len(points),len(cycles),len(cells),len(maps['half']),len(maps['cycle']),len(maps['cell'])]==[400,200,20,400,200,20]
for got,want in zip(identities[1:],[profile['xml'],profile['constants'],profile['expected_metadata']]):assert got==want
assert libraries==profile['loaded_libraries'] and dependencies==profile['dependencies']
# Fully parse inline remainder and exact sparse factor certificate.
r=Reader(pin(BASE/'inline_qp.bin'),'INLINE_QP_COMPLETE_OR_RETAINED_PREFIX');inline_stage,inline_error=r.text(),r.text();tracevalues=[r.u() for _ in range(7)];observation_source=r.text();timingmode=r.u();ages=[r.d() for _ in range(3)];geometry=r.u();r.mat();r.vec();r.mat();r.vec();r.vec();state_age=r.d();r.mat();r.vec();r.vec();r.d();inline_labels=[(r.text(),r.text()) for _ in range(r.u())];terms=[(r.text(),r.u(),r.u()) for _ in range(r.u())];task=[]
for _ in range(r.u()):task.append({'id':r.text(),'residual':r.vec(),'Js':r.vec(),'Jq':r.mat()})
fr,fc,fn=r.u(),r.u(),r.u();sparse=np.zeros((fr,fc))
for _ in range(fn):i,j,v=r.u(),r.u(),r.d();sparse[i,j]=v
r.end();assert inline_labels==labels and tracevalues[:5]==[1,0,741,13156,21] and geometry==0 and not inline_error

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
 assert (m['cell'],m['cycle'],m['half'])==(points[i]['cell'],points[i]['cycle'],points[i]['half']) and abs(points[i]['time']-.002*(i+1))<1e-12
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
# Decode result, mapping and first failure separately from summary claims.
r=Reader(pin(BASE/'candidate.bin'),'SOLVER_RESULT_AND_DATA_ONLY_PREVIEW');stop=r.text();ci=[r.u() for _ in range(7)];backendrow=r.signed();usable=r.vec();cf=[r.d() for _ in range(14)];reuse=[r.u() for _ in range(4)];reset=r.text();counts=[r.u() for _ in range(4)];rowviol=r.vec();mode=r.u();timings=[r.d() for _ in range(4)];flags=[r.u() for _ in range(2)];preview,tail,request=r.u(),r.u(),r.u();r.end()
assert ci==[0,1,1,6,7,0,20000] and usable.size==rowviol.size==0 and preview==tail==request==0 and backendrow==-1
r=Reader(pin(BASE/'solver_row_screen.bin'),'ORIGINAL_SI_INPUT_BOX_IMPLICATION_SCREEN');sp=r.text();kept,omitted=r.ids(),r.ids();proofs=[r.text() for _ in range(r.u())];environment=[r.u() for _ in range(3)];mapping=r.text();mapped=r.signed();fullnote=r.text();scanned=r.u();worst=r.signed();defaultfull=r.d();r.end()
# `rows` was the independent full-QP row list; solver roster comes from reduction.
rr=Reader(pin(BASE/'qp_equality_reduction.bin'),'STRUCTURED_ORIGINAL_TERMINAL_EQUALITY_REDUCTION');rr.text();rr.text();rr.u();rr.mat();rr.vec();rr.mat();rr.vec();reduction_eq=rr.ids();reduction_rows=rr.ids()
assert kept==reduction_rows and set(kept)|set(omitted)|set(reduction_eq)==set(range(13156)) and len(set(kept))==len(kept) and scanned==0 and worst==mapped==-1 and defaultfull==0
assert all(i in kept for i,x in enumerate(labels) if x[0].startswith(('input/','trust/','keep/')))
def completion(base):
 r=Reader(pin(base/'entry_completion.bin'),'ACTIVE_SESSION_FINAL_SCOPE_AND_TIMING');stage,error=r.text(),r.text();same,sessionpass=r.u(),r.u();sfailure=r.text();nativepass=r.u();nfailure=r.text();wall=r.d();steps,commits=r.u(),r.u();r.end();return {'stage':stage,'error':error,'boundary_same':same,'session_termination':sessionpass,'session_failure':sfailure,'native_termination':nativepass,'native_failure':nfailure,'wall':wall,'actual_steps':steps,'task_commits':commits}
finished=completion(BASE);firstfailure=completion(PACK/'actual-dell/attempt1/run-attempt1/artifacts');assert finished['boundary_same']==finished['session_termination']==finished['native_termination']==1 and finished['actual_steps']==1000 and finished['task_commits']==0
assert 'body' in firstfailure['error'].lower() and firstfailure['actual_steps']==1000 and firstfailure['task_commits']==0
# Actual warmup endpoint agrees with the physically observed starting boundary.
r=Reader(pin(BASE/'actual_warmup.bin'),'ACTUAL_TASK_INITIALIZATION_AND_PHYSICAL_WARMUP_V2');wf=[r.u() for _ in range(4)];r.text();r.text();initialC=r.nums(7);pe,re=r.d(),r.d();r.text();wn=r.u();wp=[]
for _ in range(wn):
 z={'step':r.u(),'time':r.d(),'native':r.u(),'native_read':r.u(),'scratch_read':r.u()}
 for name in ['q','v','C','a','j']:z[name]=r.nums(7)
 z['ja'],z['geo'],z['observer'],z['contacts']=r.u(),r.u(),r.u(),r.u();z['warnings']=[r.u() for _ in range(8)];z['true'],z['cover'],z['queries'],z['tcp'],z['arm']=r.d(),r.d(),r.u(),r.d(),r.d();z['stage'],z['error']=r.text(),r.text();wp.append(z)
r.end();assert wn==1000 and wf==[1,1,1,91011]
last=wp[-1];assert np.array_equal(last['q'],x0[:7]) and np.array_equal(last['v'],x0[7:14]) and np.array_equal(last['C'],x0[14:21]) and np.array_equal(last['a'],obs['a'])
assert np.array_equal(obs['v'],x0[7:14]) and np.array_equal(x0[21:],np.zeros(9)) and last['contacts']==0 and min(last['true'],last['cover'])>=.005 and max(abs(last['v']))<=1e-4
r=Reader(pin(BASE/'bootstrap.bin'),'ACTUAL_DIRECT_SESSION_API_ENTRIES');bootstrap=[r.u() for _ in range(9)];r.end();assert bootstrap[-2:]==[1000,0]
def digest(arrays,c=None):
 h=hashlib.sha256()
 for a in arrays:
  for n in a.shape:h.update(struct.pack('<Q',n))
  h.update(np.asarray(a,dtype='<f8').tobytes(order='C'))
 if c is not None:h.update(struct.pack('<d',c))
 return h.hexdigest()
assert digest([H,g,A,lower,upper,F,f],constant)==guess['original_problem_sha256']
assert digest([Hs,gs,As,ls,us])==guess['transformed_problem_sha256']
assert hashlib.sha256((BASE/'qp_equality_reduction.bin').read_bytes()).hexdigest()==guess['source_input_sha256'] and hashlib.sha256((odp/'RESULT.json').read_bytes()).hexdigest()==guess['source_RESULT_sha256']
runtime_before=pin(PACK/'actual-dell/repair2/run-attempt1/BEFORE_INPUT_IDENTITIES.json');runtime_after=pin(PACK/'actual-dell/repair2/run-attempt1/AFTER_INPUT_IDENTITIES.json');assert runtime_before==runtime_after
native_lambda=np.zeros(13156);native_lambda[reduction_rows]=R*rawy;native_U=p+Z@(D*rawx)
native_stationarity=Hs@rawx+gs+As.T@rawy;check('native_stationarity_projection',native_stationarity,D*(Z.T@(H@native_U+g+A.T@native_lambda)))
ref_objective=.5*Uref@H@Uref+g@Uref+constant;ref_objective_scaled=.5*xref@Hs@xref+gs@xref+kr;check('reference_objective',ref_objective,ref_objective_scaled)
oracle_result=json.loads((odp/'RESULT.json').read_text());assert oracle_result['native_unsolved_seed_reused'] is False and np.array_equal(seeds,np.zeros(144))
runresult=json.loads((PACK/'actual-dell/repair2/run-attempt1/compile-1.result.json').read_text());assert runresult['exit']==1 and runresult['argv'][3]==identities[0]['sha256']
summary={'scope':'ACTUAL_TASK_START_A2_MAPS_QP_AND_EXTERNAL_REFERENCE_FILE_ALGEBRA_ONLY','source_sha256':SS,'input_pins':pins,'packet_files':len(manifest),'packet_bytes':sum(v['bytes'] for v in manifest.values()),'oracle_files':len(om),'actual_source_payloads':len(sm),'literal_XML_single_include_bound_postrun':True,'postrun_exact_files_not_new_startup_proof':True,'native_scene_and_model_XML_pins':[profile['native_xml'],profile['xml']],'complete_model_metadata_exact_expected':model_metadata,'loaded_SDK_roster_matches_recorded_profile':len(libraries),'runtime_guard_pins_before_after_exact':True,'actual_runtime_guard_count':len(json.loads(runtime_before)),'compile_link_guardarrays_empty_no_complete_buildclosure':True,'source_ELF_record':identities[0],'local_ELF_bytes_verified':False,'mesh':mesh,'raw_counts':{'half_maps':400,'cycle_maps':200,'cell_maps':20},'full_QP':{'F_rows':len(F),'A_rows':len(A),'controls':160,'solver_rows':len(reduction_rows),'eliminated':len(reduction_eq),'omitted':len(omitted),'factor_PSD_min_eigenvalue':float(eigenvalues.min()),'geometry_inline_rows':geometry},'checks':checks,'observed_start':{'actual_q_v_C_w_s_r':x0.tolist(),'physical_substeps':obs['physicalsteps'],'task_boundary':[0,0],'measured_last_acceleration':obs['a'].tolist(),'source':obs['source'],'endhold_position_error_stored':pe,'endhold_rotation_error_stored':re},'native_result':{'status':ci[3],'raw_status':ci[4],'iterations':ci[6],'primal':cf[1],'dual':cf[2],'rho_updates':counts[2],'rho_estimate':cf[12],'usable_count':len(usable),'preview':preview,'tail':tail,'forward_request':request,'collector_fullSI_rows_scanned':scanned,'collector_fullSI':'UNMEASURED','forensic_diagnostics':forensicdiag,'forensic_scaled_stationarity_max':float(np.max(np.abs(native_stationarity))),'stop':stop},'external_reference':{'inputs_exact_actual_arrays':True,'recorded_and_zero_seeds_exact_zero':True,'uses_native_unsolved_seed':False,'original_problem_digest':guess['original_problem_sha256'],'transformed_problem_digest':guess['transformed_problem_sha256'],'actual_state_history_bitwise_match':True,'SLSQP_source_status':{'success':oracle_result['success'],'nit':oracle_result['nit'],'scope':oracle_result['scope']},'diagnostics':refdiag,'literal_history_PASS':not bool(refdiag['literal_history_failures']),'not_candidate_or_native_SOLVED':True,'newA3_requires_fresh_full_matrix_and_actual_history_identity_before_guess_use':True},'completion':finished,'first_XML_body_failure_preserved':firstfailure,'Model_native_solver_calls':0,'phase5':'NOT_ACCEPTED','elapsed_seconds':time.monotonic()-start_time}
summary['all_original_receipts_and_binary_roles_verified']=len(receipts);summary['actual_bootstrap_counters_load_make_reset_forward_copy_getstate_observations_steps_commits']=bootstrap
for path,v in pins.items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==v['sha256']
assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==SS
(OUT/'results.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
print('full_algebra_max',max(v if isinstance(v,float) else v['max_abs'] for v in checks.values()));print('native_forensic_worst',forensicdiag['maximum_original_SI_violation'],forensicdiag['worst_label']);print('full_dimensions',summary['full_QP'])
