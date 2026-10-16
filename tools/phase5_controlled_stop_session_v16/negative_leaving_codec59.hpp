#pragma once
#include "current_numeric_guess.hpp"
#include "lossless_evidence.hpp"
#include <optional>
namespace phase5_negative_leaving_codec59_v1 {
inline constexpr const char* role="STOP_ONLY_SMALLEST_CURRENT_ROW_NEGATIVE_MULTIPLIER_LEAVING_DIAGNOSTICS_V1";
constexpr std::uint64_t maximum_complete_payload_bytes=512ULL*48+4096;
constexpr std::uint64_t terminal_raw_upper59=phase5_boundary_retention_limits57::terminal_raw_upper+maximum_complete_payload_bytes;
constexpr std::uint64_t terminal_stored_upper59=terminal_raw_upper59+terminal_raw_upper59/4+32ULL*65536+128ULL*1024;
static_assert(maximum_complete_payload_bytes==28672&&maximum_complete_payload_bytes<1048576,"all512 exact leaving records fit unchanged1MiB per-file codec limit");
static_assert(terminal_raw_upper59<phase5_stop_tail_bound_v1::reserved_terminal_bytes&&terminal_stored_upper59<phase5_stop_tail_bound_v1::reserved_terminal_bytes,"extra complete leaving codec plus original trace/boundary/manifest conservative gzip overhead fits unchanged32MiB terminal reserve");
inline void validate(const std::optional<phase5_dynamic_numeric_v1::Result>& hint,bool requested_stop){
 if(!hint)return;const auto&h=*hint;auto need=[](bool ok,const char*why){if(!ok)throw std::invalid_argument(why);};need(h.negative_leaving.size()<=512,"bounded selected leaving count before codec");need(!h.smallest_current_row_policy||requested_stop,"policy unavailable outside stop request");if(!h.smallest_current_row_policy)need(h.negative_leaving.empty(),"no invented selected leaving records outside entered policy");
 int last=-1;
 for(const auto&e:h.negative_leaving){need(e.iteration>=0&&e.iteration<512&&e.iteration>last&&e.row>=0&&e.row<20000&&(e.side==1||e.side==-1)&&e.position>=0&&e.position<144&&std::isfinite(e.selected_multiplier)&&std::isfinite(e.minimum_multiplier)&&e.minimum_multiplier<=e.selected_multiplier&&e.selected_multiplier<-1e-12,"finite ordered measured selected leaving fields");need(static_cast<std::size_t>(e.iteration)<h.events.size(),"chosen record binds actual outer event");const auto&event=h.events[e.iteration];need(event.iteration==e.iteration&&event.worst_row==-1&&e.position<event.active_count&&event.min_multiplier==e.minimum_multiplier,"preserve true old event global min and worst-row meaning");last=e.iteration;
 }
}
inline void emit(phase5_active_evidence_v1::Evidence&out,const std::optional<phase5_dynamic_numeric_v1::Result>&hint,bool requested_stop,std::uint64_t cycle,std::uint64_t trial,const std::string&name="hint_negative_leaving_events.bin"){
 validate(hint,requested_stop);out.write(name,role,[&](phase5_active_evidence_v1::BinaryFile&f){f.u64(cycle);f.u64(trial);f.u64(hint.has_value());f.u64(requested_stop);f.u64(hint&&hint->smallest_current_row_policy);f.u64(hint?hint->negative_leaving.size():0);if(hint)for(const auto&e:hint->negative_leaving){for(int v:{e.iteration,e.row,e.side,e.position})f.u64(static_cast<std::uint64_t>(static_cast<std::int64_t>(v)));f.number(e.selected_multiplier);f.number(e.minimum_multiplier);}f.text("Data-only numerical optimizer leaving diagnostics. Stop repair chooses smallest CURRENT SCALED SOLVER A ROW index among multipliers strictly below original -1e-12. Current row is not original14756SI index; internal planning rows need separate provenance maps. Original worst_row=-1 for this branch and true global minimum multiplier remain in old current_numeric_hint events, with no changed meaning. New selected multiplier may differ from true global minimum. Position refers to ordered working set before erase; actual decision is after original direction infinity<=1e-12, KKT rank/LLT/residual/refinement gates. Up to512 records, no retry/reset. Old active repair=false loop and outputs unchanged. Original current H/g/A/l/u, original bounds/tolerances/512/10s/full-row/nativeSOLVED/SI/nonlinear/geometric/B/history/two2ms/C/stop remain; no clipping/projection/perturbation, no nonnegative-dual/fullQP/physical or phase proof from this record. Scalar records alone are not an independent reconstruction of every working set; saved input replay and final original gates remain required.");});
}
}
