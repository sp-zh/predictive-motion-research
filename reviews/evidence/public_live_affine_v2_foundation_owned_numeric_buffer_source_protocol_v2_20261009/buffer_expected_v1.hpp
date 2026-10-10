#pragma once
// Independent exactly representable binary-rational literals,fixed before outputs.
#include <array>
#include <cstdint>
namespace buffer_expected {
inline constexpr std::array<double,64> values={
 -8.,-7.5,-7.,-6.5,-6.,-5.5,-5.,-4.5,-4.,-3.5,-3.,-2.5,-2.,-1.5,-1.,-.5,
 0.,.5,1.,1.5,2.,2.5,3.,3.5,4.,4.5,5.,5.5,6.,6.5,7.,7.5,
 8.,8.5,9.,9.5,10.,10.5,11.,11.5,12.,12.5,13.,13.5,14.,14.5,15.,15.5,
 16.,16.5,17.,17.5,18.,18.5,19.,19.5,20.,20.5,21.,21.5,22.,22.5,23.,23.5};
struct Ledger {std::uint64_t live,cumulative;};
inline constexpr Ledger zero{0,0},held4{4,4},held6{6,6},held8{8,8},held64{64,64};
inline constexpr Ledger released4{0,4},released6{0,6},released8{0,8},released64{0,64};
inline constexpr Ledger both5and7{12,12},moved7from12{7,12},released12{0,12};
inline constexpr Ledger own5{5,5},own7{7,7},released5{0,5},released7{0,7};
inline constexpr Ledger both64{128,128},one64remaining{64,128},released128{0,128};
inline constexpr std::uint64_t case_count=13;
}
