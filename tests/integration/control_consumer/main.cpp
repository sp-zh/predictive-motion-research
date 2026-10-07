#include "predictive_motion_control/ik.hpp"
#include <iostream>
int main() {
  Eigen::MatrixXd matrix = Eigen::MatrixXd::Identity(6,7);
  const auto result=predictive_motion::control::solve(matrix,Eigen::VectorXd::Ones(6));
  if(result.rank!=6 || (matrix*result.dq-Eigen::VectorXd::Ones(6)).norm()>1e-12) return 1;
  std::cout << "INSTALLED_EIGEN_ONLY_CONSUMER_PASS\n";
}
