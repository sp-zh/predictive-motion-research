#pragma once
#include <cstddef>
namespace lease_expected {
inline constexpr std::size_t case_count=10;
inline constexpr const char* reentry="CHUNK_IO_REENTRY";
inline constexpr const char* poisoned="CHUNK_IO_REENTRY_OR_CLOSED_LEASE";
inline constexpr const char* moved="moved-from case budget";
inline constexpr unsigned long long zero=0;
}
