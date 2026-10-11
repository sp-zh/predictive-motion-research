#include "task_local_provider.hpp"
#include <cmath>
#include <stdexcept>
namespace phase5_active_session_qp_v1 {
TaskLinearizer bindTaskLinearizer(predictive_motion::RobotKinematics& robot,
 const WorldTaskPath& path,const std::string& id){
 if(id.empty()||id.size()>256||!path.start.allFinite()||!path.end.allFinite()||
    !path.quaternion_xyzw.allFinite()||std::abs(path.quaternion_xyzw.norm()-1)>1e-10||
    !std::isfinite(path.lateral_amplitude)||!std::isfinite(path.vertical_amplitude))
  throw std::invalid_argument("bounded pinned finite world task path required");
 return [&robot,path,id](int node,const live::State30& x){
  if(node<0||node>N||!std::isfinite(x.s)||x.s<0||x.s>1)
   throw std::invalid_argument("task node/progress outside original full horizon");
  constexpr double pi=3.14159265358979323846;
  Eigen::VectorXd q(7);for(int j=0;j<7;++j)q(j)=x.q[j];
  const Eigen::Vector3d position=path.start+x.s*(path.end-path.start)+
    Eigen::Vector3d(0,path.lateral_amplitude*std::sin(2*pi*x.s),path.vertical_amplitude*std::sin(pi*x.s));
  const auto desired=predictive_motion::poseFromXyzw(position,path.quaternion_xyzw),actual=robot.tcpPose(q);
  predictive_motion::Vector6 desired_body_derivative=predictive_motion::Vector6::Zero();
  desired_body_derivative.head<3>()=desired.rotation().transpose()*((path.end-path.start)+
    Eigen::Vector3d(0,2*pi*path.lateral_amplitude*std::cos(2*pi*x.s),pi*path.vertical_amplitude*std::cos(pi*x.s)));
  TaskLocal t;t.source_id=id;t.residual=predictive_motion::logResidual(actual,desired);
  t.Jq=robot.residualJacobian(q,desired);
  t.Js=predictive_motion::desiredBodyResidualJacobian(actual,desired)*desired_body_derivative;
  // log(actual^-1 desired); Jq=-Jlog(E^-1)*Jbody_actual,
  // Js=Jlog(E)*desired_body_derivative. Angular scaling occurs exactly once.
  return t;
 };
}
}
