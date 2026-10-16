from pathlib import Path
import os,sys,json,hashlib,re,struct
import numpy as np
sys.path.insert(0,'/private/tmp');from bounded_derived_bytes53_v1 import bounded_write
import root63_nominal_reader_v4 as n
import root62_nominal_reader_v3b as old
P=Path('/private/tmp/phase5_roundoff_command64_source_v1_20261016');S=P/'src-final-v1';O=Path('/private/tmp/root64_saved63_cause_review_v1_20261016');os.environ['P5_DERIVED53_ROOT']=str(O);sha=lambda b:hashlib.sha256(b).hexdigest()
Q=P/'pure_suite64_readback_v1';rc=json.loads((Q/'PRODUCER_RECEIPT.json').read_text())
for e in rc:
 b=(Q/e['path']).read_bytes();assert len(b)==e['bytes']and sha(b)==e['sha256']
result=json.loads((Q/'RESULT.json').read_text());assert len(result['rows'])==28 and result['complete']and all(x['exit']==0 and x['Model_native_invocations']==0 for x in result['rows']);assert(Q/'PURE_INPUT_BEFORE.json').read_bytes()==(Q/'PURE_INPUT_AFTER.json').read_bytes()
text=(S/'current_braking_nominal63_tests.cpp').read_text();warm=np.zeros((20,8))
for k in range(20):
 al=re.findall(r'warm\['+str(k)+r'\]\.alpha=\{([^}]+)\}',text);bs=re.findall(r'warm\['+str(k)+r'\]\.b=([^;]+);',text);assert len(al)==len(bs)==1;warm[k,:7]=[float(v)for v in al[0].split(',')];warm[k,7]=float(bs[0])
actualwarm=np.array(json.loads((Path('/private/tmp/root63_review_v1_20261016')/'WARM53_INPUT_CONTROLS.json').read_text()));assert np.array_equal(actualwarm,warm)
A=next(Path('/private/tmp/phase5_controlled_stop_current_braking_nominal_terminal62_v3_20261016').glob('actual-dell/*/run-attempt1/artifacts'));actual=old.parse(A/'cycle-53/trial-0/stop_objective_mode.bin',source_complete=False);C=json.loads(Path('/private/tmp/root62_stop_cause_review_v1_20261016/PINNED_PUBLIC_CONSTANTS.json').read_text());base=Q/'current-braking-warm-nominal63-tests';out=[]
for case,complete,guess in [('saved62-current53-explicit-warm',True,warm),('saved62-current53-explicit-warm-refused',False,warm.copy())]:
 if not complete:guess[0,7]=.6
 o=n.parse(base/case/'stop_objective_mode.bin',source_complete=complete);assert tuple(o[k]for k in['C','w','alpha','s','r','b'])==tuple(actual[k]for k in['C','w','alpha','s','r','b']);f=n.replay(o,C,guess);assert len(o['records'])==156
 if complete:assert o['summary'][7][:2]==(148,149)and f['successful_channels']==list(range(8))
 else:assert not o['terminal']and o['records'][-1][0:3]==(7,148,2)
 out.append(dict(case=case,replay=f,source_complete=complete))
o=n.parse(base/'trial1-no-rebuild/stop_objective_mode.bin');assert not o['records']and o['controls'][0,7]==.123 and not o['regenerate']
b=n.strict.read_artifact_bytes(base/'max1080-stream/stream.bin');r=n.R(b,'SYNTHETIC1080_STORAGE_BOUND_NO_MODEL');count=0
for c in range(8):
 for f in range(149 if c==7 else 133):assert r.take('<6Q6d')==(1,c,f,3,0,0,0.,0.,0.,0.,6.,5.);count+=1
r.end();assert count==1080

prior=Path('/private/tmp/phase5_current_braking_nominal63_source_v1_20261016/pure_suite63_readback_v1');exact=0
for sub in ['current-braking-warm-nominal63-tests','current-braking-nominal-tests']:
 for p in (Q/sub).rglob('*.bin'):
  assert p.read_bytes()==(prior/p.relative_to(Q)).read_bytes();exact+=1
assert exact>=10
newtest=(Q/'roundoff_command64_tests.stdout').read_text();assert 'PASS' in newtest and not(Q/'roundoff_command64_tests.stderr').read_bytes()
report=dict(schema='ROOT64_PURE28_ALL_HASHES_AND_ORIGINAL_NOMINAL_CORES_REVIEW_V1',payloads=len(rc),all28_exit0_declared_no_Model_native=True,pure_input_before_after_equal=True,all_inherited_nominal_binary_streams_byteexact63=exact,new_warm_success_failure_records_recomputed=out,trial1_preserved=True,max1080=True,new_roundoff_command_counterexamples_stdout=newtest,scope='Pure helper/source tests. Old analytic/warm family and saved scalar failures preserved; new opt-in boundary/domain/trueoutside/positive-slack/activefalse/firstguard/strict refusal tested. Formal all8 numerical default and new10 policy matrices separately audited. No physical stop or native64 entry implication.')
bounded_write(O/'PURE28_INHERITED_NOMINAL_AND_OPTIN_TEST_REVIEW.json',json.dumps(report,indent=2)+'\n');print(json.dumps({'payloads':len(rc),'pure28':True,'old_nominal_binary_exact':exact,'new_counterexamples_PASS':True}))
