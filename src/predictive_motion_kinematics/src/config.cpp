#include <yaml-cpp/yaml.h>

#include <filesystem>
#include <stdexcept>

#include "predictive_motion_kinematics/robot_kinematics.hpp"
namespace predictive_motion {
Pose poseFromXyzw(const Eigen::Vector3d& translation, const Eigen::Vector4d& xyzw) {
  if (!translation.allFinite() || !xyzw.allFinite() || std::abs(xyzw.norm() - 1) > 1e-10)
    throw std::invalid_argument("Quaternion xyzw must be finite and unit length");
  Eigen::Quaterniond q(xyzw[3], xyzw[0], xyzw[1], xyzw[2]);
  return Pose(q.toRotationMatrix(), translation);
}
RobotConfig loadConfig(const std::string& path) {
  auto yaml = YAML::LoadFile(path);
  RobotConfig c;
  c.urdf = (std::filesystem::path(path).parent_path() / yaml["urdf"].as<std::string>())
               .lexically_normal()
               .string();
  c.joint_names = yaml["joint_names"].as<std::vector<std::string>>();
  if (yaml["fixed_joint_positions"])
    c.fixed_joint_positions = yaml["fixed_joint_positions"].as<std::map<std::string, double>>();
  c.tcp_parent_frame = yaml["tcp_parent_frame"].as<std::string>();
  auto pose = [&yaml](const std::string& prefix) {
    auto t = yaml[prefix + "_translation"].as<std::vector<double>>();
    auto q = yaml[prefix + "_quaternion_xyzw"].as<std::vector<double>>();
    if (t.size() != 3 || q.size() != 4)
      throw std::invalid_argument("Invalid pose config dimensions");
    return poseFromXyzw(Eigen::Vector3d(t[0], t[1], t[2]), Eigen::Vector4d(q[0], q[1], q[2], q[3]));
  };
  c.flange_T_tcp = pose("tcp");
  c.world_T_base = pose("base");
  return c;
}
}  // namespace predictive_motion
