#include "capture_inventory.hpp"
#include <algorithm>
#include <initializer_list>
#include <stdexcept>
namespace phase5_public_live_affine_v2 {
namespace {
void need(bool b,const char* s){if(!b)throw std::invalid_argument(s);}
Count add(Count a,Count b){return checkedAdd(a,b);}Count mul(Count a,Count b){return checkedMultiply(a,b);}
Count sum(std::initializer_list<Count> xs){Count n=0;for(Count x:xs)n=add(n,x);return n;}
Count ceiling(Count n,Count d){need(d>0,"positive integer divisor");return n/d+(n%d!=0);}
}
namespace detail {
struct OriginalCaptureState {
  std::shared_ptr<const void> source_origin,actual_cost_origin;
  OriginalCaptureObservation observation;bool active=false;
  void reject(const char* s) noexcept{if(observation.refused)return;observation.refused=true;try{observation.first_error=s?s:"ORIGINAL_CAPTURE_REFUSAL";}catch(...){}}
};
struct CaptureInventoryStorage {
  CostDecodeOutcome source;std::shared_ptr<OriginalCaptureState> gate;
  std::optional<SharedCaseBudget> budget;std::optional<ResourcePlan> plan;FactorShape shape;
  CaptureFlowEnvelope envelope;Count n=0,t=0,s=0,du=0,dy=0,dx=0;
  bool catalogue_active=false,catalogue_poisoned=false;std::string refusal,first_catalogue_error;
  void reject(const char* why) noexcept{if(catalogue_poisoned)return;catalogue_poisoned=true;try{first_catalogue_error=why?why:"CATALOGUE_REFUSAL";}catch(...){}}
  CaptureInventoryStorage(CostDecodeOutcome&& s,std::shared_ptr<OriginalCaptureState> g):source(std::move(s)),gate(std::move(g)){}
};
struct CaptureInventoryFactory {
  static OriginalCaptureGate prepare(const AffineAssemblyOutcome& source){
    need(source.hasCompleteAssembly(),"genuine complete affine source required for original gate");
    auto state=std::make_shared<OriginalCaptureState>();state->source_origin=source.captureOriginToken();
    need(static_cast<bool>(state->source_origin),"genuine source origin absent");state->observation.expected_terms=source.captureShape().terms;
    return OriginalCaptureGate(std::move(state));
  }
  static void term(OriginalCaptureState& state,const UsedTermView& view,const std::function<void(const UsedTermView&)>& sink){
    try{need(state.observation.issued&&!state.observation.refused&&!state.active,"original callback unissued/refused/reentry");
      need(view.originalConsumerScope()&&view.captureOriginToken()==state.source_origin,"replayed/foreign/nonoriginal term view");
      const auto actual=view.captureCostToken();need(static_cast<bool>(actual),"actual private cost origin absent");
      if(!state.actual_cost_origin)state.actual_cost_origin=actual;need(state.actual_cost_origin==actual,"different owned cost origin");
      need(view.termIndex()==state.observation.terms_observed&&state.observation.terms_observed<state.observation.expected_terms&&!state.observation.canonical_observed,"original term order/replay");
      state.active=true;try{if(sink)sink(view);state.active=false;}catch(...){state.active=false;throw;}
      need(!state.observation.refused,state.observation.first_error.empty()?"nested original capture refusal retained":state.observation.first_error.c_str());++state.observation.terms_observed;
    }catch(const std::exception& e){state.reject(e.what());throw;}catch(...){state.reject("NONSTANDARD_ORIGINAL_TERM_SINK_FAILURE");throw;}
  }
  static void canonical(OriginalCaptureState& state,const CostEvaluationView& view,const std::function<void(const CostEvaluationView&)>& sink){
    try{need(state.observation.issued&&!state.observation.refused&&!state.active,"original canonical unissued/refused/reentry");
      need(view.originalConsumerScope()&&view.captureOriginToken()==state.source_origin,"replayed/foreign/nonoriginal canonical view");
      const auto actual=view.captureCostToken();need(static_cast<bool>(actual),"actual cost origin absent");
      if(!state.actual_cost_origin)state.actual_cost_origin=actual;need(state.actual_cost_origin==actual,"different canonical cost origin");
      need(state.observation.terms_observed==state.observation.expected_terms&&!state.observation.canonical_observed,"missing/replayed original canonical callback");
      state.active=true;try{if(sink)sink(view);state.active=false;}catch(...){state.active=false;throw;}
      need(!state.observation.refused,state.observation.first_error.empty()?"nested original canonical refusal retained":state.observation.first_error.c_str());state.observation.canonical_observed=true;
    }catch(const std::exception& e){state.reject(e.what());throw;}catch(...){state.reject("NONSTANDARD_ORIGINAL_CANONICAL_SINK_FAILURE");throw;}
  }
  static CaptureFlowEnvelope envelope(const ResourcePlan& p,const FactorShape& f,SharedCaseBudget& b,Count t,Count input_bytes){
    CaptureFlowEnvelope e;const Count n=p.du()/8,s=mul(t,2),du=p.du(),dy=p.dy();
    e.raw_shape_slots=p.rawResultShapeSlots();e.sdk_allowance=p.sdkPlanningAllowance();e.normalized_slots=add(mul(n,1241),mul(s,1243));e.normalizer_held=640;
    e.boundary_slots=mul(n+1,sum({30,mul(30,du),900}));e.embedding_slots=add(mul(dy,du),dy);
    e.input_slots=sum({mul(f.rows,dy),f.rows,mul(f.terms,dy),f.terms,f.addition_coefficients,f.addition_coefficients/30,mul(f.addition_records,4)});
    e.factor_work=sum({mul(4,mul(f.largest_term_rows,dy)),mul(4,mul(f.largest_term_rows,du)),mul(4,mul(du,du)),mul(2,mul(dy,du))});
    e.sample_work=sum({mul(4,mul(30,du)),3600,60});e.cost_capture_slots=sum({mul(f.rows,du+1),mul(f.terms,sum({mul(du,du),du,1})),mul(du,du),du,dy,1});
    e.original_cost_reuse=mul(f.terms+1,e.factor_work);e.once_sample_reuse=mul(s,e.sample_work);
    e.input_refill_full_read_nominal=mul(ceiling(input_bytes,128),16);e.input_refill_shortread_worst=mul(input_bytes,16);
    e.planned_existing_source_peak=p.liveCeiling(); // Includes actual requested Dense allowance when present.
    e.current_live=b.liveSlots();e.planned_live=b.liveCeiling();e.current_charges=b.cumulativeCharges();e.planned_charges=b.chargeCeiling();
    const Count minimal_extra=sum({std::max(e.writer_io_slots,e.reader_io_slots),e.retained_axes_per_chunk,e.catalogue_frame_slots});
    e.added_io_fits_now=add(e.current_live,minimal_extra)<=e.planned_live;
    // No certificate is minted from unused theoretical W: it is allocated.
    e.preplanned_workspace_transfer=false;e.full_flow_accepted=false;return e;
  }
  static CaptureInventoryOwner bind(CostDecodeOutcome&& source,OriginalCaptureGate&& original){
    CaptureInventoryOwner out(std::move(source));out.original_gate_=std::move(original.state_);try{
      need(out.original_gate_&&out.original_gate_->source_origin,"original observation gate absent/moved");
      const auto& a=out.original_.originalAssembly();need(a.captureOriginToken()==out.original_gate_->source_origin,"decoded result belongs to different genuine affine origin");
      if(out.original_gate_->actual_cost_origin){
        need(out.original_.costOutcome().captureCostToken()==out.original_gate_->actual_cost_origin,"returned owned cost differs from callback origin");}
      out.storage_=std::make_unique<CaptureInventoryStorage>(std::move(out.original_),out.original_gate_);auto* data=out.storage_.get();
      const auto& affine=data->source.originalAssembly();data->plan=affine.capturePlan();data->shape=affine.captureShape();data->budget=affine.captureBudget();
      const auto& forecast=affine.originalNormalization().originalForecast();data->n=forecast.mesh().cycles().size();data->t=forecast.mesh().total();data->s=mul(data->t,2);
      data->du=data->plan->du();data->dy=data->plan->dy();data->dx=data->plan->dx();
      data->envelope=envelope(*data->plan,data->shape,*data->budget,data->t,data->source.requestedArtifact().bytes);
      // B1 binds owner/requirements, never claims captured bytes/full resource closure.
      data->refusal="FULL_FLOW_REQUIRES_B2_PREPARTITIONED_WORKSPACE_AND_EXACT_BYTE_CLOSURE";
    }catch(const std::exception& e){if(out.original_gate_)out.original_gate_->reject(e.what());out.refused_=true;try{out.reason_=e.what();}catch(...){}}
    catch(...){if(out.original_gate_)out.original_gate_->reject("NONSTANDARD_INVENTORY_BIND_FAILURE");out.refused_=true;try{out.reason_="NONSTANDARD_INVENTORY_BIND_FAILURE";}catch(...){}}return out;
  }
};
}
OriginalCaptureGate::OriginalCaptureGate(std::shared_ptr<detail::OriginalCaptureState> s):state_(std::move(s)){}
OriginalCaptureObservation OriginalCaptureGate::observation() const{need(static_cast<bool>(state_),"moved original capture gate");return state_->observation;}
InitialCostConsumer OriginalCaptureGate::consumer(const std::function<void(const UsedTermView&)>& term_sink,const std::function<void(const CostEvaluationView&)>& canonical_sink){
  need(static_cast<bool>(state_),"moved original gate");
  if(state_->observation.issued||state_->observation.refused){state_->reject("original consumer already issued/refused");throw std::invalid_argument("original consumer already issued/refused");}
  state_->observation.issued=true;try{InitialCostConsumer out;const auto state=state_;const auto term=term_sink;const auto canonical=canonical_sink;
  out.term=[state,term](const UsedTermView& v){detail::CaptureInventoryFactory::term(*state,v,term);};
  out.canonical=[state,canonical](const CostEvaluationView& v){detail::CaptureInventoryFactory::canonical(*state,v,canonical);};
  need(!state_->observation.refused,"original hook issuance refusal retained");return out;
  }catch(const std::exception& e){state_->reject(e.what());throw;}catch(...){state_->reject("NONSTANDARD_ORIGINAL_HOOK_ISSUANCE_FAILURE");throw;}
}
CaptureInventoryOwner::CaptureInventoryOwner(CostDecodeOutcome&& s):original_(std::move(s)){}
CaptureInventoryOwner::CaptureInventoryOwner(CaptureInventoryOwner&&) noexcept=default;
CaptureInventoryOwner& CaptureInventoryOwner::operator=(CaptureInventoryOwner&&) noexcept=default;
CaptureInventoryOwner::~CaptureInventoryOwner()=default;
const CostDecodeOutcome& CaptureInventoryOwner::genuineSource() const{return storage_?storage_->source:original_;}
const CaptureFlowEnvelope& CaptureInventoryOwner::integerEnvelope() const{need(static_cast<bool>(storage_),"inventory source/plan binding refused");return storage_->envelope;}
const OriginalCaptureObservation* CaptureInventoryOwner::captureOriginalObservation() const noexcept{const auto gate=storage_?storage_->gate:original_gate_;return gate?&gate->observation:nullptr;}
bool CaptureInventoryOwner::sourceComponentComplete() const noexcept{return storage_?storage_->source.hasCompleteCost():original_.hasCompleteCost();}
std::string_view CaptureInventoryOwner::admissionRefusal() const noexcept{
  const auto& source=genuineSource();if(!source.hasCompleteCost()&&!source.refusal().empty())return source.refusal();
  if(storage_&&storage_->gate&&storage_->gate->observation.refused)return storage_->gate->observation.first_error.empty()?std::string_view("ORIGINAL_OBSERVER_REFUSAL_UNRECORDED_DETAIL"):std::string_view(storage_->gate->observation.first_error);
  if(storage_&&storage_->catalogue_poisoned)return storage_->first_catalogue_error.empty()?std::string_view("CATALOGUE_REFUSAL_UNRECORDED_DETAIL"):std::string_view(storage_->first_catalogue_error);
  return refused_?(reason_.empty()?std::string_view("INVENTORY_REFUSAL_UNRECORDED_DETAIL"):std::string_view(reason_)):(storage_?std::string_view(storage_->refusal):std::string_view("INVENTORY_NOT_BOUND"));}
void CaptureInventoryOwner::withRequirements(const std::function<void(const RequiredField&)>& visitor) const{
  need(storage_&&storage_->budget&&storage_->plan&&!refused_,"requirements source/plan absent");auto& p=*storage_;
  try{need(visitor&&!p.catalogue_active&&!p.catalogue_poisoned,"catalogue reentry/empty/first refusal retained");
  auto frame=p.budget->reserve(20); // Before one reused role/index/dimension frame.
  struct Guard{bool& active;Guard(bool& b):active(b){active=true;}~Guard(){active=false;}} guard(p.catalogue_active);
  const auto& affine=p.source.originalAssembly();const auto& norm=affine.originalNormalization();const auto& rawowner=norm.originalForecast();const auto* raw=rawowner.originalResult();
  auto emit=[&](RequiredRole role,Count first,Count second,std::initializer_list<Count> dims,FieldAvailability availability,FieldClassification classification,const char* order="row-major",bool shape_known=true){
    p.budget->chargeScratchOrCopy(20);RequiredField f;f.role=role;f.primary=first;f.secondary=second;need(dims.size()<=4,"required field rank bound");f.rank=dims.size();Count k=0;for(Count d:dims)f.dimensions[k++]=d;
    f.availability=availability;f.classification=classification;f.traversal=order;f.shape_known=shape_known;
    switch(role){
      case RequiredRole::RawMapIndices:case RequiredRole::RawFrictionBranches:case RequiredRole::RawFrictionIterations:case RequiredRole::RawClips:case RequiredRole::ChosenInitialKind:f.scalar_kind=RequiredScalarKind::I64;break;
      case RequiredRole::CostAdditionRows:case RequiredRole::CostAdditionSampleIndex:f.scalar_kind=RequiredScalarKind::U64;break;
      case RequiredRole::ProvenanceAndMetadata:case RequiredRole::InvocationAndExecution:case RequiredRole::RawFlagsAndErrors:case RequiredRole::CostNamesAndUnits:case RequiredRole::CostTopologyClosure:case RequiredRole::DecoderFrontiers:f.scalar_kind=RequiredScalarKind::Metadata;break;
      case RequiredRole::NormalizedSourceReference:case RequiredRole::StructuredInitialSelector:case RequiredRole::SampleCompositionRecipe:case RequiredRole::CanonicalOrderedConcatenation:f.scalar_kind=RequiredScalarKind::SourceReference;break;
      case RequiredRole::RawCellControl:case RequiredRole::FailureDefinedRegions:f.scalar_kind=RequiredScalarKind::Composite;break;
      default:f.scalar_kind=RequiredScalarKind::F64;
    }visitor(f);need(!p.catalogue_poisoned,"nested catalogue refusal retained");
  };
  using R=RequiredRole;using A=FieldAvailability;using C=FieldClassification;
  emit(R::ProvenanceAndMetadata,0,0,{},A::OwnedSourceReference,C::SourceMetadata);
  emit(R::InvocationAndExecution,0,0,{},A::PendingLeafBinding,C::SourceMetadata);
  emit(R::RawFlagsAndErrors,0,0,{},A::OwnedSourceReference,C::SourceMetadata);
  emit(R::RawFinalState,0,0,{30},raw&&raw->value.has_final_state?A::OwnedSourceReference:A::AbsentUpstream,C::DefinedForensic);
  for(Count k=0;k<p.n;++k){emit(R::RawCellControl,k,0,{9},A::OwnedSourceReference,C::FiniteComponent);emit(R::RawCellState,k,0,{30},raw&&k<raw->value.cell_end_states.size()?A::OwnedSourceReference:A::AbsentUpstream,C::DefinedForensic);}
  for(Count k=0;k<p.t;++k)emit(R::RawCycleState,k,0,{30},raw&&k<raw->value.cycle_end_states.size()?A::OwnedSourceReference:A::AbsentUpstream,C::DefinedForensic);
  for(Count k=0;k<p.s;++k){const auto available=raw&&k<raw->value.substeps.size()?A::OwnedSourceReference:A::AbsentUpstream;
    emit(R::RawSubstepPhysical,k,0,{28},available,C::DefinedForensic);emit(R::RawSubstepProgress,k,0,{3},available,C::DefinedForensic);
    emit(R::RawFrictionForce,k,0,{7},available,C::DefinedForensic);emit(R::RawFrictionBranches,k,0,{7},available,C::DefinedForensic);
    emit(R::RawFrictionIterations,k,0,{1},available,C::DefinedForensic);emit(R::RawFrictionKkt,k,0,{1},available,C::DefinedForensic);emit(R::RawClips,k,0,{2},available,C::DefinedForensic);}
  for(Count group=0;group<3;++group){const Count n=group==0?p.s:group==1?p.t:p.n;const Count actual=!raw?0:group==0?raw->substep_maps.size():group==1?raw->cycle_maps.size():raw->cell_maps.size();
    for(Count k=0;k<n;++k){const auto a=k<actual?A::OwnedSourceReference:A::AbsentUpstream;
      for(R r:{R::RawMapLocalA,R::RawMapCellA})emit(r,group,k,{30,30},a,C::DefinedForensic);
      for(R r:{R::RawMapLocalB,R::RawMapCellB})emit(r,group,k,{30,8},a,C::DefinedForensic);
      for(R r:{R::RawMapLocalDefect,R::RawMapCellDefect,R::RawMapOrigin,R::RawMapCellOrigin,R::RawMapEndpoint})emit(r,group,k,{30},a,C::DefinedForensic);
      emit(R::RawMapInput,group,k,{8},a,C::DefinedForensic);emit(R::RawMapIndices,group,k,{3},a,C::SourceMetadata);}}
  emit(R::NormalizedSourceReference,0,0,{},norm.hasFullNominalMaps()?A::OwnedSourceReference:A::ForensicSourceOnly,C::Recipe);
  for(Count k=0;k<=p.n;++k){const auto a=affine.hasCompleteAssembly()?A::OwnedSourceReference:A::ForensicSourceOnly;
    emit(R::BoundaryOffset,k,0,{30},a,C::FiniteComponent);emit(R::BoundaryControl,k,0,{30,p.du},a,C::FiniteComponent);emit(R::BoundaryInitial,k,0,{30,30},a,C::FiniteComponent);}
  const auto affine_available=affine.hasCompleteAssembly()?A::OwnedSourceReference:A::ForensicSourceOnly;
  emit(R::EmbeddingControl,0,0,{p.dy,p.du},affine_available,C::FiniteComponent);emit(R::EmbeddingOffset,0,0,{p.dy},affine_available,C::FiniteComponent);
  emit(R::StructuredInitialSelector,0,0,{p.dy,30},A::RecipeNotEvaluated,C::Recipe);emit(R::ChosenInitial,0,0,{30},affine_available,C::FiniteComponent);emit(R::ChosenInitialKind,0,0,{1},A::OwnedSourceReference,C::SourceMetadata);
  for(Count k=0;k<p.s;++k){emit(R::SampleCompositionRecipe,k,0,{},A::RecipeNotEvaluated,C::Recipe);
    emit(R::SampleEvaluatedOffset,k,0,{30},A::PendingLeafBinding,C::FiniteComponent);emit(R::SampleEvaluatedActualOffset,k,0,{30},A::PendingLeafBinding,C::FiniteComponent);
    emit(R::SampleEvaluatedControl,k,0,{30,p.du},A::PendingLeafBinding,C::FiniteComponent);emit(R::SampleEvaluatedInitial,k,0,{30,30},A::PendingLeafBinding,C::FiniteComponent);}
  const bool original_ok=p.gate&&!p.gate->observation.refused&&p.gate->observation.terms_observed==p.shape.terms&&p.gate->observation.canonical_observed;
  const auto original=original_ok?A::OriginalObservedNotStored:A::PendingLeafBinding;
  const CostInputRecipe* input=nullptr;try{input=&p.source.costOutcome().originalInputRecipe();}catch(const std::exception&){} // Missing authoritative snapshot remains pending.
  const std::vector<CostTermLayout>* prefix=nullptr;Count complete_prefix_terms=0;
  try{prefix=&p.source.parsedMetadataPrefix();complete_prefix_terms=p.source.observation().parsed_terms;}catch(const std::exception&){}
  emit(R::CostTopologyClosure,0,0,{},input?A::OwnedSourceReference:A::ForensicSourceOnly,C::SourceMetadata);
  const auto cost_available=p.source.hasCompleteCost()?A::OwnedSourceReference:A::ForensicSourceOnly;
  emit(R::EvaluationControl,0,0,{p.du},cost_available,C::FiniteComponent);
  for(Count k=0;k<p.shape.terms;++k){
    const CostTermLayout* descriptor=input&&k<input->terms.size()?&input->terms[k]:prefix&&k<complete_prefix_terms&&k<prefix->size()?&(*prefix)[k]:nullptr;
    const bool known=descriptor!=nullptr;const Count rows=known?descriptor->rows:0;
    emit(R::CostNamesAndUnits,k,0,{},input?A::OwnedSourceReference:known?A::ForensicSourceOnly:A::PendingLeafBinding,C::SourceMetadata);
    for(R r:{R::CostInputFactor,R::OriginalUsedFactor})emit(r,k,0,{rows,p.dy},r==R::OriginalUsedFactor?original:cost_available,C::FiniteComponent,"row-major",known);
    for(R r:{R::CostInputOffset,R::OriginalUsedOffset})emit(r,k,0,{rows},r==R::OriginalUsedOffset?original:cost_available,C::FiniteComponent,"row-major",known);
    for(R r:{R::CostInputLinear,R::OriginalUsedLinear})emit(r,k,0,{p.dy},r==R::OriginalUsedLinear?original:cost_available,C::FiniteComponent);
    for(R r:{R::CostInputConstant,R::OriginalUsedConstant})emit(r,k,0,{1},r==R::OriginalUsedConstant?original:cost_available,C::FiniteComponent);
    if(descriptor)for(Count j=0;j<descriptor->additions.size();++j){const Count n=descriptor->additions[j].parent_rows.size();emit(R::CostAdditionCoefficients,k,j,{n,30},input?A::OwnedSourceReference:A::ForensicSourceOnly,C::FiniteComponent);emit(R::CostAdditionRows,k,j,{n},input?A::OwnedSourceReference:A::ForensicSourceOnly,C::SourceMetadata);emit(R::CostAdditionSampleIndex,k,j,{1},input?A::OwnedSourceReference:A::ForensicSourceOnly,C::SourceMetadata);}
    emit(R::TermCondensedFactor,k,0,{rows,p.du},cost_available,C::FiniteComponent,"row-major",known);emit(R::TermCondensedOffset,k,0,{rows},cost_available,C::FiniteComponent,"row-major",known);
    emit(R::TermRawH,k,0,{p.du,p.du},cost_available,C::FiniteComponent);emit(R::TermGradientCoefficient,k,0,{p.du},cost_available,C::FiniteComponent);emit(R::TermConstantCoefficient,k,0,{1},cost_available,C::FiniteComponent);
    for(R r:{R::OriginalDirectValue,R::OriginalCondensedValue})emit(r,k,0,{1},original,C::FiniteComponent);
    for(R r:{R::OriginalDirectGradient,R::OriginalCondensedGradient})emit(r,k,0,{p.du},original,C::FiniteComponent);
    for(R r:{R::OriginalDirectHessian,R::OriginalCondensedHessian})emit(r,k,0,{p.du,p.du},original,C::FiniteComponent);}
  emit(R::CanonicalOrderedConcatenation,p.shape.terms,0,{p.shape.rows,p.dy},A::PendingLeafBinding,C::Recipe,"ordered-usedF-row-ranges");
  emit(R::CanonicalOrderedConcatenation,p.shape.terms,1,{p.shape.rows},A::PendingLeafBinding,C::Recipe,"ordered-usedf0-row-ranges");
  emit(R::CanonicalOrderedConcatenation,p.shape.terms,2,{p.shape.rows,p.du},A::PendingLeafBinding,C::Recipe,"ordered-Fc-row-ranges");
  emit(R::CanonicalOrderedConcatenation,p.shape.terms,3,{p.shape.rows},A::PendingLeafBinding,C::Recipe,"ordered-fc-row-ranges");
  emit(R::CanonicalRawH,0,0,{p.du,p.du},cost_available,C::FiniteComponent);emit(R::CanonicalGradientCoefficient,0,0,{p.du},cost_available,C::FiniteComponent);emit(R::CanonicalLinear,0,0,{p.dy},cost_available,C::FiniteComponent);
  for(R r:{R::CanonicalInputConstant,R::CanonicalCondensedConstant})emit(r,0,0,{1},cost_available,C::FiniteComponent);
  for(R r:{R::OriginalDirectValue,R::OriginalCondensedValue})emit(r,p.shape.terms,0,{1},original,C::FiniteComponent);
  for(R r:{R::OriginalDirectGradient,R::OriginalCondensedGradient})emit(r,p.shape.terms,0,{p.du},original,C::FiniteComponent);
  for(R r:{R::OriginalDirectHessian,R::OriginalCondensedHessian})emit(r,p.shape.terms,0,{p.du,p.du},original,C::FiniteComponent);
  if(p.plan->captureMode()==CaptureMode::DenseAuditComplete){const auto a=affine.hasCompleteAssembly()?A::OwnedSourceReference:A::ForensicSourceOnly;
    emit(R::DenseLiftedL,0,0,{p.dx,p.dx},a,C::DefinedForensic);emit(R::DenseLiftedE,0,0,{p.dx,p.du},a,C::DefinedForensic);emit(R::DenseLiftedOffset,0,0,{p.dx},a,C::DefinedForensic);emit(R::DenseInitialSelector,0,0,{p.dx,30},a,C::DefinedForensic);
    emit(R::DenseActiveLU,0,0,{p.dx,p.dx},a,C::DefinedForensic);emit(R::DenseActiveRhs,0,0,{p.dx,p.du+31},a,C::DefinedForensic);emit(R::DenseSolution,0,0,{p.dx,p.du+31},a,C::DefinedForensic);
    for(Count k=0;k<p.s;++k){emit(R::DenseSampleSelector,k,0,{30,p.dy},a,C::DefinedForensic);for(Count method=0;method<2;++method){emit(R::DenseSampleOffset,k,method,{30},a,C::DefinedForensic);emit(R::DenseSampleControl,k,method,{30,p.du},a,C::DefinedForensic);emit(R::DenseSampleInitial,k,method,{30,30},a,C::DefinedForensic);}}}
  emit(R::FailureDefinedRegions,0,0,{},A::ForensicSourceOnly,C::DefinedForensic);emit(R::DecoderFrontiers,0,0,{},A::OwnedSourceReference,C::SourceMetadata);
  }catch(const std::exception& e){p.reject(e.what());throw;}catch(...){p.reject("NONSTANDARD_CATALOGUE_VISITOR_FAILURE");throw;}
}
OriginalCaptureGate prepareOriginalCaptureGate(const AffineAssemblyOutcome& source){return detail::CaptureInventoryFactory::prepare(source);}
CaptureInventoryOwner bindCaptureInventory(CostDecodeOutcome&& source,OriginalCaptureGate&& gate){return detail::CaptureInventoryFactory::bind(std::move(source),std::move(gate));}
}
