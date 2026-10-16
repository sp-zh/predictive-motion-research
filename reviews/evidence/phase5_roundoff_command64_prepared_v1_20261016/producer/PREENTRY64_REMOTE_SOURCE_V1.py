from pathlib import Path
import sys,json,hashlib,datetime,subprocess,os
x=json.load(sys.stdin);p=Path(x['remote']);prior=Path(x['prior']);assert not(p/'ENTRY_CONSUMED64.json').exists()and not(p/'run-attempt1').exists();writer=json.loads(Path('/home/codextransfer/predictive_motion/PHASE5_WRITER_STATE_20261007.json').read_text());assert writer['owner_thread_id']=='01a114d9-3a3a-7071-b94f-624581000992'and writer['state']=='ACTIVE_SINGLE_WRITER'
for n,text in x['files'].items():
 assert '/'not in n
 with(p/n).open('x')as f:f.write(text);f.flush();os.fsync(f.fileno())
 (p/n).chmod(0o444)
r=json.loads((p/'active_run_plan.json').read_text());assert len(r['input_files'])==len({y['requested_path']for y in r['input_files']})==1737
for y in r['input_files']:
 q=Path(y['requested_path']);assert q.stat().st_size==y['bytes']and hashlib.sha256(q.read_bytes()).hexdigest()==y['sha256'];assert 'mode'not in y or q.stat().st_mode&0o7777==y['mode'];assert 'resolved_path'not in y or str(q.resolve())==y['resolved_path']
a=json.loads((prior/'profile-version1/active_input.json').read_text());b=json.loads((p/'profile-version1/active_input.json').read_text());a['session_id']=b['session_id'];a['negative_multiplier_leaving']['codec']=b['negative_multiplier_leaving']['codec'];a['roundoff_endpoint64']=b['roundoff_endpoint64'];a['first_command_contraction64']=b['first_command_contraction64'];assert a==b;assert b['roundoff_endpoint64']=={'stop_only':True,'endpoint_cap':16384,'numeric_domain':1e-12}and b['first_command_contraction64']=={'first_controls':7,'solver_fraction':.5,'strict_fraction':.75,'command_stop_threshold':1e-6}
for name,key,count in [('build-attempt1','records',40),('link-attempt1','records',29),('pure-tests-attempt1','rows',28)]:
 v=json.loads((p/name/('RESULT.json'if name=='pure-tests-attempt1'else'BUILD_RESULT.json')).read_text());assert v['complete']and len(v[key])==count and all(z['exit']==0 for z in v[key])
assert(p/'pure-tests-attempt1/PURE_INPUT_BEFORE.json').read_bytes()==(p/'pure-tests-attempt1/PURE_INPUT_AFTER.json').read_bytes();v=json.loads((p/'pure-math-attempt1/RESULT.json').read_text());assert v['input_before_after_equal']and len(v['records'])==18 and all(z['exit']==0 for z in v['records']);targeted=json.loads((p/'pure-newpolicies-attempt1/RESULT.json').read_text());assert targeted['input_before_after_equal']and targeted['all10_true_numerical_complete']and len(targeted['records'])==12
active=[]
for q in Path('/proc').iterdir():
 if q.name.isdigit():
  try:
   if(q/'comm').read_text().strip()=='active_first_cy':active.append(q.name)
  except OSError:pass
assert not active
v=subprocess.run(['/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe','-NoProfile','-NonInteractive','-Command','Get-CimInstance Win32_LogicalDisk | Select-Object DeviceID,FreeSpace,Size | ConvertTo-Json -Compress'],stdin=subprocess.DEVNULL,capture_output=True,timeout=15);assert v.returncode==0,v.stderr;vol=json.loads(v.stdout.decode('utf-8-sig'));assert all(next(y for y in vol if y['DeviceID']==key)['FreeSpace']>=80*1024**3 for key in ['C:','D:'])
sha=lambda n:hashlib.sha256((p/n).read_bytes()).hexdigest();assert r['compile_argv'][0][2]==sha('profile-version1/active_input.json')and r['compile_argv'][0][3]==sha('link-attempt1/active_first_cycle');layout=json.loads((p/'STORAGE_LAYOUT64_FINAL_V1.json').read_text());assert layout['enforcement']['capture_source_sha256']==sha('capture_terminal64.py')and layout['minimum_free_Mac_bytes']==12*1024**3
out={'schema':'FRESH64_ROUNDOFF_COMMAND_ONLINE_PREENTRY_V1','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'writer':writer['owner_thread_id'],'all_identities_stable':True,'runtime_distinct_input_count':1737,'actual_CIM_volumes':vol,'native_processes':active,'profile_original63_equal_except_session_two_policies_and_newcodec_role':True,'pure28_before_after_equal':True,'formal18_before_after_equal':True,'profile_sha256':r['compile_argv'][0][2],'ELF_sha256':r['compile_argv'][0][3],'runtime_plan_actual_sha256':sha('active_run_plan.json'),'driver_sha256':sha('active_run_driver.py'),'storage_layout_sha256':sha('STORAGE_LAYOUT64_FINAL_V1.json'),'capture_sha256':sha('capture_terminal64.py'),'native64_not_entered':True,'execution_mode':'ONLINE_ACTIVE_DEVELOPMENT_NO_OFFLINE_SUPERVISOR_QUEUE','prior63_complete_failure_evidence_retained':True}
with(p/'PREENTRY64_V1.json').open('x')as f:json.dump(out,f,indent=2);f.flush();os.fsync(f.fileno())
(p/'PREENTRY64_V1.json').chmod(0o444);print(json.dumps(out))
