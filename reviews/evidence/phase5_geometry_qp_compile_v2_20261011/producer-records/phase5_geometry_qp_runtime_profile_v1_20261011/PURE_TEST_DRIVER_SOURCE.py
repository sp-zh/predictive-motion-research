from pathlib import Path
import json,shlex,subprocess
D=Path('/private/tmp/phase5_dynamic_session_active_v1_20261011');remote=json.loads((D/'REMOTE.json').read_text())['remote'];ssh=['tools/dell-ssh.sh','-T','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','DellTransfer']
s='''import pathlib,hashlib,json,resource,subprocess,time,sys,struct
p=pathlib.Path(%r);out=p/'pure-tests-attempt1';out.mkdir(exist_ok=False);sys.path.insert(0,'/usr/lib/python3/dist-packages');import numpy as np
source=pathlib.Path('/home/codextransfer/predictive_motion/results/phase5/pilot-inputtrust-numeric-guess-v2-20261010/ACTUAL_INPUTTRUST_INPUTS.npz');before=hashlib.sha256(source.read_bytes()).hexdigest();arrays=np.load(source)
with (out/'actual_guarded_numeric_input.bin').open('xb') as f:
 for name in ['H','g','A','l','u']:
  a=arrays[name];assert np.isfinite(a).all()
  for n in a.shape:f.write(struct.pack('<Q',n))
  f.write(np.asarray(a,dtype='<f8').tobytes(order='C'))
def limits():
 resource.setrlimit(resource.RLIMIT_CPU,(30,30));resource.setrlimit(resource.RLIMIT_AS,(536870912,536870912));resource.setrlimit(resource.RLIMIT_CORE,(0,0));resource.setrlimit(resource.RLIMIT_FSIZE,(2097152,2097152))
records=[]
for name in ['cycle_support_tests','current_numeric_tests','current_numeric_oracle']:
 exe=p/'link-attempt1'/name;sha=hashlib.sha256(exe.read_bytes()).hexdigest();args=[str(exe)]+([str(out/'actual_guarded_numeric_input.bin')] if name.endswith('oracle') else []);t=time.monotonic();r=subprocess.run(args,capture_output=True,timeout=35,preexec_fn=limits,env={'PATH':'/usr/bin:/bin','LANG':'C','LC_ALL':'C','TZ':'UTC'});assert len(r.stdout)<=2097152 and len(r.stderr)<=2097152;(out/(name+'.stdout')).write_bytes(r.stdout);(out/(name+'.stderr')).write_bytes(r.stderr);assert sha==hashlib.sha256(exe.read_bytes()).hexdigest();records.append({'name':name,'exit':r.returncode,'exe_sha256':sha,'seconds':time.monotonic()-t});(out/'RESULT_PREFIX.json').write_text(json.dumps(records,indent=2)+'\\n');print(name,r.returncode,r.stdout.decode().splitlines()[0] if r.stdout else r.stderr.decode());
 if r.returncode!=0:break
assert before==hashlib.sha256(source.read_bytes()).hexdigest()
result={'records':records,'source_sha256':before,'Model':0,'physical_steps':0,'commits':0,'all_passed':len(records)==3 and all(x['exit']==0 for x in records)}
if result['all_passed']:
 lines=(out/'current_numeric_oracle.stdout').read_text().splitlines();x=np.array([float(v) for v in next(s for s in lines if s.startswith('primal,')).split(',')[1:]]);y=np.array([float(v) for v in next(s for s in lines if s.startswith('dual,')).split(',')[1:]]);H,g,A,l,u=[arrays[k] for k in ['H','g','A','l','u']];ax=A@x;stat=float(np.max(np.abs(H@x+g+A.T@y)));vio=float(np.max(np.maximum.reduce([l-ax,ax-u,np.zeros(len(l))])));U=arrays['p']+arrays['Z']@(arrays['D']*x);result.update(independent_numpy_stationarity_inf=stat,independent_numpy_scaled_violation=vio,original_alpha_max=float(np.max(np.abs(U[arrays['guard_original_columns']]))));np.savez(out/'ACTUAL_NUMERIC_HINT.npz',x=x,y=y,U=U);assert stat<=1e-10 and vio<=1e-12 and result['original_alpha_max']<=.001
(out/'RESULT.json').write_text(json.dumps(result,indent=2)+'\\n');print(json.dumps(result));assert result['all_passed']
'''%remote
x=subprocess.run(ssh+['python3 -I -B -c '+shlex.quote(s)],capture_output=True,timeout=60);print(x.stdout.decode());assert x.returncode==0,x.stderr
