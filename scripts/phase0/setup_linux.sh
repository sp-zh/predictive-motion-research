#!/usr/bin/env bash
set -euo pipefail
[[ $(id -u) == 0 ]] || { echo 'Run dependency installation with an administrator; transfer user has no sudo.'; exit 1; }
source /etc/os-release
[[ $VERSION_ID == 24.04 ]] || { echo 'Ubuntu 24.04 required'; exit 1; }
test -f /opt/ros/jazzy/setup.bash || { echo 'Install ROS Jazzy from official ROS apt repository first'; exit 1; }
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
  build-essential cmake git curl ca-certificates clang-format libeigen3-dev libgtest-dev libyaml-cpp-dev \
  libglfw3-dev libgl1-mesa-dev python3-colcon-common-extensions python3-numpy python3-matplotlib python3-yaml \
  ros-jazzy-ament-cmake ros-jazzy-ament-cmake-gtest ros-jazzy-rclcpp \
  ros-jazzy-sensor-msgs ros-jazzy-rosgraph-msgs ros-jazzy-std-srvs ros-jazzy-xacro \
  ros-jazzy-pinocchio=4.1.0-1noble.20260826.071113
