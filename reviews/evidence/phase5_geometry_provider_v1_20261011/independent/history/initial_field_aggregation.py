"""Saved provider26 CSV/raw-nominal arithmetic only. No Scene/FK/model/native calls."""
from pathlib import Path
import csv,json,hashlib,importlib.util,collections
import numpy as np
OUT=Path(__file__).resolve().parent
PACK=Path('/private/tmp/phase5_geometry_provider_checkpoint_v1_20261011')
UNIT=PACK/'actual-dell/nominal-geometry-provider-recorded-v4-20261011-attempt26';RUN=UNIT/'run-attempt1';BASE=RUN/'artifacts'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
SOURCE=Path('/private/tmp/root_independent_dynamic_actual_review_20261011/audit_dynamic_actual.py')
spec=importlib.util.spec_from_file_location('own_raw',SOURCE);raw=importlib.util.module_from_spec(spec);spec.loader.exec_module(raw)
assert sha(PACK/'READY.json')=='3617d73b1506469eddc31a381b555728dfbcada8c1665eab9030f1e51010a801'
manifest=json.loads((PACK/'READY.json').read_text())['files'];assert len(manifest)==152
for n,v in manifest.items():p=PACK/n;assert p.stat().st_size==v['bytes'] and sha(p)==v['sha256']
profile_snapshot=OUT/'profile_snapshot';pr=json.loads((OUT/'PROFILE_READY_READ.json').read_text())
for n,v in pr['files'].items():assert sha(profile_snapshot/n)==v['sha256'];assert (profile_snapshot/n).read_bytes()==(PACK/'phase5_geometry_provider_profile_v1_20261011'/n).read_bytes()
inputdata=json.loads((profile_snapshot/'ACTUAL_NOMINAL_Q400_X3.json').read_text());selected=list(csv.DictReader((BASE/'selected_geometry_rows.csv').open()));mins=list(csv.DictReader((BASE/'nominal_geometry_minima.csv').open()));fd=list(csv.DictReader((BASE/'selected_witness_regression.csv').open()));reg=list(csv.DictReader((BASE/'gradient_regression_summary.csv').open()));assert [len(selected),len(mins),len(fd),len(reg)]==[4800,1200,252,9]
# All numeric columns finite; only support/digest strings are nonnumeric.
for table,exclude in [(selected,{'nominal_digest','id'}),(mins,set()),(fd,{'id'}),(reg,set())]:
 for row in table:
  assert all(np.isfinite(float(v)) for k,v in row.items() if k not in exclude)
mi={(int(p['cycle']),int(p['sample'])):p for p in mins};groups=collections.defaultdict(list);smap={};nominal=[];splice_errors=[]
for p in selected:groups[int(p['cycle']),int(p['sample'])].append(p);smap[int(p['cycle']),int(p['sample']),p['id']]=p
true_min=cover_min=float('inf');cover_error=0.;witness_max=normal_max=0.
for cycle in range(3):
 record=inputdata['cycles'][cycle];actual=Path('/private/tmp/phase5_dynamic_session_checkpoint_v1_20261011/actual-dell/session-dynamic-three-cycle-v5-20261011-attempt20/run-attempt1/artifacts')/f'cycle-{cycle}'/'original_nominal.bin'
 assert actual.stat().st_size==record['nominal_file_bytes'] and sha(actual)==record['nominal_file_sha256'];n=raw.nominal(actual.read_bytes());nominal.append(n)
 assert n['tags'][2]==record['nominal_invocation_sha256'] and n['initial'].tobytes()==np.r_[record['actual_initial']['q'],record['actual_initial']['v'],record['actual_initial']['C'],record['actual_initial']['w'],record['actual_initial']['s'],record['actual_initial']['r']].astype('<f8').tobytes()
 # Independent lifted elimination only for the prospective SI splice contract.
 L=np.eye(630);E=np.zeros((630,160));dd=np.zeros(630);I=np.zeros((630,30));I[:30]=np.eye(30)
 for k,m in enumerate(n['maps']['cell']):rr=slice((k+1)*30,(k+2)*30);L[rr,k*30:(k+1)*30]=-m['cell_A'];E[rr,k*8:(k+1)*8]=m['cell_B'];dd[rr]=m['cell_d']
 solved=np.linalg.solve(L,np.c_[E,dd,I]);M=solved[:,:160].reshape(21,30,160);c=solved[:,160].reshape(21,30)+np.einsum('kij,j->ki',solved[:,161:].reshape(21,30,30),n['initial']);ubar=np.concatenate([u for m,u in n['controls']])
 for sample in range(400):
  source=record['samples'][sample];point=n['points'][sample];q=point['q'];qjs=np.asarray(source['q']);assert qjs.tobytes()==q.tobytes()==n['maps']['half'][sample]['state'][:7].tobytes()
  rows=groups[cycle,sample];minimum=mi[cycle,sample];assert len(rows)==4 and int(minimum['full_query_count'])==9035 and [p['id'].split('/')[0] for p in rows]==['true','true','cover','cover']
  for family in (rows[:2],rows[2:]):
   assert len({p['id'] for p in family})==2 and [(float(p['distance_m']),p['id']) for p in family]==sorted((float(p['distance_m']),p['id']) for p in family)
  assert float(rows[0]['distance_m'])==float(minimum['min_true_m']) and float(rows[2]['distance_m'])==float(minimum['min_cover_m'])
  true_min=min(true_min,float(minimum['min_true_m']));cover_min=min(cover_min,float(minimum['min_cover_m']));cover_error=max(cover_error,float(minimum['min_cover_m'])-float(minimum['min_tool_environment_true_m']));assert cover_error<=1e-7
  m=n['maps']['half'][sample];k=m['cell'];SM=m['cell_A']@M[k];SM[:,k*8:(k+1)*8]+=m['cell_B'];sc=m['cell_A']@c[k]+m['cell_d']
  for p in rows:
   assert (int(p['cell']),int(p['tick']),int(p['half']))==(point['cell'],point['cycle'],point['half']) and float(p['elapsed_s'])==point['time'] and p['nominal_digest']==n['tags'][2] and np.asarray([float(p[f'q{i}']) for i in range(7)]).tobytes()==q.tobytes()
   assert float(p['lower_m'])==.005 and float(p['upper_m'])==1e6
   normal=np.asarray([float(p['normal_'+x]) for x in ['x','y','z']]);wa=np.asarray([float(p['wa_'+x]) for x in ['x','y','z']]);wb=np.asarray([float(p['wb_'+x]) for x in ['x','y','z']]);distance=float(p['distance_m']);g=np.asarray([float(p[f'g{i}']) for i in range(7)])
   normal_max=max(normal_max,abs(np.linalg.norm(normal)-1));witness_max=max(witness_max,float(np.linalg.norm(wb-wa-distance*normal)));assert normal_max<=1e-6 and witness_max<=1e-6
   # Linearized distance in actual absolute-U coordinates; no new QP/solver.
   Arow=g@SM[:7];offset=distance+g@(sc[:7]-q);splice_errors.append(abs(Arow@ubar+offset-distance))
assert len(groups)==1200 and len(smap)==4800
fd_error=0.;smoothmax=0.;nonsmooth=0;intervalfail=0;witness_shift=normal_shift=0.;seen=set()
for p in fd:
 cycle,sample,j=int(p['cycle']),int(p['sample']),int(p['joint']);key=(cycle,sample,j,p['id']);assert key not in seen;seen.add(key);assert sample in (0,199,399) and 0<=j<7 and int(p['same_query_roster'])==1
 selectedrow=smap[cycle,sample,p['id']];d,m,pd=[float(p[x]) for x in ['base_d','minus_d','plus_d']];left,right=[float(p[x]) for x in ['left_fd','right_fd']];analytic=float(p['analytic_m_rad']);assert d==float(selectedrow['distance_m']) and analytic==float(selectedrow[f'g{j}'])
 fd_error=max(fd_error,abs(left-(d-m)/1e-6),abs(right-(pd-d)/1e-6))
 if p['id'].startswith('true/'):
  if abs(left-right)>1e-4:nonsmooth+=1
  else:smoothmax=max(smoothmax,abs(.5*(left+right)-analytic))
  if analytic<min(left,right)-1e-4 or analytic>max(left,right)+1e-4:intervalfail+=1
 witness_shift=max(witness_shift,float(p['witness_minus_base_norm']),float(p['witness_plus_base_norm']));normal_shift=max(normal_shift,float(p['normal_minus_base_norm']),float(p['normal_plus_base_norm']))
assert fd_error<=1e-12 and intervalfail==0 and len(seen)==252
assert {(int(p['cycle']),int(p['sample'])) for p in reg}=={(k,i) for k in range(3) for i in (0,199,399)}
for p in reg:assert int(p['true_interval_failures'])==0 and float(p['point_max_error'])<=1e-7 and float(p['cover_max_error'])<=1e-5 and float(p['true_smooth_max_error'])<=1e-4
# Completion aggregates are source-produced over fullqueries; recompute their saved9-row sums/maxima only.
metrics={}
for line in (BASE/'COMPLETION.txt').read_text().splitlines():
 if '=' not in line:continue
 for part in line.split(','):
  k,v=part.split('=',1);metrics[k]=v
assert metrics['success']==metrics['termination_verified']=='1' and metrics['error']==''
for name in ['point_components','cover_components','true_smooth','true_nonsmooth','true_interval_failures']:assert sum(int(p[name]) for p in reg)==int(metrics[name])
for name in ['point_max_error','cover_max_error','true_smooth_max_error']:assert max(float(p[name]) for p in reg)==float(metrics[name])
assert int(metrics['scene_attempts'])==int(metrics['scene_returns'])==1200+9*7*2==1326
assert int(metrics['primitive_attempts'])==1326*9035==11980410 and int(metrics['true_attempts'])==int(metrics['true_returns'])==1326*120 and int(metrics['cover_attempts'])==int(metrics['cover_returns'])==1326*8915
assert int(metrics['FK_attempts'])==int(metrics['FK_returns'])<=40000 and int(metrics['analytic_J_attempts'])==int(metrics['analytic_J_returns'])<=20000 and int(metrics['scene_attempts'])<=1400 and int(metrics['primitive_attempts'])<=20000000
assert all(metrics[k]=='0' for k in ['ModelF1_instances','MuJoCo_calls','physics_steps','controller_commits'])
plan=json.loads((UNIT/'active_run_plan.json').read_text());before=(RUN/'BEFORE_INPUT_IDENTITIES.json').read_bytes();after=(RUN/'AFTER_INPUT_IDENTITIES.json').read_bytes();assert before==after;actualpins=json.loads(before);assert len(actualpins)==len(plan['input_files'])==1704
for observed,expected in zip(actualpins,plan['input_files']):
 for k in ['requested_path','bytes','sha256']:assert observed[k]==expected[k]
record=json.loads((RUN/'BATCH_PREFIX.json').read_text());assert record['native_project_entry_dispatches']==1 and len(record['records'])==1 and record['records'][0]['exit']==0 and record['records'][0]['argv']==plan['compile_argv'][0]
producer=json.loads((UNIT/'profile-version1/PRODUCER.json').read_text());assert record['records'][0]['argv'][3]==producer['sha256'];assert (RUN/'BEFORE_READONLY_ROSTERS.json').read_bytes()==(RUN/'AFTER_READONLY_ROSTERS.json').read_bytes()
for n in ['src/counted_geometry.hpp','src/provider_probe.cpp','src/nominal_geometry_selection.hpp','src/upstream_geometry.hpp']:assert (UNIT/n).read_bytes()==(profile_snapshot/n).read_bytes()
result={'packet_payloads':152,'packet_bytes':sum(v['bytes'] for v in manifest.values()),'rows':4800,'poses':1200,'selectedFD_rows':252,'all9_aggregate_record_sums_maxima_match':True,'selected_witness_consistency_absmax_m':witness_max,'selected_normal_norm_error':normal_max,'selected_FD_arithmetic_error':fd_error,'selected_true_smooth_error_max':smoothmax,'selected_true_nonsmooth_components':nonsmooth,'selected_true_interval_failures':intervalfail,'selected_witness_displacement_max_m':witness_shift,'selected_normal_displacement_max':normal_shift,'prospective_SI_splice_nominal_reproduction_error_m':max(splice_errors),'min_true_m':true_min,'min_cover_m':cover_min,'common_set_cover_minus_true_max_m':cover_error,'counters':metrics,'recorded_beforeafter_pins':1704,'exact_single_dispatch_and_sourceprofile':True,'producer':producer,'limits':['Only savedselected252FD comparisons recomputed; no full33,012cover/7,549smooth rawgradient replay possible.','Sorting firstmin andselectedorder validated fromsavedrows; all9035global secondrank requires original runtime/source because rawfullroster notsaved.','No Scene/FK/Model/native/compiler/optimizer called. SIsplice is offline algebra only; no actual enlargedQP/candidate/execution certificate.','Samequery identity is not samewitness or smoothness proof; actualwitness/normal displacements retained.','Archivedq provenance is not currentowner/forecaststillActive/physicalgeometry safety.']}
for n,v in manifest.items():assert sha(PACK/n)==v['sha256']
(OUT/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
