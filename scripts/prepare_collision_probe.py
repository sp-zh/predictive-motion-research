#!/usr/bin/env python3
"""Prepare explicit q perturbations for a geometry diagnostic, never a benchmark."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import platform
import random

parser = argparse.ArgumentParser()
parser.add_argument('--input', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
with args.input.open() as f:
    rows = list(csv.DictReader(f))
rng = random.Random(5022)
args.output.parent.mkdir(parents=True, exist_ok=True)
with args.output.open('w', newline='') as f:
    writer = csv.writer(f, lineterminator='\n')
    writer.writerow(['sample'] + [f'q{j}' for j in range(1, 8)])
    for i, row in enumerate(rows):
        writer.writerow([i] + [float(row[f'q{j}']) + rng.uniform(-.005, .005) for j in range(1, 8)])
metadata = {'purpose': 'independent geometry-gradient diagnostic off the orientation-aligned path', 'seed': 5022, 'joint_perturbation_rad': .005, 'controller_trial': False, 'python': platform.python_version(), 'source_sha256': hashlib.sha256(args.input.read_bytes()).hexdigest(), 'output_sha256': hashlib.sha256(args.output.read_bytes()).hexdigest()}
args.output.with_suffix('.metadata.json').write_text(json.dumps(metadata, indent=2)+'\n')
