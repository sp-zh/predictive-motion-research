# Project backup

GitHub repository: https://github.com/sp-zh/predictive-motion-research

Visibility: **Public**, independently verified on 2026-10-08 after the human explicitly instructed “改回public” in the communication-check chat. Earlier private-backup records retain their historical wording. Credentials and local caches remain excluded.

On 2026-10-08 the human directly approved “批准本次及后续同范围公开备份”: fcbb266 and later same-scope project source, verification reports, documentation and diagnostic/showcase figures may be publicly backed up without repeated confirmation. Large raw results and dependency/build caches stay in verified Mac/Dell archives. This approval changes publication scope only; experimental run permissions and phase gates remain separate. [Verified authorization](../reviews/evidence/public_backup_authorization_20261008.json).

This repository backs up source, tests, configuration, model descriptions,
documentation, review reports, figures and small CAD artifacts. A Git push is
required to back up later local changes; this is not an automatic schedule.

Raw experimental evidence under `results/`, transfer archives under `transfer/`,
generated simulation assets, build outputs, dependency caches and SSH credentials
are excluded. Existing evidence and retained failures remain in their local
Mac/Dell locations with their original hashes. This Git repository alone cannot
restore the complete experimental dataset. Review links into excluded evidence
require those local archives.

## 2026-10-15 recoverable progress checkpoint

The [53–54/55 source checkpoint](../reviews/evidence/phase5_stop53_54_and_refinement55_v1_20261015/README.md) includes exact versioned v8 source/profile, independent saved-data reports and actual54 PNG/SVG/CSV with provenance. It preserves failures and the direct-human resumption.At source checkpoint0ef35f8,55 was prepared but unconsumed after an SSH banner timeout. This checkpoint can be publicly committed/pushed under the existing authorization while communication is restored; it does not gate the next actual entry.

[Storage identities](../reviews/evidence/phase5_stop53_54_and_refinement55_v1_20261015/STORAGE_CHECKPOINT.json) explicitly mark the new full-evidence backup INCOMPLETE.53 has a complete Mac packet and verified outer transport hash;54 has a verified selected Mac packet, with remaining raw data on Dell. New comprehensive Mac/Dell archive member readback is pending the original connection. Do not describe Git or the selected54 packet as a complete experimental-data backup. The older52 complete backup remains valid and unchanged.

The subsequent [original-channel/AC-power recovery and55 entry record](../reviews/evidence/connection_power_recovery55_20261015/README.md) preserves13 maintenance payloads, both2MiB SHA manifests, power before/after, Root qualifications and fresh55 startup evidence. The human UAC completed; AC four-setting values are0 and DC/battery policy is unchanged. Native55 is running after fresh resource/1711-input checks; no result or full experimental evidence backup is implied. This small recovery checkpoint is independent of the running experiment and does not gate it.

## Required checkpoints

Back up every completed work unit and every phase, including work still awaiting
independent acceptance. Inspect `git status` and the intended diff, commit the
completed files, then run `git push origin HEAD`. Verify the remote branch commit
identity. Milestone backups are authorized by the user; no repeated confirmation
is needed. This is a work-completion policy, not a timed background job.

For evidence excluded from Git, preserve immutable archives and failures, verify
their SHA-256 and READY manifests, and save a small checkpoint record under
`reviews/evidence/` with archive hashes, storage locations and verified copies.
Integrate completed Dell changes into the Mac checkout for backup. Do not claim
large data is backed up to GitHub: the committed record identifies local archives.
Report unsuccessful uploads or evidence copies as incomplete backups and retry
when the connection is restored. Never overwrite accepted historical evidence.

## Presentation assets

The user requests demonstrable images and permits project 3D model uploads.
Back up useful renders, plots and small STL/STEP/FreeCAD artifacts alongside
each milestone. Keep the gallery and model index in [showcase.md](showcase.md)
current, with units and evidence scope. Existing images in `figures/` and models
in `cad/generated/` are already committed. Host-specific generated simulation
XML and upstream dependency caches remain excluded.

Small task-completion MP4s, thumbnails and provenance under `videos/` are also
part of milestone backups. Select successful accurate/smooth runs for display,
record the selection criteria, and preserve the complete research outcomes.

## Earlier preparation before the daily disconnect

On2026-10-12 the human requested “之后要提前一点做备份”. The existing preparation automation now runs at02:00 America/Toronto when resumed, aiming to verify the remote SHA of completed units or a clearly scoped recoverable checkpoint before02:30, ahead of the approximate03:00 disconnect. It was PAUSED after offline52 and restored ACTIVE by the direct2026-10-15 human resume. The next offline batch ends in manual wait again; reconnecting or a scheduled wake does not authorize resuming that future wait.

Results produced later by the finite offline batch are preserved locally first and verified/backed up after connection recovery. Unfinished runs, uncopied large evidence and unverified archives are explicitly incomplete backups; a preparation checkpoint does not imply their results exist or are accepted.
