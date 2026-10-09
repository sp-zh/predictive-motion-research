# CI environment maintenance

## Deployment status (2026-10-09)

This is the **bootstrap preparation**, not a completed GHCR migration. Daily CI
still uses `ros:jazzy-ros-base-noble@sha256:066420e07f60aa18262f2479981def87ebcfcec42eefb0c0c57c4a46098348ca`.
No project GHCR image has been published or accepted by this change. There is
no final dependency-image digest to put in `ci.yml` yet. Research phase gates,
algorithms, numerical tolerances and `scripts/ci.sh` are unchanged.

The static `jobs.validation.container.image` in `.github/workflows/ci.yml` is
the single authority for daily CI; environment recording reads that reference.
`docker/ros-base-source.txt` records the upstream source for mirroring, not a
second daily CI lock. Its pinned digest is an upstream multiarchitecture index;
our mirror resolves and copies only its Linux amd64 manifest. The upstream
registry was checked on 2026-10-09: that manifest is
`sha256:a5426de405f6f0a82b0f3def3bbd3bce2a71a91421fe980c17613b4e51ef38d9`
(this is a source digest, not a published GHCR digest). It does not
promise arm64 support. The existing development Dockerfile and devcontainer
retain their original purpose.

## First deployment

1. Review and merge the bootstrap PR using normal human approval and branch
   protection. `workflow_dispatch` requires the workflow on the default branch;
   a new branch alone is not a runnable dispatch registration. Do not merge the
   later digest-switch PR until the images and full tests have been verified.
2. In the owner's [Packages page](https://github.com/sp-zh?tab=packages), verify
   `predictive-motion-research-ros-base` and `predictive-motion-research-ci`
   are unused, or are linked to this repository and owned by this project.
   Do not reuse a name of unknown origin. Dispatch requires this attestation;
   the API also refuses existing packages linked elsewhere or API errors other
   than 404. A 404 alone cannot establish absence of an inaccessible package.
3. On `master`, the repository owner reviews the exact SHA, then runs **Publish and validate CI environment**, stage `base`:

   ```bash
   gh workflow run publish-ci-images.yml --ref master \
     -f stage=base -F package_names_confirmed=true \
     -f reviewed_sha="${REVIEWED_SHA:?set the full reviewed source commit}"
   ```

   This authenticates GHCR with the job's `GITHUB_TOKEN` on the host runner,
   resolves the locked ROS index, copies its amd64 manifest with skopeo,
   compares source/target manifest bytes (config and layer references), resolves
   the target registry digest, and pulls by digest. Failure to obtain the Hub
   source stops the run without an anonymous retry loop. If the actual error
   requires Hub authentication, an owner sets **both** `DOCKERHUB_USERNAME` and
   a read-only `DOCKERHUB_TOKEN` under Repository Settings → Secrets and
   variables → Actions. Never put credentials in chat, Git, build args or logs.
   Existing GHCR bases do not require Docker Hub credentials for stage B.
4. Newly published GHCR packages initially default to **private**. Do not
   infer visibility from this public repository. After explicit owner approval,
   an owner uses Package settings → Change visibility → Public for each new
   dependency-only package. Also check its connected repository / Actions
   access is this repository. The workflow never changes these settings.
   Until public access is enabled, authenticated tests can run, but the final
   anonymous-pull gate must fail and the image is not eligible for daily CI.
   Re-run all jobs after the setting changes; each attempt gets a unique tag.
5. Inspect the successful base run's summary and artifact
   `ci-image-validation-RUN_ID-ATTEMPT`: `validation.json`, full logs,
   `test-inventory.json` and environment evidence. It must show complete tests
   and an anonymous pull. Copy its actual GHCR manifest reference into
   `BASE_REF` and its run ID into `BASE_RUN` locally (neither is a secret):

   ```bash
   : "${BASE_REF:?set the verified base manifest reference}"
   : "${BASE_RUN:?set the successful base run ID}"
   gh workflow run publish-ci-images.yml --ref master \
     -f stage=ci -F package_names_confirmed=true \
     -f base_ref="$BASE_REF" -f base_run="$BASE_RUN" \
     -f reviewed_sha="${REVIEWED_SHA:?set the full reviewed source commit}"
   ```

   Stage B checks the base run's successful conclusion, workflow, `master`
   branch, **same source commit**, digest, complete tests and anonymous access.
   If the selected ref changed, revalidate stage A at the new commit first. It builds
   with the built-in Docker builder (no separate builder image), publishes a
   uniquely tagged dependency image, resolves its registry manifest digest and
   pulls it. No project sources, build results, models or credentials enter
   its dedicated allowlist context. Stage B's fresh Linux runner pulls from
   GHCR and runs `scripts/ci.sh` without apt installation. Its test job has
   read permissions only; publishing credentials never enter the container.
   For a newly created CI package, apply the same explicit visibility approval
   and retry procedure in step 4.
6. Review both stages' actual logs and artifacts, not just green conclusions.
   Stage A uses the original setup script and full test entrypoint; stage B
   uses exactly the same checkout/entrypoint with preinstalled dependencies.
   Both must run model checksum validation, compilation, 24 native GTest
   cases, 8 statistics tests, ROS bridge integration, Pinocchio probe,
   plant/kinematics/control/nullspace consumers, installed-config smoke and
   numerical validation (2,000 samples, seed 42, h=1e-6). CTest/colcon wrapper
   counts are not additional cases. The inventory checker rejects missing,
   failed and skipped native cases. Future intentional test expansion requires
   an explicit reviewed inventory update; do not remove tests to satisfy it.
7. Create a **migration PR**. Only now set the existing `validation` container
   to `ghcr.io/sp-zh/predictive-motion-research-ci@sha256:` followed by the
   verified dependency-image registry digest. Replace only the redundant
   dependency-install step with `python3 scripts/ci/check_environment.py`.
   Preserve the workflow name, job ID, push/PR coverage, Bash, all original
   test commands and diagnostics. Keep ordinary workflow permissions read-only
   (`contents: read` suffices for the required public image).
   Record the actual base/CI references, build-source commit, successful run
   links and prior accepted digest in this document before opening the PR.
8. Run full CI on the migration PR on fresh GitHub-hosted Linux runners, inspect
   the artifacts for the full inventory and no skips, and verify job container
   initialization uses GHCR and daily apt installation is absent. Human-review
   and merge the PR; inspect the resulting **default-branch** full run. Only
   then report the long-term migration as deployed and verified.

## Environment changes and rollback

Rebuild when any of these definitions changes:

- `scripts/phase0/setup_linux.sh` (the sole apt package list and exact pins);
- `docker/Dockerfile.ci`, `docker/Dockerfile.ci.dockerignore`;
- `docker/ros-base-source.txt`;
- `scripts/ci/check_environment.py` (record/check semantics).

The image stores each definition's SHA-256, base manifest, build-source commit,
platform and full installed package inventory under
`/usr/local/share/predictive-motion-ci/environment.json`. It checks current
required package versions, exact pins and definition hashes. An algorithm or
documentation commit does not require the image build commit to equal HEAD.
The final CI digest is not an environment-hash input, so switching it does not
create a circular rebuild. Source labels also record repository, revision,
base reference and target platform. Candidate publication tags include source
SHA, run ID and attempt; daily CI must never follow tags automatically.

Ordinary pushes/PRs only test. Only the repository owner can publish manually,
only from this repository's `master` or the fixed maintenance branch
`sp/ci-environment-candidate`. Dispatch must supply the full **reviewed** commit
SHA, which must equal the selected ref; do not blindly attest to an unreviewed
moving HEAD. `packages: write` exists only on the publishing job. No fork PR or
`pull_request_target` gets publishing capability.

For later dependency changes, create `sp/ci-environment-candidate` from current
master and open an environment-update PR. Review the definitions and exact
commit first. After the workflow is registered on master, the owner dispatches
A then B on that candidate ref with its reviewed SHA (substitute that ref in the
commands above). Both runs must bind the same branch, commit and base digest.
The old daily image's drift gate should be red until the owner validates the
candidate, then adds its real digest to **the same PR**. The digest switch is
not hashed as an environment definition, so the completed PR can run full CI
green before protected-branch merging, without bypassing required checks.
Revalidate A/B if environment definitions or tested code changed after review;
only a workflow digest/validation-documentation update can use the already
verified candidate. Initial bootstrap remains the two-PR process above.
Do not relax the exact Pinocchio version if apt stops carrying it: retain the
build failure and report the package/version and log before changing policy.

Keep the current and at least one previously validated GHCR digest with
retained tags and a short validation record in Git. Do not delete packages or
old accepted images without owner approval. To roll back, PR the previous
verified dependency digest **and its matching environment definitions** from
Git history; retain all test commands and rerun full CI. A digest alone is not
a valid rollback across incompatible definition changes. There is no automatic
Docker Hub fallback. Before the first accepted GHCR version, the original
upstream digest above is the bootstrap recovery reference, with its known Hub
availability limitation; do not describe it as a previously accepted GHCR image.

Review upstream security advisories and dependency availability during planned
maintenance (suggested monthly), using the same controlled publish/verify/PR
process. This document does not schedule an automatic update. A fixed digest
freezes the supplied image; it does not guarantee byte-for-byte rebuilds from
mutable apt repositories or absolute determinism of all numerical results.

## Diagnostics and remaining network use

The checkout step gates environment collection/upload, so a failed container
initialization does not trigger container-dependent diagnostic steps with an
empty ContainerId. Its primary runner log remains the startup evidence; no
in-container script can fix startup before the container exists. After checkout,
failures still retain explicitly selected build/test logs, native XML,
numerical reports and environment metadata (30-day Actions artifacts). Keep
small accepted references/results in Git before artifact expiry. The environment
record includes actual checkout commit, run ID/attempt, static CI reference,
OS/ROS/CPU and selected tool/package versions; it never dumps all environment
variables or uploads the entire workspace.

Daily CI still downloads MuJoCo 3.3.7 (archive SHA-256 checked), pinned MuJoCo
Menagerie `4d038b3feae26ec82b46a4d586379114012a8ac7` and pinned Franka Description
`7aeeddc449edf8d62b594f9e36a81da53e7796f9` from GitHub; model manifests are checked.
Actions checkout and artifact services also use the network. Mirror publication
uses Docker Hub and host apt; dependency-image builds use Ubuntu/ROS apt.
Removing the daily Docker Hub ROS job-container pull and repeated system apt
installation does not make the full CI offline.

Private GHCR is not the selected daily design: public/fork PRs need anonymous
access. If that policy changes, a separate review must cover package/repository
access, `packages: read`, startup `container.credentials`, and fork behavior.
A later in-container login cannot fix private job-container initialization.

New Action: official `actions/upload-artifact` v4.6.2, verified release and
commit `ea165f8d65b6e75b540449e92b4886f43607fa02`; all Action references are full
commit SHAs. Existing checkout SHA is preserved.

References: [manual workflow registration](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow),
[GHCR authentication/initial visibility](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry),
[package visibility/access](https://docs.github.com/en/packages/learn-github-packages/configuring-a-packages-access-control-and-visibility).

## Bootstrap verification record

Audited repository baseline: commit
`89d12a2027060e6b1a396576b037456feed4c391`, successful full
[run 38003737981](https://github.com/sp-zh/predictive-motion-research/actions/runs/38003737981).
Command: `bash scripts/phase0/setup_linux.sh`, then `bash scripts/ci.sh`.
Its logs show Plant 4, Kinematics 7, Ik 7, Nullspace 6 native cases;
8 statistics tests; zero native skips; the numerical and both control-consumer
pass markers. Earlier full successful run 38003101921 was also inspected.
The startup-failure [run 37995122633](https://github.com/sp-zh/predictive-motion-research/actions/runs/37995122633)
shows Hub token timeout, `toomanyrequests`, no compilation/testing, and the
secondary empty `ContainerId` error. These retained failures justify this change.
The baseline log retrieved with `gh run view 38003737981 --log` had SHA-256
`fa0c0a72e0c2e615c8e7bd5c7376d4b45c8543d84e68d68343a49d044bb0e378`;
the authoritative original remains in Actions.

Local preparation checks: Actionlint v1.7.12, ShellCheck, Hadolint v2.15.1,
Python syntax checks, 11 infrastructure fixture/negative tests and all 8
original statistics tests passed. The fixture tests are not ROS/container
acceptance. Tool binaries were downloaded from their official releases into
a temporary directory and checked against the GitHub release asset hashes;
no tool caches or binaries are committed. The upstream ROS index's raw bytes
were SHA-256 checked against the locked digest before reading its platform list.

Authentication inspection was limited to status, scope names and secret names;
no secret values were read/exported. The existing CLI OAuth lacks
`read:packages`/`write:packages`; package listing returned HTTP 403. Anonymous
registry checks for both proposed names also returned 403, which cannot
establish absence versus private visibility. No existing package was overwritten.
No Docker daemon/tools are installed on this Mac, so no local image build,
GHCR publication, private-image access test or GHCR full run is claimed.
These remain bootstrap deployment gates; the workflow uses `GITHUB_TOKEN`
instead of asking for a broad PAT.
