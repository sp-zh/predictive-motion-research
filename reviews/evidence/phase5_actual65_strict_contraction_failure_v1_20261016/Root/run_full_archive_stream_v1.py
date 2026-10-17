from pathlib import Path
import os,sys,json,importlib.util,hashlib
sys.path.insert(0,'/private/tmp');from bounded_derived_bytes53_v1 import bounded_write
O=Path('/private/tmp/root65_actual_review_v1_20261016');os.environ['P5_DERIVED53_ROOT']=str(O)
M=Path('/private/tmp/phase5_physical_braking65_source_v1_20261016/postnative65-metadata-readback-v1')
assert hashlib.sha256((M/'STREAM_PREPARED.json').read_bytes()).hexdigest()=='b0d58dbf0834a7a965bbf52144206ab554e7c9a7db0ddc221a40a234d7934847'
D=Path('/Users/uot/Documents/ChatGPT/ros/transfer/cold-backups/native65-complete-direct-mac-20261016-v1')
bounded_write(O/'SINGLE_ARCHIVE_ALLOCATION_BEFORE_STREAM.json',json.dumps({'archive_aggregate_cap':4<<30,'payload_cap':7<<29,'tar_raw_cap':17<<28,'metadata_cap':16<<20,'reserve':33<<30,'attempts':1,'failed_part_stays_charged':True,'no_retry_no_reset_no_refund':True,'producer_prepare_sha256':'b0d58dbf0834a7a965bbf52144206ab554e7c9a7db0ddc221a40a234d7934847','destination':str(D),'format':'Dell immutable originals plus Mac complete verified tar, no second Dell tar stock'},indent=2)+'\n')
sp=importlib.util.spec_from_file_location('consumer','/Users/uot/Documents/ChatGPT/ros/tools/cold_stream_backup_v1/mac_consumer.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
cmd=['/Users/uot/Documents/ChatGPT/ros/tools/dell-ssh.sh','-T','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','-o','ConnectionAttempts=1','DellTransfer','python3 -I -S -B /home/codextransfer/predictive_motion/transfer/cold-archives/native65-direct-mac-20261016-v1/direct_mac_archive_producer65_v5.py stream']
bounded_write(O/'EXACT_ONCE_STREAM_ARGV.json',json.dumps(cmd,indent=2)+'\n')
r=m.copy_stream(M,D,O/'full-archive-readback',cmd,Path('/private/tmp/phase5_stop53_combined_derived_budget_v1_20261015'),wall=1200)
print(json.dumps(r,indent=2))
