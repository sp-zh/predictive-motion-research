#include <mujoco/mujoco.h>

#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <sstream>

#include "linearization.hpp"
using namespace predictive_motion;
using namespace predictive_motion::preview_adapter;
std::vector<std::string> split(const std::string& text) {
  std::vector<std::string> out;
  std::istringstream in(text);
  std::string value;
  while (std::getline(in, value, ',')) out.push_back(value);
  return out;
}
void csv(const std::filesystem::path& file, const Eigen::MatrixXd& matrix) {
  auto part = file;
  part += ".part";
  std::ofstream out(part);
  out.exceptions(std::ios::failbit | std::ios::badbit);
  out << std::scientific << std::setprecision(17);
  for (int i = 0; i < matrix.rows(); ++i) {
    for (int j = 0; j < matrix.cols(); ++j) {
      if (j) out << ',';
      out << matrix(i, j);
    }
    out << '\n';
  }
  out.close();
  std::filesystem::rename(part, file);
}
int main(int argc, char** argv) {
  if (argc != 5 && argc != 6) {
    std::cerr << "dump_first_qp root protocol recorded_raw fresh_snapshot_dir [recorded_tick]\n";
    return 2;
  }
  try {
    std::filesystem::path root = argv[1], out = argv[4];
    if (std::filesystem::exists(out)) throw std::runtime_error("Refuse snapshot overwrite");
    std::filesystem::create_directories(out);
    auto cfg = YAML::LoadFile(argv[2]);
    std::ifstream raw(argv[3]);
    std::string line;
    std::getline(raw, line);
    auto names = split(line);
    std::map<std::string, int> index;
    for (int i = 0; i < int(names.size()); ++i) index[names[i]] = i;
    std::vector<std::string> record;
    while (std::getline(raw, line)) {
      auto fields = split(line);
      if (argc == 6 ? (std::stoi(fields.at(index.at("tick"))) == std::stoi(argv[5]) &&
                       fields.at(index.at("substep")) == "2")
                    : fields.at(index.at("phase")) == "warmup") record = fields;
    }
    if (record.empty()) throw std::runtime_error("No selected recorded state");
    auto scalar = [&](const std::string& name) { return std::stod(record.at(index.at(name))); };
    auto vector = [&](const std::string& prefix) {
      Eigen::VectorXd value(7);
      for (int i = 0; i < 7; ++i) value(i) = scalar(prefix + std::to_string(i));
      return value;
    };
    RobotKinematics robot(loadConfig((root / "experiments/generated/phase4/robot.yaml").string()));
    Scene geometry((root / "experiments/generated/phase5/geometry.json").string());
    PreviewInput input;
    input.initial = {vector("q_post_"), vector("dq_post_"), scalar("s"), scalar("r")};
    input.accepted_position = vector("q_accepted_");
    input.accepted_velocity = vector("dq_accepted_");
    input.previous_acceleration = vector("command_acc_");
    input.previous_model_acceleration = vector("applied_model_acc_");
    input.previous_progress_acceleration = scalar("b");
    input.control_dt = cfg["control_dt_s"].as<double>();
    input.mesh = cfg["prediction_mesh_s"].as<std::vector<double>>();
    input.nominal = Eigen::VectorXd::Zero(input.mesh.size() * 8);
    input.lifted = cfg["qp_formulation"].as<std::string>() == "lifted";
    input.capture_dense_terms = false;
    input.joint_trust = cfg["joint_trust_rad"].as<double>();
    input.progress_trust = cfg["progress_trust"].as<double>();
    input.terminal_stop = cfg["terminal_stop"].as<bool>();
    auto& limits = input.limits;
    limits.lower = robot.lowerLimits();
    limits.upper = robot.upperLimits();
    limits.posture = input.accepted_position;
    limits.velocity = Eigen::VectorXd::Constant(7, cfg["command_velocity_rad_s"].as<double>());
    limits.acceleration =
        Eigen::VectorXd::Constant(7, cfg["command_acceleration_rad_s2"].as<double>());
    limits.jerk = Eigen::VectorXd::Constant(7, cfg["command_jerk_rad_s3"].as<double>());
    limits.progress_speed = cfg["progress_speed"].as<double>();
    limits.progress_acceleration = cfg["progress_acceleration"].as<double>();
    limits.progress_jerk = cfg["progress_jerk"].as<double>();
    limits.position_margin = cfg["position_margin_rad"].as<double>();
    limits.safe_distance = cfg["collision_safe_m"].as<double>();
    // Load only static model ranges. No mjData allocation, reset, step or future
    // plant state is used in this assembly-only replay.
    char error[1024];
    std::unique_ptr<mjModel, decltype(&mj_deleteModel)> model(
        mj_loadXML((root / "experiments/generated/inspection/scene.xml").c_str(), nullptr, error,
                   sizeof(error)),
        mj_deleteModel);
    if (!model) throw std::runtime_error(error);
    for (int i = 0; i < 7; ++i) {
      int joint = mj_name2id(model.get(), mjOBJ_JOINT, robot.jointNames()[i].c_str());
      if (joint < 0) throw std::runtime_error("joint model mismatch");
      limits.lower(i) = std::max(limits.lower(i), model->jnt_range[2 * joint]);
      limits.upper(i) = std::min(limits.upper(i), model->jnt_range[2 * joint + 1]);
    }
    input.weights = {
        cfg["tracking_weight"].as<double>(),         cfg["velocity_weight"].as<double>(),
        cfg["acceleration_weight"].as<double>(),     cfg["jerk_weight"].as<double>(),
        cfg["posture_weight"].as<double>(),          cfg["progress_reward"].as<double>(),
        cfg["terminal_progress_weight"].as<double>()};
    if (cfg["progress_reward_tau_s"])
      input.weights.progress_discount_tau = cfg["progress_reward_tau_s"].as<double>();
    auto reference = YAML::LoadFile((root / "benchmarks/reference/inspection_curve.json").string());
    Path path;
    path.start = vec(reference["start"]);
    path.end = vec(reference["end"]);
    auto xyzw = reference["quaternion_xyzw"].as<std::vector<double>>();
    path.xyzw << xyzw[0], xyzw[1], xyzw[2], xyzw[3];
    path.lateral = reference["lateral_amplitude"].as<double>();
    path.vertical = reference["vertical_amplitude"].as<double>();
    auto states = previewRollout(input.initial, input.mesh, input.nominal);
    auto stages = linearizeAdapter(robot, geometry, path, states, input, cfg,
                                   cfg["rotation_length_m"].as<double>());
    auto assembly = assemblePreview(input, stages);
    csv(out / "H.csv", assembly.qp.hessian);
    csv(out / "g.csv", assembly.qp.gradient);
    csv(out / "A.csv", assembly.qp.constraints);
    csv(out / "l.csv", assembly.qp.lower);
    csv(out / "u.csv", assembly.qp.upper);
    csv(out / "seed.csv", assembly.nominal_decision);
    csv(out / "F.csv", Eigen::MatrixXd(assembly.convex_factor));
    csv(out / "decision_offset.csv", assembly.decision_offset);
    csv(out / "controls_origin.csv", assembly.controls_origin);
    std::ofstream labels(out / "row_labels.txt.part");
    for (const auto& label : assembly.row_labels) labels << label << '\n';
    labels.close();
    std::filesystem::rename(out / "row_labels.txt.part", out / "row_labels.txt");
    csv(out / "initial_q.csv", input.initial.q);
    csv(out / "initial_v.csv", input.initial.v);
    csv(out / "accepted_q.csv", input.accepted_position);
    csv(out / "accepted_v.csv", input.accepted_velocity);
    csv(out / "previous_command_acc.csv", input.previous_acceleration);
    csv(out / "previous_model_acc.csv", input.previous_model_acceleration);
    std::cout << "variables=" << assembly.qp.gradient.size() << " rows=" << assembly.qp.lower.size()
              << " input_tick=" << scalar("tick") << " input_time_s=" << scalar("time_s")
              << " scope=assembly_replay_no_robot_trial\n";
    return 0;
  } catch (const std::exception& error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
