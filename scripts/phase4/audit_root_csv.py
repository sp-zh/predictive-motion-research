#!/usr/bin/env python3
"""Independent root audit of frozen diagnostic CSVs; no controller API calls.

Run on Linux where NumPy is available. Raw data stays on Dell. This audits
recorded states and commands, not continuous collision safety or real-time
schedulability. FK and SE(3) residuals are rebuilt from URDF with NumPy.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        while block := stream.read(8 * 1024 * 1024):
            h.update(block)
    return h.hexdigest()


def skew(a):
    x, y, z = a
    return np.array([[0., -z, y], [z, 0., -x], [-y, x, 0.]])


def rotation(axis, theta):
    w = skew(np.asarray(axis) / np.linalg.norm(axis))
    return np.eye(3) + np.sin(theta) * w + (1 - np.cos(theta)) * (w @ w)


def quaternion_rotation(q):
    x, y, z, w = q
    return np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
                     [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
                     [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])


def prepare_model(path):
    model = ET.parse(path).getroot()
    children = {j.find('child').get('link'): j for j in model.findall('joint')}
    chain = []
    link = 'fr3_link8'
    while link in children:
        joint = children[link]
        chain.insert(0, joint)
        link = joint.find('parent').get('link')
    prepared = []
    lower, upper = [], []
    names = [f'fr3_joint{i}' for i in range(1, 8)]
    for name in names:
        limit = model.find(f"joint[@name='{name}']/limit")
        lower.append(float(limit.get('lower')))
        upper.append(float(limit.get('upper')))
    for joint in chain:
        origin = joint.find('origin')
        xyz = np.fromstring(origin.get('xyz', '0 0 0'), sep=' ')
        rpy = np.fromstring(origin.get('rpy', '0 0 0'), sep=' ')
        orient = rotation([0, 0, 1], rpy[2]) @ rotation([0, 1, 0], rpy[1]) @ rotation([1, 0, 0], rpy[0])
        axis_node = joint.find('axis')
        axis = np.fromstring(axis_node.get('xyz', '1 0 0') if axis_node is not None else '1 0 0', sep=' ')
        prepared.append((joint.get('name'), joint.get('type'), xyz, orient, axis))

    def fk(q):
        p, r = np.zeros(3), np.eye(3)
        values = dict(zip(names, q))
        for name, kind, xyz, orient, axis in prepared:
            p = p + r @ xyz
            r = r @ orient
            if kind != 'fixed':
                r = r @ rotation(axis, values[name])
        return p + r @ np.array([0., 0., .32]), r

    return fk, np.array(lower), np.array(upper)


def residual_norms(actual_p, actual_r, desired_p, desired_r):
    r = actual_r.T @ desired_r
    sine_vector = np.array([r[2, 1]-r[1, 2], r[0, 2]-r[2, 0], r[1, 0]-r[0, 1]]) / 2
    sine = np.linalg.norm(sine_vector)
    angle = np.arctan2(sine, np.clip((np.trace(r)-1)/2, -1, 1))
    if angle > np.pi - 1e-6:
        raise ValueError('Near-pi rotation outside this diagnostic audit envelope')
    omega = sine_vector * (angle / sine if sine > 1e-14 else 1.)
    w = skew(omega)
    factor = (1 - .5*angle / np.tan(.5*angle)) / angle**2 if angle > 1e-4 else 1/12 + angle**2/720
    inverse_v = np.eye(3) - .5*w + factor*(w @ w)
    rho = inverse_v @ (actual_r.T @ (desired_p-actual_p))
    return np.linalg.norm(rho), angle


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--project', type=Path, required=True)
    ap.add_argument('--epoch', default='frozen-v4')
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    if args.output.exists():
        ap.error('Refuse audit overwrite')
    folder = args.project / 'results/phase4' / args.epoch
    freeze_path, progress_path = folder/'frozen.json', folder/'progress.json'
    freeze = json.loads(freeze_path.read_text())
    progress = json.loads(progress_path.read_text())
    cfg = freeze['config']
    expected = {(split, int(seed), method) for split in ('development', 'evaluation')
                for seed in cfg[split+'_seeds'] for method in cfg['methods']}
    observed = [(p['split'], int(p['seed']), p['method']) for p in progress]
    if len(observed) != len(set(observed)) or set(observed) != expected:
        raise ValueError('Frozen trial roster incomplete, duplicate or unscheduled')
    model_path = args.project/'models/fr3/fr3_arm.urdf'
    fk, lo, hi = prepare_model(model_path)
    dt, subdt = cfg['period_s'], cfg['physics_substep_s']
    reports = []
    for entry in progress:
        path = Path(entry['raw_file'])
        rows = list(csv.DictReader(path.open()))
        if len(rows) != entry['rows'] or not rows:
            raise ValueError('Raw row count differs from summary')
        def column(name):
            return np.array([float(row[name]) for row in rows])
        def matrix(prefix, width=7):
            return np.column_stack([column(prefix+str(i)) for i in range(1, width+1)])
        q, dq = matrix('q_post_'), matrix('dq_post_')
        target, accepted = matrix('q_accepted_'), matrix('dq_accepted_')
        acc, jerk = matrix('executed_acc_'), matrix('executed_jerk_')
        ca, cj = matrix('command_acc_'), matrix('command_jerk_')
        ticks, sub, times = column('tick'), column('substep'), column('time_s')
        physical = sub > 0
        active = physical & np.array([r['phase'] != 'warmup' for r in rows])
        checks = {}
        def count(name, condition):
            checks[name] = int(np.count_nonzero(condition))
        count('nonfinite_state_command', ~np.isfinite(np.hstack([q,dq,target,accepted,acc,jerk,ca,cj])).all(axis=1))
        count('contact_rows', column('contacts') != 0)
        count('physical_position_bounds', ((q < lo-1e-6) | (q > hi+1e-6)).any(axis=1))
        count('target_position_margin', active & ((target < lo+cfg['position_margin_rad']-1e-6) | (target > hi-cfg['position_margin_rad']+1e-6)).any(axis=1))
        count('executed_velocity_bounds', active & (np.abs(dq) > np.array(cfg['velocity_rad_s'])+1e-6).any(axis=1))
        count('accepted_trust_velocity', active & (np.abs(accepted) > cfg['kinematic_trust_step_rad']/dt+1e-6).any(axis=1))
        count('command_acceleration', active & (np.abs(ca) > cfg['command_acceleration_rad_s2']+1e-6/dt+1e-8).any(axis=1))
        count('command_jerk', active & (np.abs(cj) > cfg['command_jerk_rad_s3']+1e-6/dt**2+1e-8).any(axis=1))
        count('executed_acceleration', active & (np.abs(acc) > cfg['executed_acceleration_rad_s2']+1e-6).any(axis=1))
        count('executed_jerk', active & (np.abs(jerk) > cfg['executed_jerk_rad_s3']+1e-6).any(axis=1))
        count('clearance_record', column('true_clearance_m') < cfg['collision_safe_m']-1e-7)
        count('accepted_stale_state', active & (column('state_age_s') > cfg['max_state_age_s']))
        idx = np.flatnonzero(physical)
        count('physical_time_gap', np.abs(np.diff(times[idx])-subdt) > 1e-9)
        count('executed_acc_reconstruction', np.max(np.abs(np.diff(dq[idx],axis=0)/subdt-acc[idx[1:]]),axis=1) > 1e-6)
        count('executed_jerk_reconstruction', np.max(np.abs(np.diff(acc[idx],axis=0)/subdt-jerk[idx[1:]]),axis=1) > 1e-6)
        commits = np.flatnonzero(active & (sub == 1))
        prior_target = target[commits-1]
        prior_v = accepted[commits-1]
        prior_a = ca[commits-1]
        count('target_integration', np.max(np.abs(target[commits]-prior_target-dt*accepted[commits]),axis=1) > 1e-10)
        count('command_acc_reconstruction', np.max(np.abs(ca[commits]-(accepted[commits]-prior_v)/dt),axis=1) > 1e-6)
        count('command_jerk_reconstruction', np.max(np.abs(cj[commits]-(ca[commits]-prior_a)/dt),axis=1) > 1e-6)
        terminated = np.flatnonzero(sub == 0)
        for i in terminated:
            if rows[i]['phase'] != 'terminated' or 'NO_COMMAND_SIMULATION_TERMINATED' not in rows[i]['command_status']:
                raise ValueError('Unexpected unexecuted record')
            if i and (not np.array_equal(q[i],q[i-1]) or times[i] != times[i-1]):
                raise ValueError('Termination record advanced physical state')
        desired_p, desired_q = matrix('desired_translation_',3), matrix('desired_quaternion_xyzw_',4)
        max_p, max_r = 0., 0.
        chosen = sorted(set(range(0,len(rows),25)) | {len(rows)-1})
        for i in chosen:
            p,r = fk(q[i]); pe,re = residual_norms(p,r,desired_p[i],quaternion_rotation(desired_q[i]))
            max_p=max(max_p,abs(pe-float(rows[i]['pose_position_m'])))
            max_r=max(max_r,abs(re-float(rows[i]['pose_rotation_rad'])))
        checks['independent_se3_residual'] = int(max_p > 1e-10 or max_r > 1e-10)
        checks['summary_final_pose'] = int(abs(float(rows[-1]['pose_position_m'])-entry['final_position_m']) > 1e-12 or abs(float(rows[-1]['pose_rotation_rad'])-entry['final_rotation_rad']) > 1e-12)
        if entry['completed']:
            checks['false_completion'] = int(bool(entry['failure']) or len(idx) != round((cfg['warmup_s']+cfg['path_s']+cfg['settle_s'])/subdt) or entry['final_position_m'] > cfg['completion_position_m'] or entry['final_rotation_rad'] > cfg['completion_rotation_rad'])
        else:
            checks['unexplained_failure'] = int(not bool(entry['failure']))
        reports.append({'method':entry['method'],'seed':entry['seed'],'split':entry['split'],
                        'completed':entry['completed'],'failure':entry['failure'],'rows':len(rows),
                        'checks':checks,'raw_sha256':sha(path),'fk_checked_rows':len(chosen),
                        'independent_residual_position_max_error':max_p,'independent_residual_rotation_max_error':max_r})
    report = {'scope':'independent recorded-state/command/FK audit; no continuous safety or real-time proof',
              'status':'PASS' if all(not any(r['checks'].values()) for r in reports) else 'FAIL',
              'source_sha256':sha(Path(__file__)), 'freeze_sha256':sha(freeze_path),
              'progress_sha256':sha(progress_path),'urdf_sha256':sha(model_path),
              'numpy_version':np.__version__, 'trials':len(reports),
              'raw_rows':sum(r['rows'] for r in reports),'details':reports}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='details'},indent=2))
    return 0 if report['status']=='PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
