from pathlib import Path
import json,subprocess,shlex,sys,os,shutil
sys.path.insert(0,'/private/tmp');from bounded_derived_bytes53_v1 import bounded_write_bytes
D=Path(__file__).resolve().parent;os.environ['P5_DERIVED53_ROOT']=str(D);p=json.loads((D/'REMOTE57.json').read_text())['remote']
code=r"""from pathlib import Path
import json,hashlib,subprocess,datetime
p=Path(REMOTE);assert not(p/'run-attempt1').exists()and not(p/'ENTRY_CONSUMED57.json').exists();pure=json.loads((p/'pure-tests-attempt1/RESULT.json').read_text());assert pure['complete']and all(x['exit']==0 for x in pure['rows'])and len(pure['rows'])==20
r=subprocess.run(['/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe','-NoProfile','-NonInteractive','-Command','Get-CimInstance Win32_LogicalDisk | Select-Object DeviceID,FreeSpace,Size | ConvertTo-Json -Compress'],stdin=subprocess.DEVNULL,capture_output=True,timeout=15);assert r.returncode==0,r.stderr;vol=json.loads(r.stdout.decode('utf-8-sig'));v={x['DeviceID']:x for x in vol};assert all(v[x]['FreeSpace']>=80*1024**3 for x in ['C:','D:'])
a=json.loads((p/'active_run_plan.json').read_text());paths={x['requested_path']for x in a['input_files']};assert len(paths)==len(a['input_files']);profile=json.loads(Path(a['compile_argv'][0][1]).read_text());spec=profile['working_face_repair']['bounded_kkt_refinement'];assert spec=={'stop_only':True,'maximum_steps':3,'correction_relative_cap':1,'initial_double_residual_cap':1e-10,'final_double_residual_cap':1e-10,'long_double_minimum_digits':64,'diagnostic_records_max':1536,'codec':'NUMERICAL_WORKING_FACE_BASIS_FULL_ENDPOINT_AND_BOUNDED_KKT_REFINEMENT_TRACE_V2'}
assert profile['row_progress_initializer']['eligibility']=='EXCESS_ABOVE_ORIGINAL_DOMAIN_GREATER_THAN_MAXIMUM_USEFUL_UNIFORM_CHANGE' and 'flat_progress_initializer'not in profile
assert profile['working_face_repair']['near_boundary_events']==12288 and profile['working_face_repair']['near_boundary_numeric_precharge']==745000 and profile['working_face_repair']['phase_aware_maximum_stop_trials']==144
for x in a['input_files']:
 q=Path(x['requested_path']);assert q.stat().st_size==x['bytes']and hashlib.sha256(q.read_bytes()).hexdigest()==x['sha256'];assert 'mode'not in x or q.stat().st_mode&0o7777==x['mode'];assert 'resolved_path'not in x or str(q.resolve())==x['resolved_path']
active=[]
for q in Path('/proc').iterdir():
 if q.name.isdigit():
  try:
   if(q/'comm').read_text().strip()=='active_first_cy':active.append(q.name)
  except OSError:pass
assert not active
out={'schema':'FRESH57_PREENTRY_RESOURCES_ALLINPUTS_V1','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'actual_CIM_volumes':vol,'C_D_80GiBeach':True,'WSL_statvfs_used':False,'all_distinct_inputs':len(paths),'identities_stable':True,'pure20stable_pass':True,'max_V2_codec_bytes':3507749,'longdouble_digits_measured':64,'existing_native_processes':active,'argv':a['compile_argv'][0],'native_not_yet_entered':True}
with(p/'PREENTRY57_V3.json').open('x')as f:json.dump(out,f,indent=2)
print(json.dumps(out))
""".replace('REMOTE',repr(p))
r=subprocess.run(['/Users/uot/Documents/ChatGPT/ros/tools/dell-ssh.sh','-T','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','DellTransfer','python3 -I -S -B -c '+shlex.quote(code)],capture_output=True,timeout=30)
bounded_write_bytes(D/'PREENTRY57_V3.stdout',r.stdout);bounded_write_bytes(D/'PREENTRY57_V3.stderr',r.stderr);assert r.returncode==0,r.stderr
free=shutil.disk_usage(D).free;assert free>=33*1024**3
out={'Mac_free_bytes':free,'minimum33GiB':33*1024**3,'remote':json.loads(r.stdout),'scope':'Fresh native57 resources and all distinct source/model/config/dependency inputs. Five saved stop cases and six activefalse full-record regressions plus20pure PASS; all55 failures retained; native57 not yet entered. Source/model/thresholds/outer512/10s/CPU/AS/storage/counter caps unchanged. Same combined53 global derived budget.'}
bounded_write_bytes(D/'FINAL_PREENTRY57_V3.json',(json.dumps(out,indent=2)+'\n').encode());print(json.dumps(out))
