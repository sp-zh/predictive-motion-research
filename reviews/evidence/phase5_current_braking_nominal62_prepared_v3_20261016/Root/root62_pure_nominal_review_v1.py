from pathlib import Path
import sys,os,json,hashlib,struct
import numpy as np
sys.path.insert(0,'/private/tmp');from bounded_derived_bytes53_v1 import bounded_write
import root62_nominal_reader_v3b as reader
strict=reader.strict;R=reader.R
O=Path('/private/tmp/root62_stop_cause_review_v1_20261016');os.environ['P5_DERIVED53_ROOT']=str(O);P=Path('/private/tmp/phase5_current_braking_nominal62_source_v3_20261016/pure_suite62_readback_v3');C=json.loads((O/'PINNED_PUBLIC_CONSTANTS.json').read_text());receipts=json.loads((P/'PRODUCER_RECEIPT.json').read_text())
for e in receipts:
 b=(P/e['path']).read_bytes();assert len(b)==e['bytes']and hashlib.sha256(b).hexdigest()==e['sha256']
result=json.loads((P/'RESULT.json').read_text());assert result['complete']and len(result['rows'])==26 and all(x['exit']==0 and x['Model_native_invocations']==0 for x in result['rows']);assert(P/'PURE_INPUT_BEFORE.json').read_bytes()==(P/'PURE_INPUT_AFTER.json').read_bytes()
def snapshot(path):
 r=R(strict.read_artifact_bytes(path),'ACTUAL_NATIVE_SESSION_SNAPSHOT');r.text();r.text();r.take('<3Q');r.text();r.text();r.take('<3Q');r.take('<2d');r.u();q,v,C,w=[list(r.take('<7d'))for _ in range(4)];s,rate=r.take('<2d');a=list(r.take('<7d'));b=r.d();r.u();r.take('<14d');r.u();r.text()
 for _ in range(2):n=r.u();assert n<=4096;r.take('<'+str(n)+'d')
 r.end();return C,w,a,s,rate,b
A=next(Path('/private/tmp/phase5_controlled_stop_exact_cycle_terminal61_v1_20261016').glob('actual-dell/*/run-attempt1/artifacts'));sources=[O/'saved61_onset32_trial1/observation_before.bin',*[A/(x+'/observation_before.bin')for x in['cycle-43/trial-0','cycle-43/trial-1','cycle-74/trial-0','cycle-95/trial-0']]];base=P/'current-braking-nominal-tests';out=[];parsed=[]
for i,source in enumerate(sources):
 o=reader.parse(base/f'saved-{i}/stop_objective_mode.bin');C0,w,a,s,rate,b=snapshot(source);assert(o['C'],o['w'],o['alpha'],o['s'],o['r'],o['b'])==(C0,w,a,s,rate,b);f=reader.replay(o,C);assert f['successful_channels']==list(range(8));parsed.append(o);out.append(dict(case=['actual61_32','actual61_43_0','actual61_43_1','actual61_74','actual61_95'][i],source_history_values_exact=True,recomputed=f,selected_families=[e[0]for e in o['summary']],raw_bytes=o['raw_bytes']))
assert out[0]['selected_families'][7]==132 and out[0]['recomputed']['counts_per_channel'][7]==133
retry=reader.parse(base/'not-regenerated-rejected-B-trial1/stop_objective_mode.bin');want=parsed[0]['controls'].copy();want[0,0]=np.nextafter(want[0,0],1.);assert np.array_equal(retry['controls'],want)and not retry['regenerate']and not retry['records']
failure=reader.parse(base/'all132-real-refusals/stop_objective_mode.bin',source_complete=False);assert not failure['terminal']and len(failure['records'])==132 and all(x[0]==0 and x[2]for x in failure['records']);failed=reader.replay(failure,C)
b,receipt=strict.verify_artifact(base/'synthetic-record-bound/stream.bin',collect=True);r=R(b,'SYNTHETIC_MAX1072_NOMINAL_RECORD_STORAGE_BOUND_ONLY');count=0
for c in range(8):
 for f in range(148 if c==7 else 132):assert r.take('<6Q6d')==(1,c,f,3,0,0,0.,0.,0.,0.,6.,5.);count+=1
r.end();assert count==1072
report=dict(schema='ROOT62V3_PURE26_ALL_FAMILY_COUNTEREXAMPLES_AND_NEW_CODEC_REVIEW_V1',payload_hashes_verified=len(receipts),all26_exit0_declared_no_Model_native=True,pure_input_before_after_bytes_equal=True,saved_cases=out,source_case_metadata_qualification='Pure saved fixtures serialize synthetic cycle43 tags; source history values bind actual32/43x2/74/95. These are not native Model observations or owner/token factories.',rejected_B_trial1_controls_preserved=True,source_incomplete_real132_exhaustion=dict(source_complete=False,terminal_available=False,replay=failed),synthetic_max_records=1072,scope='Independent complete finite-family/reason/cell/step/observed-bound and scalar literal200macro400half/jerk/domain/lastcell input review. Old26 preparation suite not physical stop, native entry, full24 V3 transaction or SI/nonlinear/B/C acceptance. Complete prefix storage is distinct from source completion.')
bounded_write(O/'PURE26_V3_FAMILY_FULL_RECOMPUTATION.json',json.dumps(report,indent=2)+'\n');print(json.dumps({'payloads':len(receipts),'cases':[(x['case'],x['recomputed']['attempts'],x['selected_families'][7])for x in out],'real_failed_prefix132':True,'synthetic_max':count,'26_exit0':True}))
