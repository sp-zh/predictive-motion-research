#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <memory>
#include <sstream>
#include <predictive_motion_sim/plant.hpp>
#include "linearization.hpp"
#include "measured_position_guard.hpp"
#include "observation.hpp"
using namespace predictive_motion;
using namespace predictive_motion::control;
using namespace predictive_motion::geometry;
using namespace predictive_motion::preview_adapter;
std::vector<std::string> split(const std::string& line){std::stringstream stream(line);std::string cell;std::vector<std::string> out;while(std::getline(stream,cell,','))out.push_back(cell);return out;}
void matrix(const std::filesystem::path& f,const Eigen::MatrixXd& a){std::ofstream out(f);out<<std::scientific<<std::setprecision(17);for(int i=0;i<a.rows();++i){for(int j=0;j<a.cols();++j){if(j)out<<',';out<<a(i,j);}out<<'\n';}}
void csv(std::ostream& out,const Eigen::VectorXd& v){for(double x:v)out<<','<<x;}
std::vector<double> vector(const Eigen::VectorXd& v){return std::vector<double>(v.data(),v.data()+v.size());}
int main(int argc,char** argv){
 if(argc!=5){std::cerr<<"root frozen_protocol retained_csv fresh_output\n";return 2;}
 try{
  const std::filesystem::path root=argv[1],protocol=argv[2],input=argv[3],output=argv[4];
  if(std::filesystem::exists(output))throw std::runtime_error("refuse replay evidence overwrite");
  auto cfg=YAML::LoadFile(protocol.string());double dt=cfg["control_dt_s"].as<double>(),subdt=cfg["physics_substep_s"].as<double>(),safe=cfg["collision_safe_m"].as<double>();
  if(std::abs(dt-.004)>1e-14||std::abs(subdt-.002)>1e-14||qpSolverVersion()!="1.0.0")throw std::runtime_error("mesh or solver identity");
  std::ifstream file(input);std::string line;std::getline(file,line);auto header=split(line);std::map<std::string,int> column;for(int j=0;j<int(header.size());++j)column[header[j]]=j;
  std::vector<std::vector<std::string>> rows;while(std::getline(file,line))if(!line.empty())rows.push_back(split(line));
  if(rows.empty()||rows.size()%2)throw std::runtime_error("full recorded cycles required");
  auto names=YAML::LoadFile((root/"experiments/generated/phase4/robot.yaml").string())["joint_names"].as<std::vector<std::string>>();int n=names.size();
  auto read=[&](const std::vector<std::string>& row,const std::string& prefix){Eigen::VectorXd v(n);for(int j=0;j<n;++j)v(j)=std::stod(row.at(column.at(prefix+std::to_string(j))));return v;};
  Plant plant((root/"experiments/generated/inspection/scene.xml").string(),subdt);
  RobotKinematics robot(loadConfig((root/"experiments/generated/phase4/robot.yaml").string()));
  Scene geometry((root/"experiments/generated/phase5/geometry.json").string());
  std::unique_ptr<mjData,decltype(&mj_deleteData)> scratch(mj_makeData(plant.model()),mj_deleteData);
  uint32_t seed=cfg["validation_seed"].as<uint32_t>();plant.reset(seed);
  const Eigen::VectorXd initial=read(rows.front(),"target_");Eigen::VectorXd lo=robot.lowerLimits(),hi=robot.upperLimits();
  for(int j=0;j<n;++j){int joint=mj_name2id(plant.model(),mjOBJ_JOINT,names[j].c_str());plant.data()->qpos[plant.model()->jnt_qposadr[joint]]=initial(j);lo(j)=std::max(lo(j),plant.model()->jnt_range[2*joint]);hi(j)=std::min(hi(j),plant.model()->jnt_range[2*joint+1]);}
  plant.command(plant.names(),vector(initial));mj_forward(plant.model(),plant.data());
  auto measured=observe(plant,scratch.get(),robot,geometry);
  std::filesystem::create_directories(output);
  std::ofstream replay(output/"replay.csv");replay<<std::setprecision(17)<<"record,tick,substep,time_s,q_before_error,v_before_error,q_post_error,v_post_error,target_error,time_error\n";
  double maxq=0,maxv=0,maxt=0,maxc=0;Eigen::VectorXd target=initial;
  for(size_t i=0;i<rows.size();++i){
   const auto& row=rows[i];int tick=std::stoi(row.at(column.at("tick"))),sub=std::stoi(row.at(column.at("substep")));
   if(tick!=int(i/2)||sub!=int(i%2+1))throw std::runtime_error("noncontiguous prefix");
   auto logged_target=read(row,"target_");if(sub==1){target=logged_target;plant.command(plant.names(),vector(target));}
   double ce=(logged_target-target).lpNorm<Eigen::Infinity>(),qb=(measured.q-read(row,"q_before_")).lpNorm<Eigen::Infinity>(),vb=(measured.dq-read(row,"v_before_")).lpNorm<Eigen::Infinity>();
   plant.step();measured=observe(plant,scratch.get(),robot,geometry);
   double qp=(measured.q-read(row,"q_post_")).lpNorm<Eigen::Infinity>(),vp=(measured.dq-read(row,"v_post_")).lpNorm<Eigen::Infinity>(),te=std::abs(plant.time()-std::stod(row.at(column.at("time_s"))));
   maxq=std::max({maxq,qb,qp});maxv=std::max({maxv,vb,vp});maxc=std::max(maxc,ce);maxt=std::max(maxt,te);
   replay<<i<<','<<tick<<','<<sub<<','<<plant.time()<<','<<qb<<','<<vb<<','<<qp<<','<<vp<<','<<ce<<','<<te<<'\n';
   if(std::max({qb,vb,qp,vp,ce,te})>1e-12)throw std::runtime_error("prefix physical/command/time mismatch; refuse stop experiment");
  }
  replay.flush();
  CommandHistory history{measured.q,read(rows.back(),"target_"),read(rows.back(),"command_velocity_"),read(rows.back(),"command_acceleration_")};
  CommandLimits bounds{lo,hi,Eigen::VectorXd::Constant(n,cfg["command_velocity_rad_s"].as<double>()),Eigen::VectorXd::Constant(n,cfg["command_acceleration_rad_s2"].as<double>()),Eigen::VectorXd::Constant(n,cfg["command_jerk_rad_s3"].as<double>()),dt,cfg["position_margin_rad"].as<double>()};
  QpOptions options;options.absolute_tolerance=options.relative_tolerance=1e-9;options.acceptance_tolerance=1e-7;options.max_iterations=4000;options.time_limit_seconds=options.max_state_age_seconds=.05;
  std::ofstream cycles(output/"stop_cycles.csv"),raw(output/"stop_raw.csv");cycles<<"cycle,status,accepted,age_s,wall_s\n";
  raw<<"cycle,substep,time_s,contacts,true_clearance_m";for(auto prefix:{"q_","v_","target_","command_velocity_","command_acceleration_","physical_acceleration_","physical_jerk_"})for(int j=0;j<n;++j)raw<<','<<prefix<<j;raw<<'\n';raw<<std::setprecision(17);cycles<<std::setprecision(17);
  Eigen::VectorXd previous_v=measured.dq,previous_a=read(rows.back(),"physical_acceleration_");
  bool stopped=false;std::string outcome="STOP_TIMEOUT",status;int accepted=0;
  for(int cycle=0;cycle<1250;++cycle){
   auto begin=Clock::now();measured=observe(plant,scratch.get(),robot,geometry);auto capture=measured.capture;history.measured_position=measured.q;
   auto problem=constrainPreviewCommand(stoppingProblem(n),bounds,history);
   const double keep=.03+2*geometry.motion_radius_bound*((history.accepted_position-measured.q).cwiseAbs().sum()+n*.00025);
   auto snapshot=geometry.query(robot,measured.q,true,true,keep);
   std::vector<std::string> labels;for(int j=0;j<n;++j)labels.push_back("command_box/"+std::to_string(j));for(int j=0;j<n;++j){labels.push_back("command_acceleration/"+std::to_string(j));labels.push_back("command_jerk/"+std::to_string(j));}
   for(const auto& pair:snapshot.queries)if(!(pair.type=="true"&&pair.covered_tool_environment)&&pair.distance<keep){appendDamper(problem,pair.gradient,pair.distance,safe,cfg["collision_damper_eta_per_s"].as<double>());labels.push_back(pair.a+"/"+pair.b+"/"+pair.type+"/"+std::to_string(pair.cover_index));}
   problem.state_age_seconds=observationSeconds(capture);auto command=solveQp(problem,options);status=statusName(command.status);
   bool valid=command.status==QpStatus::Solved;
   if(valid)for(const Eigen::VectorXd& end:std::array<Eigen::VectorXd,2>{(measured.q+dt*command.velocity).eval(),(history.accepted_position+dt*command.velocity).eval()})for(int k=1;k<=cfg["command_subdivisions"].as<int>();++k){auto at=measured.q+double(k)/cfg["command_subdivisions"].as<int>()*(end-measured.q);auto g=geometry.query(robot,at,false,true,-INFINITY);if(std::min(g.minimum_true,g.minimum_cover)<safe)valid=false;}
   double age=observationSeconds(capture);valid=valid&&age<=.05;
   cycles<<cycle<<','<<status<<','<<valid<<','<<age<<','<<observationSeconds(begin)<<'\n';cycles.flush();
   if(!valid){outcome="NO_FEASIBLE_STOP_NO_COMMAND_SIMULATION_TERMINATED";matrix(output/"stop_H.csv",problem.hessian);matrix(output/"stop_g.csv",problem.gradient);matrix(output/"stop_A.csv",problem.constraints);matrix(output/"stop_lower.csv",problem.lower);matrix(output/"stop_upper.csv",problem.upper);std::ofstream label_file(output/"stop_rows.csv");label_file<<"row,label\n";for(int j=0;j<int(labels.size());++j)label_file<<j<<','<<labels[j]<<'\n';break;}
   Eigen::VectorXd acceleration=(command.velocity-history.accepted_velocity)/dt;
   history.accepted_velocity=command.velocity;history.accepted_acceleration=acceleration;history.accepted_position+=dt*command.velocity;plant.command(plant.names(),vector(history.accepted_position));++accepted;
   for(int sub=1;sub<=2;++sub){plant.step();measured=observe(plant,scratch.get(),robot,geometry);Eigen::VectorXd pa=(measured.dq-previous_v)/subdt,pj=(pa-previous_a)/subdt;previous_v=measured.dq;previous_a=pa;
    raw<<cycle<<','<<sub<<','<<plant.time()<<','<<measured.contacts<<','<<measured.clearance;for(const auto& v:std::vector<Eigen::VectorXd>{measured.q,measured.dq,history.accepted_position,history.accepted_velocity,history.accepted_acceleration,pa,pj})csv(raw,v);raw<<'\n';raw.flush();
    if(measured.contacts||measured.clearance<safe||!measuredPositionSafe(measured.q,lo,hi)||(measured.dq.array().abs()>mapped(YAML::LoadFile((root/"config/phase4.yaml").string())["velocity_rad_s"].as<std::vector<double>>()).array()).any()||pa.cwiseAbs().maxCoeff()>5||pj.cwiseAbs().maxCoeff()>500)throw std::runtime_error("stop executed safety failure retained");
   }
   if(history.accepted_velocity.cwiseAbs().maxCoeff()<1e-6&&measured.dq.cwiseAbs().maxCoeff()<1e-4){stopped=true;outcome="BOUNDED_STOP_OBSERVED";break;}
  }
  YAML::Emitter summary;summary<<YAML::BeginMap<<YAML::Key<<"scope"<<YAML::Value<<"Full past accepted-target physical replay including warmup; matched prefix then shared guarded stop attempt. Not a predictor/future-state input or generic stop certificate."
   <<YAML::Key<<"prefix_records"<<YAML::Value<<rows.size()<<YAML::Key<<"max_replay_q_error"<<YAML::Value<<maxq<<YAML::Key<<"max_replay_v_error"<<YAML::Value<<maxv<<YAML::Key<<"max_replay_target_error"<<YAML::Value<<maxc<<YAML::Key<<"max_replay_time_error"<<YAML::Value<<maxt
   <<YAML::Key<<"outcome"<<YAML::Value<<outcome<<YAML::Key<<"native_stop_status"<<YAML::Value<<status<<YAML::Key<<"accepted_stop_commands"<<YAML::Value<<accepted<<YAML::Key<<"completed_stop"<<YAML::Value<<stopped
   <<YAML::Key<<"final_virtual_time_s"<<YAML::Value<<plant.time()<<YAML::Key<<"final_physical_speed_rad_s"<<YAML::Value<<measured.dq.cwiseAbs().maxCoeff()<<YAML::Key<<"final_command_speed_rad_s"<<YAML::Value<<history.accepted_velocity.cwiseAbs().maxCoeff()<<YAML::EndMap;
  std::ofstream(output/"summary.yaml")<<summary.c_str()<<'\n';std::cout<<summary.c_str()<<'\n';return stopped?0:3;
 }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
