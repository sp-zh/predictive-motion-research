#include "capture_leaves.hpp"
#include "../capture_workspace/partition_internal.hpp"
#include <algorithm>
#include <initializer_list>
#include <stdexcept>
namespace phase5_public_live_affine_v2 {
namespace {
void need(bool x,const char* s){if(!x)throw std::invalid_argument(s);}
Count add(Count a,Count b){return checkedAdd(a,b);}Count mul(Count a,Count b){return checkedMultiply(a,b);}
Count size(Eigen::Index i){need(i>=0,"negative native leaf size");return static_cast<Count>(i);}
using R=RequiredRole;
Count packedCount(const phase5_public_coupled_augmented::State& s){return add(add(add(size(s.q.size()),size(s.v.size())),add(size(s.C.size()),size(s.w.size()))),2);}
double packed(const phase5_public_coupled_augmented::State& s,Count i){for(const auto* v:{&s.q,&s.v,&s.C,&s.w}){const Count n=size(v->size());if(i<n)return (*v)(static_cast<Eigen::Index>(i));i-=n;}need(i<2,"state leaf coordinate");return i==0?s.s:s.r;}
}
namespace detail {
struct CaptureLeafState {
  std::shared_ptr<const void> source_origin,actual_cost_origin;std::shared_ptr<CapturePartitionState> partition;
  SharedCaseBudget budget;std::optional<OriginalCaptureGate> gate;std::optional<CaptureInventoryOwner> owner;
  const UsedTermView* term=nullptr;const CostEvaluationView* canonical=nullptr;const AffineAssemblyOutcome* original_source=nullptr;
  CaptureLeafObservation status;ForensicBorrowObservation forensic;bool forensic_active=false;bool original_active=false,leaf_active=false;Count generation=0,metadata_payload=0;
  std::vector<BoundLeafAttempt> attempts;
  CaptureLeafState(std::shared_ptr<const void> origin,std::shared_ptr<CapturePartitionState> p,SharedCaseBudget b)
    :source_origin(std::move(origin)),partition(std::move(p)),budget(std::move(b)){}
  void reject(const char* why) noexcept{if(status.refused)return;status.refused=true;try{status.first_error=why?why:"LEAF_CAPTURE_REFUSAL";}catch(...){}}
  void rejectForensic(const char* why) noexcept{if(forensic.refused)return;forensic.refused=true;try{forensic.first_error=why?why:"FORENSIC_BORROW_REFUSAL";}catch(...){}}
  void forensicHealthy() const{need(!forensic.refused,forensic.first_error.empty()?"forensic first refusal retained":forensic.first_error.c_str());}
  void healthy() const{need(!status.refused,status.first_error.empty()?"leaf first refusal retained":status.first_error.c_str());need(!status.closed,"leaf capture closed");}
};
struct LeafBinding {
  std::shared_ptr<CaptureLeafState> owner;NumericLeafInfo info;
  ChunkScalarSource read;Count generation=0;const MathCaptureTrace* frontier=nullptr;bool forensic_only=false;
};
struct CaptureLeafFactory {
  static CaptureLeafSession prepare(const AffineAssemblyOutcome& source,const CaptureWorkspaceGrant& grant){
    need(source.hasCompleteAssembly()&&grant.state_&&grant.readyForOneAdmission(),"genuine live source/ready private partition required");
    need(source.captureOriginToken()==grant.state_->source_origin&&source.captureBudget().sameCase(grant.state_->budget),"leaf session foreign source/case");
    auto state=std::make_shared<CaptureLeafState>(source.captureOriginToken(),grant.state_,source.captureBudget());
    state->gate.emplace(prepareOriginalCaptureGate(source));return CaptureLeafSession(std::move(state));
  }
  static NumericLeafInfo info(R role,Count first,Count second,std::initializer_list<Count> shape,bool forensic=false){
    NumericLeafInfo out;out.role=role;out.primary=first;out.secondary=second;out.rank=shape.size();need(out.rank<=4,"leaf rank cap");Count n=1,k=0;for(Count d:shape){out.dimensions[k++]=d;n=mul(n,d);}
    out.count=out.defined_count=n;out.kind=forensic?ChunkScalarKind::FailureF64Bits:ChunkScalarKind::F64;out.classification=forensic?ChunkClassification::ForensicDefinedFields:ChunkClassification::FiniteFields;
    out.state=forensic?DefinedComputedState::AssignedUnvalidated:DefinedComputedState::ComputedOriginal;return out;
  }
  static ChunkScalar floating(double x,bool forensic){const auto s=ChunkScalar::f64(x);return forensic?ChunkScalar::failureF64Bits(s.bits):s;}
  static void visit(std::shared_ptr<CaptureLeafState> p,NumericLeafInfo metadata,ChunkScalarSource getter,const NumericLeafConsumer& consumer,const MathCaptureTrace* frontier=nullptr,bool forensic_only=false){
    try{if(forensic_only){p->forensicHealthy();need(p->forensic_active,"forensic scope absent");}else p->healthy();need(!p->leaf_active&&consumer,"leaf reentry/empty consumer");
      p->leaf_active=true;const Count generation=++p->generation;LeafBinding binding{p,metadata,std::move(getter),generation,frontier,forensic_only};const NumericLeafView view(&binding);
      try{consumer(view);p->leaf_active=false;}catch(...){p->leaf_active=false;throw;}if(forensic_only)p->forensicHealthy();else p->healthy();
    }catch(const std::exception& e){if(forensic_only)p->rejectForensic(e.what());else p->reject(e.what());throw;}catch(...){if(forensic_only)p->rejectForensic("NONSTANDARD_FORENSIC_LEAF_FAILURE");else p->reject("NONSTANDARD_LEAF_BORROW_FAILURE");throw;}
  }
  static const AffineAssemblyOutcome& source(CaptureLeafState& p){if(p.original_active){need(p.original_source,"original source unavailable");return *p.original_source;}need(p.owner&&p.status.attached,"returned genuine owner not attached");return p.owner->genuineSource().originalAssembly();}
  static void applied(CaptureLeafState& p){
    p.healthy();need(p.partition&&p.partition->status.applied&&!p.partition->status.refused&&p.partition->source_origin==p.source_origin&&p.budget.sameCase(p.partition->budget),"actual same-source live partition not applicable");
    const auto& a=source(p);need(a.captureOriginToken()==p.source_origin&&a.hasCompleteAssembly(),"genuine affine source no longer live/valid");
    if(p.original_active){need(p.actual_cost_origin&&(p.term||p.canonical),"original cost owner absent");}
    else {need(p.owner->genuineSource().hasCompleteCost()&&p.owner->genuineSource().capture_partition_==p.partition,"live cost owner/partition mismatch");}
  }
  static void exportBound(std::shared_ptr<CaptureLeafState> p,const NumericLeafView& leaf,const std::string& root,const std::string& name){
    try{need(!leaf.binding_->forensic_only,"readonly forensic leaf cannot export");applied(*p);need(p->status.receipt_attempts<p->partition->status.receipt_limit,"private receipt limit before file creation");
      need(root.size()<=4096&&name.size()<=128,"bounded leaf export metadata");
      p->metadata_payload=add(p->metadata_payload,add(add(root.size(),name.size()),256));need(p->metadata_payload<=ResourcePolicyV2::metadata_bytes,"retained receipt metadata payload cap");
      BoundLeafAttempt pending;pending.source_origin_=p->source_origin;pending.cost_origin_=p->actual_cost_origin;pending.partition_=p->partition;
      pending.role_=leaf.info().role;pending.primary_=leaf.info().primary;pending.secondary_=leaf.info().secondary;
      pending.original_scope_=p->original_active;pending.canonical_scope_=p->canonical!=nullptr;
      // Persist ONE actual shape snapshot/ticket even if low-level admission fails.
      pending.write_.record.axes_owner_=std::make_shared<OwnedReservation>(p->budget.reserve(4));
      auto& spec=pending.write_.record.spec;spec.relative_name=name;p->budget.chargeScratchOrCopy(12);
      spec.role="leaf-r"+std::to_string(static_cast<Count>(leaf.info().role))+"-p"+std::to_string(leaf.info().primary)+"-s"+std::to_string(leaf.info().secondary);
      spec.kind=leaf.info().kind;spec.classification=leaf.info().classification;
      spec.dimensions.assign(leaf.info().dimensions.begin(),leaf.info().dimensions.begin()+leaf.info().rank);
      pending.write_.record.count=leaf.info().count;pending.write_.record.root_path=root;pending.write_.record.encoding=p->budget.numericEncoding();
      p->attempts.push_back(std::move(pending));const auto slot=p->attempts.size()-1;++p->status.receipt_attempts;auto& attempt=p->attempts[slot];
      auto written=writeProvisionalNumericChunk(p->budget,root,attempt.write_.record.spec,[&leaf](Count i){return leaf.scalar(i);});
      if(written.record.axes_owner_)attempt.write_=std::move(written); // Existing expected shape dies before its old ticket.
      else {attempt.write_.observation=std::move(written.observation);attempt.write_.record.bytes=written.record.bytes;attempt.write_.record.sha256=std::move(written.record.sha256);}
      need(attempt.write_.closedChunk(),attempt.write_.observation.first_error.empty()?"leaf write refused":attempt.write_.observation.first_error.c_str());
      attempt.readback_.emplace(readbackNumericChunk(p->budget,root,attempt.write_.record,[&](Count i,const ChunkScalar& actual){
        attempt.comparison_attempted_=true;attempt.mismatch_index_=i;attempt.actual_=actual;attempt.expected_valid_=false;
        const auto expected=leaf.scalar(i);attempt.expected_=expected;attempt.expected_valid_=true;if(expected.kind!=actual.kind||expected.bits!=actual.bits){attempt.mismatch_=true;attempt.mismatch_index_=i;attempt.expected_=expected;attempt.actual_=actual;
          throw std::invalid_argument("actual numeric leaf semantic bit mismatch");}}));
      const auto& check=*attempt.readback_;need(check.exact_readback&&!check.observation.refused,check.observation.first_error.empty()?"leaf readback refused":check.observation.first_error.c_str());++p->status.verified_chunks;
    }catch(const std::exception& e){p->reject(e.what());throw;}catch(...){p->reject("NONSTANDARD_BOUND_LEAF_EXPORT_FAILURE");throw;}
  }
  static void originalEnter(std::shared_ptr<CaptureLeafState> p,const UsedTermView* term,const CostEvaluationView* canonical,const std::function<void(const OriginalLeafBatch&)>& sink){
    try{p->healthy();need(!p->original_active&&!p->leaf_active,"original leaf reentry");
      const auto origin=term?term->captureOriginToken():canonical->captureOriginToken();const auto cost=term?term->captureCostToken():canonical->captureCostToken();
      const auto partition=term?term->capturePartition():canonical->capturePartition();need(origin==p->source_origin&&partition==p->partition,"original leaf source/partition mismatch");
      need(term?term->originalConsumerScope():canonical->originalConsumerScope(),"later numerical replay cannot become original leaf");
      if(!p->actual_cost_origin)p->actual_cost_origin=cost;need(p->actual_cost_origin==cost,"original leaf different owned cost");
      p->original_source=term?&term->captureSource():&canonical->captureSource();p->term=term;p->canonical=canonical;p->original_active=true;
      try{applied(*p);const OriginalLeafBatch batch(p);if(sink)sink(batch);p->original_active=false;p->term=nullptr;p->canonical=nullptr;p->original_source=nullptr;}
      catch(...){p->original_active=false;p->term=nullptr;p->canonical=nullptr;p->original_source=nullptr;throw;}p->healthy();
    }catch(const std::exception& e){p->reject(e.what());throw;}catch(...){p->reject("NONSTANDARD_ORIGINAL_LEAF_FAILURE");throw;}
  }
  static void originalLeaf(std::shared_ptr<CaptureLeafState> p,R role,const NumericLeafConsumer& consumer){
    try{p->healthy();need(p->original_active&&(p->term||p->canonical),"original leaf outside producer callback");
    auto frame=p->budget.reserve(20);p->budget.chargeScratchOrCopy(20);const auto& a=source(*p).assembly();const Count du=a.du(),dy=a.dy();const Count k=p->term?p->term->termIndex():p->gate->observation().expected_terms;
    const auto* term=p->term;const auto* evaluation=term?&term->evaluation():p->canonical;NumericLeafInfo meta;ChunkScalarSource read;
    if(term){const Count rows=term->rows();switch(role){
      case R::OriginalUsedFactor:meta=info(role,k,0,{rows,dy});read=[term,dy](Count i){return ChunkScalar::f64(term->usedFactor(i/dy,i%dy));};break;
      case R::OriginalUsedOffset:meta=info(role,k,0,{rows});read=[term](Count i){return ChunkScalar::f64(term->usedOffset(i));};break;
      case R::OriginalUsedLinear:meta=info(role,k,0,{dy});read=[term](Count i){return ChunkScalar::f64(term->usedLinear(i));};break;
      case R::OriginalUsedConstant:meta=info(role,k,0,{1});read=[term](Count){return ChunkScalar::f64(term->usedConstant());};break;
      case R::TermCondensedFactor:meta=info(role,k,0,{rows,du});read=[term,du](Count i){return ChunkScalar::f64(term->factorControl(i/du,i%du));};break;
      case R::TermCondensedOffset:meta=info(role,k,0,{rows});read=[term](Count i){return ChunkScalar::f64(term->factorOffset(i));};break;
      case R::TermRawH:meta=info(role,k,0,{du,du});read=[term,du](Count i){return ChunkScalar::f64(term->rawH(i/du,i%du));};break;
      case R::TermGradientCoefficient:meta=info(role,k,0,{du});read=[term](Count i){return ChunkScalar::f64(term->gradientCoefficient(i));};break;
      case R::TermConstantCoefficient:meta=info(role,k,0,{1});read=[term](Count){return ChunkScalar::f64(term->constantCoefficient());};break;
      default:break;}}
    if(!read)switch(role){
      case R::OriginalDirectValue:meta=info(role,k,0,{1});read=[evaluation](Count){return ChunkScalar::f64(evaluation->directValue());};break;
      case R::OriginalCondensedValue:meta=info(role,k,0,{1});read=[evaluation](Count){return ChunkScalar::f64(evaluation->condensedValue());};break;
      case R::OriginalDirectGradient:meta=info(role,k,0,{du});read=[evaluation](Count i){return ChunkScalar::f64(evaluation->directGradient(i));};break;
      case R::OriginalCondensedGradient:meta=info(role,k,0,{du});read=[evaluation](Count i){return ChunkScalar::f64(evaluation->condensedGradient(i));};break;
      case R::OriginalDirectHessian:meta=info(role,k,0,{du,du});read=[evaluation,du](Count i){return ChunkScalar::f64(evaluation->directHessian(i/du,i%du));};break;
      case R::OriginalCondensedHessian:meta=info(role,k,0,{du,du});read=[evaluation,du](Count i){return ChunkScalar::f64(evaluation->condensedHessian(i/du,i%du));};break;
      default:throw std::invalid_argument("original numeric leaf role not supported in this phase");}
    visit(p,meta,std::move(read),consumer);
    }catch(const std::exception& e){p->reject(e.what());throw;}catch(...){p->reject("NONSTANDARD_ORIGINAL_LEAF_BIND_FAILURE");throw;}
  }
  static void stored(std::shared_ptr<CaptureLeafState> p,R role,Count first,Count second,const NumericLeafConsumer& consumer){
    try{p->healthy();need(p->owner&&p->status.attached&&!p->original_active&&!p->leaf_active,"stored leaf owner absent/reentry/original phase");
      switch(role){
        case R::RawFinalState:case R::EmbeddingControl:case R::EmbeddingOffset:case R::ChosenInitial:case R::ChosenInitialKind:case R::EvaluationControl:
        case R::CanonicalRawH:case R::CanonicalGradientCoefficient:case R::CanonicalLinear:case R::CanonicalInputConstant:case R::CanonicalCondensedConstant:
          need(first==0&&second==0,"global actual leaf key must be0/0");break;
        case R::RawCellState:case R::RawCycleState:case R::RawSubstepPhysical:case R::RawSubstepProgress:case R::RawFrictionForce:case R::RawFrictionBranches:
        case R::RawFrictionIterations:case R::RawFrictionKkt:case R::RawClips:case R::BoundaryOffset:case R::BoundaryControl:case R::BoundaryInitial:
        case R::CostInputFactor:case R::CostInputOffset:case R::CostInputLinear:case R::CostInputConstant:case R::TermCondensedFactor:case R::TermCondensedOffset:
        case R::TermRawH:case R::TermGradientCoefficient:case R::TermConstantCoefficient:need(second==0,"indexed actual leaf secondary must be0");break;
        case R::RawCellControl:need(second<2,"control leaf split0/1");break;
        case R::RawMapLocalA:case R::RawMapLocalB:case R::RawMapLocalDefect:case R::RawMapCellA:case R::RawMapCellB:case R::RawMapCellDefect:
        case R::RawMapOrigin:case R::RawMapCellOrigin:case R::RawMapEndpoint:case R::RawMapInput:case R::RawMapIndices:need(first<3,"actual native map group0/1/2");break;
        case R::CostAdditionCoefficients:case R::CostAdditionRows:case R::CostAdditionSampleIndex:break;
        default:throw std::invalid_argument("required role not bound in B2B1");}
      auto frame=p->budget.reserve(20);p->budget.chargeScratchOrCopy(20);
      const auto& decoded=p->owner->genuineSource();const auto& a=decoded.originalAssembly();need(a.captureOriginToken()==p->source_origin,"stored leaf source origin changed");
      const auto& norm=a.originalNormalization();const auto& forecast=norm.originalForecast();const auto* raw=forecast.originalResult();
      const bool forensic=!norm.hasFullNominalMaps();NumericLeafInfo meta;ChunkScalarSource read;
      const Eigen::MatrixXd* matrix=nullptr;const Eigen::VectorXd* vector=nullptr;const phase5_public_coupled_augmented::State* state=nullptr;
      const phase5_public_coupled_augmented_extension::Map* map=nullptr;
      if(role>=R::RawMapLocalA&&role<=R::RawMapIndices){need(raw&&first<3,"raw map group absent");const auto& maps=first==0?raw->substep_maps:first==1?raw->cycle_maps:raw->cell_maps;need(second<maps.size(),"raw map index");map=&maps[second];
        switch(role){case R::RawMapLocalA:matrix=&map->A;break;case R::RawMapLocalB:matrix=&map->B;break;case R::RawMapCellA:matrix=&map->cell_A;break;case R::RawMapCellB:matrix=&map->cell_B;break;
          case R::RawMapLocalDefect:vector=&map->defect;break;case R::RawMapCellDefect:vector=&map->cell_defect;break;case R::RawMapInput:vector=&map->input;break;
          case R::RawMapOrigin:state=&map->origin;break;case R::RawMapCellOrigin:state=&map->cell_origin;break;case R::RawMapEndpoint:state=&map->state;break;
          case R::RawMapIndices:meta=info(role,first,second,{3},forensic);meta.kind=ChunkScalarKind::I64;read=[map](Count i){return ChunkScalar::i64(i==0?map->cell:i==1?map->cycle:map->half);};break;default:break;}}
      if(role==R::RawFinalState){need(raw&&raw->value.has_final_state,"actual final state absent");state=&raw->value.final_state;}
      if(role==R::RawCellState||role==R::RawCycleState){need(raw,"raw state absent");const auto& states=role==R::RawCellState?raw->value.cell_end_states:raw->value.cycle_end_states;need(first<states.size(),"raw state index");state=&states[first];}
      if(matrix){const Count rows=size(matrix->rows()),cols=size(matrix->cols());meta=info(role,first,second,{rows,cols},forensic);read=[matrix,cols,forensic](Count i){return floating((*matrix)(static_cast<Eigen::Index>(i/cols),static_cast<Eigen::Index>(i%cols)),forensic);};}
      if(vector){meta=info(role,first,second,{size(vector->size())},forensic);read=[vector,forensic](Count i){return floating((*vector)(static_cast<Eigen::Index>(i)),forensic);};}
      if(state){meta=info(role,first,second,{packedCount(*state)},forensic);meta.traversal="actual-q/v/C/w-lengths-then-s/r";read=[state,forensic](Count i){return floating(packed(*state,i),forensic);};}
      if(role==R::RawCellControl){const auto& cells=forecast.nativeCells();need(first<cells.size()&&second<2,"raw control leaf index");const auto* cell=&cells[first];
        if(second==0){meta=info(role,first,second,{add(size(cell->alpha.size()),1)},forensic);read=[cell,forensic](Count i){return floating(i<size(cell->alpha.size())?cell->alpha(static_cast<Eigen::Index>(i)):cell->b,forensic);};}
        else {meta=info(role,first,second,{1},forensic);meta.kind=ChunkScalarKind::I64;read=[cell](Count){return ChunkScalar::i64(cell->cycles);};}}
      if(role>=R::RawSubstepPhysical&&role<=R::RawClips){need(raw&&first<raw->value.substeps.size(),"raw substep index");const auto* step=&raw->value.substeps[first];
        switch(role){case R::RawSubstepPhysical:{const Count n=add(add(size(step->q.size()),size(step->v.size())),add(size(step->C.size()),size(step->w.size())));meta=info(role,first,second,{n},forensic);meta.traversal="actual-q/v/C/w-lengths";read=[step,forensic](Count i){for(const auto* v:{&step->q,&step->v,&step->C,&step->w}){const Count n=size(v->size());if(i<n)return floating((*v)(static_cast<Eigen::Index>(i)),forensic);i-=n;}throw std::invalid_argument("physical packed leaf index");};break;}
          case R::RawSubstepProgress:meta=info(role,first,second,{3},forensic);read=[step,forensic](Count i){return floating(i==0?step->elapsed_s:i==1?step->s_reference:step->r_reference,forensic);};break;
          case R::RawFrictionForce:meta=info(role,first,second,{size(step->friction.force.size())},forensic);read=[step,forensic](Count i){return floating(step->friction.force(static_cast<Eigen::Index>(i)),forensic);};break;
          case R::RawFrictionBranches:meta=info(role,first,second,{step->friction.branches.size()},forensic);meta.kind=ChunkScalarKind::I64;read=[step](Count i){return ChunkScalar::i64(step->friction.branches.at(i));};break;
          case R::RawFrictionIterations:meta=info(role,first,second,{1},forensic);meta.kind=ChunkScalarKind::I64;read=[step](Count){return ChunkScalar::i64(step->friction.iterations);};break;
          case R::RawFrictionKkt:meta=info(role,first,second,{1},forensic);read=[step,forensic](Count){return floating(step->friction.original_kkt,forensic);};break;
          case R::RawClips:meta=info(role,first,second,{2},forensic);meta.kind=ChunkScalarKind::I64;read=[step](Count i){return ChunkScalar::i64(i==0?step->control_clips:step->force_clips);};break;default:break;}}
      if(!read&&(role>=R::BoundaryOffset&&role<=R::ChosenInitialKind)){need(a.hasCompleteAssembly(),"complete actual affine required; failure uses defined-region API");const auto* affine=&a.assembly();const Count du=affine->du(),dy=affine->dy();
        switch(role){case R::BoundaryOffset:need(first<=affine->cells(),"boundary cell");meta=info(role,first,0,{30});read=[affine,first](Count i){return ChunkScalar::f64(affine->boundaryOffset(first,i));};break;
          case R::BoundaryControl:need(first<=affine->cells(),"boundary cell");meta=info(role,first,0,{30,du});read=[affine,first,du](Count i){return ChunkScalar::f64(affine->boundaryControl(first,i/du,i%du));};break;
          case R::BoundaryInitial:need(first<=affine->cells(),"boundary cell");meta=info(role,first,0,{30,30});read=[affine,first](Count i){return ChunkScalar::f64(affine->boundaryInitial(first,i/30,i%30));};break;
          case R::EmbeddingControl:meta=info(role,0,0,{dy,du});read=[affine,du](Count i){return ChunkScalar::f64(affine->embeddingControl(i/du,i%du));};break;
          case R::EmbeddingOffset:meta=info(role,0,0,{dy});read=[affine](Count i){return ChunkScalar::f64(affine->embeddingOffset(i));};break;
          case R::ChosenInitial:meta=info(role,0,0,{30});read=[affine](Count i){return ChunkScalar::f64(affine->chosenInitial(i));};break;
          case R::ChosenInitialKind:meta=info(role,0,0,{1});meta.kind=ChunkScalarKind::I64;read=[affine](Count){return ChunkScalar::i64(static_cast<std::int64_t>(affine->initialKind()));};break;
          default:throw std::invalid_argument("recipe is not an actual stored affine leaf");}}
      if(!read){need(decoded.hasCompleteCost(),"complete cost required; failed partial fields use defined-region API");const auto* cost=&decoded.costOutcome().cost();const auto& layouts=cost->inputLayouts();const Count du=a.assembly().du(),dy=a.assembly().dy();
        if(role>=R::CostInputFactor&&role<=R::CostAdditionSampleIndex){need(first<layouts.size(),"sealed cost term index");const auto& t=layouts[first];
          switch(role){case R::CostInputFactor:meta=info(role,first,0,{t.rows,dy});read=[cost,first,dy](Count i){return ChunkScalar::f64(cost->inputFactor(first,i/dy,i%dy));};break;
            case R::CostInputOffset:meta=info(role,first,0,{t.rows});read=[cost,first](Count i){return ChunkScalar::f64(cost->inputOffset(first,i));};break;
            case R::CostInputLinear:meta=info(role,first,0,{dy});read=[cost,first](Count i){return ChunkScalar::f64(cost->inputLinear(first,i));};break;
            case R::CostInputConstant:meta=info(role,first,0,{1});read=[cost,first](Count){return ChunkScalar::f64(cost->inputConstant(first));};break;
            case R::CostAdditionCoefficients:case R::CostAdditionRows:case R::CostAdditionSampleIndex:{need(second<t.additions.size(),"sealed addition index");const auto* add=&t.additions[second];
              if(role==R::CostAdditionCoefficients){meta=info(role,first,second,{add->parent_rows.size(),30});read=[cost,first,second](Count i){return ChunkScalar::f64(cost->inputAdditionCoefficient(first,second,i/30,i%30));};}
              else if(role==R::CostAdditionRows){meta=info(role,first,second,{add->parent_rows.size()});meta.kind=ChunkScalarKind::U64;read=[add](Count i){return ChunkScalar::u64(add->parent_rows.at(i));};}
              else {meta=info(role,first,second,{1});meta.kind=ChunkScalarKind::U64;read=[add](Count){return ChunkScalar::u64(add->sample_index);};}break;}
            default:break;}}
        if(!read&&(role>=R::TermCondensedFactor&&role<=R::TermConstantCoefficient)){need(first<layouts.size(),"retained coefficient term index");const Count rows=layouts[first].rows;
          switch(role){case R::TermCondensedFactor:meta=info(role,first,0,{rows,du});read=[cost,first,du](Count i){return ChunkScalar::f64(cost->retainedFactorControl(first,i/du,i%du));};break;
            case R::TermCondensedOffset:meta=info(role,first,0,{rows});read=[cost,first](Count i){return ChunkScalar::f64(cost->retainedFactorOffset(first,i));};break;
            case R::TermRawH:meta=info(role,first,0,{du,du});read=[cost,first,du](Count i){return ChunkScalar::f64(cost->retainedRawH(first,i/du,i%du));};break;
            case R::TermGradientCoefficient:meta=info(role,first,0,{du});read=[cost,first](Count i){return ChunkScalar::f64(cost->retainedGradientCoefficient(first,i));};break;
            case R::TermConstantCoefficient:meta=info(role,first,0,{1});read=[cost,first](Count){return ChunkScalar::f64(cost->retainedConstantCoefficient(first));};break;default:break;}}
        if(!read)switch(role){case R::EvaluationControl:meta=info(role,0,0,{du});read=[cost](Count i){return ChunkScalar::f64(cost->evaluationControl(i));};break;
          case R::CanonicalRawH:meta=info(role,0,0,{du,du});read=[cost,du](Count i){return ChunkScalar::f64(cost->sumRawH(i/du,i%du));};break;
          case R::CanonicalGradientCoefficient:meta=info(role,0,0,{du});read=[cost](Count i){return ChunkScalar::f64(cost->sumGradientCoefficient(i));};break;
          case R::CanonicalLinear:meta=info(role,0,0,{dy});read=[cost](Count i){return ChunkScalar::f64(cost->sumLinear(i));};break;
          case R::CanonicalInputConstant:meta=info(role,0,0,{1});read=[cost](Count){return ChunkScalar::f64(cost->sumInputConstant());};break;
          case R::CanonicalCondensedConstant:meta=info(role,0,0,{1});read=[cost](Count){return ChunkScalar::f64(cost->sumConstantCoefficient());};break;
          default:throw std::invalid_argument("stored numeric role remains unbound; no replay or invented field");}}
      visit(p,meta,std::move(read),consumer);
    }catch(const std::exception& e){p->reject(e.what());throw;}catch(...){p->reject("NONSTANDARD_STORED_LEAF_FAILURE");throw;}
  }
  static void attach(std::shared_ptr<CaptureLeafState> state,CostDecodeOutcome&& source){
  need(static_cast<bool>(state),"moved leaf session");auto& p=*state;try{need(!p.status.attached&&!p.original_active&&!p.leaf_active&&p.gate,"leaf source already attached/active/gate absent");
    // Transfer before matching so failed binding retains genuine return as well.
    p.owner.emplace(bindCaptureInventory(std::move(source),std::move(*p.gate)));p.status.attached=true;
    const auto& actual=p.owner->genuineSource();need(actual.originalAssembly().captureOriginToken()==p.source_origin&&actual.capture_partition_==p.partition,"returned leaf source/partition mismatch");
    if(actual.hasCompleteCost()){const auto cost=actual.costOutcome().captureCostToken();need(static_cast<bool>(cost),"actual returned cost origin absent");if(!p.actual_cost_origin)p.actual_cost_origin=cost;need(cost==p.actual_cost_origin,"returned cost owner differs from original leaf scope");}
    // Already refused capture MUST still retain failed source, without restoring success.
    if(!actual.hasCompleteCost())p.reject(actual.refusal().empty()?"returned source refused":actual.refusal().data());
  }catch(const std::exception& e){p.reject(e.what());throw;}catch(...){p.reject("NONSTANDARD_LEAF_ATTACHMENT_FAILURE");throw;}
  }

};
}
NumericLeafView::NumericLeafView(detail::LeafBinding* binding):binding_(binding){}
const NumericLeafInfo& NumericLeafView::info() const{try{need(binding_&&binding_->owner->leaf_active&&binding_->generation==binding_->owner->generation,"leaf outside borrowed generation");
    if(binding_->forensic_only){need(binding_->owner->forensic_active,"forensic generation closed");binding_->owner->forensicHealthy();}else binding_->owner->healthy();return binding_->info;
  }catch(const std::exception& e){if(binding_){if(binding_->forensic_only)binding_->owner->rejectForensic(e.what());else binding_->owner->reject(e.what());}throw;}}
ChunkScalar NumericLeafView::scalar(Count i) const{try{const auto& meta=info();need(i<meta.count,"numeric leaf scalar index");return binding_->read(i);}
  catch(const std::exception& e){if(binding_){if(binding_->forensic_only)binding_->owner->rejectForensic(e.what());else binding_->owner->reject(e.what());}throw;}
  catch(...){if(binding_){if(binding_->forensic_only)binding_->owner->rejectForensic("NONSTANDARD_FORENSIC_SCALAR_FAILURE");else binding_->owner->reject("NONSTANDARD_LEAF_SCALAR_FAILURE");}throw;}}
bool NumericLeafView::readOnlyForensic() const{info();return binding_->forensic_only;}
Count NumericLeafView::frontierWritten(Count field) const{try{info();need(binding_->frontier&&field<32,"frontier absent/index");return binding_->frontier->written[field];}catch(const std::exception& e){if(binding_){if(binding_->forensic_only)binding_->owner->rejectForensic(e.what());else binding_->owner->reject(e.what());}throw;}}
std::string_view NumericLeafView::frontierStage() const{try{info();need(binding_->frontier,"frontier absent");return binding_->frontier->stage;}catch(const std::exception& e){if(binding_){if(binding_->forensic_only)binding_->owner->rejectForensic(e.what());else binding_->owner->reject(e.what());}throw;}}
OriginalLeafBatch::OriginalLeafBatch(std::shared_ptr<detail::CaptureLeafState> s):state_(std::move(s)){}
void OriginalLeafBatch::withLeaf(R r,const NumericLeafConsumer& visitor) const{detail::CaptureLeafFactory::originalLeaf(state_,r,visitor);}
void OriginalLeafBatch::exportLeaf(R r,const std::string& root,const std::string& name) const{detail::CaptureLeafFactory::originalLeaf(state_,r,[&](const NumericLeafView& leaf){detail::CaptureLeafFactory::exportBound(state_,leaf,root,name);});}
CaptureLeafSession::CaptureLeafSession(std::shared_ptr<detail::CaptureLeafState> s):state_(std::move(s)){}
CaptureLeafSession::CaptureLeafSession(CaptureLeafSession&&) noexcept=default;CaptureLeafSession& CaptureLeafSession::operator=(CaptureLeafSession&&) noexcept=default;CaptureLeafSession::~CaptureLeafSession()=default;
InitialCostConsumer CaptureLeafSession::originalConsumer(const std::function<void(const OriginalLeafBatch&)>& term,const std::function<void(const OriginalLeafBatch&)>& canonical){
  need(static_cast<bool>(state_),"moved leaf session");try{need(static_cast<bool>(state_->gate),"leaf original gate absent");state_->healthy();const auto state=state_;
    return state_->gate->consumer([state,term](const UsedTermView& v){detail::CaptureLeafFactory::originalEnter(state,&v,nullptr,term);},[state,canonical](const CostEvaluationView& v){detail::CaptureLeafFactory::originalEnter(state,nullptr,&v,canonical);});
  }catch(const std::exception& e){state_->reject(e.what());throw;}catch(...){state_->reject("NONSTANDARD_LEAF_CONSUMER_ISSUANCE_FAILURE");throw;}
}
void CaptureLeafSession::attachReturnedSource(CostDecodeOutcome&& source){detail::CaptureLeafFactory::attach(state_,std::move(source));}
void CaptureLeafSession::withStoredLeaf(R r,Count first,Count second,const NumericLeafConsumer& visitor) const{need(static_cast<bool>(state_),"moved leaf session");detail::CaptureLeafFactory::stored(state_,r,first,second,visitor);}
void CaptureLeafSession::exportStoredLeaf(R r,Count first,Count second,const std::string& root,const std::string& name){withStoredLeaf(r,first,second,[&](const NumericLeafView& leaf){detail::CaptureLeafFactory::exportBound(state_,leaf,root,name);});}
void CaptureLeafSession::withDefinedRegions(Count layer,const NumericLeafConsumer& visitor) const{
  need(static_cast<bool>(state_),"moved leaf session");auto p=state_;try{need(p->owner&&p->status.attached,"defined region owner absent");p->forensicHealthy();need(!p->leaf_active&&!p->original_active&&!p->forensic_active,"defined region reentry");
  p->forensic_active=true;struct Guard{bool& flag;Guard(bool& f):flag(f){}~Guard(){flag=false;}} guard(p->forensic_active);++p->forensic.generations;const auto& decoded=p->owner->genuineSource();Count ordinal=0;
  auto observe=[&](const RetainedNumericRegionView& region){auto frame=p->budget.reserve(20);p->budget.chargeScratchOrCopy(20);auto meta=detail::CaptureLeafFactory::info(R::FailureDefinedRegions,layer,ordinal++,{region.definedCount()},true);meta.has_composite_frontier=true;meta.state=DefinedComputedState::DefinedNotComputed;meta.assigned_prefix_known=false;meta.traversal="actual-defined-range-with-strided-write-frontiers";
    detail::CaptureLeafFactory::visit(p,meta,[&region](Count i){const auto value=ChunkScalar::f64(region.value(i));return ChunkScalar::failureF64Bits(value.bits);},visitor,&region.trace(),true);};
  if(layer==0){const auto& o=decoded.originalAssembly().originalNormalization();need(o.hasRetainedRegions(),"normalizer defined regions absent");o.withRetainedRegions(observe);}
    else if(layer==1){const auto& o=decoded.originalAssembly();need(o.hasRetainedRegions(),"affine defined regions absent");o.withRetainedRegions(observe);}
    else if(layer==2){const auto& o=decoded.costOutcome();need(o.hasRetainedRegions(),"cost defined regions absent");o.withRetainedRegions(observe);}else throw std::invalid_argument("unknown defined region layer");
  p->forensicHealthy();
  }catch(const std::exception& e){p->rejectForensic(e.what());throw;}catch(...){p->rejectForensic("NONSTANDARD_DEFINED_LEAF_FAILURE");throw;}
}
CaptureLeafObservation CaptureLeafSession::observation() const{need(static_cast<bool>(state_),"moved leaf session");return state_->status;}
ForensicBorrowObservation CaptureLeafSession::forensicObservation() const{need(static_cast<bool>(state_),"moved leaf session");return state_->forensic;}
const std::vector<BoundLeafAttempt>& CaptureLeafSession::retainedAttempts() const{need(static_cast<bool>(state_),"moved leaf session");return state_->attempts;}
void CaptureLeafSession::close(){need(static_cast<bool>(state_),"moved leaf session");try{state_->healthy();need(!state_->original_active&&!state_->leaf_active,"leaf close inside callback");state_->status.closed=true;}catch(const std::exception& e){state_->reject(e.what());throw;}catch(...){state_->reject("NONSTANDARD_LEAF_CLOSE_FAILURE");throw;}}
CaptureLeafSession prepareCaptureLeaves(const AffineAssemblyOutcome& source,const CaptureWorkspaceGrant& grant){return detail::CaptureLeafFactory::prepare(source,grant);}
}
