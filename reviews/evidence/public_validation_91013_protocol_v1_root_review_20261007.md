# Pre-run independent review: prepared validation 91013 v1

Decision: **DO_NOT_APPROVE_PREPARED_PROTOCOL_V1**. The scorer can issue PASS for missing, nonfinite or incompletely covered evidence, contrary to the declared protocol. Retain the prepared v1 and these rejection reasons; revise/freeze/check the protocol and scorer before any physical execution. No collector or runner mode was executed and no root-approval file was created.

Scorer source SHA is `2f409c6f0682412a0f6c07a4a9678a9e82bbe79824ba78f4ec56882b64c2cce3`; protocol SHA `66e3ea6665f573ef729c0d1504499f0773e2f8d6de6157c3d5f6132bb075eb40`. They match the imported 248-input preparation freeze. This review verifies relevant imported source identities; it does not claim a fresh rehash of all 248 dependencies or a complete Python environment.

## Executed gate counterexamples

[The minimal reproducer](../../scripts/phase5/audit_validation_91013_gating_v1.py) executes the unchanged scorer with explicitly synthetic CSV/metadata packets and a declared no-plant identity `PublicServo` stub. The stub rejects nonfinite q/v/target input; it only isolates predictor computation from data-integrity and final gate logic. It is not a new fitted model, simulation trial or legitimate collector record. Synthetic packets do not authorize a physical run.

All nine synthetic cases returned exit code 0 and `PASS_FRESH_CURATED_CONDITIONAL_TRACE_ONLY`:

| Case | Reproduced problem |
|---|---|
| Synthetic control | A 42-row trace with only one cycle/one QP row passes despite the protocol's complete phase roster. This is a gate baseline, not a valid collector trace. |
| Header-only empty raw | Every active horizon has zero windows, maxima stay zero, all gates pass. |
| Warmup-only raw | Zero active windows also pass. |
| NaN q_post/v_post | Endpoint residual/RMSE become NaN, maxima remain zero and gates pass; report serialization emits nonstandard JSON NaN. |
| Warmup input NaN | Three failed warmup windows are recorded, yet final PASS filters only active metrics. |
| NaN QP A0 | `sum` becomes NaN; Python `max` retains zero SI violation. The QP sidecar also differs from its captured execution hash, but still passes. |
| api_error=999 | Wrapper/native/candidate checks ignore the actual API error field. |
| Failed attempt without row group | The attempt is never inspected because only row-driven groups are checked. |
| Duplicate attempt key | Dictionary construction overwrites the earlier failed attempt with a later SOLVED entry. |

These are independent scorer weaknesses, not claims that the frozen valid collector generated such records. The complete source snapshots, synthetic inputs/reports/logs and assertions are retained. No 91012/v3/evaluation physical output was used.

## Required revision before approval

1. Validate schema, finite physical q/v/target/q_post/v_post, timestamps/continuity, exact required phase prefix/counts and complete cycle/raw coverage against the frozen protocol. Require a nonempty set of scored active windows for every declared horizon; zero-denominator strata must be explicitly ineligible. Check terminal stop state and metadata consistency rather than accepting a summary boolean alone.
2. Bind every consumed raw/summary/cycle/attempt/row file to its execution hash. Present scorer binds only `raw.csv`; it does not check the other entries already captured in `execution.raw_files`. Require successful execution/source-identity metadata consistently.
3. Require all metric/residual/RMSE and candidate/A/age numerical values to be finite. QP bounds may contain legitimate directional infinities, but must reject NaN, reversed bounds and invalid infinity direction. Preserve native SOLVED-only and original SI `1e-7`/age `.05` limits.
4. Validate **every** attempt independently (`api_error==0`, wrapper/native status, candidate size/finiteness and timing), reject duplicate `(tick,kind)` keys, and check phase/cycle/attempt relationships. Require one complete contiguous row group per attempt. The original logger exports row indices but no explicit expected constraint-row count; full group completeness needs trusted declared/reconstructed counts or a frozen `constraint_rows` capture field, not merely “whatever rows happen to remain”.
5. Make any declared failure/regime violation prevent PASS, including warmup failures under the current `window_contract`. Require completed-window counts to equal eligible full-window counts. The protocol cannot say “any failure prevents PASS” while final code silently omits warmup failures. Emit strict finite JSON.

## Runner and collector layering

Static runner review finds sensible one-shot controls: explicit approval decision/seed/exact frozen SHA, pre-run identity checks, no overwrite of run/raw directories, and creation of the run directory before invoking the collector. A failed attempt still consumes that directory and cannot be rerun under the same epoch. No approval check was bypassed or executed here. The runner's post-run source-identity result must also be required by the scorer; current scorer does not directly test that execution field.

The frozen collector enforces native/wrapper command validity, original SI/age/history/continuation and measured/accepted geometry guards, logs each actual QP, applies physical contact/clearance/position/velocity checks and emits stop/failure status. A successful intact record is therefore more constrained than the synthetic packets. Those producer/source guarantees do not make the scorer an independent completeness/finite/API certificate, and cannot detect later sidecar corruption when their captured hashes are ignored. Raw/stream completeness must be checked independently; no stronger collector guarantee is invented by this review.

The forecasting loop itself is causal: measured q/v initialize each window once, predicted q/v are propagated internally, accepted future targets are conditional inputs and measured future states are endpoint scores. It retains complete windows and phase intersections; the critical defects are data integrity and final acceptance. Scope labels correctly limit this to fresh-seed known-curated-input development, long-hold shared stop, not untouched holdout/task/250 Hz/Phase5 acceptance.

[JSON evidence](public_validation_91013_protocol_v1_root_review_20261007.json) and unique `results/phase5-reference/root-validation-91013-gating-v1-20261007` READY preserve all nine cases. Execution was isolated under Dell `/home/codextransfer/clean-audits/validation-91013-gating-v1-20261007`, using existing NumPy/PyYAML; the local bundled interpreter lacked PyYAML, so no dependency was installed. Final reproducer SHA is `4a44013e71fc2c97387aefa3cdd889c76d75a1e4b3b770581b1babf0882598d4`. The original scorer/runner bytes remain unchanged.
