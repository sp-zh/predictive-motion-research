#include "../../../tools/phase4_adapters/measured_position_guard.hpp"
#include <iostream>
#include <limits>
int main(){
  using predictive_motion::control::measuredPositionSafe;
  Eigen::VectorXd l=Eigen::VectorXd::Constant(7,-1),u=-l,q=Eigen::VectorXd::Zero(7);
  int cases=0;auto check=[&](bool condition){++cases;if(!condition)throw "guard regression";};
  check(measuredPositionSafe(q,l,u));q=l;check(measuredPositionSafe(q,l,u));q=u;check(measuredPositionSafe(q,l,u));
  for(int j=0;j<7;++j){q.setZero();q(j)=-1.000001;check(!measuredPositionSafe(q,l,u));q(j)=1.000001;check(!measuredPositionSafe(q,l,u));}
  q.setZero();q(0)=std::numeric_limits<double>::quiet_NaN();check(!measuredPositionSafe(q,l,u));
  q(0)=std::numeric_limits<double>::infinity();check(!measuredPositionSafe(q,l,u));
  q.resize(6);check(!measuredPositionSafe(q,l,u));q=Eigen::VectorXd::Zero(7);l(0)=2;check(!measuredPositionSafe(q,l,u));
  std::cout<<"PASS measured physical position guard: "<<cases<<" checks\n";
}
