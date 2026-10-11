from pathlib import Path
import json,subprocess,shlex
D=Path('/private/tmp/phase5_full144_ieee_pure_active_v1_20261011');remote=json.loads((D/'REMOTE.json').read_text())['remote'];s0=Path('/private/tmp/root_independent_dynamic_actual_review_20261011/SOURCE_SNAPSHOT.py').read_text();readers=s0[s0.index('class R:'):s0.index('def state(')]+s0[s0.index('def reduction('):s0.index('def readmap(')]+s0[s0.index('def inline_full('):s0.index('def candidate_value(')]
s='''from pathlib import Path
import os,resource,signal,json,struct,hashlib
resource.setrlimit(resource.RLIMIT_CPU,(30,30));resource.setrlimit(resource.RLIMIT_AS,(536870912,536870912));signal.alarm(40);os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='1'
import numpy as np
'''+readers+'''
p=Path(%r);out=p/'original-fixture-v1';out.mkdir(exist_ok=False);base=Path('/home/codextransfer/predictive_motion/results/phase5/session-geometry-qp-three-cycle-v4-20261011-attempt30/run-attempt1/artifacts/cycle-0');names=['inline_qp.bin','qp_equality_reduction.bin'];before={n:hashlib.sha256((base/n).read_bytes()).hexdigest() for n in names};q=inline_full((base/names[0]).read_bytes());d=reduction((base/names[1]).read_bytes());rows=[r for r in d['rows'] if r>=0];index={n:i for i,(n,u) in enumerate(q['labels'])};first=index['feedback_jerk/0/7'];assert q['l'][first]==-5 and q['u'][first]==5 and d['rhs'][15]==0 and np.count_nonzero(q['seed'])==0
with (out/'original_input.bin').open('xb') as f:
 for a in [q['H'],q['g'],q['A'],q['l'],q['u'],d['E'],d['rhs'],q['seed']]:
  assert np.isfinite(a).all()
  for dim in a.shape:f.write(struct.pack('<Q',dim))
  f.write(np.asarray(a,dtype='<f8').tobytes(order='C'))
 f.write(struct.pack('<Q',len(rows)))
 for r in rows:f.write(struct.pack('<Q',r))
assert before=={n:hashlib.sha256((base/n).read_bytes()).hexdigest() for n in names};result={'original_input_sha256':hashlib.sha256((out/'original_input.bin').read_bytes()).hexdigest(),'bytes':(out/'original_input.bin').stat().st_size,'source_hashes':before,'rows':len(rows),'fulloriginalSIrows':14756,'scope':'untransformed archived30 original matrices/E/seed/rowmap, initial progress history0; no new33forecast'};(out/'READY.json').write_text(json.dumps(result,indent=2)+'\\n');print(json.dumps(result))
'''%remote;(D/'original_fixture34.py').write_text(s);stage='''from pathlib import Path
import sys
p=Path(%r)/'original_fixture34.py'
with p.open('x') as f:f.write(sys.stdin.read())
'''%remote;x=subprocess.run(['tools/dell-ssh.sh','-T','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','DellTransfer','python3 -I -S -B -c '+shlex.quote(stage)],input=s.encode(),capture_output=True,timeout=25);assert x.returncode==0,x.stderr
