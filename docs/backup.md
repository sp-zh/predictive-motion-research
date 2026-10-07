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

To save subsequent reviewed source changes, inspect `git status` and the diff,
commit the intended files, then run `git push origin HEAD`.
