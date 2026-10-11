"""Closeout stage2: existing saved36 full factor/SI/reduction/geometry algebra only.
No Model, native, optimizer, compiler, FK, Scene, SSH, or new research case.
"""
from pathlib import Path
import sys,hashlib,json,importlib.util,ast
import numpy as np
sys.dont_write_bytecode=True
OUT=Path(__file__).resolve().parent;PACK=Path('/Users/uot/Documents/ChatGPT/ros/results/phase5-reference/nonzero-progress-actual-v1-20261011/runtime-import1');BASE=PACK/'artifacts';PROFILE=Path('/private/tmp/phase5_nonzero_progress_tail_runtime_profile_v1_20261011/profile-version1')
HELPER=Path('/private/tmp/root_independent_geometry_qp_actual_review_20261011/audit_geometry_qp_actual.py');pins={}
def pin(p,h=None):
 b=p.read_bytes();sha=hashlib.sha256(b).hexdigest();assert h is None or sha==h;pins[str(p)]={'bytes':len(b),'sha256':sha};return b
spec=importlib.util.spec_from_file_location('prior_root30_algebra',HELPER);m=importlib.util.module_from_spec(spec);pin(HELPER,'b648463d205992e217480407e8b2a5e553ac0401137b3a1ce084f1bcc3597c5b');spec.loader.exec_module(m);m.pin=pin
# Parse-only local schemas frozen from reviewed final36; don't execute stage1 body again.
stage=pin(OUT/'audit_actual36.py');tree=ast.parse(stage);ctx={'R':m.R};selected=ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['reduction','guard']],type_ignores=[]);exec(compile(selected,'<frozen-local-parse-definitions>','exec'),ctx)
profile=json.loads(pin(PROFILE/'active_input.json'));constants=json.loads(pin(Path('/private/tmp/public_live_affine_v2_integrated_first_cycle_canonical_protocol_repair_v2_20261010/proposed-files/inputs/public_constants.json'),profile['constants']['sha256']));initial=m.snapshot(pin(BASE/'observation_before.bin'))
results=[]
for cycle in range(3):
 cb=BASE/f'cycle-{cycle}';before=m.snapshot(pin(cb/'observation_before.bin'));n=m.nominal(pin(cb/'original_nominal.bin'));q=m.inline_full(pin(cb/'inline_qp.bin'));d=ctx['reduction'](pin(cb/'qp_equality_reduction.bin'));gd=ctx['guard'](pin(cb/'planning_guard.bin'));candidate=m.candidate(pin(cb/'candidate.bin'));geometry=m.parse_geometry(pin(cb/'nominal_geometry_rows.bin'))
 geom=m.verify_geometry(geometry,n,before,profile,cycle)
 orig,assembly=m.reproduce_original(n,q,before['x'],initial['x'][:7],profile,constants,geometry)
 check={};ck=lambda k,a,b,*args:m.compare(check,k,a,b,*args)
 H,g,A,l,u,F=[q[k] for k in ['H','g','A','l','u','F']]
 labels=q['labels'];eq=[next(i for i,x in enumerate(labels) if x[0]==('terminal/alpha/'+str(j) if j<7 else 'terminal/b')) for j in range(8)]+[next(i for i,x in enumerate(labels) if x[0]==('terminal/command_w/'+str(j) if j<7 else 'terminal/progress_r')) for j in range(8)]
 assert d['eq']==eq and np.array_equal(d['E'],A[eq]) and np.array_equal(d['rhs'],l[eq]) and np.array_equal(l[eq],u[eq])
 rhs=l[eq].copy();rhs[15]+=1e-13;assert np.array_equal(d['planning_rhs'],rhs)
 Z=np.zeros((160,144));Z[:144]=np.eye(144);p=np.zeros(160)
 for j in range(8):
  assert np.count_nonzero(A[eq[j]])==1 and A[eq[j],152+j]==1 and l[eq[j]]==0
  p[144+j]=rhs[8+j]/A[eq[8+j],144+j];Z[144+j]=-A[eq[8+j],:144]/A[eq[8+j],144+j]
 assert np.array_equal(Z,d['Z']) and np.array_equal(p,d['p'])
 assert d['rows'][-160:]==[-1]*160;rows=d['rows'][:-160];assert all(r>=0 and r not in eq for r in rows) and len(rows)==gd['base']
 Hr=Z.T@H@Z;gr=Z.T@(g+H@p);Ar=A[rows]@Z;lower=l[rows]-A[rows]@p;upper=u[rows]-A[rows]@p;D=1/np.sqrt(np.diag(Hr));baseR=1/np.maximum(1,np.max(np.abs(Ar*D),axis=1))
 alpha_cols=[8*k+j for k in range(20) for j in range(7)];progress_cols=[8*k+7 for k in range(20)];assert gd['cols']==alpha_cols+progress_cols
 extraA=[z.copy() for z in Z[alpha_cols]];extral=list(-.000999-p[alpha_cols]);extrau=list(.000999-p[alpha_cols])
 for k,col in enumerate(progress_cols):
  row=Z[col]/.004;shift=p[col]/.004
  if k:row=row-Z[col-8]/.004;shift-=p[col-8]/.004
  else:shift-=before['b']/.004
  extraA.append(row);extral.append(-4.999-shift);extrau.append(4.999-shift)
 Ar=np.vstack([Ar,extraA]);lower=np.r_[lower,extral];upper=np.r_[upper,extrau];extraR=1/np.maximum(1,np.max(np.abs(np.array(extraA)*D),axis=1));RR=np.r_[baseR,extraR]
 ck('Hr',d['Hr'],Hr);ck('gr',d['gr'],gr);ck('Fr',d['Fr'],F@Z);ck('Ar',d['Ar'],Ar);ck('lr',d['lr'],lower);ck('ur',d['ur'],upper);ck('D',d['D'],D);ck('R',d['R'],RR);ck('guard_R',gd['R'],extraR)
 ck('Hs',d['Hs'],D[:,None]*Hr*D);ck('gs',d['gs'],D*gr);ck('As',d['As'],RR[:,None]*Ar*D);ck('ls',d['ls'],RR*lower);ck('us',d['us'],RR*upper);ck('Fs',d['Fs'],(F@Z)*D)
 ck('seed',d['seed'],q['seed'][:144],0,0)
 ck('constant',d['errors'][0],q['constant']+g@p+.5*p@H@p)
 ck('planning_Ep',d['E']@p,rhs,2e-13,1e-12);ck('EZ',d['E']@Z,np.zeros((16,144)),2e-13,1e-12)
 originalE=float(np.max(np.abs(d['E']@p-d['rhs'])));assert originalE<=1e-12
 # Literal full/reduced objective and derivatives at actual native output, not just zero/nominal input.
 x=d['x'];Y=D*x;U=candidate['U'];ck('Y',d['Y'],Y);ck('U',U,p+Z@Y)
 fullcost=.5*U@H@U+g@U+q['constant'];redcost=.5*Y@Hr@Y+gr@Y+d['errors'][0];factorcost=.5*np.linalg.norm(F@U+q['f'])**2-.1*(assembly['M'][-1,28]@U+assembly['c'][-1,28]);ck('full_vs_reduced_cost',fullcost,redcost);ck('full_vs_factor_cost',fullcost,factorcost)
 ck('reduced_gradient',Hr@Y+gr,Z.T@(H@U+g));ck('scaled_gradient',d['Hs']@x+d['gs'],D*(Hr@Y+gr))
 results.append({'cycle':cycle,'full_original_algebra':orig,'geometry_saved_supports':geom,'reduction_algebra':check,'original_Ep_residual':originalE,'native_rows':len(d['rows']),'free_columns':144,'planning_bias_target':1e-13,'exact_E0_equivalence':False,'original_cost_at_actual_U':float(fullcost)})
for path,i in pins.items():b=Path(path).read_bytes();assert len(b)==i['bytes'] and hashlib.sha256(b).hexdigest()==i['sha256']
result={'schema':'ROOT_ACTUAL36_FULL_FILE_ALGEBRA_STAGE2_V1','cycles':results,'scope':'Full raw nominal-map lifted elimination,741factor/fullcost,14756SI,160internalguards/full144biased reduction and4800savedgeometrysupports arithmetic. No full9035 queryraw rerun, native/model/optimizer/FK/Scene/compiler calls, task/stop/realtime/Phase5 acceptance.','input_pins':pins}
(OUT/'STAGE2_RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps([{'cycle':x['cycle'],'original_Ep':x['original_Ep_residual'],'rows':x['native_rows'],'A_error':x['full_original_algebra']['A'],'F_error':x['full_original_algebra']['F'],'reduction_max':max(x['reduction_algebra'].values())} for x in results]))
