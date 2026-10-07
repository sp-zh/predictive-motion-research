// Root-owned analytic KKT case: arbitrary 3-DoF math without robot/ROS API use.
#include <predictive_motion_control/reactive_qp.hpp>
#include <Eigen/Core>
#include <iostream>
#include <cmath>
using namespace predictive_motion::control;
int main() {
  QpProblem p;
  p.hessian=Eigen::Vector3d(2,4,6).asDiagonal();
  const Eigen::Vector3d reference(1,-2,3),normal(1,2,-1),expected(3.4,.4,2.2);
  p.gradient=-p.hessian*reference;
  p.constraints=normal.transpose();p.lower=Eigen::VectorXd::Constant(1,2);
  p.upper=Eigen::VectorXd::Constant(1,std::numeric_limits<double>::infinity());
  auto r=solveQp(p);
  if(qpSolverVersion()!="1.0.0"||r.status!=QpStatus::Solved||r.velocity.size()!=3)return 1;
  const double primal=(r.velocity-expected).norm();
  const double kkt=(p.hessian*(r.velocity-reference)-4.8*normal).norm();
  if(primal>1e-6||kkt>1e-6||std::abs(normal.dot(r.velocity)-2)>1e-6)return 2;
  // For this analytic optimum the constraint multiplier is +4.8, with
  // stationarity H(x-reference)-multiplier*normal=0, independent of OSQP duals.
  std::cout.precision(17);
  std::cout<<"ROOT_INSTALLED_QP_KKT_PASS n=3 osqp="<<qpSolverVersion()
           <<" analytic_error="<<primal<<" kkt_error="<<kkt<<'\n';
}
