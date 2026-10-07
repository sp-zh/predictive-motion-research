# Expanded servo failure-state command and stop diagnostic

Date: 2026-10-07, America/Toronto. Failure-state stop availability: **FAIL**.
Diagnostics and deterministic replay checks complete; no main-MPC integration,
model coefficient/domain change, guard relaxation or Phase 5 acceptance.

The original 8 mrad expanded trial remains failed. Its original command QP was
not captured. `servo-expanded-qp-reconstruction-v1` explicitly reconstructs the
next tick 854 from the final recorded physical q/v, accepted c/w/alpha and fixed
waveform. It compiles the public model only for joint bounds and queries current
kinematic geometry; it constructs no mjData or future plant rollout. Offline
state age is zero solely for matrix analysis, never for command execution.

The reconstructed 29×7 H/g/A/l/u and row IDs are retained. Native OSQP 1.0.0
reports PRIMAL_INFEASIBLE with geometry; its 21 command-only rows solve with zero
original SI violation. Every coordinate's command-bound intersection is
nonempty. Three shaft/left cover constraints nevertheless conflict with that
box. For cover38 the required lower bound is -0.01597848782 m/s, while the
maximum over every admissible next candidate command w is -0.02099061397 m/s;
the deficit is 0.00501212615 m/s. Covers37 and39 also have positive deficits.
Direct linear-program feasibility reports infeasible. The softened normalized
margin result is negative and violates an original jerk row by 103.269;
it is not an executable candidate. All original tolerances remain unchanged.

`servo-expanded-failure-stop-replay-v1` resets the original seed/initial pose,
applies all recorded accepted targets through the full common plant, including
warmup, and compares every one of 1,708 records. q_before/q_post, v_before/v_post,
held target and timestamp errors are all exactly zero. It never injects only
the final physical state. A synthetic negative control changes the first
q_post_0 by 1e-6 rad; replay rejects it before any stop attempt, preserving the
original input. This tests the refusal to credit an unmatched replay.

Only after matching the full prefix does the new diagnostic call the shared
`stoppingProblem`/`constrainPreviewCommand` command-stop block, the existing
dynamic geometry keep range, dual-target nonlinear checks and 50 ms guard.
The identification fixture has no path-progress state. The actual first stop
QP, including H/g/A/l/u and all 67 row IDs, is captured from this new replay
attempt. It is distinct from the reconstruction and from the uncaptured old
trial command QP. Its command box has the same three geometry conflicts; the
full LP is infeasible. Root independently recomputes the original SI1e-7
tolerance-aware support proof and confirms the conflicts.

The stop result is `NO_FEASIBLE_STOP_NO_COMMAND_SIMULATION_TERMINATED`, native
PRIMAL_INFEASIBLE, return code3 and zero accepted stop commands. Virtual time
remains 3.416 s. Physical max speed is 0.03451032067 rad/s and the last accepted
command max speed 0.04339710450 rad/s. `completed_stop=false`; no fabricated zero,
physical settling, safe-hold, task completion or real-time success is credited.
The previously accepted Phase 4 and limited moving-stop evidence remain intact.

Both C++ diagnostics build in a separate native Linux cache; existing adapter
CMake, original fixture/binary, main-core source and frozen model are unchanged.
Source/binary/input hashes and verified cache closures are retained separately
for reconstruction and replay. The unit's figure shows next-command-box support
versus required geometry lower bounds and nonzero final speeds. A new actual
MuJoCo 3.3.7 model render shows the recorded failure pose using existing OSMesa,
forward geometry only, without controller execution or physics integration.
Pinned upstream assets are verified; metres/radians and existing CAD units are
preserved. Both images are visually inspected, including the corrected next
candidate command label. Rendering does not establish controller performance.

Next: prospectively freeze a geometry/jerk-compatible expanded reference using
previously accepted target increments and an explicit new-initial-target
offset. Previously observed inputs are a curated regression reference, not an
untouched old holdout. Execute fresh physical data with every original guard,
explicit stop/failure capture and unchanged model/accuracy thresholds. In
parallel, an isolated local-domain C++ transition module may be prepared after
the independent oracle, while main-MPC integration remains gated.
