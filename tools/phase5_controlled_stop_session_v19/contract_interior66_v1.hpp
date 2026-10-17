#pragma once
#include <cmath>
#include <algorithm>
#include <limits>
#include <stdexcept>
// Saved-current-QP optimizer planning subset and starting guess only.
// Never clips a native result, actual state, accepted history or command.
// Original roundoff_command64 strictFirst/firstBounds are unchanged.
namespace phase5_contract_interior66_v1 {
constexpr double tolerance_multiple=32.,original_hint_domain=1e-12;
struct Row {double old_lower=0,old_upper=0,lower=0,upper=0,seed_alpha=0,seed_y=0,blend=0,inset=0,scaled_inset=0;};
inline void need(bool b,const char*s){if(!b)throw std::invalid_argument(s);}
inline Row prepare(double lower,double upper,double nominal,double multiplier,double variable_scale,double original_native_absolute_tolerance){
 need(std::isfinite(lower)&&std::isfinite(upper)&&std::isfinite(nominal)&&lower<=nominal&&nominal<=upper&&std::isfinite(multiplier)&&multiplier>0&&multiplier<=1&&std::isfinite(variable_scale)&&variable_scale>0&&original_native_absolute_tolerance==1e-9,"finite existing nominal-containing interval and original native tolerance");
 Row r;r.old_lower=lower;r.old_upper=upper;const double width=upper-lower;
 need(std::isfinite(width)&&width>0,"nonzero genuine original planning interval");
 r.inset=std::min(tolerance_multiple*original_native_absolute_tolerance/multiplier,width/8.);r.scaled_inset=multiplier*r.inset;
 need(std::isfinite(r.inset)&&r.inset>0&&r.scaled_inset>4*original_hint_domain,"insufficient interval to reserve positive interior beyond unchanged numerical hint domain");
 r.lower=std::nextafter(lower+r.inset,std::numeric_limits<double>::infinity());r.upper=std::nextafter(upper-r.inset,-std::numeric_limits<double>::infinity());r.blend=4*r.inset/width;const double midpoint=lower+.5*width;r.seed_alpha=nominal+r.blend*(midpoint-nominal);r.seed_y=r.seed_alpha/variable_scale;
 need(std::isfinite(r.lower)&&std::isfinite(r.upper)&&lower<r.lower&&r.lower<r.upper&&r.upper<upper&&r.blend>0&&r.blend<=.5&&std::isfinite(r.seed_alpha)&&r.seed_alpha>r.lower&&r.seed_alpha<r.upper&&std::isfinite(r.seed_y),"strict inward interval and analytic affine optimizer seed; no clamping/fallback");
 return r;
}
}
