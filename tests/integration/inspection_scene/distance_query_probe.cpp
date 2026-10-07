#include <Eigen/Core>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <predictive_motion_sim/plant.hpp>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
using namespace predictive_motion;
using Matrix3 = Eigen::Matrix<double, 3, 3, Eigen::RowMajor>;
struct Bounds {
  Eigen::Vector3d center, half;
};
Bounds bounds(const mjModel* m, const mjData* d, int g) {
  Eigen::Matrix3d rotation = Eigen::Map<const Matrix3>(d->geom_xmat + 9 * g);
  return {Eigen::Map<const Eigen::Vector3d>(d->geom_xpos + 3 * g) +
              rotation * Eigen::Map<const Eigen::Vector3d>(m->geom_aabb + 6 * g),
          rotation.cwiseAbs() * Eigen::Map<const Eigen::Vector3d>(m->geom_aabb + 6 * g + 3)};
}
int main(int argc, char** argv) {
  if (argc != 4) return 2;
  try {
    Plant p(argv[1]);
    std::ifstream input(argv[2]);
    std::string line;
    std::getline(input, line);
    std::vector<std::string> names;
    std::stringstream h(line);
    while (std::getline(h, line, ',')) names.push_back(line);
    std::ofstream out(argv[3]);
    out.exceptions(std::ios::failbit | std::ios::badbit);
    out << std::setprecision(17)
        << "sample,geom1,geom2,nativeccd,distmax,query_distance,aabb_lower_bound,bracket_x,bracket_"
           "y,bracket_z";
    for (const auto& name : p.names()) out << ',' << name;
    out << '\n';
    int sample = 0, anomalies = 0;
    while (std::getline(input, line)) {
      std::stringstream s(line);
      std::vector<double> v;
      while (std::getline(s, line, ',')) v.push_back(std::stod(line));
      for (size_t j = 0; j < p.names().size(); ++j) {
        std::string key = "q" + std::to_string(j + 1);
        auto col = std::find(names.begin(), names.end(), key);
        if (col == names.end()) throw std::runtime_error("Missing q column");
        int joint = mj_name2id(p.model(), mjOBJ_JOINT, p.names()[j].c_str());
        p.data()->qpos[p.model()->jnt_qposadr[joint]] = v[col - names.begin()];
      }
      mj_forward(p.model(), p.data());
      int a = mj_name2id(p.model(), mjOBJ_GEOM, "tool_bracket");
      if (a < 0) throw std::runtime_error("No bracket");
      for (const char* name : {"fixture_base", "fixture_left", "fixture_right", "fixture_rear"}) {
        int b = mj_name2id(p.model(), mjOBJ_GEOM, name);
        auto x = bounds(p.model(), p.data(), a), y = bounds(p.model(), p.data(), b);
        double lower = ((x.center - y.center).cwiseAbs() - x.half - y.half).cwiseMax(0).norm();
        for (bool native : {true, false}) {
          if (native)
            p.model()->opt.disableflags &= ~mjDSBL_NATIVECCD;
          else
            p.model()->opt.disableflags |= mjDSBL_NATIVECCD;
          for (double cap : {10., 1., .1, .03}) {
            double distance = mj_geomDistance(p.model(), p.data(), a, b, cap, nullptr);
            out << sample << ",tool_bracket," << name << ',' << native << ',' << cap << ','
                << distance << ',' << lower << ',' << x.center.x() << ',' << x.center.y() << ','
                << x.center.z();
            for (double q : p.positions()) out << ',' << q;
            out << '\n';
            if (distance + 1e-8 < std::min(cap, lower)) anomalies++;
          }
        }
      }
      sample++;
    }
    std::cout << "DISTANCE_QUERY_DIAGNOSTIC samples=" << sample
              << " lower_bound_violations=" << anomalies << '\n';
  } catch (const std::exception& e) {
    std::cerr << e.what() << '\n';
    return 1;
  }
}
