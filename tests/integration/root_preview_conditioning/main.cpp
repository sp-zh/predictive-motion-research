// Analytic linear 7-DoF/.8s fixture isolates QP numerics from robot geometry.
// A zero-control trajectory is exactly feasible; this is not a robot trial.
#include <predictive_motion_control/predictive.hpp>
#include <iostream>
#include <fstream>
#include <iomanip>
#include <filesystem>
using namespace predictive_motion::control;
void save(const std::string& path,const Eigen::MatrixXd& m){std::ofstream f(path);f<<std::setprecision(17);for(int i=0;i<m.rows();++i){for(int j=0;j<m.cols();++j){if(j)f<<",";f<<m(i,j);}f<<"\n";}}
int main(int argc,char** argv){
 if(argc!=2)return 2;
 for(bool lifted:{false,true}){
  int n=7,N=20;PreviewInput in;in.lifted=lifted;in.initial={Eigen::VectorXd::Zero(n),Eigen::VectorXd::Zero(n),0,0};
  in.mesh=std::vector<double>(N,.04);in.nominal=Eigen::VectorXd::Zero(N*(n+1));
  in.accepted_position=in.initial.q;in.accepted_velocity=in.initial.v;
  in.previous_acceleration=in.previous_model_acceleration=Eigen::VectorXd::Zero(n);
  in.limits.lower=Eigen::VectorXd::Constant(n,-3);in.limits.upper=-in.limits.lower;
  in.limits.velocity=Eigen::VectorXd::Constant(n,.0625);in.limits.acceleration=Eigen::VectorXd::Constant(n,1);
  in.limits.jerk=Eigen::VectorXd::Constant(n,20);in.limits.posture=Eigen::VectorXd::Zero(n);
  in.limits.progress_speed=.2;in.limits.progress_acceleration=.5;in.limits.progress_jerk=5;
  in.limits.position_margin=.005;in.joint_trust=.002;in.progress_trust=.02;in.terminal_stop=true;
  in.weights={100,.01,.001,1e-5,.001,.1,.1};
  std::vector<PreviewStage> stages(N+1);Eigen::MatrixXd J=Eigen::MatrixXd::Zero(6,n);
  for(int i=0;i<6;++i){J(i,i)=.5;J(i,6)=.1*(i+1);}
  for(auto& s:stages){s.residual=Eigen::VectorXd::Zero(6);s.joint_derivative=J;s.path_derivative=Eigen::VectorXd::Constant(6,-.1);}
  auto a=assemblePreview(in,stages);std::string d=std::string(argv[1])+(lifted?"/lifted":"/condensed");std::filesystem::create_directories(d);
  save(d+"/H.csv",a.qp.hessian);save(d+"/A.csv",a.qp.constraints);save(d+"/g.csv",a.qp.gradient);save(d+"/l.csv",a.qp.lower);save(d+"/u.csv",a.qp.upper);save(d+"/seed.csv",a.nominal_decision);
  std::ofstream labels(d+"/row_labels.txt");for(auto& l:a.row_labels)labels<<l<<"\n";labels.close();
  double nominal_violation=0;auto ax=a.qp.constraints*a.nominal_decision;
  for(int i=0;i<ax.size();++i)nominal_violation=std::max({nominal_violation,a.qp.lower(i)-ax(i),ax(i)-a.qp.upper(i)});
  if(nominal_violation>1e-12||previewLimitViolation(in,in.nominal)>1e-12)return 3;
  QpOptions o;o.absolute_tolerance=o.relative_tolerance=1e-9;o.acceptance_tolerance=1e-7;o.max_iterations=4000;o.time_limit_seconds=.05;
  QpWorkspace ws;auto r=solveQpWorkspace(a.qp,o,a.nominal_decision,a.convex_factor,ws,a.row_labels);
  std::cout<<std::setprecision(17)<<"ANALYTIC_LINEAR_HORIZON lifted="<<lifted<<" n="<<a.qp.gradient.size()<<" m="<<a.qp.lower.size()<<" nominal_violation="<<nominal_violation<<" status="<<statusName(r.status)<<" iterations="<<r.iterations<<" setup_s="<<r.setup_seconds<<" solve_s="<<r.solve_seconds<<" primal="<<r.primal_residual<<" dual="<<r.dual_residual<<" command_size="<<r.velocity.size()<<"\n";
 }
 return 0;
}
