cmake_minimum_required(VERSION 3.16)
project(phase5_public_live_affine_v2_affine LANGUAGES CXX)
add_subdirectory(../normalization normalized-source EXCLUDE_FROM_ALL)
add_library(public_live_affine_v2_affine STATIC affine_assembly.cpp)
target_compile_features(public_live_affine_v2_affine PUBLIC cxx_std_17)
target_include_directories(public_live_affine_v2_affine PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
target_link_libraries(public_live_affine_v2_affine PUBLIC public_live_affine_v2_normalization)
target_compile_options(public_live_affine_v2_affine PRIVATE -Wall -Wextra -Wpedantic)
# No probe, test, Model call or runtime release in this source checkpoint.
