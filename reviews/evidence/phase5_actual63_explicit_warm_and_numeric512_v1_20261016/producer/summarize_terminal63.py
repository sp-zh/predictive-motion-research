from pathlib import Path
import sys,struct,json,hashlib,os,math,resource,time
sys.dont_write_bytecode=True;sys.path.insert(0,'/private/tmp/phase5_current_braking_nominal63_source_v1_20261016');sys.path.insert(0,'/private/tmp');sys.path.insert(0,'/private/tmp/phase5_exact_cycle_endpoint61_source_v1_20261016')
import importlib.util
_spec=importlib.util.spec_from_file_location('strictcodec58','/Users/uot/Documents/ChatGPT/ros/tools/cold_storage_verification_v1/strict_codec_reader.py');_mod=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_mod);verify_artifact=_mod.verify_artifact;manifest_entries=_mod.manifest_entries
from bounded_derived_bytes53_v1 import bounded_write_bytes
assert hashlib.sha256(Path('/Users/uot/Documents/ChatGPT/ros/tools/cold_storage_verification_v1/strict_codec_reader.py').read_bytes()).hexdigest()=='c32178a23e5254f44ee21a62be655af3236c708c02bb061564c3d8b0b8cb468a'
resource.setrlimit(resource.RLIMIT_CPU,(120,120))
P=Path('/private/tmp/phase5_controlled_stop_explicit_warm_nominal_terminal63_v1_20261016')
UNIT=next((P/'actual-dell').iterdir());BASE=UNIT/'run-attempt1/artifacts'
OUT=P/'derived';OUT.mkdir(exist_ok=False);os.environ['P5_DERIVED53_ROOT']=str(P)
ready=json.loads((P/'READY.json').read_text());roster={x['path']:x for x in ready['payload']};pins={}
def raw(p):
 p=Path(p);x=roster[str(p.relative_to(P))];b=p.read_bytes();assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256'];pins[str(p.relative_to(P))]=x
 if p.suffix=='.bin':
  manifest=p.parent/'MANIFEST.yaml';m=roster[str(manifest.relative_to(P))];assert manifest.stat().st_size==m['bytes'] and hashlib.sha256(manifest.read_bytes()).hexdigest()==m['sha256'];return verify_artifact(p,True,True)[0]
 return b
class R:
 def __init__(self,p,role):self.b=raw(p);self.i=0;assert self.text()=='P5_ACTIVE_SESSION_LOSSLESS_V1' and self.text()==role
 def u(self):assert self.i+8<=len(self.b);x=struct.unpack_from('<Q',self.b,self.i)[0];self.i+=8;return x
 def d(self):assert self.i+8<=len(self.b);x=struct.unpack_from('<d',self.b,self.i)[0];self.i+=8;return x
 def text(self):n=self.u();assert n<=len(self.b)-self.i;x=self.b[self.i:self.i+n].decode();self.i+=n;return x
 def vec(self):n=self.u();assert n<=2000000;return [self.d()for _ in range(n)]
 def end(self):assert self.i==len(self.b)
q=R(BASE/'entry_completion.bin','ACTIVE_SESSION_FINAL_SCOPE_AND_TIMING')
entry={'stage':q.text(),'error':q.text(),'boundary_unchanged':q.u(),'session_termination':q.u(),'session_error':q.text(),'native_termination':q.u(),'native_error':q.text(),'wall_seconds':q.d(),'physical_step_attempts':q.u(),'commits':q.u()};q.end()
whole=[]
for p in sorted(BASE.glob('cycle-*/whole_current_cycle.bin'),key=lambda p:int(p.parent.name.split('-')[1])):
 # Role may vary only by preserved source version: assert producer declared role.
 role=manifest_entries(p.parent/'MANIFEST.yaml')[p.name].get('role')
 # Reader receipt role text is parsed independently from header here.
 b=raw(p);n=struct.unpack_from('<Q',b,0)[0];offset=8+n;n=struct.unpack_from('<Q',b,offset)[0];role=b[offset+8:offset+8+n].decode()
 q=R(p,role);z={'cycle':q.u(),'trials_entered':q.u(),'physical_complete':q.u(),'wall':q.d(),'deadline_miss':q.u(),'last_B_error':q.text(),'fatal_error':q.text(),'trials_total':q.u(),'forecasts':q.u(),'steps':q.u(),'commits':q.u(),'scope':q.text()};q.end();whole.append(z)
q=R(BASE/'actual_stop_dwell.bin','ACTUAL_PHYSICAL_V_A_ACCEPTED_HISTORY_STOP_DWELL_V2');stop={k:q.u()for k in ['passed','failed','consecutive','required_halves','maximum_halves']};spec=[q.d()for _ in range(8)];assert spec==[1e-4,1e-3,1e-6,1e-4,1e-6,1e-4,1e-6,1e-6] and stop['required_halves']==50
stoprows=[];consecutive=0;anchor=None
for _ in range(q.u()):
 z={'global_half':q.u(),'time':q.d()}
 for k in ['v','a','C','w','alpha']:z[k]=[q.d()for _ in range(7)]
 for k in ['s','r','b']:z[k]=q.d()
 z.update({k:q.u()for k in ['guards','below','hold','consecutive']});z['C_drift']=q.d();z['s_drift']=q.d()
 assert all(math.isfinite(x)for k in ['v','a','C','w','alpha']for x in z[k])
 below=all(max(map(abs,z[k]))<=bound for k,bound in [('v',spec[0]),('a',spec[1]),('w',spec[2]),('alpha',spec[3])]) and z['r']<=spec[4] and abs(z['b'])<=spec[5]
 assert bool(z['below'])==below
 if below:
  if anchor is None:anchor=z
  cd=max(abs(x-y)for x,y in zip(z['C'],anchor['C']));sd=abs(z['s']-anchor['s']);hold=cd<=spec[6]and sd<=spec[7]
  assert cd==z['C_drift'] and sd==z['s_drift'] and bool(z['hold'])==hold
  if hold:consecutive+=1
  else:consecutive=0;anchor=None
 else:consecutive=0;anchor=None;assert not z['hold']
 assert consecutive==z['consecutive'] and z['guards'];stoprows.append(z)
stop['scope']=q.text();q.end();assert stop['consecutive']==consecutive and stop['passed']==(not stop['failed']and consecutive>=50)
traces=[]
for p in sorted(BASE.glob('cycle-*/trial-*/working_face_basis_trace.bin'),key=lambda p:(int(p.parent.parent.name.split('-')[1]),int(p.parent.name.split('-')[1]))):
 q=R(p,'NUMERICAL_WORKING_FACE_BASIS_FULL_ENDPOINT_AND_BOUNDED_KKT_REFINEMENT_TRACE_V2');z={'cycle':q.u(),'trial':q.u(),'available':q.u(),'basis':q.u()}
 for _ in range(z['basis']):
  for j in range(8):q.u()
  q.d();q.text()
  for j in range(2):
   for _ in range(q.u()):q.u()
 z['refinement_count']=q.u();assert z['refinement_count']<=1536;records=[]
 for _ in range(z['refinement_count']):
  e=dict(zip(['iteration','step','rank','dimension','reason','before_available','correction_available','after_available','accepted'],[q.u()for j in range(9)]));e.update(zip(['before','after','correction_inf','solution_inf','correction_cap','initial_double_residual'],[q.d()for j in range(6)]))
  assert e['iteration']<512 and e['step']<3 and 0<e['rank']<=e['dimension']<=288 and e['reason']<=7
  assert all(e[k]in[0,1]for k in ['before_available','correction_available','after_available','accepted'])
  assert all(math.isfinite(e[k])and e[k]>=0 for k in ['before','after','correction_inf','solution_inf','correction_cap','initial_double_residual'])
  assert e['initial_double_residual']<=1e-10 and e['correction_cap']==max(1.,e['solution_inf'])
  for flag,value in [('before_available','before'),('correction_available','correction_inf'),('after_available','after')]:assert e[flag]or e[value]==0
  assert bool(e['accepted'])==(e['reason']==0)
  if e['accepted']:assert e['before_available']and e['correction_available']and e['after_available']and e['after']<e['before']and e['correction_inf']<=e['correction_cap']
  if records and records[-1]['iteration']==e['iteration']:
   last=records[-1];assert last['accepted']and e['step']==last['step']+1 and e['rank']==last['rank']and e['dimension']==last['dimension']and e['initial_double_residual']==last['initial_double_residual']and e['before_available']and e['before']==last['after']
  else:assert e['step']==0 and(not records or e['iteration']>records[-1]['iteration'])
  records.append(e)
 z['refinement_records']=records;z['refinements_accepted']=sum(e['accepted']for e in records)
 z['endpoints']=q.u();assert z['endpoints']<=16384;h=hashlib.sha256()
 for _ in range(z['endpoints']):
  i=q.u();r=q.u();v=[q.d()for j in range(6)];assert i<512 and r<20000 and all(math.isfinite(x)for x in v)and v[3]<=v[4] and v[5]==max(0.,v[3]-v[2],v[2]-v[4]) and v[5]<=1e-12;h.update(struct.pack('<QQ6d',i,r,*v))
 z['full_ordered_event64_sha256']=h.hexdigest();q.text();q.end();traces.append(z)
# Explicit V4 role; immutable V2 parser remains unchanged.
from initializer_codec58_v4 import initializer_v4
sys.path.insert(0,'/private/tmp/root_independent_controlled_stop52_review_20261012')
from compressed_evidence50_v5 import EvidenceReadSet,load_math_definitions
rs56=EvidenceReadSet('/Users/uot/Documents/ChatGPT/ros/tools/cold_storage_verification_v1/strict_codec_reader.py');ref56=Path('/private/tmp/root_independent_controlled_stop52_review_20261012/reference_source');n56=load_math_definitions(rs56,ref56/'audit_geometry_qp_actual.py',ref56/'audit_actual39.py');initializers=[]
for file in sorted(BASE.glob('cycle-*/trial-*/numeric_feasible_initializer.bin')):
 red=n56['reduction'](raw(file.parent/'qp_equality_reduction.bin'));z=initializer_v4(raw(file),n56['R'],len(red['ls']));z['context_path']=str(file.relative_to(BASE));z['seed']=z['seed'].tolist();z['bounds_shape']=list(z.pop('bounds').shape)
 for c in z['corrections']:c['delta']=c['delta'].tolist()
 initializers.append(z)
from merged_cycle_diagnostics61_v3 import merged61
leaving_contexts=[]
for file in sorted(BASE.glob('cycle-*/trial-*/hint_kkt_rank_events.bin')):
 red=n56['reduction'](raw(file.parent/'qp_equality_reduction.bin'));hint=n56['parse_current_hint'](raw(file.parent/'current_numeric_hint.bin'));z=merged61(raw(file),n56['R'],len(red['ls']),hint.get('events'),len(red['gs']));z['context_path']=str(file.relative_to(BASE));leaving_contexts.append(z)
from braking_nominal_codec63_v1 import braking63
nominal_contexts=[]
for file in sorted(BASE.glob('cycle-*/trial-*/stop_objective_mode.bin')):
 e=manifest_entries(file.parent/'MANIFEST.yaml')[file.name]
 prefix_role,_=verify_artifact(file,True,False)
 rn=struct.unpack_from('<Q',prefix_role,0)[0];ro=8+rn;rn=struct.unpack_from('<Q',prefix_role,ro)[0];decoded_role=prefix_role[ro+8:ro+8+rn].decode()
 if decoded_role=='STOP_COST_CURRENT_HISTORY_ANALYTIC_AND_EXPLICIT_WARM_NOMINAL_V4':
  if e['complete']:z=braking63(raw(file),n56['R'],True)
  else:
   stored=file.read_bytes();ident=roster[str(file.relative_to(P))];assert len(stored)==ident['bytes']and hashlib.sha256(stored).hexdigest()==ident['sha256'];prefix,prefixfacts=verify_artifact(file,True,False);z=braking63(prefix,n56['R'],False);z['prefix_codec_receipt']=prefixfacts
  z['context_path']=str(file.relative_to(BASE));nominal_contexts.append(z)
# Only selected source-complete stored binary payloads receive independent full codec readback.
codec=[]
for p in sorted(BASE.rglob('*.bin')):
 e=manifest_entries(p.parent/'MANIFEST.yaml')[p.name]
 if e['complete']:codec.append(verify_artifact(p,False,True))
 else:codec.append({'file':str(p),'source_complete':False,'scope':'incomplete retained, no math inference'})
trend=[]
if stoprows:
 first=stoprows[0]
 for cy in sorted({(z['global_half']-1001)//2 for z in stoprows}):
  rows=[z for z in stoprows if (z['global_half']-1001)//2==cy]
  trend.append({'cycle':cy,'first_time':rows[0]['time'],'last_time':rows[-1]['time'],'actual_velocity_inf_max':max(max(map(abs,z['v']))for z in rows),'actual_acceleration_inf_max':max(max(map(abs,z['a']))for z in rows),'accepted_w_inf_max':max(max(map(abs,z['w']))for z in rows),'accepted_alpha_inf_max':max(max(map(abs,z['alpha']))for z in rows),'accepted_r_max':max(z['r']for z in rows),'accepted_abs_b_max':max(abs(z['b'])for z in rows),'C_change_from_first_brake_record_inf_max':max(max(abs(x-y)for x,y in zip(z['C'],first['C']))for z in rows),'s_change_from_first_brake_record_abs_max':max(abs(z['s']-first['s'])for z in rows),'hold_monitor_drift_available_rows':sum(z['below']for z in rows),'stop_dwell_consecutive':rows[-1]['consecutive'],'drift_scope':'First-brake-record relative diagnostic changes, not the strict hold-anchor criterion. Monitor drift zeros when below=false are unavailable, not measured zero.'})
out={'reader_qualification':'Original selected parser expected role key in strict manifest parser, which intentionally omits role; KeyError before output. Fresh reader decodes exact raw role header; original empty derived directory retained. No capture/native repeated.','schema':'PRODUCER63_SELECTED_TERMINAL_LAST_CURRENT_STOP_REVIEW_V1','entry':entry,'whole_cycles':whole,'stop':stop,'stop_records':stoprows,'braking_actual_trend_by_cycle':trend,'trace_contexts':traces,'initializer_V4_contexts':initializers,'merged_hint_diagnostic_contexts':leaving_contexts,'current_braking_nominal_V4_contexts':nominal_contexts,'selected_context_endpoint_events':sum(x['endpoints']for x in traces),'selected_codec_binary_files':len(codec),'selected_complete_codec_files':sum(bool(x['source_complete'])for x in codec),'selected_stored_binary_bytes':sum(x.get('stored_bytes',0)for x in codec),'selected_raw_binary_bytes':sum(x.get('raw_bytes',0)for x in codec),'source_input_pins':pins,'phase5':'NOT_ACCEPTED','phase6':'NOT_STARTED','scope':'Only selected producer saved-data parsing: last-current full matrices/diagnostics, all completed commits/whole-cycle records and terminal stop. Uncopied earlier full trial data remain Dell only, no whole native codec/trace-event total assertion; original physical stop thresholds independently recomputed, original full endpoint scalar checks and full stored/raw SHA/CRC/EOF for source-complete files. Root full matrices/SI/B/C acceptance review separate; process or archive completion does not prove stop/full task/4ms success.'}
bounded_write_bytes(OUT/'SUMMARY63_SELECTED.json',(json.dumps(out,indent=2)+'\n').encode())
bounded_write_bytes(OUT/'CODEC63_SELECTED.json',(json.dumps(codec,indent=2)+'\n').encode())
print(json.dumps({k:out[k]for k in ['entry','stop','selected_context_endpoint_events','selected_codec_binary_files','selected_complete_codec_files','selected_stored_binary_bytes','selected_raw_binary_bytes']}))
