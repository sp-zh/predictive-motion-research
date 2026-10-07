// Independent all-K cone oracle vs production stationary-point implementation.
// Analytic fixtures, not robot trials or universal position/collision stop proof.
#include <predictive_motion_control/predictive.hpp>
#include <iostream>
#include <cmath>
#include <random>
#include <limits>
#include <algorithm>
using namespace predictive_motion::control;
int main(){
 PreviewLimits l;l.progress_speed=.2;l.progress_acceleration=.5;l.progress_jerk=5;const double dt=.004;
 auto impossible=progressStopBounds(.1,.199,.5,dt,l);
 if(impossible.feasible||std::isfinite(impossible.acceleration)||std::abs(impossible.lower-.48)>1e-12||std::abs(impossible.upper-.09)>1e-11)return 1;
 auto valid=progressStopBounds(.1,.199,0,dt,l);
 if(!valid.feasible||std::abs(valid.acceleration+.02)>1e-12||.199+dt*valid.acceleration>l.progress_speed+1e-12)return 2;
 auto nan=progressStopBounds(std::numeric_limits<double>::quiet_NaN(),0,0,dt,l);
 if(nan.feasible||std::isfinite(nan.acceleration))return 3;
 auto future_cap=progressStopBounds(.1,.1995,.1,dt,l);if(future_cap.feasible)return 4;
 double r=.001,b=-.04,s=.1;const double expected[]={-.06,-.0775,-.0575,-.0375,-.0175,0};
 for(double e:expected){auto p=progressStopBounds(s,r,b,dt,l);if(!p.feasible||std::abs(p.acceleration-e)>1e-11)return 5;b=p.acceleration;s+=dt*r+.5*dt*dt*b;r+=dt*b;if(r < -1e-12)return 6;}
 if(std::abs(r)>1e-12||std::abs(b)>1e-12)return 7;
 std::mt19937 rng(20261007);int feasible=0,rejected=0,boundary=0;double error=0;
 for(int t=0;t<1000;++t){double rr=double(rng()%1001)/5000,prev=double(int(rng()%1001)-500)/1000;
  double lo=std::max({-.5,prev-.02,-rr/dt}),hi=std::min({.5,prev+.02,(.2-rr)/dt});
  // Every future prefix of the maximum-jerk recovery, not the producer's
  // optimized floor/ceil stationary-point formula.
  for(int k=0;k<=25;++k){lo=std::max(lo,-rr/(dt*(k+1))-.02*k/2);hi=std::min(hi,(.2-rr)/(dt*(k+1))+.02*k/2);}
  auto p=progressStopBounds(.1,rr,prev,dt,l);error=std::max({error,std::abs(p.lower-lo),std::abs(p.upper-hi)});
  if(lo<hi-1e-10&&!p.feasible)return 8;if(lo>hi+1e-10&&p.feasible)return 9;if(std::abs(lo-hi)<=1e-10)++boundary;
  if(!p.feasible){++rejected;continue;}++feasible;
  double acc=p.acceleration,speed=rr+dt*acc;if(std::abs(acc-prev)/dt>5+1e-10||std::abs(acc)>.5+1e-10||speed< -1e-12||speed>.2+1e-12)return 10;
  for(int k=0;k<26&&acc!=0;++k){acc=acc<0?std::min(0.,acc+.02):std::max(0.,acc-.02);speed+=dt*acc;if(speed< -1e-12||speed>.2+1e-12)return 11;}
 }
 if(error>1e-11)return 12;
 std::cout.precision(17);std::cout<<"ROOT_PROGRESS_CONTINUATION_PASS analytic_cases=5 sampled_states=1000 feasible="<<feasible<<" rejected="<<rejected<<" boundary_states="<<boundary<<" bound_error="<<error<<" exact_legacy_counterexample_stop=5_braking_steps_then_zero_acceleration\n";
}
