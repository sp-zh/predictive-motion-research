from pathlib import Path
import os,sys,json,hashlib,ast,struct,math
import numpy as np
sys.path.insert(0,'/private/tmp');from bounded_derived_bytes53_v1 import bounded_write
import root64_merged_reader_v4 as merged
strict=merged.strict
T=ast.parse(Path('/private/tmp/root58_selected_audit_v1.py').read_text());exec(compile(ast.Module(body=[x for x in T.body if isinstance(x,ast.ClassDef)and x.name=='R'],type_ignores=[]),'<reader>','exec'))
T=ast.parse(Path('/private/tmp/root59_production_review_v1.py').read_text());exec(compile(ast.Module(body=[x for x in T.body if isinstance(x,ast.FunctionDef)and x.name in['fixture','xy']],type_ignores=[]),'<fixtures>','exec'))
P=Path('/private/tmp/phase5_roundoff_command64_source_v1_20261016/targeted_newpolicies_v1/readback');O=Path('/private/tmp/root64_saved63_cause_review_v1_20261016');os.environ['P5_DERIVED53_ROOT']=str(O);receipt=json.loads((P/'RECEIPT.json').read_text());assert isinstance(receipt,list)
for e in receipt:
 b=(P/e['path']).read_bytes();assert len(b)==e['bytes']and hashlib.sha256(b).hexdigest()==e['sha256']
j=json.loads((P/'RESULT.json').read_text());assert j['input_before_after_equal']and j['all10_true_numerical_complete']and len(j['records'])==12 and all(x['exit']==0 for x in j['records']);cases=json.loads((P/'PLAN.json').read_text())['fixtures'];out=[]
for case in cases:
 f=Path('/private/tmp/phase5_global_interval_initializer58_source_v1_20261016/production_math_pure_v1')/(case+'.fixture')
 if case=='actual58_54_0':f=Path('/private/tmp/phase5_negative_leaving59_source_v1_20261016/production_math_pure_v1/actual58_54_0.initialized.fixture')
 elif case=='actual58_74_0':f=Path('/private/tmp/phase5_iteration74_analysis59_v1_20261016/actual58_current74_trial0.initialized.fixture')
 elif case=='actual60_43_0':f=Path('/private/tmp/phase5_bland_cycle43_analysis61_v1_20261016/actual60_current43_trial0.initialized.fixture')
 elif case=='actual63_originalbounds':f=Path('/private/tmp/phase5_saved63_roundoff_endpoint_probe_v1_20261016/fixture.bin')
 elif case=='actual63_first7_contraction':f=P.parent/'actual63_first7_contraction.bin'
 (H,g,A,lo,hi,seed),b=fixture(f);x,y=xy(P/(case+'.finalxy.bin'));primal=max(0.,float(np.max(lo-A@x)),float(np.max(A@x-hi)));stationarity=float(np.max(np.abs(H@x+g+A.T@y)));assert primal<=1e-12 and stationarity<=1e-10
 d=P/(case+'.leaving');m=merged.parse(d/'hint_kkt_rank_events.bin',len(lo));assert m['roundoff']==1 and m['available']==m['policy']==1
 for name in strict.manifest_entries(d/'MANIFEST.yaml'):strict.verify_artifact(d/name)
 legacy=merged.m61.m60.merged(d/'legacy_merged_v2.bin',len(lo));assert m['ranks']==legacy['ranks']and m['chosen']==legacy['chosen']
 ep=(P/(case+'.retained64.bin')).read_bytes();assert len(ep)%64==0 and len(ep)<=16384*64 and m['admissions']<=len(ep)//64
 for at in range(0,len(ep),64):
  it,row,start,travel,value,l,u,v=struct.unpack_from('<2Q6d',ep,at);assert it<512 and row<len(lo)and np.isfinite([start,travel,value,l,u,v]).all()and struct.pack('<2d',l,u)==struct.pack('<2d',lo[row],hi[row]);assert v==max(0.,l-value,value-u)<=1e-12
 stdout=(P/(case+'.stdout')).read_text();assert 'complete=1 error=""'in stdout
 out.append(dict(case=case,fixture_sha256=hashlib.sha256(b).hexdigest(),primal_numpy=primal,stationarity_numpy=stationarity,roundoff_new_admissions=m['admissions'],all_endpoint_records=len(ep)//64,ranks=len(m['ranks']),negative_leaving=len(m['chosen']),stdout=stdout.strip()))
A=next(Path('/private/tmp/phase5_controlled_stop_explicit_warm_nominal_terminal63_v1_20261016').glob('actual-dell/*/run-attempt1/artifacts/cycle-63/trial-0'));r=R(A/'qp_equality_reduction.bin','ORIGINAL_AND_NUMERICAL_PLANNING_TERMINAL_REDUCTION_V2');r.text();r.text();r.u();Z,p=r.mat(),r.vec();r.mat();r.vec();r.vec()
for _ in range(2):r.take('<'+str(r.u())+'Q')
r.mat();r.vec();r.mat();r.vec();r.vec();D=r.vec();x,y=xy(P/'actual63_first7_contraction.finalxy.bin');u=p+Z@(D*x);bounds=json.loads((O/'FIRST7_SAVED63_MATRIX_REVIEW.json').read_text())['rows'];wn=[]
for row in bounds:
 value=row['current_w']+.004*u[row['joint']];assert math.nextafter(abs(value),math.inf)<=row['strict_bound'];wn.append(value)
report=dict(schema='ROOT64_NEW_OPTIN10_SAVED_QP_AND_FULL_V4_CODEC_REVIEW_V1',payloads_SHA_verified=len(receipt),all12_compile_link_replay_commands_exit0=True,all10_pure_complete_under_original512_10s=True,input_before_after_equal_producer_report=True,cases=out,all_full_V4_codec_SHA_CRC_and_legacy_rank_chosen_values_equal=True,all_endpoint_records_against_original_row_domain_recomputed=True,new_first7_original_reconstructed_next_w=wn,all7_new_strict_bounds_pass=True,scope='Independent saved-QP primal/stationarity/codec/endpoint-domain certificate. Two actual63 fixtures separately bound to original matrix and first7-only restriction. Reconstructed seventh nextw remains above1e-6, and no physical state simulation/nativeOSQP/B/C/stop success follows. Full endpoint directions not serialized; no independent every-step fullvector reconstruction. Old default/active core compatibility separately checked.')
bounded_write(O/'NEWPOLICY10_FULL_MATRIX_AND_V4_REVIEW.json',json.dumps(report,indent=2)+'\n');print(json.dumps({'cases':10,'payloads':len(receipt),'all_gates':True,'new_actual63':out[-2:],'new_wnext':wn}))
