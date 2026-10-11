#include "normalization.hpp"
#include <algorithm>
#include <cmath>
#include <stdexcept>
#include <utility>

namespace phase5_active_session_v1 {
namespace {
using NativeState=phase5_public_coupled_augmented::State;
using NativeMap=phase5_public_coupled_augmented_extension::Map;
using NativeCell=phase5_public_coupled_augmented::Cell;
// Same nominal arithmetic defaults as the frozen v1 algebra source; not tunable.
constexpr double nominal_abs=2e-13,nominal_rel=2e-13;
constexpr Count scratch_slots=640;
void need(bool condition,const char* reason){if(!condition)throw std::invalid_argument(reason);}
void near(double a,double b){
  need(std::isfinite(a)&&std::isfinite(b),"nonfinite nominal identity operands");
  const double error=std::abs(a-b),limit=nominal_abs+nominal_rel*std::max(std::abs(a),std::abs(b));
  need(std::isfinite(error)&&std::isfinite(limit)&&error<=limit,"nominal arithmetic identity mismatch");
}
void stateShape(const NativeState& s){
  need(s.q.size()==7&&s.v.size()==7&&s.C.size()==7&&s.w.size()==7&&s.q.allFinite()&&s.v.allFinite()&&
       s.C.allFinite()&&s.w.allFinite()&&std::isfinite(s.s)&&std::isfinite(s.r),"finite native state30 shape required");
}
void domain(const NativeState& s,const StaticDomainRanges& ranges){
  stateShape(s);
  for(int j=0;j<7;++j)need(s.q(j)>ranges.qLower()[j]&&s.q(j)<ranges.qUpper()[j]&&
    s.C(j)>=ranges.cLower()[j]&&s.C(j)<=ranges.cUpper()[j]&&std::abs(s.w(j))<=.0625,
    "native nominal physical/command domain mismatch");
  need(s.s>=0&&s.s<=1&&s.r>=0&&s.r<=.2,"native nominal progress domain mismatch");
}
double coordinate(const NativeState& s,Count j){
  if(j<7)return s.q(j);if(j<14)return s.v(j-7);if(j<21)return s.C(j-14);if(j<28)return s.w(j-21);
  return j==28?s.s:s.r;
}
bool equal(const NativeState& a,const NativeState& b){
  stateShape(a);stateShape(b);
  for(Count j=0;j<30;++j)if(coordinate(a,j)!=coordinate(b,j))return false;
  return true;
}
void actualInitial(const NativeState& s,const State30& actual){
  stateShape(s);
  for(int j=0;j<7;++j)need(s.q(j)==actual.q[j]&&s.v(j)==actual.v[j]&&s.C(j)==actual.C[j]&&s.w(j)==actual.w[j],
                           "actual initial coordinate mismatch");
  need(s.s==actual.s&&s.r==actual.r,"actual initial progress mismatch");
}
void mapShape(const NativeMap& m){
  stateShape(m.origin);stateShape(m.cell_origin);stateShape(m.state);
  need(m.input.size()==8&&m.input.allFinite()&&m.A.rows()==30&&m.A.cols()==30&&m.A.allFinite()&&
    m.B.rows()==30&&m.B.cols()==8&&m.B.allFinite()&&m.defect.size()==30&&m.defect.allFinite()&&
    m.cell_A.rows()==30&&m.cell_A.cols()==30&&m.cell_A.allFinite()&&m.cell_B.rows()==30&&m.cell_B.cols()==8&&
    m.cell_B.allFinite()&&m.cell_defect.size()==30&&m.cell_defect.allFinite(),"finite native local/cumulative map shape required");
}
void matrixEqual(const Eigen::MatrixXd& a,const Eigen::MatrixXd& b){
  need(a.rows()==b.rows()&&a.cols()==b.cols(),"native duplicate matrix shape mismatch");
  for(Eigen::Index i=0;i<a.rows();++i)for(Eigen::Index j=0;j<a.cols();++j)need(a(i,j)==b(i,j),"native duplicate matrix mismatch");
}
void vectorEqual(const Eigen::VectorXd& a,const Eigen::VectorXd& b){
  need(a.size()==b.size(),"native duplicate vector shape mismatch");
  for(Eigen::Index j=0;j<a.size();++j)need(a(j)==b(j),"native duplicate vector mismatch");
}
void duplicate(const NativeMap& cell,const NativeMap& cycle){
  need(cell.cell==cycle.cell&&cell.cycle==cycle.cycle&&cell.half==cycle.half&&
    equal(cell.origin,cycle.origin)&&equal(cell.cell_origin,cycle.cell_origin)&&equal(cell.state,cycle.state),
    "wholecell must retain exact lastcycle native record");
  vectorEqual(cell.input,cycle.input);matrixEqual(cell.A,cycle.A);matrixEqual(cell.B,cycle.B);
  vectorEqual(cell.defect,cycle.defect);matrixEqual(cell.cell_A,cycle.cell_A);matrixEqual(cell.cell_B,cycle.cell_B);
  vectorEqual(cell.cell_defect,cycle.cell_defect);
}
void finiteProduct(double a,double b,double& sum){
  const double product=a*b;need(std::isfinite(product),"nominal product overflow");
  sum+=product;need(std::isfinite(sum),"nominal product-sum overflow");
}
void canonicalLocal(const NativeMap& m,Count half){
  const double t=physical_dt*static_cast<double>(half);
  // Physical target sensitivity is independent of virtual progress. Command
  // history advances a full4ms even in the first2ms physical sample.
  for(Count row=0;row<14;++row){
    need(m.A(row,28)==0&&m.A(row,29)==0&&m.B(row,7)==0,"physical/progress local block mismatch");
    for(Count j=0;j<7;++j){near(m.A(row,21+j),macro_dt*m.A(row,14+j));
      near(m.B(row,j),macro_dt*macro_dt*m.A(row,14+j));}
  }
  for(Count row=14;row<30;++row){
    for(Count col=0;col<30;++col){
      double expected=0;
      if(row<21){if(col==row)expected=1;if(col==row+7)expected=macro_dt;}
      else if(row<28){if(col==row)expected=1;}
      else if(row==28){if(col==28)expected=1;if(col==29)expected=t;}
      else if(col==29)expected=1;
      need(m.A(row,col)==expected,"canonical local command/progress A block mismatch");
    }
    for(Count col=0;col<8;++col){
      double expected=0;
      if(row<21&&col==row-14)expected=macro_dt*macro_dt;
      else if(row>=21&&row<28&&col==row-21)expected=macro_dt;
      else if(row==28&&col==7)expected=.5*t*t;
      else if(row==29&&col==7)expected=t;
      need(m.B(row,col)==expected,"canonical local command/progress B block mismatch");
    }
  }
}
void mapping(const NativeMap& m,Count cell,Count cycle,Count half,const NativeCell& input,
    const NativeState& origin,const NativeState& cell_origin,const NativeState& endpoint,
    const NativeMap* prior,double* scratch,CaseBudget& budget,MathCaptureTrace& trace){
  budget.chargeScratchOrCopy(scratch_slots);
  trace.memory_item=trace.item;trace.memory_stage=trace.stage;
  for(Count j=0;j<4;++j)trace.written[j]=0;std::fill_n(scratch,120,0.); // Reused fixed work charged before every map check.
  mapShape(m);
  canonicalLocal(m,half);
  need(m.cell==static_cast<int>(cell)&&m.cycle==static_cast<int>(cycle)&&m.half==static_cast<int>(half),
       "exact native map index/half roster mismatch");
  need(equal(m.origin,origin)&&equal(m.cell_origin,cell_origin)&&equal(m.state,endpoint),
       "literal map origin/endpoint source parity mismatch");
  for(int j=0;j<7;++j)need(m.input(j)==input.alpha(j),"independent cell alpha input mismatch");
  need(m.input(7)==input.b,"independent cell progress input mismatch");
  // Preserve the native defects. Check their defining subtraction order, and
  // independently check cumulative composition against previous complete cycle.
  for(Count row=0;row<30;++row){trace.row=row;
    double a=0,b=0,ca=0,cb=0;
    for(Count j=0;j<30;++j){finiteProduct(m.A(row,j),coordinate(origin,j),a);
      finiteProduct(m.cell_A(row,j),coordinate(cell_origin,j),ca);}
    for(Count j=0;j<8;++j){finiteProduct(m.B(row,j),m.input(j),b);finiteProduct(m.cell_B(row,j),m.input(j),cb);}
    scratch[row]=coordinate(endpoint,row)-a;++trace.written[0];need(std::isfinite(scratch[row]),"local nominal subtraction overflow");
    scratch[30+row]=scratch[row]-b;++trace.written[1];near(scratch[30+row],m.defect(row));
    scratch[60+row]=coordinate(endpoint,row)-ca;++trace.written[2];need(std::isfinite(scratch[60+row]),"cumulative nominal subtraction overflow");
    scratch[90+row]=scratch[60+row]-cb;++trace.written[3];near(scratch[90+row],m.cell_defect(row));
    for(Count col=0;col<30;++col){
      double value=0;
      if(prior)for(Count j=0;j<30;++j)finiteProduct(m.A(row,j),prior->cell_A(j,col),value);
      else value=m.A(row,col);
      near(value,m.cell_A(row,col));
    }
    for(Count col=0;col<8;++col){
      double value=0;
      if(prior)for(Count j=0;j<30;++j)finiteProduct(m.A(row,j),prior->cell_B(j,col),value);
      value+=m.B(row,col);need(std::isfinite(value),"cumulative input-sum overflow");near(value,m.cell_B(row,col));
    }
  }
}
void commandAndProgress(const NativeState& before,const NativeState& after,const NativeCell& control){
  // Literal recursive4ms law, distinct from the cell-origin sample polynomial.
  for(int j=0;j<7;++j){
    const double w=before.w(j)+macro_dt*control.alpha(j);
    const double C=before.C(j)+macro_dt*w;
    need(std::isfinite(w)&&std::isfinite(C)&&after.w(j)==w&&after.C(j)==C,"recursive command4ms law mismatch");
  }
  const double s=before.s+macro_dt*before.r+.5*macro_dt*macro_dt*control.b,r=before.r+macro_dt*control.b;
  need(std::isfinite(s)&&std::isfinite(r)&&after.s==s&&after.r==r,"recursive progress4ms law mismatch");
}
} // namespace

namespace detail {
struct NormalizationDiagnostics {
  OwnedNumericBuffer scratch;MathCaptureTrace trace;bool capture_active=false,poisoned=false;std::string capture_error;
  void reject(const char* why) noexcept{if(poisoned)return;poisoned=true;trace.complete=false;try{capture_error=why?why:"NORMALIZATION_CAPTURE_REFUSAL";}catch(...){}}
  explicit NormalizationDiagnostics(CaseBudget& b):scratch(b,scratch_slots){std::fill_n(scratch.data(),120,0.);trace.stage="NORMALIZE_DEFINED_PLACEHOLDERS";}
};
struct RawAnchor {OwnedPublicForecast forecast;explicit RawAnchor(OwnedPublicForecast&& s) noexcept:forecast(std::move(s)){} };
struct NormalizedInventory {
  OwnedReservation ticket;std::shared_ptr<RawAnchor> anchor;
  std::vector<NormalizedBlockView> cells,samples;
  NormalizedInventory(OwnedReservation&& reserved,std::shared_ptr<RawAnchor> source)
    :ticket(std::move(reserved)),anchor(std::move(source)){}
};
struct NormalizationFactory {
  static CaseBudget& budget(OwnedPublicForecast& source){return source.normalizationBudget();}
  static const ResourcePlan& plan(const OwnedPublicForecast& source){return source.normalizationPlan();}
  static NormalizationOutcome normalize(OwnedPublicForecast&& source){
    NormalizationOutcome out(std::move(source));
    try {
      auto& raw_source=out.original_;
      need(raw_source.transportFailure().empty()&&raw_source.structuralRefusal().empty(),"source transport/structural refusal retained");
      const auto* saved=raw_source.originalResult();need(saved,"no genuine returned raw result");
      const auto& raw=*saved;const auto& mesh=raw_source.mesh();const auto& cells=raw_source.nativeCells();
      const Count n=mesh.cycles().size(),t=mesh.total(),s=checkedMultiply(2,t);
      need(raw.value.success&&raw.value.has_final_state&&raw.extension_jacobian_success&&
        raw.first_uncertified_substep==-1&&raw.error.empty()&&raw.value.error.empty(),"unsupported/incomplete nominal source flags retained");
      need(n>0&&n<=32&&t>=n&&t<=375&&s<=750&&cells.size()==n&&raw.cell_maps.size()==n&&raw.cycle_maps.size()==t&&
        raw.substep_maps.size()==s&&raw.value.cell_end_states.size()==n&&raw.value.cycle_end_states.size()==t&&
        raw.value.substeps.size()==s,"exact complete native value/map mesh roster required");
      auto& budget=raw_source.normalizationBudget();const auto& plan=raw_source.normalizationPlan();
      need(plan.dx()==checkedMultiply(30,n+1)&&plan.du()==checkedMultiply(8,n)&&plan.dy()==checkedAdd(plan.dx(),plan.du()),
           "bound resource plan dimension mismatch");
      need(raw_source.bindingVerified(),"session startup and cycle provenance not verified");
      need(std::string_view(raw_source.normalizationCertificate())=="COMMAND_PROGRESS_EXTENSION_JACOBIAN_STRICT_PHYSICAL_V1",
           "unchanged native nominal certificate policy required");
      // Whole inventory and reused work are reserved before normalization loops.
      auto inventory_ticket=budget.reserve(checkedAdd(checkedMultiply(n,1241),checkedMultiply(s,1243)));
      out.diagnostics_=std::make_unique<NormalizationDiagnostics>(budget);
      auto& diagnostics=*out.diagnostics_;auto& scratch=diagnostics.scratch;
      // Raw ownership does not move again until all complete-record checks pass.
      Count global_cycle=0,step=0;
      const NativeState* before=&raw.substep_maps.front().origin;
      actualInitial(*before,raw_source.actualContext().actualInitial());
      const auto& ranges=raw_source.actualContext().ranges();domain(*before,ranges);
      for(Count cell=0;cell<n;++cell){
        const auto& input=cells.at(cell);need(input.cycles>0&&static_cast<Count>(input.cycles)==mesh.cycles()[cell]&&
          input.alpha.size()==7&&input.alpha.allFinite()&&std::isfinite(input.b)&&
          (input.alpha.array().abs()<=1).all(),"nominal cell cycle/control roster mismatch");
        const NativeState* cell_origin=before;const NativeMap* prior=nullptr;
        for(Count cycle=1;cycle<=mesh.cycles()[cell];++cycle){
          const auto& end=raw.value.cycle_end_states.at(global_cycle);domain(end,ranges);
          commandAndProgress(*before,end,input);
          for(Count half=1;half<=2;++half){diagnostics.trace.stage="VALIDATE_SUBSTEP";diagnostics.trace.item=step;
            const auto& point=raw.value.substeps.at(step);const auto& sm=raw.substep_maps.at(step);
            need(point.cell==static_cast<int>(cell)&&point.cycle==static_cast<int>(cycle)&&point.half==static_cast<int>(half)&&
              point.elapsed_s==physical_dt*static_cast<double>(2*global_cycle+half),"literal value tick/cycle/half/time roster mismatch");
            need(point.q.size()==7&&point.v.size()==7&&point.C.size()==7&&point.w.size()==7&&
              point.q.allFinite()&&point.v.allFinite()&&point.C.allFinite()&&point.w.allFinite()&&
              point.friction.force.size()==7&&point.friction.force.allFinite()&&point.friction.branches.size()==7&&
              point.friction.iterations>=0&&std::isfinite(point.friction.original_kkt)&&point.friction.original_kkt>=0&&
              point.control_clips==0&&point.force_clips>=0&&point.force_clips<=7,"finite raw physical/friction/clip value shape mismatch");
            for(int branch:point.friction.branches)need(branch>=-1&&branch<=2,"native friction branch label mismatch");
            const double local_t=macro_dt*static_cast<double>(cycle-1)+physical_dt*static_cast<double>(half);
            const double ref_s=cell_origin->s+local_t*cell_origin->r+.5*local_t*local_t*input.b;
            const double ref_r=cell_origin->r+local_t*input.b;
            need(std::isfinite(ref_s)&&std::isfinite(ref_r)&&point.s_reference==ref_s&&point.r_reference==ref_r,
                 "literal cell-origin polynomial progress reference mismatch");
            domain(sm.state,ranges);
            for(int j=0;j<7;++j)need(sm.state.q(j)==point.q(j)&&sm.state.v(j)==point.v(j)&&
              sm.state.C(j)==point.C(j)&&sm.state.w(j)==point.w(j)&&point.C(j)==end.C(j)&&point.w(j)==end.w(j),
              "literal halfstep physical/held-command source parity mismatch");
            need(sm.state.s==point.s_reference&&sm.state.r==point.r_reference,"sample map must retain own polynomial progress");
            diagnostics.trace.stage="NORMALIZE_SUBSTEP";mapping(sm,cell,cycle,half,input,*before,*cell_origin,sm.state,prior,scratch.data(),budget,diagnostics.trace);
            if(half==2){
              for(int j=0;j<7;++j)need(point.q(j)==end.q(j)&&point.v(j)==end.v(j),"half2 physical/cycle value parity mismatch");
              // Do NOT compare half2 sample s/r with recursive cycle-end s/r.
            }
            ++step;
          }
          const auto& cm=raw.cycle_maps.at(global_cycle);
          diagnostics.trace.stage="NORMALIZE_CYCLE";diagnostics.trace.item=global_cycle;mapping(cm,cell,cycle,2,input,*before,*cell_origin,end,prior,scratch.data(),budget,diagnostics.trace);
          const auto& second_half=raw.substep_maps.at(step-1);
          // Same local/cumulative derivative matrices, distinct literal progress
          // endpoints/defects. Do not compare or overwrite their s/r defects.
          matrixEqual(cm.A,second_half.A);matrixEqual(cm.B,second_half.B);
          matrixEqual(cm.cell_A,second_half.cell_A);matrixEqual(cm.cell_B,second_half.cell_B);
          if(cycle==mesh.cycles()[cell]){
            need(equal(end,raw.value.cell_end_states.at(cell)),"complete cycle/cell endpoint literal parity mismatch");
            const auto& full=raw.cell_maps.at(cell);mapShape(full);duplicate(full,cm);
          }
          before=&end;prior=&cm;++global_cycle;
        }
      }
      need(step==s&&global_cycle==t&&equal(raw.value.final_state,*before),"complete final literal state mismatch");
      // The source is now anchored in the outcome before any inventory/container
      // allocations, so quota/allocation refusal retains its full original data.
      out.anchor_=std::make_shared<RawAnchor>(std::move(out.original_));
      auto inventory=std::make_unique<NormalizedInventory>(std::move(inventory_ticket),out.anchor_);
      inventory->cells.reserve(static_cast<std::size_t>(n));inventory->samples.reserve(static_cast<std::size_t>(s));
      for(Count k=0;k<n;++k){inventory->cells.push_back(NormalizedBlockView(out.anchor_,false,k));++diagnostics.trace.written[4];}
      for(Count k=0;k<s;++k){inventory->samples.push_back(NormalizedBlockView(out.anchor_,true,k));++diagnostics.trace.written[5];}
      out.maps_.reset(new NormalizedNominalMaps(std::move(inventory)));diagnostics.trace.stage="COMPLETE_NORMALIZATION";diagnostics.trace.complete=true;diagnostics.trace.construction_completed=true;
    }catch(const std::exception& e){out.recordRefusal(e.what());}
    catch(...){out.recordRefusal("NONSTANDARD_NORMALIZATION_FAILURE");}
    return out;
  }
};
} // namespace detail

namespace {
const detail::NormalizedInventory& present(const std::unique_ptr<detail::NormalizedInventory>& p){
  need(static_cast<bool>(p),"moved-from normalized maps");return *p;
}
const NativeMap& cycle(const detail::NormalizedInventory& p,Count index){
  const auto* raw=p.anchor->forecast.originalResult();need(raw,"normalized raw owner missing");return raw->cycle_maps.at(index);
}
}
NormalizedBlockView::NormalizedBlockView(std::shared_ptr<detail::RawAnchor> a,bool sample,Count index)
  :anchor_(std::move(a)),sample_(sample),index_(index){}
const NativeMap& NormalizedBlockView::native() const{
  need(static_cast<bool>(anchor_),"moved-from nominal block view");const auto* raw=anchor_->forecast.originalResult();
  need(raw,"nominal raw owner missing");return sample_?raw->substep_maps.at(index_):raw->cell_maps.at(index_);
}
Count NormalizedBlockView::cell() const{return static_cast<Count>(native().cell);}
Count NormalizedBlockView::cycle() const{return static_cast<Count>(native().cycle);}
Count NormalizedBlockView::half() const{return static_cast<Count>(native().half);}
Count NormalizedBlockView::physicalTick() const{
  need(static_cast<bool>(anchor_),"moved-from nominal block view");
  if(sample_)return checkedAdd(sampleIndex(),1);
  const auto& mesh=anchor_->forecast.mesh();Count t=0;
  for(Count k=0;k<=cell();++k)t=checkedAdd(t,mesh.cycles().at(k));return checkedMultiply(2,t);
}
Count NormalizedBlockView::sampleIndex() const{need(sample_&&anchor_,"sample index unavailable for cell/moved view");return index_;}
const Eigen::MatrixXd& NormalizedBlockView::A() const{return native().cell_A;}
const Eigen::MatrixXd& NormalizedBlockView::B() const{return native().cell_B;}
const Eigen::VectorXd& NormalizedBlockView::defect() const{return native().cell_defect;}
const NativeState& NormalizedBlockView::nominalOrigin() const{return native().cell_origin;}
const NativeState& NormalizedBlockView::nominalEndpoint() const{return native().state;}
const Eigen::VectorXd& NormalizedBlockView::nominalInput() const{return native().input;}
NormalizedNominalMaps::NormalizedNominalMaps(std::unique_ptr<detail::NormalizedInventory> p):storage_(std::move(p)){}
NormalizedNominalMaps::NormalizedNominalMaps(NormalizedNominalMaps&&) noexcept=default;
NormalizedNominalMaps& NormalizedNominalMaps::operator=(NormalizedNominalMaps&&) noexcept=default;
NormalizedNominalMaps::~NormalizedNominalMaps()=default;
const std::vector<NormalizedBlockView>& NormalizedNominalMaps::cells() const{return present(storage_).cells;}
const std::vector<NormalizedBlockView>& NormalizedNominalMaps::samples() const{return present(storage_).samples;}
Count NormalizedNominalMaps::cycleCount() const{return present(storage_).anchor->forecast.mesh().total();}
const Eigen::MatrixXd& NormalizedNominalMaps::cycleA(Count k) const{return cycle(present(storage_),k).cell_A;}
const Eigen::MatrixXd& NormalizedNominalMaps::cycleB(Count k) const{return cycle(present(storage_),k).cell_B;}
const Eigen::VectorXd& NormalizedNominalMaps::cycleDefect(Count k) const{return cycle(present(storage_),k).cell_defect;}
const NativeState& NormalizedNominalMaps::cycleOrigin(Count k) const{return cycle(present(storage_),k).cell_origin;}
const NativeState& NormalizedNominalMaps::cycleEndpoint(Count k) const{return cycle(present(storage_),k).state;}
Count NormalizedNominalMaps::cycleCell(Count k) const{return static_cast<Count>(cycle(present(storage_),k).cell);}
const OwnedPublicForecast& NormalizedNominalMaps::originalForecast() const{return present(storage_).anchor->forecast;}
CaseBudget& NormalizedNominalMaps::affineBudget() const{return detail::NormalizationFactory::budget(present(storage_).anchor->forecast);}
const ResourcePlan& NormalizedNominalMaps::affinePlan() const{return detail::NormalizationFactory::plan(present(storage_).anchor->forecast);}
const std::array<bool,7>& NormalizedNominalMaps::scopeClaims() noexcept{static const std::array<bool,7> flags{};return flags;}
NormalizationOutcome::NormalizationOutcome(OwnedPublicForecast&& s) noexcept:original_(std::move(s)){}
NormalizationOutcome::NormalizationOutcome(NormalizationOutcome&&) noexcept=default;
NormalizationOutcome& NormalizationOutcome::operator=(NormalizationOutcome&&) noexcept=default;
NormalizationOutcome::~NormalizationOutcome()=default;
bool NormalizationOutcome::hasFullNominalMaps() const noexcept{return !refused_&&static_cast<bool>(maps_)&&(!diagnostics_||!diagnostics_->poisoned);}
const NormalizedNominalMaps& NormalizationOutcome::maps() const{need(hasFullNominalMaps(),"full nominal normalization refused/moved");return *maps_;}
const OwnedPublicForecast& NormalizationOutcome::originalForecast() const{return anchor_?anchor_->forecast:original_;}
std::string_view NormalizationOutcome::refusal() const noexcept{
  if(!refused_&&diagnostics_&&diagnostics_->poisoned)return diagnostics_->capture_error.empty()?std::string_view("NORMALIZATION_CAPTURE_REFUSAL_UNRECORDED_DETAIL"):std::string_view(diagnostics_->capture_error);
  if(!refused_)return {};return refusal_detail_.empty()?std::string_view("NORMALIZATION_REFUSAL_UNRECORDED_DETAIL"):std::string_view(refusal_detail_);
}
Count NormalizationOutcome::retainedDiagnosticSlots() const noexcept{return diagnostics_?scratch_slots:0;}
bool NormalizationOutcome::hasRetainedRegions() const noexcept{return static_cast<bool>(diagnostics_);}
void NormalizationOutcome::withRetainedRegions(const RetainedRegionConsumer& callback) const{
  need(static_cast<bool>(diagnostics_),"normalization diagnostic absent");
  if(!callback||diagnostics_->capture_active){diagnostics_->reject("normalization capture reentry/empty callback");throw std::invalid_argument("normalization capture reentry/empty callback");}
  auto& p=*diagnostics_;struct Guard{bool& flag;Guard(bool& b):flag(b){flag=true;}~Guard(){flag=false;}} guard(p.capture_active);
  const RetainedNumericRegionView view("normalization.current_nominal_subtractions",p.scratch.data(),120,p.trace,p.capture_active);
  try{callback(view);}catch(const std::exception& e){p.reject(e.what());throw;}catch(...){p.reject("NONSTANDARD_NORMALIZATION_CAPTURE_FAILURE");throw;}
}
void NormalizationOutcome::recordRefusal(const char* reason) noexcept{
  maps_.reset();refused_=true;if(diagnostics_)diagnostics_->trace.complete=false;try{refusal_detail_=reason?reason:"NORMALIZATION_REFUSAL";}catch(...){refusal_detail_.clear();}
}
NormalizationOutcome normalizePublic(OwnedPublicForecast&& s){return detail::NormalizationFactory::normalize(std::move(s));}
} // namespace phase5_active_session_v1
