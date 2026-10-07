#include <algorithm>
#include <chrono>
#include <cmath>
#include <numeric>
#include <predictive_motion_control/predictive.hpp>
#include <stdexcept>

namespace predictive_motion::control {
namespace {
using Clock = std::chrono::steady_clock;
double age(Clock::time_point start) {
  return std::chrono::duration<double>(Clock::now() - start).count();
}
bool positive(double x) { return std::isfinite(x) && x > 0; }
bool meshValid(const std::vector<double>& mesh) {
  return !mesh.empty() && std::all_of(mesh.begin(), mesh.end(), positive) &&
         std::isfinite(std::accumulate(mesh.begin(), mesh.end(), 0.0));
}
void stateValid(const PreviewState& x) {
  if (x.q.size() < 1 || x.v.size() != x.q.size() || !x.q.allFinite() || !x.v.allFinite() ||
      !std::isfinite(x.s) || !std::isfinite(x.r))
    throw std::invalid_argument("preview state");
}
void inputValid(const PreviewInput& in) {
  stateValid(in.initial);
  int n = in.initial.q.size();
  if (!meshValid(in.mesh) || !positive(in.control_dt) || in.control_dt > in.mesh.front() ||
      !positive(in.joint_trust) || !positive(in.progress_trust) || !std::isfinite(in.state_age) ||
      in.state_age < 0 || in.previous_acceleration.size() != n ||
      !in.previous_acceleration.allFinite() || !std::isfinite(in.previous_progress_acceleration) ||
      in.nominal.size() != int(in.mesh.size()) * (n + 1) || !in.nominal.allFinite())
    throw std::invalid_argument("preview mesh/history");
  for (const auto* v :
       {&in.limits.lower, &in.limits.upper, &in.limits.velocity, &in.limits.acceleration,
        &in.limits.jerk, &in.limits.posture, &in.accepted_position, &in.accepted_velocity,
        &in.previous_model_acceleration})
    if (v->size() != n || !v->allFinite()) throw std::invalid_argument("preview limits/history");
  if ((in.limits.lower.array() >= in.limits.upper.array()).any() ||
      (in.limits.velocity.array() <= 0).any() || (in.limits.acceleration.array() <= 0).any() ||
      (in.limits.jerk.array() <= 0).any() || !positive(in.limits.progress_speed) ||
      !positive(in.limits.progress_acceleration) || !positive(in.limits.progress_jerk) ||
      !std::isfinite(in.limits.position_margin) || in.limits.position_margin < 0 ||
      !std::isfinite(in.limits.safe_distance) || in.limits.safe_distance < 0)
    throw std::invalid_argument("preview bounds");
  if (!std::isfinite(in.weights.progress_discount_tau) || in.weights.progress_discount_tau < 0)
    throw std::invalid_argument("progress discount tau");
  for (double w :
       {in.weights.tracking, in.weights.velocity, in.weights.acceleration, in.weights.jerk,
        in.weights.posture, in.weights.progress_reward, in.weights.terminal_progress})
    if (!std::isfinite(w) || w < 0) throw std::invalid_argument("preview weights");
}
Eigen::VectorXd pack(const PreviewState& x) {
  int n = x.q.size();
  Eigen::VectorXd out(2 * n + 2);
  out << x.q, x.v, x.s, x.r;
  return out;
}
std::vector<AffineState> dynamics(const PreviewInput& in) {
  int n = in.initial.q.size(), nu = n + 1, nx = 2 * n + 2, nz = nu * in.mesh.size();
  std::vector<AffineState> states{{pack(in.initial), Eigen::MatrixXd::Zero(nx, nz)}};
  for (int k = 0; k < int(in.mesh.size()); ++k) {
    double h = in.mesh[k];
    Eigen::MatrixXd a = Eigen::MatrixXd::Identity(nx, nx), b = Eigen::MatrixXd::Zero(nx, nu);
    a.block(0, n, n, n) = h * Eigen::MatrixXd::Identity(n, n);
    a(2 * n, 2 * n + 1) = h;
    b.topLeftCorner(n, n) = .5 * h * h * Eigen::MatrixXd::Identity(n, n);
    b.block(n, 0, n, n) = h * Eigen::MatrixXd::Identity(n, n);
    b(2 * n, n) = .5 * h * h;
    b(2 * n + 1, n) = h;
    AffineState next{a * states.back().offset, a * states.back().map};
    next.map.middleCols(k * nu, nu) += b;
    if (!next.offset.allFinite() || !next.map.allFinite())
      throw std::overflow_error("preview dynamics");
    states.push_back(std::move(next));
  }
  return states;
}
}  // namespace
PreviewState previewAdvance(const PreviewState& x, const Eigen::VectorXd& u, double h) {
  stateValid(x);
  int n = x.q.size();
  if (!positive(h) || u.size() != n + 1 || !u.allFinite())
    throw std::invalid_argument("preview advance");
  PreviewState y{x.q + h * x.v + .5 * h * h * u.head(n), x.v + h * u.head(n),
                 x.s + h * x.r + .5 * h * h * u(n), x.r + h * u(n)};
  stateValid(y);
  return y;
}
QpProblem constrainPreviewCommand(QpProblem p, const CommandLimits& limits,
                                  const CommandHistory& history) {
  p = constrainCommand(std::move(p), limits, history);
  int n = p.gradient.size();
  double inv = 1 / limits.dt, inv2 = inv * inv;
  if (!std::isfinite(inv2)) throw std::overflow_error("command derivative row scale");
  for (int i = 0; i < n; ++i) {
    double ac = history.accepted_velocity(i) * inv,
           jc = history.accepted_velocity(i) * inv2 + history.accepted_acceleration(i) * inv;
    if (!std::isfinite(ac) || !std::isfinite(jc) || !std::isfinite(ac - limits.acceleration(i)) ||
        !std::isfinite(ac + limits.acceleration(i)) || !std::isfinite(jc - limits.jerk(i)) ||
        !std::isfinite(jc + limits.jerk(i)))
      throw std::overflow_error("command derivative row offset");
    appendConstraint(p, inv * Eigen::MatrixXd::Identity(n, n).row(i), ac - limits.acceleration(i),
                     ac + limits.acceleration(i));
    appendConstraint(p, inv2 * Eigen::MatrixXd::Identity(n, n).row(i), jc - limits.jerk(i),
                     jc + limits.jerk(i));
  }
  return p;
}
std::vector<PreviewState> previewRollout(const PreviewState& initial,
                                         const std::vector<double>& mesh,
                                         const Eigen::VectorXd& controls) {
  stateValid(initial);
  int nu = initial.q.size() + 1;
  if (!meshValid(mesh) || controls.size() != int(mesh.size()) * nu || !controls.allFinite())
    throw std::invalid_argument("preview rollout");
  std::vector<PreviewState> states{initial};
  for (int k = 0; k < int(mesh.size()); ++k)
    states.push_back(previewAdvance(states.back(), controls.segment(k * nu, nu), mesh[k]));
  return states;
}
PreviewAssembly assemblePreview(const PreviewInput& in, const std::vector<PreviewStage>& stages) {
  inputValid(in);
  const int n = in.initial.q.size(), nu = n + 1, nx = 2 * n + 2, N = in.mesh.size(),
            uoffset = in.lifted ? (N + 1) * nx : 0, nz = uoffset + N * nu;
  if (stages.size() != size_t(N + 1)) throw std::invalid_argument("preview stage count");
  PreviewAssembly out;
  out.nominal_states = previewRollout(in.initial, in.mesh, in.nominal);
  out.controls_offset = uoffset;
  out.controls_origin = in.lifted ? in.nominal : Eigen::VectorXd(Eigen::VectorXd::Zero(N * nu));
  out.decision_offset = Eigen::VectorXd::Zero(nz);
  if (in.lifted) {
    for (int k = 0; k <= N; ++k) {
      AffineState node{pack(out.nominal_states[k]), Eigen::MatrixXd::Zero(nx, nz)};
      node.map.middleCols(k * nx, nx).setIdentity();
      out.states.push_back(std::move(node));
      out.decision_offset.segment(k * nx, nx) = pack(out.nominal_states[k]);
    }
    out.decision_offset.tail(N * nu) = in.nominal;
    out.nominal_decision = Eigen::VectorXd::Zero(nz);
  } else {
    out.states = dynamics(in);
    out.nominal_decision = in.nominal;
  }
  QpProblem& p = out.qp;
  p.hessian = Eigen::MatrixXd::Zero(nz, nz);
  p.gradient = Eigen::VectorXd::Zero(nz);
  p.constraints.resize(0, nz);
  p.lower.resize(0);
  p.upper.resize(0);
  p.state_age_seconds = in.state_age;
  std::vector<Eigen::RowVectorXd> rows;
  std::vector<double> lows, highs;
  auto row = [&](const Eigen::RowVectorXd& m, double c, double lo, double hi,
                 const std::string& label) {
    if (!m.allFinite() || !std::isfinite(c) || std::isnan(lo) || std::isnan(hi) ||
        (std::isfinite(lo) && !std::isfinite(lo - c)) ||
        (std::isfinite(hi) && !std::isfinite(hi - c)))
      throw std::overflow_error("preview row");
    rows.push_back(m);
    lows.push_back(lo - c);
    highs.push_back(hi - c);
    out.row_labels.push_back(label);
  };
  auto box = [&](const Eigen::MatrixXd& m, const Eigen::VectorXd& c, const Eigen::VectorXd& lo,
                 const Eigen::VectorXd& hi, const std::string& label) {
    for (int i = 0; i < c.size(); ++i)
      row(m.row(i), c(i), lo(i), hi(i), label + "/" + std::to_string(i));
  };
  std::vector<Eigen::Triplet<double>> factors;
  int factor_rows = 0;
  auto square = [&](const std::string& name, const Eigen::MatrixXd& m, const Eigen::VectorXd& c,
                    double weight) {
    PreviewAssembly::Term t;
    t.name = name;
    t.gradient = 2 * weight * m.transpose() * c;
    t.constant = weight * c.squaredNorm();
    t.factor = m;
    t.offset = c;
    t.weight = weight;
    if (in.capture_dense_terms) t.hessian = 2 * weight * m.transpose() * m;
    if (!t.gradient.allFinite() || !std::isfinite(t.constant) || !std::isfinite(2 * weight) ||
        !m.allFinite())
      throw std::overflow_error("preview objective");
    if (weight > 0) {
      double root = std::sqrt(2 * weight);
      for (int i = 0; i < m.rows(); ++i)
        for (int j = 0; j < m.cols(); ++j)
          if (m(i, j) != 0) {
            double value = root * m(i, j);
            if (!std::isfinite(value)) throw std::overflow_error("preview objective factor");
            factors.emplace_back(factor_rows + i, j, value);
          }
      factor_rows += m.rows();
    }
    p.gradient += t.gradient;
    out.terms.push_back(std::move(t));
  };
  if (in.lifted) {
    box(out.states[0].map, out.states[0].offset, pack(in.initial), pack(in.initial),
        "dynamics/init");
    for (int k = 0; k < N; ++k) {
      double h = in.mesh[k];
      Eigen::MatrixXd a = Eigen::MatrixXd::Identity(nx, nx), b = Eigen::MatrixXd::Zero(nx, nu);
      a.block(0, n, n, n) = h * Eigen::MatrixXd::Identity(n, n);
      a(2 * n, 2 * n + 1) = h;
      b.topLeftCorner(n, n) = .5 * h * h * Eigen::MatrixXd::Identity(n, n);
      b.block(n, 0, n, n) = h * Eigen::MatrixXd::Identity(n, n);
      b(2 * n, n) = .5 * h * h;
      b(2 * n + 1, n) = h;
      Eigen::MatrixXd m = out.states[k + 1].map - a * out.states[k].map;
      m.middleCols(uoffset + k * nu, nu) -= b;
      box(m,
          out.states[k + 1].offset - a * out.states[k].offset -
              b * out.controls_origin.segment(k * nu, nu),
          Eigen::VectorXd::Zero(nx), Eigen::VectorXd::Zero(nx), "dynamics/" + std::to_string(k));
    }
  }
  const Eigen::VectorXd qlo = in.limits.lower.array() + in.limits.position_margin,
                        qhi = in.limits.upper.array() - in.limits.position_margin;
  // First requested endpoint velocity comes from measured v+control_dt*a0.
  // Intersect its actual command derivatives against accepted history; silently
  // treating measured v as accepted v would miss potentially huge command jerk.
  CommandLimits bridge_limits{in.limits.lower,          in.limits.upper, in.limits.velocity,
                              in.limits.acceleration,   in.limits.jerk,  in.control_dt,
                              in.limits.position_margin};
  CommandHistory history{in.initial.q, in.accepted_position, in.accepted_velocity,
                         in.previous_acceleration};
  auto bridge = constrainCommand(stoppingProblem(n), bridge_limits, history);
  Eigen::MatrixXd command_map = Eigen::MatrixXd::Zero(n, nz);
  command_map.middleCols(uoffset, n) = in.control_dt * Eigen::MatrixXd::Identity(n, n);
  for (int i = 0; i < bridge.lower.size(); ++i)
    row(bridge.constraints.row(i) * command_map,
        bridge.constraints.row(i).dot(in.initial.v + in.control_dt * out.controls_origin.head(n)),
        bridge.lower(i), bridge.upper(i),
        "first_command/history_intersection/" + std::to_string(i));
  // Direct derivative rows prevent a velocity-row tolerance being amplified
  // by 1/dt or 1/dt^2 when acceptance checks actual command derivatives.
  Eigen::MatrixXd first_acc = Eigen::MatrixXd::Zero(n, nz);
  first_acc.middleCols(uoffset, n).setIdentity();
  Eigen::VectorXd command_acc_offset =
      (in.initial.v - in.accepted_velocity) / in.control_dt + out.controls_origin.head(n);
  box(first_acc, command_acc_offset, -in.limits.acceleration, in.limits.acceleration,
      "first_command/acceleration_units");
  box(first_acc / in.control_dt, (command_acc_offset - in.previous_acceleration) / in.control_dt,
      -in.limits.jerk, in.limits.jerk, "first_command/jerk_units");
  // Discrete continuation cone on the feedback mesh, at the issued prefix
  // and terminal state. Given |b|<=A, no extremizing recovery K exceeds A/(j*dt)+1.
  const long double recovery = (long double)in.limits.progress_acceleration /
      in.limits.progress_jerk / in.control_dt;
  if (!std::isfinite(recovery) || recovery > 4096)
    throw std::invalid_argument("progress continuation row budget");
  const int recovery_steps = int(std::ceil(recovery)) + 1;
  auto coneRows = [&](const Eigen::RowVectorXd& rm, double rc,
                      const Eigen::RowVectorXd& bm, double bc, const std::string& name) {
    for (int k=1;k<=recovery_steps;++k) {
      const double t = k*in.control_dt;
      const double recovery_gain = .5*in.limits.progress_jerk*in.control_dt*
          in.control_dt*k*(k-1);
      row(rm+t*bm, rc+t*bc, -recovery_gain, INFINITY,
          name+"/lower/"+std::to_string(k));
      row(rm+t*bm, rc+t*bc, -INFINITY, in.limits.progress_speed+recovery_gain,
          name+"/upper/"+std::to_string(k));
    }
  };
  Eigen::RowVectorXd first_b = Eigen::RowVectorXd::Zero(nz);
  first_b(uoffset+n)=1;
  coneRows(in.control_dt*first_b,
      in.initial.r+in.control_dt*out.controls_origin(n), first_b,
      out.controls_origin(n), "progress/continuation/prefix");
  Eigen::RowVectorXd last_b = Eigen::RowVectorXd::Zero(nz);
  last_b(uoffset+(N-1)*nu+n)=1;
  coneRows(out.states.back().map.row(2*n+1), out.states.back().offset(2*n+1),
      last_b, out.controls_origin((N-1)*nu+n), "progress/continuation/terminal");
  for (int k = 0; k <= N; ++k) {
    const auto& affine = out.states[k];
    const auto& nominal = out.nominal_states[k];
    const auto& stage = stages[k];
    double quadrature = (k == N ? in.mesh.back() : in.mesh[k]);
    if (stage.residual.size() < 1 || stage.joint_derivative.rows() != stage.residual.size() ||
        stage.joint_derivative.cols() != n ||
        stage.path_derivative.size() != stage.residual.size() || !stage.residual.allFinite() ||
        !stage.joint_derivative.allFinite() || !stage.path_derivative.allFinite())
      throw std::invalid_argument("preview task linearization");
    Eigen::MatrixXd jm = stage.joint_derivative * affine.map.topRows(n) +
                         stage.path_derivative * affine.map.row(2 * n);
    Eigen::VectorXd jc = stage.residual +
                         stage.joint_derivative * (affine.offset.head(n) - nominal.q) +
                         stage.path_derivative * (affine.offset(2 * n) - nominal.s);
    for (double w :
         {stage.tracking_multiplier, stage.velocity_multiplier, stage.posture_multiplier})
      if (!std::isfinite(w) || w < 0) throw std::invalid_argument("preview stage weights");
    square("tracking/" + std::to_string(k), jm, jc,
           in.weights.tracking * quadrature * stage.tracking_multiplier);
    square("velocity/" + std::to_string(k), affine.map.middleRows(n, n),
           affine.offset.segment(n, n),
           in.weights.velocity * quadrature * stage.velocity_multiplier);
    square("posture/" + std::to_string(k), affine.map.topRows(n),
           affine.offset.head(n) - in.limits.posture,
           in.weights.posture * quadrature * stage.posture_multiplier);
    box(affine.map.topRows(n), affine.offset.head(n), qlo, qhi, "q/" + std::to_string(k));
    box(affine.map.middleRows(n, n), affine.offset.segment(n, n), -in.limits.velocity,
        in.limits.velocity, "v/" + std::to_string(k));
    row(affine.map.row(2 * n), affine.offset(2 * n), 0, 1, "progress/s/" + std::to_string(k));
    row(affine.map.row(2 * n + 1), affine.offset(2 * n + 1), 0, in.limits.progress_speed,
        "progress/r/" + std::to_string(k));
    box(affine.map.topRows(n), affine.offset.head(n), nominal.q.array() - in.joint_trust,
        nominal.q.array() + in.joint_trust, "trust/q/" + std::to_string(k));
    row(affine.map.row(2 * n), affine.offset(2 * n), nominal.s - in.progress_trust,
        nominal.s + in.progress_trust, "trust/s/" + std::to_string(k));
    int scalar_index = 0;
    for (const auto& scalar : stage.scalars) {
      if (!std::isfinite(scalar.value) || !std::isfinite(scalar.minimum) ||
          scalar.gradient.size() != n || !scalar.gradient.allFinite())
        throw std::invalid_argument("preview scalar linearization");
      row(scalar.gradient * affine.map.topRows(n),
          scalar.value + scalar.gradient.dot(affine.offset.head(n) - nominal.q), scalar.minimum,
          INFINITY,
          "scalar/" + std::to_string(k) + "/" +
              (scalar.id.empty() ? "ordinal" + std::to_string(scalar_index) : scalar.id));
      ++scalar_index;
    }
    for (const auto& penalty : stage.penalties) {
      if (!std::isfinite(penalty.value) || !std::isfinite(penalty.target) ||
          !std::isfinite(penalty.weight) || penalty.weight < 0 || penalty.gradient.size() != n ||
          !penalty.gradient.allFinite())
        throw std::invalid_argument("preview scalar penalty");
      square(
          "local_scalar_penalty/" + std::to_string(k), penalty.gradient * affine.map.topRows(n),
          Eigen::VectorXd::Constant(1, penalty.value - penalty.target +
                                           penalty.gradient.dot(affine.offset.head(n) - nominal.q)),
          penalty.weight * quadrature);
    }
  }
  for (int k = 0; k < N; ++k) {
    double h = in.mesh[k];
    Eigen::MatrixXd um = Eigen::MatrixXd::Zero(nu, nz);
    um.middleCols(uoffset + k * nu, nu).setIdentity();
    Eigen::VectorXd lower(nu), upper(nu);
    lower << -in.limits.acceleration, -in.limits.progress_acceleration;
    upper = -lower;
    box(um, out.controls_origin.segment(k * nu, nu), lower, upper,
        "acceleration/" + std::to_string(k));
    square("acceleration/" + std::to_string(k), um, out.controls_origin.segment(k * nu, nu),
           in.weights.acceleration * h);
    Eigen::MatrixXd jm = um;
    Eigen::VectorXd jc = Eigen::VectorXd::Zero(nu);
    double interval;
    if (k == 0) {
      jc.head(n) = -in.previous_model_acceleration;
      jc(n) = -in.previous_progress_acceleration;
      interval = in.control_dt;
    } else {
      jm.middleCols(uoffset + (k - 1) * nu, nu) -= Eigen::MatrixXd::Identity(nu, nu);
      interval = in.mesh[k - 1];
    }
    jc += out.controls_origin.segment(k * nu, nu);
    if (k > 0) jc -= out.controls_origin.segment((k - 1) * nu, nu);
    jm /= interval;
    jc /= interval;
    lower << -in.limits.jerk, -in.limits.progress_jerk;
    upper = -lower;
    box(jm, jc, lower, upper, "jerk/" + std::to_string(k));
    square("jerk/" + std::to_string(k), jm, jc, in.weights.jerk * h);
    // Quadratic Bezier control point: q0+h*v0/2. Endpoints and this point
    // enclose each continuous quadratic component (sufficient, conservative).
    const auto& a = out.states[k];
    Eigen::MatrixXd bm = a.map.topRows(n) + .5 * h * a.map.middleRows(n, n);
    Eigen::VectorXd bc = a.offset.head(n) + .5 * h * a.offset.segment(n, n);
    box(bm, bc, qlo, qhi, "intersample/q/bernstein/" + std::to_string(k));
    row(a.map.row(2 * n) + .5 * h * a.map.row(2 * n + 1),
        a.offset(2 * n) + .5 * h * a.offset(2 * n + 1), 0, 1,
        "intersample/s/bernstein/" + std::to_string(k));
    int interval_scalar = 0;
    for (const auto& scalar : stages[k].scalars) {
      row(scalar.gradient * bm, scalar.value + scalar.gradient.dot(bc - out.nominal_states[k].q),
          scalar.minimum, INFINITY,
          "intersample/scalar/bernstein/" + std::to_string(k) + "/" +
              (scalar.id.empty() ? "ordinal" + std::to_string(interval_scalar) : scalar.id));
      const auto& endpoint = out.states[k + 1];
      row(scalar.gradient * endpoint.map.topRows(n),
          scalar.value + scalar.gradient.dot(endpoint.offset.head(n) - out.nominal_states[k].q),
          scalar.minimum, INFINITY,
          "intersample/scalar/same_affine_endpoint/" + std::to_string(k) + "/" +
              (scalar.id.empty() ? "ordinal" + std::to_string(interval_scalar) : scalar.id));
      ++interval_scalar;
    }
  }
  const auto& final = out.states.back();
  PreviewAssembly::Term reward{
      "progress",
      in.capture_dense_terms ? Eigen::MatrixXd(Eigen::MatrixXd::Zero(nz, nz)) : Eigen::MatrixXd{},
      -in.weights.progress_reward * final.map.row(2 * n).transpose(),
      -in.weights.progress_reward * final.offset(2 * n),
      Eigen::MatrixXd{},
      Eigen::VectorXd{},
      0};
  if (in.weights.progress_discount_tau > 0) {
    reward.gradient.setZero(); reward.constant=0;
    double time=0;
    for(int k=0;k<N;++k) {
      const auto ab=progressDiscountCoefficients(in.mesh[k],in.weights.progress_discount_tau);
      const double decay=std::exp(-time/in.weights.progress_discount_tau);
      const double weight=in.weights.progress_reward*decay;
      reward.gradient -= weight*ab.speed*out.states[k].map.row(2*n+1).transpose();
      reward.gradient(uoffset+k*nu+n) -= weight*ab.acceleration;
      reward.constant -= weight*(ab.speed*out.states[k].offset(2*n+1)+
                                 ab.acceleration*out.controls_origin(k*nu+n));
      time+=in.mesh[k];
    }
    if (!reward.gradient.allFinite() || !std::isfinite(reward.constant))
      throw std::overflow_error("discount accumulated reward");
  }
  p.gradient += reward.gradient;
  out.terms.push_back(reward);
  square("terminal_progress", final.map.row(2 * n),
         Eigen::VectorXd::Constant(1, final.offset(2 * n) - 1), in.weights.terminal_progress);
  if (in.terminal_stop) {
    box(final.map.middleRows(n, n), final.offset.segment(n, n), Eigen::VectorXd::Zero(n),
        Eigen::VectorXd::Zero(n), "terminal/v");
    row(final.map.row(2 * n + 1), final.offset(2 * n + 1), 0, 0, "terminal/r");
  }
  p.constraints.resize(rows.size(), nz);
  p.lower.resize(rows.size());
  p.upper.resize(rows.size());
  for (int i = 0; i < int(rows.size()); ++i) {
    p.constraints.row(i) = rows[i];
    p.lower(i) = lows[i];
    p.upper(i) = highs[i];
  }
  out.convex_factor.resize(factor_rows, nz);
  out.convex_factor.setFromTriplets(factors.begin(), factors.end());
  Eigen::SparseMatrix<double> certified = out.convex_factor.transpose() * out.convex_factor;
  p.hessian = Eigen::MatrixXd(certified);
  if (!p.hessian.allFinite() || !p.gradient.allFinite())
    throw std::overflow_error("preview accumulated objective");
  return out;
}
PreviewShift shiftPreview(const std::vector<double>& old_mesh, const Eigen::VectorXd& old_controls,
                          const std::vector<double>& mesh, int n, double elapsed) {
  PreviewShift result;
  if (n < 1 || !meshValid(mesh)) return result;
  int nu = n + 1;
  result.controls = Eigen::VectorXd::Zero(mesh.size() * nu);
  if (!meshValid(old_mesh) || old_controls.size() != int(old_mesh.size()) * nu ||
      !old_controls.allFinite() || !std::isfinite(elapsed) || elapsed < 0 ||
      elapsed >= std::accumulate(old_mesh.begin(), old_mesh.end(), 0.0))
    return result;
  double new_begin = elapsed;
  for (int k = 0; k < int(mesh.size()); ++k) {
    double old_begin = 0, new_end = new_begin + mesh[k];
    for (int j = 0; j < int(old_mesh.size()); ++j) {
      double old_end = old_begin + old_mesh[j],
             overlap = std::max(0., std::min(new_end, old_end) - std::max(new_begin, old_begin));
      result.controls.segment(k * nu, nu) += overlap / mesh[k] * old_controls.segment(j * nu, nu);
      old_begin = old_end;
    }
    new_begin = new_end;
  }
  result.reset = false;
  return result;
}
double previewLimitViolation(const PreviewInput& in, const Eigen::VectorXd& controls) {
  inputValid(in);
  auto states = previewRollout(in.initial, in.mesh, controls);
  int n = in.initial.q.size(), nu = n + 1;
  double violation = 0;
  auto bound = [&](double value, double lo, double hi) {
    if (!std::isfinite(value)) {
      violation = INFINITY;
      return;
    }
    violation = std::max({violation, lo - value, value - hi});
  };
  const Eigen::VectorXd command = in.initial.v + in.control_dt * controls.head(n);
  const Eigen::VectorXd command_acc = (command - in.accepted_velocity) / in.control_dt,
                        command_jerk = (command_acc - in.previous_acceleration) / in.control_dt;
  for (int i = 0; i < n; ++i) {
    bound(command(i), -in.limits.velocity(i), in.limits.velocity(i));
    bound(command_acc(i), -in.limits.acceleration(i), in.limits.acceleration(i));
    bound(command_jerk(i), -in.limits.jerk(i), in.limits.jerk(i));
    bound(in.accepted_position(i) + in.control_dt * command(i),
          in.limits.lower(i) + in.limits.position_margin,
          in.limits.upper(i) - in.limits.position_margin);
    bound(in.initial.q(i) + in.control_dt * command(i),
          in.limits.lower(i) + in.limits.position_margin,
          in.limits.upper(i) - in.limits.position_margin);
  }
  for (int k = 0; k < int(states.size()); ++k) {
    const auto& x = states[k];
    for (int i = 0; i < n; ++i) {
      bound(x.q(i), in.limits.lower(i) + in.limits.position_margin,
            in.limits.upper(i) - in.limits.position_margin);
      bound(x.v(i), -in.limits.velocity(i), in.limits.velocity(i));
    }
    bound(x.s, 0, 1);
    bound(x.r, 0, in.limits.progress_speed);
  }
  for (int k = 0; k < int(in.mesh.size()); ++k) {
    auto u = controls.segment(k * nu, nu);
    Eigen::VectorXd previous(nu);
    double interval;
    if (k == 0) {
      previous << in.previous_model_acceleration, in.previous_progress_acceleration;
      interval = in.control_dt;
    } else {
      previous = controls.segment((k - 1) * nu, nu);
      interval = in.mesh[k - 1];
    }
    for (int i = 0; i < nu; ++i) {
      double amax = i < n ? in.limits.acceleration(i) : in.limits.progress_acceleration,
             jmax = i < n ? in.limits.jerk(i) : in.limits.progress_jerk;
      bound(u(i), -amax, amax);
      bound((u(i) - previous(i)) / interval, -jmax, jmax);
      double v = i < n ? states[k].v(i) : states[k].r, q = i < n ? states[k].q(i) : states[k].s;
      if (u(i) != 0) {
        double t = -v / u(i);
        if (t > 0 && t < in.mesh[k])
          bound(q + t * v + .5 * t * t * u(i),
                i < n ? in.limits.lower(i) + in.limits.position_margin : 0,
                i < n ? in.limits.upper(i) - in.limits.position_margin : 1);
      }
    }
  }
  // Coarse mesh jerk bounds do not certify continuation on the feedback mesh.
  // Audit the issued prefix and terminal independently.
  const auto prefix = previewAdvance(in.initial, controls.head(nu), in.control_dt);
  auto continuation = [&](const PreviewState& x, double b) {
    bound(x.s, 0, 1);
    bound(x.r, 0, in.limits.progress_speed);
    // Measure tiny native residuals in original units; do not convert a finite
    // endpoint row residual into infinity through strict state-domain rejection.
    const auto stop = progressStopBounds(std::clamp(x.s, 0., 1.),
        std::clamp(x.r, 0., in.limits.progress_speed), b, in.control_dt, in.limits);
    if (!stop.feasible) {
      if (std::isfinite(stop.lower) && std::isfinite(stop.upper) && stop.lower > stop.upper)
        violation = std::max(violation, stop.lower - stop.upper);
      else violation = INFINITY;
    }
  };
  continuation(prefix, controls(n));
  continuation(states.back(), controls((int(in.mesh.size())-1)*nu+n));
  if (in.terminal_stop) {
    for (double v : states.back().v) bound(v, 0, 0);
    bound(states.back().r, 0, 0);
  }
  return violation;
}
PreviewResult solvePreview(PreviewInput in, const PreviewLinearizer& linearize,
                           const PreviewValidator& validate, const ScpOptions& options,
                           QpWorkspace* workspace, const PreviewConsistency& consistency,
                           const PreviewQpDiagnostic& diagnostic) {
  PreviewResult result;
  const auto begin = Clock::now();
  QpWorkspace local;
  QpWorkspace& active = workspace ? *workspace : local;
  struct ResetFailure {
    QpWorkspace& w;
    PreviewResult& r;
    ~ResetFailure() {
      if (r.status != QpStatus::Solved) w.reset();
    }
  } reset_failure{active, result};
  try {
    inputValid(in);
    if (!linearize || !validate || options.max_iterations < 1 || !positive(options.min_trust) ||
        !positive(options.step_tolerance) || !positive(options.violation_tolerance) ||
        !positive(options.wall_limit) || !positive(options.shrink) || options.shrink >= 1)
      return result;
    const double initial_age = in.state_age;
    Eigen::VectorXd last, last_decision, last_offset;
    std::vector<PreviewState> last_states;
    for (int i = 0; i < options.max_iterations; ++i) {
      ScpIteration log;
      log.trust = in.joint_trust;
      auto t = Clock::now();
      auto states = previewRollout(in.initial, in.mesh, in.nominal);
      auto stages = linearize(states);
      log.linearization_s = age(t);
      t = Clock::now();
      in.state_age = initial_age + age(begin);
      auto assembly = assemblePreview(in, stages);
      log.assembly_s = age(t);
      log.variables = assembly.qp.gradient.size();
      log.rows = assembly.qp.lower.size();
      Eigen::VectorXd nominal_rows = assembly.qp.constraints * assembly.nominal_decision;
      for (int j = 0; j < nominal_rows.size(); ++j)
        log.nominal_row_violation =
            std::max({log.nominal_row_violation, assembly.qp.lower(j) - nominal_rows(j),
                      nominal_rows(j) - assembly.qp.upper(j)});
      if (age(begin) > options.wall_limit) {
        log.status = QpStatus::TimeLimit;
        result.iterations.push_back(log);
        result.status = QpStatus::TimeLimit;
        break;
      }
      assembly.qp.state_age_seconds = initial_age + age(begin);
      QpOptions qp = options.qp;
      qp.time_limit_seconds =
          std::min(qp.time_limit_seconds, std::max(1e-9, options.wall_limit - age(begin)));
      auto qp_begin = Clock::now();
      auto solution = in.variable_scale.size()
                          ? solveQpScaledWorkspace(assembly.qp, qp, assembly.nominal_decision,
                                                   assembly.convex_factor, in.variable_scale,
                                                   active, assembly.row_labels)
                          : solveQpWorkspace(assembly.qp, qp, assembly.nominal_decision,
                                             assembly.convex_factor, active, assembly.row_labels);

      if (diagnostic) diagnostic(assembly, solution);
      log.qp_original_row_violation = solution.violation;
      if(solution.maximum_violation_row>=0 && solution.maximum_violation_row<int(assembly.row_labels.size()))
        log.qp_maximum_violation_row=assembly.row_labels[solution.maximum_violation_row];
      log.qp_wrapper_s = age(qp_begin);
      log.hessian_nonzeros = solution.hessian_nonzeros;
      log.constraint_nonzeros = solution.constraint_nonzeros;
      log.rho_updates = solution.rho_updates;
      log.polish_status = solution.polish_status;
      log.workspace_reused = solution.workspace_reused;
      log.matrix_updated = solution.matrix_updated;
      log.dual_reused = solution.dual_reused;
      log.dual_mapped_rows = solution.dual_mapped_rows;
      log.qp_update_s = solution.update_seconds;
      log.reset_reason = solution.reset_reason;
      log.status = solution.status;
      log.qp_setup_s = solution.setup_seconds;
      log.qp_solve_s = solution.solve_seconds;
      log.qp_iterations = solution.iterations;
      log.qp_raw_status = solution.raw_status;
      log.solver_absolute_tolerance = solution.solver_absolute_tolerance;
      log.solver_relative_tolerance = solution.solver_relative_tolerance;
      log.initial_rho = solution.initial_rho;
      log.rho_estimate = solution.rho_estimate;
      log.minimum_row_scale = solution.minimum_row_scale;
      log.maximum_row_scale = solution.maximum_row_scale;
      log.minimum_variable_scale = solution.minimum_variable_scale;
      log.maximum_variable_scale = solution.maximum_variable_scale;
      log.qp_primal_residual = solution.primal_residual;
      log.qp_dual_residual = solution.dual_residual;
      if (solution.status != QpStatus::Solved) {
        result.iterations.push_back(log);
        result.status = solution.status;
        break;
      }
      Eigen::VectorXd candidate_controls =
          assembly.controls_origin + solution.velocity.tail(in.nominal.size());
      auto candidate = previewRollout(in.initial, in.mesh, candidate_controls);
      t = Clock::now();
      double true_violation = validate(candidate, candidate_controls);
      log.validation_checked = true;
      log.violation = std::isfinite(true_violation)
                          ? std::max(previewLimitViolation(in, candidate_controls), true_violation)
                          : std::numeric_limits<double>::quiet_NaN();
      log.validation_s = age(t);
      log.step = (candidate_controls - in.nominal).lpNorm<Eigen::Infinity>();
      log.diagnostic_controls = candidate_controls;
      if (log.violation <= options.violation_tolerance && consistency) {
        log.consistency_ratio = consistency(states, candidate, stages);
        log.consistency_checked = true;
      }
      result.iterations.push_back(log);
      if (!std::isfinite(true_violation) || true_violation < 0 ||
          (log.consistency_checked &&
           (!std::isfinite(log.consistency_ratio) || log.consistency_ratio < 0))) {
        result.status = QpStatus::InvalidInput;
        break;
      }
      if (age(begin) > options.wall_limit) {
        result.status = QpStatus::TimeLimit;
        break;
      }
      if (initial_age + age(begin) > options.qp.max_state_age_seconds) {
        result.status = QpStatus::StaleState;
        break;
      }
      if (log.violation > options.violation_tolerance) {
        active.reset();
        in.joint_trust *= options.shrink;
        in.progress_trust *= options.shrink;
        result.status = QpStatus::ConstraintViolation;
        if (in.joint_trust < options.min_trust) break;
        continue;
      }
      last = candidate_controls;
      last_decision = solution.velocity;
      last_offset = assembly.decision_offset;
      last_states = std::move(candidate);
      in.nominal = last;
      result.status = QpStatus::Solved;
      if (log.step < options.step_tolerance ||
          (log.consistency_checked && log.consistency_ratio <= 1) ||
          i == options.max_iterations - 1) {
        result.termination_reason =
            log.consistency_checked && log.consistency_ratio <= 1
                ? "MODEL_CONSISTENT_FEASIBLE_ITERATE"
                : log.step < options.step_tolerance
                    ? "SMALL_CONTROL_STEP_FEASIBLE_ITERATE"
                    : "SCP_ITERATION_BUDGET_FEASIBLE_ITERATE";
        result.controls = std::move(last);
        result.decision = std::move(last_decision);
        result.decision_offset = std::move(last_offset);
        result.states = std::move(last_states);
        break;
      }
    }
  } catch (const std::exception&) {
    result.status = QpStatus::InvalidInput;
  }
  if (result.status != QpStatus::Solved)
    result.termination_reason = statusName(result.status);
  result.elapsed = age(begin);
  return result;
}
ProgressDiscountCoefficients progressDiscountCoefficients(double duration, double tau) {
  if (!positive(duration) || !positive(tau))
    throw std::invalid_argument("progress discount cell");
  const long double h = duration, t = tau, x = h/t;
  const long double A = -t*std::expm1(-x);
  long double B;
  if (x < 1e-3L) {
    // Stable expansion of [1-(1+x)exp(-x)]/x^2, avoiding large-tau cancellation.
    long double series=.5L, power=1, factorial=2;
    for(int n=3;n<=13;++n) {
      power*=x; factorial*=n;
      series+=(n%2 ? -1.L : 1.L)*(n-1)*power/factorial;
    }
    B=h*h*series;
  } else B=t*t*(-std::expm1(-x)-x*std::exp(-x));
  if (!std::isfinite(A) || !std::isfinite(B) || A<0 || B<0 ||
      A>std::numeric_limits<double>::max() || B>std::numeric_limits<double>::max())
    throw std::overflow_error("progress discount coefficients");
  return {static_cast<double>(A),static_cast<double>(B)};
}
ProgressStop progressStopBounds(double s, double r, double previous_b, double dt,
                                const PreviewLimits& limits) {
  ProgressStop out;
  if (!std::isfinite(s) || !std::isfinite(r) || !std::isfinite(previous_b) || !positive(dt) ||
      s < 0 || s > 1 || r < 0 || r > limits.progress_speed ||
      !positive(limits.progress_speed) || !positive(limits.progress_acceleration) ||
      !positive(limits.progress_jerk)) return out;
  // Exact discrete speed cone: after the selected b, recover toward zero at
  // maximum jerk. The worst integer K lies on either side of the stationary point.
  // Long double intermediates avoid double dt^2 underflow and derived overflow.
  const long double h = dt, j = limits.progress_jerk;
  auto cone = [&](long double distance) {
    const long double z = std::max(0.L, std::sqrt(2 * distance / j) / h - 1);
    auto value = [&](long double k) {
      return -distance / (h * (k + 1)) - (j * h / 2) * k;
    };
    const long double exact = std::max(value(std::floor(z)), value(std::ceil(z)));
    // Keep a floating point interior margin when recovering from a nonzero
    // speed. Without this, roundoff can turn an exactly viable next state into
    // an empty interval on the following call. At zero the exact bound is zero.
    return distance == 0 ? 0.L : std::min(0.L, exact +
        64 * std::numeric_limits<double>::epsilon() * std::max(std::abs(exact), j*h));
  };
  const long double lo = std::max({-(long double)limits.progress_acceleration,
      (long double)previous_b - j*h, cone(r)});
  const long double hi = std::min({(long double)limits.progress_acceleration,
      (long double)previous_b + j*h, -cone((long double)limits.progress_speed-r),
      ((1.L-s)/h-r)*2/h});
  if (!std::isfinite(lo) || !std::isfinite(hi) ||
      std::abs(lo) > std::numeric_limits<double>::max() ||
      std::abs(hi) > std::numeric_limits<double>::max()) return out;
  out.lower = static_cast<double>(lo);
  out.upper = static_cast<double>(hi);
  if (lo > hi) return out;
  out.feasible = true;
  out.acceleration = std::clamp(-r / dt, out.lower, out.upper);
  return out;
}
}  // namespace predictive_motion::control
