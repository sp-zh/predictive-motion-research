from pathlib import Path
import sys,os,json,subprocess,hashlib
sys.path.insert(0,'/private/tmp');from bounded_derived_bytes53_v1 import bounded_write
O=Path('/private/tmp/root61_actual_review_v1_20261016');os.environ['P5_DERIVED53_ROOT']=str(O)
code="""from pathlib import Path
import json,datetime,hashlib
p=Path('/home/codextransfer/predictive_motion/results/phase5/session-controlled-stop-exact-cycle-endpoint-active32-brake64-dwell25-v1-20261016-attempt61/offline61-status')
out={'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pids_exist':{str(n):Path('/proc/'+str(n)).exists()for n in [12433,12434,12435]},'files':{}}
for n in ['EXIT.json','MANUAL_WAIT_AFTER_61.json','READY.json']:
 b=(p/n).read_bytes();assert len(b)<1048576
 out['files'][n]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
 if n!='READY.json':out[n]=json.loads(b)
print(json.dumps(out))"""
import shlex
r=subprocess.run(['/Users/uot/Documents/ChatGPT/ros/tools/dell-ssh.sh','DellTransfer','python3 -B -c '+shlex.quote(code)],capture_output=True,timeout=25);assert r.returncode==0,r.stderr.decode();j=json.loads(r.stdout);assert not any(j['pids_exist'].values())and j['MANUAL_WAIT_AFTER_61.json']['direct_human_resume_required']and j['EXIT.json']['automatic_retries']==0
P=Path('/private/tmp/phase5_controlled_stop_exact_cycle_terminal61_v1_20261016');B=next(P.glob('actual-dell/*'))/'offline61-status'
for n,e in j['files'].items():
 b=(B/n).read_bytes();assert len(b)==e['bytes']and hashlib.sha256(b).hexdigest()==e['sha256']
j['scope']='Original fixed-hostkey SSH read-only terminal/hash check. Three known owned PIDs absent; selected packet EXIT/manualwait/READY exact remote bytes. No process signal, source mutation or retry. PID absence alone is not an all-process proof.'
bounded_write(O/'LIVE_TERMINAL_READBACK.json',json.dumps(j,indent=2)+'\n');print(json.dumps(j))
