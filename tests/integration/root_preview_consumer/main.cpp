// Independent closed-form affine maps and direct objective/history checks.
// All inputs are analytic fixtures, not simulated/physical research trials.
#include <predictive_motion_control/predictive.hpp>
#include <iostream>
#include <random>
#include <cmath>
#include <algorithm>
#include <stdexcept>
using namespace predictive_motion::control;
struct Reference {Eigen::VectorXd q,v;double s,r;};
Reference closedState(const PreviewInput& in,const Eigen::VectorXd& u,int k) {
  const int n=in.initial.q.size(),nu=n+1;
  double t=0;for(int j=0;j<k;++j)t+=in.mesh[j];
  Reference x{in.initial.q+t*in.initial.v,in.initial.v,in.initial.s+t*in.initial.r,in.initial.r};
  double start=0;
  for(int j=0;j<k;++j) {
    const double h=in.mesh[j],moment=h*(t-start-h/2);
    x.q+=moment*u.segment(j*nu,n);x.v+=h*u.segment(j*nu,n);
    x.s+=moment*u(j*nu+n);x.r+=h*u(j*nu+n);start+=h;
  }
  return x;
}
double directCost(const PreviewInput& in,const std::vector<PreviewStage>& stages,const Eigen::VectorXd& u) {
  int n=in.initial.q.size(),nu=n+1,N=in.mesh.size();double cost=0;
  for(int k=0;k<=N;++k) {
    auto x=closedState(in,u,k),nom=closedState(in,in.nominal,k);const auto& s=stages[k];
    Eigen::VectorXd e=s.residual+s.joint_derivative*(x.q-nom.q)+s.path_derivative*(x.s-nom.s);
    double h=in.mesh[k<N?k:N-1];
    cost+=h*(in.weights.tracking*s.tracking_multiplier*e.squaredNorm()
      +in.weights.velocity*s.velocity_multiplier*x.v.squaredNorm()
      +in.weights.posture*s.posture_multiplier*(x.q-in.limits.posture).squaredNorm());
    for(const auto& penalty:s.penalties) {
      double residual=penalty.value-penalty.target+penalty.gradient.dot(x.q-nom.q);
      cost+=h*penalty.weight*residual*residual;
    }
  }
  for(int k=0;k<N;++k) {
    Eigen::VectorXd previous(nu);double elapsed;
    if(k){previous=u.segment((k-1)*nu,nu);elapsed=in.mesh[k-1];}
    else{previous.head(n)=in.previous_model_acceleration;previous(n)=in.previous_progress_acceleration;elapsed=in.control_dt;}
    auto control=u.segment(k*nu,nu);
    cost+=in.mesh[k]*(in.weights.acceleration*control.squaredNorm()
      +in.weights.jerk*((control-previous)/elapsed).squaredNorm());
  }
  double end=closedState(in,u,N).s;
  return cost-in.weights.progress_reward*end+in.weights.terminal_progress*(end-1)*(end-1);
}
int main() {
  try {
    std::mt19937 rng(20261006);auto sample=[&]{return 2.*double(rng())/4294967295.-1.;};
    double map_error=0,cost_error=0,bridge_error=0,dynamics_error=0,certificate_error=0;int map_states=0,cost_samples=0;
    for(bool lifted:{false,true}) for(auto dimensions:std::vector<std::pair<int,int>>{{1,2},{3,5},{7,20}}) {
      int n=dimensions.first,N=dimensions.second,nu=n+1,nz=N*nu;
      PreviewInput in;in.lifted=lifted;in.initial.q=Eigen::VectorXd::NullaryExpr(n,[&]{return .2*sample();});
      in.initial.v=Eigen::VectorXd::NullaryExpr(n,[&]{return .03*sample();});in.initial.s=.1;in.initial.r=.02;
      for(int k=0;k<N;++k)in.mesh.push_back(.02+.02*double(k%3));
      in.accepted_position=in.initial.q.array()+.0001;in.accepted_velocity=in.initial.v.array()+.0001;
      in.previous_acceleration=Eigen::VectorXd::Constant(n,.01);in.previous_model_acceleration=Eigen::VectorXd::Constant(n,.03);in.previous_progress_acceleration=.002;
      in.nominal=Eigen::VectorXd::NullaryExpr(nz,[&]{return .1*sample();});in.weights={1.7,.3,.2,.01,.4,.5,.6};
      in.limits.lower=Eigen::VectorXd::Constant(n,-5);in.limits.upper=-in.limits.lower;
      in.limits.velocity=Eigen::VectorXd::Constant(n,2);in.limits.acceleration=Eigen::VectorXd::Constant(n,8);
      in.limits.jerk=Eigen::VectorXd::Constant(n,1000);in.limits.posture=Eigen::VectorXd::Constant(n,.05);
      in.joint_trust=1;in.progress_trust=1;in.terminal_stop=false;
      std::vector<PreviewStage> stages;
      for(int k=0;k<=N;++k) {
        PreviewStage s;s.residual=Eigen::VectorXd::NullaryExpr(6,[&]{return .1*sample();});
        s.joint_derivative=Eigen::MatrixXd::NullaryExpr(6,n,[&]{return sample();});
        s.path_derivative=Eigen::VectorXd::NullaryExpr(6,[&]{return sample();});
        s.tracking_multiplier=.5+.5*double(k%2);s.velocity_multiplier=.4+.2*double(k%3);s.posture_multiplier=.7;
        for(int j=0;j<3;++j) {
          PreviewPenalty penalty;penalty.value=.01*sample();penalty.target=.05;penalty.weight=3.+j;
          penalty.gradient=Eigen::RowVectorXd::NullaryExpr(n,[&]{return .03*sample();});s.penalties.push_back(penalty);
        }
        stages.push_back(s);
      }
      auto assembled=assemblePreview(in,stages);double constant=0;for(auto& term:assembled.terms)constant+=term.constant;
      Eigen::MatrixXd certified=assembled.convex_factor.transpose()*assembled.convex_factor;
      certificate_error=std::max(certificate_error,(certified-assembled.qp.hessian).cwiseAbs().maxCoeff()/std::max(1.,assembled.qp.hessian.cwiseAbs().maxCoeff()));
      for(int draw=0;draw<20;++draw) {
        Eigen::VectorXd u=Eigen::VectorXd::NullaryExpr(nz,[&]{return .1*sample();});
        Eigen::VectorXd decision=assembled.nominal_decision;decision.segment(assembled.controls_offset,nz)=u-assembled.controls_origin;
        if(lifted)for(int k=0;k<=N;++k) {
          auto ref=closedState(in,u,k);Eigen::VectorXd desired(2*n+2);desired<<ref.q,ref.v,ref.s,ref.r;
          for(int row=0;row<desired.size();++row) {
            int found=-1;for(int col=0;col<decision.size();++col)if(assembled.states[k].map(row,col)!=0) {if(found>=0)throw std::runtime_error("Unsupported state embedding");found=col;}
            if(found>=0)decision(found)=(desired(row)-assembled.states[k].offset(row))/assembled.states[k].map(row,found);
            else if(std::abs(desired(row)-assembled.states[k].offset(row))>1e-12)throw std::runtime_error("Fixed initial state embedding");
          }
        }
        if(lifted)for(int row=0;row<assembled.qp.lower.size();++row)if(assembled.qp.lower(row)==assembled.qp.upper(row))
          dynamics_error=std::max(dynamics_error,std::abs(assembled.qp.constraints.row(row).dot(decision)-assembled.qp.lower(row)));
        for(int k=0;k<=N;++k) {
          auto ref=closedState(in,u,k);Eigen::VectorXd expected(2*n+2);expected<<ref.q,ref.v,ref.s,ref.r;
          Eigen::VectorXd actual=assembled.states[k].offset+assembled.states[k].map*decision;
          map_error=std::max(map_error,(actual-expected).cwiseAbs().maxCoeff());++map_states;
        }
        double direct=directCost(in,stages,u);
        double polynomial=.5*decision.dot(assembled.qp.hessian*decision)+assembled.qp.gradient.dot(decision)+constant;
        cost_error=std::max(cost_error,std::abs(direct-polynomial)/std::max(1.,std::abs(direct)));++cost_samples;
      }
      int rows=0;
      for(int row=0;row<int(assembled.row_labels.size());++row)if(assembled.row_labels[row].rfind("first_command/history_intersection/",0)==0) {
        int j=rows++;double dt=in.control_dt,lo=in.limits.lower(j)+in.limits.position_margin,hi=in.limits.upper(j)-in.limits.position_margin;
        double lower=std::max({-in.limits.velocity(j),(lo-in.initial.q(j))/dt,(lo-in.accepted_position(j))/dt,
          in.accepted_velocity(j)-dt*in.limits.acceleration(j),in.accepted_velocity(j)+dt*in.previous_acceleration(j)-dt*dt*in.limits.jerk(j)});
        double upper=std::min({in.limits.velocity(j),(hi-in.initial.q(j))/dt,(hi-in.accepted_position(j))/dt,
          in.accepted_velocity(j)+dt*in.limits.acceleration(j),in.accepted_velocity(j)+dt*in.previous_acceleration(j)+dt*dt*in.limits.jerk(j)});
        Eigen::RowVectorXd expected=Eigen::RowVectorXd::Zero(assembled.qp.gradient.size());expected(assembled.controls_offset+j)=dt;
        bridge_error=std::max({bridge_error,(assembled.qp.constraints.row(row)-expected).cwiseAbs().maxCoeff(),
          std::abs(assembled.qp.lower(row)-(lower-in.initial.v(j)-dt*assembled.controls_origin(j))),std::abs(assembled.qp.upper(row)-(upper-in.initial.v(j)-dt*assembled.controls_origin(j)))});
      }
      if(rows!=n)throw std::runtime_error("First command row count");
    }
    if(map_error>1e-12||cost_error>1e-11||bridge_error>1e-12||dynamics_error>1e-12||certificate_error>1e-12)throw std::runtime_error("Independent math mismatch");
    std::cout.precision(17);std::cout<<"ROOT_PREVIEW_ASSEMBLY_PASS seed=20261006 map_states="<<map_states
      <<" cost_samples="<<cost_samples<<" map_error="<<map_error<<" relative_cost_error="<<cost_error<<" bridge_error="<<bridge_error<<" dynamics_equality_error="<<dynamics_error<<" convex_certificate_error="<<certificate_error<<'\n';
    return 0;
  } catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
