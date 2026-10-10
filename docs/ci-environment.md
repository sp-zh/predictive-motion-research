# CI environment maintenance

Status, 2026-10-10 (America/Toronto): **deployed and verified on master**.
[Migration PR #3](https://github.com/sp-zh/predictive-motion-research/pull/3)
passed complete push/PR checks and was merged, with verified direct-human
conditional authorization, as `26ed25bf7ed97c0e73bda97f8577e976544795e8`.
[Master run 38027887735](https://github.com/sp-zh/predictive-motion-research/actions/runs/38027887735)
passed all required steps: GHCR job-container initialization, image consistency,
23 infrastructure controls, original 24 native GoogleTests + eight statistics
cases (zero skips), numerical/consumer checks and diagnostics. The old apt
installation step is absent. SDK/model downloads still use the network.

PR #2 was merged with direct human authorization at `ff27808fea77a9742cd9363c17addfbf0d1f3ca2`.
No algorithms, thresholds, research gates or original test entry points changed.

Current verified CI environment (`linux/amd64` manifest):
`ghcr.io/sp-zh/predictive-motion-research-ci@sha256:16bacb7ed79dde48cd3c60766ab04982a4096fdcfe780a492636ff5c1ed2cff6`.
Build source: `ff27808fea77a9742cd9363c17addfbf0d1f3ca2`; definition SHA-256:
`96be9686a81ab6cffd8fbdbb5f168fc54078e8d9fcb31b433bb0e9650bd1bda8`;
complete installed-package inventory SHA-256:
`5135f97de49e98f6596635bac45bb81198e1fe19407f592efc9c2d27bb3950b0`.
Inventory remains inside the retained image, retrievable with
`docker run --rm --entrypoint cat <verified-CI-ref> /usr/local/share/predictive-motion-ci/installed-packages.tsv`.

Verified GHCR ROS base (`linux/amd64` manifest):
`ghcr.io/sp-zh/predictive-motion-research-ros-base@sha256:a5426de405f6f0a82b0f3def3bbd3bce2a71a91421fe980c17613b4e51ef38d9`.
[Stage A 38026127189](https://github.com/sp-zh/predictive-motion-research/actions/runs/38026127189),
[Stage B 38026435088](https://github.com/sp-zh/predictive-motion-research/actions/runs/38026435088),
and [anonymous full CI 38026788308](https://github.com/sp-zh/predictive-motion-research/actions/runs/38026788308)
all passed at the same source commit. Each full-test job ran the original
24 native GoogleTests, eight statistics tests and numerical/consumer checks,
without test skips. Both actual Package pages show Public and this repository;
the agent did not change their visibility. Daily CI needs no registry secret.

## Current source and future release order

The pre-migration daily CI and retained development `docker/Dockerfile` use
`docker.io/library/ros:jazzy-ros-base-noble@sha256:066420e07f60aa18262f2479981def87ebcfcec42eefb0c0c57c4a46098348ca`.
This is the official multi-platform **index**, not a config ID. Linux CI targets
`linux/amd64`. The publisher retains the original tag+digest source in
`base-copy.json` as `source_original`; `source_index` is the normalized tag-free
`docker.io/library/ros@sha256:…`, and `source_platform_manifest` uses the same
repository with the amd64 digest selected from that index. `target_manifest`
is the independent GHCR result. Skopeo rejects Docker transport references that
contain both tag and digest; `scripts/ci/ros_source_reference.py` validates the
allowed repository/tag and full digest and constructs the transport references.
 The verified base and published CI candidate are recorded above; the candidate remains gated on validation.

1. Bootstrap PR #2 is already merged and the dispatch workflow is registered.
   Future environment candidates use the trusted master workflow below.
   Workflow execution never auto-merges a digest change or changes visibility.
2. Run `Publish and validate CI environment` on `master`, operation `copy-base`.
   It resolves the index's amd64 manifest, copies that platform to
   `ghcr.io/sp-zh/predictive-motion-research-ros-base`, compares source/target
   config and layer descriptors, obtains the target registry manifest digest,
   re-pulls by digest, checks Ubuntu/ROS/architecture, and executes the unchanged
   dependency installation and **full** `bash scripts/ci.sh` on a separate fresh
   GitHub-hosted runner. Inspect both jobs and their artifacts, not just the
   publication step. Retain `base-copy.json` and the full validation log.
3. At that same code commit, run `build-ci`, supplying `base_image` from the
   verified Stage A summary and its successful `base_validation_run` ID. The
   workflow checks the completed run's commit, workflow/event and release
   artifact's exact digest before building. If master has advanced, perform a
   new Stage A run; do not bypass the check. The build uses that GHCR digest,
   the existing setup script, and the Docker engine's installed BuildKit; it
   does not start an additional Docker Hub builder image. The candidate goes
   to `ghcr.io/sp-zh/predictive-motion-research-ci`, is re-pulled by its **own**
   digest, then checked and fully tested on another fresh runner without apt
   installation. No current project binaries or test results enter the image.
4. An owner must confirm package ownership, repository linkage and intended
   visibility. New GHCR packages default to private. This implementation never
   changes visibility. For public PR compatibility, after approval use the
   package Settings → Danger Zone → Change visibility → Public for the CI
   dependency package. Making the base public is optional if its Actions access
   permits future builds. Existing unlinked/foreign packages stop publication;
   review their provenance before granting this repository Actions access.
5. Run `verify-public-ci` with the exact CI digest. This uses **no registry
   login**, an isolated empty Docker auth directory and a fresh hosted runner,
   then executes the full tests again. An inaccessible/private candidate must
   fail at pull. This is the required public/fork-PR compatibility evidence.
6. Only after those runs succeed, open a migration PR: replace both the static
   `validation.container.image` and diagnostic `CI_IMAGE_REFERENCE` in `ci.yml`
   with the verified `ghcr.io/sp-zh/predictive-motion-research-ci@sha256:…`.
   The reference-agreement test prevents the two fields drifting. Replace the
   dependency-install step with `python3 scripts/check_ci_environment.py check`.
   Keep the workflow name, `validation` job ID, push/PR triggers, Bash shells,
   original full test command and diagnostics. Do not add registry write
   permission or a silent Docker Hub fallback to daily CI.
7. Inspect migration PR push/PR logs on hosted Linux runners, merge only with
   explicit owner authorization and passed checks, then inspect the new
   default-branch full CI run. The initial migration passed these gates in PR #3
   and master run 38027887735. Record current and predecessor verified refs here.

Dispatch example after registration:

```sh
gh workflow run publish-ci-images.yml --repo sp-zh/predictive-motion-research --ref master -f operation=copy-base
# Use real values from the successful Stage A run:
gh workflow run publish-ci-images.yml --repo sp-zh/predictive-motion-research --ref master -f operation=build-ci -f base_image="$VERIFIED_BASE_REF" -f base_validation_run="$VERIFIED_BASE_RUN"
gh workflow run publish-ci-images.yml --repo sp-zh/predictive-motion-research --ref master -f operation=verify-public-ci -f candidate_image="$VERIFIED_CI_REF"
```

## Credentials and release boundaries

Only explicit dispatches from this repository's `master` can publish. Ordinary
pushes and PRs do not rebuild images. Only the publishing job has `packages:
write`; validation has `contents: read` and `packages: read`, and no publishing
credential is passed to the project test container. The repository workflow's
`GITHUB_TOKEN` is used rather than a broad PAT. Checkout does not persist its
credential into the mounted source. Candidate tags use source SHA, run ID and
attempt, and existing release tags are refused rather than overwritten.

First source retrieval may still encounter Docker Hub limits. Existing safe
credentials can be supplied as repository Actions Secrets `DOCKERHUB_USERNAME`
and `DOCKERHUB_TOKEN` (Settings → Secrets and variables → Actions). Use a read-only
Docker Hub token. Do this only if source retrieval is blocked or authentication
is desired; never paste credentials into chat. Both must be set together.
There is no indefinite anonymous retry loop. A usable GHCR base avoids Docker
Hub for `build-ci` and daily CI after migration. Package API 403 is an error,
not proof that a name is free. Existing names must be linked to this repository.
The first workflow run will make the authoritative ownership/permission check;
the current desktop token cannot list Packages (HTTP 403, missing read:packages).

A private daily image would require startup-time `container.credentials` and
`packages: read` plus explicit package access for the repository. Such a setup
has not been implemented or accepted for forks. Keep daily CI unchanged until
anonymous pull is proven; do not skip fork tests or expose secrets to fork code.

## Definition consistency and candidate review

Rebuild when these environment definitions change:

- `scripts/phase0/setup_linux.sh` (the sole apt dependency list);
- `scripts/check_ci_environment.py`;
- `docker/Dockerfile.ci`;
- `docker/Dockerfile.ci.dockerignore`.

The checker compares their byte hashes, Ubuntu 24.04, Linux x86_64, ROS Jazzy,
exact `ros-jazzy-pinocchio=4.1.0-1noble.20260826.071113`, and the full installed
package inventory recorded in the image. Metadata and inventory live under
`/usr/local/share/predictive-motion-ci/`; OCI labels include source/revision,
base, platform, setup hash and combined definition hash. The definitions alone
are hashed, never current HEAD or the final image digest. An ordinary source or
documentation change does not require an image rebuild. The publisher stages an explicit four-file temporary build context. Its
Dockerfile-specific allowlist also excludes the entire workspace except those four files and leaves the
existing development `.dockerignore`/devcontainer untouched. Audit the build
context and labels/inventory on every release. Dependency installation errors
abort the build, including an unavailable pinned apt version; do not substitute
another Pinocchio version without a separately reviewed environment change.

Stage A copies an amd64 manifest from the official ROS index. Source/target
registry digests are recorded independently; config/layers are compared for
content correspondence. Stage B's digest comes from its push and is resolved
again remotely. Neither a local image ID nor a base digest is a CI image digest.
Only amd64 is promised. The baseline uses ROS/Ubuntu upstream dependencies; keep
upstream license notices and consult package redistribution terms when changing
the dependency list. The copier preserves official base contents unchanged.

Release artifacts expire after 30 days. Before accepting a digest, retain a
small reviewed release/validation record under `reviews/` with the real image
refs, source commit, run IDs, test inventory and links; retain necessary logs
externally if larger. Do not treat an expired artifact or a green badge as
proof. Review the per-suite XML/logs: 4 plant, 7 kinematics, 7 IK, 6 nullspace
GoogleTests, plus 8 Python statistics tests at the audited baseline. CTest and
colcon summaries wrap those tests and must not be counted again. Also inspect
model hashes, numerical validation (2000 samples, seed 42), ROS integration and
installed plant/kinematics/control/nullspace consumer execution. Confirm zero
test skips (compiler detection's “skipped” is not a skipped test). Tests and
thresholds remain defined by the existing scripts; do not turn these baseline
counts into permission to drop new tests. Compare Stage A/B at the same source
commit. Historical baseline comparisons across commits have limited scope.

Local bootstrap checks:

```sh
actionlint .github/workflows/ci.yml .github/workflows/publish-ci-images.yml
shellcheck scripts/publish_ci_images.sh scripts/run_ci_image.sh
bash -n scripts/publish_ci_images.sh scripts/run_ci_image.sh
python3 tests/ci/test_environment_check.py
```

Host-free negative controls cover definition/package drift, mutable refs, wrong
metadata architecture, missing records, install/test failures and diagnostic
failure propagation. A real denied anonymous pull and target-platform Docker
build/pull/full test still require the registered workflow; local mocks do not
prove registry permissions or runtime compatibility. Container initialization
failures remain visible in Actions' startup log. Checkout-success conditions
avoid attempting workspace diagnostics without a checkout; in-container scripts
cannot rescue a container that was never created.

## Updating and rolling back

Ordinary commits run tests only. For environment updates, review the diff,
perform the staged dispatches, inspect full results, then propose a PR updating
the two CI refs and removing/replacing installation only when appropriate.
Record the previous verified GHCR digest before replacement. Roll back via a
reviewed PR restoring both refs to that prior compatible digest; if definitions
also changed, restore the corresponding environment definitions in the same PR
so the checker can pass. Do not silently revert to Docker Hub. For this first dependency-image release there is no earlier preinstalled CI
image to invent. Retain the verified Stage A GHCR base as the bootstrap recovery
image: a rollback PR can use its exact `a5426de…f38d9` reference in both CI fields
and replace the consistency step with the unchanged setup script, as fully tested
in Stage A. This explicit recovery still uses GHCR, but temporarily restores apt
installation and its network requirements. For subsequent dependency releases,
keep the current `16bacb7e…2cff6` image as the previous fully verified environment
and restore its matching definitions and both refs through a rollback PR.
Keep both current CI and Stage A base release tags; do not delete either without
owner approval. The complete references above are the authority; short hashes in
this paragraph are labels only.

Retain current and at least one previous verified image/tag; never delete them
without owner confirmation. Review security updates on a controlled schedule
(e.g. monthly and on upstream advisories), keeping exact dependency changes
explicit and revalidating. A pinned digest fixes image identity; it does not
guarantee bit-for-bit future apt rebuilds or absolute numerical determinism.

Remaining network requests after migration: checkout; MuJoCo 3.3.7 release
archive; the locked MuJoCo Menagerie commit; the locked Franka description commit
and ROS model generation. Publication also uses apt repositories and, for the
initial mirror only, Docker Hub. CI is not offline. Environment collection only
records selected provenance and tools; artifacts allowlist logs, XML/numerical
reports and metadata, never the workspace, credentials or entire environment.

References: [dispatch registration](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow),
[GHCR authentication/visibility](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry),
[Dockerfile-specific context rules](https://docs.docker.com/build/concepts/context/),
[verified official upload-artifact v7.0.2 release](https://github.com/actions/upload-artifact/releases/tag/v7.0.2)
(commit `cf430e030ddbb5b0abf93d22962f4752f3646cd9`, resolved through GitHub API).
