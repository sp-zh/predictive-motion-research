# Phase 0 review

Reviewed 2026-10-04 (America/Toronto) after final source integration. Scope is the user's mandatory infrastructure gate, not a motion-control research result.

## Scope completed

Two ament packages: pinned FR3 asset provenance and a C++ MuJoCo plant/ROS bridge. MuJoCo 3.3.7 archive and Menagerie commit 4d038b3feae26ec82b46a4d586379114012a8ac7 are locked by hashes. Joint mapping comes from model names/actuators. Bridge control period is configurable, default 4 ms. Plant library has no ROS includes and can be linked by an independent CMake consumer.

Source docs, architecture, dependency matrix, mathematics, experiment/benchmark protocols, seed splits, Linux setup/fetch/build/CI scripts, Docker/devcontainer recipes and GitHub workflow are integrated into the Mac repository. Linux source and build are owned by ordinary codextransfer, not root.

## Evidence

| Mandatory gate | Actual evidence |
|---|---|
| Repository builds | results/phase0/build.log; both description/sim packages compiled |
| Robot loads and simulates | plant ModelAndClock test loads pinned scene, finds seven actuated arm hinges and advances 250 steps to one simulated second |
| Deterministic reset | ResetAndReplay compares mjSTATE_INTEGRATION for 500 commanded steps before/after reset; seed 43 changes initial state |
| Validated command boundary | transactional invalid-name/NaN/out-of-range rejection; valid command causes measured motion |
| ROS state exchange | ros-integration.log reports finite=1, commanded_motion=1, reset_service=1 and reset_state_identical=1 |
| Visualization | render.log: GUI_RENDER_OK 800x600; figures/fr3_phase0.png visually inspected against actual robot scene |
| Pinocchio compatibility | pinocchio.log: PINOCCHIO_LINK_OK 4.1.0; this is a link probe, not FR3 FK validation |
| Basic CI entrypoint works | clean-final-ci.log: independent native Linux directory fetched locked assets, built and ran tests; clean-final-test-results.log has zero failures |
| Math/plant separation | standalone consumer-build.log / consumer.log: STANDALONE_PLANT_OK time=0.004 |
| Dependencies documented | docs/dependency_matrix.md and results/phase0/metadata/dependencies.lock; upstream notices preserved |

The suite has four GTest cases; colcon's aggregate reports five tests including its registered test wrapper. Do not misreport that aggregate as five independent scientific trials.

Mac independently invoked `PM_TEST_DOMAIN=84 bash scripts/phase0/build_test.sh` on the final Linux workspace. Exit code 0, 435 received ROS messages, all command/reset flags 1, Pinocchio probe and standalone consumer succeeded. This repeats the final workflow independently of the original implementation run.

Exported source/evidence archive SHA-256: 75f17a191b06d7f26a51d1d427fbf1523f44dec7977ba8ff92285cd7ce0fec50. Mac checked it before integrating the archive and inspected the source/tests/render.

## Known issues

Docker/Podman is absent on the tested Dell environment. The digest-pinned container recipe has not been built. No GitHub remote exists, so hosted Actions has not run. These are explicitly unverified and cannot be claimed as clean-container/hosted-CI success. The original Phase 0 requirement makes containerization conditional on practicality; its mandatory basic CI entrypoint was executed locally. Final clean-environment reproducibility audit must still verify a fresh environment before whole-project completion.

No inspection CAD, FK/Jacobian validation, baseline, predictive optimization or benchmark comparison is implemented by this phase. Gripper/tool/robot-model equivalence and collision policy remain later gates. A 4 ms simulation increment and configured timer do not prove 250 Hz wall-clock execution or real-time capability.

## Technical debt

Install export references the local MuJoCo SDK, so an install tree cannot be relocated independently of its dependency prefix. ROS bridge currently rejects invalid commands and retains the prior valid actuator target; full stale-state/failure deceleration policy belongs to the later shared command guard. ROS finite-value probe checks position and dimensions; the plant checks q/dq, but independent effort/velocity message finite checks should be extended before control benchmarks.

## Scientific risk

Determinism is demonstrated only for the pinned platform/build and serial replay, not across hardware or concurrent DDS scheduling. The consumer proves architectural separability, not collision-model correctness. The current screenshot is infrastructure evidence only. No novelty, superiority, safety guarantee or timing claim is justified yet.

## Decision

PASS

All mandatory Phase 0 gates have executable evidence. Proceed only to Phase 1 kinematics validation; optional container/hosted execution remains tracked and required clean-environment auditing is not waived.
