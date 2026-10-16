#pragma once
#include "working_face_basis.hpp"
#include <cmath>
#include <algorithm>
#include <limits>
#include <stdexcept>
namespace phase5_roundoff_command64_v1 {
constexpr std::uint64_t additional_scalar_inventory=16,conservative_inventory=744960+additional_scalar_inventory;
static_assert(conservative_inventory==744976&&conservative_inventory<745000,"2 persistent roundoff fields plus sequential <=14 bound/predicate scalars, no new matrices/vectors or perendpoint bank");
constexpr double command_stop_threshold=1e-6,solver_fraction=.5,strict_fraction=.75;
inline bool zeroBoundary(double start,double travel,double lower,double upper){if(!std::isfinite(start)||!std::isfinite(travel)||!std::isfinite(lower)||!std::isfinite(upper)||lower>upper)throw std::invalid_argument("finite original roundoff endpoint inputs");return(travel>0&&upper-start<=0)||(travel<0&&start-lower<=0);}
inline bool eligible(bool stop_policy,double start,double travel,double endpoint,double lower,double upper){return stop_policy&&zeroBoundary(start,travel,lower,upper)&&phase5_working_face_basis_v1::endpointWithinExistingNumericDomain(endpoint,lower,upper);}
struct FirstBounds {double lower=0,upper=0,solver_rate_bound=0,strict_rate_bound=0,nominal_next_w=0;};
inline FirstBounds firstBounds(double w,double nominal_alpha,double old_lower,double old_upper){
 if(!std::isfinite(w)||!std::isfinite(nominal_alpha)||!std::isfinite(old_lower)||!std::isfinite(old_upper)||old_lower>nominal_alpha||nominal_alpha>old_upper)throw std::invalid_argument("finite current nominal inside original alpha guard");FirstBounds b;b.nominal_next_w=w+.004*nominal_alpha;b.solver_rate_bound=std::max({solver_fraction*std::abs(w),std::abs(b.nominal_next_w),solver_fraction*command_stop_threshold});b.strict_rate_bound=std::max({strict_fraction*std::abs(w),std::abs(b.nominal_next_w),strict_fraction*command_stop_threshold});b.strict_rate_bound=std::nextafter(b.strict_rate_bound*(1+16*std::numeric_limits<double>::epsilon()),std::numeric_limits<double>::infinity());
 // Outward rounded interval, intersected with old bounds and including its
 // genuine nominal point. This changes a planning interval, never a control.
 b.lower=std::max(old_lower,std::nextafter((-b.solver_rate_bound-w)/.004,-std::numeric_limits<double>::infinity()));b.upper=std::min(old_upper,std::nextafter((b.solver_rate_bound-w)/.004,std::numeric_limits<double>::infinity()));b.lower=std::min(b.lower,nominal_alpha);b.upper=std::max(b.upper,nominal_alpha);
 if(!std::isfinite(b.nominal_next_w)||!std::isfinite(b.solver_rate_bound)||!std::isfinite(b.strict_rate_bound)||!std::isfinite(b.lower)||!std::isfinite(b.upper)||b.lower<old_lower||b.upper>old_upper||b.lower>b.upper)throw std::invalid_argument("finite contraction intersection, old guard never expanded");return b;
}
inline bool strictFirst(double w,double alpha,const FirstBounds&b){const double next=w+.004*alpha;return std::isfinite(next)&&std::nextafter(std::abs(next),std::numeric_limits<double>::infinity())<=b.strict_rate_bound;}
}
