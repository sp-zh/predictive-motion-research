#include <iostream>
#include <pinocchio/algorithm/kinematics.hpp>
#include <pinocchio/config.hpp>
#include <pinocchio/multibody/data.hpp>
#include <pinocchio/multibody/model.hpp>
int main() {
  pinocchio::Model m;
  pinocchio::Data d(m);
  Eigen::VectorXd q = Eigen::VectorXd::Zero(m.nq);
  pinocchio::forwardKinematics(m, d, q);
  std::cout << "PINOCCHIO_LINK_OK " << PINOCCHIO_VERSION << '\n';
}
