# Reproducibility workflow

Phases 0–3 have passed their component reviews, including the corrected Phase 2 post-step observation contract. Phase 4 is in progress. Predictive-controller research benchmarks have not yet run; the commands below reproduce the completed components, not the final research experiment.

## Platform

Ubuntu 24.04 x86_64 with ROS 2 Jazzy, GCC 13, CMake 3.28, Eigen 3.4 and Pinocchio 4.1.0 from ROS binary packages. The tested Dell host uses WSL2, not a hard real-time kernel. Mac stores source and transfers data but is not the reference Linux runtime.

Run from a writable directory on a native Linux filesystem. Do not build under /mnt/d. `setup_linux.sh` is a privileged dependency installer; the dedicated SSH transfer account deliberately has no sudo, so installation is done through the Dell execution environment/administrator.

```bash
# With ROS Jazzy already installed from the official repository:
sudo bash scripts/phase0/setup_linux.sh
# Then as the ordinary workspace owner:
bash scripts/phase0/fetch_vendor.sh
bash scripts/phase0/build_test.sh
```

`fetch_vendor.sh` locks MuJoCo 3.3.7 by archive SHA-256 and Menagerie by full Git commit, then checks the FR3 file manifest. It does not use a changing main branch as the model version. `PM_CACHE` may point to a larger disk for archives, while extracted libraries remain in the Linux checkout. Download/checksum errors fail the setup.

The ROS binary repository is external and may remove old package revisions. Exact Pinocchio package version installation fails rather than silently upgrading; long-term dependency archival remains a reproducibility risk. An uncached rootless Podman build of the source-only Phase 0–3 snapshot passed, with image identity, installed packages, 24 actual unit cases, ROS exchange, 2000-sample numerical validation and installed consumers retained in [the component environment review](../reviews/clean_component_environment_review.md). Hosted Actions now has successful pinned-container runs, including [38090687120](https://github.com/sp-zh/predictive-motion-research/actions/runs/38090687120); the editor devcontainer workflow and final research reproduction remain unverified. Hosted component CI is separate from Phase5 execution and research-result reproduction.

## Phase 0 execution and artifacts

The build/test script runs colcon build/test, reports C++ tests, executes a Pinocchio link probe and checks actual ROS state/reset integration. The simulation uses position-controlled actuators and model-defined arm joints. Tests use a declared FR3_MODEL path from the pinned asset root; users do not supply hidden model files.

Artifacts live under results/phase0, including build/test output, actual rendered model image and ROS exchange evidence when those tests complete. These are infrastructure test evidence, not comparative motion-control results.

Capture environment metadata after sourcing ROS:

```bash
source /opt/ros/jazzy/setup.bash
python3 scripts/collect_environment.py --output reviews/evidence/environment.json
```

A second checkout/fresh build directory must re-run the same workflow before Phase 0 PASS. Repeat reset tests with the same pinned binaries and seed; cross-platform bitwise identity is not promised.

## CI

The hosted [workflow](https://github.com/sp-zh/predictive-motion-research/actions/runs/38090687120) has run successfully in the pinned Linux dependency image. `scripts/ci.sh` calls Phase0, Phase1 model fetch/build/numerical validation, Phase2 control-package tests/installed consumers and paired-statistics tests. Its inventory verifier requires 24 native GTest cases and 8 statistics tests, with no skipped cases. It does not call the Phase5 standalone source, first-cycle model/QP diagnostic, full closed-loop controller, plant/main/scorer benchmarks or comparative research evaluation. [Phase5 CI migration](ci-phase5-coverage.md) is a separate reviewed path; a green current workflow is not Phase5 acceptance.

`bash scripts/ci.sh` builds and tests the simulation, kinematics and control packages, runs the Phase 1 numerical validation and exercises the installed control library. Phase 3 tests are part of that control package. Full development/evaluation diagnostics use the phase-specific commands in `scripts/phase2/README.md` and `scripts/phase3/README.md` and are separate from fast CI.

## Source snapshot and clean environment

Create a source-only archive on the authoritative checkout after review:

```bash
python3 scripts/export_source.py --output /tmp/predictive-motion-source-unique
cd /tmp/predictive-motion-source-unique
test -f READY
sha256sum -c source.tar.gz.sha256
tar -xzf source.tar.gz
cd predictive_motion
sha256sum -c SOURCE.sha256
```

The export uses the same allowlist as `source_manifest.py`, preserves executable permissions and excludes credentials, raw results, generated CAD and installed dependency caches. It refuses an existing output directory and publishes `READY` last. The archive includes all original source bytes plus an internal hash manifest; identical source bytes and executable modes produce the same archive. Export from the Dell checkout once its current source has passed review: the Mac checkout does not acquire in-progress Dell changes automatically.

With a working Linux container runtime, the source directory can run `docker build --platform=linux/amd64 -f docker/Dockerfile -t predictive-motion-audit .`. The recipe has a fixed ROS base digest; `.dockerignore` excludes transfer credentials and build/results caches. Neither the recipe nor a passing build alone closes ENV-003. The final reproducibility audit must use a clean dependency environment to launch simulation, execute at least one completed research benchmark, regenerate its metrics and regenerate a main result figure. It must record the source archive identity, installed package versions, commands, exit codes and resulting artifact hashes. Until those actions actually succeed, `reviews/reproducibility_audit.md` must not report PASS.

For a rootless Podman component build, run as the ordinary Linux workspace user:

```bash
python3 scripts/clean_component_audit.py \
  --bundle /tmp/predictive-motion-source-unique \
  --output /tmp/predictive-motion-container-audit-unique
```

The wrapper verifies the archive and source hashes before creating the build context, confirms the runtime is rootless, performs an uncached build and saves command logs, image identity, package inventory and the component results baked into the image. It removes its temporary container while retaining the image for inspection. The pinned recipe limits compiler parallelism to two jobs. A recorded run reached `COMPONENT_BUILD_PASS_FINAL_AUDIT_PENDING`. The current wrapper also collects GTest XML; that collection helper was executed on the successful image. The reviewed archive identifies the earlier wrapper version used for the complete build, distinct from the final research audit.

## Data transfer

Large archives and raw results are copied using tools/dell-sync.py with partial-file recovery and SHA-256 verification. Record the result manifest. Transfer setup and secret paths in COORDINATION.md are operator context, not prerequisites for other users building this project. The research build uses relative project paths and downloadable versioned assets.

Do not duplicate all raw logs into the Mac disk, which had only about 43 GiB free at initial inspection. Bring back source, manifests, reviews, metrics and selected verified visual evidence; keep large raw experiment bundles on the Dell data disk.

## Phase 4 integration

The executed integrated diagnostic uses `scripts/phase4/build.sh` and `scripts/phase4/run.sh RAW_OUTPUT_ROOT FRESH_EPOCH`, after Phase0–3 dependencies and the CAD assembly have been generated. Math/controller and real Servo use separate CMake contexts and processes to isolate OSQP1.0 from the external ROS vendor. Exact versions/flags and frozen source/config/binary identities are in results/phase4. In a workspace that also has the old control installation, select the QP package explicitly with `-Dpredictive_motion_control_DIR=ROOT/install-phase4-math/predictive_motion_control/share/predictive_motion_control/cmake`; the independent consumer uses a fresh build directory.

The existing source exporter and manifest scripts are included. The clean Phase0–3 container success does not reproduce Phase4 or the final research/metrics/figure pipeline. ENV-003 remains open. See docs/reactive_qp.md, docs/controller_geometry.md and docs/baselines/moveit_servo.md for observer, geometry and timing boundaries.
