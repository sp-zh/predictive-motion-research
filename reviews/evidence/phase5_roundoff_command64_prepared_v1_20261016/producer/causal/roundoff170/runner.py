from pathlib import Path
import sys,json,hashlib,subprocess,resource,time
p=Path(__file__).resolve().parent;plan=json.loads((p/'PLAN.json').read_text());rows=[];inputs={str(q):{'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()}for q in [Path(x['requested_path'])for x in plan['input_files']]}
for x in plan['input_files']:assert inputs[x['requested_path']]=={'bytes':x['bytes'],'sha256':x['sha256']}
assert hashlib.sha256((p/'fixture.bin').read_bytes()).hexdigest()==plan['fixture_sha256']
def limits(cpu,mem,fs):
 def f():
  for k,v in [(resource.RLIMIT_CPU,cpu),(resource.RLIMIT_AS,mem),(resource.RLIMIT_FSIZE,fs),(resource.RLIMIT_CORE,0)]:resource.setrlimit(k,(v,v))
 return f
for label,argv,cpu,mem,fs,wall in [('compile',plan['compile'],90,2*1024**3,32*1024**2,100),('link',plan['link'],30,2*1024**3,32*1024**2,40),('replay',[str(p/'replay'),str(p/'fixture.bin'),str(p/'case'), '63','0'],30,1024**3,16*1024**2,40)]:
 start=time.monotonic()
 with(p/(label+'.stdout')).open('xb')as out,(p/(label+'.stderr')).open('xb')as err:r=subprocess.run(argv,stdin=subprocess.DEVNULL,stdout=out,stderr=err,preexec_fn=limits(cpu,mem,fs),timeout=wall)
 rows.append({'label':label,'exit':r.returncode,'wall_seconds':time.monotonic()-start,'cpu':cpu,'mem':mem,'filecap':fs,'wallcap':wall});(p/'RESULT_PREFIX.json').write_text(json.dumps(rows,indent=2));assert r.returncode==0,(p/(label+'.stderr')).read_text();print(label,r.returncode,flush=True)
assert 'complete=1 error=""'in(p/'replay.stdout').read_text();assert all(Path(q).stat().st_size==x['bytes']and hashlib.sha256(Path(q).read_bytes()).hexdigest()==x['sha256']for q,x in inputs.items());(p/'RESULT.json').write_text(json.dumps({'records':rows,'probe_numerically_complete':True,'inputs_before_after_equal':True,'scope':plan['scope']},indent=2));print((p/'replay.stdout').read_text())
