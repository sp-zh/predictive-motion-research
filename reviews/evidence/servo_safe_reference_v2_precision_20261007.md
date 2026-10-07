# Safe-reference v2 offline QP precision audit

Scope: one actually captured34×7 QP, four fresh offline frozen-wrapper solves. No plant/fitting/model/geometry/guard changes. Original failure had no exported raw_status, maximumViolationRow or candidate; none is reconstructed here.

All seven command boxes are nonempty. Independent HiGHS finds full-QP feasibility with original SI violation1.137e-13. The linked wrapper header, reactive-QP library and OSQP1.0.0 static library exactly match v2 frozen SHA identities; root-installed-v24 is reused only after that strict comparison.

| Requested abs/rel tolerance | New offline status / rawStatus | Iterations | Wrapper SI violation | Independent Solved-only SI violation | Wall [s] |
|---|---|---:|---:|---:|---:|
| 1e-09 | CONSTRAINT_VIOLATION / 1 | 142 | 1.1616e-07 | unavailable; candidate cleared | 0.000222 |
| 1e-11 | SOLVED / 1 | 156 | 3.6101e-09 | 3.610111320995202e-09 | 0.000204 |
| 1e-12 | SOLVED / 1 | 166 | 1.5216e-10 | 1.5215562143566785e-10 | 0.000198 |
| 1e-13 | SOLVED / 1 | 176 | 3.3808e-11 | 3.380762336746557e-11 | 0.000209 |

The new baseline1e-9 reports nativeSOLVED/rawStatus1 but wrapperCONSTRAINT_VIOLATION,1.1616e-7 at row16 (command jerk, index4); it exposes zero velocity entries. This is the new offline result only. Repeating the status does not identify the original failed point or its worst row.

Predetermined1e-11/1e-12/1e-13 stopping tolerances all return nativeSOLVED and wrapperSOLVED, with independent original-row validation below the unchanged1e-7 threshold. No Inaccurate/failed candidate is accepted. Max iterations4000, solver budget50ms, original bounds and acceptance are unchanged. Offline state age0 is a replay convention and does not relax the live50ms observation guard.

Original safe-reference-v2 primary failure remains retained even though its shared stop completed. These cold single-QP numerical records motivate a separately frozen prospective stricter-precision setting; they do not establish a full-run repair, arbitrary matrix convergence, online250Hz performance, model-domain extension, corrected servo contract, CTRL-001 closure or Phase5 acceptance. No authoritative configuration was edited.
