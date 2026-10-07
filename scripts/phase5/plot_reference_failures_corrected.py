#!/usr/bin/env python3
"""Correct archived plot labels from frozen configuration; no experimental change."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import yaml


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--raw-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    own = Path(__file__).read_bytes()
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    identities = {}
    fig, axes = plt.subplots(2, 2, figsize=(12, 7), constrained_layout=True)
    for i, version in enumerate(['v1', 'v2']):
        cfg_path = args.project / f'config/phase5_development/servo_validation_safe_reference_{version}.yaml'
        run = args.raw_root / f'servo-safe-reference-{version}-validation'
        cfg = yaml.safe_load(cfg_path.read_text())
        summary = yaml.safe_load((run / 'summary.yaml').read_text())
        rows = [r for r in csv.DictReader((run / 'raw.csv').open()) if r['substep'] == '2']
        for p in [cfg_path, run / 'summary.yaml', run / 'raw.csv']:
            identities[str(p)] = sha(p)
        t = [float(r['time_s']) for r in rows]
        axes[i, 0].plot(t, [float(r['command_velocity_3']) for r in rows], label='Accepted command w, joint 4 (index 3)')
        axes[i, 0].plot(t, [float(r['v_post_3']) for r in rows], label='Measured physical v, joint 4 (index 3)')
        axes[i, 0].axhline(-cfg['command_velocity_rad_s'], color='r', ls=':', label='Frozen command lower limit')
        axes[i, 0].set_ylabel('rad/s')
        axes[i, 0].set_title(version + ': ' + summary['primary_failure'])
        axes[i, 0].legend(fontsize=8)
        guard = 1000 * cfg['collision_safe_m']
        axes[i, 1].plot(t, [1000 * float(r['true_clearance_m']) for r in rows])
        axes[i, 1].axhline(guard, color='r', ls=':', label=f'Frozen {guard:g} mm guard')
        axes[i, 1].set_ylabel('Recorded true clearance (mm)')
        axes[i, 1].set_title('Shared stop ' + ('completed' if summary['completed_stop'] else 'infeasible'))
        axes[i, 1].legend(fontsize=8)
    for ax in axes[-1]:
        ax.set_xlabel('New-run simulation time (s)')
    fig.suptitle('Retained reference failures: frozen 5 mm guard; original data unchanged', fontsize=13)
    assert Path(__file__).read_bytes() == own
    for p, h in identities.items():
        assert sha(Path(p)) == h
    args.output.mkdir(parents=True, exist_ok=False)
    png = args.output / 'phase5_servo_reference_failures_corrected.png'
    fig.savefig(png, dpi=170)
    plt.close(fig)
    metadata = {'scope': __doc__, 'source_hashes': identities,
                'source_sha256': hashlib.sha256(own).hexdigest(), 'output_sha256': sha(png),
                'joint_index_zero_based': 3, 'vendor_joint_number': 4,
                'guard_source': 'Each unchanged frozen case YAML collision_safe_m=.005',
                'correction': 'Archived producer figure incorrectly displayed a hardcoded 10 mm guard. Retained unchanged in original unit archive; this plot corrects labels only.',
                'units': {'distance': 'mm', 'velocity': 'rad/s', 'time': 's'},
                'phase5_acceptance': 'PENDING'}
    png.with_suffix('.json').write_text(json.dumps(metadata, indent=2) + '\n')
    print(json.dumps({'png_sha256': sha(png), 'source_sha256': metadata['source_sha256']}))


if __name__ == '__main__':
    main()
