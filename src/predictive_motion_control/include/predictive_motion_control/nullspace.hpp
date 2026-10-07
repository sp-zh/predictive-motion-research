#pragma once
#include <Eigen/Core>
#include <functional>
namespace predictive_motion::control {
Eigen::MatrixXd exactNullProjector(const Eigen::MatrixXd& jacobian, double rank_tolerance);
// Diagnostic comparison only: positive damping gives task leakage and is not an exact null.
Eigen::MatrixXd dampedProjector(const Eigen::MatrixXd& jacobian, double damping,
                                double rank_tolerance);
struct JointObjective {
  double value;
  Eigen::VectorXd gradient;
};
JointObjective jointCenterObjective(const Eigen::VectorXd& q, const Eigen::VectorXd& lower,
                                    const Eigen::VectorXd& upper);
struct SingularIndicators {
  Eigen::VectorXd singular_values;
  double sigma_min, sigma_max, condition, manipulability, log_manipulability;
  double regularized_log_volume, minimum_gap;
  int rank;
  bool simple_min, near_rank;
};
SingularIndicators singularIndicators(const Eigen::MatrixXd& jacobian, double rank_tolerance,
                                      double regularization, double relative_gap_tolerance);
enum class SingularObjective { MinimumSingularValue, RegularizedLogVolume };
using JacobianEvaluator = std::function<Eigen::MatrixXd(const Eigen::VectorXd&)>;
struct GradientResult {
  Eigen::VectorXd gradient;
  double value, minimum_gap;
  bool simple_min, near_rank;
  int evaluations;
  double elapsed_microseconds;
};
GradientResult finiteDifferenceGradient(const Eigen::VectorXd& q,
                                        const JacobianEvaluator& evaluator,
                                        SingularObjective objective, double h,
                                        double rank_tolerance, double regularization,
                                        double relative_gap_tolerance);
struct NullspaceCommand {
  Eigen::VectorXd total, secondary;
  Eigen::MatrixXd projector;
  double raw_task_leakage;
};
NullspaceCommand addExactNullspace(const Eigen::MatrixXd& jacobian, const Eigen::VectorXd& primary,
                                   const Eigen::VectorXd& z, double rank_tolerance);
}  // namespace predictive_motion::control
