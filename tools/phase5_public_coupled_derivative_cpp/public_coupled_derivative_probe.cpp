#include "public_coupled_derivative_model.hpp"
#include <yaml-cpp/yaml.h>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iomanip>
#include <regex>
#include <set>
#include <sstream>

using phase5_public_coupled_derivative::Model;

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
YAML::Node clipNode(const std::vector<phase5_public_coupled_derivative::ClipBranch>& branches) {
 YAML::Node result(YAML::NodeType::Sequence);
 for(const auto& b:branches){YAML::Node n;n["enabled"]=b.enabled;n["side"]=b.side;n["input"]=b.input;n["output"]=b.output;n["lower"]=b.lower;n["upper"]=b.upper;n["margin"]=b.margin;n["slope"]=b.slope;result.push_back(n);}return result;
}
YAML::Node fullValue(const phase5_public_coupled_v2::StepResult& r) {
 auto n=stateNode(r);n["controls"]=vectorNode(r.controls);n["actuator"]=vectorNode(r.actuator);n["bias"]=vectorNode(r.bias);n["smooth"]=vectorNode(r.smooth);n["M"]=matrixNode(r.M);n["W"]=matrixNode(r.W);n["H"]=matrixNode(r.H);n["ell"]=vectorNode(r.ell);return n;
}
int main(int argc,char** argv) {
 if(argc!=5){std::cerr<<"model_xml public_constants cases_json fresh_output_json\n";return 2;}
 if(std::filesystem::exists(argv[4])){std::cerr<<"refuse output overwrite\n";return 2;}
 YAML::Node result;int code=0;
 try {
  Model model(argv[1],argv[2]);result["model_success"]=true;auto m=model.metadata();auto meta=result["metadata"];
  meta["pinocchio_version"]=m.pinocchio_version;meta["nq"]=m.nq;meta["nv"]=m.nv;meta["joint_names"]=m.joint_names;meta["frame_names"]=m.frame_names;meta["masses"]=vectorNode(m.masses);meta["armature"]=vectorNode(m.armature);meta["gravity"]=vectorNode(m.gravity);meta["R"]=vectorNode(m.R);meta["B"]=vectorNode(m.B);meta["D"]=vectorNode(m.damping);meta["units"]="rad,rad/s,seconds,kg,kg*m^2,Nm; fixed public FR3 physical profile";meta["idx_q"]=m.idx_q;meta["idx_v"]=m.idx_v;meta["joint_nq"]=m.joint_nq;meta["joint_nv"]=m.joint_nv;
  result["units"]="J14x21: rows qnext(rad),vnext(rad/s); columns q(rad),v(rad/s),C(rad). Control margin rad; force/slack Nm; friction gradient margin rad/s^2.";
  result["domain_scope"]="Physical2ms reference only; strict stable branches. Near/weak thresholds unsupported unique Jacobian; value retained. No generalized/one-sided, augmented/controller/task/timing acceptance.";
  auto policy=result["policy"];policy["h"]=Model::h;policy["control_margin"]=Model::control_margin;policy["force_margin"]=Model::force_margin;policy["friction_margin"]=Model::friction_margin;policy["gradient_margin"]=Model::gradient_margin;policy["max_condition"]=Model::max_condition;policy["residual_limit"]=Model::residual_limit;policy["rows"]=14;policy["columns"]=21;policy["analytic_rnea_calls"]=8;
  auto input=YAML::LoadFile(argv[3]);if(!input["cases"].IsSequence() || input["cases"].size()>128)throw std::invalid_argument("cases sequence within128 cap");result["cases"]=YAML::Node(YAML::NodeType::Sequence);
  for(const auto& e:input["cases"]) {
   YAML::Node n;n["name"]=e["name"].as<std::string>();n["value_success"]=false;n["jacobian_success"]=false;
   try {
    auto out=model.step(vectorInput(e["q"]),vectorInput(e["v"]),vectorInput(e["C"]));n["value_success"]=out.value_success;n["jacobian_success"]=out.jacobian_success;
    if(!out.error.empty())n["error"]=out.error;
    if(out.value_success)n["value"]=fullValue(out.value);
    auto d=n["diagnostics"];d["complete"]=out.jacobian_success;d["control"]=clipNode(out.control);d["actuator"]=clipNode(out.actuator);d["joint_force"]=clipNode(out.joint_force);d["solve_conditions"]=out.solve_conditions;d["solve_residuals"]=out.solve_residuals;
    if(out.friction_gradient.size()==7 && out.friction_gradient.allFinite())d["friction_gradient"]=vectorNode(out.friction_gradient);
    if(out.friction_margin.size()==7 && out.friction_margin.allFinite())d["friction_margin"]=vectorNode(out.friction_margin);
    if(out.jacobian_success){n["jacobian"]=matrixNode(out.jacobian);d["nq"]=matrixNode(out.nq);d["nv"]=matrixNode(out.nv);d["mass_q"]=YAML::Node(YAML::NodeType::Sequence);for(const auto& dm:out.mass_q)d["mass_q"].push_back(matrixNode(dm));d["smooth_jacobian"]=matrixNode(out.smooth_jacobian);d["friction_jacobian"]=matrixNode(out.friction_jacobian);d["acceleration_jacobian"]=matrixNode(out.acceleration_jacobian);}
   }catch(const std::exception& ex){n["error"]=ex.what();}
   result["cases"].push_back(n);
  }
 }catch(const std::exception& ex){result["model_success"]=false;result["error"]=ex.what();code=1;}
 std::ofstream file(argv[4]);file.exceptions(std::ios::failbit|std::ios::badbit);jsonOutput(file,result);file<<'\n';std::cout<<"Physical2ms analytic reference; frozen value model; no plant\n";return code;
}
