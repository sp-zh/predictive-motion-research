#pragma once
#include "path_adapter.hpp"
namespace predictive_motion::preview_adapter {
inline std::vector<PreviewStage> linearizeAdapter(RobotKinematics& robot, const Scene& geometry,
                                                  const Path& path,
                                                  const std::vector<PreviewState>& states,
                                                  const PreviewInput& input, const YAML::Node& cfg,
                                                  double length) {
  std::vector<PreviewStage> result;
  double keep =
      std::max(cfg["collision_activation_m"].as<double>(),
               input.limits.safe_distance +
                   2 * geometry.motion_radius_bound * input.initial.q.size() * input.joint_trust +
                   cfg["geometry_roundoff_margin_m"].as<double>());
  for (const auto& state : states) {
    auto stage = taskStage(robot, state, path, length);
    auto snapshot = geometry.query(robot, state.q, true, true, keep);
    for (const auto& pair : snapshot.queries)
      if (pair.distance < keep && !(pair.type == "true" && pair.covered_tool_environment))
        stage.scalars.push_back(
            {pair.distance, input.limits.safe_distance, pair.gradient,
             pair.a + "/" + pair.b + "/" + pair.type + "/" + std::to_string(pair.cover_index)});
    auto ind = indicators(robot, state.q, length);
    Eigen::RowVectorXd gradient = ind.nonsmooth ? Eigen::RowVectorXd::Zero(state.q.size()).eval()
                                                : sigmaGradient(robot, state.q, length);
    stage.scalars.push_back(
        {ind.sigma, cfg["singularity_safe_sigma"].as<double>(), gradient, "sigma_min"});
    if (!ind.nonsmooth && ind.sigma < cfg["singularity_target_sigma"].as<double>())
      stage.penalties.push_back({ind.sigma, cfg["singularity_target_sigma"].as<double>(),
                                 cfg["singularity_penalty"].as<double>(), gradient});
    result.push_back(std::move(stage));
  }
  return result;
}
}  // namespace predictive_motion::preview_adapter
