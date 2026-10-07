// Offline scenario screening reuses the Phase 2 C++ DLS core; it is not a controller.
#include <yaml-cpp/yaml.h>

#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <predictive_motion_control/ik.hpp>
#include <predictive_motion_kinematics/robot_kinematics.hpp>
#include <predictive_motion_sim/plant.hpp>
#include <random>
#include <stdexcept>
#include <vector>

using namespace predictive_motion;
Eigen::Vector3d v3(const YAML::Node& n) {
  auto v = n.as<std::vector<double>>();
  if (v.size() != 3) throw std::invalid_argument("Expected 3 coordinates");
  return {v[0], v[1], v[2]};
}
int object(mjModel* m, int type, const std::string& name) {
  int id = mj_name2id(m, type, name.c_str());
  if (id < 0) throw std::runtime_error("Absent scene object " + name);
  return id;
}
Eigen::VectorXd scaled(Vector6 x, double length) {
  x.tail<3>() *= length;
  return x;
}
double conservativeClearance(const mjModel* m, const mjData* d, int a, int b) {
  auto bound = [&](int g) {
    Eigen::Matrix3d rotation =
        Eigen::Map<const Eigen::Matrix<double, 3, 3, Eigen::RowMajor>>(d->geom_xmat + 9 * g);
    Eigen::Vector3d center = Eigen::Map<const Eigen::Vector3d>(d->geom_xpos + 3 * g) +
                             rotation * Eigen::Map<const Eigen::Vector3d>(m->geom_aabb + 6 * g);
    Eigen::Vector3d half =
        rotation.cwiseAbs() * Eigen::Map<const Eigen::Vector3d>(m->geom_aabb + 6 * g + 3);
    if (!center.allFinite() || !half.allFinite() || (half.array() <= 0).any())
      throw std::runtime_error("Invalid primitive bounding box");
    return std::pair<Eigen::Vector3d, Eigen::Vector3d>(center, half);
  };
  auto x = bound(a), y = bound(b);
  return ((x.first - y.first).cwiseAbs() - x.second - y.second).cwiseMax(0).norm();
}
int main(int argc, char** argv) {
  if (argc != 5) {
    std::cerr << "Usage: scene_feasibility robot.yaml scene.xml path.json outdir\n";
    return 2;
  }
  try {
    RobotKinematics k(loadConfig(argv[1]));
    Plant plant(argv[2]);
    auto cfg = YAML::LoadFile(argv[3]);
    if (cfg["units"].as<std::string>() != "m" || cfg["frame"].as<std::string>() != "world")
      throw std::invalid_argument("Path frame/units");
    auto quat = cfg["quaternion_xyzw"].as<std::vector<double>>();
    if (quat.size() != 4) throw std::invalid_argument("Quaternion dimension");
    auto base = poseFromXyzw(v3(cfg["start"]), {quat[0], quat[1], quat[2], quat[3]});
    auto start = base.translation(), end = v3(cfg["end"]);
    int samples = cfg["samples"].as<int>();
    const double length = cfg["ik_rotation_length_scale"].as<double>(),
                 tolerance = cfg["ik_error_tolerance"].as<double>(),
                 stepcap = cfg["ik_step_cap_rad"].as<double>();
    if (samples < 2 || !std::isfinite(length) || length <= 0 || tolerance <= 0 || stepcap <= 0)
      throw std::invalid_argument("Invalid IK configuration");
    control::Options options;
    options.method = control::Method::FixedDls;
    options.damping = cfg["ik_damping"].as<double>();
    Eigen::VectorXd lo = k.lowerLimits(), hi = k.upperLimits();
    std::vector<int> joint_ids;
    for (size_t j = 0; j < k.jointNames().size(); ++j) {
      int id = object(plant.model(), mjOBJ_JOINT, k.jointNames()[j]);
      joint_ids.push_back(id);
      lo[j] = std::max(lo[j], plant.model()->jnt_range[2 * id]);
      hi[j] = std::min(hi[j], plant.model()->jnt_range[2 * id + 1]);
    }
    auto out = std::filesystem::path(argv[4]);
    if (std::filesystem::exists(out) && !std::filesystem::is_empty(out))
      throw std::runtime_error("Use a fresh output directory; existing evidence is preserved");
    std::filesystem::create_directories(out);
    std::ofstream attempts(out / "attempts.csv");
    attempts.exceptions(std::ios::failbit | std::ios::badbit);
    attempts << "attempt,completed_samples,reason\n";
    std::mt19937 rng(cfg["seed"].as<uint32_t>());
    for (int attempt = 0; attempt < cfg["max_initial_guesses"].as<int>(); ++attempt) {
      Eigen::VectorXd q(lo.size());
      for (int j = 0; j < q.size(); ++j)
        q[j] = attempt == 0 ? plant.positions()[j]
                            : lo[j] + (.02 + .96 * double(rng()) / 4294967295.) * (hi[j] - lo[j]);
      q = q.cwiseMax(lo).cwiseMin(hi);
      std::vector<Eigen::VectorXd> path;
      std::vector<Pose> targets;
      std::vector<double> clearances, errors, position_errors, rotation_errors;
      std::string failure;
      for (int i = 0; i < samples; ++i) {
        double s = double(i) / (samples - 1);
        Pose desired = base;
        desired.translation() = (1 - s) * start + s * end;
        desired.translation().y() += cfg["lateral_amplitude"].as<double>() * std::sin(2 * M_PI * s);
        desired.translation().z() += cfg["vertical_amplitude"].as<double>() * std::sin(M_PI * s);
        bool converged = false;
        for (int iter = 0; iter < cfg["max_ik_iterations"].as<int>(); ++iter) {
          auto residual = scaled(logResidual(k.tcpPose(q), desired), length);
          double before = residual.norm();
          if (before < tolerance) {
            converged = true;
            break;
          }
          Eigen::MatrixXd a = -k.residualJacobian(q, desired);
          a.bottomRows(3) *= length;
          Eigen::VectorXd step = control::solve(a, residual, options).dq;
          if (step.cwiseAbs().maxCoeff() > stepcap) step *= stepcap / step.cwiseAbs().maxCoeff();
          bool accepted = false;
          for (int ls = 0; ls < 12; ++ls) {
            Eigen::VectorXd candidate = (q + step).cwiseMax(lo).cwiseMin(hi);
            if (scaled(logResidual(k.tcpPose(candidate), desired), length).norm() < before) {
              q = candidate;
              accepted = true;
              break;
            }
            step *= .5;
          }
          if (!accepted) break;
        }
        if (!converged) {
          failure = "IK_NO_CONVERGENCE";
          break;
        }
        for (int j = 0; j < q.size(); ++j)
          plant.data()->qpos[plant.model()->jnt_qposadr[joint_ids[j]]] = q[j];
        mj_forward(plant.model(), plant.data());
        for (int c = 0; c < plant.data()->ncon; ++c)
          if (plant.data()->contact[c].dist < 0) {
            failure = "CONTACT";
            break;
          }
        if (!failure.empty()) break;
        double clearance = 10;
        std::vector<const char*> tool_geoms = {"tool_adapter", "tool_shaft", "tool_sensor",
                                               "tool_tip"};
        if (mj_name2id(plant.model(), mjOBJ_GEOM, "tool_bracket") >= 0)
          tool_geoms.push_back("tool_bracket");
        for (const char* t : tool_geoms)
          for (const char* f : {"fixture_base", "fixture_left", "fixture_right", "fixture_rear"})
            clearance =
                std::min(clearance, conservativeClearance(plant.model(), plant.data(),
                                                          object(plant.model(), mjOBJ_GEOM, t),
                                                          object(plant.model(), mjOBJ_GEOM, f)));
        if (clearance < cfg["tool_fixture_clearance_m"].as<double>()) {
          failure = "TOOL_CLEARANCE";
          break;
        }
        path.push_back(q);
        targets.push_back(desired);
        clearances.push_back(clearance);
        errors.push_back(scaled(logResidual(k.tcpPose(q), desired), length).norm());
        const auto actual = k.tcpPose(q);
        position_errors.push_back((actual.translation() - desired.translation()).norm());
        rotation_errors.push_back(logResidual(actual, desired).tail<3>().norm());
      }
      attempts << attempt << ',' << path.size() << ',' << (failure.empty() ? "PASS" : failure)
               << '\n';
      attempts.flush();
      if (!failure.empty()) continue;
      std::ofstream csv(out / "feasible_path.csv");
      csv.exceptions(std::ios::failbit | std::ios::badbit);
      csv << std::setprecision(17)
          << "s,x,y,z,scaled_pose_residual,tool_fixture_clearance_lower_bound_m,position_error_m,"
             "rotation_error_rad";
      for (int j = 0; j < q.size(); ++j) csv << ",q" << j + 1;
      csv << '\n';
      for (int i = 0; i < samples; ++i) {
        csv << double(i) / (samples - 1) << ',' << targets[i].translation().x() << ','
            << targets[i].translation().y() << ',' << targets[i].translation().z() << ','
            << errors[i] << ',' << clearances[i] << ',' << position_errors[i] << ','
            << rotation_errors[i];
        for (double x : path[i]) csv << ',' << x;
        csv << '\n';
      }
      std::ofstream summary(out / "summary.json");
      summary.exceptions(std::ios::failbit | std::ios::badbit);
      summary << "{\"status\":\"PASS\",\"clearance_provider\":\"conservative world-AABB separation "
                 "lower bound for all tool primitives including optional "
                 "bracket\",\"scope\":\"discrete offline pose/contact screening "
                 "only\",\"samples\":"
              << samples << ",\"selected_attempt\":" << attempt
              << ",\"controller_trial\":false,\"continuous_collision_guarantee\":false}\n";
      std::cout << "DISCRETE_INSPECTION_PATH_PASS samples=" << samples << " attempt=" << attempt
                << '\n';
      return 0;
    }
    throw std::runtime_error("No screened feasible path in declared multistart budget");
  } catch (const std::exception& e) {
    std::cerr << e.what() << '\n';
    return 1;
  }
}
