import pathlib,json,hashlib,subprocess,shlex
p=pathlib.Path('/private/tmp/phase5_actual_task_metrics_runtime_draft_v1_20261011');remote=json.loads((p/'REMOTE.json').read_text())['remote']
s='''import pathlib,hashlib,json,resource,subprocess,time
p=pathlib.Path(%r);exe=p/'link-attempt1/actual_task_metrics_tests';out=p/'pure-tests-attempt1';out.mkdir(exist_ok=False)
before=hashlib.sha256(exe.read_bytes()).hexdigest()
def limits():
 resource.setrlimit(resource.RLIMIT_CPU,(10,10));resource.setrlimit(resource.RLIMIT_AS,(536870912,536870912));resource.setrlimit(resource.RLIMIT_CORE,(0,0));resource.setrlimit(resource.RLIMIT_FSIZE,(1048576,1048576))
t=time.monotonic();r=subprocess.run([str(exe)],capture_output=True,timeout=15,preexec_fn=limits,env={'PATH':'/usr/bin:/bin','LANG':'C','LC_ALL':'C','TZ':'UTC'});(out/'stdout.txt').write_bytes(r.stdout);(out/'stderr.txt').write_bytes(r.stderr);assert before==hashlib.sha256(exe.read_bytes()).hexdigest();result={'pure_test_exe_sha256':before,'exit':r.returncode,'wall_seconds':time.monotonic()-t,'Model':0,'MuJoCo_step':0,'commits':0};(out/'RESULT.json').write_text(json.dumps(result,indent=2)+'\\n');print(json.dumps(result));print(r.stdout.decode());assert r.returncode==0,r.stderr
'''%remote
x=subprocess.run(['tools/dell-ssh.sh','-T','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','DellTransfer','python3 -I -S -B -c '+shlex.quote(s)],capture_output=True,timeout=25);print(x.stdout.decode());assert x.returncode==0,x.stderr
