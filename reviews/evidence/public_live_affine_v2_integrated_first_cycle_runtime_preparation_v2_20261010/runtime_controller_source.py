#!/usr/bin/env python3
# SOURCE ONLY. A direct trusted Root dispatch must pin this source and a NEW
# released plan; the sealed NOT_RELEASED proposal cannot enter Popen.
from pathlib import Path
import hashlib,json,os,resource,selectors,signal,subprocess,sys,time
assert len(sys.argv)==3
plan_path=Path(sys.argv[1]);expected_sha=sys.argv[2];raw=plan_path.read_bytes()
assert len(raw)<=2*1024*1024 and hashlib.sha256(raw).hexdigest()==expected_sha
plan=json.loads(raw)
assert plan['schema']=='FIRST_CYCLE_EXTERNAL_SINGLE_RUNTIME_PLAN_1'
assert plan['decision']=='RELEASED_FOR_ONE_OFFLINE_FIRST_CYCLE_ATTEMPT'
assert plan['phase5']=='NOT_ACCEPTED' and plan['phase6']=='NOT_STARTED'
assert plan['env']=={'PATH':'/usr/bin:/bin','LANG':'C','LC_ALL':'C','TZ':'UTC'}
assert len(plan['argv'])==8 and plan['argv'][0]==plan['producer']['path']
assert plan['argv'][7]==plan['output_directory']
assert plan['limits']=={'CPU':120,'AS':4294967296,'CORE':0,'FSIZE':134217728,'NOFILE':128,'NPROC':64}
assert plan['wall_seconds']==180 and plan['stdout_limit']==1048576 and plan['stderr_limit']==1048576
attempt=Path(plan['attempt_directory']);assert not attempt.exists(),'FIRST attempt exists, STOP without retry'
for name in ['output_directory','bootstrap_claim_path','model_claim_path','controls_directory']:
 target=Path(plan[name]);assert target.is_absolute() and target.parent==attempt
 assert not target.exists()
os.umask(0o077);attempt.mkdir(mode=0o700);controls=Path(plan['controls_directory']);controls.mkdir(mode=0o700)
started=time.monotonic();events=[];current=None;before=None;rosters=None
limits_proof={}
def dump(name,value):
 (controls/name).write_text(json.dumps(value,indent=2)+'\n')
def event(stage,**fields):
 events.append({'stage':stage,'elapsed_seconds':time.monotonic()-started,**fields});dump('EVENT_PREFIX.json',events)
def identity(row):
 p=Path(row['path']);b=p.read_bytes();s=p.stat();actual={'path':str(p),'resolved_path':str(p.resolve(strict=True)),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'mode':s.st_mode&0o7777,'device':s.st_dev,'inode':s.st_ino}
 for key in ['bytes','sha256']:assert actual[key]==row[key],(str(p),key)
 for key in ['resolved_path','mode']:
  if key in row:assert actual[key]==row[key],(str(p),key)
 return actual
def directory(row):
 p=Path(row['path']);value={'path':str(p),'mode':p.stat().st_mode&0o7777,'entries':sorted(x.name for x in p.iterdir())};assert value==row,str(p);return value
def check_after():
 after=[identity(row) for row in plan['before_after_inputs']];dump('AFTER_IDENTITIES.json',after);assert after==before,'original input identity/inode/mode drift'
 after_dirs=[directory(row) for row in plan['before_after_readonly_rosters']];dump('AFTER_ROSTERS.json',after_dirs);assert after_dirs==rosters,'readonly roster drift'
def kill_owned(child):
 try:os.killpg(child.pid,signal.SIGTERM)
 except ProcessLookupError:pass
 time.sleep(.2)
 try:os.killpg(child.pid,signal.SIGKILL)
 except ProcessLookupError:pass
 try:child.wait(timeout=5)
 except subprocess.TimeoutExpired:pass
 event('OWNED_GROUP_TERMINATED',pid=child.pid)
def interrupted(signum,frame):
 if current is not None:kill_owned(current)
 event('CONTROLLER_INTERRUPTED',signal=signum);raise SystemExit(128+signum)
signal.signal(signal.SIGTERM,interrupted);signal.signal(signal.SIGINT,interrupted)
def observed_output_refusal():
 # Observation thresholds may overshoot before polling/termination. This is
 # explicitly not an aggregate admission, Parent or all-RSS guarantee.
 total=0;files=0
 for p in attempt.rglob('*'):
  if not p.is_file():continue
  n=p.stat().st_size;total+=n;files+=1
  if p.name=='MANIFEST.yaml' and n>plan['manifest_observed_limit']:return 'MANIFEST_OBSERVED_LIMIT'
  if p.name.endswith('.claim') and n>plan['claims_observed_limit_each']:return 'CLAIM_OBSERVED_LIMIT'
  if p.parent==controls and p.suffix=='.json' and n>plan['controller_metadata_observed_limit_each']:return 'CONTROL_METADATA_OBSERVED_LIMIT'
 if files>plan['fixed_file_roster_observed_limit']:return 'FIXED_FILE_ROSTER_OBSERVED_LIMIT'
 if total>plan['attempt_observed_limit']:return 'AGGREGATE_OBSERVED_LIMIT'
 return None
try:
 event('FIRST_ATTEMPT_CLAIM_NO_PROGRAM_ENTRY',trusted_plan_sha256=expected_sha)
 for label,value in plan['limits'].items():
  key=getattr(resource,'RLIMIT_'+label);soft,hard=resource.getrlimit(key);cap=value if hard==resource.RLIM_INFINITY else min(value,hard);chosen=cap if soft==resource.RLIM_INFINITY else min(soft,cap);resource.setrlimit(key,(chosen,cap));limits_proof[label]={'inherited_soft':soft,'inherited_hard':hard,'applied_soft':chosen,'applied_hard':cap}
 dump('APPLIED_LIMITS.json',limits_proof)
 producer=identity(plan['producer']);before=[identity(row) for row in plan['before_after_inputs']];rosters=[directory(row) for row in plan['before_after_readonly_rosters']]
 dump('BEFORE_IDENTITIES.json',before);dump('BEFORE_ROSTERS.json',rosters)
 # Root final review bytes are independently pinned by the exact CLI hashes.
 for path,digest in [(plan['argv'][1],plan['argv'][2]),(plan['argv'][3],plan['argv'][4]),(plan['argv'][5],plan['argv'][6])]:
  b=Path(path).read_bytes();assert len(b)<=2*1024*1024 and hashlib.sha256(b).hexdigest()==digest
 outer=json.loads(Path(plan['argv'][1]).read_text());inner=json.loads(Path(plan['argv'][3]).read_text())
 assert outer['decision']=='RELEASED_FOR_ONE_OFFLINE_FIRST_CYCLE_BOUND_COMPONENT'
 assert inner['decision']=='RELEASED_FOR_ONE_BOUND_COMPONENT_ATTEMPT'
 assert outer['producer_sha256']==producer['sha256']
 event('BEFORE_SINGLE_POPEN',actual_program_entry='UNKNOWN_UNTIL_CHILD_RESULT')
 counts={'stdout':0,'stderr':0};reason=None;killed=False;deadline=None;sel=None;child=None
 result={'argv':plan['argv'],'entry':'UNKNOWN_BEFORE_POPEN','exit':None,'first_error':None}
 dump('PROGRAM_RESULT_PREFIX.json',result)
 try:
  assert time.monotonic()-started<=plan['wall_seconds'],'PREENTRY_WALL_REFUSAL_NO_PROGRAM_ENTRY'
  assert observed_output_refusal() is None,'PREENTRY_OUTPUT_THRESHOLD_REFUSAL_NO_PROGRAM_ENTRY'
  child=subprocess.Popen(plan['argv'],cwd=attempt,env=plan['env'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True);current=child;result['entry']='POPEN_STARTED';event('PROGRAM_CHILD_STARTED',pid=child.pid)
  sel=selectors.DefaultSelector()
  with (controls/'program.stdout').open('xb') as stdout,(controls/'program.stderr').open('xb') as stderr:
   sel.register(child.stdout,selectors.EVENT_READ,('stdout',stdout));sel.register(child.stderr,selectors.EVENT_READ,('stderr',stderr))
   while sel.get_map():
    if time.monotonic()-started>plan['wall_seconds'] and reason is None:reason='WALL_LIMIT'
    if child.poll() is not None and child.returncode!=0 and reason is None:reason='NONZERO_PROGRAM_EXIT'
    observed=observed_output_refusal()
    if observed and reason is None:reason=observed
    if reason is not None and not killed:kill_owned(child);killed=True;deadline=time.monotonic()+5
    if deadline is not None and time.monotonic()>deadline:
     result['drain_incomplete']=True
     for key in list(sel.get_map().values()):sel.unregister(key.fileobj)
     break
    for key,_ in sel.select(.1):
     data=os.read(key.fileobj.fileno(),65536)
     if not data:sel.unregister(key.fileobj);continue
     name,sink=key.data;cap=plan[name+'_limit'];sink.write(data[:max(0,cap-counts[name])]);counts[name]+=len(data)
     if counts[name]>cap and reason is None:reason='STREAM_CAPTURE_LIMIT'
   result.update(exit=child.wait(timeout=5),stage='CHILD_REAPED',stop_reason=reason,observed_stream_bytes=counts)
 except BaseException as e:
  if child is not None:kill_owned(child)
  result.update(first_error=type(e).__name__+': '+str(e),stage='POPEN_CAPTURE_WAIT_FAILURE',stop_reason=reason,observed_stream_bytes=counts)
 finally:
  if sel is not None:sel.close()
  if child is not None:
   for stream in [child.stdout,child.stderr]:
    if stream is not None:stream.close()
  current=None;result['wall_seconds']=time.monotonic()-started;dump('PROGRAM_RESULT.json',result)
 check_after();assert result['exit']==0 and result['first_error'] is None and result['stop_reason'] is None,'FIRST failure retained; no retry'
 assert observed_output_refusal() is None,'Post-exit observational output refusal retained'
 manifest=Path(plan['output_directory'])/'MANIFEST.yaml';assert manifest.is_file(),'Expected actual manifest absent; retained'
 event('SINGLE_PROGRAM_RETURNED_ZERO_INDEPENDENT_CONTENT_REVIEW_REQUIRED')
 dump('CONTROLLER_RESULT.json',{'status':'ONE_EXIT_ZERO_CONTENT_NOT_ACCEPTED','result':result,'phase5':'NOT_ACCEPTED','phase6':'NOT_STARTED','execution_permission':False})
except BaseException as e:
 event('FIRST_FAILURE_STOP_NO_RETRY',error=type(e).__name__+': '+str(e))
 if before is not None:
  try:check_after()
  except BaseException as drift:dump('AFTER_FAILURE_RETAINED.json',{'error':type(drift).__name__+': '+str(drift)})
 dump('CONTROLLER_FAILURE.json',{'error':type(e).__name__+': '+str(e),'phase5':'NOT_ACCEPTED','phase6':'NOT_STARTED'});raise
