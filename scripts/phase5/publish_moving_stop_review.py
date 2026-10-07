from pathlib import Path
import csv,json,hashlib,shutil,xml.etree.ElementTree as ET
p=Path('/home/codextransfer/predictive_motion')
e=p/'results/phase5/development/moving-stop-v1'
raw=Path('/mnt/d/CodexTransfer/projects/predictive_motion/phase5/raw/moving-stop-v1')
rows=list(csv.DictReader((raw/'raw.csv').open()))
initial=next(x for x in rows if x['tick']=='694' and x['substep']=='2')
stop=[x for x in rows if x['phase']=='stopping'];last=stop[-1]
qmax=lambda x,prefix:max(abs(float(x[prefix+str(i)])) for i in range(7))
metrics={'start_s':float(initial['s']),'start_r':float(initial['r']),'start_b':float(initial['b']),
 'start_physical_speed_max':qmax(initial,'dq_post_'),
 'last_r':float(last['r']),'last_b':float(last['b']),
 'last_accepted_speed_max':qmax(last,'dq_accepted_'),
 'last_physical_speed_max':qmax(last,'dq_post_'),
 'stop_feedback_cycles':len(stop)//2,'virtual_stop_duration_s':len(stop)//2*.004,
 'min_stop_true_clearance_m':min(float(x['true_clearance_m']) for x in stop),
 'max_stop_command_acceleration':max(qmax(x,'command_acc_') for x in stop),
 'max_stop_command_jerk':max(qmax(x,'command_jerk_') for x in stop),
 'max_stop_physical_acceleration':max(qmax(x,'physical_acc_') for x in stop),
 'max_stop_physical_jerk':max(qmax(x,'physical_jerk_') for x in stop)}
# Ensure copied stop block remains byte-identical to the actual benchmark.
a=(p/'tools/phase5_adapter/phase5_benchmark.cpp').read_text()
b=(p/'tools/phase5_adapter/moving_stop_replay.cpp').read_text()
def block(s):
 start=s.index('        if (stopping) {')
 end=s.index('        cost.stop = seconds(stamp);',start)
 return s[start:end]
assert block(a)==block(b)
metrics['shared_stop_block_sha256']=hashlib.sha256(block(a).encode()).hexdigest()
audit=json.loads((e/'audit.json').read_text())
report=f'''# Exact command replay and moving-stop component review

The v14 input is preserved byte-for-byte. The component resets the same complete
MuJoCo plant with seed91011, scene/model and97 checked physical input identities,
then replays every accepted qtarget for ticks0–694 with2×2ms integration. It does
not initialize by injecting q/v. Independent observer comparisons at all1390
substeps have maximum q error{audit['max_q_error']} and dq error{audit['max_dq_error']}.
At tick695 the component injects an explicit planner-failure event and runs only
the new stopping supervisor. The shared stopping block is byte-identical to the
actual benchmark (SHA in metrics.json); the main predictive planner is bypassed.

Stopping begins at s={metrics['start_s']}, r={metrics['start_r']},
previous b={metrics['start_b']}; physical max|dq|={metrics['start_physical_speed_max']}.
The new stop completes233 feedback cycles /0.932s virtual time. Final r is
{metrics['last_r']}, b={metrics['last_b']}, max|accepted dq|=
{metrics['last_accepted_speed_max']}, max|physical dq|={metrics['last_physical_speed_max']}.
All466 stop substeps have SOLVED stopping commands, nonnegative progress speed,
zero contacts and true clearance at least{metrics['min_stop_true_clearance_m']}m.
Actual command acceleration/jerk and progress acceleration/jerk are audited against
the unchanged limits. Full-cycle timing remains in cycles.csv:233 deadline misses,
maximum0.015158847s and command age0.004889357s. No real-time claim follows.

This is a moving-stop replay component test, not an additional main research
trial, held-out evaluation, persistent prediction success, hardware result,
Phase5 gate acceptance, or a replay of the old planner's internal solver state.
The recorded physical trajectory is fully reproduced before new stopping begins.
The v14 failure and v15/v16/v17 negative development epochs remain untouched.

Evidence: results/phase5/development/moving-stop-v1/frozen.json, materialized.json,
execution.json, audit.json, metrics.json, stdout.log/stderr.log.172 pre-run inputs
are materialized without missing identities. The six raw files are under
/mnt/d/CodexTransfer/projects/predictive_motion/phase5/raw/moving-stop-v1 and all
have SHA identities in execution.json. The consumer source is
tools/phase5_adapter/moving_stop_replay.cpp; moving-stop-input/raw.csv is a copy
of the unchanged v14 input. CMake compiles against the installed pinned SDK.

PreviewConsistency and termination semantics: local model agreement is an early
acceptance test for a feasible iterate, not nonlinear optimization convergence.
The new PreviewResult.termination_reason distinguishes
MODEL_CONSISTENT_FEASIBLE_ITERATE, SMALL_CONTROL_STEP_FEASIBLE_ITERATE and
SCP_ITERATION_BUDGET_FEASIBLE_ITERATE. The benchmark appends that reason to SCP
diagnostics. max_iterations is a ceiling; the actual iterations array/log gives
the executed count. None of these reasons certifies a stationary optimum,
especially when trust bounds are active. Updated math tests and full adapter
build pass; existing moving-stop-v1 frozen source/library identities remain the
executed version, preserved before these diagnostic-only changes.

Independent root review is pending.
'''
(e/'metrics.json').write_text(json.dumps(metrics,indent=2)+'\n')
review=p/'reviews/phase_5_moving_stop_executor_review.md';review.write_text(report)
stage=Path('/mnt/c/Users/SYSUR/Documents/Codex/2026-09-16/zh/work/phase5')
for name in ['predictive.cpp','predictive_test.cpp','phase5_benchmark.cpp','moving_stop_replay.cpp']:
 source=p/('src/predictive_motion_control/src/'+name if name=='predictive.cpp' else
           'src/predictive_motion_control/test/'+name if name=='predictive_test.cpp' else
           'tools/phase5_adapter/'+name)
 shutil.copyfile(source,stage/name)
shutil.copyfile(p/'src/predictive_motion_control/include/predictive_motion_control/predictive.hpp',stage/'predictive.hpp')
shutil.copyfile(p/'tools/phase5_adapter/CMakeLists.txt',stage/'CMakeLists.txt')
for name in ['make_moving_stop_replay.py','run_moving_stop.py','publish_moving_stop_review.py']:
 shutil.copyfile(stage/name,p/'scripts/phase5'/name)
out=Path('/mnt/c/Users/SYSUR/Documents/Codex/2026-09-16/zh/outputs/phase5')
shutil.copyfile(review,out/'moving_stop_review.md')
shutil.copyfile(e/'metrics.json',out/'moving_stop_metrics.json')
print(json.dumps(metrics))
