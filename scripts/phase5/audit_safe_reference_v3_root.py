#!/usr/bin/env python3
"""Independent recorded-input scalar box prediction and actual QP/history audit.

No producer predictor, fit, plant call, or future physical-state reset is used.
This audit does not certify a domain, real-time execution, or the main controller.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np

SOURCE = Path(__file__).read_bytes()
SHA = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
MODEL_SHA = '984ee85d086aeba7da8260a20b21b301e23dfd2c698a6c61ace0ff956bbec1bb'
RAW_SHA = '5e5e2e5cde6170d548278007d6be80ac0703e832e6d1e8fb4ccbd64bfe4baa94'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--restored', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root, raw = args.restored, args.restored / 'raw/raw.csv'
    model_path = next(root.glob('project/results/**/servo-model-soft-friction-v2-frozen/model.json'))
    report_path = next(root.glob('project/results/**/model-audit/validation_report.json'))
    assert SHA(raw) == RAW_SHA and SHA(model_path) == MODEL_SHA
    model, producer = json.loads(model_path.read_text()), json.loads(report_path.read_text())
    rows = list(csv.DictReader(raw.open()))
    assert len(rows) == 5002
    assert all(int(r['tick']) == i // 2 and int(r['substep']) == i % 2 + 1 for i, r in enumerate(rows))
    read = lambda prefix: np.array([[float(r[prefix + str(j)]) for j in range(7)] for r in rows])
    q, v, c, qe, ve = [read(prefix) for prefix in ['q_before_', 'v_before_', 'target_', 'q_post_', 'v_post_']]
    active = np.array([r['phase'] != 'warmup' for r in rows])
    assert all(np.isfinite(x).all() for x in [q, v, c, qe, ve])
    assert np.max(abs(c[::2] - c[1::2])) == 0
    public = model['public_parameters']
    mass, bias = [np.array(model[k]) for k in ['mass_effective_kg_m2', 'bias_Nm']]
    kp, damping, eta, impedance, decay = [np.array(public[k]) for k in ['kp_Nm_rad', 'damping_Nm_s_rad', 'friction_bound_Nm', 'impedance', 'reference_decay_s_inv']]
    horizons, max_agreement = [], 0.0
    for length, expected in zip([1, 2, 20, 400], producer['metrics']):
        starts = np.array([i for i in range(0, len(rows) - length + 1, 2) if active[i]])
        qp, vp = q[starts].copy(), v[starts].copy()
        for k in range(length):
            smooth = kp * (c[starts + k] - qp) - damping * vp + bias
            # Independent unconstrained scalar force minimizer followed by box projection.
            hessian = 1 / mass + (1 - impedance) / (impedance * mass)
            force = np.clip(-(smooth / mass + decay * vp) / hessian, -eta, eta)
            vp = vp + .002 * (smooth + force) / (mass + .002 * damping)
            qp = qp + .002 * vp
        qerr, verr = qp - qe[starts + length - 1], vp - ve[starts + length - 1]
        metrics = dict(substeps=length, windows=len(starts), max_q_error_rad=float(np.max(abs(qerr))),
                       max_v_error_rad_s=float(np.max(abs(verr))), rmse_q_rad=float(np.sqrt(np.mean(qerr*qerr))),
                       rmse_v_rad_s=float(np.sqrt(np.mean(verr*verr))))
        assert metrics['windows'] == expected['windows']
        for name in ['max_q_error_rad', 'max_v_error_rad_s', 'rmse_q_rad', 'rmse_v_rad_s']:
            difference = abs(metrics[name] - expected[name])
            max_agreement = max(max_agreement, difference)
            assert difference < 1e-13
        qlimit, vlimit = (1e-6, 1e-4) if length <= 2 else (1e-4, 1e-3)
        metrics['passed'] = metrics['max_q_error_rad'] <= qlimit and metrics['max_v_error_rad_s'] <= vlimit
        assert metrics['passed'] == expected['passed']
        metrics['q_limit_rad'], metrics['v_limit_rad_s'] = qlimit, vlimit
        worst = np.unravel_index(np.argmax(abs(qerr)), qerr.shape)
        metrics['q_worst_start_tick_joint'] = [int(starts[worst[0]] // 2), int(worst[1])]
        assert metrics['q_worst_start_tick_joint'] == expected['q_worst_start_tick_joint']
        metrics['hold_only_windows'] = sum(all(r['phase'] == 'hold' for r in rows[i:i+length]) for i in starts)
        horizons.append(metrics)
    solves = list(csv.DictReader((root / 'raw/all_qp_solves.csv').open()))
    points, violations, seen = {}, {}, {}
    for r in solves:
        key = (int(r['tick']), r['kind'])
        assert key not in points
        assert r['wrapper_status'] == 'SOLVED' and int(r['raw_status']) == 1
        assert int(r['api_error']) == 0 and int(r['candidate_size']) == 7
        points[key] = [float(r['x'+str(j)]) for j in range(7)]
        assert all(math.isfinite(x) for x in points[key])
        violations[key], seen[key] = 0.0, []
    for r in csv.DictReader((root / 'raw/all_qp_rows.csv').open()):
        key = (int(r['tick']), r['kind'])
        x = points[key]
        value = math.fsum(float(r['A'+str(j)]) * x[j] for j in range(7))
        lower, upper = float(r['lower']), float(r['upper'])
        assert math.isfinite(value) and not math.isnan(lower) and not math.isnan(upper) and lower <= upper
        violations[key] = max(violations[key], lower-value, value-upper)
        seen[key].append(int(r['row']))
    assert len(solves) == 2002
    assert all(indices == list(range(len(indices))) and indices for indices in seen.values())
    assert max(violations.values()) <= 1e-7
    assert max(abs(violations[(int(r['tick']), r['kind'])] - float(r['SI_violation'])) for r in solves) < 1e-14
    # A solved tracking proposal at the final tick is superseded by the stop solve.
    candidate_match = 0.0
    min_margin = math.inf
    histories = 0
    for i in range(0, len(rows), 2):
        if not active[i]:
            continue
        r = rows[i]
        key = (int(r['tick']), 'stop' if (int(r['tick']), 'stop') in points else 'tracking')
        w, alpha = [[float(r[prefix + str(j)]) for j in range(7)] for prefix in ['command_velocity_', 'command_acceleration_']]
        candidate_match = max(candidate_match, max(abs(x-y) for x,y in zip(w, points[key])))
        for speed, acceleration in zip(w, alpha):
            assert abs(speed) <= .0625 + 1e-12 and abs(acceleration) <= 1 + 1e-12
            future = [max(abs(acceleration) - .004*20*k, 0) for k in range(1, 15)]
            required = .004*math.fsum(future)
            margin = .0625 - math.copysign(1, acceleration)*speed - required
            min_margin = min(min_margin, margin)
            assert margin >= -1e-12
        histories += 1
    assert candidate_match == 0 and histories == 2001
    result = dict(classification='PASS_RECORDED_QP_AND_SIGNED_HISTORY_MODEL_EXPANSION_FAIL', phase5_accepted=False,
                  source_sha256=hashlib.sha256(SOURCE).hexdigest(), raw_sha256=SHA(raw), model_sha256=SHA(model_path),
                  producer_report_sha256=SHA(report_path), forecast_metric_agreement=max_agreement,
                  horizons=horizons, actual_qp_solves=len(solves), actual_qp_rows=sum(map(len, seen.values())),
                  maximum_actual_SI_violation=max(violations.values()), accepted_candidate_match=candidate_match,
                  accepted_histories=histories, minimum_signed_speed_recovery_margin=min_margin,
                  physical_phase_substeps={phase:sum(r['phase']==phase for r in rows) for phase in sorted(set(r['phase'] for r in rows))},
                  limits=['Conditional known accepted targets only; no future plant state resets or refit.',
                          'Overlapping windows and long holds are not independent motion trials.',
                          'Actual A/l/u and candidates are audited; per-solve H/g were not directly exported.',
                          'Signed speed continuation alone proves no position, collision, or physical-stop feasibility.',
                          'Stop occurs after a long hold, not a fresh moving-stop challenge.',
                          'No main predictive-controller acceptance or online 250 Hz certificate.'])
    assert Path(__file__).read_bytes() == SOURCE and SHA(raw) == RAW_SHA and SHA(model_path) == MODEL_SHA
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output/'audit.json').write_text(json.dumps(result, indent=2)+'\n')
    (args.output/'SOURCE_SNAPSHOT.py').write_bytes(SOURCE)
    lines=['# Independent safe-reference v3 audit', '', '**Recorded QP/history checks pass; expanded model accuracy fails; Phase5 remains pending.**', '',
           'Every actual exported A/l/u row is multiplied by its own exported candidate using an independent original-SI calculation. All 2,002 solves have native SOLVED and API success; all 2,001 applied histories match recorded commands and retain discrete signed speed recovery. H/g are not directly captured for every solve.', '',
           '| Horizon | Windows | Maximum q error [rad] | Maximum v error [rad/s] | Original gate | Hold-only windows |', '|---|---:|---:|---:|---|---:|']
    for m in horizons:
        lines.append(f"| {m['substeps']*.002:g}s | {m['windows']} | {m['max_q_error_rad']:.8e} | {m['max_v_error_rad_s']:.8e} | {'PASS' if m['passed'] else 'FAIL'} | {m['hold_only_windows']} |")
    lines += ['', f"Maximum metric discrepancy against the producer: {max_agreement:.3e}. Maximum actual SI-row violation: {max(violations.values()):.8e}; original acceptance remains 1e-7.", '',
              'The scalar-box force minimizer is reconstructed independently from the frozen parameters. Each forecast initializes once from its starting measured state; later physical states serve only as endpoint comparisons. Every complete active 4ms-boundary window is retained. Short gates remain q=1e-6/v=1e-4; long gates remain q=1e-4/v=1e-3.', '',
              'The trace includes 1.712s of reference movement/braking and a long hold. Its final new stop starts already near rest. This is a recorded fixture result, not a new moving-stop challenge, domain-wide proof, main MPC pass, or timing acceptance. The model and declared local domain remain unchanged.']
    (args.output/'AUDIT.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
