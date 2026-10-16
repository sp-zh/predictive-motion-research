#pragma once
#include "lossless_evidence.hpp"
#include "current_numeric_guess.hpp"
#include <optional>
namespace phase5_boundary_event_codec_v1 {
inline constexpr const char* role="CURRENT_HINT_EXISTING_ROW_FEASIBILITY_ZERO_STEP_DIAGNOSTICS_V1";
inline void emit(phase5_active_evidence_v1::Evidence& out,const std::optional<phase5_dynamic_numeric_v1::Result>& hint,bool stop,const std::string& file="hint_boundary_events.bin"){
 if(hint){if(hint->boundary_events.size()>(stop?phase5_boundary_retention_limits57::stop_capacity:phase5_boundary_retention_limits57::active_capacity))throw std::invalid_argument("boundary codec full count before write");for(const auto&e:hint->boundary_events)if(e.iteration<0||e.iteration>=512||e.row<0||e.row>=20000||(e.side!=1&&e.side!=-1)||!std::isfinite(e.slack)||e.slack< -1e-12||e.slack>=0||!std::isfinite(e.outward_travel)||e.outward_travel<=0||e.raw_fraction!=e.slack/e.outward_travel)throw std::invalid_argument("boundary codec measured V1 record before write");}
 out.write(file,role,[&](phase5_active_evidence_v1::BinaryFile&f){f.u64(hint.has_value());if(hint){f.u64(hint->boundary_events.size());for(const auto&e:hint->boundary_events){f.u64(e.iteration);f.u64(e.row);f.u64(static_cast<std::uint64_t>(static_cast<std::int64_t>(e.side)));f.number(e.slack);f.number(e.outward_travel);f.number(e.raw_fraction);}}f.text("Stored outward_travel positive absolute direction magnitude with separate side; zero optimizer path fraction only for existing scaled-row feasibility slack>=-1e-12; no ratio epsilon relaxation or posthoc command clipping; final hint primal1e-12/stationarity1e-10/nativeSOLVED/fulloriginalSI/strict200/B400/C2 remain mandatory");});
}
}
