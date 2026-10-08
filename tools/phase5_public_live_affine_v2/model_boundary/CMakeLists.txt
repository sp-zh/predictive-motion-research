cmake_minimum_required(VERSION 3.16)
project(phase5_public_live_affine_v2_model_boundary LANGUAGES CXX)
find_package(OpenSSL REQUIRED)
find_package(yaml-cpp REQUIRED)
add_subdirectory(.. live-foundation EXCLUDE_FROM_ALL)
add_subdirectory(../../phase5_public_coupled_augmented_extension_cpp frozen-extension EXCLUDE_FROM_ALL)
add_library(public_live_affine_v2_model_boundary STATIC model_boundary.cpp)
target_compile_features(public_live_affine_v2_model_boundary PUBLIC cxx_std_17)
target_include_directories(public_live_affine_v2_model_boundary PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
target_link_libraries(public_live_affine_v2_model_boundary PUBLIC
  public_live_affine_v2_foundation public_coupled_augmented_extension
  PRIVATE yaml-cpp OpenSSL::Crypto ${CMAKE_DL_LIBS})
target_compile_options(public_live_affine_v2_model_boundary PRIVATE -Wall -Wextra -Wpedantic)
# No CLI/automatic probe/test. Configuration/build/runtime remain separately gated.
