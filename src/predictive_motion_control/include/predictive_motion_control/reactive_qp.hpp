#pragma once
#include <Eigen/Core>
#include <limits>
#include <string>

namespace predictive_motion::control {
enum class QpStatus {
  Solved, InvalidInput, StaleState, InfeasibleBounds, PrimalInfeasible,
  DualInfeasible, IterationLimit, TimeLimit, NonConvex, SetupFailure,
  SolverFailure, Inaccurate, ConstraintViolation
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
  double violation = std::numeric_limits<double>::infinity();
  double primal_residual = std::numeric_limits<double>::infinity();
  double dual_residual = std::numeric_limits<double>::infinity();
  double setup_seconds = 0.0, solve_seconds = 0.0;
};
QpResult solveQp(const QpProblem& problem, const QpOptions& options = {});
// Cartesian rows are weighted externally (e.g. angular rows * length in m).
QpProblem trackingProblem(const Eigen::MatrixXd& jacobian,
                          const Eigen::VectorXd& twist, double ridge);
struct CommandLimits {
  Eigen::VectorXd position_lower, position_upper, velocity, acceleration, jerk;
  double dt = 0.004, position_margin = 0.005;
};
struct CommandHistory {
  Eigen::VectorXd measured_position, accepted_position, accepted_velocity,
      accepted_acceleration;
};
// Intersects measured/commanded one-step q, command dq, acceleration and jerk.
// Executed velocity/acceleration/jerk require a separate physical observer.
QpProblem constrainCommand(QpProblem problem, const CommandLimits& limits,
                           const CommandHistory& history);
void appendConstraint(QpProblem& problem, const Eigen::RowVectorXd& row,
                      double lower, double upper);
// d_dot >= -eta*(d-safe). Collision gradients are external measured-state data.
void appendDamper(QpProblem& problem, const Eigen::RowVectorXd& gradient,
                  double distance, double safe_distance, double eta);
QpProblem stoppingProblem(int dof);
}  // namespace predictive_motion::control
