#include <predictive_motion_control/nullspace.hpp>
#include <iostream>
#include <stdexcept>
int main() {
  using namespace predictive_motion::control;
  Eigen::MatrixXd j(2,3); j << 1,0,.3,0,1,-.2;
  Eigen::Vector3d primary(.1,-.2,0),z(.5,-.4,.7);
  const auto result=addExactNullspace(j,primary,z,1e-10);
  if ((j*(result.total-primary)).norm()>1e-12 || (result.projector*result.projector-result.projector).norm()>1e-12)
    throw std::runtime_error("Installed projector/command contract failed");
  const auto objective=jointCenterObjective(Eigen::Vector3d(.5,.2,-.1),Eigen::Vector3d::Constant(-1),Eigen::Vector3d::Constant(1));
  if (std::abs(objective.value-.075)>1e-12 || (objective.gradient-Eigen::Vector3d(.25,.1,-.05)).norm()>1e-12)
    throw std::runtime_error("Installed objective contract failed");
  const auto indicators=singularIndicators(j,1e-10,.01,1e-5);
  if (indicators.rank!=2 || !std::isfinite(indicators.condition))
    throw std::runtime_error("Installed singular indicator contract failed");
  std::cout << "INSTALLED_EIGEN_ONLY_NULLSPACE_CONSUMER_PASS\n";
}
