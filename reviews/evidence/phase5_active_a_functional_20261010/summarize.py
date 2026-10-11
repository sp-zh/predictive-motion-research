from pathlib import Path
import hashlib
import json

src = Path('/private/tmp/phase5_active_a_functional_checkpoint_v1_20261010_collection2')
out = Path('/Users/uot/Documents/ChatGPT/ros/reviews/evidence/phase5_active_a_functional_20261010')
out.mkdir(exist_ok=True)
rows = json.loads((src / 'ACTUAL_ACTIVE_A_OUTCOMES.json').read_text())
keys = ['version', 'status', 'raw_status', 'api_error', 'iterations',
        'setup_seconds', 'solve_seconds', 'primal', 'dual', 'epsabs', 'epsrel',
        'initial_rho', 'rho_updates', 'polish_status', 'native_entry_wall_seconds',
        'native_boundary_unchanged', 'session_termination_pass',
        'native_termination_pass', 'plant_steps', 'commits', 'input_pins_count',
        'before_after_input_pins_identical', 'preview', 'forward_request', 'stop']
records = []
for attempt in rows:
    record = {k: attempt[k] for k in keys if k in attempt}
    record['original_rows'] = 13156
    record['solver_rows'] = len(attempt['retained_rows']) if 'retained_rows' in attempt else 13156
    record['omitted_rows'] = len(attempt.get('omitted_rows', []))
    record['usable_controls'] = len(attempt['controls'])
    artifacts = src / 'actual-dell' / attempt['version'] / 'run-attempt1/artifacts'
    record['source_artifacts'] = {
        p.name: {'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
        for p in artifacts.glob('*.bin')
    }
    records.append(record)
summary = {
    'schema': 'ROOT_ACTIVE_A_ACTUAL_SUMMARY_V1',
    'ready_sha256': '25b8572470112ed66f7c3735bca1e58b2aa16ca0ebbeea4bf8c1917de2fc4fdb',
    'source_outcomes_sha256': hashlib.sha256((src / 'ACTUAL_ACTIVE_A_OUTCOMES.json').read_bytes()).hexdigest(),
    'payloads_verified': 341,
    'phase5': 'NOT_ACCEPTED', 'phase6': 'NOT_STARTED', 'attempts': records,
    'qualifiers': [
        'Bounded offline development attempts, no usable candidate or physical task.',
        'Residuals refer to each solver scaling; comparisons are not physical performance or a research ranking.',
        'Repair6 omits redundant trust rows, contrary to the original proposal to retain trust. Subsequent source repair retains trust; historical source/results remain unchanged.',
        'Repair6 originalMaximumViolationRow maps reduced backend worst, not a full-original worst. No usable vector was returned, so the full-original candidate scan was not reached. Prospective repair separates these fields.',
        'Compile/link plans use Dell retained dependency paths; no portable CI reproduction claimed.'
    ]
}
(out / 'ACTUAL_SUMMARY.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps({'summary': str(out / 'ACTUAL_SUMMARY.json'), 'attempts': len(records)}))
