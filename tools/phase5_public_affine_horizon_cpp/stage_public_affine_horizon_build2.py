import hashlib,json,shutil,subprocess
from pathlib import Path
ROOT=Path('/home/codextransfer/predictive_motion');SRC=ROOT/'tools/phase5_public_affine_horizon_cpp'
BASE=ROOT/'results/phase5/development/public-affine-horizon-cpp-v1'
BUILD=ROOT/'build-public-affine-horizon-cpp-v1-attempt2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert not BUILD.exists()
assert sha(SRC/'public_affine_horizon.cpp')=='bc4ead2f085216c40da6be34b6c3d037b3f90df83757b94464f7f6ed97cef953'
assert sha(SRC/'public_affine_horizon_probe.cpp')=='7e991b0118c67989826e0c10a703c6114d4f408834ce6bda73a94018f1e6afa4'
snapshot=BASE/'source-after-compile-fix1';snapshot.mkdir(exist_ok=False)
for p in SRC.iterdir():
 if p.is_file():shutil.copyfile(p,snapshot/p.name)
shutil.copyfile(Path(__file__),BASE/Path(__file__).name)
sources={p.name:dict(sha256=sha(p),bytes=p.stat().st_size) for p in snapshot.iterdir() if p.is_file()}
record={'scope':'REVIEWED_COMPATIBILITY_FIX_FIRST_EMPTY_ONLY','preserved_failed_build':str(ROOT/'build-public-affine-horizon-cpp-v1'),'source_files':sources,'commands':[],'nonempty_calls':0,'root_review_approved':True}
def run(label,args):
 with (BASE/(label+'.stdout')).open('xb') as out,(BASE/(label+'.stderr')).open('xb') as err:r=subprocess.run(args,cwd=ROOT,stdout=out,stderr=err)
 (BASE/(label+'.exit')).write_text(str(r.returncode)+'\n');record['commands'].append(dict(label=label,argv=args,exit=r.returncode))
 (BASE/'build2_record.json').write_text(json.dumps(record,indent=2)+'\n');print(label,'exit',r.returncode,flush=True);return r.returncode
configured=run('configure_attempt2',['cmake','-S',str(SRC),'-B',str(BUILD),'-DCMAKE_BUILD_TYPE=Release','-DCMAKE_EXPORT_COMPILE_COMMANDS=ON'])
compiled=run('build_attempt2',['cmake','--build',str(BUILD),'-j','2']) if configured==0 else None
if compiled==0:
 prepared=BASE/'prepared-inputs';m=json.loads((prepared/'INPUT_MANIFEST.json').read_text());assert all(sha(prepared/k)==v['sha256'] for k,v in m['files'].items())
 binary=BUILD/'public_affine_horizon_probe';record['binary_sha256']=sha(binary)
 assert all(sha(SRC/k)==v['sha256'] for k,v in sources.items())
 run('binary_runtime_dependencies',['ldd',str(binary)])
 run('empty_attempt1',[str(binary),'--policy',str(prepared/'policy.json'),str(prepared/'empty.json'),str(BASE/'empty_attempt1.json')])
record['phase5']='NOT_ACCEPTED';record['full_freeze']='PENDING';(BASE/'build2_record.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({'build':str(BUILD),'binary_sha256':record.get('binary_sha256'),'commands':[(x['label'],x['exit']) for x in record['commands']],'nonempty_calls':0}),flush=True)
