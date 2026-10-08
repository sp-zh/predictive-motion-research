#include "public_coupled_augmented_model.hpp"
#include <yaml-cpp/yaml.h>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iomanip>
#include <regex>
#include <set>
#include <sstream>

using phase5_public_coupled_augmented::Model;
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
 if(input.size()>Model::max_cells)throw std::invalid_argument("mesh cell count cap");
 static const std::regex integer("(0|[1-9][0-9]*)");std::vector<phase5_public_coupled_augmented::Cell> result;
 for(const auto& e:input) {
  auto node=e["cycles"];
  if(!node.IsScalar() || node.Tag()=="!" || !std::regex_match(node.Scalar(),integer))throw std::invalid_argument("cycles must be unquoted canonical integer; no remainder or rounding");
  auto count=std::stoull(node.Scalar());
  if(count>Model::max_cycles)throw std::invalid_argument("mesh cycle count cap");
  phase5_public_coupled_augmented::Cell cell;cell.cycles=count;cell.alpha=vectorInput(e["alpha"]);cell.b=e["b"].as<double>();result.push_back(std::move(cell));
 }
 return result;
}
int main(int argc,char** argv) {
 if(argc!=5){std::cerr<<"model_xml public_constants cases_json fresh_output_json\n";return 2;}
 if(std::filesystem::exists(argv[4])){std::cerr<<"refuse output overwrite\n";return 2;}
 YAML::Node result;int code=0;
 try {
  Model model(argv[1],argv[2]);result["model_success"]=true;auto m=model.metadata();auto meta=result["base_metadata"];
  meta["pinocchio_version"]=m.pinocchio_version;meta["nq"]=m.nq;meta["nv"]=m.nv;meta["joint_names"]=m.joint_names;meta["frame_names"]=m.frame_names;meta["masses"]=vectorNode(m.masses);meta["armature"]=vectorNode(m.armature);meta["gravity"]=vectorNode(m.gravity);
  result["units"]="q/C rad; physical v/accepted w rad/s; alpha rad/s^2; s dimensionless; r 1/s; b 1/s^2; time seconds; mass kg/armature kg*m^2";
  result["domain_scope"]="Numerical component guard only; no physical safety, jerk, accuracy-domain, controller, task or timing acceptance.";
  auto policy=result["policy"];policy["cycle_dt"]=Model::cycle_dt;policy["substep_dt"]=Model::substep_dt;policy["max_cells"]=Model::max_cells;policy["max_each_total_cycles"]=Model::max_cycles;policy["command_v"]=Model::command_v;policy["command_a"]=Model::command_a;policy["progress_r"]=Model::progress_r;policy["progress_s_lower"]=0;policy["progress_s_upper"]=1;
  auto input=YAML::LoadFile(argv[3]);
  if(!input["cases"].IsSequence() || input["cases"].size()>128)throw std::invalid_argument("cases sequence within128 cap");
  result["cases"]=YAML::Node(YAML::NodeType::Sequence);
  for(const auto& e:input["cases"]) {
   YAML::Node n;n["name"]=e["name"].as<std::string>();n["success"]=false;n["substeps"]=YAML::Node(YAML::NodeType::Sequence);n["cycle_end_states"]=YAML::Node(YAML::NodeType::Sequence);n["cell_end_states"]=YAML::Node(YAML::NodeType::Sequence);
   try {
    auto initial=stateInput(e["state"]);auto cells=cellsInput(e["cells"]);auto out=model.rollout(initial,cells);
    n["success"]=out.success;if(!out.success)n["error"]=out.error;
    n["has_final_state"]=out.has_final_state;if(out.has_final_state)n["final_state"]=stateNode(out.final_state);
    for(const auto& p:out.substeps) {
     YAML::Node t;t["cell"]=p.cell;t["cycle"]=p.cycle;t["half"]=p.half;t["elapsed_s"]=p.elapsed_s;t["q"]=vectorNode(p.q);t["v"]=vectorNode(p.v);t["C"]=vectorNode(p.C);t["w"]=vectorNode(p.w);t["s_reference"]=p.s_reference;t["r_reference"]=p.r_reference;t["friction"]=boxNode(p.friction);t["control_clips"]=p.control_clips;t["force_clips"]=p.force_clips;n["substeps"].push_back(t);
    }
    for(const auto& z:out.cycle_end_states)n["cycle_end_states"].push_back(stateNode(z));
    for(const auto& z:out.cell_end_states)n["cell_end_states"].push_back(stateNode(z));
   }catch(const std::exception& ex){n["error"]=ex.what();n["has_final_state"]=false;}
   result["cases"].push_back(n);
  }
 }catch(const std::exception& ex){result["model_success"]=false;result["error"]=ex.what();code=1;}
 std::ofstream file(argv[4]);file.exceptions(std::ios::failbit|std::ios::badbit);jsonOutput(file,result);file<<'\n';std::cout<<"Frozen base-v2 augmented transition; no plant stepping\n";return code;
}
