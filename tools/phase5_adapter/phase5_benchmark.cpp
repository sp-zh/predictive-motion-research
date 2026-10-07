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
    QpWorkspace preview_workspace;
    PreviewInput input;
    input.lifted = cfg["qp_formulation"] && cfg["qp_formulation"].as<std::string>() == "lifted";
    input.capture_dense_terms = false;
    input.initial = {initial, Eigen::VectorXd::Zero(7), 0, 0};
    input.mesh = cfg["prediction_mesh_s"].as<std::vector<double>>();
    input.control_dt = dt;
    input.previous_acceleration = Eigen::VectorXd::Zero(7);
    input.previous_model_acceleration = Eigen::VectorXd::Zero(7);
    input.accepted_position = initial;
    input.accepted_velocity = Eigen::VectorXd::Zero(7);
    input.nominal = Eigen::VectorXd::Zero(8 * input.mesh.size());
    input.joint_trust = cfg["joint_trust_rad"].as<double>();
    input.progress_trust = cfg["progress_trust"].as<double>();
    input.terminal_stop = cfg["terminal_stop"].as<bool>();
    auto& limits = input.limits;
    limits.lower = physical_lo;
    limits.upper = physical_hi;
    limits.velocity = Eigen::VectorXd::Constant(7, cfg["command_velocity_rad_s"].as<double>());
    limits.acceleration =
        Eigen::VectorXd::Constant(7, cfg["command_acceleration_rad_s2"].as<double>());
    limits.jerk = Eigen::VectorXd::Constant(7, cfg["command_jerk_rad_s3"].as<double>());
    limits.posture = initial;
    limits.position_margin = cfg["position_margin_rad"].as<double>();
    limits.safe_distance = safe;
    limits.progress_speed = cfg["progress_speed"].as<double>();
    limits.progress_acceleration = cfg["progress_acceleration"].as<double>();
    limits.progress_jerk = cfg["progress_jerk"].as<double>();
    if (scenario == "joint_trap")
      limits.upper(6) = std::min(limits.upper(6),
                                 initial(6) + cfg["joint_trap_controller_margin_rad"].as<double>());
    input.weights = {
        cfg["tracking_weight"].as<double>(),         cfg["velocity_weight"].as<double>(),
        cfg["acceleration_weight"].as<double>(),     cfg["jerk_weight"].as<double>(),
        cfg["posture_weight"].as<double>(),          cfg["progress_reward"].as<double>(),
        cfg["terminal_progress_weight"].as<double>()};
    ScpOptions options;
    options.max_iterations = cfg["scp_iterations"].as<int>();
    options.min_trust = cfg["scp_min_trust_rad"].as<double>();
    options.shrink = cfg["scp_shrink"].as<double>();
    options.step_tolerance = cfg["scp_step_tolerance"].as<double>();
    options.violation_tolerance = cfg["nonlinear_tolerance"].as<double>();
    options.wall_limit = cfg["solver_wall_limit_s"].as<double>();
    options.qp.max_state_age_seconds = cfg["max_state_age_s"].as<double>();
    options.qp.time_limit_seconds = options.wall_limit;
    options.qp.max_iterations = cfg["solver_max_iterations"].as<int>();
    options.qp.absolute_tolerance = cfg["solver_absolute_tolerance"].as<double>();
    options.qp.relative_tolerance = cfg["solver_relative_tolerance"].as<double>();
    options.qp.acceptance_tolerance = cfg["solver_acceptance_tolerance"].as<double>();
    if (cfg["solver_initial_rho"]) options.qp.initial_rho = cfg["solver_initial_rho"].as<double>();
    QpOptions command_options = options.qp;
    command_options.initial_rho = .1;
    command_options.max_state_age_seconds = .05;
    command_options.time_limit_seconds = .05;
    if (cfg["qp_variable_scaling"] && cfg["qp_variable_scaling"].as<bool>()) {
      int uoffset = input.lifted ? int(16 * (input.mesh.size() + 1)) : 0;
      input.variable_scale = Eigen::VectorXd::Ones(uoffset + 8 * input.mesh.size());
      if (input.lifted)
        for (int k = 0; k <= int(input.mesh.size()); ++k) {
          input.variable_scale.segment(k * 16, 7).setConstant(input.joint_trust);
          input.variable_scale.segment(k * 16 + 7, 7) = limits.velocity;
          input.variable_scale(k * 16 + 14) = input.progress_trust;
          input.variable_scale(k * 16 + 15) = limits.progress_speed;
        }
      for (int k = 0; k < int(input.mesh.size()); ++k) {
        input.variable_scale.segment(uoffset + k * 8, 7) = limits.acceleration;
        input.variable_scale(uoffset + k * 8 + 7) = limits.progress_acceleration;
      }
    }
    Path path;
    if (cfg["progress_reward_tau_s"])
      input.weights.progress_discount_tau = cfg["progress_reward_tau_s"].as<double>();
    auto reference = YAML::LoadFile((root / "benchmarks/reference/inspection_curve.json").string());
    path.start = vec(reference["start"]);
    path.end = vec(reference["end"]);
    auto xyzw = reference["quaternion_xyzw"].as<std::vector<double>>();
    path.xyzw << xyzw[0], xyzw[1], xyzw[2], xyzw[3];
    path.lateral = reference["lateral_amplitude"].as<double>();
    path.vertical = reference["vertical_amplitude"].as<double>();
    if (scenario == "joint_trap" || scenario == "singularity_probe") {
      path.joint_path = true;
      path.joint_start = initial;
      path.joint_direction = Eigen::VectorXd::Zero(7);
      if (scenario == "joint_trap")
        path.joint_direction(6) = cfg["joint_path_target_increment_rad"].as<double>();
      else {
        path.joint_direction(1) = -initial(1);
        path.joint_direction(4) = -initial(4);
      }
    } else if (scenario != "inspection")
      throw std::runtime_error("unknown scenario");
    std::ofstream raw(dir / "raw.csv"), preview(dir / "preview.csv"), scp(dir / "scp.csv");
    for (auto* file : {&raw, &preview, &scp}) {
      file->exceptions(std::ios::failbit | std::ios::badbit);
      *file << std::setprecision(17);
    }
    raw << "tick,substep,time_s,phase,status,stop_status,command_issued,s,r,b,contacts,true_"
           "clearance_m,euclidean_position_m,se3_translation_m,rotation_rad,sigma_min,condition,"
           "nonsmooth,command_age_s,plan_origin_age_s";
    for (auto name : {"q_requested_", "q_model_control_", "q_accepted_", "q_post_", "dq_requested_",
                      "dq_accepted_", "dq_post_", "requested_model_acc_", "applied_model_acc_",
                      "command_acc_", "command_jerk_", "physical_acc_", "physical_jerk_"})
      headers(raw, name);
    raw << ",progress_requested_b,progress_applied_b,progress_projection_delta,"
           "material_progress_projection,tiny_progress_projection\n";
    preview << "tick,kind,node,preview_time_s,s,r,min_joint_margin_rad,true_clearance_m,cover_"
               "clearance_m,sigma_min,condition,nonsmooth,euclidean_position_m,se3_translation_m,"
               "rotation_rad";
    headers(preview, "q_");
    headers(preview, "v_");
    preview << '\n';
    scp << "tick,iteration,status,trust_rad,true_violation,step,linearization_s,assembly_s,qp_"
           "setup_s,qp_solve_s,validation_s,qp_iterations,raw_status,variables,rows,primal_"
           "residual,dual_residual,nominal_row_violation,validation_checked,qp_wrapper_s,hessian_"
           "nnz,constraint_nnz,rho_updates,polish_status,workspace_reused,matrix_updated,dual_"
           "reused,dual_mapped_rows,qp_update_s,reset_reason,consistency_checked,consistency_"
           "ratio,preview_termination_reason,solver_eps_abs,solver_eps_rel,initial_rho,rho_estimate,"
           "minimum_row_scale,maximum_row_scale,minimum_variable_scale,maximum_variable_scale,"
           "qp_original_row_violation,qp_maximum_violation_row\n";
    struct Cycle {
      int tick;
      bool issued, warm_reset;
      double observe, primary, stop, plant, logging, diagnostic, wall, age;
    };
    std::vector<Cycle> cycles;
    auto measured = observe(plant, scratch.get(), robot, geometry);
    Eigen::VectorXd prev_dq = measured.dq, prev_acc = Eigen::VectorXd::Zero(7),
                    requested = Eigen::VectorXd::Zero(7), qrequested = initial, modelq = initial,
                    model_requested_a = Eigen::VectorXd::Zero(7),
                    model_applied_a = Eigen::VectorXd::Zero(7), cmdacc = Eigen::VectorXd::Zero(7),
                    cmdjerk = Eigen::VectorXd::Zero(7);
    CommandHistory history{initial, initial, Eigen::VectorXd::Zero(7), Eigen::VectorXd::Zero(7)};
    CommandLimits command_limits{limits.lower,          limits.upper, limits.velocity,
                                 limits.acceleration,   limits.jerk,  dt,
                                 limits.position_margin};
    std::string failure, status = "HOLD", stop_status = "NOT_ATTEMPTED";
    bool stopping = false, finished = false;
    double progress = 0, progress_speed = 0, previous_b = 0, requested_b = 0, minclear = INFINITY,
           maxage = 0;
    int rawrows = 0, accepted = 0, failed_attempts = 0, interventions = 0;
    int predictive_commits = 0, path_substeps = 0, accuracy_violations = 0;
    bool diagnostic_duration_completed = false;
    std::string stop_reason;
    double progress_requested_b = 0, progress_projection_delta = 0;
    bool material_progress_projection = false, tiny_progress_projection = false;
    int tiny_progress_projections = 0, material_progress_projections = 0;
    const double progress_cache_threshold = cfg["progress_cache_projection_threshold"]
        ? cfg["progress_cache_projection_threshold"].as<double>() : 1e-9;
    if (!std::isfinite(progress_cache_threshold) || progress_cache_threshold < 0)
      throw std::runtime_error("invalid progress cache threshold");
    double max_path_position_error = 0, max_path_rotation_error = 0;
    double max_model_q_error = 0, max_command_velocity_error = 0;
    Eigen::VectorXd old_controls;
    int old_tick = -1;
    const int warmup = std::lround(cfg["warmup_s"].as<double>() / dt),
              task = std::lround(cfg["diagnostic_s"].as<double>() / dt);
    auto writeRow = [&](int tick, int sub, const std::string& phase, bool issued, double s,
                        double r, double b, double age_value, const Eigen::VectorXd& acc,
                        const Eigen::VectorXd& jerk) {
      auto desired = path.pose(robot, s);
      auto residual = logResidual(measured.tcp, desired);
      auto ind = indicators(robot, measured.q, length);
      raw << tick << ',' << sub << ',' << plant.time() << ',' << phase << ',' << status << ','
          << stop_status << ',' << issued << ',' << s << ',' << r << ',' << b << ','
          << measured.contacts << ',' << measured.clearance << ','
          << (measured.tcp.translation() - desired.translation()).norm() << ','
          << residual.head<3>().norm() << ',' << residual.tail<3>().norm() << ',' << ind.sigma
          << ',' << ind.condition << ',' << ind.nonsmooth << ',' << age_value << ','
          << plan_origin_age;
      for (const auto& v : std::vector<Eigen::VectorXd>{
               qrequested, modelq, history.accepted_position, measured.q, requested,
               history.accepted_velocity, measured.dq, model_requested_a, model_applied_a, cmdacc,
               cmdjerk, acc, jerk})
        vectorCsv(raw, v);

      raw << ',' << progress_requested_b << ',' << b << ',' << progress_projection_delta
          << ',' << material_progress_projection << ',' << tiny_progress_projection << '\n';
      ++rawrows;
      minclear = std::min(minclear, measured.clearance);
    };
    for (int tick = 0; tick < warmup + task + 2000 && !finished; ++tick) {
      auto cycle_start = Clock::now();
      Cycle cost{tick, false, false, 0, 0, 0, 0, 0, 0, 0, 0};
      auto stamp = Clock::now();
      measured = observe(plant, scratch.get(), robot, geometry);
      cost.observe = seconds(stamp);
      auto capture = measured.capture;
      history.measured_position = measured.q;
      if(tick == warmup + task && !stopping) {
        stopping = true;
        diagnostic_duration_completed = true;
        stop_reason = "NORMAL_DIAGNOSTIC_DURATION_COMPLETED";
        status = "NORMAL_STOP";
        old_controls.resize(0);
        preview_workspace.reset();
      }
      stop_status = "NOT_ATTEMPTED";
      progress_requested_b = 0;
      progress_projection_delta = 0;
      material_progress_projection = false;
      tiny_progress_projection = false;
      PreviewResult predicted;
      requested.setZero();
      requested_b = 0;
      std::vector<PreviewStage> last_stages;
      Eigen::VectorXd last_nominal;
      QpProblem reactive_problem;
      bool reactive_request = false;
      if (tick >= warmup && !stopping && method == "reactive_qp") {
        auto task_stage =
            taskStage(robot, {measured.q, measured.dq, progress, progress_speed}, path, length);
        reactive_problem = trackingProblem(
            -task_stage.joint_derivative,
            4 * task_stage.residual + task_stage.path_derivative * progress_speed, 9e-6);
        reactive_request = true;
        requested = reactive_problem.hessian.ldlt().solve(-reactive_problem.gradient);
        model_requested_a = (requested - measured.dq) / dt;
        qrequested = history.accepted_position + dt * requested;
        modelq = measured.q + .5 * dt * (measured.dq + requested);
        status = "REACTIVE_REQUEST";
        double lo = std::max(-limits.progress_acceleration, previous_b - limits.progress_jerk * dt),
               hi = std::min(limits.progress_acceleration, previous_b + limits.progress_jerk * dt);
        lo = std::max(lo, -progress_speed / dt);
        hi = std::min({hi, (limits.progress_speed - progress_speed) / dt,
                       (1 - progress - dt * progress_speed) * 2 / (dt * dt)});
        if (lo > hi) {
          stopping = true;
          failure = "REACTIVE_PROGRESS_UNAVAILABLE";
          failed_attempts++;
        } else
          requested_b = std::clamp((limits.progress_speed - progress_speed) / dt, lo, hi);
      }
      if (tick >= warmup && !stopping && method == "predictive") {
        input.initial = {measured.q, measured.dq, progress, progress_speed};
        input.accepted_position = history.accepted_position;
        input.accepted_velocity = history.accepted_velocity;
        input.previous_acceleration = history.accepted_acceleration;
        input.previous_model_acceleration = model_applied_a;
        input.previous_progress_acceleration = previous_b;
        auto shifted = shiftPreview(input.mesh, old_controls, input.mesh, 7,
                                    old_tick >= 0 ? (tick - old_tick) * dt : INFINITY);
        cost.warm_reset = shifted.reset;
        input.nominal = shifted.controls;
        if (shifted.reset) preview_workspace.reset();
        input.state_age = seconds(capture);
        auto linearize = [&](const std::vector<PreviewState>& xs) {
          std::vector<PreviewStage> stages;
          last_nominal.resize(8 * input.mesh.size());
          for (int k = 0; k < int(input.mesh.size()); ++k) {
            last_nominal.segment(k * 8, 7) = (xs[k + 1].v - xs[k].v) / input.mesh[k];
            last_nominal(k * 8 + 7) = (xs[k + 1].r - xs[k].r) / input.mesh[k];
          }
          stages = linearizeAdapter(robot, geometry, path, xs, input, cfg, length);
          last_stages = stages;
          return stages;
        };
        auto validate = [&](const std::vector<PreviewState>& xs, const Eigen::VectorXd& controls) {
          double violation = 0;
          const double roundoff = cfg["geometry_roundoff_margin_m"].as<double>(),
                       sigma_floor = cfg["singularity_safe_sigma"].as<double>();
          std::vector<double> node_distance(xs.size()), node_sigma(xs.size());
          for (int j = 0; j < int(xs.size()); ++j) {
            auto query = geometry.query(robot, xs[j].q, false, true, -INFINITY);
            node_distance[j] = std::min(query.minimum_true, query.minimum_cover);
            node_sigma[j] = indicators(robot, xs[j].q, length).sigma;
          }
          for (int k = 0; k < int(input.mesh.size()); ++k) {
            double h = input.mesh[k];
            Eigen::VectorXd u = controls.segment(k * 8, 8);
            double speed = xs[k].v.cwiseAbs().cwiseMax(xs[k + 1].v.cwiseAbs()).sum();
            bool certified = false;
            double last_gap = INFINITY;
            for (int parts = 1; parts <= cfg["geometry_max_subdivisions"].as<int>(); parts *= 2) {
              double minimum = INFINITY;
              for (int i = 0; i <= parts; ++i) {
                if (i == 0 || i == parts) {
                  int node = k + (i == parts);
                  minimum = std::min(minimum, node_distance[node]);
                  violation = std::max(violation, sigma_floor - node_sigma[node]);
                } else {
                  auto x = previewAdvance(xs[k], u, h * i / parts);
                  auto query = geometry.query(robot, x.q, false, true, -INFINITY);
                  minimum = std::min({minimum, query.minimum_true, query.minimum_cover});
                  violation =
                      std::max(violation, sigma_floor - indicators(robot, x.q, length).sigma);
                }
              }
              double conservative =
                  minimum - geometry.motion_radius_bound * speed * h / parts - roundoff;
              last_gap = safe - conservative;
              if (conservative >= safe) {
                certified = true;
                break;
              }
            }
            if (!certified) violation = std::max(violation, std::max(0., last_gap));
          }
          return std::max(0., violation);
        };
        auto consistent = [&](const std::vector<PreviewState>& nominal,
                              const std::vector<PreviewState>& candidate,
                              const std::vector<PreviewStage>& stages) {
          double ratio = 0;
          for (int k = 0; k < int(candidate.size()); ++k) {
            auto exact = taskStage(robot, candidate[k], path, length);
            Eigen::VectorXd approximation =
                stages[k].residual + stages[k].joint_derivative * (candidate[k].q - nominal[k].q) +
                stages[k].path_derivative * (candidate[k].s - nominal[k].s);
            ratio = std::max(ratio, (exact.residual - approximation).norm() /
                                        cfg["tracking_model_tolerance_m"].as<double>());
            for (const auto& penalty : stages[k].penalties) {
              double predicted_sigma =
                  penalty.value + penalty.gradient.dot(candidate[k].q - nominal[k].q);
              ratio = std::max(ratio, std::abs(indicators(robot, candidate[k].q, length).sigma -
                                               predicted_sigma) /
                                          cfg["sigma_model_tolerance"].as<double>());
            }
          }
          return ratio;
        };
        stamp = Clock::now();
        auto captureQp = [&](const PreviewAssembly& a,const QpResult& solved) {
          if (!(cfg["capture_failed_qp"] && cfg["capture_failed_qp"].as<bool>()) ||
              solved.status==QpStatus::Solved) return;
          const auto failed_dir=dir/("failed_qp_tick_"+std::to_string(tick));
          if(std::filesystem::exists(failed_dir))return;
          std::filesystem::create_directory(failed_dir);
          snapshotCsv(failed_dir/"H.csv",a.qp.hessian);snapshotCsv(failed_dir/"g.csv",a.qp.gradient);
          snapshotCsv(failed_dir/"A.csv",a.qp.constraints);snapshotCsv(failed_dir/"l.csv",a.qp.lower);
          snapshotCsv(failed_dir/"u.csv",a.qp.upper);snapshotCsv(failed_dir/"seed.csv",a.nominal_decision);
          snapshotCsv(failed_dir/"F.csv",Eigen::MatrixXd(a.convex_factor));
          snapshotCsv(failed_dir/"decision_offset.csv",a.decision_offset);
          snapshotCsv(failed_dir/"controls_origin.csv",a.controls_origin);
          snapshotCsv(failed_dir/"variable_scale.csv",input.variable_scale);
          std::ofstream labels(failed_dir/"row_labels.txt");
          for(const auto& id:a.row_labels)labels<<id<<'\n';
          std::ofstream info(failed_dir/"rejection.txt");
          info<<std::setprecision(17)<<"actual runtime assembly, not assembly replay; tick="<<tick
              <<" status="<<statusName(solved.status)<<" native_status="<<solved.raw_status
              <<" original_violation="<<solved.violation<<" row="<<solved.maximum_violation_row
              <<" eps_abs="<<options.qp.absolute_tolerance<<" eps_rel="<<options.qp.relative_tolerance
              <<" initial_rho="<<options.qp.initial_rho<<"\n";
        };
        predicted = solvePreview(input, linearize, validate, options, &preview_workspace,
                                 consistent, captureQp);
        cost.primary = seconds(stamp);
        plan_origin_age = seconds(capture);
        status = statusName(predicted.status);
        if (predicted.status == QpStatus::Solved && predicted.controls.size()) {
          model_requested_a = predicted.controls.head(7);
          requested = measured.dq + dt * model_requested_a;
          requested_b = predicted.controls(7);
          modelq = measured.q + dt * measured.dq + .5 * dt * dt * predicted.controls.head(7);
          qrequested = history.accepted_position + dt * requested;
        } else {
          stopping = true;
          failure = status;
          failed_attempts++;
          old_controls.resize(0);
        }
      }
      if (tick >= warmup && !stopping) {
        const auto continuation = progressStopBounds(
            progress, progress_speed, previous_b, dt, limits);
        if (!continuation.feasible ||
            requested_b < continuation.lower - options.violation_tolerance ||
            requested_b > continuation.upper + options.violation_tolerance) {
          stopping = true;
          failure = "PROGRESS_COMMAND_NOT_CONTINUABLE";
          failed_attempts++;
          old_controls.resize(0);
          preview_workspace.reset();
        } else {
          // The QP accepts tiny original-unit residuals. Project those residuals
          // before integrating the actual progress state; retain applied b in raw.
          const double applied_b = std::clamp(requested_b, continuation.lower,
                                             continuation.upper);
          progress_requested_b = requested_b;
          progress_projection_delta = applied_b - requested_b;
          material_progress_projection = std::abs(progress_projection_delta)>progress_cache_threshold;
          tiny_progress_projection = progress_projection_delta!=0 && !material_progress_projection;
          if (material_progress_projection) {
            material_progress_projections++;
            interventions++;
            old_controls.resize(0);
            preview_workspace.reset();
          } else if (tiny_progress_projection) tiny_progress_projections++;
          requested_b = applied_b;
        }
      }
      if (tick >= warmup && reference_mode && !stopping && method == "predictive") {
        // Explicit offline functional reference. No simulation step occurs during
        // planning. Re-read actual current state, verify the plan initial state is
        // unchanged, and enforce the original 50ms CURRENT command guard below.
        auto fresh = observe(plant, scratch.get(), robot, geometry);
        if ((fresh.q - input.initial.q).lpNorm<Eigen::Infinity>() > 1e-12 ||
            (fresh.dq - input.initial.v).lpNorm<Eigen::Infinity>() > 1e-12) {
          stopping = true;
          failure = "REFERENCE_INITIAL_STATE_CHANGED";
          failed_attempts++;
        }
        measured = fresh;
        capture = measured.capture;
        history.measured_position = measured.q;
      }
      if (tick >= warmup) {
        stamp = Clock::now();
        auto snapshot = geometry.query(
            robot, measured.q, true, true,
            std::max(.03, safe + 2 * geometry.motion_radius_bound *
                                     ((history.accepted_position - measured.q).cwiseAbs().sum() +
                                      7 * .00025)));
        auto problem = constrainPreviewCommand(
            stopping           ? stoppingProblem(7)
            : reactive_request ? reactive_problem
                               : trackingProblem(Eigen::MatrixXd::Identity(7, 7), requested, 0),
            command_limits, history);
        for (const auto& pair : snapshot.queries)
          if (!(pair.type == "true" && pair.covered_tool_environment) &&
              pair.distance <
                  std::max(.03,
                           safe + 2 * geometry.motion_radius_bound *
                                      ((history.accepted_position - measured.q).cwiseAbs().sum() +
                                       7 * .00025)))
            appendDamper(problem, pair.gradient, pair.distance, safe,
                         cfg["collision_damper_eta_per_s"].as<double>());
        auto nonlinearCommand = [&](const Eigen::VectorXd& velocity) {
          for (const Eigen::VectorXd& target : std::array<Eigen::VectorXd, 2>{
                   measured.q + dt * velocity, history.accepted_position + dt * velocity})
            for (int i = 1; i <= cfg["command_subdivisions"].as<int>(); ++i) {
              auto q = measured.q +
                       double(i) / cfg["command_subdivisions"].as<int>() * (target - measured.q);
              auto query = geometry.query(robot, q, false, true, -INFINITY);
              if (std::min(query.minimum_true, query.minimum_cover) < safe) return false;
            }
          return true;
        };
        problem.state_age_seconds = seconds(capture);
        auto command = solveQp(problem, command_options);
        bool valid = command.status == QpStatus::Solved && nonlinearCommand(command.velocity) &&
                     seconds(capture) <= command_options.max_state_age_seconds;
        if (!valid && !stopping) {
          stopping = true;
          failure = command.status == QpStatus::Solved ? "NONLINEAR_OR_STALE_COMMAND"
                                                       : statusName(command.status);
          failed_attempts++;
        }
        if (stopping) {
          // Fresh measured capture after an aged predictive attempt. Stop QP remains
          // the same common constrained minimum-velocity controller, not fabricated zero.
          measured = observe(plant, scratch.get(), robot, geometry);
          capture = measured.capture;
          history.measured_position = measured.q;
          auto stop = constrainPreviewCommand(stoppingProblem(7), command_limits, history);
          auto stop_snapshot = geometry.query(
              robot, measured.q, true, true,
              .03 + 2 * geometry.motion_radius_bound *
                        ((history.accepted_position - measured.q).cwiseAbs().sum() + 7 * .00025));
          for (const auto& pair : stop_snapshot.queries)
            if (!(pair.type == "true" && pair.covered_tool_environment) &&
                pair.distance <
                    .03 + 2 * geometry.motion_radius_bound *
                              ((history.accepted_position - measured.q).cwiseAbs().sum() +
                               7 * .00025))
              appendDamper(stop, pair.gradient, pair.distance, safe,
                           cfg["collision_damper_eta_per_s"].as<double>());
          stop.state_age_seconds = seconds(capture);
          command = solveQp(stop, command_options);
          stop_status = statusName(command.status);
          valid = command.status == QpStatus::Solved && nonlinearCommand(command.velocity) &&
                  seconds(capture) <= command_options.max_state_age_seconds;
          const auto progress_stop = progressStopBounds(
              progress, progress_speed, previous_b, dt, limits);
          if (!progress_stop.feasible) {
            valid = false;
            stop_status = "PROGRESS_STOP_UNAVAILABLE";
          } else {
            requested_b = progress_stop.acceleration;
            progress_requested_b = requested_b;
            progress_projection_delta = 0;
            material_progress_projection = tiny_progress_projection = false;
          }
        }
        cost.stop = seconds(stamp);
        cost.age = seconds(capture);
        valid = valid && cost.age <= command_options.max_state_age_seconds;
        maxage = std::max(maxage, cost.age);
        if (!valid) {
          stop_status += "_NO_COMMAND_SIMULATION_TERMINATED";
          writeRow(tick, 0, "terminated", false, progress, progress_speed, previous_b, cost.age,
                   prev_acc, Eigen::VectorXd::Zero(7));
          raw.flush();
          cost.wall = seconds(cycle_start);
          cycles.push_back(cost);
          finished = true;
          break;
        }
        if ((command.velocity - requested).lpNorm<Eigen::Infinity>() > 1e-6) {
          interventions++;
          old_controls.resize(0);
          preview_workspace.reset();
        } else if (!stopping && method == "predictive" && !material_progress_projection) {
          old_controls = predicted.controls;
          // Seed the next solve with the acceleration that was actually used.
          // The original solved rollout remains in the diagnostic preview trace.
          old_controls(7) = requested_b;
          old_tick = tick;
        }
        model_applied_a = (command.velocity - measured.dq) / dt;
        cmdacc = (command.velocity - history.accepted_velocity) / dt;
        cmdjerk = (cmdacc - history.accepted_acceleration) / dt;
        history.accepted_velocity = command.velocity;
        history.accepted_acceleration = cmdacc;
        history.accepted_position += dt * command.velocity;
        plant.command(plant.names(), std::vector<double>(history.accepted_position.data(),
                                                         history.accepted_position.data() + 7));
        cost.issued = true;
        accepted++;
        if (!stopping && method == "predictive") predictive_commits++;
      }
      double old_s = progress, old_r = progress_speed, old_b = previous_b;
      stamp = Clock::now();
      for (int sub = 1; sub <= 2; ++sub) {
        plant.step();
        measured = observe(plant, scratch.get(), robot, geometry);
        Eigen::VectorXd acc = (measured.dq - prev_dq) / subdt, jerk = (acc - prev_acc) / subdt;
        prev_dq = measured.dq;
        prev_acc = acc;
        double t = sub * subdt, s = old_s + t * old_r + .5 * t * t * requested_b,
               r = old_r + t * requested_b;
        writeRow(tick, sub,
                 tick < warmup ? "warmup"
                 : stopping    ? "stopping"
                               : "path",
                 cost.issued, s, r, requested_b, cost.age, acc, jerk);
        if (tick >= warmup && !stopping) {
          auto desired = path.pose(robot, s);
          const double position_error = (measured.tcp.translation()-desired.translation()).norm();
          const double rotation_error = logResidual(measured.tcp, desired).tail<3>().norm();
          max_path_position_error = std::max(max_path_position_error, position_error);
          max_path_rotation_error = std::max(max_path_rotation_error, rotation_error);
          path_substeps++;
          if (position_error > cfg["completion_position_m"].as<double>() ||
              rotation_error > cfg["completion_rotation_rad"].as<double>()) {
            accuracy_violations++;
            stopping = true;
            failure = "EXECUTED_TASK_ACCURACY_ENVELOPE";
            stop_reason = failure;
          }
          if (sub==2) {
            max_model_q_error = std::max(max_model_q_error,
                (modelq-measured.q).cwiseAbs().maxCoeff());
            max_command_velocity_error = std::max(max_command_velocity_error,
                (history.accepted_velocity-measured.dq).cwiseAbs().maxCoeff());
          }
        }
        if (tick >= warmup &&
            (!measuredPositionSafe(measured.q, physical_lo, physical_hi) || measured.contacts ||
             measured.clearance < safe ||
             (measured.dq.cwiseAbs().array() > physical_velocity.array()).any() ||
             acc.cwiseAbs().maxCoeff() > cfg["executed_acceleration_rad_s2"].as<double>() ||
             jerk.cwiseAbs().maxCoeff() > cfg["executed_jerk_rad_s3"].as<double>())) {
          stopping = true;
          failure = "EXECUTED_SAFETY_LIMIT";
        }
      }
      cost.plant = seconds(stamp);
      progress = old_s + dt * old_r + .5 * dt * dt * requested_b;
      progress_speed = old_r + dt * requested_b;
      previous_b = requested_b;
      if (progress < -1e-9 || progress > 1 + 1e-9 || progress_speed < -1e-9 ||
          progress_speed > limits.progress_speed + 1e-6 ||
          std::abs(requested_b) > limits.progress_acceleration + 1e-6 ||
          std::abs((requested_b - old_b) / dt) > limits.progress_jerk + 1e-6) {
        failure = "EXECUTED_PROGRESS_LIMIT";
        finished = true;
      }
      if (tick == warmup - 1 && (measured.contacts || measured.clearance < safe ||
                                 measured.dq.cwiseAbs().maxCoeff() > 1e-4)) {
        failure = "WARMUP_FAILED";
        finished = true;
      }
      stamp = Clock::now();
      for (int i = 0; i < int(predicted.iterations.size()); ++i) {
        const auto& log = predicted.iterations[i];
        scp << tick << ',' << i << ',' << statusName(log.status) << ',' << log.trust << ','
            << log.violation << ',' << log.step << ',' << log.linearization_s << ','
            << log.assembly_s << ',' << log.qp_setup_s << ',' << log.qp_solve_s << ','
            << log.validation_s << ',' << log.qp_iterations << ',' << log.qp_raw_status << ','
            << log.variables << ',' << log.rows << ',' << log.qp_primal_residual << ','
            << log.qp_dual_residual << ',' << log.nominal_row_violation << ','
            << log.validation_checked << ',' << log.qp_wrapper_s << ',' << log.hessian_nonzeros
            << ',' << log.constraint_nonzeros << ',' << log.rho_updates << ',' << log.polish_status
            << ',' << log.workspace_reused << ',' << log.matrix_updated << ',' << log.dual_reused
            << ',' << log.dual_mapped_rows << ',' << log.qp_update_s << ',' << log.reset_reason
            << ',' << log.consistency_checked << ',' << log.consistency_ratio
            << ',' << predicted.termination_reason << ',' << log.solver_absolute_tolerance
            << ',' << log.solver_relative_tolerance << ',' << log.initial_rho << ',' << log.rho_estimate
            << ',' << log.minimum_row_scale << ',' << log.maximum_row_scale
            << ',' << log.minimum_variable_scale << ',' << log.maximum_variable_scale
            << ',' << log.qp_original_row_violation << ',' << log.qp_maximum_violation_row << '\n';
      }
      auto logPrediction = [&](const std::string& kind, const std::vector<PreviewState>& xs) {
        double t = 0;
        for (int k = 0; k < int(xs.size()); ++k) {
          const auto& x = xs[k];
          auto query = geometry.query(robot, x.q, false, true, -INFINITY);
          auto ind = indicators(robot, x.q, length);
          auto desired = path.pose(robot, x.s), actual = robot.tcpPose(x.q);
          auto e = logResidual(actual, desired);
          double margin =
              std::min((x.q - limits.lower).minCoeff(), (limits.upper - x.q).minCoeff());
          preview << tick << ',' << kind << ',' << k << ',' << t << ',' << x.s << ',' << x.r << ','
                  << margin << ',' << query.minimum_true << ',' << query.minimum_cover << ','
                  << ind.sigma << ',' << ind.condition << ',' << ind.nonsmooth << ','
                  << (actual.translation() - desired.translation()).norm() << ','
                  << e.head<3>().norm() << ',' << e.tail<3>().norm();
          vectorCsv(preview, x.q);
          vectorCsv(preview, x.v);
          preview << '\n';
          if (k < int(input.mesh.size())) t += input.mesh[k];
        }
      };
      if (!predicted.states.empty()) logPrediction("accepted_model", predicted.states);
      if (!last_stages.empty()) {
        auto diagnostic_input = input;
        diagnostic_input.nominal = last_nominal;
        diagnostic_input.lifted = false;
        auto assembly = assemblePreview(diagnostic_input, last_stages);
        Eigen::LDLT<Eigen::MatrixXd> ldlt(assembly.qp.hessian);
        if (ldlt.info() == Eigen::Success) {
          Eigen::VectorXd free = ldlt.solve(-assembly.qp.gradient);
          if (free.allFinite())
            logPrediction(
                "unconstrained_quadratic_diagnostic",
                previewRollout(input.initial, input.mesh, free.tail(input.nominal.size())));
        }
      }
      cost.diagnostic = seconds(stamp);
      stamp = Clock::now();
      raw.flush();
      preview.flush();
      scp.flush();
      cost.logging = seconds(stamp);
      cost.wall = seconds(cycle_start);
      cycles.push_back(cost);
      if (stopping && history.accepted_velocity.cwiseAbs().maxCoeff() < 1e-6 &&
          measured.dq.cwiseAbs().maxCoeff() < 1e-4 && progress_speed < 1e-6 &&
          std::abs(previous_b) < 1e-3)
        finished = true;
      if (stopping && stop_reason.empty()) stop_reason = failure;
    }
    std::ofstream timing(dir / "cycles.csv");
    timing << std::setprecision(17)
           << "tick,command_issued,warm_reset,fresh_observer_s,predictive_primary_s,command_"
              "projection_and_stop_s,physics_observer_raw_s,prediction_diagnostic_and_scp_logging_"
              "s,flush_s,full_cycle_wall_s,deadline_miss,command_age_s,ros_s\n";
    double maxcycle = 0;
    int misses = 0;
    for (const auto& c : cycles) {
      timing << c.tick << ',' << c.issued << ',' << c.warm_reset << ',' << c.observe << ','
             << c.primary << ',' << c.stop << ',' << c.plant << ',' << c.diagnostic << ','
             << c.logging << ',' << c.wall << ',' << (c.wall > dt) << ',' << c.age << ",0\n";
      maxcycle = std::max(maxcycle, c.wall);
      misses += c.wall > dt;
    }
    timing.flush();
    YAML::Emitter summary;
    summary
        << YAML::BeginMap << YAML::Key << "scope" << YAML::Value
        << (reference_mode
                ? "Paused-simulation functional reference; not online/real-time success"
                : "Phase5 online component diagnostic, not full path completion/research result")
        << YAML::Key << "reference_mode" << YAML::Value << reference_mode << YAML::Key << "method"
        << YAML::Value << method << YAML::Key << "scenario" << YAML::Value << scenario << YAML::Key
        << "seed" << YAML::Value << seed << YAML::Key << "failure" << YAML::Value << failure
        << YAML::Key << "raw_rows" << YAML::Value << rawrows << YAML::Key << "accepted_commands"
        << YAML::Value << accepted << YAML::Key << "failed_predictive_or_command_attempts"
        << YAML::Value << failed_attempts << YAML::Key << "supervisor_interventions" << YAML::Value
        << interventions << YAML::Key << "progress" << YAML::Value << progress << YAML::Key
        << "progress_speed" << YAML::Value << progress_speed << YAML::Key << "min_true_clearance_m"
        << YAML::Value << minclear << YAML::Key << "max_command_age_s" << YAML::Value << maxage
        << YAML::Key << "max_full_cycle_wall_s" << YAML::Value << maxcycle << YAML::Key

        << "full_cycle_deadline_misses" << YAML::Value << misses
        << YAML::Key << "predictive_path_commits" << YAML::Value << predictive_commits
        << YAML::Key << "diagnostic_duration_completed" << YAML::Value << diagnostic_duration_completed
        << YAML::Key << "stop_reason" << YAML::Value << stop_reason
        << YAML::Key << "stop_threshold_reached" << YAML::Value <<
           (stopping && history.accepted_velocity.cwiseAbs().maxCoeff()<1e-6 &&
            measured.dq.cwiseAbs().maxCoeff()<1e-4 && progress_speed<1e-6 && std::abs(previous_b)<1e-3)

        << YAML::Key << "progress_cache_threshold_b_units" << YAML::Value << progress_cache_threshold
        << YAML::Key << "tiny_progress_projections" << YAML::Value << tiny_progress_projections
        << YAML::Key << "material_progress_projections" << YAML::Value << material_progress_projections
        << YAML::Key << "path_substeps" << YAML::Value << path_substeps
        << YAML::Key << "task_accuracy_violations" << YAML::Value << accuracy_violations
        << YAML::Key << "max_path_position_error_m" << YAML::Value << max_path_position_error
        << YAML::Key << "max_path_rotation_error_rad" << YAML::Value << max_path_rotation_error
        << YAML::Key << "max_4ms_requested_model_q_error_rad" << YAML::Value << max_model_q_error
        << YAML::Key << "max_4ms_command_vs_physical_velocity_rad_s" << YAML::Value << max_command_velocity_error
        << YAML::EndMap;
    std::ofstream(dir / "summary.yaml") << summary.c_str() << '\n';
    std::cout << summary.c_str() << '\n';
    return 0;
  } catch (const std::exception& e) {
    std::cerr << e.what() << '\n';
    return 1;
  }
}
