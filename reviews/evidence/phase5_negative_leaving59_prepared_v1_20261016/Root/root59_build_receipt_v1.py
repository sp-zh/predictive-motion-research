from pathlib import Path
import sys,os,json,subprocess,shlex,hashlib
sys.dont_write_bytecode=True;sys.path.insert(0,'/private/tmp')
from bounded_derived_bytes53_v1 import bounded_write
P=Path('/private/tmp/phase5_negative_leaving59_source_v1_20261016');O=Path('/private/tmp/root59_saved_review_v1_20261016');os.environ['P5_DERIVED53_ROOT']=str(O);remote=json.loads((P/'REMOTE59.json').read_text())['remote']
files=[d+'/'+n for d in ['build-attempt1','link-attempt1']for n in ['BUILD_RESULT.json','BEFORE_INPUT_IDENTITIES.json','AFTER_INPUT_IDENTITIES.json']]
code='''from pathlib import Path
import json,hashlib,base64
p=Path(REMOTE);out={}
for n in FILES:
 b=(p/n).read_bytes();assert len(b)<=2*1024**2;out[n]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'data':base64.b64encode(b).decode()}
print(json.dumps(out))'''.replace('REMOTE',repr(remote)).replace('FILES',repr(files))
r=subprocess.run(['tools/dell-ssh.sh','-T','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','DellTransfer','python3 -I -S -B -c '+shlex.quote(code)],capture_output=True,timeout=20);assert r.returncode==0,r.stderr.decode();assert len(r.stdout)<=8*1024**2
import base64
data=json.loads(r.stdout);proof=[]
for name,e in data.items():
 b=base64.b64decode(e['data']);assert len(b)==e['bytes']and hashlib.sha256(b).hexdigest()==e['sha256'];bounded_write(O/('PRODUCER_'+name.replace('/','_')),b.decode())
for d,count in [('build-attempt1',35),('link-attempt1',24)]:
 b=base64.b64decode(data[d+'/BEFORE_INPUT_IDENTITIES.json']['data']);a=base64.b64decode(data[d+'/AFTER_INPUT_IDENTITIES.json']['data']);assert b==a
 j=json.loads(base64.b64decode(data[d+'/BUILD_RESULT.json']['data']));assert j['complete']and len(j['records'])==count and all(x['exit_code']==0 for x in j['records'])
 proof.append(dict(stage=d,commands=count,complete=True,before_after_bytes_equal=True,runtime_invocations=j['runtime_invocations']))
bounded_write(O/'BUILD_LINK_REVIEW.json',json.dumps(dict(schema='ROOT59_ORIGINAL_SSH_BUILD_LINK_RESULTS_READBACK_V1',stages=proof,scope='Compile/link and input identities only; no new native motion or phase acceptance.'),indent=2)+'\n');print(json.dumps(proof))
