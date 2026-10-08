#include "public_coupled_augmented_extension.hpp"
#include <yaml-cpp/yaml.h>
#include <cmath>
#include <stdexcept>
namespace phase5_public_coupled_augmented_extension {
namespace {
void need(bool x,const char* msg){if(!x)throw std::invalid_argument(msg);}
constexpr double h=.004;
}
Model::Model(const std::string& xml,const std::string& constants):value_(xml,constants),derivative_(xml,constants) {
 auto c=YAML::LoadFile(constants);C_lower_.resize(7);C_upper_.resize(7);
 for(int j=0;j<7;++j){C_lower_(j)=c["control_range"][2*j].as<double>();C_upper_(j)=c["control_range"][2*j+1].as<double>();}
 need(C_lower_.allFinite() && C_upper_.allFinite(),"finite sensitivity command ranges");
}
Eigen::VectorXd Model::packed(const State& z) {
 need(z.q.size()==7 && z.v.size()==7 && z.C.size()==7 && z.w.size()==7,"packed augmented dimensions");Eigen::VectorXd x(30);x<<z.q,z.v,z.C,z.w,z.s,z.r;need(x.allFinite(),"finite packed augmented state");return x;
}
void Model::domain(const State& z) const {
 (void)packed(z);
 using Value=phase5_public_coupled_augmented::Model;
 need((z.C.array()>C_lower_.array()+control_margin).all() && (z.C.array()<C_upper_.array()-control_margin).all(),"augmented C boundary not certified by unchanged physical strict policy");
 need((z.w.array().abs()<=Value::command_v).all(),"nominal w outside original closed domain");
 need(z.s>=0 && z.s<=1 && z.r>=0 && z.r<=Value::progress_r,"nominal progress outside original closed domain");
}
void Model::local(const Eigen::MatrixXd& physical,double t,Eigen::MatrixXd& A,Eigen::MatrixXd& B) {
 need(physical.rows()==14 && physical.cols()==21 && physical.allFinite(),"finite physical transition Jacobian14x21");
 A=Eigen::MatrixXd::Zero(30,30);B=Eigen::MatrixXd::Zero(30,8);
 A.topLeftCorner(14,14)=physical.leftCols(14);A.block(0,14,14,7)=physical.rightCols(7);A.block(0,21,14,7)=h*physical.rightCols(7);B.topLeftCorner(14,7)=h*h*physical.rightCols(7);
 A.block(14,14,7,7).setIdentity();A.block(14,21,7,7)=h*Eigen::MatrixXd::Identity(7,7);B.block(14,0,7,7)=h*h*Eigen::MatrixXd::Identity(7,7);
 A.block(21,21,7,7).setIdentity();B.block(21,0,7,7)=h*Eigen::MatrixXd::Identity(7,7);
 A(28,28)=1;A(28,29)=t;A(29,29)=1;B(28,7)=.5*t*t;B(29,7)=t;
 need(A.allFinite() && B.allFinite(),"finite local augmented blocks");
}
Map Model::mapping(int cell,int cycle,int half,const State& origin,const State& endpoint,const State& cell_origin,const Eigen::VectorXd& input,const Eigen::MatrixXd& A,const Eigen::MatrixXd& B,const Eigen::MatrixXd& prior_A,const Eigen::MatrixXd& prior_B) {
 need(input.size()==8 && input.allFinite() && A.rows()==30 && A.cols()==30 && B.rows()==30 && B.cols()==8 && prior_A.rows()==30 && prior_A.cols()==30 && prior_B.rows()==30 && prior_B.cols()==8,"finite augmented mapping dimensions");
 Map out;out.cell=cell;out.cycle=cycle;out.half=half;out.origin=origin;out.state=endpoint;out.cell_origin=cell_origin;out.input=input;out.A=A;out.B=B;
 out.cell_A=A*prior_A;Eigen::MatrixXd product=A*prior_B;need(product.allFinite() && out.cell_A.allFinite(),"augmented sensitivity product overflow");out.cell_B=product+B;need(out.cell_B.allFinite(),"augmented sensitivity input-sum overflow");
 Eigen::VectorXd initial=packed(origin),cell_initial=packed(cell_origin),finish=packed(endpoint);Eigen::VectorXd a=A*initial,b=B*input,ca=out.cell_A*cell_initial,cb=out.cell_B*input;
 need(a.allFinite() && b.allFinite() && ca.allFinite() && cb.allFinite(),"affine defect product overflow");Eigen::VectorXd first=finish-a,cfirst=finish-ca;need(first.allFinite() && cfirst.allFinite(),"affine defect subtraction overflow");out.defect=first-b;out.cell_defect=cfirst-cb;need(out.defect.allFinite() && out.cell_defect.allFinite(),"affine defect final overflow");return out;
}
Result Model::rollout(const State& initial,const std::vector<Cell>& cells) {
 Result out;out.value=value_.rollout(initial,cells);int step=0;
 try {
  domain(initial);State before=initial,cell_origin=initial;Eigen::MatrixXd prior_A=Eigen::MatrixXd::Identity(30,30),prior_B=Eigen::MatrixXd::Zero(30,8),J1;
  int current_cell=-1;std::size_t complete_cycles=0;
  for(const auto& point:out.value.substeps) {
   if(point.cell!=current_cell){current_cell=point.cell;cell_origin=before;prior_A.setIdentity();prior_B.setZero();need(point.cell>=0 && point.cell<int(cells.size()),"sensitivity cell roster");need(cells[point.cell].alpha.size()==7 && cells[point.cell].alpha.allFinite() && (cells[point.cell].alpha.array().abs()<=phase5_public_coupled_augmented::Model::command_a).all(),"nominal alpha outside original closed domain");}
   Eigen::VectorXd input(8);input<<cells[point.cell].alpha,cells[point.cell].b;need(input.allFinite(),"finite augmented sensitivity input");
   State mid;mid.q=point.q;mid.v=point.v;mid.C=point.C;mid.w=point.w;mid.s=point.s_reference;mid.r=point.r_reference;domain(mid);
   Eigen::VectorXd physical_q=point.half==1?before.q:out.value.substeps[step-1].q,physical_v=point.half==1?before.v:out.value.substeps[step-1].v;
   auto d=derivative_.step(physical_q,physical_v,point.C);
   need(d.value_success && (d.value.q.array()==point.q.array()).all() && (d.value.v.array()==point.v.array()).all(),"frozen augmented/physical derivative nominal parity");
   need(d.jacobian_success,d.error.c_str());Eigen::MatrixXd physical=d.jacobian;
   if(point.half==1)J1=d.jacobian;
   else {
    need(point.half==2 && J1.rows()==14 && J1.cols()==21,"paired2ms derivative order");physical.leftCols(14)=d.jacobian.leftCols(14)*J1.leftCols(14);
    Eigen::MatrixXd product=d.jacobian.leftCols(14)*J1.rightCols(7);need(product.allFinite() && physical.leftCols(14).allFinite(),"paired physical Jacobian product overflow");physical.rightCols(7)=product+d.jacobian.rightCols(7);need(physical.allFinite(),"paired physical Jacobian sum overflow");
   }
   Eigen::MatrixXd A,B;local(physical,.002*point.half,A,B);
   auto sm=mapping(point.cell,point.cycle,point.half,before,mid,cell_origin,input,A,B,prior_A,prior_B);
   if(point.half==2 && complete_cycles<out.value.cycle_end_states.size()) {
    State end=out.value.cycle_end_states[complete_cycles];domain(end);auto cm=mapping(point.cell,point.cycle,2,before,end,cell_origin,input,A,B,prior_A,prior_B);
    if(point.cycle==cells[point.cell].cycles){need(point.cell<int(out.value.cell_end_states.size()),"completed cell value roster");need((packed(end).array()==packed(out.value.cell_end_states[point.cell]).array()).all(),"completed cycle/cell exact nominal parity");out.cell_maps.push_back(cm);}
    out.cycle_maps.push_back(cm);prior_A=cm.cell_A;prior_B=cm.cell_B;before=end;++complete_cycles;
   }
   out.substep_maps.push_back(sm);++step;
  }
  need(out.value.success && out.cell_maps.size()==cells.size(),out.value.success?"incomplete certified cell roster":out.value.error.c_str());out.extension_jacobian_success=true;
 }catch(const std::exception& e){out.first_uncertified_substep=step;out.error=e.what();}
 // On non-certification all original values remain, only a certified prefix is
 // emitted; no matrices for an uncertified final cell or stale later cycle.
 return out;
}
}
