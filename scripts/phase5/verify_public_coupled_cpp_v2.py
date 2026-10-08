#!/usr/bin/env python3
"""Frozen recorded-input C++ parity and explicit fixed-profile rejection checks."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
import csv, hashlib, json, subprocess, sys, copy, shlex, re, time, math, itertools
from pathlib import Path
import numpy as np
import yaml

ROOT=Path('/home/codextransfer/predictive_motion')
OUT=ROOT/'results/phase5/development/public-coupled-cpp-v2'
XML=ROOT/'experiments/generated/inspection/inspection_fr3.xml'
CONSTANTS=ROOT/'results/phase5/development/public-coupled-servo-v1-training/public_constants.json'
BIN=ROOT/'build-public-coupled-cpp-v2/public_coupled_probe_v2'
RAWS={
 'train91011':Path('/mnt/d/CodexTransfer/projects/predictive_motion/phase5/raw/servo-identification-v1-training/raw.csv'),
 'seen91013':Path('/mnt/d/CodexTransfer/projects/predictive_motion/phase5/raw/public-coupled-v2-development-validation-91013/raw.csv')}
HASHES={'train91011':'ab9d14efa1a5886c0683db25345f24d5cacd55343e2768eb60536fa180a11dce','seen91013':'ea70d9e8b01bc6e44387e2f4701779243bb1b202020a61aef18312fac1c054e8'}
STARTS={'train91011':[100,500,1250,2400,2500],'seen91013':[100,500,690,920,2400,2500]}
HORIZONS=[1,2,20,400]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,d):Path(p).write_text(json.dumps(d,indent=2,allow_nan=False)+'\n')
def values(row,prefix):return [float(row[prefix+str(j)]) for j in range(7)]
def exact_labels(force,eta):
 return [2 if e==0 else -1 if x<=-e else 1 if x>=e else 0 for x,e in zip(force,eta)]
def extra_box_cases(box):
 for eta in [1e-12,1e-100,float(np.finfo(float).tiny),1e-310,float(np.nextafter(0.,1.))]:
  for sign in [-1.,1.]:
   box.append(dict(name=f'tiny_bound_eta{eta:.17g}_ell{sign:g}',H=[[1.]],ell=[sign],eta=[eta],expect_success=True,oracle='analytic_1d',serialization_may_reject=bool(eta<np.finfo(float).tiny)))
 for name,ell in [('tiny_interior_positive',2.5e-13),('tiny_interior_negative',-2.5e-13),('tiny_lower_zero_gradient',1e-12),('tiny_upper_zero_gradient',-1e-12)]:
  box.append(dict(name=name,H=[[1.]],ell=[ell],eta=[1e-12],expect_success=True,oracle='analytic_1d'))
 box.append(dict(name='mixed_tiny_large_fixed',H=[[2.,.3,.1],[.3,1.5,.2],[.1,.2,2.]],ell=[1.,-.1,-2.],eta=[1e-12,1.,0.],expect_success=True,oracle='enumeration'))
 box.append(dict(name='mixed_tiny_normal_zero',H=np.eye(3).tolist(),ell=[1.,-1.,2.],eta=[1e-12,float(np.finfo(float).tiny),0.],expect_success=True,oracle='enumeration'))
def independent_oracle(inp):
 H,ell,eta=[np.asarray(inp[k],float) for k in ('H','ell','eta')];n=len(ell)
 if n==1:
  force=np.array([min(max(-ell[0]/H[0,0],-eta[0]),eta[0])]);return dict(force=force,kind='analytic_1d')
 candidates=[]
 for face in itertools.product(*[([2] if e==0 else [-1,0,1]) for e in eta]):
  force=np.zeros(n);free=[j for j,s in enumerate(face) if s==0];bound=[j for j,s in enumerate(face) if s!=0]
  for j in bound:force[j]=0 if face[j]==2 else face[j]*eta[j]
  if free:force[free]=np.linalg.solve(H[np.ix_(free,free)],-ell[free]-H[np.ix_(free,bound)]@force[bound])
  if not np.isfinite(force).all() or np.any(force < -eta) or np.any(force>eta):continue
  g=H@force+ell
  if any((s==0 and abs(g[j])>1e-12) or (s==-1 and g[j]<-1e-12) or (s==1 and g[j]>1e-12) for j,s in enumerate(face)):continue
  candidates.append((float(.5*force@H@force+ell@force),force.copy()))
 assert candidates,'enumeration has no valid face';return dict(force=min(candidates,key=lambda x:x[0])[1],kind='independent_face_enumeration',valid_faces=len(candidates))
def compare_oracle(inp,force,labels,oracle):
 expected=oracle['force'];eta=np.array(inp['eta'],float);H=np.array(inp['H'],float);ell=np.array(inp['ell'],float);checks=[];tiny=[]
 for j,(e,f,x) in enumerate(zip(eta,force,expected)):
  if e==0:ok=f==0
  elif e<1e-8:
   if x in (-e,e):ok=f==x
   else:ok=abs(f-x)<=8*math.ulp(float(x))
   tiny.append(dict(index=j,eta=float(e),expected=float(x),actual=float(f),exact_bound=bool(f==x) if x in (-e,e) else None,relative_error=float(abs(f-x)/e),ulp_error=float(abs(f-x)/math.ulp(float(x)))))
  else:ok=abs(f-x)<=1e-12
  checks.append(bool(ok))
 g=H@force+ell;truth=exact_labels(force,eta);res=[0. if label==2 else max(-g[j],0) if label==-1 else max(g[j],0) if label==1 else abs(g[j]) for j,label in enumerate(truth)]
 kkt=float(max(max(res),float(np.max(-eta-force)),float(np.max(force-eta)),0.))
 return dict(oracle_pass=all(checks) and labels==truth and kkt<=1e-10,oracle_kind=oracle['kind'],expected_force=expected.tolist(),max_force_difference=float(np.max(abs(force-expected))),branch_equal=labels==truth,independent_original_KKT=kkt,tiny_precision=tiny)
def gate_controls(output_dir=None):
 from validate_public_coupled_native_output_v2 import validate_output,NativeOutputError,load_native
 source=ROOT/'results/phase5/development/public-coupled-cpp-v1';inp=json.loads((OUT/'inputs/gate_control_inputs.json').read_text());base=json.loads((OUT/'inputs/gate_control_output.json').read_text());validate_output(base,inp)
 changes=[('empty_states',lambda x:x.__setitem__('cases',[])),('drop_state_tail',lambda x:x['cases'].pop()),('extra_state',lambda x:x['cases'].append(copy.deepcopy(x['cases'][0]))),('duplicate_state',lambda x:x['cases'][1].__setitem__('name',x['cases'][0]['name'])),('reverse_states',lambda x:x['cases'].reverse()),('string_state_bool',lambda x:x['cases'][0].__setitem__('success','true')),('int_state_bool',lambda x:x['cases'][0].__setitem__('success',1)),('string_model_bool',lambda x:x.__setitem__('model_success','true')),('empty_boxes',lambda x:x.__setitem__('box_cases',[])),('drop_box_tail',lambda x:x['box_cases'].pop()),('duplicate_box',lambda x:x['box_cases'][1].__setitem__('name',x['box_cases'][0]['name'])),('reverse_boxes',lambda x:x['box_cases'].reverse()),('string_box_bool',lambda x:x['box_cases'][0].__setitem__('success','true')),('short_trace',lambda x:x['cases'][1]['trace'].pop()),('missing_last',lambda x:x['cases'][0].pop('last')),('short_q',lambda x:x['cases'][0]['trace'][0]['q'].pop()),('nan_q',lambda x:x['cases'][0]['trace'][0]['q'].__setitem__(0,float('nan'))),('string_q',lambda x:x['cases'][0]['trace'][0]['q'].__setitem__(0,'0')),('bool_q',lambda x:x['cases'][0]['trace'][0]['q'].__setitem__(0,False)),('inf_v',lambda x:x['cases'][0]['trace'][0]['v'].__setitem__(0,float('inf'))),('string_clip',lambda x:x['cases'][0]['trace'][0].__setitem__('control_clips','0')),('negative_clip',lambda x:x['cases'][0]['trace'][0].__setitem__('force_clips',-1)),('nan_KKT',lambda x:x['cases'][0]['trace'][0]['friction'].__setitem__('original_KKT',float('nan'))),('high_KKT',lambda x:x['cases'][0]['trace'][0]['friction'].__setitem__('original_KKT',1e-9)),('short_force',lambda x:x['cases'][0]['trace'][0]['friction']['force'].pop()),('bad_branch',lambda x:x['cases'][0]['trace'][0]['friction']['branches'].__setitem__(0,3)),('nan_M',lambda x:x['cases'][0]['last']['M'][0].__setitem__(0,float('nan'))),('float_metadata_index',lambda x:x['metadata']['idx_q'].__setitem__(0,0.)),('last_mismatch',lambda x:x['cases'][0]['last']['q'].__setitem__(0,0.))]
 changes += [('overflow_JSON_integer',lambda x:x['cases'][0]['trace'][0]['q'].__setitem__(0,10**400)),('duplicate_joint_name',lambda x:x['metadata']['joint_names'].__setitem__(1,x['metadata']['joint_names'][0]))]
 records=[]
 for name,change in changes:
  native=copy.deepcopy(base);change(native)
  try:validate_output(native,inp)
  except NativeOutputError as error:records.append(dict(name=name,rejected=True,error=str(error)))
  else:raise AssertionError('synthetic invalid output accepted '+name)
 file=(output_dir or OUT/'parity-attempt2')/'synthetic_nan_native.json';bad=copy.deepcopy(base);bad['cases'][0]['trace'][0]['q'][0]=float('nan');file.write_text(json.dumps(bad)+'\n')
 try:load_native(file)
 except NativeOutputError as error:records.append(dict(name='invalid_JSON_NaN_literal',rejected=True,error=str(error)))
 else:raise AssertionError('NaN native JSON accepted')
 partial=copy.deepcopy(base);partial_inputs=copy.deepcopy(inp);partial['cases'][1]['success']=False;partial['cases'][1]['error']='synthetic declared partial failure';partial['cases'][1]['trace']=partial['cases'][1]['trace'][:1];partial_inputs['cases'][1]['expect_success']=False;partial_inputs['cases'][1]['expected_partial_steps']=1;validate_output(partial,partial_inputs)
 partial['cases'][1]['trace'][0]['v'][0]=float('nan')
 try:validate_output(partial,partial_inputs)
 except NativeOutputError as error:records.append(dict(name='negative_partial_trace_NaN',rejected=True,error=str(error)))
 else:raise AssertionError('negative partial nonfinite trace accepted')
 return dict(scope='SYNTHETIC_NATIVE_OUTPUT_GATE_CONTROL_ONLY; output mutations are not actual C++ core failures.',positive_controls=2,negative_controls=records)
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
 extra_box_cases(box);save(inp/'cases.json',dict(cases=cases,box_cases=box,incomplete=incomplete))
 c=json.loads(CONSTANTS.read_text());variants=[]
 for name,key,val in [('version','version','3.3.6'),('integrator','integrator',0),('dt','timestep',.004),('wind','wind',[1,0,0]),('gravity_comp','body_gravity_compensation',[1]+[0]*11),('body_count','body_gravity_compensation',[0]*11),('stiffness','joint_stiffness',[1]+[0]*6),('dyntype','actuator_dyntype',[1]+[0]*6),('gear','gear',[2]+c['gear'][1:]),('mapping','actuator_trnid',[1]+c['actuator_trnid'][1:]),('armature','armature',[.2]+c['armature'][1:]),('negative_eta','friction_bounds',[-1]+c['friction_bounds'][1:]),('negative_passive','passive_damping',[-1]+c['passive_damping'][1:]),('zero_invweight','invweight0',[0]+c['invweight0'][1:]),('solref_short','solref',[.003,1]+c['solref'][2:]),('solimp','solimp',[.8]+c['solimp'][1:]),('nan_gain','gainprm',['.nan']+c['gainprm'][1:]),('inf_gravity','gravity',[0,0,'.inf']),('unordered_range','control_range',[2,-2]+c['control_range'][2:]),('nonbinary_flag','control_limited',[2]+c['control_limited'][1:])]:
  d=copy.deepcopy(c);d[key]=val;file=inp/(name+'_constants.json');save(file,d);variants.append(dict(name=name,path=str(file),expect_success=False))
 save(inp/'constants_cases.json',variants)
 save(inp/'empty.json',dict(cases=[],box_cases=[]))
 save(inp/'declared_scope.json',dict(raws={name:dict(path=str(p),sha256=HASHES[name]) for name,p in RAWS.items()},starts=STARTS,horizons_substeps=HORIZONS,parity_q=1e-12,parity_v=1e-11,box_force=1e-12,original_kkt=1e-10,physical_gates={'1/2':{'q':1e-6,'v':1e-4},'20/400':{'q':1e-4,'v':1e-3}},incomplete=incomplete,scope='Previously seen TRAIN/91013; conditional recorded targets; no new plant execution, parameter fitting, runtime claim or phase acceptance.'))
 old=ROOT/'results/phase5/development/public-coupled-cpp-v1';oldinputs=json.loads((old/'inputs/cases.json').read_text());oldoutput=json.loads((old/'parity-attempt1/cpp.json').read_text())
 control_inputs=dict(cases=oldinputs['cases'][:2],box_cases=oldinputs['box_cases'][:2]);control_output=dict(model_success=oldoutput['model_success'],metadata=oldoutput['metadata'],cases=oldoutput['cases'][:2],box_cases=oldoutput['box_cases'][:2])
 save(inp/'gate_control_inputs.json',control_inputs);save(inp/'gate_control_output.json',control_output)
 save(inp/'gate_control_provenance.json',dict(scope='Prior actual v1 outputs reused only as structural gate positive control; synthetic mutations are not actual C++ core failures.',parent_output_sha256=sha(old/'parity-attempt1/cpp.json'),parent_inputs_sha256=sha(old/'inputs/cases.json')))
 scope=json.loads((inp/'declared_scope.json').read_text());scope.update(label_convention='eta0 fixed2, actual lower or upper bounds, strict interior0; exact zero-gradient bound reports that side.',tiny_force_gate='Saturated tiny positive eta must equal analytic/enumerated exact floating bound; interior <=8 ULP; no absolute1e-10 proxy.',serialization_policy='Predeclared subnormal fixtures remain in roster; only explicit bad-conversion rejection is marked unsupported serialization. Accepted wrong-zero force must fail.',state_branch_gate='Native force labels match exact bound convention; Python v1 near-bound labels are not the v2 convention.');save(inp/'declared_scope.json',scope)
def freeze():
 files=set((ROOT/'tools/phase5_public_coupled_cpp_v2').glob('*'))|set((OUT/'inputs').glob('*'))|{BIN,CONSTANTS,XML,OUT/'v1_preserved_before_v2.json',ROOT/'scripts/phase5/public_coupled_servo_v2.py',ROOT/'scripts/phase5/coupled_friction_box_v1.py',ROOT/'scripts/phase5/verify_public_coupled_cpp_v2.py',ROOT/'scripts/phase5/validate_public_coupled_native_output_v2.py'}|set(RAWS.values())
 for dep in (ROOT/'build-public-coupled-cpp-v2').rglob('*.o.d'):
  tokens=shlex.split(dep.read_text().replace('\\\n',' '))[1:]
  for token in tokens:
   p=Path(token);p=p if p.is_absolute() else ROOT/'build-public-coupled-cpp-v2'/p
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
 cache=Path('/mnt/d/CodexTransfer/projects/predictive_motion/phase5/dependency-cache/public-coupled-cpp-v2-report-repair');cache.mkdir(parents=True,exist_ok=False)
 for rec in records:
  dest=cache/rec['sha256'];
  if not dest.exists():dest.write_bytes(Path(rec['path']).read_bytes())
  assert sha(dest)==rec['sha256'];rec['immutable_copy']=str(dest)
 save(OUT/'frozen_after_report_repair_before_repeat.json',dict(schema=1,files=records,scope='Before any C++/Python forecast in this unit; metadata-only preflight already run.'))
 print('FROZEN',len(records),sha(OUT/'frozen_after_report_repair_before_repeat.json'),flush=True)
def checkfreeze():
 d=json.loads((OUT/'frozen_after_report_repair_before_repeat.json').read_text())
 for rec in d['files']:
  assert sha(rec['path'])==rec['sha256'],'live source changed '+rec['path']
  assert sha(rec['immutable_copy'])==rec['sha256'],'cached bytes changed'
 for file,digest in json.loads((OUT/'v1_preserved_before_v2.json').read_text()).items():assert sha(file)==digest,'v1 changed '+file
def runprobe(constants,inp,out):
 result=subprocess.run([str(BIN),str(XML),str(constants),str(inp),str(out)],capture_output=True,text=True)
 out.with_suffix('.stdout').write_text(result.stdout);out.with_suffix('.stderr').write_text(result.stderr);out.with_suffix('.exit').write_text(str(result.returncode)+'\n')
 from validate_public_coupled_native_output_v2 import load_native
 return load_native(out),result.returncode
def verify():
 checkfreeze();attempt=OUT/'parity-attempt2';attempt.mkdir(exist_ok=False);dataset=rows();inputs=json.loads((OUT/'inputs/cases.json').read_text())
 cpp,code=runprobe(CONSTANTS,OUT/'inputs/cases.json',attempt/'cpp.json');assert code==0
 from validate_public_coupled_native_output_v2 import validate_output
 serialization=validate_output(cpp,inputs);gate_report=gate_controls()
 sys.path.insert(0,str(ROOT/'scripts/phase5'))
 from public_coupled_servo_v2 import PublicServo
 from coupled_friction_box_v1 import solve_box
 c=json.loads(CONSTANTS.read_text());model=PublicServo(XML,c);records=[];errors=[];branches=set();nsteps=0
 meta=cpp['metadata'];assert meta['idx_q']==list(range(7)) and meta['idx_v']==list(range(7)) and meta['joint_nq']==[1]*7 and meta['joint_nv']==[1]*7
 assert meta['joint_names']==c['joint_names'] and meta['frame_names']==[f.name for f in model.model.frames]
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
   python_trace.append(dict(q=q.tolist(),v=v.tolist(),info=info));branches.update(trace['friction']['branches']);branch_equal &= exact_labels(trace['friction']['force'],c['friction_bounds'])==trace['friction']['branches'];maxkkt=max(maxkkt,info['original_KKT'],trace['friction']['original_KKT']);nsteps+=1
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
   if not out['success']:
    r.update(pass_check=True,serialization_unsupported=True,error=out['error']);r['pass']=True
   else:
    oracle=independent_oracle(inp);force=np.array(out['result']['force']);checks=compare_oracle(inp,force,out['result']['branches'],oracle);r.update(checks);r['pass']=checks['oracle_pass']
  else:r['pass']=not out['success'];r['error']=out.get('error')
  if not r['pass']:errors.append(inp['name'])
  boxrecords.append(r)
 variants=[]
 for inp in json.loads((OUT/'inputs/constants_cases.json').read_text()):
  out,code=runprobe(inp['path'],OUT/'inputs/empty.json',attempt/(inp['name']+'_constants.json'));r=dict(name=inp['name'],returncode=code,pass_check=code==1 and out['model_success'] is False,error=out.get('error'));variants.append(r)
  if not r['pass_check']:errors.append(inp['name'])
 checkfreeze();save(attempt/'report.json',dict(status='PASS_FIXED_RECORDED_CPP_PROTOTYPE_ONLY' if not errors else 'NOT_READY',phase5='NOT_ACCEPTED',phase6='NOT_STARTED',synthetic_schema_gate=gate_report,serialization_rejections=serialization,source_freeze_sha256=sha(OUT/'frozen_after_report_repair_before_repeat.json'),records=records,boxes=boxrecords,constants_rejections=variants,errors=errors,forecast_substeps=nsteps,observed_branches=sorted(branches),incomplete_retained=inputs['incomplete'],metadata=meta,limitations=['Fixed FR3 public profile only; stricter constructor rejection scope than Python. Exact-side v2 labels deliberately replace v1 near-bound labels.','Selected complete recorded windows, conditional on recorded targets, previously seen data.','No plant rerun, controller integration, Jacobian, task completion, generalization or online timing claim.']))
 print('RESULT',len(records),len(boxrecords),len(variants),nsteps,errors,flush=True)
 return 0 if not errors else 1
if __name__=='__main__':
 mode=sys.argv[1]
 if mode=='prepare':prepare()
 elif mode=='freeze':freeze()
 elif mode=='verify':sys.exit(verify())
 else:raise ValueError(mode)
