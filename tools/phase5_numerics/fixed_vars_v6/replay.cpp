// Offline equivalent singleton-equality elimination. No robot commands.
#include <osqp.h>
#include <Eigen/Core>
#include <fstream>
#include <sstream>
#include <vector>
#include <iostream>
#include <iomanip>
#include <cmath>
#include <memory>
#include <map>
#include <algorithm>
Eigen::MatrixXd load(std::string file){std::ifstream f(file);if(!f)throw std::runtime_error(file);std::string line,cell;std::vector<std::vector<double>> rows;while(std::getline(f,line)){std::istringstream s(line);std::vector<double> r;while(std::getline(s,cell,','))r.push_back(std::stod(cell));rows.push_back(r);}Eigen::MatrixXd m(rows.size(),rows.at(0).size());for(int i=0;i<m.rows();++i){if(rows[i].size()!=size_t(m.cols()))throw std::runtime_error("ragged");for(int j=0;j<m.cols();++j)m(i,j)=rows[i][j];}return m;}
struct Csc{std::vector<OSQPInt> p,i;std::vector<OSQPFloat> x;OSQPCscMatrix m{};Csc(const Eigen::MatrixXd& a,bool upper){for(int c=0;c<a.cols();++c){p.push_back(x.size());for(int r=0;r<a.rows();++r)if((!upper||r<=c)&&a(r,c)!=0){i.push_back(r);x.push_back(a(r,c));}}p.push_back(x.size());OSQPCscMatrix_set_data(&m,a.rows(),a.cols(),x.size(),x.data(),i.data(),p.data());}};
int main(int argc,char** argv){if(argc!=2)return 2;std::string d=argv[1];auto H=load(d+"/H.csv"),A=load(d+"/A.csv");Eigen::VectorXd g=load(d+"/g.csv"),l=load(d+"/l.csv"),u=load(d+"/u.csv"),seed=load(d+"/seed.csv");int n=g.size(),m=l.size();if(n!=496)return 3;
 std::map<int,std::pair<double,int>> fixed;
 for(int i=0;i<m;++i)if(std::isfinite(l(i))&&l(i)==u(i)){int col=-1;for(int j=0;j<n;++j)if(A(i,j)!=0){if(col>=0){col=-2;break;}col=j;}if(col>=0){double v=l(i)/A(i,col);auto old=fixed.find(col);if(old!=fixed.end()&&old->second.first!=v)return 4;fixed[col]={v,i};}}
 Eigen::VectorXd c=Eigen::VectorXd::Zero(n);std::vector<int> free;for(int i=0;i<n;++i)if(fixed.count(i))c(i)=fixed.at(i).first;else free.push_back(i);
 Eigen::MatrixXd T=Eigen::MatrixXd::Zero(n,free.size());Eigen::VectorXd D=Eigen::VectorXd::Ones(n);for(int k=0;k<21;++k){D.segment(k*16,7).setConstant(.002);D.segment(k*16+7,7).setConstant(.0625);D(k*16+14)=.02;D(k*16+15)=.2;}for(int k=0;k<20;++k)D(336+k*8+7)=.5;
 for(int j=0;j<int(free.size());++j)T(free[j],j)=D(free[j]);Eigen::MatrixXd Hr=T.transpose()*H*T,Ar=A*T;Eigen::VectorXd gr=T.transpose()*(H*c+g),lr=l-A*c,ur=u-A*c,zseed(free.size());for(int j=0;j<int(free.size());++j)zseed(j)=(seed(free[j])-c(free[j]))/D(free[j]);
 std::vector<int> keep;for(int i=0;i<m;++i){if(Ar.row(i).isZero(0)){if(lr(i)>0||ur(i)<0)return 5;}else keep.push_back(i);}Eigen::MatrixXd Ak(keep.size(),free.size());Eigen::VectorXd lk(keep.size()),uk(keep.size());for(int i=0;i<int(keep.size());++i){Ak.row(i)=Ar.row(keep[i]);lk(i)=lr(keep[i]);uk(i)=ur(keep[i]);}
 std::cout<<"# exact-equivalent singleton reduction fixed="<<fixed.size()<<" free="<<free.size()<<" original_rows="<<m<<" kept="<<keep.size()<<" zero_rows_removed="<<m-keep.size()<<"; original SI/KKT validated\n";
 std::cout<<"normalize_rows,rho_initial,status,iter,setup_s,solve_s,original_violation,stationarity_inf,objective,rho_updates,polish_status\n";
 for(bool norm:{false,true})for(double rho:{.01,.1,1.}){Eigen::VectorXd scales=Eigen::VectorXd::Ones(keep.size()),lo=lk,hi=uk;Eigen::MatrixXd As=Ak;if(norm)for(int i=0;i<As.rows();++i){double v=As.row(i).cwiseAbs().maxCoeff();scales(i)=1/v;As.row(i)*=scales(i);lo(i)*=scales(i);hi(i)*=scales(i);}for(int i=0;i<lo.size();++i){if(std::isinf(lo(i)))lo(i)=-OSQP_INFTY;if(std::isinf(hi(i)))hi(i)=OSQP_INFTY;}Csc P(Hr,true),Ac(As,false);OSQPSettings st;osqp_set_default_settings(&st);st.verbose=0;st.rho=rho;st.eps_abs=st.eps_rel=1e-8;st.max_iter=50000;st.time_limit=1.;st.check_termination=1;st.polishing=1;st.adaptive_rho=OSQP_ADAPTIVE_RHO_UPDATE_ITERATIONS;st.adaptive_rho_interval=50;
 OSQPSolver* raw=nullptr;int rc=osqp_setup(&raw,&P.m,gr.data(),&Ac.m,lo.data(),hi.data(),keep.size(),free.size(),&st);std::unique_ptr<OSQPSolver,decltype(&osqp_cleanup)> ptr(raw,osqp_cleanup);if(rc||!raw)return 6;osqp_warm_start(raw,zseed.data(),nullptr);rc=osqp_solve(raw);double v=INFINITY,k=INFINITY,obj=NAN;
 if(!rc&&raw->solution&&raw->solution->x&&raw->solution->y){Eigen::VectorXd x=c+T*Eigen::Map<Eigen::VectorXd>(raw->solution->x,free.size()),y=Eigen::VectorXd::Zero(m);for(int i=0;i<int(keep.size());++i)y(keep[i])=scales(i)*raw->solution->y[i];Eigen::VectorXd grad=H*x+g+A.transpose()*y;for(auto& [col,item]:fixed)y(item.second)=-grad(col)/A(item.second,col);if(x.allFinite()&&y.allFinite()){auto ax=A*x;v=0;for(int i=0;i<m;++i)v=std::max({v,l(i)-ax(i),ax(i)-u(i)});k=(H*x+g+A.transpose()*y).lpNorm<Eigen::Infinity>();obj=.5*x.dot(H*x)+g.dot(x);}}
 std::cout<<std::setprecision(17)<<norm<<","<<rho<<","<<raw->info->status_val<<","<<raw->info->iter<<","<<raw->info->setup_time<<","<<raw->info->solve_time<<","<<v<<","<<k<<","<<obj<<","<<raw->info->rho_updates<<","<<raw->info->status_polish<<"\n";}
}
