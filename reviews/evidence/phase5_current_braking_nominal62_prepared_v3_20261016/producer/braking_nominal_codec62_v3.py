"""Explicit hybrid stop nominal V3 with complete streaming family records or qualified source-failure prefix."""
import math
ROLE='STOP_COST_CURRENT_HISTORY_JOINT_HAT_PROGRESS_ENVELOPE_NOMINAL_V3'
LENGTHS=[1,2,3,4,5,6,7,8,10,12,16,19]
SUPPORTS=[2,3,4,5,6,7,8,10,12,16,19]
def braking62(raw,R,source_complete=True):
 assert len(raw)<=131072
 r=R(raw,ROLE);o=dict(cycle=r.u(),stop_mode=r.u(),factor_rows=r.u());assert o['stop_mode']==1 and o['factor_rows']==909;o['weights']=[r.d()for _ in range(5)];assert o['weights']==[100.,1000.,1000.,0.,0.];o['objective_id']=r.text();assert 0<len(o['objective_id'])<=256
 for k in ['trial','regenerated','ordinal','max_families','max_attempts','max_builds','numeric_precharge']:o[k]=r.u()
 assert o['trial']<3 and o['regenerated']in(0,1)and 0<o['ordinal']<=89 and [o[k]for k in ['max_families','max_attempts','max_builds','numeric_precharge']]==[148,1072,89,2048];assert bool(o['regenerated'])==(o['trial']==0)
 o['target_rate_floor']=r.d();assert o['target_rate_floor']==1e-8
 for k in ['current_C','current_w','previous_alpha']:o[k]=[r.d()for _ in range(7)]
 for k in ['current_s','current_r','previous_b']:o[k]=r.d()
 records=[];terminated=False;partial_tail=False
 while r.i<len(r.b):
  at=r.i
  if len(r.b)-r.i<8:partial_tail=True;break
  tag=r.u()
  if tag==0:terminated=True;break
  assert tag==1 and len(records)<1072
  if len(r.b)-r.i<88:r.i=at;partial_tail=True;break
  e={k:r.u()for k in ['channel','family','reason','cell','step']};e.update({k:r.d()for k in ['pulse','last_rate','last_position','max_jerk','observed','bound']});assert e['channel']<8 and e['family']<(148 if e['channel']==7 else 132) and e['reason']<=10 and e['cell']<=20 and e['step']<40
  if records:
   prior=records[-1]
   if e['channel']==prior['channel']:assert prior['reason']!=0 and e['family']==prior['family']+1
   else:assert e['channel']==prior['channel']+1 and prior['reason']==0 and e['family']==0
  else:assert e['channel']==e['family']==0
  assert e['reason']==1 or all(math.isfinite(e[k])for k in ['pulse','last_rate','last_position','max_jerk','observed','bound']);records.append(e)
 if not terminated:
  assert not source_complete
  o.update(attempts=records,source_complete=False,terminal_available=False,partial_record_tail=partial_tail,qualification='Retained closed/readable source-failure prefix only; every complete attempted record available here is preserved, no successful nominal/Model/math/stop claim.');return o
 o['build_complete']=r.u();o['record_count']=r.u();assert o['record_count']==len(records);summary=[]
 for channel in range(8):summary.append(dict(channel=channel,selected=r.u(),attempted=r.u(),pulse=r.d(),terminal_rate=r.d()))
 assert r.u()==20 and r.u()==8;o['controls']=[[r.d()for _ in range(8)]for _ in range(20)];assert all(math.isfinite(x)for row in o['controls']for x in row);o['scope']=r.text();r.end();assert source_complete
 if o['regenerated']:
  assert o['build_complete']==1
  for channel,e in enumerate(summary):
   own=[a for a in records if a['channel']==channel];assert own and own[-1]['reason']==0 and all(a['reason']!=0 for a in own[:-1]);assert e['selected']==own[-1]['family']and e['attempted']==len(own)and e['pulse']==own[-1]['pulse']and e['terminal_rate']==own[-1]['last_rate'];assert o['controls'][-1][channel]==0.
 else:assert not records and o['build_complete']==0 and all(e['selected']==e['attempted']==e['pulse']==e['terminal_rate']==0 for e in summary)
 o['family_parameter_scope']='Joint and progress family0..131 parameter is hat pulse; progress132..147 is convex-mix fraction with J grid [4.99,4.5,4,3.5,3,2.5,2,1.5,1,.75,.5,.25,.1,.05,.02,.01]. Original V2 role remains separately parsed.'
 o.update(attempts=records,summary=summary,source_complete=True,terminal_available=True,qualification='Scalar nominal construction diagnostics only; actual state/history unchanged, no Model/SI/B/C/physical stop proof.');return o
