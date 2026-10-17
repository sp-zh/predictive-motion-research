#pragma once
#include <cmath>
#include <algorithm>
#include <limits>
#include <stdexcept>
#include <string>
#include <cstdint>
// Explicit numerical planning subset of existing selected scaled jerk rows.
// No original SI/H/g/A, native tolerance, literal gate, state or command edit.
namespace phase5_jerk_interior67_v1 {
struct Interval {double old_lower=0,old_upper=0,lower=0,upper=0,inset=0;};
inline Interval prepareScaled(double lower,double upper,double original_absolute_tolerance){
 if(!std::isfinite(lower)||!std::isfinite(upper)||lower>=upper||original_absolute_tolerance!=1e-9)throw std::invalid_argument("finite existing planning interval and unchanged native tolerance");
 Interval r;r.old_lower=lower;r.old_upper=upper;const double width=upper-lower;r.inset=std::min(32*original_absolute_tolerance,width/8);
 r.lower=std::nextafter(lower+r.inset,std::numeric_limits<double>::infinity());r.upper=std::nextafter(upper-r.inset,-std::numeric_limits<double>::infinity());
 if(!std::isfinite(width)||!std::isfinite(r.inset)||r.inset<=4e-12||!(lower<r.lower&&r.lower<r.upper&&r.upper<upper))throw std::invalid_argument("strictly inward planning bounds beyond original hint domain; no fallback or clipping");return r;
}
inline bool isJointJerkRow(const std::string& label,const std::string& units){return label.rfind("feedback_jerk/",0)==0&&units=="rad/s^3";}
template<class Lower,class Upper,class Qualify>void tightenExistingScaledRows(Lower&lower,Upper&upper,int base,Qualify&&qualifies,double original_absolute_tolerance){
 if(base<=0||base>20000||lower.size()!=upper.size()||lower.size()<base||lower.size()>20000)throw std::invalid_argument("finite existing base and solver interval shape");
 unsigned count=0;for(int i=0;i<base;++i)if(qualifies(i)){auto a=prepareScaled(lower(i),upper(i),original_absolute_tolerance);lower(i)=a.lower;upper(i)=a.upper;++count;}
 if(count!=140)throw std::invalid_argument("all140 existing joint feedbackjerk rows required; no native solve after partial/refused planning assembly");
}

}
