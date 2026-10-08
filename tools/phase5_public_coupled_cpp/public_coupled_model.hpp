#pragma once
#include <Eigen/Core>
#include <array>
#include <memory>
#include <string>
#include <vector>

namespace phase5_public_coupled {
struct BoxResult {
  Eigen::VectorXd force;
  std::vector<int> branches;
  int iterations = 0;
  double original_kkt = 0;
};
// Original-H KKT <=1e-10; coupled active-face solve, not axis clipping.
BoxResult solveFrictionBox(const Eigen::MatrixXd& H, const Eigen::VectorXd& ell,
                          const Eigen::VectorXd& eta);
struct ModelMetadata {
  std::string pinocchio_version;
  int nq = 0, nv = 0;
  std::vector<std::string> joint_names, frame_names;
  std::vector<int> idx_q, idx_v, joint_nq, joint_nv;
  Eigen::VectorXd masses, armature, gravity, R, B, damping;
};
struct StepResult {
  Eigen::VectorXd q, v, controls, actuator, bias, smooth;
  Eigen::MatrixXd M, W, H;
  Eigen::VectorXd ell;
  BoxResult friction;
  int control_clips = 0, force_clips = 0;
};
// Own Pinocchio MJCF Model/Data; no plant pointer, mjData or stepping API.
// Fixed instantaneous affine FR3 actuator/impedance profile; h=.002.
// q/v/target dimension7, finite; q strictly inside supported joint ranges.
// CRBA includes parsed armature and tool inertia; never add them again.
// Full velocity damping remains in implicit solve even at force clamps.
// All parameters/intermediates/outputs must be finite; throw on violations.
class Model {
 public:
  Model(const std::string& mjcf_xml, const std::string& public_constants_json);
  ~Model();
  Model(const Model&) = delete;
  Model& operator=(const Model&) = delete;
  ModelMetadata metadata() const;
  StepResult step(const Eigen::VectorXd& q, const Eigen::VectorXd& v,
                  const Eigen::VectorXd& accepted_position_target);
 private:
  struct Impl;
  std::unique_ptr<Impl> impl_;
};
}  // namespace phase5_public_coupled
