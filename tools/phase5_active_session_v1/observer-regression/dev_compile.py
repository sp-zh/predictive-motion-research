#!/usr/bin/env python3
# Fresh active development compile driver; does not execute project binaries.
from pathlib import Path
import hashlib,json,os,resource,selectors,signal,subprocess,sys,time
plan_path=Path(sys.argv[1]);plan=json.loads(plan_path.read_text())
assert plan['schema']=='ACTIVE_SESSION_OBSERVER_COMPILE_V1'
out=Path(plan['output_directory']);out.mkdir(mode=0o700,exist_ok=False)
started_batch=time.monotonic();events=[];records=[];current=None
limits_spec={'CPU':120,'AS':2147483648,'CORE':0,'FSIZE':268435456,'NOFILE':64,'NPROC':32}
def dump(name,value):
 (out/name).write_text(json.dumps(value,indent=2)+'\n')
def event(stage,**fields):
 events.append({'stage':stage,'batch_elapsed_seconds':time.monotonic()-started_batch,**fields});dump('CONTROL_EVENT_PREFIX.json',events)
def identity(x):
 p=Path(x['requested_path']);s=p.stat();b=p.read_bytes();actual={'requested_path':str(p),'resolved_path':str(p.resolve(strict=True)),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'mode':s.st_mode&0o7777}
 assert actual['bytes']==x['bytes'] and actual['sha256']==x['sha256'],str(p)
 if 'resolved_path' in x:assert actual['resolved_path']==x['resolved_path'],str(p)
 if 'mode' in x:assert actual['mode']==x['mode'],str(p)
 return actual
rosters=[]
def precheck():
 ids=[identity(x) for x in plan['input_files']]
 for row in plan.get('readonly_directory_rosters',[]):
  p=Path(row['path']);actual={'path':str(p),'mode':p.stat().st_mode&0o7777,'entries':sorted(x.name for x in p.iterdir())};assert actual==row,str(p);rosters.append(actual)
 dump('BEFORE_INPUT_IDENTITIES.json',ids);dump('BEFORE_READONLY_ROSTERS.json',rosters);return ids
def postcheck(before):
 after=[identity(x) for x in plan['input_files']];assert after==before,'input drift';dump('AFTER_INPUT_IDENTITIES.json',after)
 actual=[]
 for row in rosters:
  p=Path(row['path']);value={'path':str(p),'mode':p.stat().st_mode&0o7777,'entries':sorted(x.name for x in p.iterdir())};assert value==row,str(p);actual.append(value)
 dump('AFTER_READONLY_ROSTERS.json',actual)
def kill_group(child):
 # Own newly created session only. TERM then bounded KILL; never touches another
 # task, PID selected from discovery, old files or an existing evidence attempt.
 try:os.killpg(child.pid,signal.SIGTERM)
 except ProcessLookupError:pass
 time.sleep(.2)
 try:os.killpg(child.pid,signal.SIGKILL)
 except ProcessLookupError:pass
 try:child.wait(timeout=5)
 except subprocess.TimeoutExpired:pass
 event('OWNED_PROCESS_GROUP_TERMINATED',pid=child.pid)
def interrupted(signum,frame):
 if current is not None:kill_group(current)
 event('CONTROLLER_INTERRUPTED',signal=signum);raise SystemExit(128+signum)
signal.signal(signal.SIGTERM,interrupted);signal.signal(signal.SIGINT,interrupted)
def child_limits(write_fd):
 os.umask(0o077);applied={}
 for label,value in limits_spec.items():
  key=getattr(resource,'RLIMIT_'+label);soft,hard=resource.getrlimit(key)
  cap=value if hard==resource.RLIM_INFINITY else min(value,hard)
  chosen=cap if soft==resource.RLIM_INFINITY else min(soft,cap)
  resource.setrlimit(key,(chosen,cap));applied[label]={'inherited_soft':soft,'inherited_hard':hard,'applied_soft':chosen,'applied_hard':cap}
 os.write(write_fd,(json.dumps(applied)+'\n').encode());os.close(write_fd)
def execute(kind,index,argv):
 global current
 prefix=out/(kind+'-'+str(index));start=time.monotonic();counts={'stdout':0,'stderr':0};reason=None;killed=False;drain_deadline=None
 result={'kind':kind,'index':index,'argv':argv,'stage':'BEFORE_POPEN','actual_project_tool_entry':'UNKNOWN_UNTIL_CHILD_RESULT','exit':None,'first_error':None}
 dump(prefix.name+'.result.json',result);event('BEFORE_POPEN',kind=kind,index=index)
 proof_read,proof_write=os.pipe();sel=None;child=None
 try:
  child=subprocess.Popen(argv,cwd=out,env=plan['env'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True,pass_fds=(proof_write,),preexec_fn=lambda:child_limits(proof_write))
  current=child;os.close(proof_write);proof_write=-1
  applied=os.read(proof_read,8192);result['applied_limits']=json.loads(applied.decode());event('CHILD_STARTED',kind=kind,index=index,pid=child.pid)
  sel=selectors.DefaultSelector()
  with prefix.with_suffix('.stdout').open('xb') as stdout,prefix.with_suffix('.stderr').open('xb') as stderr:
   sel.register(child.stdout,selectors.EVENT_READ,('stdout',stdout));sel.register(child.stderr,selectors.EVENT_READ,('stderr',stderr))
   while sel.get_map():
    if time.monotonic()-start>150 and reason is None:reason='COMMAND_WALL_TIMEOUT'
    if time.monotonic()-started_batch>1240 and reason is None:reason='BATCH_WALL_TIMEOUT'
    if child.poll() is not None and child.returncode!=0 and reason is None:reason='NONZERO_CHILD_EXIT'
    if reason is not None and not killed:
     kill_group(child);killed=True;drain_deadline=time.monotonic()+5
    if drain_deadline is not None and time.monotonic()>drain_deadline:
     result['drain_incomplete']=True
     for key in list(sel.get_map().values()):sel.unregister(key.fileobj)
     break
    ready=sel.select(.1)
    for key,_ in ready:
     data=os.read(key.fileobj.fileno(),65536)
     if not data:sel.unregister(key.fileobj);continue
     name,sink=key.data;keep=max(0,1048576-counts[name]);sink.write(data[:keep]);counts[name]+=len(data)
     if counts[name]>1048576 and reason is None:reason='CAPTURE_LIMIT'
   result.update(exit=child.wait(timeout=5),stage='CHILD_EXIT_REAPED',actual_project_tool_entry='Popen started; exit retained, compiler/link success only if exit0',observed_stream_bytes=counts,stop_reason=reason)
 except BaseException as e:
  if child is not None:kill_group(child)
  result.update(stage='POPEN_PREEXEC_CAPTURE_OR_WAIT_FAILURE',first_error=type(e).__name__+': '+str(e),observed_stream_bytes=counts,stop_reason=reason)
 finally:
  if sel is not None:sel.close()
  if child is not None:
   for stream in (child.stdout,child.stderr):
    if stream is not None:stream.close()
  os.close(proof_read)
  if proof_write>=0:os.close(proof_write)
  current=None;result['wall_seconds']=time.monotonic()-start;dump(prefix.name+'.result.json',result)
 return result
before=None
try:
 event('FIRST_BUILD_CLAIM_INPUTS_NOT_YET_CHECKED',plan_sha256=hashlib.sha256(plan_path.read_bytes()).hexdigest())
 assert len(plan['compile_argv'])==2
 assert plan['env']=={'PATH':'/usr/bin:/bin','LANG':'C','LC_ALL':'C','TZ':'UTC'}
 before=precheck();event('EXACT_BEFORE_INPUTS_AND_READONLY_ROSTERS_VERIFIED')
 for kind,commands in [('compile',plan['compile_argv'])]:
  for index,argv in enumerate(commands,1):
   result=execute(kind,index,argv);records.append(result);dump('BATCH_PREFIX.json',{'records':records,'complete':False,'runtime_invocations':0})
   postcheck(before)
   if result['exit']!=0 or result.get('stop_reason') is not None or result['first_error'] is not None:raise RuntimeError('First controlled compiler/link refusal; no retry')
 postcheck(before);event('COMPLETE_FOUR_ACTIVE_COMPILE_NO_RUNTIME')
 dump('BUILD_RESULT.json',{'records':records,'complete':True,'runtime_invocations':0,'phase5':'NOT_ACCEPTED','phase6':'NOT_STARTED'})
except BaseException as e:
 event('FIRST_BUILD_FAILURE_RETAINED',error=type(e).__name__+': '+str(e))
 if before is not None:
  try:postcheck(before)
  except BaseException as drift:dump('AFTER_INPUT_FAILURE_RETAINED.json',{'error':type(drift).__name__+': '+str(drift)})
 dump('BUILD_FAILURE.json',{'records':records,'error':type(e).__name__+': '+str(e),'runtime_invocations':0});raise
