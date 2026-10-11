import resource,signal,time
resource.setrlimit(resource.RLIMIT_CPU,(30,30));resource.setrlimit(resource.RLIMIT_AS,(1073741824,1073741824));signal.alarm(40)
import pathlib,sys,json,hashlib,struct,os
sys.path.insert(0,'/usr/lib/python3/dist-packages');import numpy as np
R=pathlib.Path('/home/codextransfer/predictive_motion/results/phase5');old=R/'task-start-stabilization-numeric-guess-v1-20261010-repair2';P=R/'task-start-stabilization-active-set-v1-20261010';P.mkdir(exist_ok=False);q=np.load(old/'ACTUAL_STABILIZATION_INPUTS.npz');H,g,A,l,u=[q[n] for n in ['H','g','A','l','u']];ref=np.load(old/'SLSQP_REFERENCE_ONLY.npz')['x'];v=np.load(old/'POST_KKT_DIAGNOSTIC.npz');ax=A@ref;sides=[];norm=np.max(np.abs(A),axis=1)
for k in range(len(l)):
 if norm[k]<=1e-12:continue
 if abs(ax[k]-l[k])<=1e-9:sides.append((k,-1))
 if abs(ax[k]-u[k])<=1e-9:sides.append((k,1))
faces=[sides[int(i)] for i in v['active']];events=[];completed=False
for iteration in range(20):
 B=np.asarray([sign*A[k] for k,sign in faces]);rhs=np.asarray([(-l[k] if sign<0 else u[k]) for k,sign in faces]);K=np.block([[H,B.T],[B,np.zeros((len(faces),len(faces)))]]);target=np.concatenate([-g,rhs]);sol=np.linalg.solve(K,target);x=sol[:126];lam=sol[126:];ax=A@x;low=l-ax;high=ax-u;vio=np.maximum(low,high);worst=int(np.argmax(vio));event={'iteration':iteration,'faces':[list(t) for t in faces],'maximum_violation':float(vio[worst]),'worst_scaled_row':worst,'minimum_multiplier':float(lam.min()),'stationarity':float(np.max(np.abs(H@x+g+B.T@lam)))};events.append(event)
 with (P/'ITERATION_APPEND.jsonl').open('a') as f:f.write(json.dumps(event)+'\n');f.flush();os.fsync(f.fileno())
 np.savez(P/'LATEST_DIAGNOSTIC.npz',x=x,lambda_faces=lam,K=K,rhs=target,faces=np.asarray(faces))
 if lam.min()<0:faces.pop(int(np.argmin(lam)));continue
 if vio[worst]<=1e-12:completed=True;break
 face=(worst,-1 if low[worst]>high[worst] else 1);assert face not in faces;faces.append(face)
assert completed and np.isfinite(x).all() and np.isfinite(lam).all();y=np.zeros(len(l))
for w,(k,sign) in zip(lam,faces):y[k]+=sign*w
np.savez(P/'NUMERICAL_GUESS_ONLY.npz',primal_x=x,dual_y=y);h=hashlib.sha256()
for a in [H,g,A,l,u]:
 for n in a.shape:h.update(struct.pack('<Q',n))
 h.update(np.asarray(a,dtype='<f8').tobytes(order='C'))
guess=json.loads((R/'task-start-numeric-guess-v1-20261010/guess.json').read_text());guess.update(schema='TASK_START_B_ZERO_STABILIZATION_OPTIMIZER_GUESS_V1',solver_coordinates=x.tolist(),dual_coordinates=y.tolist(),transformed_problem_sha256=h.hexdigest(),restriction='b_all0 exact bycommandcolumnselection, taskstartstabilizationonly');b=(json.dumps(guess,indent=2)+'\n').encode();(P/'guess.json').write_bytes(b);(P/'guess.json').chmod(0o444);result={'schema':'BOUNDED_STABILIZATION_ACTIVE_SET_NUMERIC_GUESS_V1','scope':'numericguessonly, notcandidate/permit; originalgates remain','events':events,'completed':completed,'scaled_violation':float(np.max(np.maximum.reduce([l-A@x,A@x-u,np.zeros(len(l))]))),'stationarity':float(np.max(np.abs(H@x+g+A.T@y))),'guess_identity':{'path':str(P/'guess.json'),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()},'Model':0,'physical_steps':0,'task_commits':0};(P/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
