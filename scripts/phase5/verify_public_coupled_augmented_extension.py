#!/usr/bin/env python3
"""Composite Jacobians induced by command/progress extension; not admissibility."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
import json,hashlib,copy,math,subprocess,sys,re,shlex
from pathlib import Path
import numpy as np
import verify_public_coupled_augmented_sensitivity as prior
from verify_public_coupled_augmented_cpp import oracle,validate as value_validate
from verify_public_coupled_derivative_cpp import validate as derivative_validate,branch
from validate_public_coupled_native_output_v2 import validate_output
ROOT=prior.ROOT;OUT=ROOT/'results/phase5/development/public-coupled-augmented-extension-cpp-v1';BIN=ROOT/'build-public-coupled-augmented-extension-cpp-v1/public_coupled_augmented_extension_probe';VALUE=prior.BASE;PHYS=prior.PHYS;DIAG=prior.DIAG;INTERIOR=prior.BIN;OLD=prior.OUT/'frozen_before_predictions.json';XML=prior.XML;CONST=prior.CONST
CERT='COMMAND_PROGRESS_EXTENSION_JACOBIAN_STRICT_PHYSICAL_V1';EPS=prior.EPS;ABS=prior.ABS;REL=prior.REL;BATCH=96
sha=prior.sha;save=prior.save;need=prior.need;pack=prior.pack;unpack=prior.unpack;point=prior.point;close=prior.close;compare=prior.compare

def prepare():
 p=OUT/'inputs';p.mkdir(exist_ok=False);old=json.loads((prior.OUT/'inputs/cases.json').read_text());oldcases=old['cases'];z=copy.deepcopy(oldcases[0]['state']);z['w']=[0.]*7;sign=np.array([1,-1,1,-1,1,-1,1]);cases=[]
 def cell(m=1,a=0.,b=0.):return dict(cycles=m,alpha=(sign*a).tolist(),b=b)
 def add(name,cells,state=z,cert=True,value=True,sub=0,cy=0,ce=0,steps=0):
  a=dict(name=name,state=copy.deepcopy(state),cells=copy.deepcopy(cells),expect_success=value,expected_value=value,expected_sensitivity=cert)
  if not cert:a.update(expected_maps=sub,expected_cycle_maps=cy,expected_cell_maps=ce)
  if not value:a.update(expected_steps=steps,expected_cycles=steps//2)
  cases.append(a);return a
 start=copy.deepcopy(z);start.update(s=0.,r=0.);add('start_s0_r0_zero',[cell()],start);add('start_s0_r0_progress10',[cell(10,.001,.01)],start)
 st=copy.deepcopy(z);st.update(s=1.,r=0.);add('terminal_s1_r0',[cell()],st)
 st=copy.deepcopy(z);st['r']=.2;add('initial_r_upper',[cell()],st)
 st=copy.deepcopy(z);st['s']=0.;add('initial_s_lower',[cell()],st)
 st=copy.deepcopy(z);st['r']=0.;add('initial_r_lower',[cell(1,.003,0.)],st)
 sat=copy.deepcopy(z);sat['C']=(np.array(z['q'])+.1*sign).tolist()
 for side in (1,-1):
  st=copy.deepcopy(sat);st['w']=[side*.0625]*7;add('initial_w_'+('upper' if side==1 else 'lower'),[cell()],st)
 for side in (1,-1):add('alpha_'+('upper' if side==1 else 'lower'),[dict(cycles=1,alpha=[float(side)]*7,b=0.)],sat)
 st=copy.deepcopy(sat);st['w']=[.0625]*7;add('initial_w_upper_inward',[dict(cycles=1,alpha=[-.5]*7,b=0.)],st)
 st=copy.deepcopy(sat);st['w']=[.0605]*7;add('generated_w_upper',[dict(cycles=1,alpha=[.5]*7,b=0.)],st)
 st=copy.deepcopy(z);st['s']=1.-.004*.08;add('generated_s_upper',[cell()],st)
 st=copy.deepcopy(z);st['r']=.2-.004*.01;add('generated_r_upper',[cell(1,0.,.01)],st)
 add('nonuniform_start_s0_r0',[cell(m,a,b) for m,a,b in [(1,.003,.01),(3,-.002,.01),(2,.001,.02),(4,0.,0.)]],start)
 seen=next(x for x in oldcases if x['name']=='seen91013_actual_history_cycle1');st=copy.deepcopy(seen['state']);st.update(s=0.,r=0.);add('seen91013_actual_history_start',[dict(cycles=1,alpha=seen['cells'][0]['alpha'],b=.01)],st)
 interior=next(x for x in oldcases if x['name']=='nonuniform_mixed');add('interior_old_api_reference',interior['cells'],interior['state'])
 oldp=json.loads((ROOT/'results/phase5/development/public-coupled-derivative-cpp-v1/inputs/cases.json').read_text())['cases']
 for name in ('weak_lower_zero_gradient','joint_force_upper_exact'):
  a=next(x for x in oldp if x['name']==name);st=copy.deepcopy(z);st.update(q=a['q'],v=a['v'],C=a['C']);add('physical_'+name,[cell()],st,False)
 c=json.loads(CONST.read_text());st=copy.deepcopy(z);st['C'][0]=c['control_range'][0];add('initial_C_boundary',[cell()],st,False)
 for name,change in [('q_dimension',lambda x:x['state'].update(q=z['q'][:6])),('mesh_quoted',lambda x:x['cells'][0].update(cycles='1')),('alpha_outside',lambda x:x['cells'][0].update(alpha=[1.01]*7)),('w_outside',lambda x:x['state'].update(w=[.063]*7)),('s_outside',lambda x:x['state'].update(s=-.01)),('r_outside',lambda x:x['state'].update(r=.201))]:
  a=add(name,[cell()],cert=False,value=False);change(a)
 st=copy.deepcopy(z);st['w']=[.060]*7;add('future_w_failure',[dict(cycles=2,alpha=[.5]*7,b=0.)],st,False,False,sub=2,cy=1,steps=2)
 st=copy.deepcopy(z);st['s']=1.-.004*.08*2.5;add('future_s_failure',[cell(3)],st,False,False,sub=4,cy=2,steps=4)
 save(p/'cases.json',dict(cases=cases));save(p/'empty.json',dict(cases=[]));fd=[]
 for a in cases[:17]:
  base=copy.deepcopy(a);base['extension_probe_only']=True;fd.append(base)
  for ei,e in enumerate(EPS):
   for j in range(38):
    for sg in (-1,1):
     x=copy.deepcopy(base);x['name']=f'{a["name"]}_e{ei}_col{j}_sign{sg}'
     if j<30:v=pack(x['state']);v[j]+=sg*e;x['state']=unpack(v)
     else:
      for ce in x['cells']:
       if j<37:ce['alpha'][j-30]+=sg*e
       else:ce['b']+=sg*e
     fd.append(x)
 manifests=[]
 for i in range(0,len(fd),BATCH):
  file=p/f'extension_fd_batch{i//BATCH:03d}.json';save(file,dict(cases=fd[i:i+BATCH],scope='Mathematical command/progress extension probes only, never admissible forward inputs.'));manifests.append(dict(path=str(file),sha256=sha(file),count=min(BATCH,len(fd)-i)))
 save(p/'extension_fd_batches.json',manifests)
 # Deterministic comparison inputs, not physical forecasts: exact rational
 # command/progress polynomials from the predeclared FD coefficients only.
 valueinputs=[];exteriorflags={}
 for x in fd:
  ref=oracle(x);valueinputs.append(dict(name=x['name'],q=x['state']['q'],v=x['state']['v'],targets=[r['C'] for r in ref],expect_success=True,extension_probe_only=True));exteriorflags[x['name']]=exterior(x,ref)
 vm=[]
 for i in range(0,len(valueinputs),BATCH):
  file=p/f'extension_value_input_batch{i//BATCH:03d}.json';save(file,dict(cases=valueinputs[i:i+BATCH],box_cases=[]));vm.append(dict(path=str(file),sha256=sha(file),count=min(BATCH,len(valueinputs)-i)))
 save(p/'extension_value_inputs_manifest.json',vm);save(p/'extension_exterior_flags_before_predictions.json',dict(scope='Mathematical extension labels at input-polynomial nodes; no admissibility claim or physical prediction.',records=exteriorflags))
 save(p/'interior_reference.json',dict(cases=[cases[16]]));save(p/'declared_scope.json',dict(certificate=CERT,nominal_cases=len(cases),prospective_certified=17,known_valid_unsupported=3,invalid=6,future_failures=2,extension_oracle_cases=len(fd),batch_cap=BATCH,epsilons=EPS,absolute_per_entry=ABS,relative_per_entry=REL,structural=2e-13,nominal_q_tolerance=1e-12,nominal_v_tolerance=1e-11,nominal_command_progress_tolerance=2e-13,previous_cases_sha256=sha(prior.OUT/'inputs/cases.json'),control_semantics='All38 producer directions: multi-cell alpha/b directions shared across cells; root tests distinct62coordinates.',extension_oracle='Exact rational command/progress, originalfa1 physical q/v self-rollout at held targets. Exterior w/alpha/s/r are mathematical probes only; no old2fa/newAPI exterior-forward call, projection or epsilon-shifted actual history.',derivative_meaning='Composite nonlinear map induced by smooth command/progress extension; full physical map not polynomial. No admissible neighborhood, direction, safety/accuracy/timing/main controller or Phase5 acceptance.'))
 print('PREPARED',len(cases),'nominals',len(fd),'extension oracles',len(manifests),'batches',flush=True)

def freeze():
 old=json.loads(OLD.read_text());files={Path(x['path']) for x in old['files']}
 for x in old['files']:need(sha(x['path'])==x['sha256'],'prior source changed')
 files|={BIN,VALUE,PHYS,DIAG,INTERIOR,OLD,Path(__file__),OUT/'contract_before_predictions.json'}|set((OUT/'inputs').glob('*'))|set((ROOT/'tools/phase5_public_coupled_augmented_extension_cpp').glob('*'))
 for dep in (ROOT/'build-public-coupled-augmented-extension-cpp-v1').rglob('*.o.d'):
  for token in shlex.split(dep.read_text().replace('\\\n',' '))[1:]:
   p=Path(token);p=p if p.is_absolute() else ROOT/'build-public-coupled-augmented-extension-cpp-v1'/p
   if p.is_file():files.add(p.resolve())
 ldd=subprocess.run(['ldd',str(BIN)],capture_output=True,text=True,check=True).stdout;(OUT/'native_dependencies.txt').write_text(ldd)
 for token in re.findall(r'(/[\w/.+\-]+)',ldd):
  p=Path(token)
  if p.is_file():files.add(p.resolve())
 cache=Path('/mnt/d/CodexTransfer/projects/predictive_motion/phase5/dependency-cache/public-coupled-augmented-extension-cpp-v1');cache.mkdir(exist_ok=False);records=[]
 for p in sorted(files):
  need(p.is_file(),'frozen file exists');digest=sha(p);dest=cache/digest
  if not dest.exists():dest.write_bytes(p.read_bytes())
  need(sha(dest)==digest,'immutable digest');records.append(dict(path=str(p),bytes=p.stat().st_size,sha256=digest,immutable_copy=str(dest)))
 save(OUT/'frozen_before_predictions.json',dict(files=records,scope='Before any new extension-native/extensionoracle predictions; original values/source/SDK/harness/contract/allinputs frozen; empty metadata preflight only.'));print('FROZEN',len(records),sha(BIN),sha(OUT/'frozen_before_predictions.json'),flush=True)
def checkfreeze():
 for r in json.loads((OUT/'frozen_before_predictions.json').read_text())['files']:need(sha(r['path'])==r['sha256'] and sha(r['immutable_copy'])==r['sha256'],'frozen live/cache changed '+r['path'])
 need(sha(INTERIOR)=='a29ccdb1b6bdc82ca16e8743d892f7801d15fd778c421d319e49052e6d571d54','interior original binary unchanged');need(sha(VALUE)=='2fa952127cdd37ceb56396231e2972d50d36c94e9a19c341c9c17169442acf57' and sha(PHYS)=='e2c75c09001ba354ca5371cbfc594a9765c62098d4cdb52e6a1442adc055c6a4' and sha(DIAG)=='fa1a00344e73d8fe2266541ba4e2b34c362351b30a4f21dfa34c04867f585a04','all original probes preserved')
def run(binary,inp,out):return prior.run(binary,inp,out)
def boundaries(z,u):return dict(w=[-1 if x==-.0625 else 1 if x==.0625 else 0 for x in z['w']],alpha=[-1 if x==-1 else 1 if x==1 else 0 for x in u[:7]],s=-1 if z['s']==0 else 1 if z['s']==1 else 0,r=-1 if z['r']==0 else 1 if z['r']==.2 else 0)
def normalized(out):
 x=copy.deepcopy(out);x['policy']=dict(cycle_dt=.004,substep_dt=.002,rows=30,state_columns=30,input_columns=8,domain_margin=1e-8,max_cells=512,max_each_total_cycles=5000)
 for a in x['cases']:a['sensitivity_success']=a.pop('extension_jacobian_success')
 return x

def validate(out,inp):
 need(out['policy']==dict(cycle_dt=.004,substep_dt=.002,rows=30,state_columns=30,input_columns=8,control_margin=1e-8,certificate_name=CERT,certifies_two_sided_admissible_neighborhood=False,nominal_domain='original closed w/alpha/s/r; unchanged strict physical C',max_cells=512,max_each_total_cycles=5000),'exact extension policy')
 need(out['policy']['certifies_two_sided_admissible_neighborhood'] is False,'typed no admissibility claim');need('full physical map is nonlinear' in out['domain_scope'],'explicit nonlinear composite scope');prior.validate(normalized(out),inp)
 for a in out['cases']:
  need('sensitivity_success' not in a and a['certifies_two_sided_admissible_neighborhood'] is False,'distinct extension field/no admissibilityclaim')
  if a['extension_jacobian_success']:need(a.get('certificate_name')==CERT,'named fullcertificate')
  else:need('certificate_name' not in a,'no fabricated fullcertificate')
  for key in ('substep_maps','cycle_maps','cell_maps'):
   for m in a[key]:
    need(m['certificate_name']==CERT and m['certifies_two_sided_admissible_neighborhood'] is False,'named prefixextension-only certificate');need(m['origin_boundary']==boundaries(m['origin'],m['input']) and m['endpoint_boundary']==boundaries(m['state'],m['input']),'exact diagnostic boundaryflags')
    for z in (m['origin_boundary'],m['endpoint_boundary']):
     for key_ in ('w','alpha'):need(type(z[key_]) is list and len(z[key_])==7 and all(type(v) is int and v in (-1,0,1) for v in z[key_]),'typed boundaryflags')
     for key_ in ('s','r'):need(type(z[key_]) is int and z[key_] in (-1,0,1),'typed progressboundary')

def gates(out,inp):
 validate(out,inp);unsupported=next(i for i,x in enumerate(inp['cases']) if not x['expected_sensitivity']);mutations=[('empty',lambda x:x.update(cases=[])),('drop',lambda x:x['cases'].pop()),('reorder',lambda x:x['cases'].reverse()),('duplicate',lambda x:x['cases'][1].update(name=x['cases'][0]['name'])),('flagstring',lambda x:x['cases'][0].update(extension_jacobian_success='true')),('flagint',lambda x:x['cases'][0].update(extension_jacobian_success=1)),('wrongcertificate',lambda x:x['cases'][0].update(certificate_name='ADMISSIBLE_DOMAIN')),('missingcertificate',lambda x:x['cases'][0].pop('certificate_name')),('case_admissibilityclaim',lambda x:x['cases'][0].update(certifies_two_sided_admissible_neighborhood=True)),('map_admissibilityclaim',lambda x:x['cases'][0]['substep_maps'][0].update(certifies_two_sided_admissible_neighborhood=True)),('policy_admissibilityclaim',lambda x:x['policy'].update(certifies_two_sided_admissible_neighborhood=True)),('wrongprefixcertificate',lambda x:x['cases'][0]['cycle_maps'][0].update(certificate_name='CENTRAL_ADMISSIBLE')),('falsestartboundary',lambda x:x['cases'][0]['cell_maps'][0]['origin_boundary'].update(s=0)),('boundarybool',lambda x:x['cases'][0]['substep_maps'][0]['origin_boundary'].update(r=False)),('missingprefixboundary',lambda x:x['cases'][0]['cycle_maps'][0].pop('endpoint_boundary')),('Arow',lambda x:x['cases'][0]['substep_maps'][0]['A'].pop()),('Bcol',lambda x:x['cases'][0]['cell_maps'][0]['B'][0].pop()),('nan',lambda x:x['cases'][0]['substep_maps'][0]['A'][0].__setitem__(0,float('nan'))),('boolmatrix',lambda x:x['cases'][0]['substep_maps'][0]['A'][0].__setitem__(0,False)),('huge',lambda x:x['cases'][0]['substep_maps'][0]['A'][0].__setitem__(0,10**400)),('shortdefect',lambda x:x['cases'][0]['cell_maps'][0]['defect'].pop()),('drophalf',lambda x:x['cases'][0]['substep_maps'].pop()),('dropcycle',lambda x:x['cases'][0]['cycle_maps'].pop()),('dropcell',lambda x:x['cases'][0]['cell_maps'].pop()),('fabricated_fullcertificate',lambda x:x['cases'][unsupported].update(certificate_name=CERT)),('fabricated_uncertifiedmap',lambda x:x['cases'][unsupported]['cell_maps'].append(copy.deepcopy(out['cases'][0]['cell_maps'][0])))]
 records=[]
 for name,change in mutations:
  bad=copy.deepcopy(out);change(bad)
  try:validate(bad,inp)
  except (ValueError,KeyError):records.append(dict(name=name,rejected=True))
  else:raise AssertionError('corrupted certificate/schema accepted '+name)
 return dict(positive_controls=1,negative_controls=records,scope='Modified-output controls only, no native failures.')

def physical_domain(z,c):
 prior.state(z);limits=np.array(c['control_range']).reshape(7,2);C=np.array(z['C']);q=np.array(z['q']);ql=np.array(c['joint_range']).reshape(7,2);need(bool(((C-limits[:,0])>1e-8).all() and ((limits[:,1]-C)>1e-8).all()),'unchanged strict C extension support');need(bool((q>ql[:,0]).all() and (q<ql[:,1]).all()),'unchanged strict physical q support')
def exterior(case,ref):
 nodes=[case['state']]+[point(dict(q=case['state']['q'],v=case['state']['v'],**x)) for x in ref];flags=dict(w=False,alpha=any(abs(a)>1 for x in case['cells'] for a in x['alpha']),s=False,r=False)
 for z in nodes:flags['w']=flags['w'] or any(abs(x)>.0625 for x in z['w']);flags['s']=flags['s'] or z['s']<0 or z['s']>1;flags['r']=flags['r'] or z['r']<0 or z['r']>.2
 return {k:bool(v) for k,v in flags.items()}

def verify():
 checkfreeze();attempt=OUT/'parity-attempt1';attempt.mkdir(exist_ok=False);inp=json.loads((OUT/'inputs/cases.json').read_text());native=run(BIN,OUT/'inputs/cases.json',attempt/'analytic.json');validate(native,inp);schema=gates(native,inp);print('Native roster/certificate schema passed',flush=True)
 value=run(VALUE,OUT/'inputs/cases.json',attempt/'original_value.json');value_validate(value,inp)
 for a,b in zip(native['cases'],value['cases']):need(a['value']=={k:v for k,v in b.items() if k!='name'},'exact original closed nominal forward '+a['name'])
 oldinp=json.loads((OUT/'inputs/interior_reference.json').read_text());old=run(INTERIOR,OUT/'inputs/interior_reference.json',attempt/'original_interior_api.json');prior.validate(old,oldinp);new=native['cases'][16];need(new['value']==old['cases'][0]['value'],'old interior exactvalue')
 for key in ('substep_maps','cycle_maps','cell_maps'):
  need(len(new[key])==len(old['cases'][0][key]),'interior maproster')
  for a,b in zip(new[key],old['cases'][0][key]):
   for field in b:need(a[field]==b[field],'exact oldinterior numerical map field '+field)
 print('Exact old2fa nominal and a29 interior-map parity passed',flush=True)
 physics=[]
 for case,ans in zip(inp['cases'][:17],native['cases'][:17]):
  previous=case['state']
  for i,p in enumerate(ans['value']['substeps']):physics.append(dict(name=f'{case["name"]}_p{i}',q=previous['q'],v=previous['v'],C=p['C'],value_success=True,jacobian_success=True));previous=point(p)
 Js=prior.batches(PHYS,physics,attempt,'nominal_physical_derivative',derivative_validate);jl={x['name']:x for x in Js};normalized_native=normalized(native);mappings=[]
 for i,(case,ans) in enumerate(zip(inp['cases'],normalized_native['cases'])):mappings.append(prior.maps(case,ans,[jl[f'{case["name"]}_p{k}'] for k in range(len(ans['substep_maps']))] if i<17 else None))
 extension=[]
 for record in json.loads((OUT/'inputs/extension_fd_batches.json').read_text()):
  need(sha(record['path'])==record['sha256'],'extension inputs frozen');extension+=json.loads(Path(record['path']).read_text())['cases']
 need(len(extension)==2601 and len(set(x['name'] for x in extension))==2601,'complete predeclared extension roster');baseinputs=[];refs={};outside={};c=json.loads(CONST.read_text())
 for case in extension:
  need(case['extension_probe_only'] is True,'explicit mathematical extensionprobe only');ref=oracle(case);refs[case['name']]=ref;outside[case['name']]=exterior(case,ref);physical_domain(case['state'],c)
  for r in ref:physical_domain(dict(q=case['state']['q'],v=case['state']['v'],C=r['C'],w=r['w'],s=r['s_reference'],r=r['r_reference']),c)
  baseinputs.append(dict(name=case['name'],q=case['state']['q'],v=case['state']['v'],targets=[x['C'] for x in ref],expect_success=True,extension_probe_only=True))
 frozen_baseinputs=[]
 for m in json.loads((OUT/'inputs/extension_value_inputs_manifest.json').read_text()):
  need(sha(m['path'])==m['sha256'],'pre-frozen extensionoracle input');frozen_baseinputs+=json.loads(Path(m['path']).read_text())['cases']
 need(frozen_baseinputs==baseinputs,'derived oracle inputs equal pre-frozen rationaltargets');need(json.loads((OUT/'inputs/extension_exterior_flags_before_predictions.json').read_text())['records']==outside,'exteriorlabels pre-frozen')
 save(attempt/'extension_exterior_nodes_PRE_CALL.json',dict(scope='Nonphysical exterior flags at exactpolynomial nodes; mathematical extension only, not admission tests; never project or run exteriorold2fa/newAPI inputs.',records=outside));bases=prior.batches(DIAG,baseinputs,attempt,'extension_value_oracle',validate_output,True);bl={x['name']:x for x in bases};outputs={};diagnostic=[]
 for case,base in zip(extension,bases):
  ref=refs[case['name']];need(len(base['trace'])==len(ref),'complete extension physicaltrace');steps=[];previous=case['state']
  for i,(p,r) in enumerate(zip(base['trace'],ref)):
   z=dict(q=p['q'],v=p['v'],C=r['C'],w=r['w'],s=r['s_reference'],r=r['r_reference']);physical_domain(z,c);need(p['control_clips']==0,'no extensioncontrolclip');steps.append(z);diagnostic.append(dict(name=f'{case["name"]}_p{i}',q=previous['q'],v=previous['v'],targets=[r['C']],expect_success=True));previous=z
  cycles=steps[1::2];cells=[];offset=0
  for ce in case['cells']:offset+=ce['cycles'];cells.append(cycles[offset-1])
  outputs[case['name']]=dict(substeps=steps,cycle_end_states=cycles,cell_end_states=cells,final_state=cells[-1])
 print('Extension oracle physicalself-rollouts passed',len(bases),'single-step diagnostics',len(diagnostic),flush=True)
 diagnostics=prior.batches(DIAG,diagnostic,attempt,'extension_physical_diagnostic',validate_output,True);dl={x['name']:x for x in diagnostics};dil={x['name']:x for x in diagnostic};signatures={}
 for case in extension:
  ss=[]
  for i,z in enumerate(outputs[case['name']]['substeps']):
   name=f'{case["name"]}_p{i}';d=dl[name]['last'];need(d['q']==z['q'] and d['v']==z['v'],'exact fa1 selfpropagated diagnostic parity');x=dil[name];ss.append(branch(dict(q=x['q'],v=x['v'],C=x['targets'][0]),d,c));M=np.array(d['M']);K=M+.002*np.diag(np.array(c['passive_damping'])-np.array(c['biasprm']).reshape(7,10)[:,2]);Hs=(np.array(d['H'])+np.array(d['H']).T)/2;free=[j for j,l in enumerate(d['friction']['branches']) if l==0]
   for mat in [M,Hs,K]+([Hs[np.ix_(free,free)]] if free else []):ev=np.linalg.eigvalsh(mat);need(bool(ev[0]>0 and ev[-1]/ev[0]<=1e12),'every extensionperturbation SPD/condition support')
  signatures[case['name']]=ss
 records=[]
 for ci,(case,ans) in enumerate(zip(inp['cases'],native['cases'])):
  rec=dict(name=case['name'],value_success=bool(ans['value']['success']),extension_jacobian_success=bool(ans['extension_jacobian_success']),certified_substeps=len(ans['substep_maps']),certified_cycles=len(ans['cycle_maps']),certified_cells=len(ans['cell_maps']),max_structural=mappings[ci]['max_structural'],max_defect=mappings[ci]['max_defect'])
  if not ans['extension_jacobian_success']:rec.update(error=ans['error'],first_uncertified_substep=ans['first_uncertified_substep']);records.append(rec);continue
  nominal=outputs[case['name']];errors=dict(q=0.,v=0.,command_progress=0.);need(len(ans['value']['substeps'])==len(nominal['substeps']),'nominal exact oracle roster')
  for p,z in zip(ans['value']['substeps'],nominal['substeps']):
   errors['q']=max(errors['q'],close(p['q'],z['q'],1e-12,'fixed nominaloracle q roundoff'));errors['v']=max(errors['v'],close(p['v'],z['v'],1e-11,'fixed nominaloracle v roundoff'))
   for key in ('C','w'):errors['command_progress']=max(errors['command_progress'],close(p[key],z[key],msg='fixed rationalnominal '+key))
   errors['command_progress']=max(errors['command_progress'],close([p['s_reference'],p['r_reference']],[z['s'],z['r']],msg='fixed rationalnominal progress'))
  epsreports=[]
  for ei,e in enumerate(EPS):
   maxima=dict(max_absolute=0.,max_gate_ratio=0.)
   for j in range(38):
    names=[f'{case["name"]}_e{ei}_col{j}_sign{s}' for s in (-1,1)];minus,plus=[outputs[n] for n in names]
    for n in names:need(signatures[n]==signatures[case['name']],'all extensionperturbations same strictphysicalbranches')
    for mapkey,endpointkey in [('global_substeps','substeps'),('global_cycles','cycle_end_states'),('global_cells','cell_end_states')]:
     need(len(mappings[ci][mapkey])==len(minus[endpointkey])==len(plus[endpointkey]),'all extensionFD endpoints')
     for k,(A,B) in enumerate(mappings[ci][mapkey]):
      fd=(pack(plus[endpointkey][k])-pack(minus[endpointkey][k]))/(2*e);col=A[:,j] if j<30 else B[:,j-30];r=compare(col,fd)
      for field in maxima:maxima[field]=max(maxima[field],r[field])
   epsreports.append(dict(epsilon=e,**maxima))
  rec.update(epsilons=epsreports,nominal_oracle_errors=errors,pass_check=True);records.append(rec)
 checkfreeze();save(attempt/'report.json',dict(status='PASS_SELECTED_COMMAND_PROGRESS_EXTENSION_JACOBIANS_ONLY',certificate_name=CERT,certifies_two_sided_admissible_neighborhood=False,phase5='NOT_ACCEPTED',phase6='NOT_STARTED',freeze_sha256=sha(OUT/'frozen_before_predictions.json'),binary_sha256=sha(BIN),records=records,synthetic_output_gates=schema,extension_oracle_cases=len(bases),original_physical_diagnostics=len(diagnostic),independent_nominal_physical_derivatives=len(Js),exterior_nonphysical_case_count=sum(any(x.values()) for x in outside.values()),exterior_node_flags_sha256=sha(attempt/'extension_exterior_nodes_PRE_CALL.json'),epsilons=EPS,absolute_per_entry=ABS,relative_per_entry=REL,scope='Selected composite Jacobians induced by smoothcommand/progress polynomialextension; fullphysicalmap nonlinear. Closednominal originalvalues unchanged; exteriornonphysicalperturbations mathematicalonly. No admissible direction/neighborhood/tangent/continuation/safety/accuracy/controller/main/plant/task/timing or Phase5 acceptance.'))
 print('PASS',len(records),'cases',len(bases),'extension oracles',len(diagnostic),'originalphysical diagnostics',flush=True)
if __name__=='__main__':globals()[sys.argv[1]]()
