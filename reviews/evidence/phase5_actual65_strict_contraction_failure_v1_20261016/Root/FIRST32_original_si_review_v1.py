from pathlib import Path
import os, sys, json, struct, ast, hashlib
import numpy as np
sys.path.insert(0, '/private/tmp')
from bounded_derived_bytes53_v1 import bounded_write
import root62_nominal_reader_v3b as nominal
strict = nominal.strict
T = ast.parse(Path('/private/tmp/root58_selected_audit_v1.py').read_text())
exec(compile(ast.Module(body=[n for n in T.body if isinstance(n, ast.ClassDef) and n.name == 'R'], type_ignores=[]), '<saved-reader>', 'exec'))
O = Path('/private/tmp/root65_actual_review_v1_20261016')
os.environ['P5_DERIVED53_ROOT'] = str(O)
A = O / 'selected/native65/run-attempt1/artifacts'
P = A / 'cycle-32/trial-0'
r = R(P / 'inline_qp.bin', 'INLINE_QP_COMPLETE_OR_RETAINED_PREFIX')
stage, error = (r.text(), r.text())
complete, refused, nf, nc, nodes, slots, agebound = r.take('<7Q')
obsid = r.text()
timing = r.u()
r.take('<3d')
geometry = r.u()
H, g, C, lo, hi = (r.mat(), r.vec(), r.mat(), r.vec(), r.vec())
stateage = r.d()
F, f, seed = (r.mat(), r.vec(), r.vec())
constant = r.d()
labels = [(r.text(), r.text()) for _ in range(r.u())]
terms = [(r.text(), r.u(), r.u()) for _ in range(r.u())]
for _ in range(r.u()):
    r.text()
    r.vec()
    r.vec()
    r.mat()
fm, fn, nnz = r.take('<3Q')
assert (fm, fn) == F.shape and nnz == np.count_nonzero(F)
seen = set()
for _ in range(nnz):
    row, col, value = r.take('<2Qd')
    assert (row, col) not in seen and row < fm and (col < fn) and (value == F[row, col])
    seen.add((row, col))
r.end()
assert complete == 1 and refused == 0 and (not error) and (nf == 909) and (F.shape == (909, 160)) and (H.shape == (160, 160)) and (C.shape == (nc, 160)) and (len(labels) == nc) and (geometry == 1)
r = R(P / 'candidate.bin', 'SOLVER_RESULT_AND_DATA_ONLY_PREVIEW')
reason = r.text()
permission, attempts, wrappers = r.take('<3Q')
status, raw_status, api_error, iterations, violation_row = r.take('<5Q')
x = r.vec()
solverfields = r.take('<14d')
r.take('<3Q')
r.u()
r.text()
r.take('<4Q')
n = r.u()
assert n == nc
stored_violations = r.arr(n)
r.u()
r.take('<4d')
r.take('<2Q')
preview = r.u()
if preview:
    for _ in range(5):
        r.arr(7)
    r.take('<8d')
    r.take('<2Q')
tail = r.u()
if tail:
    r.arr(7)
    r.arr(7)
    r.take('<2d')
    tail_exact = r.u()
forward = r.u()
if forward:
    r.arr(30)
    r.take('<2Q')
    r.text()
    r.text()
    r.text()
    r.take('<20Q')
    count = r.u()
    assert count == 20
    r.arr(160)
r.end()
assert permission == 0 and attempts == wrappers == 1 and (raw_status == 1) and (api_error == 0) and (preview == tail == forward == 1) and (len(x) == 160) and np.isfinite(x).all()
values = C @ x
v = np.maximum.reduce([np.zeros(nc), lo - values, values - hi])
maximum = float(np.max(v))
assert maximum <= 1e-07 and np.max(stored_violations) <= 1e-07
he = float(np.max(np.abs(H - F.T @ F)))
ge = float(np.max(np.abs(g - F.T @ f)))
ce = abs(constant - 0.5 * float(f @ f))
assert he <= 1e-10 * max(1.0, float(np.max(np.abs(H)))) and ge <= 1e-10 * max(1.0, float(np.max(np.abs(g)))) and (ce <= 1e-10 * max(1.0, abs(constant)))
report = dict(schema='ROOT65_ACTUAL_FIRST32_FULL_ORIGINAL_SI_AND_COST_FACTOR_REVIEW_V1', current=32, trial=0, native_raw_status=raw_status, native_attempts=1, data_only_execution_permission=False, all_original_rows=nc, controls=160, full_original_SI_violation_numpy=maximum, factor_rows=909, full_sparse_factor_entries_exact=True, H_factor_error_inf=he, g_factor_error_inf=ge, constant_factor_error=ce, source_complete_SHA_CRC_singleEOF_before_decode=True, scope='Saved actual65 current32 reaches native SOLVED, full original SI and original cost-factor consistency; data-only core permission stays false. Independent B400/C2 arithmetic is separately verified. Not stopping/task/realtime/phase acceptance.')
bounded_write(O / 'FIRST32_ORIGINAL_SI_COST_REVIEW.json', json.dumps(report, indent=2) + '\n')
print(json.dumps(report))
