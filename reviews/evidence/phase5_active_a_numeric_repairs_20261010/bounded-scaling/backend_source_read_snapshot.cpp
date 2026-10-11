#include "predictive_motion_control/reactive_qp.hpp"

#include <osqp.h>

#include <Eigen/Cholesky>
#include <Eigen/Eigenvalues>
#include <algorithm>
#include <chrono>
#include <cmath>
#include <map>
#include <memory>
#include <set>
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
    OSQPCscMatrix_set_data(&matrix, dense.rows(), dense.cols(), values.size(), values.data(),
                           indices.data(), pointers.data());
  }
};
bool positive(double x) { return std::isfinite(x) && x > 0; }
bool validBound(double x, bool lower) {
  return std::isfinite(x) || (std::isinf(x) && (lower ? x < 0 : x > 0));
}
bool vectorSize(const Eigen::VectorXd& v, int n) { return v.size() == n && v.allFinite(); }
}  // namespace
const char* statusName(QpStatus status) {
  switch (status) {
    case QpStatus::Solved:
      return "SOLVED";
    case QpStatus::InvalidInput:
      return "INVALID_INPUT";
    case QpStatus::StaleState:
      return "STALE_STATE";
    case QpStatus::InfeasibleBounds:
      return "INFEASIBLE_BOUNDS";
    case QpStatus::PrimalInfeasible:
      return "PRIMAL_INFEASIBLE";
    case QpStatus::DualInfeasible:
      return "DUAL_INFEASIBLE";
    case QpStatus::IterationLimit:
      return "ITERATION_LIMIT";
    case QpStatus::TimeLimit:
      return "TIME_LIMIT";
    case QpStatus::NonConvex:
      return "NON_CONVEX";
    case QpStatus::SetupFailure:
      return "SETUP_FAILURE";
    case QpStatus::SolverFailure:
      return "SOLVER_FAILURE";
    case QpStatus::Inaccurate:
      return "INACCURATE";
    case QpStatus::ConstraintViolation:
      return "CONSTRAINT_VIOLATION";
  }
  return "UNKNOWN";
}
struct QpWorkspace::Impl {
  OSQPSolver* raw = nullptr;
  int n = 0, m = 0;
  double initial_rho = .1;
  std::vector<OSQPInt> hp, hi, ap, ai;
  std::vector<OSQPFloat> hv, av;
  std::vector<std::string> labels;
  Eigen::VectorXd dual, variable_scale;
  std::string reason;
  void clear() {
    if (raw) osqp_cleanup(raw);
    raw = nullptr;
    n = m = 0;
    hp.clear();
    hi.clear();
    ap.clear();
    ai.clear();
    hv.clear();
    av.clear();
    labels.clear();
    dual.resize(0);
  }
  ~Impl() { clear(); }
};
QpWorkspace::QpWorkspace() : impl_(std::make_unique<Impl>()) {}
QpWorkspace::~QpWorkspace() = default;
void QpWorkspace::reset() {
  impl_->clear();
  impl_->variable_scale.resize(0);
  impl_->reason = "explicit_reset";
}
void QpWorkspace::clearDual() {
  impl_->dual.resize(0);
  impl_->reason = "feedback_dual_reset";
}
namespace {
QpResult solveQpImpl(const QpProblem&, const QpOptions&, const Eigen::VectorXd&,
                     const Eigen::SparseMatrix<double>*, QpWorkspace::Impl*,
                     const std::vector<std::string>*);
}
std::string qpSolverVersion() { return osqp_version(); }
QpResult solveQp(const QpProblem& p, const QpOptions& o) {
  return solveQpWarm(p, o, Eigen::VectorXd{});
}
QpResult solveQpWarm(const QpProblem& p, const QpOptions& o, const Eigen::VectorXd& warm) {
  return solveQpImpl(p, o, warm, nullptr, nullptr, nullptr);
}
QpResult solveQpCertified(const QpProblem& p, const QpOptions& o, const Eigen::VectorXd& warm,
                          const Eigen::SparseMatrix<double>& factor) {
  return solveQpImpl(p, o, warm, &factor, nullptr, nullptr);
}
QpResult solveQpWorkspace(const QpProblem& p, const QpOptions& o, const Eigen::VectorXd& warm,
                          const Eigen::SparseMatrix<double>& factor, QpWorkspace& workspace,
                          const std::vector<std::string>& labels) {
  if (labels.size() != size_t(p.lower.size()) ||
      std::set<std::string>(labels.begin(), labels.end()).size() != labels.size() ||
      std::any_of(labels.begin(), labels.end(), [](const std::string& x) { return x.empty(); })) {
    workspace.reset();
    return {};
  }
  if (workspace.impl_->variable_scale.size()) workspace.reset();
  return solveQpImpl(p, o, warm, &factor, workspace.impl_.get(), &labels);
}
QpResult solveQpScaledWorkspace(const QpProblem& p, const QpOptions& o, const Eigen::VectorXd& seed,
                                const Eigen::SparseMatrix<double>& factor,
                                const Eigen::VectorXd& requested_d, QpWorkspace& workspace,
                                const std::vector<std::string>& labels) {
  QpResult invalid;
  const int n = p.gradient.size(), m = p.lower.size();
  if (n < 1) {
    workspace.reset();
    return invalid;
  }
  const Eigen::VectorXd d =
      requested_d.size() ? requested_d : Eigen::VectorXd(Eigen::VectorXd::Ones(n));
  auto reject = [&]() {
    workspace.reset();
    return invalid;
  };
  if (n < 1 || d.size() != n || !d.allFinite() || (d.array() <= 0).any() || p.hessian.rows() != n ||
      p.hessian.cols() != n || !p.hessian.allFinite() || !p.gradient.allFinite() ||
      p.constraints.rows() != m || p.constraints.cols() != n || !p.constraints.allFinite() ||
      p.upper.size() != m || factor.cols() != n || seed.size() != n || !seed.allFinite() ||
      labels.size() != size_t(m) ||
      std::set<std::string>(labels.begin(), labels.end()).size() != labels.size() ||
      std::any_of(labels.begin(), labels.end(),
                  [](const std::string& value) { return value.empty(); }))
    return reject();
  double hscale = std::max(1., p.hessian.cwiseAbs().maxCoeff());
  Eigen::MatrixXd normalized = p.hessian / hscale;
  if ((normalized - normalized.transpose()).stableNorm() > 1e-12) return reject();
  for (int col = 0; col < factor.outerSize(); ++col)
    for (Eigen::SparseMatrix<double>::InnerIterator it(factor, col); it; ++it)
      if (!std::isfinite(it.value())) return reject();
  Eigen::SparseMatrix<double> original_gram = factor.transpose() * factor;
  Eigen::MatrixXd original_certificate(original_gram);
  if (!original_certificate.allFinite() ||
      (original_certificate / hscale - Eigen::MatrixXd(normalized.selfadjointView<Eigen::Upper>()))
              .stableNorm() > 1e-12)
    return reject();
  QpProblem transformed = p;
  transformed.hessian = d.asDiagonal() * p.hessian * d.asDiagonal();
  transformed.gradient = d.cwiseProduct(p.gradient);
  transformed.constraints = p.constraints * d.asDiagonal();
  Eigen::VectorXd primal = seed.cwiseQuotient(d);
  Eigen::SparseMatrix<double> diagonal(n, n);
  for (int i = 0; i < n; ++i) diagonal.insert(i, i) = d(i);
  Eigen::SparseMatrix<double> transformed_factor = factor * diagonal;
  if (!transformed.hessian.allFinite() || !transformed.gradient.allFinite() ||
      !transformed.constraints.allFinite() || !primal.allFinite())
    return reject();
  if (workspace.impl_->variable_scale.size() != n || workspace.impl_->variable_scale != d) {
    workspace.reset();
    workspace.impl_->variable_scale = d;
  }
  auto result =
      solveQpImpl(transformed, o, primal, &transformed_factor, workspace.impl_.get(), &labels);
  result.minimum_variable_scale = d.minCoeff();
  result.maximum_variable_scale = d.maxCoeff();
  if (result.status != QpStatus::Solved) return result;
  result.velocity = d.cwiseProduct(result.velocity);
  Eigen::VectorXd original_ax = p.constraints * result.velocity;
  if (!result.velocity.allFinite() || !original_ax.allFinite()) {
    result.status = QpStatus::SolverFailure;
    result.velocity.resize(0);
    workspace.reset();
    return result;
  }
  result.violation = 0;
  result.maximum_violation_row = -1;
  for (int i = 0; i < m; ++i) {
    const double value=std::max(p.lower(i)-original_ax(i),original_ax(i)-p.upper(i));
    if(value>result.violation) { result.violation=value;result.maximum_violation_row=i; }
  }
  if (result.violation > o.acceptance_tolerance) {
    result.status = QpStatus::ConstraintViolation;
    result.velocity.resize(0);
    workspace.reset();
  }
  return result;
}
namespace {
QpResult solveQpImpl(const QpProblem& p, const QpOptions& o, const Eigen::VectorXd& warm,
                     const Eigen::SparseMatrix<double>* factor, QpWorkspace::Impl* owner,
                     const std::vector<std::string>* labels) {
  QpResult r;
  struct FailureReset {
    QpWorkspace::Impl* owner;
    QpResult& result;
    ~FailureReset() {
      if (owner && result.status != QpStatus::Solved) {
        owner->clear();
        owner->reason = statusName(result.status);
      }
    }
  } failure_reset{owner, r};

  const int n = p.gradient.size(), m = p.lower.size();
  if (n <= 0 || p.hessian.rows() != n || p.hessian.cols() != n || p.constraints.cols() != n ||
      p.constraints.rows() != m || p.upper.size() != m || !p.hessian.allFinite() ||
      !p.gradient.allFinite() || !p.constraints.allFinite() ||
      !std::isfinite(p.state_age_seconds) || p.state_age_seconds < 0 || o.max_iterations < 1 ||
      !positive(o.absolute_tolerance) || !positive(o.relative_tolerance) ||
      !positive(o.acceptance_tolerance) || !positive(o.time_limit_seconds) ||
      !positive(o.max_state_age_seconds) || !positive(o.initial_rho) ||
      o.initial_rho < 1e-6 || o.initial_rho > 1e6)
    return r;
  if (warm.size() && (warm.size() != n || !warm.allFinite())) return r;
  r.solver_absolute_tolerance = o.absolute_tolerance;
  r.solver_relative_tolerance = o.relative_tolerance;
  r.initial_rho = o.initial_rho;
  if (owner && owner->raw && owner->initial_rho != o.initial_rho) {
    owner->clear();
    owner->reason = "rho_setting";
  }
  const double scale = std::max(1.0, p.hessian.cwiseAbs().maxCoeff());
  const Eigen::MatrixXd normalized = p.hessian / scale;
  if ((normalized - normalized.transpose()).stableNorm() > 1e-12) return r;
  const Eigen::MatrixXd symmetric = normalized.selfadjointView<Eigen::Upper>();
  for (int i = 0; i < m; ++i) {
    if (!validBound(p.lower(i), true) || !validBound(p.upper(i), false) ||
        (std::isfinite(p.lower(i)) && std::abs(p.lower(i)) >= OSQP_INFTY) ||
        (std::isfinite(p.upper(i)) && std::abs(p.upper(i)) >= OSQP_INFTY))
      return r;
    if (p.lower(i) > p.upper(i)) {
      r.status = QpStatus::InfeasibleBounds;
      return r;
    }
  }
  if (p.state_age_seconds > o.max_state_age_seconds) {
    r.status = QpStatus::StaleState;
    return r;
  }
  // Do not rely on solver regularization to hide indefinite input.
  if (factor) {
    if (factor->cols() != n) return r;
    for (int col = 0; col < factor->outerSize(); ++col)
      for (Eigen::SparseMatrix<double>::InnerIterator it(*factor, col); it; ++it)
        if (!std::isfinite(it.value())) return r;
    Eigen::SparseMatrix<double> product = factor->transpose() * (*factor);
    Eigen::MatrixXd certified(product);
    if (!certified.allFinite() || (certified / scale - symmetric).stableNorm() > 1e-12) return r;
  } else {
    // A successful unregularized Cholesky factorization certifies positive
    // definiteness quickly. Semidefinite/indefinite cases retain the original
    // normalized eigenvalue check; no solver regularization hides nonconvexity.
    Eigen::LLT<Eigen::MatrixXd> chol(symmetric);
    if (chol.info() != Eigen::Success || !chol.matrixL().toDenseMatrix().allFinite()) {
      Eigen::SelfAdjointEigenSolver<Eigen::MatrixXd> eig(symmetric, Eigen::EigenvaluesOnly);
      if (eig.info() != Eigen::Success || !eig.eigenvalues().allFinite()) return r;
      if (eig.eigenvalues().minCoeff() < -1e-12) {
        r.status = QpStatus::NonConvex;
        return r;
      }
    }
  }
  // Positive row scaling is an equivalent feasible set. Keep acceptance and
  // stored semantic duals in the ORIGINAL problem's SI row units.
  Eigen::VectorXd row_scale = Eigen::VectorXd::Ones(m);
  Eigen::MatrixXd solver_a = p.constraints;
  if (owner) {
    for (int i = 0; i < m; ++i) {
      double norm = p.constraints.row(i).cwiseAbs().maxCoeff();
      if (norm > 0) {
        row_scale(i) = 1 / norm;
        if (!std::isfinite(row_scale(i))) return r;
        solver_a.row(i) *= row_scale(i);
      }
    }
  }
  if (m) {
    r.minimum_row_scale = row_scale.minCoeff();
    r.maximum_row_scale = row_scale.maxCoeff();
  }
  if (!solver_a.allFinite()) return r;
  Csc h(p.hessian, true), a(solver_a, false);
  r.hessian_nonzeros = h.values.size();
  r.constraint_nonzeros = a.values.size();
  Eigen::VectorXd lower = p.lower, upper = p.upper;
  if (owner) {
    for (int i = 0; i < m; ++i) {
      if (std::isfinite(lower(i))) {
        lower(i) *= row_scale(i);
        if (!std::isfinite(lower(i)) || std::abs(lower(i)) >= OSQP_INFTY) return r;
      }
      if (std::isfinite(upper(i))) {
        upper(i) *= row_scale(i);
        if (!std::isfinite(upper(i)) || std::abs(upper(i)) >= OSQP_INFTY) return r;
      }
    }
  }
  for (int i = 0; i < m; ++i) {
    if (std::isinf(lower(i))) lower(i) = -OSQP_INFTY;
    if (std::isinf(upper(i))) upper(i) = OSQP_INFTY;
  }
  OSQPSettings settings;
  osqp_set_default_settings(&settings);
  settings.verbose = 0;
  settings.warm_starting = warm.size() > 0;
  settings.rho = o.initial_rho;
  settings.max_iter = o.max_iterations;
  settings.eps_abs = o.absolute_tolerance;
  settings.eps_rel = o.relative_tolerance;
  // Use the explicitly supplied solver stopping precision. A global worst-row
  // scale bound overconstrains all rows; acceptance still independently checks
  // EVERY original SI row below, and rejects any insufficiently accurate solve.
  settings.time_limit = o.time_limit_seconds;
  settings.check_termination = 1;
  settings.polishing = 1;
  settings.adaptive_rho = OSQP_ADAPTIVE_RHO_UPDATE_ITERATIONS;
  settings.adaptive_rho_interval = 50;
  OSQPSolver* raw = nullptr;
  std::unique_ptr<OSQPSolver, decltype(&osqp_cleanup)> local(nullptr, osqp_cleanup);
  Eigen::VectorXd dual = Eigen::VectorXd::Zero(m);
  if (owner && labels) {
    r.reset_reason = owner->reason;
    if (warm.size() && owner->n == n && owner->dual.size() == int(owner->labels.size()) &&
        owner->dual.allFinite()) {
      std::map<std::string, double> old;
      for (int i = 0; i < owner->dual.size(); ++i) old.emplace(owner->labels[i], owner->dual(i));
      for (int i = 0; i < m; ++i) {
        auto found = old.find((*labels)[i]);
        if (found != old.end()) {
          dual(i) = found->second / row_scale(i);
          ++r.dual_mapped_rows;
        }
      }
      r.dual_reused = r.dual_mapped_rows > 0;
    }
    bool same = owner->raw && owner->n == n && owner->m == m && owner->hp == h.pointers &&
                owner->hi == h.indices && owner->ap == a.pointers && owner->ai == a.indices;
    if (same) {
      raw = owner->raw;
      r.workspace_reused = true;
      auto begin = std::chrono::steady_clock::now();
      r.api_error = osqp_update_settings(raw, &settings);
      if (!r.api_error && (owner->hv != h.values || owner->av != a.values)) {
        r.matrix_updated = true;
        r.api_error = osqp_update_data_mat(raw, h.values.data(), nullptr, h.values.size(),
                                           a.values.data(), nullptr, a.values.size());
      }
      if (!r.api_error)
        r.api_error = osqp_update_data_vec(raw, p.gradient.data(), lower.data(), upper.data());
      r.update_seconds =
          std::chrono::duration<double>(std::chrono::steady_clock::now() - begin).count();
      if (r.api_error) {
        r.status = QpStatus::SolverFailure;
        return r;
      }
    } else {
      bool existed = owner->raw != nullptr;
      if (existed) r.reset_reason = "matrix_structure";
      owner->clear();
      r.api_error = osqp_setup(&raw, &h.matrix, p.gradient.data(), &a.matrix, lower.data(),
                               upper.data(), m, n, &settings);
      owner->raw = raw;
    }
    owner->initial_rho = o.initial_rho;
    owner->n = n;
    owner->m = m;
    owner->hp = h.pointers;
    owner->hi = h.indices;
    owner->ap = a.pointers;
    owner->ai = a.indices;
    owner->hv = h.values;
    owner->av = a.values;
    owner->labels = *labels;
  } else {
    r.api_error = osqp_setup(&raw, &h.matrix, p.gradient.data(), &a.matrix, lower.data(),
                             upper.data(), m, n, &settings);
    local.reset(raw);
  }
  if (r.api_error || !raw) {
    r.status = QpStatus::SetupFailure;
    return r;
  }
  if (warm.size()) {
    r.api_error = osqp_warm_start(raw, warm.data(), owner ? dual.data() : nullptr);
    if (r.api_error) {
      r.status = QpStatus::SolverFailure;
      return r;
    }
  }
  r.api_error = osqp_solve(raw);
  r.raw_status = raw->info->status_val;
  r.iterations = raw->info->iter;
  r.rho_updates = raw->info->rho_updates;
  r.rho_estimate = raw->info->rho_estimate;
  r.polish_status = raw->info->status_polish;
  r.primal_residual = raw->info->prim_res;
  r.dual_residual = raw->info->dual_res;
  r.setup_seconds = r.workspace_reused ? 0 : raw->info->setup_time;
  r.solve_seconds = raw->info->solve_time + raw->info->polish_time;
  if (r.api_error) {
    r.status = QpStatus::SolverFailure;
    return r;
  }
  switch (r.raw_status) {
    case OSQP_SOLVED:
      r.status = QpStatus::Solved;
      break;
    case OSQP_SOLVED_INACCURATE:
      r.status = QpStatus::Inaccurate;
      break;
    case OSQP_PRIMAL_INFEASIBLE:
    case OSQP_PRIMAL_INFEASIBLE_INACCURATE:
      r.status = QpStatus::PrimalInfeasible;
      break;
    case OSQP_DUAL_INFEASIBLE:
    case OSQP_DUAL_INFEASIBLE_INACCURATE:
      r.status = QpStatus::DualInfeasible;
      break;
    case OSQP_MAX_ITER_REACHED:
      r.status = QpStatus::IterationLimit;
      break;
    case OSQP_TIME_LIMIT_REACHED:
      r.status = QpStatus::TimeLimit;
      break;
    case OSQP_NON_CVX:
      r.status = QpStatus::NonConvex;
      break;
    default:
      r.status = QpStatus::SolverFailure;
  }
  if (r.status != QpStatus::Solved) return r;
  if (!raw->solution || !raw->solution->x) {
    r.status = QpStatus::SolverFailure;
    return r;
  }
  Eigen::VectorXd x = Eigen::Map<Eigen::VectorXd>(raw->solution->x, n);
  if (!x.allFinite()) {
    r.status = QpStatus::SolverFailure;
    return r;
  }
  const Eigen::VectorXd ax = p.constraints * x;
  if (!ax.allFinite() || !std::isfinite(r.primal_residual) || !std::isfinite(r.dual_residual)) {
    r.status = QpStatus::SolverFailure;
    return r;
  }
  r.violation = 0;
  for (int i = 0; i < m; ++i) {
    const double value=std::max(p.lower(i)-ax(i),ax(i)-p.upper(i));
    if(value>r.violation) { r.violation=value;r.maximum_violation_row=i; }
  }
  if (r.violation > o.acceptance_tolerance) {
    r.status = QpStatus::ConstraintViolation;
    return r;
  }
  r.velocity = x;
  if (owner) {
    if (m && raw->solution->y) {
      owner->dual = row_scale.cwiseProduct(Eigen::Map<Eigen::VectorXd>(raw->solution->y, m));
      if (!owner->dual.allFinite()) owner->dual.resize(0);
    } else
      owner->dual = Eigen::VectorXd::Zero(m);
    owner->reason.clear();
  }
  return r;
}
}  // anonymous namespace
QpProblem trackingProblem(const Eigen::MatrixXd& j, const Eigen::VectorXd& v, double ridge) {
  if (j.cols() <= 0 || j.rows() != v.size() || !j.allFinite() || !v.allFinite() ||
      !std::isfinite(ridge) || ridge < 0)
    throw std::invalid_argument("tracking input");
  QpProblem p;
  p.hessian = j.transpose() * j + ridge * Eigen::MatrixXd::Identity(j.cols(), j.cols());
  p.gradient = -j.transpose() * v;
  if (!p.hessian.allFinite() || !p.gradient.allFinite())
    throw std::overflow_error("tracking objective overflow");
  p.constraints.resize(0, j.cols());
  p.lower.resize(0);
  p.upper.resize(0);
  return p;
}
void appendConstraint(QpProblem& p, const Eigen::RowVectorXd& row, double lo, double hi) {
  if (row.size() != p.gradient.size() || !row.allFinite() || !validBound(lo, true) ||
      !validBound(hi, false))
    throw std::invalid_argument("constraint");
  const int m = p.lower.size();
  p.constraints.conservativeResize(m + 1, row.size());
  p.constraints.row(m) = row;
  p.lower.conservativeResize(m + 1);
  p.upper.conservativeResize(m + 1);
  p.lower(m) = lo;
  p.upper(m) = hi;
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
      (l.jerk.array() <= 0).any())
    throw std::invalid_argument("command limits/history");
  for (int i = 0; i < n; ++i) {
    const double qlo = l.position_lower(i) + l.position_margin;
    const double qhi = l.position_upper(i) - l.position_margin;
    if (!std::isfinite(qlo) || !std::isfinite(qhi) ||
        !std::isfinite(qlo - s.measured_position(i)) ||
        !std::isfinite(qhi - s.measured_position(i)) ||
        !std::isfinite(qlo - s.accepted_position(i)) ||
        !std::isfinite(qhi - s.accepted_position(i)) || !std::isfinite(l.dt * l.acceleration(i)) ||
        !std::isfinite(l.dt * s.accepted_acceleration(i)) ||
        !std::isfinite(l.jerk(i) * l.dt * l.dt))
      throw std::overflow_error("command bound intermediate overflow");
    const double lo = std::max(
        {-l.velocity(i), (qlo - s.measured_position(i)) / l.dt,
         (qlo - s.accepted_position(i)) / l.dt, s.accepted_velocity(i) - l.acceleration(i) * l.dt,
         s.accepted_velocity(i) + l.dt * s.accepted_acceleration(i) - l.jerk(i) * l.dt * l.dt});
    const double hi = std::min(
        {l.velocity(i), (qhi - s.measured_position(i)) / l.dt,
         (qhi - s.accepted_position(i)) / l.dt, s.accepted_velocity(i) + l.acceleration(i) * l.dt,
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
