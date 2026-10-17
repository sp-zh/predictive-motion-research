from pathlib import Path
import os, sys, ast, json, struct, hashlib
import numpy as np
sys.path.insert(0, '/private/tmp')
from bounded_derived_bytes53_v1 import bounded_write
import root63_nominal_reader_v4 as codec
strict = codec.strict
src = Path('/private/tmp/root_independent_controlled_stop52_review_20261012/reference_source/audit_geometry_qp_actual.py')
t = ast.parse(src.read_text())
wanted = ['state', 'identity', 'metadata', 'values', 'readmap', 'nominal', 'candidate_value', 'snapshot', 'validation', 'initial_validation', 'commit_record']
exec(compile(ast.Module(body=[x for x in t.body if isinstance(x, ast.ClassDef) and x.name == 'R' or (isinstance(x, ast.FunctionDef) and x.name in wanted)], type_ignores=[]), '<decoders-only>', 'exec'))
O = Path('/private/tmp/root65_actual_review_v1_20261016')
os.environ['P5_DERIVED53_ROOT'] = str(O)
A = O / 'selected/native65/run-attempt1/artifacts'
reports = []
for cycle, base in [(32, A / 'cycle-32/trial-0'), (49, A / 'cycle-49/trial-0')]:
    read = lambda name: strict.read_artifact_bytes(base / name)
    before = snapshot(read('observation_before.bin'))
    after = snapshot(read('observation_after.bin'))
    n = nominal(read('original_nominal.bin'))
    v = candidate_value(read('candidate_value.bin'))
    b = validation(read('candidate_validation.bin'))
    iv = initial_validation(read('validation_initial.bin'))
    assert n['initial'].tobytes() == v['initial'].tobytes() == before['x'].tobytes() and n['alpha'].tobytes() == before['alpha'].tobytes() and (n['b'] == before['b'])
    assert n['bound'] == n['success'] == n['extension'] == n['final_available'] == 1 and (not n['error']) and (not n['extension_error']) and (not n['tags'][0]) and (not n['tags'][1])
    assert v['success'] == v['final_available'] == 1 and (not v['error']) and (not v['transport']) and (v['nomdigest'] == n['tags'][2]) and (len(v['points']) == len(n['points']) == len(n['maps']['half']) == 400)
    assert b['passed'] == b['attempted'] == 1 and len(b['points']) == 400 and (not b['error']) and (iv['complete'] == 1) and (iv['q'].tobytes() == before['x'][:7].tobytes()) and (iv['ids'] == before['ids'])
    assert abs(np.linalg.svd(iv['J'], compute_uv=False)[-1] - iv['sigma']) < 1e-12
    delta = np.zeros(30)
    C = before['x'][14:21].copy()
    w = before['x'][21:28].copy()
    qprev = before['x'][:7]
    vprev = before['x'][7:14]
    aprev = before['a']
    pc = min(iv['true'], iv['cover'])
    ps = iv['sigma']
    s = float(before['x'][28])
    rate = float(before['x'][29])
    index = 0
    maxerr = maxtrust = intervalerror = aerr = jerr = 0.0
    for k, macro in enumerate(n['mesh']):
        cu = v['controls'][k][1]
        du = cu - n['controls'][k][1]
        for j in range(macro):
            w = w + 0.004 * cu[:7]
            C = C + 0.004 * w
            for half in [1, 2]:
                p = v['points'][index]
                m = n['maps']['half'][index]
                bb = b['points'][index]
                nz = np.r_[n['points'][index]['q'], n['points'][index]['v'], n['points'][index]['C'], n['points'][index]['w'], n['points'][index]['s'], n['points'][index]['r']]
                z = np.r_[p['q'], p['v'], p['C'], p['w'], p['s'], p['r']]
                linear = nz + m['cell_A'] @ delta + m['cell_B'] @ du
                err = float(np.max(np.abs(z - linear)))
                trust = float(np.max(np.abs(p['q'] - nz[:7])))
                aa = (p['v'] - vprev) / 0.002
                jj = (aa - aprev) / 0.002
                assert (p['cell'], p['cycle'], p['half']) == (k, j + 1, half) == (m['cell'], m['cycle'], m['half']) and p['C'].tobytes() == C.tobytes() and (p['w'].tobytes() == w.tobytes())
                time = 0.002 * half
                assert abs(p['s'] - (s + time * rate + 0.5 * time * time * cu[7])) <= 1e-12 and abs(p['r'] - (rate + time * cu[7])) <= 1e-12
                assert bb['complete'] == 1 and (not bb['error']) and (bb['queries'] == 9035) and (p['control_clips'] == p['force_clips'] == 0) and (err <= 1e-06) and (trust <= 0.002) and (max(abs(aa)) <= 5) and (max(abs(jj)) <= 500)
                assert max(abs(p['q'] - (qprev + 0.002 * p['v']))) <= 1e-12 and abs(p['time'] - 0.002 * (index + 1)) < 1e-10
                travel = float(abs(p['q'] - qprev).sum())
                gl = min(pc, bb['true'], bb['cover']) - 4 * travel - 1e-06
                sl = min(ps, bb['sigma']) - 32 * travel
                assert gl >= 0.005 and sl >= 1e-06 and (abs(err - bb['affine_error']) < 2e-13) and (abs(trust - bb['trust']) < 2e-13)
                intervalerror = max(intervalerror, abs(bb['geometry_lower'] - gl), abs(bb['sigma_lower'] - sl))
                aerr = max(aerr, float(max(abs(bb['a'] - aa))))
                jerr = max(jerr, float(max(abs(bb['j'] - jj))))
                maxerr = max(maxerr, err)
                maxtrust = max(maxtrust, trust)
                if half == 2:
                    assert z[:28].tobytes() == v['cycles'][index // 2][:28].tobytes() and np.max(np.abs(z[28:] - v['cycles'][index // 2][28:])) <= 1e-14
                qprev, vprev, aprev, pc, ps = (p['q'], p['v'], aa, min(bb['true'], bb['cover']), bb['sigma'])
                index += 1
            s = s + 0.004 * rate + 0.5 * 0.004 * 0.004 * cu[7]
            rate = rate + 0.004 * cu[7]
        assert z[:28].tobytes() == v['cells'][k][:28].tobytes() and np.max(np.abs(z[28:] - v['cells'][k][28:])) <= 1e-14
        delta = n['maps']['cell'][k]['cell_A'] @ delta + n['maps']['cell'][k]['cell_B'] @ du
    assert index == 400 and intervalerror < 1e-11 and (aerr == jerr == 0)
    cp = A / f'cycle-{cycle}/trial-0/actual_commit.bin'
    r = R(strict.read_artifact_bytes(cp), 'TWO_REAL_2MS_HELD_TARGET_COMMIT_OR_RETAINED_PARTIAL_V1')
    c = commit_record(r)
    r.end()
    assert c['flags'] == [1, 1, 2, 2] and c['before'] == [cycle, cycle] and (c['after'] == [cycle + 1, cycle + 1]) and (not c['error']) and (len(c['points']) == 2)
    q = before['x'][:7]
    vv = before['x'][7:14]
    aa0 = before['a']
    clear = min(iv['true'], iv['cover'])
    sigma = iv['sigma']
    actualerr = actualinterval = 0.0
    for i, p in enumerate(c['points']):
        assert p['step'] == i + 1 and p['returned'] == p['passed'] == p['jerk_available'] == p['geometry_complete'] == p['integration_guard'] == 1 and (p['native_read'] == p['scratch_read'] == 7) and (not p['error']) and (p['contacts'] == 0) and (p['warnings'] == [0] * 8) and (p['queries'] == 9035)
        aa = (p['v'] - vv) / 0.002
        jj = (aa - aa0) / 0.002
        assert aa.tobytes() == p['a'].tobytes() and jj.tobytes() == p['j'].tobytes() and (max(abs(aa)) <= 5) and (max(abs(jj)) <= 500)
        travel = float(abs(p['q'] - q).sum())
        gl = min(clear, p['true'], p['cover']) - 4 * travel - 1e-06
        sl = min(sigma, p['sigma']) - 32 * travel
        assert gl >= 0.005 and sl >= 1e-06 and (p['tcp_error'] <= 1e-08) and (p['arm_error'] <= 1e-08) and (p['C'].tobytes() == c['held'].tobytes() == v['points'][i]['C'].tobytes())
        actualerr = max(actualerr, float(max(abs(p['q'] - v['points'][i]['q']))), float(max(abs(p['v'] - v['points'][i]['v']))))
        actualinterval = max(actualinterval, abs(gl - p['geometry_lower']), abs(sl - p['sigma_lower']))
        q, vv, aa0, clear, sigma = (p['q'], p['v'], aa, min(p['true'], p['cover']), p['sigma'])
    assert after['x'][:7].tobytes() == q.tobytes() and after['x'][7:14].tobytes() == vv.tobytes() == after['v'].tobytes() and (after['a'].tobytes() == aa0.tobytes()) and (actualerr < 1e-12) and (actualinterval < 1e-11)
    reports.append(dict(cycle=cycle, all400_B_original_full30_affine_jointtrust_physical_jerk_geometry_sigma_intervals_recomputed=True, max30_affine_error=maxerr, jointtrust=maxtrust, all400_geometry_sigma_interval_roundoff=intervalerror, all400_acceleration_jerk_record_error=[aerr, jerr], actual_native_substeps=2, actual_value_qv_error=actualerr, actual_geometry_sigma_interval_roundoff=actualinterval, no_clip_or_force_clip=True, scope='Independent saved arithmetic and private recorded guard/real-native2half contract, not every FCL distance query or physics engine re-execution. Full sourcecomplete SHA/CRC and archive binding separately verified. No actual stop/fulltask/realtime/phase proof.'))
bounded_write(O / 'FIRST32_LAST49_B400_C2_INDEPENDENT_REVIEW.json', json.dumps({'schema': 'ROOT65_ACTUAL_TWO_SAMPLE_B400_AND_C2_CONTRACT_REVIEW_V1', 'samples': reports, 'scope': 'Actual65 first changed stop32 and last committed49 only; all19 nominal/36 stop checks and50 completion scope separate. No repeated Model/solver/physical experiment.'}, indent=2) + '\n')
print(json.dumps(reports))
