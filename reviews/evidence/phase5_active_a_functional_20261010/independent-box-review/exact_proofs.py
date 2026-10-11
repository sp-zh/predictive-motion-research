"""Independent exact-rational audit of all actual repair6 omission certificates."""
import hashlib,json,struct,time
from collections import Counter
from fractions import Fraction
from pathlib import Path
import numpy as np

SRC=Path('/private/tmp/phase5_active_box_source_review_repair6_20261010')
PACKET=Path('/private/tmp/phase5_active_a_functional_checkpoint_v1_20261010_collection2')
BASE=PACKET/'actual-dell/repair6/run-attempt1/artifacts'
OUT=Path(__file__).resolve().parent
SOURCE_SHA=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
sm=(SRC/'SOURCE_MANIFEST.json').read_bytes();assert hashlib.sha256(sm).hexdigest()=='9068e7d2b1908f26d03628991e840c555c9a8fcfa8631bedd15b50ba2f925513'
sources=json.loads(sm)['files']
for x in sources:assert digest(SRC/x['path'])==x['sha256'] and (SRC/x['path']).stat().st_size==x['bytes']
mb=(PACKET/'ACTIVE_A_FUNCTIONAL_CHECKPOINT_READY.json').read_bytes();assert hashlib.sha256(mb).hexdigest()=='25b8572470112ed66f7c3735bca1e58b2aa16ca0ebbeea4bf8c1917de2fc4fdb'
manifest=json.loads(mb);used=['ACTUAL_ACTIVE_A_OUTCOMES.json']+[f'actual-dell/repair6/run-attempt1/artifacts/{n}' for n in ['inline_qp.bin','solver_row_screen.bin','candidate.bin','MANIFEST.yaml']]+['actual-dell/repair6/dev_compile_plan.json']
for n in used:
 x=manifest['files'][n];assert digest(PACKET/n)==x['sha256'] and (PACKET/n).stat().st_size==x['bytes']
class Reader:
 def __init__(self,name,role):
  self.data=(BASE/name).read_bytes();self.pos=0
  assert self.text()=='P5_ACTIVE_SESSION_LOSSLESS_V1' and self.text()==role
 def u(self):v=struct.unpack_from('<Q',self.data,self.pos)[0];self.pos+=8;return v
 def d(self):v=struct.unpack_from('<d',self.data,self.pos)[0];self.pos+=8;return v
 def text(self):n=self.u();v=self.data[self.pos:self.pos+n].decode();self.pos+=n;return v
 def nums(self,n):v=np.frombuffer(self.data,dtype='<f8',count=n,offset=self.pos);self.pos+=n*8;return v
 def vec(self):return self.nums(self.u())
 def mat(self):r,c=self.u(),self.u();return self.nums(r*c).reshape(r,c)
r=Reader('inline_qp.bin','INLINE_QP_COMPLETE_OR_RETAINED_PREFIX');r.text();r.text()
for _ in range(7):r.u()
r.text();r.u()
for _ in range(3):r.d()
r.u();H,g,A,lo,hi=r.mat(),r.vec(),r.mat(),r.vec(),r.vec();r.d();F,f,seed=r.mat(),r.vec(),r.vec();r.d();labels=[(r.text(),r.text()) for _ in range(r.u())]
assert A.shape==(13156,160) and np.isfinite(A).all() and np.isfinite(lo).all() and np.isfinite(hi).all() and len(set(n for n,_ in labels))==13156
s=Reader('solver_row_screen.bin','ORIGINAL_SI_INPUT_BOX_IMPLICATION_SCREEN');policy=s.text();retained=[s.u() for _ in range(s.u())];omitted=[s.u() for _ in range(s.u())];proofs=[s.text() for _ in range(s.u())];fp=[s.u() for _ in range(3)];note=s.text();worst=s.u();assert s.pos==len(s.data)
assert retained==sorted(set(retained)) and omitted==sorted(set(omitted)) and len(retained)==5472 and len(omitted)==len(proofs)==7684
assert sorted(retained+omitted)==list(range(13156)) and not(set(retained)&set(omitted))
outcome=json.loads((PACKET/'ACTUAL_ACTIVE_A_OUTCOMES.json').read_text())[-1]
assert outcome['version']=='repair6' and outcome['retained_rows']==retained and outcome['omitted_rows']==omitted and outcome['outward_hex_intervals']==proofs and outcome['fp_environment']==fp and outcome['mapping_note']==note and outcome['original_maximum_violation_row']==worst
boxlo=[None]*160;boxhi=[None]*160;input_indices=[]
for i,(name,units) in enumerate(labels):
 if name.startswith('input/'):
  columns=np.flatnonzero(A[i]);assert len(columns)==1;j=int(columns[0]);assert A[i,j]==1 and boxlo[j] is None
  assert name==f'input/{j//8}/{j%8}' and units==('1/s^2' if j%8==7 else 'rad/s^2')
  assert lo[i]==(-.5 if j%8==7 else -1) and hi[i]==(.5 if j%8==7 else 1)
  boxlo[j]=Fraction.from_float(float(lo[i]));boxhi[j]=Fraction.from_float(float(hi[i]));input_indices.append(i)
assert len(input_indices)==160 and set(input_indices)<=set(retained) and all(q is not None for q in boxlo)
equalities=[i for i in range(13156) if lo[i]==hi[i]];assert len(equalities)==16 and set(equalities)<=set(retained)
def hexrational(text):
 negative=text.startswith('-');text=text.lstrip('+-');mantissa,exp=text.lower().split('p');assert mantissa.startswith('0x')
 digits=mantissa[2:].split('.');integer=digits[0]+(digits[1] if len(digits)>1 else '')
 denom=16**(len(digits[1]) if len(digits)>1 else 0);q=Fraction(int(integer,16),denom);e=int(exp)
 q=q*(1<<e) if e>=0 else q/Fraction(1<<(-e));return -q if negative else q
checks=[];started=time.monotonic();groups=Counter();trust=[];widths=[]
for i,text in zip(omitted,proofs):
 left,right=text.split();prooflo,proofhi=hexrational(left),hexrational(right)
 exactlo=Fraction();exacthi=Fraction()
 for j in np.flatnonzero(A[i]):
  aa=Fraction.from_float(float(A[i,j]));p,q=aa*boxlo[j],aa*boxhi[j];exactlo+=min(p,q);exacthi+=max(p,q)
 lower,upper=Fraction.from_float(float(lo[i])),Fraction.from_float(float(hi[i]))
 assert lower<=prooflo<=exactlo<=exacthi<=proofhi<=upper,(i,labels[i])
 assert i not in input_indices and i not in equalities
 groups['/'.join(labels[i][0].split('/')[:2])]+=1
 if labels[i][0].startswith('trust/'):trust.append(i)
 widths.append(float(max(exactlo-prooflo,proofhi-exacthi)))
 checks.append({'original_row':i,'label':labels[i][0],'units':labels[i][1],'proof_outward_hex':text,'exact_support_lower':{'n':str(exactlo.numerator),'d':str(exactlo.denominator)},'exact_support_upper':{'n':str(exacthi.numerator),'d':str(exacthi.denominator)},'enclosed_and_original_bounds_imply':True})
elapsed=time.monotonic()-started
r=Reader('candidate.bin','SOLVER_RESULT_AND_DATA_ONLY_PREVIEW');reason=r.text();execflag,attempts,wrappers,status,raw,api,iters,worstrow=[r.u() for _ in range(8)];candidate=r.vec();assert len(candidate)==0 and status==6 and raw==7 and iters==4000 and api==0 and not execflag
# Existing rational tolerance witness is preserved, not retuned.
old=Path('/private/tmp/root_independent_box_screening_review_20261010/fraction_support.json');witness=json.loads(old.read_text())['tolerance_set_counterexample']
compile_plan=json.loads((PACKET/'actual-dell/repair6/dev_compile_plan.json').read_text())
report={'scope':'ALL_ACTUAL_REPAIR6_OMITTED_IEEE_ROWS_EXACT_RATIONAL_PROOF_CHECK_NO_NATIVE_MODEL_COMPILER_SOLVER','audit_source_sha256':SOURCE_SHA,'source_manifest_sha256':hashlib.sha256(sm).hexdigest(),'actual_packet_ready_sha256':hashlib.sha256(mb).hexdigest(),'used_payload_hashes':{n:manifest['files'][n] for n in used},'source_files_verified':len(sources),'original_rows':13156,'retained_rows':len(retained),'omitted_rows':len(omitted),'all160_input_rows_exact_and_retained':True,'all16_equalities_retained':True,'all7684_actual_hex_interval_proofs_enclose_exact_IEEE_support_and_fit_original_bounds':True,'proof_max_absolute_extra_enclosure':max(widths),'exact_check_seconds':elapsed,'omitted_semantic_groups':dict(groups),'trust_rows_omitted':len(trust),'trust_original_indices':trust,'fp_environment':fp,'fp_bits_guard_matches':fp[0]==0 and fp[1]&0x0300==0x0300 and fp[1]&0x0c00==0 and fp[2]&0xe040==0,'saved_original_worst_field_scope':'mapped backend-reduced worst; not recomputed full original worst','actual_solver':{'reason':reason,'status':'ITERATION_LIMIT','raw_status':raw,'iterations':iters,'usable_candidate':False,'execution':bool(execflag),'attempts':attempts,'wrapper_entries':wrappers},'tolerance_counterexample_preserved':witness,'compile_plan_keys':list(compile_plan),'phase5':'NOT_ACCEPTED'}
for x in sources:assert digest(SRC/x['path'])==x['sha256']
for n in used:assert digest(PACKET/n)==manifest['files'][n]['sha256']
assert digest(Path(__file__))==SOURCE_SHA
(OUT/'all_omitted_exact_checks.json').write_text(json.dumps(checks,indent=2)+'\n');(OUT/'exact_report.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ('used_payload_hashes','trust_original_indices','tolerance_counterexample_preserved')},indent=2))
