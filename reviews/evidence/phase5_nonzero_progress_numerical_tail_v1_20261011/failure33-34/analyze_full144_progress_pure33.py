from pathlib import Path
import json,subprocess,shlex
D=Path('/private/tmp/phase5_nonzero_progress_active_v1_20261011');remote=json.loads((D/'REMOTE.json').read_text())['remote']
s='''from pathlib import Path
import os,resource,signal,json,hashlib
resource.setrlimit(resource.RLIMIT_CPU,(30,30));resource.setrlimit(resource.RLIMIT_AS,(536870912,536870912));signal.alarm(40);os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='1'
import numpy as np
p=Path(%r)/'pure144-fixture-v2';a=np.load(p/'INPUTS.npz');before={n:hashlib.sha256((p/n).read_bytes()).hexdigest() for n in ['INPUTS.npz','oracle.stdout']};lines=(p/'oracle.stdout').read_text().splitlines();x=np.array([float(v) for v in next(s for s in lines if s.startswith('primal,')).split(',')[1:]]);y=np.array([float(v) for v in next(s for s in lines if s.startswith('dual,')).split(',')[1:]]);U=a['p']+a['Z']@(a['D']*x);Ax=a['A']@x;fullAx=a['originalA']@U;stat=float(np.max(np.abs(a['H']@x+a['g']+a['A'].T@y)));vio=float(np.max(np.maximum.reduce([a['l']-Ax,Ax-a['u'],np.zeros(len(Ax))])));fullvio=float(np.max(np.maximum.reduce([a['originall']-fullAx,fullAx-a['originalu'],np.zeros(len(fullAx))])));alpha=U.reshape(20,8)[:,:7];b=U.reshape(20,8)[:,7];jerk=np.diff(np.r_[0.,b])/.004;s=r=0.;minimum_s=minimum_r=0.;maximum_s=maximum_r=0.;progress_failures=[];macro=0
for k,count in enumerate([1,1,2,2,3,3,4,4,5,5,6,6,8,10,12,16,20,24,28,40]):
 origin_s,origin_r=s,r
 for t in range(count):
  for half in [1,2]:
   dt=.004*t+.002*half;sh=origin_s+dt*origin_r+.5*dt*dt*b[k];rh=origin_r+dt*b[k];minimum_s=min(minimum_s,sh);minimum_r=min(minimum_r,rh);maximum_s=max(maximum_s,sh);maximum_r=max(maximum_r,rh)
   if sh<0 or sh>1 or rh<0 or rh>.2:progress_failures.append({'cell':k,'cycle':t,'half':half,'s':float(sh),'r':float(rh),'kind':'halfprogress strict'})
  ns=s+.004*r+.5*.004*.004*b[k];nr=r+.004*b[k];s,r=ns,nr;macro+=1
  if s<0 or s>1 or r<0 or r>.2:progress_failures.append({'cell':k,'cycle':t,'s':float(s),'r':float(r),'kind':'recursiveprogress strict'})
result={'scaled_stationarity_inf':stat,'scaled_violation':vio,'all14756_original_SI_violation':fullvio,'original_alpha_max':float(np.max(np.abs(alpha))),'progress_b':b.tolist(),'progress_jerk_absmax':float(np.max(np.abs(jerk))),'first_commit_s':float(.5*.004*.004*b[0]),'first_commit_r':float(.004*b[0]),'horizon_s':float(s),'horizon_r':float(r),'halfprogress_ranges':[float(minimum_s),float(maximum_s),float(minimum_r),float(maximum_r)],'strict_progress_failures':progress_failures,'scope':'archived30 initial144 hint only; nativeOSQP/strictcommand/B/C/actualnewtaskmetrics not run','Model':0,'MuJoCo_step':0};np.savez(p/'HINT.npz',x=x,y=y,U=U);(p/'ANALYSIS.json').write_text(json.dumps(result,indent=2)+'\\n');assert before=={n:hashlib.sha256((p/n).read_bytes()).hexdigest() for n in before};print(json.dumps(result));assert stat<=1e-10 and vio<=1e-12 and fullvio<=1e-7 and np.max(np.abs(alpha))<=.001 and np.max(np.abs(jerk))<=4.9995
'''%remote
x=subprocess.run(['tools/dell-ssh.sh','-T','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','DellTransfer','python3 -I -B -c '+shlex.quote(s)],capture_output=True,timeout=45);print(x.stdout.decode());assert x.returncode==0,x.stderr
