#include "public_coupled_augmented_extension.hpp"
#include <yaml-cpp/yaml.h>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iomanip>
#include <regex>
#include <set>
#include <sstream>

using phase5_public_coupled_augmented_extension::Model;
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
 YAML::Node n;n["certificate_name"]=Model::certificate_name;n["certifies_two_sided_admissible_neighborhood"]=false;n["origin_boundary"]=boundaryNode(cell?m.cell_origin:m.origin,m.input);n["endpoint_boundary"]=boundaryNode(m.state,m.input);n["cell"]=m.cell;n["cycle"]=m.cycle;n["half"]=m.half;n["origin"]=stateNode(cell?m.cell_origin:m.origin);n["state"]=stateNode(m.state);n["input"]=vectorNode(m.input);n["A"]=matrixNode(cell?m.cell_A:m.A);n["B"]=matrixNode(cell?m.cell_B:m.B);n["defect"]=vectorNode(cell?m.cell_defect:m.defect);
 if(!cell){n["cell_origin"]=stateNode(m.cell_origin);n["cell_A"]=matrixNode(m.cell_A);n["cell_B"]=matrixNode(m.cell_B);n["cell_defect"]=vectorNode(m.cell_defect);}return n;
}
int main(int argc,char** argv) {
 if(argc!=5){std::cerr<<"model_xml public_constants cases_json fresh_output_json\n";return 2;}
 if(std::filesystem::exists(argv[4])){std::cerr<<"refuse output overwrite\n";return 2;}
 YAML::Node result;int code=0;
 try {
  Model model(argv[1],argv[2]);result["model_success"]=true;auto m=model.metadata();auto meta=result["metadata"];
  meta["pinocchio_version"]=m.pinocchio_version;meta["nq"]=m.nq;meta["nv"]=m.nv;meta["joint_names"]=m.joint_names;meta["frame_names"]=m.frame_names;meta["masses"]=vectorNode(m.masses);meta["armature"]=vectorNode(m.armature);meta["gravity"]=vectorNode(m.gravity);meta["R"]=vectorNode(m.R);meta["B"]=vectorNode(m.B);meta["D"]=vectorNode(m.damping);meta["idx_q"]=m.idx_q;meta["idx_v"]=m.idx_v;meta["joint_nq"]=m.joint_nq;meta["joint_nv"]=m.joint_nv;
  meta["units"]="q/C rad,v/w rad/s,s dimensionless,r1/s; alpha rad/s^2,b1/s^2; time seconds; mass kg/armature kg*m^2";
  result["domain_scope"]="Composite-map derivatives induced by the canonical smooth command/progress polynomial extension at original closed-domain nominal values. The full physical map is nonlinear and retains unchanged strict physical branch policy. Exterior w/alpha/s/r perturbations are mathematical extension probes only, never admissible commands/history. No two-sided admissible-neighborhood, safety/accuracy/main/horizon/cost/controller/plant/task/timing certificate. Half maps diagnostic only.";
  auto policy=result["policy"];policy["cycle_dt"]=.004;policy["substep_dt"]=.002;policy["rows"]=30;policy["state_columns"]=30;policy["input_columns"]=8;policy["control_margin"]=Model::control_margin;policy["certificate_name"]=Model::certificate_name;policy["certifies_two_sided_admissible_neighborhood"]=false;policy["nominal_domain"]="original closed w/alpha/s/r; unchanged strict physical C";policy["max_cells"]=phase5_public_coupled_augmented::Model::max_cells;policy["max_each_total_cycles"]=phase5_public_coupled_augmented::Model::max_cycles;
  auto input=YAML::LoadFile(argv[3]);if(!input["cases"].IsSequence() || input["cases"].size()>128)throw std::invalid_argument("cases sequence within128 cap");result["cases"]=YAML::Node(YAML::NodeType::Sequence);
  for(const auto& e:input["cases"]) {
   YAML::Node n;n["name"]=e["name"].as<std::string>();n["extension_jacobian_success"]=false;n["certifies_two_sided_admissible_neighborhood"]=false;n["substep_maps"]=YAML::Node(YAML::NodeType::Sequence);n["cycle_maps"]=YAML::Node(YAML::NodeType::Sequence);n["cell_maps"]=YAML::Node(YAML::NodeType::Sequence);
   try {
    auto out=model.rollout(stateInput(e["state"]),cellsInput(e["cells"]));n["value"]=valueNode(out.value);n["extension_jacobian_success"]=out.extension_jacobian_success;n["first_uncertified_substep"]=out.first_uncertified_substep;if(out.extension_jacobian_success)n["certificate_name"]=Model::certificate_name;if(!out.extension_jacobian_success)n["error"]=out.error;
    for(const auto& x:out.substep_maps){n["substep_maps"].push_back(mapNode(x,false));}for(const auto& x:out.cycle_maps){n["cycle_maps"].push_back(mapNode(x,false));}for(const auto& x:out.cell_maps){n["cell_maps"].push_back(mapNode(x,true));}
   }catch(const std::exception& ex){n["error"]=ex.what();n["first_uncertified_substep"]=0;phase5_public_coupled_augmented::Result failed;failed.error=ex.what();n["value"]=valueNode(failed);}
   result["cases"].push_back(n);
  }
 }catch(const std::exception& ex){result["model_success"]=false;result["error"]=ex.what();code=1;}
 std::ofstream file(argv[4]);file.exceptions(std::ios::failbit|std::ios::badbit);jsonOutput(file,result);file<<'\n';std::cout<<"Composite-map Jacobian induced by command/progress extension; nonlinear physical map; closed nominal; no admissibility/plant claim\n";return code;
}
