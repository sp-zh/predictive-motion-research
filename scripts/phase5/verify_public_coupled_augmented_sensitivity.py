#!/usr/bin/env python3
"""Cell-local sensitivity QA; external FD composition is validation, not planner."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
import json,hashlib,copy,csv,math,re,shlex,subprocess,sys
from pathlib import Path
from fractions import Fraction as F
import numpy as np
ROOT=Path('/home/codextransfer/predictive_motion');OUT=ROOT/'results/phase5/development/public-coupled-augmented-sensitivity-cpp-v1'
BIN=ROOT/'build-public-coupled-augmented-sensitivity-cpp-v1/public_coupled_augmented_sensitivity_probe';BASE=ROOT/'build-public-coupled-augmented-cpp-v1/public_coupled_augmented_probe';PHYS=ROOT/'build-public-coupled-derivative-cpp-v1/public_coupled_derivative_probe'
XML=ROOT/'experiments/generated/inspection/inspection_fr3.xml';CONST=ROOT/'results/phase5/development/public-coupled-servo-v1-training/public_constants.json';OLD=ROOT/'results/phase5/development/public-coupled-derivative-cpp-v1/frozen_before_predictions.json'
EPS=[1e-6,3e-7];ABS=5e-7;REL=5e-6;BATCH=96
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):Path(p).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def need(x,msg):
 if not x:raise ValueError(msg)
def pack(z):return np.array(z['q']+z['v']+z['C']+z['w']+[z['s'],z['r']])
def unpack(x):return dict(q=x[:7].tolist(),v=x[7:14].tolist(),C=x[14:21].tolist(),w=x[21:28].tolist(),s=float(x[28]),r=float(x[29]))
def prepare():
 p=OUT/'inputs';p.mkdir(exist_ok=False);c=json.loads(CONST.read_text());prev=ROOT/'results/phase5/development/public-coupled-cpp-v2';pi=json.loads((prev/'inputs/cases.json').read_text());po=json.loads((prev/'parity-attempt2/cpp.json').read_text());q=np.array(next(x['q'] for x in pi['cases'] if x['name']=='nominal_zero'));n=np.array(next(x['last']['bias'] for x in po['cases'] if x['name']=='nominal_zero'));bias=np.array(c['biasprm']).reshape(7,10);kp=np.array(c['gainprm']).reshape(7,10)[:,0];C=(n-bias[:,0]-bias[:,1]*q)/kp;sign=np.array([1,-1,1,-1,1,-1,1]);z=dict(q=q.tolist(),v=[0.]*7,C=C.tolist(),w=(sign*1e-4).tolist(),s=.2,r=.08);cases=[]
 def add(name,cells,state=z,success=True,value=True,sub=None,cy=None,ce=None):
  a=dict(name=name,state=copy.deepcopy(state),cells=copy.deepcopy(cells),expect_success=value,expected_value=value,expected_sensitivity=success)
  if not value:a.update(expected_steps=0,expected_cycles=0)
  if not success:a.update(expected_maps=sub or 0,expected_cycle_maps=cy or 0,expected_cell_maps=ce or 0)
  cases.append(a);return a
 def cell(m=1,a=.003,b=.01):return dict(cycles=m,alpha=(sign*a).tolist(),b=b)
 add('all_free_cycle1',[cell()]);add('held10',[cell(10,.001,.002)]);add('split10',[cell(m,.001,.002) for m in (1,3,2,4)]);add('nonuniform_mixed',[cell(m,a,b) for m,a,b in [(1,.003,.01),(3,-.002,-.005),(2,.001,.002),(4,0.,0.)]])
 sat=copy.deepcopy(z);sat['C']=(q+.1*sign).tolist();add('strong_joint_force_cycle1',[cell()],sat)
 raw=Path('/mnt/d/CodexTransfer/projects/predictive_motion/phase5/raw/public-coupled-v2-development-validation-91013/raw.csv');need(sha(raw)=='ea70d9e8b01bc6e44387e2f4701779243bb1b202020a61aef18312fac1c054e8','seen raw identity')
 with raw.open() as f:rows=list(csv.DictReader(f))
 i=next(i for i,r in enumerate(rows) if int(r['tick'])==690 and int(r['substep'])==1);v=lambda r,k:[float(r[k+str(j)]) for j in range(7)];seen=dict(q=v(rows[i],'q_before_'),v=v(rows[i],'v_before_'),C=v(rows[i-1],'target_'),w=v(rows[i-1],'command_velocity_'),s=.2,r=.08);add('seen91013_actual_history_cycle1',[dict(cycles=1,alpha=v(rows[i],'command_acceleration_'),b=.01)],seen)
 for key,x in [('s',0.),('r',0.),('r',.2)]:
  st=copy.deepcopy(z);st[key]=x;b=.01 if key=='r' and x==0 else -.01 if key=='r' and x==.2 else 0.;add('initial_'+key+'_'+str(x),[cell(1,0.,b)],st,False)
 st=copy.deepcopy(z);st.update(s=1.,r=0.);add('terminal_s1_r0',[cell(1,0.,0.)],st,False)
 st=copy.deepcopy(z);st['w']=[.0625]*7;add('initial_command_w_boundary',[dict(cycles=1,alpha=[-.5]*7,b=0.)],st,False)
 add('alpha_boundary',[dict(cycles=1,alpha=[1.]*7,b=0.)],success=False)
 st=copy.deepcopy(z);st['w']=[.0605]*7;add('generated_w_boundary',[dict(cycles=1,alpha=[.5]*7,b=0.)],st,False)
 st=copy.deepcopy(z);st['s']=1.-.004*.08;add('generated_s_boundary_half_prefix',[cell(1,0.,0.)],st,False,sub=1)
 st=copy.deepcopy(z);st['r']=.2-.004*.01;add('generated_r_boundary_half_prefix',[cell(1,0.,.01)],st,False,sub=1)
 add('later_cell_alpha_boundary',[cell(1,0.,0.),dict(cycles=1,alpha=[1.]*7,b=0.)],success=False,sub=2,cy=1,ce=1)
 old_deriv=json.loads((ROOT/'results/phase5/development/public-coupled-derivative-cpp-v1/inputs/cases.json').read_text())
 for name in ('weak_lower_zero_gradient','joint_force_upper_exact'):
  prior=next(x for x in old_deriv['cases'] if x['name']==name);st=copy.deepcopy(z);st.update(q=prior['q'],v=prior['v'],C=prior['C'],w=[0.]*7);add('physical_'+name,[cell(1,0.,0.)],st,False)
 st=copy.deepcopy(z);st['w']=[.060]*7;a=add('forward_second_cycle_w_failure',[dict(cycles=2,alpha=[.5]*7,b=0.)],st,False,False,sub=2,cy=1);a.update(expected_steps=2,expected_cycles=1)
 for name,change in [('q_dimension',lambda x:x['state'].update(q=q.tolist()[:6])),('v_inf',lambda x:x['state'].update(v=['.inf']*7)),('C_nan',lambda x:x['state']['C'].__setitem__(0,'.nan')),('w_dimension',lambda x:x['state'].update(w=[0.]*6)),('alpha_outside',lambda x:x['cells'][0].update(alpha=[1.01]*7)),('mesh_zero',lambda x:x['cells'][0].update(cycles=0)),('mesh_quoted',lambda x:x['cells'][0].update(cycles='1')),('mesh_bool',lambda x:x['cells'][0].update(cycles=True)),('progress_outside',lambda x:x['state'].update(s=1.1)),('finite_preclamp_overflow',lambda x:x['state'].update(v=[1e308]*7))]:
  a=add(name,[cell()],success=False,value=False);change(a)
 save(p/'cases.json',dict(cases=cases));save(p/'empty.json',dict(cases=[]));fd=[]
 for a in cases[:6]:
  fd.append(copy.deepcopy(a))
  for ei,e in enumerate(EPS):
   for j in range(38):
    for sg in (-1,1):
     x=copy.deepcopy(a);x['name']=f'{a["name"]}_e{ei}_col{j}_sign{sg}'
     if j<30:
      state=pack(x['state']);state[j]+=sg*e;x['state']=unpack(state)
     else:
      for ce in x['cells']:
       if j<37:ce['alpha'][j-30]+=sg*e
       else:ce['b']+=sg*e
     fd.append(x)
 batches=[]
 for i in range(0,len(fd),BATCH):
  file=p/f'fd_batch{i//BATCH:03d}.json';save(file,dict(cases=fd[i:i+BATCH]));batches.append(dict(path=str(file),count=min(BATCH,len(fd)-i),sha256=sha(file)))
 save(p/'fd_batches.json',batches);save(p/'declared_scope.json',dict(positive_cases=6,noncertified_cases=sum(x['expected_value'] and not x['expected_sensitivity'] for x in cases),invalid_cases=sum(not x['expected_value'] for x in cases),epsilons=EPS,absolute_per_entry=ABS,relative_per_entry=REL,fd_total=len(fd),fd_batch_cap=BATCH,control_fd_semantics='For multi-cell cases each alpha/b direction is a common perturbation applied to every cell; independent root separately tests all cell input coordinates. External composition only for QA, no horizon planner delivered.',exact_structural_gates='Command/progress coefficients vs rational closed form; B_alpha=h²Q and A_w=hQ vs independent frozen physical J1/J2; all2ms semiimplicit q sensitivity identities; matched-origin affine defects.',nominal_fixture_source_sha256=sha(prev/'parity-attempt2/cpp.json'),seen_history_raw_sha256=sha(raw),scope='Interior-only cell sensitivity reference. Common actual task starts s=0/r=0 and terminal bounds excluded, not shifted to epsilon; not main-startup ready. Unsupported is not nondifferentiability proof. No global condensation/cost/controller/new plant/task/timing acceptance.'))
 print('PREPARED',len(cases),'cases',len(fd),'FD cases',len(batches),'batches',flush=True)
def freeze():
 old=json.loads(OLD.read_text());files={Path(x['path']) for x in old['files']}
 for x in old['files']:need(sha(x['path'])==x['sha256'],'prior source changed')
 files|={BIN,BASE,PHYS,OLD,ROOT/'scripts/phase5/verify_public_coupled_augmented_sensitivity.py',ROOT/'results/phase5/development/public-coupled-derivative-cpp-v1/inputs/cases.json'}|set((OUT/'inputs').glob('*'))|set((ROOT/'tools/phase5_public_coupled_augmented_sensitivity_cpp').glob('*'))
 for dep in (ROOT/'build-public-coupled-augmented-sensitivity-cpp-v1').rglob('*.o.d'):
  for token in shlex.split(dep.read_text().replace('\\\n',' '))[1:]:
   p=Path(token);p=p if p.is_absolute() else ROOT/'build-public-coupled-augmented-sensitivity-cpp-v1'/p
   if p.is_file():files.add(p.resolve())
 ldd=subprocess.run(['ldd',str(BIN)],capture_output=True,text=True,check=True).stdout;(OUT/'native_dependencies.txt').write_text(ldd)
 for token in re.findall(r'(/[\w/.+\-]+)',ldd):
  p=Path(token)
  if p.is_file():files.add(p.resolve())
 cache=Path('/mnt/d/CodexTransfer/projects/predictive_motion/phase5/dependency-cache/public-coupled-augmented-sensitivity-cpp-v1');cache.mkdir(exist_ok=False);records=[]
 for p in sorted(files):
  need(p.is_file(),'frozen file exists');digest=sha(p);dest=cache/digest
  if not dest.exists():dest.write_bytes(p.read_bytes())
  need(sha(dest)==digest,'immutable digest');records.append(dict(path=str(p),bytes=p.stat().st_size,sha256=digest,immutable_copy=str(dest)))
 save(OUT/'frozen_before_predictions.json',dict(files=records,scope='Before all sensitivity/oldaugFD forecasts. Original values/API/source/inputs/SDK frozen; metadata-only empty preflight only.'))
 print('FROZEN',len(records),sha(BIN),sha(OUT/'frozen_before_predictions.json'),flush=True)
def checkfreeze():
 for r in json.loads((OUT/'frozen_before_predictions.json').read_text())['files']:need(sha(r['path'])==r['sha256'] and sha(r['immutable_copy'])==r['sha256'],'frozen identity changed '+r['path'])
 need(sha(BASE)=='2fa952127cdd37ceb56396231e2972d50d36c94e9a19c341c9c17169442acf57' and sha(PHYS)=='e2c75c09001ba354ca5371cbfc594a9765c62098d4cdb52e6a1442adc055c6a4','original probes preserved')
def run(binary,inp,out):
 proc=subprocess.run([str(binary),str(XML),str(CONST),str(inp),str(out)],capture_output=True,text=True);out.with_suffix('.stdout').write_text(proc.stdout);out.with_suffix('.stderr').write_text(proc.stderr);out.with_suffix('.exit').write_text(str(proc.returncode)+'\n');need(proc.returncode==0,'native probe exit')
 return json.loads(out.read_text(),parse_constant=lambda x:(_ for _ in ()).throw(ValueError('invalid JSON '+x)))
def num(x):
 try:valid=type(x) in (int,float) and math.isfinite(x)
 except OverflowError:valid=False
 need(valid,'typed finite number')
def vector(x,n):need(type(x) is list and len(x)==n,'vector size');[num(a) for a in x]
def matrix(x,m,n):need(type(x) is list and len(x)==m,'matrix rows');[vector(a,n) for a in x]
def state(z):
 for key in ('q','v','C','w'):vector(z[key],7)
 num(z['s']);num(z['r'])
def finite_tree(x):
 if type(x) in (int,float):num(x)
 elif type(x) is list:
  for y in x:finite_tree(y)
 elif type(x) is dict:
  for y in x.values():finite_tree(y)
def old_values(out,inp):
 from verify_public_coupled_augmented_cpp import validate
 validate(out,inp)
def validate(out,inp):
 need(out['model_success'] is True,'typed true model');finite_tree(out);need(type(out['cases']) is list and len(out['cases'])==len(inp['cases']),'complete case roster');names=[x['name'] for x in out['cases']];need(names==[x['name'] for x in inp['cases']] and len(names)==len(set(names)),'ordered unique names')
 need(out['policy']==dict(cycle_dt=.004,substep_dt=.002,rows=30,state_columns=30,input_columns=8,domain_margin=1e-8,max_cells=512,max_each_total_cycles=5000),'exact support policy')
 converted=[]
 for case,ans in zip(inp['cases'],out['cases']):
  need(type(ans['sensitivity_success']) is bool and ans['sensitivity_success']==case['expected_sensitivity'],'typed expected sensitivity flag');need(type(ans['first_uncertified_substep']) is int,'typed first uncertified index');value=ans['value'];need(value['success']==case['expected_value'],'expected original value flag');converted.append(dict(name=case['name'],**value))
  for key in ('substep_maps','cycle_maps','cell_maps'):need(type(ans[key]) is list,'map arrays')
  counts=(len(value['substeps']),len(value['cycle_end_states']),len(value['cell_end_states'])) if case['expected_sensitivity'] else (case['expected_maps'],case['expected_cycle_maps'],case['expected_cell_maps'])
  need(tuple(len(ans[k]) for k in ('substep_maps','cycle_maps','cell_maps'))==counts,'exact certified prefix counts')
  if ans['sensitivity_success']:need(ans['first_uncertified_substep']==-1,'certified sentinel')
  else:need(type(ans['error']) is str and bool(ans['error']) and ans['first_uncertified_substep']==counts[0],'explicit non-certification error/index')
  for key in ('substep_maps','cycle_maps','cell_maps'):
   for m in ans[key]:
    for index in ('cell','cycle','half'):need(type(m[index]) is int,'typed map index')
    state(m['origin']);state(m['state']);vector(m['input'],8);matrix(m['A'],30,30);matrix(m['B'],30,8);vector(m['defect'],30)
    if key!='cell_maps':state(m['cell_origin']);matrix(m['cell_A'],30,30);matrix(m['cell_B'],30,8);vector(m['cell_defect'],30)
 old_policy=dict(cycle_dt=.004,substep_dt=.002,max_cells=512,max_each_total_cycles=5000,command_v=.0625,command_a=1.,progress_r=.2,progress_s_lower=0,progress_s_upper=1)
 old_values(dict(model_success=True,policy=old_policy,cases=converted),inp)
H=.004;D=.002
DIAG=ROOT/'build-public-coupled-cpp-v2/public_coupled_probe_v2'
def close(a,b,tol=2e-13,msg='exact structural comparison'):
 a,b=np.asarray(a,float),np.asarray(b,float);need(a.shape==b.shape,'matched shape '+msg);error=abs(a-b);need(bool(np.isfinite(error).all() and (error<=tol).all()),msg);return float(error.max(initial=0.))
def compare(a,b):
 a,b=np.asarray(a,float),np.asarray(b,float);need(a.shape==b.shape,'FD matched shape');error=abs(a-b);ratio=error/(ABS+REL*abs(a));need(bool(np.isfinite(error).all() and np.isfinite(ratio).all() and (ratio<=1).all()),'both predeclared per-entry FD gates');return dict(max_absolute=float(error.max(initial=0.)),max_gate_ratio=float(ratio.max(initial=0.)))
def point(p):return dict(q=p['q'],v=p['v'],C=p['C'],w=p['w'],s=p['s_reference'],r=p['r_reference'])
def algebra(k,half):
 h=F(1,250);t=(k-1+F(half,2))*h;A=np.zeros((16,30));B=np.zeros((16,8));I=np.eye(7)
 A[:7,14:21]=I;A[:7,21:28]=float(k*h)*I;B[:7,:7]=float(h*h*k*(k+1)/2)*I;A[7:14,21:28]=I;B[7:14,:7]=float(k*h)*I;A[14,28]=1;A[14,29]=float(t);A[15,29]=1;B[14,7]=float(t*t/2);B[15,7]=float(t);return A,B
def independent_local(J,t):
 A=np.zeros((30,30));B=np.zeros((30,8));A[:14,:14]=J[:,:14];A[:14,14:21]=J[:,14:21];A[:14,21:28]=H*J[:,14:21];B[:14,:7]=(H*H)*J[:,14:21];A[14:21,14:21]=np.eye(7);A[14:21,21:28]=H*np.eye(7);B[14:21,:7]=H*H*np.eye(7);A[21:28,21:28]=np.eye(7);B[21:28,:7]=H*np.eye(7);A[28,28]=1;A[28,29]=t;A[29,29]=1;B[28,7]=.5*t*t;B[29,7]=t;return A,B
def domain(z,c):
 state(z);limits=np.array(c['control_range']).reshape(7,2);C=np.array(z['C']);need(bool(((C-limits[:,0])>1e-8).all() and ((limits[:,1]-C)>1e-8).all()),'strict C support');need(max(abs(x) for x in z['w'])<.0625-1e-8 and min(z['s'],1-z['s'],z['r'],.2-z['r'])>1e-8,'strict augmented support')
def gate_controls(out,inp):
 validate(out,inp);mutations=[('empty',lambda x:x.update(cases=[])),('drop',lambda x:x['cases'].pop()),('reorder',lambda x:x['cases'].reverse()),('duplicate',lambda x:x['cases'][1].update(name=x['cases'][0]['name'])),('model_string',lambda x:x.update(model_success='true')),('success_string',lambda x:x['cases'][0].update(sensitivity_success='true')),('success_int',lambda x:x['cases'][0].update(sensitivity_success=1)),('index_bool',lambda x:x['cases'][0].update(first_uncertified_substep=False)),('drop_half',lambda x:x['cases'][0]['substep_maps'].pop()),('drop_cycle',lambda x:x['cases'][0]['cycle_maps'].pop()),('drop_cell',lambda x:x['cases'][0]['cell_maps'].pop()),('A_row',lambda x:x['cases'][0]['substep_maps'][0]['A'].pop()),('A_col',lambda x:x['cases'][0]['substep_maps'][0]['A'][0].pop()),('B_col',lambda x:x['cases'][0]['cell_maps'][0]['B'][0].pop()),('defect_short',lambda x:x['cases'][0]['cycle_maps'][0]['defect'].pop()),('nan',lambda x:x['cases'][0]['substep_maps'][0]['A'][0].__setitem__(0,float('nan'))),('string',lambda x:x['cases'][0]['substep_maps'][0]['B'][0].__setitem__(0,'0')),('bool',lambda x:x['cases'][0]['cell_maps'][0]['defect'].__setitem__(0,False)),('huge',lambda x:x['cases'][0]['substep_maps'][0]['A'][0].__setitem__(0,10**400)),('state_dimension',lambda x:x['cases'][0]['cell_maps'][0]['origin']['q'].pop()),('cell_A_dimension',lambda x:x['cases'][0]['cycle_maps'][0]['cell_A'].pop()),('cell_B_dimension',lambda x:x['cases'][0]['substep_maps'][0]['cell_B'][0].pop()),('wrong_policy',lambda x:x['policy'].update(domain_margin=0.)),('uncertified_error_missing',lambda x:x['cases'][6].pop('error')),('fabricated_uncertified_cell',lambda x:x['cases'][6]['cell_maps'].append(copy.deepcopy(out['cases'][0]['cell_maps'][0])))]
 records=[]
 for name,change in mutations:
  bad=copy.deepcopy(out);change(bad)
  try:validate(bad,inp)
  except (ValueError,KeyError):records.append(dict(name=name,rejected=True))
  else:raise AssertionError('synthetic corrupted output accepted '+name)
 return dict(positive_controls=1,negative_controls=records,scope='Synthetic altered-output controls; not native execution failures.')
def batches(binary,cases,path,label,validator,box=False):
 outputs=[];manifest=[]
 for i in range(0,len(cases),BATCH):
  inp=dict(cases=cases[i:i+BATCH]);
  if box:inp['box_cases']=[]
  file=path/f'{label}_inputs_{i//BATCH:03d}.json';save(file,inp);manifest.append(dict(path=str(file),sha256=sha(file),count=len(inp['cases'])))
 save(path/(label+'_PRE_CALL_MANIFEST.json'),manifest)
 for i,item in enumerate(manifest):
  inp=json.loads(Path(item['path']).read_text());need(sha(item['path'])==item['sha256'],'derived comparison input identity');out=run(binary,Path(item['path']),path/f'{label}_output_{i:03d}.json');validator(out,inp);outputs.extend(out['cases'])
 need(len(outputs)==len(cases) and [x['name'] for x in outputs]==[x['name'] for x in cases] and len(set(x['name'] for x in outputs))==len(outputs),'complete unique batched comparison roster');return outputs
def maps(case,ans,Js=None):
 """Check certified prefix only; compose globally for QA with tied cell inputs."""
 rec=dict(max_structural=0.,max_defect=0.,global_substeps=[],global_cycles=[],global_cells=[]);globalA=np.eye(30);globalB=np.zeros((30,8));priorA=np.eye(30);priorB=np.zeros((30,8));origin=case['state'];cellorigin=origin;ci=-1;cycle_index=0;previousQA=priorA[:7].copy();previousQB=priorB[:7].copy();J1=None
 for si,m in enumerate(ans['substep_maps']):
  p=ans['value']['substeps'][si];need((m['cell'],m['cycle'],m['half'])==(p['cell'],p['cycle'],p['half']),'exact map timing/order');cell=case['cells'][p['cell']];u=np.r_[cell['alpha'],cell['b']]
  if p['cell']!=ci:
   ci=p['cell'];cellorigin=origin;priorA=np.eye(30);priorB=np.zeros((30,8));previousQA=priorA[:7].copy();previousQB=priorB[:7].copy()
  if p['half']==1:previousQA=priorA[:7].copy();previousQB=priorB[:7].copy()
  A=np.array(m['A']);B=np.array(m['B']);CA=A@priorA;CB=A@priorB+B
  errors=[close(pack(m['origin']),pack(origin),0.,'matched cycle origin'),close(pack(m['cell_origin']),pack(cellorigin),0.,'matched cell origin'),close(pack(m['state']),pack(point(p)),0.,'exact halfstep nominal'),close(m['input'],u,0.,'held input'),close(m['cell_A'],CA,msg='cumulative cell A'),close(m['cell_B'],CB,msg='cumulative cell B')]
  LA,LB=algebra(1,p['half']);EA,EB=algebra(p['cycle'],p['half']);errors.extend([close(A[14:],LA,msg='local command/progress A'),close(B[14:],LB,msg='local command/progress B'),close(CA[14:],EA,msg='rational cumulative A'),close(CB[14:],EB,msg='rational cumulative B'),close(A[:14,21:28],H*A[:14,14:21],msg='accepted w hQ'),close(B[:14,:7],H*H*A[:14,14:21],msg='tiny alpha h²Q'),close(A[:14,28:],np.zeros((14,2)),0.,'physical progress zeros'),close(B[:14,7],np.zeros(14),0.,'physical b zeros'),close(CA[:7],previousQA+D*CA[7:14],msg='semiimplicit q A'),close(CB[:7],previousQB+D*CB[7:14],msg='semiimplicit q B')])
  if Js is not None:
   J=np.array(Js[si]['jacobian']);need(Js[si]['value']['q']==p['q'] and Js[si]['value']['v']==p['v'],'independent physical exact nominal')
   if p['half']==1:J1=J;P=J
   else:P=np.c_[J[:,:14]@J1[:,:14],J[:,:14]@J1[:,14:21]+J[:,14:21]]
   IA,IB=independent_local(P,p['half']*D);errors.extend([close(A,IA,msg='independent J1/J2 cycle A'),close(B,IB,msg='independent J1/J2 cycle B')])
  rec['max_defect']=max(rec['max_defect'],close(m['defect'],pack(m['state'])-A@pack(origin)-B@u,msg='local matched affine defect'),close(m['cell_defect'],pack(m['state'])-CA@pack(cellorigin)-CB@u,msg='cumulative matched affine defect'));previousQA=CA[:7].copy();previousQB=CB[:7].copy();rec['global_substeps'].append((CA@globalA,CA@globalB+CB));rec['max_structural']=max(rec['max_structural'],*errors)
  if p['half']==2 and cycle_index<len(ans['cycle_maps']):
   cm=ans['cycle_maps'][cycle_index];need((cm['cell'],cm['cycle'],cm['half'])==(ci,p['cycle'],2),'cycle map timing');close(pack(cm['state']),pack(ans['value']['cycle_end_states'][cycle_index]),0.,'exact original cycle endpoint');close(pack(cm['origin']),pack(origin),0.,'cycle origin');close(pack(cm['cell_origin']),pack(cellorigin),0.,'cycle cell origin')
   for key in ('A','B','cell_A','cell_B','input'):close(cm[key],m[key],0.,'cycle/half2 '+key)
   close(cm['defect'],pack(cm['state'])-A@pack(origin)-B@u,msg='cycle matched defect');close(cm['cell_defect'],pack(cm['state'])-CA@pack(cellorigin)-CB@u,msg='cycle cumulative defect');rec['global_cycles'].append((CA@globalA,CA@globalB+CB));priorA=CA;priorB=CB;origin=cm['state'];cycle_index+=1
   if p['cycle']==cell['cycles'] and len(rec['global_cells'])<len(ans['cell_maps']):
    ce=ans['cell_maps'][len(rec['global_cells'])];need((ce['cell'],ce['cycle'],ce['half'])==(ci,p['cycle'],2),'cell map timing');close(pack(ce['origin']),pack(cellorigin),0.,'cell-map original origin');close(pack(ce['state']),pack(ans['value']['cell_end_states'][ci]),0.,'cell nominal endpoint');close(ce['input'],u,0.,'cell held input');close(ce['A'],CA,0.,'cell final A');close(ce['B'],CB,0.,'cell final B');close(ce['defect'],pack(ce['state'])-CA@pack(cellorigin)-CB@u,msg='cell matched defect');globalA=CA@globalA;globalB=CA@globalB+CB;rec['global_cells'].append((globalA.copy(),globalB.copy()))
 need(cycle_index==len(ans['cycle_maps']) and len(rec['global_cells'])==len(ans['cell_maps']),'complete certified prefix semantics');return rec

def verify():
 checkfreeze();attempt=OUT/'parity-attempt1';attempt.mkdir(exist_ok=False);inp=json.loads((OUT/'inputs/cases.json').read_text());analytic=run(BIN,OUT/'inputs/cases.json',attempt/'analytic.json');validate(analytic,inp);gates=gate_controls(analytic,inp);print('Analytic roster/gates passed',flush=True)
 original=run(BASE,OUT/'inputs/cases.json',attempt/'original_value.json');old_values(original,inp)
 for a,b in zip(analytic['cases'],original['cases']):need(a['value']=={k:v for k,v in b.items() if k!='name'},'exact unchanged original forward result '+a['name'])
 from verify_public_coupled_derivative_cpp import validate as physical_validate,branch
 from validate_public_coupled_native_output_v2 import validate_output
 from verify_public_coupled_augmented_cpp import oracle
 physical=[]
 for case,ans in zip(inp['cases'][:6],analytic['cases'][:6]):
  prev=case['state']
  for i,p in enumerate(ans['value']['substeps']):
   physical.append(dict(name=f'{case["name"]}_physical{i}',q=prev['q'],v=prev['v'],C=p['C'],value_success=True,jacobian_success=True));prev=point(p)
 Js=batches(PHYS,physical,attempt,'nominal_physical_derivative',physical_validate);jl={x['name']:x for x in Js};print('Independent J1/J2 calls passed',len(Js),flush=True)
 mapping=[]
 for i,(case,ans) in enumerate(zip(inp['cases'],analytic['cases'])):
  j=[jl[f'{case["name"]}_physical{k}'] for k in range(len(ans['substep_maps']))] if i<6 else None;mapping.append(maps(case,ans,j))
 held=mapping[1]['global_cells'][-1];split=mapping[2]['global_cells'][-1];close(held[0],split[0],1e-12,'held/split A');close(held[1],split[1],1e-12,'held/split B');need(analytic['cases'][1]['value']['final_state']==analytic['cases'][2]['value']['final_state'],'held/split exact forward endpoint')
 fd_inputs=[];fd_outputs=[]
 for i,item in enumerate(json.loads((OUT/'inputs/fd_batches.json').read_text())):
  need(sha(item['path'])==item['sha256'],'frozen FD input identity');x=json.loads(Path(item['path']).read_text());y=run(BASE,Path(item['path']),attempt/f'fd_values_{i:03d}.json');old_values(y,x);fd_inputs.extend(x['cases']);fd_outputs.extend(y['cases'])
 need(len(fd_inputs)==918 and len(fd_outputs)==918 and [x['name'] for x in fd_inputs]==[x['name'] for x in fd_outputs] and len(set(x['name'] for x in fd_outputs))==918,'complete FD roster');fl={x['name']:x for x in fd_outputs};c=json.loads(CONST.read_text());diagnostic=[]
 for case,ans in zip(fd_inputs,fd_outputs):
  domain(case['state'],c)
  for ce in case['cells']:need(max(abs(x) for x in ce['alpha'])<1-1e-8 and math.isfinite(ce['b']),'strict FD held input')
  ref=oracle(case);need(len(ref)==len(ans['substeps']),'complete rational oracle');prev=case['state']
  for i,(p,r) in enumerate(zip(ans['substeps'],ref)):
   domain(point(p),c)
   for key in ('C','w'):close(p[key],r[key],msg='rational FD '+key)
   for key in ('s_reference','r_reference','elapsed_s'):close(p[key],r[key],msg='rational FD '+key)
   diagnostic.append(dict(name=f'{case["name"]}_physical{i}',q=prev['q'],v=prev['v'],targets=[p['C']],expect_success=True));prev=point(p)
 print('Old augmented FD roster passed',len(fd_outputs),'physical diagnostics',len(diagnostic),flush=True)
 diagnostics=batches(DIAG,diagnostic,attempt,'fd_physical_diagnostic',validate_output,True);dl={x['name']:x for x in diagnostics};dil={x['name']:x for x in diagnostic};signatures={}
 for case,ans in zip(fd_inputs,fd_outputs):
  sig=[]
  for i,p in enumerate(ans['substeps']):
   name=f'{case["name"]}_physical{i}';d=dl[name]['last'];need(d['q']==p['q'] and d['v']==p['v'] and d['friction']==p['friction'],'every original2ms diagnostic exact parity');x=dil[name];sig.append(branch(dict(q=x['q'],v=x['v'],C=x['targets'][0]),d,c));M=np.array(d['M']);K=M+D*np.diag(np.array(c['passive_damping'])-np.array(c['biasprm']).reshape(7,10)[:,2]);Hs=(np.array(d['H'])+np.array(d['H']).T)/2
   free=[j for j,x in enumerate(d['friction']['branches']) if x==0];matrices=[M,Hs,K]+([Hs[np.ix_(free,free)]] if free else [])
   for matrix_ in matrices:ev=np.linalg.eigvalsh(matrix_);need(bool(ev[0]>0 and ev[-1]/ev[0]<=1e12),'every FD matrix SPD/condition support')
  signatures[case['name']]=sig
 reports=[]
 for ci,(case,ans) in enumerate(zip(inp['cases'],analytic['cases'])):
  rec=dict(name=case['name'],value_success=bool(ans['value']['success']),sensitivity_success=bool(ans['sensitivity_success']),certified_substeps=len(ans['substep_maps']),certified_cycles=len(ans['cycle_maps']),certified_cells=len(ans['cell_maps']),max_structural=mapping[ci]['max_structural'],max_defect=mapping[ci]['max_defect'])
  if not ans['sensitivity_success']:rec['error']=ans['error'];rec['first_uncertified_substep']=ans['first_uncertified_substep'];reports.append(rec);continue
  need(ans['value']=={k:v for k,v in fl[case['name']].items() if k!='name'},'FD nominal exact original value');epsreports=[]
  for ei,e in enumerate(EPS):
   maxima=dict(max_absolute=0.,max_gate_ratio=0.)
   for j in range(38):
    names=[f'{case["name"]}_e{ei}_col{j}_sign{s}' for s in (-1,1)];minus,plus=[fl[n] for n in names]
    for n in names:need(signatures[n]==signatures[case['name']],'all perturbations retain exact strict branches')
    for key,nom in [('global_substeps','substeps'),('global_cycles','cycle_end_states'),('global_cells','cell_end_states')]:
     need(len(mapping[ci][key])==len(minus[nom])==len(plus[nom]),'FD exact endpoint roster')
     for k,(A,B) in enumerate(mapping[ci][key]):
      vminus=point(minus[nom][k]) if nom=='substeps' else minus[nom][k];vplus=point(plus[nom][k]) if nom=='substeps' else plus[nom][k];fd=(pack(vplus)-pack(vminus))/(2*e);col=A[:,j] if j<30 else B[:,j-30];r=compare(col,fd)
      for field in maxima:maxima[field]=max(maxima[field],r[field])
   epsreports.append(dict(epsilon=e,**maxima))
  rec.update(epsilons=epsreports,pass_check=True);reports.append(rec)
 checkfreeze();save(attempt/'report.json',dict(status='PASS_BOUNDED_AUGMENTED_CYCLE_CELL_SENSITIVITIES_ONLY',phase5='NOT_ACCEPTED',phase6='NOT_STARTED',freeze_sha256=sha(OUT/'frozen_before_predictions.json'),binary_sha256=sha(BIN),records=reports,synthetic_output_gates=gates,fd_augmented_cases=len(fd_outputs),fd_original_physical_diagnostics=len(diagnostic),independent_nominal_physical_derivatives=len(Js),epsilons=EPS,absolute_per_entry=ABS,relative_per_entry=REL,scope='Selected central-domain cycle/cell sensitivities; exact frozen forward values, rational command/progress, independent J1/J2, all half/cycle/cell endpoints all38 directions both epsilons, strict branch and SPD checks at every perturbation. Initial/terminal progress bounds unsupported. No main-startup readiness, global planner/controller/plant/task/timing or Phase5 acceptance.'))
 print('PASS',len(reports),'cases',len(fd_outputs),'augmented FD',len(diagnostic),'original physical diagnostics',flush=True)
if __name__=='__main__':globals()[sys.argv[1]]()
