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

The subsequent [original-channel/AC-power recovery and55 entry record](../reviews/evidence/connection_power_recovery55_20261015/README.md) preserves13 maintenance payloads, both2MiB SHA manifests, power before/after, Root qualifications and fresh55 startup evidence. The human UAC completed; AC four-setting values are0 and DC/battery policy is unchanged. At checkpointfc1eb89, native55 had entered after fresh resource/1711-input checks. Its later failure and actual56 result are recorded in the [55–56 checkpoint](../reviews/evidence/phase5_stop55_56_initializer_v1_20261015/README.md). [Prepared57](../reviews/evidence/phase5_boundary57_prepared_v2_20261015/README.md) passes targeted tests but has no native entry at checkpointdb83630; the original Mac33GiB resource check failed. These source/review backups do not establish a full raw-evidence archive or phase acceptance.

## Dell cold storage and Mac capacity

On2026-10-15 the human explicitly authorized storing suitable large files on Dell
when Mac space is insufficient, provided this does not materially disturb the
run. Root verified the direct user message
`01a142bc-35b7-7052-9899-9edf5074d7a4` in status chat
`01a10a40-558c-71a3-b343-6ff4c2709b36`.

Keep runtime hot data on the original Dell WSL ext4 filesystem. Large raw
results and cold archives may stay on Dell; Mac keeps source/Git, small review
packets, manifests, figures and necessary samples. Avoid streaming high-frequency
runtime logs over SSH or through DrvFS. Perform large migrations outside active
experimental I/O. Until an explicit revised peak-space plan is documented, retain
the original Mac33GiB and actual Dell C/D80GiB startup requirements.

Check actual Windows physical-volume capacity, including the C volume hosting
the WSL VHDX; WSL's virtual ext4 free space is not physical C-volume availability.
Before removing a Mac archive copy, make a fresh Dell copy, verify whole SHA256,
gzip CRC/single EOF and all tar-member size/hash identities against the immutable
READY manifest, verify restore readability, then atomically finalize read-only
storage and a READY record. Retain copy/verification failures. Do not remove an
unverified unique evidence file. Record exact retained paths, hashes and which
copies were actually read back. C and D on the same Dell are not independent
hardware backups; removing one duplicate archive does not establish that all new
experimental evidence is fully backed up.

The [verified cold moves and explicit bounded-Mac plan](../reviews/evidence/phase5_cold_storage_and_bounded_Mac_v1_20261015/README.md) document the revised workload for fresh57. Two historical shipping duplicates (52 and53,3,577,634,473 bytes total) were copied to Dell C, fully verified and independently streamed back before their Mac shipping copies were removed. All Mac expanded52/53 payloads and the original final52 Mac/Dell archives remain. An unrelated contemporaneous free-space decline remains unexplained; process/swap cause is not established. Old33GiB resource failures remain retained.

In the new named mode, full native results and full cold archives remain on Dell. Mac selected extraction is capped at272MiB, its single transport at512MiB, shared derived/ledger files at1GiB and the small Git/report/temp pool at1GiB: total below3GiB. Keeping8GiB reserve and rounding upward gives12GiB minimum Mac free space for this mode. Bind the mode/collector hashes at fresh preentry; failed partials cannot reset or enlarge the capture budget. Oversized review data stay on Dell and Mac review is incomplete. Original33GiB remains the old full-mirror mode, not a check claimed to have passed. Actual Dell C/D80GiB and every native/process/numerical/physical/stop bound remain unchanged. Dell-only full results are not independent two-device backups; complete new experimental-data backup remains incomplete.

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

[Actual60's checkpoint](../reviews/evidence/phase5_actual60_capacity_fix_and_numeric_failure_v1_20261016/README.md) verifies a1,933,348,287-byte complete stored-evidence archive SHA256c50a288a6eb44a23ce25f2b2e98865267df4c62c7bfeb7fa93aa56a429d079b1 on physical Mac/Dell files. All2870 members/2112 native codecs and the persisted Mac whole-file SHA/CRC pass.85 frozen source files/profile/active ELF are included; dependency/build caches are excluded. Current43 numeric512 failure and all22 failed stop observations remain. Stored-evidence replication is separate from environment restoration, phase acceptance and the older53–57 replication gaps. Git contains the small report/figure records only.

The later [actual59 failure/archive checkpoint](../reviews/evidence/phase5_actual59_artifact_roster_failure_v1_20261016/README.md) verifies the32,501,100-byte archive SHA256cecc09b2fdcfe972f6a2d833a4e177f42d74414a550d990f06f8b830a7065bd8 on Mac and Dell. All562 members/36 native codecs and the persisted Mac SHA/CRC pass. The post-C25th-output refusal, absent cycle timing and original24 complete outputs remain explicit; recoverable failed evidence does not become a successful trial. Only small recovery records are in Git, with older replication gaps unchanged.

Actual58's [archive checkpoint](../reviews/evidence/phase5_initializer58_v6_unit_v1_20261016/README.md) records a3,225,158,075-byte complete stored-evidence archive, SHA25612408b223543570a2e92fe912bddb5525d49645bec71c38631f4b069e8ff0fb5, on independent Mac and Dell physical files. Root verifies all4405 members,3496 native codecs and the persisted Mac whole-file SHA/CRC. Frozen source/profile/active ELF are included; dependency/build caches are excluded. This closes58 stored-evidence replication only, not standalone environment restoration, older53–57 gaps or any acceptance gate. The raw archive is Git-ignored; Git contains the small source/review/figure checkpoint.

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
