from pathlib import Path
import json,hashlib,shlex,subprocess
D=Path('/private/tmp/phase5_nonzero_progress_tail_margin_active_v4_20261011');meta=json.loads((D/'REMOTE.json').read_text());remote=meta['remote'];prior=remote;backend='/home/codextransfer/predictive_motion/results/phase5/session-task-start-a-primaldual-v2-20261010-attempt5'
a=json.loads(Path('/private/tmp/public_live_affine_v2_integrated_first_cycle_build_batch_once_v1_20261010/actual-dell-files/source-version1/source/EXPLICIT_COMPILE_LINK_PLAN_EXCLUDED.json').read_text());old=a['link_argv'];libs=old[old.index('-Wl,--start-group'):old.index('-Wl,-Map,'+a['output_directory']+'/link.map')];libs=[x for x in libs if not any(y in x for y in ['libpublic_live_affine_v2_affine.a','libpublic_live_affine_v2_normalization.a','libpublic_live_affine_v2_model_boundary.a'])];main=[prior+f'/build-attempt1/unit-{i}.o' for i in [1,2,3,4,5,6,7,9]]+[remote+'/build-attempt1/unit-8.o',backend+'/build-attempt1/unit-9.o',a['output_directory']+'/unit-7.o'];sets=[('active_first_cycle',main),('current_numeric_oracle',[remote+'/build-attempt1/unit-12.o'])];objects=sorted(set(x for n,seq in sets for x in seq));ssh=['tools/dell-ssh.sh','-T','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','DellTransfer']
s='''import pathlib,json,hashlib
p=pathlib.Path(%r);prior=pathlib.Path(%r);backend=pathlib.Path(%r)
for root in [p,prior]:assert json.loads((root/'build-attempt1/BUILD_RESULT.json').read_text())['complete']
reused=[]
for f in sorted((prior/'src').iterdir()):
 if f.name=='active_first_cycle.cpp':continue
 assert f.read_bytes()==(p/'src'/f.name).read_bytes(),f.name
 reused.append({'source':f.name,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
for n in ['solver_forensics.cpp','solver_forensics.hpp']:assert (p/'src'/n).read_bytes()==(backend/'src'/n).read_bytes()
files=[]
for n in %r:
 q=pathlib.Path(n);b=q.read_bytes();files.append({'requested_path':str(q),'resolved_path':str(q.resolve()),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
print(json.dumps({'fresh_compiled_translation_units':15,'fresh_linked_main_translation_units':9,'all_reused_source_header_byteidentities':reused,'backend_reuse_byteidentical':True,'input_files':files}))
'''%(remote,prior,backend,objects)
x=subprocess.run(ssh+['python3 -I -S -B -c '+shlex.quote(s)],capture_output=True,timeout=20);assert x.returncode==0,x.stderr;binding=json.loads(x.stdout);argv=[[old[0]]+seq+libs+['-Wl,-Map,'+remote+'/link-attempt1/'+n+'.map','-o',remote+'/link-attempt1/'+n] for n,seq in sets];plan={'schema':'GEOMETRY_QP_FULL144_PLANNING_TAIL_NATIVE_AND_PURE_LINK_V1','output_directory':remote+'/link-attempt1','env':a['env'],'input_files':binding['input_files'],'readonly_directory_rosters':[],'compile_argv':argv};runner=(D/'dev_compile.py').read_text().replace('ACTIVE_SESSION_PILOT_BC_COMPILE_V1','GEOMETRY_QP_FULL144_PLANNING_TAIL_NATIVE_AND_PURE_LINK_V1').replace("assert len(plan['compile_argv'])==15","assert len(plan['compile_argv'])==2");files={'dev_link.py':runner,'dev_link_plan.json':json.dumps(plan,indent=2)+'\n','LINK_OBJECT_BINDING.json':json.dumps(binding,indent=2)+'\n'}
s='''import json,pathlib,sys
p=pathlib.Path(%r)
for n,b in json.load(sys.stdin).items():
 with (p/n).open('x') as f:f.write(b)
print('native ELF+1pure ELF link staged; no runtime')
'''%remote;x=subprocess.run(ssh+['python3 -I -S -B -c '+shlex.quote(s)],input=json.dumps(files).encode(),capture_output=True,timeout=20);assert x.returncode==0,x.stderr
for n,b in files.items():(D/n).write_text(b)
print(x.stdout.decode())
