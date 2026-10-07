# Clean Phase 0–3 component environment review

Decision: **PASS**, restricted to the source-only component CI build below. This is not `reproducibility_audit.md` and does not close final research reproducibility or accept Phase 4/5.

## Identity and environment

Executed 2026-10-05 03:30:56–03:35:52 UTC on Dell WSL2, using ordinary `codextransfer` rootless Podman 4.9.3. The verified source archive contains no existing install/build/vendor directories, credentials, generated CAD or raw results. Podman confirmed rootless operation; the container used a fresh dependency installation and an uncached recipe build, without mounting the existing development checkout.

- Source archive SHA-256: `ad6e7712e4e1eda5f279148a7e9cb770a17d2e7ffe9e26bd21745c0d654a4f6e`.
- ROS base image index: `docker.io/library/ros:jazzy-ros-base-noble@sha256:066420e07f60aa18262f2479981def87ebcfcec42eefb0c0c57c4a46098348ca`, resolved for Linux amd64.
- Result image ID: `3fd79e0ee92f941f195846ba3880b447b3f4b337b02ad9f7ad6a8c3caaac1c93`.
- GCC 13.3.0, CMake 3.28.3, Eigen 3.4.0, GTest 1.14.0; installed Pinocchio `4.1.0-1noble.20260826.071113` and Coal `3.0.3-2noble.20260825.051040`. Complete package inventory is retained.

Source bundles, both attempts, image metadata and command exit codes are in `results/clean-component-build/`. `root-evidence-review.json` hashes all retained evidence files. The successful build source is preserved under `source-attempt2/`; its internal manifest identifies the exact source bytes tested. Later documentation changes are not silently assigned that executed snapshot identity.

## Failure found and repaired

The first uncached build (`8a450f01374f674359edf2d842de0aa40bebc9f2649483837693f6976b4cee8d`) passed simulation/ROS checks, Phase 1 numerical validation and all 13 control unit cases, then failed `find_package(predictive_motion_control)` in the external consumer. `scripts/phase2/ci.sh` sourced workspace setup before the first control-package installation but did not refresh it after adding that package. Existing overlays hid this defect.

The script now sources `install/setup.bash` immediately after the build and exercises both installed IK and null-space consumers. A new source archive and a full uncached retry passed. Failed logs are retained in `attempt1/`; they were not rewritten as success.

## Actual execution

| Check | Observed result |
|---|---|
| Simulation GTest cases | 4 passed |
| Kinematics GTest cases | 7 passed |
| Control GTest cases | 7 IK + 6 null-space passed |
| Actual GTest total | 24; zero failures/errors/skips in copied XML |
| Phase 1 numerical validation | 2000 configurations, seed 42, PASS |
| ROS state/command/reset integration | 433 messages; finite state, commanded motion, reset service and identical reset state all true |
| Installed plant consumer | `STANDALONE_PLANT_OK time=0.004` |
| Installed kinematics consumer | `KINEMATICS_CONSUMER_OK` |
| Installed IK consumer, executed from `/tmp` | `INSTALLED_EIGEN_ONLY_CONSUMER_PASS` |
| Installed null-space consumer, executed from `/tmp` | `INSTALLED_EIGEN_ONLY_NULLSPACE_CONSUMER_PASS` |

The GTest XML was copied from the immutable successful image by image ID; no tests were rerun just to collect it. The extra collection commands and XML hashes are in `attempt2-xml/`. The wrapper now automatically retains those XML files for future builds. Its collection helper was exercised against this image; the revised wrapper's next complete run will have its own source identity.

## Scope, risks and next acceptance

This verifies fresh userspace dependencies and source builds on the existing WSL kernel. It does not establish a different kernel, bare-metal real-time behavior, hosted GitHub Actions, the editor devcontainer workflow, a new CAD generation run or Phase 4 solver/Servo integration. The actual ROS messages count is nondeterministic; reset identity and numerical tolerances, rather than exact message counts, define acceptance.

Phase 2/3 systematic component diagnostics were separately reviewed and were not rerun by fast container CI. Predictive research benchmarks, metric aggregation and main research figure regeneration remain pending. ENV-003 closes only when the final research source and dependency environment reproduce those outputs. The pinned base, retained image identity and current package inventory do not guarantee that external apt repositories will retain every package revision indefinitely; the final environment needs an export/archive policy.
