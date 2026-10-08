cmake_minimum_required(VERSION 3.16)
project(phase5_public_affine_horizon LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
find_package(Eigen3 REQUIRED)
find_package(yaml-cpp REQUIRED)
find_package(OpenSSL REQUIRED)
add_library(public_affine_horizon STATIC public_affine_horizon.cpp public_affine_horizon_native.cpp)
target_link_libraries(public_affine_horizon PUBLIC Eigen3::Eigen)
target_include_directories(public_affine_horizon PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}
 ${CMAKE_CURRENT_SOURCE_DIR}/../phase5_public_coupled_augmented_extension_cpp
 ${CMAKE_CURRENT_SOURCE_DIR}/../phase5_public_coupled_augmented_cpp
 ${CMAKE_CURRENT_SOURCE_DIR}/../phase5_public_coupled_derivative_cpp
 ${CMAKE_CURRENT_SOURCE_DIR}/../phase5_public_coupled_cpp_v2)
target_compile_options(public_affine_horizon PRIVATE -Wall -Wextra -Wpedantic)
add_executable(public_affine_horizon_probe public_affine_horizon_probe.cpp)
target_link_libraries(public_affine_horizon_probe PRIVATE public_affine_horizon yaml-cpp OpenSSL::Crypto)
target_compile_options(public_affine_horizon_probe PRIVATE -Wall -Wextra -Wpedantic)
# Header-only carriers are consumed; no original model sources/libraries linked.
