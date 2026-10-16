from pathlib import Path
import sys,json,hashlib,os,datetime
p=Path('/home/codextransfer/predictive_motion/results/phase5/session-controlled-stop-global-interval-active32-brake64-dwell25-v1-20261016-attempt58');d=json.load(sys.stdin)
assert not(p/'ENTRY_CONSUMED58.json').exists()and not(p/'run-attempt1').exists()
for name,text in d.items():
 assert '/'not in name
 with(p/name).open('x')as f:f.write(text)
 (p/name).chmod(0o444)
plan=p/'active_run_plan.json';driver=p/'active_run_driver.py';assert hashlib.sha256(driver.read_bytes()).hexdigest()=='3a511b3f2c8aa43a5501e949598de40518e7041581bab053da1508e725028446';assert hashlib.sha256(plan.read_bytes()).hexdigest()=='e32fe13965af3b55feab1c0942c8e634ab183b760aa522a39ec2b4eae87d0f51'
pre=p/'FINAL_PREENTRY58_STORAGE_V1.json';pr=json.loads(pre.read_text());assert pr['storage_layout_plan_sha256']==hashlib.sha256((p/'STORAGE_LAYOUT58_V1.json').read_bytes()).hexdigest();assert pr['capture_source_sha256']==hashlib.sha256((p/'capture_terminal58.py').read_bytes()).hexdigest();assert (datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(pr['utc'])).total_seconds()<180
active=[]
for q in Path('/proc').iterdir():
 if q.name.isdigit():
  try:
   if(q/'comm').read_text().strip()=='active_first_cy':active.append(q.name)
  except OSError:pass
assert not active
record={'schema':'FRESH58_SINGLE_USE_NATIVE_ENTRY_MARKER_V1','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'driver_pid':os.getpid(),'runtime_plan_sha256':hashlib.sha256(plan.read_bytes()).hexdigest(),'preentry_sha256':hashlib.sha256(pre.read_bytes()).hexdigest(),'storage_layout_sha256':pr['storage_layout_plan_sha256'],'capture_sha256':pr['capture_source_sha256'],'runtime_distinct_inputs':1720,'old_attempts_consumed_retained':True,'scope':'One fresh58 bounded development entry after original saved math/pure/resource checks; no hardware/heldout/main/scorer or phase acceptance.'}
fd=os.open(p/'ENTRY_CONSUMED58.json',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o444)
with os.fdopen(fd,'w')as f:json.dump(record,f,indent=2);f.flush();os.fsync(f.fileno())
print(json.dumps(record),flush=True);os.execv('/usr/bin/python3',['/usr/bin/python3','-I','-S','-B',str(driver),str(plan)])
