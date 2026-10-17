#pragma once
#include "physical_braking_nominal65.hpp"
#include "contract_interior66_v1.hpp"
namespace phase5_causal_braking68_v1 {
namespace old=phase5_physical_braking65_v1;namespace family=phase5_current_braking_nominal63_v1;namespace live=phase5_active_session_v1;
constexpr std::uint64_t additional_trial_slots=256,whole_numeric_upper=1799688442ULL+176*additional_trial_slots;
static_assert(whole_numeric_upper==1799733498ULL&&whole_numeric_upper<1800000000ULL,"explicit pertrial reservation unchanged whole cap");
static_assert(744998<745000&&724326+additional_trial_slots<745000,"no new hint lifetime bank/flag; additional scalar scratch only outside hint");
// Actual acceleration is NOT available on both original context seams. This
// new predicate does not check it; physical a<=.001 / dwell50 remain mandatory.
template<class W,class P,class V>bool eligible(const W&w,const P&previous,const V&v,double s,double r,double b){
 if(!(std::isfinite(s)&&s>=0&&s<=1&&std::isfinite(r)&&r>0&&r<=1e-6&&std::isfinite(b)&&std::abs(b)<=1e-4))return false;
 for(int j=0;j<7;++j){if(!(std::isfinite(w[j])&&std::abs(w[j])<=.0625&&std::isfinite(previous[j])&&std::abs(previous[j])<=1&&std::isfinite(v[j])&&std::abs(v[j])<=1e-4))return false;const double a=-w[j]/.004;if(!(std::isfinite(a)&&std::abs(a)<=1&&std::abs((a-previous[j])/.004)<=19.98&&std::abs(a/.004)<=19.98))return false;}return true;
}
// Exact original channel7 family order/arithmetic/checks, without traversing
// seven joint doublehat banks first. Writes only existing controls[].b.
template<class Emit>old::Diagnostics progressOnly(const live::ObservedActual&a,const live::AcceptedCommandHistory&cmd,const live::ProgressHistory&p,const old::Baseline&baseline,const live::StaticDomainRanges&ranges,std::vector<live::NominalControl>&controls,Emit&&emit){
 old::match(a,cmd,p);old::need(baseline.valid&&baseline.boundary.completed_tick==0&&baseline.boundary.completed_command_sequence==0&&controls.size()==20,"same baseline and fixed20 existing controls");old::Diagnostics d;const double rate=p.r,prior=p.previous_b,pos=p.s;bool found=false;
 auto record=[&](std::uint64_t id,const std::array<double,20>&u,double pulse,family::Check proof){old::need(d.total_attempts<1080&&id<149,"original progress attempt bound");if(!proof.reason&&rate+.004*u[0]<old::first_progress_floor){proof.reason=12;proof.cell=proof.step=0;proof.observed=rate+.004*u[0];proof.bound=old::first_progress_floor;}++d.total_attempts;++d.attempted[7];emit(old::Attempt{7,id,proof.reason,proof.cell,proof.step,pulse,0,0,proof.rate,proof.position,proof.max_jerk,proof.observed,proof.bound});if(!proof.reason&&!found){found=true;d.selected[7]=id;d.pulse1[7]=pulse;d.terminal_rate[7]=proof.rate;for(int k=0;k<20;++k)controls[k].b=u[k];}};
 std::uint64_t id=0;for(int L:family::lengths){for(int M:family::supports){double pulse=0;const auto u=family::family(rate,prior,old::nominal_progress_target,L,M,pulse);record(id++,u,pulse,family::check(u,rate,prior,pos,true,0,0,old::nominal_progress_target));if(found)break;}if(found)break;}
 if(!found)for(int e=0;e<16;++e){double pulse=0;family::Check proof;proof.rate=rate;proof.position=pos;const auto u=family::progressEnvelope(rate,prior,old::nominal_progress_target,e,pulse,proof);if(!proof.reason)proof=family::check(u,rate,prior,pos,true,0,0,old::nominal_progress_target);record(132+e,u,pulse,proof);if(found)break;}
 if(!found){std::array<double,20>u{};for(int k=0;k<20;++k)u[k]=controls[k].b;record(148,u,0,family::check(u,rate,prior,pos,true,0,0,0.,true));}old::need(found,"original independent149 progress families exhausted");d.complete=true;return d;
}
template<class Emit>old::Diagnostics build(const live::ObservedActual&a,const live::AcceptedCommandHistory&c,const live::ProgressHistory&p,const old::Baseline&b,const live::StaticDomainRanges&ranges,std::vector<live::NominalControl>&controls,Emit&&emit){
 old::match(a,c,p);old::need(b.valid&&b.boundary.completed_tick==0&&b.boundary.completed_command_sequence==0,"same original task-start baseline boundary required");if(!eligible(c.w,c.previous_alpha,a.v,p.s,p.r,p.previous_b))return old::build(a,c,p,b,ranges,controls,std::forward<Emit>(emit));
 // No new160-array copy. Check each actual joint prefix with ORIGINAL200-step
 // scalar checker before assigning existing controls; no rounded state reset.
 for(int j=0;j<7;++j){std::array<double,20>u{};u[0]=-c.w[j]/.004;const auto proof=family::check(u,c.w[j],c.previous_alpha[j],c.C[j],false,ranges.cLower()[j],ranges.cUpper()[j],0.);emit(old::Attempt{static_cast<std::uint64_t>(j),0,proof.reason,proof.cell,proof.step,u[0],0,0,proof.rate,proof.position,proof.max_jerk,proof.observed,proof.bound});old::need(!proof.reason,"eligible prefix failed original200 joint scalar check");for(int k=0;k<20;++k)controls[k].alpha[j]=u[k];}
 auto d=progressOnly(a,c,p,b,ranges,controls,std::forward<Emit>(emit));for(int j=0;j<7;++j){d.attempted[j]=1;d.selected[j]=133;d.pulse1[j]=controls[0].alpha[j];d.terminal_rate[j]=c.w[j]+.004*controls[0].alpha[j];}d.total_attempts+=7;return d;
}
inline void intersect(double&lower,double&upper,double w,int k,double offset){old::need(k==0||k==1,"two prefix cells only");old::need(offset==0&&std::isfinite(w),"free first14 alpha coordinates exact zero offset");const double l=k==0?(-w-.25e-6)/.004:-2.5e-5,u=k==0?(-w+.25e-6)/.004:2.5e-5;lower=std::max(lower,l);upper=std::min(upper,u);old::need(std::isfinite(lower)&&std::isfinite(upper)&&lower<upper,"empty causal two-command alpha intersection refused");}
template<class U,class W>void checkReturned(const U&u,const W&w){for(int j=0;j<7;++j){const double w1=w[j]+.004*u(j),w2=w1+.004*u(8+j);old::need(std::isfinite(w1)&&std::isfinite(w2)&&std::abs(w1)<=.25e-6&&std::abs(u(8+j))<=2.5e-5&&std::abs(w2)<=.35e-6,"actual returned native two-command contract refused; no clipping");}}
}
