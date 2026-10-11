"""Independent saved actual36 file algebra. No compiler/Model/FK/Scene/native/solver/SSH.
Stage1 saved SI, literal histories, own B residual, actual C metrics; stage2 full regeneration.
"""
from pathlib import Path
import sys,hashlib,json,importlib.util,math,csv
import numpy as np
sys.dont_write_bytecode=True
OUT=Path(__file__).resolve().parent
PACK=Path('/Users/uot/Documents/ChatGPT/ros/results/phase5-reference/nonzero-progress-actual-v1-20261011/runtime-import1')
BASE=PACK/'artifacts'
SOURCE=Path('/private/tmp/phase5_nonzero_progress_tail_source_review_v1_20261011')
PROFILE=Path('/private/tmp/phase5_nonzero_progress_tail_runtime_profile_v1_20261011')
HELPER=Path('/private/tmp/root_independent_geometry_qp_actual_review_20261011/audit_geometry_qp_actual.py')
PINS={}
def pin(p,h=None):
 b=p.read_bytes();s=hashlib.sha256(b).hexdigest();assert h is None or s==h;(PINS.__setitem__(str(p),{'bytes':len(b),'sha256':s}));return b
spec=importlib.util.spec_from_file_location('root_actual30_parser',HELPER);m=importlib.util.module_from_spec(spec);pin(HELPER,'b648463d205992e217480407e8b2a5e553ac0401137b3a1ce084f1bcc3597c5b');spec.loader.exec_module(m);m.pin=pin
R=m.R;ma=m.maxabs
ready=pin(PACK/'ROOT_READY.json','a8002776d4850dc1b87df9b2aa384d8ea23e5c0f1dd527881c394a25dfe031ec');roster=json.loads(ready)
for n,i in roster['files'].items():assert len(pin(PACK/n,i['sha256']))==i['bytes']
(OUT/'ACTUAL_RUNTIME_READY_SNAPSHOT.json').write_bytes(ready)
source_ready=pin(SOURCE/'READY.json','93448302a7db20487babd926f980257686278b750a13916d6d8fe804cebe3eb1');src=json.loads(source_ready)
for n,i in src['files'].items():assert len(pin(SOURCE/n,i['sha256']))==i['bytes']
(OUT/'SOURCE_READY_SNAPSHOT.json').write_bytes(source_ready)
profile=json.loads(pin(PROFILE/'profile-version1/active_input.json'));producer=json.loads(pin(PROFILE/'profile-version1/PRODUCER.json'))
consts=json.loads(pin(Path('/private/tmp/public_live_affine_v2_integrated_first_cycle_canonical_protocol_repair_v2_20261010/proposed-files/inputs/public_constants.json'),profile['constants']['sha256']))
task=json.loads(pin(Path('/private/tmp/public_live_affine_v2_integrated_first_cycle_canonical_protocol_repair_v2_20261010/proposed-files/inputs/inspection_curve.json'),profile['task_reference']['sha256']))
def reduction(b):
 r=R(b,'ORIGINAL_AND_NUMERICAL_PLANNING_TERMINAL_REDUCTION_V2');d={'policy':r.text(),'stage':r.text(),'valid':r.u()}
 def ids():return [r.signed() for _ in range(r.u())]
 for k,f in [('Z',r.mat),('p',r.vec),('E',r.mat),('rhs',r.vec),('planning_rhs',r.vec),('eq',ids),('rows',ids),('Hr',r.mat),('gr',r.vec),('Ar',r.mat),('lr',r.vec),('ur',r.vec),('D',r.vec),('Fr',r.mat),('seed',r.vec),('x',r.vec),('Y',r.vec),('R',r.vec),('Hs',r.mat),('gs',r.vec),('As',r.mat),('ls',r.vec),('us',r.vec),('Fs',r.mat),('solver_seed',r.vec)]:d[k]=f()
 d['tag']=r.text();d['flags']=[r.u() for _ in range(5)];d['rawx'],d['rawy']=r.vec(),r.vec();d['slots']=r.u();d['errors']=[r.d() for _ in range(5)];r.end();return d

def metrics(r):
 o={'before':[r.u(),r.u()],'success':r.u(),'error':r.text(),'points':[]}
 for _ in range(r.u()):
  p={'step':r.u(),'time':r.d(),'raw':r.u()};p['elapsed'],p['dt'],p['s'],p['r']=[r.d() for _ in range(4)]
  if p['raw']:
   for k in ['actual','desired']:p[k]=[r.nums(3),r.nums(9).reshape(3,3)]
  p['measured']=r.u()
  if p['measured']:p['translation'],p['rotation'],p['within']=r.d(),r.d(),r.u()
  p['passed'],p['stage'],p['error']=r.u(),r.text(),r.text();o['points'].append(p)
 o['scope']=r.text();return o

def guard(b):
 r=R(b,'EXPLICIT_OPTIMIZER_ALPHA_PROGRESS_JERK_AND_NUMERICAL_TAIL_V3');o={'caps':[r.d() for _ in range(6)],'base':r.u(),'cols':[r.u() for _ in range(r.u())],'R':r.vec(),'label':r.text(),'scope':r.text()};r.end();return o

root_before=m.snapshot(pin(BASE/'observation_before.bin'));previous=root_before;previousU=None;summary=[];actualrows=[];metricrows=[];commits=[];metric_records=[]
root_receipts=m.verify_receipts(BASE)
for cycle in range(3):
 cb=BASE/f'cycle-{cycle}';receipts=m.verify_receipts(cb);before=m.snapshot(pin(cb/'observation_before.bin'));after=m.snapshot(pin(cb/'observation_after.bin'))
 assert before['boundary']==[cycle,cycle] and before['time']==previous['time']
 for k in ['x','alpha','v','a','ib']:assert before[k].tobytes()==previous[k].tobytes(),k
 assert before['b']==previous['b']
 n=m.nominal(pin(cb/'original_nominal.bin'));q=m.inline_full(pin(cb/'inline_qp.bin'));v=m.candidate_value(pin(cb/'candidate_value.bin'));c=m.candidate(pin(cb/'candidate.bin'));red=reduction(pin(cb/'qp_equality_reduction.bin'));gd=guard(pin(cb/'planning_guard.bin'));B=m.validation(pin(cb/'candidate_validation.bin'));iv=m.initial_validation(pin(cb/'validation_initial.bin'));timing=m.cycle_timing(pin(cb/'cycle_timing.bin'));hint=m.parse_current_hint(pin(cb/'current_numeric_hint.bin'))
 assert n['identities'][0]==producer and n['identities'][1:]==[profile[k] for k in ['xml','constants','expected_metadata']]
 assert n['deps']==profile['dependencies'] and n['libs']==profile['loaded_libraries']
 assert n['initial'].tobytes()==before['x'].tobytes() and n['alpha'].tobytes()==before['alpha'].tobytes() and n['b']==before['b']
 assert n['bound']==n['success']==n['final_available']==n['extension']==1 and n['uncertified']==-1 and not n['error'] and not n['extension_error']
 assert c['flags']==[0,1,1,0,1,0,1] and c['request_present']==1 and len(c['rowviol'])==14756
 U=c['U'];assert U.shape==(160,) and np.isfinite(U).all();Ubar=np.concatenate([a for _,a in n['controls']])
 m.compare({},'fresh_controls_only_shift',Ubar,np.zeros(160) if cycle==0 else m.shifted_controls(previousU,n['mesh']),1e-15,1e-13)
 assert v['initial'].tobytes()==c['request_x'].tobytes()==before['x'].tobytes() and c['request_ids'][:2]==before['ids'] and c['request_ids'][2]==n['tags'][2]
 assert v['facts']==([1,1,1] if cycle==0 else [0,0,1]) and v['metadata_present']==int(cycle==0) and v['nomdigest']==n['tags'][2] and v['success']==v['final_available']==1 and not v['error'] and not v['transport']
 assert len(v['points'])==len(n['maps']['half'])==400 and len(v['cycles'])==200 and len(v['cells'])==20
 for k,(_,u) in enumerate(v['controls']):assert u.tobytes()==U[k*8:k*8+8].tobytes()==c['request_controls'][k].tobytes()
 vio=np.maximum.reduce([q['l']-q['A']@U,q['A']@U-q['u'],np.zeros(14756)]);assert vio.max()<=1e-7;m.compare({},'saved_full_original_SI',vio,c['rowviol'],2e-13,1e-10)
 m.compare({},'U_reconstruction',U,red['p']+red['Z']@(red['D']*red['x']),2e-15,1e-12)
 assert red['Z'].shape==(160,144) and red['x'].shape==(144,) and red['planning_rhs'].shape==(16,)
 diff=red['planning_rhs']-red['rhs'];expected_rhs=red['rhs'].copy();expected_rhs[15]+=1e-13;assert np.count_nonzero(diff)==1 and red['planning_rhs'].tobytes()==expected_rhs.tobytes()
 assert ma(red['E']@red['p']-red['rhs'])<=1e-12 and ma(red['E']@red['Z'])<=1e-12
 history=m.rounded_history(before['x'],before['alpha'],before['b'],U,n['mesh'],q['labels'],q['l'],q['u']);assert history['cycles']==200 and not history['failures']
 for k in range(5):assert c['preview_joint'][k].tobytes()==history['first'][k].tobytes()
 assert c['preview_progress']==[history['first'][5],history['first'][6],history['first'][7],history['first'][8]]
 assert gd['caps']==[.000999,.001,4.999,4.9995,before['b'],1e-13]
 assert ma(U.reshape(20,8)[:,:7])<=.001 and max(abs(np.diff(np.r_[before['b'],U[7::8]])/.004))<=4.9995
 assert hint['present']==hint['complete']==1 and not hint['error'] and hint['x'].tobytes()==red['solver_seed'].tobytes()
 stat=ma(red['Hs']@hint['x']+red['gs']+red['As'].T@hint['y']);assert stat<=1e-10
 # Own global B deviation is propagated across cells, never reset to actual trial origins.
 assert B['attempted']==B['passed']==1 and len(B['points'])==400 and not B['error'];assert iv['q'].tobytes()==before['x'][:7].tobytes() and iv['ids']==before['ids'] and iv['time']==before['time'] and iv['complete']==1
 m.compare({},'initial_sigma',iv['sigma'],np.linalg.svd(iv['J'],compute_uv=False)[-1],1e-13,1e-12)
 delta=np.zeros(30);C=before['x'][14:21].copy();w=before['x'][21:28].copy();s,r0=before['x'][28:];pq=before['x'][:7].copy();pv=before['x'][7:14].copy();pa=before['a'].copy();clear=min(iv['true'],iv['cover']);sig=iv['sigma'];idx=0;maxaff=maxtrust=maxint=0.;brows=[]
 for k,num in enumerate(n['mesh']):
  cu=U[k*8:k*8+8];du=cu-n['controls'][k][1];os,orr=s,r0
  for tick in range(num):
   w=w+.004*cu[:7];C=C+.004*w;s,r0=s+.004*r0+.5*.004*.004*cu[7],r0+.004*cu[7]
   for half in [1,2]:
    point=v['points'][idx];mp=n['maps']['half'][idx];bp=B['points'][idx];dt=.004*tick+.002*half
    assert point['s']==os+dt*orr+.5*dt*dt*cu[7] and point['r']==orr+dt*cu[7] and 0<=point['s']<=1 and 0<=point['r']<=.2
    assert point['C'].tobytes()==C.tobytes() and point['w'].tobytes()==w.tobytes() and (point['cell'],point['cycle'],point['half'])==(k,tick+1,half)
    z=np.r_[point['q'],point['v'],point['C'],point['w'],point['s'],point['r']];lin=mp['state']+mp['cell_A']@delta+mp['cell_B']@du;res=z-lin;aff=ma(res);trust=ma(point['q']-mp['state'][:7]);aa=(point['v']-pv)/.002;jj=(aa-pa)/.002
    assert aa.tobytes()==bp['a'].tobytes() and jj.tobytes()==bp['j'].tobytes() and ma(aa)<=5 and ma(jj)<=500
    assert aff<=1e-6 and trust<=.002 and abs(aff-bp['affine_error'])<2e-13 and abs(trust-bp['trust'])<2e-13 and bp['complete']==1 and not bp['error'] and bp['queries']==9035
    travel=float(abs(point['q']-pq).sum());gl=min(clear,bp['true'],bp['cover'])-4*travel-1e-6;sl=min(sig,bp['sigma'])-32*travel;assert gl>=.005 and sl>=1e-6
    maxint=max(maxint,abs(gl-bp['geometry_lower']),abs(sl-bp['sigma_lower']));maxaff=max(maxaff,aff);maxtrust=max(maxtrust,trust)
    assert ma(point['q']-(pq+.002*point['v']))<=1e-12 and abs(point['time']-.002*(idx+1))<1e-10 and point['control_clips']==point['force_clips']==0
    brows.append([idx,k,tick+1,half,point['time']]+z.tolist()+lin.tolist()+res.tolist()+aa.tolist()+jj.tolist()+[aff,trust,bp['true'],bp['cover'],bp['sigma'],gl,sl,bp['queries']])
    pq,pv,pa,clear,sig=point['q'],point['v'],aa,min(bp['true'],bp['cover']),bp['sigma'];idx+=1
  m.compare({},'cell_progress_recurrence',v['cells'][k][28:],np.array([s,r0]),2e-16,1e-12)
  delta=n['maps']['cell'][k]['cell_A']@delta+n['maps']['cell'][k]['cell_B']@du
 assert idx==400 and maxint<1e-11 and v['final'].tobytes()==v['cells'][-1].tobytes()
 names=[f'{k}{j}' for k in ['q','v','C','w'] for j in range(7)]+['s','r'];header=['sample','cell','cycle','half','elapsed']+[pre+a for pre in ['value_','global_affine_','residual_'] for a in names]+[f'predicted_{k}{j}' for k in ['a','jerk'] for j in range(7)]+['max30','jointtrust','true_m','cover_m','sigma','geometry_interval_m','sigma_interval','queries']
 with (OUT/f'cycle_{cycle}_independent_value400.csv').open('w',newline='') as f:wr=csv.writer(f);wr.writerow(header);wr.writerows(brows)
 assert (OUT/f'cycle_{cycle}_independent_value400.csv').stat().st_size<1000000
 cs,ar,commit=m.verify_commit(cb,before,after,v,iv,c,cycle);actualrows.extend(ar);commits.append(commit)
 assert after['x'][28]==c['preview_progress'][0] and after['x'][29]==c['preview_progress'][1] and after['b']==c['preview_progress'][2]
 tr=R(pin(cb/'actual_task_errors.bin'),'ACTUAL_WORLD_TCP_TASK_ERROR_TWO_PHYSICAL_HALVES_V1');te=metrics(tr);tr.end();metric_records.append(te);assert te['before']==[cycle,cycle] and te['success']==1 and not te['error'] and len(te['points'])==2
 me=0.
 for i,p in enumerate(te['points']):
  cp=commit['points'][i];tau=.002*(i+1);ss=before['x'][28]+tau*before['x'][29]+.5*tau*tau*c['preview_progress'][2];rr=before['x'][29]+tau*c['preview_progress'][2]
  assert p['raw']==p['measured']==p['passed']==p['within']==1 and not p['error'] and p['time']==cp['time'] and p['dt']==tau and p['s']==ss and p['r']==rr and abs(p['elapsed']-tau)<1e-10
  desired=np.asarray(task['start'])+ss*(np.asarray(task['end'])-np.asarray(task['start']))+np.array([0,task['lateral_amplitude']*math.sin(2*math.pi*ss),task['vertical_amplitude']*math.sin(math.pi*ss)])
  me=max(me,ma(desired-p['desired'][0]));assert me<1e-15
  quat=np.asarray(task['quaternion_xyzw']);x,y,z,wq=quat/np.linalg.norm(quat);rot=np.array([[1-2*(y*y+z*z),2*(x*y-z*wq),2*(x*z+y*wq)],[2*(x*y+z*wq),1-2*(x*x+z*z),2*(y*z-x*wq)],[2*(x*z-y*wq),2*(y*z+x*wq),1-2*(x*x+y*y)]]);assert ma(rot-p['desired'][1])<1e-15
  for pose in [p['actual'],p['desired']]:assert np.isfinite(np.r_[pose[0],pose[1].ravel()]).all() and ma(pose[1].T@pose[1]-np.eye(3))<=1e-8 and abs(np.linalg.det(pose[1])-1)<=1e-8
  rel=p['actual'][1].T@p['desired'][1];angle=math.atan2(float(np.linalg.norm(rel-rel.T)/(2*math.sqrt(2))),float(np.clip((np.trace(rel)-1)/2,-1,1)));trans=float(np.linalg.norm(p['desired'][0]-p['actual'][0]));assert abs(angle-p['rotation'])<2e-13 and abs(trans-p['translation'])<2e-15 and trans<=.01 and angle<=.05
  metricrows.append([cycle,i+1,p['time'],ss,rr]+p['actual'][0].tolist()+p['desired'][0].tolist()+[trans,angle]+p['actual'][1].ravel().tolist()+p['desired'][1].ravel().tolist())
 summary.append({'cycle':cycle,'native':{'flags':c['flags'],'setup':c['metrics'][3],'solve':c['metrics'][4]},'SI_max':float(vio.max()),'full_SI_rows':len(vio),'free_columns':len(red['x']),'original_E_offset_error':ma(red['E']@red['p']-red['rhs']),'planning_E_offset_error':ma(red['E']@red['p']-red['planning_rhs']),'strict200_and400_pass':True,'terminal_r':history['r'],'exact_tail':c['exact_tail'],'initial_s_r_b':before['x'][28:].tolist()+[before['b']],'accepted_s_r_b':after['x'][28:].tolist()+[after['b']],'accepted_w':after['x'][21:28].tolist(),'B_max30':maxaff,'B_trust':maxtrust,'B_interval_error_all400':maxint,'C':cs,'actual_task_path_formula_error':me,'timing':timing,'hint_stationarity':stat,'binary_receipts':receipts})
 previous,previousU=after,U
entry=R(pin(BASE/'entry_completion.bin'),'ACTIVE_SESSION_FINAL_SCOPE_AND_TIMING');stage,error=entry.text(),entry.text();same,sessionpass=entry.u(),entry.u();sf=entry.text();simpass=entry.u();simf=entry.text();wall=entry.d();steps,commitnum=entry.u(),entry.u();entry.end();assert error==sf==simf=='' and sessionpass==simpass==1 and steps==1006 and commitnum==3
beforepins=pin(PACK/'BEFORE_INPUT_IDENTITIES.json');assert beforepins==pin(PACK/'AFTER_INPUT_IDENTITIES.json');pins=json.loads(beforepins)
batch=json.loads(pin(PACK/'BATCH_PREFIX.json'));assert batch['native_project_entry_dispatches']==1 and len(batch['records'])==1 and batch['records'][0]['exit']==0
r=R(pin(BASE/'retained_commit_history.bin'),'ALL_ACTUAL_COMMIT_OUTCOMES_AND_TASK_ERRORS_V2');assert r.u()==3
for c in commits:
 saved=m.commit_record(r);assert saved['before']==c['before'] and saved['after']==c['after'] and saved['flags']==c['flags']
assert r.u()==3
for te in metric_records:
 mt=metrics(r);assert mt['before']==te['before'] and mt['success']==te['success']
r.text();r.end()
with (OUT/'actual6_steps.csv').open('w',newline='') as f:w=csv.writer(f);w.writerow(['cycle','half','actual_time']+[f'{k}{j}' for k in ['q','v','C','actual_a','actual_jerk'] for j in range(7)]+['true_m','cover_m','sigma','geometry_interval_m','sigma_interval','contacts','queries']);w.writerows(actualrows)
with (OUT/'actual6_task_pose_errors.csv').open('w',newline='') as f:w=csv.writer(f);w.writerow(['cycle','half','actual_time','logical_s','logical_r']+[f'{k}{j}' for k in ['actual_xyz','desired_xyz'] for j in range(3)]+['translation_m','SO3_angle_rad']+[f'{k}{j}' for k in ['actual_R','desired_R'] for j in range(9)]);w.writerows(metricrows)
for path,i in PINS.items():b=Path(path).read_bytes();assert len(b)==i['bytes'] and hashlib.sha256(b).hexdigest()==i['sha256']
result={'schema':'ROOT_ACTUAL36_TARGETED_CHAIN_STAGE1_V1','actual_runtime_sha256':hashlib.sha256(ready).hexdigest(),'payloads':len(roster['files']),'bytes':sum(x['bytes'] for x in roster['files'].values()),'cycles':summary,'entry':{'stage':stage,'wall':wall,'actual_substeps':steps,'task_substeps':6,'commits':commitnum,'termination':[sessionpass,simpass]},'pin_records':len(pins),'pin_unique':len({x['requested_path'] for x in pins}),'task_translation_max_m':max(x[11] for x in metricrows),'task_SO3_max_rad':max(x[12] for x in metricrows),'root_receipts':root_receipts,'input_pins':PINS,'scope':'Three actual offline nonzero-progress/smallalpha transactions; stage1 saved SI/history/B/C/task metric checks, full regeneration stage2 pending. No model/native/optimizer/FK/Scene/compiler calls, no exactE0/physicalstop/task/realtime/Phase5 acceptance.'}
(OUT/'STAGE1_RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['input_pins','cycles']}));print(json.dumps([{k:x[k] for k in ['cycle','SI_max','B_max30','initial_s_r_b','accepted_s_r_b','terminal_r']} for x in summary]))
