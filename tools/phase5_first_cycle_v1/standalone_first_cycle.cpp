#include "bootstrap_observer.hpp"
#include "lossless_evidence.hpp"
#include "task_local_provider.hpp"
#include <yaml-cpp/yaml.h>
#include <openssl/evp.h>
#include <fcntl.h>
#include <unistd.h>
#include <chrono>
#include <cerrno>
#include <fstream>
#include <iostream>
#include <optional>
#include <set>
#include <stdexcept>
namespace {
namespace run=phase5_first_cycle_v1;namespace live=phase5_public_live_affine_v2;namespace bridge=phase5_integrated_horizon_qp_v1;
void need(bool v,const char* why){if(!v)throw std::invalid_argument(why);}
std::string sha(const std::string& bytes){unsigned char raw[32]{};unsigned n=0;need(EVP_Digest(bytes.data(),bytes.size(),raw,&n,EVP_sha256(),nullptr)==1&&n==32,"parsed document SHA failed");std::string s;const char* hex="0123456789abcdef";for(unsigned j=0;j<n;++j){s.push_back(hex[raw[j]>>4]);s.push_back(hex[raw[j]&15]);}return s;}
YAML::Node readPinned(const std::string& path,const std::string& digest){const auto id=live::observePinnedFile(path,digest);need(id.bytes<=2*1024*1024,"bounded trusted JSON document");std::ifstream input(path,std::ios::binary);need(static_cast<bool>(input),"pinned JSON open failed");std::string b(static_cast<std::size_t>(id.bytes),'\0');input.read(b.data(),b.size());need(input.gcount()==static_cast<std::streamsize>(b.size())&&input.peek()==EOF&&sha(b)==digest,"actual parsed document identity changed");(void)live::observePinnedFile(path,digest);return YAML::Load(b);}
void keys(const YAML::Node& n,std::initializer_list<const char*> expected){need(n.IsMap()&&n.size()==expected.size(),"exact trusted document keys");std::set<std::string> seen;for(const auto& x:n)need(seen.insert(x.first.as<std::string>()).second,"duplicate document keys");for(const char* s:expected)need(seen.count(s)==1,"missing trusted document key");}
std::string text(const YAML::Node& n){need(n.IsScalar(),"scalar trusted string required");auto s=n.as<std::string>();need(!s.empty()&&s.size()<=4096&&s.find('\0')==std::string::npos,"bounded trusted string");return s;}
live::FileIdentity artifact(const YAML::Node& n){keys(n,{"path","sha256","bytes"});auto id=live::observePinnedFile(text(n["path"]),text(n["sha256"]));need(id.bytes==n["bytes"].as<live::Count>(),"pinned artifact length");return id;}
Eigen::VectorXd vector(const YAML::Node& n,int count){need(n.IsSequence()&&n.size()==static_cast<std::size_t>(count),"exact profile vector shape");Eigen::VectorXd v(count);for(int j=0;j<count;++j)v(j)=n[j].as<double>();need(v.allFinite(),"finite frozen profile vector");return v;}
void claim(const std::string& path,const std::string& content){const int fd=::open(path.c_str(),O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC,0600);need(fd>=0,"FIRST bootstrap claim exists/unsafe; never retry");std::size_t at=0;while(at<content.size()){const auto n=::write(fd,content.data()+at,content.size()-at);if(n<0&&errno==EINTR)continue;if(n<=0){::close(fd);throw std::runtime_error("bootstrap claim prefix failure; retained");}at+=static_cast<std::size_t>(n);}const int sync=::fsync(fd),close=::close(fd);need(sync==0&&close==0,"bootstrap claim sync/close failure; retained");}
}
int main(int argc,char** argv){
 // New standalone component CLI. Never invokes old main, plant step/command,
 // candidate Model rollout, scorer or an automatically renewable permission.
 if(argc!=8){std::cerr<<"outer_review outer_sha v1_model_review model_review_sha runner_profile profile_sha fresh_output_directory\n";return 2;}
 std::unique_ptr<run::Evidence> evidence;std::unique_ptr<run::InitializedSimulation> simulation;
 run::Snapshot before,after;std::optional<live::ModelOpenOutcome> open;
 std::optional<bridge::Outcome> integration;bridge::CandidateOutcome candidate;
 std::string stage="READ_REVIEWED_OUTER_SCOPE",error;bool same=false,after_attempted=false;double observer_age=0,upstream_elapsed=0;
 try{
  auto outer=readPinned(argv[1],argv[2]);keys(outer,{"schema","decision","timing_mode","producer_sha256","profile","model_review","output_directory","bootstrap_claim_path","roles","phase5","phase6"});
  need(text(outer["schema"])=="FIRST_CYCLE_RUNTIME_RELEASE_1"&&text(outer["decision"])=="RELEASED_FOR_ONE_OFFLINE_FIRST_CYCLE_BOUND_COMPONENT"&&text(outer["timing_mode"])=="OfflineFrozenSimulationBoundary","actual trusted Root runtime release required");
  need(text(outer["phase5"])=="NOT_ACCEPTED"&&text(outer["phase6"])=="NOT_STARTED","no phase acceptance in component release");
  const auto producer=live::observeCurrentProducerElf(text(outer["producer_sha256"]));
  const auto profile_id=artifact(outer["profile"]),model_review_id=artifact(outer["model_review"]);
  need(profile_id.path==argv[5]&&profile_id.sha256==argv[6]&&model_review_id.path==argv[3]&&model_review_id.sha256==argv[4]&&text(outer["output_directory"])==argv[7],"CLI differs from frozen Root release");
  auto roles=outer["roles"];keys(roles,{"mj_loadXML","mj_makeData","mj_resetDataKeyframe","mj_forward","mj_copyData","mj_stateSize","mj_getState","joint_name_queries","key_name_queries","kinematics_constructor","kinematics_joint_names_query","model_wrapper_constructor","model_wrapper_metadata","nominal_wrapper_rollout","QP_wrapper_max","task_nodes_max","candidate_forward","plant_step","plant_commit","legacy_main","scorer"});
  const std::array<std::pair<const char*,unsigned>,21> expected={{{"mj_loadXML",1},{"mj_makeData",2},{"mj_resetDataKeyframe",1},{"mj_forward",3},{"mj_copyData",2},{"mj_stateSize",2},{"mj_getState",4},{"joint_name_queries",7},{"key_name_queries",1},{"kinematics_constructor",1},{"kinematics_joint_names_query",1},{"model_wrapper_constructor",1},{"model_wrapper_metadata",1},{"nominal_wrapper_rollout",1},{"QP_wrapper_max",1},{"task_nodes_max",21},{"candidate_forward",0},{"plant_step",0},{"plant_commit",0},{"legacy_main",0},{"scorer",0}}};
  for(const auto& x:expected)need(roles[x.first].as<unsigned>()==x.second,"runtime deliberate API roles differ");
  auto profile=readPinned(argv[5],argv[6]);keys(profile,{"schema","source_epoch","xml","constants","robot_config","task_reference","expected_initial","physical_speed","task_source_id","solver"});
  need(text(profile["schema"])=="FIRST_CYCLE_HOME_BOOTSTRAP_PROFILE_1","exact home bootstrap source profile required");
  const auto xml=artifact(profile["xml"]),constants=artifact(profile["constants"]),robot_config=artifact(profile["robot_config"]),reference=artifact(profile["task_reference"]);
  const auto epoch=text(profile["source_epoch"]);need(epoch.size()<=128,"bounded actual source epoch");
  evidence=std::make_unique<run::Evidence>(argv[7]);
  stage="VALIDATE_ORIGINAL_V1_PERMISSION_AND_FIRST_BOOTSTRAP_CLAIM";
  auto permission=live::loadReviewedForecastPermission({argv[3],argv[4]}); // All original source/SDK/metadata/claim/cost bindings stay.
  claim(text(outer["bootstrap_claim_path"]),"outer_review="+std::string(argv[2])+"\nprofile="+std::string(argv[6])+"\nproducer="+producer.sha256+"\nepoch="+epoch+"\n");
  // Cross-bind current observer XML/constants to the original V1 protocol,
  // whose complete validation remains inside its unchanged permission factory.
  auto model_review=readPinned(argv[3],argv[4]);auto protocol_descriptor=model_review["protocol"];
  const auto protocol_path=text(protocol_descriptor["path"]),protocol_sha=text(protocol_descriptor["sha256"]);
  auto model_protocol=readPinned(protocol_path,protocol_sha);bool xml_bound=false,constants_bound=false;
  for(const auto& x:model_protocol["artifacts"]){const auto role=text(x["role"]);
   if(role=="xml")xml_bound=text(x["path"])==xml.path&&text(x["sha256"])==xml.sha256&&x["bytes"].as<live::Count>()==xml.bytes;
   if(role=="constants")constants_bound=text(x["path"])==constants.path&&text(x["sha256"])==constants.sha256&&x["bytes"].as<live::Count>()==constants.bytes;}
  need(xml_bound&&constants_bound,"actual observer profile differs from original V1 Model profile");
  const auto ranges=live::loadPinnedStaticRanges(constants.path,constants.sha256);
  auto expected_initial=profile["expected_initial"];keys(expected_initial,{"q","v","C","w","s","r"});
  live::State30 expected_anchor;
  for(const auto& x:std::array<std::pair<const char*,live::JointVector*>,4>{{{"q",&expected_anchor.q},{"v",&expected_anchor.v},{"C",&expected_anchor.C},{"w",&expected_anchor.w}}}){auto v=vector(expected_initial[x.first],7);for(int j=0;j<7;++j)(*x.second)[j]=v(j);}
  expected_anchor.s=expected_initial["s"].as<double>();expected_anchor.r=expected_initial["r"].as<double>();
  stage="REAL_MUJOCO_KEYFRAME_BOOTSTRAP_AND_BEFORE_OBSERVER";
  simulation=std::make_unique<run::InitializedSimulation>(epoch);simulation->initialize(xml.path);simulation->observe(before);
  auto actual=run::makeContext(before,expected_anchor,ranges,observer_age); // Preserve the real captured age immediately.
  evidence->snapshot("observation_before.bin",before); // Current object, never copied expected/archived state.
  for(const auto& x:std::array<std::pair<const char*,const live::JointVector*>,4>{{{"q",&before.actual.q},{"v",&before.actual.v},{"C",&before.actual.C},{"w",&before.actual.w}}}){auto v=vector(expected_initial[x.first],7);for(int j=0;j<7;++j)need(v(j)==(*x.second)[j],"actual native bootstrap differs from pre-frozen prospective initial");}
  need(before.actual.s==expected_initial["s"].as<double>()&&before.actual.r==expected_initial["r"].as<double>(),"actual bootstrap progress policy differs");
  live::BatchBudget batch;auto invocation=live::prepareFrozenLiveInvocation(permission,actual,batch);
  stage="PINNED_ACTUAL_TASK_PROVIDER";
  predictive_motion::RobotKinematics robot(predictive_motion::loadConfig(robot_config.path));
  const auto& kin_names=robot.jointNames();need(kin_names.size()==7,"actual task kinematics dimension mapping");for(int j=0;j<7;++j)need(kin_names[j]=="fr3_joint"+std::to_string(j+1),"actual task kinematics order mismatch");
  auto task=readPinned(reference.path,reference.sha256);bridge::WorldTaskPath curve;
  curve.start=vector(task["start"],3);curve.end=vector(task["end"],3);curve.quaternion_xyzw=vector(task["quaternion_xyzw"],4);
  curve.lateral_amplitude=task["lateral_amplitude"].as<double>();curve.vertical_amplitude=task["vertical_amplitude"].as<double>();
  bridge::Inputs in;in.observed_age_seconds=observer_age;in.timing_mode=bridge::TimingMode::OfflineFrozenSimulationBoundary;in.simulation_boundary_asserted_frozen=true;
  const auto speeds=vector(profile["physical_speed"],7);for(int j=0;j<7;++j){in.limits.physical_speed[j]=speeds(j);in.weights.posture_reference[j]=before.actual.q[j];}
  in.objective_source_id=text(profile["task_source_id"]);in.task=bridge::bindTaskLinearizer(robot,curve,in.objective_source_id);
  auto options=profile["solver"];keys(options,{"max_iterations","absolute_tolerance","relative_tolerance","acceptance_tolerance","time_limit_seconds","max_state_age_seconds","initial_rho"});
  bridge::qp::QpOptions qo;qo.max_iterations=options["max_iterations"].as<int>();qo.absolute_tolerance=options["absolute_tolerance"].as<double>();qo.relative_tolerance=options["relative_tolerance"].as<double>();qo.acceptance_tolerance=options["acceptance_tolerance"].as<double>();qo.time_limit_seconds=options["time_limit_seconds"].as<double>();qo.max_state_age_seconds=options["max_state_age_seconds"].as<double>();qo.initial_rho=options["initial_rho"].as<double>();
  stage="ONE_ORIGINAL_MODEL_OPEN";open.emplace(live::openPinnedModel(permission,invocation));evidence->modelOpen(*open);need(open->hasModel(),"original Model open refused; actual metadata retained");
  stage="ONE_GENUINE_NOMINAL_AND_FULL_RAW_RETENTION";auto forecast=live::forecastPublic(open->model(),std::move(invocation));evidence->rawForecast(forecast);
  // Direct equivalent one-cycle orchestration is required for pre-connect raw
  // retention. Existing runFirstCycle helper is preserved but not called here.
  stage="ONE_COMPLETE_INLINE_CONNECTION";
  upstream_elapsed=std::chrono::duration<double>(std::chrono::steady_clock::now()-before.capture).count()-observer_age;need(upstream_elapsed>=0,"actual monotonic upstream elapsed invalid");in.known_upstream_elapsed_seconds=upstream_elapsed;
  integration.emplace(bridge::connect(std::move(forecast),in));evidence->integration(*integration);need(integration->complete(),"complete full horizon connection refused; retained original prefix");
  stage="ONE_QP_AND_ORIGINAL_SI_COMMAND_PROGRESS_GATES";bridge::solveOnce(*integration,qo,candidate);evidence->candidate(candidate);
  stage="AFTER_INDEPENDENT_FROZEN_BOUNDARY_OBSERVER";after_attempted=true;simulation->observe(after);evidence->snapshot("observation_after.bin",after);same=simulation->sameBoundary(before,after);need(same,"actual simulation boundary changed during offline component");
  if(!candidate.forwardRequest().has_value()){error=candidate.stopReason();stage="COMPONENT_REFUSED_CANDIDATE_RETAINED_BOUNDARY_OBSERVED";}
  else stage="DATA_DIAGNOSTIC_COMPLETE_NO_EXECUTION_PERMISSION";
 }catch(const std::exception& e){error=e.what();}catch(...){error="NONSTANDARD_FIRST_CYCLE_FAILURE";}
 // Preserve partial actual observer/facts even when its method refused. Artifact
 // names are FIRST-only, and the receipts mark absent/partial data explicitly.
 if(evidence){try{
   if(simulation&&simulation->facts().initialized&&!after_attempted){
    try{after_attempted=true;simulation->observe(after);evidence->snapshot("observation_after.bin",after);same=simulation->sameBoundary(before,after);if(!same&&error.empty())error="actual boundary mismatch after failed component";}
    catch(const std::exception& e){if(error.empty())error=e.what();}}
   if(before.stage!="NOT_OBSERVED"&&!before.complete)evidence->snapshot("observation_before_partial.bin",before);
   if(after.stage!="NOT_OBSERVED"&&!after.complete)evidence->snapshot("observation_after_partial.bin",after);
   if(simulation)evidence->bootstrap(simulation->facts());evidence->finish(stage,error,same);
  }catch(const std::exception& e){std::cerr<<"evidence_failure="<<e.what()<<'\n';return 3;}}
 std::cout<<"stage="<<stage<<" error="<<error<<" no_phase_acceptance\n";
 return error.empty()?0:1;
}
