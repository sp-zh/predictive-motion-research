#include "runtime_observer.hpp"
#include "lossless_evidence.hpp"
#include "task_local_provider.hpp"
#include <predictive_motion_kinematics/robot_kinematics.hpp>
#include <yaml-cpp/yaml.h>
#include <chrono>
#include <fstream>
#include <iostream>
#include <memory>
#include <cstring>
namespace live=phase5_active_session_v1;namespace core=phase5_active_session_qp_v1;
namespace rt=phase5_active_session_runtime_v1;namespace evidence=phase5_active_evidence_v1;
namespace {
void need(bool b,const char* s){if(!b)throw std::invalid_argument(s);}
live::FileIdentity identity(const YAML::Node& n){return {n["path"].as<std::string>(),n["sha256"].as<std::string>(),n["bytes"].as<live::Count>()};}
void pin(const live::FileIdentity& i){auto actual=live::observePinnedFile(i.path,i.sha256);need(actual.bytes==i.bytes,"active input size mismatch");}
Eigen::Vector3d vec3(const YAML::Node& n){need(n.IsSequence()&&n.size()==3,"three-vector");return {n[0].as<double>(),n[1].as<double>(),n[2].as<double>()};}
bool bits(const std::vector<mjtNum>& a,const std::vector<mjtNum>& b){return a.size()==b.size()&&(a.empty()||std::memcmp(a.data(),b.data(),a.size()*sizeof(mjtNum))==0);}
}
int main(int argc,char** argv){
 std::string stage="BEFORE_ACTIVE_INPUT",error;std::unique_ptr<evidence::Evidence> out;std::unique_ptr<rt::Simulation> simulation;std::unique_ptr<live::Session> session;rt::Snapshot before,after;bool boundary_same=false,termination_pass=false,before_write_attempted=false,after_write_attempted=false;
 const auto start=std::chrono::steady_clock::now();
 try{
  need(argc==5,"active input path/hash, new producer SHA and fresh output directory required");
  live::observePinnedFile(argv[1],argv[2]);const auto input=YAML::LoadFile(argv[1]);need(input["schema"].as<std::string>()=="ACTIVE_SESSION_OFFLINE_A_DEV_INPUT_V1","new active input schema required");
  need(input["timing_mode"].as<std::string>()=="OFFLINE_FROZEN_SIMULATION_BOUNDARY","this entry is offline only");
  out=std::make_unique<evidence::Evidence>(argv[4]);stage="ACTIVE_PINNED_INPUTS";
  live::SessionPins pins;pins.producer=live::observeCurrentProducerElf(argv[3]);pins.producer.path=std::filesystem::canonical("/proc/self/exe").string();pins.xml=identity(input["xml"]);pins.constants=identity(input["constants"]);pins.expected_metadata=identity(input["expected_metadata"]);pins.session_id=input["session_id"].as<std::string>();
  for(const auto& n:input["dependencies"]) {pins.dependencies.push_back(identity(n));}
  for(const auto& n:input["loaded_libraries"]) {pins.loaded_libraries.push_back(identity(n));}
  const auto robot_config=identity(input["robot_config"]),reference=identity(input["task_reference"]);pin(robot_config);pin(reference);
  auto bound=[&](const live::FileIdentity& x){for(const auto& d:pins.dependencies)if(d.path==x.path&&d.bytes==x.bytes&&d.sha256==x.sha256)return true;return false;};
  need(bound(robot_config)&&bound(reference),"task/robot config must belong to session pinned dependencies");
  stage="OWNED_NATIVE_BOOTSTRAP";simulation=std::make_unique<rt::Simulation>(pins.xml,pins.session_id);simulation->observe(before);before_write_attempted=true;out->snapshot("observation_before.bin",before);
  stage="REAL_TASK_KINEMATICS";auto robot_definition=predictive_motion::loadConfig(robot_config.path);
  bool urdf_bound=false;for(const auto& d:pins.dependencies)if(d.path==robot_definition.urdf){pin(d);urdf_bound=true;}need(urdf_bound,"selected URDF must belong to session dependencies");
  predictive_motion::RobotKinematics robot(robot_definition);
  const auto task=YAML::LoadFile(reference.path);core::WorldTaskPath path;path.start=vec3(task["start"]);path.end=vec3(task["end"]);for(int i=0;i<4;++i)path.quaternion_xyzw(i)=task["quaternion_xyzw"][i].as<double>();path.lateral_amplitude=task["lateral_amplitude"].as<double>();path.vertical_amplitude=task["vertical_amplitude"].as<double>();
  stage="SESSION_STARTUP_MODEL_METADATA_SDK";session=std::make_unique<live::Session>(pins);out->modelOpen(*session);need(robot.jointNames()==session->verifiedMetadata().joint_names,"actual task/Model joint coordinate order mismatch");
  if(input["termination_probe"]&&input["termination_probe"].as<bool>()){
   const auto marker=identity(input["termination_probe_marker"]);need(bound(marker),"termination probe marker must be pinned");
   need(std::filesystem::path(marker.path).parent_path()==std::filesystem::path(argv[4]).parent_path(),"probe writes restricted to fresh attempt directory");
   stage="DELIBERATE_NEW_DEPENDENCY_TERMINATION_DRIFT";
   {std::ofstream changed(marker.path,std::ios::binary|std::ios::trunc);changed.exceptions(std::ios::failbit|std::ios::badbit);changed<<"AFTER_DELIBERATE_TEST_DRIFT_V1\n";}
   bool refused=false;try{session->verifyTermination();}catch(const std::exception&){refused=true;}
   need(refused&&!session->terminationVerified()&&!session->terminationFailure().empty(),"termination drift must latch failure");
   const auto first_failure=session->terminationFailure();
   bool forecast_denied=false;try{session->forecast({}, {}, {}, {}, std::vector<live::NominalControl>(core::N));}catch(const std::invalid_argument& e){forecast_denied=std::string(e.what())=="inactive session";}
   need(forecast_denied,"failed termination must deny forecast before native entry");
   bool repeated_denied=false;try{session->verifyTermination();}catch(const std::invalid_argument&){repeated_denied=true;}
   need(repeated_denied&&session->terminationFailure()==first_failure,"repeat termination must preserve first failure");
   out->write("termination_probe.bin","EXPECTED_NEW_DEPENDENCY_DRIFT_REGRESSION",[&](evidence::BinaryFile& f){f.u64(refused);f.u64(forecast_denied);f.u64(repeated_denied);f.text(first_failure);f.u64(0);});
   simulation->observe(after);out->snapshot("observation_after.bin",after);out->bootstrap(simulation->facts());simulation->verifyTermination();
   need(bits(before.integrationBefore(),after.integrationBefore())&&simulation->terminationVerified(),"probe must not modify native state/immutable XML");
   out->finish("PASS_EXPECTED_TERMINATION_FAILURE_NO_NOMINAL", "", true);
   std::cout<<"termination_probe=PASS expected_failure="<<first_failure<<" nominal=0 steps=0 commits=0 phase5=NOT_ACCEPTED\n";return 0;
  }
  stage="GENUINE_CURRENT_NOMINAL";std::vector<live::NominalControl> controls(core::N);
  auto forecast=session->forecast(before.actualObservation(),before.acceptedHistory(),before.progressHistory(),simulation->current(before,rt::ObservationClock::OfflineFrozenSimulationBoundary),controls);
  out->rawForecast(forecast); // full original data emitted BEFORE normalization/affine/core entry
  core::Inputs inputs;inputs.task=core::bindTaskLinearizer(robot,path,input["task_source_id"].as<std::string>());inputs.objective_source_id=input["task_source_id"].as<std::string>();for(int j=0;j<7;++j){inputs.limits.physical_speed[j]=input["physical_speed"][j].as<double>();inputs.weights.posture_reference[j]=before.actualObservation().q[j];}
  inputs.observed_age_seconds=before.actualObservation().state_age_seconds;inputs.known_upstream_elapsed_seconds=std::chrono::duration<double>(std::chrono::steady_clock::now()-before.captureTime()).count()-inputs.observed_age_seconds;inputs.timing_mode=core::TimingMode::OfflineFrozenSimulationBoundary;inputs.simulation_boundary_asserted_frozen=true;
  stage="ACTUAL_FULL_INLINE_QP";auto connected=core::connect(std::move(forecast),inputs);out->integration(connected);
  const auto options_node=input["solver"];predictive_motion::control::QpOptions options;options.max_iterations=options_node["max_iterations"].as<int>();options.absolute_tolerance=options_node["absolute_tolerance"].as<double>();options.relative_tolerance=options_node["relative_tolerance"].as<double>();options.acceptance_tolerance=options_node["acceptance_tolerance"].as<double>();options.time_limit_seconds=options_node["time_limit_seconds"].as<double>();options.max_state_age_seconds=options_node["max_state_age_seconds"].as<double>();options.initial_rho=options_node["initial_rho"].as<double>();
  need(options.max_iterations==4000&&options.absolute_tolerance==1e-9&&options.relative_tolerance==1e-9&&options.acceptance_tolerance==1e-7&&options.time_limit_seconds==5&&options.max_state_age_seconds==.05&&options.initial_rho==.1,"exact active offline budget; unchanged tolerances/iteration count/rho");
  stage="ONE_ACTIVE_OFFLINE_SOLVER";core::CandidateOutcome candidate;core::solveOnce(connected,options,candidate);out->candidate(candidate);out->write("solver_row_screen.bin","ORIGINAL_SI_INPUT_BOX_IMPLICATION_SCREEN",[&](evidence::BinaryFile& f){f.text("outward-long-double-box-interval-v1; retainall160inputboxes/equalities; independentlycheckalloriginalSIrows");f.u64(candidate.retainedSolverRows().size());for(int r:candidate.retainedSolverRows())f.u64(r);f.u64(candidate.omittedSolverRows().size());for(int r:candidate.omittedSolverRows())f.u64(r);f.u64(candidate.omittedSolverIntervals().size());for(const auto& interval:candidate.omittedSolverIntervals())f.text(interval);for(unsigned v:candidate.screeningEnvironment())f.u64(v);f.text("backend.maximum_violation_row uses solver-reduced coordinates; following maps original SI");f.u64(static_cast<std::uint64_t>(static_cast<std::int64_t>(candidate.originalMaximumViolationRow())));});
  if(!connected.complete())throw std::runtime_error(std::string(connected.trace().first_error));
  if(!candidate.needsIndependentCandidateForward())throw std::runtime_error(candidate.stopReason());
  stage="ACTIVE_A_DATA_ONLY_CANDIDATE_REQUIRES_B_NO_COMMIT";
 }catch(const std::exception& e){error=e.what();}catch(...){error="unknown active entry failure";}
 // Always retain the actual native boundary and explicit termination outcome.
 if(out&&!before_write_attempted){before_write_attempted=true;try{out->snapshot("observation_before.bin",before);}catch(const std::exception& e){if(error.empty())error=e.what();}}
 if(simulation){try{simulation->observe(after);if(out){after_write_attempted=true;out->snapshot("observation_after.bin",after);}boundary_same=before.completed()&&after.completed()&&bits(before.integrationBefore(),after.integrationBefore());}catch(const std::exception& e){if(error.empty())error=e.what();}
  if(out&&!after_write_attempted){after_write_attempted=true;try{out->snapshot("observation_after.bin",after);}catch(const std::exception& e){if(error.empty())error=e.what();}}
  try{simulation->verifyTermination();}catch(const std::exception& e){if(error.empty())error=e.what();}
  if(out)try{out->bootstrap(simulation->facts());}catch(const std::exception& e){if(error.empty())error=e.what();}}
 if(session){try{session->verifyTermination();termination_pass=session->terminationVerified();}catch(const std::exception& e){if(error.empty())error=e.what();}}
 if(out){try{out->write("entry_completion.bin","ACTIVE_SESSION_FINAL_SCOPE_AND_TIMING",[&](evidence::BinaryFile& f){f.text(stage);f.text(error);f.u64(boundary_same);f.u64(termination_pass);f.text(session?session->terminationFailure():"no session created");f.u64(simulation&&simulation->terminationVerified());f.text(simulation?simulation->terminationFailure():"no native simulation created");f.number(std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count());f.u64(simulation?simulation->facts().step:0);f.u64(simulation?simulation->facts().commits:0);});out->finish(stage,error,boundary_same);}catch(const std::exception& e){if(error.empty())error=e.what();}}
 std::cout<<"stage="<<stage<<" error="<<error<<" unchanged="<<boundary_same<<" termination_verified="<<termination_pass<<" phase5=NOT_ACCEPTED\n";
 return error.empty()&&boundary_same&&termination_pass&&simulation&&simulation->terminationVerified()?0:1;
}
