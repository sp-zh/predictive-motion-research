# Project backup

Private GitHub repository: https://github.com/sp-zh/predictive-motion-research

This repository backs up source, tests, configuration, model descriptions,
documentation, review reports, figures and small CAD artifacts. A Git push is
required to back up later local changes; this is not an automatic schedule.

Raw experimental evidence under `results/`, transfer archives under `transfer/`,
generated simulation assets, build outputs, dependency caches and SSH credentials
are excluded. Existing evidence and retained failures remain in their local
Mac/Dell locations with their original hashes. This Git repository alone cannot
restore the complete experimental dataset. Review links into excluded evidence
require those local archives.

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
