#pragma once
#include <Eigen/Core>
namespace predictive_motion::control {
inline bool measuredPositionSafe(const Eigen::VectorXd& q,
                                 const Eigen::VectorXd& lower,
                                 const Eigen::VectorXd& upper) {
  return q.size()>0 && q.size()==lower.size() && q.size()==upper.size()
      && q.allFinite() && lower.allFinite() && upper.allFinite()
      && (lower.array()<=upper.array()).all()
      && (q.array()>=lower.array()).all() && (q.array()<=upper.array()).all();
}
}
