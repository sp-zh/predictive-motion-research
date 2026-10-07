#include "predictive_motion_control/nullspace.hpp"

#include <gtest/gtest.h>

#include <limits>

#include "predictive_motion_control/ik.hpp"
using namespace predictive_motion::control;
TEST(Nullspace, ExactAndDampedAreDifferent) {
  Eigen::MatrixXd j = Eigen::MatrixXd::Zero(3, 4);
  j.leftCols(3).diagonal() << 1, .1, .001;
  auto p = exactNullProjector(j, 1e-10), d = dampedProjector(j, .03, 1e-10);
  EXPECT_LT((j * p).norm(), 1e-12);
  EXPECT_LT((p * p - p).norm(), 1e-12);
  EXPECT_LT((p - p.transpose()).norm(), 1e-12);
  EXPECT_LT((p - (Eigen::Matrix4d::Identity() - pseudoInverse(j, 1e-10) * j)).norm(), 1e-12);
  EXPECT_GT((j * d).norm(), .005);
  EXPECT_GT((d * d - d).norm(), .01);
  EXPECT_EQ((dampedProjector(j, 0, 1e-10) - p).norm(), 0);
  auto c = addExactNullspace(j, Eigen::Vector4d::Ones(), Eigen::Vector4d::Ones(), 1e-10);
  EXPECT_LT(c.raw_task_leakage, 1e-12);
  EXPECT_NEAR(c.total[3], 2, 1e-12);
}
TEST(Nullspace, JointGradientAndDescent) {
  Eigen::Vector3d q(.3, -.2, .7), lo(-1, -2, -3), hi(2, 3, 4);
  auto h = jointCenterObjective(q, lo, hi);
  double step = 1e-6;
  for (int i = 0; i < 3; ++i) {
    auto a = q, b = q;
    a[i] += step;
    b[i] -= step;
    EXPECT_NEAR(h.gradient[i],
                (jointCenterObjective(a, lo, hi).value - jointCenterObjective(b, lo, hi).value) /
                    (2 * step),
                1e-9);
  }
  EXPECT_LT(jointCenterObjective(q - .01 * h.gradient, lo, hi).value, h.value);
}
TEST(Nullspace, SvdIndicatorsAndTallRankDeficiency) {
  Eigen::MatrixXd j = Eigen::MatrixXd::Zero(3, 4);
  j.leftCols(3).diagonal() << 1, .1, .001;
  auto m = singularIndicators(j, 1e-10, .01, 1e-5);
  EXPECT_NEAR(m.manipulability, .0001, 1e-15);
  EXPECT_NEAR(m.log_manipulability, std::log(.0001), 1e-12);
  EXPECT_NEAR(m.condition, 1000, 1e-10);
  EXPECT_TRUE(m.simple_min);
  EXPECT_FALSE(m.near_rank);
  auto tall = singularIndicators(Eigen::MatrixXd::Identity(4, 3), 1e-10, .01, 1e-5);
  EXPECT_EQ(tall.sigma_min, 0);
  EXPECT_EQ(tall.manipulability, 0);
  EXPECT_TRUE(std::isinf(tall.log_manipulability));
  EXPECT_TRUE(std::isfinite(tall.regularized_log_volume));
}
TEST(Nullspace, IndependentSingularDirectionalDerivative) {
  JacobianEvaluator evaluator = [](const Eigen::VectorXd& q) {
    Eigen::MatrixXd j = Eigen::MatrixXd::Zero(2, 3);
    j(0, 0) = 2 + q[0];
    j(1, 1) = .2 + .1 * q[1];
    return j;
  };
  Eigen::Vector3d q(.1, .2, .3);
  auto gradient = finiteDifferenceGradient(q, evaluator, SingularObjective::MinimumSingularValue,
                                           1e-6, 1e-10, .01, 1e-5);
  EXPECT_LT((gradient.gradient - Eigen::Vector3d(0, .1, 0)).norm(), 1e-9);
  EXPECT_EQ(gradient.evaluations, 7);
  EXPECT_TRUE(gradient.simple_min);
  auto volume = finiteDifferenceGradient(q, evaluator, SingularObjective::RegularizedLogVolume,
                                         1e-6, 1e-10, .01, 1e-5);
  EXPECT_NEAR(volume.gradient[0], 2.1 / (2.1 * 2.1 + .0001), 1e-9);
  EXPECT_NEAR(volume.gradient[1], .022 / (.22 * .22 + .0001), 1e-9);
  auto repeated = singularIndicators(Eigen::Matrix3d::Identity(), 1e-10, .01, 1e-5);
  EXPECT_FALSE(repeated.simple_min);
}
TEST(Nullspace, InvalidInputs) {
  Eigen::MatrixXd j = Eigen::MatrixXd::Identity(3, 4);
  EXPECT_THROW(exactNullProjector(j, -1), std::invalid_argument);
  EXPECT_THROW(dampedProjector(j, -.1, 1e-10), std::invalid_argument);
  j(0, 0) = std::numeric_limits<double>::quiet_NaN();
  EXPECT_THROW(exactNullProjector(j, 1e-10), std::invalid_argument);
  EXPECT_THROW(jointCenterObjective(Eigen::Vector3d::Ones(), Eigen::Vector3d::Zero(),
                                    Eigen::Vector3d::Zero()),
               std::invalid_argument);
  EXPECT_THROW(
      finiteDifferenceGradient(Eigen::Vector3d::Zero(), {}, SingularObjective::MinimumSingularValue,
                               1e-6, 1e-10, .01, 1e-5),
      std::invalid_argument);
  EXPECT_THROW(addExactNullspace(Eigen::MatrixXd::Identity(3, 4), Eigen::Vector3d::Zero(),
                                 Eigen::Vector3d::Zero(), 1e-10),
               std::invalid_argument);
}
TEST(Nullspace, FiniteSvdOverflowAndLeakageRejected) {
  Eigen::MatrixXd huge = Eigen::MatrixXd::Constant(3, 4, 1e308);
  EXPECT_THROW(exactNullProjector(huge, 1e-10), std::overflow_error);
  EXPECT_THROW(dampedProjector(huge, .03, 1e-10), std::overflow_error);
  EXPECT_THROW(singularIndicators(huge, 1e-10, .01, 1e-5), std::overflow_error);
  Eigen::MatrixXd diagonal = Eigen::MatrixXd::Zero(3, 4);
  diagonal.leftCols(3).diagonal() << 1e308, .8e308, .5e308;
  EXPECT_THROW(
      addExactNullspace(diagonal, Eigen::Vector4d::Zero(), Eigen::Vector4d::Constant(1e308), .9),
      std::overflow_error);
  auto stable = singularIndicators(Eigen::MatrixXd::Constant(1, 1, 1e308), 1e-10, 1.7e308, 1e-5);
  EXPECT_TRUE(std::isfinite(stable.regularized_log_volume));
  EXPECT_EQ(stable.rank, 1);
}
