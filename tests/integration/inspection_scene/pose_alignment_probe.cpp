// Independent acceptance audit: post-step telemetry must agree with FK(q_after).
#include <algorithm>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <pinocchio/spatial/explog.hpp>
#include <predictive_motion_kinematics/robot_kinematics.hpp>
#include <sstream>
#include <stdexcept>
#include <vector>
using namespace predictive_motion;
std::vector<std::string> split(const std::string& line) {
  std::stringstream stream(line);
  std::string word;
  std::vector<std::string> result;
  while (std::getline(stream, word, ',')) {
    if (!word.empty() && word.back() == '\r') word.pop_back();
    result.push_back(word);
  }
  return result;
}
int main(int argc, char** argv) {
  if (argc != 4) {
    std::cerr << "Usage: pose_alignment_probe robot.yaml csv_directory fresh_output.csv\n";
    return 2;
  }
  try {
    if (std::filesystem::exists(argv[3]))
      throw std::runtime_error("Preserve existing audit output");
    RobotKinematics kin(loadConfig(argv[1]));
    std::ofstream out(argv[3]);
    out.exceptions(std::ios::failbit | std::ios::badbit);
    out << std::setprecision(17);
    out << "file,samples,position_fk_max_m,rotation_fk_max_rad,position_error_metric_max_m,"
           "rotation_error_metric_max_rad,status\n";
    std::vector<std::filesystem::path> files;
    for (const auto& entry : std::filesystem::directory_iterator(argv[2]))
      if (entry.is_regular_file() && entry.path().extension() == ".csv")
        files.push_back(entry.path());
    std::sort(files.begin(), files.end());
    size_t total = 0;
    int audited = 0, failed = 0;
    for (const auto& file : files) {
      std::ifstream in(file);
      std::string line;
      if (!std::getline(in, line)) continue;
      const auto header = split(line);
      std::map<std::string, size_t> index;
      for (size_t i = 0; i < header.size(); ++i) index.emplace(header[i], i);
      if (!index.count("executed_q_0")) continue;
      size_t samples = 0;
      double position = 0, rotation = 0, pmetric = 0, rmetric = 0;
      while (std::getline(in, line)) {
        const auto fields = split(line);
        auto value = [&](const std::string& key) {
          double v = std::stod(fields.at(index.at(key)));
          if (!std::isfinite(v)) throw std::runtime_error("Nonfinite telemetry");
          return v;
        };
        Eigen::VectorXd q(kin.jointNames().size());
        for (int j = 0; j < q.size(); ++j) q[j] = value("executed_q_" + std::to_string(j));
        auto pose = [&](const std::string& prefix) {
          Eigen::Vector3d xyz;
          Eigen::Vector4d xyzw;
          for (int j = 0; j < 3; ++j) xyz[j] = value(prefix + "_tcp_xyz_" + std::to_string(j));
          for (int j = 0; j < 4; ++j) xyzw[j] = value(prefix + "_tcp_xyzw_" + std::to_string(j));
          return poseFromXyzw(xyz, xyzw);
        };
        const auto expected = kin.tcpPose(q), actual = pose("actual"), desired = pose("desired");
        position = std::max(position, (expected.translation() - actual.translation()).norm());
        rotation = std::max(
            rotation, pinocchio::log3(expected.rotation().transpose() * actual.rotation()).norm());
        pmetric =
            std::max(pmetric, std::abs((expected.translation() - desired.translation()).norm() -
                                       value("position_error")));
        rmetric = std::max(
            rmetric,
            std::abs(pinocchio::log3(expected.rotation().transpose() * desired.rotation()).norm() -
                     value("rotation_error")));
        ++samples;
      }
      if (in.bad() || !samples) throw std::runtime_error("Incomplete CSV input");
      bool pass = position <= 1e-9 && rotation <= 1e-9 && pmetric <= 1e-9 && rmetric <= 1e-9;
      out << file.filename().string() << ',' << samples << ',' << position << ',' << rotation << ','
          << pmetric << ',' << rmetric << ',' << (pass ? "PASS" : "FAIL") << '\n';
      total += samples;
      ++audited;
      if (!pass) ++failed;
    }
    out.flush();
    if (!audited) throw std::runtime_error("No executed telemetry files found");
    std::cout << "POST_STEP_FK_AUDIT " << (failed ? "FAIL" : "PASS") << " files=" << audited
              << " samples=" << total << " failed_files=" << failed << '\n';
    return failed ? 1 : 0;
  } catch (const std::exception& e) {
    std::cerr << e.what() << '\n';
    return 1;
  }
}
