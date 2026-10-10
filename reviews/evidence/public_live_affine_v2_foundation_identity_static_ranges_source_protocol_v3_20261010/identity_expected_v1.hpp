#pragma once
#include <cstddef>
namespace identity_expected {
struct Fixture {const char* name;const char* sha;std::size_t bytes;};
inline constexpr std::size_t group_count=24,target_entries=29,identity_entries=14,range_entries=15,fixture_count=17;
inline constexpr std::size_t max_fixture_count=24,max_file_bytes=16384,max_total_fixture_bytes=65536;
inline constexpr Fixture fixtures[]={
{"identity_plain.txt","65bfdc92e029fd0218f2086e96049d13f824ccbf447da4736c07dd3fa5768a99",32},
{"identity_empty.txt","e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",0},
{"ranges_valid.yaml","73936338fba4ed33377b5b8e65503ce54289459ff6d5e584f1c8f3961fbe18d4",228},
{"ranges_extra_key.yaml","af03aa14f40c785eb37724bef018e28b10b0dbe04a3054b9801210637b427a84",253},
{"ranges_nonmap.yaml","67358ed8fd6cd4d8aac33acaa376b58237beb891c3e984e505d3e57e43f7d320",10},
{"ranges_duplicate_key.yaml","e52368cc832d7e56e06e63dd6f6e2dfb209b3d3d72461b7ad6aeca0ada7bb28d",303},
{"ranges_joint13.yaml","014b437b885bcef5047982b9658a44f7e86b32105920770d205c2331ced4ffa9",225},
{"ranges_control15.yaml","72944b3c697a5895323080051500ac567adde3692d76be35cd81365b16eccd24",231},
{"ranges_joint_flags6.yaml","83e67d17f466bfdc6a6f5481df2e0a0beb5a09dcd6c4f6dc8dc521066a0317c0",225},
{"ranges_control_flags8.yaml","405c7d1d2a234dc30b5d737608e9e28469a4efd771ff0e26a4655f77e92e9c11",231},
{"ranges_joint_flag0.yaml","7e3400e801b0c24740a68ff04619323182eafc8503f12086636c1ce96845c285",228},
{"ranges_control_flag2.yaml","35cbe1fa35b4722e94f9e640718bcf748faa44bbff91e1d3642f72fe855dcfb6",228},
{"ranges_nan.yaml","9cc7617eeaab5daa18841fcd479702c495cbdb8f58ef6c0d0734f31c2f083f84",230},
{"ranges_positive_inf.yaml","8fdbeebb9c675524dc4b69c293db2f37e33e92284b7432a5a320cba88d6fa600",231},
{"ranges_negative_inf.yaml","fe80f176c4e8c61fc9e51e2f28d1ed7888d9ecb1f0d2a69d92bbc0e460f6c649",231},
{"ranges_reversed.yaml","93ff249018f53e1bdb0eaf02f221bddcaa79312bfcd11b03a6350a1973db0b28",228},
{"ranges_equal.yaml","238eb2c4d7c5d91bfc884870c88e44a1596cb724bcc2544346cd75cd2990a9dc",227},
};
inline constexpr double q_lower[7]={-4,-3.5,-3,-2.5,-2,-1.5,-1};
inline constexpr double q_upper[7]={4,3.5,3,2.5,2,1.5,1};
inline constexpr double c_lower[7]={-8,-7.5,-7,-6.5,-6,-5.5,-5};
inline constexpr double c_upper[7]={8,7.5,7,6.5,6,5.5,5};
inline constexpr const char* zero_sha="0000000000000000000000000000000000000000000000000000000000000000";
}
