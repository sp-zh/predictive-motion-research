#pragma once
#include "session_primitives.hpp"
#include "public_coupled_augmented_model.hpp"
#include <Eigen/Core>
#include <cmath>
#include <chrono>
#include <cstring>
#include <limits>
#include <stdexcept>
#include <string>
#include <array>
namespace phase5_dynamic_cycle_support_v1 {
namespace live=phase5_active_session_v1;
inline void need(bool b,const char* msg){if(!b)throw std::invalid_argument(msg);}
inline bool bits(double a,double b){return std::memcmp(&a,&b,sizeof(double))==0;}
struct Envelope {live::Count maximum_commits=3,maximum_forecasts=6,maximum_task_substeps=6;live::Count output_bytes=768ULL*1024*1024,global_journal_bytes=48ULL*1024*1024;live::Count separate_numeric_slots=48000000;live::Count provider_scene=1400,provider_primitives=20000000,provider_fk=40000,provider_jac=20000;double cycle_deadline_s=.004;};
class Ledger {Envelope e_;live::Count commits_=0,forecasts_=0,steps_=0,bytes_=0,journal_=0,actual_slots_last_=0,separate_numeric_=0;public:explicit Ledger(const Envelope& e):e_(e){need(e.maximum_commits>0&&e.maximum_commits<=128&&e.maximum_forecasts==2*e.maximum_commits&&e.maximum_task_substeps==2*e.maximum_commits&&e.cycle_deadline_s==.004&&e.output_bytes>0&&e.output_bytes<=16640ULL*1024*1024&&e.global_journal_bytes>0&&e.global_journal_bytes<=128ULL*1024*1024&&e.separate_numeric_slots>0&&e.separate_numeric_slots<=1200000000&&e.provider_scene>0&&e.provider_scene<=51600&&e.provider_primitives>0&&e.provider_primitives<=470000000&&e.provider_fk>0&&e.provider_fk<=800000&&e.provider_jac>0&&e.provider_jac<=800000,"declared finite session envelope through128");}
 void beforeForecast(){need(forecasts_<e_.maximum_forecasts,"cumulative genuine forecast cap");++forecasts_;}
 void beforeStep(){need(steps_<e_.maximum_task_substeps,"cumulative native taskstep attempt cap");++steps_;}
 void completedCommit(){need(commits_<e_.maximum_commits,"cumulative completed commit cap");++commits_;}
 void sourceSlots(live::Count actual){need(actual>=actual_slots_last_,"original Session cumulative charge must never reset");actual_slots_last_=actual;}
 void reserveNumeric(live::Count n){need(separate_numeric_<=e_.separate_numeric_slots&&n<=e_.separate_numeric_slots-separate_numeric_,"cumulative separate logical numeric charge before allocation");separate_numeric_=live::checkedAdd(separate_numeric_,n);}
 void reserveBytes(live::Count n,bool journal){auto& spent=journal?journal_:bytes_;const auto cap=journal?e_.global_journal_bytes:e_.output_bytes;need(spent<=cap&&n<=cap-spent,"global retained output budget before write");spent=live::checkedAdd(spent,n);}
 live::Count commits()const{return commits_;}live::Count forecasts()const{return forecasts_;}live::Count steps()const{return steps_;}live::Count separateNumericSlots()const{return separate_numeric_;}live::Count originalSlots()const{return actual_slots_last_;}
};
struct ProgressPoint {double s=0,r=0;};
inline ProgressPoint cellReference(double s,double r,double b,int zero_based_cycle,int half){need(zero_based_cycle>=0&&(half==1||half==2),"fixed progress clock support");const double t=.004*zero_based_cycle+.002*half;ProgressPoint x{s+t*r+.5*t*t*b,r+t*b};need(std::isfinite(x.s)&&std::isfinite(x.r)&&x.s>=0&&x.s<=1&&x.r>=0&&x.r<=.2,"original nonlinear progress reference domain");return x;}
inline Eigen::VectorXd deltaControl(const phase5_public_coupled_augmented::Cell& candidate,const phase5_public_coupled_augmented::Cell& nominal){need(candidate.cycles==nominal.cycles&&candidate.alpha.size()==7&&nominal.alpha.size()==7&&candidate.alpha.allFinite()&&nominal.alpha.allFinite()&&std::isfinite(candidate.b)&&std::isfinite(nominal.b),"genuine same-lattice nominal/candidate controls");Eigen::VectorXd u(8);u.head<7>()=candidate.alpha-nominal.alpha;u(7)=candidate.b-nominal.b;return u;}
struct HintBinding {live::State30 initial;live::JointVector previous_alpha{};double previous_b=0;live::BoundaryId boundary;std::string nominal_digest,problem_digest,row_roster_digest,support_digest;};
inline bool sameBinding(const HintBinding& a,const HintBinding& b){if(a.boundary.completed_tick!=b.boundary.completed_tick||a.boundary.completed_command_sequence!=b.boundary.completed_command_sequence||a.nominal_digest!=b.nominal_digest||a.problem_digest!=b.problem_digest||a.row_roster_digest!=b.row_roster_digest||a.support_digest!=b.support_digest)return false;for(int j=0;j<7;++j)if(!bits(a.initial.q[j],b.initial.q[j])||!bits(a.initial.v[j],b.initial.v[j])||!bits(a.initial.C[j],b.initial.C[j])||!bits(a.initial.w[j],b.initial.w[j])||!bits(a.previous_alpha[j],b.previous_alpha[j]))return false;return bits(a.initial.s,b.initial.s)&&bits(a.initial.r,b.initial.r)&&bits(a.previous_b,b.previous_b);}
enum class Stage {Observe,NominalMaps,GeometryAssembly,Solve,ValueValidation,CommitJournal,Count};
struct Timings {std::array<double,static_cast<int>(Stage::Count)> seconds;std::array<bool,static_cast<int>(Stage::Count)> measured{};double complete_cycle_s=std::numeric_limits<double>::quiet_NaN();bool complete=false,deadline_missed=false;Timings(){seconds.fill(std::numeric_limits<double>::quiet_NaN());}};
class CycleClock {using Clock=std::chrono::steady_clock;Clock::time_point start_=Clock::now();Timings& out_;public:explicit CycleClock(Timings& out):out_(out){need(!out.complete,"new cycle timing owner");}Clock::time_point begin()const{return Clock::now();}void end(Stage stage,const Clock::time_point& begin){const auto i=static_cast<int>(stage);need(i>=0&&i<static_cast<int>(Stage::Count)&&!out_.measured[i],"one measured segment per cycle");out_.seconds[i]=std::chrono::duration<double>(Clock::now()-begin).count();out_.measured[i]=true;}void finish(){need(!out_.complete,"cycle timing cannot restart/refresh");out_.complete_cycle_s=std::chrono::duration<double>(Clock::now()-start_).count();out_.complete=true;out_.deadline_missed=out_.complete_cycle_s>.004;}};
}
