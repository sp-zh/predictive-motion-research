#pragma once
#include <Eigen/Core>
#include <algorithm>
#include <Eigen/LU>
#include <chrono>
#include <cmath>
#include <stdexcept>
#include <vector>
#include <string>
namespace phase5_dynamic_numeric_v1 {
struct Face {int row=0,side=1;};
struct Event {int iteration=0,active_count=0,worst_row=-1;double violation=0,min_multiplier=0,stationarity=0,kkt_residual=0;};
struct Result {Eigen::VectorXd primal,dual;std::vector<Face> faces;std::vector<Event> events;bool complete=false;std::string error;};
// Finite feasible-start primal active-set hint. It returns numerical x/y only;
// current native OSQP/full original SI/rounded history/value/private C are gates.
inline Result derive(const Eigen::MatrixXd& H,const Eigen::VectorXd& g,const Eigen::MatrixXd& A,const Eigen::VectorXd& lower,const Eigen::VectorXd& upper,const Eigen::VectorXd& seed=Eigen::VectorXd{}){
 Result out;const auto started=std::chrono::steady_clock::now();try{const int n=g.size(),m=lower.size();auto need=[](bool ok,const char* why){if(!ok)throw std::invalid_argument(why);};
 need(n>0&&n<=144&&m>0&&m<=20000&&H.rows()==n&&H.cols()==n&&A.rows()==m&&A.cols()==n&&upper.size()==m,"bounded current numeric shapes");need(H.allFinite()&&g.allFinite()&&A.allFinite()&&lower.allFinite()&&upper.allFinite()&&(lower.array()<=upper.array()).all(),"finite current numeric matrix/bounds");
 auto within=[&](){need(std::chrono::duration<double>(std::chrono::steady_clock::now()-started).count()<=10,"current numeric wall cap10s including final scan/return");};
 out.primal=seed.size()?seed:Eigen::VectorXd::Zero(n);need(out.primal.size()==n&&out.primal.allFinite(),"current matrix finite feasible-start hint shape");out.dual=Eigen::VectorXd::Zero(m);out.events.reserve(512);out.faces.reserve(n);Eigen::VectorXd ax=A*out.primal;need((lower-ax).maxCoeff()<=1e-12&&(ax-upper).maxCoeff()<=1e-12,"current-matrix start infeasible; retained refusal, no projection");
 for(int iteration=0;iteration<512;++iteration){within();const int k=out.faces.size();Eigen::MatrixXd K=Eigen::MatrixXd::Zero(n+k,n+k);Eigen::VectorXd rhs=Eigen::VectorXd::Zero(n+k);K.topLeftCorner(n,n)=H;rhs.head(n)=-(H*out.primal+g);
 for(int j=0;j<k;++j){auto face=out.faces[j];K.block(n+j,0,1,n)=face.side*A.row(face.row);K.block(0,n+j,n,1)=face.side*A.row(face.row).transpose();}
 Eigen::FullPivLU<Eigen::MatrixXd> decomposition(K);need(decomposition.rank()==n+k,"dependent active-face KKT retained failure");const Eigen::VectorXd sol=decomposition.solve(rhs);need(sol.allFinite(),"nonfinite current KKT hint");const double residual=(K*sol-rhs).lpNorm<Eigen::Infinity>();need(residual<=1e-10,"current KKT hint residual gate");const Eigen::VectorXd direction=sol.head(n);int negative=-1;double min_lambda=0;for(int j=0;j<k;++j)if(sol(n+j)<min_lambda){min_lambda=sol(n+j);negative=j;}
 Event event;event.iteration=iteration;event.active_count=k;event.min_multiplier=min_lambda;event.kkt_residual=residual;event.stationarity=(K.topRows(n)*sol-rhs.head(n)).lpNorm<Eigen::Infinity>();
 if(direction.lpNorm<Eigen::Infinity>()<=1e-12){
  if(negative>=0&&min_lambda< -1e-12){out.events.push_back(event);out.faces.erase(out.faces.begin()+negative);continue;}
  out.dual.setZero();for(int j=0;j<k;++j)out.dual(out.faces[j].row)+=out.faces[j].side*sol(n+j);ax=A*out.primal;event.violation=std::max({0.,(lower-ax).maxCoeff(),(ax-upper).maxCoeff()});out.events.push_back(event);need(event.violation<=1e-12&&(H*out.primal+g+A.transpose()*out.dual).lpNorm<Eigen::Infinity>()<=1e-10,"current final hint primal/stationarity gates");within();out.complete=true;break;
 }
 double fraction=1;Face blocker{-1,1};const Eigen::VectorXd travel=A*direction;
 for(int r=0;r<m;++r){bool active=false;for(const auto& f:out.faces)if(f.row==r){active=true;break;}if(active)continue;double step=2;int side=1;
  if(travel(r)>1e-14)step=(upper(r)-ax(r))/travel(r);else if(travel(r)<-1e-14){step=(lower(r)-ax(r))/travel(r);side=-1;}
  need(std::isfinite(step)&&step>=-1e-10,"invalid feasible-current boundary fraction");if(step<0)step=0; // optimizer path fraction only; never clips proposed controls
  if(step<fraction){fraction=step;blocker={r,side};}
 }
 out.primal+=fraction*direction;need(out.primal.allFinite(),"finite current hint face step");ax=A*out.primal;event.worst_row=blocker.row;event.violation=std::max({0.,(lower-ax).maxCoeff(),(ax-upper).maxCoeff()});need(event.violation<=1e-12,"feasible face search left current bounds");out.events.push_back(event);
 if(blocker.row>=0){need(k<n,"current active face cap before append");out.faces.push_back(blocker);}
 }
 need(out.complete,"current numeric iteration cap512");within();
 }catch(const std::exception& e){out.complete=false;out.error=e.what();}return out;
}
}
