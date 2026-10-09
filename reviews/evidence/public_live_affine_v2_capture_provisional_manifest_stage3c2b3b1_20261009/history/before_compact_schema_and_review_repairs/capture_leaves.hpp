#pragma once
#include "capture_inventory.hpp"
#include "capture_workspace.hpp"
#include "numeric_chunks.hpp"
namespace phase5_public_live_affine_v2 {
enum class ProvisionalManifestMode;class ProvisionalManifestAttempt;
class MetadataLeafView;class ReferenceLeafView;class CoverageObligationView;
namespace detail {struct CaptureLeafState;struct CaptureLeafFactory;struct LeafBinding;}
struct NumericLeafInfo {
  RequiredRole role;Count primary=0,secondary=0,count=0,rank=0;
  std::array<Count,4> dimensions{};
  ChunkScalarKind kind=ChunkScalarKind::F64;ChunkClassification classification=ChunkClassification::FiniteFields;
  DefinedComputedState state=DefinedComputedState::UnknownUntilLeafBinding;
  Count defined_count=0,assigned_prefix=0;bool assigned_prefix_known=false;
  bool has_composite_frontier=false;
  const char* assignment_traversal="same-as-storage";
  const char* traversal="row-major";
};
class NumericLeafView final {
 public:
  NumericLeafView(const NumericLeafView&)=delete;NumericLeafView& operator=(const NumericLeafView&)=delete;
  const NumericLeafInfo& info() const;
  ChunkScalar scalar(Count index) const;
  bool readOnlyForensic() const;
  Count frontierWritten(Count field) const;
  std::string_view frontierStage() const;
 private:
  explicit NumericLeafView(detail::LeafBinding*);
  detail::LeafBinding* binding_;friend struct detail::CaptureLeafFactory;
};
using NumericLeafConsumer=std::function<void(const NumericLeafView&)>;
struct ForensicBorrowObservation {bool refused=false;Count generations=0;std::string first_error;};
struct CaptureLeafObservation {Count receipt_attempts=0,verified_chunks=0,ancillary_receipt_attempts=0,samples_completed=0;bool samples_attempted=false;bool attached=false,closed=false,refused=false;std::string first_error;};
class OriginalLeafBatch final {
 public:
  OriginalLeafBatch(const OriginalLeafBatch&)=delete;OriginalLeafBatch& operator=(const OriginalLeafBatch&)=delete;
  void withLeaf(RequiredRole,const NumericLeafConsumer&) const;
  void exportLeaf(RequiredRole,const std::string& absolute_root,const std::string& provisional_name) const;
 private:
  explicit OriginalLeafBatch(std::shared_ptr<detail::CaptureLeafState>);
  std::shared_ptr<detail::CaptureLeafState> state_;friend struct detail::CaptureLeafFactory;
};
class SampleLeafBatch final {
 public:
  SampleLeafBatch(const SampleLeafBatch&)=delete;SampleLeafBatch& operator=(const SampleLeafBatch&)=delete;
  Count sampleIndex() const;Count cell() const;Count tick() const;Count cycle() const;Count half() const;
  void withLeaf(RequiredRole,const NumericLeafConsumer&) const;
  void exportLeaf(RequiredRole,const std::string& root,const std::string& provisional_name) const;
 private:
  explicit SampleLeafBatch(std::shared_ptr<detail::CaptureLeafState>);
  std::shared_ptr<detail::CaptureLeafState> state_;friend struct detail::CaptureLeafFactory;
};
class BoundLeafAttempt final {
 public:
  BoundLeafAttempt(const BoundLeafAttempt&)=delete;BoundLeafAttempt& operator=(const BoundLeafAttempt&)=delete;
  BoundLeafAttempt(BoundLeafAttempt&&) noexcept=default;BoundLeafAttempt& operator=(BoundLeafAttempt&&) noexcept=default;
  Count originalAttemptSequence() const noexcept{return attempt_sequence_;}
  RequiredRole role() const noexcept{return role_;}Count primary() const noexcept{return primary_;}Count secondary() const noexcept{return secondary_;}
  const ChunkWriteOutcome& write() const noexcept{return write_;}
  const std::optional<ChunkReadOutcome>& readback() const noexcept{return readback_;}
  bool comparisonAttempted() const noexcept{return comparison_attempted_;}bool expectedScalarValid() const noexcept{return expected_valid_;}
  bool sampleScope() const noexcept{return sample_scope_;}Count sampleCell() const noexcept{return sample_cell_;}Count sampleTick() const noexcept{return sample_tick_;}Count sampleCycle() const noexcept{return sample_cycle_;}Count sampleHalf() const noexcept{return sample_half_;}
  bool semanticMismatch() const noexcept{return mismatch_;}Count mismatchIndex() const noexcept{return mismatch_index_;}
  ChunkScalar expectedScalar() const noexcept{return expected_;}ChunkScalar actualScalar() const noexcept{return actual_;}
 private:
  BoundLeafAttempt()=default;
  std::shared_ptr<const void> source_origin_,cost_origin_;std::shared_ptr<detail::CapturePartitionState> partition_;
  const char* storage_traversal_="row-major";const char* assignment_traversal_="same-as-storage";
  DefinedComputedState computed_state_=DefinedComputedState::UnknownUntilLeafBinding;Count generation_=0,attempt_sequence_=0;
  RequiredRole role_;Count primary_=0,secondary_=0;bool original_scope_=false,canonical_scope_=false,sample_scope_=false;Count sample_cell_=0,sample_tick_=0,sample_cycle_=0,sample_half_=0;
  ChunkWriteOutcome write_;std::optional<ChunkReadOutcome> readback_;
  bool comparison_attempted_=false,expected_valid_=false,mismatch_=false;Count mismatch_index_=0;ChunkScalar expected_,actual_;
  friend struct detail::CaptureLeafFactory;
};
class CaptureLeafSession final {
 public:
  CaptureLeafSession(const CaptureLeafSession&)=delete;CaptureLeafSession& operator=(const CaptureLeafSession&)=delete;
  CaptureLeafSession(CaptureLeafSession&&) noexcept;CaptureLeafSession& operator=(CaptureLeafSession&&) noexcept;~CaptureLeafSession();
  InitialCostConsumer originalConsumer(const std::function<void(const OriginalLeafBatch&)>& term_sink={},
                                       const std::function<void(const OriginalLeafBatch&)>& canonical_sink={});
  void attachReturnedSource(CostDecodeOutcome&&);
  void withStoredLeaf(RequiredRole,Count primary,Count secondary,const NumericLeafConsumer&) const;
  void exportStoredLeaf(RequiredRole,Count primary,Count secondary,const std::string& absolute_root,const std::string& provisional_name);
  void streamSamplesOnce(const std::function<void(const SampleLeafBatch&)>&);
  void withDefinedRegions(Count layer,const NumericLeafConsumer&) const; //0 normalizer/1 affine/2 cost.
  CaptureLeafObservation observation() const;
  ForensicBorrowObservation forensicObservation() const;
  const std::vector<BoundLeafAttempt>& retainedAttempts() const;
  void withMetadata(const std::function<void(const MetadataLeafView&)>&) const;
  void withReferences(const std::function<void(const ReferenceLeafView&)>&) const;
  void withCoverageObligations(const std::function<void(const CoverageObligationView&)>&) const;
  void captureProvisionalManifest(const std::string& root,const std::string& name,ProvisionalManifestMode);
  const ProvisionalManifestAttempt* retainedProvisionalManifest() const;
  void close();
  bool fullCaptureComplete() const noexcept{return false;}
 private:
  explicit CaptureLeafSession(std::shared_ptr<detail::CaptureLeafState>);
  std::shared_ptr<detail::CaptureLeafState> state_;friend struct detail::CaptureLeafFactory;
};
CaptureLeafSession prepareCaptureLeaves(const AffineAssemblyOutcome&,const CaptureWorkspaceGrant&);
// Private genuine leaves only. Composite metadata/sample/fullmanifest unbound.
}
