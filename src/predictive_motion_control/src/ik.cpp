#include "predictive_motion_control/ik.hpp"

#include <Eigen/SVD>
#include <cmath>
#include <limits>
#include <stdexcept>
namespace predictive_motion::control {
namespace {
void validate(const Eigen::MatrixXd& a, double tolerance) {
  if (a.rows() == 0 || a.cols() == 0 || !a.allFinite() || !std::isfinite(tolerance) ||
      tolerance < 0 || tolerance >= 1)
    throw std::invalid_argument("Invalid matrix or relative rank tolerance");
}
Eigen::VectorXd inverseGains(const Eigen::VectorXd& s, double tolerance) {
  Eigen::VectorXd gains = Eigen::VectorXd::Zero(s.size());
  const double cutoff = tolerance * s[0];
  for (int i = 0; i < s.size(); ++i)
    if (s[i] > cutoff && s[i] > 0) gains[i] = 1 / s[i];
  return gains;
}
}  // namespace
Eigen::MatrixXd pseudoInverse(const Eigen::MatrixXd& a, double tolerance) {
  validate(a, tolerance);
  Eigen::JacobiSVD<Eigen::MatrixXd> svd(a, Eigen::ComputeThinU | Eigen::ComputeThinV);
  Eigen::MatrixXd result = svd.matrixV() *
                           inverseGains(svd.singularValues(), tolerance).asDiagonal() *
                           svd.matrixU().transpose();
  if (!result.allFinite()) throw std::overflow_error("Nonfinite pseudoinverse");
  return result;
}
Solution solve(const Eigen::MatrixXd& a, const Eigen::VectorXd& twist, const Options& o) {
  validate(a, o.relative_rank_tolerance);
  if (twist.size() != a.rows() || !twist.allFinite() || !std::isfinite(o.damping) ||
      o.damping < 0 || !std::isfinite(o.adaptive_sigma_threshold) ||
      o.adaptive_sigma_threshold <= 0)
    throw std::invalid_argument("Invalid twist or damping configuration");
  if (o.method != Method::MoorePenrose && o.method != Method::FixedDls &&
      o.method != Method::AdaptiveDls)
    throw std::invalid_argument("Unknown method");
  Eigen::JacobiSVD<Eigen::MatrixXd> svd(a, Eigen::ComputeThinU | Eigen::ComputeThinV);
  const Eigen::VectorXd s = svd.singularValues();
  int rank = 0;
  for (double value : s)
    if (value > o.relative_rank_tolerance * s[0] && value > 0) ++rank;
  double damping = o.method == Method::MoorePenrose ? 0 : o.damping;
  if (o.method == Method::AdaptiveDls) {
    const double ratio = s[s.size() - 1] / o.adaptive_sigma_threshold;
    damping *= std::sqrt(std::max(0.0, 1 - ratio * ratio));
  }
  Eigen::VectorXd gains;
  if (damping == 0) {
    gains = inverseGains(s, o.relative_rank_tolerance);
  } else {
    // Algebraically sigma/(sigma^2+lambda^2), arranged to avoid squaring overflow.
    gains.resize(s.size());
    for (int i = 0; i < s.size(); ++i) {
      const double scale = std::max(s[i], damping);
      const double x = s[i] / scale, y = damping / scale;
      gains[i] = (x / (x * x + y * y)) / scale;
    }
  }
  Eigen::VectorXd dq = svd.matrixV() * gains.asDiagonal() * svd.matrixU().transpose() * twist;
  if (!dq.allFinite()) throw std::overflow_error("Nonfinite requested joint velocity");
  const double condition =
      rank == s.size() ? s[0] / s[s.size() - 1] : std::numeric_limits<double>::infinity();
  return {dq, s, rank, condition, damping, (a * dq - twist).norm()};
}
}  // namespace predictive_motion::control
