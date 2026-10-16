from pathlib import Path
import sys,os,json,subprocess,selectors,time,signal
M=Path(__file__).resolve().parent
assert not(M/'STREAM_CONSUMED.json').exists(),'fresh once fixture only'
p=subprocess.Popen([sys.executable,'-I','-S','-B',str(M/'direct_mac_archive_producer65_v4.py'),'stream'],stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
prefix=bytearray()
while len(prefix)<8192:
 b=p.stdout.read(8192-len(prefix))
 if not b:break
 prefix.extend(b)
p.stdout.close();p.stdout=None;sel=selectors.DefaultSelector();sel.register(p.stderr,selectors.EVENT_READ);error=bytearray();start=time.monotonic()
while sel.get_map():
 if time.monotonic()-start>30:p.kill();raise TimeoutError('test-only failed pipe child cleanup30s')
 for key,_ in sel.select(.1):
  b=os.read(key.fileobj.fileno(),65536)
  if not b:sel.unregister(key.fileobj)
  else:assert len(b)<=65536-len(error);error.extend(b)
rc=p.wait(timeout=3);assert rc!=0 and(M/'STREAM_FAILURE.json').is_file()and(M/'STREAM_CONSUMED.json').is_file()and not(M/'STREAM_SENT.json').exists()
record={'purpose':'PROTOCOL_TEST_ONLY','intentional_child_output_pipe_closed_after_bytes':len(prefix),'producer_exit':rc,'producer_failure_preserved':True,'stderr':error.decode(errors='replace')[-12000:],'no_native_or_Model':True,'no_retry_refund_or_READY':True}
b=(json.dumps(record,indent=2)+'\n').encode();assert len(b)<=16384 and sum(q.stat().st_size for q in M.iterdir()if q.is_file())+len(b)<=1048576
with(M/'PIPE_FAILURE_WRAPPER_RESULT.json').open('xb')as f:f.write(b);f.flush();os.fsync(f.fileno())
# Emit the already-preserved real producer failed prefix once for Mac consumer rejection.
at=0
while at<len(prefix):at+=os.write(1,prefix[at:])
sys.stderr.write(json.dumps(record)+'\n');sys.stderr.flush();raise SystemExit(73)
