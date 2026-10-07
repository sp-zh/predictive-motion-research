#pragma once
#include <stdexcept>

#include "predictive_motion_kinematics/robot_kinematics.hpp"
#include "predictive_motion_sim/plant.hpp"
namespace predictive_motion {
// Position-derived observations only. Scratch caches must never replace the plant's
// dynamics, constraint solver, contact/effort or integration/warm-start state.
inline Pose observeTcp(Plant& plant, mjData* scratch, const RobotConfig& config,
                       const std::string& siteName) {
  if (!scratch || scratch == plant.data())
    throw std::invalid_argument("Require independent observation workspace");
  const int site = mj_name2id(plant.model(), mjOBJ_SITE, siteName.c_str());
  if (site < 0) throw std::runtime_error("Missing configured flange site");
  mju_copy(scratch->qpos, plant.data()->qpos, plant.model()->nq);
  mj_kinematics(plant.model(), scratch);
  Pose flange(
      Eigen::Map<const Eigen::Matrix<double, 3, 3, Eigen::RowMajor>>(scratch->site_xmat + 9 * site),
      Eigen::Map<const Eigen::Vector3d>(scratch->site_xpos + 3 * site));
  return config.world_T_base * flange * config.flange_T_tcp;
}
}  // namespace predictive_motion
