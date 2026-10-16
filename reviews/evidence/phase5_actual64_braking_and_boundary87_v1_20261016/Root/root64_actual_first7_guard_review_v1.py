from pathlib import Path
import ast,sys,os,json,struct,math
import numpy as np
sys.path.insert(0,'/private/tmp');from bounded_derived_bytes53_v1 import bounded_write
import root63_nominal_reader_v4 as nominal
strict=nominal.strict
T=ast.parse(Path('/private/tmp/root58_selected_audit_v1.py').read_text());exec(compile(ast.Module(body=[x for x in T.body if isinstance(x,ast.ClassDef)and x.name=='R'],type_ignores=[]),'<reader>','exec'))
O=Path('/private/tmp/root64_actual_review_v1_20261016');os.environ['P5_DERIVED53_ROOT']=str(O);A=next(Path('/private/tmp/phase5_controlled_stop_roundoff_command_terminal64_v1_20261016').glob('actual-dell/*/run-attempt1/artifacts'));out=[]
for cycle,base in[(32,A/'cycle-32/trial-0'),(86,O/'cycle86')]:
 m=nominal.parse(A/f'cycle-{cycle}/trial-0/stop_objective_mode.bin');r=R(base/'planning_guard.bin','EXPLICIT_ALPHA_PROGRESS_JERK_AND_CURRENT_FIRST_COMMAND_CONTRACTION_V6');guard,strict_guard,pg,ps,previous_b,target=r.take('<6d');br=r.u();cols=list(r.take('<'+str(r.u())+'Q'));scales=r.vec();label=r.text();center=r.vec();limiting=r.u();trustrows=list(r.take('<'+str(r.u())+'Q'));proof=r.mat();margin=r.d();stop=r.u();fractions=r.take('<3d');count=r.u();assert stop==1 and fractions==(.5,.75,1e-6)and count==7 and np.array_equal(center,m['controls'].reshape(160));records=[]
 for j in range(7):
  assert r.u()==j;w,nom,wn,sb,tb,l,u=r.take('<7d');assert(w,nom)==(m['w'][j],center[j]);expectedwn=w+.004*nom;expectedsb=max(.5*abs(w),abs(expectedwn),.5e-6);expectedtb=math.nextafter(max(.75*abs(w),abs(expectedwn),.75e-6)*(1+16*np.finfo(float).eps),math.inf);oldl=max(-1.,nom-guard);oldu=min(1.,nom+guard);expectedl=min(max(oldl,math.nextafter((-expectedsb-w)/.004,-math.inf)),nom);expectedu=max(min(oldu,math.nextafter((expectedsb-w)/.004,math.inf)),nom);assert(wn,sb,tb,l,u)==(expectedwn,expectedsb,expectedtb,expectedl,expectedu)and oldl<=l<=nom<=u<=oldu;records.append(dict(j=j,w=w,nominal=nom,nominal_next=wn,solver_bound=sb,strict_bound=tb,lower=l,upper=u))
 r.text();r.end();r=R(A/f'cycle-{cycle}/trial-0/candidate.bin','SOLVER_RESULT_AND_DATA_ONLY_PREVIEW');r.text();r.take('<3Q');r.take('<5Q');x=r.vec();wnext=[]
 for e in records:
  j=e['j'];nextw=e['w']+.004*x[j];assert math.nextafter(abs(nextw),math.inf)<=e['strict_bound'];wnext.append(float(nextw))
 out.append(dict(cycle=cycle,all7_current_history_bounds_recomputed=True,oldguard_not_expanded=True,original_candidate_strict_nextw_gate_pass=True,new_nextw=wnext,first7=records))
bounded_write(O/'ACTUAL32_86_FIRST7_GUARD_V6_REVIEW.json',json.dumps({'schema':'ROOT64_ACTUAL_FIRST_LAST_STOP7ROW_GUARD_AND_UNCLIPPED_CANDIDATE_REVIEW_V1','samples':out,'scope':'Independent current-history/nominal/interval/strict candidate check; source and all original SI/cost/B/C checks separate. Smaller planning domain never implies unconditional physical contraction or stop acceptance.'},indent=2)+'\n');print(json.dumps([{k:v for k,v in x.items()if k!='first7'}for x in out]))
