#!/usr/bin/env python3
"""Frozen recorded-input C++ parity and explicit fixed-profile rejection checks."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
import csv, hashlib, json, subprocess, sys, copy, shlex, re, time
from pathlib import Path
import numpy as np
import yaml

ROOT=Path('/home/codextransfer/predictive_motion')
OUT=ROOT/'results/phase5/development/public-coupled-cpp-v1'
XML=ROOT/'experiments/generated/inspection/inspection_fr3.xml'
CONSTANTS=ROOT/'results/phase5/development/public-coupled-servo-v1-training/public_constants.json'
BIN=ROOT/'build-public-coupled-cpp-v1/public_coupled_probe'
RAWS={
 'train91011':Path('/mnt/d/CodexTransfer/projects/predictive_motion/phase5/raw/servo-identification-v1-training/raw.csv'),
 'seen91013':Path('/mnt/d/CodexTransfer/projects/predictive_motion/phase5/raw/public-coupled-v2-development-validation-91013/raw.csv')}
HASHES={'train91011':'ab9d14efa1a5886c0683db25345f24d5cacd55343e2768eb60536fa180a11dce','seen91013':'ea70d9e8b01bc6e44387e2f4701779243bb1b202020a61aef18312fac1c054e8'}
STARTS={'train91011':[100,500,1250,2400,2500],'seen91013':[100,500,690,920,2400,2500]}
HORIZONS=[1,2,20,400]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,d):Path(p).write_text(json.dumps(d,indent=2,allow_nan=False)+'\n')
def values(row,prefix):return [float(row[prefix+str(j)]) for j in range(7)]
def rows():
 out={}
 for name,p in RAWS.items():
  assert sha(p)==HASHES[name],name+' raw changed'
  with p.open() as f:out[name]=list(csv.DictReader(f))
 return out
def prepare():
 inp=OUT/'inputs';inp.mkdir(exist_ok=False);r=rows();cases=[];incomplete=[]
 for dataset,starts in STARTS.items():
  for tick in starts:
   matches=[i for i,row in enumerate(r[dataset]) if int(row['tick'])==tick and int(row['substep'])==1]
   assert len(matches)==1
   index=matches[0]
   for steps in HORIZONS:
    name=f'{dataset}_tick{tick}_steps{steps}'
    if index+steps>len(r[dataset]):incomplete.append(dict(name=name,available=len(r[dataset])-index,requested=steps));continue
    first=r[dataset][index]
    cases.append(dict(name=name,q=values(first,'q_before_'),v=values(first,'v_before_'),targets=[values(x,'target_') for x in r[dataset][index:index+steps]],dataset=dataset,index=index,steps=steps,expect_success=True))
 first=r['train91011'][1000];q=values(first,'q_before_');v=values(first,'v_before_');target=values(first,'target_')
 for name,vel,targ in [('nominal_zero',[0.]*7,q),('mixed_velocity',[.1,-.1,.03,-.03,.1,-.1,.1],q),('force_clamp',v,[x+.1 for x in q]),('control_and_force_clamp',v,[100.]*7)]:
  cases.append(dict(name=name,q=q,v=vel,targets=[targ],expect_success=True))
 for name,key,val in [('q_nan','q',['.nan']+q[1:]),('v_inf','v',['.inf']+v[1:]),('target_nan','targets',[['.nan']+target[1:]]),('q_wrong_dimension','q',q[:6]),('v_wrong_dimension','v',v[:6]),('target_wrong_dimension','targets',[target[:6]]),('preclamp_finite_overflow','v',[1e308]*7),('joint_boundary','q',[-2.7437]+q[1:])]:
  c=dict(name=name,q=q,v=v,targets=[target],expect_success=False);c[key]=val;cases.append(c)
 box=[]
 def b(name,H,ell,eta,success=True):box.append(dict(name=name,H=H,ell=ell,eta=eta,expect_success=success))
 b('free',[[2.,.5],[.5,1.5]],[.1,-.1],[1.,1.]);b('coupled_bounds',[[2.,.9],[.9,1.]],[4.,-3.],[1.,.5]);b('zero_eta',[[2.,.5],[.5,1.5]],[2.,-1.],[0.,1.])
 H=np.eye(7)*2+.1*(np.ones((7,7))-np.eye(7));b('mixed_seven',H.tolist(),[4.,-4.,0.,1.,-1.,3.,-3.],[1.]*7)
 b('threshold',[[1.]],[1.],[1.]);b('negative_eta',[[1.]],[0.],[-1.],False);b('dimension',[[1.]],[0.,0.],[1.],False)
 b('asymmetric',[[2.,.5],[.4,2.]],[0.,0.],[1.,1.],False);b('non_spd',[[0.]],[1.],[1.],False)
 b('nan_hessian',[['.nan']],[0.],[1.],False);b('inf_ell',[[1.]],['.inf'],[1.],False);b('nan_eta',[[1.]],[0.],['.nan'],False)
 b('finite_solve_overflow',[[1e-308]],[1e308],[1.],False);b('empty',[],[],[],False)
 save(inp/'cases.json',dict(cases=cases,box_cases=box,incomplete=incomplete))
 c=json.loads(CONSTANTS.read_text());variants=[]
 for name,key,val in [('version','version','3.3.6'),('integrator','integrator',0),('dt','timestep',.004),('wind','wind',[1,0,0]),('gravity_comp','body_gravity_compensation',[1]+[0]*11),('body_count','body_gravity_compensation',[0]*11),('stiffness','joint_stiffness',[1]+[0]*6),('dyntype','actuator_dyntype',[1]+[0]*6),('gear','gear',[2]+c['gear'][1:]),('mapping','actuator_trnid',[1]+c['actuator_trnid'][1:]),('armature','armature',[.2]+c['armature'][1:]),('negative_eta','friction_bounds',[-1]+c['friction_bounds'][1:]),('negative_passive','passive_damping',[-1]+c['passive_damping'][1:]),('zero_invweight','invweight0',[0]+c['invweight0'][1:]),('solref_short','solref',[.003,1]+c['solref'][2:]),('solimp','solimp',[.8]+c['solimp'][1:]),('nan_gain','gainprm',['.nan']+c['gainprm'][1:]),('inf_gravity','gravity',[0,0,'.inf']),('unordered_range','control_range',[2,-2]+c['control_range'][2:]),('nonbinary_flag','control_limited',[2]+c['control_limited'][1:])]:
  d=copy.deepcopy(c);d[key]=val;file=inp/(name+'_constants.json');save(file,d);variants.append(dict(name=name,path=str(file),expect_success=False))
 save(inp/'constants_cases.json',variants)
 save(inp/'empty.json',dict(cases=[],box_cases=[]))
 save(inp/'declared_scope.json',dict(raws={name:dict(path=str(p),sha256=HASHES[name]) for name,p in RAWS.items()},starts=STARTS,horizons_substeps=HORIZONS,parity_q=1e-12,parity_v=1e-11,box_force=1e-12,original_kkt=1e-10,physical_gates={'1/2':{'q':1e-6,'v':1e-4},'20/400':{'q':1e-4,'v':1e-3}},incomplete=incomplete,scope='Previously seen TRAIN/91013; conditional recorded targets; no new plant execution, parameter fitting, runtime claim or phase acceptance.'))
def freeze():
 files=set((ROOT/'tools/phase5_public_coupled_cpp').glob('*'))|set((OUT/'inputs').glob('*'))|{BIN,CONSTANTS,XML,ROOT/'scripts/phase5/public_coupled_servo_v2.py',ROOT/'scripts/phase5/coupled_friction_box_v1.py',ROOT/'scripts/phase5/verify_public_coupled_cpp.py'}|set(RAWS.values())
 for dep in (ROOT/'build-public-coupled-cpp-v1').rglob('*.o.d'):
  tokens=shlex.split(dep.read_text().replace('\\\n',' '))[1:]
  for token in tokens:
   p=Path(token);p=p if p.is_absolute() else ROOT/'build-public-coupled-cpp-v1'/p
   if p.is_file():files.add(p.resolve())
 ldd=subprocess.run(['ldd',str(BIN)],capture_output=True,text=True,check=True).stdout
 (OUT/'native_dependencies.txt').write_text(ldd)
 for token in re.findall(r'(/[\w/.+\-]+)',ldd):
  p=Path(token)
  if p.is_file():files.add(p.resolve())
 files|=set((ROOT/'.vendor/menagerie/franka_fr3/assets').glob('*'))
 files.add(ROOT/'src/predictive_motion_description/manifests/fr3.sha256')
 for file in ['/usr/bin/c++','/usr/bin/cmake','/opt/ros/jazzy/lib/x86_64-linux-gnu/cmake/pinocchio/pinocchioConfig.cmake']:
  files.add(Path(file).resolve())
 records=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(files) if p.is_file()]
 cache=Path('/mnt/d/CodexTransfer/projects/predictive_motion/phase5/dependency-cache/public-coupled-cpp-v1');cache.mkdir(parents=True,exist_ok=False)
 for rec in records:
  dest=cache/rec['sha256'];
  if not dest.exists():dest.write_bytes(Path(rec['path']).read_bytes())
  assert sha(dest)==rec['sha256'];rec['immutable_copy']=str(dest)
 save(OUT/'frozen_before_predictions.json',dict(schema=1,files=records,scope='Before any C++/Python forecast in this unit; metadata-only preflight already run.'))
 print('FROZEN',len(records),sha(OUT/'frozen_before_predictions.json'),flush=True)
def checkfreeze():
 d=json.loads((OUT/'frozen_before_predictions.json').read_text())
 for rec in d['files']:
  assert sha(rec['path'])==rec['sha256'],'live source changed '+rec['path']
  assert sha(rec['immutable_copy'])==rec['sha256'],'cached bytes changed'
def runprobe(constants,inp,out):
 result=subprocess.run([str(BIN),str(XML),str(constants),str(inp),str(out)],capture_output=True,text=True)
 out.with_suffix('.stdout').write_text(result.stdout);out.with_suffix('.stderr').write_text(result.stderr);out.with_suffix('.exit').write_text(str(result.returncode)+'\n')
 return json.loads(out.read_text()),result.returncode
def verify():
 checkfreeze();attempt=OUT/'parity-attempt1';attempt.mkdir(exist_ok=False);dataset=rows();inputs=json.loads((OUT/'inputs/cases.json').read_text())
 cpp,code=runprobe(CONSTANTS,OUT/'inputs/cases.json',attempt/'cpp.json');assert code==0 and cpp['model_success'] is True
 sys.path.insert(0,str(ROOT/'scripts/phase5'))
 from public_coupled_servo_v2 import PublicServo
 from coupled_friction_box_v1 import solve_box
 c=json.loads(CONSTANTS.read_text());model=PublicServo(XML,c);records=[];errors=[];branches=set();nsteps=0
 meta=cpp['metadata'];assert meta['idx_q']==list(range(7)) and meta['idx_v']==list(range(7)) and meta['joint_nq']==[1]*7 and meta['joint_nv']==[1]*7
 assert meta['armature']==c['armature'] and abs(meta['masses'][-1]-1.077143)<1e-14
 assert np.array_equal(np.asarray(meta['masses']),np.array([i.mass for i in model.model.inertias]))
 for inp,out in zip(inputs['cases'],cpp['cases']):
  assert inp['name']==out['name'];r=dict(name=inp['name'],expected_success=inp['expect_success'],cpp_success=out['success'])
  if not inp['expect_success']:
   r['pass']=not out['success'];r['error']=out.get('error');records.append(r)
   if not r['pass']:errors.append(inp['name'])
   continue
  if not out['success']:r['pass']=False;r['error']=out.get('error');errors.append(inp['name']);records.append(r);continue
  q=np.array(inp['q']);v=np.array(inp['v']);dq=[];dv=[];dpq=[];dpv=[];python_trace=[];branch_equal=True;maxkkt=0
  for k,(target,trace) in enumerate(zip(inp['targets'],out['trace'])):
   q,v,info=model.step(q,v,target);dq.append(float(np.max(abs(q-np.array(trace['q'])))));dv.append(float(np.max(abs(v-np.array(trace['v'])))))
   python_trace.append(dict(q=q.tolist(),v=v.tolist(),info=info));branches.update(trace['friction']['branches']);branch_equal &= info['branches']==trace['friction']['branches'];maxkkt=max(maxkkt,info['original_KKT'],trace['friction']['original_KKT']);nsteps+=1
   assert info['control_clips']==trace['control_clips'] and info['force_clips']==trace['force_clips']
   if 'dataset' in inp:
    actual=dataset[inp['dataset']][inp['index']+k];dpq.append(float(np.max(abs(np.array(trace['q'])-values(actual,'q_post_')))));dpv.append(float(np.max(abs(np.array(trace['v'])-values(actual,'v_post_')))))
  r.update(max_parity_q=max(dq),max_parity_v=max(dv),branch_equal=bool(branch_equal),max_original_kkt=maxkkt,steps=len(out['trace']),python_trace=python_trace)
  r['pass']=r['max_parity_q']<=1e-12 and r['max_parity_v']<=1e-11 and branch_equal and maxkkt<=1e-10 and len(out['trace'])==len(inp['targets'])
  if dpq:
   qgate,vgate=(1e-6,1e-4) if inp['steps']<=2 else (1e-4,1e-3);r.update(max_physical_q=max(dpq),max_physical_v=max(dpv),q_gate=qgate,v_gate=vgate);r['pass'] &= max(dpq)<=qgate and max(dpv)<=vgate
  records.append(r)
  if not r['pass']:errors.append(inp['name'])
  print(inp['name'],r['pass'],r['max_parity_q'],r['max_parity_v'],flush=True)
 boxrecords=[]
 for inp,out in zip(inputs['box_cases'],cpp['box_cases']):
  r=dict(name=inp['name'],cpp_success=out['success'],expected_success=inp['expect_success'])
  if inp['expect_success']:
   force,info=solve_box(inp['H'],inp['ell'],inp['eta']);r.update(max_force_difference=float(np.max(abs(force-np.array(out['result']['force'])))),branch_equal=info['branches']==out['result']['branches'],kkt=out['result']['original_KKT']);r['pass']=out['success'] and r['max_force_difference']<=1e-12 and r['branch_equal'] and r['kkt']<=1e-10
  else:r['pass']=not out['success'];r['error']=out.get('error')
  if not r['pass']:errors.append(inp['name'])
  boxrecords.append(r)
 variants=[]
 for inp in json.loads((OUT/'inputs/constants_cases.json').read_text()):
  out,code=runprobe(inp['path'],OUT/'inputs/empty.json',attempt/(inp['name']+'_constants.json'));r=dict(name=inp['name'],returncode=code,pass_check=code==1 and out['model_success'] is False,error=out.get('error'));variants.append(r)
  if not r['pass_check']:errors.append(inp['name'])
 checkfreeze();save(attempt/'report.json',dict(status='PASS_FIXED_RECORDED_CPP_PROTOTYPE_ONLY' if not errors else 'NOT_READY',phase5='NOT_ACCEPTED',phase6='NOT_STARTED',source_freeze_sha256=sha(OUT/'frozen_before_predictions.json'),records=records,boxes=boxrecords,constants_rejections=variants,errors=errors,forecast_substeps=nsteps,observed_branches=sorted(branches),incomplete_retained=inputs['incomplete'],metadata=meta,limitations=['Fixed FR3 public profile only; stricter constructor rejection scope than Python.','Selected complete recorded windows, conditional on recorded targets, previously seen data.','No plant rerun, controller integration, Jacobian, task completion, generalization or online timing claim.']))
 print('RESULT',len(records),len(boxrecords),len(variants),nsteps,errors,flush=True)
 return 0 if not errors else 1
if __name__=='__main__':
 mode=sys.argv[1]
 if mode=='prepare':prepare()
 elif mode=='freeze':freeze()
 elif mode=='verify':sys.exit(verify())
 else:raise ValueError(mode)
