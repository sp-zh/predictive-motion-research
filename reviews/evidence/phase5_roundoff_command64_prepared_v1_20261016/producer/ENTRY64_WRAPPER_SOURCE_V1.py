from pathlib import Path
import sys,json,hashlib,datetime,os
x=json.load(sys.stdin);p=Path(x['remote']);pre=json.loads((p/'PREENTRY64_V1.json').read_text());age=(datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(pre['utc'])).total_seconds();assert 0<=age<180;assert pre['all_identities_stable']and pre['runtime_distinct_input_count']==1737 and pre['execution_mode']=='ONLINE_ACTIVE_DEVELOPMENT_NO_OFFLINE_SUPERVISOR_QUEUE';assert not(p/'run-attempt1').exists()and not(p/'ENTRY_CONSUMED64.json').exists()
for n,k in [('active_run_plan.json','runtime_plan_actual_sha256'),('active_run_driver.py','driver_sha256'),('STORAGE_LAYOUT64_FINAL_V1.json','storage_layout_sha256'),('capture_terminal64.py','capture_sha256')]:assert hashlib.sha256((p/n).read_bytes()).hexdigest()==pre[k]
active=[]
for q in Path('/proc').iterdir():
 if q.name.isdigit():
  try:
   if(q/'comm').read_text().strip()=='active_first_cy':active.append(q.name)
  except OSError:pass
assert not active
with(p/'LOCAL_ENTRY_INTENT64.json').open('x')as f:json.dump(x['intent'],f,indent=2);f.flush();os.fsync(f.fileno())
r={'schema':'FRESH64_ROUNDOFF_COMMAND_SINGLE_USE_NATIVE_ENTRY_V1','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'driver_pid':os.getpid(),'runtime_plan_sha256':pre['runtime_plan_actual_sha256'],'runtime_distinct_inputs':1737,'profile_sha256':pre['profile_sha256'],'ELF_sha256':pre['ELF_sha256'],'preentry_actual_sha256':hashlib.sha256((p/'PREENTRY64_V1.json').read_bytes()).hexdigest(),'preentry_age_seconds':age,'storage_layout_sha256':pre['storage_layout_sha256'],'capture_sha256':pre['capture_sha256'],'earlier63_consumed_failure_preserved':True,'native_attempts':1,'automatic_retries':0,'execution_mode':'ONLINE_NO_OFFLINE_SUPERVISOR_QUEUE','scope':'Fresh64 after40compile29link28pure18formal46corebyteexact and10newpolicy cases. No original numeric512/10s/16384/745K/1.8B/24slot/12Graw6Gstored32Mtail or physical/stop expansion. New current-history guard is planning subset only; genuine newModel/nativeSOLVED/SI/B400/two2ms/C/stop all mandatory. No hardware/heldout/main/scorer/research acceptance.'}
fd=os.open(p/'ENTRY_CONSUMED64.json',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o444)
with os.fdopen(fd,'w')as f:json.dump(r,f,indent=2);f.flush();os.fsync(f.fileno())
print(json.dumps(r),flush=True);os.execv('/usr/bin/python3',['/usr/bin/python3','-I','-S','-B',str(p/'active_run_driver.py'),str(p/'active_run_plan.json')])
