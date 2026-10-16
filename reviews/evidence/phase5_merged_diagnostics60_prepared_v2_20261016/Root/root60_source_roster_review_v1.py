from pathlib import Path
import os,sys,json,hashlib,re
sys.dont_write_bytecode=True;sys.path.insert(0,'/private/tmp')
from bounded_derived_bytes53_v1 import bounded_write
R=Path('/Users/uot/Documents/ChatGPT/ros');P=Path('/private/tmp/phase5_merged_hint_diagnostics60_source_v2_20261016');V1=Path('/private/tmp/phase5_merged_hint_diagnostics60_source_v1_20261016');S=P/'src-final-v1';OLD=R/'tools/phase5_controlled_stop_session_v12';O=Path('/private/tmp/root60_merged_review_v1_20261016');O.mkdir(exist_ok=True);os.environ['P5_DERIVED53_ROOT']=str(O)
def sha(b):return hashlib.sha256(b).hexdigest()
j=json.loads((S/'SOURCE_IDENTITIES.json').read_text());assert len(j['files'])==84 and len(list(S.iterdir()))==85
for name,e in j['files'].items():
 b=(S/name).read_bytes();assert len(b)==e['bytes']and sha(b)==e['sha256']
changes=[p.name for p in S.iterdir()if not(OLD/p.name).exists()or(OLD/p.name).read_bytes()!=p.read_bytes()];assert set(changes)=={'README.md','active_first_cycle.cpp','SOURCE_IDENTITIES.json','merged_hint_diagnostics60.hpp','merged_hint_diagnostics60_tests.cpp'}
v2changes=[p.name for p in S.iterdir()if(V1/'src-final-v1'/p.name).read_bytes()!=p.read_bytes()];assert set(v2changes)=={'SOURCE_IDENTITIES.json','merged_hint_diagnostics60_tests.cpp'}
for n in ['current_numeric_guess.hpp','negative_leaving59.hpp','lossless_evidence.cpp','lossless_evidence.hpp','integrated_horizon_qp.cpp','integrated_horizon_qp.hpp']:
 assert(S/n).read_bytes()==(OLD/n).read_bytes()
binding=json.loads((P/'FROZEN_SUCCESSFUL24_ROSTER_BINDING.json').read_text());mp=Path(binding['source_manifest']);mb=mp.read_bytes();assert sha(mb)==binding['source_manifest_identity']['sha256']=='f398787ea00a8350056196898b5292b736071e4d0eeb164b3a93c2d8f8919525' and len(mb)==14405
ready=next(mp.parents[i]/'READY.json'for i in range(len(mp.parents))if(mp.parents[i]/'READY.json').exists());assert sha(ready.read_bytes())==binding['source_packet_READY_sha256']=='80afd6ecffd138417a78ea1fab50ccc19663e7f8e2d88c04132c4dfbe52cb7ba'
names=[x.removeprefix('  - file: ')for x in mb.decode().splitlines()if x.startswith('  - file: ')];assert len(names)==24 and len(set(names))==24 and names==binding['ordered_binary_names']and names[-1]=='cycle_timing.bin'
test=(S/'merged_hint_diagnostics60_tests.cpp').read_text();encoded=re.search(r'names=(\{.*?\});',test).group(1);source_names=re.findall(r'"([A-Za-z0-9_]+\.bin)"',encoded);assert source_names==names
old=json.loads((OLD/'profile/active_input.json').read_text());new=json.loads((P/'profile-version1/active_input.json').read_text());old.pop('session_id');new.pop('session_id');a=old.pop('negative_multiplier_leaving');b=new.pop('negative_multiplier_leaving');assert old==new
assert set(k for k in set(a)|set(b)if a.get(k)!=b.get(k))=={'codec','artifact_file'} and b['artifact_file']=='hint_kkt_rank_events.bin'and b['codec']=='CONSISTENT_SINGULAR_ACTIVE_FACE_KKT_AND_STOP_SELECTED_LEAVING_DIAGNOSTICS_V2'
out=dict(schema='ROOT60_FROZEN_SOURCE_V2_AND_ACTUAL58_ORDERED24_ROSTER_BINDING_V1',source84_manifest_entries_verified=True,source_files_including_manifest=85,changed_vs59=changes,v2_changes_vs_failed_v1=v2changes,method_QP_evidence24_source_bytes_unchanged=True,original_canonical_reader24_unchanged=True,profile_changes_only_session_and_codec_file=True,ordered24names_bitexact_to_sealed_actual58_manifest=True,last24th_file='cycle_timing.bin',retained25th_refusal_name='hint_negative_leaving_events.bin',merged_bound_bytes=512*32+512*48+4096,unchanged_numeric_inventory=744208,unchanged_numeric_allowance=745000,scope='Source/binding review only. Failed v1 test string generation is preserved, v2 fixes two string literals without method/resource changes. Compile/pure/native results require their own evidence; synthetic output chain is not Model/C/task/stop acceptance.')
bounded_write(O/'SOURCE_AND_ORDERED24_ROSTER_REVIEW.json',json.dumps(out,indent=2)+'\n');print(json.dumps(out))
