"""Metadata-only correction; no matrix/model/native/optimizer rerun."""
from pathlib import Path
import hashlib,json
OUT=Path(__file__).resolve().parent
OLD=Path('/private/tmp/root_independent_nonzero_progress_actual_review_20261011')
ROOT=Path('/Users/uot/Documents/ChatGPT/ros/results/phase5-reference/nonzero-progress-actual-v1-20261011/runtime-import1')
sha=lambda b:hashlib.sha256(b).hexdigest()
ready=(OLD/'READY.json').read_bytes();assert sha(ready)=='0e255995ed9c762085b38fae8cc2e8e6e58c53d45bd7a1fef33ccde07f6e5f4d'
old=json.loads(ready)
for n,i in old['files'].items():
 b=(OLD/n).read_bytes();assert len(b)==i['bytes'] and sha(b)==i['sha256']
runtime=(ROOT/'ROOT_READY.json').read_bytes();assert sha(runtime)=='a8002776d4850dc1b87df9b2aa384d8ea23e5c0f1dd527881c394a25dfe031ec';rr=json.loads(runtime)
stage=json.loads((OLD/'STAGE1_RESULT.json').read_bytes())
records=[];paths=[]
for prefix in ['artifacts']+[f'artifacts/cycle-{i}' for i in range(3)]:
 n=prefix+'/MANIFEST.yaml';b=(ROOT/n).read_bytes();i=rr['files'][n];assert len(b)==i['bytes'] and sha(b)==i['sha256']
 names=[line.split(': ',1)[1] for line in b.decode().splitlines() if line.startswith('  - file: ')]
 assert len(names)==len(set(names));paths.extend(prefix+'/'+x for x in names)
 records.append({'manifest':n,'bytes':len(b),'sha256':sha(b),'file_entries':len(names),'unique_within_manifest':len(set(names)),'task_metric_entry_count':sum(x=='actual_task_errors.bin' for x in names)})
assert [r['file_entries'] for r in records]==[8,17,17,17]
assert stage['root_receipts']['files']==8 and [x['binary_receipts']['files'] for x in stage['cycles']]==[17,17,17]
assert len(paths)==len(set(paths))==59
assert (OLD/'READY.json').read_bytes()==ready
result={'schema':'ROOT_ACTUAL36_RECEIPT_COUNT_CORRECTION_V1','correct_unique_receipt_count':59,'parent_count':8,'per_cycle_counts':[17,17,17],'prior_report_count':62,'cause':'Documentation error in REVIEW.md and agent messages; original checker saved correct8+17+17+17 counts and did not calculate62. Three task-metric binaries were reread separately for metric parsing, but those reads do not add receipts.','additional_task_metric_parse_reads':3,'additional_receipts_from_those_reads':0,'original_review_ready_sha256':sha(ready),'original_review_payload_count':len(old['files']),'original_review_payloads_unchanged':True,'runtime_ready_sha256':sha(runtime),'manifests':records,'qualified_unique_receipt_paths':paths,'scope':'Count/metadata correction only; original algebra/history/B/C/TCP conclusions unchanged. No matrix/model/native/optimizer/compiler/FK/Scene/SSH rerun or new work approval.'}
(OUT/'CORRECTION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['correct_unique_receipt_count','parent_count','per_cycle_counts','original_review_payloads_unchanged']}))
