#include <yaml-cpp/yaml.h>

#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <pinocchio/spatial/explog.hpp>
#include <predictive_motion_kinematics/robot_kinematics.hpp>
#include <predictive_motion_sim/plant.hpp>
#include <random>
#include <stdexcept>
#include <vector>

using namespace predictive_motion;
int id(mjModel* m, int type, const char* name) {
  const int result = mj_name2id(m, type, name);
  if (result < 0) throw std::runtime_error(std::string("Missing scene object: ") + name);
  return result;
}
void close(double a, double b, const char* reason) {
  if (!std::isfinite(a) || std::abs(a - b) > 1e-9) throw std::runtime_error(reason);
}
// Separation of enclosing world boxes is a conservative distance lower bound.
// Native MuJoCo distance queries are retained as diagnostics only (GEO002).
double conservativeClearance(const mjModel* m, const mjData* d, int a, int b) {
  auto bound = [&](int g) {
    Eigen::Matrix3d rotation =
        Eigen::Map<const Eigen::Matrix<double, 3, 3, Eigen::RowMajor>>(d->geom_xmat + 9 * g);
    Eigen::Vector3d center = Eigen::Map<const Eigen::Vector3d>(d->geom_xpos + 3 * g) +
                             rotation * Eigen::Map<const Eigen::Vector3d>(m->geom_aabb + 6 * g);
    Eigen::Vector3d half =
        rotation.cwiseAbs() * Eigen::Map<const Eigen::Vector3d>(m->geom_aabb + 6 * g + 3);
    if (!center.allFinite() || !half.allFinite() || (half.array() <= 0).any())
      throw std::runtime_error("Invalid primitive bounding box");
    return std::pair<Eigen::Vector3d, Eigen::Vector3d>(center, half);
  };
  auto x = bound(a), y = bound(b);
  return ((x.first - y.first).cwiseAbs() - x.second - y.second).cwiseMax(0).norm();
}
int main(int argc, char** argv) {
  if (argc != 5) {
    std::cerr << "Usage: scene_probe scene.xml robot.yaml cad.json evidence.json\n";
    return 2;
  }
  try {
    Plant plant(argv[1]);
    RobotKinematics kin(loadConfig(argv[2]));
    auto cad = YAML::LoadFile(argv[3]);
    auto m = plant.model();
    auto d = plant.data();
    if (plant.names() != kin.jointNames())
      throw std::runtime_error("Scene/kinematics joint order mismatch");
    int shaft = id(m, mjOBJ_GEOM, "tool_shaft"), left = id(m, mjOBJ_GEOM, "fixture_left"),
        right = id(m, mjOBJ_GEOM, "fixture_right");
    close(m->geom_size[3 * shaft], cad["tool"]["shaft_radius"].as<double>(), "Shaft radius scale");
    close(m->geom_size[3 * shaft + 1] * 2, cad["tool"]["length"].as<double>(),
          "Shaft length scale");
    close(m->geom_pos[3 * right + 1] - m->geom_pos[3 * left + 1] - m->geom_size[3 * left + 1] -
              m->geom_size[3 * right + 1],
          cad["fixture"]["channel_width"].as<double>(), "Channel was filled or scaled incorrectly");
    int tcp = id(m, mjOBJ_SITE, "inspection_tcp");
    std::mt19937 rng(913);
    double max_position = 0, max_rotation = 0;
    for (int sample = 0; sample < 64; ++sample) {
      Eigen::VectorXd q(kin.jointNames().size());
      for (int j = 0; j < q.size(); ++j) {
        int joint = id(m, mjOBJ_JOINT, kin.jointNames()[j].c_str());
        double lo = std::max(kin.lowerLimits()[j], m->jnt_range[2 * joint]);
        double hi = std::min(kin.upperLimits()[j], m->jnt_range[2 * joint + 1]);
        q[j] = lo + (0.05 + 0.9 * double(rng()) / 4294967295.0) * (hi - lo);
        d->qpos[m->jnt_qposadr[joint]] = q[j];
      }
      mj_forward(m, d);
      auto expected = kin.tcpPose(q);
      Eigen::Matrix3d rotation =
          Eigen::Map<const Eigen::Matrix<double, 3, 3, Eigen::RowMajor>>(d->site_xmat + 9 * tcp);
      max_position = std::max(
          max_position,
          (expected.translation() - Eigen::Map<const Eigen::Vector3d>(d->site_xpos + 3 * tcp))
              .norm());
      max_rotation = std::max(max_rotation,
                              pinocchio::log3(expected.rotation().transpose() * rotation).norm());
    }
    if (max_position > 1e-9 || max_rotation > 1e-9)
      throw std::runtime_error("Physical inspection site/TCP mismatch");
    plant.reset(42);
    std::unique_ptr<mjData, decltype(&mj_deleteData)> observation(mj_makeData(m), mj_deleteData);
    if (!observation) throw std::runtime_error("Cannot allocate observation data");
    const int state_size = mj_stateSize(m, mjSTATE_INTEGRATION);
    std::vector<double> state_before(state_size), state_after(state_size);
    double post_position = 0, post_rotation = 0;
    double clearance = std::numeric_limits<double>::infinity();
    double native_distance = std::numeric_limits<double>::infinity();
    int max_contacts = 0;
    std::vector<const char*> tool_geoms = {"tool_adapter", "tool_shaft", "tool_sensor", "tool_tip"};
    if (cad["tool"]["camera_bracket"].as<bool>()) tool_geoms.push_back("tool_bracket");
    for (int step = 0; step < 1000; ++step) {
      plant.step();
      // Synchronize observations without touching the integration/warm-start data.
      mj_getState(m, plant.data(), state_before.data(), mjSTATE_INTEGRATION);
      mj_copyData(observation.get(), m, plant.data());
      mj_forward(m, observation.get());
      mj_getState(m, plant.data(), state_after.data(), mjSTATE_INTEGRATION);
      if (state_before != state_after)
        throw std::runtime_error("Observation changed integration state");
      d = observation.get();
      close(d->time, plant.time(), "Observation time mismatch");
      const auto positions = plant.positions();
      const auto expected =
          kin.tcpPose(Eigen::Map<const Eigen::VectorXd>(positions.data(), positions.size()));
      const Eigen::Matrix3d rotation =
          Eigen::Map<const Eigen::Matrix<double, 3, 3, Eigen::RowMajor>>(d->site_xmat + 9 * tcp);
      post_position = std::max(
          post_position,
          (expected.translation() - Eigen::Map<const Eigen::Vector3d>(d->site_xpos + 3 * tcp))
              .norm());
      post_rotation = std::max(post_rotation,
                               pinocchio::log3(expected.rotation().transpose() * rotation).norm());
      max_contacts = std::max(max_contacts, d->ncon);
      for (const char* tool : tool_geoms)
        for (const char* fixture :
             {"fixture_base", "fixture_left", "fixture_right", "fixture_rear"}) {
          const int a = id(m, mjOBJ_GEOM, tool), b = id(m, mjOBJ_GEOM, fixture);
          clearance = std::min(clearance, conservativeClearance(m, d, a, b));
          native_distance = std::min(native_distance, mj_geomDistance(m, d, a, b, 10, nullptr));
        }
    }
    std::ofstream out(argv[4]);
    out.exceptions(std::ios::failbit | std::ios::badbit);
    const bool clear =
        max_contacts == 0 && clearance >= 0.01 && post_position <= 1e-9 && post_rotation <= 1e-9;
    out << std::setprecision(17) << "{\"status\":\"" << (clear ? "PASS" : "FAIL")
        << "\",\"tcp_random_samples\":64,\"seed\":913,\"tcp_position_max_m\":" << max_position
        << ",\"tcp_rotation_max_rad\":" << max_rotation
        << ",\"post_step_tcp_position_max_m\":" << post_position
        << ",\"post_step_tcp_rotation_max_rad\":" << post_rotation
        << ",\"observation_does_not_change_integration_state\":true"
        << ",\"held_steps\":1000,\"held_sim_seconds\":" << plant.time()
        << ",\"max_total_contacts\":" << max_contacts
        << ",\"clearance_provider\":\"conservative world-AABB separation lower bound\""
        << ",\"all_tool_components_included\":true"
        << ",\"min_tool_fixture_clearance_lower_bound_m\":" << clearance
        << ",\"native_distance_diagnostic_min_m\":" << native_distance
        << ",\"collision_validation_complete\":false}\n";
    std::cout << "INSPECTION_SCENE_TCP_UNITS_AND_STEP_" << (clear ? "PASS" : "FAIL")
              << " contacts=" << max_contacts << " clearance_lower_bound=" << clearance << '\n';
    if (!clear) {
      std::cerr << "Scene startup contact/clearance gate FAIL\n";
      return 1;
    }
  } catch (const std::exception& e) {
    std::cerr << e.what() << '\n';
    return 1;
  }
}
