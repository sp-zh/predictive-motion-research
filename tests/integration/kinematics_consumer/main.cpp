#include <iostream>
#include <predictive_motion_kinematics/robot_kinematics.hpp>
int main(int argc, char** argv) {
  if (argc != 2) return 2;
  predictive_motion::RobotKinematics k(predictive_motion::loadConfig(argv[1]));
  auto q = 0.5 * (k.lowerLimits() + k.upperLimits());
  auto T = k.tcpPose(q);
  std::cout << "KINEMATICS_CONSUMER_OK tcp=" << T.translation().transpose() << '\n';
  return T.translation().allFinite() ? 0 : 1;
}
