cmake_minimum_required(VERSION 3.22)
project(phase5_active_session_v1 LANGUAGES CXX)

if(NOT CMAKE_SYSTEM_NAME STREQUAL "Linux")
  message(FATAL_ERROR "Active Session provenance uses Linux proc/inode/ELF interfaces")
endif()
if(NOT CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
  message(FATAL_ERROR "A compiler with explicit non-fast-math flags is required")
endif()

find_package(Eigen3 REQUIRED)
find_package(osqp 1.0.0 EXACT CONFIG REQUIRED)
find_package(OpenSSL REQUIRED)
find_package(yaml-cpp REQUIRED)
add_subdirectory(../phase5_public_live_affine_v2 foundation EXCLUDE_FROM_ALL)
add_subdirectory(../phase5_public_coupled_augmented_extension_cpp model-extension EXCLUDE_FROM_ALL)

# Build the existing QP implementation from repository source, rather than
# linking a retained Dell archive or invoking an archived executable.
add_library(active_session_qp_backend STATIC
  ../../src/predictive_motion_control/src/reactive_qp.cpp)
target_include_directories(active_session_qp_backend PUBLIC
  ../../src/predictive_motion_control/include)
target_compile_features(active_session_qp_backend PUBLIC cxx_std_17)
target_link_libraries(active_session_qp_backend PUBLIC Eigen3::Eigen osqp::osqpstatic)

add_library(active_session_prediction STATIC
  model_boundary.cpp normalization.cpp affine_assembly.cpp integrated_horizon_qp.cpp
  solver_forensics.cpp)
target_include_directories(active_session_prediction PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
target_compile_features(active_session_prediction PUBLIC cxx_std_17)
target_link_libraries(active_session_prediction PUBLIC
  public_live_affine_v2_foundation public_coupled_augmented_extension
  active_session_qp_backend PRIVATE OpenSSL::Crypto yaml-cpp ${CMAKE_DL_LIBS})

foreach(target active_session_qp_backend active_session_prediction)
  target_compile_options(${target} PRIVATE -Wall -Wextra -Wpedantic
    -fno-fast-math -ffp-contract=off)
endforeach()

add_executable(active_session_invariants invariant_tests.cpp)
target_link_libraries(active_session_invariants PRIVATE active_session_prediction)
add_executable(active_session_box_tests box_screen_tests.cpp)
target_link_libraries(active_session_box_tests PRIVATE active_session_prediction)
foreach(target active_session_invariants active_session_box_tests)
  target_compile_options(${target} PRIVATE -fno-fast-math -ffp-contract=off)
endforeach()

include(CTest)
set(ACTIVE_SESSION_CONSTANTS "" CACHE FILEPATH "Pinned constants file for the context invariants")
set(ACTIVE_SESSION_CONSTANTS_SHA256 "" CACHE STRING "Expected SHA-256 of that constants file")
if(BUILD_TESTING)
  add_test(NAME active_session_box_implication COMMAND active_session_box_tests)
  set_tests_properties(active_session_box_implication PROPERTIES TIMEOUT 10)
  if(ACTIVE_SESSION_CONSTANTS OR ACTIVE_SESSION_CONSTANTS_SHA256)
    if(NOT EXISTS "${ACTIVE_SESSION_CONSTANTS}" OR NOT ACTIVE_SESSION_CONSTANTS_SHA256 MATCHES "^[0-9a-f]+$")
      message(FATAL_ERROR "Context invariants require an existing constants file and lowercase SHA-256")
    endif()
    string(LENGTH "${ACTIVE_SESSION_CONSTANTS_SHA256}" digest_length)
    if(NOT digest_length EQUAL 64)
      message(FATAL_ERROR "Context invariant digest must have 64 hex characters")
    endif()
    add_test(NAME active_session_context_history_ledger COMMAND active_session_invariants
      "${ACTIVE_SESSION_CONSTANTS}" "${ACTIVE_SESSION_CONSTANTS_SHA256}")
    set_tests_properties(active_session_context_history_ledger PROPERTIES TIMEOUT 10)
  else()
    message(STATUS "Context invariant executable built; test not registered without pinned constants")
  endif()
endif()

option(ACTIVE_SESSION_BUILD_NATIVE_ENTRY "Build the offline entry and observer (does not run them)" OFF)
if(ACTIVE_SESSION_BUILD_NATIVE_ENTRY)
  find_package(predictive_motion_kinematics REQUIRED)
  find_path(ACTIVE_SESSION_MUJOCO_INCLUDE mujoco/mujoco.h
    HINTS "$ENV{MUJOCO_ROOT}/include" REQUIRED)
  find_library(ACTIVE_SESSION_MUJOCO_LIBRARY mujoco
    HINTS "$ENV{MUJOCO_ROOT}/lib" REQUIRED)
  add_library(active_session_runtime STATIC runtime_observer.cpp task_local_provider.cpp lossless_evidence.cpp)
  target_include_directories(active_session_runtime PUBLIC ${ACTIVE_SESSION_MUJOCO_INCLUDE})
  target_link_libraries(active_session_runtime PUBLIC active_session_prediction
    predictive_motion_kinematics::robot_kinematics ${ACTIVE_SESSION_MUJOCO_LIBRARY} yaml-cpp)
  target_compile_options(active_session_runtime PRIVATE -Wall -Wextra -Wpedantic
    -fno-fast-math -ffp-contract=off)
  add_executable(active_session_first_cycle active_first_cycle.cpp)
  target_link_libraries(active_session_first_cycle PRIVATE active_session_runtime)
  add_executable(active_session_observer_tests observer_tests.cpp)
  target_link_libraries(active_session_observer_tests PRIVATE active_session_runtime)
  foreach(target active_session_first_cycle active_session_observer_tests)
    target_compile_options(${target} PRIVATE -fno-fast-math -ffp-contract=off)
  endforeach()
  # No Model/observer/solver/physical entry is registered as an automatic test.
  # Actual profiles, source/SDK/ELF bindings and finite attempt limits belong
  # to the fresh runtime driver, not the mere presence of a CMake target.
endif()
