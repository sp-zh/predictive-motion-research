#pragma once
#include <Eigen/Core>
namespace predictive_motion::control {
enum class Method { MoorePenrose, FixedDls, AdaptiveDls };
struct Options {
  Method method = Method::MoorePenrose;
  double relative_rank_tolerance = 1e-10;
  double damping = 0.01;
  double adaptive_sigma_threshold = 0.05;
};
struct Solution {
  Eigen::VectorXd dq;
  Eigen::VectorXd singular_values;
  int rank;
  double condition;
  double damping;
  double task_residual;
};
Eigen::MatrixXd pseudoInverse(const Eigen::MatrixXd& matrix, double relative_tolerance);
Solution solve(const Eigen::MatrixXd& jacobian, const Eigen::VectorXd& twist,
               const Options& options = {});
}  // namespace predictive_motion::control
