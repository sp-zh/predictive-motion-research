#include "public_affine_horizon_internal.hpp"
#include "public_coupled_augmented_extension.hpp"
#include <cmath>
namespace phase5_public_affine_horizon {
using namespace detail;
namespace {
Vector pack(const phase5_public_coupled_augmented::State& z,ProblemBudget& b){
 require(z.q.size()==7&&z.v.size()==7&&z.C.size()==7&&z.w.size()==7,"native state dimensions");
 auto v=zeros(30,b);v<<z.q,z.v,z.C,z.w,z.s,z.r;finite(v);return v;
}
Matrix copyM(const Matrix& m,ProblemBudget& b){finite(m);auto v=zeros(m.rows(),m.cols(),b);v=m;return v;}
Vector copyV(const Vector& m,ProblemBudget& b){finite(m);auto v=zeros(m.size(),b);v=m;return v;}
void dimensions(const phase5_public_coupled_augmented_extension::Map& m){
 require(m.A.rows()==30&&m.A.cols()==30&&m.B.rows()==30&&m.B.cols()==8&&m.defect.size()==30&&
 m.cell_A.rows()==30&&m.cell_A.cols()==30&&m.cell_B.rows()==30&&m.cell_B.cols()==8&&m.cell_defect.size()==30&&m.input.size()==8,"native map dimensions");
 finite(m.A);finite(m.B);finite(m.defect);finite(m.cell_A);finite(m.cell_B);finite(m.cell_defect);finite(m.input);
}
}
Problem normalize_public_native(const phase5_public_coupled_augmented_extension::Result& saved,const Problem& descriptor,const SourceIdentity& identity,const Limits& l,ProblemBudget& b){
 fixed(l);require(saved.value.success&&saved.value.has_final_state&&saved.extension_jacobian_success&&saved.first_uncertified_substep==-1,"native incomplete/unsupported source refusal");
 require(descriptor.nx==30&&descriptor.nu==8&&descriptor.source.full_nominal_source_certified&&
 identity.full_nominal_source_certified&&identity.source_binary_sha256=="f1b7e6c7e4219fec2beb310540c725b448dcf021b3a95ddafc2922e8849bf1d6"&&
 identity.certificate_name=="COMMAND_PROGRESS_EXTENSION_JACOBIAN_STRICT_PHYSICAL_V1"&&!identity.file_sha256.empty(),"native provenance/descriptor");
 const auto N=descriptor.cells.size();require(N>0&&N<=l.max_cells&&descriptor.nominal_cells.size()==N,"native descriptor cell cap");
 std::size_t cycles=0;for(const auto& c:descriptor.cells){require(c.cycles>0,"native cycles");cycles=add(cycles,c.cycles);}auto samples=mul(2,cycles);require(samples<=l.max_samples,"native sample cap");
 require(saved.cell_maps.size()==N&&saved.cycle_maps.size()==cycles&&saved.substep_maps.size()==samples&&saved.value.cell_end_states.size()==N&&saved.value.cycle_end_states.size()==cycles&&saved.value.substeps.size()==samples&&descriptor.nominal_samples.size()==samples,"native exact complete roster");
 Problem p;p.nx=30;p.nu=8;p.source=identity;p.actual_initial=copyV(descriptor.actual_initial,b);p.cells.reserve(N);p.samples.reserve(samples);p.nominal_cells.reserve(N);p.nominal_samples.reserve(samples);
 std::size_t step=0,cy=0;
 for(std::size_t c=0;c<N;++c){const auto& nom=descriptor.nominal_cells[c];const auto& m=saved.cell_maps[c];dimensions(m);
  require(m.cell==int(c)&&m.cycle==descriptor.cells[c].cycles&&m.half==2,"native cell roster");
  auto origin=pack(m.cell_origin,b),end=pack(m.state,b);require(exact(origin,nom.origin)&&exact(m.input,nom.input)&&exact(end,nom.endpoint)&&exact(end,pack(saved.value.cell_end_states[c],b)),"native wholecell literal origins/input/end");
  Transition t;t.cycles=descriptor.cells[c].cycles;t.A=copyM(m.cell_A,b);t.B=copyM(m.cell_B,b);t.defect=copyV(m.cell_defect,b);p.cells.push_back(std::move(t));
  p.nominal_cells.push_back({std::move(origin),copyV(m.input,b),std::move(end)});
  for(int k=1;k<=descriptor.cells[c].cycles;++k){const auto& cm=saved.cycle_maps[cy];dimensions(cm);
   require(cm.cell==int(c)&&cm.cycle==k&&cm.half==2&&exact(pack(cm.cell_origin,b),nom.origin)&&exact(cm.input,nom.input)&&exact(pack(cm.state,b),pack(saved.value.cycle_end_states[cy],b)),"native cycle roster/value");
   // Cycle-local origin uses the prior literal cycle map endpoint. Half2 and
   // cycle progress references can differ by rounding; do not replace either.
   auto prior=k==1?copyV(nom.origin,b):pack(saved.cycle_maps[cy-1].state,b);
   require(exact(pack(cm.origin,b),prior),"native cycle-local origin");
   residual(cm.A,cm.B,cm.defect,prior,cm.input,pack(cm.state,b),l,b);
   residual(cm.cell_A,cm.cell_B,cm.cell_defect,nom.origin,cm.input,pack(cm.state,b),l,b);
   for(int h=1;h<=2;++h){const auto& sm=saved.substep_maps[step];dimensions(sm);const auto& v=saved.value.substeps[step];
    require(sm.cell==int(c)&&sm.cycle==k&&sm.half==h&&v.cell==int(c)&&v.cycle==k&&v.half==h,"native half roster");
    require(std::isfinite(v.elapsed_s)&&std::abs(v.elapsed_s-.002*(step+1))<=l.arithmetic_abs+l.arithmetic_rel*std::abs(v.elapsed_s),"native elapsed time");
    auto so=pack(sm.cell_origin,b),se=pack(sm.state,b);require(exact(so,nom.origin)&&exact(sm.input,nom.input)&&exact(pack(sm.origin,b),prior),"native sample origin/input");
    phase5_public_coupled_augmented::State physical;b.reserve(28);physical.q=v.q;physical.v=v.v;physical.C=v.C;physical.w=v.w;physical.s=v.s_reference;physical.r=v.r_reference;
    require(exact(se,pack(physical,b))&&exact(se,descriptor.nominal_samples[step].endpoint),"native sampled literal value");
    residual(sm.A,sm.B,sm.defect,prior,sm.input,se,l,b);
    Sample s;s.cell=c;s.cycle=k;s.half=h;s.A=copyM(sm.cell_A,b);s.B=copyM(sm.cell_B,b);s.defect=copyV(sm.cell_defect,b);p.samples.push_back(std::move(s));
    p.nominal_samples.push_back({std::move(so),copyV(sm.input,b),std::move(se)});++step;
   }++cy;
  }
 }
 require(exact(pack(saved.value.final_state,b),p.nominal_cells.back().endpoint),"native final state");return p;
}
} // namespace phase5_public_affine_horizon
