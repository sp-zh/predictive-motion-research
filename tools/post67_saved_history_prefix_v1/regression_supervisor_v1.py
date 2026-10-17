from pathlib import Path
import os,json,hashlib,subprocess,resource,ctypes,selectors,time,signal
D=Path('/mnt/d/CodexTransfer/post67-command-history-v1-20261016/saved64');B=D.parent/'build96/targeted-build-attempt1';case=os.environ['SAVED_CASE'];assert case in ['32','95'];assert time.time()<1792203097.37632;assert json.loads((B/'BUILD_RESULT.json').read_text())['complete'];P=D/('regression'+case+'-attempt1');P.mkdir(exist_ok=False);assert not(D/('REGRESSION'+case+'_CONSUMED.json')).exists()
with(D/('REGRESSION'+case+'_CONSUMED.json')).open('x')as f:json.dump({'cap':2*1024**2,'maximum_native_saved_QP_calls':2,'native_controller_or_Model_calls':0,'binary_output_roster':['case.baseline.native.bin','case.baseline.U.bin','case.new.hint.bin','case.inward.native.bin','case.inward.U.bin'],'per_child_file_cap':262144,'stdout_and_stderr_each_cap':131072,'metadata_cap':1048576,'no_retry_reset_or_refund':True},f);f.flush();os.fsync(f.fileno())
def sha(q):
 h=hashlib.sha256();n=0
 with q.open('rb')as f:
  while b:=f.read(65536):h.update(b);n+=len(b)
 return {'path':str(q),'bytes':n,'sha256':h.hexdigest()}
inputs=[D/('fixture'+case+'.bin'),B/'saved_jerk_native',D.parent/'build96/source/history_prefix_v1.hpp',D.parent/'build96/source/saved_prefix_native.cpp',D/('hint'+case+'.bin'),D/('candidate'+case+'.bin')];before=[sha(p)for p in inputs]
libc=ctypes.CDLL(None,use_errno=True)
class Rules(ctypes.Structure):_fields_=[('handled',ctypes.c_uint64)]
class Rule(ctypes.Structure):_pack_=1;_fields_=[('allowed',ctypes.c_uint64),('parent_fd',ctypes.c_int32)]
def limits():
 for k,n in [(resource.RLIMIT_CPU,90),(resource.RLIMIT_AS,1024**3),(resource.RLIMIT_FSIZE,262144),(resource.RLIMIT_CORE,0)]:resource.setrlimit(k,(n,n))
 fd=libc.syscall(444,ctypes.byref(Rules((1<<1)|sum(1<<b for b in range(4,15)))),ctypes.sizeof(Rules),0);assert fd>=0;root=os.open(P,os.O_PATH|os.O_CLOEXEC);rule=Rule((1<<1)|(1<<7)|(1<<8)|(1<<14),root);assert libc.syscall(445,fd,1,ctypes.byref(rule),0)==0;os.close(root);assert libc.prctl(38,1,0,0,0)==0 and libc.syscall(446,fd,0)==0;os.close(fd)
argv=[str(B/'saved_jerk_native'),str(D/('fixture'+case+'.bin')),str(P/'case'),str(D/('hint'+case+'.bin')),str(D/('candidate'+case+'.bin'))];started=time.monotonic();p=subprocess.Popen(argv,cwd=P,env={'PATH':'/usr/bin:/bin','LANG':'C','LC_ALL':'C','TZ':'UTC','TMPDIR':str(D/'scratch-never-writable')},stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True,close_fds=True,preexec_fn=limits);sel=selectors.DefaultSelector();sel.register(p.stdout,selectors.EVENT_READ,'out');sel.register(p.stderr,selectors.EVENT_READ,'err');capt={'out':bytearray(),'err':bytearray()};failure=None
try:
 while sel.get_map():
  if time.time()>=1792203097.37632 or time.monotonic()-started>120:raise TimeoutError('finite saved-only batch120s')
  for key,_ in sel.select(.1):
   b=os.read(key.fileobj.fileno(),65536)
   if not b:sel.unregister(key.fileobj);continue
   assert len(b)<=131072-len(capt[key.data]);capt[key.data].extend(b)
 rc=p.wait(timeout=5)
except BaseException as e:
 failure=repr(e);os.killpg(p.pid,signal.SIGKILL);rc=p.wait(timeout=5)
finally:sel.close();p.stdout.close();p.stderr.close()
for key,b in capt.items():
 with(P/('regression.std'+key)).open('xb')as f:f.write(b);f.flush();os.fsync(f.fileno())
after=[sha(q)for q in inputs];report={'schema':'SAVED66_JERK_INTERIOR_ACTUAL_HINT_NATIVE_REGRESSION_ANALYSIS3_V1','argv':argv,'exit':rc,'failure':failure,'wall':time.monotonic()-started,'before':before,'after':after,'inputs_before_after_equal':before==after,'stdout':capt['out'].decode(),'stderr':capt['err'].decode(),'outputs':[sha(q)for q in P.iterdir()if q.is_file()],'no_Model_or_controller68':True,'case':case,'saved_only_recorded_candidate_progress_not_online_nominal':True,'no_original66_file_modified':True};assert len(json.dumps(report).encode())<1048576
with(P/'RESULT.json').open('x')as f:json.dump(report,f,indent=2);f.flush();os.fsync(f.fileno())
assert sum(q.stat().st_size for q in D.rglob('*')if q.is_file())<=64*1024**2;print(json.dumps(report));assert before==after and rc==0
