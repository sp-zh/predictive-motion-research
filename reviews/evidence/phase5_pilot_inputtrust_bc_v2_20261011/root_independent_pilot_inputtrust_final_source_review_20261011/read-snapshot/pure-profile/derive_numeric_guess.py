import resource,signal,time
started=time.monotonic();resource.setrlimit(resource.RLIMIT_CPU,(55,55));resource.setrlimit(resource.RLIMIT_AS,(2147483648,2147483648));resource.setrlimit(resource.RLIMIT_FSIZE,(33554432,33554432));resource.setrlimit(resource.RLIMIT_CORE,(0,0));signal.alarm(60)
import pathlib,sys,json,hashlib,struct,os
sys.path.insert(0,'/usr/lib/python3/dist-packages');import numpy as np
from scipy.optimize import minimize,LinearConstraint,nnls
R=pathlib.Path('/home/codextransfer/predictive_motion/results/phase5');P=R/'pilot-inputtrust-numeric-guess-v2-20261010';P.mkdir(exist_ok=False)
result={'schema':'PILOT_INPUTTRUST_PURE_OPTIMIZER_GUESS_V1','stage':'BEFORE_INPUT','Model':0,'physical_steps':0,'commits':0,'solver_alpha_guard':.000999,'strict_alpha_guard':.001}
(P/'RESULT_PREFIX.json').write_text(json.dumps(result,indent=2)+'\n')
before=None;sdk=[];files=[]
try:
 files=[R/'task-start-stabilization-numeric-guess-v1-20261010-repair2/ACTUAL_STABILIZATION_INPUTS.npz',R/'task-start-linear-oracle-v2-20261010-attempt1/oracle-artifacts-attempt1/ACTUAL_ORACLE_INPUTS.npz',R/'task-start-numeric-guess-v1-20261010/guess.json'];before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files};(P/'BEFORE_INPUTS.json').write_text(json.dumps(before,indent=2)+'\n');sdk=[]
 for root in [pathlib.Path('/usr/lib/python3/dist-packages/numpy'),pathlib.Path('/usr/lib/python3/dist-packages/scipy')]:
  for z in sorted(root.rglob('*')):
   if z.is_file() and z.suffix in ['.py','.so']:sdk.append((str(z),hashlib.sha256(z.read_bytes()).hexdigest()))
 assert len(sdk)<=5000;(P/'SDK_BEFORE.json').write_text(json.dumps(sdk)+'\n')
 a=np.load(files[0]);original=np.load(files[1]);H,g,A0,l0,u0=[a[n].copy() for n in ['H','g','A','l','u']];cols=a['columns'];expected=np.array([k*8+j for k in range(18) for j in range(7)],dtype=np.int64);assert np.array_equal(cols,expected);assert H.shape==(126,126) and A0.shape==(6211,126);selected=[original['H'][np.ix_(expected,expected)],original['g'][expected],original['A'][:,expected],original['l'],original['u']];assert all(x.shape==y.shape and x.dtype==y.dtype and x.tobytes(order='C')==y.tobytes(order='C') for x,y in zip([H,g,A0,l0,u0],selected));assert original['Z'].shape==(160,144) and original['D'].shape==(144,) and original['p'].shape==(160,);result['literal_base_selection_verified']=True;Z=original['Z'][:,cols];D=original['D'][cols];p=original['p'];alpha_columns=np.array([k*8+j for k in range(20) for j in range(7)]);unscaled=Z[alpha_columns].copy();values=unscaled*D[None,:];multipliers=1/np.maximum(1,np.max(np.abs(values),axis=1));guard_A=multipliers[:,None]*values;guard_l=multipliers*(-.000999-p[alpha_columns]);guard_u=multipliers*(.000999-p[alpha_columns]);A=np.vstack([A0,guard_A]);l=np.concatenate([l0,guard_l]);u=np.concatenate([u0,guard_u]);assert A.shape==(6351,126) and np.isfinite(A).all();np.savez(P/'ACTUAL_INPUTTRUST_INPUTS.npz',H=H,g=g,A=A,l=l,u=u,Z=Z,D=D,p=p,guard_original_columns=alpha_columns,guard_multiplier=multipliers)
 result.update(stage='BEFORE_BOUNDED_SLSQP',n=126,m=6351,original_rows=6211,additional_guard_rows=140,max_iterations=500);(P/'RESULT_PREFIX.json').write_text(json.dumps(result,indent=2)+'\n')
 def callback(x):
  if time.monotonic()-started>48:raise TimeoutError('bounded pureinputtrust')
  with (P/'SLSQP_ITERATIONS.jsonl').open('a') as f:f.write(json.dumps({'elapsed':time.monotonic()-started,'max_scaled_violation':float(np.max(np.maximum.reduce([l-A@x,A@x-u,np.zeros(len(l))])))})+'\n');f.flush();os.fsync(f.fileno())
 solver_start=time.monotonic();opt=minimize(lambda x:.5*x@H@x+g@x,np.zeros(126),jac=lambda x:H@x+g,method='SLSQP',constraints=[LinearConstraint(A,l,u)],callback=callback,options={'maxiter':500,'ftol':1e-12});result.update(slsqp_success=bool(opt.success),slsqp_status=int(opt.status),slsqp_message=str(opt.message),slsqp_iterations=int(opt.nit),slsqp_elapsed_seconds=time.monotonic()-solver_start);np.savez(P/'SLSQP_REFERENCE_ONLY.npz',x=opt.x);assert opt.success
 x=opt.x;ax=A@x;norm=np.max(np.abs(A),axis=1);sides=[];vectors=[]
 for k in range(len(l)):
  if norm[k]<=1e-12:continue
  if abs(ax[k]-l[k])<=1e-9:sides.append((k,-1));vectors.append(-A[k])
  if abs(ax[k]-u[k])<=1e-9:sides.append((k,1));vectors.append(A[k])
 assert 0<len(sides)<=3000;M=np.asarray(vectors).T;weights,residual=nnls(M,-(H@x+g),maxiter=20000);active=np.flatnonzero(weights>0);faces=[sides[i] for i in active];assert 0<len(faces)<=126;completed=False;events=[]
 for iteration in range(20):
  if time.monotonic()-started>50:raise TimeoutError('bounded activeface refinement')
  B=np.asarray([sign*A[k] for k,sign in faces]);rhs=np.asarray([(-l[k] if sign<0 else u[k]) for k,sign in faces]);K=np.block([[H,B.T],[B,np.zeros((len(faces),len(faces)))]]);target=np.concatenate([-g,rhs]);sol=np.linalg.solve(K,target);x=sol[:126];lam=sol[126:];ax=A@x;low=l-ax;high=ax-u;violation=np.maximum(low,high);worst=int(np.argmax(violation));event={'iteration':iteration,'faces':faces,'max_scaled_violation':float(violation[worst]),'worst_row':worst,'minimum_multiplier':float(lam.min()),'stationarity_inf':float(np.max(np.abs(H@x+g+B.T@lam)))};events.append(event)
  with (P/'ACTIVE_FACE_ITERATIONS.jsonl').open('a') as f:f.write(json.dumps(event)+'\n');f.flush();os.fsync(f.fileno())
  np.savez(P/'LATEST_KKT_DIAGNOSTIC.npz',K=K,rhs=target,solution=sol,faces=np.asarray(faces))
  if lam.min()<0:faces.pop(int(np.argmin(lam)));continue
  if violation[worst]<=1e-12:completed=True;break
  face=(worst,-1 if low[worst]>high[worst] else 1);assert face not in faces;faces.append(face)
 assert completed and np.isfinite(x).all();y=np.zeros(6351)
 for w,(k,sign) in zip(lam,faces):y[k]+=sign*w
 U=p+Z@(D*x);assert np.all(np.abs(U[alpha_columns])<=.001) and all(U[k*8+7]==0 for k in range(20));np.savez(P/'NUMERICAL_GUESS_ONLY.npz',primal_x=x,dual_y=y,originalU=U)
 h=hashlib.sha256()
 for v in [H,g,A,l,u]:
  for n in v.shape:h.update(struct.pack('<Q',n))
  h.update(np.asarray(v,dtype='<f8').tobytes(order='C'))
 guess=json.loads(files[2].read_text());guess.update(schema='TASK_START_B_ZERO_INPUT_TRUST_OPTIMIZER_GUESS_V1',solver_coordinates=x.tolist(),dual_coordinates=y.tolist(),transformed_problem_sha256=h.hexdigest(),solver_alpha_guard=.000999,strict_alpha_guard=.001,restriction='additional140originalalpha coordinateguardrows+betaall0; optimizerguessonly notcontrols/candidate');data=(json.dumps(guess,indent=2)+'\n').encode();assert len(data)<=512*1024;(P/'guess.json').write_bytes(data);(P/'guess.json').chmod(0o444)
 after={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files};assert before==after;(P/'AFTER_INPUTS.json').write_text(json.dumps(after,indent=2)+'\n');sdk_after=[(p,hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()) for p,h in sdk];assert sdk_after==sdk;(P/'SDK_AFTER.json').write_text(json.dumps(sdk_after)+'\n');result.update(stage='PURE_INPUTTRUST_GUESS_COMPLETE_NOT_CANDIDATE',bindings_valid=True,events=events,whole_seconds=time.monotonic()-started,nnls_residual_l2=float(residual),scaled_violation=float(np.max(np.maximum.reduce([l-A@x,A@x-u,np.zeros(len(l))]))),stationarity_inf=float(np.max(np.abs(H@x+g+A.T@y))),dual_shape=6351,alpha_original_max=float(np.max(np.abs(U[alpha_columns]))),transformed_problem_sha256=h.hexdigest(),guess_identity={'path':str(P/'guess.json'),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()},error=None)
except Exception as e:result.update(stage='RETAINED_PURE_INPUTTRUST_FAILURE',error=type(e).__name__+': '+str(e),whole_seconds=time.monotonic()-started,bindings_valid=False)
# Best-effort input/SDK guards also on ordinary failure; signals/CPU kill may
# skip this, in which case the external1350-pin driver retains the boundary.
for label,expected_rows in [('INPUTS',before),('SDK',dict(sdk) if sdk else None)]:
 try:
  if expected_rows is None:raise RuntimeError('before guard unavailable')
  observed={name:hashlib.sha256(pathlib.Path(name).read_bytes()).hexdigest() for name in expected_rows};(P/('FINAL_'+label+'_CHECK.json')).write_text(json.dumps({'passed':observed==expected_rows,'observed':observed},indent=2)+'\n')
  if observed!=expected_rows:result.update(bindings_valid=False,error='final '+label+' input identity drift',stage='RETAINED_PURE_INPUTTRUST_FAILURE')
 except Exception as e:
  (P/('FINAL_'+label+'_CHECK.json')).write_text(json.dumps({'passed':False,'error':type(e).__name__+': '+str(e)})+'\n');result['bindings_valid']=False
result['whole_seconds']=time.monotonic()-started
(P/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if not result.get('bindings_valid',False):raise SystemExit(1)

