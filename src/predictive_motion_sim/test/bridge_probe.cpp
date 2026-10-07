#include <chrono>
#include <cmath>
#include <iostream>
#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/joint_state.hpp>
#include <std_srvs/srv/trigger.hpp>
#include <thread>
int main(int argc, char** argv) {
  rclcpp::init(argc, argv);
  auto n = std::make_shared<rclcpp::Node>("phase0_bridge_probe");
  int count = 0;
  double initial = 0, latest = 0;
  sensor_msgs::msg::JointState command;
  bool valid = true;
  std::vector<std::vector<double>> reset_states;
  auto sub = n->create_subscription<sensor_msgs::msg::JointState>(
      "joint_states", 10, [&](sensor_msgs::msg::JointState::ConstSharedPtr m) {
        valid = valid && m->name.size() == 7 && m->position.size() == 7 &&
                m->velocity.size() == 7 && m->effort.size() == 7;
        if (!valid) {
          return;
        }
        for (double q : m->position) {
          valid = valid && std::isfinite(q);
        }
        if (m->header.stamp.sec == 0 && m->header.stamp.nanosec == 0) {
          reset_states.push_back(m->position);
        }
        latest = m->position[0];
        if (count++ == 0) {
          initial = latest;
          command.name = m->name;
          command.position = m->position;
          command.position[0] += 0.05;
        }
      });
  auto pub = n->create_publisher<sensor_msgs::msg::JointState>("joint_position_command", 10);
  auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(5);
  while (std::chrono::steady_clock::now() < deadline && rclcpp::ok()) {
    rclcpp::spin_some(n);
    if (count > 0) pub->publish(command);
    std::this_thread::sleep_for(std::chrono::milliseconds(10));
  }
  bool motion = latest - initial > 0.01;
  auto client = n->create_client<std_srvs::srv::Trigger>("reset_simulation");
  bool reset = false;
  if (client->wait_for_service(std::chrono::seconds(2))) {
    reset = true;
    for (int i = 0; i < 2; ++i) {
      auto f = client->async_send_request(std::make_shared<std_srvs::srv::Trigger::Request>());
      if (rclcpp::spin_until_future_complete(n, f, std::chrono::seconds(2)) !=
              rclcpp::FutureReturnCode::SUCCESS ||
          !f.get()->success) {
        reset = false;
        break;
      }
      auto end = std::chrono::steady_clock::now() + std::chrono::seconds(1);
      while (reset_states.size() < static_cast<size_t>(i + 1) &&
             std::chrono::steady_clock::now() < end) {
        rclcpp::spin_some(n);
        std::this_thread::sleep_for(std::chrono::milliseconds(5));
      }
    }
  }
  bool replay = reset_states.size() == 2 && reset_states[0] == reset_states[1];
  std::cout << "messages=" << count << " finite=" << valid << " commanded_motion=" << motion
            << " reset_service=" << reset << " reset_state_identical=" << replay << '\n';
  rclcpp::shutdown();
  return count > 20 && valid && motion && reset && replay ? 0 : 1;
}
