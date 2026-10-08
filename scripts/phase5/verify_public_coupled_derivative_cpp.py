#!/usr/bin/env python3
"""Frozen local analytic physical2ms reference, independently differenced base."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
import json,hashlib,csv,copy,math,subprocess,sys,re,shlex
from pathlib import Path
import numpy as np
ROOT=Path('/home/codextransfer/predictive_motion');OUT=ROOT/'results/phase5/development/public-coupled-derivative-cpp-v1'
BIN=ROOT/'build-public-coupled-derivative-cpp-v1/public_coupled_derivative_probe';BASE=ROOT/'build-public-coupled-cpp-v2/public_coupled_probe_v2'
XML=ROOT/'experiments/generated/inspection/inspection_fr3.xml';CONST=ROOT/'results/phase5/development/public-coupled-servo-v1-training/public_constants.json'
OLD=ROOT/'results/phase5/development/public-coupled-augmented-cpp-v1/frozen_before_predictions.json'
RAWS={'train91011':Path('/mnt/d/CodexTransfer/projects/predictive_motion/phase5/raw/servo-identification-v1-training/raw.csv'),'seen91013':Path('/mnt/d/CodexTransfer/projects/predictive_motion/phase5/raw/public-coupled-v2-development-validation-91013/raw.csv')}
HASHES={'train91011':'ab9d14efa1a5886c0683db25345f24d5cacd55343e2768eb60536fa180a11dce','seen91013':'ea70d9e8b01bc6e44387e2f4701779243bb1b202020a61aef18312fac1c054e8'}
EPS=[1e-6,3e-7];ABS=5e-7;REL=5e-6
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):Path(p).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def vals(r,p):return [float(r[p+str(j)]) for j in range(7)]
def need(x,msg):
 if not x:raise ValueError(msg)
def prepare():
 inputs=OUT/'inputs';inputs.mkdir(exist_ok=False);c=json.loads(CONST.read_text());cases=[]
 for dataset,ticks in {'train91011':[100,500,1250,2400],'seen91013':[100,500,690,920,2400]}.items():
  need(sha(RAWS[dataset])==HASHES[dataset],'raw identity')
  with RAWS[dataset].open() as f:rows=list(csv.DictReader(f))
  for tick in ticks:
   row=next(r for r in rows if int(r['tick'])==tick and int(r['substep'])==1)
   cases.append(dict(name=f'{dataset}_tick{tick}',q=vals(row,'q_before_'),v=vals(row,'v_before_'),C=vals(row,'target_'),value_success=True,jacobian_success=True,dataset=dataset,tick=tick))
 prev=ROOT/'results/phase5/development/public-coupled-cpp-v2';oldinp=json.loads((prev/'inputs/cases.json').read_text());oldout=json.loads((prev/'parity-attempt2/cpp.json').read_text());q=np.array(next(x['q'] for x in oldinp['cases'] if x['name']=='nominal_zero'));old=next(x['last'] for x in oldout['cases'] if x['name']=='nominal_zero');M=np.array(old['M']);W=np.array(old['W']);n=np.array(old['bias'])
 # Static public R is read from the retained native metadata, no parameter fitting.
 H=(W+W.T)/2+np.diag(oldout['metadata']['R']);eta=np.array(c['friction_bounds']);kp=np.array(c['gainprm']).reshape(7,10)[:,0];bias=np.array(c['biasprm']).reshape(7,10);zero=[0.]*7
 def command(tau,v=zero):return ((np.array(tau)-bias[:,0]-bias[:,1]*q-bias[:,2]*np.array(v))/kp).tolist()
 def add(name,C,v=zero,jac=True,fixture=None):
  z=dict(name=name,q=q.tolist(),v=list(v),C=list(C),value_success=True,jacobian_success=jac)
  if fixture is not None:z['fixture']=fixture
  cases.append(z)
 def friction_case(name,f,g,jac=True):
  f=np.array(f);g=np.array(g);smooth=M@(-H@f+g);tau=n+smooth;C=command(tau)
  ranges=np.array(c['joint_actuator_force_range']).reshape(7,2);control=np.array(c['control_range']).reshape(7,2)
  need(bool(np.all(tau>ranges[:,0]) and np.all(tau<ranges[:,1]) and np.all(np.array(C)>control[:,0]) and np.all(np.array(C)<control[:,1])),'predeclared synthetic within fixed unclipped static profile')
  add(name,C,jac=jac,fixture=dict(force=f.tolist(),gradient=g.tolist(),construction='Public affine torque + retained M/n/H at nominal_zero; algebraic state design, no fit/plant.'))
 friction_case('all_free',zero,zero)
 mixed=zero.copy();mixed[0]=-eta[0];mixed[1]=eta[1];mixed[2]=.2*eta[2];g=zero.copy();g[0]=.1;g[1]=-.1;friction_case('mixed_strict_lower_upper_free',mixed,g)
 f=[(-1 if j%2==0 else 1)*eta[j] for j in range(7)];g=[(.3 if j%2==0 else -.3) for j in range(7)];friction_case('all_strict_friction_bounds',f,g)
 add('strict_joint_force_saturation',(q+np.array([.1,-.1,.1,-.1,.1,-.1,.1])).tolist())
 C=command(n);C[0]=c['control_range'][0]-.2;add('strict_control_saturation',C)
 f=zero.copy();f[0]=-eta[0];friction_case('weak_lower_zero_gradient',f,zero,False)
 f=zero.copy();f[0]=eta[0];friction_case('weak_upper_zero_gradient',f,zero,False)
 f=zero.copy();f[0]=-eta[0]+.5e-7;friction_case('near_free_lower_slack',f,zero,False)
 for label,delta in [('exact',0.),('inside',5e-9),('outside',-5e-9)]:
  C=command(n);C[0]=c['control_range'][0]+delta;add('control_lower_'+label,C,jac=False)
 for label,delta in [('exact',0.),('near_inside',-.5e-7)]:
  tau=n.copy();tau[0]=c['joint_actuator_force_range'][1]+delta;add('joint_force_upper_'+label,command(tau),jac=False)
 initial=copy.deepcopy(cases[9])
 for key,value,label in [('q',q.tolist()[:6],'q_dimension'),('v',zero[:6],'v_dimension'),('C',zero[:6],'C_dimension'),('q',['.nan']+q.tolist()[1:],'q_nan'),('v',['.inf']+zero[1:],'v_inf'),('C',['.nan']+zero[1:],'C_nan'),('v',[1e308]*7,'finite_preclamp_overflow'),('q',[c['joint_range'][0]]+q.tolist()[1:],'physical_joint_boundary')]:
  z=copy.deepcopy(initial);z.update(name=label,value_success=False,jacobian_success=False);z[key]=value;cases.append(z)
 positives=[z for z in cases if z['jacobian_success']];fd=[]
 for z in positives:
  fd.append(dict(name=z['name']+'_base',q=z['q'],v=z['v'],targets=[z['C']],expect_success=True))
  for ei,e in enumerate(EPS):
   for j in range(21):
    for sign in (-1,1):
     a=copy.deepcopy(z);key=('q','v','C')[j//7];a[key][j%7]+=sign*e
     fd.append(dict(name=f'{z["name"]}_e{ei}_col{j}_sign{sign}',q=a['q'],v=a['v'],targets=[a['C']],expect_success=True,epsilon=e,column=j,sign=sign,parent=z['name']))
 save(inputs/'cases.json',dict(cases=cases));save(inputs/'fd_cases.json',dict(cases=fd,box_cases=[]));save(inputs/'empty.json',dict(cases=[]))
 save(inputs/'declared_scope.json',dict(epsilons=EPS,absolute_per_entry=ABS,relative_per_entry=REL,gate='abs(error)<=abs+rel*abs(analytic) for both independently reported epsilon values; same strict friction/clip branches for every perturbation.',rows=14,columns=21,positive_cases=len(positives),threshold_unsupported=sum(z['value_success'] and not z['jacobian_success'] for z in cases),invalid_value_cases=sum(not z['value_success'] for z in cases),fixture_source_inputs_sha256=sha(prev/'inputs/cases.json'),fixture_source_output_sha256=sha(prev/'parity-attempt2/cpp.json'),scope='Bounded physical2ms analytic reference; retained seen states and prospective algebraic fixtures. No fitting, plant, augmented/controller/task/timing acceptance.'))
 print('PREPARED',len(cases),len(positives),len(fd),flush=True)
def freeze():
 prior=json.loads(OLD.read_text());files={Path(x['path']) for x in prior['files']}
 for x in prior['files']:need(sha(x['path'])==x['sha256'],'prior augmented/v2 live changed')
 files|={BIN,BASE,OLD,ROOT/'scripts/phase5/verify_public_coupled_derivative_cpp.py',ROOT/'results/phase5/development/public-coupled-cpp-v2/parity-attempt2/cpp.json',ROOT/'results/phase5/development/public-coupled-cpp-v2/inputs/cases.json'}|set((OUT/'inputs').glob('*'))|set((ROOT/'tools/phase5_public_coupled_derivative_cpp').glob('*'))
 for dep in (ROOT/'build-public-coupled-derivative-cpp-v1').rglob('*.o.d'):
  for token in shlex.split(dep.read_text().replace('\\\n',' '))[1:]:
   p=Path(token);p=p if p.is_absolute() else ROOT/'build-public-coupled-derivative-cpp-v1'/p
   if p.is_file():files.add(p.resolve())
 ldd=subprocess.run(['ldd',str(BIN)],capture_output=True,text=True,check=True).stdout;(OUT/'native_dependencies.txt').write_text(ldd)
 for token in re.findall(r'(/[\w/.+\-]+)',ldd):
  p=Path(token)
  if p.is_file():files.add(p.resolve())
 cache=Path('/mnt/d/CodexTransfer/projects/predictive_motion/phase5/dependency-cache/public-coupled-derivative-cpp-v1');cache.mkdir(exist_ok=False);records=[]
 for p in sorted(files):
  need(p.is_file(),'freeze file exists');digest=sha(p);dest=cache/digest
  if not dest.exists():dest.write_bytes(p.read_bytes())
  need(sha(dest)==digest,'immutable digest');records.append(dict(path=str(p),sha256=digest,bytes=p.stat().st_size,immutable_copy=str(dest)))
 save(OUT/'frozen_before_predictions.json',dict(files=records,prior_freeze_sha256=sha(OLD),scope='Before all derivative/FD forecasts; metadata-only empty roster preflight only. Prior augmented+v2 source/probes/constants/raw preserved.'))
 print('FROZEN',len(records),sha(BIN),sha(OUT/'frozen_before_predictions.json'),flush=True)
def checkfreeze():
 for rec in json.loads((OUT/'frozen_before_predictions.json').read_text())['files']:need(sha(rec['path'])==rec['sha256'] and sha(rec['immutable_copy'])==rec['sha256'],'live/immutable changed '+rec['path'])
 need(sha(BASE)=='fa1a00344e73d8fe2266541ba4e2b34c362351b30a4f21dfa34c04867f585a04','original base probe')
def run(binary,inp,out):
 p=subprocess.run([str(binary),str(XML),str(CONST),str(inp),str(out)],capture_output=True,text=True);out.with_suffix('.stdout').write_text(p.stdout);out.with_suffix('.stderr').write_text(p.stderr);out.with_suffix('.exit').write_text(str(p.returncode)+'\n');need(p.returncode==0,'probe success')
 return json.loads(out.read_text(),parse_constant=lambda x:(_ for _ in ()).throw(ValueError('invalid JSON '+x)))
def num(x):
 try:ok=type(x) in (int,float) and math.isfinite(x)
 except OverflowError:ok=False
 need(ok,'typed finite numeric value')
def vector(x,n):need(type(x) is list and len(x)==n,'vector length');[num(y) for y in x]
def matrix(x,m,n):need(type(x) is list and len(x)==m,'matrix rows');[vector(row,n) for row in x]
def finite_tree(x):
 if type(x) in (int,float):num(x)
 elif type(x) is list:
  for y in x:finite_tree(y)
 elif type(x) is dict:
  for y in x.values():finite_tree(y)
def validate(out,inp):
 need(out['model_success'] is True,'typed true model');finite_tree(out);need(type(out['cases']) is list and len(out['cases'])==len(inp['cases']),'full roster');names=[z['name'] for z in out['cases']];need(names==[z['name'] for z in inp['cases']] and len(names)==len(set(names)),'ordered unique names')
 expected=dict(h=.002,control_margin=1e-8,force_margin=1e-7,friction_margin=1e-7,gradient_margin=1e-7,max_condition=1e12,residual_limit=1e-10,rows=14,columns=21,analytic_rnea_calls=8);need(out['policy']==expected,'exact policy')
 converted=[];baseinp=[]
 for case,ans in zip(inp['cases'],out['cases']):
  for key in ('value_success','jacobian_success'):need(type(ans[key]) is bool and ans[key]==case[key],'typed expected '+key)
  need(ans['value_success'] or not ans['jacobian_success'],'no Jacobian without value')
  if not ans['jacobian_success']:need(type(ans.get('error')) is str and bool(ans['error']),'explicit unsupported/invalid error')
  if ans['value_success']:
   value=ans['value'];converted.append(dict(name=case['name'],success=True,trace=[value],last=value));d=ans['diagnostics'];need(type(d['complete']) is bool and d['complete']==ans['jacobian_success'],'diagnostic flag')
   for key in ('control','actuator','joint_force'):
    need(type(d[key]) is list and len(d[key])==7,'all nested clip diagnostics')
    for b in d[key]:
     need(type(b['enabled']) is bool and type(b['side']) is int and b['side'] in (-1,0,1) and type(b['slope']) in (int,float) and b['slope'] in (0,1),'typed clip side/slope')
     for field in ('input','output','lower','upper','margin'):num(b[field])
     if not b['enabled']:need(b['side']==0 and b['slope']==1 and b['margin']==0,'disabled branch convention')
   vector(d['friction_gradient'],7);vector(d['friction_margin'],7)
  else:need('value' not in ans,'no fabricated failed value');converted.append(dict(name=case['name'],success=False,error=ans['error'],trace=[]))
  baseinp.append(dict(name=case['name'],q=case['q'],v=case['v'],targets=[case['C']],expect_success=case['value_success']))
  if ans['jacobian_success']:
   matrix(ans['jacobian'],14,21);d=ans['diagnostics'];matrix(d['nq'],7,7);matrix(d['nv'],7,7);need(type(d['mass_q']) is list and len(d['mass_q'])==7,'mass tensor7');[matrix(m,7,7) for m in d['mass_q']]
   for k in ('smooth_jacobian','friction_jacobian','acceleration_jacobian'):matrix(d[k],7,21)
   need(type(d['solve_conditions']) is list and len(d['solve_conditions'])>=4 and len(d['solve_conditions'])==len(d['solve_residuals']),'all successful solve diagnostics')
   for x in d['solve_conditions']:num(x);need(1<=x<=1e12,'condition bound')
   for x in d['solve_residuals']:num(x);need(0<=x<=1e-10,'residual bound')
  else:need('jacobian' not in ans,'unsupported must omit unique Jacobian')
 from validate_public_coupled_native_output_v2 import validate_output
 validate_output(dict(model_success=True,metadata=out['metadata'],cases=converted,box_cases=[]),dict(cases=baseinp,box_cases=[]))
def gate_controls(out,inp):
 records=[];mutations=[('empty',lambda x:x.update(cases=[])),('drop',lambda x:x['cases'].pop()),('reverse',lambda x:x['cases'].reverse()),('model_string',lambda x:x.update(model_success='true')),('value_bool_string',lambda x:x['cases'][0].update(value_success='true')),('jac_bool_int',lambda x:x['cases'][0].update(jacobian_success=1)),('missing_jac',lambda x:x['cases'][0].pop('jacobian')),('jac_short_row',lambda x:x['cases'][0]['jacobian'].pop()),('jac_short_col',lambda x:x['cases'][0]['jacobian'][0].pop()),('jac_nan',lambda x:x['cases'][0]['jacobian'][0].__setitem__(0,float('nan'))),('jac_string',lambda x:x['cases'][0]['jacobian'][0].__setitem__(0,'0')),('jac_bool',lambda x:x['cases'][0]['jacobian'][0].__setitem__(0,False)),('mass_tensor_short',lambda x:x['cases'][0]['diagnostics']['mass_q'].pop()),('mass_tensor_nan',lambda x:x['cases'][0]['diagnostics']['mass_q'][0][0].__setitem__(0,float('nan'))),('bad_condition',lambda x:x['cases'][0]['diagnostics']['solve_conditions'].__setitem__(0,1e13)),('bad_residual',lambda x:x['cases'][0]['diagnostics']['solve_residuals'].__setitem__(0,1e-9)),('missing_clip',lambda x:x['cases'][0]['diagnostics']['joint_force'].pop()),('value_nan',lambda x:x['cases'][0]['value']['v'].__setitem__(0,float('nan'))),('huge_integer',lambda x:x['cases'][0]['jacobian'][0].__setitem__(0,10**400))]
 unsupported=next(i for i,z in enumerate(inp['cases']) if z['value_success'] and not z['jacobian_success']);mutations.append(('fabricated_unsupported_J',lambda x:x['cases'][unsupported].update(jacobian=out['cases'][0]['jacobian'])))
 for name,change in mutations:
  bad=copy.deepcopy(out);change(bad)
  try:validate(bad,inp)
  except (ValueError,KeyError):records.append(dict(name=name,rejected=True))
  else:raise AssertionError('synthetic corruption accepted '+name)
 return dict(positive_controls=1,negative_controls=records,scope='Modified-output QA controls only, not native failures.')
def branch(case,value,c):
 control=[];act=[];joint=[];C=np.array(case['C']);q=np.array(case['q']);v=np.array(case['v']);kp=np.array(c['gainprm']).reshape(7,10)[:,0];bias=np.array(c['biasprm']).reshape(7,10)
 def stage(x,lo,hi,enabled,margin):
  if not enabled:return x,0
  side=-1 if x<lo else 1 if x>hi else 0;distance=lo-x if side==-1 else x-hi if side==1 else min(x-lo,hi-x);need(distance>margin,'FD strict clip margin');return min(max(x,lo),hi),side
 for j in range(7):
  u,b=stage(C[j],*c['control_range'][2*j:2*j+2],c['control_limited'][j],1e-8);control.append(b);y=kp[j]*u+bias[j,0]+bias[j,1]*q[j]+bias[j,2]*v[j]
  y,b=stage(y,*c['actuator_force_range'][2*j:2*j+2],c['actuator_force_limited'][j],1e-7);act.append(b);y,b=stage(y,*c['joint_actuator_force_range'][2*j:2*j+2],c['joint_actuator_force_limited'][j],1e-7);joint.append(b)
 f=np.array(value['friction']['force']);eta=np.array(c['friction_bounds']);g=np.array(value['H'])@f+np.array(value['ell']);labels=[]
 for j in range(7):
  label=2 if eta[j]==0 else -1 if f[j]<=-eta[j] else 1 if f[j]>=eta[j] else 0;labels.append(label)
  if label==0:need(eta[j]-abs(f[j])>1e-7 and abs(g[j])<=1e-10,'FD strict free friction')
  elif label!=2:need((g[j] if label==-1 else -g[j])>1e-7,'FD strict active gradient')
 need(labels==value['friction']['branches'],'exact FD friction labels');return control,act,joint,labels
def compare(a,b):
 a=np.asarray(a);b=np.asarray(b);error=abs(a-b);ratio=error/(ABS+REL*abs(a));need(bool(np.isfinite(error).all() and np.isfinite(ratio).all() and (ratio<=1).all()),'independent FD threshold');return dict(max_absolute=float(error.max()),max_gate_ratio=float(ratio.max()))
def verify():
 checkfreeze();attempt=OUT/'parity-attempt1';attempt.mkdir(exist_ok=False);inp=json.loads((OUT/'inputs/cases.json').read_text());native=run(BIN,OUT/'inputs/cases.json',attempt/'analytic.json');validate(native,inp);gates=gate_controls(native,inp)
 fdinp=json.loads((OUT/'inputs/fd_cases.json').read_text());fd=run(BASE,OUT/'inputs/fd_cases.json',attempt/'fd.json');from validate_public_coupled_native_output_v2 import validate_output
 validate_output(fd,fdinp);lookup={x['name']:x for x in fd['cases']};inlookup={x['name']:x for x in fdinp['cases']};c=json.loads(CONST.read_text());records=[]
 for case,ans in zip(inp['cases'],native['cases']):
  rec=dict(name=case['name'],value_success=ans['value_success'],jacobian_success=ans['jacobian_success'])
  if not ans['jacobian_success']:rec['error']=ans['error'];records.append(rec);continue
  value=ans['value'];baseline=lookup[case['name']+'_base']['last'];need(value==baseline,'exact original probe value/diagnostics');signature=branch(case,value,c);rec['branches']=dict(control=signature[0],actuator=signature[1],joint_force=signature[2],friction=signature[3]);J=np.array(ans['jacobian']);d=ans['diagnostics'];reports=[]
  if 'fixture' in case:
   need(max(abs(np.array(value['friction']['force'])-case['fixture']['force']))<=1e-10 and max(abs(np.array(d['friction_gradient'])-case['fixture']['gradient']))<=1e-10,'prospective force/gradient fixture')
  for ei,e in enumerate(EPS):
   approx=np.zeros((14,21));nq=np.zeros((7,7));nv=np.zeros((7,7));mass=[np.zeros((7,7)) for _ in range(7)]
   for j in range(21):
    names=[f'{case["name"]}_e{ei}_col{j}_sign{sgn}' for sgn in (-1,1)];pair=[lookup[x]['last'] for x in names]
    for name,val in zip(names,pair):
     fdcase=inlookup[name];need(branch(dict(q=fdcase['q'],v=fdcase['v'],C=fdcase['targets'][0]),val,c)==signature,'every FD perturbation same strict branches')
    approx[:,j]=(np.r_[pair[1]['q'],pair[1]['v']]-np.r_[pair[0]['q'],pair[0]['v']])/(2*e)
    if j<7:nq[:,j]=(np.array(pair[1]['bias'])-pair[0]['bias'])/(2*e);mass[j]=(np.array(pair[1]['M'])-pair[0]['M'])/(2*e)
    elif j<14:nv[:,j-7]=(np.array(pair[1]['bias'])-pair[0]['bias'])/(2*e)
   reports.append(dict(epsilon=e,transition=compare(J,approx),nq=compare(d['nq'],nq),nv=compare(d['nv'],nv),mass_q=[compare(d['mass_q'][j],mass[j]) for j in range(7)],finite_difference=approx.tolist()))
  rec.update(epsilons=reports,pass_check=True);records.append(rec)
 checkfreeze();save(attempt/'report.json',dict(status='PASS_BOUNDED_PHYSICAL_DERIVATIVE_REFERENCE_ONLY',phase5='NOT_ACCEPTED',phase6='NOT_STARTED',records=records,synthetic_output_gates=gates,freeze_sha256=sha(OUT/'frozen_before_predictions.json'),epsilons=EPS,absolute_per_entry=ABS,relative_per_entry=REL,fd_native_cases=len(fdinp['cases']),scope='Analytic SDK fullM/nle derivative, strict selected branches, two independent native finite-difference epsilon comparisons. No plant/fitting/augmented/controller/task/timing claim.'))
 print('PASS',len(records),'cases',len(fdinp['cases']),'independent base calls',flush=True)
if __name__=='__main__':globals()[sys.argv[1]]()
