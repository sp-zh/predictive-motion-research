#pragma once
#include <algorithm>
#include <cmath>
#include <limits>
#include <stdexcept>
#include <vector>

namespace phase5_diagnostic {
struct Limits {double velocity,acceleration,jerk,dt;};
struct Interval {bool feasible=false;double lower=0,upper=0;};
struct Row {int coefficient;double lower,upper;};
inline void check(double w,double alpha,const Limits& l) {
  for(double x:{w,alpha,l.velocity,l.acceleration,l.jerk,l.dt})
    if(!std::isfinite(x))throw std::invalid_argument("nonfinite command cone input");
  if(std::min({l.velocity,l.acceleration,l.jerk,l.dt})<=0)
    throw std::invalid_argument("positive command cone limits required");
  long double recovery=(long double)l.acceleration/l.jerk/l.dt;
  if(!std::isfinite(recovery)||recovery>4096)
    throw std::invalid_argument("command continuation row budget");
}
inline long double recoveryLimit(long double distance,const Limits& l) {
  if(distance<0)throw std::invalid_argument("outside command speed bound");
  const long double j=l.jerk,h=l.dt;
  const long double n=std::max(0.L,std::sqrt(2*distance/j)/h-1);
  auto f=[&](long double k){return distance/(h*(k+1))+.5L*j*h*k;};
  const long double exact=std::min(f(std::floor(n)),f(std::ceil(n)));
  return distance==0?0.L:std::max(0.L,exact-64*std::numeric_limits<double>::epsilon()*std::max(std::abs(exact),j*h));
}
// Pure command-speed continuation; not position/geometry/physical safety.
inline Interval accelerationInterval(double w,double alpha,const Limits& l) {
  check(w,alpha,l);Interval out;
  if(std::abs(w)>l.velocity||std::abs(alpha)>l.acceleration)return out;
  const long double h=l.dt,j=l.jerk,V=l.velocity,A=l.acceleration;
  const long double lo=std::max({-A,(long double)alpha-j*h,-recoveryLimit((long double)w+V,l)});
  const long double hi=std::min({A,(long double)alpha+j*h,recoveryLimit(V-(long double)w,l)});
  out.lower=double(lo);out.upper=double(hi);
  if((long double)out.lower<lo)out.lower=std::nextafter(out.lower,INFINITY);
  if((long double)out.upper>hi)out.upper=std::nextafter(out.upper,-INFINITY);
  out.feasible=out.lower<=out.upper;return out;
}
inline std::vector<Row> candidateVelocityRows(double w,const Limits& l) {
  check(w,0,l);std::vector<Row> rows;
  int maxK=int(std::ceil((long double)l.acceleration/l.jerk/l.dt))+1;
  for(int K=1;K<=maxK;++K){
    long double recovery=.5L*l.jerk*l.dt*l.dt*K*(K-1);
    long double offset=(K-1)*(long double)w;
    rows.push_back({K,double(offset-l.velocity-recovery),double(offset+l.velocity+recovery)});
  }
  return rows;
}
}
