#pragma once
#include "cost_input_decoder.hpp"
#include <array>
namespace phase5_public_live_affine_v2 {
namespace detail {struct OriginalCaptureState;struct CaptureInventoryStorage;struct CaptureInventoryFactory;}
enum class RequiredRole {
  ProvenanceAndMetadata,InvocationAndExecution,RawFlagsAndErrors,RawFinalState,RawCellControl,
  RawCellState,RawCycleState,RawSubstepPhysical,RawSubstepProgress,RawFrictionForce,
  RawFrictionBranches,RawFrictionIterations,RawFrictionKkt,RawClips,RawMapLocalA,
  RawMapLocalB,RawMapLocalDefect,RawMapCellA,RawMapCellB,RawMapCellDefect,
  RawMapOrigin,RawMapCellOrigin,RawMapEndpoint,RawMapInput,RawMapIndices,
  NormalizedSourceReference,BoundaryOffset,BoundaryControl,BoundaryInitial,
  EmbeddingControl,EmbeddingOffset,StructuredInitialSelector,ChosenInitial,ChosenInitialKind,EvaluationControl,
  SampleCompositionRecipe,SampleEvaluatedOffset,SampleEvaluatedActualOffset,
  SampleEvaluatedControl,SampleEvaluatedInitial,CostNamesAndUnits,CostInputFactor,
  CostInputOffset,CostInputLinear,CostInputConstant,CostAdditionCoefficients,
  CostAdditionRows,CostAdditionSampleIndex,CostTopologyClosure,OriginalUsedFactor,OriginalUsedOffset,OriginalUsedLinear,
  OriginalUsedConstant,TermCondensedFactor,TermCondensedOffset,TermRawH,
  TermGradientCoefficient,TermConstantCoefficient,OriginalDirectValue,
  OriginalDirectGradient,OriginalDirectHessian,OriginalCondensedValue,
  OriginalCondensedGradient,OriginalCondensedHessian,CanonicalOrderedConcatenation,
  CanonicalRawH,CanonicalGradientCoefficient,CanonicalLinear,CanonicalInputConstant,
  CanonicalCondensedConstant,DenseLiftedL,DenseLiftedE,DenseLiftedOffset,
  DenseInitialSelector,DenseActiveLU,DenseActiveRhs,DenseSolution,DenseSampleSelector,
  DenseSampleOffset,DenseSampleControl,DenseSampleInitial,FailureDefinedRegions,
  DecoderFrontiers,CountRoles
};
enum class FieldAvailability {OwnedSourceReference,OriginalObservedNotStored,
  RecipeNotEvaluated,PendingLeafBinding,AbsentUpstream,ForensicSourceOnly};
enum class RequiredScalarKind {F64,U64,I64,Metadata,SourceReference,Composite};
enum class DefinedComputedState {UnknownUntilLeafBinding,DefinedNotComputed,ComputedOriginal,AssignedUnvalidated,NotPresent};
enum class FieldClassification {SourceMetadata,FiniteComponent,DefinedForensic,Recipe};
struct RequiredField {
  RequiredRole role;Count primary=0,secondary=0;
  std::array<Count,4> dimensions{};Count rank=0;
  FieldAvailability availability=FieldAvailability::PendingLeafBinding;
  FieldClassification classification=FieldClassification::SourceMetadata;
  const char* traversal="declared-row-major";bool mandatory=true;
  RequiredScalarKind scalar_kind=RequiredScalarKind::Composite;
  DefinedComputedState defined_computed=DefinedComputedState::UnknownUntilLeafBinding;
  bool shape_known=true;
  bool actual_leaf_bound=false,bytes_captured=false,exact_readback=false;
};
struct OriginalCaptureObservation {Count expected_terms=0,terms_observed=0;bool canonical_observed=false,issued=false,refused=false;std::string first_error;};
class OriginalCaptureGate final {
 public:
  OriginalCaptureGate(const OriginalCaptureGate&)=delete;OriginalCaptureGate& operator=(const OriginalCaptureGate&)=delete;
  OriginalCaptureGate(OriginalCaptureGate&&) noexcept=default;OriginalCaptureGate& operator=(OriginalCaptureGate&&) noexcept=default;
  // Borrow genuine ORIGINAL views only; this records observations, not bytes.
  InitialCostConsumer consumer(const std::function<void(const UsedTermView&)>& term_sink={},
                               const std::function<void(const CostEvaluationView&)>& canonical_sink={});
  OriginalCaptureObservation observation() const;
 private:
  explicit OriginalCaptureGate(std::shared_ptr<detail::OriginalCaptureState>);
  std::shared_ptr<detail::OriginalCaptureState> state_;friend struct detail::CaptureInventoryFactory;
};
struct CaptureFlowEnvelope {
  Count raw_shape_slots=0,sdk_allowance=0,normalized_slots=0,normalizer_held=0;
  Count boundary_slots=0,embedding_slots=0,input_slots=0,cost_capture_slots=0,factor_work=0,sample_work=0;
  Count original_cost_reuse=0,once_sample_reuse=0,input_cache_slots=16;
  Count writer_io_slots=20,reader_io_slots=28,retained_axes_per_chunk=4,catalogue_frame_slots=20;
  Count input_refill_full_read_nominal=0,input_refill_shortread_worst=0,planned_existing_source_peak=0;
  Count current_live=0,planned_live=0,current_charges=0,planned_charges=0;
  bool added_io_fits_now=false,preplanned_workspace_transfer=false,full_flow_accepted=false;
};
class CaptureInventoryOwner final {
 public:
  CaptureInventoryOwner(const CaptureInventoryOwner&)=delete;CaptureInventoryOwner& operator=(const CaptureInventoryOwner&)=delete;
  CaptureInventoryOwner(CaptureInventoryOwner&&) noexcept;CaptureInventoryOwner& operator=(CaptureInventoryOwner&&) noexcept;~CaptureInventoryOwner();
  const CostDecodeOutcome& genuineSource() const;
  const CaptureFlowEnvelope& integerEnvelope() const;
  bool sourceComponentComplete() const noexcept;
  bool fullCaptureComplete() const noexcept{return false;} // B1 cannot publish/verify closure.
  void withRequirements(const std::function<void(const RequiredField&)>&) const;
  std::string_view admissionRefusal() const noexcept;
 private:
  explicit CaptureInventoryOwner(CostDecodeOutcome&&);
  CostDecodeOutcome original_;std::shared_ptr<detail::OriginalCaptureState> original_gate_;std::unique_ptr<detail::CaptureInventoryStorage> storage_;
  std::string reason_;bool refused_=false;friend struct detail::CaptureInventoryFactory;
};
OriginalCaptureGate prepareOriginalCaptureGate(const AffineAssemblyOutcome&);
CaptureInventoryOwner bindCaptureInventory(CostDecodeOutcome&&,OriginalCaptureGate&&);
// Caller NumericChunkRecord/hash/count cannot mint owner/coverage/completeness.
}
