from pathlib import Path
import os,sys,json,importlib.util,hashlib
sys.path.insert(0,'/private/tmp');from bounded_derived_bytes53_v1 import bounded_write
O=Path('/private/tmp/root65_mac_consumer_review_v2_20261016');os.environ['P5_DERIVED53_ROOT']=str(O)
sp=importlib.util.spec_from_file_location('consumer','/Users/uot/Documents/ChatGPT/ros/tools/cold_stream_backup_v1/mac_consumer.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
M=Path('/private/tmp/phase5_direct_stream65_fixture_test1_20261016/pipe_metadata')
p=json.loads((M/'STREAM_PREPARED.json').read_text());assert p['purpose']=='PROTOCOL_TEST_ONLY' and p['limits']['archive_bytes']==1<<20
cmd=['/Users/uot/Documents/ChatGPT/ros/tools/dell-ssh.sh','-T','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','-o','ConnectionAttempts=1','DellTransfer','python3 -I -S -B /home/codextransfer/predictive_motion/transfer/cold-archives/protocol65-direct-stream-test3-pipe-failure-20261016/PIPE_FAILURE_WRAPPER.py']
bounded_write(O/'PIPE_SSH_COMMAND.json',json.dumps(cmd,indent=2)+'\n')
D=O/'real-ssh-pipe-failure';R=O/'real-ssh-pipe-failure-report'
try:
 m.copy_stream(M,D,R,cmd,Path('/private/tmp/phase5_stop53_combined_derived_budget_v1_20261015'),wall=120)
 raise AssertionError('broken stream unexpectedly passed')
except (ValueError,EOFError,__import__('tarfile').ReadError) as e:
 part=D/'complete.tar.gz.part';assert part.exists() and part.stat().st_size==8192
 assert not (D/'READY.json').exists() and not (D/'complete.tar.gz').exists()
 f=json.loads((R/'FAILURE.json').read_text());assert f['no_retry_no_reset_no_refund'] and f['no_confirmed_READY_claim']
 r={'pass':True,'error':repr(e),'part_bytes':part.stat().st_size,'part_sha256':hashlib.sha256(part.read_bytes()).hexdigest(),'no_READY':True,'fresh_once_only':True,'prior_case_not_retried':True}
 bounded_write(O/'PIPE_FAILURE_EXPECTED_REJECTION.json',json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
