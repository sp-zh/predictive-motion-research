#pragma once
#include "model_boundary.hpp"
#include "cycle_support.hpp"
#include "owner_binding.hpp"
#include "actual_task_metrics.hpp"
#include "task_local_provider.hpp"
#include "nominal_geometry_provider.hpp"
#include "counted_geometry.hpp"
#include <mujoco/mujoco.h>
#include <chrono>
#include <memory>
#include <limits>
#include <functional>
namespace predictive_motion {class RobotKinematics;namespace geometry {class Scene;}}
namespace phase5_active_session_qp_v1 {class Outcome;class CandidateOutcome;}
namespace phase5_pilot_candidate_validation_v1 {struct Assessment;}
namespace phase5_active_session_runtime_v1 {
namespace live=phase5_active_session_v1;
struct PhysicalHistory {
 bool acceleration_available=false;
 live::JointVector last_actual_velocity{},last_actual_acceleration{};
 live::Count total_actual_substeps=0;std::string source_id;
};
struct WarmupPoint;
struct WarmupSpec {
 live::FileIdentity feasible_csv,robot_config,geometry_config,task_reference;
 std::vector<live::FileIdentity> dependencies;
 unsigned seed=91011;
 std::function<void(const WarmupPoint&,const std::string&)> retain_event;
};
struct WarmupPoint {
 live::Count substep=0;double simulation_time=0;bool native_returned=false;int native_joints_read=0,scratch_joints_read=0;
 live::JointVector q{},v{},C{},acceleration{},jerk{};
 bool jerk_available=false,geometry_complete=false,independent_observer_guard=false;
 int contacts=0;std::array<int,mjNWARNING> warnings{};
 double minimum_true=std::numeric_limits<double>::quiet_NaN(),minimum_cover=std::numeric_limits<double>::quiet_NaN();
 double tcp_frame_error=std::numeric_limits<double>::quiet_NaN(),arm_frame_error=std::numeric_limits<double>::quiet_NaN();
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
struct ActualTaskError {bool measured=false;double elapsed=0,logical_s=0,logical_r=0;phase5_actual_task_metrics_v1::Pose actual_world{},desired_world{};phase5_actual_task_metrics_v1::Error error{};};
struct CommitPoint {WarmupPoint actual;ActualTaskError task_error;double sigma=std::numeric_limits<double>::quiet_NaN(),geometry_interval_lower=std::numeric_limits<double>::quiet_NaN(),sigma_interval_lower=std::numeric_limits<double>::quiet_NaN();bool passed=false;};
struct CommitOutcome {bool attempted=false,success=false;live::Count native_step_attempts=0,native_returns=0;std::vector<CommitPoint> points;std::string stage="NOT_STARTED",error;live::BoundaryId history_before{},history_after{};live::JointVector held_C{};double before_time=0,after_time=0;};
class ValidatedCandidate final {
 public:ValidatedCandidate(const ValidatedCandidate&)=delete;ValidatedCandidate& operator=(const ValidatedCandidate&)=delete;~ValidatedCandidate()=default;
 private:ValidatedCandidate()=default;std::shared_ptr<const void> owner;Snapshot boundary;std::unique_ptr<live::OwnedCandidateValue> value;live::JointVector C{},w{},alpha{},speed{},q_lower{},q_upper{};double s=0,r=0,b=0;std::string nominal_digest;bool consumed=false;friend class Simulation;
};
enum class ObservationClock {OnlineWallAge,OfflineFrozenSimulationBoundary};
struct NativeFacts {live::Count load_xml=0,make_data=0,reset=0,forward=0,copy=0,get_state=0,observations=0,step=0,commits=0,warmup_step_attempts=0,warmup_completed_steps=0;};
// Own native integration and independent observation storage. No public target
// write/step/history-update API exists until validated-candidate transaction.
class Simulation final {
 public:
 Simulation(const live::FileIdentity& xml,const std::string& epoch,const phase5_dynamic_cycle_support_v1::Envelope&);
 ~Simulation();
 const WarmupOutcome& initializeAndWarmup(const WarmupSpec&);
 const WarmupOutcome& warmupOutcome() const noexcept{return warmup_;}
 Simulation(const Simulation&)=delete;Simulation& operator=(const Simulation&)=delete;
 void observe(Snapshot&);
 double ageSeconds(const Snapshot&) const; // elapsed since original capture; no timestamp or stored-age mutation
 live::CurrentBoundaryExpectation current(const Snapshot&,ObservationClock=ObservationClock::OnlineWallAge) const;
 std::unique_ptr<ValidatedCandidate> validateCandidate(const Snapshot&,const phase5_active_session_qp_v1::Outcome&,const phase5_active_session_qp_v1::CandidateOutcome&,live::OwnedCandidateValue&&,const live::JointVector&,phase5_pilot_candidate_validation_v1::Assessment&);
 void bindExpectedPredictionSession(const live::Session&);
 void buildNominalGeometry(const Snapshot&,const live::Session&,const live::OwnedPublicForecast&,phase5_nominal_geometry_provider_v1::Result&,const std::function<void(live::Count)>&);
 const phase5_geometry_provider_counted_v2::Counts& providerGeometryCounts()const noexcept{return provider_geometry_counts_;}
 const CommitOutcome& commit(ValidatedCandidate&,const std::function<void(const CommitPoint&,const std::string&)>&);
 const CommitOutcome& commitOutcome() const noexcept{return commit_history_.empty()?never_committed_:commit_history_.back();}
 const std::vector<CommitOutcome>& commitHistory() const noexcept{return commit_history_;}
 double structuralReachBound() const noexcept{return structural_reach_bound_;}
 void verifyTermination();
 bool terminationVerified() const noexcept{return terminated_&&termination_passed_;}
 const std::string& terminationFailure() const noexcept{return termination_failure_;}
 const NativeFacts& facts() const noexcept{return facts_;}
 private:
 std::unique_ptr<mjModel,decltype(&mj_deleteModel)> model_{nullptr,mj_deleteModel};
 std::unique_ptr<mjData,decltype(&mj_deleteData)> state_{nullptr,mj_deleteData},scratch_{nullptr,mj_deleteData};
 std::array<int,7> qpos_{},dof_{},actuators_{};
 PhysicalHistory physical_;WarmupOutcome warmup_;CommitOutcome never_committed_;std::vector<CommitOutcome> commit_history_;phase5_dynamic_cycle_support_v1::Envelope scope_;
 live::Count task_step_attempts_=0;
 double structural_reach_bound_=0;
 phase5_active_session_qp_v1::WorldTaskPath actual_task_path_;bool actual_task_path_bound_=false;
 std::unique_ptr<predictive_motion::RobotKinematics> warmup_robot_;
 std::unique_ptr<predictive_motion::geometry::Scene> warmup_geometry_;
 phase5_designated_owner_v1::Binding expected_prediction_owner_;
 phase5_geometry_provider_counted_v2::Counts provider_geometry_counts_;
 std::unique_ptr<phase5_geometry_provider_counted_v2::CountedScene> provider_geometry_;live::FileIdentity geometry_pin_;live::Count geometry_boundary_=std::numeric_limits<live::Count>::max();
 std::vector<live::FileIdentity> warmup_pins_;
 live::JointVector C_{},w_{},previous_alpha_{};double s_=0,r_=0,previous_b_=0;
 live::BoundaryId completed_{};std::string epoch_;NativeFacts facts_;
 live::FileIdentity xml_pin_;
 std::shared_ptr<const void> owner_token_=std::make_shared<char>(0);
 live::Count validation_boundary_=std::numeric_limits<live::Count>::max();
 bool failed_=false,in_flight_=false,terminated_=false,termination_passed_=false;
 std::string termination_failure_;
};
}
