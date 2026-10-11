#pragma once
#include "model_boundary.hpp"
#include <mujoco/mujoco.h>
#include <chrono>
#include <memory>
namespace phase5_active_session_runtime_v1 {
namespace live=phase5_active_session_v1;
class Snapshot final {
 public:
 const live::ObservedActual& actualObservation() const noexcept{return observed;}
 const live::AcceptedCommandHistory& acceptedHistory() const noexcept{return command;}
 const live::ProgressHistory& progressHistory() const noexcept{return progress;}
 const std::vector<mjtNum>& integrationBefore() const noexcept{return integration_before;}
 const std::vector<mjtNum>& integrationAfter() const noexcept{return integration_after;}
 double simulationTime() const noexcept{return simulation_time;}
 bool completed() const noexcept{return complete;}
 const std::string& failure() const noexcept{return error;}
 private:
 std::shared_ptr<const void> owner_token;
 live::ObservedActual observed;
 live::AcceptedCommandHistory command;
 live::ProgressHistory progress;
 std::chrono::steady_clock::time_point capture;
 std::vector<mjtNum> integration_before,integration_after;
 double simulation_time=0;int contacts=0;
 bool complete=false;std::string stage="NOT_STARTED",error;
 friend class Simulation;
};
enum class ObservationClock {OnlineWallAge,OfflineFrozenSimulationBoundary};
struct NativeFacts {live::Count load_xml=0,make_data=0,reset=0,forward=0,copy=0,get_state=0,observations=0,step=0,commits=0;};
// Own native integration and independent observation storage. No public target
// write/step/history-update API exists until validated-candidate transaction.
class Simulation final {
 public:
 Simulation(const live::FileIdentity& xml,const std::string& epoch);
 Simulation(const Simulation&)=delete;Simulation& operator=(const Simulation&)=delete;
 void observe(Snapshot&);
 double ageSeconds(const Snapshot&) const; // elapsed since original capture; no timestamp or stored-age mutation
 live::CurrentBoundaryExpectation current(const Snapshot&,ObservationClock=ObservationClock::OnlineWallAge) const;
 void verifyTermination();
 const NativeFacts& facts() const noexcept{return facts_;}
 private:
 std::unique_ptr<mjModel,decltype(&mj_deleteModel)> model_{nullptr,mj_deleteModel};
 std::unique_ptr<mjData,decltype(&mj_deleteData)> state_{nullptr,mj_deleteData},scratch_{nullptr,mj_deleteData};
 std::array<int,7> qpos_{},dof_{},actuators_{};
 live::JointVector C_{},w_{},previous_alpha_{};double s_=0,r_=0,previous_b_=0;
 live::BoundaryId completed_{};std::string epoch_;NativeFacts facts_;
 live::FileIdentity xml_pin_;
 std::shared_ptr<const void> owner_token_=std::make_shared<char>(0);
 bool failed_=false,in_flight_=false,terminated_=false;
};
}
