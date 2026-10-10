# GHCR CI bootstrap review — 2026-10-09 Toronto

Scope is CI infrastructure only. Phase5 NOT_ACCEPTED / Phase6 NOT_STARTED and
existing research files/failures remain untouched in the primary checkout.
Independent worktree/branch: `sp/ghcr-ci-infrastructure`.

Audited baseline: `51c7eb143ac66a34c188729608a51413a7f29f0c`, default branch
`master`, [run 38015143167](https://github.com/sp-zh/predictive-motion-research/actions/runs/38015143167).
All validation steps executed successfully, including installation and
`bash scripts/ci.sh`. Logs confirm 4 plant + 7 kinematics + 7 IK + 6 nullspace
GoogleTests, 8 Python statistics tests, no skipped tests; model hash checks,
2000-sample seed-42 numerical validation, ROS integration and installed consumer
checks ran. Colcon's 5/8/15 summaries include wrapper results, not additional
independent tests. This is an original-environment baseline, not GHCR evidence.

[Failure 37995122633](https://github.com/sp-zh/predictive-motion-research/actions/runs/37995122633)
at `7bfc4e8cf810c0b3027ec9424da0b18fc7210c64` failed in container initialization:
Docker Hub auth/manifest timeouts, unauthenticated pull rate limit, followed by
ContainerId-null error. Project compilation/tests did not run in that failure.
Recent successful master runs do not eliminate this supply failure mode.

Initial audit found only `ci.yml`, no open PR, only remote master, and no existing
migration workflow on master. A later historical check found closed, unmerged
[bootstrap PR #1](https://github.com/sp-zh/predictive-motion-research/pull/1),
checkpoint `ee0c708c7c915d3fc458fb152cce5be075d5eb53`; no closure explanation was
available in its comments. Its native XML/test inventory verifier was reused as
`scripts/ci/verify_test_results.py`, with current log paths and stricter statistics
skip rejection; no second active migration was found. Its earlier hosted green
runs are historical preparation evidence, not GHCR publication proof. GitHub auth permits repository/workflow operations but lacks
Packages scopes; listing Packages returns HTTP 403. Repository Secrets listing
was empty. No Docker runtime/copy tool is installed on this Mac. Existing package
names and visibility cannot be conclusively checked with this desktop token;
the trusted workflow checks ownership before publishing and fails closed on 403
or unlinked packages. No image was published and no registry digest invented.

Implementation: environment-only Dockerfile with explicit four-file staged context and allowlist;
existing apt setup retained including exact Pinocchio; fail-closed consistency
checker; trusted master dispatch stages; registry manifest/content and re-pull
checks; separate read-only full-test job; explicit empty-auth public validation;
allowlisted diagnostics and safe provenance collection; maintenance/runbook.
Daily CI retains its original base/install/full-test entry, name and job ID.
Workflow permissions, actions' verified full SHA, no mutable CI digest, unchanged
test scripts, no algorithm edits, and no automatic merge/visibility change were
reviewed in the complete diff.

Static/host-free checks: actionlint v1.7.12 (official release archive verified
against upstream checksums), Hadolint v2.15.1 (upstream checksum verified),
ShellCheck, Bash parse, Python source compile,
15 infrastructure tests, and whitespace/diff review. Tests include real subprocess
install/test nonzero exits and failed diagnostics, plus dependency-drift controls.
They do not establish a Linux Docker build, GHCR access or full new-image tests.

Deployment is **code prepared, waiting for bootstrap PR merge/registration**.
After manual merge, the workflow GITHUB_TOKEN can attempt publication without a
new PAT. A Package ownership/access or Docker Hub credential blocker must be
reported with its actual failed run. Public Package visibility needs separate
owner confirmation before anonymous verification and the second migration PR.
Current daily CI has not switched; no Stage A/B/public verification has occurred.
See [maintenance runbook](../docs/ci-environment.md) for exact acceptance gates.

Initial 2026-10-09 snapshot visual provenance (retained in Git at `9ea9269`): `figures/ci/ghcr-bootstrap-status.svg`/`.png` are a static
status chart from the two linked baseline Actions logs; five explicit observed
/pass/fail/pending rows, no simulated or inferred controller values. PNG is
1200×640; inspected for legibility. No physical units apply. SHA-256:

- `figures/ci/ghcr-bootstrap-status.svg`: `59a69f9ab8eb4ea74135c71f5823cbd9d39cfbedb30b2e41a11aea3468eca498`
- `figures/ci/ghcr-bootstrap-status.png`: `0d1c509984e13131943cff75ea43fccc05a90534f8b2e495afd7aaa8e3dad7fd`


Real preparation validation: [push 38016299622](https://github.com/sp-zh/predictive-motion-research/actions/runs/38016299622)
at `2c647666f4e47639716e1694484c13909faec7cf` completed all original tests,
the 15 infrastructure cases and the native inventory audit; downloaded XML/logs
independently confirm 24 native tests, 8 statistics cases and zero skips. The
artifact confirms x86_64 Ubuntu 24.04.5 and the exact pinned Pinocchio version.
Its checkout-SHA diagnostic failed with Git dubious ownership even though the
workflow was green; that failure remains in the run artifact. The collector now
uses a safe.directory argument limited to this read command and the actual
workspace path, without global configuration or a wildcard trust exemption.
At that checkpoint this correction still required a new hosted run; see the follow-up below. The initial historical baseline
and all preparation runs remain original ROS/Docker Hub environment evidence,
not GHCR publication/migration proof.


Final implementation validation (original ROS environment):

- [push run 38016564467](https://github.com/sp-zh/predictive-motion-research/actions/runs/38016564467): actual checkout `5a2055e0a8191ef34398bc8d1e58fa5c425ec057`, attempt 1; all steps successful, 15 infrastructure cases + 24 native GoogleTests + 8 statistics tests, zero skips.
- [PR run 38016566562](https://github.com/sp-zh/predictive-motion-research/actions/runs/38016566562): actual checkout `6e32056c762c0d6e49b6c2a88ac4e14a9010f796`, attempt 1; all steps successful, 15 infrastructure cases + 24 native GoogleTests + 8 statistics tests, zero skips.

Downloaded both artifacts and independently reran the native XML/full-log audit.
The inventory enumeration order is filesystem-dependent; testcase identity sets
and counts match the generated report (order is not a test outcome). Both
checkout-SHA reads now succeed. Ubuntu 24.04/x86_64, exact Pinocchio, run/attempt,
image ref, numerical marker and original test/consumer execution were checked.
The PR's effective checkout is GitHub's synthetic merge commit, distinct from
source branch checkpoint `5a2055e0a8191ef34398bc8d1e58fa5c425ec057`.
PR artifact ID `11656058077`, 645876 bytes, GitHub archive SHA-256
`ca58dff8307864026ae44dd9e00752761395eac6f461522f59f5ed7a320de597`
(**artifact digest, not an image digest**), retained by Actions for 30 days.
Local inspection copies are under `/private/tmp/ros-ci-final-pr-artifact` and
`/private/tmp/ros-ci-final-push-artifact`; these temporary paths are not durable
experimental archives. The source, report and figure milestone are backed up on
the public repair branch; original Actions logs preserve the provenance failure.

No GHCR base/CI publication, anonymous pull, new-image full CI or default-branch
migration has occurred. [PR #2](https://github.com/sp-zh/predictive-motion-research/pull/2)
requires manual bootstrap merge/registration before those stages can run.
The final follow-up commit only records completed validation; executable CI
sources are identical to the tested `5a2055e` checkpoint. Research phase gates,
algorithms, thresholds and primary workspace remain outside this repair.


Skopeo source-reference repair — 2026-10-09 Toronto

Starting PR #2 head was rechecked as `ad045b2432dcb25d904b50e8e451b4fc25add898`;
no newer branch change or uncommitted work was present. The publisher now calls
one shared validated parser for the Dockerfile lock, normalized index and selected
platform reference; it preserves the original source record and the existing
index digest. Eight targeted regressions were added to the existing suite (23
cases total; the prior 15 remain unchanged). Static checks passed: Actionlint,
Hadolint, ShellCheck, Bash parse, Python syntax and diff whitespace.

Actual read-only test on Dell WSL Linux x86_64, Skopeo 1.13.3 from Ubuntu package
`1.13.3+ds1-2ubuntu0.24.04.3`, SHA-256
`d908a86538f6d4bc49ea9c7423e5fb279a5c8cfc1f9bc7bd505f8bfe25d29be3`.
The package was downloaded and extracted under `/tmp/pm-skopeo-readonly.q9J9QD`;
it was not installed into the host. Existing system libraries were used. An
explicit empty auth file isolated this test from registry login credentials.
The exact production parser and retained Dockerfile were transferred with matching
SHA-256 (`1ae382029518896ef96d3e30149f312cda924a06667fa836211bc9e7655d3dbe`
and `f656d0e83c32e2254c124959df9f788d4ff5d77d4e31f5bcd8dbe0ee53cf50c6`).
Each inspect was bounded by a 25-second command timeout and 35-second external
timeout, with one invocation per reference and no retry loop.

Command form: `skopeo --command-timeout 25s inspect --authfile <empty-auth.json>
--raw docker://<reference>` (read-only):

- Original `docker.io/library/ros:jazzy-ros-base-noble@sha256:066420e07f60aa18262f2479981def87ebcfcec42eefb0c0c57c4a46098348ca`: exit 1, exact “Docker references with both a tag and digest are currently not supported” parse error.
- Normalized `docker.io/library/ros@sha256:066420e07f60aa18262f2479981def87ebcfcec42eefb0c0c57c4a46098348ca`: exit 0, OCI index/schema 2 with four descriptors; raw bytes hash equals the unchanged index digest.
- Selected linux/amd64 `docker.io/library/ros@sha256:a5426de405f6f0a82b0f3def3bbd3bce2a71a91421fe980c17613b4e51ef38d9`: exit 0, OCI manifest/schema 2, ten layers; raw bytes hash equals the selected digest. Config digest is `sha256:04b9d24bad695363d48418c1109d23e9738774b88a2017ec6d01ff9df4c3072c` (config identity, not a registry image reference).

This proves both reference parsing and registry reads for the actual locked
source. It does **not** prove copying or publishing: no `skopeo copy`, Docker
push, GHCR release or Package visibility operation ran. Raw stdout/stderr remain
in that isolated Dell temporary directory and inspection copies under
`/private/tmp/ros-skopeo-readonly-evidence` on Mac; these are diagnostic temporary
copies, not durable experimental archives. The small source/digest/results
record is retained here. PR merge remains paused; formal CI retains the original
container, dependency installation, algorithms, phase state and test entry.


Stage A deployment checkpoint — 2026-10-10 Toronto

The human explicitly authorized “授权合并 PR #2 并继续部署”. PR #2 head
`9ea92693b71007a93a6881400bcf8b1c118b5fc3` was merged normally to
`ff27808fea77a9742cd9363c17addfbf0d1f3ca2`; no history rewrite or branch-protection
bypass. Publication workflow registration was confirmed before dispatch.
[Stage A run 38026127189](https://github.com/sp-zh/predictive-motion-research/actions/runs/38026127189)
completed both publication and read-only validation jobs successfully.
Original source remains `docker.io/library/ros:jazzy-ros-base-noble@sha256:066420e07f60aa18262f2479981def87ebcfcec42eefb0c0c57c4a46098348ca`;
normalized index uses the same digest without a tag. Selected source and actual
GHCR target manifest both resolved to `sha256:a5426de405f6f0a82b0f3def3bbd3bce2a71a91421fe980c17613b4e51ef38d9`.
This equality was measured, not assumed. Target is
`ghcr.io/sp-zh/predictive-motion-research-ros-base@sha256:a5426de405f6f0a82b0f3def3bbd3bce2a71a91421fe980c17613b4e51ef38d9`,
linux/amd64 only, with source config and all ten layer descriptors matching.
The job re-pulled the target digest and checked architecture, Ubuntu and ROS.

Downloaded and independently audited native XML/full logs from Stage A and
[original-container run 38026123434](https://github.com/sp-zh/predictive-motion-research/actions/runs/38026123434).
Both checkout the same `ff27808` commit, execute 24 identical native GoogleTest
cases plus eight statistics cases, zero skips, and retain numerical/consumer
markers. Selected tool/library version command outputs are identical. This is
an environment-supply comparison, not a controller-performance claim.
Stage A still installed the unchanged setup script and exact Pinocchio version.
Release and validation artifacts are under `/private/tmp/ros-ghcr-stage-a-release`
and `/private/tmp/ros-ghcr-stage-a-validation` for local inspection; Actions retains
its named artifacts for 30 days. Small immutable references/results are retained
here; temporary directories are not claimed as durable experimental backups.

Stage B was dispatched at the same commit using that successful run's artifact.
Its publisher checks confirmed the base Package belongs to this repository. The
candidate was built from the explicit four-file context, pushed and re-pulled as
`ghcr.io/sp-zh/predictive-motion-research-ci@sha256:16bacb7ed79dde48cd3c60766ab04982a4096fdcfe780a492636ff5c1ed2cff6`.
[Run 38026435088](https://github.com/sp-zh/predictive-motion-research/actions/runs/38026435088)
has not yet completed full validation at this checkpoint. Its actual Package
page shows Public and links this repository; no visibility setting was changed
by the agent. Anonymous pull is still unverified. Daily CI remains unchanged.

Stage A status visual: 1200×640, inspected; source is the run IDs and result
records above. Infrastructure scope only, no physical model units. SHA-256:

- `figures/ci/ghcr-bootstrap-status.svg`: `5a704657a68fbbad5a7feab06c97f63b1c37859635f90b51e4013d483f39d6e9`
- `figures/ci/ghcr-bootstrap-status.png`: `9566b6c1cfe3717d30acdb529ee40f18aba00e89352c03329632c7d2fbeb1b82`


Stage B and public verification checkpoint — 2026-10-10 Toronto

[Stage B 38026435088](https://github.com/sp-zh/predictive-motion-research/actions/runs/38026435088)
completed publication, digest re-pull and the separate read-only full-test job.
The actual CI manifest is `ghcr.io/sp-zh/predictive-motion-research-ci@sha256:16bacb7ed79dde48cd3c60766ab04982a4096fdcfe780a492636ff5c1ed2cff6`.
It has its own registry identity, distinct from base/config IDs. Downloaded its
metadata, inventory and native XML/logs: all four environment definition hashes
match repository bytes; Ubuntu 24.04/Jazzy/x86_64 and exact Pinocchio match;
24 native + eight statistics tests, zero skips, numerical/consumer markers pass.
Image source commit is `ff27808`; definition hash is `96be9686a81ab6cffd8fbdbb5f168fc54078e8d9fcb31b433bb0e9650bd1bda8`;
full package inventory hash is `5135f97de49e98f6596635bac45bb81198e1fe19407f592efc9c2d27bb3950b0`.
The context contained only four declared definition files, no source checkout,
.git, private data, model/cache, build/install/log or credential files. Runtime
absence checks at the image workspace root passed. No old project binaries or
old test outcomes were embedded; tests compiled the checked-out source anew.

Actual Package pages show Public and project ownership for both names; no
visibility setting was changed by the agent. [Public verification 38026788308](https://github.com/sp-zh/predictive-motion-research/actions/runs/38026788308)
used a fresh GitHub-hosted Linux runner with a new empty Docker auth directory,
no login, and successfully pulled the exact CI digest and ran the same full tests
at `ff27808`. Its publishing job was intentionally skipped by operation;
all required validation/test steps executed. Artifact XML/full logs were
independently audited, with 24 native/eight statistics cases and zero skips.

Additional isolated Linux negative controls: anonymous Skopeo read of the real
public CI manifest returned the exact digest; a loopback private-manifest fixture
served the same bytes but returned authentication-required/exit 1 with empty auth,
and returned the valid bytes with ephemeral fixture auth. The loopback fixture
and ephemeral auth were stopped/deleted; no real Package visibility or access was
changed. This tests controlled private registry access, not a claim about an
unprovided private GHCR package. The real checker against the published image's
metadata rejected a changed definition with exit 1 before tests. Existing real
subprocess negatives retain nonzero test/install exits even if diagnostics fail.
The first negative collector expected only “unauthorized”, while Skopeo correctly
returned “authentication required”; its assertion failure is retained at
`/private/tmp/ros-ghcr-negative-control.log`. The corrected collector passed at
`/private/tmp/ros-ghcr-negative-control-v2.log`; no image or production source
changed for that collector repair. Loopback HTTP/TLS override applied only to
that isolated fixture; all real registry reads used normal TLS verification.

Verified direct-human authorization to merge the final migration after passing
checks was read from the userMessage in chat `01a122f5-a5da-7461-850e-7af06b79ce33`,
turn `01a1243a-d86d-7fa0-8185-add59dc7730e`: “等新环境的全部测试通过后，再合并这第二个 PR，并核对 master 的运行结果。”
That chat is independently reviewing only, with this chat the sole implementer.
The migration changes only the two static CI image refs and replaces repeated
apt setup with the fail-closed definition/package checker. It retains workflow
name, validation ID, push/PR scope, read-only permissions and all original tests.
Default-branch migration remains pending until the final PR and master run pass.

Verified-image/migration-pending visual checkpoint: same 1200×640 dimensions and
infrastructure-only scope; newly rendered PNG inspected. SHA-256:

- `figures/ci/ghcr-bootstrap-status.svg`: `6e98372cbf98c2c832ff0f18a54d1353fbeb351dbbe96ddff06eaf34566520b1`
- `figures/ci/ghcr-bootstrap-status.png`: `740c91ffe1fc1350ea6f60fef698198b46b2cce05f8ec04b0c099b45c418a26c`
