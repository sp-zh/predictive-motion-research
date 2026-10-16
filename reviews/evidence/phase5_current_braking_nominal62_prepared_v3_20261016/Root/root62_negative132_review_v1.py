from pathlib import Path
import sys,os,json,hashlib
sys.path.insert(0,'/private/tmp');from bounded_derived_bytes53_v1 import bounded_write
import root62_nominal_reader_v2 as reader
O=Path('/private/tmp/root62_stop_cause_review_v1_20261016');os.environ['P5_DERIVED53_ROOT']=str(O);P=Path('/private/tmp/phase5_current_braking_nominal62_source_v2_20261016/onset32_refusal_pure_v2/readback')
for e in json.loads((P/'PRODUCER_RECEIPT.json').read_text()):
 b=(P/e['path']).read_bytes();assert len(b)==e['bytes']and hashlib.sha256(b).hexdigest()==e['sha256']
o=reader.parse(P/'retained-failure/stop_objective_mode.bin',source_complete=False);assert not o['terminal']and len(o['records'])==155
h=json.loads((O/'SAVED61_ONSET32_HISTORY.json').read_text());assert o['C']==h['C']and o['w']==h['w']and o['alpha']==h['previous_alpha']and(o['s'],o['r'],o['b'])==(h['s'],h['r'],h['previous_b']);x=reader.replay(o,json.loads((O/'PINNED_PUBLIC_CONSTANTS.json').read_text()));assert x['counts_per_channel'][7]==132 and all(r[2]for r in o['records']if r[0]==7)
j=dict(schema='ROOT62_OLD132_REAL_CXX_FIRST_STOP32_NEGATIVE_PREFIX_REVIEW_V1',all_copied_payload_SHA_size=True,old132_onset32_actual_history_byte_values_equal=True,raw_prefix_stored_SHA_CRC_singleEOF_verified=True,source_complete=False,terminal_available=False,records=155,all132progress_failures_original_order_and_reason_bound_recomputed=True,replay=x,scope='Expected finite-family rejection reproduced in C++ scalar helper, not a native controller/Model run or proof all feasible progress plans are impossible. Original closed/raw prefix is retained as incomplete source; no complete24-directory or stopping acceptance claim.')
bounded_write(O/'OLD132_ONSET32_NEGATIVE_PREFIX_ROOT_REVIEW.json',json.dumps(j,indent=2)+'\n');print(json.dumps(j))
