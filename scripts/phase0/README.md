# Linux Phase0 commands

Run `setup_linux.sh` once as administrator on Ubuntu 24.04 with the official Jazzy apt repository. The `codextransfer` user deliberately has no sudo. Run remaining commands as the workspace owner on native Linux storage:

```
export PM_CACHE=/mnt/d/CodexTransfer/projects/predictive_motion/cache
bash scripts/phase0/fetch_vendor.sh
bash scripts/phase0/build_test.sh
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 run predictive_motion_sim render_model "$PWD/.vendor/menagerie/franka_fr3/scene.xml" "$PWD/results/phase0/fr3.ppm"
```

The bridge advances 4 ms of simulated time per wall timer callback; this is a target schedule, not a real-time performance claim. Publish all model-derived joint names and position targets to `joint_position_command`. Outputs are `joint_states` and `clock`. `reset_simulation` restores the fixed seed and resets simulated time; consumers must handle backward clock jumps. Invalid commands preserve the previous targets. The default scene and upstream actuator gains are unchanged. No prediction, control optimization or real hardware is included.

MuJoCo SDK binaries are Linux x86_64. Deterministic replay is required within the same binary/model/platform; cross-platform bitwise identity is not asserted. The probe only proves Pinocchio C++ linkage, not FR3 kinematic validation (Phase1).

`ci.sh` is the headless CI entrypoint. Container and hosted CI execution require separate verification; a successful local run is not a hosted CI result. Fetch fails if upstream artifacts disappear or if the pinned SHA256 differs.
