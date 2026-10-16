from pathlib import Path
import sys,os,json,hashlib,shlex,subprocess,base64
sys.path.insert(0,'/private/tmp');from bounded_derived_bytes53_v1 import bounded_write
O=Path('/private/tmp/root62_stop_cause_review_v1_20261016');os.environ['P5_DERIVED53_ROOT']=str(O);P=Path('/private/tmp/phase5_current_braking_nominal62_source_v3_20261016');remote=json.loads((P/'REMOTE62.json').read_text())['remote'];relative=[f'{d}/{n}'for d in['build-attempt1','link-attempt1']for n in['BEFORE_INPUT_IDENTITIES.json','AFTER_INPUT_IDENTITIES.json','BUILD_RESULT.json']]
code='''from pathlib import Path
import os,json,hashlib,base64
root=Path(ROOT);out=[]
for name in NAMES:
 p=root/name;fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW)
 try:
  a=os.fstat(fd);assert a.st_size<=4194304;b=os.read(fd,4194305);z=os.fstat(fd);assert(a.st_ino,a.st_size,a.st_mtime_ns)==(z.st_ino,z.st_size,z.st_mtime_ns)and len(b)==a.st_size
 finally:os.close(fd)
 out.append({'path':name,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'data':base64.b64encode(b).decode()})
print(json.dumps(out))'''.replace('ROOT',repr(remote)).replace('NAMES',repr(relative))
r=subprocess.run(['/Users/uot/Documents/ChatGPT/ros/tools/dell-ssh.sh','-T','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','DellTransfer','python3 -I -S -B -c '+shlex.quote(code)],capture_output=True,timeout=25);assert r.returncode==0,r.stderr.decode();rows=json.loads(r.stdout);got={}
for e in rows:
 b=base64.b64decode(e['data']);assert len(b)==e['bytes']and hashlib.sha256(b).hexdigest()==e['sha256'];got[e['path']]=b;bounded_write(O/('PRODUCER62V3_'+e['path'].replace('/','_')),b.decode())
facts=[]
for d,n in[('build-attempt1',38),('link-attempt1',27)]:
 assert got[d+'/BEFORE_INPUT_IDENTITIES.json']==got[d+'/AFTER_INPUT_IDENTITIES.json'];j=json.loads(got[d+'/BUILD_RESULT.json']);facts.append(dict(directory=d,expected_units=n,result_keys=list(j),result=j))
bounded_write(O/'BUILD38_LINK27_ORIGINAL_SSH_READBACK.json',json.dumps(dict(schema='ROOT62V3_BUILD_LINK_ORIGINAL_SSH_READBACK_V1',six_metadata_SHA_size_stable_fd_verified=True,input_before_after_bytes_equal=True,results=facts,scope='Compiler/link results only, not controller or stopping acceptance.'),indent=2)+'\n');print(json.dumps([{k:v for k,v in x['result'].items()if k not in['input_files','commands','compile_units','results']}for x in facts])[:4000])
