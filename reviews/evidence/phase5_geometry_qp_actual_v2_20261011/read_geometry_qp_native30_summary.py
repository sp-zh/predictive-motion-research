from pathlib import Path
import struct,json,math,hashlib,sys
ROOT=Path(sys.argv[1]);P=Path(sys.argv[2]);P.mkdir(exist_ok=False)
class R:
 def __init__(self,p):self.b=p.read_bytes();self.i=0
 def raw(self,n):b=self.b[self.i:self.i+n];assert len(b)==n;self.i+=n;return b
 def u(self):return struct.unpack('<Q',self.raw(8))[0]
 def signed(self):n=self.u();return n if n<(1<<63) else n-(1<<64)
 def f(self):return struct.unpack('<d',self.raw(8))[0]
 def text(self):return self.raw(self.u()).decode()
 def vec(self):n=self.u();assert n<=1000000;return [self.f() for _ in range(n)]
 def head(self):assert self.text()=='P5_ACTIVE_SESSION_LOSSLESS_V1';return self.text()
 def fixedstate(self):return {**{k:[self.f() for _ in range(7)] for k in ['q','v','C','w']},'s':self.f(),'r':self.f()}
 def state(self):return {**{k:self.vec() for k in ['q','v','C','w']},'s':self.f(),'r':self.f()}
 def end(self):assert self.i==len(self.b),(self.i,len(self.b))
def matrix(q):
 r,c=q.u(),q.u();assert r*c<=2000000;return [[q.f() for _ in range(c)] for _ in range(r)]
def snapshot(path):
 q=R(path);out={'role':q.head(),'observation_id':q.text(),'transaction_id':q.text(),'boundary':[q.u(),q.u()],'complete':q.u(),'stage':q.text(),'error':q.text(),'joints_read':q.u(),'before_written':q.u(),'after_written':q.u(),'simulation_time':q.f(),'observer_age':q.f(),'contact_free':q.u(),'state':q.fixedstate(),'previous_alpha':[q.f() for _ in range(7)],'previous_b':q.f(),'acceleration_available':q.u(),'last_actual_velocity':[q.f() for _ in range(7)],'last_actual_acceleration':[q.f() for _ in range(7)],'total_actual_substeps':q.u(),'physical_source_id':q.text(),'integration_before':q.vec(),'integration_after':q.vec()};q.end();return out
q=R(ROOT/'entry_completion.bin');entry={'role':q.head(),'stage':q.text(),'error':q.text(),'boundary_unchanged':q.u(),'session_termination_pass':q.u(),'session_termination_error':q.text(),'native_termination_pass':q.u(),'native_termination_error':q.text(),'entry_wall_seconds':q.f(),'total_physical_step_attempts':q.u(),'commits':q.u()};q.end()
q=R(ROOT/'bootstrap.bin');q.head();entry['native_facts']={k:q.u() for k in ['load_xml','make_data','reset','forward','copy','get_state','observations','step','commits']};q.end();cycles=[]
O=P/'cycle-json';O.mkdir(exist_ok=False)
for cycle in range(3):
 D=ROOT/('cycle-'+str(cycle));C=O/('cycle-'+str(cycle));C.mkdir();e={}
 q=R(D/'candidate_validation.bin');a={'role':q.head(),'attempted':q.u(),'passed':q.u(),'stage':q.text(),'error':q.text(),'reach_bound_m':q.f(),'geometry_radius_m':q.f(),'sigma_lipschitz':q.f(),'interval_scope':q.text(),'points':[]}
 for _ in range(q.u()):
  p={k:q.u() for k in ['sample','cell','cycle','half']};p['elapsed']=q.f();p['acceleration']=[q.f() for _ in range(7)];p['jerk']=[q.f() for _ in range(7)]
  for k in ['min_true','min_cover','sigma','geometry_interval_lower','sigma_interval_lower','affine_error','joint_trust']:p[k]=q.f()
  p.update(geometry_queries=q.u(),complete=q.u(),stage=q.text(),error=q.text());a['points'].append(p)
 q.end()
 q=R(D/'candidate_value.bin');v={'role':q.head(),'facts':{k:q.u() for k in ['constructor_attempts','metadata_attempts','rollout_attempts']},'metadata_present':q.u()}
 if v['metadata_present']:
  m={'pinocchio_version':q.text(),'nq':q.u(),'nv':q.u()}
  for k in ['joint_names','frame_names']:m[k]=[q.text() for _ in range(q.u())]
  for k in ['idx_q','idx_v','joint_nq','joint_nv']:m[k]=[q.u() for _ in range(q.u())]
  for k in ['masses','armature','gravity','R','B','damping']:m[k]=q.vec()
  v['metadata']=m
 v.update(transport_error=q.text(),nominal_digest=q.text(),candidate_digest=q.text(),actual_initial=q.fixedstate(),cells=[])
 for _ in range(q.u()):v['cells'].append({'cycles':q.u(),'alpha':q.vec(),'b':q.f()})
 v['raw_exists']=q.u();v['substeps']=[]
 if v['raw_exists']:
  v.update(success=q.u(),has_final_state=q.u(),error=q.text(),final_state=q.state())
  for _ in range(q.u()):
   p={k:q.u() for k in ['cell','cycle','half']};p.update(elapsed=q.f(),s=q.f(),r=q.f())
   for k in ['q','v','C','w','friction_force']:p[k]=q.vec()
   p.update(friction_branches=[q.signed() for _ in range(q.u())],friction_iterations=q.u(),original_kkt=q.f(),control_clips=q.u(),force_clips=q.u());v['substeps'].append(p)
  for k in ['cycle_end_states','cell_end_states']:v[k]=[q.state() for _ in range(q.u())]
 q.end();e['candidate_value_summary']={k:v[k] for k in ['facts','raw_exists','success','has_final_state','error','transport_error','nominal_digest','candidate_digest']};e['candidate_value_summary'].update(substeps=len(v['substeps']),cycle_states=len(v['cycle_end_states']),cell_states=len(v['cell_end_states']))
 e['assessment_summary']={k:a[k] for k in a if k!='points'};e['assessment_summary'].update(retained_points=len(a['points']),completed_points=sum(p['complete'] for p in a['points']),first_failure=next((z for z in a['points'] if not z['complete'] or z['error']),None),last_completed_point=next((z for z in reversed(a['points']) if z['complete']),None))
 
 if (D/'actual_commit.bin').exists():
  q=R(D/'actual_commit.bin');c={'role':q.head(),'attempted':q.u(),'success':q.u(),'native_step_attempts':q.u(),'native_returns':q.u(),'stage':q.text(),'error':q.text(),'history_before':[q.u(),q.u()],'history_after':[q.u(),q.u()],'held_C':[q.f() for _ in range(7)],'before_time':q.f(),'after_time':q.f(),'points':[]}
  for _ in range(q.u()):
   z={'substep':q.u(),'simulation_time':q.f(),'native_returned':q.u(),'native_joints_read':q.u(),'scratch_joints_read':q.u()}
   for k in ['q','v','C','acceleration','jerk']:z[k]=[q.f() for _ in range(7)]
   z.update(jerk_available=q.u(),geometry_complete=q.u(),independent_observer_guard=q.u(),contacts=q.u(),warnings=[q.u() for _ in range(8)])
   for k in ['minimum_true','minimum_cover','tcp_frame_error','arm_frame_error','sigma','geometry_interval_lower','sigma_interval_lower']:z[k]=q.f()
   z.update(geometry_queries=q.u(),passed=q.u(),stage=q.text(),error=q.text());c['points'].append(z)
  q.end();(C/'ACTUAL_COMMIT.json').write_text(json.dumps(c,indent=2)+'\n');e['commit_summary']=c
 if (D/'planning_guard.bin').exists():
  q=R(D/'planning_guard.bin');g={'role':q.head(),'solver_alpha_guard':q.f(),'strict_alpha_guard':q.f(),'base_solver_row_count':q.u(),'original_alpha_columns':[q.u() for _ in range(q.u())],'guard_row_scale':q.vec(),'backend_internal_guard_label':q.text(),'scope':q.text()};q.end();e['planning_guard_summary']={k:g[k] for k in g if k not in ['original_alpha_columns','guard_row_scale']};e['planning_guard_summary']['guard_rows']=len(g['original_alpha_columns']);(C/'ACTUAL_PLANNING_GUARD.json').write_text(json.dumps(g,indent=2)+'\n')
 (C/'ACTUAL_PILOT_SUMMARY.json').write_text(json.dumps(e,indent=2)+'\n');(C/'ACTUAL_CANDIDATE_VALIDATION.json').write_text(json.dumps(a,indent=2)+'\n');(C/'ACTUAL_CANDIDATE_VALUE.json').write_text(json.dumps(v,indent=2)+'\n')
 q=R(D/'candidate.bin');role=q.head();candidate={'role':role,'stop_reason':q.text(),'execution_permission':q.u(),'solve_attempts':q.u(),'solver_wrapper_entries':q.u(),'status_enum':q.u(),'raw_status':q.u(),'api_error':q.u(),'iterations':q.u(),'maximum_violation_row_u64':q.u(),'control_vector':q.vec()}
 for k in ['violation','primal_residual','dual_residual','setup_seconds','solve_seconds','minimum_row_scale','maximum_row_scale','minimum_variable_scale','maximum_variable_scale','solver_absolute_tolerance','solver_relative_tolerance','initial_rho','rho_estimate','update_seconds']:candidate[k]=q.f()
 for k in ['workspace_reused','matrix_updated','dual_reused','dual_mapped_rows']:candidate[k]=q.u()
 candidate['reset_reason']=q.text()
 for k in ['hessian_nonzeros','constraint_nonzeros','rho_updates','polish_status']:candidate[k]=q.u()
 candidate['original_row_violations']=[q.f() for _ in range(q.u())];candidate['timing_mode']=q.u()
 for k in ['original_observer_age','known_upstream_elapsed','connection_and_solver_elapsed','known_wall_age']:candidate[k]=q.f()
 for k in ['known_current_age_within_policy','complete_online_observation_timing_proved']:candidate[k]=q.u()
 candidate['forensic_preview_exists']=q.u()
 if candidate['forensic_preview_exists']:
  values=[q.f() for _ in range(43)];candidate['preview_values']=values;candidate['preview_boundary']=[q.u(),q.u()]
 candidate['terminal_tail_exists']=q.u()
 if candidate['terminal_tail_exists']:candidate['tail']=[q.f() for _ in range(16)]+[q.u()]
 candidate['forward_request_exists']=q.u();assert candidate['forward_request_exists']
 request={'state30':[q.f() for _ in range(30)],'boundary':[q.u(),q.u()],'observation_id':q.text(),'transaction_id':q.text(),'nominal_sha256':q.text(),'cycles':[q.u() for _ in range(20)]}
 request['controls']=[[q.f() for _ in range(8)] for _ in range(q.u())];assert len(request['controls'])==20 and all(v[7]==0 for v in request['controls']);candidate['forward_request']=request
 assert q.i==len(q.b)
 
 q.end();(C/'ACTUAL_SOLVER_SUMMARY.json').write_text(json.dumps(candidate,indent=2)+'\n')
 q=R(D/'validation_initial.bin');initial={'role':q.head(),'q':[q.f() for _ in range(7)],'observation_id':q.text(),'transaction_id':q.text(),'simulation_time':q.f(),'weighted_body_jacobian':matrix(q),'minimum_true':q.f(),'minimum_cover':q.f(),'sigma':q.f(),'geometry_complete':q.u(),'scope':q.text()};q.end();(C/'VALIDATION_INITIAL.json').write_text(json.dumps(initial,indent=2)+'\n')
 q=R(D/'cycle_timing.bin');timing={'role':q.head(),'cycle':q.u(),'complete':q.u(),'complete_cycle_seconds':q.f(),'deadline_missed':q.u(),'segments':[]}
 for name in ['observe','nominal_maps','geometry_assembly','solve','value_validation','commit_journal']:timing['segments'].append({'name':name,'measured':q.u(),'seconds':q.f()})
 timing['ledger']={name:q.u() for name in ['completed_commits','forecast_budget_reservations','step_budget_reservations','original_session_charged_slots','separate_logical_reserved_slots']};timing['scope']=q.text();q.end();(C/'CYCLE_TIMING.json').write_text(json.dumps(timing,indent=2)+'\n')
 before=snapshot(D/'observation_before.bin');after=snapshot(D/'observation_after.bin');(C/'OBSERVATION_BEFORE.json').write_text(json.dumps(before,indent=2)+'\n');(C/'OBSERVATION_AFTER.json').write_text(json.dumps(after,indent=2)+'\n')
 assert a['passed'] and not a['error'] and len(a['points'])==400 and all(p['complete'] and not p['error'] for p in a['points'])
 assert c['success'] and not c['error'] and c['native_step_attempts']==2 and c['native_returns']==2 and len(c['points'])==2
 assert c['history_before']==[cycle,cycle] and c['history_after']==[cycle+1,cycle+1] and before['boundary']==c['history_before'] and after['boundary']==c['history_after']
 assert before['state']==v['actual_initial'] and before['state']['q']==initial['q'] and initial['observation_id']==before['observation_id'] and initial['simulation_time']==before['simulation_time']
 assert after['state']['C']==c['held_C'] and before['total_actual_substeps']==1000+2*cycle and after['total_actual_substeps']==1002+2*cycle
 assert all(p['passed'] and p['geometry_complete'] and p['independent_observer_guard'] and p['contacts']==0 and all(w==0 for w in p['warnings']) and p['C']==c['held_C'] for p in c['points'])
 assert timing['complete'] and timing['cycle']==cycle and all(z['measured'] and math.isfinite(z['seconds']) for z in timing['segments']) and timing['deadline_missed']==(timing['complete_cycle_seconds']>.004)
 assert timing['ledger']['completed_commits']==cycle+1 and timing['ledger']['forecast_budget_reservations']==2*(cycle+1) and timing['ledger']['step_budget_reservations']==2*(cycle+1)
 assert len(candidate['original_row_violations'])==14756 and max(candidate['original_row_violations'])<=1e-7 and candidate['forward_request_exists'] and candidate['raw_status']==1
 metrics={'cycle':cycle,'boundary_before':before['boundary'],'boundary_after':after['boundary'],'time_before':before['simulation_time'],'time_after':after['simulation_time'],'native_osqp_iterations':candidate['iterations'],'maximum_original_SI_violation':max(candidate['original_row_violations']),'max_affine_error':max(p['affine_error'] for p in a['points']),'max_joint_trust':max(p['joint_trust'] for p in a['points']),'min_true_clearance_m':min(p['min_true'] for p in a['points']),'min_cover_clearance_m':min(p['min_cover'] for p in a['points']),'min_sigma':min(p['sigma'] for p in a['points']),'max_predicted_acceleration':max(abs(x) for p in a['points'] for x in p['acceleration']),'max_predicted_jerk':max(abs(x) for p in a['points'] for x in p['jerk']),'max_actual_acceleration':max(abs(x) for p in c['points'] for x in p['acceleration']),'max_actual_jerk':max(abs(x) for p in c['points'] for x in p['jerk']),'candidate_value_facts':v['facts'],'task_progress':after['state']['s'],'timing':timing};cycles.append(metrics)
(P/'ACTUAL_DYNAMIC_SUMMARY.json').write_text(json.dumps({'entry':entry,'cycles':cycles,'scope':'one actual warm1000 and3 current reobserved beta0/smallalpha transactions; selected geometryQP1600 assistance rows present; no fulltask/stop/online/phase acceptance'},indent=2)+'\n')
assert entry['commits']==3 and entry['total_physical_step_attempts']==1006 and not entry['error'] and entry['session_termination_pass'] and entry['native_termination_pass']
print(json.dumps({'entry':entry,'cycles':cycles},indent=2))
