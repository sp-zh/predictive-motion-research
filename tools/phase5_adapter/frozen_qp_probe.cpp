#include <Eigen/Eigenvalues>
#include <chrono>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <predictive_motion_control/reactive_qp.hpp>
#include <sstream>
using namespace predictive_motion::control;
Eigen::MatrixXd load(const std::filesystem::path& p) {
  std::ifstream file(p);
  std::string line;
  std::vector<std::vector<double>> rows;
  int cols = -1;
  while (std::getline(file, line)) {
    std::istringstream input(line);
    std::string token;
    std::vector<double> row;
    while (std::getline(input, token, ',')) row.push_back(std::stod(token));
    if (cols < 0) cols = row.size();
    if (int(row.size()) != cols) throw std::runtime_error("CSV shape");
    rows.push_back(std::move(row));
  }
  Eigen::MatrixXd result(rows.size(), std::max(0, cols));
  for (int i = 0; i < int(rows.size()); ++i)
    for (int j = 0; j < cols; ++j) result(i, j) = rows[i][j];
  return result;
}
int main(int argc, char** argv) {
  if (argc != 3 && argc != 5 && argc != 7) return 2;
  std::filesystem::path dir = argv[1];
  std::string mode = argv[2];
  QpProblem p;
  p.hessian = load(dir / "H.csv");
  p.gradient = load(dir / "g.csv").col(0);
  p.constraints = load(dir / "A.csv");
  p.lower = load(dir / "l.csv").col(0);
  p.upper = load(dir / "u.csv").col(0);
  Eigen::VectorXd seed = load(dir / "seed.csv").col(0);
  std::ifstream label_file(dir / "row_labels.txt");
  std::vector<std::string> labels;
  std::string label;
  while (std::getline(label_file, label)) labels.push_back(label);
  Eigen::SparseMatrix<double> factor;
  if (std::filesystem::exists(dir / "F.csv")) {
    Eigen::MatrixXd r = load(dir / "F.csv");
    factor = r.sparseView(0, 0);
  } else {
    Eigen::SelfAdjointEigenSolver<Eigen::MatrixXd> eig(p.hessian);
    if (eig.info() != Eigen::Success || eig.eigenvalues().minCoeff() < -1e-12)
      throw std::runtime_error("No PSD factor");
    Eigen::MatrixXd r =
        eig.eigenvalues().cwiseMax(0.).cwiseSqrt().asDiagonal() * eig.eigenvectors().transpose();
    factor = r.sparseView(0, 0);
  }
  const QpProblem original = p;
  Eigen::VectorXd scale = Eigen::VectorXd::Ones(seed.size());
  if (mode == "variable_workspace") {
    if (seed.size() == 496) {
      for (int k = 0; k <= 20; ++k) {
        scale.segment(k * 16, 7).setConstant(.002);
        scale.segment(k * 16 + 7, 7).setConstant(.0625);
        scale(k * 16 + 14) = .02;
        scale(k * 16 + 15) = .2;
      }
      for (int k = 0; k < 20; ++k) scale(336 + k * 8 + 7) = .5;
    } else if (seed.size() == 160) {
      for (int k = 0; k < 20; ++k) scale(k * 8 + 7) = .5;
    } else
      throw std::runtime_error("Unknown reference layout");
    p.hessian = scale.asDiagonal() * p.hessian * scale.asDiagonal();
    p.gradient = scale.cwiseProduct(p.gradient);
    p.constraints = p.constraints * scale.asDiagonal();
    Eigen::SparseMatrix<double> diagonal = scale.asDiagonal().toDenseMatrix().sparseView();
    factor = factor * diagonal;
    seed = seed.cwiseQuotient(scale);
  }
  QpOptions o;
  o.absolute_tolerance = 1e-9;
  o.relative_tolerance = 1e-9;
  o.acceptance_tolerance = 1e-7;
  o.max_iterations = 4000;
  o.time_limit_seconds = argc >= 5 ? std::stod(argv[3]) : .05;
  if (argc >= 5) o.max_iterations = std::stoi(argv[4]);
  if (argc == 7) {
    o.absolute_tolerance = std::stod(argv[5]);
    o.relative_tolerance = std::stod(argv[6]);
  }
  QpWorkspace workspace;
  auto begin = std::chrono::steady_clock::now();
  auto result = mode == "certified_cold" ? solveQpCertified(p, o, seed, factor)
                                         : solveQpWorkspace(p, o, seed, factor, workspace, labels);
  double wall = std::chrono::duration<double>(std::chrono::steady_clock::now() - begin).count();
  double violation = INFINITY;
  if (result.status == QpStatus::Solved) {
    Eigen::VectorXd x = scale.cwiseProduct(result.velocity), a = original.constraints * x;
    violation = 0;
    for (int i = 0; i < a.size(); ++i)
      violation = std::max({violation, original.lower(i) - a(i), a(i) - original.upper(i)});
    if (violation > o.acceptance_tolerance) {
      result.status = QpStatus::ConstraintViolation;
      result.velocity.resize(0);
    }
  }
  std::cout << std::setprecision(17) << "mode=" << mode << " status=" << statusName(result.status)
            << " budget_s=" << o.time_limit_seconds << " maxiter=" << o.max_iterations
            << " eps_abs=" << o.absolute_tolerance << " eps_rel=" << o.relative_tolerance
            << " acceptance_si=" << o.acceptance_tolerance << " n=" << p.gradient.size() << " m=" << p.lower.size()
            << " iterations=" << result.iterations << " wall=" << wall
            << " setup=" << result.setup_seconds << " solve=" << result.solve_seconds
            << " primal_solver=" << result.primal_residual
            << " dual_solver=" << result.dual_residual << " original_violation=" << violation
            << " scale_min=" << result.minimum_row_scale
            << " scale_max=" << result.maximum_row_scale << " rho_updates=" << result.rho_updates
            << " polish=" << result.polish_status << '\n';
  return 0;
}
