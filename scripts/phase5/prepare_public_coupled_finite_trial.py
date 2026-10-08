#!/usr/bin/env python3
"""Deterministic pre-call finite closed-trial roster; no numerical models."""
import copy,json,hashlib
from pathlib import Path
ROOT=Path('/home/codextransfer/predictive_motion')
OUT=ROOT/'results/phase5/development/public-coupled-finite-trial-cpp-v1'
def prepare():
 root=json.loads((OUT/'roster_dependencies/root_boundary_cases.json').read_text())['cases']
 old=json.loads((ROOT/'results/phase5/development/public-coupled-augmented-extension-cpp-v1/inputs/cases.json').read_text())['cases']
 def source(a):return {k:copy.deepcopy(a[k]) for k in ('state','cells')}
 start=source(root[0]);bound=source(next(x for x in root if x['name']=='root_boundary_initial_w_plusV'))
 cases=[]
 def add(name,nominal,trial,expected=None):
  p=dict(name=name,nominal=copy.deepcopy(nominal),trial=copy.deepcopy(trial),provenance='Prospective finite diagnostic; no new seed or holdout.')
  if expected:p['expected_outcome']=expected
  cases.append(p)
 add('startup_identity',start,start,'sampled_strict_branches_unchanged')
 for ei,e in enumerate((1e-6,3e-7)):
  for field in ('s','r','b'):
   for sign in (-1,1):
    t=copy.deepcopy(start)
    if field=='b':t['cells'][0]['b']+=sign*e
    else:t['state'][field]+=sign*e
    add(f'startup_{field}_e{ei}_sign{sign}',start,t,'forward_failed' if sign<0 else 'sampled_strict_branches_unchanged')
  for key,j,sign in (('q',1,1),('C',1,-1)):
   t=copy.deepcopy(bound);t['state'][key][j]+=sign*e
   add(f'known_w_bound_{key}{j}_e{ei}',bound,t,'sampled_branch_changed' if ei==0 else 'sampled_strict_branches_unchanged')
   cases[-1]['provenance']='Already seen retained root FD counterexample/diagnostic; fixed original steps, no retuning or independent holdout.'
 mesh=source(next(x for x in root if x['name']=='root_boundary_nonuniform_distinct_controls'))
 t=copy.deepcopy(mesh);t['state']['q'][0]+=2e-7;t['state']['w'][0]+=1e-6;t['state']['s']=1e-6;t['state']['r']=1e-6
 for i,c in enumerate(t['cells']):
  c['alpha']=[a+(i+1)*1e-5*(1 if j%2==0 else -1) for j,a in enumerate(c['alpha'])]
  c['b']+=[.001,-.002,.003,.004][i]
 add('distinct_nonuniform_global_chain',mesh,t)
 t=copy.deepcopy(mesh);t['state']['q'][0]+=2e-4;t['state']['w'][0]+=1e-4;t['state']['s']=1e-6;t['state']['r']=1e-6
 for i,c in enumerate(t['cells']):
  c['alpha']=[a+(i+1)*.01*(1 if j%2==0 else -1) for j,a in enumerate(c['alpha'])]
  c['b']+=[.001,-.002,.003,.004][i]
 add('finite_distinct_nonuniform_global_chain',mesh,t)
 t=copy.deepcopy(mesh)
 for c,m in zip(t['cells'],(2,2,3,3)):c['cycles']=m
 add('same_total_different_integer_mesh',mesh,t,'mesh_mismatch')
 t=copy.deepcopy(mesh);t['cells']=[copy.deepcopy(mesh['cells'][0])];t['cells'][0]['cycles']=10
 add('same_total_different_cell_count',mesh,t,'mesh_mismatch')
 for name in ('physical_weak_lower_zero_gradient','physical_joint_force_upper_exact','initial_C_boundary'):
  p=source(next(x for x in old if x['name']==name));add(name+'_both',p,p,'unsupported')
  add(name+'_trial',start,p,'unsupported')
 p=source(next(x for x in old if x['name']=='future_s_failure'))
 nominal=copy.deepcopy(start);nominal['cells'][0]['cycles']=3
 add('future_trial_original_prefix',nominal,p,'forward_failed')
 add('future_nominal_original_prefix',p,nominal,'forward_failed')
 for key,val in (('s',-.01),('r',.201),('w',[.063]*7)):
  t=copy.deepcopy(start);t['state'][key]=val;add('initial_trial_outside_'+key,start,t,'forward_failed')
 t=copy.deepcopy(start);t['cells'][0]['alpha']=[1.01]*7;add('trial_alpha_outside',start,t,'forward_failed')
 t=copy.deepcopy(start);t['cells'][0]['cycles']='1';add('trial_quoted_cycles',start,t,'forward_failed')
 t=copy.deepcopy(start);t['state']['q']=t['state']['q'][:6];add('trial_q_dimension_no_outputs',start,t,'forward_failed')
 t=copy.deepcopy(start);t['state']['v'][0]='.nan';add('trial_nonfinite_no_outputs',start,t,'forward_failed')
 add('nominal_nonfinite_no_maps',t,start,'forward_failed')
 for key,val in [('alpha',[0.]*6),('b','.nan')]:
  t=copy.deepcopy(start);t['cells']=[copy.deepcopy(start['cells'][0]) for _ in range(3)];t['cells'][2][key]=val
  n=copy.deepcopy(start);n['cells']=[copy.deepcopy(start['cells'][0]) for _ in range(3)]
  add('later_invalid_'+key+'_original_global_precheck',n,t,'forward_failed')
 t=copy.deepcopy(start);t['cells'][0]['cycles']=0;add('zero_cycle_topology_only',t,t,'forward_failed')
 t=copy.deepcopy(start);t['cells']=[];add('empty_topology_only',t,t,'forward_failed')
 t=copy.deepcopy(start);t['state']['w']=[.060]*7
 t['cells']=[dict(cycles=1,alpha=[0.]*7,b=0.),dict(cycles=2,alpha=[.5]*7,b=0.)]
 n=copy.deepcopy(start);n['cells']=[dict(cycles=1,alpha=[0.]*7,b=0.),dict(cycles=2,alpha=[0.]*7,b=0.)]
 add('later_generated_command_domain_prefix',n,t,'forward_failed')
 inputs=OUT/'inputs';inputs.mkdir(exist_ok=False)
 (inputs/'cases.json').write_text(json.dumps(dict(cases=cases),indent=2,allow_nan=False)+'\n')
 (inputs/'empty.json').write_text('{"cases":[]}\n')
 declaration=dict(cases=len(cases),explicit_fixed_expected_outcomes={x['name']:x.get('expected_outcome','observe classification from separately verified physical outputs; no required branch verdict') for x in cases},known_epsilon_cases=(1e-6,3e-7),new_plant=False,new_seed=False,no_model_calls_in_prepare=True,nominal_trial_rollouts='Original closed2fa, independent self-propagated physicalq/v; originalf1/e2c unchanged',affine='GLOBAL nominal cell chain; own cell control deviations; no trial-origin reset',source_roster_sha256=hashlib.sha256((OUT/'roster_dependencies/root_boundary_cases.json').read_bytes()).hexdigest(),retained_original_root_gate='FAIL immutable; this finite diagnostic does not replace oldFDgate')
 (inputs/'declared_scope.json').write_text(json.dumps(declaration,indent=2,allow_nan=False)+'\n')
 print(json.dumps(declaration,indent=2))
if __name__=='__main__':prepare()
