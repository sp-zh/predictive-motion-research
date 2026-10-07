#include "predictive_motion_sim/plant.hpp"

#include <algorithm>
#include <cmath>
#include <limits>
#include <random>
#include <set>
#include <stdexcept>
namespace predictive_motion {
Plant::Plant(const std::string& path, double period) {
  char error[2048]{};
  model_.reset(mj_loadXML(path.c_str(), nullptr, error, sizeof(error)));
  if (!model_) throw std::runtime_error(error);
  if (!std::isfinite(period) || period <= 0) throw std::invalid_argument("Invalid period");
  const double ratio = period / model_->opt.timestep;
  if (!std::isfinite(ratio) || ratio > std::numeric_limits<int>::max())
    throw std::invalid_argument("Period exceeds supported substep count");
  substeps_ = static_cast<int>(std::llround(ratio));
  if (substeps_ < 1 || std::abs(ratio - substeps_) > 1e-9)
    throw std::invalid_argument("Period must be an integer multiple of model timestep");
  data_.reset(mj_makeData(model_.get()));
  if (!data_) throw std::runtime_error("mj_makeData failed");
  for (int a = 0; a < model_->nu; ++a) {
    if (model_->actuator_trntype[a] != mjTRN_JOINT) continue;
    const int j = model_->actuator_trnid[2 * a];
    if (model_->jnt_type[j] != mjJNT_HINGE) continue;
    const char* name = mj_id2name(model_.get(), mjOBJ_JOINT, j);
    if (!name) throw std::runtime_error("Unnamed actuated hinge");
    names_.emplace_back(name);
    joints_.push_back(j);
    actuators_.push_back(a);
  }
  if (names_.empty()) throw std::runtime_error("No directly actuated hinge joints");
  reset(42);
}
void Plant::reset(uint32_t seed) {
  const int home = mj_name2id(model_.get(), mjOBJ_KEY, "home");
  if (home >= 0)
    mj_resetDataKeyframe(model_.get(), data_.get(), home);
  else
    mj_resetData(model_.get(), data_.get());
  // Explicit mt19937 integer mapping avoids implementation-specific distribution behavior.
  std::mt19937 rng(seed);
  for (size_t i = 0; i < joints_.size(); ++i) {
    const int j = joints_[i], adr = model_->jnt_qposadr[j];
    const double perturbation = (static_cast<double>(rng()) / 4294967295.0 - 0.5) * 0.002;
    double q = data_->qpos[adr] + perturbation;
    if (model_->jnt_limited[j])
      q = std::clamp(q, model_->jnt_range[2 * j], model_->jnt_range[2 * j + 1]);
    data_->qpos[adr] = q;
    data_->ctrl[actuators_[i]] = q;
  }
  mj_forward(model_.get(), data_.get());
}
void Plant::step() {
  for (int i = 0; i < substeps_; ++i) mj_step(model_.get(), data_.get());
  if (data_->warning[mjWARN_BADQPOS].number || data_->warning[mjWARN_BADQVEL].number ||
      data_->warning[mjWARN_BADQACC].number)
    throw std::runtime_error("MuJoCo numerical warning; stopping simulation");
  for (double q : positions())
    if (!std::isfinite(q)) throw std::runtime_error("Nonfinite simulation state");
  for (double v : velocities())
    if (!std::isfinite(v)) throw std::runtime_error("Nonfinite simulation velocity");
}
void Plant::command(const std::vector<std::string>& names, const std::vector<double>& q) {
  if (names.size() != names_.size() || q.size() != names.size())
    throw std::invalid_argument("Command must specify every actuated hinge exactly once");
  std::set<std::string> seen;
  std::vector<double> next(names_.size());
  for (size_t k = 0; k < names.size(); ++k) {
    auto it = std::find(names_.begin(), names_.end(), names[k]);
    if (it == names_.end() || !seen.insert(names[k]).second || !std::isfinite(q[k]))
      throw std::invalid_argument("Invalid command name/value");
    const size_t i = static_cast<size_t>(it - names_.begin());
    const int j = joints_[i], a = actuators_[i];
    if (model_->jnt_limited[j] &&
        (q[k] < model_->jnt_range[2 * j] || q[k] > model_->jnt_range[2 * j + 1]))
      throw std::invalid_argument("Joint target outside model limits");
    if (model_->actuator_ctrllimited[a] &&
        (q[k] < model_->actuator_ctrlrange[2 * a] || q[k] > model_->actuator_ctrlrange[2 * a + 1]))
      throw std::invalid_argument("Actuator target outside model limits");
    next[i] = q[k];
  }
  for (size_t i = 0; i < next.size(); ++i) data_->ctrl[actuators_[i]] = next[i];
}
std::vector<double> Plant::positions() const {
  std::vector<double> v;
  for (int j : joints_) v.push_back(data_->qpos[model_->jnt_qposadr[j]]);
  return v;
}
std::vector<double> Plant::velocities() const {
  std::vector<double> v;
  for (int j : joints_) v.push_back(data_->qvel[model_->jnt_dofadr[j]]);
  return v;
}
std::vector<double> Plant::efforts() const {
  std::vector<double> v;
  for (int j : joints_) v.push_back(data_->qfrc_actuator[model_->jnt_dofadr[j]]);
  return v;
}
}  // namespace predictive_motion
