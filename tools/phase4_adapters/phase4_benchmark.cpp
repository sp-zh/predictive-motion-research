#include "geometry.hpp"
#include "measured_position_guard.hpp"
#include <predictive_motion_control/ik.hpp>
#include <predictive_motion_control/reactive_qp.hpp>
#include <predictive_motion_sim/plant.hpp>
#include <Eigen/LU>
#include <Eigen/Cholesky>
#include <chrono>
#include <filesystem>
#include <iomanip>
#include <iostream>
#include <random>
#include <sstream>
#include <cstdio>
#include <fcntl.h>
#include <poll.h>
#include <sys/wait.h>
#include <unistd.h>
using namespace predictive_motion;
using namespace predictive_motion::control;
using namespace predictive_motion::geometry;
using Clock=std::chrono::steady_clock;
double seconds(Clock::time_point begin){return std::chrono::duration<double>(Clock::now()-begin).count();}
Eigen::VectorXd mapped(const std::vector<double>& v){return Eigen::Map<const Eigen::VectorXd>(v.data(),v.size());}
void clipNorm(Eigen::Ref<Eigen::VectorXd> v,double maximum){if(v.norm()>maximum)v*=maximum/v.norm();}
struct ServoReply { Eigen::VectorXd position,velocity;int status=-1,pid=-1;double api=0,sync=0,ipc=0;bool fresh=false; };
class ServoChild {
  pid_t pid=-1;FILE* input=nullptr;FILE* output=nullptr;
 public:
  ServoChild(const std::string& exe,const std::string& directory,const std::string& logfile) {
    int request[2],reply[2];if(pipe(request)||pipe(reply))throw std::runtime_error("IPC pipe");
    pid=fork();if(pid<0)throw std::runtime_error("IPC fork");
    if(pid==0) {
      dup2(request[0],STDIN_FILENO);dup2(reply[1],STDOUT_FILENO);
      int log=open(logfile.c_str(),O_WRONLY|O_CREAT|O_EXCL,0600);if(log<0)_exit(126);
      dup2(log,STDERR_FILENO);close(log);
      close(request[0]);close(request[1]);close(reply[0]);close(reply[1]);
      setenv("ROS_DOMAIN_ID","71",1);setenv("ROS_AUTOMATIC_DISCOVERY_RANGE","LOCALHOST",1);
      execl(exe.c_str(),exe.c_str(),directory.c_str(),nullptr);_exit(127);
    }
    close(request[0]);close(reply[1]);input=fdopen(request[1],"w");output=fdopen(reply[0],"r");
    if(!input||!output)throw std::runtime_error("IPC stream");
  }
  ~ServoChild(){if(input)fclose(input);if(output)fclose(output);if(pid>0){int status;waitpid(pid,&status,0);}}
  ServoReply call(int seq,const Eigen::VectorXd& q,const Eigen::VectorXd& dq,const Vector6& world) {
    const auto start=Clock::now();
    fprintf(input,"%d",seq);for(double x:q)fprintf(input," %.17g",x);
    for(double x:dq)fprintf(input," %.17g",x);for(double x:world)fprintf(input," %.17g",x);
    fputc('\n',input);if(fflush(input))throw std::runtime_error("Servo write failed");
    char* line=nullptr;size_t length=0;ServoReply result;
    while(true) {
      pollfd descriptor{fileno(output),POLLIN,0};
      if(poll(&descriptor,1,10000)<=0){free(line);throw std::runtime_error("Servo timeout");}
      if(getline(&line,&length,output)<=0){free(line);throw std::runtime_error("Servo process failed");}
      std::string text(line);if(text.rfind("RESULT ",0)!=0)continue;
      std::istringstream in(text.substr(7));int received,fresh;
      in>>received>>result.pid>>result.status>>fresh>>result.api>>result.sync;
      result.position.resize(q.size());result.velocity.resize(q.size());
      for(double& x:result.position)in>>x;for(double& x:result.velocity)in>>x;
      free(line);
      if(!in||received!=seq||!result.position.allFinite()||!result.velocity.allFinite())throw std::runtime_error("Invalid Servo reply");
      result.fresh=fresh;result.ipc=seconds(start);return result;
    }
  }
};
struct Observed { Eigen::VectorXd q,dq;Pose tcp;double clearance,seconds,fk_error,frame_error;int contacts;Clock::time_point capture; };
Observed observe(Plant& plant,mjData* scratch,RobotKinematics& robot,const Scene& geometry) {
  const auto start=Clock::now();const auto* model=plant.model();
  const unsigned int spec=mjSTATE_INTEGRATION;std::vector<mjtNum> before(mj_stateSize(model,spec)),after(before.size());
  mj_getState(model,plant.data(),before.data(),spec);
  mj_copyData(scratch,model,plant.data());mj_forward(model,scratch);
  const auto capture=Clock::now();
  const Eigen::VectorXd q=mapped(plant.positions()),dq=mapped(plant.velocities());
  const Pose tcp=robot.tcpPose(q);
  const int site=mj_name2id(model,mjOBJ_SITE,"inspection_tcp");if(site<0)throw std::runtime_error("Missing TCP site");
  Pose actual(Eigen::Map<const Eigen::Matrix<double,3,3,Eigen::RowMajor>>(scratch->site_xmat+9*site),Eigen::Map<const V>(scratch->site_xpos+3*site));
  double fk_error=logResidual(tcp,actual).norm(),frame_error=0;
  for(const auto& object:geometry.objects)if(object.category=="arm") {
    int body=mj_name2id(model,mjOBJ_BODY,object.frame.c_str());if(body<0)throw std::runtime_error("Missing common body");
    Pose physical(Eigen::Map<const Eigen::Matrix<double,3,3,Eigen::RowMajor>>(scratch->xmat+9*body),Eigen::Map<const V>(scratch->xpos+3*body));
    frame_error=std::max(frame_error,logResidual(robot.framePose(q,object.frame),physical).norm());
  }
  auto query=geometry.query(robot,q,false,false);
  mj_getState(model,plant.data(),after.data(),spec);
  if(before!=after||fk_error>1e-8||frame_error>1e-8)throw std::runtime_error("Independent observer contract violated");
  return {q,dq,tcp,query.minimum_true,seconds(start),fk_error,frame_error,scratch->ncon,capture};
}
void vectorCsv(std::ostream& out,const Eigen::VectorXd& v){for(double x:v)out<<','<<x;}
void vectorHeader(std::ostream& out,const std::string& prefix,int n=7){for(int i=1;i<=n;++i)out<<','<<prefix<<i;}
int main(int argc,char**argv) {
  if(argc!=8){std::cerr<<"phase4_benchmark root protocol method seed split raw.csv summary.yaml\n";return 2;}
  try {
    const std::filesystem::path root=argv[1], raw=argv[6], summary=argv[7];
    if(std::filesystem::exists(raw)||std::filesystem::exists(summary))throw std::runtime_error("Refuse evidence overwrite");
    std::filesystem::create_directories(raw.parent_path());std::filesystem::create_directories(summary.parent_path());
    const auto cfg=YAML::LoadFile(argv[2]);const std::string method=argv[3],split=argv[5];
    if(qpSolverVersion()!="1.0.0")throw std::runtime_error("Wrong OSQP runtime ABI/version");
    const uint32_t seed=std::stoul(argv[4]);
    const double dt=cfg["period_s"].as<double>(),subdt=cfg["physics_substep_s"].as<double>();
    const double safe=cfg["collision_safe_m"].as<double>(),activation=cfg["collision_activation_m"].as<double>();
    const double trust=cfg["kinematic_trust_step_rad"].as<double>(),eta=cfg["collision_damper_eta_per_s"].as<double>();
    const double length=cfg["rotation_length_m"].as<double>(),gain=cfg["feedback_gain_per_s"].as<double>();
    Plant plant((root/"experiments/generated/inspection/scene.xml").string(),subdt);
    auto robot_config=loadConfig((root/"experiments/generated/phase4/robot.yaml").string());
    RobotKinematics robot(robot_config);Scene geometry((root/"experiments/generated/phase4/geometry.json").string());
    std::unique_ptr<mjData,decltype(&mj_deleteData)> scratch(mj_makeData(plant.model()),mj_deleteData);
    if(!scratch)throw std::runtime_error("observer allocation");
    std::ifstream csv(root/"results/cad/path_screening_aabb/feasible_path.csv");std::string line;
    std::getline(csv,line);std::getline(csv,line);std::istringstream cells(line);std::vector<double> values;
    while(std::getline(cells,line,','))values.push_back(std::stod(line));
    Eigen::VectorXd initial(7);std::mt19937 rng(seed);
    for(int i=0;i<7;++i)initial(i)=values.at(values.size()-7+i)+(double(rng())/4294967295.-.5)*.0002;
    plant.reset(seed);
    CommandLimits limits;limits.dt=dt;limits.position_margin=cfg["position_margin_rad"].as<double>();
    limits.position_lower=robot.lowerLimits();limits.position_upper=robot.upperLimits();
    limits.velocity=mapped(cfg["velocity_rad_s"].as<std::vector<double>>());
    const Eigen::VectorXd physical_velocity_limit=limits.velocity;
    limits.velocity=limits.velocity.cwiseMin(Eigen::VectorXd::Constant(7,trust/dt));
    limits.acceleration=Eigen::VectorXd::Constant(7,cfg["command_acceleration_rad_s2"].as<double>());
    limits.jerk=Eigen::VectorXd::Constant(7,cfg["command_jerk_rad_s3"].as<double>());
    for(int i=0;i<7;++i) {
      int joint=mj_name2id(plant.model(),mjOBJ_JOINT,plant.names()[i].c_str());
      plant.data()->qpos[plant.model()->jnt_qposadr[joint]]=initial(i);
      limits.position_lower(i)=std::max(limits.position_lower(i),plant.model()->jnt_range[2*joint]);
      limits.position_upper(i)=std::min(limits.position_upper(i),plant.model()->jnt_range[2*joint+1]);
    }
    plant.command(plant.names(),std::vector<double>(initial.data(),initial.data()+7));mj_forward(plant.model(),plant.data());
    CommandHistory history{initial,initial,Eigen::VectorXd::Zero(7),Eigen::VectorXd::Zero(7)};
    QpOptions options;options.max_iterations=cfg["solver_max_iterations"].as<int>();
    options.time_limit_seconds=cfg["solver_time_limit_s"].as<double>();options.max_state_age_seconds=cfg["max_state_age_s"].as<double>();
    std::ofstream out(raw);out.exceptions(std::ios::failbit|std::ios::badbit);out<<std::setprecision(17);
    out<<"tick,substep,time_s,phase,primary_status,command_status,failure,contacts,true_clearance_m,controller_cover_m,pose_position_m,pose_rotation_rad,geometry_s,primary_s,assembly_s,qp_setup_s,qp_solve_s,nonlinear_s,observer_s,state_age_s,active_rows,servo_status,servo_pid,servo_api_s,servo_sync_s,servo_ipc_s,fk_error,frame_error";
    out<<",proposal_qp_status,proposal_qp_raw_status,proposal_qp_api_error,proposal_qp_iterations,proposal_qp_violation,proposal_qp_setup_s,proposal_qp_solve_s,stop_attempted,stop_qp_status";
    for(const auto& name:{"q_requested_","q_accepted_","q_pre_","q_post_","dq_requested_","dq_native_","dq_accepted_","dq_pre_","dq_post_","command_acc_","command_jerk_","executed_acc_","executed_jerk_"})vectorHeader(out,name);
    vectorHeader(out,"desired_translation_",3);vectorHeader(out,"desired_quaternion_xyzw_",4);out<<'\n';
    auto measured=observe(plant,scratch.get(),robot,geometry);
    Eigen::VectorXd previous_dq=measured.dq,previous_acc=Eigen::VectorXd::Zero(7);
    auto reference=YAML::LoadFile((root/"benchmarks/reference/inspection_curve.json").string());
    const V start=vec(reference["start"]),end=vec(reference["end"]);
    const double lateral=reference["lateral_amplitude"].as<double>(),vertical=reference["vertical_amplitude"].as<double>();
    auto xyzw=reference["quaternion_xyzw"].as<std::vector<double>>();
    Pose desired=poseFromXyzw(start,Eigen::Vector4d(xyzw[0],xyzw[1],xyzw[2],xyzw[3]));
    const double path_seconds=cfg["path_s"].as<double>(),settle_seconds=cfg["settle_s"].as<double>();
    const int warmup_ticks=std::lround(cfg["warmup_s"].as<double>()/dt),path_ticks=std::lround((path_seconds+settle_seconds)/dt);
    std::unique_ptr<ServoChild> servo;
    if(method=="moveit_servo") {
      servo=std::make_unique<ServoChild>((root/"build-phase4-servo/servo_sidecar").string(),(root/"experiments/generated/phase4").string(),raw.string()+".servo.log");
      const auto initialized=servo->call(0,measured.q,measured.dq,Vector6::Zero());
      if(!initialized.fresh || (initialized.position-measured.q).norm()>1e-10 || initialized.velocity.norm()>1e-10)
        throw std::runtime_error("Servo zero-request initialization contract");
    }
    bool stopping=false,finished=false;std::string failure,phase="warmup",primary_status="HOLD",command_status="HOLD";
    int rows=0,interventions=0;double peak_error=0,min_clearance=1e9,max_age=0,max_fk=0,max_frame=0;
    double geometry_s=0,primary_s=0,assembly_s=0,nonlinear_s=0,state_age=0,cover_distance=std::numeric_limits<double>::quiet_NaN();
    int active_rows=0;QpResult solution;ServoReply reply;
    QpResult proposal;bool stop_attempted=false;
    Eigen::VectorXd requested=Eigen::VectorXd::Zero(7),native=Eigen::VectorXd::Zero(7),qrequested=initial;
    Eigen::VectorXd cmd_acc=Eigen::VectorXd::Zero(7),cmd_jerk=Eigen::VectorXd::Zero(7);
    auto nonlinearSafe=[&](const Eigen::VectorXd& velocity) {
      const auto begin=Clock::now();const int count=cfg["nonlinear_subdivisions"].as<int>();
      bool valid=true;
      for(const Eigen::VectorXd& target:std::array<Eigen::VectorXd,2>{history.measured_position+dt*velocity,history.accepted_position+dt*velocity}) {
        for(int i=1;i<=count;++i) {
          auto q=history.measured_position+(double(i)/count)*(target-history.measured_position);
          auto query=geometry.query(robot,q,false,true,-std::numeric_limits<double>::infinity());
          if(query.minimum_true<safe || query.minimum_cover<safe)valid=false;
        }
      }
      nonlinear_s+=seconds(begin);return valid;
    };
    for(int tick=0;tick<warmup_ticks+path_ticks+2000 && !finished;++tick) {
      Eigen::VectorXd preq=measured.q,predq=measured.dq;
      geometry_s=primary_s=assembly_s=nonlinear_s=state_age=0;reply=ServoReply{};solution=QpResult{};proposal=QpResult{};stop_attempted=false;active_rows=0;
      if(tick>=warmup_ticks) {
        phase=stopping?"stopping":"path";const auto read_time=measured.capture;history.measured_position=measured.q;
        const double t=(tick-warmup_ticks)*dt,u=std::clamp(t/path_seconds,0.0,1.0);
        const double s=u*u*u*(10+u*(-15+6*u)),ds=30*u*u*(1-u)*(1-u)/path_seconds;
        desired.translation()=(1-s)*start+s*end;desired.translation().y()+=lateral*std::sin(2*M_PI*s);desired.translation().z()+=vertical*std::sin(M_PI*s);
        V world_feedforward=(end-start)*ds;world_feedforward.y()+=lateral*2*M_PI*std::cos(2*M_PI*s)*ds;world_feedforward.z()+=vertical*M_PI*std::cos(M_PI*s)*ds;
        Vector6 target_body=Vector6::Zero();target_body.head<3>()=desired.rotation().transpose()*world_feedforward;
        const auto e=logResidual(measured.tcp,desired);
        Matrix6 left=desiredBodyResidualJacobian(desired,measured.tcp);
        Vector6 body=left.fullPivLu().solve(gain*e+desiredBodyResidualJacobian(measured.tcp,desired)*target_body);
        clipNorm(body.head(3),cfg["max_linear_request_m_s"].as<double>());clipNorm(body.tail(3),cfg["max_angular_request_rad_s"].as<double>());
        Jacobian j=robot.tcpJacobian(measured.q,Reference::Local);Jacobian scaled=j;scaled.bottomRows(3)*=length;
        Vector6 task=body;task.tail<3>()*=length;
        const double relative_motion_bound=2*geometry.motion_radius_bound*((history.accepted_position-measured.q).cwiseAbs().sum()+7*trust);
        const double keep_below=std::max(activation,safe+relative_motion_bound+1e-9);
        const auto geom_begin=Clock::now();auto snapshot=geometry.query(robot,measured.q,true,true,keep_below);
        geometry_s=seconds(geom_begin);cover_distance=snapshot.minimum_cover;
        if(snapshot.minimum_true<safe || snapshot.minimum_cover<safe){stopping=true;if(failure.empty())failure="MEASURED_CLEARANCE_LIMIT";}
        QpProblem problem;const auto primary_begin=Clock::now();primary_status="OK";
        if(!stopping) {
          if(method=="reactive_qp") {problem=trackingProblem(scaled,task,cfg["ridge"].as<double>());requested=problem.hessian.ldlt().solve(-problem.gradient);native=requested;}
          else if(method=="moveit_servo") {
            if(!servo)servo=std::make_unique<ServoChild>((root/"build-phase4-servo/servo_sidecar").string(),(root/"experiments/generated/phase4").string(),raw.string()+".servo.log");
            Vector6 world=body;world.head<3>()=measured.tcp.rotation()*body.head<3>();world.tail<3>()=measured.tcp.rotation()*body.tail<3>();
            reply=servo->call(tick,measured.q,measured.dq,world);native=reply.velocity;requested=(reply.position-history.accepted_position)/dt;
            if(!reply.fresh || reply.status==-1 || reply.status==2 || reply.status==5 || reply.status==6){stopping=true;failure="SERVO_STATUS_"+std::to_string(reply.status);primary_status=failure;}
          } else {
            Options ik;ik.method=method=="mp"?Method::MoorePenrose:method=="fixed_dls"?Method::FixedDls:Method::AdaptiveDls;
            ik.damping=method=="fixed_dls"?cfg["fixed_dls_damping"].as<double>():cfg["adaptive_dls_max_damping"].as<double>();
            ik.adaptive_sigma_threshold=cfg["adaptive_sigma_threshold"].as<double>();
            requested=solve(scaled,task,ik).dq;native=requested;
          }
        }
        primary_s=seconds(primary_begin);qrequested=history.accepted_position+dt*requested;
        if(stopping){problem=stoppingProblem(7);primary_status=failure;}
        else if(method!="reactive_qp")problem=trackingProblem(Eigen::MatrixXd::Identity(7,7),requested,0);
        const auto assembly_begin=Clock::now();problem=constrainCommand(problem,limits,history);
        for(const auto& pair:snapshot.queries)if(pair.distance<keep_below) {
          if(pair.type=="true" && pair.covered_tool_environment)continue;
          appendDamper(problem,pair.gradient,pair.distance,safe,eta);++active_rows;
        }
        assembly_s=seconds(assembly_begin);state_age=seconds(read_time);problem.state_age_seconds=state_age;
        solution=solveQp(problem,options);command_status=statusName(solution.status);
        proposal=solution;
        const bool candidate_safe=solution.status==QpStatus::Solved && nonlinearSafe(solution.velocity);
        state_age=seconds(read_time);
        if(!candidate_safe || state_age>options.max_state_age_seconds) {
          if(!stopping){stopping=true;failure=solution.status!=QpStatus::Solved?command_status:state_age>options.max_state_age_seconds?"STALE_BEFORE_COMMAND":"NONLINEAR_REJECT";}
          stop_attempted=true;
          QpProblem stop=constrainCommand(stoppingProblem(7),limits,history);
          for(const auto& pair:snapshot.queries)if(pair.distance<keep_below && !(pair.type=="true" && pair.covered_tool_environment))appendDamper(stop,pair.gradient,pair.distance,safe,eta);
          // A stopping failure is explicit. No infeasible zero/old command is issued.
          stop.state_age_seconds=seconds(read_time);solution=solveQp(stop,options);
          const bool stop_safe=solution.status==QpStatus::Solved && nonlinearSafe(solution.velocity);
          state_age=seconds(read_time);
          if(!stop_safe || state_age>options.max_state_age_seconds) {
            command_status=std::string("STOP_UNAVAILABLE_")+statusName(solution.status)+"_NO_COMMAND_SIMULATION_TERMINATED";phase="terminated";
            max_age=std::max(max_age,state_age);
            out<<tick<<",0,"<<plant.time()<<','<<phase<<','<<primary_status<<','<<command_status<<','<<failure<<','<<measured.contacts<<','<<measured.clearance<<','<<cover_distance<<','<<e.head<3>().norm()<<','<<e.tail<3>().norm()<<','<<geometry_s<<','<<primary_s<<','<<assembly_s<<','<<solution.setup_seconds<<','<<solution.solve_seconds<<','<<nonlinear_s<<','<<measured.seconds<<','<<state_age<<','<<active_rows<<','<<reply.status<<','<<reply.pid<<','<<reply.api<<','<<reply.sync<<','<<reply.ipc<<','<<measured.fk_error<<','<<measured.frame_error;
            out<<','<<statusName(proposal.status)<<','<<proposal.raw_status<<','<<proposal.api_error<<','<<proposal.iterations<<','<<proposal.violation<<','<<proposal.setup_seconds<<','<<proposal.solve_seconds<<','<<stop_attempted<<','<<statusName(solution.status);
            for(const auto& v:std::array<Eigen::VectorXd,13>{qrequested,history.accepted_position,preq,measured.q,requested,native,history.accepted_velocity,predq,measured.dq,cmd_acc,cmd_jerk,previous_acc,Eigen::VectorXd::Zero(7)})vectorCsv(out,v);
            vectorCsv(out,desired.translation());vectorCsv(out,Eigen::Vector4d(xyzw[0],xyzw[1],xyzw[2],xyzw[3]));out<<'\n';++rows;finished=true;break;
          }
          command_status="STOPPING_SOLVED";
        }
        if(stopping)phase="stopping";
        if((solution.velocity-requested).norm()>1e-6)++interventions;
        cmd_acc=(solution.velocity-history.accepted_velocity)/dt;cmd_jerk=(cmd_acc-history.accepted_acceleration)/dt;
        history.accepted_velocity=solution.velocity;history.accepted_acceleration=cmd_acc;history.accepted_position+=dt*solution.velocity;
        plant.command(plant.names(),std::vector<double>(history.accepted_position.data(),history.accepted_position.data()+7));
      }
      for(int sub=1;sub<=2;++sub) {
        plant.step();measured=observe(plant,scratch.get(),robot,geometry);
        Eigen::VectorXd acc=(measured.dq-previous_dq)/subdt,jerk=(acc-previous_acc)/subdt;
        previous_dq=measured.dq;previous_acc=acc;
        Vector6 e=logResidual(measured.tcp,desired);peak_error=std::max(peak_error,e.head<3>().norm());
        min_clearance=std::min(min_clearance,measured.clearance);max_age=std::max(max_age,state_age);
        max_fk=std::max(max_fk,measured.fk_error);max_frame=std::max(max_frame,measured.frame_error);
        out<<tick<<','<<sub<<','<<plant.time()<<','<<phase<<','<<primary_status<<','<<command_status<<','<<failure<<','<<measured.contacts<<','<<measured.clearance<<','<<cover_distance<<','<<e.head<3>().norm()<<','<<e.tail<3>().norm()<<','<<geometry_s<<','<<primary_s<<','<<assembly_s<<','<<solution.setup_seconds<<','<<solution.solve_seconds<<','<<nonlinear_s<<','<<measured.seconds<<','<<state_age<<','<<active_rows<<','<<reply.status<<','<<reply.pid<<','<<reply.api<<','<<reply.sync<<','<<reply.ipc<<','<<measured.fk_error<<','<<measured.frame_error;
        out<<','<<statusName(proposal.status)<<','<<proposal.raw_status<<','<<proposal.api_error<<','<<proposal.iterations<<','<<proposal.violation<<','<<proposal.setup_seconds<<','<<proposal.solve_seconds<<','<<stop_attempted<<','<<(stop_attempted?statusName(solution.status):"NOT_ATTEMPTED");
        for(const auto& v:std::array<Eigen::VectorXd,13>{qrequested,history.accepted_position,preq,measured.q,requested,native,history.accepted_velocity,predq,measured.dq,cmd_acc,cmd_jerk,acc,jerk})vectorCsv(out,v);
        vectorCsv(out,desired.translation());vectorCsv(out,Eigen::Vector4d(xyzw[0],xyzw[1],xyzw[2],xyzw[3]));out<<'\n';++rows;
        if(tick>=warmup_ticks && !stopping &&
           (!measuredPositionSafe(measured.q,limits.position_lower,limits.position_upper) || measured.contacts || measured.clearance<safe || (measured.dq.cwiseAbs().array()>physical_velocity_limit.array()).any() ||
            acc.cwiseAbs().maxCoeff()>cfg["executed_acceleration_rad_s2"].as<double>() || jerk.cwiseAbs().maxCoeff()>cfg["executed_jerk_rad_s3"].as<double>())) {
          stopping=true;failure="EXECUTED_SAFETY_LIMIT";
        }
      }
      if(tick==warmup_ticks-1) {
        if(measured.contacts || measured.clearance<safe || measured.dq.cwiseAbs().maxCoeff()>1e-4) {failure="WARMUP_FAILED";finished=true;}
      }
      if(stopping && history.accepted_velocity.cwiseAbs().maxCoeff()<1e-6 && measured.dq.cwiseAbs().maxCoeff()<1e-4)finished=true;
      if(tick>=warmup_ticks+path_ticks-1 && !stopping)finished=true;
    }
    const Vector6 final=logResidual(measured.tcp,desired);
    bool completed=failure.empty() && final.head<3>().norm()<=cfg["completion_position_m"].as<double>() && final.tail<3>().norm()<=cfg["completion_rotation_rad"].as<double>();
    if(failure.empty() && !completed)failure="POSE_TOLERANCE";
    YAML::Emitter report;report<<YAML::BeginMap<<YAML::Key<<"method"<<YAML::Value<<method<<YAML::Key<<"seed"<<YAML::Value<<seed<<YAML::Key<<"split"<<YAML::Value<<split
      <<YAML::Key<<"completed"<<YAML::Value<<completed<<YAML::Key<<"failure"<<YAML::Value<<failure<<YAML::Key<<"rows"<<YAML::Value<<rows
      <<YAML::Key<<"final_position_m"<<YAML::Value<<final.head<3>().norm()<<YAML::Key<<"final_rotation_rad"<<YAML::Value<<final.tail<3>().norm()
      <<YAML::Key<<"minimum_true_clearance_m"<<YAML::Value<<min_clearance<<YAML::Key<<"peak_position_m"<<YAML::Value<<peak_error
      <<YAML::Key<<"interventions"<<YAML::Value<<interventions<<YAML::Key<<"max_state_age_s"<<YAML::Value<<max_age
      <<YAML::Key<<"max_fk_error"<<YAML::Value<<max_fk<<YAML::Key<<"max_frame_error"<<YAML::Value<<max_frame<<YAML::EndMap;
    std::ofstream(summary)<<report.c_str()<<'\n';std::cout<<method<<' '<<seed<<" completed="<<completed<<" failure="<<failure<<" rows="<<rows<<std::endl;
    return 0;
  }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}
}
