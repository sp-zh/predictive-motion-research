cmake_minimum_required(VERSION 3.16)
project(phase5_public_live_affine_v2_foundation LANGUAGES CXX)
find_package(OpenSSL REQUIRED)
find_package(yaml-cpp REQUIRED)
add_library(public_live_affine_v2_foundation STATIC
  foundation_resources.cpp foundation_context.cpp foundation_identity.cpp)
target_compile_features(public_live_affine_v2_foundation PUBLIC cxx_std_17)
target_include_directories(public_live_affine_v2_foundation PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
target_link_libraries(public_live_affine_v2_foundation PRIVATE OpenSSL::Crypto yaml-cpp)
target_compile_options(public_live_affine_v2_foundation PRIVATE -Wall -Wextra -Wpedantic)
# Source-only stage: this target has no executable or old Model/plant dependency.
