cmake_minimum_required(VERSION 3.16)
project(phase5_integrated_horizon_qp_v1 LANGUAGES CXX)
# Candidate intended at tools/phase5_integrated_horizon_qp_v1. Configuration and
# discovery/build are NOT released by this source file or its presence in Git.
find_package(Eigen3 REQUIRED)
find_package(osqp 1.0.0 EXACT CONFIG REQUIRED)
add_subdirectory(../phase5_public_live_affine_v2/affine live-affine EXCLUDE_FROM_ALL)
add_library(phase5_integrated_horizon_qp_v1 STATIC integrated_horizon_qp.cpp first_cycle_component.cpp)
target_compile_features(phase5_integrated_horizon_qp_v1 PUBLIC cxx_std_17)
target_include_directories(phase5_integrated_horizon_qp_v1 PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}
  ${CMAKE_CURRENT_SOURCE_DIR}/../../src/predictive_motion_control/include)
# Isolated original QP implementation. No legacy predictive.cpp or main target.
add_library(phase5_integrated_qp_backend_v1 STATIC
  ../../src/predictive_motion_control/src/reactive_qp.cpp)
target_include_directories(phase5_integrated_qp_backend_v1 PUBLIC
  ${CMAKE_CURRENT_SOURCE_DIR}/../../src/predictive_motion_control/include)
target_compile_features(phase5_integrated_qp_backend_v1 PUBLIC cxx_std_17)
target_link_libraries(phase5_integrated_qp_backend_v1 PUBLIC Eigen3::Eigen osqp::osqpstatic)
target_link_libraries(phase5_integrated_horizon_qp_v1 PUBLIC
  public_live_affine_v2_affine phase5_integrated_qp_backend_v1)
target_compile_options(phase5_integrated_horizon_qp_v1 PRIVATE -Wall -Wextra -Wpedantic)
# Complete future build enables the actual task provider and pins its
# Pinocchio/kinematics/config/reference closure separately.
# No CLI/main/test/solver/Model/plant invocation is configured here.
option(PHASE5_BUILD_TASK_PROVIDER "Build separately frozen actual task provider" OFF)
if(PHASE5_BUILD_TASK_PROVIDER)
  find_package(predictive_motion_kinematics REQUIRED)
  add_library(phase5_integrated_task_provider_v1 STATIC task_local_provider.cpp)
  target_compile_features(phase5_integrated_task_provider_v1 PUBLIC cxx_std_17)
  target_include_directories(phase5_integrated_task_provider_v1 PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
  target_link_libraries(phase5_integrated_task_provider_v1 PUBLIC
    phase5_integrated_horizon_qp_v1 predictive_motion_kinematics::robot_kinematics)
  target_compile_options(phase5_integrated_task_provider_v1 PRIVATE -Wall -Wextra -Wpedantic)
endif()
