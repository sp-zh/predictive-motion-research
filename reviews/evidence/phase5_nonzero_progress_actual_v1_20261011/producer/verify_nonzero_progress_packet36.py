from pathlib import Path
import hashlib,json,csv,struct,math
P=Path('/private/tmp/phase5_nonzero_progress_actual_checkpoint_v1_20261011');runtime=P/'actual-dell/session-nonzero-progress-planning-tail-three-cycle-v1-20261011-attempt36/run-attempt1';all_before=json.loads((runtime/'BEFORE_INPUT_IDENTITIES.json').read_text());all_after=json.loads((runtime/'AFTER_INPUT_IDENTITIES.json').read_text());assert all_before==all_after and len(all_before)==1703
result=json.loads((runtime/'BUILD_RESULT.json').read_text());assert result['complete'] and len(result['records'])==1 and result['records'][0]['exit']==0 and not result['records'][0]['stop_reason']
receipts=[]
for p in sorted((runtime/'artifacts').rglob('MANIFEST.yaml')):
 # YAML is available via remote; local dependency-free manifest extraction uses
 # emitted fixed scalar lines, never treats this as generic YAML parser.
 lines=p.read_text().splitlines();files=[];current=None
 for s in lines:
  t=s.strip()
  if t.startswith('- file: '):
   if current:files.append(current)
   current={'file':t[len('- file: '):]}
  elif current and ': ' in t:
   key,value=t.split(': ',1);current[key]=value
 if current:files.append(current)
 assert files and all(f['complete']=='true' and f['hash_valid']=='true' for f in files)
 for f in files:
  q=p.parent/f['file'];b=q.read_bytes();assert len(b)==int(f['bytes']) and hashlib.sha256(b).hexdigest()==f['sha256'],q
 receipts.append({'path':str(p.relative_to(P)),'binary_receipts':len(files)})
for k in range(3):
 d=runtime/'artifacts'/f'cycle-{k}';events=list(csv.reader((d/'actual_commit_journal.csv').open()));expected=['BEFORE_VALIDATED_HELD_TARGET_WRITE','VALIDATED_HELD_TARGET_WRITTEN_NO_STEP_YET']+2*['BEFORE_NATIVE_COMMIT_STEP_ATTEMPT','NATIVE_COMMIT_STEP_RETURNED_BEFORE_SCRATCH','COMPLETE_ACTUAL_COMMIT_OBSERVATION_AND_GEOMETRY'];assert [e[0] for e in events]==expected and len(events)==8
assert len(list(csv.reader((runtime/'artifacts/actual_step_journal.csv').open())))==3000
out={'schema':'PRODUCER_NONZERO_PROGRESS_FULL_CAPTURE_VERIFICATION_V1','before_after_identity_requests_verified':1703,'unique_requested_paths':len({r['requested_path'] for r in all_before}),'runtime_exit0_complete':True,'all_manifest_receipts':receipts,'binary_receipts_verified':sum(r['binary_receipts'] for r in receipts),'warmup_durable_journal_events':3000,'actual_commit_journal_events':[8,8,8],'scope':'byte hashing + fixed emitted manifests and event order, not independent native recomputation/collision engine/fault-injection proof'};(P/'CAPTURE_VERIFICATION.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
