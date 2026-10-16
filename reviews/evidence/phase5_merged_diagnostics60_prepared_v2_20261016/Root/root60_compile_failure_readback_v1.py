from pathlib import Path
import sys,os,json,hashlib,base64,subprocess,shlex
sys.dont_write_bytecode=True;sys.path.insert(0,'/private/tmp')
from bounded_derived_bytes53_v1 import bounded_write
P=Path('/private/tmp/phase5_merged_hint_diagnostics60_source_v1_20261016');O=Path('/private/tmp/root60_merged_review_v1_20261016');os.environ['P5_DERIVED53_ROOT']=str(O);remote=json.loads((P/'REMOTE60.json').read_text())['remote']
code='''from pathlib import Path
import json,base64,hashlib
p=Path(REMOTE);out={}
for n in ['BUILD_FAILURE.json','BUILD_RESULT.json','BATCH_PREFIX.json','compile-36.result.json','compile-36.stderr','compile-36.stdout','BEFORE_INPUT_IDENTITIES.json','AFTER_INPUT_IDENTITIES.json']:
 q=p/'build-attempt1'/n
 if q.exists():
  b=q.read_bytes();assert len(b)<=2*1024**2;out[n]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'data':base64.b64encode(b).decode()}
print(json.dumps({'files':out,'entry_exists':(p/'ENTRY_CONSUMED60.json').exists(),'native_run_exists':(p/'run-attempt1').exists()}))'''.replace('REMOTE',repr(remote))
r=subprocess.run(['/Users/uot/Documents/ChatGPT/ros/tools/dell-ssh.sh','-T','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','DellTransfer','python3 -I -S -B -c '+shlex.quote(code)],capture_output=True,timeout=20);assert r.returncode==0,r.stderr.decode();assert len(r.stdout)<=8*1024**2;result=json.loads(r.stdout);assert not result['entry_exists']and not result['native_run_exists'];data={}
for name,e in result['files'].items():
 b=base64.b64decode(e['data']);assert len(b)==e['bytes']and hashlib.sha256(b).hexdigest()==e['sha256'];data[name]=b;bounded_write(O/('FAILED_V1_'+name),b.decode())
summary=dict(schema='ROOT60_V1_REAL_COMPILER_FAILURE_PRESERVED_V1',remote=remote,entry_exists=False,native_run_exists=False,files={k:dict(bytes=len(v),sha256=hashlib.sha256(v).hexdigest())for k,v in data.items()},scope='Failed36th test compilation from bad generator, not native simulation. Frozen v1 source and every available original build failure file retained; newv2 target is separate, no consumed59 replay.')
bounded_write(O/'FAILED_V1_READBACK_INDEX.json',json.dumps(summary,indent=2)+'\n');print(json.dumps(dict(files=list(data),entry=False,run=False)))
for name in ['BUILD_FAILURE.json','BATCH_PREFIX.json','compile-36.result.json']:
 if name in data:
  j=json.loads(data[name]);print(name,'keys',list(j));print({k:v for k,v in j.items()if k in ['complete','stage','exit','error','first_error','stop_reason']})
