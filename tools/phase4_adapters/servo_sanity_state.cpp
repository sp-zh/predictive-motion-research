#include "geometry.hpp"
#include <Eigen/SVD>
#include <iomanip>
#include <iostream>
#include <random>
using namespace predictive_motion;
using namespace predictive_motion::geometry;
int main(int argc,char**argv) {
  if(argc!=4)return 2;
  RobotKinematics robot(loadConfig(argv[1]));Scene scene(argv[2]);std::mt19937 rng(71007);
  for(int attempt=0;attempt<10000;++attempt) {
    Eigen::VectorXd q(7);
    for(int i=0;i<7;++i)q(i)=robot.lowerLimits()(i)+(.05+.9*double(rng())/4294967295.)*(robot.upperLimits()(i)-robot.lowerLimits()(i));
    Eigen::JacobiSVD<Jacobian> svd(robot.tcpJacobian(q,Reference::Local));
    const auto s=svd.singularValues();const double condition=s(0)/s(5);
    if(condition>12)continue;
    try {
      auto snapshot=scene.query(robot,q,false,false);
      if(snapshot.minimum_true<.012 || snapshot.minimum_tool_environment_true<.03)continue;
      YAML::Emitter result;result<<YAML::BeginMap<<YAML::Key<<"seed"<<YAML::Value<<71007<<YAML::Key<<"attempt"<<YAML::Value<<attempt
        <<YAML::Key<<"condition"<<YAML::Value<<condition<<YAML::Key<<"minimum_true_m"<<YAML::Value<<snapshot.minimum_true
        <<YAML::Key<<"minimum_tool_environment_m"<<YAML::Value<<snapshot.minimum_tool_environment_true<<YAML::Key<<"q"<<YAML::Value<<YAML::Flow<<YAML::BeginSeq;
      for(double x:q)result<<x;result<<YAML::EndSeq<<YAML::EndMap;
      std::ofstream(argv[3])<<result.c_str()<<'\n';std::cout<<result.c_str()<<'\n';return 0;
    }catch(const std::exception&){continue;}
  }
  return 1;
}
