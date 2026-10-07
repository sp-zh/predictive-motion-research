#include <mujoco/mujoco.h>

#include <algorithm>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <memory>
#include <pinocchio/spatial/explog.hpp>
#include <random>
#include <stdexcept>

#include "predictive_motion_kinematics/robot_kinematics.hpp"
using namespace predictive_motion;
struct Stats {
  std::vector<double> values;
  void add(double x) {
    if (!std::isfinite(x)) throw std::runtime_error("Nonfinite error statistic");
    values.push_back(x);
  }
  double max() const { return *std::max_element(values.begin(), values.end()); }
  void json(std::ostream& out) const {
    auto sorted = values;
    std::sort(sorted.begin(), sorted.end());
    double mean = 0;
    for (double x : sorted) mean += x;
    auto quantile = [&](double p) { return sorted[static_cast<size_t>(p * (sorted.size() - 1))]; };
    out << "{\"count\":" << sorted.size() << ",\"mean\":" << mean / sorted.size()
        << ",\"median\":" << quantile(0.5) << ",\"p95\":" << quantile(0.95)
        << ",\"p99\":" << quantile(0.99) << ",\"max\":" << sorted.back() << "}";
  }
};
Pose mujocoBody(mjModel* m, mjData* d, const std::string& name) {
  int id = mj_name2id(m, mjOBJ_BODY, name.c_str());
  if (id < 0) throw std::runtime_error("Missing MuJoCo body: " + name);
  Eigen::Matrix3d R =
      Eigen::Map<const Eigen::Matrix<double, 3, 3, Eigen::RowMajor>>(d->xmat + 9 * id);
  return Pose(R, Eigen::Map<const Eigen::Vector3d>(d->xpos + 3 * id));
}
Pose mujocoSite(mjModel* m, mjData* d, const std::string& name) {
  int id = mj_name2id(m, mjOBJ_SITE, name.c_str());
  if (id < 0) throw std::runtime_error("Missing MuJoCo site: " + name);
  Eigen::Matrix3d R =
      Eigen::Map<const Eigen::Matrix<double, 3, 3, Eigen::RowMajor>>(d->site_xmat + 9 * id);
  return Pose(R, Eigen::Map<const Eigen::Vector3d>(d->site_xpos + 3 * id));
}
Jacobian numericalJacobian(RobotKinematics& k, const Eigen::VectorXd& q, double h, Reference ref) {
  const auto T = k.tcpPose(q);
  Jacobian J(6, q.size());
  for (int j = 0; j < q.size(); ++j) {
    auto plus = q, minus = q;
    plus[j] += h;
    minus[j] -= h;
    auto Tp = k.tcpPose(plus), Tm = k.tcpPose(minus);
    Eigen::Vector3d linear = (Tp.translation() - Tm.translation()) / (2 * h);
    Eigen::Vector3d angular = (pinocchio::log3(T.rotation().transpose() * Tp.rotation()) -
                               pinocchio::log3(T.rotation().transpose() * Tm.rotation())) /
                              (2 * h);
    if (ref == Reference::Local)
      linear = T.rotation().transpose() * linear;
    else
      angular = T.rotation() * angular;
    J.col(j).head<3>() = linear;
    J.col(j).tail<3>() = angular;
  }
  return J;
}
Jacobian numericalResidual(RobotKinematics& k, const Eigen::VectorXd& q, const Pose& desired,
                           double h) {
  Jacobian J(6, q.size());
  for (int j = 0; j < q.size(); ++j) {
    auto p = q, m = q;
    p[j] += h;
    m[j] -= h;
    J.col(j) = (logResidual(k.tcpPose(p), desired) - logResidual(k.tcpPose(m), desired)) / (2 * h);
  }
  return J;
}
int main(int argc, char** argv) {
  if (argc != 4) {
    std::cerr << "Usage: numerical_validation config.yaml scene.xml output_dir\n";
    return 2;
  }
  try {
    auto c = loadConfig(argv[1]);
    RobotKinematics k(c);
    auto rotatedConfig = c;
    rotatedConfig.world_T_base =
        Pose(Eigen::AngleAxisd(0.7, Eigen::Vector3d(1, 2, 3).normalized()).toRotationMatrix(),
             Eigen::Vector3d(0.4, -0.2, 0.1));
    rotatedConfig.flange_T_tcp.rotation() =
        Eigen::AngleAxisd(0.4, Eigen::Vector3d::UnitY()).toRotationMatrix();
    RobotKinematics rotated(rotatedConfig);
    char error[2048]{};
    std::unique_ptr<mjModel, decltype(&mj_deleteModel)> m(
        mj_loadXML(argv[2], nullptr, error, sizeof(error)), mj_deleteModel);
    if (!m) throw std::runtime_error(error);
    std::unique_ptr<mjData, decltype(&mj_deleteData)> d(mj_makeData(m.get()), mj_deleteData);
    std::vector<int> joints;
    Eigen::VectorXd lower = k.lowerLimits(), upper = k.upperLimits();
    for (int i = 0; i < lower.size(); ++i) {
      int id = mj_name2id(m.get(), mjOBJ_JOINT, k.jointNames()[i].c_str());
      if (id < 0) throw std::runtime_error("Joint name mismatch");
      joints.push_back(id);
      lower[i] = std::max(lower[i], m->jnt_range[2 * id]);
      upper[i] = std::min(upper[i], m->jnt_range[2 * id + 1]);
      if (lower[i] >= upper[i]) throw std::runtime_error("Disjoint joint limits");
    }
    std::filesystem::create_directories(argv[3]);
    auto outdir = std::filesystem::path(argv[3]);
    std::ofstream csv(outdir / "samples.csv"), eps(outdir / "epsilon_scan.csv"),
        summary(outdir / "summary.json");
    csv << std::setprecision(17);
    eps << std::setprecision(17);
    summary << std::setprecision(17);
    csv << "sample,seed,q1,q2,q3,q4,q5,q6,q7,link7_translation,link7_rotation,flange_translation,"
           "flange_rotation,tcp_translation,tcp_rotation,joint_origin_max,joint_axis_max,local_"
           "translation_abs,local_rotation_abs,local_full_abs,local_full_rel,lwa_translation_abs,"
           "lwa_rotation_abs,lwa_full_abs,lwa_full_rel,residual_abs,residual_rel,desired_body_abs,"
           "desired_body_rel,rotated_local_abs,rotated_local_rel,rotated_lwa_abs,rotated_lwa_rel\n";
    eps << "sample,h,local_abs,lwa_abs,residual_abs,desired_body_abs\n";
    std::map<std::string, Stats> stats;
    std::mt19937 rng(42);
    auto uniform = [&]() { return static_cast<double>(rng()) / 4294967295.0; };
    auto checkModel = [&](const Eigen::VectorXd& q, bool record) {
      mj_resetData(m.get(), d.get());
      for (size_t i = 0; i < joints.size(); ++i) d->qpos[m->jnt_qposadr[joints[i]]] = q[i];
      mj_forward(m.get(), d.get());
      std::vector<double> errors;
      for (const auto& pair : std::vector<std::pair<std::string, Pose>>{
               {"fr3_link7", mujocoBody(m.get(), d.get(), "fr3_link7")},
               {c.tcp_parent_frame, mujocoSite(m.get(), d.get(), "attachment_site")}}) {
        auto pin = k.framePose(q, pair.first);
        errors.push_back((pin.translation() - pair.second.translation()).norm());
        errors.push_back(
            pinocchio::log3(pin.rotation().transpose() * pair.second.rotation()).norm());
      }
      auto mjtcp = mujocoSite(m.get(), d.get(), "attachment_site") * c.flange_T_tcp;
      auto pintcp = k.tcpPose(q);
      errors.push_back((pintcp.translation() - mjtcp.translation()).norm());
      errors.push_back(pinocchio::log3(pintcp.rotation().transpose() * mjtcp.rotation()).norm());
      double origin = 0, axis = 0;
      for (size_t i = 0; i < joints.size(); ++i) {
        const auto jointpose = k.framePose(q, k.jointNames()[i]);
        origin = std::max(origin, (jointpose.translation() -
                                   Eigen::Map<const Eigen::Vector3d>(d->xanchor + 3 * joints[i]))
                                      .norm());
        const auto frameJ = k.frameJacobian(q, k.jointNames()[i], Reference::LocalWorldAligned);
        axis = std::max(axis, (frameJ.col(i).tail<3>() -
                               Eigen::Map<const Eigen::Vector3d>(d->xaxis + 3 * joints[i]))
                                  .norm());
      }
      errors.push_back(origin);
      errors.push_back(axis);
      const std::vector<std::string> names = {
          "link7_translation", "link7_rotation", "flange_translation", "flange_rotation",
          "tcp_translation",   "tcp_rotation",   "joint_origin_max",   "joint_axis_max"};
      if (record)
        for (size_t i = 0; i < names.size(); ++i) stats[names[i]].add(errors[i]);
      return errors;
    };
    auto zeroErrors = checkModel(Eigen::VectorXd::Zero(lower.size()), false);
    for (double x : zeroErrors)
      if (x > 1e-9) throw std::runtime_error("Model zero-reference mismatch");
    for (int sample = 0; sample < 2000; ++sample) {
      Eigen::VectorXd q(lower.size());
      for (int j = 0; j < q.size(); ++j)
        q[j] = lower[j] + (0.02 + 0.96 * uniform()) * (upper[j] - lower[j]);
      auto modelErrors = checkModel(q, true);
      Vector6 delta;
      for (int i = 0; i < 6; ++i) delta[i] = (uniform() - 0.5) * (i < 3 ? 0.2 : 1.0);
      const Pose actual = k.tcpPose(q), desired = actual * pinocchio::exp6(delta);
      auto local = k.tcpJacobian(q, Reference::Local),
           lwa = k.tcpJacobian(q, Reference::LocalWorldAligned),
           residual = k.residualJacobian(q, desired);
      Matrix6 desiredJ = desiredBodyResidualJacobian(actual, desired);
      auto evaluate = [&](double h) {
        auto nlocal = numericalJacobian(k, q, h, Reference::Local),
             nlwa = numericalJacobian(k, q, h, Reference::LocalWorldAligned),
             nr = numericalResidual(k, q, desired, h);
        Matrix6 nd;
        for (int i = 0; i < 6; ++i) {
          Vector6 step = Vector6::Zero();
          step[i] = h;
          nd.col(i) = (logResidual(actual, desired * pinocchio::exp6(step)) -
                       logResidual(actual, desired * pinocchio::exp6(-step))) /
                      (2 * h);
        }
        return std::vector<double>{(local.topRows<3>() - nlocal.topRows<3>()).norm(),
                                   (local.bottomRows<3>() - nlocal.bottomRows<3>()).norm(),
                                   (local - nlocal).norm(),
                                   (local - nlocal).norm() / std::max(local.norm(), 1e-12),
                                   (lwa.topRows<3>() - nlwa.topRows<3>()).norm(),
                                   (lwa.bottomRows<3>() - nlwa.bottomRows<3>()).norm(),
                                   (lwa - nlwa).norm(),
                                   (lwa - nlwa).norm() / std::max(lwa.norm(), 1e-12),
                                   (residual - nr).norm(),
                                   (residual - nr).norm() / std::max(residual.norm(), 1e-12),
                                   (desiredJ - nd).norm(),
                                   (desiredJ - nd).norm() / std::max(desiredJ.norm(), 1e-12)};
      };
      auto errors = evaluate(1e-6);
      for (auto ref : {Reference::Local, Reference::LocalWorldAligned}) {
        auto J = rotated.tcpJacobian(q, ref);
        auto nJ = numericalJacobian(rotated, q, 1e-6, ref);
        double error = (J - nJ).norm();
        errors.push_back(error);
        errors.push_back(error / std::max(J.norm(), 1e-12));
      }
      csv << sample << ",42";
      for (double value : q) csv << ',' << value;
      for (double x : modelErrors) csv << ',' << x;
      for (double x : errors) csv << ',' << x;
      csv << '\n';
      const std::vector<std::string> names = {
          "local_translation_abs", "local_rotation_abs", "local_full_abs",   "local_full_rel",
          "lwa_translation_abs",   "lwa_rotation_abs",   "lwa_full_abs",     "lwa_full_rel",
          "residual_abs",          "residual_rel",       "desired_body_abs", "desired_body_rel",
          "rotated_local_abs",     "rotated_local_rel",  "rotated_lwa_abs",  "rotated_lwa_rel"};
      for (size_t i = 0; i < names.size(); ++i) stats[names[i]].add(errors[i]);
      if (sample < 50)
        for (double h : {1e-4, 1e-5, 1e-6, 1e-7}) {
          auto e = evaluate(h);
          eps << sample << ',' << h << ',' << e[2] << ',' << e[6] << ',' << e[8] << ',' << e[10]
              << '\n';
        }
    }
    bool pass = true;
    for (const auto& [name, s] : stats) {
      double threshold = name.find("_rel") != std::string::npos
                             ? 1e-6
                             : (name.find("_abs") != std::string::npos ? 1e-6 : 1e-9);
      if (s.max() > threshold) pass = false;
    }
    summary << "{\n\"samples\":2000,\"seed\":42,\"h\":1e-6,\"relative_denominator_floor\":1e-12,"
               "\"model_tolerance\":1e-9,\"derivative_tolerance\":1e-6,\"status\":\""
            << (pass ? "PASS" : "FAIL") << "\",\n\"zero_reference_errors\":[";
    for (size_t i = 0; i < zeroErrors.size(); ++i) {
      if (i) summary << ',';
      summary << zeroErrors[i];
    }
    summary << "],\n\"statistics\":{\n";
    bool first = true;
    for (const auto& [name, s] : stats) {
      if (!first) summary << ",\n";
      first = false;
      summary << '"' << name << "\":";
      s.json(summary);
    }
    summary << "\n}}\n";
    std::cout << "NUMERICAL_" << (pass ? "PASS" : "FAIL") << " samples=2000 seed=42 h=1e-6\n";
    for (const auto& [name, s] : stats)
      std::cout << name << " max=" << std::setprecision(12) << s.max() << '\n';
    return pass ? 0 : 1;
  } catch (const std::exception& e) {
    std::cerr << e.what() << '\n';
    return 1;
  }
}
