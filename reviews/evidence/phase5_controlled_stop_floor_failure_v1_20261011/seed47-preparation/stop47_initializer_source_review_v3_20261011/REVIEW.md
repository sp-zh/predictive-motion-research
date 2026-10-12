47 initializer independent narrow source review, v2 refusal and v3 repair

SOURCE ONLY; no compiler, pure regression, Model, OSQP, MuJoCo, controller, or physical execution by this reviewer. This confirms a source delta and does not establish stop success or phase acceptance.

V2 refusal: row_direction_bounds.resize(m,4) left an uninitialized suffix when a row check threw; prepare caught the error and returned the entire matrix. Core and codec then copied/wrote that unreadable suffix. The original v2 source/build/link and refusal record remain preserved.

V3 repair: the full matrix starts at Zero. row_bounds_written advances only after a completed row. The core retains that count, and the codec writes its u64 before the matrix and explicitly declares unwritten zeros unavailable as evidence. The source regression checks a second-row flat refusal produces count1 of2, finite matrix and exact-zero suffix. No extra prefix materialization was introduced; the250000 precharge and existing scalar slack cover this delta.

The initializer is stop-only, applies solely to new optimizer startingguess before currenthint/native, and rechecks all augmented rows at unchanged1e-12. epsilon<=1e-6 and max3 attempts remain. Original nativeSOLVED/fullSI/strict/B/privateC and success-C/stop/error gates remain; checked owner/runtime/candidate/currenthint/stop monitor/Ledger files match v2 bytewise. No remaining concrete execution blocker was found in this reviewed source delta.

All54 v3 source size/SHA bindings match SOURCE_PREPARATION.json, source-manifest SHA e0fef85269c2fd2f1617ff19f6c960379c901c37cffe44286c407f9644f25c4b. The codec role remainsV1; v2 produced no native initializer payload. The first native output is intended to use v3 and a decoder that explicitly reads the new count and binds source/profile. That future execution is not claimed here. Phase5 NOT_ACCEPTED, Phase6 NOT_STARTED.
