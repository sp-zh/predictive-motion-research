#!/usr/bin/env python3
import datetime,hashlib,json,subprocess,sys,csv
from pathlib import Path
p=Path('/home/codextransfer/predictive_motion');base=p/'results/phase5/development/signed-command-cone-v1';base.mkdir(exist_ok=False);sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
files=[p/'scripts/phase5/signed_command_velocity_cone.py',p/'scripts/phase5/signed_command_velocity_cone_test.py',Path(__file__),p/'src/predictive_motion_control/src/predictive.cpp',Path('/mnt/d/CodexTransfer/projects/predictive_motion/phase5/raw/servo-safe-reference-v1-validation/raw.csv')]
(base/'frozen.json').write_text(json.dumps({'before_tests_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':{str(f):sha(f) for f in files},'limits':{'V':.0625,'A':1.,'J':20.,'dt':.004},'scope':'Isolated signed-command speed continuation mathematics only; no geometry/position stop guarantee; no plant/main-MPC integration'},indent=2)+'\n')
proc=subprocess.run([sys.executable,str(files[1])],text=True,capture_output=True);(base/'tests.stdout').write_text(proc.stdout);(base/'tests.stderr').write_text(proc.stderr)
sys.path.insert(0,str(p/'scripts/phase5'));from signed_command_velocity_cone import acceleration_interval
rows=[r for r in csv.DictReader(files[-1].open()) if int(r['substep'])==2];bad=[]
for r in rows:
 if int(r['tick'])<500:continue
 for j in range(7):
  w=float(r['command_velocity_'+str(j)]);a=float(r['command_acceleration_'+str(j)])
  if acceleration_interval(w,a,.0625,1.,20.,.004) is None:bad.append({'tick':int(r['tick']),'joint':j,'w':w,'alpha':a})
report={'return_code':proc.returncode,'test_scope':'Independent maximum-jerk sequences, reflection, hard boundaries, actual failed history, one-step-feasible/future-infeasible candidate, repeated stops and QP-row equivalence; no native QP/real plant','retained_source_input_sha256':sha(files[-1]),'first_noncontinuable_history':bad[0] if bad else None,'noncontinuable_histories':bad,'source_unchanged':all(sha(f)==json.loads((base/'frozen.json').read_text())['files'][str(f)] for f in files),'status':'PASS_ISOLATED_SPEED_CONE' if proc.returncode==0 else 'FAIL_RETAINED','main_MPC_integrated':False,'phase5_accepted':False}
(base/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(proc.stderr);print(json.dumps(report,indent=2));raise SystemExit(proc.returncode)
