from pathlib import Path
import os,sys,json,hashlib,re,struct
import numpy as np
sys.path.insert(0,'/private/tmp');from bounded_derived_bytes53_v1 import bounded_write
import root63_nominal_reader_v4 as n
import root62_nominal_reader_v3b as old
P=Path('/private/tmp/phase5_current_braking_nominal63_source_v1_20261016');S=P/'src-final-v1';R=Path('/Users/uot/Documents/ChatGPT/ros');O=Path('/private/tmp/root63_review_v1_20261016');os.environ['P5_DERIVED53_ROOT']=str(O);sha=lambda b:hashlib.sha256(b).hexdigest()
j=json.loads((S/'SOURCE_IDENTITIES.json').read_text());assert len(j['files'])==93 and len(list(S.iterdir()))==94
for name,e in j['files'].items():
 b=(S/name).read_bytes();assert len(b)==e['bytes']and sha(b)==e['sha256']
prev=R/'tools/phase5_controlled_stop_session_v15';pj=json.loads((prev/'SOURCE_IDENTITIES.json').read_text());changed=[k for k in pj['files']if(S/k).read_bytes()!=(prev/k).read_bytes()];added=sorted(set(j['files'])-set(pj['files']));assert set(changed)=={'README.md','active_first_cycle.cpp'}and set(added)=={'current_braking_nominal63.hpp','current_braking_nominal63_tests.cpp','braking_nominal63_codec.hpp'}
a=json.loads((prev/'profile/active_input.json').read_text());b=json.loads((P/'profile-version1/active_input.json').read_text());diff=[k for k in a.keys()|b.keys()if a.get(k)!=b.get(k)];assert set(diff)=={'session_id','current_braking_nominal62'}
codec=(S/'braking_nominal63_codec.hpp').read_text();assert 'maximum_header_scope==3192'in codec and 'maximum_proven_payload==109056'in codec
assert 1080*96+1280+4096==109056<131072 and 133*7+149==1080 and 144*131072==18874368 and 1799506160+89*2048==1799688432<1800000000 and 744912+48==744960<745000
Q=P/'pure_suite63_readback_v1';rc=json.loads((Q/'PRODUCER_RECEIPT.json').read_text())
for e in rc:
 b=(Q/e['path']).read_bytes();assert len(b)==e['bytes']and sha(b)==e['sha256']
result=json.loads((Q/'RESULT.json').read_text());assert len(result['rows'])==27 and result['complete']and all(x['exit']==0 and x['Model_native_invocations']==0 for x in result['rows']);assert(Q/'PURE_INPUT_BEFORE.json').read_bytes()==(Q/'PURE_INPUT_AFTER.json').read_bytes()
text=(S/'current_braking_nominal63_tests.cpp').read_text();warm=np.zeros((20,8))
for k in range(20):
 al=re.findall(r'warm\['+str(k)+r'\]\.alpha=\{([^}]+)\}',text);bs=re.findall(r'warm\['+str(k)+r'\]\.b=([^;]+);',text);assert len(al)==len(bs)==1;warm[k,:7]=[float(v)for v in al[0].split(',')];warm[k,7]=float(bs[0])
actualwarm=np.array(json.loads((O/'WARM53_INPUT_CONTROLS.json').read_text()));assert np.array_equal(actualwarm,warm)
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
report=dict(schema='ROOT63_FROZEN94_SOURCE_PROFILE_PURE27_AND_WARM_PROVENANCE_REVIEW_V1',all93_manifest_payloads_verified=True,total_source_files=94,changed_old_files=changed,unchanged_old_payloads=88,added_files=added,profile_changed_keys=diff,all_numeric_QP_original_SI_cost_initializer_nonlinear_geometric_history_B_C_stop_sources_byteexact62=True,record_bytes=96,maximum_attempts=1080,maximum_payload=109056,hard_file_cap=131072,all144_stop_files_max=18874368,whole_numeric_upper=1799688432,conservative_hint_peak=744960,pure_payloads_SHA_verified=len(rc),all27_pure_exit0_declared_no_Model_native=True,pure_input_before_after_equal=True,warm_literal_all160_doubles_equal_actual63_previous52_accepted_candidate_overlap_shift=True,history_fields_equal_exact_actual62_failure53=True,new_pure_cases=out,trial1_no_rebuild=True,synthetic_max1080=True,old62_perturbed74_fixture_preserved_and_qualified=True,scope='Frozen-source and saved scalar/helper review. Warm original1/.5,20/5 limits do not inherit analytic .999 planning margins; old analytic margins unchanged. No owner/token/permission transfer. Not full physical stop/task/realtime/phase proof. Original63 numeric512 failure remains.')
bounded_write(O/'SOURCE94_PURE27_AND_WARM_PROVENANCE.json',json.dumps(report,indent=2)+'\n');print(json.dumps({'source94':True,'unchanged88':True,'pure27':True,'new_scalar156_success_and156_failure':True,'max1080':True}))
