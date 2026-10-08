#include "public_coupled_model.hpp"
#include <Eigen/Cholesky>
#include <algorithm>
#include <cmath>
#include <stdexcept>

namespace phase5_public_coupled_v2 {
namespace {
constexpr double tolerance = 1e-10;
void require(bool condition, const char* message) {
  if (!condition) throw std::invalid_argument(message);
}
Eigen::VectorXd solve(const Eigen::MatrixXd& A, const Eigen::VectorXd& b) {
  require(A.allFinite() && b.allFinite(), "nonfinite box linear-system input");
  Eigen::LLT<Eigen::MatrixXd> factor(A);
  require(factor.info() == Eigen::Success && factor.matrixL().toDenseMatrix().allFinite(),
          "box Hessian not finite SPD");
  Eigen::VectorXd x = factor.solve(b);
  require(factor.info() == Eigen::Success && x.allFinite(), "nonfinite box linear solve");
  Eigen::VectorXd product=A*x,residual=product-b;
  double scale=1+A.cwiseAbs().maxCoeff()*x.cwiseAbs().maxCoeff()*A.cols()+b.cwiseAbs().maxCoeff();
  require(product.allFinite() && residual.allFinite() && std::isfinite(scale),"nonfinite box solve residual");
  require(residual.cwiseAbs().maxCoeff()/scale<=tolerance,"box linear solve residual");
  return x;
}
}  // namespace
BoxResult solveFrictionBox(const Eigen::MatrixXd& H, const Eigen::VectorXd& ell,
                          const Eigen::VectorXd& eta) {
  int n = ell.size();
  require(n > 0 && n <= 7 && H.rows() == n && H.cols() == n && eta.size() == n,
          "box dimension (supported n1..7)");
  require(H.allFinite() && ell.allFinite() && eta.allFinite() && (eta.array() >= 0).all(),
          "box finite input/nonnegative bound");
  Eigen::MatrixXd difference = H-H.transpose();
  require(difference.allFinite() && difference.cwiseAbs().maxCoeff() <= tolerance,
          "asymmetric box Hessian");
  Eigen::MatrixXd symmetric = .5*(H+H.transpose());
  require(symmetric.allFinite(), "nonfinite symmetrized box Hessian");
  Eigen::VectorXd lower = -eta, upper = eta, x = solve(symmetric, -ell);
  std::vector<int> status(n, 0);
  for (int j=0; j<n; ++j) {
    x(j) = std::clamp(x(j), lower(j), upper(j));
    if (x(j) <= lower(j)) status[j] = -1;
    if (x(j) >= upper(j)) status[j] = 1;
    if (eta(j) == 0) status[j] = 2;
  }
  for (int iteration=1; iteration<=100; ++iteration) {
    std::vector<int> free, bound;
    for (int j=0; j<n; ++j) (status[j] == 0 ? free : bound).push_back(j);
    if (!free.empty()) {
      int count = free.size(); Eigen::MatrixXd block(count,count); Eigen::VectorXd rhs(count);
      for (int i=0; i<count; ++i) {
        rhs(i) = -ell(free[i]);
        for (int j : bound) rhs(i) -= symmetric(free[i],j)*x(j);
        for (int j=0; j<count; ++j) block(i,j) = symmetric(free[i],free[j]);
      }
      Eigen::VectorXd target = solve(block,rhs), direction(count);
      double alpha = 1; std::vector<double> ratios(count, 2); std::vector<int> sides(count,0);
      for (int j=0; j<count; ++j) {
        int index = free[j]; direction(j) = target(j)-x(index);
        require(std::isfinite(direction(j)), "nonfinite box direction");
        if (target(j) < lower(index)) {ratios[j]=(lower(index)-x(index))/direction(j);sides[j]=-1;}
        if (target(j) > upper(index)) {ratios[j]=(upper(index)-x(index))/direction(j);sides[j]=1;}
        require(std::isfinite(ratios[j]), "nonfinite box ratio");
        alpha = std::min(alpha,ratios[j]);
      }
      if (alpha < 1) {
        for (int j=0; j<count; ++j) {
          int index=free[j];double moved=x(index)+std::max(0.,alpha)*direction(j);
          require(std::isfinite(moved), "nonfinite box line-search point");
          x(index)=std::clamp(moved,lower(index),upper(index));
        }
        for (int j=0; j<count; ++j) if (ratios[j] <= alpha+1e-14) {
          int index=free[j];status[index]=sides[j];x(index)=sides[j]<0 ? lower(index) : upper(index);
        }
        continue;
      }
      for (int j=0; j<count; ++j) x(free[j])=target(j);
    }
    Eigen::VectorXd gradient=symmetric*x+ell;
    require(gradient.allFinite(), "nonfinite box gradient");
    double worst=0;int release=-1;
    for (int j=0; j<n; ++j) {
      double bad=status[j]==-1 ? std::max(-gradient(j),0.) : status[j]==1 ? std::max(gradient(j),0.) : 0.;
      if (bad > worst) {worst=bad;release=j;}
    }
    if (worst > tolerance) {status[release]=0;continue;}
    Eigen::VectorXd original=H*x+ell;
    require(x.allFinite() && original.allFinite(), "nonfinite original box KKT");
    double violation=0;std::vector<int> labels(n,0);
    for (int j=0; j<n; ++j) {
      // True bound sides do not overlap for positive eta, even subnormals.
      // At an exact bound with zero gradient, report that bound side.
      if (eta(j)==0) labels[j]=2;
      else if (x(j)<=lower(j)) labels[j]=-1;
      else if (x(j)>=upper(j)) labels[j]=1;
      double stationarity=labels[j]==0 ? std::abs(original(j)) : labels[j]==-1 ? std::max(-original(j),0.) : labels[j]==1 ? std::max(original(j),0.) : 0.;
      violation=std::max({violation,stationarity,lower(j)-x(j),x(j)-upper(j)});
    }
    require(std::isfinite(violation) && violation<=tolerance, "original box KKT failure");
    return {x,labels,iteration,violation};
  }
  throw std::runtime_error("coupled box active-face iteration limit");
}
}  // namespace phase5_public_coupled_v2
