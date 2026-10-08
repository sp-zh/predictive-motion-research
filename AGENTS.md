# Project paused by the user

The human explicitly instructed on 2026-10-08: “完成当前最小工作后就保存，上传git，不要继续了”. Finish only the current minimal checkpoint preservation and private Git push/remote verification, then stop all project research, implementation, repairs, builds and experiments. Do not run a nonempty affine kernel/checker, original model/plant, scorer or seed91013 physical run; do not issue a run approval or continue Phase5/later phases until the human explicitly resumes. Prior continuation and dispatch instructions are revoked. Preserve accepted Phase4 evidence and all existing files/failures. Phase5 remains NOT_ACCEPTED; Phase6 is NOT_STARTED. PROJECT_PAUSED.json records this pause; prior resumption and pause history remain under reviews/evidence/.

# Required milestone backups

The user requires a backup after every completed work unit and every phase.
Inspect the intended diff, exclude credentials and local caches, commit the
completed source/configuration/tests/reviews/documentation, and push to the
private repository https://github.com/sp-zh/predictive-motion-research.
Verify that the remote branch contains the committed checkpoint before reporting
the backup complete. Existing user authorization covers these milestone pushes;
do not request permission again for routine backups to this private repository.

For large experimental evidence excluded from Git, preserve immutable archives
and retained failures, verify SHA-256 and READY manifests, and commit a small
checkpoint record under reviews/evidence/ documenting archive identities,
Mac/Dell storage locations and which copies have actually been verified.
Coordinate Dell-produced changes into the Mac backup checkout before declaring
a milestone backed up. A backup does not imply that a phase gate has passed.
If a push or evidence copy fails, retain the local checkpoint and report the
backup as incomplete until the failure is resolved. See docs/backup.md.

# Demonstrable visual deliverables

The user requires presentation-ready images and permits uploading project 3D
models to the private Git repository. For each completed part or phase, create
or update relevant actual simulation/CAD renders and evidence-backed plots,
and maintain docs/showcase.md as the visual entry point. Include useful small
STL/STEP/FreeCAD models in cad/generated/ and figures in figures/ in milestone
commits. Inspect newly produced visuals and model units before delivery; record
their source parameters/data, hashes and validation scope. Preserve failures
and distinguish development diagnostics from accepted research results.
Rendered or illustrative assets do not establish controller performance.
Large assets require a suitable storage plan rather than silently omitting them
or committing build caches. Preserve upstream model attribution and licenses.

The user also requests several videos of the arm completing its task, favoring
successful, accurate and smooth runs for presentation. Select a few verified
successful cases using declared criteria, render actual recorded motion or
capture actual execution, and back up small MP4s, thumbnails and provenance in
videos/. Label replay, method, seed, playback speed and acceptance scope. Keep
all failures in the research evidence and disclose showcase selection; curated
clips do not establish a research ranking. Add accepted Phase 5 task videos when
successful complete trajectories become available.
