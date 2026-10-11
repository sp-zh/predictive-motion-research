"""Independent dynamic three-cycle saved-file audit. No Model/native/compiler/solver/SSH.
Prepared from declared frozen V2 layouts. Only evaluate a supplied sealed READY.
Future400-point values remain predictions; actual6 points are separately labelled.
"""
from pathlib import Path
import hashlib,json,struct,csv,argparse
import numpy as np
PINS={}
OUT=Path(__file__).resolve().parent
def pin(p,h=None):
 b=p.read_bytes();s=hashlib.sha256(b).hexdigest()
 if h:assert s==h,(str(p),s,h)
 PINS[str(p)]={'bytes':len(b),'sha256':s};return b
class R:
 def __init__(self,b,role):self.b=b;self.i=0;assert self.text()=='P5_ACTIVE_SESSION_LOSSLESS_V1' and self.text()==role
 def u(self):assert self.i+8<=len(self.b);x=struct.unpack_from('<Q',self.b,self.i)[0];self.i+=8;return x
 def signed(self):x=self.u();return x-(1<<64) if x>=(1<<63) else x
 def d(self):assert self.i+8<=len(self.b);x=struct.unpack_from('<d',self.b,self.i)[0];self.i+=8;return x
 def text(self):n=self.u();assert n<=len(self.b)-self.i;s=self.b[self.i:self.i+n].decode();self.i+=n;return s
 def nums(self,n):assert n<=10_000_000 and self.i+n*8<=len(self.b);x=np.frombuffer(self.b,dtype='<f8',count=n,offset=self.i).copy();self.i+=n*8;return x
 def vec(self):return self.nums(self.u())
 def mat(self):n,m=self.u(),self.u();return self.nums(n*m).reshape(n,m)
 def end(self):assert self.i==len(self.b),(self.i,len(self.b))

def state(r):
 vs=[r.vec() for _ in range(4)];assert all(x.shape==(7,) for x in vs);return np.concatenate(vs+[[r.d(),r.d()]])

def identity(r):return dict(path=r.text(),sha256=r.text(),bytes=r.u())

def metadata(r):
 m=dict(pinocchio_version=r.text(),nq=r.u(),nv=r.u())
 for k in ['joint_names','frame_names']:m[k]=[r.text() for _ in range(r.u())]
 for k in ['idx_q','idx_v','joint_nq','joint_nv']:m[k]=[r.signed() for _ in range(r.u())]
 for k in ['masses','armature','gravity','R','B','damping']:m[k]=r.vec().tolist()
 return m

def values(r):
 points=[]
 for _ in range(r.u()):
  p=dict(cell=r.u(),cycle=r.u(),half=r.u(),time=r.d(),s=r.d(),r=r.d())
  for k in ['q','v','C','w','force']:p[k]=r.vec();assert p[k].shape==(7,) and np.isfinite(p[k]).all()
  p['branches']=[r.signed() for _ in range(r.u())];p.update(iterations=r.u(),kkt=r.d(),control_clips=r.u(),force_clips=r.u())
  assert len(p['branches'])==7 and np.isfinite(p['kkt']) and p['kkt']<=1e-10
  points.append(p)
 cycles=[state(r) for _ in range(r.u())];cells=[state(r) for _ in range(r.u())]
 return points,cycles,cells

def snapshot(b):
 r=R(b,'ACTUAL_NATIVE_SESSION_SNAPSHOT');ids=[r.text(),r.text()];boundary=[r.u(),r.u()];complete=r.u();stage,error=r.text(),r.text();[r.u() for _ in range(3)];time,age=r.d(),r.d();contact=r.u();x=r.nums(30);alpha=r.nums(7);b=r.d();available=r.u();v,a=r.nums(7),r.nums(7);steps=r.u();source=r.text();ib,ia=r.vec(),r.vec();r.end()
 assert complete==available==contact==1 and not error and np.array_equal(ib,ia)
 return dict(ids=ids,boundary=boundary,time=time,age=age,x=x,alpha=alpha,b=b,v=v,a=a,steps=steps,source=source,ib=ib,ia=ia)

def maxabs(x):return float(np.max(np.abs(x)))

def scalar(v):
 if v in ('true','false'):return v=='true'
 if v.isdecimal():return int(v)
 if v.startswith(chr(34)):return json.loads(v)
 return v

def reduction(data):
 rr=R(data,'STRUCTURED_ORIGINAL_TERMINAL_EQUALITY_REDUCTION');d={'policy':rr.text(),'stage':rr.text(),'valid':rr.u()}
 def ids():return [rr.signed() for _ in range(rr.u())]
 for name,fn in [('Z',rr.mat),('p',rr.vec),('E',rr.mat),('rhs',rr.vec),('eq',ids),('rows',ids),('Hr',rr.mat),('gr',rr.vec),('Ar',rr.mat),('lr',rr.vec),('ur',rr.vec),('D',rr.vec),('Fr',rr.mat),('seed',rr.vec),('x',rr.vec),('Y',rr.vec),('R',rr.vec),('Hs',rr.mat),('gs',rr.vec),('As',rr.mat),('ls',rr.vec),('us',rr.vec),('Fs',rr.mat),('solver_seed',rr.vec)]:d[name]=fn()
 d['tag']=rr.text();d['flags']=[rr.u() for _ in range(5)];d['rawx'],d['rawy']=rr.vec(),rr.vec();d['slots']=rr.u();d['errors']=[rr.d() for _ in range(5)];rr.end();return d

def readmap(r):
 m=dict(cell=r.u(),cycle=r.u(),half=r.u())
 for k in ['origin','state','cell_origin']:m[k]=state(r)
 m['u']=r.vec()
 for k in ['A','B','cell_A','cell_B']:m[k]=r.mat()
 m['d'],m['cell_d']=r.vec(),r.vec();return m

def nominal(data):
 r=R(data,'ORIGINAL_GENUINE_NOMINAL_BEFORE_ADAPTER');n={'tags':[r.text() for _ in range(5)],'identities':[identity(r) for _ in range(4)],'session':r.text()}
 n['deps']=[identity(r) for _ in range(r.u())];n['libs']=[identity(r) for _ in range(r.u())];n['metadata']=metadata(r);n['initial']=r.nums(30);n['alpha']=r.nums(7);n['b']=r.d();n['bound']=r.u();n['mesh']=[r.u() for _ in range(r.u())];n['controls']=[(r.u(),np.r_[r.vec(),r.d()]) for _ in range(r.u())]
 assert r.u()==1;n['success'],n['final_available'],n['error']=r.u(),r.u(),r.text();n['final']=state(r);n['extension'],n['uncertified'],n['extension_error']=r.u(),r.signed(),r.text();n['points'],n['cycles'],n['cells']=values(r);n['maps']={k:[readmap(r) for _ in range(r.u())] for k in ['half','cycle','cell']};r.end();return n

def inline_full(data):
 r=R(data,'INLINE_QP_COMPLETE_OR_RETAINED_PREFIX');p={'stage':r.text(),'error':r.text(),'info':[r.u() for _ in range(7)],'observation_source':r.text(),'timingmode':r.u(),'ages':[r.d() for _ in range(3)],'geometry':r.u()}
 for k,fn in [('H',r.mat),('g',r.vec),('A',r.mat),('l',r.vec),('u',r.vec)]:p[k]=fn()
 p['age']=r.d();p['F'],p['f'],p['seed'],p['constant']=r.mat(),r.vec(),r.vec(),r.d();p['labels']=[(r.text(),r.text()) for _ in range(r.u())];p['terms']=[(r.text(),r.u(),r.u()) for _ in range(r.u())];p['task']=[{'id':r.text(),'residual':r.vec(),'Js':r.vec(),'Jq':r.mat()} for _ in range(r.u())]
 rows,cols,n=r.u(),r.u(),r.u();p['sparseF']=np.zeros((rows,cols))
 for _ in range(n):i,j,v=r.u(),r.u(),r.d();p['sparseF'][i,j]=v
 r.end();return p

def candidate_value(data):
 r=R(data,'ORIGINAL_GENUINE_CANDIDATE_VALUE_NO_EXECUTION');v={'facts':[r.u() for _ in range(3)]};v['metadata_present']=r.u();v['metadata']=metadata(r) if v['metadata_present'] else None;v['transport'],v['nomdigest'],v['digest']=r.text(),r.text(),r.text();v['initial']=r.nums(30);v['controls']=[(r.u(),np.r_[r.vec(),r.d()]) for _ in range(r.u())];assert r.u()==1;v['success'],v['final_available'],v['error']=r.u(),r.u(),r.text();v['final']=state(r);v['points'],v['cycles'],v['cells']=values(r);r.end();return v

def initial_validation(data):
 r=R(data,'BOUND_CURRENT_INITIAL_WEIGHTED_JACOBIAN_AND_GEOMETRY_V1');o={'q':r.nums(7),'ids':[r.text(),r.text()],'time':r.d(),'J':r.mat(),'true':r.d(),'cover':r.d(),'sigma':r.d(),'complete':r.u(),'scope':r.text()};r.end();return o

def validation(data):
 r=R(data,'FULL_PREDICTED_VALUE_DOMAINS_AND_DISCRETE_INTERPOLATION_V1');o={'attempted':r.u(),'passed':r.u(),'stage':r.text(),'error':r.text(),'reach':r.d(),'radius':r.d(),'sigmaL':r.d(),'scope':r.text()};ps=[]
 for _ in range(r.u()):
  p=dict(sample=r.u(),cell=r.u(),cycle=r.u(),half=r.u(),elapsed=r.d(),a=r.nums(7),j=r.nums(7))
  for k in ['true','cover','sigma','geometry_lower','sigma_lower','affine_error','trust']:p[k]=r.d()
  p.update(queries=r.u(),complete=r.u(),stage=r.text(),error=r.text());ps.append(p)
 o['points']=ps;r.end();return o

def commit_record(r):
 o={'flags':[r.u() for _ in range(4)],'stage':r.text(),'error':r.text(),'before':[r.u(),r.u()],'after':[r.u(),r.u()],'held':r.nums(7),'time0':r.d(),'time1':r.d()};ps=[]
 for _ in range(r.u()):
  p=dict(step=r.u(),time=r.d(),returned=r.u(),native_read=r.u(),scratch_read=r.u())
  for k in ['q','v','C','a','j']:p[k]=r.nums(7)
  for k in ['jerk_available','geometry_complete','integration_guard','contacts']:p[k]=r.u()
  p['warnings']=[r.u() for _ in range(8)]
  for k in ['true','cover','tcp_error','arm_error','sigma','geometry_lower','sigma_lower']:p[k]=r.d()
  p.update(queries=r.u(),passed=r.u(),stage=r.text(),error=r.text());ps.append(p)
 o['points']=ps;return o

def cycle_timing(data):
 r=R(data,'ACTUAL_OFFLINE_CYCLE_SEGMENTS_AND_4MS_MISS');o={'cycle':r.u(),'finalized':r.u(),'wall':r.d(),'missed':r.u(),'segments':[(r.u(),r.d()) for _ in range(6)],'counts':[r.u() for _ in range(5)],'scope':r.text()};r.end();return o

def parse_current_hint(data):
 r=R(data,'BOUNDED_CURRENT_MATRIX_OPTIMIZER_HINT_NOT_CANDIDATE');o={'present':r.u()}
 if o['present']:
  o.update(complete=r.u(),error=r.text(),x=r.vec(),y=r.vec());o['events']=[{'iteration':r.u(),'active':r.u(),'worst':r.signed(),'violation':r.d(),'min_lambda':r.d(),'stationarity':r.d(),'residual':r.d()} for _ in range(r.u())];o['faces']=[(r.u(),r.signed()) for _ in range(r.u())]
 o['scope']=r.text();r.end();return o

def compare(checks,name,a,b,atol=1e-11,rtol=1e-10):
 a,b=np.asarray(a),np.asarray(b);assert a.shape==b.shape and np.isfinite(a).all() and np.isfinite(b).all(),name
 err=np.abs(a-b);assert np.all(err<=atol+rtol*np.maximum(abs(a),abs(b))),(name,float(err.max()))
 checks[name]=float(err.max()) if err.size else 0

def reproduce_original(n,p,x0,posture_reference,profile,consts):
 """Independent lifted solve and literal original-cost/row regeneration."""
 checks={};check=lambda name,a,b,*args:compare(checks,name,a,b,*args)
 maps=n['maps'];cells=n['cells'];points=n['points'];mesh=n['mesh'];controls=n['controls'];previous_alpha=n['alpha'];previous_b=n['b']
 H,g,A,lower,upper,F,f,seed,constant,labels,terms,task,sparse=[p[k] for k in ['H','g','A','l','u','F','f','seed','constant','labels','terms','task','sparseF']]
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
  factor(T,v,100*duration,f'tracking/node/{k}');factor(M[k,7:14],c[k,7:14],.01*duration,f'physical_velocity/node/{k}');factor(M[k,:7],c[k,:7]-posture_reference,.001*duration,f'posture/node/{k}')
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
 return checks,dict(M=M,c=c,P=P,Sm=Sm,Sc=Sc,Ubar=U)

def candidate(data):
 r=R(data,'SOLVER_RESULT_AND_DATA_ONLY_PREVIEW');o={'stop':r.text(),'flags':[r.u() for _ in range(7)],'backend_row':r.signed(),'U':r.vec(),'metrics':[r.d() for _ in range(14)],'reuse':[r.u() for _ in range(4)],'reset':r.text(),'counts':[r.u() for _ in range(4)],'rowviol':r.vec(),'mode':r.u(),'age_fields':[r.d() for _ in range(4)],'timing_flags':[r.u() for _ in range(2)]}
 o['preview_present']=r.u()
 if o['preview_present']:o['preview_joint']=[r.nums(7) for _ in range(5)];o['preview_progress']=[r.d() for _ in range(4)];o['half_s'],o['half_r']=r.nums(2),r.nums(2);o['preview_from']=[r.u(),r.u()]
 o['tail_present']=r.u()
 if o['tail_present']:o['tail_w'],o['tail_alpha'],o['tail_r'],o['tail_b'],o['exact_tail']=r.nums(7),r.nums(7),r.d(),r.d(),r.u()
 o['request_present']=r.u()
 if o['request_present']:o['request_x']=r.nums(30);o['request_boundary']=[r.u(),r.u()];o['request_ids']=[r.text() for _ in range(3)];o['request_mesh']=[r.u() for _ in range(20)];o['request_controls']=[r.nums(8) for _ in range(r.u())]
 r.end();return o

def verify_reduction(q,d,guard):
 checks={};ck=lambda n,a,b,*args:compare(checks,n,a,b,*args)
 H,g,A,l,u,F=[q[k] for k in ['H','g','A','l','u','F']];labels=q['labels'];eq=[next(i for i,v in enumerate(labels) if v[0]==('terminal/alpha/'+str(j) if j<7 else 'terminal/b')) for j in range(8)]+[next(i for i,v in enumerate(labels) if v[0]==('terminal/command_w/'+str(j) if j<7 else 'terminal/progress_r')) for j in range(8)]
 assert d['eq']==eq and np.array_equal(d['E'],A[eq]) and np.array_equal(d['rhs'],l[eq]) and np.array_equal(l[eq],u[eq])
 Z144=np.zeros((160,144));Z144[:144]=np.eye(144);p=np.zeros(160)
 for j in range(8):
  assert np.count_nonzero(A[eq[j]])==1 and A[eq[j],152+j]==1 and l[eq[j]]==0
  pivot=144+j;p[pivot]=l[eq[8+j]]/A[eq[8+j],pivot];Z144[pivot]=-A[eq[8+j],:144]/A[eq[8+j],pivot]
 cols=[8*k+j for k in range(18) for j in range(7)];Z=Z144[:,cols];assert np.array_equal(d['Z'],Z) and np.array_equal(d['p'],p)
 assert d['rows'][-140:]==[-1]*140;rows=d['rows'][:-140]
 H144=Z144.T@H@Z144;D144=1/np.sqrt(np.diag(H144));A144=A[rows]@Z144;Rbase=1/np.maximum(1,np.max(np.abs(A144*D144),axis=1));D=D144[cols]
 ck('Hr',d['Hr'],Z.T@H@Z);ck('gr',d['gr'],Z.T@(g+H@p));ck('Fr',d['Fr'],F@Z);ck('D',d['D'],D);ck('Rbase',d['R'][:-140],Rbase)
 ck('Ar',d['Ar'][:-140],A[rows]@Z);ck('lr',d['lr'][:-140],l[rows]-A[rows]@p);ck('ur',d['ur'][:-140],u[rows]-A[rows]@p)
 gs=[8*k+j for k in range(20) for j in range(7)];assert guard['cols']==gs and guard['caps']==[.000999,.001]
 ck('guardAr',d['Ar'][-140:],Z[gs]);ck('guardlr',d['lr'][-140:],-.000999-p[gs]);ck('guardur',d['ur'][-140:],.000999-p[gs]);ck('guardR',d['R'][-140:],1/np.maximum(1,np.max(np.abs(Z[gs]*D),axis=1)))
 ck('Hs',d['Hs'],D[:,None]*d['Hr']*D);ck('gs',d['gs'],D*d['gr']);ck('As',d['As'],d['R'][:,None]*d['Ar']*D);ck('ls',d['ls'],d['R']*d['lr']);ck('us',d['us'],d['R']*d['ur']);ck('Fs',d['Fs'],d['Fr']*D)
 ck('constant',d['errors'][0],q['constant']+g@p+.5*p@H@p);ck('equalities_p',d['E']@p,d['rhs']);ck('equalities_Z',d['E']@Z,np.zeros((16,126)))
 return checks

def rounded_history(x0,prev_alpha,prev_b,U,mesh,labels,l,u):
 C=x0[14:21].copy();w=x0[21:28].copy();s,rr=x0[28:];previous=prev_alpha.copy();pb=prev_b;tick=0;fail=[];index={label:i for i,(label,unit) in enumerate(labels)};first=None
 for k,m in enumerate(mesh):
  s0,r0=s,rr;a=U[k*8:k*8+7];b=U[k*8+7]
  for t in range(m):
   tick+=1;nw=w+.004*a;nc=C+.004*nw;ia=(nw-w)/.004;j=(ia-previous)/.004
   if maxabs(a)>1 or maxabs(ia)>1 or maxabs(j)>20 or maxabs(nw)>.0625 or abs(b)>.5 or abs((b-pb)/.004)>5:fail.append(tick)
   for d in range(7):
    row=index[f'command/C/tick/{tick}/{d}'];offset=x0[14+d]+tick*.004*x0[21+d]
    if nc[d]<l[row]+offset or nc[d]>u[row]+offset:fail.append(('C',tick,d))
   for half in (1,2):
    dt=.004*t+.002*half;sr=s0+dt*r0+.5*dt*dt*b;rrh=r0+dt*b
    if not(0<=sr<=1 and 0<=rrh<=.2):fail.append(('progress',tick,half))
   ns=s+.004*rr+.5*.004*.004*b;nr=rr+.004*b
   if not(0<=ns<=1 and 0<=nr<=.2):fail.append(('progress_recursive',tick))
   if first is None:first=(nc.copy(),nw.copy(),a.copy(),ia.copy(),j.copy(),ns,nr,b,(b-pb)/.004)
   C,w,s,rr,previous,pb=nc,nw,ns,nr,ia,b
 return {'cycles':tick,'failures':fail,'final_w':w,'final_alpha':previous,'s':s,'r':rr,'b':pb,'first':first}

def check_forecast_and_B(n,v,before,assessment,initial,cycle,out):
 assert n['initial'].tobytes()==before['x'].tobytes() and n['alpha'].tobytes()==before['alpha'].tobytes() and n['b']==before['b']
 assert n['bound']==n['success']==n['final_available']==n['extension']==1 and n['uncertified']==-1 and not n['error'] and not n['extension_error'] and not n['tags'][0] and not n['tags'][1]
 assert v['metadata_present']==(1 if cycle==0 else 0)
 assert v['facts']==([1,1,1] if cycle==0 else [0,0,1]) and v['success']==v['final_available']==1 and not v['transport'] and not v['error'] and v['initial'].tobytes()==before['x'].tobytes() and v['nomdigest']==n['tags'][2]
 assert [len(v['points']),len(v['cycles']),len(v['cells'])]==[400,200,20] and len(n['points'])==len(n['maps']['half'])==400
 assert initial['q'].tobytes()==before['x'][:7].tobytes() and initial['ids']==before['ids'] and initial['time']==before['time'] and initial['complete']==1 and initial['J'].shape==(6,7) and np.isfinite(initial['J']).all()
 compare({},'initial_sigma',initial['sigma'],np.linalg.svd(initial['J'],compute_uv=False)[-1],1e-13,1e-12)
 assert assessment['attempted']==assessment['passed']==1 and not assessment['error'] and len(assessment['points'])==400
 delta=np.zeros(30);C=before['x'][14:21].copy();w=before['x'][21:28].copy();prevq=before['x'][:7].copy();prevv=before['x'][7:14].copy();preva=before['a'].copy();pc=min(initial['true'],initial['cover']);ps=initial['sigma'];index=0;rows=[];maxerr=maxtrust=intervalerror=aerr=jerr=0.
 for k,mcount in enumerate(n['mesh']):
  cu=v['controls'][k][1];nu=n['controls'][k][1];du=cu-nu
  for t in range(mcount):
   w=w+.004*cu[:7];C=C+.004*w
   for half in (1,2):
    p=v['points'][index];m=n['maps']['half'][index];b=assessment['points'][index];nz=np.r_[n['points'][index]['q'],n['points'][index]['v'],n['points'][index]['C'],n['points'][index]['w'],n['points'][index]['s'],n['points'][index]['r']]
    z=np.r_[p['q'],p['v'],p['C'],p['w'],p['s'],p['r']];linear=nz+m['cell_A']@delta+m['cell_B']@du;res=z-linear;err=maxabs(res);trust=maxabs(p['q']-nz[:7]);aa=(p['v']-prevv)/.002;jj=(aa-preva)/.002
    assert (p['cell'],p['cycle'],p['half'])==(k,t+1,half)==(m['cell'],m['cycle'],m['half']) and p['C'].tobytes()==C.tobytes() and p['w'].tobytes()==w.tobytes() and p['s']==p['r']==0
    assert b['complete']==1 and not b['error'] and b['queries']==9035 and p['control_clips']==p['force_clips']==0 and err<=1e-6 and trust<=.002 and maxabs(aa)<=5 and maxabs(jj)<=500
    assert maxabs(p['q']-(prevq+.002*p['v']))<=1e-12 and abs(p['time']-.002*(index+1))<1e-10
    travel=float(abs(p['q']-prevq).sum());gl=min(pc,b['true'],b['cover'])-4*travel-1e-6;sl=min(ps,b['sigma'])-32*travel
    intervalerror=max(intervalerror,abs(b['geometry_lower']-gl),abs(b['sigma_lower']-sl));aerr=max(aerr,maxabs(b['a']-aa));jerr=max(jerr,maxabs(b['j']-jj));assert gl>=.005 and sl>=1e-6 and abs(err-b['affine_error'])<2e-13 and abs(trust-b['trust'])<2e-13
    maxerr=max(maxerr,err);maxtrust=max(maxtrust,trust);rows.append([index,k,t+1,half,p['time']]+z.tolist()+linear.tolist()+res.tolist()+aa.tolist()+jj.tolist()+[err,trust,b['true'],b['cover'],b['sigma'],gl,sl,b['queries']])
    if half==2:assert z.tobytes()==v['cycles'][index//2].tobytes()
    prevq,prevv,preva,pc,ps=p['q'],p['v'],aa,min(b['true'],b['cover']),b['sigma'];index+=1
  assert z.tobytes()==v['cells'][k].tobytes();delta=n['maps']['cell'][k]['cell_A']@delta+n['maps']['cell'][k]['cell_B']@du
 assert index==400 and aerr==jerr==0 and v['final'].tobytes()==v['cells'][-1].tobytes() and intervalerror<1e-11
 names=[f'{k}{j}' for k in ['q','v','C','w'] for j in range(7)]+['s','r'];header=['sample','cell','cycle','half','elapsed']+[pre+s for pre in ['value_','global_affine_','residual_'] for s in names]+[f'predicted_{k}{j}' for k in ['a','jerk'] for j in range(7)]+['max30','jointtrust','true_m','cover_m','sigma','geometry_interval_m','sigma_interval','queries']
 file=out/f'cycle_{cycle}_independent_value400.csv'
 with file.open('w',newline='') as fd:
  wcsv=csv.writer(fd);wcsv.writerow(header);wcsv.writerows([[format(float(x),'.17g') for x in row] for row in rows])
 assert file.stat().st_size<1000000
 return {'max30':maxerr,'jointtrust':maxtrust,'a_j_record_difference':[aerr,jerr],'interval_arithmetic_error_all400_including_first':intervalerror,'genuine_value_facts':v['facts'],'CSV_bytes':file.stat().st_size}

def verify_commit(base,before,after,cv,iv,candidate_record,cycle):
 r=R(pin(base/'actual_commit.bin'),'TWO_REAL_2MS_HELD_TARGET_COMMIT_OR_RETAINED_PARTIAL_V1');c=commit_record(r);r.end()
 assert c['flags']==[1,1,2,2] and c['before']==[cycle,cycle] and c['after']==[cycle+1,cycle+1] and not c['error'] and len(c['points'])==2
 assert c['time0']==before['time'] and c['time1']==after['time'] and c['held'].tobytes()==candidate_record['preview_joint'][0].tobytes()
 q=before['x'][:7];v=before['x'][7:14];a=before['a'];clear=min(iv['true'],iv['cover']);sigma=iv['sigma'];err=interval=0.;rows=[]
 for i,p in enumerate(c['points']):
  assert p['step']==i+1 and p['returned']==p['passed']==p['jerk_available']==p['geometry_complete']==p['integration_guard']==1 and p['native_read']==p['scratch_read']==7 and not p['error'] and p['contacts']==0 and p['warnings']==[0]*8 and p['queries']==9035
  assert abs(p['time']-c['time0']-.002*(i+1))<1e-10 and p['C'].tobytes()==c['held'].tobytes()==cv['points'][i]['C'].tobytes()
  aa=(p['v']-v)/.002;jj=(aa-a)/.002;assert aa.tobytes()==p['a'].tobytes() and jj.tobytes()==p['j'].tobytes() and maxabs(aa)<=5 and maxabs(jj)<=500
  travel=float(abs(p['q']-q).sum());gl=min(clear,p['true'],p['cover'])-4*travel-1e-6;sl=min(sigma,p['sigma'])-32*travel
  interval=max(interval,abs(gl-p['geometry_lower']),abs(sl-p['sigma_lower']));assert gl>=.005 and sl>=1e-6 and p['tcp_error']<=1e-8 and p['arm_error']<=1e-8
  err=max(err,maxabs(p['q']-cv['points'][i]['q']),maxabs(p['v']-cv['points'][i]['v']));rows.append([cycle,i+1,p['time']]+p['q'].tolist()+p['v'].tolist()+p['C'].tolist()+p['a'].tolist()+p['j'].tolist()+[p['true'],p['cover'],p['sigma'],gl,sl,p['contacts'],p['queries']])
  q,v,a,clear,sigma=p['q'],p['v'],aa,min(p['true'],p['cover']),p['sigma']
 assert after['x'][:7].tobytes()==q.tobytes() and after['x'][7:14].tobytes()==v.tobytes()==after['v'].tobytes() and after['a'].tobytes()==a.tobytes()
 assert after['x'][14:21].tobytes()==c['held'].tobytes() and after['x'][21:28].tobytes()==candidate_record['preview_joint'][1].tobytes() and after['alpha'].tobytes()==candidate_record['preview_joint'][3].tobytes()
 assert before['steps']==1000+2*cycle and after['steps']==1002+2*cycle and after['boundary']==[cycle+1,cycle+1]
 journal=pin(base/'actual_commit_journal.csv');jr=list(csv.reader(journal.decode().splitlines()));assert len(jr)==8 and all(len(p)==58 for p in jr)
 expected=['BEFORE_VALIDATED_HELD_TARGET_WRITE','VALIDATED_HELD_TARGET_WRITTEN_NO_STEP_YET']+['BEFORE_NATIVE_COMMIT_STEP_ATTEMPT','NATIVE_COMMIT_STEP_RETURNED_BEFORE_SCRATCH','COMPLETE_ACTUAL_COMMIT_OBSERVATION_AND_GEOMETRY']*2
 assert [p[0] for p in jr]==expected
 for i,p in enumerate(jr):
  numbers=np.array([float(t) for t in p[1:]]);assert numbers[28:35].tobytes()==c['held'].tobytes()
  if i>=2:
   cp=c['points'][(i-2)//3];phase=(i-2)%3;assert numbers[0]==cp['step']
   assert np.array_equal(numbers[2:5],[[0,0,0],[1,7,0],[1,7,7]][phase])
   if phase>=1:assert numbers[14:21].tobytes()==cp['q'].tobytes() and numbers[21:28].tobytes()==cp['v'].tobytes()
   if phase==2:assert numbers[35:42].tobytes()==cp['a'].tobytes() and numbers[42:49].tobytes()==cp['j'].tobytes()
 r=R(pin(base/'commit_journal_receipt.bin'),'ACTUAL_DURABLE_NATIVE_STEP_JOURNAL_PREFIX_V3');r.text();jsha=r.text();counts=[r.u() for _ in range(5)];r.text();r.end();assert jsha==hashlib.sha256(journal).hexdigest() and counts==[len(journal),len(journal),8,8,0]
 return {'value_actual_qv_absmax':err,'actual_first_and_second_interval_arithmetic_error':interval,'history':c['before']+c['after'],'times':[p['time'] for p in c['points']],'journal_events':8},rows,c

def verify_receipts(base):
 receipts={};fields={};current=None
 for line in pin(base/'MANIFEST.yaml').decode().splitlines():
  if line=='files:':continue
  if line.startswith('  - file: '):name=scalar(line[len('  - file: '):]);assert name not in receipts;current={};receipts[name]=current
  elif line.startswith('    '):key,value=line[4:].split(': ',1);assert key not in current;current[key]=scalar(value)
  else:key,value=line.split(': ',1);assert key not in fields;fields[key]=scalar(value)
 for name,v in receipts.items():
  b=pin(base/name,v['sha256']);assert len(b)==v['bytes'] and v['created'] and v['complete'] and v['hash_valid'] and not v['error'];R(b,v['role'])
 assert sum(v['bytes'] for v in receipts.values())==fields['output_bytes']
 return {'files':len(receipts),'bytes':fields['output_bytes'],'core_data_only_execution_permission':fields['core_data_only_execution_permission']}

def shifted_controls(U,mesh):
 # Independent piecewise-constant control integral over shifted cell intervals.
 oldedges=np.r_[0,np.cumsum(mesh)];newedges=np.r_[1,1+np.cumsum(mesh)];weights=np.maximum(0,np.minimum(newedges[1:,None],oldedges[None,1:])-np.maximum(newedges[:-1,None],oldedges[None,:-1]))/np.asarray(mesh)[:,None]
 return (weights@U.reshape(20,8)).reshape(160)

def main():
 ss=hashlib.sha256(Path(__file__).read_bytes()).hexdigest();ap=argparse.ArgumentParser();ap.add_argument('--packet',required=True);ap.add_argument('--ready-sha',required=True);args=ap.parse_args();pack=Path(args.packet)
 ready=pin(pack/'READY.json',args.ready_sha);manifest=json.loads(ready)['files']
 for name,v in manifest.items():assert len(pin(pack/name,v['sha256']))==v['bytes']
 (OUT/'PACKET_READY_READ.json').write_bytes(ready)
 unit=pack/'actual-dell/session-dynamic-three-cycle-v5-20261011-attempt20';run=unit/'run-attempt1';base=run/'artifacts'
 source=Path('/private/tmp/phase5_dynamic_source_review_v2_20261011');sm=json.loads(pin(source/'READY.json','bf27985f7f2ac9d4d5626e596de9ee47f453fda9f575d581053455a19ccca12e'))
 for n,v in sm['files'].items():
  if n.startswith('src/'):assert pin(unit/n,v['sha256'])==pin(source/n,v['sha256'])
 profile=json.loads(pin(unit/'profile-version1/active_input.json','2de29ad696bb58a5cf87fec360df5c6f57561d7b1e95ad794bbcb868e39bc90e'));producer=json.loads(pin(unit/'profile-version1/PRODUCER.json'));root_before=snapshot(pin(base/'observation_before.bin'));root_receipts=verify_receipts(base)
 constpath=Path('/private/tmp/public_live_affine_v2_integrated_first_cycle_canonical_protocol_repair_v2_20261010/proposed-files/inputs/public_constants.json');consts=json.loads(pin(constpath,profile['constants']['sha256']))
 previous=root_before;previousU=None;results=[];actualrows=[];commits=[];originalslots=[]
 for cycle in range(3):
  cb=base/f'cycle-{cycle}';receipt=verify_receipts(cb);before=snapshot(pin(cb/'observation_before.bin'));after=snapshot(pin(cb/'observation_after.bin'))
  assert before['boundary']==[cycle,cycle] and before['x'].tobytes()==previous['x'].tobytes() and before['alpha'].tobytes()==previous['alpha'].tobytes() and before['v'].tobytes()==previous['v'].tobytes() and before['a'].tobytes()==previous['a'].tobytes() and before['ib'].tobytes()==previous['ib'].tobytes() and before['time']==previous['time']
  n=nominal(pin(cb/'original_nominal.bin'));q=inline_full(pin(cb/'inline_qp.bin'));cv=candidate_value(pin(cb/'candidate_value.bin'));cr=candidate(pin(cb/'candidate.bin'));iv=initial_validation(pin(cb/'validation_initial.bin'));assessment=validation(pin(cb/'candidate_validation.bin'));red=reduction(pin(cb/'qp_equality_reduction.bin'));timing=cycle_timing(pin(cb/'cycle_timing.bin'));hint=parse_current_hint(pin(cb/'current_numeric_hint.bin'))
  assert n['identities'][0]==producer and n['identities'][1:]==[profile[k] for k in ['xml','constants','expected_metadata']] and n['deps']==profile['dependencies'] and n['libs']==profile['loaded_libraries']
  assert q['info'][:5]==[1,0,741,13156,21] and q['geometry']==0 and not q['error'] and cr['flags'][3:]==[0,1,0,1] and cr['flags'][:3]==[0,1,1] and cr['request_present']==1
  U=cr['U'];assert U.shape==(160,) and np.isfinite(U).all() and np.all(U[7::8]==0)
  Ubar=np.concatenate([u for m,u in n['controls']]);compare({},'control-only_nominal_shift',Ubar,np.zeros(160) if cycle==0 else shifted_controls(previousU,n['mesh']),1e-15,1e-13)
  assert cv['initial'].tobytes()==before['x'].tobytes() and cr['request_x'].tobytes()==before['x'].tobytes() and cr['request_boundary']==before['boundary'] and cr['request_ids'][:2]==before['ids'] and cr['request_ids'][2]==n['tags'][2]
  assert all(np.r_[a].tobytes()==U[k*8:k*8+8].tobytes()==cr['request_controls'][k].tobytes() for k,(m,a) in enumerate(cv['controls']))
  original,assembly=reproduce_original(n,q,before['x'],root_before['x'][:7],profile,consts)
  rr=R(pin(cb/'planning_guard.bin'),'EXPLICIT_OPTIMIZER_ORIGINAL_ALPHA_SUBSET_GUARD_V1');guard={'caps':[rr.d(),rr.d()],'base':rr.u(),'cols':[rr.u() for _ in range(rr.u())],'R':rr.vec(),'label':rr.text(),'scope':rr.text()};rr.end();trans=verify_reduction(q,red,guard)
  ax=q['A']@U;vio=np.maximum.reduce([q['l']-ax,ax-q['u'],np.zeros(13156)]);assert vio.max()<=1e-7;compare({},'all_original_violations',vio,cr['rowviol'])
  compare({},'U_from_scaled',U,red['p']+red['Z']@(red['D']*red['x']));assert maxabs(U.reshape(20,8)[:,:7])<=.001
  history=rounded_history(before['x'],before['alpha'],before['b'],U,n['mesh'],q['labels'],q['l'],q['u']);assert history['cycles']==200 and not history['failures']
  for i in range(5):assert cr['preview_joint'][i].tobytes()==history['first'][i].tobytes()
  assert hint['present']==hint['complete']==1 and not hint['error'];assert hint['x'].tobytes()==red['solver_seed'].tobytes()
  hstat=maxabs(red['Hs']@hint['x']+red['gs']+red['As'].T@hint['y']);hax=red['As']@hint['x'];hvio=float(np.maximum.reduce([red['ls']-hax,hax-red['us'],np.zeros(len(hax))]).max());assert hstat<=1e-10 and hvio<=1e-12
  bsummary=check_forecast_and_B(n,cv,before,assessment,iv,cycle,OUT);csummary,rows,c=verify_commit(cb,before,after,cv,iv,cr,cycle);actualrows.extend(rows);commits.append(c)
  assert timing['cycle']==cycle and timing['finalized']==timing['missed']==1 and np.isfinite(timing['wall']) and timing['wall']>.004 and all(flag==1 and np.isfinite(value) and value>=0 for flag,value in timing['segments'])
  assert timing['counts'][:3]==[cycle+1,2*(cycle+1),2*(cycle+1)] and timing['counts'][4]==8459213*(cycle+1);originalslots.append(timing['counts'][3])
  results.append({'cycle':cycle,'original_algebra':original,'reduction_algebra':trans,'SI_max':float(vio.max()),'strict200_pass':True,'alpha_max':maxabs(U.reshape(20,8)[:,:7]),'hint_stationarity':hstat,'hint_violation':hvio,'hint_events':len(hint['events']),'nominal_nonzero_control':bool(np.any(Ubar!=0)),'accepted_initial_w_max':maxabs(before['x'][21:28]),'terminal_p_max':maxabs(red['p']),'B':bsummary,'C':csummary,'timing':timing,'binary_receipts':receipt,'native':{'status':cr['flags'][3],'raw':cr['flags'][4],'iterations':cr['flags'][6],'setup':cr['metrics'][3],'solve':cr['metrics'][4]},'exact_command_progress_tail':cr['exact_tail']})
  previous,previousU=after,U
 assert originalslots==sorted(originalslots) and len(set(originalslots))==3
 end=snapshot(pin(base/'observation_after.bin'));assert end['x'].tobytes()==previous['x'].tobytes() and end['a'].tobytes()==previous['a'].tobytes() and end['steps']==1006 and end['boundary']==[3,3]
 r=R(pin(base/'entry_completion.bin'),'ACTIVE_SESSION_FINAL_SCOPE_AND_TIMING');stage,error=r.text(),r.text();same,sessionpass=r.u(),r.u();sf=r.text();simpass=r.u();simf=r.text();wall=r.d();steps,commitcount=r.u(),r.u();r.end();assert stage=='COMPLETE_THREE_REOBSERVED_REPROPAGATED_CYCLES_NOT_FULL_TASK' and error==sf==simf=='' and same==0 and sessionpass==simpass==1 and steps==1006 and commitcount==3
 r=R(pin(base/'retained_commit_history.bin'),'ALL_ACTUAL_COMMIT_OUTCOMES_INCLUDING_PARTIAL_FAILURES');assert r.u()==3
 for c in commits:
  saved=commit_record(r)
  for key in ['flags','before','after','stage','error','time0','time1']:assert saved[key]==c[key]
  assert saved['held'].tobytes()==c['held'].tobytes()
  for ps,pc in zip(saved['points'],c['points']):
   for key in ps:assert np.array_equal(ps[key],pc[key]) if isinstance(ps[key],np.ndarray) else ps[key]==pc[key]
 r.text();r.end()
 r=R(pin(base/'bootstrap.bin'),'ACTUAL_DIRECT_SESSION_API_ENTRIES');facts=[r.u() for _ in range(9)];r.end();assert facts[:3]==[1,2,1] and facts[-2:]==[1006,3]
 beforepins=pin(run/'BEFORE_INPUT_IDENTITIES.json');afterpins=pin(run/'AFTER_INPUT_IDENTITIES.json');assert beforepins==afterpins;pinrows=json.loads(beforepins);assert len(pinrows)==1696 and len({v['requested_path'] for v in pinrows})==1667
 dispatch=json.loads(pin(run/'BATCH_PREFIX.json'));assert dispatch['native_project_entry_dispatches']==1 and len(dispatch['records'])==1 and dispatch['records'][0]['exit']==0
 release=json.loads(pin(pack/'ROOT_ONE_THREE_CYCLE_RELEASE.json'));assert dispatch['records'][0]['argv']==release['sole_child_argv']
 with (OUT/'independent_actual6_steps.csv').open('w',newline='') as fd:
  writer=csv.writer(fd);writer.writerow(['cycle','half','actual_time']+[f'{k}{j}' for k in ['q','v','C','actual_a','actual_jerk'] for j in range(7)]+['true_m','cover_m','sigma','geometry_interval_m','sigma_interval','contacts','queries']);writer.writerows(actualrows)
 summary={'scope':'Three actual offline beta0/smallalpha restricted transactions, no Model/native/solver call by this audit, no task/rest/D-E/realtime/Phase5 acceptance','packet_sha':args.ready_sha,'payloads':len(manifest),'bytes':sum(x['bytes'] for x in manifest.values()),'source_sha256':ss,'cycles':results,'bootstrap':facts,'entry':{'stage':stage,'wall':wall,'physicalsteps':steps,'tasksubsteps':6,'commits':3,'session_termination':sessionpass,'simulation_termination':simpass},'root_binary_receipts':root_receipts,'pin_records':1696,'pin_unique':1667,'same_recorded_before_after':True,'dispatches':1,'phase5':'NOT_ACCEPTED','input_pins':PINS}
 for path,v in list(PINS.items()):b=Path(path).read_bytes();assert len(b)==v['bytes'] and hashlib.sha256(b).hexdigest()==v['sha256']
 assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==ss
 (OUT/'SOURCE_SNAPSHOT.py').write_bytes(Path(__file__).read_bytes());(OUT/'RESULT.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({k:v for k,v in summary.items() if k!='input_pins'},indent=2))

if __name__=='__main__':main()
