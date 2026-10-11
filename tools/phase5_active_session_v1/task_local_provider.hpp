#pragma once
#include "integrated_horizon_qp.hpp"
#include <predictive_motion_kinematics/robot_kinematics.hpp>
namespace phase5_active_session_qp_v1 {
struct WorldTaskPath {
 Eigen::Vector3d start,end;Eigen::Vector4d quaternion_xyzw;
 double lateral_amplitude=0,vertical_amplitude=0;
};
// Borrow actual kinematics; copy bounded world-curve parameters. The source
// runner freezes robot config/URDF/TCP/base and path before any queries.
// No coal/geometry/legacy predictive.cpp dependency or safety certificate.
TaskLinearizer bindTaskLinearizer(predictive_motion::RobotKinematics&,
 const WorldTaskPath&,const std::string& source_id);
}
