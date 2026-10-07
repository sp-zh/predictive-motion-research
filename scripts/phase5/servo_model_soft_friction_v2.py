#!/usr/bin/env python3
"""Train-only positive diagonal soft-friction servo candidate and frozen validation."""
import argparse
import datetime
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from scipy.optimize import least_squares
import yaml
from servo_model_v1 import trace, sha, write_new, POLICY, DT, N


def public_parameters(xml_file, robot_config):
    root = ET.parse(xml_file).getroot()
    if root.find('option').get('integrator') != 'implicitfast':
        raise ValueError('only declared implicitfast interface supported')
    names = yaml.safe_load(Path(robot_config).read_text())['joint_names']
    if len(names) != N:
        raise ValueError('fixture dimension mismatch')
    defaults = {}
    def default_walk(node, inherited):
        attributes = dict(inherited)
        joint = node.find('joint')
        if joint is not None:
            attributes.update(joint.attrib)
        defaults[node.get('class', '')] = attributes
        for child in node.findall('default'):
            default_walk(child, attributes)
    default_walk(root.find('default'), {})
    joints = {}
    def walk(node, child_class=''):
        child_class = node.get('childclass', child_class)
        for child in node:
            if child.tag == 'joint':
                value = dict(defaults.get(child.get('class', child_class), {}))
                value.update(child.attrib)
                joints[child.get('name')] = value
            elif child.tag == 'body':
                walk(child, child_class)
    walk(root.find('worldbody'))
    actuators = {node.get('joint'): node.attrib for node in root.find('actuator') if node.tag == 'position'}
    kp, damping, eta, impedance, reference = [], [], [], [], []
    for name in names:
        joint, actuator = joints[name], actuators[name]
        imp = [float(x) for x in joint.get('solimpfriction', '.9 .95 .001 .5 2').split()]
        ref = [float(x) for x in joint.get('solreffriction', '.02 1').split()]
        if not 0 < imp[0] < 1 or not imp[1] > 0 or not all(x > 0 for x in ref):
            raise ValueError('unsupported reference parameters')
        kp.append(float(actuator['kp']))
        damping.append(float(actuator['kv']) + float(joint.get('damping', '0')))
        eta.append(float(joint.get('frictionloss', '0')))
        impedance.append(imp[0]); reference.append(2 / (imp[1] * max(ref[0], 2 * DT)))
    return {'joint_names': names, 'kp_Nm_rad': kp, 'damping_Nm_s_rad': damping, 'friction_bound_Nm': eta,
            'impedance': impedance, 'reference_decay_s_inv': reference,
            'source_xml_sha256': sha(xml_file), 'source_robot_config_sha256': sha(robot_config),
            'default_parameter_basis': 'MuJoCo 3.3.7 solimpfriction=.9 .95 .001 .5 2 and solreffriction=.02 1 unless explicitly overridden',
            'public_sources': ['https://mujoco.readthedocs.io/en/3.3.7/computation/index.html',
                               'https://github.com/google-deepmind/mujoco/blob/3.3.7/src/engine/engine_core_constraint.c']}


def arrays(model):
    return [np.array(model[k]) for k in ['mass_effective_kg_m2', 'bias_Nm']] + [np.array(model['public_parameters'][k]) for k in
             ['kp_Nm_rad', 'damping_Nm_s_rad', 'friction_bound_Nm', 'impedance', 'reference_decay_s_inv']]


def step(q, v, c, model):
    mass, bias, kp, damping, eta, imp, decay = arrays(model)
    smooth_force = kp * (c - q) - damping * v + bias
    friction = -np.clip(imp * (smooth_force + mass * decay * v), -eta, eta)
    vn = v + DT / (mass + DT * damping) * (smooth_force + friction)
    return q + DT * vn, vn


def tangent(q, v, c, model):
    mass, bias, kp, damping, eta, imp, decay = arrays(model)
    smooth_force = kp * (c - q) - damping * v + bias
    interior = abs(imp * (smooth_force + mass * decay * v)) < eta
    gain = DT / (mass + DT * damping)
    dvq = -gain * (1 - imp * interior) * kp
    dvv = 1 - gain * ((1 - imp * interior) * damping + interior * imp * mass * decay)
    p = np.block([[np.eye(N) + DT * np.diag(dvq), DT * np.diag(dvv)], [np.diag(dvq), np.diag(dvv)]])
    b = np.vstack([-DT * np.diag(dvq), -np.diag(dvq)])
    qn, vn = step(q, v, c, model)
    offset = np.r_[qn, vn] - p @ np.r_[q, v] - b @ c
    return p, b, offset


def identify(q, v, c, vn, public):
    kp, damping, eta, imp, decay = [np.array(public[k]) for k in ['kp_Nm_rad', 'damping_Nm_s_rad', 'friction_bound_Nm', 'impedance', 'reference_decay_s_inv']]
    masses, biases, diagnostics = [], [], []
    for j in range(N):
        def residual(x):
            mass, bias = np.exp(x[0]), x[1]
            smooth_force = kp[j] * (c[:, j] - q[:, j]) - damping[j] * v[:, j] + bias
            friction = -np.clip(imp[j] * (smooth_force + mass * decay[j] * v[:, j]), -eta[j], eta[j])
            vp = v[:, j] + DT / (mass + DT * damping[j]) * (smooth_force + friction)
            return (vp - vn[:, j]) / .001
        result = least_squares(residual, [np.log(.5), float(-kp[j] * np.mean(c[:, j] - q[:, j]))],
                               bounds=([-6.9, -50], [3.9, 50]), xtol=1e-12, ftol=1e-12, gtol=1e-12)
        if not result.success or not np.isfinite(result.x).all():
            raise ValueError('parameter fit failure')
        masses.append(float(np.exp(result.x[0]))); biases.append(float(result.x[1]))
        diagnostics.append({'success': bool(result.success), 'status': int(result.status), 'evaluations': result.nfev,
                            'optimality': float(result.optimality), 'response_jacobian_rank': int(np.linalg.matrix_rank(result.jac)),
                            'response_jacobian_condition': float(np.linalg.cond(result.jac)),
                            'scaled_response_rmse': float(np.sqrt(np.mean(result.fun ** 2))),
                            'bound_active': result.active_mask.tolist()})
        if diagnostics[-1]['response_jacobian_rank'] != 2 or any(result.active_mask):
            raise ValueError('unidentified/bound-active effective parameters')
    return masses, biases, diagnostics


def evaluate(model, rows, data):
    q, v, c, qn, vn = [data[k] for k in ['q_before_', 'v_before_', 'target_', 'q_post_', 'v_post_']]
    active = np.array([r['phase'] != 'warmup' for r in rows])
    box = model['local_box']
    error = c - q
    bad = active & (((q < box['q_min']) | (q > box['q_max'])).any(axis=1) | (abs(v) > box['v_abs_max']).any(axis=1) | ((error < box['target_error_min']) | (error > box['target_error_max'])).any(axis=1))
    metrics = []
    for hi, length in enumerate(model['policy']['horizons_substeps']):
        starts = np.array([i for i in range(0, len(rows) - length + 1, 2) if active[i]])
        qp, vp = q[starts].copy(), v[starts].copy()
        for k in range(length):
            qp, vp = step(qp, vp, c[starts + k], model)
        qe, ve = qp - qn[starts + length - 1], vp - vn[starts + length - 1]
        qm, vm = float(np.max(abs(qe))), float(np.max(abs(ve)))
        qlim, vlim = model['policy']['position_error_limits_rad'][hi], model['policy']['velocity_error_limits_rad_s'][hi]
        metrics.append({'substeps': length, 'duration_s': length * DT, 'windows': len(starts), 'max_q_error_rad': qm,
                        'max_v_error_rad_s': vm, 'q_limit_rad': qlim, 'v_limit_rad_s': vlim, 'passed': qm <= qlim and vm <= vlim,
                        'rmse_q_rad': float(np.sqrt(np.mean(qe ** 2))), 'rmse_v_rad_s': float(np.sqrt(np.mean(ve ** 2))),
                        'q_worst_start_tick_joint': [int(starts[np.unravel_index(np.argmax(abs(qe)), qe.shape)[0]] // 2), int(np.unravel_index(np.argmax(abs(qe)), qe.shape)[1])]})
    passed = all(m['passed'] for m in metrics) and not any(bad)
    return {'gate': 'PASS_LOCAL_EMPIRICAL' if passed else 'FAIL_MODEL_INELIGIBLE', 'metrics': metrics,
            'active_domain_bad_rows': int(sum(bad)), 'scope': model['policy']['scope'], 'no_refit': True,
            'conditional_target_replay': True, 'overlapping_windows_not_independent_trials': True}


def fit(args):
    execution = json.loads(args.execution.read_text())
    if execution['return_code'] != 0 or execution['argv'][-2] != '91011' or execution['raw_files']['raw.csv'] != sha(args.raw):
        raise ValueError('completed 91011 identity required')
    public = public_parameters(args.xml, args.robot_config)
    rows, data = trace(args.raw)
    mask = np.array([r['phase'] == 'excitation' for r in rows])
    q, v, c, vn = [data[k][mask] for k in ['q_before_', 'v_before_', 'target_', 'v_post_']]
    masses, biases, diagnostics = identify(q, v, c, vn, public)
    policy = dict(POLICY)
    for obsolete in ['full_rank_required', 'scaled_condition_max', 'stable_hold_spectral_radius_max']:
        policy.pop(obsolete, None)
    policy.update({'model_class': 'positive diagonal local inertia plus published soft box friction and implicit damping',
                   'equations': ['s=kp*(c-q)-D*v+g', 'f=-clip(imp*(s+m*B*v),-eta,eta)',
                                 'v_next=v+.002/(m+.002*D)*(s+f)', 'q_next=q+.002*v_next'],
                   'solver': 'seven independent bounded least-squares fits of log effective inertia and constant bias; no 91012 reads',
                   'fit_parameter_bounds': {'log_inertia': [-6.9, 3.9], 'bias_Nm': [-50, 50]},
                   'gate': 'all frozen horizon maxima and local q/v/target-error domain coverage; finite positive parameters, fit rank2 and no parameter bound active; observed training or holdout errors are not robust bounds',
                   'coupling': 'physical coupling omitted; effective fitted parameters are not measured physical body inertia',
                   'nonsmooth_boundary': 'exact clip forward transition; tangent exists away from clip thresholds; no smoothness claim at thresholds',
                   'scope': 'local empirical development model only; training is not independent validation; no robust uncertainty/terminal/task/online/Phase5 certificate'})
    model = {'schema': 2, 'status': 'FROZEN_CANDIDATE_NOT_ACCEPTED', 'training_seed': 91011,
             'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'policy': policy,
             'training_raw_sha256': sha(args.raw), 'training_execution_sha256': sha(args.execution), 'script_sha256': sha(__file__),
             'trace_reader_sha256': sha(Path(__file__).with_name('servo_model_v1.py')), 'public_parameters': public,
             'mass_effective_kg_m2': masses, 'bias_Nm': biases, 'fit_diagnostics': diagnostics,
             'training_ranges': {'q_min': q.min(0).tolist(), 'q_max': q.max(0).tolist(), 'v_min': v.min(0).tolist(), 'v_max': v.max(0).tolist(), 'accepted_target_min': c.min(0).tolist(), 'accepted_target_max': c.max(0).tolist(), 'target_error_min': (c-q).min(0).tolist(), 'target_error_max': (c-q).max(0).tolist()},
             'local_box': {'q_min': (q.min(0) - .002).tolist(), 'q_max': (q.max(0) + .002).tolist(), 'v_abs_max': .005, 'target_error_min': ((c-q).min(0)-.0003).tolist(), 'target_error_max': ((c-q).max(0)+.0003).tolist()}}
    args.output.mkdir(exist_ok=False)
    write_new(args.output / 'model.json', model)
    report = evaluate(model, rows, data)
    report.update({'training_only': True, 'model_sha256': sha(args.output / 'model.json'), 'raw_sha256': sha(args.raw)})
    write_new(args.output / 'training_report.json', report)
    print(json.dumps(report, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw', type=Path, required=True); parser.add_argument('--execution', type=Path, required=True)
    parser.add_argument('--xml', type=Path, required=True); parser.add_argument('--robot-config', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    fit(parser.parse_args())


if __name__ == '__main__':
    main()
