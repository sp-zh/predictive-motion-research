from pathlib import Path
import sys,os,json,datetime,hashlib
P=Path('/home/codextransfer/predictive_motion/results/phase5/session-controlled-stop-physical-braking-first-progress-direct-mac-v1-20261016-attempt65');name=sys.argv[1];assert name.startswith('PREENTRY65_')and name.endswith('.json')and '/'not in name;pre=json.loads((P/name).read_text());age=(datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(pre['utc'])).total_seconds();assert 0<=age<180 and pre['all_runtime_inputs_stable']and pre['runtime_input_count']==1743 and pre['native65_not_entered'];assert not(P/'ENTRY_CONSUMED65.json').exists()and not(P/'run-attempt1').exists()
for n,k in [('active_run_plan.json','runtime_plan_sha256'),('active_run_driver.py','driver_sha256'),('STORAGE_LAYOUT65_V1.json','layout_sha256'),('once_entry65_v1.py','entry_wrapper_sha256')]:assert hashlib.sha256((P/n).read_bytes()).hexdigest()==pre[k]
for q in Path('/proc').iterdir():
 if q.name.isdigit():
  try:assert(q/'comm').read_text().strip()!='active_first_cy','another native active'
  except OSError:pass
r={'schema':'FRESH65_PHYSICAL_BRAKING_FIRST_PROGRESS_SINGLE_USE_NATIVE_ENTRY_V1','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'driver_pid':os.getpid(),'preentry_sha256':hashlib.sha256((P/name).read_bytes()).hexdigest(),'preentry_age_seconds':age,'runtime_plan_sha256':pre['runtime_plan_sha256'],'profile_sha256':pre['profile_sha256'],'ELF_sha256':pre['ELF_sha256'],'runtime_input_count':1743,'native_attempts':1,'automatic_retries':0,'execution_mode':'ONLINE_NO_OFFLINE_SUPERVISOR_QUEUE','all64_and_prior_failures_retained':True,'scope':'Actual fresh65 only; original math/physical/SI/nonlinear/geometry/B/history/two2ms/C/stop/global counters remain; stricter physicalhot3G shares originalspent/tail. Entry is not completion/acceptance.'}
fd=os.open(P/'ENTRY_CONSUMED65.json',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o444)
with os.fdopen(fd,'w')as f:json.dump(r,f,indent=2);f.flush();os.fsync(f.fileno())
print(json.dumps(r),flush=True);os.execv('/usr/bin/python3',['/usr/bin/python3','-I','-S','-B',str(P/'active_run_driver.py'),str(P/'active_run_plan.json')])
