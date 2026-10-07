#include <Eigen/Cholesky>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <predictive_motion_sim/plant.hpp>
#include <random>
#include <sstream>

#include "linearization.hpp"
#include "measured_position_guard.hpp"
#include "observation.hpp"
using namespace predictive_motion;
using namespace predictive_motion::control;
using namespace predictive_motion::geometry;
using namespace predictive_motion::preview_adapter;
using Clock = std::chrono::steady_clock;
double seconds(Clock::time_point begin) {
  return std::chrono::duration<double>(Clock::now() - begin).count();
}
void vectorCsv(std::ostream& out, const Eigen::VectorXd& v) {
  for (double x : v) out << ',' << x;
}
void snapshotCsv(const std::filesystem::path& file,const Eigen::MatrixXd& matrix) {
  std::ofstream out(file);out.exceptions(std::ios::failbit|std::ios::badbit);
  out<<std::scientific<<std::setprecision(17);
  for(int i=0;i<matrix.rows();++i) {
    for(int j=0;j<matrix.cols();++j) {if(j)out<<',';out<<matrix(i,j);}
    out<<'\n';
  }
}
void headers(std::ostream& out, const std::string& prefix, int n = 7) {
  for (int i = 0; i < n; ++i) out << ',' << prefix << i;
}
int main(int argc, char** argv) {
  if (argc != 7) {
    std::cerr << "phase5_benchmark root protocol method scenario seed fresh_raw_directory\n";
    return 2;
  }
  try {
    const std::filesystem::path root = argv[1], dir = argv[6];
    const std::string method = argv[3], scenario = argv[4];
    const uint32_t seed = std::stoul(argv[5]);
    if (method != "predictive" && method != "reactive_qp")
      throw std::runtime_error("unknown method");
    if (std::filesystem::exists(dir)) throw std::runtime_error("Refuse evidence overwrite");
    std::filesystem::create_directories(dir);
    auto cfg = YAML::LoadFile(argv[2]);
    bool reference_mode = cfg["execution_mode"] &&
                          cfg["execution_mode"].as<std::string>() == "paused_simulation_reference";
    double plan_origin_age = 0;
    double dt = cfg["control_dt_s"].as<double>(), subdt = cfg["physics_substep_s"].as<double>(),
           safe = cfg["collision_safe_m"].as<double>(),
           length = cfg["rotation_length_m"].as<double>();
    if (std::abs(dt - 2 * subdt) > 1e-14 || qpSolverVersion() != "1.0.0")
      throw std::runtime_error("control/physics mesh or solver identity");
    Plant plant((root / "experiments/generated/inspection/scene.xml").string(), subdt);
    RobotKinematics robot(loadConfig((root / "experiments/generated/phase4/robot.yaml").string()));
    Scene geometry((root / "experiments/generated/phase5/geometry.json").string());
    std::unique_ptr<mjData, decltype(&mj_deleteData)> scratch(mj_makeData(plant.model()),
                                                              mj_deleteData);
    std::ifstream pathfile(root / "results/cad/path_screening_aabb/feasible_path.csv");
    std::string line;
    std::getline(pathfile, line);
    std::getline(pathfile, line);
    std::istringstream cells(line);
    std::vector<double> values;
    while (std::getline(cells, line, ',')) values.push_back(std::stod(line));
    Eigen::VectorXd initial(7);
    std::mt19937 rng(seed);
    for (int i = 0; i < 7; ++i)
      initial(i) = values.at(values.size() - 7 + i) + (double(rng()) / 4294967295. - .5) * .0002;
    plant.reset(seed);
    Eigen::VectorXd physical_lo = robot.lowerLimits(), physical_hi = robot.upperLimits();
    auto inherited_cfg = YAML::LoadFile((root / "config/phase4.yaml").string());
    Eigen::VectorXd physical_velocity =
        mapped(inherited_cfg["velocity_rad_s"].as<std::vector<double>>());
    for (int i = 0; i < 7; ++i) {
      int joint = mj_name2id(plant.model(), mjOBJ_JOINT, plant.names()[i].c_str());
      plant.data()->qpos[plant.model()->jnt_qposadr[joint]] = initial(i);
      physical_lo(i) = std::max(physical_lo(i), plant.model()->jnt_range[2 * joint]);
      physical_hi(i) = std::min(physical_hi(i), plant.model()->jnt_range[2 * joint + 1]);
    }
    plant.command(plant.names(), std::vector<double>(initial.data(), initial.data() + 7));
    mj_forward(plant.model(), plant.data());

    // Independent local servo identification/validation fixture. Only the
    // existing accepted position target interface is excited; no future plant
    // query is used as a predictor. Data is fitted later from completed traces.
    const bool validation=scenario=="servo_validation";
    if(!validation) throw std::runtime_error("new validation-only fixture; training is not repeated");
    const double frequency_base=cfg["validation_frequency_base_hz"].as<double>();
    const double frequency_step=cfg["validation_frequency_step_hz"].as<double>();
    const double phase_step=cfg["validation_phase_step_rad"].as<double>();
    std::ifstream reference(cfg["accepted_reference_csv"].as<std::string>());
    if(!reference) throw std::runtime_error("missing frozen accepted-target reference");
    std::string reference_line;std::getline(reference,reference_line);
    std::vector<Eigen::VectorXd> offsets;
    while(std::getline(reference,reference_line)) {
      std::istringstream stream(reference_line);std::string cell;std::getline(stream,cell,',');
      if(std::stoi(cell)!=int(offsets.size()))throw std::runtime_error("reference clock");
      Eigen::VectorXd offset(7);for(int j=0;j<7;++j){std::getline(stream,cell,',');offset(j)=std::stod(cell);}offsets.push_back(offset);
    }
    if(offsets.size()!=928||!offsets.front().isZero(0))throw std::runtime_error("reference identity/dimension");
    bool forced_stop=false;std::string primary_failure,stop_failure;
    const double duration=cfg["identification_duration_s"].as<double>();
    const double amplitude=cfg["identification_amplitude_rad"].as<double>();
    CommandLimits bounds{physical_lo,physical_hi,
      Eigen::VectorXd::Constant(7,cfg["command_velocity_rad_s"].as<double>()),
      Eigen::VectorXd::Constant(7,cfg["command_acceleration_rad_s2"].as<double>()),
      Eigen::VectorXd::Constant(7,cfg["command_jerk_rad_s3"].as<double>()),dt,
      cfg["position_margin_rad"].as<double>()};
    CommandHistory history{initial,initial,Eigen::VectorXd::Zero(7),Eigen::VectorXd::Zero(7)};
    QpOptions o;o.absolute_tolerance=o.relative_tolerance=1e-9;
    o.acceptance_tolerance=1e-7;o.max_iterations=4000;
    o.time_limit_seconds=o.max_state_age_seconds=.05;
    std::ofstream raw(dir/"raw.csv"),cycles(dir/"cycles.csv");
    raw<<std::setprecision(17)<<"tick,substep,time_s,phase,contacts,true_clearance_m";
    for(auto prefix:{"q_before_","v_before_","target_","q_post_","v_post_","command_velocity_",
                     "command_acceleration_","command_jerk_","physical_acceleration_","physical_jerk_"})
      headers(raw,prefix);
    raw<<'\n';cycles<<std::setprecision(17)<<"tick,full_cycle_wall_s,command_age_s,status,deadline_miss\n";
    auto measured=observe(plant,scratch.get(),robot,geometry);
    Eigen::VectorXd previous_v=measured.dq,previous_a=Eigen::VectorXd::Zero(7);
    const int warmup=std::lround(2./dt),task=std::lround(duration/dt);
    bool completed=false;double min_clear=INFINITY,max_velocity=0;
    for(int tick=0;tick<warmup+task+1250;++tick) {
      auto begin=Clock::now();measured=observe(plant,scratch.get(),robot,geometry);
      history.measured_position=measured.q;
      auto capture=measured.capture;double command_age=0;
      Eigen::VectorXd acceleration=Eigen::VectorXd::Zero(7),jerk=acceleration;
      std::string status="HOLD";
      if(tick>=warmup) {
        const double t=(tick-warmup)*dt;
        Eigen::VectorXd request=Eigen::VectorXd::Zero(7);
        if(tick<warmup+task && !forced_stop) {
          Eigen::VectorXd desired=initial+offsets.at(std::min(tick,int(offsets.size()-1)));
          request=(desired-history.accepted_position)/dt;
        }
        auto q=constrainPreviewCommand(trackingProblem(Eigen::MatrixXd::Identity(7,7),request,0),bounds,history);
        auto query=geometry.query(robot,measured.q,true,true,.03);
        for(const auto& pair:query.queries)
          if(!(pair.type=="true"&&pair.covered_tool_environment)&&pair.distance<.03)
            appendDamper(q,pair.gradient,pair.distance,safe,2.);
        q.state_age_seconds=seconds(capture);
        auto validCommand=[&](const QpResult& candidate) {
          if(candidate.status!=QpStatus::Solved)return false;
          for(const Eigen::VectorXd& end:std::array<Eigen::VectorXd,2>{(measured.q+dt*candidate.velocity).eval(),(history.accepted_position+dt*candidate.velocity).eval()})
            for(int k=1;k<=4;++k){Eigen::VectorXd at=measured.q+double(k)/4*(end-measured.q);auto g=geometry.query(robot,at,false,true,-INFINITY);if(std::min(g.minimum_true,g.minimum_cover)<safe)return false;}
          return seconds(capture)<=.05;
        };
        auto result=solveQp(q,o);status=statusName(result.status);
        if(!validCommand(result)&&!forced_stop){
          forced_stop=true;primary_failure=result.status==QpStatus::Solved?"NONLINEAR_OR_STALE":status;
          snapshotCsv(dir/"first_rejected_H.csv",q.hessian);snapshotCsv(dir/"first_rejected_g.csv",q.gradient);
          snapshotCsv(dir/"first_rejected_A.csv",q.constraints);snapshotCsv(dir/"first_rejected_lower.csv",q.lower);snapshotCsv(dir/"first_rejected_upper.csv",q.upper);
        }
        if(forced_stop || tick>=warmup+task){
          measured=observe(plant,scratch.get(),robot,geometry);capture=measured.capture;history.measured_position=measured.q;
          auto stop=constrainPreviewCommand(stoppingProblem(7),bounds,history);
          double keep=.03+2*geometry.motion_radius_bound*((history.accepted_position-measured.q).cwiseAbs().sum()+7*.00025);
          auto snapshot=geometry.query(robot,measured.q,true,true,keep);
          for(const auto& pair:snapshot.queries)if(!(pair.type=="true"&&pair.covered_tool_environment)&&pair.distance<keep)appendDamper(stop,pair.gradient,pair.distance,safe,2.);
          stop.state_age_seconds=seconds(capture);result=solveQp(stop,o);status=statusName(result.status);
          if(!validCommand(result)){
            stop_failure=status+"_NO_FEASIBLE_STOP_NO_COMMAND_SIMULATION_TERMINATED";
            snapshotCsv(dir/"stop_H.csv",stop.hessian);snapshotCsv(dir/"stop_g.csv",stop.gradient);snapshotCsv(dir/"stop_A.csv",stop.constraints);snapshotCsv(dir/"stop_lower.csv",stop.lower);snapshotCsv(dir/"stop_upper.csv",stop.upper);
            cycles<<tick<<','<<seconds(begin)<<','<<seconds(capture)<<','<<stop_failure<<','<<(seconds(begin)>dt)<<'\n';cycles.flush();break;
          }
        }
        command_age=seconds(capture);
        Eigen::VectorXd next=history.accepted_position+dt*result.velocity;
        acceleration=(result.velocity-history.accepted_velocity)/dt;
        jerk=(acceleration-history.accepted_acceleration)/dt;
        history.accepted_velocity=result.velocity;history.accepted_acceleration=acceleration;history.accepted_position=next;
        plant.command(plant.names(),std::vector<double>(next.data(),next.data()+7));

      }
      for(int sub=1;sub<=2;++sub) {
        auto q_before=measured.q,v_before=measured.dq;
        plant.step();measured=observe(plant,scratch.get(),robot,geometry);
        Eigen::VectorXd physical_a=(measured.dq-previous_v)/subdt;
        Eigen::VectorXd physical_j=(physical_a-previous_a)/subdt;
        previous_v=measured.dq;previous_a=physical_a;
        raw<<tick<<','<<sub<<','<<plant.time()<<','
           <<(tick<warmup?"warmup":forced_stop||tick>=warmup+task?"stopping":"excitation")
           <<','<<measured.contacts<<','<<measured.clearance;
        for(const auto& v:std::vector<Eigen::VectorXd>{q_before,v_before,history.accepted_position,
              measured.q,measured.dq,history.accepted_velocity,acceleration,jerk,physical_a,physical_j})vectorCsv(raw,v);
        raw<<'\n';min_clear=std::min(min_clear,measured.clearance);
        max_velocity=std::max(max_velocity,measured.dq.cwiseAbs().maxCoeff());
        if(measured.contacts||measured.clearance<safe||(measured.dq.array().abs()>physical_velocity.array()).any()||
           !measuredPositionSafe(measured.q,physical_lo,physical_hi)||
           (tick>=warmup&&(physical_a.cwiseAbs().maxCoeff()>5||physical_j.cwiseAbs().maxCoeff()>500)))
          throw std::runtime_error("identification executed safety");
      }
      raw.flush();double wall=seconds(begin);
      cycles<<tick<<','<<wall<<','<<command_age<<','<<status<<','<<(wall>dt)<<'\n';cycles.flush();
      if((forced_stop||tick>=warmup+task)&&history.accepted_velocity.cwiseAbs().maxCoeff()<1e-6&&
         measured.dq.cwiseAbs().maxCoeff()<1e-4) {completed=true;break;}
    }
    YAML::Emitter summary;summary<<YAML::BeginMap<<YAML::Key<<"scope"<<YAML::Value
      <<"Local servo identification/held-out development validation fixture; not a motion research trial"
      <<YAML::Key<<"seed"<<YAML::Value<<seed<<YAML::Key<<"fixture"<<YAML::Value<<scenario
      <<YAML::Key<<"primary_failure"<<YAML::Value<<primary_failure<<YAML::Key<<"stop_failure"<<YAML::Value<<stop_failure<<YAML::Key<<"completed_stop"<<YAML::Value<<completed<<YAML::Key<<"min_clearance_m"<<YAML::Value<<min_clear
      <<YAML::Key<<"max_physical_velocity_rad_s"<<YAML::Value<<max_velocity<<YAML::EndMap;
    std::ofstream(dir/"summary.yaml")<<summary.c_str()<<'\n';std::cout<<summary.c_str()<<'\n';
    return completed&&primary_failure.empty()?0:3;
  } catch(const std::exception& e) {std::cerr<<e.what()<<'\n';return 1;}
}
