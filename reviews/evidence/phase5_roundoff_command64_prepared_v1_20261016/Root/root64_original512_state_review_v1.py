from pathlib import Path
import os,sys,ast,json,struct,hashlib
import numpy as np
sys.path.insert(0,'/private/tmp');from bounded_derived_bytes53_v1 import bounded_write
import root63_nominal_reader_v4 as n
strict=n.strict
T=ast.parse(Path('/private/tmp/root58_selected_audit_v1.py').read_text());exec(compile(ast.Module(body=[x for x in T.body if isinstance(x,ast.ClassDef)and x.name=='R'],type_ignores=[]),'<reader>','exec'))
T=ast.parse(Path('/private/tmp/root59_production_review_v1.py').read_text());exec(compile(ast.Module(body=[x for x in T.body if isinstance(x,ast.FunctionDef)and x.name in['fixture','xy']],type_ignores=[]),'<fixture>','exec'))
P=Path('/private/tmp/phase5_saved63_cycle_diagnostic_v2_20261016/readback');O=Path('/private/tmp/root64_saved63_cause_review_v1_20261016');os.environ['P5_DERIVED53_ROOT']=str(O);A=next(Path('/private/tmp/phase5_controlled_stop_explicit_warm_nominal_terminal63_v1_20261016').glob('actual-dell/*/run-attempt1/artifacts/cycle-63/trial-0'))
r=R(A/'current_numeric_hint.bin','BOUNDED_CURRENT_MATRIX_OPTIMIZER_HINT_NOT_CANDIDATE');assert r.u()==1 and r.u()==0 and r.text()=='current numeric iteration cap512';x,y=r.vec(),r.vec();count=r.u();assert count==512;ev=[r.take('<3q4d')for _ in range(count)];faces=[r.take('<2q')for _ in range(r.u())];r.text();r.end();sx,sy=xy(P/'case.finalxy.bin');assert x.tobytes()==sx.tobytes()and y.tobytes()==sy.tobytes();assert b''.join(struct.pack('<3q4d',*v)for v in ev)==(P/'case.states.bin').read_bytes()
b=(P/'case.snapshots.bin').read_bytes();at=0;ordered=set();unordered=set();pattern=set();epochs=set();ro=ru=0
for i in range(512):
 it,g,nc,k,negative=struct.unpack_from('<5q',b,at);at+=40;direction,selected,residual=struct.unpack_from('<3d',b,at);at+=24;assert it==i and nc==144 and 0<=k<=144 and negative<k and -1<=negative and residual<=1e-10;bits=b[at:at+8*nc];assert len(bits)==8*nc;at+=8*nc;ff=tuple(struct.unpack_from('<2q',b,at+16*j)for j in range(k));at+=16*k;assert all(0<=row<7364 and side in[-1,1]for row,side in ff);key=(g,bits,ff);key2=(g,bits,tuple(sorted(ff)));ro+=key in ordered;ru+=key2 in unordered;ordered.add(key);unordered.add(key2);epochs.add(g);pattern.add(bits)
assert at==len(b)==1063104 and ro==ru==0 and epochs=={0}and len(pattern)==42
report=dict(schema='ROOT64_ORIGINAL_ACTUAL63_512_PRIMAL_FACES_MASK_DIAGNOSTIC_REVIEW_V1',actual_hint_SHA256=hashlib.sha256((A/'current_numeric_hint.bin').read_bytes()).hexdigest(),instrumented_final_x_y_and_all512_events_byteexact_actual_failure=True,all512_snapshots_fully_decoded=True,snapshot_bytes=len(b),unique_primal_bitpatterns=42,mask_epochs=[0],exact_ordered_state_repeats=ro,exact_unordered_state_repeats=ru,old_two_step_cycle_qualification_not_generalized=True,scope='Saved-only instrumentation reproduces the original failure exactly, with no repeated full state. Does not support arbitrary longer-cycle masking. No Model/native64/physical stopping proof; old failure retained.')
bounded_write(O/'ORIGINAL63_ALL512_FULL_STATE_REVIEW.json',json.dumps(report,indent=2)+'\n');print(json.dumps(report))
