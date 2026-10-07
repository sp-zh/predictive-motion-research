#include <gtest/gtest.h>

#include <algorithm>
#include <cstdlib>
#include <limits>
#include <pinocchio/spatial/explog.hpp>

#include "predictive_motion_kinematics/robot_kinematics.hpp"
using namespace predictive_motion;
RobotConfig config() {
  const char* path = std::getenv("KINEMATICS_CONFIG");
  if (!path) throw std::runtime_error("KINEMATICS_CONFIG required");
  return loadConfig(path);
}
Eigen::VectorXd mid(RobotKinematics& k) { return 0.5 * (k.lowerLimits() + k.upperLimits()); }
TEST(Kinematics, NamesBoundsAndFixedHand) {
  RobotKinematics k(config());
  EXPECT_EQ(k.jointNames().size(), 7u);
  EXPECT_EQ(k.lowerLimits().size(), 7);
  EXPECT_TRUE((k.upperLimits().array() > k.lowerLimits().array()).all());
  auto q = mid(k);
  EXPECT_TRUE(k.tcpPose(q).translation().allFinite());
  auto c = config();
  c.fixed_joint_positions.clear();
  EXPECT_THROW(RobotKinematics(std::move(c)), std::invalid_argument);
}
TEST(Kinematics, QuaternionConventionAndInvalidInput) {
  auto t =
      poseFromXyzw(Eigen::Vector3d::Zero(), Eigen::Vector4d(0, 0, std::sqrt(0.5), std::sqrt(0.5)));
  EXPECT_NEAR((t.rotation() * Eigen::Vector3d::UnitX() - Eigen::Vector3d::UnitY()).norm(), 0,
              1e-14);
  EXPECT_THROW(poseFromXyzw(Eigen::Vector3d::Zero(), Eigen::Vector4d::Zero()),
               std::invalid_argument);
  EXPECT_THROW(poseFromXyzw(Eigen::Vector3d::Zero(), Eigen::Vector4d(0, 0, 0, 2)),
               std::invalid_argument);
  auto nan = Eigen::Vector4d(0, 0, 0, std::numeric_limits<double>::quiet_NaN());
  EXPECT_THROW(poseFromXyzw(Eigen::Vector3d::Zero(), nan), std::invalid_argument);
  EXPECT_NEAR(logResidual(t, t).norm(), 0, 1e-14);
  Eigen::Vector4d quaternion(0, 0, std::sqrt(0.5), std::sqrt(0.5));
  EXPECT_NEAR((poseFromXyzw(Eigen::Vector3d::Zero(), -quaternion).rotation() - t.rotation()).norm(),
              0, 1e-14);
}
TEST(Kinematics, ToolAndRotatedTranslatedBase) {
  auto c = config();
  RobotKinematics baseline(c);
  auto q = mid(baseline);
  auto T = baseline.tcpPose(q);
  auto base = Pose(Eigen::AngleAxisd(0.7, Eigen::Vector3d(1, 2, 3).normalized()).toRotationMatrix(),
                   Eigen::Vector3d(0.4, -0.2, 0.1));
  c.world_T_base = base;
  RobotKinematics rotated(c);
  EXPECT_NEAR(logResidual(base * T, rotated.tcpPose(q)).norm(), 0, 1e-12);
  EXPECT_NEAR(
      (baseline.tcpJacobian(q, Reference::Local) - rotated.tcpJacobian(q, Reference::Local)).norm(),
      0, 1e-12);
  auto J = baseline.tcpJacobian(q, Reference::LocalWorldAligned);
  J.topRows<3>() = base.rotation() * J.topRows<3>();
  J.bottomRows<3>() = base.rotation() * J.bottomRows<3>();
  EXPECT_NEAR((J - rotated.tcpJacobian(q, Reference::LocalWorldAligned)).norm(), 0, 1e-12);
  auto expected = baseline.framePose(q, c.tcp_parent_frame) * c.flange_T_tcp;
  EXPECT_NEAR(logResidual(expected, T).norm(), 0, 1e-12);
}
TEST(Kinematics, RotationNearPiAndBranchCut) {
  const auto I = Pose::Identity();
  for (double angle : {0.0, 1e-9, 3.141592653589793 - 1e-5, 3.141592653589793 - 1e-8}) {
    Pose t(Eigen::AngleAxisd(angle, Eigen::Vector3d(1, 2, 3).normalized()).toRotationMatrix(),
           Eigen::Vector3d(0.1, -0.2, 0.3));
    auto e = logResidual(I, t);
    EXPECT_TRUE(e.allFinite());
    EXPECT_NEAR(e.tail<3>().norm(), angle, 1e-7);
    EXPECT_NEAR(logResidual(pinocchio::exp6(e), t).norm(), 0, 1e-7);
    EXPECT_TRUE(desiredBodyResidualJacobian(I, t).allFinite());
  }
  // The principal SO3 log is discontinuous at pi; no derivative is asserted across it.
  Eigen::Vector3d axis(0, 0, 1);
  double delta = 1e-6;
  auto before = logResidual(
      I, Pose(Eigen::AngleAxisd(M_PI - delta, axis).toRotationMatrix(), Eigen::Vector3d::Zero()));
  auto after = logResidual(
      I, Pose(Eigen::AngleAxisd(M_PI + delta, axis).toRotationMatrix(), Eigen::Vector3d::Zero()));
  EXPECT_GT((before - after).norm(), 6.0);
}
TEST(Kinematics, RejectInvalidCoordinatesAndFrames) {
  RobotKinematics k(config());
  auto q = mid(k);
  q[0] = std::numeric_limits<double>::quiet_NaN();
  EXPECT_THROW(k.tcpPose(q), std::invalid_argument);
  EXPECT_THROW(k.tcpPose(Eigen::VectorXd::Zero(2)), std::invalid_argument);
  EXPECT_THROW(k.framePose(mid(k), "nonexistent"), std::invalid_argument);
  EXPECT_THROW(k.tcpJacobian(mid(k), static_cast<Reference>(-1)), std::invalid_argument);
  auto c = config();
  c.joint_names.back() = c.joint_names.front();
  EXPECT_THROW(RobotKinematics(std::move(c)), std::invalid_argument);
}
TEST(Kinematics, NearPiDerivativeAwayFromCut) {
  const Pose actual = Pose::Identity();
  const Pose desired(
      Eigen::AngleAxisd(M_PI - 1e-3, Eigen::Vector3d(1, 2, 3).normalized()).toRotationMatrix(),
      Eigen::Vector3d(0.1, -0.2, 0.3));
  Matrix6 numerical;
  const double h = 1e-6;
  for (int i = 0; i < 6; ++i) {
    Vector6 step = Vector6::Zero();
    step[i] = h;
    numerical.col(i) = (logResidual(actual, desired * pinocchio::exp6(step)) -
                        logResidual(actual, desired * pinocchio::exp6(-step))) /
                       (2 * h);
  }
  const double error = (numerical - desiredBodyResidualJacobian(actual, desired)).norm();
  std::cout << "near_pi_desired_body_derivative_error=" << error << '\n';
  EXPECT_LT(error, 1e-5);
}
TEST(Kinematics, ConfiguredJointOrderIsPreserved) {
  auto c = config();
  RobotKinematics original(c);
  auto q = mid(original);
  q[0] += 0.1;
  q[2] -= 0.2;
  std::reverse(c.joint_names.begin(), c.joint_names.end());
  RobotKinematics reordered(c);
  EXPECT_NEAR(logResidual(original.tcpPose(q), reordered.tcpPose(q.reverse().eval())).norm(), 0,
              1e-12);
  auto J = original.tcpJacobian(q, Reference::Local);
  auto permuted = reordered.tcpJacobian(q.reverse().eval(), Reference::Local);
  for (int i = 0; i < q.size(); ++i)
    EXPECT_NEAR((J.col(i) - permuted.col(q.size() - 1 - i)).norm(), 0, 1e-12);
}
