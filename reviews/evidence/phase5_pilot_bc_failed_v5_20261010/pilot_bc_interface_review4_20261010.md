# B/C immutable Ahead4 interface review — 2026-10-10

Reviewed `/private/tmp/phase5_pilot_bc_ahead_review_v4_20261010/src` and `/private/tmp/phase5_pilot_bc_runtime_profile_review_v4_20261010`. No compiler/native executable/simulation was run, and no reviewed source was edited.

## Identity checks

- Ahead4 READY: all 26 listed files match declared bytes/SHA-256. READY SHA-256: `d041a586f24168ed85e11c9baf234bb741cd053cf14e2aa576c72aeecbdc967f`.
- Runtime-profile READY: all 9 listed files match. READY SHA-256: `3d9f9df6283a0d7c2350f044ad6c58bf5913c378388db06d76e6218307c0b4db`.
- All 24 current attempt11 source entries in the runtime plan match the corresponding local Ahead4 bytes/SHA. This is comparison against the declared remote identities; it is not direct verification of remote files or a native execution.
- The plan dispatches exactly one new ELF with explicit input SHA and producer SHA. Its field `compile_argv` carries that runtime dispatch; driver comments retain compile wording, but the schema/actual argv/result annotation identify a runtime invocation.

## Previous findings repaired

- `Outcome::retainedLimits()` returns the owned `Storage.inputs.limits` and rejects a moved owner (`integrated_horizon_qp.cpp:223`). B speed is bitwise compared to that original profile (`candidate_validation.cpp:13`).
- Private token owns speed and the original Model/URDF q-domain intersection (`runtime_observer.hpp:75`, cpp:129). C uses the token fields. Mutable shared validation-limit members are gone.
- `validation_attempted_` latches before assessment. Public report is reset/recomputed, and caller-set passed cannot manufacture a token (cpp:122–126).
- C's reserve is inside the guarded attempt (cpp:134–136).
- Target-write attempt and written events precede both step event sequences (cpp:140–144). Each recorder append writes a complete bounded line and fsyncs before the next action. Missing written/returned events leave the corresponding action UNKNOWN/possibly partial.
- The source performs full query/witness checks but retains aggregate geometry evidence; Ahead4 READY states that limitation. Assessment/actual commit output retains minima/counts/interval diagnostics rather than per-query witnesses. This is not full retained witness evidence.

## Remaining concrete failure-to-success edge

`candidate_validation.cpp:27` sets `out.passed=true` before assigning the success-stage string. Its catch at :28 records an error without clearing passed. Similarly, `runtime_observer.cpp:156` sets `commit_.success=true` before assigning the final stage; :157 records an exception without changing success. Under the declared AS limit, a post-validation/post-publication string allocation failure can therefore produce true + nonempty error.

Private validation currently checks only report.passed, and the frontend's `active_first_cycle.cpp:86/:89/:100` checks token/success without rejecting the internal Assessment/Commit error. Thus a captured internal error can be omitted from the overall return condition. Minimal repair: require both `report.passed && report.error.empty()` before token minting and `committed.success && committed.error.empty()` before component success. Preserve factual history/counters if publication already occurred; the generic catch's `HISTORY_UNPUBLISHED` label should not be used for an error after actual publication. This is an exception-path issue, not a weakening of the ordinary numerical gates.

## Normal-path verification

- Snapshot owner/current ID/task boundary/time are checked again after B and before C; integration bytes must match. Value retains the same active Session and nominal binding. Token constructor and payload are private, consumed once, and failed runtime blocks future observation/current use.
- B validates all 400 ordered native value substeps, actual-history binding, exact held-C/w recurrence, beta0, physical domains and derivatives, clips/friction KKT, original affine/trust checks, full true+cover query/witness consistency and weighted sigma. NaN-sensitive actual q/v, acceleration, jerk, per-arm residual and singular values have finite/refusal gates. Interval comparisons reject NaN. The existing normalized source/affine owners remain the provenance of map arrays.
- C holds the same C for two real `mj_step` calls. Native return counters/physical history advance on returns. Accepted command/progress history and task sequence publish after both actual halves satisfy warning/contact/clock/position/velocity/derivative/frame/geometry/sigma checks. Failed partial steps remain physical advances and do not synthesize accepted history.
- Reach now uses maximum root-to-link translation-chain length, not the sum of sibling accelerometer branches. Unique child edges, cycle bounds, exactly seven unit rotational axes, frame binding and finite AABB/TCP/cover extents are checked. The private bound must be ≤2m. Root's independent math review owns the detailed 4/32 Lipschitz proof. Support remains only the discrete endpoints' linear interpolation, not continuous MuJoCo/hardware motion.
- Evidence receipt capacity is 24; ordinary full path uses 17 FIRST artifacts. Binary output has a 128 MiB aggregate cap, with a 4 MiB final-role reserve. Each of the two journals has a separate 12 MiB cap. These are separate limits, not a 128 MiB total-directory claim. Runtime CPU120s/AS2GiB and wall150s/stream1MiB limits are present and inherited limits are clamped.
- The final return requires empty outer error, actual C success and both Session/Simulation termination verification. It correctly permits changed integration after C; `boundary_same` is retained as a factual comparison rather than demanded after physical advancement. Successful cleanup observation returns only a completed Snapshot; observation failure becomes an outer error.

## Nonblocking evidence-collector limitation

The frontend calls commit journal receipt before writing `actual_commit.bin` (:87–88). Receipt failure can skip the detailed commit outcome file even though the owned outcome remains available; cleanup still retains native counters/after Snapshot when usable, and durable journal bytes remain. Independent best-effort outcome/receipt cleanup would preserve more failure evidence. This does not cause a normal numerical refusal to be promoted.

Phase5 remains NOT_ACCEPTED and Phase6 NOT_STARTED. A successful one-cycle stabilization pilot would not establish task completion, repeated sessions, stop acceptance, real-time operation, or a research ranking.
