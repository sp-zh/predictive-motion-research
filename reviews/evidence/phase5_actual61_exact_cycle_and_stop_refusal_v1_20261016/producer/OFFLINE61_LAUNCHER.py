from pathlib import Path
import subprocess,json,os,hashlib,datetime,sys,time
p=Path('/home/codextransfer/predictive_motion/results/phase5/session-controlled-stop-exact-cycle-endpoint-active32-brake64-dwell25-v1-20261016-attempt61');pre=json.loads((p/'PREENTRY61_V1.json').read_text());assert pre['all_identities_stable']and pre['native_not_entered']and pre['runtime_distinct_input_count']==1728;age=(datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(pre['utc'])).total_seconds();assert 0<=age<180,'fresh actual resources/inputs required before sole entry';assert not(p/'ENTRY_CONSUMED61.json').exists()and not(p/'run-attempt1').exists()and not(p/'offline61-status').exists()
plan=p/'active_run_plan.json';driver=p/'active_run_driver.py';sup=p/'offline61_supervisor.py'
for file,key in [(plan,'runtime_plan_actual_sha256'),(driver,'driver_sha256'),(sup,'supervisor_sha256'),(p/'STORAGE_LAYOUT61_V1.json','storage_layout_sha256'),(p/'capture_terminal61.py','capture_sha256')]:assert hashlib.sha256(file.read_bytes()).hexdigest()==pre[key]
active=[]
for q in Path('/proc').iterdir():
 if q.name.isdigit():
  try:
   if(q/'comm').read_text().strip()=='active_first_cy':active.append(q.name)
  except OSError:pass
assert not active
intent={'schema':'FRESH61_SINGLE_USE_DETACHED_LOCAL_ENTRY_V1','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'launcher_pid':os.getpid(),'launcher_sid':os.getsid(0),'runtime_distinct_inputs':1728,'runtime_plan_sha256':pre['runtime_plan_actual_sha256'],'profile_sha256':pre['profile_sha256'],'ELF_sha256':pre['ELF_sha256'],'supervisor_sha256':pre['supervisor_sha256'],'preentry_file':str(p/'PREENTRY61_V1.json'),'preentry_sha256':hashlib.sha256((p/'PREENTRY61_V1.json').read_bytes()).hexdigest(),'preentry_age_seconds':age,'entry_attempts':1,'retries':0,'scope':'One fresh61 finite local development batch after37compile26link25pure/8saved6active/originalgates/actualCIM/allpins stable. No consumed run replay/expanded caps/model modification/hardware/formalholdout/main/scorer/phase release. Terminal MANUAL_WAIT_AFTER_61 requires directhuman resume; network/automatic messages do not resume.'}
fd=os.open(p/'ENTRY_CONSUMED61.json',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o444)
with os.fdopen(fd,'w')as f:json.dump(intent,f,indent=2);f.flush();os.fsync(f.fileno())
args=['/usr/bin/python3','-I','-S','-B',str(sup),'--driver',str(driver),'--driver-sha256',pre['driver_sha256'],'--plan',str(plan),'--plan-sha256',pre['runtime_plan_actual_sha256'],'--status-directory',str(p/'offline61-status'),'--wall-seconds','3600','--output-bytes','6845104128']
with(p/'offline61-supervisor.stdout').open('xb')as out,(p/'offline61-supervisor.stderr').open('xb')as err:child=subprocess.Popen(args,stdin=subprocess.DEVNULL,stdout=out,stderr=err,start_new_session=True,close_fds=True,cwd=p,env={'PATH':'/usr/bin:/bin','LANG':'C','LC_ALL':'C','TZ':'UTC'})
s=(Path('/proc')/str(child.pid)/'stat').read_text();fields=s[s.rfind(')')+2:].split();rec={'schema':'FRESH61_LOCAL_SUPERVISOR_POPENCLOSE_LAUNCH_V1','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'supervisor_pid':child.pid,'supervisor_ppid_initial':int(fields[1]),'supervisor_pgid':int(fields[2]),'supervisor_sid':int(fields[3]),'supervisor_start_ticks':int(fields[19]),'launcher_pid':os.getpid(),'launcher_sid':os.getsid(0),'new_session':int(fields[3])==child.pid,'stdin':'DEVNULL','stdout':'local regular file','stderr':'local regular file','close_fds':True,'ssh_detach_survival':'NOT_YET_OBSERVED','program_attempts':1,'automatic_retries':0,'post_batch':'MANUAL_WAIT_DIRECT_HUMAN_RESUME'};assert rec['new_session']
with(p/'OFFLINE61_LAUNCH.json').open('x')as f:json.dump(rec,f,indent=2);f.flush();os.fsync(f.fileno())
print(json.dumps(rec),flush=True)
