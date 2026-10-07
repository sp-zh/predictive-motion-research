#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <chrono>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <pinocchio/spatial/explog.hpp>
#include <random>
#include <set>

#include "observation_snapshot.hpp"
#include "predictive_motion_control/ik.hpp"
#include "predictive_motion_control/nullspace.hpp"
#include "predictive_motion_kinematics/robot_kinematics.hpp"
#include "predictive_motion_sim/plant.hpp"
using namespace predictive_motion;
using namespace predictive_motion::control;
namespace fs = std::filesystem;
struct Settings {
  YAML::Node y;
  double get(const char* key) const { return y[key].as<double>(); }
  void validate() const {
    for (auto key : {"period", "rotation_length_scale", "gradient_h", "directional_check_h",
                     "log_volume_regularization", "feedback_gain", "path_seconds",
                     "completion_position_tolerance", "completion_rotation_tolerance",
                     "peak_position_tolerance", "peak_rotation_tolerance"})
      if (!std::isfinite(get(key)) || get(key) <= 0)
        throw std::invalid_argument(std::string("Invalid positive setting ") + key);
    for (auto key : {"warmup_seconds", "settle_seconds", "reference_joint_amplitude",
                     "joint_objective_weight", "sigma_objective_weight",
                     "log_volume_objective_weight", "score_pose_weight", "score_joint_cost_weight",
                     "score_sigma_weight", "score_speed_weight", "score_intervention_weight",
                     "score_failure_penalty", "primary_damping", "singular_gap_relative_tolerance"})
      if (!std::isfinite(get(key)) || get(key) < 0)
        throw std::invalid_argument(std::string("Invalid nonnegative setting ") + key);
    for (auto key : {"near_quantile", "joint_objective_quantile"})
      if (!std::isfinite(get(key)) || get(key) < 0 || get(key) > 1)
        throw std::invalid_argument("Invalid selection quantile");
    if (!std::isfinite(get("search_margin")) || get("search_margin") < 0 ||
        get("search_margin") >= .5 || y["search_samples"].as<int>() < 100 ||
        y["search_samples"].as<int>() > 1000000)
      throw std::invalid_argument("Invalid search configuration");
    if (!std::isfinite(get("rank_relative_tolerance")) || get("rank_relative_tolerance") < 0 ||
        get("rank_relative_tolerance") >= 1)
      throw std::invalid_argument("Invalid relative rank tolerance");
    for (auto key : {"warmup_seconds", "path_seconds", "settle_seconds"})
      if (std::abs(get(key) / get("period") - std::round(get(key) / get("period"))) > 1e-8 ||
          get(key) / get("period") > 10000000)
        throw std::invalid_argument("Invalid duration/period ratio");
    std::set<uint32_t> seeds;
    for (auto key : {"development_seeds", "evaluation_seeds"}) {
      auto v = y[key].as<std::vector<uint32_t>>();
      if (v.empty()) throw std::invalid_argument("Empty seeds");
      for (auto seed : v)
        if (!seeds.insert(seed).second) throw std::invalid_argument("Overlapping/duplicate seeds");
    }
    std::set<double> gains;
    for (double x : y["secondary_gain_candidates"].as<std::vector<double>>())
      if (!std::isfinite(x) || x <= 0 || !gains.insert(x).second)
        throw std::invalid_argument("Invalid gain candidate");
    if (gains.empty()) throw std::invalid_argument("Empty gain candidates");
    auto primary = y["primary_method"].as<std::string>();
    if (primary != "mp" && primary != "dls") throw std::invalid_argument("Invalid primary method");
  }
};
std::ofstream output(const fs::path& p) {
  std::ofstream f(p);
  if (!f) throw std::runtime_error("Cannot write " + p.string());
  f.exceptions(std::ios::badbit | std::ios::failbit);
  f << std::setprecision(17);
  return f;
}
Eigen::VectorXd vector(const std::vector<double>& v) {
  return Eigen::Map<const Eigen::VectorXd>(v.data(), v.size());
}
void values(std::ostream& f, const Eigen::VectorXd& v) {
  for (double x : v) f << ',' << x;
}
void columns(std::ostream& f, const char* name, int n) {
  for (int i = 0; i < n; ++i) f << ',' << name << '_' << i;
}
Eigen::MatrixXd weighted(Eigen::MatrixXd j, double length) {
  j.bottomRows(3) *= length;
  return j;
}
Eigen::VectorXd weightedTwist(Vector6 v, double length) {
  v.tail(3) *= length;
  return v;
}
Eigen::VectorXd normalizedMargins(const Eigen::VectorXd& q, const Eigen::VectorXd& lo,
                                  const Eigen::VectorXd& hi) {
  return ((q - lo).array() / (hi - lo).array()).min((hi - q).array() / (hi - lo).array());
}
void initialize(Plant& p, const Eigen::VectorXd& q) {
  mj_resetData(p.model(), p.data());
  for (int i = 0; i < q.size(); ++i) {
    int j = mj_name2id(p.model(), mjOBJ_JOINT, p.names()[i].c_str());
    p.data()->qpos[p.model()->jnt_qposadr[j]] = q[i];
  }
  p.command(p.names(), std::vector<double>(q.data(), q.data() + q.size()));
  mj_forward(p.model(), p.data());
}
Pose measuredTcp(Plant& p, mjData* snapshot, const RobotConfig& c, const std::string& name) {
  return observeTcp(p, snapshot, c, name);
}
struct Candidate {
  Eigen::VectorXd q;
  double sigma, h;
  int index;
};
SingularIndicators metrics(const Eigen::MatrixXd& j, const Settings& s) {
  return singularIndicators(j, s.get("rank_relative_tolerance"), s.get("log_volume_regularization"),
                            s.get("singular_gap_relative_tolerance"));
}
void metricColumns(std::ostream& f, const std::string& prefix) {
  for (auto name : {"sigma_min", "sigma_max", "condition", "manipulability", "log_manipulability",
                    "regularized_log_volume", "rank", "min_gap", "simple_min", "near_rank"})
    f << ',' << prefix << '_' << name;
  columns(f, (prefix + "_sigma").c_str(), 6);
}
void metricValues(std::ostream& f, const SingularIndicators& m) {
  f << ',' << m.sigma_min << ',' << m.sigma_max << ',' << m.condition << ',' << m.manipulability
    << ',' << m.log_manipulability << ',' << m.regularized_log_volume << ',' << m.rank << ','
    << m.minimum_gap << ',' << m.simple_min << ',' << m.near_rank;
  values(f, m.singular_values);
}
std::map<std::string, Candidate> search(RobotKinematics& k, Plant& p, const Settings& s,
                                        const Eigen::VectorXd& lo, const Eigen::VectorXd& hi,
                                        uint32_t seed, const fs::path& folder) {
  std::mt19937 rng(seed);
  std::vector<Candidate> pool;
  auto f = output(folder / ("search_" + std::to_string(seed) + ".csv"));
  f << "index,eligible,H_joint,min_normalized_margin";
  metricColumns(f, "scaled");
  metricColumns(f, "unscaled");
  columns(f, "q", lo.size());
  f << '\n';
  for (int step = 0; step < s.y["search_samples"].as<int>(); ++step) {
    Eigen::VectorXd q(lo.size());
    for (int i = 0; i < q.size(); ++i) {
      double u = static_cast<double>(rng()) / 4294967295.;
      q[i] =
          lo[i] + (hi[i] - lo[i]) * (s.get("search_margin") + (1 - 2 * s.get("search_margin")) * u);
    }
    Eigen::MatrixXd j = k.tcpJacobian(q, Reference::Local);
    auto scaled = metrics(weighted(j, s.get("rotation_length_scale")), s), unscaled = metrics(j, s);
    auto h = jointCenterObjective(q, lo, hi);
    initialize(p, q);
    bool eligible = true;
    for (int c = 0; c < p.data()->ncon; ++c)
      if (p.data()->contact[c].dist < 0) eligible = false;
    f << step << ',' << eligible << ',' << h.value << ','
      << normalizedMargins(q, lo, hi).minCoeff();
    metricValues(f, scaled);
    metricValues(f, unscaled);
    values(f, q);
    f << '\n';
    if (eligible) pool.push_back({q, scaled.sigma_min, h.value, step});
  }
  if (pool.size() < 100) throw std::runtime_error("Insufficient eligible configurations");
  f.flush();
  std::sort(pool.begin(), pool.end(),
            [](const auto& a, const auto& b) { return a.sigma < b.sigma; });
  auto singular = pool[static_cast<size_t>(s.get("near_quantile") * (pool.size() - 1))];
  double minSigma = pool.front().sigma, medianSigma = pool[pool.size() / 2].sigma;
  std::sort(pool.begin(), pool.end(), [](const auto& a, const auto& b) { return a.h < b.h; });
  auto joint = pool[static_cast<size_t>(s.get("joint_objective_quantile") * (pool.size() - 1))];
  auto selection = output(folder / ("search_" + std::to_string(seed) + "_selection.yaml"));
  selection << "searched: " << s.y["search_samples"].as<int>() << "\neligible: " << pool.size()
            << "\nminimum_sigma: " << minSigma << "\nmedian_sigma: " << medianSigma
            << "\nsingularity_index: " << singular.index
            << "\nsingularity_sigma: " << singular.sigma << "\njoint_limit_index: " << joint.index
            << "\njoint_limit_H: " << joint.h << '\n';
  selection.flush();
  return {{"joint_limit", joint}, {"singularity", singular}};
}
struct MethodRun {
  std::string name;
  double gain;
};
struct Trial {
  uint32_t seed;
  std::string kind, reference, method, primary, code = "COMPLETED";
  double gain;
  int steps = 0, interventions = 0, velocityViolations = 0, positionViolations = 0, fdInvalid = 0,
      controlOverruns = 0;
  double meanP = 0, meanR = 0, peakP = 0, peakR = 0, finalP = 0, finalR = 0, initialH = 0,
         finalH = 0, initialSigma = 0, finalSigma = 0, initialMargin = 0, finalMargin = 0;
  double rawMax = 0, acceptedMax = 0, executedMax = 0, rawLeakMax = 0, guardLeakMax = 0,
         computeMean = 0, gradientMean = 0, computeMax = 0, score = 0;
};
Trial track(RobotKinematics& k, Plant& p, const RobotConfig& robot, const Settings& s,
            const Eigen::VectorXd& lo, const Eigen::VectorXd& hi, const Eigen::VectorXd& vmax,
            const Candidate& start, uint32_t seed, const std::string& kind,
            const std::string& reference, const MethodRun& method, const fs::path& folder) {
  Trial r;
  r.seed = seed;
  r.kind = kind;
  r.reference = reference;
  r.method = method.name;
  r.gain = method.gain;
  r.primary = s.y["primary_method"].as<std::string>();
  int n = lo.size();
  double dt = s.get("period"), duration = s.get("path_seconds");
  initialize(p, start.q);
  for (int step = 0; step < std::llround(s.get("warmup_seconds") / dt); ++step) p.step();
  std::unique_ptr<mjData, decltype(&mj_deleteData)> snapshot(mj_makeData(p.model()), mj_deleteData);
  if (!snapshot) throw std::runtime_error("Pose snapshot allocation failed");
  Eigen::VectorXd target = start.q, amplitude = Eigen::VectorXd::Zero(n);
  std::mt19937 rng(seed + 77);
  if (reference == "path")
    for (int i = 0; i < n; ++i)
      amplitude[i] =
          (rng() % 2 ? 1 : -1) * std::min(s.get("reference_joint_amplitude"),
                                          .5 * std::min(start.q[i] - lo[i], hi[i] - start.q[i]));
  auto desiredJoint = [&](double time) {
    double u = std::clamp(time / duration, 0., 1.);
    double a = .5 * (1 - std::cos(2 * M_PI * u)),
           v = time < duration ? M_PI / duration * std::sin(2 * M_PI * u) : 0.;
    return std::pair<Eigen::VectorXd, Eigen::VectorXd>{start.q + amplitude * a, amplitude * v};
  };
  Options primary;
  primary.relative_rank_tolerance = s.get("rank_relative_tolerance");
  primary.method = r.primary == "mp" ? Method::MoorePenrose : Method::FixedDls;
  primary.damping = s.get("primary_damping");
  JacobianEvaluator evaluator = [&](const Eigen::VectorXd& q) {
    return weighted(k.tcpJacobian(q, Reference::Local), s.get("rotation_length_scale"));
  };
  std::string name = kind + "_" + reference + "_" + std::to_string(seed) + "_" + method.name + "_" +
                     std::to_string(method.gain) + ".csv";
  auto f = output(folder / name);
  f << "time_before,time_after,primary,objective,gain,primary_damping,position_error,rotation_"
       "error,H_joint,min_normalized_margin,min_radian_margin,joint_directional_derivative,raw_"
       "unscaled_JPz_leakage,raw_scaled_JPz_leakage,guard_unscaled_task_distortion,guard_scaled_"
       "task_distortion,postguard_task_difference,primary_task_residual,gradient_us,control_"
       "compute_us,gradient_evaluations,gradient_simple_min,gradient_near_rank,gradient_min_gap,"
       "velocity_intervention,position_intervention,measured_velocity_violation,measured_position_"
       "violation";
  metricColumns(f, "scaled");
  metricColumns(f, "unscaled");
  for (auto column :
       {"q_before", "primary_dq", "z", "secondary_dq", "requested_dq", "accepted_dq",
        "accepted_q_target", "executed_q", "executed_dq", "reference_q", "normalized_margin"})
    columns(f, column, n);
  columns(f, "residual", 6);
  columns(f, "desired_twist_body", 6);
  columns(f, "actual_tcp_xyz", 3);
  columns(f, "desired_tcp_xyz", 3);
  columns(f, "actual_tcp_xyzw", 4);
  columns(f, "desired_tcp_xyzw", 4);
  f << '\n';
  bool initialized = false;
  int totalSteps = std::llround((duration + s.get("settle_seconds")) / dt);
  for (int step = 0; step < totalSteps; ++step) {
    std::string stage = "CONTROLLER_EXCEPTION";
    try {
      auto begin = std::chrono::steady_clock::now();
      double t = step * dt;
      Eigen::VectorXd q = vector(p.positions());
      auto actual = k.tcpPose(q);
      auto [qref, dqref] = desiredJoint(t);
      auto desired = k.tcpPose(qref);
      Vector6 e = logResidual(actual, desired),
              body = k.tcpJacobian(qref, Reference::Local) * dqref;
      Eigen::MatrixXd j = k.tcpJacobian(q, Reference::Local),
                      scaledJ = weighted(j, s.get("rotation_length_scale"));
      auto sm = metrics(scaledJ, s), um = metrics(j, s);
      auto joint = jointCenterObjective(q, lo, hi);
      auto margins = normalizedMargins(q, lo, hi);
      if (!initialized) {
        r.initialH = joint.value;
        r.initialSigma = sm.sigma_min;
        r.initialMargin = margins.minCoeff();
        initialized = true;
      }
      stage = "SOLVER_EXCEPTION";
      Eigen::MatrixXd a = weighted(-k.residualJacobian(q, desired), s.get("rotation_length_scale"));
      Vector6 rhs =
          s.get("feedback_gain") * e + desiredBodyResidualJacobian(actual, desired) * body;
      auto solved = solve(a, weightedTwist(rhs, s.get("rotation_length_scale")), primary);
      Eigen::VectorXd z = Eigen::VectorXd::Zero(n);
      double gradientUs = 0, minGap = sm.minimum_gap;
      int evaluations = 0;
      bool simple = sm.simple_min, near = sm.near_rank;
      if (method.name == "joint" || method.name == "combined")
        z -= method.gain * s.get("joint_objective_weight") * joint.gradient;
      if (method.name == "sigma_min" || method.name == "combined" || method.name == "log_volume") {
        bool volume = method.name == "log_volume";
        auto gradient = finiteDifferenceGradient(
            q, evaluator,
            volume ? SingularObjective::RegularizedLogVolume
                   : SingularObjective::MinimumSingularValue,
            s.get("gradient_h"), s.get("rank_relative_tolerance"),
            s.get("log_volume_regularization"), s.get("singular_gap_relative_tolerance"));
        z += method.gain *
             s.get(volume ? "log_volume_objective_weight" : "sigma_objective_weight") *
             gradient.gradient;
        gradientUs = gradient.elapsed_microseconds;
        evaluations = gradient.evaluations;
        simple = gradient.simple_min;
        near = gradient.near_rank;
        minGap = gradient.minimum_gap;
      }
      auto command = addExactNullspace(scaledJ, solved.dq, z, s.get("rank_relative_tolerance"));
      stage = "CONTROLLER_EXCEPTION";
      Eigen::VectorXd accepted = command.total.cwiseMax(-vmax).cwiseMin(vmax),
                      next = target + dt * accepted, guarded = next.cwiseMax(lo).cwiseMin(hi);
      bool velocity = (accepted - command.total).norm() > 1e-12,
           position = (next - guarded).norm() > 1e-12;
      accepted = (guarded - target) / dt;
      target = guarded;
      double rawLeak = (j * command.secondary).norm(),
             guardLeak = (j * (accepted - command.total)).norm();
      p.command(k.jointNames(), std::vector<double>(target.data(), target.data() + n));
      double compute =
          std::chrono::duration<double, std::micro>(std::chrono::steady_clock::now() - begin)
              .count();
      stage = "PLANT_NUMERICAL_EXCEPTION";
      p.step();
      stage = "CONTROLLER_EXCEPTION";
      Eigen::VectorXd measured = vector(p.positions()), speed = vector(p.velocities());
      auto [nextref, unused] = desiredJoint(t + dt);
      (void)unused;
      desired = k.tcpPose(nextref);
      actual = measuredTcp(p, snapshot.get(), robot, s.y["plant_flange_site"].as<std::string>());
      double pe = (actual.translation() - desired.translation()).norm(),
             re = pinocchio::log3(actual.rotation().transpose() * desired.rotation()).norm();
      bool vViolation = (speed.cwiseAbs().array() > vmax.array() + 1e-9).any(),
           pViolation = (measured.array() < lo.array() - 1e-9).any() ||
                        (measured.array() > hi.array() + 1e-9).any();
      r.steps++;
      r.meanP += pe;
      r.meanR += re;
      r.peakP = std::max(r.peakP, pe);
      r.peakR = std::max(r.peakR, re);
      r.finalP = pe;
      r.finalR = re;
      r.interventions += velocity || position;
      r.velocityViolations += vViolation;
      r.positionViolations += pViolation;
      r.fdInvalid += evaluations && (!simple || near);
      r.controlOverruns += compute > dt * 1e6;
      r.computeMean += compute;
      r.gradientMean += gradientUs;
      r.computeMax = std::max(r.computeMax, compute);
      r.rawMax = std::max(r.rawMax, command.total.cwiseAbs().maxCoeff());
      r.acceptedMax = std::max(r.acceptedMax, accepted.cwiseAbs().maxCoeff());
      r.executedMax = std::max(r.executedMax, speed.cwiseAbs().maxCoeff());
      r.rawLeakMax = std::max(r.rawLeakMax, rawLeak);
      r.guardLeakMax = std::max(r.guardLeakMax, guardLeak);
      r.score += accepted.norm() * s.get("score_speed_weight");
      f << t << ',' << t + dt << ',' << r.primary << ',' << method.name << ',' << method.gain << ','
        << solved.damping << ',' << pe << ',' << re << ',' << joint.value << ','
        << margins.minCoeff() << ',' << (q - lo).cwiseMin(hi - q).minCoeff() << ','
        << joint.gradient.dot(command.secondary) << ',' << rawLeak << ','
        << command.raw_task_leakage << ',' << guardLeak << ','
        << (scaledJ * (accepted - command.total)).norm() << ','
        << (j * (accepted - solved.dq)).norm() << ',' << solved.task_residual << ',' << gradientUs
        << ',' << compute << ',' << evaluations << ',' << simple << ',' << near << ',' << minGap
        << ',' << velocity << ',' << position << ',' << vViolation << ',' << pViolation;
      metricValues(f, sm);
      metricValues(f, um);
      values(f, q);
      values(f, solved.dq);
      values(f, z);
      values(f, command.secondary);
      values(f, command.total);
      values(f, accepted);
      values(f, target);
      values(f, measured);
      values(f, speed);
      values(f, nextref);
      values(f, margins);
      values(f, e);
      values(f, body);
      values(f, actual.translation());
      values(f, desired.translation());
      values(f, Eigen::Quaterniond(actual.rotation()).coeffs());
      values(f, Eigen::Quaterniond(desired.rotation()).coeffs());
      f << '\n';
    } catch (const std::ios_base::failure&) {
      throw;
    } catch (const std::exception& error) {
      r.code = stage;
      auto err = output(folder / (name + ".error.txt"));
      err << "step=" << step << " code=" << stage << '\n' << error.what() << '\n';
      err.flush();
      break;
    }
  }
  f.flush();
  Eigen::VectorXd finalq = vector(p.positions());
  r.finalH = jointCenterObjective(finalq, lo, hi).value;
  r.finalSigma = metrics(evaluator(finalq), s).sigma_min;
  r.finalMargin = normalizedMargins(finalq, lo, hi).minCoeff();
  int count = std::max(1, r.steps);
  r.meanP /= count;
  r.meanR /= count;
  r.computeMean /= count;
  r.gradientMean /= count;
  r.score /= count;
  if (r.velocityViolations || r.positionViolations) r.code = "EXECUTED_LIMIT_VIOLATION";
  if (r.code == "COMPLETED" &&
      (r.finalP > s.get("completion_position_tolerance") ||
       r.finalR > s.get("completion_rotation_tolerance") ||
       r.peakP > s.get("peak_position_tolerance") || r.peakR > s.get("peak_rotation_tolerance")))
    r.code = "POSE_TOLERANCE_FAILURE";
  r.score += s.get("score_pose_weight") * (r.meanP + s.get("rotation_length_scale") * r.meanR) +
             s.get("score_joint_cost_weight") * (r.finalH - r.initialH) -
             s.get("score_sigma_weight") *
                 std::log((r.finalSigma + s.get("log_volume_regularization")) /
                          (r.initialSigma + s.get("log_volume_regularization"))) +
             s.get("score_intervention_weight") * r.interventions / count;
  if (r.code != "COMPLETED") r.score += s.get("score_failure_penalty");
  return r;
}
void writeTrial(std::ostream& f, const Trial& r) {
  f << r.seed << ',' << r.kind << ',' << r.reference << ',' << r.method << ',' << r.gain << ','
    << r.primary << ',' << r.code << ',' << r.steps << ',' << r.meanP << ',' << r.meanR << ','
    << r.peakP << ',' << r.peakR << ',' << r.finalP << ',' << r.finalR << ',' << r.initialH << ','
    << r.finalH << ',' << r.initialSigma << ',' << r.finalSigma << ',' << r.initialMargin << ','
    << r.finalMargin << ',' << r.rawMax << ',' << r.acceptedMax << ',' << r.executedMax << ','
    << r.interventions << ',' << r.velocityViolations << ',' << r.positionViolations << ','
    << r.rawLeakMax << ',' << r.guardLeakMax << ',' << r.gradientMean << ',' << r.computeMean << ','
    << r.computeMax << ',' << r.controlOverruns << ',' << r.fdInvalid << ',' << r.score << '\n';
}
int main(int argc, char** argv) {
  if (argc != 8) {
    std::cerr << "Usage: phase3_benchmark robot.yaml scene.xml design.yaml out "
                 "development|evaluation selection.yaml design_sha\n";
    return 2;
  }
  try {
    Settings s{YAML::LoadFile(argv[3])};
    s.validate();
    auto robot = loadConfig(argv[1]);
    RobotKinematics k(robot);
    Plant p(argv[2], s.get("period"));
    if (k.jointNames() != p.names())
      throw std::runtime_error("Plant/config joint ordering mismatch");
    fs::path out = argv[4];
    fs::create_directories(out);
    std::string mode = argv[5];
    if (mode != "development" && mode != "evaluation") throw std::invalid_argument("Invalid mode");
    auto lo = k.lowerLimits(), hi = k.upperLimits();
    auto vmax = vector(s.y["velocity_limits"].as<std::vector<double>>());
    if (vmax.size() != lo.size() || !vmax.allFinite() || (vmax.array() <= 0).any())
      throw std::invalid_argument("Invalid velocity configuration");
    for (int i = 0; i < lo.size(); ++i) {
      int j = mj_name2id(p.model(), mjOBJ_JOINT, k.jointNames()[i].c_str());
      if (j < 0 || p.model()->jnt_type[j] != mjJNT_HINGE)
        throw std::runtime_error("Missing named hinge");
      lo[i] = std::max(lo[i], p.model()->jnt_range[2 * j]);
      hi[i] = std::min(hi[i], p.model()->jnt_range[2 * j + 1]);
      for (int a = 0; a < p.model()->nu; ++a)
        if (p.model()->actuator_trnid[2 * a] == j && p.model()->actuator_ctrllimited[a]) {
          lo[i] = std::max(lo[i], p.model()->actuator_ctrlrange[2 * a]);
          hi[i] = std::min(hi[i], p.model()->actuator_ctrlrange[2 * a + 1]);
        }
    }
    if ((hi.array() <= lo.array()).any()) throw std::runtime_error("Empty limit intersection");
    auto bounds = output(out / "bounds.csv");
    bounds << "joint,lower,upper,velocity\n";
    for (int i = 0; i < lo.size(); ++i)
      bounds << k.jointNames()[i] << ',' << lo[i] << ',' << hi[i] << ',' << vmax[i] << '\n';
    bounds.flush();
    std::vector<MethodRun> methods{{"none", 0}};
    auto gains = s.y["secondary_gain_candidates"].as<std::vector<double>>();
    YAML::Node selected;
    if (mode == "evaluation") {
      selected = YAML::LoadFile(argv[6]);
      if (selected["design_sha256"].as<std::string>() != argv[7])
        throw std::runtime_error("Frozen design mismatch");
    }
    for (auto name : {"joint", "sigma_min", "log_volume", "combined"}) {
      if (mode == "development")
        for (double gain : gains) methods.push_back({name, gain});
      else {
        double gain = selected[name].as<double>();
        if (std::find(gains.begin(), gains.end(), gain) == gains.end())
          throw std::runtime_error("Selected gain outside frozen set");
        methods.push_back({name, gain});
      }
    }
    auto table = output(out / "trials.csv");
    table << "seed,case,reference,objective,gain,primary,code,steps,mean_position_error,mean_"
             "rotation_error,peak_position_error,peak_rotation_error,final_position_error,final_"
             "rotation_error,initial_H,final_H,initial_sigma,final_sigma,initial_min_margin,final_"
             "min_margin,raw_dq_max,accepted_dq_max,executed_dq_max,interventions,measured_"
             "velocity_violations,measured_position_violations,raw_JPz_leakage_max,guard_task_"
             "distortion_max,gradient_mean_us,control_mean_us,control_max_us,control_overruns,fd_"
             "flagged_samples,score\n";
    std::vector<Trial> trials;
    for (uint32_t seed : s.y[mode == "development" ? "development_seeds" : "evaluation_seeds"]
                             .as<std::vector<uint32_t>>()) {
      auto cases = search(k, p, s, lo, hi, seed, out);
      for (const auto& item : cases)
        for (auto reference : {"hold", "path"})
          for (const auto& method : methods) {
            Trial r;
            try {
              r = track(k, p, robot, s, lo, hi, vmax, item.second, seed, item.first, reference,
                        method, out);
            } catch (const std::ios_base::failure&) {
              throw;
            } catch (const std::exception& error) {
              r.seed = seed;
              r.kind = item.first;
              r.reference = reference;
              r.method = method.name;
              r.gain = method.gain;
              r.primary = s.y["primary_method"].as<std::string>();
              r.code = "INITIALIZATION_EXCEPTION";
              r.score = s.get("score_failure_penalty");
              auto err = output(out / (item.first + "_" + reference + "_" + std::to_string(seed) +
                                       "_" + method.name + "_" + std::to_string(method.gain) +
                                       ".init-error.txt"));
              err << error.what() << '\n';
              err.flush();
            }
            writeTrial(table, r);
            table.flush();
            trials.push_back(r);
            std::cout << mode << ' ' << seed << ' ' << item.first << ' ' << reference << ' '
                      << method.name << ' ' << method.gain << ' ' << r.code << " score=" << r.score
                      << '\n';
          }
    }
    if (mode == "development") {
      auto selection = output(argv[6]);
      selection << "design_sha256: " << argv[7] << '\n';
      auto tuning = output(out / "tuning.csv");
      tuning << "objective,gain,trials,mean_score\n";
      for (auto name : {"joint", "sigma_min", "log_volume", "combined"}) {
        double best = std::numeric_limits<double>::infinity(), chosen = 0;
        for (double gain : gains) {
          int count = 0;
          double score = 0;
          for (const auto& r : trials)
            if (r.method == name && r.gain == gain) {
              count++;
              score += r.score;
            }
          if (count != 8) throw std::runtime_error("Missing gain tuning scenario");
          score /= count;
          tuning << name << ',' << gain << ',' << count << ',' << score << '\n';
          if (score < best) {
            best = score;
            chosen = gain;
          }
        }
        selection << name << ": " << chosen << '\n';
      }
      selection.flush();
      tuning.flush();
    }
    std::cout << "PHASE3_" << mode << "_DATA_COMPLETE\n";
  } catch (const std::exception& error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
