from pathlib import Path
import os,sys,json,importlib.util,hashlib
sys.path.insert(0,'/private/tmp')
from bounded_derived_bytes53_v1 import bounded_write_bytes,bounded_write
O=Path('/private/tmp/root65_mac_consumer_review_v2_20261016')
os.environ['P5_DERIVED53_ROOT']=str(O)
sp=importlib.util.spec_from_file_location('consumer',Path('/Users/uot/Documents/ChatGPT/ros/tools/cold_stream_backup_v1/mac_consumer.py'))
m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
M=Path('/private/tmp/phase5_direct_stream65_fixture_test1_20261016/metadata')
A=O/'ARCHIVE_ALLOCATION.json'
if not A.exists():bounded_write(A,json.dumps({'scope':'fresh real SSH protocol cases only, not native65','aggregate_archive_attempt_cap':16<<20,'test1_reserved_before_attempt':8<<20,'pipe_failure_case_reserved_before_attempt':8<<20,'no_refund_or_retry':True},indent=2)+'\n')
T=O/'tampered-metadata';T.mkdir()
for p in M.iterdir():
 b=p.read_bytes()
 if p.name=='STREAM_PREPARED.json':
  v=json.loads(b);key=next(n for n in v['metadata_members'] if n.startswith('direct_mac_archive_producer'));v['metadata_members'][key]['sha256']='0'*64;b=(json.dumps(v,indent=2)+'\n').encode()
 bounded_write_bytes(T/p.name,b)
sentinel=O/'MUST_NOT_START_PRODUCER'
try:
 m.copy_stream(T,O/'tampered-destination',O/'tampered-report',[sys.executable,'-c',f'from pathlib import Path;Path({str(sentinel)!r}).touch()'],wall=30)
 raise AssertionError('tampered identity accepted')
except ValueError as e:
 assert str(e).startswith('declared metadata member identity mismatch: '),repr(e)
 assert not sentinel.exists() and not (O/'tampered-destination').exists()
 assert not m.safe_name('a'+chr(0)+'b') and not m.safe_name('../a') and m.safe_name('native65/a.bin')
 bounded_write(O/'TAMPERED_METADATA_REJECTED_BEFORE_PRODUCER.json',json.dumps({'pass':True,'error':str(e),'producer_not_started':True,'NUL_path_rejected':True},indent=2)+'\n')
cmd=['/Users/uot/Documents/ChatGPT/ros/tools/dell-ssh.sh','-T','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','-o','ConnectionAttempts=1','DellTransfer','python3 -I -S -B /home/codextransfer/predictive_motion/transfer/cold-archives/protocol65-direct-stream-test1-20261016/direct_mac_archive_producer65_v4.py stream']
bounded_write(O/'REAL_SSH_COMMAND.json',json.dumps(cmd,indent=2)+'\n')
r=m.copy_stream(M,O/'real-ssh-positive',O/'real-ssh-positive-report',cmd,Path('/private/tmp/phase5_stop53_combined_derived_budget_v1_20261015'),wall=120)
print(json.dumps(r,indent=2))
