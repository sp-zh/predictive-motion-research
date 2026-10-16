from pathlib import Path
import os,sys,json,hashlib,struct,math,importlib.util
sys.dont_write_bytecode=True;sys.path.insert(0,'/private/tmp')
from bounded_derived_bytes53_v1 import bounded_write
ROOT=Path('/Users/uot/Documents/ChatGPT/ros');BASE=Path('/private/tmp/phase5_merged_hint_diagnostics60_source_v2_20261016');O=Path('/private/tmp/root60_merged_review_v1_20261016');ROLE='CONSISTENT_SINGULAR_ACTIVE_FACE_KKT_AND_STOP_SELECTED_LEAVING_DIAGNOSTICS_V2'
spec=importlib.util.spec_from_file_location('strict60',ROOT/'tools/cold_storage_verification_v1/strict_codec_reader.py');strict=importlib.util.module_from_spec(spec);spec.loader.exec_module(strict)
class R:
 def __init__(self,b,role):
  self.b=b;self.at=0;assert self.text()=='P5_ACTIVE_SESSION_LOSSLESS_V1'and self.text()==role
 def take(self,fmt):
  n=struct.calcsize(fmt);assert self.at+n<=len(self.b);v=struct.unpack_from(fmt,self.b,self.at);self.at+=n;return v
 def text(self):
  n=self.take('<Q')[0];assert n<=1024**2 and self.at+n<=len(self.b);s=self.b[self.at:self.at+n].decode();self.at+=n;return s
 def end(self):assert self.at==len(self.b)
def merged(path,actual_rows=20000,events=None):
 b=strict.read_artifact_bytes(path);assert len(b)<=45056;r=R(b,ROLE);cycle,trial,available,stop,policy,count=r.take('<6Q');assert all(x in [0,1]for x in [available,stop,policy])and policy<=stop and policy<=available and count<=512;ranks=[];last=-1
 for _ in range(count):
  it,rank,dimension,residual=r.take('<3Qd');assert last<it<512 and 0<rank<=dimension<=288 and math.isfinite(residual)and 0<=residual<=1e-10
  if events is not None:assert it<len(events)and dimension==144+events[it][1]
  ranks.append((it,rank,dimension,residual));last=it
 count=r.take('<Q')[0];assert count<=512;chosen=[];last=-1
 for _ in range(count):
  it,row,side,pos,selected,minimum=r.take('<4q2d');assert last<it<512 and 0<=row<actual_rows and side in [-1,1]and 0<=pos<144 and all(math.isfinite(x)for x in [selected,minimum])and minimum<=selected<-1e-12
  if events is not None:assert it<len(events)and events[it][0]==it and events[it][2]==-1 and pos<events[it][1]and minimum==events[it][4]
  chosen.append((it,row,side,pos,selected,minimum));last=it
 scope=r.text();r.end();assert not chosen or policy;assert available or not(ranks or chosen or policy)
 return dict(cycle=cycle,trial=trial,hint_available=available,requested_stop=stop,policy_activated=policy,ranks=ranks,chosen=chosen,scope=scope,raw_bytes=len(b),raw_sha256=hashlib.sha256(b).hexdigest())
def main():
 os.environ['P5_DERIVED53_ROOT']=str(O);P=BASE/'pure_suite60_readback_v1';receipt=json.loads((P/'PRODUCER_RECEIPT.json').read_text())
 for e in receipt:
  b=(P/e['path']).read_bytes();assert len(b)==e['bytes']and hashlib.sha256(b).hexdigest()==e['sha256']
 result=json.loads((P/'RESULT.json').read_text());assert result['complete']and len(result['rows'])==24 and all(x['exit']==0 and x['Model_native_invocations']==0 for x in result['rows']);assert(P/'PURE_INPUT_BEFORE.json').read_bytes()==(P/'PURE_INPUT_AFTER.json').read_bytes()
 Q=P/'merged-hint-codec-tests';facts=[];maximum=None
 for case in ['maximum','active','unavailable','full-successful-24-roster']:
  path=Q/case/'hint_kkt_rank_events.bin';m=merged(path);n=512 if case!='unavailable'else 0;assert len(m['ranks'])==n
  for i,row in enumerate(m['ranks']):assert row==(i,144,288,0.)
  want=512 if case in ['maximum','full-successful-24-roster']else 0;assert len(m['chosen'])==want
  for i,row in enumerate(m['chosen']):assert row==(i,i,1 if i%2 else -1,i%144,-2.,-9.)
  if case=='maximum':maximum=m
  if case=='full-successful-24-roster':assert m['ranks']==maximum['ranks']and m['chosen']==maximum['chosen']
  assert(m['hint_available'],m['requested_stop'],m['policy_activated'])=={'maximum':(1,1,1),'active':(1,0,0),'unavailable':(0,1,0),'full-successful-24-roster':(1,1,1)}[case]
  facts.append(dict(case=case,raw_bytes=m['raw_bytes'],raw_sha256=m['raw_sha256'],rank_count=len(m['ranks']),chosen_count=len(m['chosen']),all_records_exact=True,codec=strict.verify_artifact(path)))
 binding=json.loads((BASE/'FROZEN_SUCCESSFUL24_ROSTER_BINDING.json').read_text());T=Q/'full-successful-24-roster';entries=strict.manifest_entries(T/'MANIFEST.yaml');assert list(entries)==binding['ordered_binary_names']and len(entries)==24 and not(T/'hint_negative_leaving_events.bin').exists();roster_receipts=[]
 for name in entries:
  path=T/name;roster_receipts.append(strict.verify_artifact(path))
  if name!='hint_kkt_rank_events.bin':
   r=R(strict.read_artifact_bytes(path),'SYNTHETIC_COMPLETE_TRIAL_ROSTER_SLOT_ONLY');assert r.take('<Q')==(0,);r.end()
 assert'SYNTHETIC_COMPLETE24_ROSTER_AND_EXPECTED25TH_REFUSAL'in(T/'MANIFEST.yaml').read_text()
 report=dict(schema='ROOT60_FULL_MERGED512_AND_ORDERED24_OUTPUT_CHAIN_REVIEW_V1',producer_payload_hashes_verified=len(receipt),pure24_pass=True,pure_no_model_native_invocations=True,pure_before_after_inputs_byte_equal=True,new_codec_cases=facts,all24_ordered_files_complete_SHA_CRC_EOF=True,last_cycle_timing_retained=True,expected_25th_separate_file_absent=True,all24_file_receipts=roster_receipts,retained_reader_error='Initial audit script used an invalid Python keyword starting25th, SyntaxError before imports/reads/writes. Corrected identifier only; no test, capture or native rerun.',scope='Synthetic output-count integration and complete codec data only; original24 cap/reader retained. No Model/physicalC/stop/task/phase acceptance. Scalar records are not full eligible-working-set proof.')
 bounded_write(O/'PURE24_MERGED_AND_FULL_ROSTER_REVIEW.json',json.dumps(report,indent=2)+'\n');print(json.dumps(dict(pure=24,payloads=len(receipt),cases=[(x['case'],x['rank_count'],x['chosen_count'],x['raw_bytes'])for x in facts],ordered24_complete=True)))
if __name__=='__main__':main()
