#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <memory>
#include <sstream>
#include <predictive_motion_sim/plant.hpp>
#include "linearization.hpp"
using namespace predictive_motion;
using namespace predictive_motion::control;
using namespace predictive_motion::geometry;
using namespace predictive_motion::preview_adapter;
std::vector<std::string> split(const std::string& line) {
  std::stringstream stream(line);std::string item;std::vector<std::string> out;
  while(std::getline(stream,item,','))out.push_back(item);
  return out;
}
void matrix(const std::filesystem::path& file,const Eigen::MatrixXd& value) {
  std::ofstream out(file);out.exceptions(std::ios::failbit|std::ios::badbit);
  out<<std::scientific<<std::setprecision(17);
  for(int row=0;row<value.rows();++row){for(int col=0;col<value.cols();++col){if(col)out<<',';out<<value(row,col);}out<<'\n';}
}
std::vector<double> vector(const Eigen::VectorXd& value){return std::vector<double>(value.data(),value.data()+value.size());}
void result(YAML::Emitter& out,const std::string& key,const QpResult& r) {
  out<<YAML::Key<<key<<YAML::Value<<YAML::BeginMap
     <<YAML::Key<<"status"<<YAML::Value<<statusName(r.status)
     <<YAML::Key<<"native_status"<<YAML::Value<<r.raw_status
     <<YAML::Key<<"iterations"<<YAML::Value<<r.iterations
     <<YAML::Key<<"has_usable_command"<<YAML::Value<<(r.status==QpStatus::Solved)
     <<YAML::Key<<"original_row_violation"<<YAML::Value<<r.violation
     <<YAML::Key<<"primal_residual"<<YAML::Value<<r.primal_residual
     <<YAML::Key<<"dual_residual"<<YAML::Value<<r.dual_residual<<YAML::EndMap;
}
int main(int argc,char** argv) {
  if(argc!=5){std::cerr<<"root protocol retained_raw_csv fresh_offline_output\n";return 2;}
  try {
    const std::filesystem::path root=argv[1],protocol=argv[2],raw=argv[3],output=argv[4];
    if(std::filesystem::exists(output))throw std::runtime_error("refuse output overwrite");
    auto cfg=YAML::LoadFile(protocol.string());
    auto robot_cfg=YAML::LoadFile((root/"experiments/generated/phase4/robot.yaml").string());
    auto names=robot_cfg["joint_names"].as<std::vector<std::string>>();int n=names.size();
    std::ifstream file(raw);std::string line;std::getline(file,line);auto header=split(line);
    std::map<std::string,int> columns;for(int i=0;i<int(header.size());++i)columns[header[i]]=i;
    std::getline(file,line);auto first=split(line),last=first;
    while(std::getline(file,line))if(!line.empty())last=split(line);
    if(first.size()!=header.size()||last.size()!=header.size()||std::stoi(last.at(columns.at("substep")))!=2)
      throw std::runtime_error("retained trace must end after a complete control cycle");
    auto read=[&](const std::vector<std::string>& row,const std::string& prefix){Eigen::VectorXd value(n);for(int j=0;j<n;++j)value(j)=std::stod(row.at(columns.at(prefix+std::to_string(j))));return value;};
    Eigen::VectorXd initial=read(first,"target_");
    CommandHistory history{read(last,"q_post_"),read(last,"target_"),read(last,"command_velocity_"),read(last,"command_acceleration_")};
    int tick=std::stoi(last.at(columns.at("tick")))+1;
    double dt=cfg["control_dt_s"].as<double>(),safe=cfg["collision_safe_m"].as<double>();
    if(std::abs(dt-.004)>1e-14||qpSolverVersion()!="1.0.0")throw std::runtime_error("mesh/solver identity");
    // Only compile the public model to read joint bounds. No mjData, real plant
    // state, mj_forward, mj_step, reset or replay is constructed or executed.
    char error[1024]={};
    std::unique_ptr<mjModel,decltype(&mj_deleteModel)> model(mj_loadXML((root/"experiments/generated/inspection/scene.xml").c_str(),nullptr,error,sizeof(error)),mj_deleteModel);
    if(!model)throw std::runtime_error(error);
    RobotKinematics robot(loadConfig((root/"experiments/generated/phase4/robot.yaml").string()));
    Scene geometry((root/"experiments/generated/phase5/geometry.json").string());
    Eigen::VectorXd lower=robot.lowerLimits(),upper=robot.upperLimits();
    for(int j=0;j<n;++j){int index=mj_name2id(model.get(),mjOBJ_JOINT,names[j].c_str());if(index<0)throw std::runtime_error("joint mapping");lower(j)=std::max(lower(j),model->jnt_range[2*index]);upper(j)=std::min(upper(j),model->jnt_range[2*index+1]);}
    CommandLimits bounds{lower,upper,Eigen::VectorXd::Constant(n,cfg["command_velocity_rad_s"].as<double>()),
      Eigen::VectorXd::Constant(n,cfg["command_acceleration_rad_s2"].as<double>()),Eigen::VectorXd::Constant(n,cfg["command_jerk_rad_s3"].as<double>()),dt,cfg["position_margin_rad"].as<double>()};
    const int warmup=std::lround(2./dt),task=std::lround(cfg["identification_duration_s"].as<double>()/dt);
    double t=(tick-warmup)*dt,ramp=std::min(1.,t/.8),envelope=ramp*ramp*ramp*(10-15*ramp+6*ramp*ramp);
    Eigen::VectorXd request=Eigen::VectorXd::Zero(n),desired=history.accepted_position;
    if(tick>=warmup&&tick<warmup+task)for(int j=0;j<n;++j){double f=cfg["validation_frequency_base_hz"].as<double>()+cfg["validation_frequency_step_hz"].as<double>()*j;desired(j)=initial(j)+cfg["identification_amplitude_rad"].as<double>()*envelope*std::sin(2*3.141592653589793*f*t+cfg["validation_phase_step_rad"].as<double>()*j);request(j)=(desired(j)-history.accepted_position(j))/dt;}
    auto problem=constrainPreviewCommand(trackingProblem(Eigen::MatrixXd::Identity(n,n),request,0),bounds,history);
    auto boxes=problem;
    std::vector<std::string> labels;for(int j=0;j<n;++j)labels.push_back("command_box/"+std::to_string(j));
    for(int j=0;j<n;++j){labels.push_back("command_acceleration/"+std::to_string(j));labels.push_back("command_jerk/"+std::to_string(j));}
    auto query=geometry.query(robot,history.measured_position,true,true,.03);
    for(const auto& pair:query.queries)if(!(pair.type=="true"&&pair.covered_tool_environment)&&pair.distance<.03){appendDamper(problem,pair.gradient,pair.distance,safe,2.);labels.push_back(pair.a+"/"+pair.b+"/"+pair.type+"/"+std::to_string(pair.cover_index));}
    // State-age zero is solely an offline-matrix diagnostic convention. No
    // command is executed; it does not relax the live 50 ms guard.
    problem.state_age_seconds=boxes.state_age_seconds=0;
    QpOptions o;o.absolute_tolerance=o.relative_tolerance=1e-9;o.acceptance_tolerance=1e-7;o.max_iterations=4000;o.time_limit_seconds=o.max_state_age_seconds=.05;
    auto full=solveQp(problem,o),box_result=solveQp(boxes,o);
    std::filesystem::create_directories(output);
    matrix(output/"H.csv",problem.hessian);matrix(output/"g.csv",problem.gradient);matrix(output/"A.csv",problem.constraints);matrix(output/"lower.csv",problem.lower);matrix(output/"upper.csv",problem.upper);
    std::ofstream rows(output/"rows.csv");rows<<"row,label\n";for(int j=0;j<int(labels.size());++j)rows<<j<<','<<labels[j]<<'\n';
    if(full.status==QpStatus::Solved)matrix(output/"candidate.csv",full.velocity);
    if(box_result.status==QpStatus::Solved)matrix(output/"box_candidate.csv",box_result.velocity);
    YAML::Emitter meta;meta<<YAML::BeginMap<<YAML::Key<<"scope"<<YAML::Value<<"Offline reconstruction from retained final encoder/accepted histories; not captured original runtime matrices; no plant replay or accepted command"
      <<YAML::Key<<"next_tick"<<YAML::Value<<tick<<YAML::Key<<"excitation_time_s"<<YAML::Value<<t
      <<YAML::Key<<"qp_rows"<<YAML::Value<<problem.constraints.rows()<<YAML::Key<<"box_rows"<<YAML::Value<<boxes.constraints.rows()
      <<YAML::Key<<"solver_version"<<YAML::Value<<qpSolverVersion()<<YAML::Key<<"offline_state_age_s"<<YAML::Value<<0.
      <<YAML::Key<<"measured_q"<<YAML::Value<<vector(history.measured_position)<<YAML::Key<<"measured_v"<<YAML::Value<<vector(read(last,"v_post_"))
      <<YAML::Key<<"accepted_target"<<YAML::Value<<vector(history.accepted_position)<<YAML::Key<<"accepted_velocity"<<YAML::Value<<vector(history.accepted_velocity)
      <<YAML::Key<<"accepted_acceleration"<<YAML::Value<<vector(history.accepted_acceleration)<<YAML::Key<<"request"<<YAML::Value<<vector(request)
      <<YAML::Key<<"desired_target"<<YAML::Value<<vector(desired)<<YAML::Key<<"minimum_query_true_m"<<YAML::Value<<query.minimum_true<<YAML::Key<<"minimum_query_cover_m"<<YAML::Value<<query.minimum_cover;
    result(meta,"with_geometry",full);result(meta,"boxes_only",box_result);meta<<YAML::EndMap;
    std::ofstream(output/"reconstruction.yaml")<<meta.c_str()<<'\n';std::cout<<meta.c_str()<<'\n';return 0;
  }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
