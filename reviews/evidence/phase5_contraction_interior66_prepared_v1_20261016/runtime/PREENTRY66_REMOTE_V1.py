from pathlib import Path
import sys,json,os,hashlib,subprocess,datetime
x=json.load(sys.stdin);P=Path('/home/codextransfer/predictive_motion/results/phase5/session-controlled-stop-first-command-interior-direct-mac-v1-20261016-attempt66');D=Path('/mnt/d/CodexTransfer/phase5-numeric-integration66-20261016-attempt1');T=Path('/mnt/d/CodexTransfer/phase5-numeric-integration66-regression2-20261016');assert not(P/'ENTRY_CONSUMED66.json').exists()and not(P/'run-attempt1').exists();name=x['record_name'];assert name.startswith('PREENTRY66_')and name.endswith('.json')and '/'not in name and not(P/name).exists()
owner=json.loads(Path('/home/codextransfer/predictive_motion/PHASE5_WRITER_STATE_20261007.json').read_text());assert owner['owner_thread_id']=='01a114d9-3a3a-7071-b94f-624581000992'and owner['state']=='ACTIVE_SINGLE_WRITER'
def sha(p):
 p=Path(p);s=p.stat();h=hashlib.sha256();n=0
 with p.open('rb')as f:
  while b:=f.read(65536):h.update(b);n+=len(b)
 assert n==s.st_size and(s.st_ino,s.st_size,s.st_mtime_ns)==(p.stat().st_ino,p.stat().st_size,p.stat().st_mtime_ns);return h.hexdigest()
plan=json.loads((P/'active_run_plan66_v1.json').read_text());assert len(plan['input_files'])==len({v['requested_path']for v in plan['input_files']})==1745
for e in plan['input_files']:
 q=Path(e['requested_path']);assert q.stat().st_size==e['bytes']and sha(q)==e['sha256'];assert 'resolved_path'not in e or str(q.resolve())==e['resolved_path'];assert 'mode'not in e or q.stat().st_mode&0o7777==e['mode']
profile=json.loads((P/'profile-version1/active_input.json').read_text());assert profile['schema']=='CONTROLLED_STOP_PHYSICAL_DOUBLEHAT_FIRST_PROGRESS_INTERIOR_V6'and profile['first_command_interior_policy66']=='INWARD_32_ABS_TOL_AFFINE_NOMINAL_MIDPOINT_V1'
old=json.loads(Path('/home/codextransfer/predictive_motion/results/phase5/session-controlled-stop-physical-braking-first-progress-direct-mac-v1-20261016-attempt65/profile-version1/active_input.json').read_text());old['historical_scope_preserved']=old['scope']
for k in ['schema','session_id','scope','first_command_interior_policy66']:old[k]=profile[k]
assert old==profile,'only explicit planning interior policy/identity/scope changes; original maths/solver/stop/limits same'
stock=0;builds=[]
for root,cap in [(D,96*1024**2),(T,32*1024**2)]:
 b=json.loads((root/'targeted-build-attempt1/BUILD_RESULT.json').read_text());assert b['complete']and all(r['exit']==0 and r['error']is None for r in b['records'])and b['zero_disk_scratch'];assert(root/'targeted-build-attempt1/BEFORE_INPUT_IDENTITIES.json').read_bytes()==(root/'targeted-build-attempt1/AFTER_INPUT_IDENTITIES.json').read_bytes();n=sum(q.stat().st_size for q in root.rglob('*')if q.is_file());assert n<=cap and not list((root/'scratch-never-writable').rglob('*'));stock+=n;builds.append({'root':str(root),'bytes':n,'precharged':cap,'compile_link_records':len(b['records'])})
pure=json.loads((T/'pure-tests-attempt1/RESULT.json').read_text());assert pure['exit']==0 and pure['immutable_inputs_stable']and 'all126 nonbeta bits preserved'in pure['stdout']and 'strict7=PASS'in pure['stdout'];failure=json.loads((D/'pure-tests-attempt1/RESULT.json').read_text());assert failure['exit']==1 and 'V6 checks whole current matrix'in failure['stderr'],'preserve wrong raytable test assertion failure'
fixture=Path('/home/codextransfer/predictive_motion/transfer/cold-archives/protocol66-single-test1-20261016');sent=json.loads((fixture/'STREAM_SENT.json').read_text());assert sent['complete']and sent['sha256']=='502b03e5e56936809a7348f9433a611c2baed5f6867e18e5d013760078416a74'and sent['source_before_after_stable']
active=[]
for q in Path('/proc').iterdir():
 if q.name.isdigit():
  try:
   argv=(q/'cmdline').read_bytes().split(b'\0');first=Path(argv[0].decode(errors='replace')).name if argv and argv[0]else''
   if first.startswith('active_first_cy'):active.append(q.name)
  except OSError:pass
assert not active
v=subprocess.run(['/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe','-NoProfile','-NonInteractive','-Command','Get-CimInstance Win32_LogicalDisk | Select-Object DeviceID,FreeSpace,Size | ConvertTo-Json -Compress'],stdin=subprocess.DEVNULL,capture_output=True,timeout=15);assert v.returncode==0;vol=json.loads(v.stdout.decode('utf-8-sig'));free={z['DeviceID']:int(z['FreeSpace'])for z in vol};assert free['C:']>=80*1024**3+3*1024**3+128*1024**2 and free['D:']>=80*1024**3+128*1024**2
mac=x['Mac_readiness'];age=(datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(mac['utc'])).total_seconds();assert 0<=age<=180 and mac['free_bytes']>=41*1024**3 and mac['source_and_saved_scalar_independent_review_pass']and mac['real66_single_protocol_persisted_readback_pass']and mac['prepared_source_checkpoint']and mac['remote_master_independently_verified']and mac['ELF_persistent_Mac_SHA_verified']=='ad722b0adc8e736d82f2dc138131632452e5c334c5aba7c237ac3f2549d141a6'
assert plan['compile_argv'][0][2]==sha(P/'profile-version1/active_input.json')and plan['compile_argv'][0][3]==sha(P/'link-attempt1/active_first_cycle')==sha(D/'targeted-build-attempt1/active_first_cycle')
result={'schema':'FRESH66_FIRST_COMMAND_INTERIOR_SINGLE_USE_PREENTRY_V1','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'writer':owner['owner_thread_id'],'runtime_input_count':1745,'all_runtime_inputs_stable':True,'profile_sha256':plan['compile_argv'][0][2],'ELF_sha256':plan['compile_argv'][0][3],'runtime_plan_sha256':sha(P/'active_run_plan66_v1.json'),'driver_sha256':sha(P/'active_run_driver66_v1.py'),'layout_sha256':sha(P/'STORAGE_LAYOUT66_V1.json'),'entry_wrapper_sha256':sha(P/'once_entry66_v1.py'),'actual_volumes':vol,'D_build_stocks':builds,'V6_initializer_and_pure_regression_pass':True,'old_bad_test_assertion_failure_preserved':True,'Mac_readiness':mac,'active_native_processes':active,'native66_not_entered':True,'execution_mode':'ONLINE_NO_OFFLINE_SUPERVISOR_QUEUE','scope':'Fresh66 finite current maths/physical/stop limits unchanged. Entry qualification is not Model/fulltask/stop/phase acceptance; no old65 replay.'}
with(P/name).open('x')as f:json.dump(result,f,indent=2);f.flush();os.fsync(f.fileno())
(P/name).chmod(0o444);print(json.dumps(result))
