from pathlib import Path
import json,subprocess,resource,hashlib,time
p=Path(__file__).resolve().parent;source=Path('/home/codextransfer/predictive_motion/results/phase5/session-controlled-stop-merged-hint-diag-active32-brake64-dwell25-v2-20261016-attempt60/src');inputs=[q for q in p.iterdir()if q.is_file()]+[q for q in source.iterdir()if q.is_file()];before={str(q):{'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()}for q in inputs};records=[]
def limits(cpu,mem,fs):
 def f():
  for k,v in [(resource.RLIMIT_CPU,cpu),(resource.RLIMIT_AS,mem),(resource.RLIMIT_FSIZE,fs),(resource.RLIMIT_CORE,0)]:resource.setrlimit(k,(v,v))
 return f
def run(label,args,cpu=25,mem=512*1024**2,fs=16*1024**2,wall=30):
 start=time.monotonic()
 with(p/(label+'.stdout')).open('xb')as out,(p/(label+'.stderr')).open('xb')as err:r=subprocess.run(args,stdin=subprocess.DEVNULL,stdout=out,stderr=err,timeout=wall,preexec_fn=limits(cpu,mem,fs))
 records.append({'label':label,'exit':r.returncode,'wall_s':time.monotonic()-start,'argv':args,'CPU':cpu,'AS':mem,'FSIZE':fs,'wallcap':wall});(p/'RESULT_PREFIX.json').write_text(json.dumps(records,indent=2));assert r.returncode==0,(p/(label+'.stderr')).read_text();print(label,r.returncode,flush=True)
for name,cpp in [('baseline','baseline61.cpp'),('dual','dual61_probe.cpp')]:
 run(name+'_compile',['g++','-std=c++17','-O2','-DNDEBUG','-fno-fast-math','-ffp-contract=off','-I/usr/include/eigen3','-I'+str(source),str(p/cpp),'-o',str(p/name)],90,2*1024**3,32*1024**2,100)
run('baseline_run',[str(p/'baseline'),str(p/'actual60_current43_trial0.initialized.fixture'),str(p/'baseline')]);assert(p/'baseline.finalxy.bin').read_bytes()==(p/'ACTUAL_PARTIAL_XY.bin').read_bytes();assert(p/'baseline.states.bin').read_bytes()==(p/'ACTUAL_EVENTS56.bin').read_bytes();assert(p/'baseline.faces16.bin').read_bytes()==(p/'ACTUAL_FINAL_FACES16.bin').read_bytes()
run('dual_run',[str(p/'dual'),str(p/'actual60_current43_trial0.initialized.fixture'),str(p/'ACTUAL_PARTIAL_XY.bin'),str(p/'RECONSTRUCTED_LAST_STATIONARY_FACES16.bin'),str(p/'dual')]);assert all(q.stat().st_size==before[str(q)]['bytes']and hashlib.sha256(q.read_bytes()).hexdigest()==before[str(q)]['sha256']for q in inputs)
(p/'RESULT.json').write_text(json.dumps({'schema':'PURE61_SAVED60_BASELINE_EXACT_AND_NONNEGATIVE_DUAL_CERTIFICATE_PROBE_V1','records':records,'input_pins':before,'input_before_after_equal':True,'old_partial_xy_all512events_and_finalfaces_bitexact':True,'scope':'Old numeric source replay plus finite auxiliary dual-search diagnostic at saved fixed primal. NNLS factor updates only, no actual-state/control/candidate projection. Cert success is direct original primal/dual-sign/stationarity, not process exit. No Model/nativeOSQP/B/C/physical/task/phase acceptance; new native source61 not prepared.'},indent=2));print((p/'baseline_run.stdout').read_text());print((p/'dual_run.stdout').read_text())
