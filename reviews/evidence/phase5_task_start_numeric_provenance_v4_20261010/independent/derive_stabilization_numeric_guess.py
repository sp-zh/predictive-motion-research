import resource,signal,time
start=time.monotonic();resource.setrlimit(resource.RLIMIT_CPU,(45,45));resource.setrlimit(resource.RLIMIT_AS,(2147483648,2147483648));signal.alarm(50)
import pathlib,sys,json,struct,hashlib
sys.path.insert(0,'/usr/lib/python3/dist-packages');import numpy as np;from scipy.optimize import minimize,LinearConstraint,nnls
R=pathlib.Path('/home/codextransfer/predictive_motion/results/phase5');O=R/'task-start-linear-oracle-v2-20261010-attempt1/oracle-artifacts-attempt1';P=R/'task-start-stabilization-numeric-guess-v1-20261010';P.mkdir(exist_ok=False);a=np.load(O/'ACTUAL_ORACLE_INPUTS.npz');cols=np.array([k*8+j for k in range(18) for j in range(7)]);H=a['H'][np.ix_(cols,cols)].copy();g=a['g'][cols].copy();A=a['A'][:,cols].copy();l=a['l'].copy();u=a['u'].copy();result={'schema':'STABILIZATION_EXACT_B_ZERO_NUMERIC_GUESS_V1','scope':'explicitconservativeplanning subset b_all0; originalfullQP/terminalE/gates preserved; componentonly nofulltaskprogress','Model':0,'physical_steps':0,'commits':0,'columns':cols.tolist(),'native_shape':[126,len(l)]};(P/'RESULT_PREFIX.json').write_text(json.dumps(result,indent=2)+'\n');np.savez(P/'ACTUAL_STABILIZATION_INPUTS.npz',H=H,g=g,A=A,l=l,u=u,columns=cols)
x=np.linalg.solve(H,-g);ax=A@x;vio=np.max(np.maximum.reduce([l-ax,ax-u,np.zeros(len(l))]));events=[]
if vio>1e-10:
 def cb(x):
  events.append({'iteration':len(events)+1,'elapsed_s':time.monotonic()-start})
  with (P/'ITERATION_APPEND.jsonl').open('a') as f:f.write(json.dumps(events[-1])+'\n');f.flush()
  if time.monotonic()-start>40:raise TimeoutError('boundedstabilizationalgebra')
 opt=minimize(lambda v:.5*v@H@v+g@v,np.zeros(126),jac=lambda v:H@v+g,method='SLSQP',constraints=[LinearConstraint(A,l,u)],callback=cb,options={'maxiter':500,'ftol':1e-12});assert opt.success;x=opt.x;ax=A@x;result['slsqp_iterations']=int(opt.nit)
else:result['unconstrained_feasible']=True
sides=[];vectors=[];norm=np.max(np.abs(A),axis=1)
for k in range(len(l)):
 if norm[k]<=1e-12:continue
 if abs(ax[k]-l[k])<=1e-9:sides.append((k,-1));vectors.append(-A[k])
 if abs(ax[k]-u[k])<=1e-9:sides.append((k,1));vectors.append(A[k])
y=np.zeros(len(l));weights=np.array([]);active=np.array([],dtype=int)
if sides:
 assert len(sides)<=3000;M=np.asarray(vectors).T;weights,_=nnls(M,-(H@x+g),maxiter=20000);active=np.flatnonzero(weights>0)
 if len(active):
  assert len(active)<=126;B=M[:,active].T;rhs=np.asarray([(-l[sides[i][0]] if sides[i][1]<0 else u[sides[i][0]]) for i in active]);K=np.block([[H,B.T],[B,np.zeros((len(active),len(active)))]]);sol=np.linalg.solve(K,np.concatenate([-g,rhs]));assert np.min(sol[126:])>=0;x=sol[:126]
  for w,i in zip(sol[126:],active):k,sign=sides[i];y[k]+=sign*w
ax=A@x;vio=float(np.max(np.maximum.reduce([l-ax,ax-u,np.zeros(len(l))])));assert vio<=1e-10 and np.isfinite(x).all() and np.isfinite(y).all();Z=a['Z'][:,cols];D=a['D'][cols];U=a['p']+Z@(D*x);assert all(U[k*8+7]==0 for k in range(20));np.savez(P/'NUMERICAL_GUESS_ONLY.npz',primal_x=x,dual_y=y,originalU=U)
h=hashlib.sha256()
for v in [H,g,A,l,u]:
 for n in v.shape:h.update(struct.pack('<Q',n))
 h.update(np.asarray(v,dtype='<f8').tobytes(order='C'))
guess=json.loads((R/'task-start-numeric-guess-v1-20261010/guess.json').read_text());guess.update(schema='TASK_START_B_ZERO_STABILIZATION_OPTIMIZER_GUESS_V1',solver_coordinates=x.tolist(),dual_coordinates=y.tolist(),transformed_problem_sha256=h.hexdigest(),restriction='b_all0 exact bycolumnelimination; taskstart stabilizationonly');b=(json.dumps(guess,indent=2)+'\n').encode();(P/'guess.json').write_bytes(b);(P/'guess.json').chmod(0o444);result.update(error=None,active_face_count=len(active),stationarity_inf=float(np.max(np.abs(H@x+g+A.T@y))),scaled_violation=vio,b_all_exact_zero=True,whole_seconds=time.monotonic()-start,guess_identity={'path':str(P/'guess.json'),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()});(P/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='columns'}))
