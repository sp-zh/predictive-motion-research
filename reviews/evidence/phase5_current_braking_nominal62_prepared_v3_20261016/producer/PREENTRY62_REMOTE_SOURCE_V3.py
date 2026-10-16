from pathlib import Path
import sys,json,hashlib,datetime,subprocess,os
payload=json.load(sys.stdin);p=Path(payload['remote']);old=Path(payload['oldremote']);assert not(p/'run-attempt1').exists()and not(p/'ENTRY_CONSUMED62.json').exists()
writer=json.loads(Path('/home/codextransfer/predictive_motion/PHASE5_WRITER_STATE_20261007.json').read_text());assert writer['owner_thread_id']=='01a114d9-3a3a-7071-b94f-624581000992'and writer['state']=='ACTIVE_SINGLE_WRITER'
for name,text in payload['files'].items():
 assert '/'not in name
 with(p/name).open('x')as f:f.write(text);f.flush();os.fsync(f.fileno())
 (p/name).chmod(0o444)
run=json.loads((p/'active_run_plan.json').read_text());assert len(run['input_files'])==len({x['requested_path']for x in run['input_files']})==1731
for x in run['input_files']:
 q=Path(x['requested_path']);assert q.stat().st_size==x['bytes']and hashlib.sha256(q.read_bytes()).hexdigest()==x['sha256'];assert 'mode'not in x or q.stat().st_mode&0o7777==x['mode'];assert 'resolved_path'not in x or str(q.resolve())==x['resolved_path']
profile=json.loads((p/'profile-version1/active_input.json').read_text());prior=json.loads((old/'profile-version1/active_input.json').read_text());config=profile['current_braking_nominal62'];assert config=={'strategy':'CURRENT_HISTORY_JOINT132_PROGRESS132_PLUS16_ENVELOPE_FIRST_STOP_TRIAL','maximum_builds':89,'numeric_precharge':2048,'maximum_family_attempts':1072,'codec':'STOP_COST_CURRENT_HISTORY_JOINT_HAT_PROGRESS_ENVELOPE_NOMINAL_V3'};prior['session_id']=profile['session_id'];prior['current_braking_nominal62']=config;assert profile==prior,'all model/gate/math/resource/profile fields remain original61 except new session and explicit planning policy'
assert run['compile_argv'][0][2]==hashlib.sha256((p/'profile-version1/active_input.json').read_bytes()).hexdigest();assert run['compile_argv'][0][3]==hashlib.sha256((p/'link-attempt1/active_first_cycle').read_bytes()).hexdigest()
for directory,key,count in [('build-attempt1','records',38),('link-attempt1','records',27),('pure-tests-attempt1','rows',26)]:
 d=json.loads((p/directory/('RESULT.json'if directory=='pure-tests-attempt1'else'BUILD_RESULT.json')).read_text());assert d['complete']and len(d[key])==count and all(x['exit']==0 for x in d[key])
assert(p/'pure-tests-attempt1/PURE_INPUT_BEFORE.json').read_bytes()==(p/'pure-tests-attempt1/PURE_INPUT_AFTER.json').read_bytes();formal=json.loads((p/'pure-math-attempt1/RESULT.json').read_text());assert formal['input_before_after_equal']and len(formal['records'])==18 and all(x['exit']==0 for x in formal['records'])
active=[]
for q in Path('/proc').iterdir():
 if q.name.isdigit():
  try:
   if(q/'comm').read_text().strip()=='active_first_cy':active.append(q.name)
  except OSError:pass
assert not active
r=subprocess.run(['/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe','-NoProfile','-NonInteractive','-Command','Get-CimInstance Win32_LogicalDisk | Select-Object DeviceID,FreeSpace,Size | ConvertTo-Json -Compress'],stdin=subprocess.DEVNULL,capture_output=True,timeout=15);assert r.returncode==0,r.stderr;vol=json.loads(r.stdout.decode('utf-8-sig'));v={x['DeviceID']:x for x in vol};assert all(v[x]['FreeSpace']>=80*1024**3 for x in ['C:','D:']);storage=json.loads((p/'STORAGE_LAYOUT62_V3.json').read_text());assert storage['minimum_free_Mac_bytes']==12*1024**3 and storage['enforcement']['capture_source_sha256']==hashlib.sha256((p/'capture_terminal62.py').read_bytes()).hexdigest()
rec={'schema':'FRESH62_V3_ONLINE_PREENTRY_BOUND_RESOURCES_AND_INPUTS','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'writer':writer['owner_thread_id'],'actual_CIM_volumes':vol,'C_D_80GiBeach':True,'WSL_statvfs_used_as_CIM':False,'runtime_distinct_input_count':1731,'all_identities_stable':True,'pure26_before_after_stable':True,'formal8saved6active18commands_stable':True,'all_original61_profile_fields_equal_except_session_and_new_planning_policy':True,'native_processes':active,'profile_sha256':run['compile_argv'][0][2],'ELF_sha256':run['compile_argv'][0][3],'runtime_plan_actual_sha256':hashlib.sha256((p/'active_run_plan.json').read_bytes()).hexdigest(),'storage_layout_sha256':hashlib.sha256((p/'STORAGE_LAYOUT62_V3.json').read_bytes()).hexdigest(),'capture_sha256':hashlib.sha256((p/'capture_terminal62.py').read_bytes()).hexdigest(),'driver_sha256':hashlib.sha256((p/'active_run_driver.py').read_bytes()).hexdigest(),'native_not_entered':True,'execution_mode':'ONLINE_ACTIVE_DEVELOPMENT_NO_OFFLINE_SUPERVISOR_QUEUE','earlier61_consumed_and_original64brake_failure_retained':True}
with(p/'PREENTRY62_V3.json').open('x')as f:json.dump(rec,f,indent=2);f.flush();os.fsync(f.fileno())
(p/'PREENTRY62_V3.json').chmod(0o444);print(json.dumps(rec))
