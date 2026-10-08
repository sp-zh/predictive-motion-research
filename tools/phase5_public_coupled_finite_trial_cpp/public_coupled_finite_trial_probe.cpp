#include "public_coupled_finite_trial.hpp"
#include <yaml-cpp/yaml.h>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iomanip>
#include <regex>
#include <set>
#include <sstream>

using phase5_public_coupled_finite_trial::Model;
using ExtensionModel=phase5_public_coupled_augmented_extension::Model;
using phase5_public_coupled_augmented::State;
std::string quoted(const std::string& s) {
  std::ostringstream o;o<<'"';
  for(unsigned char c:s){if(c=='"' || c=='\\')o<<'\\'<<c;else if(c<32)o<<"\\u"<<std::hex<<std::setw(4)<<std::setfill('0')<<int(c)<<std::dec;else o<<c;}
  o<<'"';return o.str();
}
void jsonOutput(std::ostream& o,const YAML::Node& n,bool stringValue=false) {
  static const std::set<std::string> strings={"name","error","units","pinocchio_version","joint_names","frame_names"};
  static const std::regex number("-?(0|[1-9][0-9]*)(\\.[0-9]+)?([eE][+-]?[0-9]+)?");
  if(n.IsMap()){o<<'{';bool first=true;for(const auto& item:n){if(!first)o<<',';first=false;auto key=item.first.as<std::string>();o<<quoted(key)<<':';jsonOutput(o,item.second,strings.count(key));}o<<'}';}
  else if(n.IsSequence()){o<<'[';bool first=true;for(const auto& item:n){if(!first)o<<',';first=false;jsonOutput(o,item,stringValue);}o<<']';}
  else if(n.IsNull())o<<"null";
  else{auto s=n.as<std::string>();if(!stringValue && (s=="true" || s=="false" || std::regex_match(s,number)))o<<s;else o<<quoted(s);}
}
YAML::Node vectorNode(const Eigen::VectorXd& v) {
  YAML::Node n(YAML::NodeType::Sequence);for(double x:v)n.push_back(x);
  return n;
}
YAML::Node matrixNode(const Eigen::MatrixXd& m) {
  YAML::Node n(YAML::NodeType::Sequence);
  for(int i=0;i<m.rows();++i)n.push_back(vectorNode(m.row(i).transpose()));
  return n;
}
Eigen::VectorXd vectorInput(const YAML::Node& n) {
  if(!n.IsSequence())throw std::invalid_argument("input vector sequence required");
  Eigen::VectorXd v(n.size());for(int j=0;j<v.size();++j)v(j)=n[j].as<double>();return v;
}
Eigen::MatrixXd matrixInput(const YAML::Node& n) {
  if(!n.IsSequence() || !n.size() || !n[0].IsSequence())throw std::invalid_argument("input matrix sequence");
  Eigen::MatrixXd m(n.size(),n[0].size());
  for(int i=0;i<m.rows();++i){if(int(n[i].size())!=m.cols())throw std::invalid_argument("input matrix ragged");for(int j=0;j<m.cols();++j)m(i,j)=n[i][j].as<double>();}return m;
}
YAML::Node boxNode(const phase5_public_coupled_v2::BoxResult& b) {
  YAML::Node n;n["force"]=vectorNode(b.force);n["branches"]=b.branches;n["iterations"]=b.iterations;n["original_KKT"]=b.original_kkt;return n;
}
YAML::Node stateNode(const phase5_public_coupled_v2::StepResult& r) {
  YAML::Node n;n["q"]=vectorNode(r.q);n["v"]=vectorNode(r.v);n["control_clips"]=r.control_clips;n["force_clips"]=r.force_clips;n["friction"]=boxNode(r.friction);return n;
}
State stateInput(const YAML::Node& e) {
 State z;z.q=vectorInput(e["q"]);z.v=vectorInput(e["v"]);z.C=vectorInput(e["C"]);z.w=vectorInput(e["w"]);z.s=e["s"].as<double>();z.r=e["r"].as<double>();return z;
}
YAML::Node stateNode(const State& z) {
 YAML::Node n;n["q"]=vectorNode(z.q);n["v"]=vectorNode(z.v);n["C"]=vectorNode(z.C);n["w"]=vectorNode(z.w);n["s"]=z.s;n["r"]=z.r;return n;
}
std::vector<phase5_public_coupled_augmented::Cell> cellsInput(const YAML::Node& input) {
 if(!input.IsSequence())throw std::invalid_argument("mesh cells sequence required");
 if(input.size()>phase5_public_coupled_augmented::Model::max_cells)throw std::invalid_argument("mesh cell count cap");
 static const std::regex integer("(0|[1-9][0-9]*)");std::vector<phase5_public_coupled_augmented::Cell> result;
 for(const auto& e:input) {
  auto node=e["cycles"];
  if(!node.IsScalar() || node.Tag()=="!" || !std::regex_match(node.Scalar(),integer))throw std::invalid_argument("cycles must be unquoted canonical integer; no remainder or rounding");
  auto count=std::stoull(node.Scalar());
  if(count>phase5_public_coupled_augmented::Model::max_cycles)throw std::invalid_argument("mesh cycle count cap");
  phase5_public_coupled_augmented::Cell cell;cell.cycles=count;cell.alpha=vectorInput(e["alpha"]);cell.b=e["b"].as<double>();result.push_back(std::move(cell));
 }
 return result;
}
YAML::Node valueNode(const phase5_public_coupled_augmented::Result& v) {
 YAML::Node n;n["success"]=v.success;n["has_final_state"]=v.has_final_state;if(!v.success)n["error"]=v.error;if(v.has_final_state)n["final_state"]=stateNode(v.final_state);
 n["substeps"]=YAML::Node(YAML::NodeType::Sequence);n["cycle_end_states"]=YAML::Node(YAML::NodeType::Sequence);n["cell_end_states"]=YAML::Node(YAML::NodeType::Sequence);
 for(const auto& p:v.substeps){YAML::Node t;t["cell"]=p.cell;t["cycle"]=p.cycle;t["half"]=p.half;t["elapsed_s"]=p.elapsed_s;t["q"]=vectorNode(p.q);t["v"]=vectorNode(p.v);t["C"]=vectorNode(p.C);t["w"]=vectorNode(p.w);t["s_reference"]=p.s_reference;t["r_reference"]=p.r_reference;t["friction"]=boxNode(p.friction);t["control_clips"]=p.control_clips;t["force_clips"]=p.force_clips;n["substeps"].push_back(t);}
 for(const auto& z:v.cycle_end_states){n["cycle_end_states"].push_back(stateNode(z));}for(const auto& z:v.cell_end_states){n["cell_end_states"].push_back(stateNode(z));}return n;
}
YAML::Node boundaryNode(const State& z,const Eigen::VectorXd& input) {
 YAML::Node n;n["w"]=YAML::Node(YAML::NodeType::Sequence);n["alpha"]=YAML::Node(YAML::NodeType::Sequence);
 for(int j=0;j<7;++j){n["w"].push_back(z.w(j)==-.0625?-1:z.w(j)==.0625?1:0);n["alpha"].push_back(input(j)==-1?-1:input(j)==1?1:0);}
 n["s"]=z.s==0?-1:z.s==1?1:0;n["r"]=z.r==0?-1:z.r==.2?1:0;return n;
}
YAML::Node mapNode(const phase5_public_coupled_augmented_extension::Map& m,bool cell) {
 YAML::Node n;n["certificate_name"]=ExtensionModel::certificate_name;n["certifies_two_sided_admissible_neighborhood"]=false;n["origin_boundary"]=boundaryNode(cell?m.cell_origin:m.origin,m.input);n["endpoint_boundary"]=boundaryNode(m.state,m.input);n["cell"]=m.cell;n["cycle"]=m.cycle;n["half"]=m.half;n["origin"]=stateNode(cell?m.cell_origin:m.origin);n["state"]=stateNode(m.state);n["input"]=vectorNode(m.input);n["A"]=matrixNode(cell?m.cell_A:m.A);n["B"]=matrixNode(cell?m.cell_B:m.B);n["defect"]=vectorNode(cell?m.cell_defect:m.defect);
 if(!cell){n["cell_origin"]=stateNode(m.cell_origin);n["cell_A"]=matrixNode(m.cell_A);n["cell_B"]=matrixNode(m.cell_B);n["cell_defect"]=vectorNode(m.cell_defect);}return n;
}
void noClaims(YAML::Node& n) {
 n["certifies_connecting_segment"]=false;n["certifies_perturbation_ball"]=false;
 n["certifies_admissibility"]=false;n["certifies_execution"]=false;n["certifies_safety"]=false;
 n["certifies_uniform_error_bound"]=false;n["certifies_controller_readiness"]=false;
}
phase5_public_coupled_finite_trial::Input trialInput(const YAML::Node& n) {
 phase5_public_coupled_finite_trial::Input input;
 try{input.state=stateInput(n["state"]);input.cells=cellsInput(n["cells"]);}
 catch(const std::exception& e){input.parse_error=e.what();}
 return input;
}
YAML::Node clipNode(const std::vector<phase5_public_coupled_derivative::ClipBranch>& c) {
 YAML::Node out(YAML::NodeType::Sequence);
 for(const auto& b:c){YAML::Node n;n["enabled"]=b.enabled;n["side"]=b.side;n["input"]=b.input;n["output"]=b.output;
  n["lower"]=b.lower;n["upper"]=b.upper;n["margin"]=b.margin;n["slope"]=b.slope;out.push_back(n);}
 return out;
}
YAML::Node inspectionNode(const phase5_public_coupled_finite_trial::Inspection& a) {
 YAML::Node n;noClaims(n);n["cell"]=a.cell;n["cycle"]=a.cycle;n["half"]=a.half;n["elapsed_s"]=a.elapsed_s;
 n["q_before"]=vectorNode(a.q_before);n["v_before"]=vectorNode(a.v_before);n["C"]=vectorNode(a.C);
 n["exact_value_parity"]=a.exact_value_parity;n["strict_C"]=a.strict_C;n["signature_complete"]=a.signature_complete;
 const auto& d=a.physical;n["value_success"]=d.value_success;n["jacobian_success"]=d.jacobian_success;
 if(!d.error.empty()){n["error"]=d.error;}
 n["control"]=clipNode(d.control);n["actuator"]=clipNode(d.actuator);n["joint_force"]=clipNode(d.joint_force);
 if(d.value_success){n["physical_value"]=stateNode(d.value);}
 n["friction_gradient"]=vectorNode(d.friction_gradient);n["friction_margin"]=vectorNode(d.friction_margin);
 n["solve_conditions"]=d.solve_conditions;n["solve_residuals"]=d.solve_residuals;
 if(d.jacobian_success){n["jacobian"]=matrixNode(d.jacobian);}
 return n;
}
YAML::Node comparisonNode(const phase5_public_coupled_finite_trial::Comparison& a) {
 YAML::Node n;noClaims(n);n["cell"]=a.cell;n["cycle"]=a.cycle;n["half"]=a.half;n["elapsed_s"]=a.elapsed_s;
 n["nominal_strict"]=a.nominal_strict;n["trial_strict"]=a.trial_strict;
 n["signatures_available"]=a.signatures_available;n["branches_equal"]=a.branches_equal;return n;
}
YAML::Node residualNode(const phase5_public_coupled_finite_trial::Residual& a) {
 YAML::Node n;noClaims(n);n["endpoint"]=a.endpoint;n["cell"]=a.cell;n["cycle"]=a.cycle;n["half"]=a.half;
 n["nominal_state"]=stateNode(a.nominal_state);n["trial_state"]=stateNode(a.trial_state);
 n["nominal_cell_origin"]=stateNode(a.nominal_cell_origin);n["cell_origin_deviation"]=vectorNode(a.cell_origin_deviation);
 n["input_deviation"]=vectorNode(a.input_deviation);n["linear_deviation"]=vectorNode(a.linear_deviation);
 n["prediction"]=vectorNode(a.prediction);n["residual"]=vectorNode(a.residual);
 const char* names[]={"q","v","C","w","s","r"};const char* units[]={"rad","rad/s","rad","rad/s","dimensionless","1/s"};
 const int offset[]={0,7,14,21,28,29},size[]={7,7,7,7,1,1};
 for(int j=0;j<6;++j){YAML::Node b;b["units"]=units[j];b["max_absolute"]=a.residual.segment(offset[j],size[j]).cwiseAbs().maxCoeff();n["block_residuals"][names[j]]=b;}
 return n;
}
YAML::Node nominalNode(const phase5_public_coupled_augmented_extension::Result& a) {
 YAML::Node n;n["value"]=valueNode(a.value);n["extension_jacobian_success"]=a.extension_jacobian_success;
 n["first_uncertified_substep"]=a.first_uncertified_substep;n["certifies_two_sided_admissible_neighborhood"]=false;
 if(a.extension_jacobian_success){n["certificate_name"]=ExtensionModel::certificate_name;}
 if(!a.error.empty()){n["error"]=a.error;}
 for(const auto* key:{"substep_maps","cycle_maps","cell_maps"}){n[key]=YAML::Node(YAML::NodeType::Sequence);}
 for(const auto& m:a.substep_maps){n["substep_maps"].push_back(mapNode(m,false));}
 for(const auto& m:a.cycle_maps){n["cycle_maps"].push_back(mapNode(m,false));}
 for(const auto& m:a.cell_maps){n["cell_maps"].push_back(mapNode(m,true));}
 return n;
}
int main(int argc,char** argv) {
 if(argc!=5){std::cerr<<"model_xml public_constants cases_json fresh_output_json\n";return 2;}
 if(std::filesystem::exists(argv[4])){std::cerr<<"refuse output overwrite\n";return 2;}
 YAML::Node result;int code=0;
 try {
  Model model(argv[1],argv[2]);result["model_success"]=true;auto m=model.metadata();auto meta=result["metadata"];
  meta["pinocchio_version"]=m.pinocchio_version;meta["nq"]=m.nq;meta["nv"]=m.nv;meta["joint_names"]=m.joint_names;meta["frame_names"]=m.frame_names;
  meta["masses"]=vectorNode(m.masses);meta["armature"]=vectorNode(m.armature);meta["gravity"]=vectorNode(m.gravity);meta["R"]=vectorNode(m.R);meta["B"]=vectorNode(m.B);meta["D"]=vectorNode(m.damping);meta["idx_q"]=m.idx_q;meta["idx_v"]=m.idx_v;meta["joint_nq"]=m.joint_nq;meta["joint_nv"]=m.joint_nv;
  meta["units"]="q/C rad,v/w rad/s,s dimensionless,r1/s; alpha rad/s^2,b1/s^2; time seconds; mass kg/armature kg*m^2";
  result["domain_scope"]="Finite original closed-domain nominal and trial self-rollouts; full per-joint signatures at actual sampled 2ms inputs only. Endpoint branch agreement proves no connecting segment or perturbation ball. GLOBAL affine residuals use literal nonlinear nominal endpoints and propagated nominal cell chains; no uniform error bound, admissibility, execution, safety, main controller, task, timing or Phase5 acceptance.";
  auto policy=result["policy"];noClaims(policy);policy["name"]=Model::policy_name;policy["cycle_dt"]=.004;policy["substep_dt"]=.002;
  policy["state_rows"]=30;policy["cell_input_columns"]=8;policy["mesh"]="same cell count and exact cycles per cell; topology equality only; original closed forward checks validity";
  policy["signature"]="per-joint enabled+side of control/actuator/joint-force, exact friction side; at actual step INPUT";
  policy["outcome_precedence"]="parse-forward-failed, mesh-mismatch, forward-failed, unsupported, sampled-branch-changed, sampled-strict-branches-unchanged";
  policy["affine"]="GLOBAL nominal cell-prefix A/B; propagated nominal cell-end deviation; distinct cell inputs; literal nominal baseline; actual-minus-linear residual";
  auto input=YAML::LoadFile(argv[3]);if(!input["cases"].IsSequence() || input["cases"].size()>128)throw std::invalid_argument("cases sequence within128 cap");
  result["cases"]=YAML::Node(YAML::NodeType::Sequence);
  for(const auto& e:input["cases"]) {
   YAML::Node n;n["name"]=e["name"].as<std::string>();noClaims(n);
   auto a=model.diagnose(trialInput(e["nominal"]),trialInput(e["trial"]));
   n["nominal"]=nominalNode(a.nominal);n["trial"]=valueNode(a.trial);n["outcome"]=a.outcome;
   n["mesh_matches"]=a.mesh_matches;n["all_forward_complete"]=a.all_forward_complete;n["all_sampled_strict"]=a.all_sampled_strict;
   n["sampled_branch_change"]=a.sampled_branch_change;n["all_sampled_signatures_equal"]=a.all_sampled_signatures_equal;
   if(!a.error.empty()){n["error"]=a.error;}if(!a.affine_error.empty()){n["affine_error"]=a.affine_error;}
   for(const auto* key:{"nominal_inspections","trial_inspections","comparisons","residuals"}){n[key]=YAML::Node(YAML::NodeType::Sequence);}
   for(const auto& p:a.nominal_inspections){n["nominal_inspections"].push_back(inspectionNode(p));}
   for(const auto& p:a.trial_inspections){n["trial_inspections"].push_back(inspectionNode(p));}
   for(const auto& p:a.comparisons){n["comparisons"].push_back(comparisonNode(p));}
   for(const auto& p:a.residuals){n["residuals"].push_back(residualNode(p));}
   result["cases"].push_back(n);
  }
 }catch(const std::exception& e){result["model_success"]=false;result["error"]=e.what();code=1;}
 std::ofstream file(argv[4]);file.exceptions(std::ios::failbit|std::ios::badbit);jsonOutput(file,result);file<<'\n';
 std::cout<<"Sampled finite closed-trial branch diagnostics only; GLOBAL nominal cell-chain affine residuals; no path/controller certificate\n";return code;
}
