#include "public_coupled_derivative_model.hpp"
#include <pinocchio/parsers/mjcf.hpp>
#include <pinocchio/algorithm/rnea-derivatives.hpp>
#include <Eigen/Cholesky>
#include <Eigen/Eigenvalues>
#include <yaml-cpp/yaml.h>
#include <algorithm>
#include <cmath>
#include <stdexcept>
namespace phase5_public_coupled_derivative {
namespace {
void need(bool x,const char* msg){if(!x)throw std::invalid_argument(msg);}
Eigen::VectorXd read(const YAML::Node& c,const char* key,int n) {
 auto a=c[key];need(a.IsSequence() && int(a.size())==n,"derivative constant dimensions");Eigen::VectorXd v(n);
 for(int j=0;j<n;++j){v(j)=a[j].as<double>();}need(v.allFinite(),"finite derivative constants");return v;
}
Eigen::MatrixXd shape(const Eigen::VectorXd& v,int n){Eigen::MatrixXd m(7,n);for(int j=0;j<7;++j)for(int k=0;k<n;++k)m(j,k)=v(j*n+k);return m;}
ClipBranch clip(double x,double lo,double hi,bool enabled) {
 ClipBranch b;b.enabled=enabled;b.input=x;b.lower=lo;b.upper=hi;b.output=x;
 if(enabled){b.output=std::clamp(x,lo,hi);b.side=x<lo?-1:x>hi?1:0;b.slope=b.side==0?1:0;b.margin=b.side==-1?lo-x:b.side==1?x-hi:std::min(x-lo,hi-x);need(std::isfinite(b.margin),"finite clip margin arithmetic");}
 return b;
}
Eigen::MatrixXd solve(const Eigen::MatrixXd& A,const Eigen::MatrixXd& b,Result& out) {
 need(A.rows()>0 && A.rows()==A.cols() && A.rows()==b.rows() && A.allFinite() && b.allFinite(),"finite derivative solve dimensions/intermediates");
 Eigen::SelfAdjointEigenSolver<Eigen::MatrixXd> eig(A);
 need(eig.info()==Eigen::Success && eig.eigenvalues().allFinite() && eig.eigenvalues()(0)>0,"derivative solve SPD eigenvalues");double cond=eig.eigenvalues().tail(1)(0)/eig.eigenvalues()(0);
 need(std::isfinite(cond) && cond<=Model::max_condition,"derivative solve condition unsupported");out.solve_conditions.push_back(cond);
 Eigen::LLT<Eigen::MatrixXd> fac(A);need(fac.info()==Eigen::Success && fac.matrixL().toDenseMatrix().allFinite(),"derivative finite LLT");Eigen::MatrixXd x=fac.solve(b);
 need(fac.info()==Eigen::Success && x.allFinite(),"derivative solve finite result");Eigen::MatrixXd product=A*x,res=product-b;
 double scale=1+A.cwiseAbs().maxCoeff()*x.cwiseAbs().maxCoeff()*A.cols()+b.cwiseAbs().maxCoeff();
 need(product.allFinite() && res.allFinite() && std::isfinite(scale),"derivative residual arithmetic finite");double r=res.cwiseAbs().maxCoeff()/scale;
 need(std::isfinite(r) && r<=Model::residual_limit,"derivative scaled solve residual");out.solve_residuals.push_back(r);return x;
}
}
struct Model::Impl {
 phase5_public_coupled_v2::Model base;pinocchio::Model model;std::unique_ptr<pinocchio::Data> data;
 Eigen::VectorXd kp,bias0,biasq,biasv,passive,eta;
 std::array<Eigen::MatrixXd,3> ranges;std::array<Eigen::VectorXd,3> flags;
 Impl(const std::string& xml,const std::string& constants):base(xml,constants) {
  auto c=YAML::LoadFile(constants);auto gains=shape(read(c,"gainprm",70),10),bias=shape(read(c,"biasprm",70),10);kp=gains.col(0);bias0=bias.col(0);biasq=bias.col(1);biasv=bias.col(2);passive=read(c,"passive_damping",7);eta=read(c,"friction_bounds",7);
  const char* rn[]={"control_range","actuator_force_range","joint_actuator_force_range"};const char* fn[]={"control_limited","actuator_force_limited","joint_actuator_force_limited"};
  for(int k=0;k<3;++k){ranges[k]=shape(read(c,rn[k],14),2);flags[k]=read(c,fn[k],7);}
  pinocchio::mjcf::buildModel(xml,model);auto meta=base.metadata();need(model.nq==7 && model.nv==7 && model.names.size()==8,"derivative model dimension mapping");
  for(int j=0;j<7;++j)need(model.names[j+1]==meta.joint_names[j] && model.joints[j+1].idx_q()==j && model.joints[j+1].idx_v()==j && model.joints[j+1].nq()==1 && model.joints[j+1].nv()==1,"derivative scalar joint mapping");
  need((model.armature.array()==meta.armature.array()).all(),"derivative armature identity/no addition");for(int j=0;j<int(model.inertias.size());++j)need(model.inertias[j].mass()==meta.masses(j),"derivative body/tool mass identity");
  model.gravity.linear()=meta.gravity;data=std::make_unique<pinocchio::Data>(model);
 }
 void rnea(const Eigen::VectorXd& q,const Eigen::VectorXd& v,const Eigen::VectorXd& a,Eigen::MatrixXd& dq,Eigen::MatrixXd& dv,Eigen::MatrixXd& da) {
  // SDK requires zero outputs; only upper da is supplied. Armature added once by SDK.
  dq=Eigen::MatrixXd::Zero(7,7);dv=Eigen::MatrixXd::Zero(7,7);da=Eigen::MatrixXd::Zero(7,7);
  pinocchio::computeRNEADerivatives(model,*data,q,v,a,dq,dv,da);da=Eigen::MatrixXd(da.selfadjointView<Eigen::Upper>());
  need(dq.allFinite() && dv.allFinite() && da.allFinite() && data->tau.allFinite(),"finite RNEA derivatives/torque");
 }
};
Model::Model(const std::string& xml,const std::string& constants):impl_(std::make_unique<Impl>(xml,constants)){}
Model::~Model()=default;
phase5_public_coupled_v2::ModelMetadata Model::metadata() const{return impl_->base.metadata();}
Result Model::step(const Eigen::VectorXd& q,const Eigen::VectorXd& v,const Eigen::VectorXd& C) {
 Result out;auto& s=*impl_;
 try {
  out.value=s.base.step(q,v,C);out.value_success=true;auto& val=out.value;auto meta=s.base.metadata();
  need(val.friction.original_kkt<=residual_limit,"base original KKT gate");Eigen::VectorXd force_slope(7),control_slope(7);
  for(int j=0;j<7;++j) {
   auto c=clip(C(j),s.ranges[0](j,0),s.ranges[0](j,1),s.flags[0](j)!=0);out.control.push_back(c);control_slope(j)=c.slope;
   double raw=s.kp(j)*c.output+s.bias0(j)+s.biasq(j)*q(j)+s.biasv(j)*v(j);need(std::isfinite(raw),"finite derivative affine actuator arithmetic");
   auto act=clip(raw,s.ranges[1](j,0),s.ranges[1](j,1),s.flags[1](j)!=0);out.actuator.push_back(act);
   auto joint=clip(act.output,s.ranges[2](j,0),s.ranges[2](j,1),s.flags[2](j)!=0);out.joint_force.push_back(joint);force_slope(j)=act.slope*joint.slope;
   need(c.output==val.controls(j) && joint.output==val.actuator(j),"derivative/base exact nested clamp values");
  }
  out.friction_gradient=val.H*val.friction.force+val.ell;out.friction_margin=Eigen::VectorXd::Zero(7);need(out.friction_gradient.allFinite(),"finite original friction gradient");std::vector<int> free;
  bool stable=true;
  for(int j=0;j<7;++j) {
   stable=stable && (!out.control[j].enabled || out.control[j].margin>control_margin) && (!out.actuator[j].enabled || out.actuator[j].margin>force_margin) && (!out.joint_force[j].enabled || out.joint_force[j].margin>force_margin);
   double f=val.friction.force(j),e=s.eta(j),g=out.friction_gradient(j);int exact=e==0?2:f<=-e?-1:f>=e?1:0;
   need(exact==val.friction.branches[j],"exact base friction side labels");
   if(exact==0){out.friction_margin(j)=e-std::abs(f);stable=stable && out.friction_margin(j)>friction_margin && std::abs(g)<=residual_limit;free.push_back(j);}
   else if(exact==2){need(f==0,"fixed zero friction force");out.friction_margin(j)=0;}
   else{out.friction_margin(j)=exact==-1?g:-g;stable=stable && out.friction_margin(j)>gradient_margin;}
  }
  need(stable,"unsupported weak/near friction or nested clamp threshold; value retained, no unique Jacobian");
  Eigen::MatrixXd Mcheck,dv_dummy;s.rnea(q,v,Eigen::VectorXd::Zero(7),out.nq,out.nv,Mcheck);
  need((s.data->tau-val.bias).cwiseAbs().maxCoeff()<=1e-10 && (Mcheck-val.M).cwiseAbs().maxCoeff()<=1e-10,"RNEA baseline torque/M matches frozen base including armature");
  out.mass_q.assign(7,Eigen::MatrixXd::Zero(7,7));
  for(int k=0;k<7;++k){Eigen::VectorXd basis=Eigen::VectorXd::Zero(7);basis(k)=1;Eigen::MatrixXd dq,da;s.rnea(q,v,basis,dq,dv_dummy,da);Eigen::MatrixXd contraction=dq-out.nq;need(contraction.allFinite(),"finite mass derivative contraction");for(int j=0;j<7;++j)out.mass_q[j].col(k)=contraction.col(j);}
  for(auto& dm:out.mass_q){dm=Eigen::MatrixXd(dm.selfadjointView<Eigen::Upper>());need(dm.allFinite(),"finite symmetric CRBA mass derivative");}
  out.smooth_jacobian=Eigen::MatrixXd::Zero(7,21);
  out.smooth_jacobian.leftCols(7)=(force_slope.cwiseProduct(s.biasq)).asDiagonal().toDenseMatrix()-out.nq;
  out.smooth_jacobian.middleCols(7,7)=(force_slope.cwiseProduct(s.biasv)).asDiagonal().toDenseMatrix()-s.passive.asDiagonal().toDenseMatrix()-out.nv;
  out.smooth_jacobian.rightCols(7)=(force_slope.cwiseProduct(s.kp).cwiseProduct(control_slope)).asDiagonal();need(out.smooth_jacobian.allFinite(),"finite smooth force Jacobian");
  // Match explicit QP Hessian symmetrization; original-H KKT remains the guard.
  Eigen::MatrixXd Hsym=.5*(val.H+val.H.transpose());need(Hsym.allFinite(),"finite symmetrized Hessian");
  (void)solve(val.M,Eigen::MatrixXd::Identity(7,7),out);(void)solve(Hsym,Eigen::MatrixXd::Identity(7,7),out);
  Eigen::MatrixXd rhs=val.W*out.smooth_jacobian;
  for(int j=0;j<7;++j){Eigen::MatrixXd dw=-val.W*out.mass_q[j]*val.W;Eigen::MatrixXd dh=.5*(dw+dw.transpose());Eigen::VectorXd d=dw*val.smooth+dh*val.friction.force;need(dw.allFinite() && dh.allFinite() && d.allFinite(),"finite inverse/Hessian/friction derivative arithmetic");rhs.col(j)+=d;rhs(j,j+7)+=meta.B(j);}
  need(rhs.allFinite(),"finite friction derivative RHS");out.friction_jacobian=Eigen::MatrixXd::Zero(7,21);
  if(!free.empty()){Eigen::MatrixXd Hff(free.size(),free.size()),rf(free.size(),21);for(int i=0;i<int(free.size());++i){rf.row(i)=-rhs.row(free[i]);for(int j=0;j<int(free.size());++j)Hff(i,j)=Hsym(free[i],free[j]);}Eigen::MatrixXd df=solve(Hff,rf,out);for(int i=0;i<int(free.size());++i)out.friction_jacobian.row(free[i])=df.row(i);}
  Eigen::MatrixXd implicit=val.M;implicit.diagonal()+=h*meta.damping;Eigen::VectorXd acceleration=solve(implicit,val.smooth+val.friction.force,out);
  Eigen::MatrixXd arhs=out.smooth_jacobian+out.friction_jacobian;
  for(int j=0;j<7;++j)arhs.col(j)-=out.mass_q[j]*acceleration;
  need(arhs.allFinite(),"finite implicit acceleration derivative RHS");out.acceleration_jacobian=solve(implicit,arhs,out);out.jacobian=Eigen::MatrixXd::Zero(14,21);out.jacobian.bottomRows(7)=h*out.acceleration_jacobian;out.jacobian.bottomRows(7).middleCols(7,7).diagonal().array()+=1.;out.jacobian.topRows(7)=h*out.jacobian.bottomRows(7);out.jacobian.topRows(7).leftCols(7).diagonal().array()+=1.;need(out.jacobian.allFinite(),"finite transition Jacobian");out.jacobian_success=true;
 }catch(const std::exception& e){out.error=e.what();}
 return out;
}
}
