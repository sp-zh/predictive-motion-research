#pragma once
#include "runtime_observer.hpp"
#include "integrated_horizon_qp.hpp"
#include "geometry.hpp"
namespace phase5_pilot_candidate_validation_v1 {
namespace live=phase5_active_session_v1;namespace core=phase5_active_session_qp_v1;namespace rt=phase5_active_session_runtime_v1;
struct Point {int sample=0,cell=0,cycle=0,half=0;double elapsed=0;live::JointVector acceleration{},jerk{};double min_true=0,min_cover=0,sigma=0,geometry_interval_lower=0,sigma_interval_lower=0,affine_error=0,joint_trust=0;std::size_t geometry_queries=0;bool complete=false;std::string stage="NOT_STARTED",error;};
struct Assessment {live::JointVector initial_q{};Eigen::MatrixXd initial_weighted_body_tcp_jacobian;double initial_true=std::numeric_limits<double>::quiet_NaN(),initial_cover=std::numeric_limits<double>::quiet_NaN(),initial_sigma=std::numeric_limits<double>::quiet_NaN(),initial_simulation_time=std::numeric_limits<double>::quiet_NaN();std::string initial_observation_id,initial_transaction_id;bool initial_geometry_complete=false;bool attempted=false,passed=false;std::vector<Point> points;std::string stage="NOT_STARTED",error;double reach_bound=0,geometry_radius=0,sigma_lipschitz=32;};
// Pure predicted-value checks, no native future/step/history API or execution permit.
void assess(const rt::Snapshot&,const core::Outcome&,const core::CandidateOutcome&,const live::OwnedCandidateValue&,predictive_motion::RobotKinematics&,const predictive_motion::geometry::Scene&,const live::JointVector& physical_speed,Assessment&);
}
