#include "geometry.hpp"
#include <predictive_motion_control/reactive_qp.hpp>
#include <predictive_motion_sim/plant.hpp>
#include <iomanip>
#include <iostream>
#include <sstream>
using namespace predictive_motion;
using namespace predictive_motion::geometry;
using namespace predictive_motion::control;
Eigen::VectorXd asEigen(const std::vector<double>& x){return Eigen::Map<const Eigen::VectorXd>(x.data(),x.size());}
int main(int argc,char**argv) {
  if(argc!=3)return 2;
  try {
    const std::string root=argv[1];const double dt=.004,subdt=.002;
    Plant plant(root+"/experiments/generated/inspection/scene.xml",subdt);
    RobotKinematics robot(loadConfig(root+"/experiments/generated/phase4/robot.yaml"));Scene geometry(root+"/experiments/generated/phase4/geometry.json");
    std::ifstream input(root+"/results/cad/path_screening_aabb/feasible_path.csv");std::string line;std::getline(input,line);std::getline(input,line);
    std::istringstream cells(line);std::vector<double> v;while(std::getline(cells,line,','))v.push_back(std::stod(line));
    Eigen::VectorXd q(7);for(int i=0;i<7;++i)q(i)=v.at(v.size()-7+i);
    plant.reset(71007);for(int i=0;i<7;++i)plant.data()->qpos[i]=q(i);
    plant.command(plant.names(),std::vector<double>(q.data(),q.data()+7));mj_forward(plant.model(),plant.data());
    for(int i=0;i<1000;++i)plant.step();
    CommandLimits limits{robot.lowerLimits(),robot.upperLimits(),Eigen::VectorXd::Constant(7,.0625),Eigen::VectorXd::Ones(7),Eigen::VectorXd::Constant(7,20),dt,.005};
    CommandHistory history{asEigen(plant.positions()),q,Eigen::VectorXd::Zero(7),Eigen::VectorXd::Zero(7)};
    auto scratch=std::unique_ptr<mjData,decltype(&mj_deleteData)>(mj_makeData(plant.model()),mj_deleteData);
    Eigen::VectorXd previous=asEigen(plant.velocities()),previous_acc=Eigen::VectorXd::Zero(7);
    std::ofstream out(argv[2]);out<<std::setprecision(17)<<"tick,substep,phase,time,command_velocity,command_acceleration,command_jerk,measured_velocity,executed_acceleration_max,executed_jerk_max,true_clearance,contacts,fault_status,stop_status\n";
    double max_acc=0,max_jerk=0,min_clear=1e9,moving_speed=0;bool stopped=false;
    for(int tick=0;tick<1750;++tick) {
      history.measured_position=asEigen(plant.positions());const bool stop=tick>=250;
      Eigen::VectorXd requested=Eigen::VectorXd::Zero(7);requested(6)=.02;
      QpProblem problem=stop?stoppingProblem(7):trackingProblem(Eigen::MatrixXd::Identity(7,7),requested,0);
      std::string fault="NONE";
      if(tick==250) {
        auto bad=problem;bad.gradient(0)=std::numeric_limits<double>::quiet_NaN();auto failed=solveQp(bad);
        if(failed.status!=QpStatus::InvalidInput || failed.velocity.size())throw std::runtime_error("Fault generated usable command");
        fault=statusName(failed.status);moving_speed=std::abs(plant.velocities().at(6));
        if(moving_speed<.005)throw std::runtime_error("Stop injection was not moving");
      }
      problem=constrainCommand(problem,limits,history);
      const double threshold=std::max(.03,.005+2*geometry.motion_radius_bound*((history.accepted_position-history.measured_position).cwiseAbs().sum()+7*.00025)+1e-9);
      auto snapshot=geometry.query(robot,history.measured_position,true,true,threshold);
      for(const auto& pair:snapshot.queries)if(pair.distance<threshold && !(pair.type=="true" && pair.covered_tool_environment))appendDamper(problem,pair.gradient,pair.distance,.005,2);
      auto solution=solveQp(problem);if(solution.status!=QpStatus::Solved)throw std::runtime_error(std::string("Stop infeasible: ")+statusName(solution.status));
      for(int sample=1;sample<=4;++sample) {
        Eigen::VectorXd candidate=history.measured_position+(double(sample)/4)*(history.accepted_position+dt*solution.velocity-history.measured_position);
        auto check=geometry.query(robot,candidate,false,true,-std::numeric_limits<double>::infinity());
        if(check.minimum_true<.005 || check.minimum_cover<.005)throw std::runtime_error("Nonlinear stop rejection");
      }
      const Eigen::VectorXd cmdacc=(solution.velocity-history.accepted_velocity)/dt,cmdjerk=(cmdacc-history.accepted_acceleration)/dt;
      if(cmdacc.cwiseAbs().maxCoeff()>1.00025+1e-8 || cmdjerk.cwiseAbs().maxCoeff()>20.0625+1e-8)throw std::runtime_error("Stop command derivative limit");
      history.accepted_position+=dt*solution.velocity;history.accepted_velocity=solution.velocity;history.accepted_acceleration=cmdacc;
      plant.command(plant.names(),std::vector<double>(history.accepted_position.data(),history.accepted_position.data()+7));
      for(int sub=1;sub<=2;++sub) {
        plant.step();mj_copyData(scratch.get(),plant.model(),plant.data());mj_forward(plant.model(),scratch.get());
        Eigen::VectorXd measured=asEigen(plant.velocities()),acc=(measured-previous)/subdt,jerk=(acc-previous_acc)/subdt;
        previous=measured;previous_acc=acc;
        const auto truth=geometry.query(robot,asEigen(plant.positions()),false,false);min_clear=std::min(min_clear,truth.minimum_true);
        max_acc=std::max(max_acc,acc.cwiseAbs().maxCoeff());max_jerk=std::max(max_jerk,jerk.cwiseAbs().maxCoeff());
        out<<tick<<','<<sub<<','<<(stop?"stopping":"moving")<<','<<plant.time()<<','<<solution.velocity(6)<<','<<cmdacc(6)<<','<<cmdjerk(6)<<','<<measured(6)<<','<<acc.cwiseAbs().maxCoeff()<<','<<jerk.cwiseAbs().maxCoeff()<<','<<truth.minimum_true<<','<<scratch->ncon<<','<<fault<<','<<statusName(solution.status)<<'\n';
        if(scratch->ncon || truth.minimum_true<.005 || acc.cwiseAbs().maxCoeff()>5 || jerk.cwiseAbs().maxCoeff()>500)throw std::runtime_error("Stop physical limit/contact violation");
      }
      if(stop && history.accepted_velocity.cwiseAbs().maxCoeff()<1e-6 && history.accepted_acceleration.cwiseAbs().maxCoeff()<1e-3 && asEigen(plant.velocities()).cwiseAbs().maxCoeff()<1e-4){stopped=true;break;}
    }
    std::cout<<"moving_speed="<<moving_speed<<" stopped="<<stopped<<" max_executed_acc="<<max_acc<<" max_executed_jerk="<<max_jerk<<" min_true_clearance="<<min_clear<<'\n';
    return stopped?0:1;
  }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}
}
