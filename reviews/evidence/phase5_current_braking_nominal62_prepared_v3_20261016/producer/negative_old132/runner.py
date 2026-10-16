from pathlib import Path
import json,resource,subprocess,time,hashlib
p=Path(__file__).resolve().parent;plan=json.loads((p/'PLAN.json').read_text());source=Path('/home/codextransfer/predictive_motion/results/phase5/session-controlled-stop-current-braking-nominal-active32-brake64-dwell25-v2-20261016-attempt62/src');inputs=[q for q in source.iterdir()if q.is_file()]+[q for q in p.iterdir()if q.is_file()]+[Path(x)for a in plan.values()for x in a if x.startswith('/')and Path(x).is_file()]+[Path('/home/codextransfer/predictive_motion/results/phase5/integrated-first-cycle-v1-20261010/runtime-profile-version2/inputs/public_constants.json')];inputs=list(dict.fromkeys(inputs));before={str(q):hashlib.sha256(q.read_bytes()).hexdigest()for q in inputs};rows=[]
def limits(cpu,mem,fs):
 def f():
  for k,v in [(resource.RLIMIT_CPU,cpu),(resource.RLIMIT_AS,mem),(resource.RLIMIT_FSIZE,fs),(resource.RLIMIT_CORE,0)]:resource.setrlimit(k,(v,v))
 return f
for label,argv,cpu,mem,fs,wall in [('compile',plan['compile'],90,2*1024**3,32*1024**2,100),('link',plan['link'],90,2*1024**3,32*1024**2,100),('run',[str(p/'onset'),str(p/'retained-failure')],25,512*1024**2,16*1024**2,30)]:
 start=time.monotonic()
 with(p/(label+'.stdout')).open('xb')as out,(p/(label+'.stderr')).open('xb')as err:r=subprocess.run(argv,stdin=subprocess.DEVNULL,stdout=out,stderr=err,timeout=wall,preexec_fn=limits(cpu,mem,fs))
 rows.append({'label':label,'exit':r.returncode,'wall_s':time.monotonic()-start,'CPU':cpu,'AS':mem,'FSIZE':fs,'wallcap':wall});(p/'RESULT_PREFIX.json').write_text(json.dumps(rows,indent=2));assert r.returncode==0,(p/(label+'.stderr')).read_text();print(label,r.returncode,flush=True)
assert all(hashlib.sha256(q.read_bytes()).hexdigest()==before[str(q)]for q in inputs);(p/'RESULT.json').write_text(json.dumps({'schema':'SAVED32_V2_REAL_SOURCE132_REFUSAL_PREFIX_ONLY_V1','rows':rows,'input_before_after_equal':True,'scope':'Expected old V2 planner failure, process0 not a feasible plan. Prefix source incomplete retained; no Model/native/stop acceptance.'},indent=2));print((p/'run.stdout').read_text())
