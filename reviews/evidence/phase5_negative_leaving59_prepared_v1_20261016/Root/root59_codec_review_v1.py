from pathlib import Path
import ast,sys,os,json,struct,hashlib,importlib.util
import numpy as np
sys.dont_write_bytecode=True;sys.path.insert(0,'/private/tmp')
from bounded_derived_bytes53_v1 import bounded_write
ROOT=Path('/Users/uot/Documents/ChatGPT/ros');O=Path('/private/tmp/root59_saved_review_v1_20261016');os.environ['P5_DERIVED53_ROOT']=str(O)
spec=importlib.util.spec_from_file_location('strict',ROOT/'tools/cold_storage_verification_v1/strict_codec_reader.py');strict=importlib.util.module_from_spec(spec);spec.loader.exec_module(strict)
tree=ast.parse(Path('/private/tmp/root58_selected_audit_v1.py').read_text());exec(compile(ast.Module(body=[x for x in tree.body if isinstance(x,ast.ClassDef)and x.name=='R'],type_ignores=[]),'<Reader-only>','exec'))
P=Path('/private/tmp/phase5_negative_leaving59_source_v1_20261016/pure_suite59_readback_v1');receipt=json.loads((P/'PRODUCER_RECEIPT.json').read_text())
for e in receipt:
 b=(P/e['path']).read_bytes();assert len(b)==e['bytes']and hashlib.sha256(b).hexdigest()==e['sha256']
result=json.loads((P/'RESULT.json').read_text());assert result['complete']and len(result['rows'])==23 and all(e['exit']==0 and e['Model_native_invocations']==0 for e in result['rows'])
assert (P/'PURE_INPUT_BEFORE.json').read_bytes()==(P/'PURE_INPUT_AFTER.json').read_bytes()
role='STOP_ONLY_SMALLEST_CURRENT_ROW_NEGATIVE_MULTIPLIER_LEAVING_DIAGNOSTICS_V1';facts=[]
for case in ['maximum','unavailable','active']:
 p=P/'negative-leaving-codec-tests'/case/'hint_negative_leaving_events.bin';r=R(p,role);cycle,trial,available,stop,policy,count=r.take('<6Q');assert count==(512 if case=='maximum'else 0)
 for i in range(count):
  it,row,side,pos,chosen,minimum=r.take('<4q2d');assert (it,row,side,pos,chosen,minimum)==(i,i,1 if i%2 else -1,i%144,-2.,-9.)
 scope=r.text();r.end();assert (available,stop,policy)=={'maximum':(1,1,1),'unavailable':(0,1,0),'active':(1,0,0)}[case]
 assert len(r.b)<=28672;facts.append(dict(case=case,count=count,raw_bytes=len(r.b),raw_sha256=hashlib.sha256(r.b).hexdigest(),all_records_exact=True,codec=strict.verify_artifact(p)))
q=Path('/private/tmp/phase5_iteration74_analysis59_v1_20261016')
def rawvector(p):
 b=p.read_bytes();assert len(b)==144*8;return np.frombuffer(b,dtype='<f8')
# Reconstruct nominal/D anew from pinned actual reduction, independently of the supplement claim.
A=next(Path('/private/tmp/phase5_controlled_stop_global_interval_terminal58_v1_20261016').glob('actual-dell/*/run-attempt1/artifacts/cycle-74/trial-0'))
r=R(A/'qp_equality_reduction.bin','ORIGINAL_AND_NUMERICAL_PLANNING_TERMINAL_REDUCTION_V2');r.text();r.text();r.u();r.mat();r.vec();r.mat();r.vec();r.vec()
for _ in range(2):
 for __ in range(r.u()):r.u()
r.mat();r.vec();r.mat();r.vec();r.vec();D=r.vec();r.mat();seed=r.vec()
assert rawvector(q/'ORIGINAL_SCALE_D144.bin').tobytes()==D.tobytes()and rawvector(q/'ORIGINAL_NOMINAL_SCALED_SEED144.bin').tobytes()==(seed/D).tobytes()
out=dict(schema='ROOT59_COMPLETE_NEW_CODEC_AND_23_PURE_REVIEW_V1',producer_payload_hashes_verified=len(receipt),pure_tests_passed=23,all_pure_no_model_or_native=True,before_after_pure_inputs_byte_equal=True,new_codec_cases=facts,actual74_original_nominal_and_D_separate_files_exact=True,reader_failure_qualification='First nominal/D reader assumed length-prefixed vectors; these two explicit files are raw144 doubles. Assertion failed before report writes. Corrected fixed1152-byte format; saved-data audit only, no replay or native rerun.',scope='All512 synthetic chosen/minimum records fully decoded, plus unavailable and active-no-policy records. These scalar records are not independent eligible-working-set replay or a convergence proof. No new simulation or phase acceptance.')
bounded_write(O/'NEW_CODEC_AND_PURE_TEST_REVIEW.json',json.dumps(out,indent=2)+'\n');print(json.dumps(dict(pure_tests=23,payloads=len(receipt),new_cases=[(x['case'],x['count'],x['raw_bytes'])for x in facts],nominal_D_exact=True)))
