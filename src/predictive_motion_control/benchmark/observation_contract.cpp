#include <fstream>
#include <iomanip>
#include <iostream>
#include <pinocchio/spatial/explog.hpp>

#include "observation_snapshot.hpp"
using namespace predictive_motion;
std::vector<double> state(Plant& p) {
  std::vector<double> values(mj_stateSize(p.model(), mjSTATE_INTEGRATION));
  mj_getState(p.model(), p.data(), values.data(), mjSTATE_INTEGRATION);
  return values;
}
int main(int argc, char** argv) {
  if (argc != 4) return 2;
  try {
    auto config = loadConfig(argv[1]);
    RobotKinematics k(config);
    Plant observed(argv[2], .004), unobserved(argv[2], .004);
    std::unique_ptr<mjData, decltype(&mj_deleteData)> scratch(mj_makeData(observed.model()),
                                                              mj_deleteData);
    auto start = observed.positions();
    double maxP = 0, maxR = 0, maxCacheGap = 0;
    std::ofstream f(argv[3]);
    f.exceptions(std::ios::failbit | std::ios::badbit);
    f << std::setprecision(17)
      << "step,time,fk_position_error,fk_rotation_error,old_site_position_gap,old_site_rotation_"
         "gap,integration_state_unchanged,replay_identical\n";
    for (int step = 0; step < 200; ++step) {
      auto target = start;
      for (size_t i = 0; i < target.size(); ++i)
        target[i] += .02 * std::sin(step * .004 * 2 + i * .3);
      observed.command(observed.names(), target);
      unobserved.command(unobserved.names(), target);
      observed.step();
      unobserved.step();
      auto before = state(observed);
      double time = observed.time();
      int id = mj_name2id(observed.model(), mjOBJ_SITE, "attachment_site");
      Pose old(Eigen::Map<const Eigen::Matrix<double, 3, 3, Eigen::RowMajor>>(
                   observed.data()->site_xmat + 9 * id),
               Eigen::Map<const Eigen::Vector3d>(observed.data()->site_xpos + 3 * id));
      old = config.world_T_base * old * config.flange_T_tcp;
      auto pose = observeTcp(observed, scratch.get(), config, "attachment_site");
      auto q = observed.positions();
      auto expected = k.tcpPose(Eigen::Map<const Eigen::VectorXd>(q.data(), q.size()));
      double pe = (pose.translation() - expected.translation()).norm(),
             re = pinocchio::log3(pose.rotation().transpose() * expected.rotation()).norm(),
             gap = (old.translation() - expected.translation()).norm(),
             rgap = pinocchio::log3(old.rotation().transpose() * expected.rotation()).norm();
      bool unchanged = before == state(observed) && time == observed.time(),
           identical = state(observed) == state(unobserved);
      if (!unchanged || !identical || pe > 1e-12 || re > 1e-12)
        throw std::runtime_error("Observation synchronization contract failed");
      maxP = std::max(maxP, pe);
      maxR = std::max(maxR, re);
      maxCacheGap = std::max(maxCacheGap, gap);
      f << step << ',' << time << ',' << pe << ',' << re << ',' << gap << ',' << rgap << ','
        << unchanged << ',' << identical << '\n';
    }
    f.flush();
    std::cout << std::setprecision(17)
              << "OBSERVATION_SAME_Q_TIME_FK_NO_MUTATION_REPLAY_PASS max_position=" << maxP
              << " max_rotation=" << maxR << " cached_site_gap=" << maxCacheGap << '\n';
  } catch (const std::exception& error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
