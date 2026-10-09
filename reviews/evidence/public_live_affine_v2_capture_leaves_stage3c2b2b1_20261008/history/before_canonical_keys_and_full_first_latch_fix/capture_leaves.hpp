#pragma once
#include "capture_inventory.hpp"
#include "capture_workspace.hpp"
#include "numeric_chunks.hpp"
namespace phase5_public_live_affine_v2 {
namespace detail {struct CaptureLeafState;struct CaptureLeafFactory;struct LeafBinding;}
struct NumericLeafInfo {
  RequiredRole role;Count primary=0,secondary=0,count=0,rank=0;
  std::array<Count,4> dimensions{};
  ChunkScalarKind kind=ChunkScalarKind::F64;ChunkClassification classification=ChunkClassification::FiniteFields;
  DefinedComputedState state=DefinedComputedState::UnknownUntilLeafBinding;
  Count defined_count=0,assigned_prefix=0;bool assigned_prefix_known=false;
  bool has_composite_frontier=false;
  const char* traversal="row-major";
};
class NumericLeafView final {
 public:
  NumericLeafView(const NumericLeafView&)=delete;NumericLeafView& operator=(const NumericLeafView&)=delete;
  const NumericLeafInfo& info() const;
  ChunkScalar scalar(Count index) const;
  Count frontierWritten(Count field) const;
  std::string_view frontierStage() const;
 private:
  explicit NumericLeafView(detail::LeafBinding*);
  detail::LeafBinding* binding_;friend struct detail::CaptureLeafFactory;
};
using NumericLeafConsumer=std::function<void(const NumericLeafView&)>;
struct CaptureLeafObservation {Count receipt_attempts=0,verified_chunks=0;bool attached=false,closed=false,refused=false;std::string first_error;};
class OriginalLeafBatch final {
 public:
  OriginalLeafBatch(const OriginalLeafBatch&)=delete;OriginalLeafBatch& operator=(const OriginalLeafBatch&)=delete;
  void withLeaf(RequiredRole,const NumericLeafConsumer&) const;
  void exportLeaf(RequiredRole,const std::string& absolute_root,const std::string& provisional_name) const;
 private:
  explicit OriginalLeafBatch(std::shared_ptr<detail::CaptureLeafState>);
  std::shared_ptr<detail::CaptureLeafState> state_;friend struct detail::CaptureLeafFactory;
};
class BoundLeafAttempt final {
 public:
  BoundLeafAttempt(const BoundLeafAttempt&)=delete;BoundLeafAttempt& operator=(const BoundLeafAttempt&)=delete;
  BoundLeafAttempt(BoundLeafAttempt&&) noexcept=default;BoundLeafAttempt& operator=(BoundLeafAttempt&&) noexcept=default;
  RequiredRole role() const noexcept{return role_;}Count primary() const noexcept{return primary_;}Count secondary() const noexcept{return secondary_;}
  const ChunkWriteOutcome& write() const noexcept{return write_;}
  const std::optional<ChunkReadOutcome>& readback() const noexcept{return readback_;}
  bool semanticMismatch() const noexcept{return mismatch_;}Count mismatchIndex() const noexcept{return mismatch_index_;}
  ChunkScalar expectedScalar() const noexcept{return expected_;}ChunkScalar actualScalar() const noexcept{return actual_;}
 private:
  BoundLeafAttempt()=default;
  std::shared_ptr<const void> source_origin_,cost_origin_;std::shared_ptr<detail::CapturePartitionState> partition_;
  RequiredRole role_;Count primary_=0,secondary_=0;bool original_scope_=false,canonical_scope_=false;
  ChunkWriteOutcome write_;std::optional<ChunkReadOutcome> readback_;
  bool mismatch_=false;Count mismatch_index_=0;ChunkScalar expected_,actual_;
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
  void withDefinedRegions(Count layer,const NumericLeafConsumer&) const; //0 normalizer/1 affine/2 cost.
  CaptureLeafObservation observation() const;
  const std::vector<BoundLeafAttempt>& retainedAttempts() const;
  void close();
  bool fullCaptureComplete() const noexcept{return false;}
 private:
  explicit CaptureLeafSession(std::shared_ptr<detail::CaptureLeafState>);
  std::shared_ptr<detail::CaptureLeafState> state_;friend struct detail::CaptureLeafFactory;
};
CaptureLeafSession prepareCaptureLeaves(const AffineAssemblyOutcome&,const CaptureWorkspaceGrant&);
// Private genuine leaves only. Composite metadata/sample/fullmanifest unbound.
}
