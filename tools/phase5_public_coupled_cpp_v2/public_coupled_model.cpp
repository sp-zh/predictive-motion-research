#include "public_coupled_model.hpp"
#include <Eigen/Cholesky>
#include <pinocchio/parsers/mjcf.hpp>
#include <pinocchio/algorithm/crba.hpp>
#include <pinocchio/algorithm/rnea.hpp>
#include <yaml-cpp/yaml.h>
#include <algorithm>
#include <cmath>
#include <stdexcept>

namespace phase5_public_coupled_v2 {
namespace {
constexpr double h=.002;
void require(bool condition,const std::string& message) {
  if (!condition) throw std::invalid_argument(message);
}
Eigen::VectorXd array(const YAML::Node& c,const std::string& name,int count) {
  auto node=c[name];require(node.IsSequence() && int(node.size())==count,"constant dimension "+name);
  Eigen::VectorXd out(count);
  for (int j=0;j<count;++j) out(j)=node[j].as<double>();
  require(out.allFinite(),"nonfinite constant "+name);return out;
}
double scalar(const YAML::Node& c,const std::string& name) {
  double x=c[name].as<double>();require(std::isfinite(x),"nonfinite constant "+name);return x;
}
bool allEqual(const Eigen::VectorXd& v,double x) {return (v.array()==x).all();}
Eigen::MatrixXd shaped(const Eigen::VectorXd& v,int columns) {
  Eigen::MatrixXd out(7,columns);for(int j=0;j<7;++j)for(int k=0;k<columns;++k)out(j,k)=v(j*columns+k);return out;
}
Eigen::MatrixXd solve(const Eigen::MatrixXd& A,const Eigen::MatrixXd& rhs,const char* name) {
  require(A.allFinite() && rhs.allFinite(),std::string("nonfinite ")+name+" input");
  Eigen::LLT<Eigen::MatrixXd> factor(A);
  require(factor.info()==Eigen::Success && factor.matrixL().toDenseMatrix().allFinite(),std::string(name)+" not finite SPD");
  Eigen::MatrixXd x=factor.solve(rhs);
  require(factor.info()==Eigen::Success && x.allFinite(),std::string("nonfinite ")+name+" solve");
  Eigen::MatrixXd product=A*x, residual=product-rhs;
  double scale=1+A.cwiseAbs().maxCoeff()*x.cwiseAbs().maxCoeff()*A.cols()+rhs.cwiseAbs().maxCoeff();
  require(product.allFinite() && residual.allFinite() && std::isfinite(scale),std::string("nonfinite ")+name+" residual");
  require(residual.cwiseAbs().maxCoeff()/scale<=1e-10,std::string(name)+" solve residual");return x;
}
}  // namespace
struct Model::Impl {
  pinocchio::Model model;
  std::unique_ptr<pinocchio::Data> data;
  Eigen::VectorXd kp,bias0,biasq,biasv,passive,D,eta,R,B;
  std::array<Eigen::MatrixXd,4> ranges;
  std::array<Eigen::VectorXd,4> flags;
  Impl(const std::string& xml,const std::string& constants) {
    auto c=YAML::LoadFile(constants);
    require(std::string(PINOCCHIO_VERSION)=="4.1.0" && c["version"].as<std::string>()=="3.3.7","pinned model versions");
    for (auto name:{"nq","nv","nu"}) require(scalar(c,name)==7,"fixed FR3 dimensions");
    require(scalar(c,"neq")==0 && scalar(c,"integrator")==3 && scalar(c,"timestep")==h,"model clock/constraints/integrator");
    for (auto name:{"disableflags","actuator_disablegroups","density","viscosity"}) require(scalar(c,name)==0,"unsupported public force setting");
    for (auto pair:{std::pair<const char*,int>{"wind",3},{"joint_stiffness",7},{"body_gravity_compensation",12}})
      require(allEqual(array(c,pair.first,pair.second),0),std::string("unsupported public force ")+pair.first);
    for (auto name:{"actuator_dyntype","actuator_gaintype","actuator_trntype"})require(allEqual(array(c,name,7),0),"unsupported affine actuator type");
    require(allEqual(array(c,"actuator_biastype",7),1),"unsupported affine actuator bias");
    auto ids=shaped(array(c,"actuator_trnid",14),2);
    for (int j=0;j<7;++j)require(ids(j,0)==j && ids(j,1)==-1,"actuator mapping");
    auto gain=shaped(array(c,"gainprm",70),10),bias=shaped(array(c,"biasprm",70),10),gear=shaped(array(c,"gear",42),6);
    require(allEqual(gear.col(0),1) && gear.rightCols(5).isZero(0) && gain.rightCols(9).isZero(0) && bias.rightCols(7).isZero(0),"unsupported affine gain/gear");
    kp=gain.col(0);bias0=bias.col(0);biasq=bias.col(1);biasv=bias.col(2);passive=array(c,"passive_damping",7);D=passive-biasv;eta=array(c,"friction_bounds",7);
    require(D.allFinite() && (D.array()>=0).all() && (passive.array()>=0).all() && (eta.array()>=0).all(),"nonnegative finite damping/friction");
    auto impedance=shaped(array(c,"solimp",35),5),reference=shaped(array(c,"solref",14),2);Eigen::VectorXd expected(5);expected<<.9,.95,.001,.5,2;
    for (int j=0;j<7;++j)require((impedance.row(j).transpose().array()==expected.array()).all(),"unsupported impedance profile");
    require((reference.array()>0).all() && (reference.col(0).array()>=2*h).all(),"unsupported reference positivity/timeconst below2h");
    auto invweight=array(c,"invweight0",7);double minimum=scalar(c,"minimum_value");require(minimum>0 && (invweight.array()>0).all(),"positive regularizer constants");
    R.resize(7);B.resize(7);
    for (int j=0;j<7;++j) {
      double regular=(1-impedance(j,0))/impedance(j,0)*invweight(j);
      double denominator=impedance(j,1)*reference(j,0);
      require(std::isfinite(regular) && std::isfinite(denominator) && denominator>0,"nonfinite reference coefficient intermediate");
      R(j)=std::max(minimum,regular);B(j)=2/denominator;
    }
    require(R.allFinite() && B.allFinite(),"nonfinite reference coefficients");
    std::array<const char*,4> rangeNames={"control_range","actuator_force_range","joint_actuator_force_range","joint_range"};
    std::array<const char*,4> flagNames={"control_limited","actuator_force_limited","joint_actuator_force_limited","joint_limited"};
    for (int i=0;i<4;++i) {
      ranges[i]=shaped(array(c,rangeNames[i],14),2);flags[i]=array(c,flagNames[i],7);
      require((ranges[i].col(0).array()<=ranges[i].col(1).array()).all(),"ordered actuator/joint ranges");
      for (int j=0;j<7;++j)require(flags[i](j)==0 || flags[i](j)==1,"binary public limit flags");
    }
    pinocchio::mjcf::buildModel(xml,model);
    require(model.nq==7 && model.nv==7 && model.names.size()==8,"MJCF fixed FR3 mapping");
    auto names=c["joint_names"];require(names.IsSequence() && names.size()==7,"joint-name dimensions");
    for (int j=0;j<7;++j) {
      require(model.names[j+1]==names[j].as<std::string>(),"MJCF joint name mapping");
      const auto& joint=model.joints[j+1];
      require(joint.nq()==1 && joint.nv()==1 && joint.idx_q()==j && joint.idx_v()==j,"MJCF scalar joint index mapping");
    }
    auto armature=array(c,"armature",7);require((model.armature.array()==armature.array()).all(),"parsed armature identity (no duplicate addition)");
    model.gravity.linear()=array(c,"gravity",3);data=std::make_unique<pinocchio::Data>(model);
  }
  void state(const Eigen::VectorXd& q,const Eigen::VectorXd& v) const {
    require(q.size()==7 && v.size()==7 && q.allFinite() && v.allFinite(),"finite state dimension7");
    for (int j=0;j<7;++j)if(flags[3](j))require(q(j)>ranges[3](j,0) && q(j)<ranges[3](j,1),"joint-limit-free regime");
  }
};
Model::Model(const std::string& xml,const std::string& constants):impl_(std::make_unique<Impl>(xml,constants)) {}
Model::~Model()=default;
ModelMetadata Model::metadata() const {
  auto& s=*impl_;ModelMetadata out;out.pinocchio_version=PINOCCHIO_VERSION;out.nq=s.model.nq;out.nv=s.model.nv;
  out.joint_names.assign(s.model.names.begin()+1,s.model.names.end());
  for (std::size_t j=1;j<s.model.joints.size();++j) {
    const auto& joint=s.model.joints[j];out.idx_q.push_back(joint.idx_q());out.idx_v.push_back(joint.idx_v());out.joint_nq.push_back(joint.nq());out.joint_nv.push_back(joint.nv());
  }
  for (const auto& f:s.model.frames)out.frame_names.push_back(f.name);
  out.masses.resize(s.model.inertias.size());for (int j=0;j<out.masses.size();++j)out.masses(j)=s.model.inertias[j].mass();
  out.armature=s.model.armature;out.gravity=s.model.gravity.linear();out.R=s.R;out.B=s.B;out.damping=s.D;
  require(out.masses.allFinite() && out.armature.allFinite() && out.gravity.allFinite(),"nonfinite static model metadata");return out;
}
StepResult Model::step(const Eigen::VectorXd& q,const Eigen::VectorXd& v,const Eigen::VectorXd& target) {
  auto& s=*impl_;s.state(q,v);require(target.size()==7 && target.allFinite(),"finite target dimension7");StepResult out;
  out.controls=target;
  for (int j=0;j<7;++j)if(s.flags[0](j))out.controls(j)=std::clamp(out.controls(j),s.ranges[0](j,0),s.ranges[0](j,1));
  out.control_clips=(out.controls.array()!=target.array()).count();
  out.actuator=s.kp.cwiseProduct(out.controls)+s.bias0+s.biasq.cwiseProduct(q)+s.biasv.cwiseProduct(v);
  require(out.actuator.allFinite(),"nonfinite pre-clamp affine actuator");Eigen::VectorXd original=out.actuator;
  for (int i=1;i<=2;++i)for(int j=0;j<7;++j)if(s.flags[i](j))out.actuator(j)=std::clamp(out.actuator(j),s.ranges[i](j,0),s.ranges[i](j,1));
  out.force_clips=(out.actuator.array()!=original.array()).count();
  const auto& mass=pinocchio::crba(s.model,*s.data,q);out.M=mass.selfadjointView<Eigen::Upper>();
  require(out.M.allFinite(),"nonfinite CRBA mass");
  out.bias=pinocchio::nonLinearEffects(s.model,*s.data,q,v);require(out.bias.allFinite(),"nonfinite rigid bias");
  Eigen::VectorXd passive=s.passive.cwiseProduct(v);require(passive.allFinite(),"nonfinite passive force");
  out.smooth=out.actuator-passive-out.bias;require(out.smooth.allFinite(),"nonfinite smooth force");
  out.W=solve(out.M,Eigen::MatrixXd::Identity(7,7),"mass inverse");out.H=out.W;out.H.diagonal()+=s.R;
  Eigen::VectorXd reference=s.B.cwiseProduct(v);require(reference.allFinite(),"nonfinite friction velocity reference");out.ell=out.W*out.smooth+reference;
  require(out.H.allFinite() && out.ell.allFinite(),"nonfinite friction quadratic");out.friction=solveFrictionBox(out.H,out.ell,s.eta);
  Eigen::MatrixXd implicit=out.M;implicit.diagonal()+=h*s.D;Eigen::VectorXd force=out.smooth+out.friction.force;
  require(implicit.allFinite() && force.allFinite(),"nonfinite implicit system");Eigen::VectorXd acceleration=solve(implicit,force,"implicit damping");
  out.v=v+h*acceleration;out.q=q+h*out.v;s.state(out.q,out.v);return out;
}
}  // namespace phase5_public_coupled_v2
