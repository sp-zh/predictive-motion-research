# B/C pilot interface review 1 — 2026-10-10

Scope: read-only source review of `/private/tmp/phase5_pilot_bc_active_v1_20261010/src`. No compiler, project native executable, simulation, or project-chat tool was run. This is a development review, not phase acceptance. The entry had not yet connected B/C when reviewed. Root reports attempt8 nine-TU compile/link success; that is externally reported evidence, not an independent compile result here.

## Necessary interface repair

**Token-specific limits can be overwritten before consumption.** In the initially reviewed `runtime_observer.cpp:125`, every successful `validateCandidate` writes `Simulation::validated_speed_`; `commit` uses that mutable member for its actual-velocity gate. Validation can be invoked twice against the same current Snapshot because only `!commit_.attempted` is checked. A second successful validation can therefore change the limit used to consume the first token. The currently inspected source also puts q-domain intersections in mutable `validated_q_lower_/upper_`, which has the same issue.

`candidate_validation.cpp:13` checks caller speed only for finite positivity. It does not establish that the B/C limit equals the `connected` problem's original physical-speed profile. Bind it to a read-only `Outcome::retainedLimits()` getter, retain speed and the URDF/Model q-domain intersection inside the private token, and consume those token fields. A one-validation latch is appropriate for this explicitly one-pilot API. Root accepted this repair and described prospective attempt9; the changes were not yet present in the last inspected source.

## Failure-prefix repair already confirmed

The initially reviewed commit source wrote native ctrl before its first durable commit event. The latest source now has `BEFORE_VALIDATED_HELD_TARGET_WRITE` at `runtime_observer.cpp:135`, the seven ctrl writes at :136, and `VALIDATED_HELD_TARGET_WRITTEN_NO_STEP_YET` at :137, preceding the two physical-step event sequences. This resolves the missing target-write prefix. A terminal write-attempt without a written event must remain UNKNOWN/possibly partial; it cannot mean that ctrl was unchanged. The recorder must provide the same bounded durable write semantics as the warmup journal when the entry is connected.

## Concrete failure-record issue

`runtime_observer.cpp:130` consumes the token and latches `commit_.attempted`, then calls `commit_.points.reserve(2)` outside the `try` at :131. An allocation exception therefore bypasses the sticky failure/error recording branch, leaving attempted=true with stage `NOT_STARTED`. Put the allocation before the irreversible attempt latch, or place it inside the guarded attempt so the owned outcome records the failure. This is an error-path consistency issue, not a claim that a native step already occurred.

## Evidence integration still needed before claiming full retained B/C evidence

`candidate_validation.cpp:7` checks full configured true-pair and cover roster count and all distance/normal/witness consistency. Its `Point` retains only minima/counts/derived diagnostics; the actual `geometry::Snapshot` is discarded. Similarly, C's `CommitPoint` retains minima/counts, while :146–147 discards the per-query records. Thus current code performs witness validation but does not retain full witness/roster evidence. Entry integration should serialize the checked pair identities, cover index, distances, normals and witnesses under a bounded payload plan, including checked prefixes on failure, or label its evidence as aggregate-only. Current `lossless_evidence` exposes candidate raw value serialization, but no Assessment/CommitOutcome writer yet; this is expected unfinished integration, not an alleged compiler error.

## Confirmed source properties

- `ValidatedCandidate` has a private constructor and retains the actual Snapshot owner token, copied boundary/integration bits and moved owned candidate value. A caller-supplied `Assessment::passed` cannot manufacture a token: Simulation resets the report and reruns assessment.
- Validation and commit both require current owner-bound Snapshot provenance. Validation rechecks exact integration bytes after assessment; commit checks them before target writes.
- OwnedCandidateValue holds a shared Session storage owner; `sessionActive()` rejects terminated or failed sessions. Its raw result/cells remain owned for token lifetime. Candidate Model/ticket/budget destruction order is sound.
- First C and accepted w derive from the native-accepted first4ms proposal. The same target is held for exactly two `mj_step` calls. Physical substep counters/history advance on actual returns; accepted C/w/alpha/progress and task tick/sequence publish only after both observed halves pass. Observed partial failures latch failed and block future current/observe use; a token is consumed once.
- Source/model cycle indexing is consistent: cells are zero-based and native cycle is one-based. Candidate assessment's `tick+1` matches the canonical Model.
- Existing geometry APIs used by the draft (`Snapshot`, `objects`, `cover`, `excluded`, local AABB) match the canonical header. No definite source-level compile/API mismatch was found. A real compile must include the new `candidate_validation.cpp` translation unit.
- Reach construction sums all URDF joint-origin translation norms and the largest attached local geometry/TCP/cover extent; only rotational/fixed joints are accepted, seven rotational joints are required, and the bound must be finite and ≤2m. Root's independent math reviewer owns the detailed Lipschitz proof. This review does not certify a continuous native trajectory: the source explicitly scopes interval support to the discrete endpoints' linear interpolation.
- Phase5 remains NOT_ACCEPTED; these interfaces and a future pilot do not establish repeated sessions, stop/full-task acceptance or a research advantage.
