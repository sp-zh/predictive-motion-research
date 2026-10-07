#pragma once
#include <Eigen/Core>
#include <Eigen/SparseCore>
#include <limits>
#include <memory>
#include <string>
#include <vector>

namespace predictive_motion::control {
enum class QpStatus {
  Solved,
  InvalidInput,
  StaleState,
  InfeasibleBounds,
  PrimalInfeasible,
  DualInfeasible,
  IterationLimit,
  TimeLimit,
  NonConvex,
  SetupFailure,
  SolverFailure,
  Inaccurate,
  ConstraintViolation
};
const char* statusName(QpStatus status);
std::string qpSolverVersion();
struct QpOptions {
  int max_iterations = 4000;
  double absolute_tolerance = 1e-7;
  double relative_tolerance = 1e-7;
  double acceptance_tolerance = 1e-6;
  double time_limit_seconds = 0.05;
  double max_state_age_seconds = 0.05;
  // Initial penalty for fresh solver setup only; adaptive rho remains enabled.
  double initial_rho = 0.1;
};
// min .5 x'Hx + g'x, lower <= A*x <= upper. SI units supplied by caller.
// A solved result is the only result that contains a usable command.
struct QpProblem {
  Eigen::MatrixXd hessian, constraints;
  Eigen::VectorXd gradient, lower, upper;
  double state_age_seconds = 0.0;
};
struct QpResult {
  QpStatus status = QpStatus::InvalidInput;
  Eigen::VectorXd velocity;
  int raw_status = 0, api_error = 0, iterations = 0;
  int maximum_violation_row = -1;
  double violation = std::numeric_limits<double>::infinity();
  double primal_residual = std::numeric_limits<double>::infinity();
  double dual_residual = std::numeric_limits<double>::infinity();
  double setup_seconds = 0.0, solve_seconds = 0.0;
  bool workspace_reused = false, matrix_updated = false, dual_reused = false;
  double minimum_row_scale = 1, maximum_row_scale = 1;
  double minimum_variable_scale = 1, maximum_variable_scale = 1;
  double solver_absolute_tolerance = 0, solver_relative_tolerance = 0;
  double initial_rho = 0, rho_estimate = 0;
  int dual_mapped_rows = 0;
  double update_seconds = 0;
  std::string reset_reason;
  int hessian_nonzeros = 0, constraint_nonzeros = 0, rho_updates = 0, polish_status = 0;
};
QpResult solveQp(const QpProblem& problem, const QpOptions& options = {});
// Fresh matrix/setup and zero dual state on every solve. Optional finite primal
// seed only: no retained factorization or dual/matrix reuse is claimed.
QpResult solveQpWarm(const QpProblem& problem, const QpOptions& options,
                     const Eigen::VectorXd& primal_seed);
QpResult solveQpCertified(const QpProblem& problem, const QpOptions& options,
                          const Eigen::VectorXd& seed, const Eigen::SparseMatrix<double>& factor);
class QpWorkspace;
// x=D*z, with explicit positive finite D. Returns x in original coordinates;
// original PSD certificate and original SI constraints are checked independently.
QpResult solveQpScaledWorkspace(const QpProblem&, const QpOptions&, const Eigen::VectorXd&,
                                const Eigen::SparseMatrix<double>&, const Eigen::VectorXd&,
                                QpWorkspace&, const std::vector<std::string>&);
// Cartesian rows are weighted externally (e.g. angular rows * length in m).
class QpWorkspace {
 public:
  struct Impl;
  QpWorkspace();
  ~QpWorkspace();
  void reset();
  void clearDual();
  QpWorkspace(const QpWorkspace&) = delete;
  QpWorkspace& operator=(const QpWorkspace&) = delete;

 private:
  std::unique_ptr<Impl> impl_;
  friend QpResult solveQpWorkspace(const QpProblem&, const QpOptions&, const Eigen::VectorXd&,
                                   const Eigen::SparseMatrix<double>&, QpWorkspace&,
                                   const std::vector<std::string>&);
  friend QpResult solveQpScaledWorkspace(const QpProblem&, const QpOptions&, const Eigen::VectorXd&,
                                         const Eigen::SparseMatrix<double>&, const Eigen::VectorXd&,
                                         QpWorkspace&, const std::vector<std::string>&);
};
QpResult solveQpWorkspace(const QpProblem& problem, const QpOptions& options,
                          const Eigen::VectorXd& seed, const Eigen::SparseMatrix<double>& factor,
                          QpWorkspace& workspace, const std::vector<std::string>& row_labels);
QpProblem trackingProblem(const Eigen::MatrixXd& jacobian, const Eigen::VectorXd& twist,
                          double ridge);
struct CommandLimits {
  Eigen::VectorXd position_lower, position_upper, velocity, acceleration, jerk;
  double dt = 0.004, position_margin = 0.005;
};
struct CommandHistory {
  Eigen::VectorXd measured_position, accepted_position, accepted_velocity, accepted_acceleration;
};
// Intersects measured/commanded one-step q, command dq, acceleration and jerk.
// Executed velocity/acceleration/jerk require a separate physical observer.
QpProblem constrainCommand(QpProblem problem, const CommandLimits& limits,
                           const CommandHistory& history);
void appendConstraint(QpProblem& problem, const Eigen::RowVectorXd& row, double lower,
                      double upper);
// d_dot >= -eta*(d-safe). Collision gradients are external measured-state data.
void appendDamper(QpProblem& problem, const Eigen::RowVectorXd& gradient, double distance,
                  double safe_distance, double eta);
QpProblem stoppingProblem(int dof);
}  // namespace predictive_motion::control
