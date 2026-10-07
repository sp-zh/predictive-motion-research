#!/usr/bin/env python3
"""Offline causal affine servo candidate; training and frozen validation only."""
import argparse
import csv
import datetime
import hashlib
import json
from pathlib import Path

import numpy as np

N = 7
DT = .002
POLICY = {
    'model_class': 'translation-invariant coupled affine implicit-Euler velocity map',
    'equations': ['v_next=E*(accepted_target-q)+V*v+d', 'q_next=q+0.002*v_next'],
    'state_order': 'q[7],v[7]; SI radians and radians/second',
    'fit_rows': '91011 excitation only; warmup/stopping excluded',
    'solver': 'center and standardize 14 features; numpy.linalg.lstsq, no ridge or selected hyperparameters',
    'full_rank_required': 15,
    'scaled_condition_max': 1000.,
    'stable_hold_spectral_radius_max': 1.,
    'horizons_substeps': [1, 2, 20, 400],
    'position_error_limits_rad': [1e-6, 1e-6, 1e-4, 1e-4],
    'velocity_error_limits_rad_s': [1e-4, 1e-4, 1e-3, 1e-3],
    'rollout_start_policy': 'each 4ms command boundary in excitation/stopping; no warmup; window cannot extend beyond recorded data',
    'conditioning': 'offline predictions initialized from measured q/v once; use recorded accepted targets for subsequent held intervals; never reinitialize within a window',
    'hold_transition': '4ms transition is exactly two 2ms physical steps at the same already accepted target; only integer 2ms durations supported',
    'local_position_box': 'training excitation min/max physical q expanded by 0.002 rad per side',
    'local_velocity_abs_max_rad_s': .005,
    'gate': 'all prefrozen horizon maxima, finite coefficients, rank, stability and local box coverage must pass; otherwise ineligible for controller integration',
    'scope': 'empirical held-out development validation only; no robust error bound, 10mm task/stop/online/hardware certificate; no final evaluation seeds',
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_new(path, value):
    with Path(path).open('x') as out:
        out.write(json.dumps(value, indent=2, allow_nan=False) + '\n')


def trace(raw):
    rows = list(csv.DictReader(Path(raw).open()))
    if not rows:
        raise ValueError('empty trace')
    vector = lambda prefix: np.array([[float(r[prefix + str(j)]) for j in range(N)] for r in rows])
    a = {p: vector(p) for p in ['q_before_', 'v_before_', 'target_', 'q_post_', 'v_post_']}
    for p, values in a.items():
        if not np.isfinite(values).all():
            raise ValueError('nonfinite ' + p)
    for i, r in enumerate(rows):
        if int(r['tick']) != i // 2 or int(r['substep']) != i % 2 + 1:
            raise ValueError('noncontiguous fixed microsteps')
        if abs(float(r['time_s']) - (i + 1) * DT) > 1e-8:
            raise ValueError('unexpected physics clock')
    if np.max(abs(a['q_post_'][:-1] - a['q_before_'][1:])) > 1e-12 or np.max(abs(a['v_post_'][:-1] - a['v_before_'][1:])) > 1e-12:
        raise ValueError('broken physical state chain')
    if np.max(abs(a['target_'][::2] - a['target_'][1::2])) > 1e-12:
        raise ValueError('target changed inside 4ms hold')
    return rows, a


def identify(q, v, c, vn):
    x = np.column_stack([c - q, v])
    mu, scale = x.mean(0), x.std(0)
    if np.any(scale < 1e-12):
        raise ValueError('unexcited features')
    z = np.column_stack([(x - mu) / scale, np.ones(len(x))])
    t, _, rank, singular = np.linalg.lstsq(z, vn, rcond=None)
    condition = float(singular[0] / singular[-1])
    if rank != 15 or condition > POLICY['scaled_condition_max']:
        raise ValueError('insufficient identification rank/conditioning')
    coef = t[:14] / scale[:, None]
    d = t[14] - mu @ coef
    return coef[:7].T, coef[7:].T, d, {'samples': len(x), 'rank': int(rank), 'scaled_condition': condition,
                                     'feature_mean': mu.tolist(), 'feature_scale': scale.tolist()}


def matrices(e, v, d):
    p = np.block([[np.eye(N) - DT * e, DT * v], [-e, v]])
    b = np.vstack([DT * e, e])
    f = np.concatenate([DT * d, d])
    return p, b, f


def step(q, v, target, e, vv, d):
    vn = (target - q) @ e.T + v @ vv.T + d
    return q + DT * vn, vn


def evaluate(model, rows, a):
    e, vv, d = (np.array(model[k]) for k in ['E', 'V', 'd'])
    q, v, target, qn, vn = (a[k] for k in ['q_before_', 'v_before_', 'target_', 'q_post_', 'v_post_'])
    local = model['local_box']
    domain = (q >= np.array(local['q_min'])) & (q <= np.array(local['q_max']))
    active = np.array([r['phase'] != 'warmup' for r in rows])
    domain_bad = int(np.sum(active & ((~domain).any(axis=1) | (abs(v) > local['v_abs_max']).any(axis=1))))
    metrics, selected = [], []
    for hi, length in enumerate(model['policy']['horizons_substeps']):
        starts = np.array([i for i in range(0, len(rows) - length + 1, 2) if active[i]], dtype=int)
        if not len(starts):
            raise ValueError('no rollout windows')
        qp, vp = q[starts].copy(), v[starts].copy()
        for k in range(length):
            qp, vp = step(qp, vp, target[starts + k], e, vv, d)
        qe, ve = qp - qn[starts + length - 1], vp - vn[starts + length - 1]
        qm, vm = float(np.max(abs(qe))), float(np.max(abs(ve)))
        qlim = model['policy']['position_error_limits_rad'][hi]
        vlim = model['policy']['velocity_error_limits_rad_s'][hi]
        metrics.append({'substeps': length, 'duration_s': length * DT, 'windows': len(starts),
                        'max_q_error_rad': qm, 'max_v_error_rad_s': vm,
                        'rmse_q_rad': float(np.sqrt(np.mean(qe ** 2))), 'rmse_v_rad_s': float(np.sqrt(np.mean(ve ** 2))),
                        'q_limit_rad': qlim, 'v_limit_rad_s': vlim, 'passed': qm <= qlim and vm <= vlim,
                        'q_worst_start_tick_joint': [int(starts[np.unravel_index(np.argmax(abs(qe)), qe.shape)[0]] // 2), int(np.unravel_index(np.argmax(abs(qe)), qe.shape)[1])],
                        'v_worst_start_tick_joint': [int(starts[np.unravel_index(np.argmax(abs(ve)), ve.shape)[0]] // 2), int(np.unravel_index(np.argmax(abs(ve)), ve.shape)[1])]})
        if length == 400:
            j = int(np.unravel_index(np.argmax(abs(qe)), qe.shape)[1])
            selected = [{'start_time_s': float(rows[i]['time_s']) - DT, 'end_time_s': float(rows[i + length - 1]['time_s']),
                         'joint': j, 'q_error_rad': float(qe[ii, j]), 'v_error_rad_s': float(ve[ii, j])}
                        for ii, i in enumerate(starts)]
    passed = all(m['passed'] for m in metrics) and domain_bad == 0 and model['hold_spectral_radius'] < 1.
    return {'scope': model['policy']['scope'], 'gate': 'PASS_LOCAL_EMPIRICAL' if passed else 'FAIL_MODEL_INELIGIBLE',
            'model_coefficients_unchanged': True, 'active_domain_bad_rows': domain_bad, 'metrics': metrics,
            'microstep_q_integrator_identity_error_rad': float(np.max(abs(qn - q - DT * vn)))}, selected


def fit(args):
    execution = json.loads(args.execution.read_text())
    if execution['return_code'] != 0 or execution['argv'][-2] != '91011':
        raise ValueError('fit requires completed 91011 training only')
    if execution['raw_files']['raw.csv'] != sha(args.raw):
        raise ValueError('training trace identity mismatch')
    rows, a = trace(args.raw)
    mask = np.array([r['phase'] == 'excitation' for r in rows])
    q, v, c, vn = (a[k][mask] for k in ['q_before_', 'v_before_', 'target_', 'v_post_'])
    e, vv, d, diagnostics = identify(q, v, c, vn)
    p, b, f = matrices(e, vv, d)
    model = {'schema': 1, 'status': 'FROZEN_CANDIDATE_NOT_ACCEPTED', 'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
             'policy': POLICY, 'training_seed': 91011, 'training_raw_sha256': sha(args.raw), 'training_execution_sha256': sha(args.execution),
             'script_sha256': sha(__file__), 'numpy_version': np.__version__, 'E': e.tolist(), 'V': vv.tolist(), 'd': d.tolist(),
             'P_2ms': p.tolist(), 'Q_2ms': b.tolist(), 'affine_2ms': f.tolist(), 'fit_diagnostics': diagnostics,
             'hold_spectral_radius': float(max(abs(np.linalg.eigvals(p)))),
             'local_box': {'q_min': (q.min(0) - .002).tolist(), 'q_max': (q.max(0) + .002).tolist(), 'v_abs_max': .005},
             'integration_eligibility': 'must pass frozen heldout validation before any controller integration; empirical bounds do not certify stopping'}
    if not np.isfinite(p).all() or model['hold_spectral_radius'] >= 1:
        raise ValueError('nonfinite or unstable candidate')
    args.output.mkdir(exist_ok=False)
    write_new(args.output / 'model.json', model)
    report, selected = evaluate(model, rows, a)
    report.update({'training_only': True, 'raw_sha256': sha(args.raw), 'model_sha256': sha(args.output / 'model.json')})
    write_new(args.output / 'training_report.json', report)
    write_new(args.output / 'training_800ms_errors.json', selected)
    print(json.dumps({k: val for k, val in report.items() if k != 'metrics'}, indent=2))
    print(json.dumps(report['metrics'], indent=2))


def validate(args):
    model = json.loads(args.model.read_text())
    execution = json.loads(args.execution.read_text())
    freeze = json.loads(args.frozen.read_text())
    if execution['return_code'] != 0 or execution['argv'][-2] != '91012':
        raise ValueError('validation requires completed 91012 fixture')
    if freeze['files'].get(str(args.model)) != sha(args.model):
        raise ValueError('model absent/changed from pretrial freeze')
    if execution['raw_files']['raw.csv'] != sha(args.raw):
        raise ValueError('validation trace identity mismatch')
    rows, a = trace(args.raw)
    report, selected = evaluate(model, rows, a)
    report.update({'seed': 91012, 'raw_sha256': sha(args.raw), 'model_sha256': sha(args.model), 'frozen_sha256': sha(args.frozen),
                   'validation_execution_sha256': sha(args.execution), 'script_sha256': sha(__file__), 'no_refit': True})
    args.output.mkdir(exist_ok=False)
    write_new(args.output / 'validation_report.json', report)
    write_new(args.output / 'validation_800ms_errors.json', selected)
    print(json.dumps(report, indent=2))
    return 0 if report['gate'] == 'PASS_LOCAL_EMPIRICAL' else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='mode', required=True)
    for mode in ['fit', 'validate']:
        p = sub.add_parser(mode)
        p.add_argument('--raw', type=Path, required=True)
        p.add_argument('--execution', type=Path, required=True)
        p.add_argument('--output', type=Path, required=True)
        if mode == 'validate':
            p.add_argument('--model', type=Path, required=True)
            p.add_argument('--frozen', type=Path, required=True)
    args = parser.parse_args()
    return fit(args) if args.mode == 'fit' else validate(args)


if __name__ == '__main__':
    raise SystemExit(main())
