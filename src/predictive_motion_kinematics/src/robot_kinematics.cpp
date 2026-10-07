#include "predictive_motion_kinematics/robot_kinematics.hpp"

#include <pinocchio/algorithm/frames.hpp>
#include <pinocchio/algorithm/jacobian.hpp>
#include <pinocchio/algorithm/joint-configuration.hpp>
#include <pinocchio/algorithm/model.hpp>
#include <pinocchio/parsers/urdf.hpp>
#include <pinocchio/spatial/explog.hpp>
#include <set>
#include <stdexcept>
namespace predictive_motion {
namespace {
void validatePose(const Pose& pose) {
  if (!pose.translation().allFinite() || !pose.rotation().allFinite() ||
      (pose.rotation().transpose() * pose.rotation() - Eigen::Matrix3d::Identity()).norm() >
          1e-10 ||
      std::abs(pose.rotation().determinant() - 1) > 1e-10)
    throw std::invalid_argument("Invalid SE3 pose");
}
Matrix6 rotateTwist(const Eigen::Matrix3d& R) {
  Matrix6 out = Matrix6::Zero();
  out.topLeftCorner<3, 3>() = R;
  out.bottomRightCorner<3, 3>() = R;
  return out;
}
}  // namespace
Vector6 logResidual(const Pose& actual, const Pose& desired) {
  validatePose(actual);
  validatePose(desired);
  return pinocchio::log6(actual.inverse() * desired).toVector();
}
Matrix6 desiredBodyResidualJacobian(const Pose& actual, const Pose& desired) {
  validatePose(actual);
  validatePose(desired);
  Matrix6 J;
  pinocchio::Jlog6(actual.inverse() * desired, J);
  return J;
}
struct RobotKinematics::Impl {
  RobotConfig config;
  pinocchio::Model model;
  std::unique_ptr<pinocchio::Data> data;
  std::vector<int> qindices, vindices;
  Eigen::VectorXd lower, upper;
  explicit Impl(RobotConfig c) : config(std::move(c)) {
    validatePose(config.world_T_base);
    validatePose(config.flange_T_tcp);
    pinocchio::Model full;
    pinocchio::urdf::buildModel(config.urdf, full);
    std::set<std::string> retained(config.joint_names.begin(), config.joint_names.end());
    if (retained.empty() || retained.size() != config.joint_names.size())
      throw std::invalid_argument("Empty or duplicate joint names");
    for (const auto& name : retained)
      if (!full.existJointName(name))
        throw std::invalid_argument("Unknown retained joint: " + name);
    Eigen::VectorXd reference = pinocchio::neutral(full);
    std::vector<pinocchio::JointIndex> locked;
    for (const auto& [name, q] : config.fixed_joint_positions) {
      if (!full.existJointName(name) || retained.count(name))
        throw std::invalid_argument("Invalid fixed joint: " + name);
      auto id = full.getJointId(name);
      if (full.joints[id].nq() != 1 || !std::isfinite(q))
        throw std::invalid_argument("Fixed joint must have one coordinate");
      auto qi = full.joints[id].idx_q();
      if (q < full.lowerPositionLimit[qi] || q > full.upperPositionLimit[qi])
        throw std::invalid_argument("Fixed joint outside limits");
      reference[qi] = q;
    }
    for (pinocchio::JointIndex id = 1; id < static_cast<pinocchio::JointIndex>(full.njoints);
         ++id) {
      if (!retained.count(full.names[id])) {
        if (!config.fixed_joint_positions.count(full.names[id]))
          throw std::invalid_argument("Every removed joint needs explicit fixed configuration: " +
                                      full.names[id]);
        locked.push_back(id);
      }
    }
    pinocchio::buildReducedModel(full, locked, reference, model);
    data = std::make_unique<pinocchio::Data>(model);
    if (!model.existFrame(config.tcp_parent_frame))
      throw std::invalid_argument("Unknown TCP parent frame");
    lower.resize(config.joint_names.size());
    upper.resize(config.joint_names.size());
    for (size_t i = 0; i < config.joint_names.size(); ++i) {
      auto id = model.getJointId(config.joint_names[i]);
      if (model.joints[id].nq() != 1 || model.joints[id].nv() != 1)
        throw std::invalid_argument("Only one-coordinate retained joints supported");
      qindices.push_back(model.joints[id].idx_q());
      vindices.push_back(model.joints[id].idx_v());
      lower[i] = model.lowerPositionLimit[qindices.back()];
      upper[i] = model.upperPositionLimit[qindices.back()];
      if (!std::isfinite(lower[i]) || !std::isfinite(upper[i]) || lower[i] >= upper[i])
        throw std::invalid_argument("Joint bounds must be finite and strictly ordered");
    }
  }
  Eigen::VectorXd coordinates(const Eigen::VectorXd& q) const {
    if (q.size() != static_cast<int>(qindices.size()) || !q.allFinite())
      throw std::invalid_argument("Invalid joint coordinate dimensions/values");
    Eigen::VectorXd packed = pinocchio::neutral(model);
    for (size_t i = 0; i < qindices.size(); ++i) packed[qindices[i]] = q[i];
    return packed;
  }
  pinocchio::FrameIndex frame(const std::string& name) const {
    if (!model.existFrame(name)) throw std::invalid_argument("Unknown frame: " + name);
    return model.getFrameId(name);
  }
  Pose pose(const Eigen::VectorXd& q, const std::string& name, const Pose& offset) {
    pinocchio::forwardKinematics(model, *data, coordinates(q));
    pinocchio::updateFramePlacements(model, *data);
    return config.world_T_base * data->oMf[frame(name)] * offset;
  }
  Jacobian jacobian(const Eigen::VectorXd& q, const std::string& name, const Pose& offset,
                    Reference ref) {
    if (ref != Reference::Local && ref != Reference::LocalWorldAligned)
      throw std::invalid_argument("Invalid Jacobian reference enum");
    pinocchio::computeJointJacobians(model, *data, coordinates(q));
    pinocchio::updateFramePlacements(model, *data);
    Jacobian full = Jacobian::Zero(6, model.nv);
    pinocchio::getFrameJacobian(model, *data, frame(name), pinocchio::LOCAL, full);
    full = offset.inverse().toActionMatrix() * full;
    if (ref == Reference::LocalWorldAligned)
      full = rotateTwist((config.world_T_base * data->oMf[frame(name)] * offset).rotation()) * full;
    Jacobian selected(6, qindices.size());
    for (size_t i = 0; i < vindices.size(); ++i) selected.col(i) = full.col(vindices[i]);
    return selected;
  }
};
RobotKinematics::RobotKinematics(RobotConfig config)
    : impl_(std::make_unique<Impl>(std::move(config))) {}
RobotKinematics::~RobotKinematics() = default;
RobotKinematics::RobotKinematics(RobotKinematics&&) noexcept = default;
RobotKinematics& RobotKinematics::operator=(RobotKinematics&&) noexcept = default;
Pose RobotKinematics::tcpPose(const Eigen::VectorXd& q) {
  return impl_->pose(q, impl_->config.tcp_parent_frame, impl_->config.flange_T_tcp);
}
Pose RobotKinematics::framePose(const Eigen::VectorXd& q, const std::string& frame) {
  return impl_->pose(q, frame, Pose::Identity());
}
Jacobian RobotKinematics::tcpJacobian(const Eigen::VectorXd& q, Reference ref) {
  return impl_->jacobian(q, impl_->config.tcp_parent_frame, impl_->config.flange_T_tcp, ref);
}
Jacobian RobotKinematics::frameJacobian(const Eigen::VectorXd& q, const std::string& frame,
                                        Reference ref) {
  return impl_->jacobian(q, frame, Pose::Identity(), ref);
}
Jacobian RobotKinematics::residualJacobian(const Eigen::VectorXd& q, const Pose& desired) {
  const Pose E = tcpPose(q).inverse() * desired;
  validatePose(desired);
  Matrix6 jlog;
  pinocchio::Jlog6(E.inverse(), jlog);
  return -jlog * tcpJacobian(q, Reference::Local);
}
const Eigen::VectorXd& RobotKinematics::lowerLimits() const { return impl_->lower; }
const Eigen::VectorXd& RobotKinematics::upperLimits() const { return impl_->upper; }
const std::vector<std::string>& RobotKinematics::jointNames() const {
  return impl_->config.joint_names;
}
}  // namespace predictive_motion
