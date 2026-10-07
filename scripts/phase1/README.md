# Phase1 numerical validation

Run as the ordinary workspace owner after the Phase0 fetch/setup:

```
bash scripts/phase1/fetch_model.sh
bash scripts/phase1/build_test.sh
```

The Pinocchio mathematical library has no ROS or MuJoCo runtime coupling. Its mutable data workspace is instance-local; use separate instances for concurrent threads. Runtime inputs use the configured joint-name order; inputs must be finite and dimensionally valid. Kinematics evaluation deliberately permits out-of-limit coordinates for differential evaluation; command-bound checks belong to the controller boundary.

Seven FR3 arm joints are retained. Both official hand finger joints are explicitly locked at 0.02m. Flange is official `fr3_link8`, exactly `fr3_link7 * TransZ(0.107m)`; TCP is flange * TransZ(0.32m). All names and offsets are in YAML, with no robot-type branch. Configured transforms are real SE3 and quaternions are explicitly unit `xyzw`; nonunit/NaN inputs are rejected rather than silently normalized.

Twists and log vectors are linear;angular. The residual is `e=log(T(q)^-1 Td)`. Its joint derivative is `-Jlog6(E^-1) J_LOCAL`; right/body perturbations of desired pose use `Jlog6(E)`. LOCAL_WORLD_ALIGNED rotates both LOCAL blocks to world axes at the TCP origin; it is not WORLD spatial twist at the world origin. A tool-frame rotation and lever arm are handled by the SE3 adjoint, not an empirical compensation.

Numerical tests use mt19937 seed42 and an explicit integer-to-uniform mapping, 2000 configurations inside the intersection of URDF/MuJoCo limits with a 2% margin, `h=1e-6`, and central differences. Translation uses positions; rotation uses SO3 log in the midpoint body basis, never Euler angles. Relative error is Frobenius absolute error divided by `max(analytic_norm,1e-12)`; absolute error governs near-zero derivatives. CSV stores every sample and q; summary records mean, median, p95, p99 and maximum. The first 50 samples also scan h in 1e-4,1e-5,1e-6,1e-7. Mixed six-row norms are numerical-consistency measures, not a physical tracking metric.

Model matching tolerance is 1e-9 m/rad (much tighter than physical model fidelity, but comfortably above double-precision accumulation). Derivative absolute/relative tolerance is 1e-6 (allows finite-difference cancellation without relaxing to macroscopic error). A zero-coordinate structural check proves axis/zero-offset agreement even though zero may lie outside operational limits. Random trials remain within limits. Near-pi tests validate finite reconstruction and derivatives at pi-1e-3; the principal log is discontinuous across pi, and differentiability exactly on the branch cut is not claimed.

Source and installed configurations have distinct, correct relative URDF paths. Installed config/model can be used from `/tmp`; the standalone CMake consumer verifies the installed export. Generated URDFs preserve official source XML; only the auto-generated comment's absolute source path is normalized for stable hashes. `official_source.tar.gz` preserves pinned official xacro/YAML/scripts and license notices; original meshes remain in the pinned upstream repository/cache and are not required by the FK parser. These are infrastructure/numerical tests, not control baselines or research-performance claims.
