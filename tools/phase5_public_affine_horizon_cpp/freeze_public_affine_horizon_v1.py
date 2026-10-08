"""Full immutable dependency snapshot; no numerical kernel/checker/model calls."""
import hashlib,json,re,shutil,subprocess,sys,sysconfig
from pathlib import Path
ROOT=Path('/home/codextransfer/predictive_motion')
BASE=ROOT/'results/phase5/development/public-affine-horizon-cpp-v1'
SRC=ROOT/'tools/phase5_public_affine_horizon_cpp'
BUILD1=ROOT/'build-public-affine-horizon-cpp-v1'
BUILD2=ROOT/'build-public-affine-horizon-cpp-v1-attempt2'
AUDIT=Path('/home/codextransfer/clean-audits/root-affine-horizon-20261008')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def regular(p):return p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'
assert not (BASE/'frozen_before_predictions.json').exists()
build=json.loads((BASE/'build2_record.json').read_text())
assert {x['label']:x['exit'] for x in build['commands']}['build_attempt2']==0
assert {x['label']:x['exit'] for x in build['commands']}['empty_attempt1']==0
assert build['nonempty_calls']==0
prepared=BASE/'prepared-inputs';m=json.loads((prepared/'INPUT_MANIFEST.json').read_text())
assert all(sha(prepared/k)==v['sha256'] for k,v in m['files'].items())
rootready=json.loads((AUDIT/'prepared-v1/READY.json').read_text())
assert all(sha(AUDIT/'prepared-v1'/k)==v['sha256'] and (AUDIT/'prepared-v1'/k).stat().st_size==v['bytes'] for k,v in rootready['files'].items())
assert sha(AUDIT/'prepared-v1/READY.json')=='693dacaeb450b602096dd40324cfc0975b0ee2da47f1f6e8305960bea5cacb1b'
binary=BUILD2/'public_affine_horizon_probe';assert sha(binary)==build['binary_sha256']
empty=json.loads((BASE/'empty_attempt1.json').read_text());assert empty['cases']==[]
assert empty['metadata']['policy_sha256']==sha(prepared/'policy.json')
assert all(type(v) is bool and not v for v in empty['metadata']['scope'].values())
files=set()
def put(p):
 p=Path(p)
 if regular(p):files.add(p.absolute())
def tree(p):
 for f in Path(p).rglob('*'):
  if regular(f):put(f)
# Preserve initial compile failure, exact build state, all source history and
# current compiled binary/flags/dependency records. Caches enter archive only.
for p in (SRC,BUILD1,BUILD2):tree(p)
for p in BASE.rglob('*'):
 if regular(p) and 'dependency-snapshot' not in p.parts:put(p)
tree(AUDIT/'prepared-v1')
for p in AUDIT.iterdir():
 if regular(p):put(p)
# Complete currently used header SDK trees plus compiler-discovered includes.
for p in ('/usr/include/eigen3','/usr/include/yaml-cpp','/usr/include/openssl','/usr/include/x86_64-linux-gnu/openssl'):tree(p)
for module in ('phase5_public_coupled_augmented_extension_cpp','phase5_public_coupled_augmented_cpp','phase5_public_coupled_derivative_cpp','phase5_public_coupled_cpp_v2'):
 for p in (ROOT/'tools'/module).glob('*.hpp'):put(p)
for buildtree in (BUILD1,BUILD2):
 for dep in buildtree.rglob('*.o.d'):
  text=dep.read_text().replace('\\\n',' ')
  for name in text.split()[1:]:
   if name.startswith('/'):put(name)
# Actual toolchain programs, not just version strings. Diagnostic print commands
# never execute this project's numerical binary.
identity={}
for prog in ('c++','cmake','python3','as','ld','ar','ranlib','make'):
 found=shutil.which(prog);assert found;put(found);put(Path(found).resolve());identity[prog]=str(Path(found).resolve())
for name in ('cc1plus','collect2','libstdc++.so','libgcc_s.so.1'):
 flag='-print-prog-name='+name if name in ('cc1plus','collect2') else '-print-file-name='+name
 value=subprocess.check_output(['c++',flag],text=True).strip();p=Path(value);assert p.is_file();put(p);put(p.resolve());identity[name]=str(p.resolve())
for p in re.findall(r'(/[^\s()]+)',(BASE/'binary_runtime_dependencies.stdout').read_text()):
 f=Path(p)
 if f.is_file():put(f);put(f.resolve())
runtime_reports={}
# Toolchain dynamic dependencies and Python verification SDK are also frozen.
for program,path in identity.items():
 result=subprocess.run(['ldd',path],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 runtime_reports[program]={'path':path,'exit':result.returncode,'stdout':result.stdout,'stderr':result.stderr}
 for name in re.findall(r'(/[^\s()]+)',result.stdout):
  dep=Path(name)
  if dep.is_file():put(dep);put(dep.resolve())
stdlib=Path(sysconfig.get_path('stdlib'))
if stdlib.exists():
 for p in stdlib.rglob('*'):
  if regular(p) and not any(part in ('site-packages','dist-packages') for part in p.relative_to(stdlib).parts):put(p)
for base in sys.path:
 if not base:continue
 for name in ('numpy','numpy.libs'):
  package=Path(base)/name
  if package.is_dir():
   tree(package)
   for shared in package.rglob('*.so'):
    result=subprocess.run(['ldd',str(shared)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    runtime_reports[str(shared)]={'exit':result.returncode,'stdout':result.stdout,'stderr':result.stderr}
    for lib in re.findall(r'(/[^\s()]+)',result.stdout):
     dep=Path(lib)
     if dep.is_file():put(dep);put(dep.resolve())
report_path=BASE/'toolchain_and_python_runtime_dependencies.json'
with report_path.open('x') as f:json.dump(runtime_reports,f,indent=2);f.write('\n')
put(report_path)
put('/etc/ssl/openssl.cnf')
for p in (Path('/usr/lib/x86_64-linux-gnu/ossl-modules'),):
 if p.exists():tree(p)
put(Path(__file__))
snapshot=BASE/'dependency-snapshot';snapshot.mkdir(exist_ok=False)
entries=[]
for p in sorted(files):
 data=p.read_bytes();digest=hashlib.sha256(data).hexdigest();assert sha(p)==digest
 cache=snapshot/digest
 if not cache.exists():
  with cache.open('xb') as f:f.write(data)
 assert sha(cache)==digest
 entries.append(dict(path=str(p),sha256=digest,bytes=len(data),cache=str(cache.relative_to(BASE))))
record={'schema_version':1,'scope':'FROZEN_GENERAL_AFFINE_ALGEBRA_INPUTS_NO_NONEMPTY_CALLS','prerequisite_private_checkpoint':'1690a64be272ad01165a022ed10175bd50457fcf','binary':str(binary),'binary_sha256':sha(binary),'compiler_tools':identity,'dependencies':entries,'dependency_count':len(entries),'producer_input_manifest_sha256':sha(prepared/'INPUT_MANIFEST.json'),'root_prepared_ready_sha256':sha(AUDIT/'prepared-v1/READY.json'),'root_inputs_sha256':sha(AUDIT/'prepared-v1/inputs.json'),'root_policy_sha256':sha(AUDIT/'prepared-v1/policy.json'),'retained_compile_attempt1_exit':2,'configure_attempt2_exit':0,'build_attempt2_exit':0,'empty_attempt1_exit':0,'nonempty_calls':0,'phase5':'NOT_ACCEPTED','earlier_fd_failure':'RETAINED_IMMUTABLE','all_seven_claims_false':True}
freeze=BASE/'frozen_before_predictions.json'
with freeze.open('x') as f:json.dump(record,f,indent=2);f.write('\n')
verified=[]
for e in entries:
 assert sha(Path(e['path']))==e['sha256'] and sha(BASE/e['cache'])==e['sha256'];verified.append(e['sha256'])
ready={'freeze_sha256':sha(freeze),'binary_sha256':sha(binary),'dependency_count':len(entries),'all_live_and_cache_sha256_verified':True,'nonempty_calls':0,'requires_root_release_before_nonempty':True}
with (BASE/'FREEZE_READY.json').open('x') as f:json.dump(ready,f,indent=2);f.write('\n')
print(json.dumps(ready),flush=True)
