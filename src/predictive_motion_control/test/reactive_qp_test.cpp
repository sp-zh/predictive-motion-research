#include "predictive_motion_control/reactive_qp.hpp"
#include <gtest/gtest.h>
#include <Eigen/Cholesky>
using namespace predictive_motion::control;
TEST(ReactiveQp, RuntimeVersionIsPinned) { EXPECT_EQ(qpSolverVersion(),"1.0.0"); }
TEST(ReactiveQp, UnconstrainedRidgeEquivalence) {
  Eigen::MatrixXd j(3, 4);
  j << 1, 2, 0, 1, 0, 1, 2, 3, 1, 0, 3, 1;
  Eigen::Vector3d twist(.1, -.2, .3);
  auto p = trackingProblem(j, twist, .01);
  auto r = solveQp(p);
  ASSERT_EQ(r.status, QpStatus::Solved);
  EXPECT_LT((r.velocity - p.hessian.ldlt().solve(-p.gradient)).norm(), 1e-6);
}
TEST(ReactiveQp, VelocityBoundAndDamper) {
  auto p = trackingProblem(Eigen::Matrix2d::Identity(), Eigen::Vector2d(1, -1), 0);
  appendConstraint(p, Eigen::RowVector2d(1, 0), -.2, .2);
  appendDamper(p, Eigen::RowVector2d(0, 1), .015, .01, 2);
  auto r = solveQp(p);
  ASSERT_EQ(r.status, QpStatus::Solved);
  EXPECT_NEAR(r.velocity(0), .2, 1e-6);
  EXPECT_NEAR(r.velocity(1), -.01, 1e-6);
}
TEST(ReactiveQp, ActiveMeasuredAndAcceptedPositionBounds) {
  CommandLimits l;
  l.position_lower = Eigen::VectorXd::Constant(1, -1);
  l.position_upper = Eigen::VectorXd::Constant(1, 1);
  l.velocity = Eigen::VectorXd::Constant(1, 10);
  l.acceleration = Eigen::VectorXd::Constant(1, 100);
  l.jerk = Eigen::VectorXd::Constant(1, 1e6);
  l.dt = .1; l.position_margin = .01;
  CommandHistory h;
  h.measured_position = Eigen::VectorXd::Constant(1, .97);
  h.accepted_position = Eigen::VectorXd::Constant(1, .98);
  h.accepted_velocity = h.accepted_acceleration = Eigen::VectorXd::Zero(1);
  auto p = constrainCommand(trackingProblem(Eigen::MatrixXd::Identity(1, 1),
                           Eigen::VectorXd::Constant(1, 1), 0), l, h);
  auto r = solveQp(p);
  ASSERT_EQ(r.status, QpStatus::Solved);
  EXPECT_NEAR(r.velocity(0), .1, 1e-6);
}
TEST(ReactiveQp, CommandAccelerationAndJerk) {
  CommandLimits l;
  l.position_lower = Eigen::VectorXd::Constant(1, -10);
  l.position_upper = Eigen::VectorXd::Constant(1, 10);
  l.velocity = Eigen::VectorXd::Constant(1, 2);
  l.acceleration = Eigen::VectorXd::Constant(1, 1);
  l.jerk = Eigen::VectorXd::Constant(1, 20);
  CommandHistory h;
  h.measured_position = h.accepted_position = h.accepted_velocity =
      h.accepted_acceleration = Eigen::VectorXd::Zero(1);
  auto p = constrainCommand(trackingProblem(Eigen::MatrixXd::Identity(1, 1),
                           Eigen::VectorXd::Constant(1, 1), 0), l, h);
  auto r = solveQp(p);
  ASSERT_EQ(r.status, QpStatus::Solved);
  EXPECT_NEAR(r.velocity(0), 20 * .004 * .004, 1e-7);
}
TEST(ReactiveQp, CoupledInfeasibleNoCommand) {
  auto p = stoppingProblem(2);
  appendConstraint(p, Eigen::RowVector2d(1, 0), 1, 2);
  appendConstraint(p, Eigen::RowVector2d(0, 1), 1, 2);
  appendConstraint(p, Eigen::RowVector2d(1, 1), -1, 0);
  auto r = solveQp(p);
  EXPECT_EQ(r.status, QpStatus::PrimalInfeasible);
  EXPECT_EQ(r.velocity.size(), 0);
}
TEST(ReactiveQp, ContradictoryBoundsNoCommand) {
  auto p = stoppingProblem(1);
  appendConstraint(p, Eigen::RowVectorXd::Ones(1), 1, -1);
  auto r = solveQp(p);
  EXPECT_EQ(r.status, QpStatus::InfeasibleBounds);
  EXPECT_EQ(r.velocity.size(), 0);
}
TEST(ReactiveQp, NonFiniteAndStaleNoCommand) {
  auto p = stoppingProblem(2);
  p.gradient(0) = std::numeric_limits<double>::quiet_NaN();
  EXPECT_EQ(solveQp(p).status, QpStatus::InvalidInput);
  p.gradient.setZero(); p.state_age_seconds = .051;
  auto r = solveQp(p);
  EXPECT_EQ(r.status, QpStatus::StaleState);
  EXPECT_EQ(r.velocity.size(), 0);
  p.state_age_seconds = -1;
  EXPECT_EQ(solveQp(p).status, QpStatus::InvalidInput);
}
TEST(ReactiveQp, SolverIterationLimitNoCommand) {
  auto p = trackingProblem(Eigen::Matrix2d::Identity(), Eigen::Vector2d(1, 2), .001);
  QpOptions o; o.max_iterations = 1;
  auto r = solveQp(p, o);
  EXPECT_EQ(r.status, QpStatus::IterationLimit);
  EXPECT_EQ(r.velocity.size(), 0);
}
TEST(ReactiveQp, SolverTimeLimitNoCommand) {
  auto p = trackingProblem(Eigen::MatrixXd::Identity(100, 100),
                          Eigen::VectorXd::Ones(100), .01);
  QpOptions o; o.time_limit_seconds = 1e-12;
  auto r = solveQp(p, o);
  EXPECT_EQ(r.status, QpStatus::TimeLimit);
  EXPECT_EQ(r.velocity.size(), 0);
}
TEST(ReactiveQp, NonConvexNoCommand) {
  auto p = stoppingProblem(2); p.hessian(0, 0) = -1;
  auto r = solveQp(p);
  EXPECT_EQ(r.status, QpStatus::NonConvex);
  EXPECT_EQ(r.velocity.size(), 0);
}
TEST(ReactiveQp, FiniteInputOverflowDoesNotHideIndefiniteHessian) {
  auto p = stoppingProblem(2);
  p.hessian(0, 0) = -1e155; p.hessian(1, 1) = 1e155;
  auto r = solveQp(p);
  EXPECT_EQ(r.status, QpStatus::NonConvex);
  EXPECT_EQ(r.velocity.size(), 0);
  EXPECT_THROW(trackingProblem(Eigen::MatrixXd::Constant(2, 2, 1e200),
                              Eigen::Vector2d::Ones(), .01), std::overflow_error);
}
TEST(ReactiveQp, FiniteConstraintOverflowNeverProducesAcceptedCommand) {
  auto p=stoppingProblem(1);p.gradient(0)=-2;
  appendConstraint(p,Eigen::RowVectorXd::Constant(1,1e308),
                   -std::numeric_limits<double>::infinity(),std::numeric_limits<double>::infinity());
  auto r=solveQp(p);
  EXPECT_NE(r.status,QpStatus::Solved);
  EXPECT_EQ(r.velocity.size(),0);
}
TEST(ReactiveQp, BuilderOverflowAndInvalidBoundsAreExplicit) {
  auto p=stoppingProblem(1);
  EXPECT_THROW(appendDamper(p,Eigen::RowVectorXd::Ones(1),1e308,0,1e308),std::overflow_error);
  appendConstraint(p,Eigen::RowVectorXd::Ones(1),0,std::numeric_limits<double>::infinity());
  p.upper(0)=std::numeric_limits<double>::quiet_NaN();
  EXPECT_EQ(solveQp(p).status,QpStatus::InvalidInput);
}
TEST(ReactiveQp, DualUnboundedIsDistinctFromPrimalInfeasible) {
  auto p=stoppingProblem(1);p.hessian.setZero();p.gradient(0)=-1;
  auto r=solveQp(p);
  EXPECT_EQ(r.status,QpStatus::DualInfeasible);
  EXPECT_EQ(r.velocity.size(),0);
}
TEST(ReactiveQp, StopRespectsAccelerationAndRejectsInfeasibleStop) {
  CommandLimits l;
  l.position_lower = Eigen::VectorXd::Constant(1, -1);
  l.position_upper = Eigen::VectorXd::Constant(1, 1);
  l.velocity = Eigen::VectorXd::Constant(1, 2);
  l.acceleration = Eigen::VectorXd::Constant(1, 1);
  l.jerk = Eigen::VectorXd::Constant(1, 20);
  CommandHistory h;
  h.measured_position = h.accepted_position = Eigen::VectorXd::Zero(1);
  h.accepted_velocity = Eigen::VectorXd::Constant(1, .1);
  h.accepted_acceleration = Eigen::VectorXd::Constant(1, -1);
  auto r = solveQp(constrainCommand(stoppingProblem(1), l, h));
  ASSERT_EQ(r.status, QpStatus::Solved);
  EXPECT_NEAR(r.velocity(0), .096, 1e-6);
  h.measured_position(0) = h.accepted_position(0) = .999;
  r = solveQp(constrainCommand(stoppingProblem(1), l, h));
  EXPECT_EQ(r.status, QpStatus::InfeasibleBounds);
  EXPECT_EQ(r.velocity.size(), 0);
}
