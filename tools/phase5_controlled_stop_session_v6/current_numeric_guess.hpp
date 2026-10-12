#pragma once
#include <Eigen/Core>
#include "working_face_basis.hpp"
#include <memory>
#include <algorithm>
#include <Eigen/LU>
#include <Eigen/Cholesky>
#include <chrono>
#include <cmath>
#include <stdexcept>
#include <vector>
#include <string>
namespace phase5_dynamic_numeric_v1 {
using Face=phase5_working_face_basis_v1::Face;
struct BoundaryEvent {int iteration=0,row=-1,side=1;double slack=0,outward_travel=0,raw_fraction=0;};
inline double feasibleBoundaryFraction(double slack,double positive_travel){if(!std::isfinite(slack)||!std::isfinite(positive_travel)||positive_travel<=0||slack< -1e-12)throw std::invalid_argument("invalid current feasibility slack/travel");if(slack<=0)return 0;if(slack>=positive_travel)return 1;const double fraction=slack/positive_travel;if(!std::isfinite(fraction)||fraction<0)throw std::invalid_argument("nonfinite current boundary fraction");return fraction;}
struct Event {int iteration=0,active_count=0,worst_row=-1;double violation=0,min_multiplier=0,stationarity=0,kkt_residual=0;};
struct RankEvent {int iteration=0,rank=0,dimension=0;double original_residual=0;};
struct KktSolution {Eigen::VectorXd value;int rank=0,dimension=0;double residual=0;};
inline KktSolution solveKkt(const Eigen::MatrixXd& K,const Eigen::VectorXd& rhs,int primal_dimension){
 auto need=[](bool b,const char* msg){if(!b)throw std::invalid_argument(msg);};need(K.rows()==K.cols()&&K.rows()==rhs.size()&&primal_dimension>0&&primal_dimension<=K.rows()&&K.allFinite()&&rhs.allFinite(),"finite original KKT shape");Eigen::FullPivLU<Eigen::MatrixXd> decomposition(K);KktSolution out;out.rank=decomposition.rank();out.dimension=K.rows();out.value=decomposition.solve(rhs);need(out.value.allFinite(),"nonfinite current KKT hint");out.residual=(K*out.value-rhs).lpNorm<Eigen::Infinity>();need(std::isfinite(out.residual)&&out.residual<=1e-10,"current KKT hint residual gate");if(out.rank<out.dimension){const Eigen::MatrixXd H=K.topLeftCorner(primal_dimension,primal_dimension);need((H-H.transpose()).cwiseAbs().maxCoeff()<=1e-12,"singular KKT needs original symmetric Hessian");Eigen::LLT<Eigen::MatrixXd> positive(H);need(positive.info()==Eigen::Success&&out.rank>=primal_dimension,"singular KKT needs positive Hessian and sufficient rank");const Eigen::MatrixXd L=positive.matrixL();need(L.allFinite()&&(L.diagonal().array()>0).all(),"singular KKT needs finite positive original LLT factor");}return out;
}
struct Result {Eigen::VectorXd primal,dual;std::vector<Face> faces;std::vector<Event> events;std::vector<BoundaryEvent> boundary_events;std::vector<RankEvent> rank_events;std::shared_ptr<phase5_working_face_basis_v1::Trace> working_face_trace;bool complete=false;std::string error;};
// Finite feasible-start primal active-set hint. It returns numerical x/y only;
// current native OSQP/full original SI/rounded history/value/private C are gates.
inline Result derive(const Eigen::MatrixXd& H,const Eigen::VectorXd& g,const Eigen::MatrixXd& A,const Eigen::VectorXd& lower,const Eigen::VectorXd& upper,const Eigen::VectorXd& seed=Eigen::VectorXd{},bool repair_working_faces=false){
 Result out;const auto started=std::chrono::steady_clock::now();try{const int n=g.size(),m=lower.size();auto need=[](bool ok,const char* why){if(!ok)throw std::invalid_argument(why);};
 need(n>0&&n<=144&&m>0&&m<=20000&&H.rows()==n&&H.cols()==n&&A.rows()==m&&A.cols()==n&&upper.size()==m,"bounded current numeric shapes");need(H.allFinite()&&g.allFinite()&&A.allFinite()&&lower.allFinite()&&upper.allFinite()&&(lower.array()<=upper.array()).all(),"finite current numeric matrix/bounds");
 auto within=[&](){need(std::chrono::duration<double>(std::chrono::steady_clock::now()-started).count()<=10,"current numeric wall cap10s including final scan/return");};
 if(repair_working_faces){out.working_face_trace=std::make_shared<phase5_working_face_basis_v1::Trace>();out.working_face_trace->basis.reserve(512);out.working_face_trace->endpoints.reserve(4096);}out.primal=seed.size()?seed:Eigen::VectorXd::Zero(n);need(out.primal.size()==n&&out.primal.allFinite(),"current matrix finite feasible-start hint shape");out.dual=Eigen::VectorXd::Zero(m);out.events.reserve(512);out.faces.reserve(n);out.boundary_events.reserve(1024);out.rank_events.reserve(512);Eigen::VectorXd ax=A*out.primal;need(ax.allFinite(),"finite current start row values");need((lower-ax).maxCoeff()<=1e-12&&(ax-upper).maxCoeff()<=1e-12,"current-matrix start infeasible; retained refusal, no projection");
 std::vector<unsigned char> previously_dropped;if(repair_working_faces)previously_dropped.assign(m,0);
 for(int iteration=0;iteration<512;++iteration){within();const int k=out.faces.size();Eigen::MatrixXd K=Eigen::MatrixXd::Zero(n+k,n+k);Eigen::VectorXd rhs=Eigen::VectorXd::Zero(n+k);K.topLeftCorner(n,n)=H;rhs.head(n)=-(H*out.primal+g);
 for(int j=0;j<k;++j){auto face=out.faces[j];K.block(n+j,0,1,n)=face.side*A.row(face.row);K.block(0,n+j,n,1)=face.side*A.row(face.row).transpose();}
 const auto solved=solveKkt(K,rhs,n);const Eigen::VectorXd& sol=solved.value;const double residual=solved.residual;if(solved.rank<solved.dimension){need(out.rank_events.size()<512,"finite singular KKT diagnostics cap");out.rank_events.push_back({iteration,solved.rank,solved.dimension,residual});}const Eigen::VectorXd direction=sol.head(n);int negative=-1;double min_lambda=0;for(int j=0;j<k;++j)if(sol(n+j)<min_lambda){min_lambda=sol(n+j);negative=j;}
 Event event;event.iteration=iteration;event.active_count=k;event.min_multiplier=min_lambda;event.kkt_residual=residual;event.stationarity=(K.topRows(n)*sol-rhs.head(n)).lpNorm<Eigen::Infinity>();
 if(direction.lpNorm<Eigen::Infinity>()<=1e-12){
  if(negative>=0&&min_lambda< -1e-12){out.events.push_back(event);out.faces.erase(out.faces.begin()+negative);continue;}
  out.dual.setZero();for(int j=0;j<k;++j)out.dual(out.faces[j].row)+=out.faces[j].side*sol(n+j);ax=A*out.primal;need(ax.allFinite(),"finite final/current row values");event.violation=std::max({0.,(lower-ax).maxCoeff(),(ax-upper).maxCoeff()});out.events.push_back(event);need(event.violation<=1e-12&&(H*out.primal+g+A.transpose()*out.dual).lpNorm<Eigen::Infinity>()<=1e-10,"current final hint primal/stationarity gates");within();out.complete=true;break;
 }
 double fraction=1;Face blocker{-1,1};Eigen::VectorXd full_point,full_values;if(repair_working_faces){full_point=out.primal+direction;need(full_point.allFinite(),"finite numerical full-step point");full_values=A*full_point;need(full_values.allFinite(),"finite allrow numerical full-step values");}const Eigen::VectorXd travel=A*direction;need(travel.allFinite(),"finite current hint outward travel");
 for(int r=0;r<m;++r){bool active=false;for(const auto& f:out.faces)if(f.row==r){active=true;break;}if(active)continue;
  if(repair_working_faces&&previously_dropped[r]&&phase5_working_face_basis_v1::endpointWithinExistingNumericDomain(full_values(r),lower(r),upper(r))){need(out.working_face_trace->endpoints.size()<4096,"finite previouslydropped fullendpoint diagnostics cap");out.working_face_trace->endpoints.push_back({iteration,r,ax(r),travel(r),full_values(r),lower(r),upper(r),std::max({0.,lower(r)-full_values(r),full_values(r)-upper(r)})});continue;}
  double step=2;int side=1;
  double slack=0,positive_travel=0;if(travel(r)>0){slack=upper(r)-ax(r);positive_travel=travel(r);}else if(travel(r)<0){slack=ax(r)-lower(r);positive_travel=-travel(r);side=-1;}
  if(positive_travel>0){if(slack<0){need(out.boundary_events.size()<1024,"finite current near-boundary diagnostic cap");out.boundary_events.push_back({iteration,r,side,slack,positive_travel,slack/positive_travel});}step=feasibleBoundaryFraction(slack,positive_travel);}
  need(std::isfinite(step)&&step>=0,"finite nonnegative optimizer boundary fraction"); // Existing1e-12 scaled-row feasibility allowance only; no controls are projected/clipped.

  if(step<fraction){fraction=step;blocker={r,side};}
 }
 out.primal+=fraction*direction;need(out.primal.allFinite(),"finite current hint face step");ax=A*out.primal;need(ax.allFinite(),"finite updated current row values");event.worst_row=blocker.row;event.violation=std::max({0.,(lower-ax).maxCoeff(),(ax-upper).maxCoeff()});need(event.violation<=1e-12,"feasible face search left current bounds");out.events.push_back(event);
 if(blocker.row>=0){
  if(repair_working_faces&&static_cast<int>(out.faces.size())==n){
   need(out.working_face_trace->basis.size()<512,"finite face basis diagnostics cap before allocation");auto reduced=phase5_working_face_basis_v1::reduce(A,out.faces,iteration,blocker.row,blocker.side);out.working_face_trace->basis.push_back(std::move(reduced));const auto& proof=out.working_face_trace->basis.back();need(proof.complete&&proof.error.empty(),proof.error.c_str());
   std::vector<Face> kept;kept.reserve(n);for(int j=0;j<n;++j)if(!std::binary_search(proof.kept_positions.begin(),proof.kept_positions.end(),j))previously_dropped[out.faces[j].row]=1;for(int position:proof.kept_positions)kept.push_back(out.faces[position]);out.faces=std::move(kept);
  }
  need(static_cast<int>(out.faces.size())<n,"current active face cap before append");out.faces.push_back(blocker);
 }
 }
 need(out.complete,"current numeric iteration cap512");within();
 }catch(const std::exception& e){out.complete=false;out.error=e.what();}return out;
}
}
