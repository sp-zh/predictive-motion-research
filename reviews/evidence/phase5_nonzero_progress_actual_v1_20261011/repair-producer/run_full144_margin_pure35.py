from pathlib import Path
import json,subprocess,shlex
D=Path('/private/tmp/phase5_full144_margin_pure_active_v1_20261011');remote=json.loads((D/'REMOTE.json').read_text())['remote']
s='''from pathlib import Path
import json,resource,subprocess,time,hashlib
p=Path(%r);out=p/'pure-margin-cases-v1';out.mkdir(exist_ok=False);exe=p/'build-attempt1/progress_numeric_forensics';input=Path('/home/codextransfer/predictive_motion/results/phase5/full144-ieee-terminal-pure-v1-20261011-attempt34/original-fixture-v1/original_input.bin');before={str(q):hashlib.sha256(q.read_bytes()).hexdigest() for q in [exe,input]};assert before[str(input)]=='896943953327260fdf3c7dbc1f337b90e2d4a013bf6a8fa28c37f1d43d32139c'
def limits():
 resource.setrlimit(resource.RLIMIT_CPU,(30,30));resource.setrlimit(resource.RLIMIT_AS,(536870912,536870912));resource.setrlimit(resource.RLIMIT_CORE,(0,0));resource.setrlimit(resource.RLIMIT_FSIZE,(1048576,1048576))
records=[]
for name,delta in [('zero','0'),('reduced','1e-18'),('planning','1e-13')]:
 t=time.monotonic();r=subprocess.run([str(exe),str(input),delta],capture_output=True,timeout=35,preexec_fn=limits,env={'PATH':'/usr/bin:/bin','LANG':'C','LC_ALL':'C','TZ':'UTC'});assert len(r.stdout)<=1048576 and len(r.stderr)<=1048576;(out/(name+'.stdout')).write_bytes(r.stdout);(out/(name+'.stderr')).write_bytes(r.stderr);assert before=={str(q):hashlib.sha256(q.read_bytes()).hexdigest() for q in [exe,input]};lines=r.stdout.decode().splitlines();rec={'name':name,'delta_argument':delta,'exit':r.returncode,'wall_s':time.monotonic()-t,'first_line':lines[0] if lines else r.stderr.decode(),'terminal_line':lines[-1] if lines else '', 'hashes':before};records.append(rec);(out/'RESULT_PREFIX.json').write_text(json.dumps(records,indent=2)+'\\n');print(json.dumps(rec))
(out/'RESULT.json').write_text(json.dumps({'records':records,'complete':True,'pure_process_dispatches':3,'scope':'saved30 firstfullQP; all200 literal+400cellrefs; no newModel/B/C/physics/controller','Model':0,'Scene':0,'native_OSQP':0,'MuJoCo_step':0},indent=2)+'\\n')
'''%remote
x=subprocess.run(['tools/dell-ssh.sh','-T','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','DellTransfer','python3 -I -S -B -c '+shlex.quote(s)],capture_output=True,timeout=60);print(x.stdout.decode());assert x.returncode==0,x.stderr
