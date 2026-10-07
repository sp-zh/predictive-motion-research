#include "predictive_motion_sim/plant.hpp"

#include <gtest/gtest.h>

#include <cmath>
#include <cstdlib>
#include <limits>
using predictive_motion::Plant;
std::string model_path() {
  const char* p = std::getenv("FR3_MODEL");
  if (!p) throw std::runtime_error("FR3_MODEL required");
  return p;
}
TEST(Plant, ModelAndClock) {
  Plant p(model_path());
  EXPECT_EQ(p.names().size(), 7u);
  EXPECT_EQ(mj_version(), 337);
  for (int i = 0; i < 250; ++i) p.step();
  EXPECT_NEAR(p.time(), 1.0, 1e-12);
}
TEST(Plant, ResetAndReplay) {
  Plant p(model_path());
  p.reset(42);
  auto q0 = p.positions();
  auto state = [&p]() {
    std::vector<double> s(mj_stateSize(p.model(), mjSTATE_INTEGRATION));
    mj_getState(p.model(), p.data(), s.data(), mjSTATE_INTEGRATION);
    return s;
  };
  const auto initial = state();
  auto apply = [&](int step) {
    auto target = q0;
    for (size_t j = 0; j < target.size(); ++j) target[j] += 0.01 * std::sin(0.01 * step + 0.2 * j);
    p.command(p.names(), target);
  };
  std::vector<std::vector<double>> trace;
  for (int i = 0; i < 500; ++i) {
    apply(i);
    p.step();
    trace.push_back(state());
  }
  EXPECT_NE(initial, state());
  p.reset(42);
  EXPECT_EQ(initial, state());
  EXPECT_EQ(p.time(), 0);
  for (int i = 0; i < 500; ++i) {
    apply(i);
    p.step();
    EXPECT_EQ(trace[i], state()) << "step=" << i;
  }
  p.reset(43);
  EXPECT_NE(initial, state());
}
TEST(Plant, TransactionalCommandAndMotion) {
  Plant p(model_path());
  auto q = p.positions();
  auto old = q;
  q[0] += 0.05;
  p.command(p.names(), q);
  for (int i = 0; i < 250; ++i) {
    p.step();
  }
  EXPECT_GT(p.positions()[0] - old[0], 0.01);
  auto ctrl = std::vector<double>(p.data()->ctrl, p.data()->ctrl + p.model()->nu);
  q.back() = std::numeric_limits<double>::quiet_NaN();
  EXPECT_THROW(p.command(p.names(), q), std::invalid_argument);
  EXPECT_EQ(ctrl, std::vector<double>(p.data()->ctrl, p.data()->ctrl + p.model()->nu));
  q = p.positions();
  q[0] = 100;
  EXPECT_THROW(p.command(p.names(), q), std::invalid_argument);
  auto names = p.names();
  names.back() = names.front();
  EXPECT_THROW(p.command(names, p.positions()), std::invalid_argument);
}
TEST(Plant, InvalidModelAndPeriod) {
  EXPECT_THROW(Plant("/missing.xml"), std::runtime_error);
  EXPECT_THROW(Plant(model_path(), 0.003), std::invalid_argument);
  EXPECT_THROW(Plant(model_path(), std::numeric_limits<double>::infinity()), std::invalid_argument);
  Plant p(model_path(), 0.008);
  p.step();
  EXPECT_NEAR(p.time(), 0.008, 1e-12);
}
