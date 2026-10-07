#include <gtest/gtest.h>

#include <Eigen/Cholesky>
#include <limits>
#include <predictive_motion_control/predictive.hpp>
using namespace predictive_motion::control;
namespace {
PreviewInput input(int n = 1, int N = 2) {
  PreviewInput in;
  in.initial = {Eigen::VectorXd::Zero(n), Eigen::VectorXd::Zero(n), 0, 0};
  in.mesh = std::vector<double>(N, .04);
  in.previous_acceleration = Eigen::VectorXd::Zero(n);
  in.previous_model_acceleration = in.previous_acceleration;
  in.accepted_position = in.initial.q;
  in.accepted_velocity = in.initial.v;
  in.nominal = Eigen::VectorXd::Zero(N * (n + 1));
  in.limits.lower = Eigen::VectorXd::Constant(n, -10);
  in.limits.upper = -in.limits.lower;
  in.limits.velocity = Eigen::VectorXd::Constant(n, 10);
  in.limits.acceleration = Eigen::VectorXd::Constant(n, 100);
  in.limits.jerk = Eigen::VectorXd::Constant(n, 1e6);
  in.limits.posture = Eigen::VectorXd::Zero(n);
  in.limits.progress_speed = 10;
  in.limits.progress_acceleration = 100;
  in.limits.progress_jerk = 1e6;
  in.limits.position_margin = 0;
  in.joint_trust = 10;
  in.progress_trust = 10;
  in.terminal_stop = false;
  return in;
}
std::vector<PreviewStage> stages(const PreviewInput& in, double target = 0) {
  auto xs = previewRollout(in.initial, in.mesh, in.nominal);
  std::vector<PreviewStage> out;
  for (auto& x : xs) {
    PreviewStage s;
    s.residual = x.q.array() - target;
    s.joint_derivative = Eigen::MatrixXd::Identity(x.q.size(), x.q.size());
    s.path_derivative = Eigen::VectorXd::Zero(x.q.size());
    out.push_back(s);
  }
  return out;
}
QpOptions tight() {
  QpOptions o;
  o.absolute_tolerance = 1e-10;
  o.relative_tolerance = 1e-10;
  o.acceptance_tolerance = 1e-8;
  o.time_limit_seconds = 1;
  o.max_state_age_seconds = 1;
  return o;
}
PreviewLinearizer linearizer(PreviewInput in, double target) {
  return [in, target](const std::vector<PreviewState>& xs) {
    auto out = stages(in, target);
    for (int i = 0; i < int(out.size()); ++i) out[i].residual = xs[i].q.array() - target;
    return out;
  };
}
ScpOptions scp() {
  ScpOptions o;
  o.qp = tight();
  o.wall_limit = 1;
  o.violation_tolerance = 1e-6;
  return o;
}
}  // namespace
TEST(Preview, ExactDynamicsAndNonuniformDurations) {
  auto in = input(3, 3);
  in.initial.q << 1, 2, 3;
  in.initial.v << .2, -.3, .4;
  in.initial.s = .3;
  in.initial.r = .1;
  in.mesh = {.01, .03, .06};
  Eigen::VectorXd u(12);
  u << 1, 2, 3, .2, -2, 1, -1, -.1, .2, .3, .4, .05;
  auto xs = previewRollout(in.initial, in.mesh, u);
  EXPECT_NEAR(xs[1].q(0), 1.00205, 1e-14);
  EXPECT_NEAR(xs[1].v(0), .21, 1e-14);
  EXPECT_NEAR(xs[1].s, .30101, 1e-14);
  EXPECT_NEAR(xs[1].r, .102, 1e-14);
  in.nominal = u;
  auto a = assemblePreview(in, stages(in));
  for (int k = 0; k < 4; ++k) {
    auto z = a.states[k].offset + a.states[k].map * u;
    EXPECT_LT((z.head(3) - xs[k].q).norm(), 1e-14);
    EXPECT_LT((z.segment(3, 3) - xs[k].v).norm(), 1e-14);
    EXPECT_NEAR(z(6), xs[k].s, 1e-14);
  }
}
TEST(Preview, IndependentRationalTwoStageCoupling) {
  auto in = input();
  in.mesh = {1, 1};
  in.weights = {.5, .5, .05, 0, 0, 0, 0};
  auto s = stages(in, 1);
  s[0].tracking_multiplier = s[1].tracking_multiplier = 0;
  s[0].velocity_multiplier = s[1].velocity_multiplier = 0;
  auto a = assemblePreview(in, s);
  EXPECT_NEAR(a.qp.hessian(0, 0), 3.35, 1e-13);
  EXPECT_NEAR(a.qp.hessian(0, 2), 1.75, 1e-13);
  EXPECT_NEAR(a.qp.hessian(2, 2), 1.35, 1e-13);
  EXPECT_NEAR(a.qp.gradient(0), -1.5, 1e-13);
  EXPECT_NEAR(a.qp.gradient(2), -.5, 1e-13);
  auto sol = solveQp(a.qp, tight());
  ASSERT_EQ(sol.status, QpStatus::Solved);
  EXPECT_NEAR(sol.velocity(0), 115. / 146, 1e-8);
  EXPECT_NEAR(sol.velocity(2), -95. / 146, 1e-8);
  EXPECT_GT(std::abs(sol.velocity(0) - 1.5 / 3.35), .3);
  auto xs = previewRollout(in.initial, in.mesh, sol.velocity);
  EXPECT_NEAR(xs.back().q(0), 125. / 146, 1e-8);
}
TEST(Preview, IndependentRationalJointProgressCoupling) {
  auto in = input(1, 1);
  in.mesh = {1};
  in.initial.r = .1;
  in.weights = {.5, 0, .05, 0, 0, .2, 0};
  auto s = stages(in);
  for (auto& v : s) {
    v.residual(0) = -in.initial.r;
    v.path_derivative(0) = -1;
  }
  s[0].residual(0) = 0;
  auto a = assemblePreview(in, s);
  EXPECT_NEAR(a.qp.hessian(0, 0), .35, 1e-13);
  EXPECT_NEAR(a.qp.hessian(0, 1), -.25, 1e-13);
  EXPECT_NEAR(a.qp.hessian(1, 1), .35, 1e-13);
  EXPECT_NEAR(a.qp.gradient(0), -.05, 1e-13);
  EXPECT_NEAR(a.qp.gradient(1), -.05, 1e-13);
  auto sol = solveQp(a.qp, tight());
  ASSERT_EQ(sol.status, QpStatus::Solved);
  EXPECT_NEAR(sol.velocity(0), .5, 1e-8);
  EXPECT_NEAR(sol.velocity(1), .5, 1e-8);
}
TEST(Preview, AllObjectiveTermsReconstructTotal) {
  auto in = input(2, 3);
  auto a = assemblePreview(in, stages(in, .2));
  Eigen::MatrixXd h = Eigen::MatrixXd::Zero(9, 9);
  Eigen::VectorXd g = Eigen::VectorXd::Zero(9);
  for (auto& t : a.terms) {
    h += t.hessian;
    g += t.gradient;
    EXPECT_TRUE(t.hessian.allFinite());
  }
  EXPECT_LT((h - a.qp.hessian).norm(), 1e-12);
  EXPECT_LT((g - a.qp.gradient).norm(), 1e-12);
  EXPECT_EQ(a.row_labels.size(), size_t(a.qp.lower.size()));
}
TEST(Preview, EndpointSafeInteriorUnsafeIsRejected) {
  auto in = input(1, 1);
  in.mesh = {1};
  in.initial.q(0) = .9;
  in.initial.v(0) = 2;
  in.accepted_position = in.initial.q;
  in.accepted_velocity = in.initial.v;
  in.limits.upper(0) = 1;
  Eigen::VectorXd u(2);
  u << -4, 0;
  auto xs = previewRollout(in.initial, in.mesh, u);
  EXPECT_NEAR(xs.back().q(0), .9, 1e-13);
  EXPECT_NEAR(previewLimitViolation(in, u), .4, 1e-12);
  in.nominal = u;
  auto a = assemblePreview(in, stages(in));
  auto ax = a.qp.constraints * u;
  EXPECT_GT((ax - a.qp.upper).maxCoeff(), .4);
}
TEST(Preview, FractionalShiftPreservesVelocityNotPositionMoment) {
  Eigen::VectorXd old(4);
  old << 1, 0, -1, 0;
  auto shifted = shiftPreview({.04, .04}, old, {.04, .04}, 1, .004);
  ASSERT_FALSE(shifted.reset);
  EXPECT_NEAR(shifted.controls(0), .8, 1e-14);
  EXPECT_NEAR(shifted.controls(2), -.9, 1e-14);
  PreviewState x{Eigen::VectorXd::Constant(1, .1), Eigen::VectorXd::Constant(1, .2), 0, 0};
  Eigen::VectorXd u(2);
  u << 1, 0;
  auto measured = previewAdvance(x, u, .004);
  auto reconstructed = previewRollout(measured, {.04, .04}, shifted.controls);
  EXPECT_NEAR(reconstructed[1].v(0), .236, 1e-14);
  EXPECT_NEAR(.109752 - reconstructed[1].q(0), .000144, 1e-14);
}
TEST(Preview, WarmResetOnExpiredInvalidChangedDimensions) {
  Eigen::VectorXd old = Eigen::VectorXd::Zero(4);
  EXPECT_TRUE(shiftPreview({.04, .04}, old, {.04, .04}, 1, .08).reset);
  EXPECT_TRUE(shiftPreview({.04, .04}, old, {.04, .04}, 2, .004).reset);
  old(0) = NAN;
  EXPECT_TRUE(shiftPreview({.04, .04}, old, {.04, .04}, 1, .004).reset);
  EXPECT_TRUE(shiftPreview({-.04, .04}, old, {.04, .04}, 1, .004).reset);
}
TEST(Preview, MeasuredVelocityNeverSilentlyReplacesCommandHistory) {
  auto in = input(1, 1);
  in.initial.v(0) = .1;
  in.accepted_velocity(0) = .15;
  in.limits.acceleration(0) = 1;
  in.limits.jerk(0) = 20;
  Eigen::VectorXd u(2);
  u << .5, 0;
  EXPECT_GT(previewLimitViolation(in, u), 2900);
  auto a = assemblePreview(in, stages(in));
  auto ax = a.qp.constraints * u;
  EXPECT_GT((a.qp.lower - ax).maxCoeff(), .04);
  auto sol = solveQp(a.qp, tight());
  EXPECT_EQ(sol.status, QpStatus::PrimalInfeasible);
  EXPECT_EQ(sol.velocity.size(), 0);
}
TEST(Preview, FirstJerkUsesControlIntervalLaterUsesMesh) {
  auto in = input();
  in.control_dt = .004;
  in.mesh = {.04, .06};
  in.limits.jerk(0) = 20;
  Eigen::VectorXd u(4);
  u << .08, 0, .88, 0;
  EXPECT_LE(previewLimitViolation(in, u), 1e-12);
  u(0) = .081;
  EXPECT_GT(previewLimitViolation(in, u), .249);
  u << .08, 0, .89, 0;
  EXPECT_GT(previewLimitViolation(in, u), .249);
}
TEST(Preview, ProgressMonotoneAndTerminalNoDivisionAtZeroSpeed) {
  auto in = input(1, 1);
  in.initial.s = 1;
  in.terminal_stop = true;
  auto a = assemblePreview(in, stages(in));
  auto sol = solveQp(a.qp, tight());
  ASSERT_EQ(sol.status, QpStatus::Solved);
  EXPECT_LT(sol.velocity.norm(), 1e-8);
  auto xs = previewRollout(in.initial, in.mesh, sol.velocity);
  EXPECT_NEAR(xs.back().s, 1, 1e-10);
  EXPECT_NEAR(xs.back().r, 0, 1e-10);
  Eigen::VectorXd negative(2);
  negative << 0, -.1;
  EXPECT_GT(previewLimitViolation(in, negative), 0);
}
TEST(Preview, FutureScalarConstraintCouplesEarlyAction) {
  auto in = input(1, 2);
  in.mesh = {.5, .5};
  in.initial.v(0) = .4;
  in.accepted_velocity = in.initial.v;
  in.weights = {1, 0, .01, 0, 0, 0, 0};
  auto s = stages(in, 1);
  auto nominal_states = previewRollout(in.initial, in.mesh, in.nominal);
  int k = 0;
  for (auto& stage : s) {
    PreviewScalar c;
    c.value = .5 - nominal_states[k++].q(0);
    c.minimum = .1;
    c.gradient = Eigen::RowVectorXd::Constant(1, -1);
    stage.scalars.push_back(c);
  }
  auto a = assemblePreview(in, s);
  auto sol = solveQp(a.qp, tight());
  ASSERT_EQ(sol.status, QpStatus::Solved);
  auto xs = previewRollout(in.initial, in.mesh, sol.velocity);
  EXPECT_LT(xs.back().q(0), .401);
  EXPECT_LT(sol.velocity(0), .5);
  EXPECT_GT(.5 - in.initial.q(0), .1);
}
TEST(Preview, NonlinearRejectShrinksAndReturnsNoUsableCommand) {
  auto in = input();
  auto o = scp();
  o.max_iterations = 3;
  auto r = solvePreview(in, linearizer(in, .1), [](const auto&, const auto&) { return .001; }, o);
  EXPECT_EQ(r.status, QpStatus::ConstraintViolation);
  ASSERT_EQ(r.iterations.size(), 3u);
  EXPECT_NEAR(r.iterations[1].trust, in.joint_trust * .5, 1e-12);
  EXPECT_NEAR(r.iterations[2].trust, in.joint_trust * .25, 1e-12);
  EXPECT_EQ(r.controls.size(), 0);
}
TEST(Preview, SolvedSCPExposesFullRollout) {
  auto in = input(3, 3);
  auto r =
      solvePreview(in, linearizer(in, .01), [](const auto&, const auto&) { return 0.; }, scp());
  ASSERT_EQ(r.status, QpStatus::Solved);
  EXPECT_EQ(r.controls.size(), 12);
  EXPECT_EQ(r.states.size(), 4u);
  EXPECT_LE(previewLimitViolation(in, r.controls), 1e-6);
}
TEST(Preview, InvalidDerivedOverflowFiniteInput) {
  auto in = input();
  in.mesh = {1e200, 1e200};
  EXPECT_THROW(assemblePreview(in, stages(in)), std::exception);
  in = input();
  in.limits.lower(0) = -1e308;
  in.initial.q(0) = 1e308;
  in.accepted_position = in.initial.q;
  EXPECT_THROW(assemblePreview(in, stages(in)), std::exception);
}
TEST(Preview, NonfiniteLinearizationOrValidationFailsClosed) {
  auto in = input();
  auto s = stages(in);
  s[1].joint_derivative(0, 0) = NAN;
  EXPECT_THROW(assemblePreview(in, s), std::invalid_argument);
  auto r = solvePreview(in, linearizer(in, 0), [](const auto&, const auto&) { return NAN; }, scp());
  EXPECT_EQ(r.status, QpStatus::InvalidInput);
  EXPECT_EQ(r.controls.size(), 0);
}
TEST(Preview, StaleStateAndWallDeadlineHaveNoCommand) {
  auto in = input();
  in.state_age = 2;
  auto r = solvePreview(in, linearizer(in, .1), [](const auto&, const auto&) { return 0.; }, scp());
  EXPECT_EQ(r.status, QpStatus::StaleState);
  EXPECT_EQ(r.controls.size(), 0);
  in.state_age = 0;
  auto o = scp();
  o.wall_limit = 1e-12;
  r = solvePreview(in, linearizer(in, .1), [](const auto&, const auto&) { return 0.; }, o);
  EXPECT_EQ(r.status, QpStatus::TimeLimit);
  EXPECT_EQ(r.controls.size(), 0);
}
TEST(Preview, PrimalSeedValidationAndFreshDualReset) {
  auto in = input();
  auto a = assemblePreview(in, stages(in, .1));
  auto first = solveQpWarm(a.qp, tight(), in.nominal);
  ASSERT_EQ(first.status, QpStatus::Solved);
  auto second = solveQpWarm(a.qp, tight(), first.velocity);
  ASSERT_EQ(second.status, QpStatus::Solved);
  EXPECT_LT((first.velocity - second.velocity).norm(), 1e-6);
  Eigen::VectorXd bad = first.velocity;
  bad(0) = NAN;
  EXPECT_EQ(solveQpWarm(a.qp, tight(), bad).status, QpStatus::InvalidInput);
  bad.resize(1);
  EXPECT_EQ(solveQpWarm(a.qp, tight(), bad).status, QpStatus::InvalidInput);
  a.qp.lower(0) = 2;
  a.qp.upper(0) = 1;
  auto failure = solveQpWarm(a.qp, tight(), first.velocity);
  EXPECT_EQ(failure.status, QpStatus::InfeasibleBounds);
  EXPECT_EQ(failure.velocity.size(), 0);
}
TEST(Preview, OptionalFutureSingularityPenaltyChangesEarlyInput) {
  auto in = input();
  in.mesh = {.5, .5};
  in.weights = {0, 0, .01, 0, 0, 0, 0};
  auto s = stages(in);
  PreviewPenalty penalty;
  penalty.value = .01;
  penalty.target = .02;
  penalty.weight = 100;
  penalty.gradient = Eigen::RowVectorXd::Ones(1);
  s.back().penalties.push_back(penalty);
  auto a = assemblePreview(in, s);
  auto r = solveQp(a.qp, tight());
  ASSERT_EQ(r.status, QpStatus::Solved);
  EXPECT_GT(r.velocity(0), .02);
  EXPECT_GT(previewRollout(in.initial, in.mesh, r.velocity).back().q(0), .009);
}
TEST(Preview, ActualSolverLimitsRemainDistinctFromNonlinearRejection) {
  auto in = input(3, 20);
  auto a = assemblePreview(in, stages(in, 1));
  auto o = tight();
  o.max_iterations = 1;
  auto r = solveQpWarm(a.qp, o, in.nominal);
  EXPECT_EQ(r.status, QpStatus::IterationLimit);
  EXPECT_EQ(r.velocity.size(), 0);
  o = tight();
  o.time_limit_seconds = 1e-12;
  r = solveQpWarm(a.qp, o, in.nominal);
  EXPECT_EQ(r.status, QpStatus::TimeLimit);
  EXPECT_EQ(r.velocity.size(), 0);
}
TEST(Preview, TrueNonlinearRejectCanRecoverAfterTrustShrink) {
  auto in = input();
  int validations = 0;
  auto r = solvePreview(
      in, linearizer(in, .01),
      [&](const auto&, const auto&) { return ++validations == 1 ? .001 : 0.; }, scp());
  ASSERT_EQ(r.status, QpStatus::Solved);
  ASSERT_GE(r.iterations.size(), 2u);
  EXPECT_NEAR(r.iterations[1].trust, .5 * in.joint_trust, 1e-12);
  EXPECT_GT(r.controls.size(), 0);
}
TEST(Preview, DistinctModelAndCommandAccelerationHistoriesRemainFeasible) {
  auto in = input();
  in.initial.v(0) = .1;
  in.accepted_velocity(0) = .1008;
  in.previous_model_acceleration(0) = .5;
  in.previous_acceleration(0) = .3;
  in.limits.acceleration(0) = 1;
  in.limits.jerk(0) = 20;
  Eigen::VectorXd u(4);
  u << .5, 0, .5, 0;
  EXPECT_LE(previewLimitViolation(in, u), 1e-10);
  auto a = assemblePreview(in, stages(in));
  auto sol = solveQp(a.qp, tight());
  ASSERT_EQ(sol.status, QpStatus::Solved);
  EXPECT_LE(previewLimitViolation(in, sol.velocity), 1e-6);
  in.previous_model_acceleration = in.previous_acceleration;
  EXPECT_GT(previewLimitViolation(in, u), 29.9);
}
TEST(Preview, CommandProjectionChecksDerivativesInActualUnits) {
  CommandLimits l;
  l.dt = .004;
  l.position_margin = 0;
  l.position_lower = Eigen::VectorXd::Constant(3, -1);
  l.position_upper = -l.position_lower;
  l.velocity = Eigen::VectorXd::Ones(3);
  l.acceleration = Eigen::VectorXd::Ones(3);
  l.jerk = Eigen::VectorXd::Constant(3, 20);
  CommandHistory h{Eigen::VectorXd::Zero(3), Eigen::VectorXd::Zero(3), Eigen::VectorXd::Zero(3),
                   Eigen::VectorXd::Zero(3)};
  auto p = constrainPreviewCommand(
      trackingProblem(Eigen::MatrixXd::Identity(3, 3), Eigen::VectorXd::Constant(3, .00032), 0), l,
      h);
  auto result = solveQp(p, tight());
  ASSERT_EQ(result.status, QpStatus::Solved);
  EXPECT_LE((result.velocity / l.dt / l.dt).maxCoeff(), 20 + 1e-8);
  Eigen::VectorXd slightly = Eigen::VectorXd::Constant(3, .00032 + 1e-8);
  auto av = p.constraints * slightly;
  EXPECT_GT((av - p.upper).maxCoeff(), .000624);
}
TEST(Preview, LiftedAndCondensedCoupledOptimaAreEquivalent) {
  auto in = input();
  in.mesh = {1, 1};
  in.weights = {.5, .5, .05, 0, 0, 0, 0};
  auto s = stages(in, 1);
  s[0].tracking_multiplier = s[1].tracking_multiplier = 0;
  s[0].velocity_multiplier = s[1].velocity_multiplier = 0;
  auto condensed = assemblePreview(in, s);
  auto c =
      solveQpCertified(condensed.qp, tight(), condensed.nominal_decision, condensed.convex_factor);
  ASSERT_EQ(c.status, QpStatus::Solved);
  in.lifted = true;
  auto lifted = assemblePreview(in, s);
  auto l = solveQpCertified(lifted.qp, tight(), lifted.nominal_decision, lifted.convex_factor);
  ASSERT_EQ(l.status, QpStatus::Solved);
  EXPECT_EQ(l.velocity.size(), 16);
  EXPECT_LT((l.velocity.tail(4) - c.velocity).norm(), 1e-7);
  auto x = previewRollout(in.initial, in.mesh, l.velocity.tail(4));
  for (int k = 0; k < 3; ++k) {
    EXPECT_NEAR(l.velocity(k * 4), x[k].q(0), 1e-8);
    EXPECT_NEAR(l.velocity(k * 4 + 1), x[k].v(0), 1e-8);
  }
}
TEST(Preview, LiftedDynamicsAndAllCostsMatchExactCondensation) {
  auto in = input(3, 5);
  in.mesh = {.02, .04, .06, .03, .05};
  in.initial.q << .1, -.2, .3;
  in.initial.v << .01, -.02, .03;
  in.initial.s = .2;
  in.initial.r = .04;
  in.accepted_position = in.initial.q;
  in.accepted_velocity = in.initial.v;
  auto s = stages(in, .3);
  auto c = assemblePreview(in, s);
  Eigen::VectorXd u = Eigen::VectorXd::LinSpaced(20, -.02, .02);
  auto x = previewRollout(in.initial, in.mesh, u);
  in.lifted = true;
  in.capture_dense_terms = false;
  auto l = assemblePreview(in, s);
  Eigen::VectorXd z(l.qp.gradient.size());
  for (int k = 0; k < 6; ++k) z.segment(k * 8, 8) << x[k].q, x[k].v, x[k].s, x[k].r;
  z.tail(20) = u;
  z -= l.decision_offset;
  double cvalue = .5 * u.dot(c.qp.hessian * u) + c.qp.gradient.dot(u),
         lvalue = .5 * z.dot(l.qp.hessian * z) + l.qp.gradient.dot(z);
  for (const auto& t : c.terms) cvalue += t.constant;
  for (const auto& t : l.terms) lvalue += t.constant;
  EXPECT_NEAR(cvalue, lvalue, 1e-11);
  Eigen::VectorXd az = l.qp.constraints * z;
  for (int i = 0; i < int(l.row_labels.size()); ++i)
    if (l.row_labels[i].rfind("dynamics/", 0) == 0) {
      EXPECT_NEAR(az(i), l.qp.lower(i), 1e-14);
      EXPECT_NEAR(az(i), l.qp.upper(i), 1e-14);
    }
}
TEST(Preview, LiftedHorizonRetainsSparseStageStructure) {
  auto in = input(7, 20);
  auto s = stages(in, .01);
  auto c = assemblePreview(in, s);
  in.lifted = true;
  in.capture_dense_terms = false;
  auto l = assemblePreview(in, s);
  EXPECT_EQ(l.qp.gradient.size(), 496);
  EXPECT_EQ(l.controls_offset, 336);
  EXPECT_LT((l.qp.constraints.array() != 0).count(), (c.qp.constraints.array() != 0).count());
  EXPECT_LT((l.qp.hessian.array() != 0).count(), (c.qp.hessian.array() != 0).count());
  Eigen::MatrixXd certified(l.convex_factor.transpose() * l.convex_factor);
  EXPECT_LT((l.qp.hessian - certified).norm(), 1e-12);
}
TEST(Preview, WrongConvexityCertificateFailsClosed) {
  auto in = input();
  auto a = assemblePreview(in, stages(in, .1));
  Eigen::SparseMatrix<double> wrong(0, a.qp.gradient.size());
  auto r = solveQpCertified(a.qp, tight(), in.nominal, wrong);
  EXPECT_EQ(r.status, QpStatus::InvalidInput);
  EXPECT_EQ(r.velocity.size(), 0);
}
TEST(Preview, LiftedSCPReturnsFullDecisionAndExactReconstructedRollout) {
  auto in = input(3, 4);
  in.lifted = true;
  in.capture_dense_terms = false;
  auto r =
      solvePreview(in, linearizer(in, .01), [](const auto&, const auto&) { return 0.; }, scp());
  ASSERT_EQ(r.status, QpStatus::Solved);
  EXPECT_EQ(r.controls.size(), 16);
  EXPECT_EQ(r.decision.size(), 56);
  EXPECT_EQ(r.states.size(), 5u);
  EXPECT_LT((r.controls - (r.decision + r.decision_offset).tail(16)).norm(), 1e-12);
}

TEST(Preview, ProgressStopRejectsAnEmptySpeedJerkIntersection) {
  auto in = input();
  in.limits.progress_speed = .2;
  in.limits.progress_acceleration = .5;
  in.limits.progress_jerk = 5;
  auto stop = progressStopBounds(.5, .199, .5, .004, in.limits);
  EXPECT_FALSE(stop.feasible);
  EXPECT_NEAR(stop.lower, .48, 1e-14);
  EXPECT_LT(stop.upper, .25);
  stop = progressStopBounds(1, 0, 0, .004, in.limits);
  ASSERT_TRUE(stop.feasible);
  EXPECT_NEAR(stop.acceleration, 0, 1e-14);
}
TEST(Preview, NonzeroNominalCenteringPreservesAllCostsAndInequalities) {
  auto in = input(3, 5);
  in.mesh = {.02, .04, .06, .03, .05};
  in.initial.q << .1, -.2, .3;
  in.initial.v << .01, -.02, .03;
  in.initial.s = .2;
  in.initial.r = .04;
  in.accepted_position = in.initial.q;
  in.accepted_velocity = in.initial.v;
  in.nominal = Eigen::VectorXd::LinSpaced(20, -.03, .03);
  auto s = stages(in, .3);
  auto c = assemblePreview(in, s);
  Eigen::VectorXd u = Eigen::VectorXd::LinSpaced(20, -.02, .02);
  auto x = previewRollout(in.initial, in.mesh, u);
  in.lifted = true;
  in.capture_dense_terms = false;
  auto l = assemblePreview(in, s);
  Eigen::VectorXd z(l.qp.gradient.size());
  for (int k = 0; k < 6; ++k) z.segment(k * 8, 8) << x[k].q, x[k].v, x[k].s, x[k].r;
  z.tail(20) = u;
  z -= l.decision_offset;
  double cv = .5 * u.dot(c.qp.hessian * u) + c.qp.gradient.dot(u),
         lv = .5 * z.dot(l.qp.hessian * z) + l.qp.gradient.dot(z);
  for (auto& t : c.terms) cv += t.constant;
  for (auto& t : l.terms) lv += t.constant;
  EXPECT_NEAR(cv, lv, 1e-11);
  Eigen::VectorXd ca = c.qp.constraints * u, la = l.qp.constraints * z;
  int offset = 48;
  ASSERT_EQ(la.size(), ca.size() + offset);
  for (int i = 0; i < ca.size(); ++i) {
    if (std::isfinite(c.qp.lower(i))) {
      EXPECT_NEAR(ca(i) - c.qp.lower(i), la(i + offset) - l.qp.lower(i + offset), 1e-9);
    }
    if (std::isfinite(c.qp.upper(i))) {
      EXPECT_NEAR(c.qp.upper(i) - ca(i), l.qp.upper(i + offset) - la(i + offset), 1e-9);
    }
  }
}
TEST(Preview, ConvexityCertificateResidualCannotAmplifyWithDimension) {
  for (int n : {128, 496}) {
    QpProblem p;
    p.hessian = Eigen::MatrixXd::Constant(n, n, -9e-13);
    p.gradient = Eigen::VectorXd::Zero(n);
    p.constraints = Eigen::MatrixXd::Identity(n, n);
    p.lower = Eigen::VectorXd::Constant(n, -1);
    p.upper = -p.lower;
    Eigen::SparseMatrix<double> wrong(1, n);
    auto r = solveQpCertified(p, tight(), Eigen::VectorXd::Zero(n), wrong);
    EXPECT_EQ(r.status, QpStatus::InvalidInput);
    EXPECT_EQ(r.velocity.size(), 0);
  }
}
TEST(Preview, ValidSemidefiniteGramCertificateIsAccepted) {
  QpProblem p;
  p.hessian = Eigen::MatrixXd::Zero(3, 3);
  p.hessian(0, 0) = 1;
  p.gradient = Eigen::VectorXd::Zero(3);
  p.gradient(0) = -.25;
  p.constraints = Eigen::MatrixXd::Identity(3, 3);
  p.lower = Eigen::VectorXd::Constant(3, -1);
  p.upper = -p.lower;
  Eigen::SparseMatrix<double> factor(1, 3);
  factor.insert(0, 0) = 1;
  auto r = solveQpCertified(p, tight(), Eigen::VectorXd::Zero(3), factor);
  ASSERT_EQ(r.status, QpStatus::Solved);
  EXPECT_NEAR(r.velocity(0), .25, 1e-8);
  EXPECT_NEAR(r.velocity(1), 0, 1e-8);
  EXPECT_NEAR(r.velocity(2), 0, 1e-8);
}
TEST(Preview, WorkspaceReusesAndUpdatesMatricesWithoutChangingOptimum) {
  auto p = trackingProblem(Eigen::MatrixXd::Identity(2, 2), Eigen::VectorXd::Constant(2, 2), 0);
  p.constraints = Eigen::MatrixXd::Identity(2, 2);
  p.lower = Eigen::VectorXd::Zero(2);
  p.upper = Eigen::VectorXd::Ones(2);
  Eigen::SparseMatrix<double> factor(2, 2);
  factor.setIdentity();
  QpWorkspace ws;
  auto r = solveQpWorkspace(p, tight(), Eigen::VectorXd::Zero(2), factor, ws, {"a", "b"});
  ASSERT_EQ(r.status, QpStatus::Solved);
  EXPECT_FALSE(r.workspace_reused);
  p.gradient = Eigen::VectorXd::Constant(2, -3);
  auto next = solveQpWorkspace(p, tight(), r.velocity, factor, ws, {"a", "b"});
  ASSERT_EQ(next.status, QpStatus::Solved);
  EXPECT_TRUE(next.workspace_reused);
  EXPECT_TRUE(next.dual_reused);
  EXPECT_FALSE(next.matrix_updated);
  EXPECT_LT((next.velocity - Eigen::VectorXd::Ones(2)).norm(), 1e-8);
  p.constraints *= 2;
  p.hessian *= 2;
  factor *= std::sqrt(2.);
  next = solveQpWorkspace(p, tight(), next.velocity, factor, ws, {"a", "b"});
  ASSERT_EQ(next.status, QpStatus::Solved);
  EXPECT_TRUE(next.workspace_reused);
  EXPECT_TRUE(next.matrix_updated);
  EXPECT_LT((next.velocity - Eigen::VectorXd::Constant(2, .5)).norm(), 1e-8);
}
TEST(Preview, WorkspaceResetsFailuresAndFeedbackDualsExplicitly) {
  auto p = trackingProblem(Eigen::MatrixXd::Identity(2, 2), Eigen::VectorXd::Constant(2, 2), 0);
  p.constraints = Eigen::MatrixXd::Identity(2, 2);
  p.lower = Eigen::VectorXd::Zero(2);
  p.upper = Eigen::VectorXd::Ones(2);
  Eigen::SparseMatrix<double> factor(2, 2);
  factor.setIdentity();
  QpWorkspace ws;
  auto r = solveQpWorkspace(p, tight(), Eigen::VectorXd::Zero(2), factor, ws, {"a", "b"});
  ASSERT_EQ(r.status, QpStatus::Solved);
  ws.clearDual();
  r = solveQpWorkspace(p, tight(), r.velocity, factor, ws, {"a", "b"});
  ASSERT_EQ(r.status, QpStatus::Solved);
  EXPECT_TRUE(r.workspace_reused);
  EXPECT_FALSE(r.dual_reused);
  p.state_age_seconds = 2;
  r = solveQpWorkspace(p, tight(), r.velocity, factor, ws, {"a", "b"});
  EXPECT_EQ(r.status, QpStatus::StaleState);
  EXPECT_EQ(r.velocity.size(), 0);
  p.state_age_seconds = 0;
  r = solveQpWorkspace(p, tight(), Eigen::VectorXd::Zero(2), factor, ws, {"a", "b"});
  ASSERT_EQ(r.status, QpStatus::Solved);
  EXPECT_FALSE(r.workspace_reused);
  EXPECT_FALSE(r.dual_reused);
}
TEST(Preview, WorkspaceSemanticRowsControlDualMapping) {
  auto p = trackingProblem(Eigen::MatrixXd::Identity(2, 2), Eigen::VectorXd::Constant(2, 2), 0);
  p.constraints = Eigen::MatrixXd::Identity(2, 2);
  p.lower = Eigen::VectorXd::Zero(2);
  p.upper = Eigen::VectorXd::Ones(2);
  Eigen::SparseMatrix<double> factor(2, 2);
  factor.setIdentity();
  QpWorkspace ws;
  auto r = solveQpWorkspace(p, tight(), Eigen::VectorXd::Zero(2), factor, ws, {"a", "b"});
  ASSERT_EQ(r.status, QpStatus::Solved);
  r = solveQpWorkspace(p, tight(), r.velocity, factor, ws, {"new_a", "new_b"});
  ASSERT_EQ(r.status, QpStatus::Solved);
  EXPECT_TRUE(r.workspace_reused);
  EXPECT_FALSE(r.dual_reused);
  r = solveQpWorkspace(p, tight(), r.velocity, factor, ws, {"duplicate", "duplicate"});
  EXPECT_EQ(r.status, QpStatus::InvalidInput);
  EXPECT_EQ(r.velocity.size(), 0);
}

TEST(Preview, WorkspaceRowScalingPreservesOriginalUnitsAndOptimum) {
  QpProblem p;
  p.hessian = Eigen::MatrixXd::Identity(2, 2);
  p.gradient = Eigen::VectorXd::Constant(2, -2);
  p.constraints = Eigen::MatrixXd::Zero(2, 2);
  p.constraints(0, 0) = 250;
  p.constraints(1, 1) = .004;
  p.lower = Eigen::VectorXd::Zero(2);
  p.upper.resize(2);
  p.upper << 20, .004;
  Eigen::SparseMatrix<double> factor(2, 2);
  factor.setIdentity();
  QpWorkspace ws;
  auto r = solveQpWorkspace(p, tight(), Eigen::VectorXd::Zero(2), factor, ws,
                            {"jerk_units", "velocity_units"});
  ASSERT_EQ(r.status, QpStatus::Solved);
  EXPECT_NEAR(r.velocity(0), .08, 1e-8);
  EXPECT_NEAR(r.velocity(1), 1, 1e-8);
  EXPECT_LE((p.constraints * r.velocity - p.upper).maxCoeff(), tight().acceptance_tolerance);
  EXPECT_NEAR(r.minimum_row_scale, .004, 1e-14);
  EXPECT_NEAR(r.maximum_row_scale, 250, 1e-12);
}
TEST(Preview, WorkspaceNoRowsAndZeroRowsRemainWellDefined) {
  auto p = trackingProblem(Eigen::MatrixXd::Identity(2, 2), Eigen::VectorXd::Constant(2, .25), 0);
  Eigen::SparseMatrix<double> factor(2, 2);
  factor.setIdentity();
  QpWorkspace ws;
  auto r = solveQpWorkspace(p, tight(), Eigen::VectorXd::Zero(2), factor, ws, {});
  ASSERT_EQ(r.status, QpStatus::Solved);
  EXPECT_LT((r.velocity - Eigen::VectorXd::Constant(2, .25)).norm(), 1e-8);
  p.constraints = Eigen::MatrixXd::Zero(1, 2);
  p.lower = Eigen::VectorXd::Constant(1, -1);
  p.upper = Eigen::VectorXd::Constant(1, 1);
  r = solveQpWorkspace(p, tight(), r.velocity, factor, ws, {"constant"});
  ASSERT_EQ(r.status, QpStatus::Solved);
  p.lower(0) = .1;
  r = solveQpWorkspace(p, tight(), r.velocity, factor, ws, {"constant"});
  EXPECT_EQ(r.status, QpStatus::PrimalInfeasible);
  EXPECT_EQ(r.velocity.size(), 0);
}
TEST(Preview, ExtremeRowNormalizationFailsWithoutIssuingACandidate) {
  auto p = trackingProblem(Eigen::MatrixXd::Identity(1, 1), Eigen::VectorXd::Zero(1), 0);
  p.constraints = Eigen::MatrixXd::Constant(1, 1, 1e-310);
  p.lower = Eigen::VectorXd::Constant(1, -1);
  p.upper = -p.lower;
  Eigen::SparseMatrix<double> factor(1, 1);
  factor.setIdentity();
  QpWorkspace ws;
  auto r = solveQpWorkspace(p, tight(), Eigen::VectorXd::Zero(1), factor, ws, {"tiny"});
  EXPECT_EQ(r.status, QpStatus::InvalidInput);
  EXPECT_EQ(r.velocity.size(), 0);
  p.constraints(0, 0) = 1e-20;
  p.lower(0) = -1e20;
  p.upper(0) = 1e20;
  r = solveQpWorkspace(p, tight(), Eigen::VectorXd::Zero(1), factor, ws, {"scaled_bound_overflow"});
  EXPECT_EQ(r.status, QpStatus::InvalidInput);
  EXPECT_EQ(r.velocity.size(), 0);
  p.lower(0) = -1;
  p.upper(0) = 1;
  r = solveQpWorkspace(p, tight(), Eigen::VectorXd::Zero(1), factor, ws, {"tiny_but_finite"});
  ASSERT_EQ(r.status, QpStatus::Solved);
  EXPECT_NEAR(r.velocity(0), 0, 1e-12);
}
TEST(Preview, VariableScaleReturnsOriginalCoordinatesAndChecksOriginalRows) {
  QpProblem p;
  p.hessian = Eigen::MatrixXd::Identity(2, 2);
  p.gradient = Eigen::VectorXd::Constant(2, -2);
  p.constraints = Eigen::MatrixXd::Zero(2, 2);
  p.constraints(0, 0) = 250;
  p.constraints(1, 1) = .004;
  p.lower = Eigen::VectorXd::Zero(2);
  p.upper.resize(2);
  p.upper << 20, .004;
  Eigen::SparseMatrix<double> factor(2, 2);
  factor.setIdentity();
  Eigen::VectorXd d(2);
  d << .02, .5;
  QpWorkspace ws;
  auto r = solveQpScaledWorkspace(p, tight(), Eigen::VectorXd::Zero(2), factor, d, ws,
                                  {"jerk", "velocity"});
  ASSERT_EQ(r.status, QpStatus::Solved);
  EXPECT_NEAR(r.velocity(0), .08, 1e-8);
  EXPECT_NEAR(r.velocity(1), 1, 1e-8);
  EXPECT_LE((p.constraints * r.velocity - p.upper).maxCoeff(), tight().acceptance_tolerance);
  r = solveQpScaledWorkspace(p, tight(), r.velocity, factor, d, ws, {"jerk", "velocity"});
  ASSERT_EQ(r.status, QpStatus::Solved);
  EXPECT_TRUE(r.workspace_reused);
  d(0) = .1;
  r = solveQpScaledWorkspace(p, tight(), r.velocity, factor, d, ws, {"jerk", "velocity"});
  ASSERT_EQ(r.status, QpStatus::Solved);
  EXPECT_FALSE(r.workspace_reused);
}
TEST(Preview, VariableScaleDefaultsAndInvalidDerivedProductsFailClosed) {
  auto p = trackingProblem(Eigen::MatrixXd::Identity(2, 2), Eigen::VectorXd::Constant(2, .25), 0);
  Eigen::SparseMatrix<double> factor(2, 2);
  factor.setIdentity();
  QpWorkspace ws;
  auto r = solveQpScaledWorkspace(p, tight(), Eigen::VectorXd::Zero(2), factor, Eigen::VectorXd{},
                                  ws, {});
  ASSERT_EQ(r.status, QpStatus::Solved);
  EXPECT_LT((r.velocity - Eigen::VectorXd::Constant(2, .25)).norm(), 1e-8);
  for (double value : {0., -1., std::numeric_limits<double>::quiet_NaN(), 1e308}) {
    Eigen::VectorXd d = Eigen::VectorXd::Constant(2, value);
    r = solveQpScaledWorkspace(p, tight(), Eigen::VectorXd::Ones(2), factor, d, ws, {});
    EXPECT_EQ(r.status, QpStatus::InvalidInput);
    EXPECT_EQ(r.velocity.size(), 0);
  }
}
TEST(Preview, VariableScaleCannotHideAnInvalidOriginalCertificate) {
  QpProblem p;
  p.hessian = -1e-10 * Eigen::MatrixXd::Identity(2, 2);
  p.gradient = Eigen::VectorXd::Zero(2);
  p.constraints = Eigen::MatrixXd::Identity(2, 2);
  p.lower = Eigen::VectorXd::Constant(2, -1);
  p.upper = -p.lower;
  Eigen::SparseMatrix<double> factor(1, 2);
  QpWorkspace ws;
  auto r = solveQpScaledWorkspace(p, tight(), Eigen::VectorXd::Zero(2), factor,
                                  Eigen::VectorXd::Constant(2, 1e-8), ws, {"a", "b"});
  EXPECT_EQ(r.status, QpStatus::InvalidInput);
  EXPECT_EQ(r.velocity.size(), 0);
}
TEST(Preview, ExactModelConsistencyTerminatesOnlyAfterTrueFeasibility) {
  auto in = input(3, 4);
  auto r = solvePreview(
      in, linearizer(in, .01), [](const auto&, const auto&) { return 0.; }, scp(), nullptr,
      [](const auto&, const auto&, const auto&) { return 0.; });
  ASSERT_EQ(r.status, QpStatus::Solved);
  ASSERT_EQ(r.iterations.size(), 1u);
  EXPECT_TRUE(r.iterations[0].validation_checked);
  EXPECT_TRUE(r.iterations[0].consistency_checked);
  EXPECT_EQ(r.termination_reason, "MODEL_CONSISTENT_FEASIBLE_ITERATE");
  EXPECT_GT(r.iterations[0].step, scp().step_tolerance);
  r = solvePreview(
      in, linearizer(in, .01), [](const auto&, const auto&) { return .001; }, scp(), nullptr,
      [](const auto&, const auto&, const auto&) { return 0.; });
  EXPECT_EQ(r.status, QpStatus::ConstraintViolation);
  EXPECT_EQ(r.controls.size(), 0);
}
TEST(Preview, InvalidConsistencyAuditReturnsNoUsableControls) {
  auto in = input();
  auto r = solvePreview(
      in, linearizer(in, .01), [](const auto&, const auto&) { return 0.; }, scp(), nullptr,
      [](const auto&, const auto&, const auto&) { return double(NAN); });
  EXPECT_EQ(r.status, QpStatus::InvalidInput);
  EXPECT_EQ(r.controls.size(), 0);
}

TEST(Preview, ProgressStopPreservesFiniteJerkContinuation) {
  auto in = input();
  in.limits.progress_speed=.2; in.limits.progress_acceleration=.5; in.limits.progress_jerk=5;
  for (auto initial : {std::pair<double,double>{.001,-.04},
                      {.006045132810726585,-.16792036875525984}}) {
    double s=.2, r=initial.first, b=initial.second;
    for (int k=0;k<100;++k) {
      auto stop=progressStopBounds(s,r,b,.004,in.limits);
      ASSERT_TRUE(stop.feasible) << k << " " << r << " " << b;
      EXPECT_LE(std::abs(stop.acceleration-b),.020000000001);
      s+=.004*r+.5*.004*.004*stop.acceleration;
      r+=.004*stop.acceleration; b=stop.acceleration;
      EXPECT_GE(r,-1e-16);
      // Remove harmless endpoint roundoff before the next strict state check.
      if (std::abs(r)<1e-16) r=0;
    }
    EXPECT_NEAR(r,0,1e-14); EXPECT_NEAR(b,0,1e-14);
  }
}
TEST(Preview, ProgressConeMatchesBruteIntegerOracleAndUpperSymmetry) {
  auto in=input(); in.limits.progress_speed=.2;
  in.limits.progress_acceleration=.5; in.limits.progress_jerk=5;
  for (double r : {0.,.00004,.001,.002493451800168315,.006045132810726585,.1,.199,.2}) {
    auto stop=progressStopBounds(.1,r,0,.004,in.limits);
    double lower=-1e9,upper=1e9;
    for(int k=0;k<200;++k) {
      lower=std::max(lower,-r/(.004*(k+1))-.01*k);
      upper=std::min(upper,(.2-r)/(.004*(k+1))+.01*k);
    }
    EXPECT_NEAR(stop.lower,std::max(-.02,lower),1e-13);
    EXPECT_NEAR(stop.upper,std::min(.02,upper),1e-13);
  }
}
TEST(Preview, ProgressStopDerivedExtremeInputsFailClosedOrRemainFinite) {
  auto in=input();
  for(double dt : {1e-300,1e300,std::numeric_limits<double>::denorm_min()}) {
    auto stop=progressStopBounds(.2,.01,0,dt,in.limits);
    if(stop.feasible) {
      EXPECT_TRUE(std::isfinite(stop.acceleration));
      EXPECT_TRUE(std::isfinite(stop.lower)); EXPECT_TRUE(std::isfinite(stop.upper));
    }
  }
  for(double r : {-1.,1e300,double(NAN)})
    EXPECT_FALSE(progressStopBounds(.2,r,0,.004,in.limits).feasible);
  EXPECT_FALSE(progressStopBounds(1.01,0,0,.004,in.limits).feasible);
}

TEST(Preview, TerminalZeroSpeedDoesNotExcuseNegativeAcceleration) {
  auto in=input(1,1); in.mesh={.04}; in.control_dt=.004;
  in.initial.r=.0016; in.previous_progress_acceleration=-.04;
  in.limits.progress_jerk=5; in.limits.progress_acceleration=.5;
  in.nominal=Eigen::VectorXd::Zero(2); in.nominal(1)=-.04;
  EXPECT_GT(previewLimitViolation(in,in.nominal),.019);
  auto a=assemblePreview(in,stages(in,0));
  auto v=a.qp.constraints*a.nominal_decision;
  bool rejected=false;
  for(int i=0;i<v.size();++i)
    if(a.row_labels[i].find("progress/continuation/terminal/lower/")==0)
      rejected |= v(i)<a.qp.lower(i)-1e-12;
  EXPECT_TRUE(rejected);
}

TEST(Preview, ExplicitRhoKeepsOriginalOptimumAndResetsChangedWorkspaceSetting) {
  auto q=trackingProblem(Eigen::MatrixXd::Identity(2,2),Eigen::VectorXd::Constant(2,.25),0);
  Eigen::SparseMatrix<double> f(2,2);f.setIdentity(); QpWorkspace w;auto o=tight();
  auto r=solveQpWorkspace(q,o,Eigen::VectorXd::Zero(2),f,w,{});
  ASSERT_EQ(r.status,QpStatus::Solved);
  o.initial_rho=1;
  r=solveQpWorkspace(q,o,r.velocity,f,w,{});
  ASSERT_EQ(r.status,QpStatus::Solved);
  EXPECT_FALSE(r.workspace_reused); EXPECT_EQ(r.reset_reason,"rho_setting");
  EXPECT_NEAR(r.initial_rho,1,1e-14); EXPECT_NEAR(r.solver_absolute_tolerance,o.absolute_tolerance,1e-15);
  EXPECT_LT((r.velocity-Eigen::VectorXd::Constant(2,.25)).norm(),1e-8);
  for(double value : {0.,1e-12,1e8,double(NAN)}) {
    o.initial_rho=value; r=solveQpWorkspace(q,o,Eigen::VectorXd::Zero(2),f,w,{});
    EXPECT_EQ(r.status,QpStatus::InvalidInput);EXPECT_EQ(r.velocity.size(),0);
  }
}

TEST(Preview, DiscountCellMatchesIndependentSimpsonAndStableLargeTauLimit) {
  for (auto h_tau : {std::pair<double,double>{.04,.3},{.02,10.},{.08,.03},{.004,.003}}) {
    double h=h_tau.first,tau=h_tau.second;auto ab=progressDiscountCoefficients(h,tau);
    double a=0,b=0;const int N=20000;
    for(int k=0;k<=N;++k) {
      double x=h*k/N,w=k==0||k==N?1:k%2?4:2;
      a+=w*std::exp(-x/tau);b+=w*x*std::exp(-x/tau);
    }
    EXPECT_NEAR(ab.speed,h*a/(3*N),1e-13);
    EXPECT_NEAR(ab.acceleration,h*b/(3*N),1e-13);
  }
  auto ab=progressDiscountCoefficients(.04,1e12);
  EXPECT_NEAR(ab.speed,.04,1e-14);EXPECT_NEAR(ab.acceleration,.0008,1e-15);
  for(double invalid : {0.,-1.,double(NAN),double(INFINITY)})
    EXPECT_THROW(progressDiscountCoefficients(.04,invalid),std::invalid_argument);
  EXPECT_THROW(progressDiscountCoefficients(0,.3),std::invalid_argument);
  EXPECT_THROW(progressDiscountCoefficients(1e308,1e308),std::overflow_error);
}
TEST(Preview, DiscountNonuniformCostAndEveryGradientAxisMatchIndependentIntegration) {
  for(bool lifted : {false,true}) {
    auto in=input(3,3);in.mesh={.02,.06,.03};in.initial.s=.2;in.initial.r=.03;
    in.nominal=Eigen::VectorXd::LinSpaced(12,-.005,.005);in.lifted=lifted;
    in.weights.progress_reward=.7;in.weights.progress_discount_tau=.3;
    auto a=assemblePreview(in,stages(in));
    auto term=*std::find_if(a.terms.begin(),a.terms.end(),[](const auto& t){return t.name=="progress";});
    const int uoffset=lifted?32:0;
    Eigen::VectorXd z=Eigen::VectorXd::LinSpaced(a.qp.gradient.size(),-.002,.003);
    auto integral=[&](const Eigen::VectorXd& decision) {
      double total=0,time=0;
      for(int k=0;k<3;++k) {
        double r=a.states[k].offset(7)+a.states[k].map.row(7).dot(decision);
        double b=a.controls_origin(k*4+3)+decision(uoffset+k*4+3),h=in.mesh[k],sum=0;
        const int M=2000;
        for(int j=0;j<=M;++j) {
          double t=h*j/M,w=j==0||j==M?1:j%2?4:2;
          sum+=w*std::exp(-(time+t)/.3)*(r+b*t);
        }
        total+=h*sum/(3*M);time+=h;
      }
      return -.7*total;
    };
    EXPECT_NEAR(term.gradient.dot(z)+term.constant,integral(z),1e-13);
    for(int i=0;i<z.size();++i) {
      auto plus=z,minus=z;plus(i)+=1e-6;minus(i)-=1e-6;
      EXPECT_NEAR(term.gradient(i),(integral(plus)-integral(minus))/2e-6,1e-10);
    }
    auto old=in;old.weights.progress_discount_tau=0;auto baseline=assemblePreview(old,stages(old));
    EXPECT_EQ((baseline.qp.constraints-a.qp.constraints).norm(),0);
    EXPECT_TRUE((baseline.qp.lower.array()==a.qp.lower.array()).all());
    EXPECT_TRUE((baseline.qp.upper.array()==a.qp.upper.array()).all());
    EXPECT_EQ((baseline.qp.hessian-a.qp.hessian).norm(),0);
  }
}
TEST(Preview, DiscountPrefersEarlierEqualProgressAndRecoversOriginalRewardLimit) {
  auto in=input(1,20);in.weights={0,0,0,0,0,1,0};
  auto early=Eigen::VectorXd::Zero(40).eval(),late=early;
  early(1)=.02;early(3)=-.02;late(21)=.02;late(23)=-.02;
  auto cost=[&](const PreviewInput& x,const Eigen::VectorXd& z) {
    auto a=assemblePreview(x,stages(x));
    auto t=*std::find_if(a.terms.begin(),a.terms.end(),[](const auto& t){return t.name=="progress";});
    return t.gradient.dot(z)+t.constant;
  };
  EXPECT_NEAR(cost(in,early),cost(in,late),1e-15);
  in.weights.progress_discount_tau=.3;EXPECT_LT(cost(in,early),cost(in,late));
  in.initial.s=.2;in.weights.progress_discount_tau=1e12;
  double discounted=cost(in,early);in.weights.progress_discount_tau=0;
  EXPECT_NEAR(discounted-cost(in,early),.2,1e-13);
}
