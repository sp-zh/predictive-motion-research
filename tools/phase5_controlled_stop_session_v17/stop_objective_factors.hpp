#pragma once
#include <Eigen/Core>
#include <stdexcept>
namespace phase5_stop_objective_factors_v1 {
struct Rows {Eigen::Matrix<double,8,160> matrix;Eigen::Matrix<double,8,1> offset;};
inline Rows fromBoundary(const Eigen::MatrixXd& map,const Eigen::VectorXd& constant){if(map.rows()!=30||map.cols()!=160||constant.size()!=30||!map.allFinite()||!constant.allFinite())throw std::invalid_argument("stop factor finite actual boundary map shape");Rows r;r.matrix.topRows<7>()=map.middleRows(21,7);r.matrix.row(7)=map.row(29);r.offset.head<7>()=constant.segment(21,7);r.offset(7)=constant(29);return r;}
}
