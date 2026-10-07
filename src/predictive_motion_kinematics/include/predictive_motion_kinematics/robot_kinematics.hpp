#pragma once
#include <Eigen/Core>
#include <Eigen/Geometry>
#include <map>
#include <memory>
#include <pinocchio/spatial/se3.hpp>
#include <string>
#include <vector>
namespace predictive_motion {
using Pose = pinocchio::SE3;
using Vector6 = Eigen::Matrix<double, 6, 1>;
using Matrix6 = Eigen::Matrix<double, 6, 6>;
using Jacobian = Eigen::Matrix<double, 6, Eigen::Dynamic>;
enum class Reference { Local, LocalWorldAligned };
struct RobotConfig {
  std::string urdf;
  std::vector<std::string> joint_names;
  std::map<std::string, double> fixed_joint_positions;
  std::string tcp_parent_frame;
  Pose flange_T_tcp = Pose::Identity();
  Pose world_T_base = Pose::Identity();
};
RobotConfig loadConfig(const std::string& yaml_path);
// Input quaternion order is explicitly x,y,z,w. Reject nonfinite/nonunit input.
Pose poseFromXyzw(const Eigen::Vector3d& translation, const Eigen::Vector4d& xyzw);
Vector6 logResidual(const Pose& actual, const Pose& desired);
Matrix6 desiredBodyResidualJacobian(const Pose& actual, const Pose& desired);
class RobotKinematics {
 public:
  explicit RobotKinematics(RobotConfig config);
  ~RobotKinematics();
  RobotKinematics(RobotKinematics&&) noexcept;
  RobotKinematics& operator=(RobotKinematics&&) noexcept;
  RobotKinematics(const RobotKinematics&) = delete;
  RobotKinematics& operator=(const RobotKinematics&) = delete;
  Pose tcpPose(const Eigen::VectorXd& q);
  Pose framePose(const Eigen::VectorXd& q, const std::string& frame);
  Jacobian tcpJacobian(const Eigen::VectorXd& q, Reference reference);
  Jacobian frameJacobian(const Eigen::VectorXd& q, const std::string& frame, Reference reference);
  Jacobian residualJacobian(const Eigen::VectorXd& q, const Pose& desired);
  const Eigen::VectorXd& lowerLimits() const;
  const Eigen::VectorXd& upperLimits() const;
  const std::vector<std::string>& jointNames() const;

 private:
  struct Impl;
  std::unique_ptr<Impl> impl_;
};
}  // namespace predictive_motion
