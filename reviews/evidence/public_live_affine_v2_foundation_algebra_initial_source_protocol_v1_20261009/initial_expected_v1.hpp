#pragma once
#include <cstddef>
namespace initial_expected {
inline constexpr std::size_t groups=11;
inline constexpr std::size_t target_entries=97;
// Fixed scalar literals only: not a stored State30 or dynamically allocated buffer.
inline constexpr double tuple[30]={-7.5,-7,-6.5,-6,-5.5,-5,-4.5,-4,-3.5,-3,-2.5,-2,-1.5,-1,-0.5,0,0.5,1,1.5,2,2.5,3,3.5,4,4.5,5,5.5,6,6.5,7};
inline constexpr bool negative_zero[30]={false,true,false,true,false,true,false,true,false,true,false,true,false,true,false,true,false,true,false,true,false,true,false,true,false,true,false,true,false,true};
inline constexpr double shifted_q0=1000000,shifted_s=3,shifted_r=-2;
inline constexpr double mutation_joint=1234,mutation_s=-10,mutation_r=1000;
inline constexpr const char* joint_reason="nonfinite joint vector";
inline constexpr const char* progress_reason="nonfinite progress state";
}
