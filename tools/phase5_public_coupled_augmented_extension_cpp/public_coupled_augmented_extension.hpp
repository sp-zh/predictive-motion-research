#pragma once
#include "public_coupled_augmented_model.hpp"
#include "public_coupled_derivative_model.hpp"
#include <Eigen/Core>
#include <string>
#include <vector>
namespace phase5_public_coupled_augmented_extension {
using State=phase5_public_coupled_augmented::State;
using Cell=phase5_public_coupled_augmented::Cell;
struct Map {
 int cell=0,cycle=0,half=0;
 State origin,state,cell_origin;Eigen::VectorXd input;
 Eigen::MatrixXd A,B,cell_A,cell_B;Eigen::VectorXd defect,cell_defect;
};
struct Result {
 phase5_public_coupled_augmented::Result value;
 bool extension_jacobian_success=false;
 int first_uncertified_substep=-1;
 std::string error;
 std::vector<Map> substep_maps,cycle_maps,cell_maps;
};
// Separate cell-local30x30/30x8 and cycle-local maps, not a horizon planner.
// Nonlinear nominal values are the frozen augmented model, never linear resets.
// Original closed w/alpha/s/r domain admits the nominal only. Derivatives are
// of the composite map induced by command/progress polynomial extension;
// the full physical map remains nonlinear, with strict physical branches.
// A certificate never certifies two-sided admissible perturbations or safety.
class Model {
 public:
 static constexpr double control_margin=1e-8;
 static constexpr const char* certificate_name="COMMAND_PROGRESS_EXTENSION_JACOBIAN_STRICT_PHYSICAL_V1";
 Model(const std::string& xml,const std::string& constants);
 Result rollout(const State& initial,const std::vector<Cell>& cells);
 phase5_public_coupled_v2::ModelMetadata metadata() const{return derivative_.metadata();}
 private:
 phase5_public_coupled_augmented::Model value_;
 phase5_public_coupled_derivative::Model derivative_;
 Eigen::VectorXd C_lower_,C_upper_;
 void domain(const State& z) const;
 static Eigen::VectorXd packed(const State& z);
 static void local(const Eigen::MatrixXd& physical,double progress_dt,Eigen::MatrixXd& A,Eigen::MatrixXd& B);
 static Map mapping(int cell,int cycle,int half,const State& origin,const State& endpoint,const State& cell_origin,const Eigen::VectorXd& input,const Eigen::MatrixXd& A,const Eigen::MatrixXd& B,const Eigen::MatrixXd& prior_A,const Eigen::MatrixXd& prior_B);
};
}
