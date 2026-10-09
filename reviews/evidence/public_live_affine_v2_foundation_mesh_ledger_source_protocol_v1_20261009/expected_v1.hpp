#pragma once
// Independent frozen literal expectations. No values obtained from project execution.
#include <cstdint>
#include <vector>
namespace expected {
using Count=std::uint64_t;
inline constexpr Count max_count=18446744073709551615ULL;
inline constexpr Count small_live=1042685, small_charge=1053269, small_output=8537912;
inline constexpr Count batch_case_live=11147216, batch_case_charge=28647416, batch_case_output=41363088;
inline constexpr Count batch_live_cap=64000000, batch_live_remainder=8263920;
inline constexpr Count batch_charge_cap=1024000000, batch_charge_prefix=1002659560, batch_charge_remainder=21340440;
inline constexpr Count metadata_cap=8388608;
inline const std::vector<Count> balanced_20_375={18,19,19,19,18,19,19,19,18,19,19,19,18,19,19,19,18,19,19,19};
struct Integer { const char* id; bool multiply; Count a,b,result; };
inline constexpr Integer integer_success[]={
  {"add_zero_max",false,0ULL,18446744073709551615ULL,18446744073709551615ULL},
  {"add_exact_max",false,18446744073709551614ULL,1ULL,18446744073709551615ULL},
  {"add_small",false,17ULL,25ULL,42ULL},
  {"multiply_zero_max",true,18446744073709551615ULL,0ULL,0ULL},
  {"multiply_max_one",true,18446744073709551615ULL,1ULL,18446744073709551615ULL},
  {"multiply_square_below_overflow",true,4294967295ULL,4294967295ULL,18446744065119617025ULL},
};
inline constexpr Integer integer_overflow[]={
  {"add_overflow",false,18446744073709551615ULL,1ULL,0},
  {"multiply_overflow",true,18446744073709551615ULL,2ULL,0},
  {"multiply_square_overflow",true,4294967296ULL,4294967296ULL,0},
};
struct Decimal { const char* id; const char* text; Count cycles; };
inline constexpr Decimal decimal_success[]={
  {"decimal_one_cycle","0.004",1},
  {"decimal_leading_dot",".004",1},
  {"decimal_200","0.8",200},
  {"decimal_375","1.5",375},
  {"decimal_one_second","1",250},
  {"decimal_leading_trailing_zeros","00.0040",1},
  {"decimal_374","1.496",374},
};
inline constexpr Decimal decimal_invalid[]={
  {"decimal_empty","",0},
  {"decimal_zero","0",0},
  {"decimal_off_lattice","0.002",0},
  {"decimal_quarter",".25",0},
  {"decimal_three_quarters",".75",0},
  {"decimal_fraction_over_cap","1.501",0},
  {"decimal_over_cap","1.504",0},
  {"decimal_negative","-0.004",0},
  {"decimal_plus","+0.004",0},
  {"decimal_exponent","4e-3",0},
  {"decimal_space"," 0.004",0},
  {"decimal_two_dots","0..004",0},
  {"decimal_final_dot","1.",0},
  {"decimal_only_dot",".",0},
  {"decimal_letters","nan",0},
  {"decimal_length33","111111111111111111111111111111111",0},
};
inline constexpr Decimal decimal_overflow[]={
  {"decimal_numerator_overflow","18446744073709551616",0},
  {"decimal_scaled_overflow","18446744073709551615",0},
  {"decimal_denominator_overflow",".00000000000000000000",0},
};
inline constexpr Count case_count=66;
} // namespace expected
