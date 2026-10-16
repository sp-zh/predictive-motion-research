from pathlib import Path
import sys,os,json,struct,hashlib,re,ast
import numpy as np
sys.dont_write_bytecode=True;sys.path.insert(0,'/private/tmp')
from bounded_derived_bytes53_v1 import bounded_write
O=Path('/private/tmp/root61_cycle_review_v1_20261016');os.environ['P5_DERIVED53_ROOT']=str(O)
tree=ast.parse(Path('/private/tmp/root58_selected_audit_v1.py').read_text());exec(compile(ast.Module(body=[x for x in tree.body if isinstance(x,ast.ClassDef)and x.name=='R'],type_ignores=[]),'<reader-only>','exec'))
tree=ast.parse(Path('/private/tmp/root59_production_review_v1.py').read_text());exec(compile(ast.Module(body=[x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name in['fixture','xy']],type_ignores=[]),'<arrays-only>','exec'))
P=Path('/private/tmp/phase5_bland_cycle43_analysis61_v1_20261016');(H,g,A,lo,hi,seed),b=fixture(P/'actual60_current43_trial0.initialized.fixture');q=P/'dual_readback_v1';raw=(q/'dual.certificate.bin').read_bytes();at=0;values=[]
for _ in range(3):
 n=struct.unpack_from('<Q',raw,at)[0];at+=8;values.append(np.frombuffer(raw,dtype='<f8',count=n,offset=at));at+=8*n
assert at==len(raw)==60944;x,lam,y=values;assert x.shape==(144,)and lam.shape==(127,)and y.shape==(7344,)and np.isfinite(lam).all()and float(np.min(lam))>=0
oldx,oldy=xy(P/'ACTUAL_PARTIAL_XY.bin');assert oldx.tobytes()==x.tobytes();v=max(0.,float(np.max(lo-A@x)),float(np.max(A@x-hi)));s=float(np.max(np.abs(H@x+g+A.T@y)));assert v<=1e-12 and s>1e-10
Q=Path('/private/tmp/phase5_cycle61_witness_compat_v3_20261016/readback');receipt=json.loads((Q/'PRODUCER_RECEIPT.json').read_text())
for e in receipt:
 z=(Q/e['path']).read_bytes();assert len(z)==e['bytes']and hashlib.sha256(z).hexdigest()==e['sha256']
assert(Q/'baseline_witness.states.bin').read_bytes()==(P/'ACTUAL_EVENTS56.bin').read_bytes()and(Q/'baseline_witness.finalxy.bin').read_bytes()==(P/'ACTUAL_PARTIAL_XY.bin').read_bytes()and(Q/'baseline_witness.faces16.bin').read_bytes()==(P/'ACTUAL_FINAL_FACES16.bin').read_bytes()
def witness(path):
 return[(line.split()[0],dict(re.findall(r'(\w+)=([^ ]+)',line)))for line in path.read_text().splitlines()if line.startswith(('FULLPOINT_WITNESS','STEP_WITNESS','NEGATIVE_WITNESS'))]
old=witness(Q/'baseline_witness.stderr');new=witness(Q/'stop_actual60_43_0.stderr');f0=next(d for typ,d in old if typ=='FULLPOINT_WITNESS'and d['iteration']=='220');f1=next(d for typ,d in new if typ=='FULLPOINT_WITNESS'and d['iteration']=='220');assert f0['mask']==f0['guard_eligible']=='0'and f1['mask']==f1['guard_eligible']=='1'
for key in['start','lower','upper','travel','slack','rawfraction','fullpoint','row_full_violation','full_allrow_violation','endpoint_domain','direction_inf']:assert f0[key]==f1[key]
assert float(f0['start'])==float(f0['lower'])and float(f0['slack'])==float(f0['rawfraction'])==0 and max(0.,float(f0['lower'])-float(f0['fullpoint']),float(f0['fullpoint'])-float(f0['upper']))==float(f0['row_full_violation'])<=1e-12 and float(f0['full_allrow_violation'])<=1e-12 and float(f0['direction_inf'])>1e-12
b0=next(d for typ,d in old if typ=='STEP_WITNESS'and d['iteration']=='220');b1=next(d for typ,d in new if typ=='STEP_WITNESS'and d['iteration']=='220');assert b0['fraction']==b1['fraction']=='0'and b0['blocker']=='7250'and b1['blocker']=='7251'
report=dict(schema='ROOT61_FAILED_DUAL_AND_EXACT_BASELINE_DIRECT_ENDPOINT_WITNESS_REVIEW_V1',NNLS=dict(certificate_sha256=hashlib.sha256(raw).hexdigest(),primal_unchanged=True,lambda_min=float(np.min(lam)),original_fullrow_violation=v,original_fullstationarity=s,certificate_rejected=True,no_nonexistence_claim=True),v3_payload_hashes_verified=len(receipt),baseline512events_partialxy_finalfaces_byte_equal_actual60=True,witness220_old=f0,witness220_new=f1,old_blocker7250_new_blocker7251_fraction_still0=True,retained_reader_failure='First inline checker used system Python without NumPy and failed before evidence reads/writes. This standalone checker uses bundled NumPy; no controller/probe/capture was repeated.',scope='Direct source instrument witness scalar arithmetic and exact unchanged baseline checked. Full before/after snapshots are not serialized by native V3 indices; source/targeted tests support trigger. Original endpoint1e-12 gate unchanged; no Model/OSQP/B/C/physical/stop/phase acceptance.')
bounded_write(O/'FAILED_DUAL_AND_DIRECT_WITNESS_REVIEW.json',json.dumps(report,indent=2)+'\n');print(json.dumps(dict(NNLS_stationarity=s,NNLS_rejected=True,v3_payloads=len(receipt),baseline_exact=True,witness_row_violation=float(f0['row_full_violation']),witness_allrow_violation=float(f0['full_allrow_violation']),oldblocker=b0['blocker'],newblocker=b1['blocker'])))
