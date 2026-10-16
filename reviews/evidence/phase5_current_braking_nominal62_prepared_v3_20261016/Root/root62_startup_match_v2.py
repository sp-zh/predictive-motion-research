from pathlib import Path
import sys,os,json
sys.path.insert(0,'/private/tmp');from bounded_derived_bytes53_v1 import bounded_write
O=Path('/private/tmp/root62_stop_cause_review_v1_20261016');os.environ['P5_DERIVED53_ROOT']=str(O);plan=json.loads((O/'ACTUAL62_active_run_plan.json').read_text());before=json.loads((O/'ACTUAL62_run-attempt1_BEFORE_INPUT_IDENTITIES.json').read_text());assert len(before)==len(plan['input_files'])==1731;undeclared=0
for observed,expected in zip(before,plan['input_files']):
 for k in ['requested_path','bytes','sha256']:assert observed[k]==expected[k]
 if 'resolved_path'in expected:assert observed['resolved_path']==expected['resolved_path']
 else:assert observed['resolved_path']==expected['requested_path'];undeclared+=1
j=dict(schema='ROOT62_ACTUAL1731_STARTUP_RECEIPTS_MATCH_FROZEN_PLAN_V2',count=1731,all_declared_requested_bytes_SHA_and_resolved_fields_match=True,plan_resolved_path_undeclared_source_records=undeclared,undeclared_resolved_paths_equal_requested=True,reader_qualification='First aggregate checker assumed resolved_path present in every plan entry. Source/profile entries declare requested/size/SHA only. KeyError after separate exact-original74 report was successfully written; no runtime/capture repeated. Corrected checker compares all declared fields and additionally requires equal requested/resolved path for those entries.',scope='Independently received original driver startup observations match all declared plan identities; all91 source/profile hashes separately verified. No full dependency rehash/cold IO during native; termination identity still pending.')
bounded_write(O/'ACTUAL62_ALL1731_BEFORE_RECEIPTS_MATCH_PLAN.json',json.dumps(j,indent=2)+'\n');print(json.dumps(j))
