#include "runtime_observer.hpp"
#include <cmath>
#include <cstring>
#include <stdexcept>
namespace phase5_active_session_runtime_v1 {
namespace {void need(bool c,const char* why){if(!c)throw std::invalid_argument(why);}
bool bits(const std::vector<mjtNum>& a,const std::vector<mjtNum>& b){return a.size()==b.size()&&(a.empty()||std::memcmp(a.data(),b.data(),a.size()*sizeof(mjtNum))==0);}}
Simulation::Simulation(const live::FileIdentity& xml,const std::string& epoch):epoch_(epoch),xml_pin_(xml){
 static_assert(mjVERSION_HEADER==337&&sizeof(mjtNum)==8,"fixed MuJoCo ABI");
 need(!epoch.empty()&&epoch.size()<=128,"bounded current simulation epoch required");
 for(unsigned char c:epoch) need(c>=33&&c<=126,"printable epoch identity required");
 const auto file=live::observePinnedFile(xml.path,xml.sha256);need(file.bytes==xml.bytes,"native XML size changed");
 char error[2048]{};++facts_.load_xml;model_.reset(mj_loadXML(xml.path.c_str(),nullptr,error,sizeof(error)));need(bool(model_),error);
 need(model_->nq==7&&model_->nv==7&&model_->nu==7&&model_->neq==0&&model_->opt.timestep==.002,"fixed native shape/2ms clock");
 ++facts_.make_data;state_.reset(mj_makeData(model_.get()));need(bool(state_),"native integration allocation");
 ++facts_.make_data;scratch_.reset(mj_makeData(model_.get()));need(bool(scratch_),"independent scratch allocation");
 const int key=mj_name2id(model_.get(),mjOBJ_KEY,"home");need(key>=0,"declared home initialization required");
 ++facts_.reset;mj_resetDataKeyframe(model_.get(),state_.get(),key);
 for(int j=0;j<7;++j){const std::string name="fr3_joint"+std::to_string(j+1);const int joint=mj_name2id(model_.get(),mjOBJ_JOINT,name.c_str());need(joint>=0&&model_->jnt_type[joint]==mjJNT_HINGE,"native scalar joint mapping");qpos_[j]=model_->jnt_qposadr[joint];dof_[j]=model_->jnt_dofadr[joint];need(qpos_[j]==j&&dof_[j]==j,"fixed native coordinate order");int actuator=-1;for(int a=0;a<model_->nu;++a)if(model_->actuator_trntype[a]==mjTRN_JOINT&&model_->actuator_trnid[2*a]==joint){need(actuator<0,"duplicate actuator mapping");actuator=a;}need(actuator==j,"fixed actual actuator mapping");actuators_[j]=actuator;C_[j]=state_->ctrl[actuator];need(std::isfinite(C_[j]),"nonfinite bootstrap accepted target");}
 ++facts_.forward;mj_forward(model_.get(),state_.get());need(state_->time==0,"home initialization advanced simulation");
 const auto end=live::observePinnedFile(xml.path,xml.sha256);need(end.bytes==file.bytes,"native XML changed across parse");
}
void Simulation::observe(Snapshot& out){
 need(!failed_&&!terminated_&&!in_flight_&&!out.complete&&out.stage=="NOT_STARTED","failed/inflight/reused observer attempt");
 facts_.observations=live::checkedAdd(facts_.observations,1);
 try{
  out.owner_token=owner_token_;out.stage="INDEPENDENT_OBSERVER_BEFORE";const int n=mj_stateSize(model_.get(),mjSTATE_INTEGRATION);need(n>0&&n<=65536,"bounded integration observation");out.integration_before.resize(n);out.integration_after.resize(n);++facts_.get_state;mj_getState(model_.get(),state_.get(),out.integration_before.data(),mjSTATE_INTEGRATION);out.before_written=true;
  ++facts_.copy;need(mj_copyData(scratch_.get(),model_.get(),state_.get())==scratch_.get(),"native scratch copy failed");++facts_.forward;mj_forward(model_.get(),scratch_.get());
  out.capture=std::chrono::steady_clock::now();out.stage="ACTUAL_ENCODER_AND_OWNED_HISTORY";
  const std::string observation="OBS_"+epoch_+"_"+std::to_string(facts_.observations),transaction="TX_"+epoch_+"_"+std::to_string(completed_.completed_command_sequence);
  auto& o=out.observed;o.boundary=completed_;o.observation_id=observation;o.transaction_id=transaction;o.current_contact_free=scratch_->ncon==0;
  for(int j=0;j<7;++j){o.q[j]=scratch_->qpos[qpos_[j]];o.v[j]=scratch_->qvel[dof_[j]];need(std::isfinite(o.q[j])&&std::isfinite(o.v[j])&&scratch_->ctrl[actuators_[j]]==C_[j],"nonfinite encoder or accepted target differs from native ctrl");out.joints_read=j+1;}
  out.command.C=C_;out.command.w=w_;out.command.previous_alpha=previous_alpha_;out.command.boundary=completed_;out.command.observation_id=observation;out.command.transaction_id=transaction;
  out.progress.s=s_;out.progress.r=r_;out.progress.previous_b=previous_b_;out.progress.boundary=completed_;out.progress.observation_id=observation;out.progress.transaction_id=transaction;
  out.contacts=scratch_->ncon;out.simulation_time=scratch_->time;
  out.stage="INDEPENDENT_OBSERVER_AFTER";++facts_.get_state;mj_getState(model_.get(),state_.get(),out.integration_after.data(),mjSTATE_INTEGRATION);out.after_written=true;need(bits(out.integration_before,out.integration_after),"scratch observer changed integration state");need(out.contacts==0,"current observed contact");need(out.simulation_time==state_->time,"scratch/current clock mismatch");
  o.completed=true;out.command.completed=true;out.progress.completed=true;out.complete=true;out.stage="COMPLETE_CURRENT_NATIVE_BOUNDARY";out.observed.state_age_seconds=ageSeconds(out);
 }catch(const std::exception& e){out.error=e.what();failed_=true;throw;}
}
double Simulation::ageSeconds(const Snapshot& out) const{need(out.complete,"incomplete observation");return std::chrono::duration<double>(std::chrono::steady_clock::now()-out.capture).count();}
live::CurrentBoundaryExpectation Simulation::current(const Snapshot& out,ObservationClock clock) const{
 need(out.complete&&out.owner_token==owner_token_&&!failed_&&!terminated_&&!in_flight_&&out.observed.observation_id=="OBS_"+epoch_+"_"+std::to_string(facts_.observations)&&out.observed.boundary.completed_tick==completed_.completed_tick&&out.observed.boundary.completed_command_sequence==completed_.completed_command_sequence,"not current completed snapshot");
 need(out.simulation_time==state_->time,"snapshot simulation boundary advanced");
 if(clock==ObservationClock::OnlineWallAge)need(ageSeconds(out)<=.004,"current native observer stale at online use");
 else need(clock==ObservationClock::OfflineFrozenSimulationBoundary,"unknown observation clock mode");
 live::CurrentBoundaryExpectation c;c.boundary=completed_;c.observation_id=out.observed.observation_id;c.transaction_id=out.observed.transaction_id;c.maximum_age_seconds=.004;c.no_command_in_flight=true;return c;
}
void Simulation::verifyTermination(){need(!terminated_,"native simulation already terminated");terminated_=true;try{const auto f=live::observePinnedFile(xml_pin_.path,xml_pin_.sha256);need(f.bytes==xml_pin_.bytes,"native XML changed at termination");termination_passed_=true;}catch(const std::exception& e){termination_failure_=e.what();throw;}catch(...){termination_failure_="unknown native termination failure";throw;}}
}
