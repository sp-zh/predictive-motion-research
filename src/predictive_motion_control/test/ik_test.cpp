#include "predictive_motion_control/ik.hpp"

#include <gtest/gtest.h>

#include <Eigen/Cholesky>
#include <limits>
using namespace predictive_motion::control;
TEST(Ik, MoorePenroseIdentitiesRectangularAndRankDeficient) {
  Eigen::MatrixXd a(3, 4);
  a << 1, 2, 3, 4, 0, 1, 0, 1, 2, 4, 6, 8;
  const auto p = pseudoInverse(a, 1e-10);
  EXPECT_LT((a * p * a - a).norm(), 1e-12);
  EXPECT_LT((p * a * p - p).norm(), 1e-12);
  EXPECT_LT((a * p - (a * p).transpose()).norm(), 1e-12);
  EXPECT_LT((p * a - (p * a).transpose()).norm(), 1e-12);
  auto result = solve(a, Eigen::Vector3d(1, 2, 3));
  EXPECT_EQ(result.rank, 2);
  EXPECT_TRUE(result.dq.allFinite());
  EXPECT_TRUE(std::isinf(result.condition));
}
TEST(Ik, FullRankAndDlsNormalEquation) {
  Eigen::MatrixXd a(3, 4);
  a << 1, 2, 0, 1, 0, 2, 1, 0, 1, 0, 3, 2;
  Eigen::Vector3d b(1, -2, .3);
  EXPECT_LT((solve(a, b).dq - a.transpose() * (a * a.transpose()).ldlt().solve(b)).norm(), 1e-12);
  Options o;
  o.method = Method::FixedDls;
  o.damping = .03;
  EXPECT_LT(
      (solve(a, b, o).dq -
       a.transpose() * (a * a.transpose() + .0009 * Eigen::Matrix3d::Identity()).ldlt().solve(b))
          .norm(),
      1e-12);
}
TEST(Ik, SingularSweepAndExactZeroRemainFinite) {
  for (double sigma : {1., .1, .001, 1e-6, 1e-12, 0.}) {
    Eigen::Matrix3d a = Eigen::Matrix3d::Identity();
    a(2, 2) = sigma;
    auto mp = solve(a, Eigen::Vector3d::UnitZ());
    Options o;
    o.method = Method::FixedDls;
    o.damping = .01;
    auto dls = solve(a, Eigen::Vector3d::UnitZ(), o);
    EXPECT_TRUE(mp.dq.allFinite());
    EXPECT_LE(dls.dq.norm(), 50. + 1e-12);
    if (sigma > 1e-10)
      EXPECT_NEAR(mp.dq[2], 1 / sigma, 1e-6);
    else
      EXPECT_EQ(mp.dq[2], 0);
    EXPECT_NEAR(dls.dq[2], sigma / (sigma * sigma + .0001), 1e-10);
    o.damping = 0;
    EXPECT_LT((solve(a, Eigen::Vector3d::UnitZ(), o).dq - mp.dq).norm(), 1e-12);
  }
  EXPECT_EQ(pseudoInverse(Eigen::MatrixXd::Zero(3, 4), 1e-10).norm(), 0);
}
TEST(Ik, RankToleranceAndAdaptivePolicy) {
  Eigen::Matrix3d a = Eigen::Matrix3d::Identity();
  a(2, 2) = 1e-8;
  Options o;
  o.relative_rank_tolerance = 1e-7;
  EXPECT_EQ(solve(a, Eigen::Vector3d::Ones(), o).rank, 2);
  o.relative_rank_tolerance = 1e-9;
  EXPECT_EQ(solve(a, Eigen::Vector3d::Ones(), o).rank, 3);
  o.method = Method::AdaptiveDls;
  o.damping = .03;
  o.adaptive_sigma_threshold = .05;
  EXPECT_NEAR(solve(a, Eigen::Vector3d::Ones(), o).damping, .03, 1e-12);
  a(2, 2) = .1;
  EXPECT_EQ(solve(a, Eigen::Vector3d::Ones(), o).damping, 0);
}
TEST(Ik, InvalidInputs) {
  Eigen::MatrixXd a = Eigen::MatrixXd::Identity(3, 4);
  Eigen::VectorXd b = Eigen::VectorXd::Ones(3);
  EXPECT_THROW(solve(a, Eigen::VectorXd::Ones(2)), std::invalid_argument);
  EXPECT_THROW(pseudoInverse(Eigen::MatrixXd(0, 4), 1e-10), std::invalid_argument);
  a(0, 0) = std::numeric_limits<double>::quiet_NaN();
  EXPECT_THROW(solve(a, b), std::invalid_argument);
  a(0, 0) = 1;
  b[0] = std::numeric_limits<double>::infinity();
  EXPECT_THROW(solve(a, b), std::invalid_argument);
  b[0] = 1;
  for (double value : {-1., 1., std::numeric_limits<double>::infinity()})
    EXPECT_THROW(pseudoInverse(a, value), std::invalid_argument);
  Options o;
  o.damping = -.01;
  EXPECT_THROW(solve(a, b, o), std::invalid_argument);
  o.damping = std::numeric_limits<double>::quiet_NaN();
  EXPECT_THROW(solve(a, b, o), std::invalid_argument);
  o.damping = .01;
  o.adaptive_sigma_threshold = 0;
  EXPECT_THROW(solve(a, b, o), std::invalid_argument);
  o.adaptive_sigma_threshold = .05;
  o.method = static_cast<Method>(42);
  EXPECT_THROW(solve(a, b, o), std::invalid_argument);
}
TEST(Ik, GlobalScalingRequiresDampingScaling) {
  Eigen::MatrixXd a(3, 4);
  a << 1, 2, 0, 1, 0, 2, 1, 0, 1, 0, 3, 2;
  Eigen::Vector3d b(1, -2, .3);
  Options o;
  o.method = Method::FixedDls;
  o.damping = .03;
  auto first = solve(a, b, o);
  o.damping *= 10;
  EXPECT_LT((solve(10 * a, 10 * b, o).dq - first.dq).norm(), 1e-12);
}
TEST(Ik, OverflowIsAnExplicitFailure) {
  Eigen::Matrix3d a = .001 * Eigen::Matrix3d::Identity();
  Eigen::Vector3d b = Eigen::Vector3d::Constant(std::numeric_limits<double>::max());
  EXPECT_THROW(solve(a, b), std::overflow_error);
  EXPECT_THROW(pseudoInverse(1e-310 * Eigen::Matrix3d::Identity(), 1e-10), std::overflow_error);
}
