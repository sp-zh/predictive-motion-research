from pathlib import Path
import resource,signal,os,struct,json,hashlib
resource.setrlimit(resource.RLIMIT_CPU,(30,30));resource.setrlimit(resource.RLIMIT_AS,(536870912,536870912));signal.alarm(40);os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='1'
import numpy as np
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

def reduction(data):
 rr=R(data,'STRUCTURED_ORIGINAL_TERMINAL_EQUALITY_REDUCTION');d={'policy':rr.text(),'stage':rr.text(),'valid':rr.u()}
 def ids():return [rr.signed() for _ in range(rr.u())]
 for name,fn in [('Z',rr.mat),('p',rr.vec),('E',rr.mat),('rhs',rr.vec),('eq',ids),('rows',ids),('Hr',rr.mat),('gr',rr.vec),('Ar',rr.mat),('lr',rr.vec),('ur',rr.vec),('D',rr.vec),('Fr',rr.mat),('seed',rr.vec),('x',rr.vec),('Y',rr.vec),('R',rr.vec),('Hs',rr.mat),('gs',rr.vec),('As',rr.mat),('ls',rr.vec),('us',rr.vec),('Fs',rr.mat),('solver_seed',rr.vec)]:d[name]=fn()
 d['tag']=rr.text();d['flags']=[rr.u() for _ in range(5)];d['rawx'],d['rawy']=rr.vec(),rr.vec();d['slots']=rr.u();d['errors']=[rr.d() for _ in range(5)];rr.end();return d

def inline_full(data):
 r=R(data,'INLINE_QP_COMPLETE_OR_RETAINED_PREFIX');p={'stage':r.text(),'error':r.text(),'info':[r.u() for _ in range(7)],'observation_source':r.text(),'timingmode':r.u(),'ages':[r.d() for _ in range(3)],'geometry':r.u()}
 for k,fn in [('H',r.mat),('g',r.vec),('A',r.mat),('l',r.vec),('u',r.vec)]:p[k]=fn()
 p['age']=r.d();p['F'],p['f'],p['seed'],p['constant']=r.mat(),r.vec(),r.vec(),r.d();p['labels']=[(r.text(),r.text()) for _ in range(r.u())];p['terms']=[(r.text(),r.u(),r.u()) for _ in range(r.u())];p['task']=[{'id':r.text(),'residual':r.vec(),'Js':r.vec(),'Jq':r.mat()} for _ in range(r.u())]
 rows,cols,n=r.u(),r.u(),r.u();p['sparseF']=np.zeros((rows,cols))
 for _ in range(n):i,j,v=r.u(),r.u(),r.d();p['sparseF'][i,j]=v
 r.end();return p


p=Path('/home/codextransfer/predictive_motion/results/phase5/session-nonzero-progress-geometry-three-cycle-v1-20261011-attempt33');out=p/'pure144-fixture-v2';out.mkdir(exist_ok=False)
base=Path('/home/codextransfer/predictive_motion/results/phase5/session-geometry-qp-three-cycle-v4-20261011-attempt30/run-attempt1/artifacts/cycle-0');names=['inline_qp.bin','qp_equality_reduction.bin'];before={n:hashlib.sha256((base/n).read_bytes()).hexdigest() for n in names};q=inline_full((base/names[0]).read_bytes());d=reduction((base/names[1]).read_bytes());assert q['H'].shape==(160,160) and q['A'].shape==(14756,160) and d['E'].shape==(16,160) and len(d['eq'])==16
Z=np.zeros((160,144));Z[:144]=np.eye(144);offset=np.zeros(160)
for j in range(8):
 row=d['E'][8+j];pivot=144+j;offset[pivot]=d['rhs'][8+j]/row[pivot];Z[pivot]=-row[:144]/row[pivot]
assert np.max(np.abs(d['E']@Z))<1e-12 and np.max(np.abs(d['E']@offset-d['rhs']))<1e-12
rows=[r for r in d['rows'] if r>=0];H=Z.T@q['H']@Z;g=Z.T@(q['g']+q['H']@offset);Dscale=1/np.sqrt(np.diag(H));A=q['A'][rows]@Z;l=q['l'][rows]-q['A'][rows]@offset;u=q['u'][rows]-q['A'][rows]@offset;extraA=[];extral=[];extrau=[]
for k in range(20):
 for j in range(7):
  c=8*k+j;extraA.append(Z[c]);extral.append(-.000999-offset[c]);extrau.append(.000999-offset[c])
# Source30 initial current has s=r=previousb=0, as bound by original progress
# first-jerk original row and rhs. This archived fixture is not a new forecast.
index={name:i for i,(name,units) in enumerate(q['labels'])};first=index['feedback_jerk/0/7'];assert q['l'][first]==-5 and q['u'][first]==5;previousb=0.
for k in range(20):
 c=8*k+7;v=Z[c]/.004;shift=offset[c]/.004
 if k:v=v-Z[c-8]/.004;shift-=offset[c-8]/.004
 else:shift-=previousb/.004
 extraA.append(v);extral.append(-4.999-shift);extrau.append(4.999-shift)
A=np.vstack([A,np.asarray(extraA)]);l=np.r_[l,extral];u=np.r_[u,extrau];As=A*Dscale;Rscale=1/np.maximum(1,np.max(np.abs(As),axis=1));As*=Rscale[:,None];ls=l*Rscale;us=u*Rscale;Hs=Dscale[:,None]*H*Dscale[None,:];gs=Dscale*g
assert np.count_nonzero(q['seed'][:144])==0 and min(ls)>=-1e300 and max(us)<=1e300 and np.max(ls)<=1e-12 and np.min(us)>=-1e-12
with (out/'input.bin').open('xb') as f:
 for a in [Hs,gs,As,ls,us]:
  assert np.isfinite(a).all()
  for dim in a.shape:f.write(struct.pack('<Q',dim))
  f.write(np.asarray(a,dtype='<f8').tobytes(order='C'))
np.savez(out/'INPUTS.npz',H=Hs,g=gs,A=As,l=ls,u=us,Z=Z,p=offset,D=Dscale,originalH=q['H'],originalg=q['g'],originalA=q['A'],originall=q['l'],originalu=q['u'],originalF=q['F'],originalf=q['f'],current_nominal_seed=q['seed'],base_original_rows=rows)
assert before=={n:hashlib.sha256((base/n).read_bytes()).hexdigest() for n in names}
result={'fixture_path':str(out/'input.bin'),'fixture_sha256':hashlib.sha256((out/'input.bin').read_bytes()).hexdigest(),'fixture_bytes':(out/'input.bin').stat().st_size,'archived_source_hashes':before,'reduced_dim':144,'rows':len(ls),'original_rows':14756,'extra_alpha_rows':140,'extra_progress_jerk_rows':20,'previousb':previousb,'scope':'numpy mathematics fixture of saved30 initial QP; no new forecast/native OSQP/physics/current33exactIEEE claim','Model':0,'Scene':0,'MuJoCo':0};(out/'READY.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
