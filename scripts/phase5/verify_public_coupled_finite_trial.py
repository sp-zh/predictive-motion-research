#!/usr/bin/env python3
"""Fixed finite-trial diagnostic verification; no residual-quality acceptance."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
import copy,json,shlex,re,subprocess,sys
from pathlib import Path
import numpy as np
import verify_public_coupled_augmented_extension as old
from prepare_public_coupled_finite_trial import prepare
ROOT=old.ROOT;OUT=ROOT/'results/phase5/development/public-coupled-finite-trial-cpp-v1'
BIN=ROOT/'build-public-coupled-finite-trial-cpp-v1/public_coupled_finite_trial_probe'
OLD=old.OUT/'frozen_before_predictions.json'
sha=old.sha;save=old.save;need=old.need;pack=old.pack;point=old.point
CLAIMS=['certifies_connecting_segment','certifies_perturbation_ball','certifies_admissibility','certifies_execution','certifies_safety','certifies_uniform_error_bound','certifies_controller_readiness']
UNITS=['rad','rad/s','rad','rad/s','dimensionless','1/s']
BLOCKS=[('q',0,7),('v',7,7),('C',14,7),('w',21,7),('s',28,1),('r',29,1)]
def close(a,b,msg):
 x=np.asarray(a);y=np.asarray(b);need(x.shape==y.shape and x.dtype.kind in 'fiu' and y.dtype.kind in 'fiu' and np.isfinite(x).all() and np.isfinite(y).all(),msg+' finite shape')
 need(float(np.max(np.abs(x-y)))<=2e-13,msg+' fixed arithmetic tolerance')
def exact(a,b):
 if type(a) is bool or type(b) is bool:return type(a) is bool and type(b) is bool and a is b
 if isinstance(a,dict) and isinstance(b,dict):return a.keys()==b.keys() and all(exact(a[k],b[k]) for k in a)
 if isinstance(a,list) and isinstance(b,list):return len(a)==len(b) and all(exact(x,y) for x,y in zip(a,b))
 if type(a) in (int,float) and type(b) in (int,float):return bool(np.isfinite(float(a)) and np.isfinite(float(b)) and a==b)
 return type(a) is type(b) and a==b
def no_claims(x):
 for key in CLAIMS:need(x.get(key) is False,'typed false '+key)
def numbers(x):
 if isinstance(x,dict):
  for v in x.values():numbers(v)
 elif isinstance(x,list):
  for v in x:numbers(v)
 elif type(x) in (int,float):need(np.isfinite(float(x)),'finite numerical output')
def run(binary,inputs,path):
 save(path.with_name(path.stem+'_inputs.json'),dict(cases=inputs))
 return old.run(binary,path.with_name(path.stem+'_inputs.json'),path)
def freeze():
 files={Path(x['path']) for x in json.loads(OLD.read_text())['files']}
 for x in json.loads(OLD.read_text())['files']:need(sha(x['path'])==x['sha256'],'old extension source unchanged')
 files|={BIN,OLD,Path(__file__),ROOT/'scripts/phase5/prepare_public_coupled_finite_trial.py',OUT/'contract_before_predictions.json'}
 files|=set((OUT/'inputs').glob('*'))|set((OUT/'roster_dependencies').glob('*'))|set((ROOT/'tools/phase5_public_coupled_finite_trial_cpp').glob('*'))
 build=ROOT/'build-public-coupled-finite-trial-cpp-v1'
 files|={OUT/'empty_metadata.json',OUT/'check_finite_trial_metadata_preflight2.py',OUT/'metadata_preflight2.json',OUT/'finite_trial_preflight_failure1.json',OUT/'build_finite_trial_preflight.py',build/'CMakeCache.txt',build/'compile_commands.json',Path('/usr/bin/cmake').resolve(),Path('/usr/bin/c++').resolve()}
 for dep in build.rglob('*.o.d'):
  for token in shlex.split(dep.read_text().replace('\\\n',' '))[1:]:
   p=Path(token);p=p if p.is_absolute() else build/p
   if p.is_file():files.add(p.resolve())
 ldd=subprocess.run(['ldd',str(BIN)],capture_output=True,text=True,check=True).stdout;(OUT/'native_dependencies.txt').write_text(ldd)
 for token in re.findall(r'(/[\w/.+\-]+)',ldd):
  p=Path(token)
  if p.is_file():files.add(p.resolve())
 cache=Path('/mnt/d/CodexTransfer/projects/predictive_motion/phase5/dependency-cache/public-coupled-finite-trial-cpp-v1');cache.mkdir(exist_ok=False);records=[]
 for p in sorted(files):
  digest=sha(p);dest=cache/digest
  if not dest.exists():dest.write_bytes(p.read_bytes())
  need(sha(dest)==digest,'immutable digest');records.append(dict(path=str(p),bytes=p.stat().st_size,sha256=digest,immutable_copy=str(dest)))
 save(OUT/'frozen_before_predictions.json',dict(files=records,scope='Before any finite trial native/reference numeric diagnostics; all source/runtime/input/policy frozen, empty metadata only.'))
 print('FROZEN',len(records),sha(BIN),sha(OUT/'frozen_before_predictions.json'),flush=True)
def checkfreeze():
 for r in json.loads((OUT/'frozen_before_predictions.json').read_text())['files']:need(sha(r['path'])==r['sha256'] and sha(r['immutable_copy'])==r['sha256'],'frozen identity '+r['path'])
 old.checkfreeze();need(sha(old.BIN)=='f1b7e6c7e4219fec2beb310540c725b448dcf021b3a95ddafc2922e8849bf1d6','original f1 unchanged')
def parse_valid(x):
 return isinstance(x.get('state'),dict) and isinstance(x.get('cells'),list) and all(type(c.get('cycles')) is int and c['cycles']>=0 for c in x['cells'])
def signature(d):
 return tuple(tuple((b['enabled'],b['side']) for b in d['diagnostics'][k]) for k in ('control','actuator','joint_force'))+(tuple(d['value']['friction']['branches']),)
def strict(d,C,constants):
 ranges=np.array(constants['control_range']).reshape(7,2);x=np.array(C)
 return bool(d['jacobian_success'] and len(d['diagnostics']['control'])==7 and ((x-ranges[:,0])>1e-8).all() and ((ranges[:,1]-x)>1e-8).all())
def expected_residuals(case,ext,trial):
 if not parse_valid(case['nominal']) or not parse_valid(case['trial']):return []
 if not ext['substep_maps'] or not trial['substeps']:return []
 n=case['nominal'];t=case['trial']
 if len(n['cells'])!=len(t['cells']) or any(a['cycles']!=b['cycles'] for a,b in zip(n['cells'],t['cells'])):return []
 dev=pack(t['state'])-pack(n['state']);results=[];offset=0
 for cell,(nc,tc) in enumerate(zip(n['cells'],t['cells'])):
  if not any(m['cell']==cell for m in ext['substep_maps']) or not any(p['cell']==cell for p in trial['substeps']):break
  du=np.r_[np.array(tc['alpha'])-np.array(nc['alpha']),tc['b']-nc['b']]
  for kind,key in [('substep','substep_maps'),('cycle','cycle_maps'),('cell','cell_maps')]:
   for m in ext[key]:
    if m['cell']!=cell:continue
    actual=None
    if kind=='substep':
     p=next((x for x in trial['substeps'] if (x['cell'],x['cycle'],x['half'])==(m['cell'],m['cycle'],m['half'])),None)
     if p is not None:actual=point(p)
    elif kind=='cycle':
     index=offset+m['cycle']-1
     if index<len(trial['cycle_end_states']):actual=trial['cycle_end_states'][index]
    elif cell<len(trial['cell_end_states']):actual=trial['cell_end_states'][cell]
    if actual is None:continue
    A=np.asarray(m['A'] if kind=='cell' else m['cell_A']);B=np.asarray(m['B'] if kind=='cell' else m['cell_B'])
    linear=A@dev+B@du;prediction=pack(m['state'])+linear;residual=pack(actual)-prediction
    results.append(dict(endpoint=kind,cell=m['cell'],cycle=m['cycle'],half=m['half'],nominal_state=m['state'],trial_state=actual,nominal_cell_origin=m.get('cell_origin',m['origin']),cell_origin_deviation=dev,input_deviation=du,linear_deviation=linear,prediction=prediction,residual=residual))
  end=next((m for m in ext['cell_maps'] if m['cell']==cell),None)
  if end is None:break
  dev=np.asarray(end['A'])@dev+np.asarray(end['B'])@du;offset+=nc['cycles']
 return results
def validate(out,inp,values,extensions,physical,constants):
 need(out['model_success'] is True and len(out['cases'])==len(inp['cases']),'complete native output')
 need([x['name'] for x in out['cases']]==[x['name'] for x in inp['cases']],'fixed case identity/order');numbers(out)
 need(out['policy']['name']=='FINITE_CLOSED_TRIAL_SAMPLED_BRANCH_DIAGNOSTIC_V1' and out['policy']['mesh']=='same cell count and exact cycles per cell; topology equality only; original closed forward checks validity','distinct policy')
 need('GLOBAL' in out['policy']['affine'] and 'GLOBAL' in out['domain_scope'],'explicit GLOBAL scope');no_claims(out['policy'])
 summaries=[]
 for case,a in zip(inp['cases'],out['cases']):
  name=case['name'];no_claims(a);need(a['outcome']!='diagnostic_error' and 'error' not in a and 'affine_error' not in a,'no infrastructure error')
  n=values[name+'_nominal'];t=values[name+'_trial'];ext=extensions[name]
  need(exact(a['nominal'],{k:v for k,v in ext.items() if k!='name'}),'exact unchanged original f1 maps/closed nominal')
  need(exact(a['trial'],{k:v for k,v in t.items() if k!='name'}),'exact original2fa trial')
  need(exact(a['nominal']['value'],{k:v for k,v in n.items() if k!='name'}),'exact original2fa nominal')
  parse_ok=parse_valid(case['nominal']) and parse_valid(case['trial'])
  mesh=parse_ok and len(case['nominal']['cells'])==len(case['trial']['cells']) and all(x['cycles']==y['cycles'] for x,y in zip(case['nominal']['cells'],case['trial']['cells']))
  need(type(a['mesh_matches']) is bool and a['mesh_matches']==mesh,'exact integer mesh flag')
  allstrict=True;side_data=[]
  for side,value in [('nominal',n),('trial',t)]:
   inspections=a[side+'_inspections'];need(len(inspections)==len(value['substeps']),'actual produced points only');q=case[side]['state']['q'];v=case[side]['state']['v'];diagnostics=[]
   for index,(p,i) in enumerate(zip(value['substeps'],inspections)):
    d=physical[f'{name}_{side}_p{index}'];no_claims(i)
    need((i['cell'],i['cycle'],i['half'],i['elapsed_s'])==(p['cell'],p['cycle'],p['half'],p['elapsed_s']),'exact step timestamps')
    need(i['q_before']==q and i['v_before']==v and i['C']==p['C'],'own nonlinear input no teacher forcing')
    need(i['exact_value_parity'] is True and i['value_success'] is d['value_success'],'exact physical parity flags')
    need(i['jacobian_success'] is d['jacobian_success'],'original strict support')
    value_subset={k:d['value'][k] for k in ('q','v','control_clips','force_clips','friction')};need(exact(i['physical_value'],value_subset),'exact physical value metadata')
    need(i['signature_complete'] is True,'full per-joint signatures complete')
    for key in ('control','actuator','joint_force','solve_conditions','solve_residuals'):
     need(exact(i[key],d['diagnostics'][key]),'exact original per-axis '+key)
    for key in ('friction_gradient','friction_margin'):need(i[key]==d['diagnostics'].get(key,[]),'exact '+key)
    if d['jacobian_success']:need(i['jacobian']==d['jacobian'],'exact physical Jacobian')
    else:need('jacobian' not in i and i.get('error')==d['error'],'unsupported no fabricated Jacobian')
    ranges=np.asarray(constants['control_range']).reshape(7,2);C=np.array(p['C'])
    Cstrict=bool(((C-ranges[:,0])>1e-8).all() and ((ranges[:,1]-C)>1e-8).all())
    need(i['strict_C'] is Cstrict,'unchanged strict C support')
    diagnostics.append(d);allstrict=allstrict and strict(d,p['C'],constants);q=p['q'];v=p['v']
   side_data.append(diagnostics)
  complete=bool(n['success'] and t['success']);allstrict=bool(complete and side_data[0] and len(side_data[0])==len(side_data[1]) and allstrict)
  need(a['all_forward_complete'] is complete and a['all_sampled_strict'] is allstrict,'full complete/strict flags')
  pairs=min(len(side_data[0]),len(side_data[1])) if mesh else 0;need(len(a['comparisons'])==pairs,'common actual timestamps only')
  changed=False;equal=bool(mesh and complete and side_data[0] and len(side_data[0])==len(side_data[1]))
  for index,c in enumerate(a['comparisons']):
   no_claims(c);x,y=side_data[0][index],side_data[1][index];p=n['substeps'][index];s=t['substeps'][index]
   need((c['cell'],c['cycle'],c['half'],c['elapsed_s'])==(p['cell'],p['cycle'],p['half'],p['elapsed_s']),'comparison timestamp')
   eq=signature(x)==signature(y);need(c['branches_equal'] is eq and c['signatures_available'] is True,'full branch comparison');changed=changed or not eq;equal=equal and eq
   need(c['nominal_strict'] is strict(x,p['C'],constants) and c['trial_strict'] is strict(y,s['C'],constants),'per-point original strict support')
  need(a['sampled_branch_change'] is bool(changed) and a['all_sampled_signatures_equal'] is bool(equal),'partial/full branch flags')
  outcome='forward_failed' if not parse_ok else 'mesh_mismatch' if not mesh else 'forward_failed' if not complete else 'unsupported' if not allstrict or not ext['extension_jacobian_success'] else 'sampled_branch_changed' if changed else 'sampled_strict_branches_unchanged'
  need(a['outcome']==outcome,'independently reconstructed outcome')
  if 'expected_outcome' in case:need(outcome==case['expected_outcome'],'fixed predeclared known outcome '+name)
  expected=expected_residuals(case,ext,t);need(len(expected)==len(a['residuals']),'all available certified nominal-prefix residuals')
  maxima={key:0. for key,_,_ in BLOCKS}
  for got,ref in zip(a['residuals'],expected):
   no_claims(got)
   for key in ('endpoint','cell','cycle','half','nominal_state','trial_state','nominal_cell_origin'):need(got[key]==ref[key],'literal nominal/trial own origins '+key)
   for key in ('cell_origin_deviation','input_deviation','linear_deviation','prediction','residual'):close(got[key],ref[key],'GLOBAL independently composed '+key)
   for j,(key,index,count) in enumerate(BLOCKS):
    b=got['block_residuals'][key];maximum=float(np.max(np.abs(np.array(got['residual'])[index:index+count])))
    need(b['units']==UNITS[j] and type(b['max_absolute']) in (float,int),'residual block SI')
    close([b['max_absolute']],[maximum],'exact reported block maximum');maxima[key]=max(maxima[key],maximum)
  summaries.append(dict(name=name,outcome=outcome,nominal_actual_steps=len(n['substeps']),trial_actual_steps=len(t['substeps']),paired_actual_steps=pairs,residual_endpoints=len(expected),max_global_affine_residual_by_block=maxima,no_residual_quality_acceptance=True))
 return summaries
def teacher_forced_global_control(out):
 case=next(x for x in out['cases'] if x['name']=='finite_distinct_nonuniform_global_chain')
 got=next(x for x in case['residuals'] if x['endpoint']=='substep' and x['cell']==1)
 map_=next(x for x in case['nominal']['substep_maps'] if (x['cell'],x['cycle'],x['half'])==(got['cell'],got['cycle'],got['half']))
 wrong=pack(case['trial']['cell_end_states'][0])-pack(map_['cell_origin'])
 linear=np.asarray(map_['cell_A'])@wrong+np.asarray(map_['cell_B'])@np.asarray(got['input_deviation'])
 prediction=pack(got['nominal_state'])+linear;residual=pack(got['trial_state'])-prediction
 for key,value in [('cell_origin_deviation',wrong),('linear_deviation',linear),('prediction',prediction),('residual',residual)]:got[key]=value.tolist()
 for key,index,count in BLOCKS:got['block_residuals'][key]['max_absolute']=float(np.max(np.abs(residual[index:index+count])))
def verify():
 checkfreeze();attempt=OUT/'parity-attempt1';attempt.mkdir(exist_ok=False);inp=json.loads((OUT/'inputs/cases.json').read_text())
 native=old.run(BIN,OUT/'inputs/cases.json',attempt/'native.json')
 flat=[];nom=[]
 for case in inp['cases']:
  for side in ('nominal','trial'):flat.append(dict(name=case['name']+'_'+side,**case[side]))
  nom.append(dict(name=case['name'],**case['nominal']))
 refs=run(old.VALUE,flat,attempt/'original_closed_values');ext=run(old.BIN,nom,attempt/'original_nominal_extension')
 values={x['name']:x for x in refs['cases']};extensions={x['name']:x for x in ext['cases']}
 physical_inputs=[]
 for case in inp['cases']:
  for side in ('nominal','trial'):
   q=case[side]['state']['q'];v=case[side]['state']['v']
   for j,p in enumerate(values[case['name']+'_'+side]['substeps']):
    physical_inputs.append(dict(name=f'{case["name"]}_{side}_p{j}',q=q,v=v,C=p['C']))
    q=p['q'];v=p['v']
 physical={}
 for offset in range(0,len(physical_inputs),96):
  out=run(old.PHYS,physical_inputs[offset:offset+96],attempt/f'original_physical_{offset//96:03d}')
  for x in out['cases']:physical[x['name']]=x
 constants=json.loads(old.CONST.read_text());records=validate(native,inp,values,extensions,physical,constants)
 controls=[
  ('actual_origin_reset_mislabeled_GLOBAL',teacher_forced_global_control),
  ('drop_case',lambda x:x['cases'].pop()),
  ('wrong_order',lambda x:x['cases'].reverse()),
  ('false_safety_certificate',lambda x:x['cases'][0].update(certifies_safety=True)),
  ('flag_as_integer',lambda x:x['cases'][0].update(all_forward_complete=1)),
  ('per_joint_enabled_as_int',lambda x:x['cases'][0]['trial_inspections'][0]['control'][0].update(enabled=1)),
  ('wrong_per_joint_branch',lambda x:x['cases'][0]['trial_inspections'][0]['joint_force'][0].update(side=1)),
  ('missing_per_joint_branch',lambda x:x['cases'][0]['trial_inspections'][0]['control'].pop()),
  ('fabricated_future_point',lambda x:x['cases'][-1]['trial_inspections'].append(copy.deepcopy(x['cases'][0]['trial_inspections'][0]))),
  ('wrong_global_prediction',lambda x:x['cases'][0]['residuals'][0]['prediction'].__setitem__(0,x['cases'][0]['residuals'][0]['prediction'][0]+.001)),
  ('wrong_units',lambda x:x['cases'][0]['residuals'][0]['block_residuals']['q'].update(units='m')),
  ('fake_branch_unchanged',lambda x:next(c for c in x['cases'] if c['name']=='known_w_bound_q1_e0').update(outcome='sampled_strict_branches_unchanged')),
  ('same_duration_mesh_equal',lambda x:next(c for c in x['cases'] if c['name']=='same_total_different_integer_mesh').update(mesh_matches=True)),
  ('nan_residual',lambda x:x['cases'][0]['residuals'][0]['residual'].__setitem__(0,float('nan'))),
 ]
 negative=[]
 for name,change in controls:
  bad=copy.deepcopy(native);change(bad)
  try:validate(bad,inp,values,extensions,physical,constants)
  except (ValueError,KeyError):negative.append(dict(name=name,rejected=True))
  else:raise AssertionError('synthetic output accepted '+name)
 checkfreeze()
 report=dict(status='PASS_FIXED_FINITE_SAMPLED_TRIAL_DIAGNOSTICS_ONLY',phase5='NOT_ACCEPTED',phase6='NOT_STARTED',records=records,fixed_cases=len(inp['cases']),original_closed_rollouts=len(flat),original_nominal_extension_rollouts=len(nom),original_physical_diagnostics=len(physical_inputs),synthetic_output_controls=dict(positive=1,negative=negative),freeze_sha256=sha(OUT/'frozen_before_predictions.json'),binary_sha256=sha(BIN),retained_root_FD_gate='FAIL unchanged',global_residuals='Reported per-block finite arithmetic only; no smallness/pass threshold, uniform bound or controller admission',no_claims=CLAIMS)
 save(attempt/'report.json',report);print(json.dumps(report,indent=2),flush=True)
if __name__=='__main__':globals()[sys.argv[1]]()
