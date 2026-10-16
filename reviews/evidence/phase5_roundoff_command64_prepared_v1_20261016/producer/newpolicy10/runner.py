from pathlib import Path
import json,hashlib,resource,subprocess,time
p=Path(__file__).resolve().parent;d=json.loads((p/'PLAN.json').read_text());paths=sorted(set([q for q in p.iterdir()if q.is_file()]+[Path(x['requested_path'])for x in d['input_files']]+list(map(Path,d['fixtures'].values()))));before={str(q):{'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()}for q in paths}
for x in d['input_files']:assert before[x['requested_path']]=={'bytes':x['bytes'],'sha256':x['sha256']}
assert before[str(p/'actual63_first7_contraction.bin')]['sha256']==d['fixture_local_sha256'];rows=[]
def limits(cpu,mem,fs):
 def f():
  for k,v in [(resource.RLIMIT_CPU,cpu),(resource.RLIMIT_AS,mem),(resource.RLIMIT_FSIZE,fs),(resource.RLIMIT_CORE,0)]:resource.setrlimit(k,(v,v))
 return f
def run(label,argv,cpu,mem,fs,wall):
 start=time.monotonic()
 with(p/(label+'.stdout')).open('xb')as out,(p/(label+'.stderr')).open('xb')as err:x=subprocess.run(argv,stdin=subprocess.DEVNULL,stdout=out,stderr=err,timeout=wall,preexec_fn=limits(cpu,mem,fs))
 rows.append({'label':label,'exit':x.returncode,'wall_s':time.monotonic()-start,'CPU':cpu,'AS':mem,'FSIZE':fs,'wallcap':wall});(p/'RESULT_PREFIX.json').write_text(json.dumps(rows,indent=2));assert x.returncode==0,(p/(label+'.stderr')).read_text();print(label,x.returncode,flush=True)
run('compile',d['compile'],90,2*1024**3,32*1024**2,100);run('link',d['link'],30,2*1024**3,32*1024**2,40)
for name,fixture in d['fixtures'].items():
 run(name,[str(p/'replay'),fixture,str(p/name),str(63 if name.startswith('actual63')else 43 if name=='actual60_43_0'else 74 if name=='actual58_74_0'else 54 if name=='actual58_54_0'else 0),'0'],25,512*1024**2,16*1024**2,30);assert 'complete=1 error=""'in(p/(name+'.stdout')).read_text(),'true math completeness required separately'
assert all(q.stat().st_size==before[str(q)]['bytes']and hashlib.sha256(q.read_bytes()).hexdigest()==before[str(q)]['sha256']for q in paths);(p/'RESULT.json').write_text(json.dumps({'records':rows,'input_before_after_equal':True,'all10_true_numerical_complete':True,'scope':'Ten saved pure numerical newpolicy cases incl actual63 oldbounds numericalfix alone and actual63 new7bounds combined. Original512/10s/16384/1e-12 unchanged; no Model/nativeOSQP/B/C/physical-stop/native64/phase acceptance.'},indent=2));print('All10 saved numerical cases complete; no Model/nativeOSQP/B/C/physics')
