#pragma once
#include <functional>
#include <predictive_motion_control/reactive_qp.hpp>
#include <vector>

namespace predictive_motion::control {
// x=[q,v,s,r], u=[a,b]; q/v radians and rad/s, s dimensionless.
struct PreviewState {
  Eigen::VectorXd q, v;
  double s = 0, r = 0;
};
struct PreviewLimits {
  Eigen::VectorXd lower, upper, velocity, acceleration, jerk, posture;
  double progress_speed = 0.2, progress_acceleration = 0.5, progress_jerk = 5;
  double safe_distance = 0.005, position_margin = 0.005;
};
struct PreviewWeights {
  double tracking = 100, velocity = 0.01, acceleration = 0.001, jerk = 0.00001;
  double posture = 0.01, progress_reward = 0.1, terminal_progress = 0.1;
  // Zero preserves the original terminal-only reward. Positive tau weights
  // actual constant-acceleration cell progress by exp(-preview_time/tau).
  double progress_discount_tau = 0;

};
// Every row is a lower bounded scalar local model value + gradient*(q-qbar).
// Distances and optional minimum singular values are supplied by an adapter.
struct PreviewScalar {
  double value = 0, minimum = 0;
  Eigen::RowVectorXd gradient;
  std::string id;
};
struct PreviewPenalty {
  double value = 0, target = 0, weight = 0;
  Eigen::RowVectorXd gradient;
};
struct PreviewStage {
  Eigen::VectorXd residual, path_derivative;
  Eigen::MatrixXd joint_derivative;
  std::vector<PreviewScalar> scalars;
  std::vector<PreviewPenalty> penalties;
  double tracking_multiplier = 1, velocity_multiplier = 1, posture_multiplier = 1;
};
struct ProgressDiscountCoefficients { double speed = 0, acceleration = 0; };
ProgressDiscountCoefficients progressDiscountCoefficients(double duration, double tau);
struct PreviewInput {
  PreviewState initial;
  std::vector<double> mesh;
  Eigen::VectorXd previous_acceleration;
  // Previously applied measured-state kinematic input, distinct from the
  // accepted command acceleration above when tracking velocity lags.
  Eigen::VectorXd previous_model_acceleration;
  // Separate persistent command history; model state remains measured q/v.
  Eigen::VectorXd accepted_position, accepted_velocity;
  double previous_progress_acceleration = 0, control_dt = 0.004, state_age = 0;
  PreviewLimits limits;
  PreviewWeights weights;
  // Nominal is reconstructed from initial using the exact piecewise accelerations.
  Eigen::VectorXd nominal;
  Eigen::VectorXd variable_scale;
  double joint_trust = 0.02, progress_trust = 0.1;
  bool terminal_stop = true;
  bool lifted = false, capture_dense_terms = true;
};
struct AffineState {
  Eigen::VectorXd offset;
  Eigen::MatrixXd map;
};
struct PreviewAssembly {
  QpProblem qp;
  std::vector<AffineState> states;
  std::vector<PreviewState> nominal_states;
  std::vector<std::string> row_labels;
  int controls_offset = 0;
  Eigen::VectorXd nominal_decision;
  Eigen::VectorXd decision_offset, controls_origin;
  Eigen::SparseMatrix<double> convex_factor;
  // Objective terms: .5*z'H*z+g'z+constant, exposed independently.
  struct Term {
    std::string name;
    Eigen::MatrixXd hessian;
    Eigen::VectorXd gradient;
    double constant = 0;
    Eigen::MatrixXd factor;
    Eigen::VectorXd offset;
    double weight = 0;
  };
  std::vector<Term> terms;
};
std::vector<PreviewState> previewRollout(const PreviewState& initial,
                                         const std::vector<double>& mesh,
                                         const Eigen::VectorXd& controls);
PreviewState previewAdvance(const PreviewState& state, const Eigen::VectorXd& control, double h);
PreviewAssembly assemblePreview(const PreviewInput& input, const std::vector<PreviewStage>& stages);
// Same feasible command set, with additional acceleration/jerk rows in their
// own units so the final row acceptance tolerance is not amplified by dt.
QpProblem constrainPreviewCommand(QpProblem problem, const CommandLimits& limits,
                                  const CommandHistory& history);
// Mean acceleration of old piecewise constant controls over each new interval,
// after elapsed seconds. Tail extension is zero acceleration. Always reconstruct
// states from fresh measurement. Invalid/expired mesh or controls returns reset.
struct PreviewShift {
  Eigen::VectorXd controls;
  bool reset = true;
};
PreviewShift shiftPreview(const std::vector<double>& old_mesh, const Eigen::VectorXd& old_controls,
                          const std::vector<double>& new_mesh, int dof, double elapsed);
// Exact continuous extrema for q/s quadratics and v/r linears, plus discrete a/jerk.
double previewLimitViolation(const PreviewInput& input, const Eigen::VectorXd& controls);
using PreviewLinearizer =
    std::function<std::vector<PreviewStage>(const std::vector<PreviewState>&)>;
// Adapter must check nonlinear collision/singularity across the full trajectory,
// including intersample conservative bounds. No plant rollout is passed to it.
using PreviewValidator =
    std::function<double(const std::vector<PreviewState>&, const Eigen::VectorXd&)>;
// Dimensionless maximum model error / declared per-quantity tolerance.
// Optional convergence audit, separate from mandatory feasibility validation.
using PreviewConsistency =
    std::function<double(const std::vector<PreviewState>&, const std::vector<PreviewState>&,
                         const std::vector<PreviewStage>&)>;
using PreviewQpDiagnostic = std::function<void(const PreviewAssembly&, const QpResult&)>;
struct ScpOptions {
  QpOptions qp;
  int max_iterations = 3;
  double min_trust = 1e-6, shrink = 0.5, step_tolerance = 1e-5;
  double violation_tolerance = 1e-7, wall_limit = 0.05;
};
struct ScpIteration {
  QpStatus status = QpStatus::InvalidInput;
  double trust = 0, violation = std::numeric_limits<double>::quiet_NaN(), step = 0,
         linearization_s = 0, assembly_s = 0, validation_s = 0;
  bool validation_checked = false;
  bool consistency_checked = false;
  double consistency_ratio = std::numeric_limits<double>::quiet_NaN();
  Eigen::VectorXd diagnostic_controls;
  double qp_setup_s = 0, qp_solve_s = 0;
  int qp_iterations = 0, qp_raw_status = 0, variables = 0, rows = 0;
  double qp_primal_residual = 0, qp_dual_residual = 0, nominal_row_violation = 0;
  double qp_wrapper_s = 0;
  int hessian_nonzeros = 0, constraint_nonzeros = 0, rho_updates = 0, polish_status = 0;
  bool workspace_reused = false, matrix_updated = false, dual_reused = false;
  int dual_mapped_rows = 0;
  double qp_update_s = 0;
  double qp_original_row_violation = std::numeric_limits<double>::infinity();
  std::string qp_maximum_violation_row;
  double solver_absolute_tolerance = 0, solver_relative_tolerance = 0;
  double initial_rho = 0, rho_estimate = 0;
  double minimum_row_scale = 1, maximum_row_scale = 1;
  double minimum_variable_scale = 1, maximum_variable_scale = 1;
  std::string reset_reason;
};
struct PreviewResult {
  QpStatus status = QpStatus::InvalidInput;
  // Acceptance reasons describe feasible iterates, never nonlinear optimality
  // or convergence. max_iterations is a ceiling, not an executed iteration count.
  std::string termination_reason = "INVALID_INPUT";
  Eigen::VectorXd controls;
  Eigen::VectorXd decision;
  Eigen::VectorXd decision_offset;
  std::vector<PreviewState> states;
  std::vector<ScpIteration> iterations;
  double elapsed = 0;
};
struct ProgressStop {
  bool feasible = false;
  double lower = 0, upper = 0, acceleration = std::numeric_limits<double>::quiet_NaN();
};
ProgressStop progressStopBounds(double s, double r, double previous_b, double dt,
                                const PreviewLimits& limits);
PreviewResult solvePreview(PreviewInput input, const PreviewLinearizer& linearize,
                           const PreviewValidator& validate, const ScpOptions& options = {},
                           QpWorkspace* workspace = nullptr,
                           const PreviewConsistency& consistency = {},
                           const PreviewQpDiagnostic& diagnostic = {});
}  // namespace predictive_motion::control
