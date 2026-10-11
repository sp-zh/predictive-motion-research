#include "runtime_observer.hpp"
#include <cmath>
#include <cstring>
#include <stdexcept>
#include <fstream>
#include <sstream>
#include <random>
#include <algorithm>
#include <predictive_motion_kinematics/robot_kinematics.hpp>
#include "geometry.hpp"
#include <yaml-cpp/yaml.h>
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
Simulation::~Simulation()=default;
const WarmupOutcome& Simulation::initializeAndWarmup(const WarmupSpec& spec){
 need(!warmup_.attempt_entered&&!failed_&&!terminated_&&!in_flight_&&facts_.observations==0&&facts_.step==0&&facts_.commits==0,"one bootstrap only before observations/prediction/commit");
 warmup_.attempt_entered=true;warmup_.seed=spec.seed;in_flight_=true;
 try{
  need(spec.seed==91011||spec.seed==91012,"declared development bootstrap seeds only");
  warmup_pins_=spec.dependencies;warmup_pins_.push_back(spec.feasible_csv);warmup_pins_.push_back(spec.robot_config);warmup_pins_.push_back(spec.geometry_config);warmup_pins_.push_back(spec.task_reference);
  auto pin=[](const live::FileIdentity& f){const auto q=live::observePinnedFile(f.path,f.sha256);need(q.bytes==f.bytes,"warmup input size changed");};for(const auto& f:warmup_pins_)pin(f);
  auto bound=[&](const std::string& path){return std::any_of(warmup_pins_.begin(),warmup_pins_.end(),[&](const auto& f){return f.path==path;});};
  auto definition=predictive_motion::loadConfig(spec.robot_config.path);need(bound(definition.urdf),"warmup selected URDF must be pinned");
  const auto geometry_config=YAML::LoadFile(spec.geometry_config.path);need(geometry_config["arm"].IsSequence()&&geometry_config["arm"].size()<=16,"bounded warmup arm primitives");for(const auto& arm:geometry_config["arm"])need(bound(arm["file"].as<std::string>()),"warmup convex asset must be pinned");
  const auto task=YAML::LoadFile(spec.task_reference.path);need(task["start"].size()==3&&task["quaternion_xyzw"].size()==4,"declared path initial pose shape");Eigen::Vector3d start;Eigen::Vector4d quat;for(int j=0;j<3;++j)start(j)=task["start"][j].as<double>();for(int j=0;j<4;++j)quat(j)=task["quaternion_xyzw"][j].as<double>();need(start.allFinite()&&quat.allFinite()&&std::abs(quat.norm()-1)<=1e-10,"finite task start pose");const auto desired=predictive_motion::poseFromXyzw(start,quat);
  warmup_robot_=std::make_unique<predictive_motion::RobotKinematics>(definition);warmup_geometry_=std::make_unique<predictive_motion::geometry::Scene>(spec.geometry_config.path);
  need(warmup_robot_->jointNames()==std::vector<std::string>({"fr3_joint1","fr3_joint2","fr3_joint3","fr3_joint4","fr3_joint5","fr3_joint6","fr3_joint7"}),"warmup kinematic coordinate order");
  std::ifstream csv(spec.feasible_csv.path);need(bool(csv),"warmup CSV open");std::string line;need(bool(std::getline(csv,line))&&bool(std::getline(csv,line))&&line.size()<4096,"warmup first data row only");std::istringstream cells(line);std::vector<double> values;
  while(std::getline(cells,line,',')){need(values.size()<128,"bounded CSV columns");std::size_t used=0;const double value=std::stod(line,&used);need(used==line.size()&&std::isfinite(value),"exact finite CSV field");values.push_back(value);}
  need(values.size()>=7,"CSV last7 joint values");std::mt19937 rng(spec.seed);
  for(int j=0;j<7;++j){const double q=values[values.size()-7+j]+(double(rng())/4294967295.-.5)*.0002;need(std::isfinite(q)&&q>model_->jnt_range[2*j]&&q<model_->jnt_range[2*j+1]&&q>=model_->actuator_ctrlrange[2*j]&&q<=model_->actuator_ctrlrange[2*j+1],"declared bootstrap q/control ranges");warmup_.declared_initial_q[j]=q;}
  warmup_.retained_points.reserve(1000);warmup_.stage="BEFORE_DECLARED_INITIAL_ASSIGNMENT";
  // One explicit bootstrap assignment, not a candidate or controller commit.
  for(int j=0;j<7;++j){state_->qpos[qpos_[j]]=warmup_.declared_initial_q[j];state_->qvel[dof_[j]]=0;state_->ctrl[actuators_[j]]=warmup_.declared_initial_q[j];C_[j]=warmup_.declared_initial_q[j];}
  ++facts_.forward;mj_forward(model_.get(),state_.get());warmup_.initial_assignment_completed=true;
  physical_=PhysicalHistory{};physical_.last_actual_velocity.fill(0);const double start_time=state_->time;
  const int integration_size=mj_stateSize(model_.get(),mjSTATE_INTEGRATION);need(integration_size>0&&integration_size<=65536,"bounded warmup observer integration state");std::vector<mjtNum> before(integration_size),after(integration_size);
  for(int i=0;i<1000;++i){
   warmup_.retained_points.emplace_back();auto& point=warmup_.retained_points.back();point.substep=i+1;point.C=C_;point.stage="BEFORE_IRREVERSIBLE_NATIVE_STEP";
   ++facts_.warmup_step_attempts;++facts_.step;mj_step(model_.get(),state_.get());++facts_.warmup_completed_steps;physical_.total_actual_substeps=facts_.warmup_completed_steps;
   point.stage="INDEPENDENT_ACTUAL_WARMUP_OBSERVATION";++facts_.get_state;mj_getState(model_.get(),state_.get(),before.data(),mjSTATE_INTEGRATION);++facts_.copy;need(mj_copyData(scratch_.get(),model_.get(),state_.get())==scratch_.get(),"warmup scratch copy");++facts_.forward;mj_forward(model_.get(),scratch_.get());
   point.simulation_time=scratch_->time;point.contacts=scratch_->ncon;for(int k=0;k<mjNWARNING;++k)point.warnings[k]=scratch_->warning[k].number;
   for(int j=0;j<7;++j){point.q[j]=scratch_->qpos[qpos_[j]];point.v[j]=scratch_->qvel[dof_[j]];need(std::isfinite(point.q[j])&&std::isfinite(point.v[j])&&scratch_->ctrl[actuators_[j]]==C_[j],"actual warmup finite encoder/held C");point.acceleration[j]=(point.v[j]-physical_.last_actual_velocity[j])/.002;if(physical_.acceleration_available)point.jerk[j]=(point.acceleration[j]-physical_.last_actual_acceleration[j])/.002;else point.jerk[j]=std::numeric_limits<double>::quiet_NaN();need(std::isfinite(point.acceleration[j])&&(!physical_.acceleration_available||std::isfinite(point.jerk[j])),"finite actual warmup acceleration/availablejerk");}
   point.jerk_available=physical_.acceleration_available;physical_.last_actual_velocity=point.v;physical_.last_actual_acceleration=point.acceleration;physical_.acceleration_available=true;physical_.source_id="WARMUP_"+epoch_+"_SUBSTEP_"+std::to_string(i+1);
   ++facts_.get_state;mj_getState(model_.get(),state_.get(),after.data(),mjSTATE_INTEGRATION);point.independent_observer_guard=bits(before,after);need(point.independent_observer_guard,"warmup scratch mutated integration state");
   point.stage="REAL_FULL_GEOMETRY_WARMUP_QUERY";const Eigen::Map<const Eigen::VectorXd> q(point.q.data(),7);const auto geometry=warmup_geometry_->query(*warmup_robot_,q,false,true);point.minimum_true=geometry.minimum_true;point.minimum_cover=geometry.minimum_cover;point.geometry_queries=geometry.queries.size();point.geometry_complete=std::isfinite(point.minimum_true)&&std::isfinite(point.minimum_cover)&&!geometry.queries.empty();need(point.geometry_complete,"complete finite true/cover warmup geometry");point.stage="COMPLETE_ACTUAL_2MS_WARMUP_POINT";
  }
  const auto& last=warmup_.retained_points.back();const Eigen::Map<const Eigen::VectorXd> final_q(last.q.data(),7);const auto actual_pose=warmup_robot_->tcpPose(final_q);warmup_.final_position_error=(actual_pose.translation()-start).norm();warmup_.final_rotation_error=predictive_motion::logResidual(actual_pose,desired).tail<3>().norm();need(std::isfinite(warmup_.final_position_error)&&std::isfinite(warmup_.final_rotation_error),"finite actual TCP start errors");need(std::abs(last.simulation_time-start_time-2.)<=1e-10,"actual1000steps/2second warmup clock");need(last.contacts==0&&std::min(last.minimum_true,last.minimum_cover)>=.005,"original warmup end contact/fullclearance gate");double speed=0;for(double v:last.v)speed=std::max(speed,std::abs(v));need(speed<=1e-4,"original warmup end measuredvelocity gate");
  for(const auto& f:warmup_pins_)pin(f);
  // Task cycle/command sequence remain0; actual physical warmupsteps/time are
  // explicit and separate. Fresh observer afterwards captures actual q/v.
  need(completed_.completed_tick==0&&completed_.completed_command_sequence==0&&s_==0&&r_==0,"bootstrap is not controller history advancement");warmup_.success=true;warmup_.stage="COMPLETE_DECLARED_ACTUAL_WARMUP_NO_TASK_COMMIT";in_flight_=false;
 }catch(const std::exception& e){warmup_.error=e.what();if(!warmup_.retained_points.empty())warmup_.retained_points.back().error=e.what();failed_=true;in_flight_=false;warmup_.stage="RETAINED_WARMUP_FAILURE_OR_PARTIAL_ADVANCEMENT";}catch(...){warmup_.error="unknown warmup failure";failed_=true;in_flight_=false;warmup_.stage="RETAINED_WARMUP_FAILURE_OR_PARTIAL_ADVANCEMENT";}
 return warmup_;
}
void Simulation::observe(Snapshot& out){
 need(!failed_&&!terminated_&&!in_flight_&&!out.complete&&out.stage=="NOT_STARTED","failed/inflight/reused observer attempt");
 facts_.observations=live::checkedAdd(facts_.observations,1);
 try{
  out.physical=physical_;out.owner_token=owner_token_;out.stage="INDEPENDENT_OBSERVER_BEFORE";const int n=mj_stateSize(model_.get(),mjSTATE_INTEGRATION);need(n>0&&n<=65536,"bounded integration observation");out.integration_before.resize(n);out.integration_after.resize(n);++facts_.get_state;mj_getState(model_.get(),state_.get(),out.integration_before.data(),mjSTATE_INTEGRATION);out.before_written=true;
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
void Simulation::verifyTermination(){need(!terminated_,"native simulation already terminated");terminated_=true;try{const auto f=live::observePinnedFile(xml_pin_.path,xml_pin_.sha256);need(f.bytes==xml_pin_.bytes,"native XML changed at termination");for(const auto& p:warmup_pins_){const auto q=live::observePinnedFile(p.path,p.sha256);need(q.bytes==p.bytes,"warmup input changed at termination");}termination_passed_=true;}catch(const std::exception& e){termination_failure_=e.what();throw;}catch(...){termination_failure_="unknown native termination failure";throw;}}
}
