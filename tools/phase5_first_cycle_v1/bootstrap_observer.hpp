#pragma once
#include "integrated_horizon_qp.hpp"
#include <mujoco/mujoco.h>
#include <chrono>
#include <memory>
#include <string>
#include <vector>
namespace phase5_first_cycle_v1 {
namespace bridge=phase5_integrated_horizon_qp_v1;
namespace live=phase5_public_live_affine_v2;
struct Snapshot {
 live::State30 actual;
 std::vector<mjtNum> integration_before,integration_after;
 int contacts=0,joints_read=0;double simulation_time=0;
 bool complete=false,integration_before_written=false,integration_after_written=false;
 std::string stage="NOT_OBSERVED",first_error;
 std::string epoch,source;
 std::chrono::steady_clock::time_point capture;
};
struct BootstrapFacts {
 unsigned load_xml=0,make_data=0,reset_keyframe=0,forward=0,copy_data=0,state_size=0,get_state=0;
 unsigned joint_name_queries=0,key_name_queries=0;
 bool initialized=false;std::string first_error;
 // Deliberate direct C API entries; not all library/IO/backend calls.
};
class InitializedSimulation final {
 public:
  explicit InitializedSimulation(const std::string& source_epoch);
  void initialize(const std::string& exact_profile_xml);
  void observe(Snapshot&); // Independently forward scratch; integration stays untouched.
  const BootstrapFacts& facts() const noexcept{return facts_;}
  bool sameBoundary(const Snapshot&,const Snapshot&) const;
 private:
  std::unique_ptr<mjModel,decltype(&mj_deleteModel)> model_{nullptr,mj_deleteModel};
  std::unique_ptr<mjData,decltype(&mj_deleteData)> state_{nullptr,mj_deleteData},scratch_{nullptr,mj_deleteData};
  std::string epoch_;BootstrapFacts facts_;bool initialize_attempted_=false;unsigned observations_=0;
  std::array<int,7> joints_{},qpos_{},dof_{},actuators_{};
};
// Real native snapshot -> genuine value validator. No archived state/carrier.
live::LiveActualContext makeContext(const Snapshot&,const live::State30& frozen_nominal_anchor,const live::StaticDomainRanges&,double& recorded_observer_age);
}
