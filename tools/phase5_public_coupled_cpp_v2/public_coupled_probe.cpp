#include "public_coupled_model.hpp"
#include <yaml-cpp/yaml.h>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iomanip>
#include <regex>
#include <set>
#include <sstream>

using phase5_public_coupled_v2::Model;
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
int main(int argc,char** argv) {
  if(argc!=5){std::cerr<<"model_xml public_constants_json cases_yaml fresh_output_json\n";return 2;}
  if(std::filesystem::exists(argv[4])){std::cerr<<"refuse output overwrite\n";return 2;}
  YAML::Node result;int code=0;
  try {
    Model model(argv[1],argv[2]);auto meta=model.metadata();result["model_success"]=true;
    auto m=result["metadata"];m["units"]="mass kg; armature kg*m^2; q rad; v rad/s; target rad; h seconds; own Pinocchio model contains tool mass";m["pinocchio_version"]=meta.pinocchio_version;m["nq"]=meta.nq;m["nv"]=meta.nv;m["joint_names"]=meta.joint_names;m["frame_names"]=meta.frame_names;
    m["idx_q"]=meta.idx_q;m["idx_v"]=meta.idx_v;m["joint_nq"]=meta.joint_nq;m["joint_nv"]=meta.joint_nv;
    m["masses"]=vectorNode(meta.masses);m["armature"]=vectorNode(meta.armature);m["gravity"]=vectorNode(meta.gravity);m["R"]=vectorNode(meta.R);m["B"]=vectorNode(meta.B);m["D"]=vectorNode(meta.damping);
    auto cases=YAML::LoadFile(argv[3]);result["cases"]=YAML::Node(YAML::NodeType::Sequence);
    if(cases["cases"])for(const auto& entry:cases["cases"]) {
      YAML::Node out;out["name"]=entry["name"].as<std::string>();out["trace"]=YAML::Node(YAML::NodeType::Sequence);
      try {
        Eigen::VectorXd q=vectorInput(entry["q"]),v=vectorInput(entry["v"]);
        if(!entry["targets"].IsSequence() || !entry["targets"].size())throw std::invalid_argument("nonempty conditional targets required");
        for(const auto& target:entry["targets"]) {
          auto step=model.step(q,v,vectorInput(target));q=step.q;v=step.v;out["trace"].push_back(stateNode(step));
          out["last"]=stateNode(step);out["last"]["M"]=matrixNode(step.M);out["last"]["W"]=matrixNode(step.W);out["last"]["H"]=matrixNode(step.H);out["last"]["ell"]=vectorNode(step.ell);out["last"]["bias"]=vectorNode(step.bias);out["last"]["smooth"]=vectorNode(step.smooth);out["last"]["actuator"]=vectorNode(step.actuator);out["last"]["controls"]=vectorNode(step.controls);
        }
        out["success"]=true;
      }catch(const std::exception& e){out["success"]=false;out["error"]=e.what();}
      result["cases"].push_back(out);
    }
    result["box_cases"]=YAML::Node(YAML::NodeType::Sequence);
    if(cases["box_cases"])for(const auto& entry:cases["box_cases"]) {
      YAML::Node out;out["name"]=entry["name"].as<std::string>();
      try {out["result"]=boxNode(phase5_public_coupled_v2::solveFrictionBox(matrixInput(entry["H"]),vectorInput(entry["ell"]),vectorInput(entry["eta"])));out["success"]=true;}
      catch(const std::exception& e){out["success"]=false;out["error"]=e.what();}
      result["box_cases"].push_back(out);
    }
  }catch(const std::exception& e){result["model_success"]=false;result["error"]=e.what();code=1;}
  std::ofstream file(argv[4]);file.exceptions(std::ios::failbit|std::ios::badbit);jsonOutput(file,result);file<<'\n';std::cout<<"Independent public transition probe output; no plant stepping\n";return code;
}
