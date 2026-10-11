"""Exact IEEE/Fraction row proportionality and dominance; no solver/model."""
import hashlib,json,struct,time
from collections import defaultdict,Counter
from fractions import Fraction
from pathlib import Path
import numpy as np
PACK=Path('/private/tmp/phase5_active_a_functional_checkpoint_v1_20261010_collection2')
OUT=Path(__file__).resolve().parent
SS=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
ready=(PACK/'ACTIVE_A_FUNCTIONAL_CHECKPOINT_READY.json').read_bytes();assert hashlib.sha256(ready).hexdigest()=='25b8572470112ed66f7c3735bca1e58b2aa16ca0ebbeea4bf8c1917de2fc4fdb'
manifest=json.loads(ready)['files'];rel='actual-dell/repair6/run-attempt1/artifacts/inline_qp.bin';b=(PACK/rel).read_bytes();assert hashlib.sha256(b).hexdigest()==manifest[rel]['sha256']
ob=(PACK/'ACTUAL_ACTIVE_A_OUTCOMES.json').read_bytes();assert hashlib.sha256(ob).hexdigest()==manifest['ACTUAL_ACTIVE_A_OUTCOMES.json']['sha256'];outcome=json.loads(ob)[-1];assert outcome['version']=='repair6'
class Reader:
 def __init__(self):self.i=0
 def u(self):v=struct.unpack_from('<Q',b,self.i)[0];self.i+=8;return v
 def d(self):v=struct.unpack_from('<d',b,self.i)[0];self.i+=8;return v
 def text(self):n=self.u();v=b[self.i:self.i+n].decode();self.i+=n;return v
 def nums(self,n):v=np.frombuffer(b,dtype='<f8',count=n,offset=self.i);self.i+=8*n;return v
 def vec(self):return self.nums(self.u())
 def mat(self):r,c=self.u(),self.u();return self.nums(r*c).reshape(r,c)
r=Reader();assert r.text()=='P5_ACTIVE_SESSION_LOSSLESS_V1' and r.text()=='INLINE_QP_COMPLETE_OR_RETAINED_PREFIX';r.text();r.text()
for _ in range(7):r.u()
r.text();r.u()
for _ in range(3):r.d()
r.u();H,g,A,lower,upper=r.mat(),r.vec(),r.mat(),r.vec(),r.vec();r.d();F,f,seed=r.mat(),r.vec(),r.vec();r.d();labels=[(r.text(),r.text()) for _ in range(r.u())]
assert A.shape==(13156,160) and np.isfinite(A).all() and np.isfinite(lower).all() and np.isfinite(upper).all()
start=time.monotonic();bitgroups=defaultdict(list);valuegroups=defaultdict(list)
for i,row in enumerate(A):
 bitgroups[row.tobytes()].append(i);copy=row.copy();copy[copy==0]=0.;valuegroups[copy.tobytes()].append(i)
proportional=defaultdict(list);pivots={}
for rows in valuegroups.values():
 i=rows[0];nonzero=np.flatnonzero(A[i])
 if not len(nonzero):key=()
 else:
  pivot=Fraction.from_float(float(A[i,nonzero[0]]));key=tuple((int(j),(Fraction.from_float(float(A[i,j]))/pivot).numerator,(Fraction.from_float(float(A[i,j]))/pivot).denominator) for j in nonzero)
 proportional[key].extend(rows)
 for ix in rows:pivots[ix]=Fraction.from_float(float(A[ix,nonzero[0]])) if len(nonzero) else Fraction(0)
def interval(i):
 pivot=pivots[i];l,u=Fraction.from_float(float(lower[i])),Fraction.from_float(float(upper[i]));assert pivot!=0
 return (l/pivot,u/pivot) if pivot>0 else (u/pivot,l/pivot)
def mandatory(i):return labels[i][0].startswith(('input/','trust/','keep/')) or lower[i]==upper[i]
eq={i for i in range(len(labels)) if lower[i]==upper[i]}
trust={i for i,x in enumerate(labels) if x[0].startswith('trust/')}
ret6=set(outcome['retained_rows']);restored=ret6|trust
profiles={'all_original':set(range(13156)),'actual_repair6_retained':ret6,'repair6_matrix_with_trust_restored':restored,'trust_restored_after_explicit16_equality_elimination':restored-eq}
summary={};certificates={}
for name,subset in profiles.items():
 kept=set();removed=[];group_count=0;repeatgroups=0;two_witness=0;examples=[]
 for key,indices in proportional.items():
  inds=sorted(set(indices)&subset)
  if not inds:continue
  group_count+=1
  if len(inds)>1:repeatgroups+=1
  required=[i for i in inds if mandatory(i)];keepers=set(required)
  if not key:
   # Original zero rows may be removed only if exactly feasible and nonmandatory.
   for i in inds:
    if lower[i]<=0<=upper[i] and not mandatory(i):removed.append({'row':i,'witness_rows':[],'zero_feasible':True})
    else:keepers.add(i)
  else:
   intervals={i:interval(i) for i in inds};maxlower=max(x[0] for x in intervals.values());minupper=min(x[1] for x in intervals.values());assert maxlower<=minupper
   lowerowners=[i for i in inds if intervals[i][0]==maxlower];upperowners=[i for i in inds if intervals[i][1]==minupper]
   loowner=next((i for i in lowerowners if i in keepers),lowerowners[0]);hiowner=next((i for i in upperowners if i in keepers),upperowners[0]);keepers|={loowner,hiowner}
   for i in inds:
    if i not in keepers:
     assert maxlower>=intervals[i][0] and minupper<=intervals[i][1]
     one=[j for j in keepers if intervals[j][0]>=intervals[i][0] and intervals[j][1]<=intervals[i][1]]
     witnesses=[min(one)] if one else [loowner,hiowner];two_witness+=not bool(one)
     removed.append({'row':i,'witness_rows':witnesses,'zero_feasible':False})
  kept|=keepers
  if len(inds)>1 and len(examples)<12:examples.append({'rows':inds,'labels':[labels[i][0] for i in inds],'retained':sorted(keepers),'lower_owner':None if not key else loowner,'upper_owner':None if not key else hiowner})
 assert set(i for i in subset if mandatory(i))<=kept
 assert kept|{x['row'] for x in removed}==subset and not(kept&{x['row'] for x in removed})
 groups=Counter('/'.join(labels[x['row']][0].split('/')[:2]) for x in removed)
 summary[name]={'rows':len(subset),'distinct_exact_proportional_groups':group_count,'repeated_proportional_groups':repeatgroups,'retained_by_exact_dominance':len(kept),'removable_nonmandatory':len(removed),'removal_uses_two_retained_side_owners':int(two_witness),'removal_semantic_groups':dict(groups),'mandatory_rows_all_preserved':True,'representative_groups':examples}
 certificates[name]=[{'original_row':x['row'],'label':labels[x['row']][0],'units':labels[x['row']][1],'retained_original_witness_rows':x['witness_rows'],'witness_labels':[labels[i][0] for i in x['witness_rows']],'zero_row_feasible':x['zero_feasible']} for x in removed]
native={k:outcome[k] for k in ['raw_status','iterations','primal','dual','setup_seconds','solve_seconds','rho_updates','rho_estimate','initial_rho','polish_status','workspace_reused','dual_reused','controls']}
costgroups=defaultdict(list)
for i in range(len(f)):costgroups[np.r_[F[i],f[i]].tobytes()].append(i)
result={'scope':'EXACT_STORED_ORIGINAL_IEEE_ROWS_AND_FRACTION_PROPORTIONS_ONLY_NO_SOLVER_MODEL','source_sha256':SS,'input_ready_sha256':hashlib.sha256(ready).hexdigest(),'input_inline_sha256':manifest[rel]['sha256'],'bit_identical_row_groups':len(bitgroups),'bit_identical_repeated_groups':sum(len(v)>1 for v in bitgroups.values()),'bit_identical_extra_rows':sum(len(v)-1 for v in bitgroups.values()),'exact_numeric_row_groups_signed_zero_canonicalized':len(valuegroups),'exact_proportional_groups':len(proportional),'zero_row_count':len(proportional.get((),[])),'profiles':summary,'factor_diagnostics':{'rows':len(f),'zero_coefficient_rows':int(np.sum(np.all(F==0,axis=1))),'bit_identical_affine_residual_groups':len(costgroups),'extra_identical_affine_residual_rows':sum(len(v)-1 for v in costgroups.values()),'deleting_cost_rows_without_weight_constant_compensation_is_invalid':True,'solver_uses_summed_H_not_F_rows_as_constraints':True},'native_repair6_info':native,'elapsed_seconds':time.monotonic()-start,'actual_A14_not_claimed':'No actual A14 solver diagnostics or transformed duplicate matrix parsed in this unit','cost_proportionality_scope':'Constraint duplication cannot establish cause of slow dual convergence; summing squared cost terms is not interchangeable with deleting them','phase5':'NOT_ACCEPTED'}
assert hashlib.sha256((PACK/rel).read_bytes()).hexdigest()==manifest[rel]['sha256'] and hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==SS
(OUT/'results.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');(OUT/'dominance_certificates.json').write_text(json.dumps(certificates,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='profiles'},indent=2))
print(json.dumps({k:{kk:vv for kk,vv in v.items() if kk!='representative_groups'} for k,v in summary.items()},indent=2))
