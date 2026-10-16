from pathlib import Path
import sys,os,json,struct,hashlib,ast,math
import numpy as np
sys.dont_write_bytecode=True;sys.path.insert(0,'/private/tmp')
from bounded_derived_bytes53_v1 import bounded_write
import root60_merged_parser_and_tests_v1 as m60
strict=m60.strict
ROOT=Path('/Users/uot/Documents/ChatGPT/ros');BASE=Path('/private/tmp/phase5_exact_cycle_endpoint61_source_v1_20261016');O=Path('/private/tmp/root61_cycle_review_v1_20261016');os.environ['P5_DERIVED53_ROOT']=str(O)
ROLE='CONSISTENT_SINGULAR_KKT_STOP_LEAVING_AND_EXACT_CYCLE_ENDPOINT_ELIGIBILITY_V3'
def parse(path,actual_rows=20000,events=None):
 b=strict.read_artifact_bytes(path);assert len(b)<=46208;r=m60.R(b,ROLE);cycle,trial,available,stop,policy,count=r.take('<6Q');assert count<=512 and all(x in[0,1]for x in[available,stop,policy])and policy<=stop and policy<=available;ranks=[];last=-1
 for _ in range(count):
  it,rank,dim,res=r.take('<3Qd');assert last<it<512 and 0<rank<=dim<=288 and math.isfinite(res)and 0<=res<=1e-10
  if events is not None:assert it<len(events)and dim==144+events[it][1]
  ranks.append((it,rank,dim,res));last=it
 count=r.take('<Q')[0];assert count<=512;chosen=[];last=-1
 for _ in range(count):
  it,row,side,pos,selected,minimum=r.take('<4q2d');assert last<it<512 and 0<=row<actual_rows and side in[-1,1]and 0<=pos<144 and all(math.isfinite(x)for x in[selected,minimum])and minimum<=selected<-1e-12
  if events is not None:assert it<len(events)and events[it][0]==it and events[it][2]==-1 and pos<events[it][1]and minimum==events[it][4]
  chosen.append((it,row,side,pos,selected,minimum));last=it
 exact,n,count=r.take('<3Q');assert exact in[0,1]and exact<=policy and n<=144 and count<=n;indices=list(r.take('<'+str(count)+'Q'))if count else[];assert indices==sorted(set(indices));rows=[]
 for index in indices:
  assert index<len(chosen);e=chosen[index];assert any(q[0]+2==e[0]and q[1:4]==e[1:4]for q in chosen[:index]);rows.append(e[1])
 assert len(set(rows))==len(rows)and(not indices or exact)and(available or not(ranks or chosen or exact or indices));scope=r.text();r.end()
 return dict(cycle=cycle,trial=trial,available=available,stop=stop,policy=policy,ranks=ranks,chosen=chosen,exact=exact,n=n,indices=indices,raw_bytes=len(b),scope=scope)
def check_receipt(p,name='PRODUCER_RECEIPT.json'):
 j=json.loads((p/name).read_text())
 for e in j:
  b=(p/e['path']).read_bytes();assert len(b)==e['bytes']and hashlib.sha256(b).hexdigest()==e['sha256']
 return len(j)
def main():
 Q=BASE/'pure_suite61_readback_v1';number=check_receipt(Q);j=json.loads((Q/'RESULT.json').read_text());assert len(j['rows'])==25 and j['complete']and all(x['exit']==0 and x['Model_native_invocations']==0 for x in j['rows']);assert(Q/'PURE_INPUT_BEFORE.json').read_bytes()==(Q/'PURE_INPUT_AFTER.json').read_bytes()
 T=Q/'exact-cycle-codec-tests';assert(T/'maximum/hint_kkt_rank_events.bin').exists();facts=[]
 for case in ['maximum','not-entered','unavailable','active','full-successful-24-roster']:
  p=T/case/'hint_kkt_rank_events.bin';m=parse(p)
  if case in['maximum','full-successful-24-roster']:
   assert(len(m['ranks']),len(m['chosen']),m['exact'],m['n'])==(512,512,1,144)and m['indices']==[3*i+2 for i in range(144)]
   for i,e in enumerate(m['ranks']):assert e==(i,144,288,0.)
   for i,e in enumerate(m['chosen']):
    it,row,side,pos,selected,minimum=e;assert it==i and selected==-2 and minimum==-9
    if i<432 and i%3 in[0,2]:assert(row,side,pos)==(i//3,-1,i//3)
    else:assert(row,side,pos)==(1000+i,1 if i%2 else-1,i%144)
  else:assert not(m['ranks']or m['chosen']or m['indices']or m['exact'])
  facts.append(dict(case=case,rank_count=len(m['ranks']),chosen_count=len(m['chosen']),eligibility_count=len(m['indices']),raw_bytes=m['raw_bytes']))
 T=T/'full-successful-24-roster';entries=strict.manifest_entries(T/'MANIFEST.yaml');assert len(entries)==24 and 'cycle_timing.bin'in entries and 'hint_negative_leaving_events.bin'not in entries
 for name in entries:strict.verify_artifact(T/name)
 pure=dict(schema='ROOT61_PURE25_COMPLETE_V3_MAX144_AND24_SLOTS_V1',payload_hashes_verified=number,all25_exit0_no_model_native=True,pure_before_after_bytes_equal=True,cases=facts,all24_receipts_full_SHA_CRC_EOF=True,expected25th_file_absent=True,retained_reader_qualification='First glob found older V2 maximum test files as well as newV3, so unique-match assertion failed before output writes. Corrected to explicit exact-cycle-codec-tests; no replay, capture or native retry.',scope='Synthetic output/eligibility unit tests, not controller/physical/phase acceptance. Max scalar indices do not store full comparison snapshots.')
 bounded_write(O/'PURE25_V3_MAX144_AND_ROSTER_REVIEW.json',json.dumps(pure,indent=2)+'\n')
 # Generic saved-array readers from prior reviewed auditors; no audit mains executed.
 tree=ast.parse(Path('/private/tmp/root58_selected_audit_v1.py').read_text());exec(compile(ast.Module(body=[x for x in tree.body if isinstance(x,ast.ClassDef)and x.name in['R','RV4']],type_ignores=[]),'<Reader-only>','exec'),globals())
 tree=ast.parse(Path('/private/tmp/root59_production_review_v1.py').read_text());exec(compile(ast.Module(body=[x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name in['sha','fixture','xy']],type_ignores=[]),'<array-functions-only>','exec'),globals())
 P=BASE/'production_math_pure_v1/readback';number=check_receipt(P);j=json.loads((P/'RESULT.json').read_text());assert all(x['exit']==0 for x in j['records'])and j['input_before_after_equal'];old60=Path('/private/tmp/phase5_merged_hint_diagnostics60_source_v2_20261016/production_math_pure_v1/readback');oldfixtures=Path('/private/tmp/phase5_global_interval_initializer58_source_v1_20261016/production_math_pure_v1');old54=Path('/private/tmp/phase5_negative_leaving59_source_v1_20261016/production_math_pure_v1/actual58_54_0.initialized.fixture');cases=['actual56_48_1','old52_40_0','old53_40_1','old54_43_0','old55_40_2','actual58_54_0','actual58_74_0','actual60_43_0'];out=[]
 for case in cases:
  f=oldfixtures/(case+'.fixture')
  if case=='actual58_54_0':f=old54
  if case=='actual58_74_0':f=Path('/private/tmp/phase5_iteration74_analysis59_v1_20261016/actual58_current74_trial0.initialized.fixture')
  if case=='actual60_43_0':f=Path('/private/tmp/phase5_bland_cycle43_analysis61_v1_20261016/actual60_current43_trial0.initialized.fixture')
  (H,g,A,lo,hi,seed),b=fixture(f);pin=next(v for k,v in j['input_pins'].items()if k.endswith('/'+f.name));assert pin['sha256']==sha(b)and pin['bytes']==len(b);prefix=P/('stop_'+case);x,y=xy(Path(str(prefix)+'.finalxy.bin'));v=max(0.,float(np.max(lo-A@x)),float(np.max(A@x-hi)));s=float(np.max(np.abs(H@x+g+A.T@y)));assert v<=1e-12 and s<=1e-10
  states=Path(str(prefix)+'.states.bin').read_bytes();assert len(states)%56==0 and 0<len(states)<=512*56;events=[struct.unpack_from('<3q4d',states,i)for i in range(0,len(states),56)];d=Path(str(prefix)+'.leaving');m=parse(d/'hint_kkt_rank_events.bin',len(lo),events);legacy=m60.merged(d/'legacy_merged_v2.bin',len(lo),events);assert m['ranks']==legacy['ranks']and m['chosen']==legacy['chosen'];assert b''.join(struct.pack('<3Qd',*e)for e in m['ranks'])==b''.join(struct.pack('<3Qd',*e)for e in legacy['ranks']);assert b''.join(struct.pack('<4q2d',*e)for e in m['chosen'])==b''.join(struct.pack('<4q2d',*e)for e in legacy['chosen'])
  core={}
  if case!='actual60_43_0':
   for ext in['finalxy.bin','states.bin','boundary48.bin','retained64.bin','refinement120.bin']:
    core[ext]=Path(str(prefix)+'.'+ext).read_bytes()==(old60/('stop_'+case+'.'+ext)).read_bytes();assert core[ext]
   assert not m['indices']
  else:
   assert len(events)==284 and len(m['indices'])==6 and [m['chosen'][i][1]for i in m['indices']]==[7250,7251,7252,7253,7254,7277]and sha(Path(str(prefix)+'.finalxy.bin').read_bytes())=='31e7612c6c9fc52cb714ae52225d8d38634547bfb8989bfe3dc42bebf9ceab97'
  endpoint=Path(str(prefix)+'.retained64.bin').read_bytes();assert len(endpoint)%64==0 and len(endpoint)<=16384*64
  for at in range(0,len(endpoint),64):
   it,row,start,travel,value,l,u,violation=struct.unpack_from('<2q6d',endpoint,at);assert 0<=it<512 and 0<=row<len(lo)and np.isfinite([start,travel,value,l,u,violation]).all()and violation==max(0.,l-value,value-u)<=1e-12
  out.append(dict(case=case,fixture_sha256=sha(b),events=len(events),full_rows=len(lo),primal_numpy=v,stationarity_numpy=s,old60_five_core_bytes_equal=core,rank_count=len(m['ranks']),chosen_count=len(m['chosen']),eligibility_count=len(m['indices']),same_Result_all_old_V2_records_exact=True))
 active=[]
 for case in['old52_40_0','old53_40_1','old54_43_0','ACTIVE_constrained','ACTIVE_interior','ACTIVE_zero']:
  b=(P/('active_'+case+'.core.bin')).read_bytes();assert b==(old60/('active_'+case+'.core.bin')).read_bytes();active.append(dict(case=case,sha256=sha(b),entire_core_byte_equal60=True))
 report=dict(schema='ROOT61_FORMAL8STOP6ACTIVE_ORIGINAL_GATES_AND_V3_RECORD_REVIEW_V1',payload_hashes_verified=number,all_driver_commands_exit0=True,input_before_after_equal_report=True,eight_saved_stop=out,six_active=active,scope='Saved numerical hint only. Prior7 five-core bytes and6 active cores exact60; same Result V2/V3 records complete, not independent eligible-state snapshots or generic convergence. All original native/SI/nonlinear/B/C/physical/stop/task gates remain.')
 bounded_write(O/'FORMAL8_STOP6_ACTIVE_V3_REVIEW.json',json.dumps(report,indent=2)+'\n');print(json.dumps(dict(pure25=True,maxcases=facts,formal_payloads=number,stop=[(x['case'],x['events'],x['eligibility_count'])for x in out],active6_equal=True)))
if __name__=='__main__':main()
