# Actual61: exact-cycle repair crosses the saved blockage; stop still fails

Offline61 was invoked once at 2026-10-16 02:38:28 Toronto and ended naturally. It completes **96 commands / 192 simulated 2 ms task substeps / 384 ms**, comprising 32 active and 64 braking commands, with 173 trials and 346 forecasts. Entry wall time is 667.127381108 s. The 1,192 physical steps include 1,000 warm-up steps.

The terminal error is **`actual stop thresholds not reached in declared64 brake commands`**. All **128** actual stop observations fail the original simultaneous thresholds; dwell remains **0/50** and the later 25-command hold section is never entered. The stop monitor's `passed=0, failed=0` describes monitor state, not successful stopping. Each of the 96 whole-current records has physical_complete=1 before the post-loop stop refusal; every whole-current wall time misses 4 ms. The final whole record cannot replace the terminal result. No complete task, realtime result, successful task video, hardware permission or phase acceptance follows. Phase5 remains NOT_ACCEPTED; Phase6 remains NOT_STARTED.

## What changed and what was checked

[Frozen v14 source/profile](../../../tools/phase5_controlled_stop_session_v14/README.md) preserves 88 source files including the 87-entry identity manifest. The stop-only change recognizes an exact two-iteration optimizer repeat using full primal bits, full ordered row/side faces, selected row/side and unchanged monotone eligibility generation. It only permits the existing full-endpoint numerical-domain check for that row, under the original 1e-12 limit. It does not unconditionally ignore constraints, project physical state, prove a nonnegative dual exists or establish general convergence. Original QP assembly, initializer, SI/nonlinear/geometric/B/history/two-2ms/C/stop criteria remain unchanged.

The added fixed workspace is 704 scalar/index slots: total 744,912 below the unchanged 745,000 reservation. The unchanged whole numeric bound is 1,799,506,160 below 1.8 billion. V3 retains 512 rank records, 512 chosen-leaving records and at most 144 references to those existing records, with a 46,208-byte raw bound. It retains 24 per-trial output slots and the old explicit reader. Native indices do not serialize complete optimizer-state comparison snapshots; exact-trigger evidence combines source, targeted tests and the direct pure witness.

Root verifies the saved 37 compile, 26 link and 25 pure results; the eight saved stop QPs pass unchanged full-row primal 1e-12 and stationarity 1e-10 gates. The previous seven stop cases retain all five core outputs byte-for-byte and six active cores remain byte-identical. Same-Result V2/V3 old fields agree completely. These are preparation/compatibility results, separate from actual stopping. Preliminary source and reader-assumption failures are retained.

The original512-event actual60 failure is reproduced exactly. A preliminary NNLS certificate has nonnegative multipliers but full stationarity **0.020461411420954992**, exceeding 1e-10; it is rejected and preserved, including its 60,944-byte certificate. Exit0 did not make that certificate valid. This is not a proof that no suitable dual exists. Direct witnesses expose the zero-fraction row7250 cycle; the production change uses bounded generation tracking rather than the prototype's extra full-mask comparison.

Actual61 current43/trial0 has the bit-exact same six-field initialized fixture as the failed actual60 current43/trial0, including original nominal seed and D. Its 284 hint events and final x/y are byte-exact with the production pure replay; six eligibility references identify rows7250–7254 and7277. Original full-row primal residual is 5.464270529109694e-13 and stationarity is 2.3592239273284576e-16. Current43 still requires two trials before C; trial0's repaired hint/native entry alone is not a claim of B/C acceptance.

Root independently checks 1,019 selected payload hashes and all 316 complete binary codecs (stored/raw SHA, CRC and single EOF), decodes all 96 whole records, recomputes all 128 stop predicates/anchor resets and verifies 1,728 before/after input identities byte-for-byte. [Actual review](Root/actual/RESULT.json), [current43 binding](Root/actual/ACTUAL43_MATRIX_AND_FORMAL_BINDING.json), [all stop rows](Root/actual/STOP_ROWS.json), [preparation reviews](Root/preparation/SOURCE88_AND_SUPERVISOR_AST_REVIEW.json). This is not an independent re-audit of every original SI/nonlinear/geometric/B/C calculation.

## Offline termination and manual wait

Root AST review binds the original offline52 supervisor engine except61/62 string labels. One driver invocation, original resource/deadline limits, detached local logs and no automatic retries are retained. Fresh SSH observed identical detached process identities during execution. After completion, [live original-channel readback](Root/actual/LIVE_TERMINAL_READBACK.json) at07:00:46 UTC confirms the three known supervisor/driver/native PIDs absent and EXIT/manualwait/READY exact remote bytes. This is not a claim to have enumerated all processes.

The driver exits1 after the retained stop refusal. [MANUAL_WAIT_AFTER_61](offline61-status/MANUAL_WAIT_AFTER_61.json) requires direct human resume; existing daily02:00 Toronto heartbeat is [PAUSED](status_chat/OFFLINE61_AUTOMATION_PAUSED.json). Only result preservation, necessary review and recoverable backup continue. No new development, controller/pure probes or62 may start from network restoration, elapsed time, old resume or agent messages. Direct human continue in the status chat is required. The previous PROJECT state and pre-entry pending snapshots are retained as dated evidence, superseded by this terminal record.

## Verified recovery and public backup scope

Complete61 stored evidence has independent physical archive files on Mac and Dell:

- Mac: `transfer/cold-backups/native61-complete-20261016-v1/complete61.tar.gz`
- Dell: `/home/codextransfer/predictive_motion/transfer/cold-archives/native61-complete-20261016-v1/complete61.tar.gz`
- Size **3,627,990,572 bytes**, SHA-256 **f06f0e976963bebaeee86a612d0ecae435f128b9599041a6cc854e2d4686bcf8**.
- All5,045 archive members, including4,028 complete native codecs with9,744,956,831 raw bytes, verified by Root. All stored/raw SHA, inner/outer CRC and single-EOF checks pass. The persisted Mac file was reopened and checked in full.
- [Mac/Dell READY](archive/MAC_ARCHIVE_READY.json), [Root readback](archive/FULL_ARCHIVE_MAC_READBACK_AND_COPY.json), [original Dell READY](archive/DELL_READY.json). Its original Mac_PENDING wording remains historical; the new Root proof closes that separate physical-copy task.

The separately bounded one-attempt post-native copy uses a4GiB archive cap,16MiB metadata cap and original33GiB free-space checks before/after. It does not change/refund the in-run12GiB or selected-capture budgets. Frozen source/profile/active ELF are included; build/dependency caches are excluded. This verifies stored-evidence recovery, not standalone environment restoration. Earlier58/59/60 verified physical copies remain; older53–57 complete-replication gaps remain unresolved.

Git includes the small frozen source, profile, reviews, original negative certificate and [all-observation diagnostic plot](../../../figures/phase5_stop61_actual_braking_20261016.png), with source hashes and selection provenance. Large raw evidence/ELFs, credentials and caches are excluded. The current public commit/push must be checked against the remote before reporting public backup complete. The earlier actual60 checkpointac121c3 was verified by02:27 Toronto, meeting this day's02:30 preparation target; this later61 outcome does not retroactively belong to that checkpoint.
