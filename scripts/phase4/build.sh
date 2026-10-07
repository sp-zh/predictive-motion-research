#!/usr/bin/env bash
set -eo pipefail
root=$(cd "$(dirname "$0")/../.." && pwd)
cd "$root"
source /opt/ros/jazzy/setup.bash
source install/setup.bash
export MUJOCO_ROOT="$root/.vendor/mujoco-3.3.7"
export LD_LIBRARY_PATH="$MUJOCO_ROOT/lib:$LD_LIBRARY_PATH"
# Sources must be provisioned at these exact commits, not a moving tag.
test "$(git -C .vendor/osqp-1.0.0 rev-parse HEAD)" = 236713ce9a56c182ac3230d52108f952afce1523
cmake -S .vendor/osqp-1.0.0 -B .vendor/osqp-1.0.0-build -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="$root/.vendor/osqp-1.0.0-install" -DOSQP_VERSION=1.0.0 -DOSQP_BUILD_SHARED_LIB=OFF -DOSQP_BUILD_STATIC_LIB=ON -DOSQP_USE_FLOAT=OFF -DOSQP_USE_LONG=OFF -DOSQP_ENABLE_PROFILING=ON -DOSQP_ENABLE_PRINTING=OFF -DOSQP_ENABLE_INTERRUPT=OFF -DOSQP_CODEGEN=OFF -DOSQP_BUILD_DEMO_EXE=OFF -DOSQP_BUILD_UNITTESTS=OFF
test "$(git -C .vendor/osqp-1.0.0-build/_deps/qdldl-src rev-parse HEAD)" = 138fdac58b9cd1c4137ff1b99152c8108a6cff5b
cmake --build .vendor/osqp-1.0.0-build -j2
cmake --install .vendor/osqp-1.0.0-build
colcon build --packages-select predictive_motion_control --build-base build-phase4-math --install-base install-phase4-math --cmake-args -DBUILD_BENCHMARKS=OFF -DBUILD_REACTIVE_QP=ON -DBUILD_TESTING=ON -DCMAKE_BUILD_TYPE=Release -Dosqp_DIR="$root/.vendor/osqp-1.0.0-install/lib/cmake/osqp"
source install-phase4-math/setup.bash
colcon test --packages-select predictive_motion_control --build-base build-phase4-math --install-base install-phase4-math --event-handlers console_direct+
colcon test-result --test-result-base build-phase4-math --verbose
python3 tools/phase4_adapters/generate_geometry.py
cmake -S tools/phase4_adapters -B build-phase4-adapters -DCMAKE_BUILD_TYPE=Release -Dpredictive_motion_control_DIR="$root/install-phase4-math/predictive_motion_control/share/predictive_motion_control/cmake" -Dosqp_DIR="$root/.vendor/osqp-1.0.0-install/lib/cmake/osqp"
cmake --build build-phase4-adapters -j2
# Separate CMake context and process. MoveIt may import its OSQP vendor target.
cmake -S tools/phase4_servo -B build-phase4-servo -DCMAKE_BUILD_TYPE=Release
cmake --build build-phase4-servo -j2
