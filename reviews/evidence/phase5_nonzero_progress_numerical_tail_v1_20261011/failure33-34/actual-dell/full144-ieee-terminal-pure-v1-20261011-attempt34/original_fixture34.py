from pathlib import Path
import os,resource,signal,json,struct,hashlib
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


p=Path('/home/codextransfer/predictive_motion/results/phase5/full144-ieee-terminal-pure-v1-20261011-attempt34');out=p/'original-fixture-v1';out.mkdir(exist_ok=False);base=Path('/home/codextransfer/predictive_motion/results/phase5/session-geometry-qp-three-cycle-v4-20261011-attempt30/run-attempt1/artifacts/cycle-0');names=['inline_qp.bin','qp_equality_reduction.bin'];before={n:hashlib.sha256((base/n).read_bytes()).hexdigest() for n in names};q=inline_full((base/names[0]).read_bytes());d=reduction((base/names[1]).read_bytes());rows=[r for r in d['rows'] if r>=0];index={n:i for i,(n,u) in enumerate(q['labels'])};first=index['feedback_jerk/0/7'];assert q['l'][first]==-5 and q['u'][first]==5 and d['rhs'][15]==0 and np.count_nonzero(q['seed'])==0
with (out/'original_input.bin').open('xb') as f:
 for a in [q['H'],q['g'],q['A'],q['l'],q['u'],d['E'],d['rhs'],q['seed']]:
  assert np.isfinite(a).all()
  for dim in a.shape:f.write(struct.pack('<Q',dim))
  f.write(np.asarray(a,dtype='<f8').tobytes(order='C'))
 f.write(struct.pack('<Q',len(rows)))
 for r in rows:f.write(struct.pack('<Q',r))
assert before=={n:hashlib.sha256((base/n).read_bytes()).hexdigest() for n in names};result={'original_input_sha256':hashlib.sha256((out/'original_input.bin').read_bytes()).hexdigest(),'bytes':(out/'original_input.bin').stat().st_size,'source_hashes':before,'rows':len(rows),'fulloriginalSIrows':14756,'scope':'untransformed archived30 original matrices/E/seed/rowmap, initial progress history0; no new33forecast'};(out/'READY.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
