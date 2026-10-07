// Independent offline geometry audit, never used as a runtime controller adapter.
#include <coal/distance.h>
#include <coal/shape/geometric_shapes.h>

#include <Eigen/Geometry>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <memory>
#include <predictive_motion_kinematics/robot_kinematics.hpp>
#include <predictive_motion_sim/plant.hpp>
#include <random>
#include <sstream>
#include <stdexcept>
#include <vector>
using namespace predictive_motion;
using V = Eigen::Vector3d;
using R = Eigen::Matrix3d;
using T = coal::Transform3s;
using G = std::shared_ptr<coal::CollisionGeometry>;

coal::DistanceResult query(const G& a, const T& x, const G& b, const T& y) {
  coal::DistanceRequest request;
  request.enable_signed_distance = true;
  request.gjk_tolerance = 1e-10;
  request.epa_tolerance = 1e-10;
  request.gjk_max_iterations = 256;
  coal::DistanceResult result;
  coal::distance(a.get(), x, b.get(), y, request, result);
  if (!std::isfinite(result.min_distance) || !result.normal.allFinite() ||
      !result.nearest_points[0].allFinite() || !result.nearest_points[1].allFinite())
    throw std::runtime_error("Nonfinite Coal query result");
  return result;
}
double witnessError(const coal::DistanceResult& r) {
  return (r.nearest_points[1] - r.nearest_points[0] - r.min_distance * r.normal).norm();
}
T transform(const mjData* d, int g) {
  return T(Eigen::Map<const Eigen::Matrix<double, 3, 3, Eigen::RowMajor>>(d->geom_xmat + 9 * g),
           Eigen::Map<const V>(d->geom_xpos + 3 * g));
}
G shape(const mjModel* m, int g) {
  const double* s = m->geom_size + 3 * g;
  switch (m->geom_type[g]) {
    case mjGEOM_BOX:
      return std::make_shared<coal::Box>(2 * s[0], 2 * s[1], 2 * s[2]);
    case mjGEOM_CYLINDER:
      return std::make_shared<coal::Cylinder>(s[0], 2 * s[1]);
    case mjGEOM_SPHERE:
      return std::make_shared<coal::Sphere>(s[0]);
    default:
      throw std::runtime_error("Unsupported primitive in audit");
  }
}
int object(const mjModel* m, int type, const std::string& name) {
  int g = mj_name2id(m, type, name.c_str());
  if (g < 0) throw std::runtime_error("Missing object " + name);
  return g;
}
std::vector<std::string> cells(const std::string& line) {
  std::stringstream stream(line);
  std::string item;
  std::vector<std::string> result;
  while (std::getline(stream, item, ',')) {
    if (!item.empty() && item.back() == '\r') item.pop_back();
    result.push_back(item);
  }
  return result;
}
int main(int argc, char** argv) {
  if (argc != 5) {
    std::cerr << "Usage: coal_query_probe scene.xml robot.yaml poses.csv fresh_outdir\n";
    return 2;
  }
  try {
    const auto out = std::filesystem::path(argv[4]);
    if (std::filesystem::exists(out) && !std::filesystem::is_empty(out))
      throw std::runtime_error("Preserve evidence: use a fresh output directory");
    std::filesystem::create_directories(out);
    std::ofstream analytic(out / "analytic.csv"), scene(out / "scene.csv"),
        summary(out / "summary.json");
    for (auto* f : {&analytic, &scene, &summary}) {
      f->exceptions(std::ios::badbit | std::ios::failbit);
      *f << std::setprecision(17);
    }
    analytic << "sample,case,expected_distance,query_distance,witness_error,swap_distance_error,"
                "normal_error\n";
    int failures = 0, analytic_cases = 0, scene_cases = 0;
    double analytic_max = 0, witness_max = 0, gradient_max = 0, transform_max = 0;
    std::mt19937 rng(5021);
    std::uniform_real_distribution<double> u(0, 1);
    // Sphere/sphere includes penetration; rotated box/sphere remains separated
    // and has an exact closest-point formula independent of GJK.
    for (int i = 0; i < 2000; ++i) {
      const bool spheres = i < 1000;
      const double r1 = .01 + .04 * u(rng), r2 = .01 + .04 * u(rng);
      V direction(u(rng) - .5, u(rng) - .5, u(rng) - .5);
      direction.normalize();
      R rotation = Eigen::AngleAxisd(6 * u(rng), direction).toRotationMatrix();
      V origin(u(rng) - .5, u(rng) - .5, u(rng) - .5), center;
      G a;
      double expected;
      V normal;
      if (spheres) {
        double separation = .002 + .18 * u(rng);
        center = origin + separation * direction;
        expected = separation - r1 - r2;
        normal = direction;
        a = std::make_shared<coal::Sphere>(r1);
      } else {
        V half(.02 + .03 * u(rng), .02 + .03 * u(rng), .02 + .03 * u(rng));
        V local = direction.cwiseProduct(half + V::Constant(.12 + r2));
        // Push along all components to ensure external non-touching cases.
        local += V::Constant(.18 + r2);
        V closest = local.cwiseMax(-half).cwiseMin(half), delta = local - closest;
        center = origin + rotation * local;
        expected = delta.norm() - r2;
        normal = rotation * delta.normalized();
        a = std::make_shared<coal::Box>(2 * half);
      }
      G b = std::make_shared<coal::Sphere>(r2);
      auto result = query(a, T(rotation, origin), b, T(R::Identity(), center));
      auto swapped = query(b, T(R::Identity(), center), a, T(rotation, origin));
      double error = std::abs(expected - result.min_distance), witness = witnessError(result);
      double swap = std::abs(result.min_distance - swapped.min_distance),
             ne = (normal - result.normal).norm();
      analytic << i << ',' << (spheres ? "sphere_sphere" : "rotated_box_sphere") << ',' << expected
               << ',' << result.min_distance << ',' << witness << ',' << swap << ',' << ne << '\n';
      analytic_max = std::max(analytic_max, error);
      witness_max = std::max(witness_max, witness);
      if (error > 1e-7 || witness > 1e-7 || swap > 1e-7 || ne > 1e-6) ++failures;
      ++analytic_cases;
    }
    // Unique separating axis cases also check signed primitive penetration.
    for (int i = 0; i < 1000; ++i) {
      const bool boxes = i < 500;
      V axis(u(rng) - .5, u(rng) - .5, u(rng) - .5);
      axis.normalize();
      R rotation = Eigen::AngleAxisd(6 * u(rng), axis).toRotationMatrix();
      V origin(u(rng) - .5, u(rng) - .5, u(rng) - .5);
      double separation = .008 + .10 * u(rng), radius = .01 + .01 * u(rng);
      G a = boxes ? G(std::make_shared<coal::Box>(.05, .20, .20))
                  : G(std::make_shared<coal::Cylinder>(.025, .4));
      G b = boxes ? G(std::make_shared<coal::Box>(.05, .20, .20))
                  : G(std::make_shared<coal::Sphere>(radius));
      const V normal = rotation.col(0), center = origin + separation * normal;
      const double expected = separation - (boxes ? .05 : .025 + radius);
      auto result = query(a, T(rotation, origin), b, T(rotation, center));
      auto swapped = query(b, T(rotation, center), a, T(rotation, origin));
      double error = std::abs(expected - result.min_distance), witness = witnessError(result);
      double swap = std::abs(result.min_distance - swapped.min_distance),
             ne = (normal - result.normal).norm();
      analytic << 2000 + i << ',' << (boxes ? "aligned_box_box_signed" : "cylinder_sphere_signed")
               << ',' << expected << ',' << result.min_distance << ',' << witness << ',' << swap
               << ',' << ne << '\n';
      analytic_max = std::max(analytic_max, error);
      witness_max = std::max(witness_max, witness);
      if (error > 1e-7 || witness > 1e-7 || swap > 1e-7 || ne > 1e-6) ++failures;
      ++analytic_cases;
    }
    Plant plant(argv[1]);
    RobotKinematics kin(loadConfig(argv[2]));
    if (plant.names() != kin.jointNames()) throw std::runtime_error("Joint order mismatch");
    struct Primitive {
      std::string name;
      int id;
      G geometry;
      Pose tcp_T_shape;
      T fixed;
    };
    std::vector<Primitive> tools, fixtures;
    const auto initial_positions = plant.positions();
    const Pose initial_tcp = kin.tcpPose(
        Eigen::Map<const Eigen::VectorXd>(initial_positions.data(), initial_positions.size()));
    for (const auto& name :
         {"tool_adapter", "tool_shaft", "tool_sensor", "tool_tip", "tool_bracket"}) {
      int g = mj_name2id(plant.model(), mjOBJ_GEOM, name);
      if (g < 0 && std::string(name) == "tool_bracket") continue;
      if (g < 0) throw std::runtime_error("Missing tool primitive");
      auto tf = transform(plant.data(), g);
      tools.push_back({name, g, shape(plant.model(), g),
                       initial_tcp.inverse() * Pose(tf.rotation(), tf.translation()), tf});
    }
    for (const auto& name : {"fixture_base", "fixture_left", "fixture_right", "fixture_rear"}) {
      int g = object(plant.model(), mjOBJ_GEOM, name);
      fixtures.push_back(
          {name, g, shape(plant.model(), g), Pose::Identity(), transform(plant.data(), g)});
    }
    scene << "sample,tool,fixture,coal_distance,witness_error,swapped_distance_error,gradient_max_"
             "abs,primitive_transform_error,one_sided_slope_gap_max,witness_slope_envelope_"
             "violation_max\n";
    std::ifstream input(argv[3]);
    if (!input) throw std::runtime_error("Missing pose CSV");
    std::string line;
    std::getline(input, line);
    auto header = cells(line);
    int sample = 0;
    while (std::getline(input, line)) {
      auto values = cells(line);
      Eigen::VectorXd q(plant.names().size());
      for (int j = 0; j < q.size(); ++j) {
        auto col = std::find(header.begin(), header.end(), "q" + std::to_string(j + 1));
        if (col == header.end()) throw std::runtime_error("Missing q column");
        q[j] = std::stod(values.at(col - header.begin()));
        int joint = object(plant.model(), mjOBJ_JOINT, plant.names()[j]);
        plant.data()->qpos[plant.model()->jnt_qposadr[joint]] = q[j];
      }
      mj_forward(plant.model(), plant.data());
      const Pose tcp = kin.tcpPose(q);
      const auto jac = kin.tcpJacobian(q, Reference::LocalWorldAligned);
      for (const auto& a : tools) {
        const Pose pose = tcp * a.tcp_T_shape;
        T tf(pose.rotation(), pose.translation());
        auto actual = transform(plant.data(), a.id);
        double terr = std::max((actual.translation() - tf.translation()).norm(),
                               (actual.rotation() - tf.rotation()).norm());
        transform_max = std::max(transform_max, terr);
        for (const auto& b : fixtures) {
          auto result = query(a.geometry, tf, b.geometry, b.fixed);
          auto swapped = query(b.geometry, b.fixed, a.geometry, tf);
          double witness = witnessError(result),
                 swap = std::abs(result.min_distance - swapped.min_distance);
          const V lever = result.nearest_points[0] - tcp.translation();
          Eigen::RowVectorXd predicted(q.size());
          for (int j = 0; j < q.size(); ++j)
            predicted[j] = -result.normal.dot(jac.topRows<3>().col(j) +
                                              jac.bottomRows<3>().col(j).cross(lever));
          double ge = 0, slope_gap = 0, envelope = 0;
          for (int j = 0; j < q.size(); ++j) {
            Eigen::VectorXd plus = q, minus = q;
            plus[j] += 1e-6;
            minus[j] -= 1e-6;
            auto x = kin.tcpPose(plus) * a.tcp_T_shape, y = kin.tcpPose(minus) * a.tcp_T_shape;
            double dp = query(a.geometry, T(x.rotation(), x.translation()), b.geometry, b.fixed)
                            .min_distance;
            double dm = query(a.geometry, T(y.rotation(), y.translation()), b.geometry, b.fixed)
                            .min_distance;
            double fd = (dp - dm) / 2e-6;
            const double right = (dp - result.min_distance) / 1e-6,
                         left = (result.min_distance - dm) / 1e-6;
            slope_gap = std::max(slope_gap, std::abs(right - left));
            envelope = std::max(envelope, std::max({0., std::min(right, left) - predicted[j],
                                                    predicted[j] - std::max(right, left)}));
            ge = std::max(ge, std::abs(fd - predicted[j]));
          }
          gradient_max = std::max(gradient_max, ge);
          witness_max = std::max(witness_max, witness);
          scene << sample << ',' << a.name << ',' << b.name << ',' << result.min_distance << ','
                << witness << ',' << swap << ',' << ge << ',' << terr << ',' << slope_gap << ','
                << envelope << '\n';
          if (result.min_distance <= 0 || witness > 1e-7 || swap > 1e-7 || ge > 2e-4 || terr > 1e-9)
            ++failures;
          ++scene_cases;
        }
      }
      ++sample;
    }
    if (sample < 2) throw std::runtime_error("Insufficient scene samples");
    summary
        << "{\"status\":\"" << (failures ? "FAIL" : "PASS")
        << "\",\"analytic_seed\":5021,\"analytic_cases\":" << analytic_cases
        << ",\"scene_pose_samples\":" << sample << ",\"scene_pair_cases\":" << scene_cases
        << ",\"failed_cases\":" << failures << ",\"analytic_distance_max_error_m\":" << analytic_max
        << ",\"witness_max_error_m\":" << witness_max
        << ",\"distance_gradient_max_abs_m_per_rad\":" << gradient_max
        << ",\"primitive_transform_max_error\":" << transform_max
        << ",\"runtime_controller_adapter\":false,\"mesh_and_self_collision_validated\":false}\n";
    analytic.flush();
    scene.flush();
    summary.flush();
    std::cout << "COAL_QUERY_AUDIT " << (failures ? "FAIL" : "PASS") << " failed_cases=" << failures
              << " gradient_max=" << gradient_max << '\n';
    return failures ? 1 : 0;
  } catch (const std::exception& e) {
    std::cerr << e.what() << '\n';
    return 1;
  }
}
