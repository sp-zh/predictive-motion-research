#pragma once
#include <Eigen/Core>
#include <cmath>
#include <stdexcept>
#include <vector>

namespace phase5_local_model {
using Vector=Eigen::VectorXd;using Matrix=Eigen::MatrixXd;
constexpr double command_dt=.004,physical_dt=.002;
struct Model {
 Vector mass,bias,kp,damping,friction,impedance,decay,q_min,q_max,error_min,error_max;
 double velocity_abs_max=0;
 int n()const{return int(mass.size());}
 void validate()const {
  int count=n();if(count<1)throw std::invalid_argument("empty soft servo model");
  for(const auto* v:{&mass,&bias,&kp,&damping,&friction,&impedance,&decay,&q_min,&q_max,&error_min,&error_max})
   if(v->size()!=count||!v->allFinite())throw std::invalid_argument("model dimension or nonfinite parameter");
  if((mass.array()<=0).any()||(kp.array()<=0).any()||(damping.array()<0).any()||(friction.array()<0).any()||
     (impedance.array()<=0).any()||(impedance.array()>1).any()||(decay.array()<=0).any()||
     (q_min.array()>q_max.array()).any()||(error_min.array()>error_max.array()).any()||
     !std::isfinite(velocity_abs_max)||velocity_abs_max<=0)throw std::invalid_argument("invalid soft model bounds");
 }
 void domain(const Vector& z)const {
  validate();
  int count=n();if(z.size()!=4*count+2||!z.allFinite())throw std::invalid_argument("state dimension or nonfinite");
  Vector q=z.head(count),v=z.segment(count,count),e=z.segment(2*count,count)-q;
  if((q.array()<q_min.array()).any()||(q.array()>q_max.array()).any()||
     (v.array().abs()>velocity_abs_max).any()||(e.array()<error_min.array()).any()||
     (e.array()>error_max.array()).any()||z(4*count)<0||z(4*count)>1||z(4*count+1)<0||z(4*count+1)>.2)
   throw std::domain_error("initial or forecast state outside frozen local model domain");
 }
};
struct Transition {Vector state,defect;Matrix A,B;std::vector<std::vector<int>> branches;int clip_equalities=0;};
// All inputs causal: measured q/v and prior accepted c/w are distinct.
// Pure empirical model, no real plant rollouts and no performance certificate.
inline Transition cycle(const Vector& initial,const Vector& control,const Model& model) {
 model.validate();model.domain(initial);int n=model.n(),nx=4*n+2,nu=n+1;
 if(control.size()!=nu||!control.allFinite())throw std::invalid_argument("control dimension or nonfinite");
 Transition out;out.A=Matrix::Identity(nx,nx);out.B=Matrix::Zero(nx,nu);out.defect=Vector::Zero(nx);
 out.A.block(2*n,3*n,n,n)=command_dt*Matrix::Identity(n,n);
 out.B.block(2*n,0,n,n)=command_dt*command_dt*Matrix::Identity(n,n);
 out.B.block(3*n,0,n,n)=command_dt*Matrix::Identity(n,n);
 out.A(nx-2,nx-1)=command_dt;out.B(nx-2,n)=.5*command_dt*command_dt;out.B(nx-1,n)=command_dt;
 Vector current=initial;
 current.segment(3*n,n)+=command_dt*control.head(n);
 current.segment(2*n,n)+=command_dt*current.segment(3*n,n);
 current(nx-2)+=command_dt*initial(nx-1)+.5*command_dt*command_dt*control(n);
 current(nx-1)+=command_dt*control(n);
 for(int sub=0;sub<2;++sub){
  model.domain(current);Vector next=current;Matrix P=Matrix::Identity(nx,nx);std::vector<int> branches;
  for(int j=0;j<n;++j){
   double q=current(j),v=current(n+j),c=current(2*n+j),m=model.mass(j),D=model.damping(j),k=model.kp(j);
   double smooth=k*(c-q)-D*v+model.bias(j);
   double drive=model.impedance(j)*(smooth+m*model.decay(j)*v),eta=model.friction(j),force;
   int branch=0;if(drive>=eta){force=-eta;branch=1;}else if(drive<=-eta){force=eta;branch=-1;}else force=-drive;
   if(std::abs(drive)==eta)++out.clip_equalities;
   double gain=physical_dt/(m+physical_dt*D),inside=branch==0?1.:0.;
   double dvq=-gain*k*(1-model.impedance(j)*inside);
   double dvv=1-gain*((1-model.impedance(j)*inside)*D+model.impedance(j)*inside*m*model.decay(j));
   next(n+j)=v+gain*(smooth+force);next(j)=q+physical_dt*next(n+j);
   P(j,j)=1+physical_dt*dvq;P(j,n+j)=physical_dt*dvv;P(j,2*n+j)=-physical_dt*dvq;
   P(n+j,j)=dvq;P(n+j,n+j)=dvv;P(n+j,2*n+j)=-dvq;branches.push_back(branch);
  }
  Vector f=next-P*current;out.A=(P*out.A).eval();out.B=(P*out.B).eval();out.defect=(P*out.defect+f).eval();
  current=next;model.domain(current);out.branches.push_back(branches);
 }
 out.state=current;return out;
}
inline int periods(double duration) {
 if(!std::isfinite(duration)||duration<=0)throw std::invalid_argument("positive finite integer4ms mesh required");
 double count=std::round(duration/command_dt);
 if(count<1||count>100000||std::abs(duration-command_dt*count)>1e-12)throw std::invalid_argument("undefined4ms mesh remainder");
 return int(count);
}
inline Transition cell(const Vector& initial,const Vector& control,int count,const Model& model) {
 if(count<1||count>100000)throw std::invalid_argument("cell count");
 model.validate();model.domain(initial);
 if(control.size()!=model.n()+1||!control.allFinite())throw std::invalid_argument("control dimension or nonfinite");
 int nx=int(initial.size()),nu=int(control.size());Transition out;out.state=initial;out.A=Matrix::Identity(nx,nx);out.B=Matrix::Zero(nx,nu);out.defect=Vector::Zero(nx);
 for(int i=0;i<count;++i){auto t=cycle(out.state,control,model);out.A=(t.A*out.A).eval();out.B=(t.A*out.B+t.B).eval();out.defect=(t.A*out.defect+t.defect).eval();out.state=t.state;out.clip_equalities+=t.clip_equalities;out.branches.insert(out.branches.end(),t.branches.begin(),t.branches.end());}
 return out;
}
}
