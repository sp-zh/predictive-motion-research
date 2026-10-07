#pragma once
#include <Eigen/SVD>
#include <predictive_motion_control/predictive.hpp>

#include "geometry.hpp"
namespace predictive_motion::preview_adapter {
using namespace predictive_motion::geometry;
using namespace predictive_motion::control;
struct Path {
  V start, end;
  Eigen::Vector4d xyzw;
  double lateral = 0, vertical = 0;
  Eigen::VectorXd joint_start, joint_direction;
  bool joint_path = false;
  Pose pose(RobotKinematics& robot, double s) const {
    if (joint_path) return robot.tcpPose(joint_start + s * joint_direction);
    V position = start + s * (end - start) +
                 V(0, lateral * std::sin(2 * M_PI * s), vertical * std::sin(M_PI * s));
    return poseFromXyzw(position, xyzw);
  }
  Vector6 derivative(RobotKinematics& robot, double s) const {
    if (joint_path)
      return robot.tcpJacobian(joint_start + s * joint_direction, Reference::Local) *
             joint_direction;
    auto desired = pose(robot, s);
    Vector6 nu = Vector6::Zero();
    nu.head<3>() = desired.rotation().transpose() *
                   ((end - start) + V(0, 2 * M_PI * lateral * std::cos(2 * M_PI * s),
                                      M_PI * vertical * std::cos(M_PI * s)));
    return nu;
  }
};
struct Indicators {
  double sigma, condition, gap;
  bool nonsmooth;
};
inline Indicators indicators(RobotKinematics& robot, const Eigen::VectorXd& q, double length) {
  auto j = robot.tcpJacobian(q, Reference::Local);
  j.bottomRows(3) *= length;
  Eigen::JacobiSVD<Eigen::MatrixXd> svd(j);
  auto s = svd.singularValues();
  if (!s.allFinite()) throw std::runtime_error("invalid SVD");
  int m = s.size();
  double gap = m > 1 ? s(m - 2) - s(m - 1) : INFINITY;
  return {s(m - 1), s(m - 1) > 0 ? s(0) / s(m - 1) : INFINITY, gap, s(m - 1) < 1e-10 || gap < 1e-7};
}
inline Eigen::RowVectorXd sigmaGradient(RobotKinematics& robot, const Eigen::VectorXd& q,
                                        double length) {
  Eigen::RowVectorXd g(q.size());
  for (int i = 0; i < q.size(); ++i) {
    auto plus = q, minus = q;
    plus(i) += 1e-6;
    minus(i) -= 1e-6;
    g(i) = (indicators(robot, plus, length).sigma - indicators(robot, minus, length).sigma) / 2e-6;
  }
  return g;
}
inline PreviewStage taskStage(RobotKinematics& robot, const PreviewState& x, const Path& path,
                              double length) {
  auto desired = path.pose(robot, x.s), actual = robot.tcpPose(x.q);
  PreviewStage stage;
  stage.residual = logResidual(actual, desired);
  stage.joint_derivative = robot.residualJacobian(x.q, desired);
  stage.path_derivative =
      desiredBodyResidualJacobian(actual, desired) * path.derivative(robot, x.s);
  stage.residual.tail(3) *= length;
  stage.joint_derivative.bottomRows(3) *= length;
  stage.path_derivative.tail(3) *= length;
  return stage;
}
}  // namespace predictive_motion::preview_adapter
