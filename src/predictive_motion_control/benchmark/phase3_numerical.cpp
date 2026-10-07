#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <random>

#include "predictive_motion_control/ik.hpp"
#include "predictive_motion_control/nullspace.hpp"
#include "predictive_motion_kinematics/robot_kinematics.hpp"
using namespace predictive_motion;
using namespace predictive_motion::control;
struct Stats {
  std::vector<double> v;
  void add(double x) {
    if (!std::isfinite(x)) throw std::runtime_error("Nonfinite statistic");
    v.push_back(x);
  }
  void print(std::ostream& f) const {
    auto a = v;
    std::sort(a.begin(), a.end());
    double total = 0;
    for (double x : a) total += x;
    auto quantile = [&](double p) { return a[static_cast<size_t>(p * (a.size() - 1))]; };
    f << "{\"count\":" << a.size() << ",\"mean\":" << total / a.size()
      << ",\"median\":" << quantile(.5) << ",\"p95\":" << quantile(.95)
      << ",\"p99\":" << quantile(.99) << ",\"max\":" << a.back() << '}';
  }
};
int main(int argc, char** argv) {
  if (argc != 4) {
    std::cerr << "Usage: phase3_numerical robot.yaml phase3.yaml out\n";
    return 2;
  }
  try {
    auto cfg = YAML::LoadFile(argv[2]);
    RobotKinematics k(loadConfig(argv[1]));
    std::filesystem::create_directories(argv[3]);
    std::ofstream f(std::filesystem::path(argv[3]) / "samples.csv");
    f.exceptions(std::ios::failbit | std::ios::badbit);
    f << std::setprecision(17);
    f << "sample,exact_leakage,symmetry,idempotency,damped_leakage,damped_idempotency,joint_"
         "gradient_abs,joint_projected_derivative,joint_finite_descent,sigma_direction_abs,sigma_"
         "direction_rel,log_volume_direction_abs,log_volume_direction_rel,simple_min,near_rank,min_"
         "singular_gap,gradient_sigma_us,gradient_volume_us";
    for (auto name : {"q", "direction", "gradient_sigma", "gradient_volume", "gradient_joint"})
      for (int i = 0; i < k.lowerLimits().size(); ++i) f << ',' << name << '_' << i;
    for (auto name : {"synthetic_J", "model_scaled_J"})
      for (int i = 0; i < 42; ++i) f << ',' << name << '_' << i;
    f << '\n';
    std::mt19937 rng(cfg["numerical_seed"].as<uint32_t>());
    auto random = [&]() { return static_cast<double>(rng()) / 4294967295.; };
    const int count = cfg["numerical_samples"].as<int>();
    if (count < 2000) throw std::invalid_argument("Require at least2000 numerical samples");
    const double h = cfg["gradient_h"].as<double>(), dh = cfg["directional_check_h"].as<double>(),
                 tol = cfg["rank_relative_tolerance"].as<double>(),
                 epsilon = cfg["log_volume_regularization"].as<double>(),
                 gap = cfg["singular_gap_relative_tolerance"].as<double>(),
                 length = cfg["rotation_length_scale"].as<double>();
    std::map<std::string, Stats> stats;
    int validSigma = 0, flagged = 0;
    JacobianEvaluator evaluator = [&](const Eigen::VectorXd& q) {
      Eigen::MatrixXd j = k.tcpJacobian(q, Reference::Local);
      j.bottomRows(3) *= length;
      return j;
    };
    for (int sample = 0; sample < count; ++sample) {
      // Synthetic random Jacobians include exact rank loss and almost singular retained rows.
      Eigen::MatrixXd j(6, 7);
      for (int r = 0; r < 6; ++r)
        for (int c = 0; c < 7; ++c) j(r, c) = 2 * random() - 1;
      if (sample % 20 == 0)
        j.row(5) = j.row(0) + j.row(1);
      else if (sample % 25 == 0)
        j.row(5) *= 1e-8;
      auto p = exactNullProjector(j, tol),
           d = dampedProjector(j, cfg["projector_comparison_damping"].as<double>(), tol);
      const double leak = (j * p).norm(), sym = (p - p.transpose()).norm(),
                   idem = (p * p - p).norm(), dleak = (j * d).norm(), didem = (d * d - d).norm();
      if (leak > 1e-8 || sym > 1e-12 || idem > 1e-12)
        throw std::runtime_error("Exact projector numerical gate failed");
      Eigen::VectorXd q(k.lowerLimits().size()), direction(q.size());
      for (int i = 0; i < q.size(); ++i) {
        q[i] =
            k.lowerLimits()[i] + (.02 + .96 * random()) * (k.upperLimits()[i] - k.lowerLimits()[i]);
        direction[i] = 2 * random() - 1;
      }
      direction.normalize();
      auto joint = jointCenterObjective(q, k.lowerLimits(), k.upperLimits());
      Eigen::VectorXd numerical(q.size());
      for (int i = 0; i < q.size(); ++i) {
        auto plus = q, minus = q;
        plus[i] += h;
        minus[i] -= h;
        numerical[i] = (jointCenterObjective(plus, k.lowerLimits(), k.upperLimits()).value -
                        jointCenterObjective(minus, k.lowerLimits(), k.upperLimits()).value) /
                       (2 * h);
      }
      const double gerror = (joint.gradient - numerical).norm();
      auto actual = evaluator(q);
      auto fp = exactNullProjector(actual, tol);
      Eigen::VectorXd secondary = -fp * joint.gradient;
      const double derivative = joint.gradient.dot(secondary),
                   descent =
                       jointCenterObjective(q + 1e-4 * secondary, k.lowerLimits(), k.upperLimits())
                           .value -
                       joint.value;
      if (gerror > 1e-8 || derivative > 1e-12 || descent > 1e-12)
        throw std::runtime_error("Joint gradient/descent gate failed");
      auto gs = finiteDifferenceGradient(q, evaluator, SingularObjective::MinimumSingularValue, h,
                                         tol, epsilon, gap);
      auto gl = finiteDifferenceGradient(q, evaluator, SingularObjective::RegularizedLogVolume, h,
                                         tol, epsilon, gap);
      auto mp = singularIndicators(evaluator(q + dh * direction), tol, epsilon, gap),
           mm = singularIndicators(evaluator(q - dh * direction), tol, epsilon, gap);
      double sigmaFD = (mp.sigma_min - mm.sigma_min) / (2 * dh),
             logFD = (mp.regularized_log_volume - mm.regularized_log_volume) / (2 * dh);
      double se = std::abs(gs.gradient.dot(direction) - sigmaFD),
             le = std::abs(gl.gradient.dot(direction) - logFD);
      double sr = se / std::max(1e-8, std::abs(sigmaFD)), lr = le / std::max(1e-8, std::abs(logFD));
      const bool simple = gs.simple_min && mp.simple_min && mm.simple_min,
                 near = gs.near_rank || mp.near_rank || mm.near_rank;
      if (simple && !near) {
        validSigma++;
        if (se > 1e-6) throw std::runtime_error("Simple sigma directional gate failed");
        stats["sigma_direction_abs_simple"].add(se);
        stats["sigma_direction_rel_simple"].add(sr);
      } else
        flagged++;
      if (le > 1e-5) throw std::runtime_error("Regularized log directional gate failed");
      for (auto metric : std::vector<std::pair<std::string, double>>{
               {"exact_leakage", leak},
               {"symmetry", sym},
               {"idempotency", idem},
               {"damped_leakage", dleak},
               {"damped_idempotency", didem},
               {"joint_gradient_abs", gerror},
               {"log_volume_direction_abs", le},
               {"log_volume_direction_rel", lr},
               {"gradient_sigma_us", gs.elapsed_microseconds},
               {"gradient_volume_us", gl.elapsed_microseconds}})
        stats[metric.first].add(metric.second);
      f << sample << ',' << leak << ',' << sym << ',' << idem << ',' << dleak << ',' << didem << ','
        << gerror << ',' << derivative << ',' << descent << ',' << se << ',' << sr << ',' << le
        << ',' << lr << ',' << simple << ',' << near << ',' << gs.minimum_gap << ','
        << gs.elapsed_microseconds << ',' << gl.elapsed_microseconds;
      for (const auto& v :
           std::vector<Eigen::VectorXd>{q, direction, gs.gradient, gl.gradient, joint.gradient})
        for (double value : v) f << ',' << value;
      for (const auto& matrix : std::vector<Eigen::MatrixXd>{j, actual})
        for (int row = 0; row < 6; ++row)
          for (int col = 0; col < 7; ++col) f << ',' << matrix(row, col);
      f << '\n';
    }
    f.flush();
    std::ofstream s(std::filesystem::path(argv[3]) / "summary.json");
    s.exceptions(std::ios::failbit | std::ios::badbit);
    s << std::setprecision(17);
    s << "{\"status\":\"PASS\",\"samples\":" << count << ",\"sigma_direction_valid\":" << validSigma
      << ",\"sigma_direction_flagged\":" << flagged << ",\"statistics\":{";
    bool first = true;
    for (const auto& entry : stats) {
      if (!first) s << ',';
      first = false;
      s << '"' << entry.first << "\":";
      entry.second.print(s);
    }
    s << "}}\n";
    s.flush();
    std::cout << "PHASE3_2000_PROJECTOR_GRADIENT_DIRECTIONAL_CHECKS_PASS\n";
  } catch (const std::exception& error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
