#include "bootstrap_observer.hpp"
#include <cmath>
#include <cstring>
#include <stdexcept>
#include <utility>
namespace phase5_first_cycle_v1 {
namespace {void need(bool x,const char* why){if(!x)throw std::invalid_argument(why);}
bool exact(const std::vector<mjtNum>& a,const std::vector<mjtNum>& b){return a.size()==b.size()&&(a.empty()||std::memcmp(a.data(),b.data(),a.size()*sizeof(mjtNum))==0);}}
InitializedSimulation::InitializedSimulation(const std::string& epoch):epoch_(epoch){need(!epoch.empty()&&epoch.size()<=128,"pinned new source epoch required");}
void InitializedSimulation::initialize(const std::string& xml){
 need(!initialize_attempted_,"bootstrap already attempted; no retry");initialize_attempted_=true;
 try{
  static_assert(mjVERSION_HEADER==337,"reviewed MuJoCo3.3.7 header required");
  static_assert(sizeof(mjtNum)==8,"lossless double MuJoCo input required");
  char error[2048]{};++facts_.load_xml;model_.reset(mj_loadXML(xml.c_str(),nullptr,error,sizeof(error)));need(static_cast<bool>(model_),error);
  need(model_->nq==7&&model_->nv==7&&model_->nu==7&&model_->neq==0&&model_->opt.timestep==.002,"exact current native profile shape/clock");
  ++facts_.make_data;state_.reset(mj_makeData(model_.get()));need(static_cast<bool>(state_),"native integration data allocation failed");
  ++facts_.make_data;scratch_.reset(mj_makeData(model_.get()));need(static_cast<bool>(scratch_),"native observer data allocation failed");
  ++facts_.key_name_queries;const int home=mj_name2id(model_.get(),mjOBJ_KEY,"home");need(home>=0,"pinned home keyframe required; no fallback reset");
  ++facts_.reset_keyframe;mj_resetDataKeyframe(model_.get(),state_.get(),home);
  for(int j=0;j<7;++j){const auto name="fr3_joint"+std::to_string(j+1);++facts_.joint_name_queries;
   const int id=mj_name2id(model_.get(),mjOBJ_JOINT,name.c_str());need(id>=0&&model_->jnt_type[id]==mjJNT_HINGE,"real scalar joint map required");
   joints_[j]=id;qpos_[j]=model_->jnt_qposadr[id];dof_[j]=model_->jnt_dofadr[id];need(qpos_[j]==j&&dof_[j]==j,"fixed profile coordinate order");
   int actuator=-1;for(int a=0;a<model_->nu;++a)if(model_->actuator_trntype[a]==mjTRN_JOINT&&model_->actuator_trnid[2*a]==id){need(actuator<0,"duplicate actual actuator mapping");actuator=a;}
   need(actuator==j,"fixed profile actual actuator order required");actuators_[j]=actuator;
  }
  ++facts_.forward;mj_forward(model_.get(),state_.get());need(state_->time==0,"initialization must not advance simulation");facts_.initialized=true;
 }catch(const std::exception& e){facts_.first_error=e.what();throw;}
}
void InitializedSimulation::observe(Snapshot& out){
 need(facts_.initialized&&observations_<2,"exact two current observer attempts required; no retry");++observations_;
 need(!out.complete&&out.stage=="NOT_OBSERVED","snapshot container already used");
 try{out.stage="READ_ACTUAL_INTEGRATION_BEFORE";out.epoch=epoch_;out.source="CURRENT_NATIVE_KEYFRAME_BOOTSTRAP_NO_COMMITS";
 ++facts_.state_size;const int n=mj_stateSize(model_.get(),mjSTATE_INTEGRATION);need(n>0&&n<=65536,"bounded actual integration state");
 out.integration_before.resize(n);out.integration_after.resize(n);
 ++facts_.get_state;mj_getState(model_.get(),state_.get(),out.integration_before.data(),mjSTATE_INTEGRATION);out.integration_before_written=true;
 out.stage="FORWARD_INDEPENDENT_NATIVE_SCRATCH";++facts_.copy_data;need(mj_copyData(scratch_.get(),model_.get(),state_.get())==scratch_.get(),"independent native data copy failed");
 ++facts_.forward;mj_forward(model_.get(),scratch_.get());out.capture=std::chrono::steady_clock::now();
 out.stage="READ_ACTUAL_MAPPED_COORDINATES_CTRL";for(int j=0;j<7;++j){out.actual.q[j]=scratch_->qpos[qpos_[j]];out.actual.v[j]=scratch_->qvel[dof_[j]];out.actual.C[j]=scratch_->ctrl[actuators_[j]];
  need(std::isfinite(out.actual.q[j])&&std::isfinite(out.actual.v[j])&&std::isfinite(out.actual.C[j]),"nonfinite actual native observation");
  out.joints_read=j+1;out.actual.w[j]=0; // Explicit keyframe-bootstrap history policy, not measured two-commit derivative.
 }
 out.actual.s=0;out.actual.r=0;out.contacts=scratch_->ncon;out.simulation_time=scratch_->time;
 out.stage="READ_ACTUAL_INTEGRATION_AFTER";++facts_.get_state;mj_getState(model_.get(),state_.get(),out.integration_after.data(),mjSTATE_INTEGRATION);out.integration_after_written=true;
 need(exact(out.integration_before,out.integration_after)&&out.simulation_time==0,"observer mutated frozen integration boundary");
 need(out.contacts==0,"actual initialized contact-free boundary required");out.complete=true;out.stage="COMPLETE_UNCHANGED_NATIVE_BOOTSTRAP_OBSERVATION";
 }catch(const std::exception& e){out.first_error=e.what();facts_.first_error=e.what();throw;}
}
bool InitializedSimulation::sameBoundary(const Snapshot& a,const Snapshot& b) const{
 return a.complete&&b.complete&&a.epoch==epoch_&&b.epoch==epoch_&&a.source==b.source&&a.simulation_time==b.simulation_time&&
 a.contacts==b.contacts&&exact(a.integration_before,b.integration_before)&&exact(a.integration_after,b.integration_after)&&
 a.actual.q==b.actual.q&&a.actual.v==b.actual.v&&a.actual.C==b.actual.C&&a.actual.w==b.actual.w&&a.actual.s==b.actual.s&&a.actual.r==b.actual.r;
}
live::LiveActualContext makeContext(const Snapshot& actual,const live::State30& expected_anchor,const live::StaticDomainRanges& ranges,double& recorded_age){
 need(actual.complete,"actual completed observer snapshot required");
 const live::BoundaryId boundary{0,0};const std::string observation="INITIALIZATION_OBSERVATION_"+actual.epoch,transaction="INITIALIZATION_COMPLETED_"+actual.epoch;
 live::ObservedActual observed;observed.q=actual.actual.q;observed.v=actual.actual.v;observed.boundary=boundary;
 observed.observation_id=observation;observed.transaction_id=transaction;observed.completed=true;observed.current_contact_free=actual.contacts==0;
 recorded_age=std::chrono::duration<double>(std::chrono::steady_clock::now()-actual.capture).count();observed.state_age_seconds=recorded_age;
 live::AcceptedCommandHistory command;command.C=actual.actual.C;command.w=actual.actual.w;command.previous_alpha={};
 command.boundary=boundary;command.observation_id=observation;command.transaction_id=transaction;command.completed=true;
 live::ProgressHistory progress;progress.s=actual.actual.s;progress.r=actual.actual.r;progress.previous_b=0;
 progress.boundary=boundary;progress.observation_id=observation;progress.transaction_id=transaction;progress.completed=true;
 live::NominalAnchor anchor{expected_anchor,boundary};live::CurrentBoundaryExpectation current;
 current.boundary=boundary;current.observation_id=observation;current.transaction_id=transaction;current.no_command_in_flight=true;current.maximum_age_seconds=.004;
 // completed tick/sequence0 records real source initialization, not a prior step
 // or accepted controller commit. Only actual ctrl is the initial command target.
 return live::validateLiveActual(observed,command,progress,anchor,current,ranges);
}
}
