#include <yaml-cpp/yaml.h>

#include <Eigen/SVD>
#include <algorithm>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <pinocchio/spatial/explog.hpp>
#include <random>
#include <set>
#include <stdexcept>

#include "observation_snapshot.hpp"
#include "predictive_motion_control/ik.hpp"
#include "predictive_motion_kinematics/robot_kinematics.hpp"
#include "predictive_motion_sim/plant.hpp"
using namespace predictive_motion;
using namespace predictive_motion::control;
namespace fs = std::filesystem;
struct Settings {
  YAML::Node y;
  double get(const char* key) const { return y[key].as<double>(); }
  void validate() const {
    for (const auto* key :
         {"period", "rotation_length_scale", "feedback_gain", "adaptive_sigma_threshold",
          "path_seconds", "completion_position_tolerance", "completion_rotation_tolerance",
          "peak_position_tolerance", "peak_rotation_tolerance", "sweep_twist_norm"})
      if (!std::isfinite(get(key)) || get(key) <= 0)
        throw std::invalid_argument(std::string("Invalid positive configuration: ") + key);
    for (const auto* key :
         {"warmup_seconds", "settle_seconds", "nominal_joint_amplitude", "near_joint_amplitude",
          "objective_speed_weight", "objective_intervention_weight", "objective_failure_penalty"})
      if (!std::isfinite(get(key)) || get(key) < 0)
        throw std::invalid_argument(std::string("Invalid nonnegative configuration: ") + key);
    if (get("search_margin") < 0 || get("search_margin") >= .5 ||
        !std::isfinite(get("search_margin")))
      throw std::invalid_argument("Invalid search margin");
    if (!std::isfinite(get("near_quantile")) || !std::isfinite(get("nominal_quantile")) ||
        get("near_quantile") < 0 || get("nominal_quantile") > 1 ||
        get("near_quantile") >= get("nominal_quantile"))
      throw std::invalid_argument("Invalid search quantiles");
    if (y["search_samples"].as<int>() < 100 || y["search_samples"].as<int>() > 1000000 ||
        y["sweep_points"].as<int>() < 2 || y["sweep_points"].as<int>() > 1000000)
      throw std::invalid_argument("Invalid search/sweep count");
    if (get("rank_relative_tolerance") < 0 || get("rank_relative_tolerance") >= 1 ||
        !std::isfinite(get("rank_relative_tolerance")))
      throw std::invalid_argument("Invalid rank tolerance");
    if ((get("path_seconds") + get("settle_seconds") + get("warmup_seconds")) / get("period") >
        10000000)
      throw std::invalid_argument("Excessive step count");
    for (const auto* key : {"path_seconds", "settle_seconds", "warmup_seconds"})
      if (std::abs(get(key) / get("period") - std::round(get(key) / get("period"))) > 1e-8)
        throw std::invalid_argument("Duration must be period aligned");
    auto dev = y["development_seeds"].as<std::vector<uint32_t>>(),
         eval = y["evaluation_seeds"].as<std::vector<uint32_t>>();
    if (dev.empty() || eval.empty()) throw std::invalid_argument("Empty trial seeds");
    std::set<uint32_t> seeds;
    for (auto seed : dev)
      if (!seeds.insert(seed).second) throw std::invalid_argument("Duplicate development seed");
    for (auto seed : eval)
      if (!seeds.insert(seed).second)
        throw std::invalid_argument("Overlapping/duplicate evaluation seed");
    std::set<double> candidates;
    for (double value : y["damping_candidates"].as<std::vector<double>>())
      if (!std::isfinite(value) || value <= 0 || !candidates.insert(value).second)
        throw std::invalid_argument("Invalid damping candidates");
    if (candidates.empty()) throw std::invalid_argument("Empty damping candidates");
  }
};
struct Candidate {
  Eigen::VectorXd q;
  double sigma;
  int index;
};
struct Pair {
  Candidate nominal, near;
};
struct MethodRun {
  std::string name;
  Options options;
};
struct Trial {
  std::string method, kind, code;
  uint32_t seed;
  double damping, mean_p = 0, mean_r = 0, peak_p = 0, peak_r = 0, final_p = 0, final_r = 0;
  double raw_max = 0, accepted_max = 0, executed_max = 0, objective = 0;
  int interventions = 0, steps = 0, measured_velocity_violations = 0,
      measured_position_violations = 0;
};
std::ofstream output(const fs::path& p) {
  std::ofstream f(p);
  if (!f) throw std::runtime_error("Cannot write " + p.string());
  f.exceptions(std::ios::badbit | std::ios::failbit);
  f << std::setprecision(17);
  return f;
}
Eigen::VectorXd vector(const std::vector<double>& values) {
  return Eigen::Map<const Eigen::VectorXd>(values.data(), values.size());
}
void values(std::ostream& f, const Eigen::VectorXd& q) {
  for (double x : q) f << ',' << x;
}
void columns(std::ostream& f, const std::string& name, int n) {
  for (int i = 0; i < n; ++i) f << ',' << name << '_' << i;
}
Eigen::MatrixXd weighted(const Eigen::MatrixXd& j, double length) {
  Eigen::MatrixXd a = j;
  a.bottomRows(3) *= length;
  return a;
}
Eigen::VectorXd weightedTwist(const Vector6& b, double length) {
  Eigen::VectorXd result = b;
  result.tail(3) *= length;
  return result;
}
void initialize(Plant& plant, const Eigen::VectorXd& q) {
  mj_resetData(plant.model(), plant.data());
  for (int i = 0; i < q.size(); ++i) {
    int j = mj_name2id(plant.model(), mjOBJ_JOINT, plant.names()[i].c_str());
    plant.data()->qpos[plant.model()->jnt_qposadr[j]] = q[i];
  }
  plant.command(plant.names(), std::vector<double>(q.data(), q.data() + q.size()));
  mj_forward(plant.model(), plant.data());
}
Pose measuredTcp(Plant& p, mjData* snapshot, const RobotConfig& c) {
  return observeTcp(p, snapshot, c, c.tcp_parent_frame);
}
Pair search(RobotKinematics& k, Plant& p, const Settings& s, const Eigen::VectorXd& lo,
            const Eigen::VectorXd& hi, uint32_t seed, const fs::path& out) {
  std::mt19937 rng(seed);
  std::vector<Candidate> pool;
  auto f = output(out / ("search_" + std::to_string(seed) + ".csv"));
  f << "index,eligible,sigma_min,sigma_max,condition";
  columns(f, "q", lo.size());
  f << '\n';
  const int count = s.y["search_samples"].as<int>();
  for (int i = 0; i < count; ++i) {
    Eigen::VectorXd q(lo.size());
    for (int j = 0; j < q.size(); ++j) {
      const double u = static_cast<double>(rng()) / 4294967295.;
      const double margin = s.get("search_margin");
      q[j] = lo[j] + (hi[j] - lo[j]) * (margin + (1 - 2 * margin) * u);
    }
    Eigen::JacobiSVD<Eigen::MatrixXd> svd(
        weighted(k.tcpJacobian(q, Reference::Local), s.get("rotation_length_scale")));
    const auto sigma = svd.singularValues();
    initialize(p, q);
    bool eligible = true;
    for (int c = 0; c < p.data()->ncon; ++c)
      if (p.data()->contact[c].dist < 0) eligible = false;
    f << i << ',' << eligible << ',' << sigma.tail(1)[0] << ',' << sigma[0] << ','
      << sigma[0] / sigma.tail(1)[0];
    values(f, q);
    f << '\n';
    if (eligible) pool.push_back({q, sigma.tail(1)[0], i});
  }
  if (pool.size() < 100) throw std::runtime_error("Insufficient contact-free search candidates");
  std::sort(pool.begin(), pool.end(),
            [](const Candidate& a, const Candidate& b) { return a.sigma < b.sigma; });
  auto choose = [&](const char* key) {
    return pool[static_cast<size_t>(s.get(key) * (pool.size() - 1))];
  };
  Pair pair{choose("nominal_quantile"), choose("near_quantile")};
  auto stats = output(out / ("search_" + std::to_string(seed) + "_selection.yaml"));
  stats << "seed: " << seed << "\nsearched: " << count << "\neligible: " << pool.size()
        << "\nminimum_sigma: " << pool.front().sigma
        << "\nmedian_sigma: " << pool[pool.size() / 2].sigma
        << "\np95_sigma: " << pool[static_cast<size_t>(.95 * (pool.size() - 1))].sigma
        << "\nnominal_index: " << pair.nominal.index << "\nnominal_sigma: " << pair.nominal.sigma
        << "\nnear_index: " << pair.near.index << "\nnear_sigma: " << pair.near.sigma << '\n';
  f.flush();
  stats.flush();
  return pair;
}
void sweep(RobotKinematics& k, const Settings& s, const Pair& pair, uint32_t seed,
           const std::vector<MethodRun>& methods, const fs::path& out) {
  auto f = output(out / ("sweep_" + std::to_string(seed) + ".csv"));
  f << "fraction,method,damping_candidate,damping,sigma_min,condition,rank,requested_dq_norm,task_"
       "residual";
  columns(f, "q", pair.near.q.size());
  columns(f, "scaled_twist", 6);
  columns(f, "requested_dq", pair.near.q.size());
  f << '\n';
  const int count = s.y["sweep_points"].as<int>();
  for (int step = 0; step < count; ++step) {
    double u = static_cast<double>(step) / (count - 1);
    Eigen::VectorXd q = (1 - u) * pair.near.q + u * pair.nominal.q;
    Eigen::MatrixXd a =
        weighted(k.tcpJacobian(q, Reference::Local), s.get("rotation_length_scale"));
    Eigen::JacobiSVD<Eigen::MatrixXd> svd(a, Eigen::ComputeThinU);
    Eigen::VectorXd twist = s.get("sweep_twist_norm") * svd.matrixU().col(5);
    for (const auto& method : methods) {
      auto r = solve(a, twist, method.options);
      f << u << ',' << method.name << ',' << method.options.damping << ',' << r.damping << ','
        << r.singular_values[5] << ',' << r.condition << ',' << r.rank << ',' << r.dq.norm() << ','
        << r.task_residual;
      values(f, q);
      values(f, twist);
      values(f, r.dq);
      f << '\n';
    }
  }
  f.flush();
}
Trial track(RobotKinematics& k, Plant& p, const RobotConfig& siteConfig, const Settings& s,
            const Eigen::VectorXd& lo, const Eigen::VectorXd& hi, const Eigen::VectorXd& vmax,
            const Candidate& start, uint32_t seed, const std::string& kind, const MethodRun& method,
            const fs::path& out) {
  const int n = lo.size();
  std::unique_ptr<mjData, decltype(&mj_deleteData)> snapshot(mj_makeData(p.model()), mj_deleteData);
  if (!snapshot) throw std::runtime_error("Pose snapshot allocation failed");
  const double dt = s.get("period"), duration = s.get("path_seconds");
  const bool weak = kind == "weak_direction";
  Vector6 generator = Vector6::Zero();
  const Pose initialPose = k.tcpPose(start.q);
  if (weak) {
    if (!std::isfinite(s.get("weak_reference_amplitude")) || s.get("weak_reference_amplitude") <= 0)
      throw std::invalid_argument("Invalid weak reference amplitude");
    Eigen::JacobiSVD<Eigen::MatrixXd> svd(
        weighted(k.tcpJacobian(start.q, Reference::Local), s.get("rotation_length_scale")),
        Eigen::ComputeThinU);
    generator = svd.matrixU().col(5);
    generator.tail(3) /= s.get("rotation_length_scale");
    auto referenceLog =
        output(out / ("weak_reference_" + std::to_string(seed) + "_" + method.name + ".yaml"));
    referenceLog << "amplitude: " << s.get("weak_reference_amplitude") << "\nduration: " << duration
                 << "\nsigma_min: " << svd.singularValues()[5] << "\ngenerator_linear_angular: [";
    for (int i = 0; i < 6; ++i) referenceLog << (i ? ", " : "") << generator[i];
    referenceLog << "]\ninitial_xyz: [";
    for (int i = 0; i < 3; ++i) referenceLog << (i ? ", " : "") << initialPose.translation()[i];
    referenceLog << "]\ninitial_xyzw: [";
    Eigen::Vector4d quat = Eigen::Quaterniond(initialPose.rotation()).coeffs();
    for (int i = 0; i < 4; ++i) referenceLog << (i ? ", " : "") << quat[i];
    referenceLog << "]\n";
    referenceLog.flush();
  }
  Trial result;
  result.seed = seed;
  result.kind = kind;
  result.method = method.name;
  result.damping = method.options.damping;
  initialize(p, start.q);
  for (int i = 0; i < std::llround(s.get("warmup_seconds") / dt); ++i) p.step();
  Eigen::VectorXd qcommand = start.q;
  std::mt19937 rng(seed + 77);
  Eigen::VectorXd amplitude(n);
  for (int i = 0; i < n; ++i) {
    const double maxamplitude =
        kind == "nominal" ? s.get("nominal_joint_amplitude") : s.get("near_joint_amplitude");
    const double sign = (rng() % 2) ? 1 : -1;
    amplitude[i] =
        sign * std::min(maxamplitude, .5 * std::min(start.q[i] - lo[i], hi[i] - start.q[i]));
  }
  auto reference = [&](double time) {
    double u = std::clamp(time / duration, 0., 1.);
    // One closed, smooth joint-space excursion; always feasible within intersection bounds.
    double wave = .5 * (1 - std::cos(2 * M_PI * u));
    double speed = time < duration ? M_PI / duration * std::sin(2 * M_PI * u) : 0.;
    return std::pair<Eigen::VectorXd, Eigen::VectorXd>{start.q + wave * amplitude,
                                                       speed * amplitude};
  };
  auto weakReference = [&](double time) {
    double u = std::clamp(time / duration, 0., 1.);
    double displacement = s.get("weak_reference_amplitude") * .5 * (1 - std::cos(2 * M_PI * u));
    double speed = time < duration ? s.get("weak_reference_amplitude") * M_PI / duration *
                                         std::sin(2 * M_PI * u)
                                   : 0.;
    return std::pair<Pose, Vector6>{initialPose * pinocchio::exp6(generator * displacement),
                                    generator * speed};
  };
  std::string filename = kind + "_" + std::to_string(seed) + "_" + method.name + "_" +
                         std::to_string(method.options.damping) + ".csv";
  auto f = output(out / filename);
  f << "time_before,time_after,method,damping,sigma_min,condition,rank,requested_task_residual,"
       "position_error,rotation_error,velocity_intervention,position_intervention,measured_"
       "velocity_violation,measured_position_violation";
  for (const auto& name : {"q_before", "requested_dq", "accepted_dq", "accepted_q_target",
                           "executed_q", "executed_dq", "reference_q"})
    columns(f, name, n);
  columns(f, "desired_twist_body", 6);
  columns(f, "residual", 6);
  columns(f, "actual_tcp_xyz", 3);
  columns(f, "desired_tcp_xyz", 3);
  columns(f, "actual_tcp_xyzw", 4);
  columns(f, "desired_tcp_xyzw", 4);
  f << '\n';
  const int steps = std::llround((duration + s.get("settle_seconds")) / dt);
  result.code = "COMPLETED";
  for (int step = 0; step < steps; ++step) {
    std::string stage = "CONTROLLER_EXCEPTION";
    try {
      double time = step * dt;
      auto [qref, dqref] = reference(time);
      Eigen::VectorXd q = vector(p.positions());
      auto actual = k.tcpPose(q);
      auto desired = k.tcpPose(qref);
      Vector6 body;
      if (weak) {
        auto desiredPair = weakReference(time);
        desired = desiredPair.first;
        body = desiredPair.second;
        qref = start.q;
      } else
        body = k.tcpJacobian(qref, Reference::Local) * dqref;
      Vector6 e = logResidual(actual, desired);
      Eigen::MatrixXd a = weighted(-k.residualJacobian(q, desired), s.get("rotation_length_scale"));
      Vector6 rhs =
          s.get("feedback_gain") * e + desiredBodyResidualJacobian(actual, desired) * body;
      stage = "SOLVER_EXCEPTION";
      auto r = solve(a, weightedTwist(rhs, s.get("rotation_length_scale")), method.options);
      stage = "CONTROLLER_EXCEPTION";
      // Persistent position-target integrator, common componentwise velocity/position guard.
      Eigen::VectorXd accepted = r.dq.cwiseMax(-vmax).cwiseMin(vmax);
      bool velocity = (accepted - r.dq).norm() > 1e-12;
      Eigen::VectorXd next = qcommand + dt * accepted;
      Eigen::VectorXd guarded = next.cwiseMax(lo).cwiseMin(hi);
      bool position = (guarded - next).norm() > 1e-12;
      accepted = (guarded - qcommand) / dt;
      qcommand = guarded;
      p.command(k.jointNames(), std::vector<double>(qcommand.data(), qcommand.data() + n));
      stage = "PLANT_NUMERICAL_EXCEPTION";
      p.step();
      stage = "CONTROLLER_EXCEPTION";
      Eigen::VectorXd measured = vector(p.positions()), speed = vector(p.velocities());
      auto [nextref, unused] = reference(time + dt);
      (void)unused;
      if (weak) {
        desired = weakReference(time + dt).first;
        nextref = start.q;
      } else
        desired = k.tcpPose(nextref);
      actual = measuredTcp(p, snapshot.get(), siteConfig);
      const double perror = (actual.translation() - desired.translation()).norm();
      const double rerror =
          pinocchio::log3(actual.rotation().transpose() * desired.rotation()).norm();
      bool measuredVelocity = (speed.cwiseAbs().array() > vmax.array() + 1e-9).any();
      bool measuredPosition = (measured.array() < lo.array() - 1e-9).any() ||
                              (measured.array() > hi.array() + 1e-9).any();
      result.mean_p += perror;
      result.mean_r += rerror;
      result.peak_p = std::max(result.peak_p, perror);
      result.peak_r = std::max(result.peak_r, rerror);
      result.final_p = perror;
      result.final_r = rerror;
      result.raw_max = std::max(result.raw_max, r.dq.cwiseAbs().maxCoeff());
      result.accepted_max = std::max(result.accepted_max, accepted.cwiseAbs().maxCoeff());
      result.executed_max = std::max(result.executed_max, speed.cwiseAbs().maxCoeff());
      result.interventions += velocity || position;
      result.measured_velocity_violations += measuredVelocity;
      result.measured_position_violations += measuredPosition;
      result.steps++;
      result.objective += s.get("objective_speed_weight") * accepted.norm();
      f << time << ',' << time + dt << ',' << method.name << ',' << r.damping << ','
        << r.singular_values[5] << ',' << r.condition << ',' << r.rank << ',' << r.task_residual
        << ',' << perror << ',' << rerror << ',' << velocity << ',' << position << ','
        << measuredVelocity << ',' << measuredPosition;
      values(f, q);
      values(f, r.dq);
      values(f, accepted);
      values(f, qcommand);
      values(f, measured);
      values(f, speed);
      values(f, nextref);
      values(f, body);
      values(f, e);
      values(f, actual.translation());
      values(f, desired.translation());
      values(f, Eigen::Quaterniond(actual.rotation()).coeffs());
      values(f, Eigen::Quaterniond(desired.rotation()).coeffs());
      f << '\n';
    } catch (const std::ios_base::failure&) {
      throw;
    } catch (const std::exception& error) {
      result.code = stage;
      auto failure = output(out / (filename + ".error.txt"));
      failure << "step=" << step << " time=" << step * dt << " code=" << stage << "\n"
              << error.what() << '\n';
      failure.flush();
      break;
    }
  }
  f.flush();
  const int measured_count = std::max(1, result.steps);
  result.mean_p /= measured_count;
  result.mean_r /= measured_count;
  result.objective /= measured_count;
  if (result.measured_velocity_violations || result.measured_position_violations)
    result.code = "EXECUTED_LIMIT_VIOLATION";
  if (result.code == "COMPLETED" && (result.final_p > s.get("completion_position_tolerance") ||
                                     result.final_r > s.get("completion_rotation_tolerance") ||
                                     result.peak_p > s.get("peak_position_tolerance") ||
                                     result.peak_r > s.get("peak_rotation_tolerance")))
    result.code = "TRACKING_TOLERANCE_FAILURE";
  result.objective +=
      result.mean_p + s.get("rotation_length_scale") * result.mean_r +
      s.get("objective_intervention_weight") * result.interventions / measured_count;
  if (result.code != "COMPLETED") result.objective += s.get("objective_failure_penalty");
  return result;
}
void writeTrial(std::ostream& f, const Trial& r) {
  f << r.seed << ',' << r.kind << ',' << r.method << ',' << r.damping << ',' << r.code << ','
    << r.steps << ',' << r.mean_p << ',' << r.mean_r << ',' << r.peak_p << ',' << r.peak_r << ','
    << r.final_p << ',' << r.final_r << ',' << r.raw_max << ',' << r.accepted_max << ','
    << r.executed_max << ',' << r.interventions << ',' << r.measured_velocity_violations << ','
    << r.measured_position_violations << ',' << r.objective << '\n';
}
int main(int argc, char** argv) {
  if (argc != 8) {
    std::cerr << "Usage: phase2_benchmark robot.yaml scene.xml phase2.yaml results_dir "
                 "development|evaluation selection.yaml config_sha256\n";
    return 2;
  }
  try {
    auto robot = loadConfig(argv[1]);
    RobotKinematics k(robot);
    Settings s{YAML::LoadFile(argv[3])};
    s.validate();
    fs::path out = argv[4];
    fs::create_directories(out);
    const std::string mode = argv[5];
    if (mode != "development" && mode != "evaluation" && mode != "weak-direction")
      throw std::invalid_argument("Invalid mode");
    Plant p(argv[2], s.get("period"));
    if (p.names() != k.jointNames())
      throw std::runtime_error("Plant/configured joint ordering mismatch");
    Eigen::VectorXd lo = k.lowerLimits(), hi = k.upperLimits();
    Eigen::VectorXd vmax = vector(s.y["velocity_limits"].as<std::vector<double>>());
    if (vmax.size() != lo.size() || !vmax.allFinite() || (vmax.array() <= 0).any())
      throw std::invalid_argument("Invalid velocity limits");
    for (int i = 0; i < lo.size(); ++i) {
      int j = mj_name2id(p.model(), mjOBJ_JOINT, k.jointNames()[i].c_str());
      if (j < 0 || p.model()->jnt_type[j] != mjJNT_HINGE)
        throw std::runtime_error("Expected named hinge");
      lo[i] = std::max(lo[i], p.model()->jnt_range[2 * j]);
      hi[i] = std::min(hi[i], p.model()->jnt_range[2 * j + 1]);
      for (int a = 0; a < p.model()->nu; ++a)
        if (p.model()->actuator_trnid[2 * a] == j && p.model()->actuator_ctrllimited[a]) {
          lo[i] = std::max(lo[i], p.model()->actuator_ctrlrange[2 * a]);
          hi[i] = std::min(hi[i], p.model()->actuator_ctrlrange[2 * a + 1]);
        }
    }
    if ((lo.array() >= hi.array()).any()) throw std::runtime_error("Empty position intersection");
    auto bounds = output(out / "bounds.csv");
    bounds << "joint,lower,upper,velocity\n";
    for (int i = 0; i < lo.size(); ++i)
      bounds << k.jointNames()[i] << ',' << lo[i] << ',' << hi[i] << ',' << vmax[i] << '\n';
    bounds.flush();
    auto siteConfig = robot;
    siteConfig.tcp_parent_frame = s.y["plant_flange_site"].as<std::string>();
    Options base;
    base.relative_rank_tolerance = s.get("rank_relative_tolerance");
    base.adaptive_sigma_threshold = s.get("adaptive_sigma_threshold");
    base.damping = 0;
    std::vector<MethodRun> methods{{"mp", base}};
    if (mode == "development") {
      for (double damping : s.y["damping_candidates"].as<std::vector<double>>())
        for (auto name : {"fixed", "adaptive"}) {
          auto options = base;
          options.method = std::string(name) == "fixed" ? Method::FixedDls : Method::AdaptiveDls;
          options.damping = damping;
          methods.push_back({name, options});
        }
    } else {
      auto chosen = YAML::LoadFile(argv[6]);
      if (chosen["config_sha256"].as<std::string>() != argv[7])
        throw std::runtime_error("Frozen configuration hash mismatch");
      for (auto name : {"fixed", "adaptive"}) {
        auto options = base;
        options.method = std::string(name) == "fixed" ? Method::FixedDls : Method::AdaptiveDls;
        options.damping = chosen[name].as<double>();
        const auto candidates = s.y["damping_candidates"].as<std::vector<double>>();
        if (std::find(candidates.begin(), candidates.end(), options.damping) == candidates.end())
          throw std::invalid_argument("Selected damping outside frozen candidate set");
        methods.push_back({name, options});
      }
    }
    std::vector<Trial> trials;
    auto table = output(out / "trials.csv");
    table << "seed,kind,method,damping,code,steps,mean_position_error,mean_rotation_error,peak_"
             "position_error,peak_rotation_error,final_position_error,final_rotation_error,raw_dq_"
             "max,accepted_dq_max,executed_dq_max,interventions,measured_velocity_violations,"
             "measured_position_violations,objective\n";
    const auto seeds = s.y[mode == "development"      ? "development_seeds"
                           : mode == "weak-direction" ? "weak_seeds"
                                                      : "evaluation_seeds"]
                           .as<std::vector<uint32_t>>();
    if (mode == "weak-direction") {
      if (seeds.empty() || !std::isfinite(s.get("weak_reference_amplitude")) ||
          s.get("weak_reference_amplitude") <= 0)
        throw std::invalid_argument("Invalid weak diagnostic configuration");
      std::set<uint32_t> unique;
      auto dev = s.y["development_seeds"].as<std::vector<uint32_t>>(),
           eval = s.y["evaluation_seeds"].as<std::vector<uint32_t>>();
      for (auto seed : seeds)
        if (!unique.insert(seed).second || std::find(dev.begin(), dev.end(), seed) != dev.end() ||
            std::find(eval.begin(), eval.end(), seed) != eval.end())
          throw std::invalid_argument("Overlapping weak diagnostic seeds");
    }
    for (uint32_t seed : seeds) {
      auto pair = search(k, p, s, lo, hi, seed, out);
      sweep(k, s, pair, seed, methods, out);
      const std::vector<std::string> kinds = mode == "weak-direction"
                                                 ? std::vector<std::string>{"weak_direction"}
                                                 : std::vector<std::string>{"nominal", "near"};
      for (const auto& kind : kinds)
        for (const auto& method : methods) {
          Trial trial;
          try {
            trial = track(k, p, siteConfig, s, lo, hi, vmax,
                          std::string(kind) == "nominal" ? pair.nominal : pair.near, seed, kind,
                          method, out);
          } catch (const std::ios_base::failure&) {
            throw;
          } catch (const std::exception& error) {
            trial.seed = seed;
            trial.kind = kind;
            trial.method = method.name;
            trial.damping = method.options.damping;
            trial.code = "INITIALIZATION_EXCEPTION";
            trial.objective = s.get("objective_failure_penalty");
            auto failure =
                output(out / (std::string(kind) + "_" + std::to_string(seed) + "_" + method.name +
                              "_" + std::to_string(method.options.damping) + ".init-error.txt"));
            failure << error.what() << '\n';
            failure.flush();
          }
          writeTrial(table, trial);
          table.flush();
          trials.push_back(trial);
          std::cout << mode << ' ' << seed << ' ' << kind << ' ' << method.name << ' '
                    << method.options.damping << ' ' << trial.code
                    << " objective=" << trial.objective << '\n';
        }
    }
    if (mode == "development") {
      auto selection = output(argv[6]);
      selection << "config_sha256: " << argv[7] << '\n';
      auto tuning = output(out / "tuning.csv");
      tuning << "method,damping,trials,mean_objective\n";
      for (auto name : {"fixed", "adaptive"}) {
        double best = std::numeric_limits<double>::infinity(), chosen = 0;
        for (double damping : s.y["damping_candidates"].as<std::vector<double>>()) {
          double objective = 0;
          int count = 0;
          for (const auto& trial : trials)
            if (trial.method == name && trial.damping == damping) {
              objective += trial.objective;
              count++;
            }
          if (count == 0) throw std::runtime_error("Missing tuning trial");
          objective /= count;
          tuning << name << ',' << damping << ',' << count << ',' << objective << '\n';
          if (objective < best) {
            best = objective;
            chosen = damping;
          }
        }
        selection << name << ": " << chosen << '\n';
      }
      selection.flush();
      tuning.flush();
    }
    std::cout << "PHASE2_" << mode << "_DATA_COMPLETE\n";
  } catch (const std::exception& error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
