#include "public_coupled_finite_trial.hpp"
#include <yaml-cpp/yaml.h>
#include <stdexcept>
#include <algorithm>
namespace phase5_public_coupled_finite_trial {
namespace {
void need(bool x,const char* message){if(!x)throw std::invalid_argument(message);}
}
Model::Model(const std::string& xml,const std::string& constants):
 extension_(xml,constants),value_(xml,constants),physical_(xml,constants) {
 auto c=YAML::LoadFile(constants);C_lower_.resize(7);C_upper_.resize(7);
 for(int j=0;j<7;++j){C_lower_(j)=c["control_range"][2*j].as<double>();C_upper_(j)=c["control_range"][2*j+1].as<double>();}
 need(C_lower_.allFinite() && C_upper_.allFinite(),"finite original C ranges");
}
Eigen::VectorXd Model::pack(const State& z) {
 need(z.q.size()==7 && z.v.size()==7 && z.C.size()==7 && z.w.size()==7,"finite trial state dimensions");
 Eigen::VectorXd a(30);a<<z.q,z.v,z.C,z.w,z.s,z.r;need(a.allFinite(),"finite trial packed state");return a;
}
State Model::point(const phase5_public_coupled_augmented::Substep& p) {
 State z;z.q=p.q;z.v=p.v;z.C=p.C;z.w=p.w;z.s=p.s_reference;z.r=p.r_reference;return z;
}
std::vector<Inspection> Model::inspect(const Input& input,const phase5_public_coupled_augmented::Result& value) {
 std::vector<Inspection> list;Eigen::VectorXd q=input.state.q,v=input.state.v;
 for(const auto& p:value.substeps) {
  Inspection a;a.cell=p.cell;a.cycle=p.cycle;a.half=p.half;a.elapsed_s=p.elapsed_s;
  a.q_before=q;a.v_before=v;a.C=p.C;a.physical=physical_.step(q,v,p.C);
  const auto& d=a.physical;
  a.exact_value_parity=d.value_success && d.value.q.size()==p.q.size() && d.value.v.size()==p.v.size() &&
   (d.value.q.array()==p.q.array()).all() && (d.value.v.array()==p.v.array()).all();
  need(a.exact_value_parity,"original physical value differs from original closed rollout");
  a.strict_C=p.C.size()==7 && (p.C.array()>C_lower_.array()+phase5_public_coupled_derivative::Model::control_margin).all() &&
   (p.C.array()<C_upper_.array()-phase5_public_coupled_derivative::Model::control_margin).all();
  a.signature_complete=d.control.size()==7 && d.actuator.size()==7 && d.joint_force.size()==7 && d.value.friction.branches.size()==7;
  list.push_back(std::move(a));q=p.q;v=p.v;
 }
 return list;
}
bool Model::strict(const Inspection& a) {
 return a.exact_value_parity && a.strict_C && a.signature_complete && a.physical.jacobian_success;
}
bool Model::signatureEqual(const Inspection& a,const Inspection& b) {
 if(!a.signature_complete || !b.signature_complete)return false;
 const auto& x=a.physical;const auto& y=b.physical;
 for(int j=0;j<7;++j) {
  for(const auto& pair:{std::make_pair(&x.control[j],&y.control[j]),std::make_pair(&x.actuator[j],&y.actuator[j]),std::make_pair(&x.joint_force[j],&y.joint_force[j])})
   if(pair.first->enabled!=pair.second->enabled || pair.first->side!=pair.second->side)return false;
  if(x.value.friction.branches[j]!=y.value.friction.branches[j])return false;
 }
 return true;
}
void Model::affine(const Input& nominal,const Input& trial,Result& r) {
 if(!nominal.parse_error.empty() || !trial.parse_error.empty() || !r.mesh_matches)return;
 if(r.nominal.substep_maps.empty() || r.trial.substeps.empty())return;
 Eigen::VectorXd deviation=pack(trial.state)-pack(nominal.state);need(deviation.allFinite(),"initial deviation overflow");
 const auto& n=r.nominal;const auto& t=r.trial;
 for(int cell=0;cell<int(nominal.cells.size());++cell) {
  const bool nominal_prefix=std::any_of(n.substep_maps.begin(),n.substep_maps.end(),[&](const auto& m){return m.cell==cell;});
  const bool trial_prefix=std::any_of(t.substeps.begin(),t.substeps.end(),[&](const auto& p){return p.cell==cell;});
  if(!nominal_prefix || !trial_prefix)break;
  need(nominal.cells[cell].alpha.size()==7 && trial.cells[cell].alpha.size()==7,"cell input dimensions");
  Eigen::VectorXd du(8);du.head(7)=trial.cells[cell].alpha-nominal.cells[cell].alpha;du(7)=trial.cells[cell].b-nominal.cells[cell].b;
  need(du.allFinite(),"cell input deviation overflow");
  auto record=[&](const phase5_public_coupled_augmented_extension::Map& map,const State* actual,const char* kind) {
   if(!actual)return;
   Residual a;a.endpoint=kind;a.cell=map.cell;a.cycle=map.cycle;a.half=map.half;a.nominal_state=map.state;
   a.trial_state=*actual;a.nominal_cell_origin=map.cell_origin;a.cell_origin_deviation=deviation;a.input_deviation=du;
   a.linear_deviation=map.cell_A*deviation+map.cell_B*du;need(a.linear_deviation.allFinite(),"cell prefix affine deviation overflow");
   a.prediction=pack(map.state)+a.linear_deviation;need(a.prediction.allFinite(),"literal nominal baseline plus deviation overflow");
   a.residual=pack(*actual)-a.prediction;need(a.residual.allFinite(),"actual minus affine prediction overflow");r.residuals.push_back(std::move(a));
  };
  for(const auto& m:n.substep_maps)if(m.cell==cell) {
   const State* found=nullptr;State actual;
   for(const auto& p:t.substeps)if(p.cell==m.cell && p.cycle==m.cycle && p.half==m.half){actual=point(p);found=&actual;break;}
   record(m,found,"substep");
  }
  for(const auto& m:n.cycle_maps)if(m.cell==cell) {
   int offset=0;for(int j=0;j<cell;++j)offset+=nominal.cells[j].cycles;int index=offset+m.cycle-1;
   record(m,index>=0 && index<int(t.cycle_end_states.size())?&t.cycle_end_states[index]:nullptr,"cycle");
  }
  const phase5_public_coupled_augmented_extension::Map* end=nullptr;
  for(const auto& m:n.cell_maps)if(m.cell==cell){end=&m;break;}
  if(!end)break; // A certified whole cell is needed to propagate the nominal chain.
  record(*end,cell<int(t.cell_end_states.size())?&t.cell_end_states[cell]:nullptr,"cell");
  Eigen::VectorXd next=end->cell_A*deviation+end->cell_B*du;
  need(next.allFinite(),"cell-chain deviation overflow");deviation=std::move(next);
 }
}
Result Model::diagnose(const Input& ni,const Input& ti) {
 Result r;
 if(ni.parse_error.empty())r.nominal=extension_.rollout(ni.state,ni.cells);
 else {r.nominal.value.error=ni.parse_error;r.nominal.error=ni.parse_error;r.nominal.first_uncertified_substep=0;}
 if(ti.parse_error.empty())r.trial=value_.rollout(ti.state,ti.cells);else r.trial.error=ti.parse_error;
 r.mesh_matches=ni.parse_error.empty() && ti.parse_error.empty() && ni.cells.size()==ti.cells.size();
 if(r.mesh_matches)for(std::size_t j=0;j<ni.cells.size();++j)r.mesh_matches=r.mesh_matches && ni.cells[j].cycles==ti.cells[j].cycles;
 r.all_forward_complete=r.nominal.value.success && r.trial.success;
 try {
  r.nominal_inspections=inspect(ni,r.nominal.value);r.trial_inspections=inspect(ti,r.trial);
  r.all_sampled_strict=r.all_forward_complete && !r.nominal_inspections.empty() && r.nominal_inspections.size()==r.trial_inspections.size();
  for(const auto& a:r.nominal_inspections)r.all_sampled_strict=r.all_sampled_strict && strict(a);
  for(const auto& a:r.trial_inspections)r.all_sampled_strict=r.all_sampled_strict && strict(a);
  r.all_sampled_signatures_equal=r.mesh_matches && r.all_forward_complete && r.nominal_inspections.size()==r.trial_inspections.size() && !r.nominal_inspections.empty();
  if(r.mesh_matches)for(std::size_t j=0;j<std::min(r.nominal_inspections.size(),r.trial_inspections.size());++j) {
   const auto& a=r.nominal_inspections[j];const auto& b=r.trial_inspections[j];
   need(a.cell==b.cell && a.cycle==b.cycle && a.half==b.half && a.elapsed_s==b.elapsed_s,"matching nominal/trial sampled timestamps");
   Comparison c;c.cell=a.cell;c.cycle=a.cycle;c.half=a.half;c.elapsed_s=a.elapsed_s;
   c.nominal_strict=strict(a);c.trial_strict=strict(b);c.signatures_available=a.signature_complete && b.signature_complete;
   c.branches_equal=c.signatures_available && signatureEqual(a,b);r.comparisons.push_back(c);
   if(c.signatures_available && !c.branches_equal)r.sampled_branch_change=true;
   r.all_sampled_signatures_equal=r.all_sampled_signatures_equal && c.branches_equal;
  }
  if(!ni.parse_error.empty() || !ti.parse_error.empty())r.outcome="forward_failed";
  else if(!r.mesh_matches)r.outcome="mesh_mismatch";
  else if(!r.all_forward_complete)r.outcome="forward_failed";
  else if(!r.all_sampled_strict || !r.nominal.extension_jacobian_success)r.outcome="unsupported";
  else if(r.sampled_branch_change)r.outcome="sampled_branch_changed";
  else {need(r.all_sampled_signatures_equal,"complete exact signatures");r.outcome="sampled_strict_branches_unchanged";}
 }catch(const std::exception& e){r.outcome="diagnostic_error";r.error=e.what();}
 try{affine(ni,ti,r);}catch(const std::exception& e){r.affine_error=e.what();}
 return r;
}
}
