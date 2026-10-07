#include "predictive_motion_control/nullspace.hpp"

#include <Eigen/SVD>
#include <chrono>
#include <cmath>
#include <limits>
#include <stdexcept>
namespace predictive_motion::control {
namespace {
void validate(const Eigen::MatrixXd& j, double tolerance) {
  if (j.rows() == 0 || j.cols() == 0 || !j.allFinite() || !std::isfinite(tolerance) ||
      tolerance < 0 || tolerance >= 1)
    throw std::invalid_argument("Invalid Jacobian/rank tolerance");
}
void checkSvd(const Eigen::JacobiSVD<Eigen::MatrixXd>& svd) {
  if (svd.info() != Eigen::Success || !svd.singularValues().allFinite())
    throw std::overflow_error("SVD failed or singular values are not representable");
}
}  // namespace
Eigen::MatrixXd exactNullProjector(const Eigen::MatrixXd& j, double tolerance) {
  validate(j, tolerance);
  Eigen::JacobiSVD<Eigen::MatrixXd> svd(j, Eigen::ComputeThinV);
  checkSvd(svd);
  Eigen::MatrixXd p = Eigen::MatrixXd::Identity(j.cols(), j.cols());
  const auto& s = svd.singularValues();
  // Equivalent to I-Jdagger*J, but avoids cancellation amplified by reciprocal tiny sigma.
  for (int i = 0; i < s.size(); ++i)
    if (s[i] > tolerance * s[0] && s[i] > 0)
      p.noalias() -= svd.matrixV().col(i) * svd.matrixV().col(i).transpose();
  if (!p.allFinite() || !(j * p).allFinite())
    throw std::overflow_error("Nonfinite exact projector/leakage");
  return p;
}
Eigen::MatrixXd dampedProjector(const Eigen::MatrixXd& j, double damping, double tolerance) {
  validate(j, tolerance);
  if (!std::isfinite(damping) || damping < 0) throw std::invalid_argument("Invalid damping");
  if (damping == 0) return exactNullProjector(j, tolerance);
  Eigen::JacobiSVD<Eigen::MatrixXd> svd(j, Eigen::ComputeThinV);
  checkSvd(svd);
  Eigen::MatrixXd p = Eigen::MatrixXd::Identity(j.cols(), j.cols());
  for (int i = 0; i < svd.singularValues().size(); ++i) {
    const double sigma = svd.singularValues()[i], scale = std::max(sigma, damping);
    const double a = sigma / scale, b = damping / scale, coefficient = a * a / (a * a + b * b);
    p.noalias() -= coefficient * svd.matrixV().col(i) * svd.matrixV().col(i).transpose();
  }
  if (!p.allFinite() || !(j * p).allFinite())
    throw std::overflow_error("Nonfinite damped projector/leakage");
  return p;
}
JointObjective jointCenterObjective(const Eigen::VectorXd& q, const Eigen::VectorXd& lo,
                                    const Eigen::VectorXd& hi) {
  if (q.size() == 0 || lo.size() != q.size() || hi.size() != q.size() || !q.allFinite() ||
      !lo.allFinite() || !hi.allFinite() || (hi.array() <= lo.array()).any())
    throw std::invalid_argument("Invalid joint objective inputs/bounds");
  Eigen::VectorXd range = hi - lo, delta = q - (lo + range * .5);
  const double value = (delta.array() / range.array()).square().sum();
  Eigen::VectorXd gradient = 2 * delta.array() / range.array().square();
  if (!std::isfinite(value) || !gradient.allFinite())
    throw std::overflow_error("Joint objective overflow");
  return {value, gradient};
}
SingularIndicators singularIndicators(const Eigen::MatrixXd& j, double tolerance, double epsilon,
                                      double gapTolerance) {
  validate(j, tolerance);
  if (!std::isfinite(epsilon) || epsilon <= 0 || !std::isfinite(gapTolerance) || gapTolerance < 0)
    throw std::invalid_argument("Invalid regularization/gap tolerance");
  Eigen::JacobiSVD<Eigen::MatrixXd> svd(j);
  checkSvd(svd);
  // Pad missing task singular values for underactuated tall matrices: det(JJ^T)=0.
  Eigen::VectorXd s = Eigen::VectorXd::Zero(j.rows());
  s.head(svd.singularValues().size()) = svd.singularValues();
  int rank = 0;
  double logProduct = 0, regularized = 0;
  for (double sigma : s) {
    if (sigma > tolerance * s[0] && sigma > 0) rank++;
    logProduct += sigma > 0 ? std::log(sigma) : -std::numeric_limits<double>::infinity();
    const double hypotenuse = std::hypot(sigma, epsilon);
    if (std::isfinite(hypotenuse))
      regularized += std::log(hypotenuse);
    else {
      const double scale = std::max(sigma, epsilon), a = sigma / scale, b = epsilon / scale;
      regularized += std::log(scale) + .5 * std::log(a * a + b * b);
    }
  }
  const double minimum = s[s.size() - 1], gap = s.size() > 1
                                                    ? s[s.size() - 2] - minimum
                                                    : std::numeric_limits<double>::infinity();
  const bool near = minimum <= tolerance * s[0] || minimum == 0;
  return {s,
          minimum,
          s[0],
          rank == s.size() ? s[0] / minimum : std::numeric_limits<double>::infinity(),
          std::exp(logProduct),
          logProduct,
          regularized,
          gap,
          rank,
          gap > gapTolerance * std::max(s[0], 1e-12),
          near};
}
GradientResult finiteDifferenceGradient(const Eigen::VectorXd& q,
                                        const JacobianEvaluator& evaluator,
                                        SingularObjective objective, double h, double tolerance,
                                        double epsilon, double gapTolerance) {
  if (q.size() == 0 || !q.allFinite() || !evaluator || !std::isfinite(h) || h <= 0)
    throw std::invalid_argument("Invalid finite-difference inputs");
  if (objective != SingularObjective::MinimumSingularValue &&
      objective != SingularObjective::RegularizedLogVolume)
    throw std::invalid_argument("Unknown singular objective");
  auto begin = std::chrono::steady_clock::now();
  Eigen::MatrixXd center = evaluator(q);
  if (center.cols() != q.size()) throw std::invalid_argument("Jacobian coordinates mismatch");
  auto metric = singularIndicators(center, tolerance, epsilon, gapTolerance);
  auto value = [&](const SingularIndicators& m) {
    return objective == SingularObjective::MinimumSingularValue ? m.sigma_min
                                                                : m.regularized_log_volume;
  };
  Eigen::VectorXd gradient(q.size());
  double minimumGap = metric.minimum_gap;
  bool simple = metric.simple_min, near = metric.near_rank;
  for (int i = 0; i < q.size(); ++i) {
    Eigen::VectorXd plus = q, minus = q;
    plus[i] += h;
    minus[i] -= h;
    auto jp = evaluator(plus), jm = evaluator(minus);
    if (jp.rows() != center.rows() || jp.cols() != center.cols() || jm.rows() != center.rows() ||
        jm.cols() != center.cols())
      throw std::invalid_argument("Changing evaluator dimensions");
    auto mp = singularIndicators(jp, tolerance, epsilon, gapTolerance),
         mm = singularIndicators(jm, tolerance, epsilon, gapTolerance);
    minimumGap = std::min({minimumGap, mp.minimum_gap, mm.minimum_gap});
    simple = simple && mp.simple_min && mm.simple_min;
    near = near || mp.near_rank || mm.near_rank;
    gradient[i] = (value(mp) - value(mm)) / (2 * h);
  }
  if (!gradient.allFinite()) throw std::overflow_error("Nonfinite singular gradient");
  double elapsed =
      std::chrono::duration<double, std::micro>(std::chrono::steady_clock::now() - begin).count();
  return {gradient, value(metric), minimumGap, simple, near, static_cast<int>(1 + 2 * q.size()),
          elapsed};
}
NullspaceCommand addExactNullspace(const Eigen::MatrixXd& j, const Eigen::VectorXd& primary,
                                   const Eigen::VectorXd& z, double tolerance) {
  validate(j, tolerance);
  if (primary.size() != j.cols() || z.size() != j.cols() || !primary.allFinite() || !z.allFinite())
    throw std::invalid_argument("Invalid null-space command dimensions/values");
  auto p = exactNullProjector(j, tolerance);
  Eigen::VectorXd secondary = p * z, total = primary + secondary;
  if (!total.allFinite()) throw std::overflow_error("Nonfinite null-space command");
  const double leakage = (j * secondary).stableNorm();
  if (!std::isfinite(leakage)) throw std::overflow_error("Nonfinite task leakage");
  return {total, secondary, p, leakage};
}
}  // namespace predictive_motion::control
