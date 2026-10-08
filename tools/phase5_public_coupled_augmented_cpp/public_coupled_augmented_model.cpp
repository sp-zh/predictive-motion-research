#include "public_coupled_augmented_model.hpp"
#include <yaml-cpp/yaml.h>
#include <cmath>
#include <stdexcept>
namespace phase5_public_coupled_augmented {
namespace {
void need(bool condition,const char* message) {if(!condition)throw std::invalid_argument(message);}
}
Model::Model(const std::string& xml,const std::string& constants):base_(xml,constants) {
 auto c=YAML::LoadFile(constants);q_lower_.resize(7);q_upper_.resize(7);C_lower_.resize(7);C_upper_.resize(7);
 for(int j=0;j<7;++j) {
  need(c["joint_limited"][j].as<int>()==1 && c["control_limited"][j].as<int>()==1,"fixed bounded FR3 command/joint profile");
  q_lower_(j)=c["joint_range"][2*j].as<double>();q_upper_(j)=c["joint_range"][2*j+1].as<double>();
  C_lower_(j)=c["control_range"][2*j].as<double>();C_upper_(j)=c["control_range"][2*j+1].as<double>();
 }
 need(q_lower_.allFinite() && q_upper_.allFinite() && C_lower_.allFinite() && C_upper_.allFinite(),"finite augmented static ranges");
}
void Model::progress(double s,double r) {
 need(std::isfinite(s) && std::isfinite(r),"finite progress state/reference");
 need(s>=0 && s<=1 && r>=0 && r<=progress_r,"declared progress state/reference domain");
}
void Model::state(const State& z) const {
 need(z.q.size()==7 && z.v.size()==7 && z.C.size()==7 && z.w.size()==7,"augmented q/v/C/w dimension7");
 need(z.q.allFinite() && z.v.allFinite() && z.C.allFinite() && z.w.allFinite(),"finite augmented q/v/C/w");
 need((z.q.array()>q_lower_.array()).all() && (z.q.array()<q_upper_.array()).all(),"strict physical joint-limit-free domain");
 need((z.C.array()>=C_lower_.array()).all() && (z.C.array()<=C_upper_.array()).all(),"accepted C within public control domain; no clipping");
 need((z.w.array().abs()<=command_v).all(),"declared accepted command velocity domain");progress(z.s,z.r);
}
Result Model::rollout(const State& initial,const std::vector<Cell>& cells) {
 Result out;
 try {
  state(initial);out.final_state=initial;out.has_final_state=true;
  need(!cells.empty() && cells.size()<=max_cells,"positive bounded mesh cell roster");
  int total=0;
  for(const auto& cell:cells) {
   need(cell.cycles>0 && cell.cycles<=max_cycles && total<=max_cycles-cell.cycles,"positive integer4ms mesh cycles within total cap");total+=cell.cycles;
   need(cell.alpha.size()==7 && cell.alpha.allFinite() && std::isfinite(cell.b),"finite alpha7/b input");
   need((cell.alpha.array().abs()<=command_a).all(),"declared command acceleration domain");
  }
  int completed=0;
  for(std::size_t index=0;index<cells.size();++index) {
   const auto& cell=cells[index];State origin=out.final_state;
   for(int k=1;k<=cell.cycles;++k) {
    const State before=out.final_state;State next=before;
    // Accepted command history is independent of physical v/q.
    next.w=before.w+cycle_dt*cell.alpha;
    next.C=before.C+cycle_dt*next.w;
    double next_s=before.s+cycle_dt*before.r+.5*cycle_dt*cycle_dt*cell.b;
    double next_r=before.r+cycle_dt*cell.b;
    need(next.w.allFinite() && next.C.allFinite(),"nonfinite command update arithmetic");
    next.s=next_s;next.r=next_r;state(next);
    for(int half=1;half<=2;++half) {
     double t=cycle_dt*(k-1)+substep_dt*half;
     double ref_s=origin.s+t*origin.r+.5*t*t*cell.b,ref_r=origin.r+t*cell.b;
     progress(ref_s,ref_r);
     auto physical=base_.step(next.q,next.v,next.C);
     need(physical.control_clips==0,"unexpected base control clipping; reject augmented C");
     next.q=physical.q;next.v=physical.v;state(next);
     Substep point;point.cell=index;point.cycle=k;point.half=half;
     point.elapsed_s=substep_dt*(2*completed+half);point.s_reference=ref_s;point.r_reference=ref_r;
     point.q=next.q;point.v=next.v;point.C=next.C;point.w=next.w;point.friction=physical.friction;
     point.control_clips=physical.control_clips;point.force_clips=physical.force_clips;out.substeps.push_back(std::move(point));
    }
    out.final_state=next;out.cycle_end_states.push_back(next);++completed;
   }
   out.cell_end_states.push_back(out.final_state);
  }
  out.success=true;
 }catch(const std::exception& e){out.error=e.what();}
 // On failure, final_state is the last complete cycle (or validated initial);
 // all successfully completed half steps remain in substeps, never discarded.
 return out;
}
} // namespace phase5_public_coupled_augmented
