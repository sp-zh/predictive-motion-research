// Offline solver-only settings diagnostic. Never issues robot commands.
#include <osqp.h>
#include <Eigen/Core>
#include <fstream>
#include <sstream>
#include <vector>
#include <iostream>
#include <iomanip>
#include <cmath>
#include <memory>
Eigen::MatrixXd load(std::string file){std::ifstream f(file);if(!f)throw std::runtime_error(file);std::string line,cell;std::vector<std::vector<double>> rows;while(std::getline(f,line)){std::istringstream s(line);std::vector<double> r;while(std::getline(s,cell,','))r.push_back(std::stod(cell));rows.push_back(r);}Eigen::MatrixXd m(rows.size(),rows.at(0).size());for(int i=0;i<m.rows();++i){if(rows[i].size()!=size_t(m.cols()))throw std::runtime_error("ragged");for(int j=0;j<m.cols();++j)m(i,j)=rows[i][j];}return m;}
struct Csc{std::vector<OSQPInt> p,i;std::vector<OSQPFloat> x;OSQPCscMatrix m{};Csc(const Eigen::MatrixXd& a,bool upper){for(int c=0;c<a.cols();++c){p.push_back(x.size());for(int r=0;r<a.rows();++r)if((!upper||r<=c)&&a(r,c)!=0){i.push_back(r);x.push_back(a(r,c));}}p.push_back(x.size());OSQPCscMatrix_set_data(&m,a.rows(),a.cols(),x.size(),x.data(),i.data(),p.data());}};
int main(int argc,char** argv){if(argc!=3)return 2;std::string d=argv[1];auto H=load(d+"/H.csv"),A=load(d+"/A.csv");Eigen::VectorXd g=load(d+"/g.csv"),l=load(d+"/l.csv"),u=load(d+"/u.csv"),seed=load(d+"/seed.csv");int n=g.size(),m=l.size();if(H.rows()!=n||H.cols()!=n||A.cols()!=n||A.rows()!=m||u.size()!=m||seed.size()!=n)return 3;
 std::cout<<"scale_variables,normalize_rows,rho_initial,status,iter,setup_s,solve_s,original_violation,stationarity_inf,objective,rho_updates,polish_status\n";
 for(bool var:{true})for(bool norm:{true})for(double rho:{.1}){
  Eigen::VectorXd D=Eigen::VectorXd::Ones(n);if(var){if(n!=496)return 4;for(int k=0;k<21;++k){D.segment(k*16,7).setConstant(.002);D.segment(k*16+7,7).setConstant(.0625);D(k*16+14)=.02;D(k*16+15)=.2;}for(int k=0;k<20;++k)D(336+k*8+7)=.5;}
  Eigen::MatrixXd Hs=D.asDiagonal()*H*D.asDiagonal();Eigen::VectorXd gs=D.cwiseProduct(g),zs=seed.cwiseQuotient(D);
  Eigen::VectorXd scales=Eigen::VectorXd::Ones(m),lo=l,hi=u;Eigen::MatrixXd As=A*D.asDiagonal();
  if(norm)for(int i=0;i<m;++i){double s=As.row(i).cwiseAbs().maxCoeff();if(s>0){scales(i)=1/s;As.row(i)*=scales(i);lo(i)*=scales(i);hi(i)*=scales(i);}}
  for(int i=0;i<m;++i){if(std::isinf(lo(i)))lo(i)=-OSQP_INFTY;if(std::isinf(hi(i)))hi(i)=OSQP_INFTY;}
  Csc P(Hs,true),Ac(As,false);OSQPSettings st;osqp_set_default_settings(&st);st.verbose=0;st.rho=rho;st.eps_abs=st.eps_rel=1e-9;st.max_iter=20000;st.time_limit=2.;st.check_termination=1;st.polishing=1;st.adaptive_rho=OSQP_ADAPTIVE_RHO_UPDATE_ITERATIONS;st.adaptive_rho_interval=50;
  OSQPSolver* raw=nullptr;int rc=osqp_setup(&raw,&P.m,gs.data(),&Ac.m,lo.data(),hi.data(),m,n,&st);std::unique_ptr<OSQPSolver,decltype(&osqp_cleanup)> ptr(raw,osqp_cleanup);if(rc||!raw){std::cout<<var<<","<<norm<<","<<rho<<",SETUP_FAILURE\n";continue;}
  osqp_warm_start(raw,zs.data(),nullptr);rc=osqp_solve(raw);double v=INFINITY,k=INFINITY,obj=NAN;
  if(!rc&&raw->solution&&raw->solution->x&&raw->solution->y){Eigen::VectorXd x=D.cwiseProduct(Eigen::Map<Eigen::VectorXd>(raw->solution->x,n)),y=scales.cwiseProduct(Eigen::Map<Eigen::VectorXd>(raw->solution->y,m));if(x.allFinite()&&y.allFinite()){auto ax=A*x;v=0;for(int i=0;i<m;++i)v=std::max({v,l(i)-ax(i),ax(i)-u(i)});k=(H*x+g+A.transpose()*y).lpNorm<Eigen::Infinity>();obj=.5*x.dot(H*x)+g.dot(x);if(raw->info->status_val==OSQP_SOLVED && v<=1e-7 && k<=1e-7){std::ofstream xf(std::string(argv[2])+"-x.csv"),yf(std::string(argv[2])+"-y.csv");xf<<std::setprecision(17);yf<<std::setprecision(17);for(int j=0;j<n;++j)xf<<x(j)<<"\n";for(int j=0;j<m;++j)yf<<y(j)<<"\n";}}}
  std::cout<<std::setprecision(17)<<var<<","<<norm<<","<<rho<<","<<raw->info->status_val<<","<<raw->info->iter<<","<<raw->info->setup_time<<","<<raw->info->solve_time<<","<<v<<","<<k<<","<<obj<<","<<raw->info->rho_updates<<","<<raw->info->status_polish<<"\n";
 }
}
