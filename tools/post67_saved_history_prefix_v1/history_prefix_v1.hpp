#pragma once
#include <array>
#include <cmath>
#include <stdexcept>
namespace post67_history_prefix_v1 {
using Controls=std::array<double,160>;using Joints=std::array<double,7>;
struct Proposal{Controls controls{};bool eligible=false;unsigned scalar_refusals=0;};
inline Proposal propose(const Joints&w,const Joints&previous,const Joints&v,const Joints&a,const Controls&original_nominal,const Controls&recorded_candidate){
 Proposal p;p.controls=original_nominal;bool physical=true;
 for(unsigned j=0;j<7;++j){if(!std::isfinite(w[j])||!std::isfinite(previous[j])||!std::isfinite(v[j])||!std::isfinite(a[j]))throw std::invalid_argument("finite actual accepted/physical history");const double first=-w[j]/.004;const bool ok=std::abs(first)<=1.&&std::abs((first-previous[j])/.004)<=19.98&&std::abs(first/.004)<=19.98;p.scalar_refusals+=!ok;physical=physical&&std::abs(v[j])<=1e-4&&std::abs(a[j])<=1e-3;}
 if(p.scalar_refusals||!physical)return p;
 for(unsigned k=0;k<20;++k){p.controls[8*k+7]=recorded_candidate[8*k+7];for(unsigned j=0;j<7;++j)p.controls[8*k+j]=k==0?-w[j]/.004:0.;}
 p.eligible=true;return p;
}
// A proposed nominal-control sequence only. Caller must regenerate genuine
// Model forecast before any new Model/B/C use; fixed saved affine study does
// not certify new nonlinear maps. No actual state/history/control is clipped.
}
