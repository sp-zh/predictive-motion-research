from pathlib import Path
import sys,os,json,ast,hashlib,struct
import numpy as np
sys.path.insert(0,'/private/tmp');from bounded_derived_bytes53_v1 import bounded_write
import root61_parser_and_formal_review_v1 as m61
strict=m61.strict
T=ast.parse(Path('/private/tmp/root58_selected_audit_v1.py').read_text());exec(compile(ast.Module(body=[x for x in T.body if isinstance(x,ast.ClassDef)and x.name=='R'],type_ignores=[]),'<saved-reader>','exec'))
O=Path('/private/tmp/root62_stop_cause_review_v1_20261016');os.environ['P5_DERIVED53_ROOT']=str(O);A=next(Path('/private/tmp/phase5_controlled_stop_exact_cycle_terminal61_v1_20261016').glob('actual-dell/*/run-attempt1/artifacts'))
def metadata(r):
 version=r.text();nq,nv=r.take('<2Q')
 for _ in range(2):
  for __ in range(r.u()):r.text()
 for _ in range(4):
  for __ in range(r.u()):r.u()
 vectors=[r.vec()for _ in range(6)]
 return dict(version=version,nq=nq,nv=nv)
def dynamic_state(r):
 q,v,C,w=[r.vec()for _ in range(4)];assert all(len(x)==7 for x in[q,v,C,w]);s,rate=r.take('<2d');return dict(q=q,v=v,C=C,w=w,s=s,r=rate)
rows=[]
for case,path in [('32/1',O/'saved61_onset32_trial1/candidate_value.bin'),('43/1',A/'cycle-43/trial-1/candidate_value.bin'),('74/0',A/'cycle-74/trial-0/candidate_value.bin'),('95/0',A/'cycle-95/trial-0/candidate_value.bin')]:
 strict.verify_artifact(path);r=R(path,'ORIGINAL_GENUINE_CANDIDATE_VALUE_NO_EXECUTION');r.take('<3Q');present=r.u();
 if present:metadata(r)
 transport,nominal,invocation=r.text(),r.text(),r.text();initial=[r.arr(7)for _ in range(4)];initial_s,initial_r=r.take('<2d');count=r.u();assert count==20;controls=[]
 for _ in range(count):cy=r.u();a=r.vec();b=r.d();assert len(a)==7;controls.append((cy,a,b))
 assert r.u()==1;success,final_present=r.take('<2Q');error=r.text();final=dynamic_state(r);assert success and final_present and not error and not transport
 n=r.u();assert n==400;sub=[];previous_v=initial[1]
 for i in range(n):
  cell,cycle,half=r.take('<3Q');elapsed,sref,rref=r.take('<3d');q,v,C,w,force=[r.vec()for _ in range(5)];assert all(len(x)==7 for x in[q,v,C,w,force]);branches=[r.u()for _ in range(r.u())];r.u();r.d();r.take('<2Q');assert abs(elapsed-.002*(i+1))<1e-12
  acc=(v-previous_v)/.002;previous_v=v;alpha=controls[cell][1];b=controls[cell][2];norms=[float(np.max(np.abs(x)))for x in[v,acc,w,alpha]]+[rref,abs(b)];below=all(x<=y for x,y in zip(norms,[1e-4,1e-3,1e-6,1e-4,1e-6,1e-4]));sub.append(dict(elapsed=elapsed,v=norms[0],a=norms[1],w=norms[2],alpha=norms[3],r=norms[4],b=norms[5],below=below,q=q,v_vector=v))
 for expected in[200,20]:
  assert r.u()==expected
  for _ in range(expected):dynamic_state(r)
 r.end();first_below=next((x['elapsed']for x in sub if x['below']),None);simultaneous=sum(x['below']for x in sub)
 sample=lambda x:{k:v for k,v in x.items()if k not in['q','v_vector']}
 cycle=int(case.split('/')[0]);trial=int(case.split('/')[1]);commit=A/f'cycle-{cycle}/trial-{trial}/actual_commit.bin';c=R(commit,'TWO_REAL_2MS_HELD_TARGET_COMMIT_OR_RETAINED_PARTIAL_V1');attempted,complete,steps,returns=c.take('<4Q');c.text();ce=c.text();c.take('<4Q');c.arr(7);c.take('<2d');points=c.u();assert(attempted,complete,steps,returns,points)==(1,1,2,2,2)and not ce;diffs=[]
 for i in range(points):
  c.u();c.d();c.take('<3Q');cq,cv,cc,ca,cj=[c.arr(7)for _ in range(5)];c.take('<4Q');c.take('<8Q');c.take('<7d');c.take('<2Q');c.text();c.text();diffs.append(dict(q_error_inf=float(np.max(np.abs(cq-sub[i]['q']))),v_error_inf=float(np.max(np.abs(cv-sub[i]['v_vector'])))))
 c.end();rows.append(dict(case=case,source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),controls=20,predicted_halves=400,first_simultaneous_predicted_below_s=first_below,simultaneous_predicted_below_count=simultaneous,at4ms=sample(sub[1]),at64brake_window256ms=sample(sub[127]),at800ms=sample(sub[-1]),first_actual_two_halves_model_errors=diffs))
report=dict(schema='ROOT62_EXISTING61_CANDIDATE_FORECAST_STOP_DIAGNOSTIC_V1',reader_qualification='Initial saved-value decoder incorrectly required an optional observedMetadata field. Source serializes it conditionally; corrected reader follows presence flag. No native/Model/capture repeated.',cases=rows,scope='Decode genuine saved61 value-only forecasts and compare first actual2ms halves; no Model/plant invocation or new experiment. Full400 horizon is the saved forecast of a fixed candidate, not the later receding actual trajectory. Predicted simultaneous thresholds omit actual hold-anchor dwell and are not stop acceptance. Original stop sample applies accepted command w to both physical halves, while model substeps report integrated w; this difference is explicit.')
bounded_write(O/'SAVED61_FORECAST_STOP_DIAGNOSTIC.json',json.dumps(report,indent=2)+'\n');print(json.dumps(report))
