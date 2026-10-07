#include <predictive_motion_control/reactive_qp.hpp>
#include <chrono>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <vector>
using namespace predictive_motion::control;
Eigen::MatrixXd csv(const std::filesystem::path& path) {
  std::ifstream in(path);std::string line;std::vector<std::vector<double>> rows;
  while(std::getline(in,line)){std::stringstream stream(line);std::string cell;std::vector<double> row;while(std::getline(stream,cell,','))row.push_back(std::stod(cell));if(!row.empty())rows.push_back(row);}
  if(rows.empty())throw std::runtime_error("empty matrix");
  Eigen::MatrixXd out(rows.size(),rows[0].size());
  for(int i=0;i<int(rows.size());++i){if(rows[i].size()!=rows[0].size())throw std::runtime_error("ragged matrix");for(int j=0;j<int(rows[i].size());++j)out(i,j)=rows[i][j];}return out;
}
int main(int argc,char** argv){
  if(argc!=3)return 2;const std::filesystem::path input=argv[1],output=argv[2];
  if(std::filesystem::exists(output))throw std::runtime_error("refuse output overwrite");
  QpProblem p;p.hessian=csv(input/"first_rejected_H.csv");p.gradient=csv(input/"first_rejected_g.csv");p.constraints=csv(input/"first_rejected_A.csv");p.lower=csv(input/"first_rejected_lower.csv");p.upper=csv(input/"first_rejected_upper.csv");p.state_age_seconds=0;
  std::filesystem::create_directories(output);std::ofstream log(output/"solves.csv");log<<std::setprecision(17);
  log<<"case,tolerance,status,raw_status,api_error,iterations,violation,maximum_violation_row,primal_residual,dual_residual,setup_seconds,solve_seconds,wall_seconds,solver_absolute_tolerance,solver_relative_tolerance,velocity_entries,workspace_reused,solver_version\n";
  const double tolerances[]={1e-9,1e-11,1e-12,1e-13};
  for(int k=0;k<4;++k){QpOptions o;o.absolute_tolerance=o.relative_tolerance=tolerances[k];o.acceptance_tolerance=1e-7;o.max_iterations=4000;o.time_limit_seconds=o.max_state_age_seconds=.05;
    auto begin=std::chrono::steady_clock::now();auto r=solveQp(p,o);double wall=std::chrono::duration<double>(std::chrono::steady_clock::now()-begin).count();
    log<<k<<','<<tolerances[k]<<','<<statusName(r.status)<<','<<r.raw_status<<','<<r.api_error<<','<<r.iterations<<','<<r.violation<<','<<r.maximum_violation_row<<','<<r.primal_residual<<','<<r.dual_residual<<','<<r.setup_seconds<<','<<r.solve_seconds<<','<<wall<<','<<r.solver_absolute_tolerance<<','<<r.solver_relative_tolerance<<','<<r.velocity.size()<<','<<r.workspace_reused<<','<<qpSolverVersion()<<'\n';log.flush();
    if(r.status==QpStatus::Solved){std::ofstream point(output/("case"+std::to_string(k)+"_solved_x.csv"));point<<std::setprecision(17);for(double x:r.velocity)point<<x<<'\n';}
    else if(r.velocity.size())throw std::runtime_error("non-SOLVED result exposed a candidate");
  }
  std::cout<<"OFFLINE_FRESH_FROZEN_QP_PRECISION_SWEEP_COMPLETE cases=4 original_candidate_not_recovered\n";
}
