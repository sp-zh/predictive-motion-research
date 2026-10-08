#pragma once
#include "public_coupled_model.hpp"
#include <Eigen/Core>
#include <string>
#include <vector>
namespace phase5_public_coupled_augmented {
struct State {Eigen::VectorXd q,v,C,w;double s=0,r=0;};
struct Cell {int cycles=0;Eigen::VectorXd alpha;double b=0;};
struct Substep {
 int cell=0,cycle=0,half=0;double elapsed_s=0,s_reference=0,r_reference=0;
 Eigen::VectorXd q,v,C,w;phase5_public_coupled_v2::BoxResult friction;
 int control_clips=0,force_clips=0;
};
struct Result {
 bool success=false,has_final_state=false;std::string error;
 State final_state;std::vector<Substep> substeps;
 std::vector<State> cycle_end_states,cell_end_states;
};
// Numerical component domain: inherited fixed-FR3 strict physical q/free-contact
// regime, finite physical v; C within public control bounds; |w|<=.0625,
// |alpha|<=1, s in[0,1], r in[0,.2], finite signed b.
// Positive integer4ms cycles; <=512cells and <=5000each/totalcycles.
// No silent command/progress clipping/reset; physical force clamps belong to
// the frozen base v2 law and are returned explicitly. No jerk/physical-guard,
// controller, task, accuracy-domain or real-time acceptance is implied.
class Model {
 public:
 static constexpr double cycle_dt=.004,substep_dt=.002;
 static constexpr int max_cells=512,max_cycles=5000;
 static constexpr double command_v=.0625,command_a=1.,progress_r=.2;
 Model(const std::string& xml,const std::string& constants);
 Result rollout(const State& initial,const std::vector<Cell>& cells);
 phase5_public_coupled_v2::ModelMetadata metadata() const {return base_.metadata();}
 private:
 phase5_public_coupled_v2::Model base_;
 Eigen::VectorXd q_lower_,q_upper_,C_lower_,C_upper_;
 void state(const State& value) const;
 static void progress(double s,double r);
};
} // namespace phase5_public_coupled_augmented
