import hashlib,json,shutil,subprocess
from pathlib import Path
ROOT=Path('/home/codextransfer/predictive_motion')
SRC=ROOT/'tools/phase5_public_affine_horizon_cpp'
BASE=ROOT/'results/phase5/development/public-affine-horizon-cpp-v1'
BUILD=ROOT/'build-public-affine-horizon-cpp-v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(SRC/'SOURCE_MANIFEST.json')=='af52d0c908266f6b9462047309b2c73fb91b40a24a9461ded9475afaf307ec2c'
manifest=json.loads((SRC/'SOURCE_MANIFEST.json').read_text())
assert all(sha(SRC/k)==v['sha256'] for k,v in manifest['files'].items() if '/' not in k)
BASE.mkdir(parents=True,exist_ok=False)
assert not BUILD.exists()
snap=BASE/'source-before-build';snap.mkdir()
for p in SRC.iterdir():
 if p.is_file():shutil.copyfile(p,snap/p.name)
shutil.copyfile(Path(__file__),BASE/Path(__file__).name)
record={'source_manifest_sha256':sha(SRC/'SOURCE_MANIFEST.json'),'prerequisite_private_checkpoint':'1690a64be272ad01165a022ed10175bd50457fcf','scope':'FIRST_CONFIGURE_BUILD_INPUT_PREP_EMPTY_ONLY_NO_NONEMPTY_CALLS','commands':[]}
def run(label,args):
 with (BASE/(label+'.stdout')).open('xb') as out,(BASE/(label+'.stderr')).open('xb') as err:
  r=subprocess.run(args,stdout=out,stderr=err,cwd=ROOT)
 (BASE/(label+'.exit')).write_text(str(r.returncode)+'\n')
 record['commands'].append({'label':label,'argv':args,'exit':r.returncode})
 (BASE/'stage_record.json').write_text(json.dumps(record,indent=2)+'\n')
 print(label,'exit',r.returncode,flush=True)
 return r.returncode
run('compiler_version',['c++','--version'])
run('cmake_version',['cmake','--version'])
run('sdk_versions',['dpkg-query','-W','libeigen3-dev','libyaml-cpp-dev','libssl-dev'])
configured=run('configure_attempt1',['cmake','-S',str(SRC),'-B',str(BUILD),'-DCMAKE_BUILD_TYPE=Release','-DCMAKE_EXPORT_COMPILE_COMMANDS=ON'])
compiled=run('build_attempt1',['cmake','--build',str(BUILD),'-j','2']) if configured==0 else None
# Literal input preparation uses only stdlib/fixed definitions/saved source bytes.
prepared=run('prepare_attempt1',['python3',str(SRC/'prepare_public_affine_horizon.py'),'--source','/home/codextransfer/clean-audits/root-affine-horizon-20261008/archived_sources.json','--output',str(BASE/'prepared-inputs')])
if prepared==0:
 m=json.loads((BASE/'prepared-inputs/INPUT_MANIFEST.json').read_text())
 assert all(sha(BASE/'prepared-inputs'/k)==v['sha256'] and (BASE/'prepared-inputs'/k).stat().st_size==v['bytes'] for k,v in m['files'].items())
 record['prepared_inputs_manifest_sha256']=sha(BASE/'prepared-inputs/INPUT_MANIFEST.json')
if compiled==0 and prepared==0:
 assert all(sha(SRC/k)==v['sha256'] for k,v in manifest['files'].items() if '/' not in k)
 binary=BUILD/'public_affine_horizon_probe';record['binary_sha256']=sha(binary)
 run('binary_runtime_dependencies',['ldd',str(binary)])
 # Exactly one empty call; no nonempty inputs or checker/model executions.
 run('empty_attempt1',[str(binary),'--policy',str(BASE/'prepared-inputs/policy.json'),str(BASE/'prepared-inputs/empty.json'),str(BASE/'empty_attempt1.json')])
record['phase5']='NOT_ACCEPTED';record['full_freeze']='PENDING_ROOT_INPUT_READY';record['nonempty_calls']=0
(BASE/'stage_record.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({'base':str(BASE),'commands':[(r['label'],r['exit']) for r in record['commands']],'binary_sha256':record.get('binary_sha256'),'nonempty_calls':0}),flush=True)
