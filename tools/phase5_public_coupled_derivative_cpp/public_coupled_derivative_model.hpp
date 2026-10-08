#pragma once
#include "public_coupled_model.hpp"
#include <Eigen/Core>
#include <memory>
#include <string>
#include <vector>
namespace phase5_public_coupled_derivative {
struct ClipBranch {bool enabled=false;int side=0;double input=0,output=0,lower=0,upper=0,margin=0,slope=1;};
struct Result {
 bool value_success=false,jacobian_success=false;std::string error;
 phase5_public_coupled_v2::StepResult value;
 Eigen::MatrixXd jacobian,nq,nv,smooth_jacobian,friction_jacobian,acceleration_jacobian;
 std::vector<Eigen::MatrixXd> mass_q;
 std::vector<ClipBranch> control,actuator,joint_force;
 Eigen::VectorXd friction_gradient,friction_margin;
 std::vector<double> solve_conditions,solve_residuals;
};
// Physical2ms reference only: 14x21 derivative wrt q7/v7/C7.
// Own derivative Pinocchio model/data, frozen base model owns value prediction.
// Strict stable branches only; weak/near thresholds retain value, omit Jacobian.
// No one-sided/generalized, augmented, controller, task or timing acceptance.
class Model {
 public:
 static constexpr double h=.002,control_margin=1e-8,force_margin=1e-7,friction_margin=1e-7,gradient_margin=1e-7,max_condition=1e12,residual_limit=1e-10;
 Model(const std::string& xml,const std::string& constants);
 ~Model();
 Result step(const Eigen::VectorXd& q,const Eigen::VectorXd& v,const Eigen::VectorXd& C);
 phase5_public_coupled_v2::ModelMetadata metadata() const;
 private:struct Impl;std::unique_ptr<Impl> impl_;
};
}
