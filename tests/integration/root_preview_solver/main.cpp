// Independent nonzero-state LQ optimum and separated-history interval oracle.
#include <predictive_motion_control/predictive.hpp>
#include <iostream>
#include <cmath>
#include <stdexcept>
using namespace predictive_motion::control;
PreviewInput fixture(bool lifted){
  PreviewInput in;in.lifted=lifted;in.initial={Eigen::VectorXd::Constant(1,1.2),Eigen::VectorXd::Constant(1,.05),.2,.1};
  in.mesh={1,1};in.nominal=Eigen::VectorXd::Zero(4);
  in.previous_acceleration=in.previous_model_acceleration=Eigen::VectorXd::Zero(1);
  in.accepted_position=in.initial.q;in.accepted_velocity=in.initial.v;
  in.limits.lower=Eigen::VectorXd::Constant(1,-10);in.limits.upper=-in.limits.lower;
  in.limits.velocity=Eigen::VectorXd::Constant(1,10);in.limits.acceleration=Eigen::VectorXd::Constant(1,100);
  in.limits.jerk=Eigen::VectorXd::Constant(1,1e6);in.limits.posture=Eigen::VectorXd::Zero(1);
  in.limits.position_margin=0;in.limits.progress_speed=10;in.limits.progress_acceleration=100;in.limits.progress_jerk=1e6;
  in.joint_trust=in.progress_trust=10;in.terminal_stop=false;in.weights={.5,.5,.05,0,0,0,0};return in;
}
ScpOptions options(){ScpOptions o;o.max_iterations=3;o.wall_limit=2;o.violation_tolerance=1e-7;
  o.qp.absolute_tolerance=1e-10;o.qp.relative_tolerance=1e-10;o.qp.acceptance_tolerance=1e-8;
  o.qp.max_iterations=20000;o.qp.time_limit_seconds=2;o.qp.max_state_age_seconds=2;return o;}
int main(){try{
  double error=0;int cases=0;
  for(bool lifted:{false,true}){
    auto in=fixture(lifted);auto linearize=[](const std::vector<PreviewState>& xs){std::vector<PreviewStage> out;
      for(int k=0;k<int(xs.size());++k){PreviewStage s;s.residual=Eigen::VectorXd::Constant(1,xs[k].q(0)-1.8);
        s.joint_derivative=Eigen::MatrixXd::Ones(1,1);s.path_derivative=Eigen::VectorXd::Zero(1);
        if(k+1<int(xs.size()))s.tracking_multiplier=s.velocity_multiplier=0;out.push_back(s);}return out;};
    auto result=solvePreview(in,linearize,[](const auto&,const auto&){return 0.;},options());
    if(result.status!=QpStatus::Solved||result.controls.size()!=4||result.states.size()!=3)throw std::runtime_error("Analytic optimum solve failed");
    error=std::max({error,std::abs(result.controls(0)-119./292),std::abs(result.controls(2)+111./292)});
    if(error>1e-7)throw std::runtime_error("Nonzero-state optimum mismatch");++cases;
    // Shifted-state/history intervals: shared-center [.02,.18] is disjoint
    // from actual-command interval [.22,.38]; model-center .3 admits .3.
    in=fixture(lifted);in.mesh={.04,.04};in.initial={Eigen::VectorXd::Zero(1),Eigen::VectorXd::Constant(1,.0092),0,0};
    in.accepted_position=in.initial.q;in.accepted_velocity=Eigen::VectorXd::Constant(1,.01);
    in.previous_acceleration=Eigen::VectorXd::Constant(1,.1);in.previous_model_acceleration=Eigen::VectorXd::Constant(1,.3);
    in.limits.acceleration(0)=1;in.limits.jerk(0)=20;in.weights={0,0,.05,0,0,0,0};
    Eigen::VectorXd candidate(4);candidate<<.3,0,.3,0;
    if(previewLimitViolation(in,candidate)>1e-10)throw std::runtime_error("Separated history rejects known feasible candidate");++cases;
    auto stages=std::vector<PreviewStage>(3);for(auto& s:stages){s.residual=Eigen::VectorXd::Zero(1);s.path_derivative=Eigen::VectorXd::Zero(1);s.joint_derivative=Eigen::MatrixXd::Zero(1,1);}
    auto separated=assemblePreview(in,stages);auto qpo=options().qp;
    auto solved=solveQpCertified(separated.qp,qpo,separated.nominal_decision,separated.convex_factor);
    if(solved.status!=QpStatus::Solved)throw std::runtime_error("Separated interval problem not solved");++cases;
    in.previous_model_acceleration=in.previous_acceleration;auto shared=assemblePreview(in,stages);
    auto rejected=solveQpCertified(shared.qp,qpo,shared.nominal_decision,shared.convex_factor);
    if(rejected.status!=QpStatus::PrimalInfeasible||rejected.velocity.size())throw std::runtime_error("Shared interval contradiction not explicit");++cases;
  }
  std::cout.precision(17);std::cout<<"ROOT_PREVIEW_SOLVER_PASS analytic_fixture_checks="<<cases<<" nonzero_state_control_error="<<error<<'\n';return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
