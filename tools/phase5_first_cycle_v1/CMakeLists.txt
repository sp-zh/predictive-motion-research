cmake_minimum_required(VERSION 3.22)
# NONE avoids compiler/version/discovery probes. The one bounded explicit build
# uses the reviewed existing compiler/SDK/static input identities and argv plan.
project(phase5_first_cycle_explicit_v1 NONE)
if(NOT DEFINED FIRST_CYCLE_BUILD_PLAN)
  message(FATAL_ERROR "Exact separately reviewed FIRST_CYCLE_BUILD_PLAN is required")
endif()
add_custom_target(first_cycle_component
  COMMAND /usr/bin/python3.12 -I -S -B ${CMAKE_CURRENT_SOURCE_DIR}/build_once_v2.py ${FIRST_CYCLE_BUILD_PLAN}
  VERBATIM)
# No test, executable launch, metadata, symbol/version probe or automatic run.
