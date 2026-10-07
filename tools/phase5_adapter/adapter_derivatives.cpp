#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>

#include "path_adapter.hpp"
using namespace predictive_motion;
using namespace predictive_motion::preview_adapter;
int main(int argc, char** argv) {
  if (argc != 3) return 2;
  RobotKinematics robot(loadConfig(argv[1]));
  std::ifstream file(argv[2]);
  std::string line;
  std::getline(file, line);
  std::getline(file, line);
  std::istringstream row(line);
  std::vector<double> values;
  while (std::getline(row, line, ',')) values.push_back(std::stod(line));
  Eigen::VectorXd q(7);
  for (int i = 0; i < 7; ++i) q(i) = values[values.size() - 7 + i];
  Path path;
  path.start = V(.72, -.03, .395);
  path.end = V(.92, -.03, .395);
  path.xyzw << .5, .5, .5, .5;
  path.lateral = .007;
  path.vertical = .010;
  double maxq = 0, maxs = 0, maxsig = 0;
  int checks = 0, nonsmooth = 0;
  for (int kind = 0; kind < 2; ++kind) {
    if (kind) {
      path.joint_path = true;
      path.joint_start = q;
      path.joint_direction = Eigen::VectorXd::Constant(7, .02);
    }
    for (double s : {0., .2, .7, 1.}) {
      PreviewState x{q, Eigen::VectorXd::Zero(7), s, 0};
      auto stage = taskStage(robot, x, path, .3);
      double eps = 1e-6;
      for (int j = 0; j < 7; ++j) {
        auto plus = x, minus = x;
        plus.q(j) += eps;
        minus.q(j) -= eps;
        Eigen::VectorXd fd = ((taskStage(robot, plus, path, .3).residual -
                               taskStage(robot, minus, path, .3).residual) /
                              (2 * eps))
                                 .eval();
        double error = (fd - stage.joint_derivative.col(j)).norm();
        maxq = std::max(maxq, error);
        ++checks;
      }
      auto plus = x, minus = x;
      plus.s += eps;
      minus.s -= eps;
      Eigen::VectorXd fd = ((taskStage(robot, plus, path, .3).residual -
                             taskStage(robot, minus, path, .3).residual) /
                            (2 * eps))
                               .eval();
      maxs = std::max(maxs, (fd - stage.path_derivative).norm());
      ++checks;
      auto sg = sigmaGradient(robot, q, .3);
      Eigen::VectorXd direction = Eigen::VectorXd::LinSpaced(7, -.3, .3);
      auto dfd = (indicators(robot, q + 2 * eps * direction, .3).sigma -
                  indicators(robot, q - 2 * eps * direction, .3).sigma) /
                 (4 * eps);
      maxsig = std::max(maxsig, std::abs(dfd - sg.dot(direction)));
      ++checks;
      nonsmooth += indicators(robot, q, .3).nonsmooth;
    }
  }
  std::cout << std::setprecision(17) << "{\"checks\":" << checks << ",\"residual_q_max\":" << maxq
            << ",\"residual_s_max\":" << maxs << ",\"sigma_direction_max\":" << maxsig
            << ",\"nonsmooth\":" << nonsmooth << "}\n";
  return maxq < 1e-6 && maxs < 1e-6 && maxsig < 1e-6 ? 0 : 1;
}
