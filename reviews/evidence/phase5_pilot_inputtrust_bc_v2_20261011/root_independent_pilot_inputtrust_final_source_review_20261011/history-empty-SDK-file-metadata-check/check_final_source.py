"""Final frozen source/profile metadata review only; no derive/matrix/runtime call."""
from pathlib import Path
import hashlib,json,difflib
OUT=Path(__file__).resolve().parent
SRC=Path('/private/tmp/phase5_pilot_inputtrust_ahead_review_v3_20261010')
PURE=Path('/private/tmp/phase5_pilot_inputtrust_pure_profile_v3_20261010')
OLD=Path('/private/tmp/phase5_pilot_inputtrust_ahead_review_v1_20261010')
BASE=Path('/private/tmp/phase5_pilot_bc_ahead_review_v5_20261010')
def sha(b):return hashlib.sha256(b).hexdigest()
def packet(path,pin):
 b=(path/'READY.json').read_bytes();assert sha(b)==pin
 m=json.loads(b)['files'];files={}
 for name,v in m.items():
  rel=Path(name);assert not rel.is_absolute() and '..' not in rel.parts
  data=(path/name).read_bytes();assert len(data)==v['bytes'] and sha(data)==v['sha256'];files[name]=data
 return b,files
source=Path(__file__).read_bytes()
sr,n=packet(SRC,'374c592d7a1481c9860953612f4623ee054e1a6683f5a7d3ee46d7e9caa1da51')
pr,p=packet(PURE,'3895d4418205e9fc5c8cf9a962f84df8f6f1b8fbc95f11aab0b89e237c120aee')
old,o=packet(OLD,'9b0c2f7327d7853e1f5544d6d9f6fd39318f3bb6ceb107522979c5bf02fc17dd')
baser,b=packet(BASE,'7495e8ecd0bf8c169eda2eb3bd18471e0bc48c556390bd6ae5eac54a86b9dc97')
assert len(n)==27 and len(p)==3 and p['derive_numeric_guess.py']==n['derive_numeric_guess.py']
changed=[k for k in o if o[k]!=n[k]];assert sorted(changed)==['PROTOCOL.json','derive_numeric_guess.py','src/integrated_horizon_qp.cpp']
cpp=n['src/integrated_horizon_qp.cpp'];start=cpp.index(b'void solveOnceStabilizationInputTrustNumericGuess(');end=cpp.index(b'Eigen::VectorXd shiftControlGuess(',start)
assert cpp[:start]+cpp[end:]==b['src/integrated_horizon_qp.cpp']
plan=json.loads(p['pure_plan.json']);assert sha(p['pure_plan.json'])=='2c01609b28f8a54dd9b4bdb5230059d43f1cd1da01b8b0a77814a241e92d0472'
assert plan['schema']=='PILOT_INPUTTRUST_PURE_RUNTIME_V1' and len(plan['input_files'])==1350 and len(plan['compile_argv'])==1
assert plan['env']=={'PATH':'/usr/bin:/bin','LANG':'C','LC_ALL':'C','TZ':'UTC'}
inputs={x['requested_path']:x for x in plan['input_files']};assert len(inputs)==1350
for row in inputs.values():assert row['bytes']>0 and len(row['sha256'])==64 and row['requested_path']==row['resolved_path']
expected={
 'task-start-stabilization-numeric-guess-v1-20261010-repair2/ACTUAL_STABILIZATION_INPUTS.npz':'f4f8d7c0fbb42e270279d83a83c7746b52107670352800da8bd5409ba1417e12',
 'task-start-linear-oracle-v2-20261010-attempt1/oracle-artifacts-attempt1/ACTUAL_ORACLE_INPUTS.npz':'3fa8228457f27b66208a1b3b02547b0727a65946a99bc9e2651c8f98d1decdc0',
 'task-start-numeric-guess-v1-20261010/guess.json':'b9563e031892611491bfab40d7126e5de3858f25dc2adb85bc132fd6904fce01'}
for suffix,h in expected.items():
 matches=[x for name,x in inputs.items() if name.endswith('/'+suffix)];assert len(matches)==1 and matches[0]['sha256']==h
argv=plan['compile_argv'][0];assert argv[:8]==['/usr/bin/env','OPENBLAS_NUM_THREADS=1','OMP_NUM_THREADS=1','MKL_NUM_THREADS=1','/usr/bin/python3.12','-I','-S','-B'] and len(argv)==9
assert inputs[argv[-1]]['sha256']==sha(n['derive_numeric_guess.py']) and inputs[argv[-1]]['bytes']==len(n['derive_numeric_guess.py'])
assert plan['readonly_directory_rosters']==[]
for group,files in [('source',n),('pure-profile',p)]:
 for name,data in files.items():
  target=OUT/'read-snapshot'/group/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
(OUT/'SOURCE_READY_READ.json').write_bytes(sr);(OUT/'PURE_READY_READ.json').write_bytes(pr);(OUT/'PREVIOUS_SOURCE_READY_READ.json').write_bytes(old)
(OUT/'SOURCE_DELTA.diff').write_text(''.join(''.join(difflib.unified_diff(o[name].decode().splitlines(True),n[name].decode().splitlines(True),fromfile='Inputtrust1/'+name,tofile='Inputtrust3/'+name)) for name in changed))
r={'schema':'ROOT_INPUTTRUST_FINAL_SOURCE_PURE_PROFILE_REVIEW_V1','source_sha256':sha(source),'source_ready_sha256':sha(sr),'pure_ready_sha256':sha(pr),'source_payloads':27,'source_bytes':sum(map(len,n.values())),'pure_payloads':3,'pure_bytes':sum(map(len,p.values())),'changed_previous_payloads':changed,'all_existing_core_cpp_bytes_preserved':True,'pure_plan_hash':sha(p['pure_plan.json']),'declared_input_files':1350,'declared_data_hashes_match_previous_audits':True,'derive_source_matches_plan_and_source_freeze':True,'actual_remote1350_hash_check_performed_here':False,'source_selection_assertions_present':True,'ordinary_failure_final_input_and_SDK_checks_present':True,'invalid_hint_exit1_present':True,'source_request_catch_reset_repair_present':True,'math_guard_proof_reused_READY':'15ba759f6ff86dc38720d16d9d969257c889080c1d85f2100eb1409511cbe9d4','scope':'source/profile metadata only; no matrix/optimizer/Model/native execution','verdict':'SOURCE_AND_FROZEN_PURE_PLAN_DELTA_CONSISTENT','runtime_release':False,'phase5_accepted':False}
assert packet(SRC,sha(sr))==(sr,n) and packet(PURE,sha(pr))==(pr,p) and Path(__file__).read_bytes()==source
(OUT/'SOURCE_SNAPSHOT.py').write_bytes(source);(OUT/'RESULT.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
