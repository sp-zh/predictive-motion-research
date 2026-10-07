#!/usr/bin/env python3
"""Independent window/gate retention audit; not numerical forecast recomputation."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

SOURCE = Path(__file__).read_bytes()
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['raw', 'report', 'output']:
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    raw_hash, report_hash = sha(args.raw), sha(args.report)
    assert raw_hash == 'ab9d14efa1a5886c0683db25345f24d5cacd55343e2768eb60536fa180a11dce'
    assert report_hash == 'd695307c46f1b68312a7e0d7a2b6954c3de815a8402c3d2cd622607f32d6a07d'
    rows = list(csv.DictReader(args.raw.open()))
    report = json.loads(args.report.read_text())
    assert len(rows) == 5380
    assert all(int(r['tick']) == i // 2 and int(r['substep']) == i % 2 + 1 for i, r in enumerate(rows))
    roster = []
    for length in [1, 2, 20, 400]:
        kinds = {kind: [] for kind in ['active', 'warmup']}
        for i in range(0, len(rows) - length + 1, 2):
            kinds['warmup' if rows[i]['phase'] == 'warmup' else 'active'].append(i)
        for kind, indices in kinds.items():
            matches = [m for m in report['metrics'] if m['duration_s'] == length * .002 and m['scope'] == kind]
            assert len(matches) == 1
            m = matches[0]
            assert len(indices) == m['windows'] == m['completed_windows'] and m['failed_windows'] == 0
            assert all(math.isfinite(m[key]) for key in ['max_q_error_rad', 'max_v_error_rad_s', 'rmse_q_rad', 'rmse_v_rad_s'])
            qlimit, vlimit = (1e-6, 1e-4) if length <= 2 else (1e-4, 1e-3)
            assert m['q_limit_rad'] == qlimit and m['v_limit_rad_s'] == vlimit
            assert m['passed'] == (m['max_q_error_rad'] <= qlimit and m['max_v_error_rad_s'] <= vlimit)
            sequences = {}
            for i in indices:
                sequence = '->'.join(dict.fromkeys(r['phase'] for r in rows[i:i+length]))
                sequences[sequence] = sequences.get(sequence, 0) + 1
            roster.append(dict(horizon_s=length*.002, start_scope=kind, windows=len(indices), phase_sequence_windows=sequences))
    assert len(report['metrics']) == 8 and report['failures'] == [] and report['gate'] == 'PASS_PUBLIC_COUPLED_TRAINING_ONLY'
    result = dict(source_sha256=hashlib.sha256(SOURCE).hexdigest(), raw_sha256=raw_hash,
                  producer_report_sha256=report_hash, recorded_rows=len(rows), roster=roster,
                  scope='Independent count/gate/phase-roster audit only; no full numerical forecast recomputation. Warmup denotes start phase; all crossing windows retained. Overlapping windows are not independent trials.')
    assert Path(__file__).read_bytes() == SOURCE and sha(args.raw) == raw_hash and sha(args.report) == report_hash
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output/'audit.json').write_text(json.dumps(result, indent=2)+'\n')
    (args.output/'SOURCE_SNAPSHOT.py').write_bytes(SOURCE)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
