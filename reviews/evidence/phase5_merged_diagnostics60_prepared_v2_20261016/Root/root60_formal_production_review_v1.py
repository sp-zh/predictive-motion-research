from pathlib import Path
import sys,os,json,struct,hashlib,ast
import numpy as np
sys.dont_write_bytecode=True;sys.path.insert(0,'/private/tmp')
from bounded_derived_bytes53_v1 import bounded_write
import root60_merged_parser_and_tests_v1 as m60
strict=m60.strict
ROOT=Path('/Users/uot/Documents/ChatGPT/ros');BASE=Path('/private/tmp/phase5_merged_hint_diagnostics60_source_v2_20261016');P=BASE/'production_math_pure_v1/readback';OLD=Path('/private/tmp/phase5_global_interval_initializer58_source_v1_20261016/production_math_pure_v1');OLD59=Path('/private/tmp/phase5_negative_leaving59_source_v1_20261016/production_math_pure_v1/readback');O=Path('/private/tmp/root60_merged_review_v1_20261016');os.environ['P5_DERIVED53_ROOT']=str(O)
tree=ast.parse(Path('/private/tmp/root58_selected_audit_v1.py').read_text());exec(compile(ast.Module(body=[x for x in tree.body if isinstance(x,ast.ClassDef)and x.name in ['R','RV4']],type_ignores=[]),'<Reader-only>','exec'))
tree=ast.parse(Path('/private/tmp/root59_production_review_v1.py').read_text());exec(compile(ast.Module(body=[x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name in ['sha','fixture','xy','actualfixture']],type_ignores=[]),'<saved-fixture-functions-only>','exec'))
receipt=json.loads((P/'PRODUCER_RECEIPT.json').read_text())
for e in receipt:
 b=(P/e['path']).read_bytes();assert len(b)==e['bytes']and sha(b)==e['sha256']
j=json.loads((P/'RESULT.json').read_text());assert len(j['records'])==17 and all(x['exit']==0 for x in j['records'])and j['input_before_after_equal']
out=[]
for case in ['actual56_48_1','old52_40_0','old53_40_1','old54_43_0','old55_40_2','actual58_54_0','actual58_74_0']:
 if case=='actual58_54_0':f=BASE/'production_math_pure_v1/actual58_54_0.initialized.fixture'
 elif case=='actual58_74_0':f=Path('/private/tmp/phase5_iteration74_analysis59_v1_20261016/actual58_current74_trial0.initialized.fixture')
 else:f=OLD/(case+'.fixture')
 (H,g,A,lo,hi,seed),raw=fixture(f);pin=next(v for k,v in j['input_pins'].items()if k.endswith('/'+f.name));assert pin['sha256']==sha(raw)and pin['bytes']==len(raw)
 if case.startswith('actual58_'):assert raw==actualfixture(int(case.split('_')[1]))
 prefix=P/('stop_'+case);oldprefix=OLD59/('stop_'+case);x,y=xy(Path(str(prefix)+'.finalxy.bin'));v=max(0.,float(np.max(lo-A@x)),float(np.max(A@x-hi)));s=float(np.max(np.abs(H@x+g+A.T@y)));assert v<=1e-12 and s<=1e-10
 compare={}
 for ext in ['finalxy.bin','states.bin','boundary48.bin','retained64.bin','refinement120.bin','full72.bin']:
  compare[ext]=Path(str(prefix)+'.'+ext).read_bytes()==Path(str(oldprefix)+'.'+ext).read_bytes();assert compare[ext]
 states=Path(str(prefix)+'.states.bin').read_bytes();assert len(states)%56==0 and 0<len(states)<=512*56;events=[struct.unpack_from('<3q4d',states,at)for at in range(0,len(states),56)]
 merged_dir=Path(str(prefix)+'.leaving');m=m60.merged(merged_dir/'hint_kkt_rank_events.bin',len(lo),events);assert(m['hint_available'],m['requested_stop'],m['policy_activated'])==(1,1,1)
 r=R(merged_dir/'legacy_rank_v1.bin','CONSISTENT_SINGULAR_ACTIVE_FACE_KKT_ORIGINAL_RESIDUALS_V1');assert r.u()==1;rank_count=r.u();assert rank_count==len(m['ranks']);legacy_rank_bytes=r.b[r.i:r.i+32*rank_count];r.i+=32*rank_count;r.text();r.end();merged_rank_bytes=b''.join(struct.pack('<3Qd',*e)for e in m['ranks']);assert legacy_rank_bytes==merged_rank_bytes and all(e[1]>=144 for e in m['ranks'])
 r=R(merged_dir/'legacy_chosen_v1.bin','STOP_ONLY_SMALLEST_CURRENT_ROW_NEGATIVE_MULTIPLIER_LEAVING_DIAGNOSTICS_V1');assert r.take('<5Q')==(m['cycle'],m['trial'],1,1,1);chosen_count=r.u();assert chosen_count==len(m['chosen']);legacy_chosen_bytes=r.b[r.i:r.i+48*chosen_count];r.i+=48*chosen_count;r.text();r.end();merged_chosen_bytes=b''.join(struct.pack('<4q2d',*e)for e in m['chosen']);assert merged_chosen_bytes==legacy_chosen_bytes
 assert strict.read_artifact_bytes(merged_dir/'legacy_chosen_v1.bin')==strict.read_artifact_bytes(Path(str(oldprefix)+'.leaving/hint_negative_leaving_events.bin'))
 assert 'complete=1 error=""'in Path(str(prefix)+'.stdout').read_text()
 out.append(dict(case=case,fixture_sha256=sha(raw),events=len(events),full_current_rows=len(lo),final_primal_numpy=v,final_stationarity_numpy=s,old59_saved_core_byte_comparisons=compare,rank_records=rank_count,chosen_records=chosen_count,same_Result_rank_and_chosen_fields_all_bytes_equal=True,chosen_complete_legacy_raw_bytes_equal_prior59=True,old59_independent_raw_rank_baseline_available=False,all_record_domains_and_old_globalmin_event_binding=True,merged_codec_bytes=m['raw_bytes']))
active=[]
for case in ['old52_40_0','old53_40_1','old54_43_0','ACTIVE_constrained','ACTIVE_interior','ACTIVE_zero']:
 b=(P/('active_'+case+'.core.bin')).read_bytes();assert b==(OLD59/('active_'+case+'.core.bin')).read_bytes();active.append(dict(case=case,bytes=len(b),sha256=sha(b),whole_core_byte_equal59=True))
report=dict(schema='ROOT60_FORMAL7STOP6ACTIVE_SAME_RESULT_MERGED_FORMAT_AND_PRIOR59_CORE_REVIEW_V1',payload_hashes_verified=len(receipt),all17_driver_commands_exit0=True,input_before_after_equal_report=True,seven_saved_stop=out,six_activefalse=active,scope='Independent full-row numerical gates and exact preserved saved core/legacy chosen bytes versus59. All rank/chosen formatter fields compare bit-exact within one same Result; prior59 independent raw rank arrays were not saved, so no false baseline-rank byte claim. No new Model/nativeOSQP/physicalC/stop/task/4ms/research acceptance. Original59 remains failed and consumed.')
bounded_write(O/'FORMAL7_STOP6_ACTIVE_MERGED_REVIEW.json',json.dumps(report,indent=2)+'\n');print(json.dumps(dict(payloads=len(receipt),stop=[(x['case'],x['events'],x['rank_records'],x['chosen_records'])for x in out],all_prior59_core_bytes_equal=True,all_same_Result_legacy_merged_fields_equal=True,active_equal=len(active))))
