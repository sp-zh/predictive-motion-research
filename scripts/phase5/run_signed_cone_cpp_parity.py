#!/usr/bin/env python3
import csv,datetime,hashlib,json,math,random,subprocess,sys
from pathlib import Path
p=Path('/home/codextransfer/predictive_motion');base=p/'results/phase5/development/signed-command-cone-cpp-v1';base.mkdir(exist_ok=False);sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
oracle=p/'scripts/phase5/signed_command_velocity_cone.py';old=json.loads((p/'results/phase5/development/signed-command-cone-v1/frozen.json').read_text());assert sha(oracle)==old['files'][str(oracle)]
sys.path.insert(0,str(oracle.parent));from signed_command_velocity_cone import acceleration_interval,candidate_velocity_rows,continuation_stop
raw=Path('/mnt/d/CodexTransfer/projects/predictive_motion/phase5/raw/servo-safe-reference-v1-validation/raw.csv');cases=[]
for row in csv.DictReader(raw.open()):
 if int(row['substep'])==2 and int(row['tick'])>=760:cases.append((float(row['command_velocity_3']),float(row['command_acceleration_3']),.0625,1.,20.,.004))
for w,a in [(0,0),(.0625,0),(-.0625,0),(.062,.16),(-.061980006326262695,-.51999999999999091),(.0625000001,0),(0,1.00000001)]:cases.append((w,a,.0625,1.,20.,.004))
rng=random.Random(20261010)
for _ in range(2000):
 V,A,J,dt=rng.choice([(.0625,1.,20.,.004),(.1,.9,25.,.005),(.3,1.3,17.,.002)])
 cases.append((rng.uniform(-V,V),rng.uniform(-A,A),V,A,J,dt))
input_file=base/'cases.csv'
with input_file.open('x',newline='') as f:
 writer=csv.writer(f);writer.writerow(['case','w','alpha','V','A','J','dt'])
 for i,c in enumerate(cases):writer.writerow([i]+list(c))
expected=[]
for i,c in enumerate(cases):expected.append({'case':i,'interval':acceleration_interval(*c),'stop':continuation_stop(*c),'rows':candidate_velocity_rows(c[0],*c[2:])})
(base/'expected.json').write_text(json.dumps(expected)+'\n')
binary=p/'build-signed-command-cone-v1/signed_velocity_cone_probe';files=[oracle,Path(__file__),p/'tools/phase5_command_cone/signed_velocity_cone.hpp',p/'tools/phase5_command_cone/signed_velocity_cone_probe.cpp',p/'tools/phase5_command_cone/CMakeLists.txt',p/'build-signed-command-cone-v1/CMakeCache.txt',binary,input_file,base/'expected.json',raw]
freeze={'before_probe_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':{str(f):sha(f) for f in files},'scope':'Standalone C++ command-speed continuation parity only; no native solver/plant/main-MPC integration','oracle_previously_frozen':True,'compiler':subprocess.run(['/usr/bin/c++','--version'],capture_output=True,text=True).stdout.splitlines()[0]}
(base/'frozen.json').write_text(json.dumps(freeze,indent=2)+'\n')
proc=subprocess.run([str(binary),str(input_file),str(base/'actual.csv'),str(base/'actual_rows.csv')],capture_output=True,text=True);(base/'stdout.log').write_text(proc.stdout);(base/'stderr.log').write_text(proc.stderr)
assert proc.returncode==0,proc.stderr
actual=list(csv.DictReader((base/'actual.csv').open()));assert len(actual)==len(expected)
max_interval_error=0.;max_stop_error=0.;max_row_error=0.;failures=[]
for r,e in zip(actual,expected):
 feasible=bool(int(r['feasible']));assert int(r['case'])==e['case']
 if feasible!=(e['interval'] is not None):failures.append({'case':e['case'],'reason':'feasibility disagreement'});continue
 if feasible:
  error=max(abs(float(r[k])-v) for k,v in zip(('lower_acceleration','upper_acceleration'),e['interval']));max_interval_error=max(max_interval_error,error)
  error=max(abs(float(r[k])-v) for k,v in zip(('stop_velocity','stop_acceleration'),e['stop']));max_stop_error=max(max_stop_error,error)
expected_rows={(e['case'],K):(lo,hi) for e in expected for K,lo,hi in e['rows']};actual_rows=list(csv.DictReader((base/'actual_rows.csv').open()));assert len(actual_rows)==len(expected_rows)
for r in actual_rows:
 bounds=expected_rows[(int(r['case']),int(r['K']))];max_row_error=max(max_row_error,*[abs(float(r[k])-v) for k,v in zip(('lower','upper'),bounds)])
if max(max_interval_error,max_stop_error,max_row_error)>5e-14:failures.append({'reason':'numeric parity tolerance exceeded'})
unchanged=all(sha(f)==h for f,h in freeze['files'].items());assert unchanged
report={'gate':'PASS_ISOLATED_CPP_SPEED_CONE' if not failures else 'FAIL_RETAINED','cases':len(cases),'logged_rows':len(actual_rows),'max_interval_error':max_interval_error,'max_stop_error':max_stop_error,'max_row_error':max_row_error,'tolerance':5e-14,'failures':failures,'source_binary_inputs_unchanged':unchanged,'limitations':'Python mathematical contract parity, not independent native QP/plant test. Prior frozen mathematical contract had independent sequence tests. Command derivatives/position/geometry/physical guards separate; no main MPC integration or Phase5 acceptance.'}
(base/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));raise SystemExit(bool(failures))
