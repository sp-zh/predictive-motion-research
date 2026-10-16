#pragma once
#include "model_boundary.hpp"
#include "exact_cycle_endpoint61.hpp"
#include <array>
#include <algorithm>
#include <cmath>
#include <stdexcept>
namespace phase5_current_braking_nominal62_v1 {
namespace live=phase5_active_session_v1;
constexpr std::array<int,20> mesh{1,1,2,2,3,3,4,4,5,5,6,6,8,10,12,16,20,24,28,40};
constexpr std::array<int,12> lengths{1,2,3,4,5,6,7,8,10,12,16,19};
constexpr std::array<int,11> supports{2,3,4,5,6,7,8,10,12,16,19};
constexpr std::uint64_t maximum_families=148,maximum_attempts=1072,maximum_builds=89,build_numeric_precharge=2048,retained_diagnostic_slots=48;
constexpr std::uint64_t whole_numeric_upper=phase5_boundary_retention_limits57::prospective_whole_numeric_upper+maximum_builds*build_numeric_precharge;
static_assert(whole_numeric_upper==1799688432&&whole_numeric_upper<1800000000,"at most121-32=89 new nominal builds, precharge2048 each, unchanged1.8B whole bound");
static_assert(phase5_exact_cycle61_v1::conservative_inventory+retained_diagnostic_slots==744960&&744960<745000,"only <=48 scalar nominal diagnostics remain during original numeric hint; candidate scratch dies before forecast");
struct Diagnostics {std::array<std::uint64_t,8> selected{},attempted{};std::array<double,8> pulse{},terminal_rate{};std::uint64_t total_attempts=0;bool complete=false;};
struct Attempt {std::uint64_t channel=0,family=0,reason=0,cell=0,step=0;double pulse=0,last_rate=0,last_position=0,max_jerk=0,observed=0,bound=0;};
struct Check {std::uint64_t reason=0,cell=0,step=0;double rate=0,position=0,max_jerk=0,observed=0,bound=0;};
inline void need(bool b,const char*why){if(!b)throw std::invalid_argument(why);}
inline std::array<double,20> family(double rate,double previous,double target,int L,int M,double&pulse){
 std::array<double,20> base{},shape{},out{};const int peak=(M-1)/2;double base_change=0,den=0;
 for(int k=0;k<20;++k){base[k]=previous*std::max(0.,1.-double(k+1)/L);shape[k]=k<M?std::min(double(k+1)/(peak+1),double(M-k)/(M-peak)):0.;base_change+=.004*mesh[k]*base[k];den+=.004*mesh[k]*shape[k];}need(std::isfinite(den)&&den>0,"finite braking family denominator");pulse=(target-rate-base_change)/den;need(std::isfinite(pulse),"finite braking family pulse");for(int k=0;k<20;++k)out[k]=base[k]+pulse*shape[k];return out;
}
constexpr std::array<double,16> progress_jerks{4.99,4.5,4.,3.5,3.,2.5,2.,1.5,1.,.75,.5,.25,.1,.05,.02,.01};
inline std::array<double,20> progressEnvelope(double rate,double previous,double target,int family,double&fraction,Check&failure){
 std::array<double,20> lower{},upper{},out{};const double j=progress_jerks.at(family);double low_change=0,high_change=0;fraction=0;
 for(int k=0;k<20;++k){lower[k]=std::max({previous-j*.004*(k+1),-j*.004*(19-k),-.4995});upper[k]=std::min({previous+j*.004*(k+1),j*.004*(19-k),.4995});if(lower[k]>upper[k]){failure.reason=9;failure.cell=k;failure.observed=lower[k];failure.bound=upper[k];return out;}low_change+=.004*mesh[k]*lower[k];high_change+=.004*mesh[k]*upper[k];}
 const double denominator=high_change-low_change;if(!(denominator>0)&&std::isfinite(denominator)){failure.reason=10;failure.observed=denominator;failure.bound=0;return out;}fraction=(target-rate-low_change)/denominator;if(!std::isfinite(fraction)||fraction<0||fraction>1){failure.reason=10;failure.observed=fraction;failure.bound=fraction<0?0.:1.;return out;}
 for(int k=0;k<20;++k)out[k]=(1-fraction)*lower[k]+fraction*upper[k];return out;
}
inline Check check(const std::array<double,20>&u,double rate,double previous,double position,bool progress,double C_lower,double C_upper,double target){
 Check out;out.rate=rate;out.position=position;const double accel=progress?.5:1.,jerk=progress?5.:20.;auto fail=[&](std::uint64_t reason,double observed,double bound){out.reason=reason;out.observed=observed;out.bound=bound;return out;};
 for(int k=0;k<20;++k){out.cell=k;out.step=0;const double a=u[k];if(!std::isfinite(a))return fail(1,a,0);if(std::abs(a)>accel*.999)return fail(2,std::abs(a),accel*.999);const double j0=std::abs((a-previous)/.004);if(j0>jerk*.999)return fail(3,j0,jerk*.999);
  if(progress){const double bernstein=out.position+.5*.004*mesh[k]*out.rate;if(!std::isfinite(bernstein)||bernstein<0||bernstein>1)return fail(6,bernstein,bernstein<0?0.:1.);}
  for(int step=0;step<mesh[k];++step){out.step=step;if(progress){for(double t:{.002,.004}){const double ss=out.position+t*out.rate+.5*t*t*a,rr=out.rate+t*a;if(!std::isfinite(ss)||ss<0||ss>1)return fail(6,ss,ss<0?0.:1.);if(!std::isfinite(rr)||rr<=0||rr>.2)return fail(6,rr,rr<=0?0.:.2);}const double nexts=out.position+.004*out.rate+.5*.004*.004*a,nextr=out.rate+.004*a;out.position=nexts;out.rate=nextr;const double j=std::abs((a-previous)/.004);out.max_jerk=std::max(out.max_jerk,j);if(j>5.)return fail(3,j,5.);previous=a;}
   else{const double next=out.rate+.004*a,implied=(next-out.rate)/.004,j=std::abs((implied-previous)/.004),C=out.position+.004*next;if(!std::isfinite(next)||!std::isfinite(C)||!std::isfinite(j))return fail(1,0,0);if(std::abs(implied)>1.)return fail(2,std::abs(implied),1.);if(j>20.)return fail(3,j,20.);if(std::abs(next)>.0625)return fail(4,std::abs(next),.0625);if(C<C_lower+.005||C>C_upper-.005)return fail(5,C,C<C_lower+.005?C_lower+.005:C_upper-.005);out.rate=next;out.position=C;previous=implied;out.max_jerk=std::max(out.max_jerk,j);}
  }
 }
 out.cell=20;out.step=0;if(u.back()!=0)return fail(7,u.back(),0);if(!std::isfinite(out.rate)||std::abs(out.rate-target)>1e-12)return fail(8,std::abs(out.rate-target),1e-12);out.observed=out.rate;out.bound=target;return out;
}
template<class Emit> Diagnostics build(const live::AcceptedCommandHistory&cmd,const live::ProgressHistory&progress,const live::StaticDomainRanges&ranges,std::vector<live::NominalControl>&controls,Emit&&emit){
 need(controls.size()==20,"fixed20 existing nominal vector");need(cmd.completed&&progress.completed&&cmd.boundary.completed_tick==progress.boundary.completed_tick&&cmd.boundary.completed_command_sequence==progress.boundary.completed_command_sequence&&cmd.observation_id==progress.observation_id&&cmd.transaction_id==progress.transaction_id&&!cmd.observation_id.empty()&&cmd.observation_id.size()<=256&&!cmd.transaction_id.empty()&&cmd.transaction_id.size()<=256,"matching completed current history identity/boundary");need(std::isfinite(progress.s)&&progress.s>=0&&progress.s<=1&&std::isfinite(progress.r)&&progress.r>0&&progress.r<=.2&&std::isfinite(progress.previous_b)&&std::abs(progress.previous_b)<=.5,"finite positive genuine current progress history");
 for(int j=0;j<7;++j)need(std::isfinite(cmd.C[j])&&cmd.C[j]>=ranges.cLower()[j]+.005&&cmd.C[j]<=ranges.cUpper()[j]-.005&&std::isfinite(cmd.w[j])&&std::abs(cmd.w[j])<=.0625&&std::isfinite(cmd.previous_alpha[j])&&std::abs(cmd.previous_alpha[j])<=1.,"finite genuine current command history/domain");
 // Sequential <=20base+20shape+20candidate+160next controls plus scalar state;
 // no family bank, no Model call and no actual state/accepted history changes.
 std::array<live::NominalControl,20> next{};Diagnostics diagnostics;
 for(int channel=0;channel<8;++channel){const bool prog=channel==7;const double rate=prog?progress.r:cmd.w[channel],prior=prog?progress.previous_b:cmd.previous_alpha[channel],target=prog?std::min(1e-8,rate):0.,position=prog?progress.s:cmd.C[channel];bool found=false;std::uint64_t id=0;
  for(int L:lengths){for(int M:supports){need(diagnostics.total_attempts<maximum_attempts&&id<132,"finite132x8 nominal family preattempt cap");double pulse=0;const auto candidate=family(rate,prior,target,L,M,pulse);const auto proof=check(candidate,rate,prior,position,prog,prog?0:ranges.cLower()[channel],prog?0:ranges.cUpper()[channel],target);++diagnostics.total_attempts;++diagnostics.attempted[channel];emit(Attempt{static_cast<std::uint64_t>(channel),id,proof.reason,proof.cell,proof.step,pulse,proof.rate,proof.position,proof.max_jerk,proof.observed,proof.bound});if(!proof.reason){diagnostics.selected[channel]=id;diagnostics.pulse[channel]=pulse;diagnostics.terminal_rate[channel]=proof.rate;for(int k=0;k<20;++k){if(prog)next[k].b=candidate[k];else next[k].alpha[channel]=candidate[k];}found=true;break;}++id;}if(found)break;}
  if(!found&&prog){for(int envelope=0;envelope<16;++envelope){need(diagnostics.total_attempts<maximum_attempts,"finite1072 joint-plus-progress preattempt cap");double fraction=0;Check proof;proof.rate=rate;proof.position=position;const auto candidate=progressEnvelope(rate,prior,target,envelope,fraction,proof);if(!proof.reason)proof=check(candidate,rate,prior,position,true,0,0,target);++diagnostics.total_attempts;++diagnostics.attempted[channel];const std::uint64_t family_id=132+envelope;emit(Attempt{7,family_id,proof.reason,proof.cell,proof.step,fraction,proof.rate,proof.position,proof.max_jerk,proof.observed,proof.bound});if(!proof.reason){diagnostics.selected[channel]=family_id;diagnostics.pulse[channel]=fraction;diagnostics.terminal_rate[channel]=proof.rate;for(int k=0;k<20;++k)next[k].b=candidate[k];found=true;break;}}}
  need(found,"finite132 joint or132plus16 progress nominal families exhausted; all failures retained, no inherited nominal fallback");
 }
 // Commit only a completely checked planning vector; never clip/project any
 // actual state, accepted C/w/alpha/s/r/b, proposed execution or frozen source.
 for(int k=0;k<20;++k)controls[k]=next[k];diagnostics.complete=true;return diagnostics;
}
}
