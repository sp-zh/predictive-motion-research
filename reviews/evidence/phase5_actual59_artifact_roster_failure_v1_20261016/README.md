# Actual59: first command retained, fixed24-file integration failure

Fresh59 entered once at2026-10-16T05:30:09.276705Z (Toronto01:30), driver8900,
native8901. It naturally terminates with **`bounded fixed artifact names`**
after **1 committed command /2 actual simulated2ms task substeps /4ms**.
The separate1000 warmup steps are not task duration. It enters1 trial and2
forecasts. Stop has0 observations, dwell0/50; the stop-only leaving policy is
not activated. This early failure does not test the saved current74 repair in
motion. Phase5 **NOT_ACCEPTED**, Phase6 **NOT_STARTED**; no hardware/held-out run.

Root independently verifies435 selected payloads (47,489,969 bytes), all36
complete binaries (56,122,442 decoded bytes), stored/raw SHA256, CRC and single
EOF.1723 before/after input records match byte-for-byte. Session/native
termination checks pass. Entry wall is16.451755091s; the separate whole-cycle
record is4.701052433s and misses4ms. It records physical completion,1C and2 task
steps even though later evidence emission fails. The descriptive stage
`COMPLETE_REOBSERVED_DYNAMIC_TRANSACTION_DIAGNOSTIC` does not erase its fatal
error or establish a completed session. [Independent result](Root/RESULT.json),
[all selected codec receipts](Root/CODEC_RECEIPTS.json),
[trial file roster](Root/TRIAL0_ARTIFACT_ROSTER.json),
[saved-data auditor](Root/ROOT_ACTUAL_SAVED_DATA_AUDITOR.py).

The two retained actual task points have worldTCP translation errors
.0032157178896001933 and.0032157330466065503m, orientation errors
.005484309707863156 and.005484323044733557rad. Root recomputes both from the
saved actual/desired poses; each meets the original10mm/.05rad point flags.
This is a two-point measurement, not full task, stop, continuous plant safety
or a complete independent original B/C/SI re-audit. There is no new successful
task video. [The latest longer actual braking figure remains58](../phase5_initializer58_v6_unit_v1_20261016/README.md).

## Concrete integration cause

Frozen v12 `lossless_evidence.cpp:56` requires `receipts_.size()<24`, in addition
to safe literal file names. It is a fixed per-directory output count, **not an
enumerated filename whitelist**. Root initially described it as a whitelist
before checking the exact condition; this is the correction.

The new standalone `hint_negative_leaving_events.bin` adds one output to the
complete successful-C path. All24 earlier binary receipts are complete,
including actual commit, actual task errors, after-observation and fine timing.
The final25th `cycle_timing.bin` is refused before receipt insertion and does
not exist. The outer `whole_current_cycle.bin` uses a separate directory and
remains available. No missing per-stage timing is reconstructed or substituted.
The single-codec synthetic test had not covered this full output chain: this
is an integration-test gap, not a passing full integration test or a Bland
numerical failure. The consumed59 source, cap, input files and evidence remain
unchanged; no retry or retroactive expansion is permitted.

Fresh60 development merges all old KKT-rank and new chosen-leaving fields into
the existing `hint_kkt_rank_events.bin`, with a distinct explicit V2 role.
It retains the24-file limit and original canonical24-entry reader. The proposed
full payload bound is512×32+512×48+4096=45056bytes; all records must remain,
with original numeric/storage/native/physical/stop caps. A targeted pure
regression must exercise the complete24-file successful output roster including
final cycle timing and still refuse a25th output. This is a synthetic output
integration check, not Model/C execution. New60 compile/regression/entry results
must be recorded separately.

## Actual immutable entry and storage binding

[Root entry binding](entry/ACTUAL_ENTRY_BINDING_REVIEW.json) checks the executed
runtime plan SHA256
`3f5938f2074500fc89622f5e83e95da4116d5d06368ed45a426010f090cc6f4f`,
all83 frozen Git source files, profile and ELF against actual runtime pins.
The entire parsed prepared/actual plan objects agree. Its observed terminal
flag is explicitly an early observation, superseded by the decoded result.
Profile SHA256 `187e08287b4fa7146692310c585d6d09fc0bad06af782136d136dd8e207c5f67`;
ELF SHA256 `9566564550c1515d17b67b5af4ed0868cb7b78492663a49dd24c09b33a63485d`.
Original finite caps and human-authorized bounded-Mac storage mode remain.

[Metadata qualifications](entry/PREENTRY59_STORAGE_METADATA_QUALIFIERS.json)
preserve copy-forward `during58` wording and the original executable filename
containing58 without rewriting the actual59 plan/ENTRY. `old33GiB_gate_passed:false`
means no claim that the old full-mirror-mode gate executed; current Mac free
space exceeds33GiB. It is not a measurement of current insufficient space.

Selected packet READY SHA256
`19aea2dcb34cb58193996cc3f3029fcbf1f50be9173c20aec8692a1f201cc5c5`;
single transport27,669,492bytes, SHA256
`fda63b19348bb591c6d741506b95fcf0e9f89631e2c96899ae3e5dfb0e9d052b`.
All retained original selected capture limits remain; no second capture/reset.
Full59 stored-evidence cross-device archive verification is **complete** for
the declared stored execution evidence. The32,501,100-byte archive SHA256 is
`cecc09b2fdcfe972f6a2d833a4e177f42d74414a550d990f06f8b830a7065bd8`.

- Dell: `/home/codextransfer/predictive_motion/transfer/cold-archives/native59-complete-20261016-v1/complete59.tar.gz`
- Mac: `/Users/uot/Documents/ChatGPT/ros/transfer/cold-backups/native59-complete-20261016-v1/complete59.tar.gz`

Root independently verifies all562 members (558 payload files), all36 native
codecs, outer CRC/single EOF and the actual persisted Mac whole-file SHA/CRC.
All83 frozen source files match actual runtime pins and archive member identities;
profile/active ELF are included, dependency/build caches excluded.
[Root full readback](archive/FULL_ARCHIVE_MAC_READBACK_AND_COPY.json),
[Mac READY](archive/MAC_ARCHIVE_READY.json),
[separate post-native plan](archive/POST_NATIVE_MAC_BACKUP_PLAN.json),
[original Dell READY](archive/DELL_READY.json),
[bounded streaming auditor](archive/ROOT_FULL_ARCHIVE_AUDITOR.py).
The separate post-native copy keeps a4GiB part/final limit,16MiB metadata and
the original33GiB free before/after; it does not expand in-run12GiB mode or
selected-capture caps. Both final archive copies and metadata are read-only.
The original Dell READY's Mac-pending wording is preserved; the later Mac
READY SHA256 `bfcd7d736edcd1a6d9e9bf9ac6a9b3bc41d6ec0b58c6039e47c4badc8172ef8f`
supplies the new independent proof. Git includes only the small records, not
the raw archive. Stored-evidence recoverability does not prove a standalone
environment restoration or successful math/task/stop/phase outcome.
The verified complete58 Mac/Dell archive remains separate; older53–57
replication gaps remain. [Archive records](ARCHIVE_FILES.json).
[Small copied-file manifest](FILES.json).
