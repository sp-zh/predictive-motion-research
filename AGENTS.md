# Project resumed by the user

The user explicitly resumed this project on 2026-10-06: “可以继续项目”. The prior Phase4 pause is lifted. Continue Phase5 and subsequent authorized project work, while preserving all accepted Phase4 evidence and retained failures. Phase5 remains unaccepted until its independent root gate. PROJECT_PAUSED.json records the resumed state; reviews/evidence/project_pause_20261005.json preserves the earlier pause.

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
