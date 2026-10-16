import sys,os,json,ast,struct,hashlib,numpy as np
from pathlib import Path
sys.path.insert(0,'/private/tmp');sys.path.insert(0,'/private/tmp/root65_codec_independent_review_v1_20261016')
from bounded_derived_bytes53_v1 import bounded_write
import reader
O=Path('/private/tmp/root65_codec_independent_review_v1_20261016');os.environ['P5_DERIVED53_ROOT']=str(O);P=O/'actual-pure-readback/pure-tests-attempt1/physical65'
T=ast.parse(Path('/private/tmp/root_independent_controlled_stop52_review_20261012/reference_source/audit_geometry_qp_actual.py').read_text());exec(compile(ast.Module(body=[x for x in T.body if isinstance(x,ast.ClassDef)and x.name=='R'or isinstance(x,ast.FunctionDef)and x.name=='snapshot'],type_ignores=[]),'<snapshot-only>','exec'))
A=next(Path('/private/tmp/phase5_controlled_stop_roundoff_command_terminal64_v1_20261016').glob('actual-dell/*/run-attempt1/artifacts'))
base=snapshot(reader.old.strict.read_artifact_bytes(A/'cycle-0/trial-0/observation_before.bin'));bias=base['x'][14:21]-base['x'][:7]
constants=json.loads(Path('/private/tmp/root62_stop_cause_review_v1_20261016/PINNED_PUBLIC_CONSTANTS.json').read_text());results=[]
for cycle in [32,87]:
 o=reader.parse(P/f'saved64-current{cycle}/stop_objective_mode.bin');r=reader.replay(o,constants)
 s=snapshot(reader.old.strict.read_artifact_bytes(A/f'cycle-{cycle}/trial-0/observation_before.bin'))
 for key,v in [('q',s['x'][:7]),('v',s['x'][7:14]),('C',s['x'][14:21]),('w',s['x'][21:28]),('alpha',s['alpha']),('baseline_offset',bias)]:assert np.array_equal(o[key],v),key
 assert o['s']==s['x'][28]and o['r']==s['x'][29]and o['b']==s['b']
 no=reader.parse(P/f'no-rebuild-{cycle}/stop_objective_mode.bin');assert no['regenerate']==0 and np.array_equal(no['controls'],o['controls'])
 r.update(cycle=cycle,history_bitexact_to_original_actual64=True,selected=[s[0]for s in o['summary']],no_rebuild_case_keeps_prior_table=True);results.append(r)
raw,receipt=reader.old.strict.verify_artifact(P/'max1080/all.bin',collect=True);rr=reader.old.R(raw,'PURE65_1080_SYNTHETIC_STORAGE_NO_MODEL');count=0
for c in range(8):
 for f in range(149 if c==7 else 133):
  assert rr.u()==1;row=rr.take('<5Q8d');assert row==(c,f,13,20,0,0.,0.,0.,0.,0.,0.,1.,0.);count+=1
rr.end();assert count==1080
v={'schema':'ROOT65_REAL_CPP_V5_CODEC_AND_LITERAL_SCALAR_REVIEW_V1','cases':results,'max1080_storage_records_exact112bytes':True,'max1080_raw_bytes':len(raw),'all_codecs_verified_against_original_manifests':True,'no_new_Model_native65_or_SI_B_C_run':True,'nonzero_history_formula_qualification':'Root exact original oldlower uses +previous/h; C++ helper test arbitrary oldlower uses -previous/h, both nonbinding for its two cases, so it proves function behavior but not original shift replication. Separate Root counterexamples bind correct actual row algebra.','scope':'Independent actual C++ codec/stored and family scalar/provenance checks on saved actual64 histories. No current65 controller/physical-stop or phase acceptance.'}
bounded_write(O/'REAL_CPP_CODEC_AND_SCALAR_REVIEW.json',json.dumps(v,indent=2)+'\n');print(json.dumps(v))
