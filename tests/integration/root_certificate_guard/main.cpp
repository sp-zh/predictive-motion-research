// Diagnostic counterexample: coefficientwise certificate error can amplify
// into a negative eigenvalue beyond the declared spectral tolerance.
#include <predictive_motion_control/reactive_qp.hpp>
#include <Eigen/Core>
#include <Eigen/SparseCore>
#include <iostream>
using namespace predictive_motion::control;
int main(){
  constexpr int n=128;constexpr double epsilon=9e-13;
  QpProblem p;p.hessian=Eigen::MatrixXd::Constant(n,n,-epsilon);
  p.gradient=Eigen::VectorXd::Zero(n);p.constraints=Eigen::MatrixXd::Identity(n,n);
  p.lower=Eigen::VectorXd::Constant(n,-1);p.upper=-p.lower;
  Eigen::SparseMatrix<double> factor(1,n);
  auto ordinary=solveQp(p);auto certified=solveQpCertified(p,QpOptions{},Eigen::VectorXd::Zero(n),factor);
  std::cout.precision(17);
  std::cout<<"n="<<n<<" max_entry_certificate_error="<<epsilon<<" actual_min_eigenvalue="<<-n*epsilon
           <<" ordinary_status="<<statusName(ordinary.status)<<" certified_status="<<statusName(certified.status)
           <<" certified_command_size="<<certified.velocity.size()<<'\n';
  if(ordinary.status!=QpStatus::NonConvex)return 2;
  // Regression mode: no certified command may escape this invalid certificate.
  return certified.status!=QpStatus::Solved&&certified.velocity.size()==0?0:1;
}
