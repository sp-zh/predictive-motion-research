from pathlib import Path
import sys,os,json,hashlib,base64,subprocess,shlex
sys.path.insert(0,'/private/tmp');from bounded_derived_bytes53_v1 import bounded_write
O=Path('/private/tmp/root62_stop_cause_review_v1_20261016');os.environ['P5_DERIVED53_ROOT']=str(O);P=Path('/private/tmp/phase5_current_braking_nominal62_source_v3_20261016');remote=json.loads((P/'REMOTE62.json').read_text())['remote']
code='''from pathlib import Path
import os,json,base64,hashlib,datetime
root=Path(REMOTE_ROOT_SENTINEL);files=[]
for name in ['ENTRY_CONSUMED62.json','active_run_plan.json','run-attempt1/BEFORE_INPUT_IDENTITIES.json']:
 p=root/name;fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW)
 try:
  a=os.fstat(fd);assert a.st_size<=4194304;b=os.read(fd,4194305);z=os.fstat(fd);assert(a.st_ino,a.st_size,a.st_mtime_ns)==(z.st_ino,z.st_size,z.st_mtime_ns)and len(b)==a.st_size
 finally:os.close(fd)
 files.append({'path':name,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'data':base64.b64encode(b).decode()})
procs=[]
for pid in [15688,15689]:
 p=Path('/proc')/str(pid)
 if not p.exists():procs.append({'pid':pid,'exists':False});continue
 s=(p/'stat').read_text();a=s[s.rfind(')')+2:].split();procs.append({'pid':pid,'comm':(p/'comm').read_text().strip(),'state':a[0],'ppid':int(a[1]),'pgrp':int(a[2]),'session':int(a[3]),'starttime_ticks':int(a[19]),'argv':(p/'cmdline').read_bytes().decode().split('\\0')[:-1]})
print(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':files,'processes':procs}))'''
assert code.count('REMOTE_ROOT_SENTINEL')==1;code=code.replace('REMOTE_ROOT_SENTINEL',repr(remote));r=subprocess.run(['/Users/uot/Documents/ChatGPT/ros/tools/dell-ssh.sh','-T','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','DellTransfer','python3 -I -S -B -c '+shlex.quote(code)],capture_output=True,timeout=25);assert r.returncode==0,r.stderr.decode();j=json.loads(r.stdout);objects={}
for e in j['files']:
 b=base64.b64decode(e['data']);assert len(b)==e['bytes']and hashlib.sha256(b).hexdigest()==e['sha256'];objects[e['path']]=json.loads(b);bounded_write(O/('ACTUAL62_'+e['path'].replace('/','_')),b.decode())
entry=objects['ENTRY_CONSUMED62.json'];plan=objects['active_run_plan.json'];before=objects['run-attempt1/BEFORE_INPUT_IDENTITIES.json'];assert len(plan['input_files'])==1731 and len(before)==1731 and len(plan['compile_argv'])==1
assert next(e['sha256']for e in j['files']if e['path']=='active_run_plan.json')=='bc0719fb5502992fa723df239e80b8e3bd8aa1f495f4a360ddd42c32878e08a1';pins={e['requested_path']:e for e in plan['input_files']};S=P/'src-final-v2'
for p in S.iterdir():
 e=pins[remote+'/src/'+p.name];b=p.read_bytes();assert len(b)==e['bytes']and hashlib.sha256(b).hexdigest()==e['sha256']
profile=P/'profile-version1/active_input.json';argv=plan['compile_argv'][0];assert hashlib.sha256(profile.read_bytes()).hexdigest()==argv[2]=='a1945573f7b1d54e1e1d2e23583fd56e77b49ea608f7c5193a6d08f59e4932aa'and argv[3]=='b934c08f4ddf86e4034deb29fa7da08d12c5b1af287c72ae8ca26738bfa49d20'
report={'schema':'ROOT62_ACTUAL_ENTRY_PLAN_SOURCE_PROFILE_AND_PID_ORIGINAL_SSH_READBACK_V1','observed_utc':j['utc'],'entry':entry,'runtime_plan_sha256':'bc0719fb5502992fa723df239e80b8e3bd8aa1f495f4a360ddd42c32878e08a1','plan_inputs':len(pins),'before_inputs':len(before),'all91_source_bytes_equal_actual_plan':True,'profile_SHA_bound':True,'native_ELF_SHA_bound':argv[3],'processes':j['processes'],'scope':'Original SSH read-only actual entry/plan/startup-input receipts. Running process identity is a live observation, not completion. Existing online driver is not claimed detached/offline; no new entry/retry/source write or full cold IO performed by Root.'}
bounded_write(O/'ACTUAL62_ENTRY_AND_RUNNING_REVIEW.json',json.dumps(report,indent=2)+'\n');print(json.dumps(report))
