#pragma once
#include "public_coupled_augmented_extension.hpp"
#include <string>
#include <vector>
namespace phase5_public_coupled_finite_trial {
using State=phase5_public_coupled_augmented::State;
using Cell=phase5_public_coupled_augmented::Cell;
struct Input {
 State state;std::vector<Cell> cells;std::string parse_error;
};
struct Inspection {
 int cell=0,cycle=0,half=0;double elapsed_s=0;
 Eigen::VectorXd q_before,v_before,C;
 phase5_public_coupled_derivative::Result physical;
 bool exact_value_parity=false,strict_C=false,signature_complete=false;
};
struct Comparison {
 int cell=0,cycle=0,half=0;double elapsed_s=0;
 bool nominal_strict=false,trial_strict=false,signatures_available=false,branches_equal=false;
};
struct Residual {
 std::string endpoint;int cell=0,cycle=0,half=0;
 State nominal_state,trial_state,nominal_cell_origin;
 Eigen::VectorXd cell_origin_deviation,input_deviation,linear_deviation,prediction,residual;
};
struct Result {
 phase5_public_coupled_augmented_extension::Result nominal;
 phase5_public_coupled_augmented::Result trial;
 std::vector<Inspection> nominal_inspections,trial_inspections;
 std::vector<Comparison> comparisons;
 std::vector<Residual> residuals;
 bool mesh_matches=false,all_forward_complete=false,all_sampled_strict=false;
 bool sampled_branch_change=false,all_sampled_signatures_equal=false;
 std::string outcome="diagnostic_error",error,affine_error;
};
// Sampled endpoints only. No segment, ball, admissibility, execution, safety,
// uniform error bound, optimizer or controller certificate.
class Model {
 public:
 static constexpr const char* policy_name="FINITE_CLOSED_TRIAL_SAMPLED_BRANCH_DIAGNOSTIC_V1";
 Model(const std::string& xml,const std::string& constants);
 Result diagnose(const Input& nominal,const Input& trial);
 phase5_public_coupled_v2::ModelMetadata metadata() const{return extension_.metadata();}
 private:
 phase5_public_coupled_augmented_extension::Model extension_;
 phase5_public_coupled_augmented::Model value_;
 phase5_public_coupled_derivative::Model physical_;
 Eigen::VectorXd C_lower_,C_upper_;
 std::vector<Inspection> inspect(const Input& input,const phase5_public_coupled_augmented::Result& value);
 static Eigen::VectorXd pack(const State& state);
 static State point(const phase5_public_coupled_augmented::Substep& point);
 static bool signatureEqual(const Inspection& a,const Inspection& b);
 static bool strict(const Inspection& a);
 static void affine(const Input& nominal,const Input& trial,Result& result);
};
}
