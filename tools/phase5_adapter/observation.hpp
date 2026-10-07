#pragma once
#include <chrono>
#include <predictive_motion_sim/plant.hpp>

#include "geometry.hpp"
using namespace predictive_motion;
using namespace predictive_motion::geometry;
using Clock = std::chrono::steady_clock;
inline double observationSeconds(Clock::time_point start) {
  return std::chrono::duration<double>(Clock::now() - start).count();
}
inline Eigen::VectorXd mapped(const std::vector<double>& v) {
  return Eigen::Map<const Eigen::VectorXd>(v.data(), v.size());
}
struct Observed {
  Eigen::VectorXd q, dq;
  Pose tcp;
  double clearance, seconds, fk_error, frame_error;
  int contacts;
  Clock::time_point capture;
};
Observed observe(Plant& plant, mjData* scratch, RobotKinematics& robot, const Scene& geometry) {
  const auto start = Clock::now();
  const auto* model = plant.model();
  const unsigned int spec = mjSTATE_INTEGRATION;
  std::vector<mjtNum> before(mj_stateSize(model, spec)), after(before.size());
  mj_getState(model, plant.data(), before.data(), spec);
  mj_copyData(scratch, model, plant.data());
  mj_forward(model, scratch);
  const auto capture = Clock::now();
  const Eigen::VectorXd q = mapped(plant.positions()), dq = mapped(plant.velocities());
  const Pose tcp = robot.tcpPose(q);
  const int site = mj_name2id(model, mjOBJ_SITE, "inspection_tcp");
  if (site < 0) throw std::runtime_error("Missing TCP site");
  Pose actual(
      Eigen::Map<const Eigen::Matrix<double, 3, 3, Eigen::RowMajor>>(scratch->site_xmat + 9 * site),
      Eigen::Map<const V>(scratch->site_xpos + 3 * site));
  double fk_error = logResidual(tcp, actual).norm(), frame_error = 0;
  for (const auto& object : geometry.objects)
    if (object.category == "arm") {
      int body = mj_name2id(model, mjOBJ_BODY, object.frame.c_str());
      if (body < 0) throw std::runtime_error("Missing common body");
      Pose physical(
          Eigen::Map<const Eigen::Matrix<double, 3, 3, Eigen::RowMajor>>(scratch->xmat + 9 * body),
          Eigen::Map<const V>(scratch->xpos + 3 * body));
      frame_error =
          std::max(frame_error, logResidual(robot.framePose(q, object.frame), physical).norm());
    }
  auto query = geometry.query(robot, q, false, false);
  mj_getState(model, plant.data(), after.data(), spec);
  if (before != after || fk_error > 1e-8 || frame_error > 1e-8)
    throw std::runtime_error("Independent observer contract violated");
  return {q,
          dq,
          tcp,
          query.minimum_true,
          observationSeconds(start),
          fk_error,
          frame_error,
          scratch->ncon,
          capture};
}
