#pragma once
#include <predictive_motion_control/reactive_qp.hpp>
namespace phase5_active_solver_forensics_v1 {
struct ForensicIterates {
 bool wrapper_attempted=false;
 unsigned native_solve_attempts=0;int raw_status=0;
 bool primal_present=false,dual_present=false;
 Eigen::VectorXd primal,dual;
 // No usable flag, candidate authorization, warmstart reuse or execution API.
};
predictive_motion::control::QpResult solveCertified(const predictive_motion::control::QpProblem&,const predictive_motion::control::QpOptions&,const Eigen::VectorXd&,const Eigen::SparseMatrix<double>&,ForensicIterates&);
predictive_motion::control::QpResult solveCertifiedPrimalDualGuess(const predictive_motion::control::QpProblem&,const predictive_motion::control::QpOptions&,const Eigen::VectorXd&,const Eigen::VectorXd&,const Eigen::SparseMatrix<double>&,ForensicIterates&);
}
