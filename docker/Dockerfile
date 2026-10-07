# Immutable ROS base image index inspected from Docker Hub on 2026-10-04.
# Recipe is not counted as verified until an actual container build runs.
FROM docker.io/library/ros:jazzy-ros-base-noble@sha256:066420e07f60aa18262f2479981def87ebcfcec42eefb0c0c57c4a46098348ca
ENV DEBIAN_FRONTEND=noninteractive
ENV CMAKE_BUILD_PARALLEL_LEVEL=2 MAKEFLAGS=-j2
WORKDIR /workspaces/predictive_motion
COPY scripts/phase0/setup_linux.sh /tmp/predictive-motion-setup.sh
RUN bash /tmp/predictive-motion-setup.sh && rm -rf /var/lib/apt/lists/*
COPY . .
RUN bash scripts/ci.sh
CMD ["bash"]
