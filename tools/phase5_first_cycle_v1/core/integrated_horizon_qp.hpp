#pragma once
// Versioned SOURCE candidate. No executable and no new witness/session factory.
#include "affine_assembly.hpp"
#include <predictive_motion_control/reactive_qp.hpp>
#include <Eigen/Core>
#include <Eigen/SparseCore>
#include <array>
#include <functional>
#include <memory>
#include <optional>
#include <string>
#include <vector>

namespace phase5_integrated_horizon_qp_v1 {
namespace live = phase5_public_live_affine_v2;
namespace qp = predictive_motion::control;
constexpr int N=20, T=200, S=400, NX=30, NU=8, NZ=160;
// Exact nonuniform diagnostic lattice: sum200 macro cycles=.8s. Task3s is a
// separate750-commit session, NOT a750-cycle forecast inside this component.
inline constexpr std::array<live::Count,N> lattice{1,1,2,2,3,3,4,4,5,5,6,6,8,10,12,16,20,24,28,40};
struct Limits {
  live::JointVector physical_speed{}; // Required separately from command speed.
  double command_speed=.0625,command_acceleration=1,command_jerk=20;
  double progress_speed=.2,progress_acceleration=.5,progress_jerk=5;
  double position_margin=.005,joint_trust=.002,progress_trust=.02;
};
struct Weights {
  double tracking=100,physical_velocity=.01,posture=.001;
  double command_acceleration=.001,command_jerk=.00001;
  double progress_acceleration=.001,progress_jerk=.00001;
  double progress_reward=.1,terminal_progress=.1,rotation_length=.3;
  live::JointVector posture_reference{};
};
// Caller-provided local task mathematics, not a safety/execution certificate.
// Residual/Jq/Js are raw translation[m], rotation[rad] in one declared local
// residual convention; adapter weights angular rows by rotation_length[m].
struct TaskLocal {
  Eigen::Matrix<double,6,1> residual,Js;
  Eigen::Matrix<double,6,7> Jq;
  std::string source_id; // Fixed task/kinematics/path identity supplied by runner.
};
using TaskLinearizer=std::function<TaskLocal(int node,const live::State30& nominal)>;
// Linearized geometric rows only. Each scalar carries its own SI units.
// Empty rows are allowed for a QP component diagnostic, recorded as uncovered.
struct GeometryRow {
  int sample=-1;std::string id,units;
  Eigen::Matrix<double,1,7> Jq;
  double nominal_value=0,lower=0,upper=0;
};
enum class TimingMode {OfflineFrozenSimulationBoundary,OnlineWallAge};
struct Inputs {
  Limits limits;Weights weights;TaskLinearizer task;
  std::string objective_source_id;
  std::vector<GeometryRow> geometry;
  double observed_age_seconds=0; // Original observer age, never refreshed.
  double known_upstream_elapsed_seconds=0; // Actual external observer/preparation timing.
  TimingMode timing_mode=TimingMode::OfflineFrozenSimulationBoundary;
  bool simulation_boundary_asserted_frozen=false; // Assertion, not an execution witness.
};
struct RowIdentity {std::string label,units;};
struct TermIdentity {std::string name;int first_factor_row=0,rows=0;};
struct AssemblyTrace {
  std::string stage="NOT_STARTED",first_error;
  int factor_rows_written=0,constraint_rows_written=0,task_nodes_returned=0;
  bool complete=false,refused=false,linear_geometry_present=false;
  bool snapshot_age_bound=false;
  std::string observation_source="CALLER_ASSERTIONS_ONLY";
  TimingMode timing_mode=TimingMode::OfflineFrozenSimulationBoundary;
  double original_observer_age=0,known_upstream_elapsed=0,connection_elapsed=0;
  std::uint64_t planned_numeric_slots=0;
};
struct Problem {
  qp::QpProblem original_si;
  Eigen::MatrixXd F;Eigen::VectorXd f,seed;
  Eigen::SparseMatrix<double> psd_factor;
  double constant=0;
  std::vector<RowIdentity> rows;
  std::vector<TermIdentity> terms;
  std::vector<TaskLocal> retained_task_prefix;
  // Actual matrices/partial prefix retained on failure; only complete() admits.
};
class Outcome final {
 public:
  Outcome(const Outcome&)=delete;Outcome& operator=(const Outcome&)=delete;
  Outcome(Outcome&&) noexcept;Outcome& operator=(Outcome&&) noexcept;~Outcome();
  bool complete() const noexcept;
  const AssemblyTrace& trace() const;
  const Problem& retainedProblem() const; // Partial data are forensic, not success.
  const live::AffineAssemblyOutcome& originalAssembly() const;
 private:
  struct Storage;std::unique_ptr<Storage> storage_;
  explicit Outcome(std::unique_ptr<Storage>);
  friend Outcome connect(live::OwnedPublicForecast&&,const Inputs&);
  friend class CandidateOutcome;
  friend void solveOnce(Outcome&,const qp::QpOptions&,class CandidateOutcome&);
};
// This function cannot construct a forecast from raw bytes/fixtures/State30.
// Genuine one-use Model release must produce the argument independently.
Outcome connect(live::OwnedPublicForecast&&,const Inputs&);
struct CandidateForwardRequest {
  live::State30 actual_initial_at_completed_boundary;
  std::vector<live::NominalControl> candidate_controls;
  std::array<live::Count,N> cycles=lattice;
  live::BoundaryId boundary;
  std::string observation_id,transaction_id,nominal_invocation_sha256;
  // Data-only request. No Model factory, permission, runtime or plant API.
};
struct TerminalTailObservation {
  live::JointVector final_w{},last_alpha{};double final_r=0,last_b=0;
  bool exact_zero_command_progress_tail=false;
  // Only if exact, conditional command/progress zero extension. Physical
  // stopping/equilibrium/geometry are not proved by either exact or near-zero.
};
struct CandidateTiming {
  TimingMode mode=TimingMode::OfflineFrozenSimulationBoundary;
  double original_observer_age=0,known_upstream_elapsed=0,connection_and_solver_elapsed=0,known_wall_age=0;
  bool known_current_age_within_policy=false,complete_online_observation_timing_proved=false;
};
class CandidateOutcome final {
 public:
  CandidateOutcome()=default;
  const qp::QpResult& solverResult() const noexcept{return result_;}
  const std::string& stopReason() const noexcept{return stop_reason_;}
  const std::vector<double>& originalRowViolations() const noexcept{return violations_;}
  const std::optional<live::CommandProposal>& forensicFirstPreview() const noexcept{return preview_;}
  const std::optional<CandidateForwardRequest>& forwardRequest() const noexcept{return request_;}
  const std::optional<TerminalTailObservation>& terminalTail() const noexcept{return tail_;}
  const CandidateTiming& timing() const noexcept{return timing_;}
  const std::optional<CandidateForwardRequest>& forensicForwardRequest() const noexcept{return forensic_request_;}
  bool executionPermission() const noexcept{return false;}
  bool needsIndependentCandidateForward() const noexcept{return request_.has_value();}
  unsigned solveAttempts() const noexcept{return solve_attempts_;}
  unsigned solverWrapperEntries() const noexcept{return solver_wrapper_entries_;}
  // Fresh forward and original SI/geometry/physical-tail validation remain
  // required even when stopReason()==CANDIDATE_FORWARD_REQUIRED.
 private:
  qp::QpResult result_;std::string stop_reason_="NOT_ATTEMPTED";
  std::vector<double> violations_;std::optional<live::CommandProposal> preview_;
  std::optional<CandidateForwardRequest> request_,forensic_request_;
  std::optional<TerminalTailObservation> tail_;CandidateTiming timing_;unsigned solve_attempts_=0,solver_wrapper_entries_=0;
  friend void solveOnce(Outcome&,const qp::QpOptions&,CandidateOutcome&);
};
// Source contains exactly one solver entry, latched before dispatch. Runtime
// requires a separately reviewed protocol. No retry/shrink/projection/fallback.
void solveOnce(Outcome&,const qp::QpOptions&,CandidateOutcome&);
// Controls only. No states/maps/duals are shifted; next genuine forecast must
// repropagate from the next independently completed actual/history boundary.
Eigen::VectorXd shiftControlGuess(const Eigen::VectorXd& old_controls,live::Count elapsed_cycles);
} // namespace phase5_integrated_horizon_qp_v1
