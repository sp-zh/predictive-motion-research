#pragma once
#include "model_boundary.hpp"
#include <mujoco/mujoco.h>
#include <chrono>
#include <memory>
#include <limits>
namespace predictive_motion {class RobotKinematics;namespace geometry {class Scene;}}
namespace phase5_active_session_runtime_v1 {
namespace live=phase5_active_session_v1;
struct PhysicalHistory {
 bool acceleration_available=false;
 live::JointVector last_actual_velocity{},last_actual_acceleration{};
 live::Count total_actual_substeps=0;std::string source_id;
};
struct WarmupSpec {
 live::FileIdentity feasible_csv,robot_config,geometry_config,task_reference;
 std::vector<live::FileIdentity> dependencies;
 unsigned seed=91011;
};
struct WarmupPoint {
 live::Count substep=0;double simulation_time=0;
 live::JointVector q{},v{},C{},acceleration{},jerk{};
 bool jerk_available=false,geometry_complete=false,independent_observer_guard=false;
 int contacts=0;std::array<int,mjNWARNING> warnings{};
 double minimum_true=std::numeric_limits<double>::quiet_NaN(),minimum_cover=std::numeric_limits<double>::quiet_NaN();
 std::size_t geometry_queries=0;std::string stage="BEFORE_OBSERVATION",error;
};
struct WarmupOutcome {
 bool attempt_entered=false,initial_assignment_completed=false,success=false;
 unsigned seed=0;live::JointVector declared_initial_q{};
 std::vector<WarmupPoint> retained_points;
 std::string stage="NOT_STARTED",error;
 double final_rotation_error=std::numeric_limits<double>::quiet_NaN();
 double final_position_error=std::numeric_limits<double>::quiet_NaN();
};
class Snapshot final {
 public:
 const PhysicalHistory& physicalHistory() const noexcept{return physical;}
 const live::ObservedActual& actualObservation() const noexcept{return observed;}
 const live::AcceptedCommandHistory& acceptedHistory() const noexcept{return command;}
 const live::ProgressHistory& progressHistory() const noexcept{return progress;}
 const std::vector<mjtNum>& integrationBefore() const noexcept{return integration_before;}
 const std::vector<mjtNum>& integrationAfter() const noexcept{return integration_after;}
 double simulationTime() const noexcept{return simulation_time;}
 const std::chrono::steady_clock::time_point& captureTime() const noexcept{return capture;}
 bool completed() const noexcept{return complete;}
 const std::string& failure() const noexcept{return error;}
 const std::string& stageName() const noexcept{return stage;}
 int jointsRead() const noexcept{return joints_read;}
 bool beforeWritten() const noexcept{return before_written;}
 bool afterWritten() const noexcept{return after_written;}
 private:
 std::shared_ptr<const void> owner_token;
 PhysicalHistory physical;
 live::ObservedActual observed;
 live::AcceptedCommandHistory command;
 live::ProgressHistory progress;
 std::chrono::steady_clock::time_point capture;
 std::vector<mjtNum> integration_before,integration_after;
 double simulation_time=0;int contacts=0;
 int joints_read=0;bool before_written=false,after_written=false;
 bool complete=false;std::string stage="NOT_STARTED",error;
 friend class Simulation;
};
enum class ObservationClock {OnlineWallAge,OfflineFrozenSimulationBoundary};
struct NativeFacts {live::Count load_xml=0,make_data=0,reset=0,forward=0,copy=0,get_state=0,observations=0,step=0,commits=0,warmup_step_attempts=0,warmup_completed_steps=0;};
// Own native integration and independent observation storage. No public target
// write/step/history-update API exists until validated-candidate transaction.
class Simulation final {
 public:
 Simulation(const live::FileIdentity& xml,const std::string& epoch);
 ~Simulation();
 const WarmupOutcome& initializeAndWarmup(const WarmupSpec&);
 const WarmupOutcome& warmupOutcome() const noexcept{return warmup_;}
 Simulation(const Simulation&)=delete;Simulation& operator=(const Simulation&)=delete;
 void observe(Snapshot&);
 double ageSeconds(const Snapshot&) const; // elapsed since original capture; no timestamp or stored-age mutation
 live::CurrentBoundaryExpectation current(const Snapshot&,ObservationClock=ObservationClock::OnlineWallAge) const;
 void verifyTermination();
 bool terminationVerified() const noexcept{return terminated_&&termination_passed_;}
 const std::string& terminationFailure() const noexcept{return termination_failure_;}
 const NativeFacts& facts() const noexcept{return facts_;}
 private:
 std::unique_ptr<mjModel,decltype(&mj_deleteModel)> model_{nullptr,mj_deleteModel};
 std::unique_ptr<mjData,decltype(&mj_deleteData)> state_{nullptr,mj_deleteData},scratch_{nullptr,mj_deleteData};
 std::array<int,7> qpos_{},dof_{},actuators_{};
 PhysicalHistory physical_;WarmupOutcome warmup_;
 std::unique_ptr<predictive_motion::RobotKinematics> warmup_robot_;
 std::unique_ptr<predictive_motion::geometry::Scene> warmup_geometry_;
 std::vector<live::FileIdentity> warmup_pins_;
 live::JointVector C_{},w_{},previous_alpha_{};double s_=0,r_=0,previous_b_=0;
 live::BoundaryId completed_{};std::string epoch_;NativeFacts facts_;
 live::FileIdentity xml_pin_;
 std::shared_ptr<const void> owner_token_=std::make_shared<char>(0);
 bool failed_=false,in_flight_=false,terminated_=false,termination_passed_=false;
 std::string termination_failure_;
};
}
