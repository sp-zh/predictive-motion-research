#include <predictive_motion_control/reactive_qp.hpp>
#include <iostream>
using namespace predictive_motion::control;
int main() {
  auto p=trackingProblem(Eigen::MatrixXd::Identity(4,4),Eigen::VectorXd::Ones(4),.01);
  appendConstraint(p,Eigen::RowVector4d(1,0,0,0),-.2,.2);
  auto result=solveQp(p);
  if(qpSolverVersion()!="1.0.0" || result.status!=QpStatus::Solved || std::abs(result.velocity(0)-.2)>1e-6)return 1;
  std::cout<<"Installed four-DOF Eigen-only consumer OSQP="<<qpSolverVersion()<<" PASS\n";
}
