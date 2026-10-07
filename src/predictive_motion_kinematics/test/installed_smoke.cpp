#include <iostream>

#include "predictive_motion_kinematics/robot_kinematics.hpp"
int main(int argc, char** argv) {
  if (argc != 2) return 2;
  try {
    auto config = predictive_motion::loadConfig(argv[1]);
    predictive_motion::RobotKinematics k(config);
    auto q = (k.lowerLimits() + k.upperLimits()) * 0.5;
    auto T = k.tcpPose(q);
    auto J = k.tcpJacobian(q, predictive_motion::Reference::Local);
    if (!T.translation().allFinite() || !J.allFinite()) return 1;
    std::cout << "INSTALLED_CONFIG_OK joints=" << k.jointNames().size() << " urdf=" << config.urdf
              << '\n';
    return 0;
  } catch (const std::exception& e) {
    std::cerr << e.what() << '\n';
    return 1;
  }
}
