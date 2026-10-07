#include <chrono>
#include <iostream>
#include <rclcpp/rclcpp.hpp>
#include <rosgraph_msgs/msg/clock.hpp>
#include <sensor_msgs/msg/joint_state.hpp>
#include <std_srvs/srv/trigger.hpp>

#include "predictive_motion_sim/plant.hpp"
class Bridge : public rclcpp::Node {
 public:
  Bridge() : Node("mujoco_state_bridge") {
    const auto path = declare_parameter<std::string>("model_path", "");
    seed_ = declare_parameter<int>("seed", 42);
    if (seed_ < 0) throw std::invalid_argument("Seed must be nonnegative");
    const double period = declare_parameter<double>("control_period_seconds", 0.004);
    plant_ = std::make_unique<predictive_motion::Plant>(path, period);
    plant_->reset(static_cast<uint32_t>(seed_));
    pub_ = create_publisher<sensor_msgs::msg::JointState>("joint_states", 10);
    clock_ = create_publisher<rosgraph_msgs::msg::Clock>("clock", 10);
    command_ = create_subscription<sensor_msgs::msg::JointState>(
        "joint_position_command", 10, [this](sensor_msgs::msg::JointState::ConstSharedPtr msg) {
          try {
            plant_->command(msg->name, msg->position);
          } catch (const std::exception& e) {
            RCLCPP_WARN(get_logger(), "Rejected command: %s", e.what());
          }
        });
    reset_ = create_service<std_srvs::srv::Trigger>(
        "reset_simulation", [this](const std::shared_ptr<std_srvs::srv::Trigger::Request>,
                                   std::shared_ptr<std_srvs::srv::Trigger::Response> response) {
          plant_->reset(static_cast<uint32_t>(seed_));
          response->success = true;
          response->message = "Fixed-seed state restored; simulation time reset to zero";
          publish();
        });
    timer_ = create_wall_timer(
        std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::duration<double>(period)),
        [this] {
          plant_->step();
          publish();
        });
  }

 private:
  void publish() {
    auto stamp = rclcpp::Time(static_cast<int64_t>(plant_->time() * 1e9));
    sensor_msgs::msg::JointState msg;
    msg.header.stamp = stamp;
    msg.name = plant_->names();
    msg.position = plant_->positions();
    msg.velocity = plant_->velocities();
    msg.effort = plant_->efforts();
    pub_->publish(msg);
    rosgraph_msgs::msg::Clock c;
    c.clock = stamp;
    clock_->publish(c);
  }
  int seed_{};
  std::unique_ptr<predictive_motion::Plant> plant_;
  rclcpp::Publisher<sensor_msgs::msg::JointState>::SharedPtr pub_;
  rclcpp::Publisher<rosgraph_msgs::msg::Clock>::SharedPtr clock_;
  rclcpp::Subscription<sensor_msgs::msg::JointState>::SharedPtr command_;
  rclcpp::Service<std_srvs::srv::Trigger>::SharedPtr reset_;
  rclcpp::TimerBase::SharedPtr timer_;
};
int main(int argc, char** argv) {
  rclcpp::init(argc, argv);
  try {
    rclcpp::spin(std::make_shared<Bridge>());
  } catch (const std::exception& e) {
    std::cerr << e.what() << '\n';
    rclcpp::shutdown();
    return 1;
  }
  rclcpp::shutdown();
}
