// Actual installed MoveIt Servo 2.12.4 C++ API. This process never links OSQP 1.x.
#include <moveit_servo/servo.hpp>
#include <moveit/robot_model_loader/robot_model_loader.hpp>
#include <moveit/planning_scene_monitor/planning_scene_monitor.hpp>
#include <moveit_msgs/msg/collision_object.hpp>
#include <sensor_msgs/msg/joint_state.hpp>
#include <shape_msgs/msg/solid_primitive.hpp>
#include <shape_msgs/msg/plane.hpp>
#include <yaml-cpp/yaml.h>
#include <chrono>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <mutex>
#include <sstream>
#include <thread>
#include <unistd.h>
#include <execinfo.h>
#include <csignal>
namespace {
std::string read(const std::string& name) {
  std::ifstream in(name); if(!in)throw std::runtime_error("missing "+name);
  return std::string(std::istreambuf_iterator<char>(in),{});
}
struct Request {
  uint64_t seq=0;
  Eigen::VectorXd q=Eigen::VectorXd::Zero(7),dq=Eigen::VectorXd::Zero(7);
  Eigen::Vector<double,6> twist=Eigen::Vector<double,6>::Zero();
};
bool parse(const std::string& line,Request& r) {
  std::istringstream in(line);in>>r.seq;
  for(int i=0;i<7;++i)in>>r.q(i);
  for(int i=0;i<7;++i)in>>r.dq(i);
  for(int i=0;i<6;++i)in>>r.twist(i);
  return bool(in) && r.q.allFinite() && r.dq.allFinite() && r.twist.allFinite();
}
}
int main(int argc,char**argv) {
  if(argc!=2)return 2;
  std::signal(SIGSEGV, [](int signal){void* frames[64];int n=backtrace(frames,64);backtrace_symbols_fd(frames,n,2);_exit(128+signal);});
  try {
    const std::string directory=argv[1];
    std::string line;Request request;
    if(!std::getline(std::cin,line) || !parse(line,request))return 2;
    rclcpp::init(argc,argv);
    rclcpp::NodeOptions options;
    options.parameter_overrides({
      rclcpp::Parameter("robot_description",read(directory+"/servo_arm.urdf")),
      rclcpp::Parameter("robot_description_semantic",read(directory+"/servo_arm.srdf")),
      rclcpp::Parameter("robot_description_kinematics.arm.kinematics_solver","kdl_kinematics_plugin/KDLKinematicsPlugin"),
      rclcpp::Parameter("robot_description_kinematics.arm.kinematics_solver_timeout",.05),
      rclcpp::Parameter("moveit_servo.move_group_name","arm"),
      rclcpp::Parameter("moveit_servo.publish_period",.004),
      rclcpp::Parameter("moveit_servo.command_in_type","speed_units"),
      rclcpp::Parameter("moveit_servo.check_collisions",true),
      rclcpp::Parameter("moveit_servo.collision_check_rate",250.0),
      rclcpp::Parameter("moveit_servo.use_smoothing",true),
      rclcpp::Parameter("moveit_servo.joint_limit_margins",std::vector<double>{.005}),
      rclcpp::Parameter("moveit_servo.is_primary_planning_scene_monitor",false),
      rclcpp::Parameter("moveit_servo.apply_twist_commands_about_ee_frame",true)});
    auto node=std::make_shared<rclcpp::Node>("phase4_actual_servo",options);
    rclcpp::executors::SingleThreadedExecutor executor;executor.add_node(node);
    std::thread spin([&]{executor.spin();});
    auto loader=std::make_shared<robot_model_loader::RobotModelLoader>(node,"robot_description",true);
    auto monitor=std::make_shared<planning_scene_monitor::PlanningSceneMonitor>(node,loader);
    if(!monitor->getPlanningScene())throw std::runtime_error("No planning scene");
    auto model=monitor->getRobotModel();auto group=model->getJointModelGroup("arm");
    const auto names=group->getActiveJointModelNames();
    if(names.size()!=7)throw std::runtime_error("Expected seven joints");
    // Actual CSM needs measured JointState timestamps before Servo constructor.
    monitor->startStateMonitor("phase4_measured_joints");
    monitor->getStateMonitor()->enableCopyDynamics(true);
    auto publisher=node->create_publisher<sensor_msgs::msg::JointState>("phase4_measured_joints",10);
    std::mutex mutex;Request latest=request;std::atomic<bool> publishing{true};
    std::thread publish([&]{
      while(publishing && rclcpp::ok()) {
        sensor_msgs::msg::JointState msg;msg.name=names;msg.header.stamp=node->now();
        {std::lock_guard<std::mutex> lock(mutex);
         msg.position.assign(latest.q.data(),latest.q.data()+7);msg.velocity.assign(latest.dq.data(),latest.dq.data()+7);}
        publisher->publish(msg);std::this_thread::sleep_for(std::chrono::milliseconds(2));
      }
    });
    auto config=YAML::LoadFile(directory+"/geometry.json");
    {
      planning_scene_monitor::LockedPlanningSceneRW scene(monitor);
      scene->getCurrentStateNonConst().setJointGroupPositions(group,request.q);
      scene->getCurrentStateNonConst().setJointGroupVelocities(group,request.dq);
      scene->getCurrentStateNonConst().update();
      for(auto primitive:config["primitives"])if(primitive["body"].as<std::string>()=="inspection_fixture") {
        moveit_msgs::msg::CollisionObject object;object.header.frame_id="base";
        object.id=primitive["name"].as<std::string>();object.operation=object.ADD;
        shape_msgs::msg::SolidPrimitive box;box.type=box.BOX;
        for(auto s:primitive["size_m"])box.dimensions.push_back(2*s.as<double>());
        geometry_msgs::msg::Pose pose;pose.orientation.w=1;
        pose.position.x=primitive["local_position_m"][0].as<double>();
        pose.position.y=primitive["local_position_m"][1].as<double>();
        pose.position.z=primitive["local_position_m"][2].as<double>();
        object.primitives.push_back(box);object.primitive_poses.push_back(pose);
        if(!scene->processCollisionObjectMsg(object))throw std::runtime_error("fixture rejected");
      }
      moveit_msgs::msg::CollisionObject floor;floor.id="floor";floor.header.frame_id="base";floor.operation=floor.ADD;
      // This backend crashes for mesh/plane queries. The finite box contains
      // every reachable below-floor point (top=floor_z, bottom=floor_z-8m).
      const double floor_z=config["floor_z"].as<double>();
      if(std::abs(floor_z)+config["motion_radius_bound_m"].as<double>()>=2)
        throw std::runtime_error("Finite floor enclosure bound unsupported");
      shape_msgs::msg::SolidPrimitive floor_box;floor_box.type=floor_box.BOX;
      floor_box.dimensions={8,8,8};floor.primitives.push_back(floor_box);
      geometry_msgs::msg::Pose origin;origin.orientation.w=1;origin.position.z=floor_z-4;floor.primitive_poses.push_back(origin);
      scene->processCollisionObjectMsg(floor);
      scene->getAllowedCollisionMatrixNonConst().setEntry("fr3_link0","floor",true);
    }
    auto listener=std::make_shared<servo::ParamListener>(node,"moveit_servo");
    {
      moveit_servo::Servo servo(node,listener,monitor);
      servo.setCommandType(moveit_servo::CommandType::TWIST);
      moveit_servo::KinematicState initial(7);
      initial.joint_names=names;initial.positions=request.q;initial.velocities=request.dq;
      initial.accelerations=Eigen::VectorXd::Zero(7);servo.resetSmoothing(initial);
      do {
        const auto start=std::chrono::steady_clock::now();
        {std::lock_guard<std::mutex> lock(mutex);latest=request;}
        bool synchronized=false;
        for(int attempt=0;attempt<40;++attempt) {
          Eigen::VectorXd received;
          Eigen::VectorXd received_velocity;
          auto current=monitor->getStateMonitor()->getCurrentState();
          current->copyJointGroupPositions(group,received);current->copyJointGroupVelocities(group,received_velocity);
          if((received-request.q).cwiseAbs().maxCoeff()<1e-12 && (received_velocity-request.dq).cwiseAbs().maxCoeff()<1e-12){synchronized=true;break;}
          std::this_thread::sleep_for(std::chrono::milliseconds(1));
        }
        auto state=std::make_shared<moveit::core::RobotState>(model);
        state->setJointGroupPositions(group,request.q);state->setJointGroupVelocities(group,request.dq);state->update();
        {
          planning_scene_monitor::LockedPlanningSceneRW scene(monitor);
          scene->getCurrentStateNonConst()=*state;
        }
        // Real collision monitor remains asynchronous at 250Hz. A current-state
        // CSM match is not proof its last collision cycle used that state; the
        // external common supervisor independently checks measured-state safety.
        const auto api_start=std::chrono::steady_clock::now();
        moveit_servo::TwistCommand command;command.frame_id="base";command.velocities=request.twist;
        auto next=servo.getNextJointState(state,command);
        const auto end=std::chrono::steady_clock::now();
        std::cout<<std::setprecision(17)<<"RESULT "<<request.seq<<' '<<getpid()<<' '
                 <<static_cast<int>(servo.getStatus())<<' '<<synchronized<<' '
                 <<std::chrono::duration<double>(end-api_start).count()<<' '
                 <<std::chrono::duration<double>(end-start).count();
        for(int i=0;i<next.positions.size();++i)std::cout<<' '<<next.positions(i);
        for(int i=0;i<next.velocities.size();++i)std::cout<<' '<<next.velocities(i);
        std::cout<<std::endl;
      }while(std::getline(std::cin,line) && parse(line,request));
    }
    publishing=false;publish.join();executor.cancel();spin.join();rclcpp::shutdown();
    return 0;
  }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}
}
