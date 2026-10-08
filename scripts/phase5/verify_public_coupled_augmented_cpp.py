#!/usr/bin/env python3
"""Bounded component-only augmentation QA; no plant, fitting or controller."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
import csv,hashlib,json,copy,sys,subprocess,math,re,shlex
from pathlib import Path
from fractions import Fraction as F
ROOT=Path('/home/codextransfer/predictive_motion')
OUT=ROOT/'results/phase5/development/public-coupled-augmented-cpp-v1'
BIN=ROOT/'build-public-coupled-augmented-cpp-v1/public_coupled_augmented_probe'
BASE=ROOT/'build-public-coupled-cpp-v2/public_coupled_probe_v2'
XML=ROOT/'experiments/generated/inspection/inspection_fr3.xml'
CONST=ROOT/'results/phase5/development/public-coupled-servo-v1-training/public_constants.json'
OLD=ROOT/'results/phase5/development/public-coupled-cpp-v2/frozen_after_report_repair_before_repeat.json'
RAWS={'train91011':Path('/mnt/d/CodexTransfer/projects/predictive_motion/phase5/raw/servo-identification-v1-training/raw.csv'),'seen91013':Path('/mnt/d/CodexTransfer/projects/predictive_motion/phase5/raw/public-coupled-v2-development-validation-91013/raw.csv')}
HASHES={'train91011':'ab9d14efa1a5886c0683db25345f24d5cacd55343e2768eb60536fa180a11dce','seen91013':'ea70d9e8b01bc6e44387e2f4701779243bb1b202020a61aef18312fac1c054e8'}
STARTS={'train91011':[100,500,1250,2400,2500],'seen91013':[100,500,690,920,2400,2500]}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):Path(p).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def vals(row,p):return [float(row[p+str(j)]) for j in range(7)]
def rows():
 result={}
 for name,p in RAWS.items():
  assert sha(p)==HASHES[name]
  with p.open() as f:result[name]=list(csv.DictReader(f))
 return result
def oracle(case):
 """Exact rational closed form per cell, binary input floats as exact rationals."""
 z=case['state'];C=list(map(F,z['C']));w=list(map(F,z['w']));s=F(z['s']);r=F(z['r']);d=F(1,250);points=[];elapsed=F(0)
 for ci,cell in enumerate(case['cells']):
  a=list(map(F,cell['alpha']));b=F(cell['b']);m=cell['cycles']
  for k in range(1,m+1):
   ck=[C[j]+k*d*w[j]+d*d*k*(k+1)*a[j]/2 for j in range(7)];wk=[w[j]+k*d*a[j] for j in range(7)]
   for h in (1,2):
    t=(k-1+F(h,2))*d
    points.append(dict(cell=ci,cycle=k,half=h,elapsed_s=float(elapsed+t),C=list(map(float,ck)),w=list(map(float,wk)),s_reference=float(s+t*r+t*t*b/2),r_reference=float(r+t*b)))
  C=[C[j]+m*d*w[j]+d*d*m*(m+1)*a[j]/2 for j in range(7)];w=[w[j]+m*d*a[j] for j in range(7)];s,r=s+m*d*r+(m*d)**2*b/2,r+m*d*b;elapsed+=m*d
 return points
def prepare():
 inp=OUT/'inputs';inp.mkdir(exist_ok=False);data=rows();cases=[];incomplete=[]
 for name,starts in STARTS.items():
  for tick in starts:
   idx=next(i for i,x in enumerate(data[name]) if int(x['tick'])==tick and int(x['substep'])==1)
   for cycles in (1,10,200):
    label=f'{name}_tick{tick}_cycles{cycles}'
    if idx+cycles*2>len(data[name]):incomplete.append(dict(name=label,requested_cycles=cycles,available_cycles=(len(data[name])-idx)//2));continue
    first=data[name][idx];prev=data[name][idx-1]
    cases.append(dict(name=label,state=dict(q=vals(first,'q_before_'),v=vals(first,'v_before_'),C=vals(prev,'target_'),w=vals(prev,'command_velocity_'),s=.2,r=.03),cells=[dict(cycles=1,alpha=vals(data[name][idx+2*k],'command_acceleration_'),b=0.) for k in range(cycles)],expect_success=True,dataset=name,index=idx))
 q=vals(data['train91011'][1000],'q_before_');v=vals(data['train91011'][1000],'v_before_');sign=[1,-1,1,-1,1,-1,1]
 state=dict(q=q,v=v,C=[x+2e-4 for x in q],w=[x+1e-4 for x in v],s=.2,r=.08)
 def pos(name,cells,z=state):cases.append(dict(name=name,state=copy.deepcopy(z),cells=cells,expect_success=True))
 pos('nonuniform_mixed',[dict(cycles=m,alpha=[a*x for x in sign],b=b) for m,a,b in [(1,.07,.03),(10,-.04,-.01),(3,.02,.02),(2,0.,0.)]])
 pos('held10',[dict(cycles=10,alpha=[.01*x for x in sign],b=.02)])
 pos('split10',[dict(cycles=1,alpha=[.01*x for x in sign],b=.02) for _ in range(10)])
 pos('negative_b',[dict(cycles=10,alpha=[0.]*7,b=-.1)])
 pos('zero_control',[dict(cycles=3,alpha=[0.]*7,b=0.)])
 positives=copy.deepcopy(cases)
 def neg(name,change,steps=0,ends=0):
  z=dict(name=name,state=copy.deepcopy(state),cells=[dict(cycles=1,alpha=[0.]*7,b=0.)],expect_success=False,expected_steps=steps,expected_cycles=ends);change(z);cases.append(z)
 for key in ('q','v','C','w'):
  neg(key+'_short',lambda z,k=key:z['state'].__setitem__(k,z['state'][k][:6]))
  neg(key+'_nan',lambda z,k=key:z['state'][k].__setitem__(0,'.nan'))
 for key,val in [('s',-.1),('s',1.1),('r',-.01),('r',.21),('s','.inf'),('r','.nan')]:neg(f'{key}_invalid_{val}',lambda z,k=key,x=val:z['state'].__setitem__(k,x))
 neg('C_outside',lambda z:z['state']['C'].__setitem__(0,3.))
 neg('q_boundary',lambda z:z['state']['q'].__setitem__(0,-2.7437))
 neg('w_outside',lambda z:z['state']['w'].__setitem__(0,.063))
 neg('physical_finite_overflow',lambda z:z['state'].__setitem__('v',[1e308]*7))
 for val in (0,-1,.5,True,'1','.nan',5001,10**100):neg('cycles_'+str(val),lambda z,x=val:z['cells'][0].__setitem__('cycles',x))
 neg('empty_mesh',lambda z:z.update(cells=[]))
 neg('too_many_cells',lambda z:z.update(cells=[dict(cycles=1,alpha=[0.]*7,b=0.)]*513))
 neg('total_cycle_cap',lambda z:z.update(cells=[dict(cycles=3000,alpha=[0.]*7,b=0.)]*2))
 neg('alpha_dimension',lambda z:z['cells'][0].update(alpha=[0.]*6))
 neg('alpha_outside',lambda z:z['cells'][0].update(alpha=[1.01]*7))
 neg('alpha_inf',lambda z:z['cells'][0].update(alpha=['.inf']*7))
 neg('b_nan',lambda z:z['cells'][0].update(b='.nan'))
 neg('second_cycle_w_failure',lambda z:(z['state'].update(w=[.060]*7),z.update(cells=[dict(cycles=2,alpha=[.5]*7,b=0.)])),2,1)
 neg('second_cycle_r_failure',lambda z:(z['state'].update(r=.195),z.update(cells=[dict(cycles=2,alpha=[0.]*7,b=1.)])),2,1)
 save(inp/'cases.json',dict(cases=cases,incomplete=incomplete))
 save(inp/'base_cases.json',dict(cases=[dict(name=z['name'],q=z['state']['q'],v=z['state']['v'],targets=[p['C'] for p in oracle(z)],expect_success=True) for z in positives],box_cases=[]))
 save(inp/'empty.json',dict(cases=[]))
 save(inp/'declared_scope.json',dict(starts=STARTS,horizon_cycles=[1,10,200],incomplete=incomplete,positive_cases=len(positives),negative_cases=len(cases)-len(positives),algebra_tolerance=2e-13,paired_base_q_tolerance=1e-12,paired_base_v_tolerance=1e-11,physical_gates={'1cycle':[1e-6,1e-4],'10/200cycles':[1e-4,1e-3]},scope='Fixed numerical component only; previously seen conditional command acceleration from actual accepted history. Virtual progress not recorded plant progress. No new plant, Jacobian, controller, task, accuracy-domain or timing acceptance.'))
def freeze():
 files={Path(x['path']) for x in json.loads(OLD.read_text())['files']};files|={BIN,BASE,OLD,ROOT/'scripts/phase5/verify_public_coupled_augmented_cpp.py'}|set((OUT/'inputs').glob('*'))|set((ROOT/'tools/phase5_public_coupled_augmented_cpp').glob('*'))
 for dep in (ROOT/'build-public-coupled-augmented-cpp-v1').rglob('*.o.d'):
  for token in shlex.split(dep.read_text().replace('\\\n',' '))[1:]:
   p=Path(token);p=p if p.is_absolute() else ROOT/'build-public-coupled-augmented-cpp-v1'/p
   if p.is_file():files.add(p.resolve())
 ldd=subprocess.run(['ldd',str(BIN)],capture_output=True,text=True,check=True).stdout;(OUT/'native_dependencies.txt').write_text(ldd)
 for token in re.findall(r'(/[\w/.+\-]+)',ldd):
  p=Path(token)
  if p.is_file():files.add(p.resolve())
 cache=Path('/mnt/d/CodexTransfer/projects/predictive_motion/phase5/dependency-cache/public-coupled-augmented-cpp-v1');cache.mkdir(exist_ok=False)
 records=[]
 for p in sorted(files):
  assert p.is_file(),str(p);digest=sha(p);dest=cache/digest
  if not dest.exists():dest.write_bytes(p.read_bytes())
  assert sha(dest)==digest;records.append(dict(path=str(p),bytes=p.stat().st_size,sha256=digest,immutable_copy=str(dest)))
 save(OUT/'frozen_before_predictions.json',dict(files=records,base_probe_sha256=sha(BASE),scope='Before all augmented forecasts; metadata-only empty roster preflight allowed; component-only domain.'))
 print('FROZEN',len(records),sha(BIN),sha(OUT/'frozen_before_predictions.json'),flush=True)
def checkfreeze():
 for rec in json.loads((OUT/'frozen_before_predictions.json').read_text())['files']:
  assert sha(rec['path'])==rec['sha256'],'live changed '+rec['path'];assert sha(rec['immutable_copy'])==rec['sha256']
 assert sha(BASE)=='fa1a00344e73d8fe2266541ba4e2b34c362351b30a4f21dfa34c04867f585a04'
def run(binary,inp,out):
 proc=subprocess.run([str(binary),str(XML),str(CONST),str(inp),str(out)],capture_output=True,text=True)
 out.with_suffix('.stdout').write_text(proc.stdout);out.with_suffix('.stderr').write_text(proc.stderr);out.with_suffix('.exit').write_text(str(proc.returncode)+'\n');assert proc.returncode==0
 return json.loads(out.read_text(),parse_constant=lambda x:(_ for _ in ()).throw(ValueError('invalid JSON '+x)))
def need(x,msg):
 if not x:raise ValueError(msg)
def number(x):
 try:ok=type(x) in (int,float) and math.isfinite(x)
 except OverflowError:ok=False
 need(ok,'typed finite native number')
def vector(v):need(type(v) is list and len(v)==7,'dimension7');[number(x) for x in v]
def finite_tree(x):
 if type(x) in (int,float):number(x)
 elif type(x) is list:
  for v in x:finite_tree(v)
 elif type(x) is dict:
  for v in x.values():finite_tree(v)
def state(z):
 need(type(z) is dict,'state map')
 for key in ('q','v','C','w'):vector(z[key])
 for key in ('s','r'):number(z[key])
def validate(out,inputs):
 need(out['model_success'] is True,'model typed true');finite_tree(out)
 need(out['policy']==dict(cycle_dt=.004,substep_dt=.002,max_cells=512,max_each_total_cycles=5000,command_v=.0625,command_a=1,progress_r=.2,progress_s_lower=0,progress_s_upper=1),'exact declared policy')
 need(type(out['cases']) is list and len(out['cases'])==len(inputs['cases']),'exact roster length');names=[x['name'] for x in out['cases']];need(names==[x['name'] for x in inputs['cases']] and len(names)==len(set(names)),'ordered unique roster')
 for case,answer in zip(inputs['cases'],out['cases']):
  need(type(answer['success']) is bool and answer['success']==case['expect_success'],'typed expected case success');need(type(answer['has_final_state']) is bool,'typed final flag')
  if not answer['success']:need(type(answer['error']) is str and bool(answer['error']),'explicit failure error')
  ns=2*sum(x['cycles'] for x in case['cells']) if case['expect_success'] else case['expected_steps'];ne=ns//2
  for key in ('substeps','cycle_end_states','cell_end_states'):need(type(answer[key]) is list,'typed trace arrays')
  need(len(answer['substeps'])==ns and len(answer['cycle_end_states'])==ne,'exact trace and complete cycle roster')
  if answer['success']:need(len(answer['cell_end_states'])==len(case['cells']) and answer['has_final_state'],'complete cells/final')
  if answer['has_final_state']:state(answer['final_state'])
  else:need('final_state' not in answer,'no fabricated final state')
  for end in answer['cycle_end_states']+answer['cell_end_states']:state(end)
  for k,p in enumerate(answer['substeps']):
   for key in ('q','v','C','w'):vector(p[key])
   for key in ('cell','cycle','half','control_clips','force_clips'):need(type(p[key]) is int,'typed native index/clips')
   need(p['half']==k%2+1 and p['control_clips']==0 and 0<=p['force_clips']<=7,'half/control/force policy')
   for key in ('elapsed_s','s_reference','r_reference'):number(p[key])
   box=p['friction'];vector(box['force']);need(type(box['iterations']) is int and 1<=box['iterations']<=100,'QP iterations');need(type(box['branches']) is list and len(box['branches'])==7 and all(type(x) is int and x in (-1,0,1,2) for x in box['branches']),'QP branches');number(box['original_KKT']);need(0<=box['original_KKT']<=1e-10,'original KKT')
   if k%2:need(p['C']==answer['substeps'][k-1]['C'] and p['w']==answer['substeps'][k-1]['w'],'held C/w both halves')
  for k,end in enumerate(answer['cycle_end_states']):
   for key in ('q','v','C','w'):need(end[key]==answer['substeps'][2*k+1][key],'cycle endpoint consistency')
  if ne:need(answer['has_final_state'] and answer['final_state']==answer['cycle_end_states'][-1],'retained final complete cycle')
def gate_controls(out,inputs):
 validate(out,inputs);mutations=[('empty_roster',lambda x:x.update(cases=[])),('drop_tail',lambda x:x['cases'].pop()),('reverse',lambda x:x['cases'].reverse()),('duplicate_name',lambda x:x['cases'][1].update(name=x['cases'][0]['name'])),('string_success',lambda x:x['cases'][0].update(success='true')),('int_success',lambda x:x['cases'][0].update(success=1)),('model_string',lambda x:x.update(model_success='true')),('short_trace',lambda x:x['cases'][0]['substeps'].pop()),('short_cycle',lambda x:x['cases'][0]['cycle_end_states'].pop()),('short_cells',lambda x:x['cases'][0]['cell_end_states'].pop()),('missing_final',lambda x:x['cases'][0].pop('final_state')),('final_bool',lambda x:x['cases'][0].update(has_final_state=1)),('short_q',lambda x:x['cases'][0]['substeps'][0]['q'].pop()),('nan_v',lambda x:x['cases'][0]['substeps'][0]['v'].__setitem__(0,float('nan'))),('string_C',lambda x:x['cases'][0]['substeps'][0]['C'].__setitem__(0,'0')),('bool_w',lambda x:x['cases'][0]['substeps'][0]['w'].__setitem__(0,False)),('huge_s',lambda x:x['cases'][0]['substeps'][0].update(s_reference=10**400)),('wrong_half',lambda x:x['cases'][0]['substeps'][0].update(half=2)),('bad_KKT',lambda x:x['cases'][0]['substeps'][0]['friction'].update(original_KKT=1e-9)),('clip',lambda x:x['cases'][0]['substeps'][0].update(control_clips=1)),('final_mismatch',lambda x:x['cases'][0]['final_state']['q'].__setitem__(0,0.))]
 records=[]
 for name,change in mutations:
  bad=copy.deepcopy(out);change(bad)
  try:validate(bad,inputs)
  except (ValueError,KeyError):records.append(dict(name=name,rejected=True))
  else:raise AssertionError('corrupted output accepted '+name)
 return dict(positive_controls=1,negative_controls=records,scope='Synthetic mutated-output controls only, not actual C++ failures.')
def verify():
 checkfreeze();attempt=OUT/'parity-attempt1';attempt.mkdir(exist_ok=False);inputs=json.loads((OUT/'inputs/cases.json').read_text());aug=run(BIN,OUT/'inputs/cases.json',attempt/'augmented.json');validate(aug,inputs);gates=gate_controls(aug,inputs)
 base=run(BASE,OUT/'inputs/base_cases.json',attempt/'base.json');from validate_public_coupled_native_output_v2 import validate_output
 baseinp=json.loads((OUT/'inputs/base_cases.json').read_text());validate_output(base,baseinp);need(len(base['cases'])==sum(x['expect_success'] for x in inputs['cases']),'paired roster')
 data=rows();records=[];bi=0
 for case,answer in zip(inputs['cases'],aug['cases']):
  rec=dict(name=case['name'],success=answer['success'])
  if not answer['success']:rec.update(error=answer['error'],retained_substeps=len(answer['substeps']),retained_complete_cycles=len(answer['cycle_end_states']));records.append(rec);continue
  ref=oracle(case);paired=base['cases'][bi];bi+=1;need(paired['name']==case['name'],'paired exact name');maxima=dict(command=0.,progress=0.,paired_q=0.,paired_v=0.,physical_q=0.,physical_v=0.)
  for k,(p,r,bp) in enumerate(zip(answer['substeps'],ref,paired['trace'])):
   for key in ('cell','cycle','half'):need(p[key]==r[key],'exact mesh order')
   for key in ('C','w'):maxima['command']=max(maxima['command'],max(abs(x-y) for x,y in zip(p[key],r[key])))
   for key in ('s_reference','r_reference','elapsed_s'):maxima['progress']=max(maxima['progress'],abs(p[key]-r[key]))
   for key in ('q','v'):maxima['paired_'+key]=max(maxima['paired_'+key],max(abs(x-y) for x,y in zip(p[key],bp[key])))
   if 'dataset' in case:
    actual=data[case['dataset']][case['index']+k]
    for key,prefix in [('C','target_'),('w','command_velocity_')]:maxima['command']=max(maxima['command'],max(abs(x-y) for x,y in zip(p[key],vals(actual,prefix))))
    for key in ('q','v'):maxima['physical_'+key]=max(maxima['physical_'+key],max(abs(x-y) for x,y in zip(p[key],vals(actual,key+'_post_'))))
  need(maxima['command']<=2e-13 and maxima['progress']<=2e-13 and maxima['paired_q']<=1e-12 and maxima['paired_v']<=1e-11,'algebra/paired thresholds')
  for k,end in enumerate(answer['cycle_end_states']):need(abs(end['s']-ref[2*k+1]['s_reference'])<=2e-13 and abs(end['r']-ref[2*k+1]['r_reference'])<=2e-13,'cycle progress')
  offset=0
  for j,cell in enumerate(case['cells']):offset+=cell['cycles'];need(answer['cell_end_states'][j]==answer['cycle_end_states'][offset-1],'cell endpoint consistency')
  if 'dataset' in case:
   qg,vg=(1e-6,1e-4) if len(ref)==2 else (1e-4,1e-3);need(maxima['physical_q']<=qg and maxima['physical_v']<=vg,'unchanged recorded regression gates')
  rec.update(maxima=maxima,substeps=len(ref),pass_check=True);records.append(rec)
 checkfreeze();save(attempt/'report.json',dict(status='PASS_BOUNDED_AUGMENTED_COMPONENT_ONLY',phase5='NOT_ACCEPTED',phase6='NOT_STARTED',freeze_sha256=sha(OUT/'frozen_before_predictions.json'),records=records,synthetic_output_gates=gates,incomplete_retained=inputs['incomplete'],forecast_substeps=sum(len(x['substeps']) for x in aug['cases']),scope='Independent rational command/progress and frozen native base physical composition, conditional seen records. Component only, no plant/task/controller/timing acceptance.'))
 print('PASS',len(records),'cases',sum(len(x['substeps']) for x in aug['cases']),'substeps',flush=True)
if __name__=='__main__':globals()[sys.argv[1]]()
