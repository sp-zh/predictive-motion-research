from pathlib import Path
import hashlib,json,subprocess,os,sys,time,csv
p=Path('/home/codextransfer/predictive_motion')
e=p/'results/phase5/development/moving-stop-v1';e.mkdir(exist_ok=False)
sha=lambda x:hashlib.sha256(Path(x).read_bytes()).hexdigest()
old=json.loads((p/'results/phase5/development/reference-v14/frozen.json').read_text())
current={};checked=[]
for name,digest in old['files'].items():
 x=Path(name)
 if not x.exists():raise RuntimeError('original identity missing '+name)
 current[name]=sha(x)
 if any(part in name for part in ['/models/','/experiments/generated/','/cad/generated/',
       '/.vendor/menagerie/franka_fr3/','/.vendor/mujoco-3.3.7/',
       '/config/phase5_reference.yaml','/results/cad/path_screening_aabb/feasible_path.csv',
       '/benchmarks/reference/inspection_curve.json','/lib/libplant.a','/lib/librobot_kinematics.a']):
  assert current[name]==digest,'Replay physical input changed '+name
  checked.append(name)
for x in [p/'tools/phase5_adapter/moving_stop_replay.cpp',p/'tools/phase5_adapter/CMakeLists.txt',
          p/'build-phase5-adapter/moving_stop_replay',p/'results/phase5/development/moving-stop-input/raw.csv',
          Path(__file__)]:current[str(x)]=sha(x)
freeze={'files':current,'scope':'exact v14 accepted-command replay followed by shared moving-stop component test',
 'physical_identity_matches_v14':checked,'frozen_before_run_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
(e/'frozen.json').write_text(json.dumps(freeze,indent=2)+'\n')
sys.path.insert(0,str(p/'scripts/phase5'));from materialize_identity import materialize
materialize(e/'frozen.json')
raw=Path('/mnt/d/CodexTransfer/projects/predictive_motion/phase5/raw/moving-stop-v1')
assert not raw.exists()
argv=[str(p/'build-phase5-adapter/moving_stop_replay'),str(p),str(p/'config/phase5_reference.yaml'),
      'predictive','inspection','91011',str(raw)]
env=dict(os.environ);env['LD_LIBRARY_PATH']=str(p/'.vendor/mujoco-3.3.7/lib')+':'+env.get('LD_LIBRARY_PATH','')
start=time.monotonic()
with (e/'stdout.log').open('w') as out,(e/'stderr.log').open('w') as err:
 code=subprocess.call(argv,stdout=out,stderr=err,env=env,cwd=p)
meta={'argv':argv,'return_code':code,'wall_s':time.monotonic()-start,
 'raw_files':{x.name:sha(x) for x in raw.iterdir() if x.is_file()}}
(e/'execution.json').write_text(json.dumps(meta,indent=2)+'\n')
print(json.dumps(meta))
if (raw/'summary.yaml').exists():print((raw/'summary.yaml').read_text())
assert code==0,(e/'stderr.log').read_text()
errors=list(csv.DictReader((raw/'replay_error.csv').open()))
rows=list(csv.DictReader((raw/'raw.csv').open()))
assert len(errors)==1390 and len([x for x in rows if x['phase']=='recorded_command_replay'])==1390
assert all(float(x['q_max_error'])<=1e-10 and float(x['dq_max_error'])<=1e-10 for x in errors)
stop=[x for x in rows if x['phase']=='stopping'];assert stop and rows[-1]['phase']=='stopping'
assert all(x['stop_status']=='SOLVED' and x['command_issued']=='1' for x in stop)
assert all(int(x['contacts'])==0 and float(x['true_clearance_m'])>=.005 for x in rows)
for x in stop:
 assert float(x['r'])>=0 and 0<=float(x['s'])<=1
 assert abs(float(x['b']))<=.5+1e-12
 for i in range(7):
  assert abs(float(x[f'command_acc_{i}']))<=1+1e-6
  assert abs(float(x[f'command_jerk_{i}']))<=20+1e-6
prior_b=float(next(x for x in rows if x['tick']=='694' and x['substep']=='2')['b'])
for x in stop:
 if x['substep']=='2':
  assert abs((float(x['b'])-prior_b)/.004)<=5+1e-10
  prior_b=float(x['b'])
last=stop[-1]
assert float(last['r'])<1e-6 and abs(float(last['b']))<1e-3
assert max(abs(float(last[f'dq_accepted_{i}'])) for i in range(7))<1e-6
assert max(abs(float(last[f'dq_post_{i}'])) for i in range(7))<1e-4
audit={'scope':freeze['scope'],'audit':'PASS','replayed_substeps':len(errors),
 'max_q_error':max(float(x['q_max_error']) for x in errors),
 'max_dq_error':max(float(x['dq_max_error']) for x in errors),'stop_substeps':len(stop),
 'last':last,'physical_identity_matches_v14':len(checked),'metadata_sha256':sha(e/'execution.json')}
(e/'audit.json').write_text(json.dumps(audit,indent=2)+'\n')
print(json.dumps({k:v for k,v in audit.items() if k!='last'}))
