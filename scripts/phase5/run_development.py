from pathlib import Path
import hashlib,json,os,subprocess,sys,time,re
r=Path('/home/codextransfer/predictive_motion');epoch=sys.argv[1];method=sys.argv[2];scenario=sys.argv[3];seed=int(sys.argv[4])
assert method in ['predictive','reactive_qp'] and scenario in ['inspection','joint_trap','singularity_probe'] and seed in [91011,91012]
protocol=sys.argv[5] if len(sys.argv)>5 else ('config/phase5_reference.yaml' if epoch.startswith('reference-') else 'config/phase5.yaml')
result=r/'results/phase5/development'/epoch;result.mkdir(exist_ok=True)
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
files={}
for directory in ['src/predictive_motion_control','scripts/phase5','tools/phase5_adapter','tools/phase4_adapters','models/fr3','experiments/generated/phase4','experiments/generated/phase5','experiments/generated/inspection','cad/generated','.vendor/menagerie/franka_fr3','.vendor/franka_prefix']:
 for p in (r/directory).rglob('*'):
  if p.is_file() and '__pycache__' not in p.parts:files[str(p)]=sha(p)
for name in [protocol,'config/phase5.yaml','config/phase4.yaml','build-phase5-adapter/phase5_benchmark','build-phase5-adapter/CMakeCache.txt','build-phase5-math/predictive_motion_control/CMakeCache.txt','results/cad/path_screening_aabb/feasible_path.csv','benchmarks/reference/inspection_curve.json','install-phase5-math/predictive_motion_control/lib/libpredictive_controller.a','install-phase5-math/predictive_motion_control/lib/libreactive_qp.a']:
 files[str(r/name)]=sha(r/name)
for p in (r/'.vendor/osqp-1.0.0-install/lib').glob('*.a'):files[str(p)]=sha(p)
ldd=subprocess.check_output(['ldd',str(r/'build-phase5-adapter/phase5_benchmark')],text=True)
for line in ldd.splitlines():
 for name in re.findall(r'(?:=>\s+)?(/\S+)',line):
  p=Path(name)
  if p.is_file():files[str(p.resolve())]=sha(p.resolve())
identity={'files':dict(sorted(files.items())),'ldd':ldd,'scope':'development epoch; not held-out evaluation or final research','frozen_before_first_trial_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
freeze=result/'frozen.json'
if freeze.exists():assert json.loads(freeze.read_text())['files']==identity['files'],'Source/input identity changed; use a fresh epoch and preserve the old one'
else:freeze.write_text(json.dumps(identity,indent=2)+'\n')
sys.path.insert(0,str(r/'scripts/phase5'))
from materialize_identity import materialize
materialize(freeze)
raw=Path('/mnt/d/CodexTransfer/projects/predictive_motion/phase5/raw')/epoch/f'{method}_{scenario}_{seed}'
assert not raw.exists()
argv=[str(r/'build-phase5-adapter/phase5_benchmark'),str(r),str(r/protocol),method,scenario,str(seed),str(raw)]
env=dict(os.environ);env['LD_LIBRARY_PATH']=str(r/'.vendor/mujoco-3.3.7/lib')+':'+env.get('LD_LIBRARY_PATH','')
print('START '+' '.join(argv),flush=True);start=time.monotonic()
with (result/f'{method}_{scenario}_{seed}.stdout').open('wb') as out,(result/f'{method}_{scenario}_{seed}.stderr').open('wb') as err:
 code=subprocess.call(argv,stdout=out,stderr=err,env=env,cwd=r)
metadata={'argv':argv,'return_code':code,'wall_s':time.monotonic()-start,'raw_files':{str(p.relative_to(raw)):sha(p) for p in raw.rglob('*') if p.is_file()}}
(result/f'{method}_{scenario}_{seed}.metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
if (raw/'summary.yaml').exists():print((raw/'summary.yaml').read_text(),flush=True)
else:print('FAILED_WITHOUT_SUMMARY; return code '+str(code),flush=True)
print('END '+json.dumps(metadata),flush=True)
