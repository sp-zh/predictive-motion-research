#pragma once
#include <array>
#include <algorithm>
#include <cmath>
#include <stdexcept>
namespace phase5_actual_task_metrics_v1 {
using Vec3=std::array<double,3>;using Rot3=std::array<double,9>;
struct Pose {Vec3 position;Rot3 rotation;};
struct Error {double translation_m=0,orientation_rad=0;bool within_10mm_005rad=false;};
inline void validate(const Pose& p){for(double x:p.position)if(!std::isfinite(x))throw std::invalid_argument("finite actual/desired world position");for(double x:p.rotation)if(!std::isfinite(x))throw std::invalid_argument("finite actual/desired world rotation");double err=0;for(int i=0;i<3;++i)for(int j=0;j<3;++j){double dot=0;for(int k=0;k<3;++k)dot+=p.rotation[k*3+i]*p.rotation[k*3+j];err=std::max(err,std::abs(dot-(i==j?1.:0.)));}const auto& r=p.rotation;double det=r[0]*(r[4]*r[8]-r[5]*r[7])-r[1]*(r[3]*r[8]-r[5]*r[6])+r[2]*(r[3]*r[7]-r[4]*r[6]);if(err>1e-8||std::abs(det-1)>1e-8)throw std::invalid_argument("proper orthonormal world rotation");}
// World position difference, distinct from SE(3) log translation. SO(3) angle
// lies in [0,pi]. This metric grants no execution or success permission.
inline Error measure(const Pose& actual,const Pose& desired){validate(actual);validate(desired);Error o;Vec3 dp;for(int i=0;i<3;++i)dp[i]=desired.position[i]-actual.position[i];o.translation_m=std::hypot(dp[0],dp[1],dp[2]);Rot3 rel{};for(int i=0;i<3;++i)for(int j=0;j<3;++j)for(int k=0;k<3;++k)rel[i*3+j]+=actual.rotation[k*3+i]*desired.rotation[k*3+j];const double cosine=std::clamp((rel[0]+rel[4]+rel[8]-1)*.5,-1.,1.);const double sine=.5*std::hypot(rel[7]-rel[5],rel[2]-rel[6],rel[3]-rel[1]);o.orientation_rad=std::atan2(sine,cosine);if(!std::isfinite(o.translation_m)||!std::isfinite(o.orientation_rad))throw std::invalid_argument("finite actual world task error");o.within_10mm_005rad=o.translation_m<=.01&&o.orientation_rad<=.05;return o;}
}
