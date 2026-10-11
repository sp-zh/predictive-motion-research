"""Actual matrix-only equality elimination/whitening oracle; no solver/model."""
import hashlib,json,struct
from fractions import Fraction
from pathlib import Path
import numpy as np

PACKET=Path('/private/tmp/phase5_active_a_functional_checkpoint_v1_20261010_collection2')
FILE='actual-dell/repair6/run-attempt1/artifacts/inline_qp.bin'
OUT=Path(__file__).resolve().parent
SOURCE_SHA=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
ready=(PACKET/'ACTIVE_A_FUNCTIONAL_CHECKPOINT_READY.json').read_bytes()
assert hashlib.sha256(ready).hexdigest()=='25b8572470112ed66f7c3735bca1e58b2aa16ca0ebbeea4bf8c1917de2fc4fdb'
desc=json.loads(ready)['files'][FILE];b=(PACKET/FILE).read_bytes();assert len(b)==desc['bytes'] and hashlib.sha256(b).hexdigest()==desc['sha256']
class Reader:
 def __init__(self):self.pos=0
 def u(self):v=struct.unpack_from('<Q',b,self.pos)[0];self.pos+=8;return v
 def d(self):v=struct.unpack_from('<d',b,self.pos)[0];self.pos+=8;return v
 def text(self):n=self.u();v=b[self.pos:self.pos+n].decode();self.pos+=n;return v
 def nums(self,n):a=np.frombuffer(b,dtype='<f8',count=n,offset=self.pos).copy();self.pos+=8*n;return a
 def vec(self):return self.nums(self.u())
 def mat(self):r,c=self.u(),self.u();return self.nums(r*c).reshape(r,c)
r=Reader();assert r.text()=='P5_ACTIVE_SESSION_LOSSLESS_V1' and r.text()=='INLINE_QP_COMPLETE_OR_RETAINED_PREFIX';r.text();r.text()
for _ in range(7):r.u()
r.text();r.u()
for _ in range(3):r.d()
r.u();H,g,A,lo,hi=r.mat(),r.vec(),r.mat(),r.vec(),r.vec();r.d();F,f,seed=r.mat(),r.vec(),r.vec();k=r.d();labels=[(r.text(),r.text()) for _ in range(r.u())]
assert H.shape==(160,160) and F.shape==(741,160) and A.shape==(13156,160)
for v in [H,g,A,lo,hi,F,f,seed]:assert np.isfinite(v).all()
eq=np.flatnonzero(lo==hi);assert len(eq)==16
E=A[eq];rhs=lo[eq]
expected=[s for j in range(7) for s in [f'terminal/command_w/{j}',f'terminal/alpha/{j}']]+['terminal/progress_r','terminal/b']
assert [labels[i][0] for i in eq]==expected
mesh=[1,1,2,2,3,3,4,4,5,5,6,6,8,10,12,16,20,24,28,40]
coeff=[]
for m in mesh:
 c=0.
 for _ in range(m):c+=.004
 coeff.append(c)
for j in range(8):
 iw=2*j if j<7 else 14;ia=2*j+1 if j<7 else 15
 v=np.zeros(160);v[j::8]=coeff;assert np.array_equal(E[iw],v)
 v=np.zeros(160);v[19*8+j]=1;assert np.array_equal(E[ia],v) and rhs[ia]==0
# Exact16x16 minor: terminal last-cell inputs and one preceding cell per axis.
pivots=list(range(19*8,20*8))+list(range(18*8,19*8));minor=E[:,pivots]
Q=[[Fraction.from_float(float(x)) for x in row] for row in minor];det=Fraction(1);sign=1
for col in range(16):
 pivot=next(i for i in range(col,16) if Q[i][col]!=0)
 if pivot!=col:Q[pivot],Q[col]=Q[col],Q[pivot];sign=-sign
 diagonal=Q[col][col];det*=diagonal
 for i in range(col+1,16):
  factor=Q[i][col]/diagonal
  for j in range(col,16):Q[i][j]-=factor*Q[col][j]
det*=sign;assert det!=0
singular=np.linalg.svd(E,compute_uv=False);assert singular[-1]>1e-12
orthogonal,_=np.linalg.qr(E.T,mode='complete');Z=orthogonal[:,16:]
p=E.T@np.linalg.solve(E@E.T,rhs)
checks={}
def check(name,a,b,atol=1e-10,rtol=1e-10):
 aa,bb=np.asarray(a),np.asarray(b);assert aa.shape==bb.shape and np.isfinite(aa).all() and np.isfinite(bb).all()
 err=np.abs(aa-bb);gate=atol+rtol*np.maximum(np.abs(aa),np.abs(bb));assert np.all(err<=gate),(name,float(err.max()))
 checks[name]=float(np.max(err,initial=0))
check('nullspace_equality',E@Z,np.zeros((16,144)),1e-12,0);check('particular_equality',E@p,rhs,1e-12,0);check('orthonormal_basis',Z.T@Z,np.eye(144),1e-12,0)
linear=g-F.T@f;linear_constant=k-.5*float(f@f)
rng=np.random.default_rng(20261010)
random_y=[rng.uniform(-3e-4,3e-4,size=144) for _ in range(6)]
shift=rng.uniform(-1e-4,1e-4,size=144)
charts=[p,p+Z@shift];chart_summaries=[];max_si=0.;max_input=0.
def cost(U):return .5*float(U@H@U)+float(g@U)+k
for ci,pc in enumerate(charts):
 Hr=Z.T@H@Z;gr=Z.T@(H@pc+g);kr=k+float(g@pc)+.5*float(pc@H@pc)
 Fr=F@Z;fr=F@pc+f;Ar=A@Z;offset=A@pc;lr=lo-offset;ur=hi-offset
 lr_linear=Z.T@linear;constant_linear=linear_constant+float(linear@pc)
 check(f'chart{ci}_factor_H',Fr.T@Fr,Hr)
 check(f'chart{ci}_factor_g',Fr.T@fr+lr_linear,gr)
 check(f'chart{ci}_factor_constant',.5*float(fr@fr)+constant_linear,kr)
 vectors=[np.zeros(144),Z.T@(seed-pc)]+random_y
 for vi,y in enumerate(vectors):
  U=pc+Z@y;check(f'chart{ci}_vector{vi}_equality',E@U,rhs,1e-12,0)
  transformed=.5*float(y@Hr@y)+float(gr@y)+kr
  factorcost=.5*float((Fr@y+fr)@(Fr@y+fr))+float(lr_linear@y)+constant_linear
  check(f'chart{ci}_vector{vi}_objective',cost(U),transformed)
  check(f'chart{ci}_vector{vi}_factorobjective',cost(U),factorcost)
  check(f'chart{ci}_vector{vi}_gradient',Z.T@(H@U+g),Hr@y+gr)
  original=A@U;reconstructed=Ar@y+offset
  check(f'chart{ci}_vector{vi}_rows',original,reconstructed)
  check(f'chart{ci}_vector{vi}_lower_slack',original-lo,Ar@y-lr)
  check(f'chart{ci}_vector{vi}_upper_slack',hi-original,ur-Ar@y)
  max_si=max(max_si,float(np.maximum.reduce([np.zeros(13156),lo-original,original-hi]).max()))
  caps=np.tile([1]*7+[.5],20);assert np.all(np.abs(U)<=caps)
  max_input=max(max_input,float(np.max(np.abs(U))))
 # One predeclared analytic directional gradient, two central-difference steps.
 y=random_y[0];direction=np.linspace(-1,1,144);direction/=np.linalg.norm(direction)
 grad=float(direction@(Hr@y+gr))
 def reduced_cost(v):return cost(pc+Z@v)
 for eps in [1e-5,1e-6]:check(f'chart{ci}_FD_{eps}',(reduced_cost(y+eps*direction)-reduced_cost(y-eps*direction))/(2*eps),grad,1e-7,1e-7)
 eig=np.linalg.eigvalsh(.5*(Hr+Hr.T));assert eig.min()>0
 chart_summaries.append({'chart':ci,'particular_norm':float(np.linalg.norm(pc)),'rhs_nonzero':bool(np.any(rhs!=0)),'particular_nonzero':bool(np.any(pc!=0)),'reduced_variables':144,'reduced_H_condition':float(eig.max()/eig.min())})
# Full SPD whitening by backward triangular solve, not an explicit matrix inverse.
L=np.linalg.cholesky(H);LT=L.T;T=np.zeros((160,160));I=np.eye(160)
for i in range(159,-1,-1):T[i]=(I[i]-LT[i,i+1:]@T[i+1:])/LT[i,i]
check('whitening_triangular_identity',LT@T,I,1e-12,0)
Hw=T.T@H@T;Fw=F@T;gw=T.T@g;Aw=A@T
check('whitening_H_identity',Hw,I,1e-12,0);check('whitening_factor_identity',Fw.T@Fw,I,1e-12,0)
for vi,x in enumerate([LT@seed,np.zeros(160)]+[rng.uniform(-1e-5,1e-5,size=160) for _ in range(6)]):
 U=T@x;caps=np.tile([1]*7+[.5],20);assert np.all(np.abs(U)<=caps)
 check(f'white{vi}_coordinate_back',LT@U,x,1e-12,0)
 check(f'white{vi}_objective',cost(U),.5*float(x@Hw@x)+float(gw@x)+k)
 check(f'white{vi}_gradient',T.T@(H@U+g),Hw@x+gw)
 check(f'white{vi}_rows',A@U,Aw@x)
 check(f'white{vi}_factor',F@U+f,Fw@x+f)
 check(f'white{vi}_equality',E@U,(E@T)@x,1e-12,0)
eig=np.linalg.eigvalsh(H)
result={'scope':'ACTUAL_SAVED_LINEAR_QP_MATRIX_ALGEBRA_ONLY_NO_SOLVER_MODEL_PHYSICS','source_sha256':SOURCE_SHA,'input_ready_sha256':hashlib.sha256(ready).hexdigest(),'inline_qp_identity':desc,'equality_rows':eq.tolist(),'equality_labels':[labels[i][0] for i in eq],'exact_minor_columns':pivots,'exact_minor_determinant':{'n':str(det.numerator),'d':str(det.denominator)},'exact_rank':16,'equality_singular_values':singular.tolist(),'rhs':rhs.tolist(),'random_seed':20261010,'chart_summaries':chart_summaries,'number_nullspace_testvectors':16,'number_whitening_testvectors':8,'checks':checks,'max_nullspace_test_input_abs':max_input,'max_original_SI_violation_of_random_testvectors':max_si,'random_vectors_scope':'bounded inputs and equality checks only; not feasible nonlinear/executable candidates','full_H_condition':float(eig.max()/eig.min()),'whitened_H_condition':float(np.linalg.cond(Hw)),'all_cost_constants_and_linear_terms_retained':True,'transformed_arrays_serialized':False,'solver_speed_claim':False,'plant_accuracy_claim':False,'phase5':'NOT_ACCEPTED'}
assert hashlib.sha256((PACKET/FILE).read_bytes()).hexdigest()==desc['sha256'] and hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==SOURCE_SHA
(OUT/'results.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ['checks','exact_minor_determinant','equality_singular_values','rhs','equality_rows','equality_labels']},indent=2))
print('max_check_absolute_error',max(checks.values()))
