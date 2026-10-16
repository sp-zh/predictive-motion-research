#pragma once
#include "working_face_basis.hpp"
#include "stop_tail_byte_bound.hpp"
#include <stdexcept>
#include <vector>
namespace phase5_boundary_retention_limits57 {
constexpr std::uint64_t active_capacity=1024,stop_capacity=12288;
// Preserve the entire original active-only refusal string for bitwise legacy
// comparisons; active1024 is unchanged, stop12288 is used only for stop trials.
template<class Event>inline void append(std::vector<Event>& records,const Event& event,bool stop){
 if(records.size()>=(stop?stop_capacity:active_capacity))throw std::invalid_argument(stop?"finite current near-boundary diagnostic cap (stop12288,active1024)":"finite current near-boundary diagnostic cap (stop4096,active1024)");
 records.push_back(event);
}

constexpr std::uint64_t conservative_numeric_inventory57=phase5_working_face_basis_v1::conservative_numeric_inventory55+(stop_capacity-phase5_working_face_basis_v1::declared_stop_boundary_capacity54)*6;
constexpr std::uint64_t declared_numeric_allowance57=745000;
constexpr std::uint64_t fixed_global_trials=176,fixed_active_commits=32,maximum_stop_trials=fixed_global_trials-fixed_active_commits;
// Every stop trial occurs only after32 completed active commands, each with at
// leastone already-consumed trial. Failed active sessions have zero stop trials.
// Keep the old proven whole upper bound, add only possible stop-trial deltas.
constexpr std::uint64_t original_whole_numeric_upper=1793026160;
constexpr std::uint64_t prospective_whole_numeric_upper=original_whole_numeric_upper+maximum_stop_trials*(declared_numeric_allowance57-phase5_working_face_basis_v1::declared_numeric_allowance53);
// Three u64 plus three IEEE doubles per complete boundary event. Original V1
// header/scope text is less than4096 bytes; output and tail budgets stay fixed.
constexpr std::uint64_t maximum_complete_boundary_codec_bytes=stop_capacity*48+4096;
static_assert(conservative_numeric_inventory57==741008&&conservative_numeric_inventory57<declared_numeric_allowance57,"all12288 full boundary events precharged before allocation");
static_assert(maximum_stop_trials==144&&prospective_whole_numeric_upper==1799506160&&prospective_whole_numeric_upper<1800000000,"fixed32 active first plus176 trial total preserves original1.8B global limit");
static_assert(maximum_complete_boundary_codec_bytes==593920&&maximum_complete_boundary_codec_bytes<1048576,"complete V1 boundary payload below1MiB, no records omitted");
constexpr std::uint64_t terminal_raw_upper=phase5_stop_tail_bound_v1::maximum_terminal_bytes+maximum_complete_boundary_codec_bytes;
constexpr std::uint64_t terminal_stored_upper=terminal_raw_upper+terminal_raw_upper/4+32ULL*65536+128ULL*1024;
static_assert(terminal_raw_upper<phase5_stop_tail_bound_v1::reserved_terminal_bytes&&terminal_stored_upper<phase5_stop_tail_bound_v1::reserved_terminal_bytes,"full boundary plus prior terminal, conservative25percent gzip overhead,32flush blocks and128KiB manifests fit original32MiB raw andstored tail; failed partial never resets charges");
}
