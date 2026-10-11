#include <cstdint>
#include <limits>
#include <stdexcept>
#include <string>
#include <iostream>
namespace phase5_active_session_v1 {using Count=std::uint64_t;
Count checkedAdd(Count a, Count b) {
  if (b > std::numeric_limits<Count>::max() - a)
    throw std::overflow_error("integer shape addition overflow");
  return a + b;
}

}
namespace phase5_dynamic_cycle_support_v1 {namespace live=phase5_active_session_v1;
inline void need(bool b,const char* msg){if(!b)throw std::invalid_argument(msg);}
struct Envelope {live::Count maximum_commits=3,maximum_forecasts=6,maximum_task_substeps=6,maximum_trials_per_commit=1;live::Count output_bytes=768ULL*1024*1024,global_journal_bytes=48ULL*1024*1024;live::Count separate_numeric_slots=48000000;live::Count provider_scene=1400,provider_primitives=20000000,provider_fk=40000,provider_jac=20000;double cycle_deadline_s=.004;};
class Ledger {Envelope e_;live::Count commits_=0,forecasts_=0,steps_=0,bytes_=0,journal_=0,actual_slots_last_=0,separate_numeric_=0,trials_=0,trial_boundary_=std::numeric_limits<live::Count>::max(),trial_next_=0;public:explicit Ledger(const Envelope& e):e_(e){need(e.maximum_commits>0&&e.maximum_commits<=128&&e.maximum_trials_per_commit>0&&e.maximum_trials_per_commit<=3&&e.maximum_forecasts==2*e.maximum_commits*e.maximum_trials_per_commit&&e.maximum_task_substeps==2*e.maximum_commits&&e.cycle_deadline_s==.004&&e.output_bytes>0&&e.output_bytes<=25088ULL*1024*1024&&e.global_journal_bytes>0&&e.global_journal_bytes<=128ULL*1024*1024&&e.separate_numeric_slots>0&&e.separate_numeric_slots<=1800000000&&e.provider_scene>0&&e.provider_scene<=78000&&e.provider_primitives>0&&e.provider_primitives<=700000000&&e.provider_fk>0&&e.provider_fk<=1100000&&e.provider_jac>0&&e.provider_jac<=1100000,"declared finite session envelope through128");}
 void beforeTrial(live::Count boundary,live::Count trial){need(boundary==commits_&&trial<e_.maximum_trials_per_commit&&trials_<e_.maximum_commits*e_.maximum_trials_per_commit,"bounded new current trial before any forecast");if(boundary!=trial_boundary_){need(trial==0,"new current boundary trial starts zero");trial_boundary_=boundary;trial_next_=0;}need(trial==trial_next_,"fresh ordered current trial ID");++trial_next_;++trials_;}
 live::Count trials()const{return trials_;}
 void beforeForecast(){need(forecasts_<e_.maximum_forecasts,"cumulative genuine forecast cap");++forecasts_;}
 void beforeStep(){need(steps_<e_.maximum_task_substeps,"cumulative native taskstep attempt cap");++steps_;}
 void completedCommit(){need(commits_<e_.maximum_commits,"cumulative completed commit cap");++commits_;}
 void sourceSlots(live::Count actual){need(actual>=actual_slots_last_,"original Session cumulative charge must never reset");actual_slots_last_=actual;}
 void reserveNumeric(live::Count n){need(separate_numeric_<=e_.separate_numeric_slots&&n<=e_.separate_numeric_slots-separate_numeric_,"cumulative separate logical numeric charge before allocation");separate_numeric_=live::checkedAdd(separate_numeric_,n);}
 void reserveBytes(live::Count n,bool journal){auto& spent=journal?journal_:bytes_;const auto cap=journal?e_.global_journal_bytes:e_.output_bytes;need(spent<=cap&&n<=cap-spent,"global retained output budget before write");spent=live::checkedAdd(spent,n);}
 live::Count commits()const{return commits_;}live::Count forecasts()const{return forecasts_;}live::Count steps()const{return steps_;}live::Count separateNumericSlots()const{return separate_numeric_;}live::Count originalSlots()const{return actual_slots_last_;}
};

}
struct Feedback{bool success=false;std::string error;};
int main(){using namespace phase5_dynamic_cycle_support_v1;
 for(const char* point:{"receipt_write","actual_commit_write","after_observe","timing_manifest"}){
  Envelope envelope;envelope.maximum_commits=64;envelope.maximum_trials_per_commit=3;envelope.maximum_forecasts=384;envelope.maximum_task_substeps=128;Ledger ledger(envelope);
  ledger.beforeTrial(0,0);ledger.beforeForecast();ledger.beforeForecast();ledger.beforeStep();ledger.beforeStep();
  Feedback committed{true,{}};bool physical_commit_completed=false;std::string error;
  try{if(committed.success&&committed.error.empty()){physical_commit_completed=true;ledger.completedCommit();}throw std::runtime_error(point);}catch(const std::exception& e){error=e.what();}
  const bool final_package_pass=error.empty()&&committed.success&&committed.error.empty();
  if(!physical_commit_completed||ledger.commits()!=1||ledger.steps()!=2||ledger.forecasts()!=2||ledger.trials()!=1||error!=point||final_package_pass)return 1;
  std::cout<<point<<" physical_success=1 completedCommit=1 steps=2 forecasts=2 trials=1 final_package_pass=0 error="<<error<<"\n";
 }
 {Envelope envelope;Ledger ledger(envelope);Feedback committed{false,"partial C failure"};bool physical_commit_completed=false;
  if(committed.success&&committed.error.empty()){physical_commit_completed=true;ledger.completedCommit();}
  if(physical_commit_completed||ledger.commits()!=0)return 2;
 }
 std::cout<<"PASS actual-source Ledger/latch fault injection; no full entry/Model/OSQP/physics execution\n";return 0;
}
