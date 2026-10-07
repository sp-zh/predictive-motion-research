#include "predictive_motion_control/reactive_qp.hpp"
#include <osqp.h>
#include <Eigen/Eigenvalues>
#include <algorithm>
#include <cmath>
#include <memory>
#include <stdexcept>
#include <vector>

namespace predictive_motion::control {
namespace {
struct Csc {
  std::vector<OSQPInt> pointers, indices;
  std::vector<OSQPFloat> values;
  OSQPCscMatrix matrix{};
  Csc(const Eigen::MatrixXd& dense, bool upper_only) {
    for (int col = 0; col < dense.cols(); ++col) {
      pointers.push_back(static_cast<OSQPInt>(values.size()));
      for (int row = 0; row < dense.rows(); ++row) {
        if ((!upper_only || row <= col) && dense(row, col) != 0.0) {
          indices.push_back(row);
          values.push_back(dense(row, col));
        }
      }
    }
    pointers.push_back(static_cast<OSQPInt>(values.size()));
    OSQPCscMatrix_set_data(&matrix, dense.rows(), dense.cols(), values.size(),
                          values.data(), indices.data(), pointers.data());
  }
};
bool positive(double x) { return std::isfinite(x) && x > 0; }
bool validBound(double x, bool lower) {
  return std::isfinite(x) || (std::isinf(x) && (lower ? x < 0 : x > 0));
}
bool vectorSize(const Eigen::VectorXd& v, int n) {
  return v.size() == n && v.allFinite();
}
}
const char* statusName(QpStatus status) {
  switch (status) {
    case QpStatus::Solved: return "SOLVED";
    case QpStatus::InvalidInput: return "INVALID_INPUT";
    case QpStatus::StaleState: return "STALE_STATE";
    case QpStatus::InfeasibleBounds: return "INFEASIBLE_BOUNDS";
    case QpStatus::PrimalInfeasible: return "PRIMAL_INFEASIBLE";
    case QpStatus::DualInfeasible: return "DUAL_INFEASIBLE";
    case QpStatus::IterationLimit: return "ITERATION_LIMIT";
    case QpStatus::TimeLimit: return "TIME_LIMIT";
    case QpStatus::NonConvex: return "NON_CONVEX";
    case QpStatus::SetupFailure: return "SETUP_FAILURE";
    case QpStatus::SolverFailure: return "SOLVER_FAILURE";
    case QpStatus::Inaccurate: return "INACCURATE";
    case QpStatus::ConstraintViolation: return "CONSTRAINT_VIOLATION";
  }
  return "UNKNOWN";
}
std::string qpSolverVersion() { return osqp_version(); }
QpResult solveQp(const QpProblem& p, const QpOptions& o) {
  QpResult r;
  const int n = p.gradient.size(), m = p.lower.size();
  if (n <= 0 || p.hessian.rows() != n || p.hessian.cols() != n ||
      p.constraints.cols() != n || p.constraints.rows() != m || p.upper.size() != m ||
      !p.hessian.allFinite() || !p.gradient.allFinite() || !p.constraints.allFinite() ||
      !std::isfinite(p.state_age_seconds) || p.state_age_seconds < 0 ||
      o.max_iterations < 1 || !positive(o.absolute_tolerance) ||
      !positive(o.relative_tolerance) || !positive(o.acceptance_tolerance) ||
      !positive(o.time_limit_seconds) || !positive(o.max_state_age_seconds)) return r;
  const double scale = std::max(1.0, p.hessian.cwiseAbs().maxCoeff());
  const Eigen::MatrixXd normalized = p.hessian / scale;
  if ((normalized - normalized.transpose()).cwiseAbs().maxCoeff() > 1e-12) return r;
  for (int i = 0; i < m; ++i) {
    if (!validBound(p.lower(i), true) || !validBound(p.upper(i), false) ||
        (std::isfinite(p.lower(i)) && std::abs(p.lower(i)) >= OSQP_INFTY) ||
        (std::isfinite(p.upper(i)) && std::abs(p.upper(i)) >= OSQP_INFTY)) return r;
    if (p.lower(i) > p.upper(i)) { r.status = QpStatus::InfeasibleBounds; return r; }
  }
  if (p.state_age_seconds > o.max_state_age_seconds) {
    r.status = QpStatus::StaleState; return r;
  }
  // Do not rely on solver regularization to hide indefinite input.
  Eigen::SelfAdjointEigenSolver<Eigen::MatrixXd> eig(normalized);
  if (eig.info() != Eigen::Success || !eig.eigenvalues().allFinite()) return r;
  if (eig.eigenvalues().minCoeff() < -1e-12) {
    r.status = QpStatus::NonConvex; return r;
  }
  Csc h(p.hessian, true), a(p.constraints, false);
  Eigen::VectorXd lower = p.lower, upper = p.upper;
  for (int i = 0; i < m; ++i) {
    if (std::isinf(lower(i))) lower(i) = -OSQP_INFTY;
    if (std::isinf(upper(i))) upper(i) = OSQP_INFTY;
  }
  OSQPSettings settings;
  osqp_set_default_settings(&settings);
  settings.verbose = 0;
  settings.warm_starting = 0;
  settings.max_iter = o.max_iterations;
  settings.eps_abs = o.absolute_tolerance;
  settings.eps_rel = o.relative_tolerance;
  settings.time_limit = o.time_limit_seconds;
  settings.check_termination = 1;
  settings.polishing = 1;
  settings.adaptive_rho = OSQP_ADAPTIVE_RHO_UPDATE_ITERATIONS;
  settings.adaptive_rho_interval = 50;
  OSQPSolver* raw = nullptr;
  r.api_error = osqp_setup(&raw, &h.matrix, p.gradient.data(), &a.matrix,
                           lower.data(), upper.data(), m, n, &settings);
  std::unique_ptr<OSQPSolver, decltype(&osqp_cleanup)> solver(raw, osqp_cleanup);
  if (r.api_error || !raw) { r.status = QpStatus::SetupFailure; return r; }
  r.api_error = osqp_solve(raw);
  r.raw_status = raw->info->status_val;
  r.iterations = raw->info->iter;
  r.primal_residual = raw->info->prim_res;
  r.dual_residual = raw->info->dual_res;
  r.setup_seconds = raw->info->setup_time;
  r.solve_seconds = raw->info->solve_time + raw->info->polish_time;
  if (r.api_error) { r.status = QpStatus::SolverFailure; return r; }
  switch (r.raw_status) {
    case OSQP_SOLVED: r.status = QpStatus::Solved; break;
    case OSQP_SOLVED_INACCURATE: r.status = QpStatus::Inaccurate; break;
    case OSQP_PRIMAL_INFEASIBLE: case OSQP_PRIMAL_INFEASIBLE_INACCURATE:
      r.status = QpStatus::PrimalInfeasible; break;
    case OSQP_DUAL_INFEASIBLE: case OSQP_DUAL_INFEASIBLE_INACCURATE:
      r.status = QpStatus::DualInfeasible; break;
    case OSQP_MAX_ITER_REACHED: r.status = QpStatus::IterationLimit; break;
    case OSQP_TIME_LIMIT_REACHED: r.status = QpStatus::TimeLimit; break;
    case OSQP_NON_CVX: r.status = QpStatus::NonConvex; break;
    default: r.status = QpStatus::SolverFailure;
  }
  if (r.status != QpStatus::Solved || !raw->solution || !raw->solution->x) return r;
  Eigen::VectorXd x = Eigen::Map<Eigen::VectorXd>(raw->solution->x, n);
  if (!x.allFinite()) { r.status = QpStatus::SolverFailure; return r; }
  const Eigen::VectorXd ax = p.constraints * x;
  if (!ax.allFinite() || !std::isfinite(r.primal_residual) ||
      !std::isfinite(r.dual_residual)) { r.status = QpStatus::SolverFailure; return r; }
  r.violation = 0;
  for (int i = 0; i < m; ++i)
    r.violation = std::max({r.violation, p.lower(i) - ax(i), ax(i) - p.upper(i)});
  if (r.violation > o.acceptance_tolerance) {
    r.status = QpStatus::ConstraintViolation; return r;
  }
  r.velocity = x;
  return r;
}
QpProblem trackingProblem(const Eigen::MatrixXd& j, const Eigen::VectorXd& v, double ridge) {
  if (j.cols() <= 0 || j.rows() != v.size() || !j.allFinite() || !v.allFinite() ||
      !std::isfinite(ridge) || ridge < 0) throw std::invalid_argument("tracking input");
  QpProblem p;
  p.hessian = j.transpose() * j + ridge * Eigen::MatrixXd::Identity(j.cols(), j.cols());
  p.gradient = -j.transpose() * v;
  if (!p.hessian.allFinite() || !p.gradient.allFinite())
    throw std::overflow_error("tracking objective overflow");
  p.constraints.resize(0, j.cols()); p.lower.resize(0); p.upper.resize(0);
  return p;
}
void appendConstraint(QpProblem& p, const Eigen::RowVectorXd& row, double lo, double hi) {
  if (row.size() != p.gradient.size() || !row.allFinite() ||
      !validBound(lo, true) || !validBound(hi, false)) throw std::invalid_argument("constraint");
  const int m = p.lower.size();
  p.constraints.conservativeResize(m + 1, row.size());
  p.constraints.row(m) = row;
  p.lower.conservativeResize(m + 1); p.upper.conservativeResize(m + 1);
  p.lower(m) = lo; p.upper(m) = hi;
}
void appendDamper(QpProblem& p, const Eigen::RowVectorXd& g, double d, double safe, double eta) {
  if (!std::isfinite(d) || !std::isfinite(safe) || safe < 0 || !positive(eta))
    throw std::invalid_argument("damper");
  const double bound = -eta * (d - safe);
  if (!std::isfinite(bound)) throw std::overflow_error("damper bound overflow");
  appendConstraint(p, g, bound, std::numeric_limits<double>::infinity());
}
QpProblem constrainCommand(QpProblem p, const CommandLimits& l, const CommandHistory& s) {
  const int n = p.gradient.size();
  if (!positive(l.dt) || !std::isfinite(l.position_margin) || l.position_margin < 0 ||
      !vectorSize(l.position_lower, n) || !vectorSize(l.position_upper, n) ||
      !vectorSize(l.velocity, n) || !vectorSize(l.acceleration, n) || !vectorSize(l.jerk, n) ||
      !vectorSize(s.measured_position, n) || !vectorSize(s.accepted_position, n) ||
      !vectorSize(s.accepted_velocity, n) || !vectorSize(s.accepted_acceleration, n) ||
      (l.velocity.array() <= 0).any() || (l.acceleration.array() <= 0).any() ||
      (l.jerk.array() <= 0).any()) throw std::invalid_argument("command limits/history");
  for (int i = 0; i < n; ++i) {
    const double qlo = l.position_lower(i) + l.position_margin;
    const double qhi = l.position_upper(i) - l.position_margin;
    if (!std::isfinite(qlo) || !std::isfinite(qhi) ||
        !std::isfinite(qlo - s.measured_position(i)) ||
        !std::isfinite(qhi - s.measured_position(i)) ||
        !std::isfinite(qlo - s.accepted_position(i)) ||
        !std::isfinite(qhi - s.accepted_position(i)) ||
        !std::isfinite(l.dt * l.acceleration(i)) ||
        !std::isfinite(l.dt * s.accepted_acceleration(i)) ||
        !std::isfinite(l.jerk(i) * l.dt * l.dt))
      throw std::overflow_error("command bound intermediate overflow");
    const double lo = std::max({-l.velocity(i), (qlo - s.measured_position(i)) / l.dt,
      (qlo - s.accepted_position(i)) / l.dt,
      s.accepted_velocity(i) - l.acceleration(i) * l.dt,
      s.accepted_velocity(i) + l.dt * s.accepted_acceleration(i) - l.jerk(i) * l.dt * l.dt});
    const double hi = std::min({l.velocity(i), (qhi - s.measured_position(i)) / l.dt,
      (qhi - s.accepted_position(i)) / l.dt,
      s.accepted_velocity(i) + l.acceleration(i) * l.dt,
      s.accepted_velocity(i) + l.dt * s.accepted_acceleration(i) + l.jerk(i) * l.dt * l.dt});
    if (!std::isfinite(lo) || !std::isfinite(hi))
      throw std::overflow_error("command bounds overflow");
    appendConstraint(p, Eigen::MatrixXd::Identity(n, n).row(i), lo, hi);
  }
  return p;
}
QpProblem stoppingProblem(int n) {
  if (n <= 0) throw std::invalid_argument("dof");
  return trackingProblem(Eigen::MatrixXd::Identity(n, n), Eigen::VectorXd::Zero(n), 0);
}
}  // namespace predictive_motion::control
