"""Independent NumPy algebra audit of recorded Phase 3 numerical inputs."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
import yaml

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--input', type=Path, default=root/'results/phase3/numerical_postguard')
args = parser.parse_args()
design = yaml.safe_load((root/'config/phase3.yaml').read_text())
robot_path = root/'src/predictive_motion_kinematics/config/fr3.yaml'
robot = yaml.safe_load(robot_path.read_text())
model = ET.parse(robot_path.parent/robot['urdf']).getroot()
limits = {joint.attrib['name']: joint.find('limit') for joint in model.findall('joint')}
lo = np.array([float(limits[name].attrib['lower']) for name in robot['joint_names']])
hi = np.array([float(limits[name].attrib['upper']) for name in robot['joint_names']])
span = hi-lo
n = len(lo)
with (args.input/'samples.csv').open() as f:
    rows = list(csv.DictReader(f))
assert len(rows) >= 2000
maximum = {}
def check(key, value, expected, tolerance):
    error = float(np.linalg.norm(np.asarray(value)-np.asarray(expected)))
    maximum[key] = max(maximum.get(key, 0), error)
    assert np.isfinite(error) and error <= tolerance, (key, error, tolerance)
def projector(j):
    _, sigma, vh = np.linalg.svd(j, full_matrices=True)
    rank = int(np.count_nonzero((sigma > design['rank_relative_tolerance']*sigma[0]) & (sigma > 0)))
    # Null-vector outer products, instead of subtracting retained vectors from I.
    basis = vh[rank:].T
    return basis@basis.T
def array(row, name, count):
    return np.array([float(row[f'{name}_{j}']) for j in range(count)])
for row in rows:
    j = array(row, 'synthetic_J', 6*n).reshape(6, n)
    p = projector(j)
    damping = design['projector_comparison_damping']
    # Independent ridge normal-equation construction of the damped projector.
    d = np.linalg.solve(j.T@j + damping*damping*np.eye(n), damping*damping*np.eye(n))
    check('exact_leakage', np.linalg.norm(j@p), float(row['exact_leakage']), 1e-12)
    check('symmetry', np.linalg.norm(p-p.T), float(row['symmetry']), 1e-12)
    check('idempotency', np.linalg.norm(p@p-p), float(row['idempotency']), 1e-12)
    check('damped_leakage', np.linalg.norm(j@d), float(row['damped_leakage']), 1e-8)
    check('damped_idempotency', np.linalg.norm(d@d-d), float(row['damped_idempotency']), 1e-8)
    q = array(row, 'q', n)
    gradient = 2*(q-(lo+hi)/2)/span**2
    check('joint_gradient', gradient, array(row, 'gradient_joint', n), 1e-12)
    model_j = array(row, 'model_scaled_J', 6*n).reshape(6, n)
    secondary = -projector(model_j)@gradient
    derivative = gradient@secondary
    assert derivative <= 1e-12
    check('joint_projected_derivative', derivative, float(row['joint_projected_derivative']), 1e-12)
    value = lambda x: np.sum(((x-(lo+hi)/2)/span)**2)
    descent = value(q+1e-4*secondary)-value(q)
    assert descent <= 1e-12
    check('joint_finite_descent', descent, float(row['joint_finite_descent']), 1e-12)
    direction = array(row, 'direction', n)
    check('direction_norm', np.linalg.norm(direction), 1, 1e-12)
    assert float(row['sigma_direction_abs']) <= 1e-6 or not int(row['simple_min']) or int(row['near_rank'])
    assert float(row['log_volume_direction_abs']) <= 1e-5
summary = {'status': 'PASS', 'samples': len(rows), 'scope': 'independent algebra on saved matrices and objective inputs; FK/derivative model checks remain separate', 'numpy': np.__version__, 'maximum_recompute_difference': maximum, 'input_sha256': hashlib.sha256((args.input/'samples.csv').read_bytes()).hexdigest(), 'auditor_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
(args.input.parent/'root_numerical_review.json').write_text(json.dumps(summary, indent=2)+'\n')
print(json.dumps(summary, indent=2))
