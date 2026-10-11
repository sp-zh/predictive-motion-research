from pathlib import Path
import json,subprocess,shlex
D=Path('/private/tmp/phase5_full144_ieee_pure_active_v1_20261011');remote=json.loads((D/'REMOTE.json').read_text())['remote']
s='''from pathlib import Path
import json,resource,subprocess,time,hashlib,os
p=Path(%r);o=p/'original-fixture-v1';ready=json.loads((o/'READY.json').read_text());exe=p/'build-attempt1/progress_numeric_forensics';input=o/'original_input.bin';before={str(q):hashlib.sha256(q.read_bytes()).hexdigest() for q in [exe,input]};assert before[str(input)]==ready['original_input_sha256'];assert not(o/'RESULT.json').exists()
def limits():
 resource.setrlimit(resource.RLIMIT_CPU,(30,30));resource.setrlimit(resource.RLIMIT_AS,(536870912,536870912));resource.setrlimit(resource.RLIMIT_CORE,(0,0));resource.setrlimit(resource.RLIMIT_FSIZE,(1048576,1048576))
t=time.monotonic();r=subprocess.run([str(exe),str(input)],capture_output=True,timeout=35,preexec_fn=limits,env={'PATH':'/usr/bin:/bin','LANG':'C','LC_ALL':'C','TZ':'UTC','OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1'});assert len(r.stdout)<=1048576 and len(r.stderr)<=1048576;(o/'oracle.stdout').write_bytes(r.stdout);(o/'oracle.stderr').write_bytes(r.stderr);assert before=={str(q):hashlib.sha256(q.read_bytes()).hexdigest() for q in [exe,input]};result={'exit':r.returncode,'wall_s':time.monotonic()-t,'first_line':r.stdout.decode().splitlines()[0] if r.stdout else r.stderr.decode(),'input_and_exe_hashes':before,'native_OSQP':0,'Model':0,'Scene':0,'MuJoCo_step':0,'scope':'One pure Eigen original saved30 14756QP full144 reconstruction/hint/strictprogress; no new33genuine forecast/controller proof'};(o/'RESULT.json').write_text(json.dumps(result,indent=2)+'\\n');print(json.dumps(result))
'''
x=subprocess.run(['tools/dell-ssh.sh','-T','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','DellTransfer','python3 -I -S -B -c '+shlex.quote(s%remote)],capture_output=True,timeout=45);print(x.stdout.decode());assert x.returncode==0,x.stderr
