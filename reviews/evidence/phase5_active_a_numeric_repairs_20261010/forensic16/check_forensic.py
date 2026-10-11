"""Independent saved unsolved raw iterate diagnostics only; no model, solve or candidate."""
import hashlib,json,struct,time,csv
from pathlib import Path
import numpy as np
OUT=Path(__file__).resolve().parent
PACK=Path('/private/tmp/phase5_active_a_forensic_checkpoint_v3_20261010')
START_SOURCE=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(); t0=time.monotonic();pins={}
def pin(path,expected=None):
 b=path.read_bytes();h=hashlib.sha256(b).hexdigest()
 if expected:assert h==expected,(str(path),h,expected)
 pins[str(path)]={'bytes':len(b),'sha256':h};return b
ready=pin(PACK/'ACTIVE_A_FORENSIC_CHECKPOINT_READY.json','37ec40acd1c7beb5cc2a5cd77c3c41847e7be2a749c79f7513cb688049013d72')
manifest=json.loads(ready)['files']
def payload(rel):
 v=manifest[rel];b=pin(PACK/rel,v['sha256']);assert len(b)==v['bytes'];return b
ids=json.loads(payload('FORENSIC_NATIVE_ARTIFACT_IDENTITIES.json'))
base='actual-dell/repair16/run-attempt1/artifacts/'
for name,v in ids.items():
 b=payload(base+name);assert len(b)==v['bytes'] and hashlib.sha256(b).hexdigest()==v['sha256']
assert len(ids)==11
sm=payload('source-review-frozen/SOURCE_MANIFEST.json');source_manifest=json.loads(sm)
for name,v in source_manifest.items():
 b=payload('source-review-frozen/'+name);assert hashlib.sha256(b).hexdigest()==v['sha256'] and len(b)==v['bytes']
class Reader:
 def __init__(self,b,role):
  self.b=b;self.i=0;assert self.text()=='P5_ACTIVE_SESSION_LOSSLESS_V1';assert self.text()==role
 def u(self):
  assert self.i+8<=len(self.b);v=struct.unpack_from('<Q',self.b,self.i)[0];self.i+=8;return v
 def signed(self):
  v=self.u();return v-(1<<64) if v>=(1<<63) else v
 def d(self):
  assert self.i+8<=len(self.b);v=struct.unpack_from('<d',self.b,self.i)[0];self.i+=8;return v
 def text(self):
  n=self.u();assert n<=len(self.b)-self.i;v=self.b[self.i:self.i+n].decode();self.i+=n;return v
 def nums(self,n):
  assert n<=10_000_000 and self.i+8*n<=len(self.b)
  v=np.frombuffer(self.b,dtype='<f8',count=n,offset=self.i).copy();self.i+=8*n;return v
 def vec(self):return self.nums(self.u())
 def mat(self):r,c=self.u(),self.u();return self.nums(r*c).reshape(r,c)
 def ids(self):return [self.u() for _ in range(self.u())]
 def end(self):assert self.i==len(self.b),(self.i,len(self.b))
receipts={};manifest_fields={};current=None
def scalar(s):
 if s in ('true','false'):return s=='true'
 if s.isdecimal():return int(s)
 if s.startswith('"'):return json.loads(s)
 return s
for line in payload(base+'MANIFEST.yaml').decode().splitlines():
 if line=='files:':continue
 if line.startswith('  - file: '):
  name=scalar(line[len('  - file: '):]);assert name not in receipts;current={};receipts[name]=current
 elif line.startswith('    '):
  key,value=line[4:].split(': ',1);assert key not in current;current[key]=scalar(value)
 else:
  key,value=line.split(': ',1);assert key not in manifest_fields;manifest_fields[key]=scalar(value)
assert manifest_fields['schema']=='ACTIVE_SESSION_EVIDENCE_MANIFEST_V1' and manifest_fields['execution_permission'] is False
assert set(receipts)==set(ids)-{'MANIFEST.yaml'} and sum(x['bytes'] for x in receipts.values())==manifest_fields['output_bytes']
for name,v in receipts.items():
 assert v['created'] is True and v['complete'] is True and v['hash_valid'] is True and v['error']==''
 assert v['bytes']==ids[name]['bytes'] and v['sha256']==ids[name]['sha256']
 Reader(payload(base+name),v['role']) # All original binary headers/role tags.
boot=Reader(payload(base+'bootstrap.bin'),'ACTUAL_DIRECT_SESSION_API_ENTRIES');bootstrap=[boot.u() for _ in range(9)];boot.end();assert bootstrap[-2:]==[0,0]
def snapshot(name):
 r=Reader(payload(base+name),'ACTUAL_NATIVE_SESSION_SNAPSHOT');identities=[r.text(),r.text()];boundary=[r.u(),r.u()];complete=r.u();stage,failure=r.text(),r.text();counts=[r.u() for _ in range(3)];simtime,age=r.d(),r.d();contactfree=r.u();state=r.nums(30);alpha=r.nums(7);b=r.d();integrationbefore,integrationafter=r.vec(),r.vec();r.end()
 return {'boundary':boundary,'complete':complete,'stage':stage,'failure':failure,'simtime':simtime,'state':state,'alpha':alpha,'b':b,'contactfree':contactfree,'integrationbefore':integrationbefore,'integrationafter':integrationafter}
before,after=snapshot('observation_before.bin'),snapshot('observation_after.bin')
assert before['boundary']==after['boundary']==[0,0] and before['simtime']==after['simtime']==0 and before['contactfree']==after['contactfree']==1
assert np.array_equal(before['state'],after['state']) and np.array_equal(before['integrationbefore'],after['integrationbefore']) and np.array_equal(before['integrationafter'],after['integrationafter'])
def inline(b):
 r=Reader(b,'INLINE_QP_COMPLETE_OR_RETAINED_PREFIX');stage,error=r.text(),r.text();info=[r.u() for _ in range(7)];r.text();r.u()
 for _ in range(3):r.d()
 r.u();H,g,A,l,u=r.mat(),r.vec(),r.mat(),r.vec(),r.vec();r.d();F,f,seed=r.mat(),r.vec(),r.vec();k=r.d();labels=[(r.text(),r.text()) for _ in range(r.u())]
 assert H.shape==(160,160) and A.shape==(13156,160) and F.shape==(741,160) and len(labels)==13156
 assert all(np.isfinite(x).all() for x in [H,g,A,l,u,F,f,seed]) and np.isfinite(k)
 return H,g,A,l,u,F,f,seed,k,labels,info
H,g,A,l,u,F,f,seed,k,labels,inline_info=inline(payload(base+'inline_qp.bin'))
r=Reader(payload(base+'qp_equality_reduction.bin'),'STRUCTURED_ORIGINAL_TERMINAL_EQUALITY_REDUCTION')
policy,stage=r.text(),r.text();valid=r.u();Z,p,E,rhs=r.mat(),r.vec(),r.mat(),r.vec();eq,rows=r.ids(),r.ids()
Hr,gr,Ar,lr,ur,D,Fr,seedr,usablex,usabley,R,Hs,gs,As,ls,us,Fs,seeds=(r.mat(),r.vec(),r.mat(),r.vec(),r.vec(),r.vec(),r.mat(),r.vec(),r.vec(),r.vec(),r.vec(),r.mat(),r.vec(),r.mat(),r.vec(),r.vec(),r.mat(),r.vec())
coordinate_tag=r.text();wrapper,native,raw_status,presentx,presenty=[r.u() for _ in range(5)];x,lam=r.vec(),r.vec()
slots=r.u();kr,eorigin,emap,efactor,esfactor=[r.d() for _ in range(5)];r.end()
assert wrapper==native==presentx==presenty==1 and raw_status==7 and valid==1
assert 'not usable controls' in coordinate_tag and x.shape==(144,) and lam.shape==(6034,) and usablex.size==usabley.size==0
assert Z.shape==(160,144) and len(rows)==6034 and len(eq)==16 and all(np.isfinite(a).all() for a in [x,lam,Z,p,E,rhs,D,R,Hs,gs,As,ls,us])
assert np.all(D>0) and np.all((R>0)&(R<=1)) and np.array_equal(E,A[eq]) and np.array_equal(rhs,l[eq])
# Reconstruct every saved affine transform from original coefficients.
errors={}
def check(name,a,b):
 assert np.shape(a)==np.shape(b);err=float(np.max(np.abs(np.asarray(a)-b))) if np.size(a) else 0.;errors[name]=err
 assert np.all(np.abs(np.asarray(a)-b)<=1e-11+1e-10*np.abs(b)),(name,err)
check('reduced_H',Hr,Z.T@H@Z);check('reduced_g',gr,Z.T@(g+H@p));check('reduced_A',Ar,A[rows]@Z)
check('reduced_l',lr,l[rows]-A[rows]@p);check('reduced_u',ur,u[rows]-A[rows]@p)
check('reduced_F',Fr,F@Z);check('D',D,1/np.sqrt(np.diag(Hr)))
check('R',R,1/np.maximum(1,np.max(np.abs(Ar*D),axis=1)))
check('scaled_H',Hs,D[:,None]*Hr*D);check('scaled_g',gs,D*gr)
check('scaled_A',As,R[:,None]*(Ar*D));check('scaled_l',ls,R*lr);check('scaled_u',us,R*ur);check('scaled_F',Fs,Fr*D)
U=p+Z@(D*x);ax=A@U;sax=As@x
viol=np.maximum(np.maximum(l-ax,ax-u),0);sv=np.maximum(np.maximum(ls-sax,sax-us),0)
worst=int(np.argmax(viol));order=np.argsort(viol)[::-1][:20]
lam_original=np.zeros(13156);lam_original[rows]=R*lam
stationarity_original=H@U+g+A.T@lam_original
stationarity_scaled=Hs@x+gs+As.T@lam
check('projected_stationarity_mapping',stationarity_scaled,D*(Z.T@stationarity_original))
criterion=1e-9+1e-9*max(float(np.max(np.abs(Hs@x))),float(np.max(np.abs(As.T@lam))),float(np.max(np.abs(gs))))
slack_upper=u-ax;slack_lower=ax-l
cp_original=np.maximum(lam_original,0)*slack_upper+np.maximum(-lam_original,0)*slack_lower
cp_scaled=np.maximum(lam,0)*(us-sax)+np.maximum(-lam,0)*(sax-ls)
check('complementarity_row_mapping',cp_scaled,cp_original[rows])
dualorder=np.argsort(np.abs(lam_original))[::-1][:20]
# Preserve raw multiplier sign: positive selects upper face, negative lower.
topduals=[{'original_row':int(i),'label':labels[i][0],'units':labels[i][1],'original_multiplier':float(lam_original[i]),'selected_face':'upper' if lam_original[i]>0 else 'lower','selected_face_slack':float(slack_upper[i] if lam_original[i]>0 else slack_lower[i]),'signed_complementarity_product':float(cp_original[i])} for i in dualorder]
c=Reader(payload(base+'candidate.bin'),'SOLVER_RESULT_AND_DATA_ONLY_PREVIEW');stop=c.text();ci=[c.u() for _ in range(7)];backendrow=c.signed();candidate=c.vec();cf=[c.d() for _ in range(14)];reuse=[c.u() for _ in range(4)];reset=c.text();counts=[c.u() for _ in range(4)];rowviol=c.vec();mode=c.u();timings=[c.d() for _ in range(4)];flags=[c.u() for _ in range(2)];preview,tail,request=c.u(),c.u(),c.u();c.end()
assert ci==[0,1,1,6,7,0,20000] and candidate.size==rowviol.size==0 and preview==tail==request==0 and backendrow==-1
assert cf[9:12]==[1e-9,1e-9,.1] and cf[5:9]==[1.,1.,1.,1.]
assert abs(float(np.max(np.abs(stationarity_scaled)))-cf[2])<1e-12
# Real initial/history from original nominal header; no future q/v is needed.
nr=Reader(payload(base+'original_nominal.bin'),'ORIGINAL_GENUINE_NOMINAL_BEFORE_ADAPTER')
rawtags=[nr.text() for _ in range(5)];assert not rawtags[0] and not rawtags[1]
def identity():return {'path':nr.text(),'sha':nr.text(),'bytes':nr.u()}
startup=[identity() for _ in range(4)];session_id=nr.text()
dependencies=[identity() for _ in range(nr.u())];libraries=[identity() for _ in range(nr.u())]
version,nq,nv=nr.text(),nr.u(),nr.u()
for _ in range(2):[nr.text() for _ in range(nr.u())]
for _ in range(4):[nr.signed() for _ in range(nr.u())]
metadata=[nr.vec() for _ in range(6)]
x0=nr.nums(30);prioralpha=nr.nums(7);priorb=nr.d();binding=nr.u();mesh=[nr.u() for _ in range(nr.u())]
assert np.array_equal(x0,before['state']) and np.array_equal(prioralpha,before['alpha']) and priorb==before['b']
assert mesh==[1,1,2,2,3,3,4,4,5,5,6,6,8,10,12,16,20,24,28,40] and binding==1
# Literal command/history replay of forensic U, never physical-model rollout.
C=x0[14:21].copy();w=x0[21:28].copy();s,pr=float(x0[28]),float(x0[29]);previous=prioralpha.copy();pb=priorb;h=.004
history=[];tick=0
def violation(kind,value,limit,cell,tick,j=None):
 return {'kind':kind,'value':float(value),'limit':float(limit),'excess':float(max(0.,value-limit)),'cell':cell,'tick':tick,'joint':j}
events=[];maxima={'alpha':0.,'implied_alpha':0.,'command_jerk':0.,'command_speed':0.,'progress_b':0.,'progress_jerk':0.}
labelid={a:i for i,(a,b) in enumerate(labels)}
for cell,ncycle in enumerate(mesh):
 alpha=U[8*cell:8*cell+7];b=float(U[8*cell+7]);os,orr=s,pr
 for localcycle in range(ncycle):
  tick+=1;nextw=w+h*alpha;nextC=C+h*nextw;implied=(nextw-w)/h;jerk=(implied-previous)/h
  for j in range(7):
   for name,value,limit in [('alpha',abs(alpha[j]),1.),('implied_alpha',abs(implied[j]),1.),('command_jerk',abs(jerk[j]),20.),('command_speed',abs(nextw[j]),.0625)]:
    maxima[name]=max(maxima[name],float(value));ev=violation(name,value,limit,cell,tick,j)
    if ev['excess']>0:events.append(ev)
   # Recover absolute command limits from original affine row offset C0+t*w0.
   i=labelid[f'command/C/tick/{tick}/{j}'];offset=x0[14+j]+tick*h*x0[21+j]
   if nextC[j]<l[i]+offset or nextC[j]>u[i]+offset:events.append({'kind':'command_position','cell':cell,'tick':tick,'joint':j,'value':float(nextC[j]),'lower':float(l[i]+offset),'upper':float(u[i]+offset)})
  for name,value,limit in [('progress_b',abs(b),.5),('progress_jerk',abs((b-pb)/h),5.)]:
   maxima[name]=max(maxima[name],value);ev=violation(name,value,limit,cell,tick)
   if ev['excess']>0:events.append(ev)
  for half in [1,2]:
   t=h*localcycle+.002*half;ss=os+t*orr+.5*t*t*b;rr=orr+t*b
   if not (0<=ss<=1 and 0<=rr<=.2):events.append({'kind':'half_progress_domain','cell':cell,'tick':tick,'half':half,'s':ss,'r':rr})
  ns=s+h*pr+.5*h*h*b;nr=pr+h*b
  if not(0<=ns<=1 and 0<=nr<=.2):events.append({'kind':'recursive_progress_domain','cell':cell,'tick':tick,'s':ns,'r':nr})
  C,w,s,pr,previous,pb=nextC,nextw,ns,nr,implied,b
  history.append([tick,cell,*C,*w,*implied,*jerk,s,pr,b,(b-(priorb if tick==1 else history[-1][-2]))/h])
history_result={'actual_initial':x0.tolist(),'previous_alpha':prioralpha.tolist(),'previous_b':priorb,'cycles':tick,'maxima':maxima,'failed_strict_checks_count':len(events),'first_failure':events[0] if events else None,'largest_command_jerk_excess':max([e.get('excess',0) for e in events if e['kind']=='command_jerk'],default=0),'final_command_w':w.tolist(),'last_alpha':U[152:159].tolist(),'final_progress_r':pr,'last_b':float(U[159]),'exact_stopped_command_progress':bool(np.all(w==0) and np.all(U[152:159]==0) and pr==0 and U[159]==0),'physical_stop_not_evaluated':True}
with (OUT/'forensic_full_rows.csv').open('w',newline='') as fcsv:
 cw=csv.writer(fcsv);cw.writerow(['original_row','label','units','lower','A_U','upper','violation','original_multiplier','selected_signed_complementarity'])
 for i in range(13156):cw.writerow([i,*labels[i],l[i],ax[i],u[i],viol[i],lam_original[i],cp_original[i]])
with (OUT/'forensic_command_history.csv').open('w',newline='') as fcsv:
 cw=csv.writer(fcsv);cw.writerow(['tick','cell']+[f'{n}{j}' for n in ['C','w','implied_alpha','command_jerk'] for j in range(7)]+['s','r','b','progress_jerk']);cw.writerows(history)
(OUT/'strict_history_failures.json').write_text(json.dumps(events,indent=2,allow_nan=False)+'\n')
result={'scope':'SAVED_UNSOLVED_NATIVE_ITERATE_FILE_ONLY_DIAGNOSTICS_NOT_CANDIDATE','source_sha256':START_SOURCE,'input_pins':pins,'artifact_count_including_manifest':len(ids),'all_artifact_hashes_receipts_and_binary_role_headers_verified':True,'bootstrap_counters_load_make_reset_forward_copy_getstate_observations_step_commits':bootstrap,'native_boundary_state_and_integration_arrays_unchanged':True,'source_manifest_sha256':hashlib.sha256(sm).hexdigest(),'source_payloads_verified':len(source_manifest),'coordinate_tag':coordinate_tag,'raw_capture_flags':[wrapper,native,raw_status,presentx,presenty],'raw_x_count':len(x),'raw_dual_count':len(lam),'usable_control_count':len(candidate),'saved_usable_reduced_and_scaled_counts':[len(usablex),len(usabley)],'transform_errors':errors,'full_original_SI_forensic_only':{'worst_row':worst,'label':labels[worst][0],'units':labels[worst][1],'maximum_violation':float(viol[worst]),'rows_above_1e_7':int(np.sum(viol>1e-7)),'largest20':[{'row':int(i),'label':labels[i][0],'violation':float(viol[i])} for i in order]},'original_terminal_equality_maximum':float(np.max(np.abs(E@U-rhs))),'scaled_constraint_violation':float(sv.max()),'KKT':{'scaled_stationarity_infinity':float(np.max(np.abs(stationarity_scaled))),'declared_unscaled_termination_dual_formula':criterion,'criterion_met':bool(np.max(np.abs(stationarity_scaled))<=criterion),'native_reported_dual':cf[2],'projection_mapping_error':errors['projected_stationarity_mapping'],'signed_complementarity_maxabs':float(np.max(np.abs(cp_scaled))),'signed_complementarity_min':float(np.min(cp_scaled)),'original_selected_multiplier_formula':'lambda_original[solver_rows]=R*lambda_scaled; eliminated equality multipliers not recorded','no_auxiliary_OSQP_z_captured':True,'scaled_box_distance_is_not_general_native_internal_primal_certificate':True,'largest20_original_multipliers':topduals},'strict_history_forensic_only':history_result,'actual_native_result':{'status':ci[3],'raw_status':ci[4],'iterations':ci[6],'primal':cf[1],'dual':cf[2],'setup_seconds':cf[3],'solve_seconds':cf[4],'rho_updates':counts[2],'rho_estimate':cf[12],'preview':preview,'tail':tail,'request':request,'reason':stop},'original_collector_SI_scanned_rows':len(rowviol),'collector_SI_status':'UNMEASURED; this audit forensic scan does not alter collector gates','model_calls':0,'solver_calls':0,'plant_calls':0,'phase5':'NOT_ACCEPTED','elapsed_seconds':time.monotonic()-t0}
for name,v in pins.items():assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==v['sha256']
assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==START_SOURCE
(OUT/'results.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('input_pins','strict_history_forensic_only')},indent=2));print(json.dumps(history_result,indent=2))
