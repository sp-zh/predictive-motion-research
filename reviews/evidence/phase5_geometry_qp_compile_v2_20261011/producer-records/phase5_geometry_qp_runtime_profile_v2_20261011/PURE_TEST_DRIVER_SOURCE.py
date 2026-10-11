import pathlib,json,subprocess,shlex
D=pathlib.Path('/private/tmp/phase5_geometry_qp_session_active_v2_20261011');remote=json.loads((D/'REMOTE.json').read_text())['remote']
s='''import pathlib,json,hashlib,resource,subprocess,time
p=pathlib.Path(%r);out=p/'pure-tests-attempt1';out.mkdir(exist_ok=False);records=[]
def limits():
 resource.setrlimit(resource.RLIMIT_CPU,(10,10));resource.setrlimit(resource.RLIMIT_AS,(536870912,536870912));resource.setrlimit(resource.RLIMIT_CORE,(0,0));resource.setrlimit(resource.RLIMIT_FSIZE,(1048576,1048576))
for name in ['owner_binding_tests','cycle_support_tests','current_numeric_tests']:
 exe=p/'link-attempt1'/name;digest=hashlib.sha256(exe.read_bytes()).hexdigest();t=time.monotonic();r=subprocess.run([str(exe)],capture_output=True,timeout=15,preexec_fn=limits,env={'PATH':'/usr/bin:/bin','LANG':'C','LC_ALL':'C','TZ':'UTC'});(out/(name+'.stdout.txt')).write_bytes(r.stdout);(out/(name+'.stderr.txt')).write_bytes(r.stderr);assert digest==hashlib.sha256(exe.read_bytes()).hexdigest();rec={'name':name,'exe_sha256':digest,'exit':r.returncode,'wall_seconds':time.monotonic()-t,'actual_Session':0,'Model':0,'MuJoCo_step':0,'commits':0};records.append(rec);(out/'RESULT.json').write_text(json.dumps({'records':records,'complete':False},indent=2)+'\\n');print(json.dumps(rec));print(r.stdout.decode());assert r.returncode==0,r.stderr
(out/'RESULT.json').write_text(json.dumps({'records':records,'complete':True,'scope':'Pure codecs and arithmetic only; owner test lacks explicit weak.expired assertion; no actual foreign SDK Session negative control'},indent=2)+'\\n')
'''%remote
x=subprocess.run(['tools/dell-ssh.sh','-T','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','DellTransfer','python3 -I -S -B -c '+shlex.quote(s)],capture_output=True,timeout=55);print(x.stdout.decode());assert x.returncode==0,x.stderr
