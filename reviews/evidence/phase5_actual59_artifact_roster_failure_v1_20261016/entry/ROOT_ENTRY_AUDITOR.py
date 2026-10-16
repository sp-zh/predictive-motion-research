from pathlib import Path
import sys,os,json,hashlib,base64,subprocess,shlex,datetime
sys.dont_write_bytecode=True;sys.path.insert(0,'/private/tmp')
from bounded_derived_bytes53_v1 import bounded_write
R=Path('/Users/uot/Documents/ChatGPT/ros');P=Path('/private/tmp/phase5_negative_leaving59_source_v1_20261016');O=Path('/private/tmp/root59_saved_review_v1_20261016');os.environ['P5_DERIVED53_ROOT']=str(O);remote=json.loads((P/'REMOTE59.json').read_text())['remote']
code='''from pathlib import Path
import json,hashlib,base64,datetime
p=Path(REMOTE);files={}
for n in ['ENTRY_CONSUMED59.json','active_run_plan.json']:
 b=(p/n).read_bytes();assert len(b)<=2*1024**2;files[n]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'data':base64.b64encode(b).decode()}
a=p/'run-attempt1/artifacts';print(json.dumps({'files':files,'observation_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'terminal_present':(a/'entry_completion.bin').exists(),'max_cycle_directory':max([int(x.name.split('-')[1])for x in a.glob('cycle-*')],default=-1)}))'''.replace('REMOTE',repr(remote))
r=subprocess.run(['tools/dell-ssh.sh','-T','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','DellTransfer','python3 -I -S -B -c '+shlex.quote(code)],capture_output=True,timeout=20);assert r.returncode==0,r.stderr.decode();assert len(r.stdout)<=4*1024**2;j=json.loads(r.stdout);data={}
for name,e in j['files'].items():
 b=base64.b64decode(e['data']);assert len(b)==e['bytes']and hashlib.sha256(b).hexdigest()==e['sha256'];data[name]=b
entry=json.loads(data['ENTRY_CONSUMED59.json']);plan=json.loads(data['active_run_plan.json']);assert hashlib.sha256(data['active_run_plan.json']).hexdigest()=='3f5938f2074500fc89622f5e83e95da4116d5d06368ed45a426010f090cc6f4f';assert plan==json.loads((P/'active_run_plan.json').read_text());assert len(plan['input_files'])==1723
for p in (R/'tools/phase5_controlled_stop_session_v12').iterdir():
 if not p.is_file():continue
 e=next(e for e in plan['input_files']if e['requested_path']==remote+'/src/'+p.name);b=p.read_bytes();assert e['bytes']==len(b)and e['sha256']==hashlib.sha256(b).hexdigest()
profile=R/'tools/phase5_controlled_stop_session_v12/profile/active_input.json';assert hashlib.sha256(profile.read_bytes()).hexdigest()==plan['compile_argv'][0][2]=='187e08287b4fa7146692310c585d6d09fc0bad06af782136d136dd8e207c5f67';assert plan['compile_argv'][0][3]=='9566564550c1515d17b67b5af4ed0868cb7b78492663a49dd24c09b33a63485d'
pre=(P/'FINAL_PREENTRY59_STORAGE_V1.json').read_bytes();layout=(P/'STORAGE_LAYOUT59_V1.json').read_bytes();capture=(P/'capture_terminal59.py').read_bytes()
assert hashlib.sha256(pre).hexdigest()=='1fb5cdb87b1829d98e06c52ce1bc2e20ebc69a3defc49e865a1ba0b55fe546c2';assert hashlib.sha256(layout).hexdigest()=='a7eee99dcb28b4c0e27f5ce46f5eccc036cd298d0d3136751958506f1baae890';assert hashlib.sha256(capture).hexdigest()=='71a29b2c2c61f2c753ae2d01042773c27ead1a9248a882a250f7ab265acf2e26'
out=dict(schema='ROOT59_ACTUAL_ONCE_ENTRY_FROZEN_SOURCE_AND_PLAN_BINDING_V1',entry=entry,remote_runtime_plan_sha256=hashlib.sha256(data['active_run_plan.json']).hexdigest(),prepared_and_actual_plan_complete_parsed_objects_equal=True,all1723_input_records_bound=True,all83_Git_source_files_match_actual_runtime_pins=True,profile_sha256=plan['compile_argv'][0][2],ELF_sha256=plan['compile_argv'][0][3],preentry_sha256=hashlib.sha256(pre).hexdigest(),storage_plan_sha256=hashlib.sha256(layout).hexdigest(),capture_sha256=hashlib.sha256(capture).hexdigest(),observed_utc=j['observation_utc'],max_cycle_directory=j['max_cycle_directory'],terminal_present=j['terminal_present'],scope='Original once59 already entered by sole Dell writer. No second entry or mutation. Directory progress alone is not a completed C, stopping, task or phase outcome. No Model/native action on Mac. Copy-forward storage prose is qualified separately without replacing executed plan.')
for name,b in [('ACTUAL_ENTRY59.json',data['ENTRY_CONSUMED59.json']),('ACTUAL_RUNTIME_PLAN59.json',data['active_run_plan.json']),('ACTUAL_ENTRY_BINDING_REVIEW.json',(json.dumps(out,indent=2)+'\n').encode())]:bounded_write(O/name,b.decode())
print(json.dumps({k:v for k,v in out.items()if k!='entry'}));print(json.dumps(entry))
