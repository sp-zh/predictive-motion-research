# Exact command replay and moving-stop component review

The v14 input is preserved byte-for-byte. The component resets the same complete
MuJoCo plant with seed91011, scene/model and97 checked physical input identities,
then replays every accepted qtarget for ticks0–694 with2×2ms integration. It does
not initialize by injecting q/v. Independent observer comparisons at all1390
substeps have maximum q error0.0 and dq error0.0.
At tick695 the component injects an explicit planner-failure event and runs only
the new stopping supervisor. The shared stopping block is byte-identical to the
actual benchmark (SHA in metrics.json); the main predictive planner is bypassed.

Stopping begins at s=0.06029618753193305, r=0.006045132810726585,
previous b=-0.16792036875525984; physical max|dq|=0.01603588920932871.
The new stop completes233 feedback cycles /0.932s virtual time. Final r is
1.136718215215271e-18, b=0.0, max|accepted dq|=
0.0, max|physical dq|=9.9328133974416e-05.
All466 stop substeps have SOLVED stopping commands, nonnegative progress speed,
zero contacts and true clearance at least0.015631824794838337m.
Actual command acceleration/jerk and progress acceleration/jerk are audited against
the unchanged limits. Full-cycle timing remains in cycles.csv:233 deadline misses,
maximum0.015158847s and command age0.004889357s. No real-time claim follows.

This is a moving-stop replay component test, not an additional main research
trial, held-out evaluation, persistent prediction success, hardware result,
Phase5 gate acceptance, or a replay of the old planner's internal solver state.
The recorded physical trajectory is fully reproduced before new stopping begins.
The v14 failure and v15/v16/v17 negative development epochs remain untouched.

Evidence: results/phase5/development/moving-stop-v1/frozen.json, materialized-identity.json,
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
