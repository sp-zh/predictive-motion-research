#pragma once
#include <Eigen/Core>
#include <algorithm>
#include <cmath>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>
namespace phase5_bounded_progress_seed_v1 {
struct Attempt {double epsilon=0,worst_violation=0;bool finite=false;};
struct Result {Eigen::VectorXd seed;Eigen::MatrixXd row_direction_bounds;std::vector<Attempt> attempts;std::size_t row_bounds_written=0;bool complete=false,changed=false;double epsilon=0,interval_lower=0,interval_upper=1e-6,initial_violation=0;std::string error;};
inline Result prepare(const Eigen::MatrixXd& A,const Eigen::VectorXd& lower,const Eigen::VectorXd& upper,const Eigen::VectorXd& nominal,const Eigen::VectorXd& scale){
 Result out;auto need=[](bool b,const char* message){if(!b)throw std::invalid_argument(message);};
 try{need(A.rows()>0&&A.rows()<=20000&&A.cols()==144&&lower.size()==A.rows()&&upper.size()==A.rows()&&nominal.size()==144&&scale.size()==144,"bounded initializer shapes before allocation");need(A.allFinite()&&lower.allFinite()&&upper.allFinite()&&nominal.allFinite()&&scale.allFinite()&&(scale.array()>0).all()&&(lower.array()<=upper.array()).all(),"finite bounded initializer arrays and positive scale");
  out.seed=nominal;const Eigen::VectorXd base=A*nominal;need(base.allFinite(),"finite nominal row values");out.initial_violation=std::max({0.,(lower-base).maxCoeff(),(base-upper).maxCoeff()});if(out.initial_violation<=1e-12){out.complete=true;return out;}
  Eigen::VectorXd direction=Eigen::VectorXd::Zero(144);for(int cell=0;cell<18;++cell)direction(8*cell+7)=1/scale(8*cell+7);need(direction.allFinite(),"finite freeprogress initializer direction");const Eigen::VectorXd travel=A*direction;need(travel.allFinite(),"finite initializer directional row values");out.row_direction_bounds=Eigen::MatrixXd::Zero(A.rows(),4);out.attempts.reserve(3);long double lo=0,hi=1e-6L;
  // Use exactly the existing1e-12 starting-guess allowance for ray bounds;
  // nominal/hint feasibility threshold and all original final gates unchanged.
  for(int row=0;row<A.rows();++row){long double rlo=0,rhi=1e-6L;const long double value=base(row),delta=travel(row);if(delta==0){need(lower(row)-base(row)<=1e-12&&base(row)-upper(row)<=1e-12,"initializer flat row infeasible; wholepolytope unknown");}else{rlo=(static_cast<long double>(lower(row))-1e-12L-value)/delta;rhi=(static_cast<long double>(upper(row))+1e-12L-value)/delta;if(delta<0)std::swap(rlo,rhi);need(std::isfinite(rlo)&&std::isfinite(rhi),"finite initializer interval endpoints");lo=std::max(lo,rlo);hi=std::min(hi,rhi);}const double encodedLower=static_cast<double>(rlo),encodedUpper=static_cast<double>(rhi);need(std::isfinite(encodedLower)&&std::isfinite(encodedUpper),"finite serializable row interval diagnostics");out.row_direction_bounds.row(row)<<base(row),travel(row),encodedLower,encodedUpper;++out.row_bounds_written;}
  out.interval_lower=static_cast<double>(lo);out.interval_upper=static_cast<double>(hi);need(std::isfinite(lo)&&std::isfinite(hi)&&lo>=0&&hi<=1e-6L&&lo<hi,"bounded initializer ray has no interior; wholepolytope unknown");
  const long double width=hi-lo,margin=std::min(1e-8L,width/4);const long double choices[3]={lo+margin,lo+width/2,hi-margin};
  for(long double choice:choices){const double epsilon=static_cast<double>(choice);need(std::isfinite(epsilon)&&epsilon>0&&epsilon<=1e-6,"finite declared optimizer initializer step");const Eigen::VectorXd seed=nominal+epsilon*direction;const Eigen::VectorXd values=A*seed;Attempt attempt;attempt.epsilon=epsilon;attempt.finite=seed.allFinite()&&values.allFinite();attempt.worst_violation=attempt.finite?std::max({0.,(lower-values).maxCoeff(),(values-upper).maxCoeff()}):std::numeric_limits<double>::infinity();out.attempts.push_back(attempt);if(attempt.finite&&attempt.worst_violation<=1e-12){out.seed=seed;out.complete=true;out.changed=true;out.epsilon=epsilon;return out;}}
  need(false,"bounded initializer recheck failed; retained attempts no tolerance change");
 }catch(const std::exception& e){out.complete=false;out.error=e.what();}return out;
}
// Only a NEW optimizer starting guess, before native solve. Does not change
// actual state, nominal Model invocation or returned native candidate. Original
// native/full14756SI/rounded200/half400/genuineB/privateC remain required.
}
