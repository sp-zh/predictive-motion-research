from pathlib import Path
import sys,os,json,hashlib,base64,subprocess,shlex
sys.dont_write_bytecode=True;sys.path.insert(0,'/private/tmp')
from bounded_derived_bytes53_v1 import bounded_write
R=Path('/Users/uot/Documents/ChatGPT/ros');P=Path('/private/tmp/phase5_merged_hint_diagnostics60_source_v2_20261016');O=Path('/private/tmp/root60_merged_review_v1_20261016');os.environ['P5_DERIVED53_ROOT']=str(O);remote=json.loads((P/'REMOTE60.json').read_text())['remote']
code='''from pathlib import Path
import json,base64,hashlib,datetime
p=Path(REMOTE);out={}
for n in ['ENTRY_CONSUMED60.json','active_run_plan.json']:
 b=(p/n).read_bytes();assert len(b)<=2*1024**2;out[n]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'data':base64.b64encode(b).decode()}
a=p/'run-attempt1/artifacts';print(json.dumps({'files':out,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'terminal_present':(a/'entry_completion.bin').exists(),'max_cycle_directory':max([int(x.name.split('-')[1])for x in a.glob('cycle-*')],default=-1)}))'''.replace('REMOTE',repr(remote))
r=subprocess.run(['tools/dell-ssh.sh','-T','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','DellTransfer','python3 -I -S -B -c '+shlex.quote(code)],capture_output=True,timeout=20);assert r.returncode==0,r.stderr.decode();assert len(r.stdout)<=4*1024**2;j=json.loads(r.stdout);data={}
for n,e in j['files'].items():
 b=base64.b64decode(e['data']);assert len(b)==e['bytes']and hashlib.sha256(b).hexdigest()==e['sha256'];data[n]=b
sha=lambda b:hashlib.sha256(b).hexdigest();assert sha(data['active_run_plan.json'])=='7881fc625bde535894ea2939b91d4eb7598e09d3aa17b8eae0be4f2511ff1028';plan=json.loads(data['active_run_plan.json']);entry=json.loads(data['ENTRY_CONSUMED60.json']);assert plan==json.loads((P/'active_run_plan.json').read_text())and len(plan['input_files'])==1725
count=0
for p in(R/'tools/phase5_controlled_stop_session_v13').iterdir():
 if p.is_file():
  e=next(x for x in plan['input_files']if x['requested_path']==remote+'/src/'+p.name);b=p.read_bytes();assert e['bytes']==len(b)and e['sha256']==sha(b);count+=1
assert count==85
assert sha((R/'tools/phase5_controlled_stop_session_v13/profile/active_input.json').read_bytes())==plan['compile_argv'][0][2]=='0f92a85fdac7f1a17c3818e99af6b005b34510dd4159ec51606947ddd8a3d989';assert plan['compile_argv'][0][3]=='6f90633440152bbc3e9be7c32939be25df4889bae1cd6157bd660a32acded155'
hashes={n:sha((P/n).read_bytes())for n in ['FINAL_PREENTRY60_STORAGE_V1.json','STORAGE_LAYOUT60_V1.json','capture_terminal60.py']};assert hashes=={'FINAL_PREENTRY60_STORAGE_V1.json':'15d6d528a1202767c8b7a91dd80d483704a3e54c71d88bf90c91b9f368ca0bc4','STORAGE_LAYOUT60_V1.json':'3be147beaa876d003c7ec635fafb4d73c160717cd3663eba15cd9ca6b1788fca','capture_terminal60.py':'5f5a57e763f2c778efef115693c90b5900a6a5f11c7759008cb72f5ef3635838'}
report=dict(schema='ROOT60_V2_ACTUAL_ONCE_ENTRY_AND_FULL_FROZEN_INPUT_BINDING_V1',entry=entry,actual_runtime_sha256=sha(data['active_run_plan.json']),all_prepared_and_actual_parsed_plan_objects_equal=True,runtime_input_records=1725,all85_frozen_Git_source_files_match_actual_runtime_pins=True,profile_sha256=plan['compile_argv'][0][2],ELF_sha256=plan['compile_argv'][0][3],preentry_storage_capture_hashes=hashes,observed_utc=j['utc'],terminal_present=j['terminal_present'],max_cycle_directory=j['max_cycle_directory'],scope='Existing once60v2 entry only, no duplicate dispatch or source mutation. Directory progress is not an independently decoded completed command, stop or task. Original entry scope literal fresh59 is retained and qualified by actual60 schema/v2 absolute paths/pins and separate metadata qualifier. Formal outcome and complete evidence backup remain pending.')
for name,b in [('ACTUAL_ENTRY60.json',data['ENTRY_CONSUMED60.json']),('ACTUAL_RUNTIME_PLAN60.json',data['active_run_plan.json']),('ACTUAL_ENTRY_BINDING_REVIEW.json',(json.dumps(report,indent=2)+'\n').encode())]:bounded_write(O/name,b.decode())
print(json.dumps({k:v for k,v in report.items()if k not in ['entry','scope']}))
