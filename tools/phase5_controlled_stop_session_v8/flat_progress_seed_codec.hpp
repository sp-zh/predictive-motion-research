#pragma once
#include "bounded_flat_progress_seed_v4.hpp"
#include "lossless_evidence.hpp"
namespace phase5_flat_progress_seed_codec_v2 {
using Result=phase5_flat_progress_seed_candidate50_v4::Result;
constexpr std::uint64_t maximum_payload_bytes=1024ULL*1024;
inline void validate(const Result& r,bool attempted){
 auto need=[](bool b,const char* s){if(!b)throw std::invalid_argument(s);};const auto& u=r.retry;
 need(r.error.size()<=1024&&r.baseline_error.size()<=1024&&u.error.size()<=1024,"bounded initializer diagnostic strings before codec");
 need(r.corrections.size()<=8&&r.flat_changed==!r.corrections.empty()&&r.baseline_rows_written<=20000&&std::isfinite(r.baseline_violation)&&r.baseline_violation>=0,"bounded measured baseline and flat availability before codec");
 need((u.seed.size()==0||u.seed.size()==144)&&u.seed.allFinite()&&u.row_direction_bounds.rows()<=20000&&(u.row_direction_bounds.cols()==0||u.row_direction_bounds.cols()==4)&&u.row_direction_bounds.allFinite()&&u.row_bounds_written<=static_cast<std::size_t>(u.row_direction_bounds.rows())&&u.attempts.size()<=3,"bounded retry row/seed/prefix shapes before codec");
 need(std::isfinite(u.epsilon)&&std::isfinite(u.initial_violation)&&u.initial_violation>=0&&std::isfinite(u.interval_lower)&&std::isfinite(u.interval_upper),"finite uniform diagnostic values before codec");
 need(!u.changed||(r.retry_available&&u.complete&&u.error.empty()&&u.epsilon>0&&u.epsilon<=1e-6),"uniform changed explicit positive epsilon availability");need(u.changed||u.epsilon==0,"unchanged uniform has zero epsilon");
 if(!r.retry_available)need(!u.complete&&!u.changed&&u.seed.size()==0&&u.row_direction_bounds.size()==0&&u.attempts.empty(),"unavailable retry has no manufactured result");
 if(r.complete)need(attempted&&r.error.empty()&&r.retry_available&&u.complete&&u.error.empty()&&u.seed.size()==144,"outer combined success owns retry and empty error");
 if(!attempted)need(!r.complete&&!r.flat_changed&&!r.retry_available&&r.corrections.empty()&&r.error.empty()&&r.baseline_error.empty(),"unattempted initializer unavailable");
 for(const auto& a:u.attempts)need(std::isfinite(a.epsilon)&&a.epsilon>0&&a.epsilon<=1e-6&&(a.finite?(std::isfinite(a.worst_violation)&&a.worst_violation>=0):a.worst_violation==std::numeric_limits<double>::infinity()),"bounded uniform attempt diagnostics");
 for(const auto& c:r.corrections){need(c.row>=0&&c.row<20000&&c.delta.size()==144&&c.delta.allFinite()&&std::isfinite(c.before)&&std::isfinite(c.after)&&std::isfinite(c.lower)&&std::isfinite(c.upper)&&c.lower<=c.upper&&std::isfinite(c.full_violation)&&c.full_violation>=0&&std::isfinite(c.physical_delta_inf)&&c.physical_delta_inf>=0&&c.physical_delta_inf<=1e-6,"bounded finite correction diagnostics");for(int j=0;j<144;++j)if(j%8!=7)need(c.delta(j)==0,"only free18 beta corrective delta allowed");}
}
inline void emit(phase5_active_evidence_v1::Evidence& out,const Result& r,bool attempted,std::uint64_t cycle,std::uint64_t trial,const std::string& name){
 validate(r,attempted);out.write(name,"DATA_ONLY_BOUNDED_FLAT_AND_UNIFORM_CURRENT_MATRIX_INITIALIZER_BEFORE_NATIVE_SOLVE_V2",[&](phase5_active_evidence_v1::BinaryFile& f){const auto& u=r.retry;
 for(auto v:{cycle,trial,std::uint64_t(attempted),std::uint64_t(r.complete),std::uint64_t(r.flat_changed||u.changed),std::uint64_t(r.flat_changed),std::uint64_t(r.retry_available),std::uint64_t(u.complete),std::uint64_t(u.changed)})f.u64(v);
 f.text(r.error);f.text(r.baseline_error);f.u64(r.baseline_rows_written);f.number(r.baseline_violation);
 for(double v:{u.epsilon,u.initial_violation,u.interval_lower,u.interval_upper})f.number(v);f.text(u.error);f.vector(u.seed);f.u64(u.row_bounds_written);f.matrix(u.row_direction_bounds);f.u64(u.attempts.size());for(const auto& a:u.attempts){f.number(a.epsilon);f.u64(a.finite);f.number(a.worst_violation);}
 f.u64(r.corrections.size());for(const auto& c:r.corrections){f.u64(c.row);for(double v:{c.before,c.after,c.lower,c.upper,c.full_violation,c.physical_delta_inf})f.number(v);f.vector(c.delta);}
 f.text("Data-only current optimizer starting seed. Combined complete/error is authoritative; retry complete is separately measured and not combined acceptance. Combined changed=flat_changed OR uniform_changed; flat_changed can be true with zero uniform epsilon. Baseline scalar refusal retained; baseline row bounds unavailable. Retry written prefix only measured, unwritten zeros unavailable. At most8 flat corrections, deficit<=1e-10 eligibility, at most3 uniform choices, only18 free beta coordinates, all successful nonbeta nominal bits preserved. Combined displacement of18 free beta in original units<=1e-6, not a bound on all20 Z-reconstructed U beta and every augmented row<=original1e-12 hard recheck. No wholepolytope certificate, Model/actualstate/nativecandidate change, native/fullSI/literal200/400/B/C/stop acceptance. 250000 separate numeric precharge;1MiB whole codec cap.");});
}
// Max20000x4 row bounds=640000B, seed1152B,8*(row+6scalar+vector144)
// <10000B,3 attempt72B,3 strings3072B, headers/text<4096B, total<1MiB.
}
