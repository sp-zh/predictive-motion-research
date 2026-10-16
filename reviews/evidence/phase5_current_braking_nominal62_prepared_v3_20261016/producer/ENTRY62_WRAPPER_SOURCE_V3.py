from pathlib import Path
import sys,json,hashlib,datetime,os
context=json.load(sys.stdin);p=Path(context['remote']);pre=json.loads((p/'PREENTRY62_V3.json').read_text());age=(datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(pre['utc'])).total_seconds();assert 0<=age<180,'fresh preentry required before sole unconsumed entry';assert pre['all_identities_stable']and pre['runtime_distinct_input_count']==1731 and pre['execution_mode']=='ONLINE_ACTIVE_DEVELOPMENT_NO_OFFLINE_SUPERVISOR_QUEUE';assert not(p/'ENTRY_CONSUMED62.json').exists()and not(p/'run-attempt1').exists()
for name,key in [('active_run_plan.json','runtime_plan_actual_sha256'),('active_run_driver.py','driver_sha256'),('STORAGE_LAYOUT62_V3.json','storage_layout_sha256'),('capture_terminal62.py','capture_sha256')]:assert hashlib.sha256((p/name).read_bytes()).hexdigest()==pre[key]
active=[]
for q in Path('/proc').iterdir():
 if q.name.isdigit():
  try:
   if(q/'comm').read_text().strip()=='active_first_cy':active.append(q.name)
  except OSError:pass
assert not active
with(p/'LOCAL_ENTRY_INTENT62.json').open('x')as f:json.dump(context['intent'],f,indent=2);f.flush();os.fsync(f.fileno())
record={'schema':'FRESH62_V3_ONLINE_SINGLE_USE_NATIVE_ENTRY','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'driver_pid':os.getpid(),'runtime_plan_sha256':pre['runtime_plan_actual_sha256'],'runtime_distinct_inputs':1731,'profile_sha256':pre['profile_sha256'],'ELF_sha256':pre['ELF_sha256'],'preentry_actual_sha256':hashlib.sha256((p/'PREENTRY62_V3.json').read_bytes()).hexdigest(),'preentry_age_seconds':age,'storage_layout_sha256':pre['storage_layout_sha256'],'capture_sha256':pre['capture_sha256'],'old61_consumed_preserved':True,'native_attempts':1,'automatic_retries':0,'execution_mode':'ONLINE_NO_OFFLINE_SUPERVISOR_QUEUE','scope':'Fresh62 same functional work package after38compile27link26pure/old8saved6active exact and original74 extra input-corrected pure; all original math/SI/nonlinear/geometry/B/history/two2ms/C/stop/resources unchanged. Current-history nominal planning only, no hardware/heldout/main/scorer/research acceptance.'}
fd=os.open(p/'ENTRY_CONSUMED62.json',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o444)
with os.fdopen(fd,'w')as f:json.dump(record,f,indent=2);f.flush();os.fsync(f.fileno())
print(json.dumps(record),flush=True);os.execv('/usr/bin/python3',['/usr/bin/python3','-I','-S','-B',str(p/'active_run_driver.py'),str(p/'active_run_plan.json')])
