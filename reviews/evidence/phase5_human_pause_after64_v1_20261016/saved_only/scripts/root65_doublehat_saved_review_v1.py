from pathlib import Path
import os,sys,json,ast,struct,math,hashlib
import numpy as np
sys.path.insert(0,'/private/tmp');from bounded_derived_bytes53_v1 import bounded_write
import root63_nominal_reader_v4 as old
strict=old.strict
T=ast.parse(Path('/private/tmp/root_independent_controlled_stop52_review_20261012/reference_source/audit_geometry_qp_actual.py').read_text());exec(compile(ast.Module(body=[x for x in T.body if isinstance(x,ast.ClassDef)and x.name=='R'or isinstance(x,ast.FunctionDef)and x.name=='snapshot'],type_ignores=[]),'<snapshot-only>','exec'))
P=Path('/private/tmp/phase5_physical_stop_nominal_design_v1_20261016');j=json.loads((P/'SAVED64_DOUBLEHAT_PHYSICAL_AND_PROGRESS_DESIGN.json').read_text());O=Path('/private/tmp/root65_saved_design_review_v1_20261016');O.mkdir();os.environ['P5_DERIVED53_ROOT']=str(O);A=next(Path('/private/tmp/phase5_controlled_stop_roundoff_command_terminal64_v1_20261016').glob('actual-dell/*/run-attempt1/artifacts'));base=snapshot(strict.read_artifact_bytes(A/'cycle-0/trial-0/observation_before.bin'));offset=base['x'][14:21]-base['x'][:7];assert offset.tolist()==j['baseline_offset_C_minus_q'];constants=json.loads(Path('/private/tmp/root62_stop_cause_review_v1_20261016/PINNED_PUBLIC_CONSTANTS.json').read_text());out=[]
def integr(u,w,C):
 for a,m in zip(u,old.MESH):
  for _ in range(m):w=w+.004*a;C=C+.004*w
 return w,C
for case in j['cases']:
 cycle=case['cycle'];s=snapshot(strict.read_artifact_bytes(A/f'cycle-{cycle}/trial-0/observation_before.bin'));physical=s['x'];assert case['snapshot']['q']==physical[:7].tolist()and case['snapshot']['v']==physical[7:14].tolist()and case['snapshot']['C']==physical[14:21].tolist()and case['snapshot']['w']==physical[21:28].tolist();targets=physical[:7]+offset-.02*physical[7:14];valid=[];selected=[];maxpulseerr=0.;maxterminalerr=0.
 for ch,c in enumerate(case['channels']):
  assert c['target_C']==targets[ch]and len(c['records'])==132;chosen=None;chosenid=None;validc=0
  for rec in c['records']:
   f=rec['family'];L=old.LENGTHS[f//11];M=old.SUPPORTS[f%11];prior=s['alpha'][ch];rate=physical[21+ch];pos=physical[14+ch];b0=[prior*max(0.,1.-(k+1)/L)for k in range(20)];peak=(M-1)//2;a=[min((k+1)/(peak+1),(M-k)/(M-peak))if k<M else 0. for k in range(20)];b=[a[18-k]if k<=18 else 0. for k in range(20)];v0,C0=integr(b0,rate,pos);wa,Ca=integr(a,0.,0.);wb,Cb=integr(b,0.,0.);det=wa*Cb-wb*Ca;scale=abs(wa*Cb)+abs(wb*Ca)
   if not scale>0 or abs(det)<=1e-10*scale:assert rec['reason']==11;continue
   p=np.linalg.solve(np.array([[wa,wb],[Ca,Cb]]),np.array([-v0,targets[ch]-C0]));maxpulseerr=max(maxpulseerr,abs(p[0]-rec['pulse1']),abs(p[1]-rec['pulse2']));u=[b0[k]+rec['pulse1']*a[k]+rec['pulse2']*b[k]for k in range(20)];proof=old.check(u,rate,prior,pos,False,constants['control_range'][2*ch],constants['control_range'][2*ch+1],0.)
   if proof[0]==0 and abs(proof[4]-targets[ch])>1e-12:proof=(13,proof[1],proof[2],*proof[3:])
   assert proof[:3]==(rec['reason'],rec['cell'],rec['step']),(cycle,ch,f,proof[:3],rec['reason'])
   for key,v in zip(['last_rate','last_position','max_jerk','observed','bound'],proof[3:]):assert abs(v-rec[key])<=1e-12*max(1.,abs(v),abs(rec[key]))
   if rec['reason']==0:
    assert np.max(np.abs(np.array([b0[k]+p[0]*a[k]+p[1]*b[k]for k in range(20)])-u))<=1e-11;score=abs(pos+.004*(rate+.004*u[0])-targets[ch]);assert score==rec['score'];validc+=1;maxterminalerr=max(maxterminalerr,abs(proof[4]-targets[ch]))
    if chosen is None or score<chosen:chosen=score;chosenid=f
  assert chosenid==c['selected']['record']['family'];selected.append(chosenid);valid.append(validc)
  u=c['selected']['controls'];assert np.array_equal(np.array(u),np.array(case['selected_controls'])[:,ch]);p=old.check(u,physical[21+ch],s['alpha'][ch],physical[14+ch],False,constants['control_range'][2*ch],constants['control_range'][2*ch+1],0.);assert p[0]==0 and abs(p[4]-targets[ch])<=1e-12
 progress=case['progress'];chosen=None
 for rec in progress['records']:
  f=rec['family'];assert f<148
  if f<132:u,pulse=old.family(physical[29],s['b'],2e-7,f);early=None
  else:u,pulse,early=old.envelope(physical[29],s['b'],2e-7,f-132,physical[28])
  pr=old.check(u,physical[29],s['b'],physical[28],True,0,0,2e-7)if early is None else early
  reason,cell,step=pr[:3]
  if reason==0 and physical[29]+.004*u[0]<1e-7:reason,cell,step=12,0,0
  assert(reason,cell,step)==(rec['reason'],rec['cell'],rec['step'])
  if reason==0:chosen=f;break
 assert chosen==progress['selected']['record']['family'];out.append(dict(cycle=cycle,all132x7_records_recomputed=True,all_reason_cell_step_and_literal_recurrences_match=True,doublehat_numpy_2x2_solve_pulse_error_inf=maxpulseerr,selected_exact_earliest_score_min=selected,valid_joint_counts=valid,maximum_terminal_C_target_error=maxterminalerr,progress_selected=chosen,progress_nominal_terminal_target=2e-7,first_progress_rate_lower=1e-7))
report=dict(schema='ROOT65_TWO_REAL_SAVED_HISTORY_DOUBLEHAT_AND_PROGRESS_DESIGN_REVIEW_V1',baseline_same_actual64_session0=True,baseline_physical_velocity_inf=float(np.max(np.abs(base['x'][7:14]))),baseline_bias7=offset.tolist(),T_seconds=.02,cases=out,maximum_proposed_record_bytes=112,maximum_payload_bound=126336,baseline_retained_scalar_count=10,scope='Independent saved-data family generation/scalar/history/progress/selection review and independent2x2 coefficient solve only. Current q/v/history unchanged, warmup bias approximate and nonzero-v, no exact gravity equilibrium. No new source65 native/Model/OSQP/SI/B/C or physical stop claim. New firstprogress/position targets are prospective planning restrictions; original gates/caps remain.')
bounded_write(O/'DOUBLEHAT_TWO_HISTORY_INDEPENDENT_REVIEW.json',json.dumps(report,indent=2)+'\n');print(json.dumps(report))
