#pragma once
#include <mujoco/mujoco.h>

#include <cstdint>
#include <memory>
#include <string>
#include <vector>
namespace predictive_motion {
class Plant {
 public:
  explicit Plant(const std::string& path, double period = 0.004);
  void reset(uint32_t seed);
  void step();
  void command(const std::vector<std::string>& names, const std::vector<double>& q);
  std::vector<double> positions() const;
  std::vector<double> velocities() const;
  std::vector<double> efforts() const;
  const std::vector<std::string>& names() const { return names_; }
  mjModel* model() { return model_.get(); }
  mjData* data() { return data_.get(); }
  double time() const { return data_->time; }

 private:
  std::unique_ptr<mjModel, decltype(&mj_deleteModel)> model_{nullptr, mj_deleteModel};
  std::unique_ptr<mjData, decltype(&mj_deleteData)> data_{nullptr, mj_deleteData};
  std::vector<std::string> names_;
  std::vector<int> joints_, actuators_;
  int substeps_{};
};
}  // namespace predictive_motion
