#pragma once
// Stage 1 implementation source. No Model dependency or runnable entry point.
#include <array>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

namespace phase5_public_live_affine_v2 {
using Count = std::uint64_t;
using JointVector = std::array<double, 7>;
constexpr double macro_dt = .004;
constexpr double physical_dt = .002;
constexpr Count state_dimension = 30;
constexpr Count input_dimension = 8;

class ResourcePolicyV2 final {
 public:
  static constexpr Count cells = 32, cycles = 375, samples = 750;
  static constexpr Count terms = 32, rows = 8192, term_rows = 256;
  static constexpr Count addition_coefficients = 4000000, addition_records = 8192;
  static constexpr Count matrix_entries = 12000000, live_slots = 64000000;
  static constexpr Count case_charges = 512000000, batch_charges = 1024000000;
  static constexpr Count output_bytes = 256 * 1024 * 1024;
  static constexpr Count metadata_bytes = 8 * 1024 * 1024;
}; // Version-fixed ceilings, not configurable upward by a caller.

Count checkedAdd(Count a, Count b);
Count checkedMultiply(Count a, Count b);
enum class MeshPolicy { UniformExact, BalancedInteger, ExplicitCycles };
enum class CaptureMode { CompactComplete, DenseAuditComplete };
enum class NumericEncoding { LosslessBinary, FullNumericJson };
struct HorizonSpec {
  Count steps = 20, total_macro_cycles = 200;
  MeshPolicy policy = MeshPolicy::UniformExact;
  std::vector<Count> explicit_cycles;
};
class CycleMesh final {
 public:
  const std::vector<Count>& cycles() const noexcept { return cycles_; }
  Count total() const noexcept { return total_; }
 private:
  CycleMesh() = default;
  std::vector<Count> cycles_;
  Count total_ = 0;
  friend CycleMesh planMesh(const HorizonSpec&);
};
// Decimal seconds only; exact 4ms divisibility, no exponent/rounding/cover policy.
Count exactDecimalSecondsToCycles(const std::string& seconds);
CycleMesh planMesh(const HorizonSpec& spec);

struct FactorShape {
  Count terms = 0, rows = 0, largest_term_rows = 0;
  Count addition_coefficients = 0, addition_records = 0;
};
class ResourcePlan final {
 public:
  Count liveCeiling() const noexcept { return live_; }
  Count chargeCeiling() const noexcept { return charges_; }
  Count outputCeiling() const noexcept { return output_; }
  Count metadataCeiling() const noexcept { return ResourcePolicyV2::metadata_bytes; }
  Count sdkPlanningAllowance() const noexcept { return sdk_allowance_; }
  Count rawResultShapeSlots() const noexcept { return raw_; }
  Count dx() const noexcept { return dx_; }
  Count du() const noexcept { return du_; }
  Count dy() const noexcept { return dy_; }
  CaptureMode captureMode() const noexcept { return mode_; }
  NumericEncoding numericEncoding() const noexcept { return encoding_; }
  Count memberCaptureSlots() const noexcept { return member_slots_; }
  Count memberCaptureCharges() const noexcept { return member_charges_; }
 private:
  ResourcePlan() = default;
  Count live_ = 0, charges_ = 0, output_ = 0, sdk_allowance_ = 0, raw_ = 0;
  Count dx_ = 0, du_ = 0, dy_ = 0;
  Count member_slots_=0,member_charges_=0;
  CaptureMode mode_ = CaptureMode::CompactComplete;
  NumericEncoding encoding_ = NumericEncoding::LosslessBinary;
  friend ResourcePlan planResourcesWithMemberCaptureV1(const CycleMesh&,const FactorShape&,CaptureMode,NumericEncoding,Count,Count);
  friend ResourcePlan planResources(const CycleMesh&, const FactorShape&,
                                     CaptureMode, NumericEncoding);
};
ResourcePlan planResources(const CycleMesh&, const FactorShape&,
                           CaptureMode, NumericEncoding);

// Private source factories derive these quantities from actual frozen rosters.
// This plan alone is NOT a genuine source or execution witness.
ResourcePlan planResourcesWithMemberCaptureV1(const CycleMesh&,const FactorShape&,CaptureMode,NumericEncoding,Count owned_slots,Count added_charges);

namespace detail {
struct BatchState; struct CaseState; struct ForecastFactory; struct ForecastReleaseState;
}
class OwnedReservation final {
 public:
  OwnedReservation(const OwnedReservation&) = delete;
  OwnedReservation& operator=(const OwnedReservation&) = delete;
  OwnedReservation(OwnedReservation&&) noexcept;
  OwnedReservation& operator=(OwnedReservation&&) noexcept;
  ~OwnedReservation();
  Count slots() const noexcept { return slots_; }
 private:
  void release() noexcept;
  OwnedReservation(std::shared_ptr<detail::CaseState>, Count);
  std::shared_ptr<detail::CaseState> state_;
  Count slots_ = 0;
  friend class CaseBudget;
};
// Tickets are lifetime primitives, not automatic inspection of external storage.
// A raw result owner must destroy its raw result BEFORE its ticket. A borrow must
// keep its ticket for the entire borrowed storage use. No public early release.
class OwnedNumericBuffer final {
 public:
  OwnedNumericBuffer(class CaseBudget&, Count slots);
  OwnedNumericBuffer(const OwnedNumericBuffer&) = delete;
  OwnedNumericBuffer& operator=(const OwnedNumericBuffer&) = delete;
  OwnedNumericBuffer(OwnedNumericBuffer&&) noexcept;
  OwnedNumericBuffer& operator=(OwnedNumericBuffer&&) noexcept;
  Count size() const noexcept { return reservation_.slots(); }
  double* data() noexcept { return data_.get(); }
  const double* data() const noexcept { return data_.get(); }
 private:
  OwnedReservation reservation_; // Destroyed AFTER data_.
  std::unique_ptr<double[]> data_;
};
class BatchBudget final {
 public:
  BatchBudget();
  BatchBudget(const BatchBudget&) = delete;
  BatchBudget& operator=(const BatchBudget&) = delete;
  BatchBudget(BatchBudget&&) noexcept = default;
  BatchBudget& operator=(BatchBudget&&) noexcept = default;
  Count liveSlots() const;
  Count cumulativeCharges() const;
 private:
  std::shared_ptr<detail::BatchState> state_;
  friend class CaseBudget;
};
// Single-threaded per batch; charges are never refunded, including failures.
class SharedCaseBudget;class ChunkIOLease;
class CaseBudget final {
 public:
  CaseBudget(BatchBudget&, const ResourcePlan&);
  CaseBudget(const CaseBudget&) = delete;
  CaseBudget& operator=(const CaseBudget&) = delete;
  CaseBudget(CaseBudget&&) noexcept = default;
  CaseBudget& operator=(CaseBudget&&) noexcept = default;
  OwnedReservation reserve(Count slots); // Call BEFORE buffer materialization.
  void chargeScratchOrCopy(Count slots); // Cumulative use of already owned work.
  void chargeMetadataBytes(Count bytes); // Actual encoded aggregate, no refund.
  void chargeUniqueOutputBytes(Count bytes); // Writer counts each unique blob once.
  Count liveSlots() const;
  bool sameBatch(const BatchBudget&) const noexcept;
  Count cumulativeCharges() const;
  Count outputBytes() const;
  Count metadataBytes() const;
  SharedCaseBudget share() const; // Same ledger; lifetime-safe IO lease, no new plan.
 private:
  explicit CaseBudget(std::shared_ptr<detail::CaseState>);
  std::shared_ptr<detail::CaseState> state_;
  friend class SharedCaseBudget;
};
class SharedCaseBudget final {
 public:
  OwnedReservation reserve(Count);
  void chargeScratchOrCopy(Count);
  void chargeMetadataBytes(Count);
  void chargeUniqueOutputBytes(Count);
  Count outputBytes() const;
  Count metadataBytes() const;
  Count outputCeiling() const;
  NumericEncoding numericEncoding() const;
  ChunkIOLease beginChunkIO();
  Count liveSlots() const;
  Count liveCeiling() const;
  Count cumulativeCharges() const;
  Count chargeCeiling() const;
  bool sameCase(const SharedCaseBudget&) const noexcept;
 private:
  explicit SharedCaseBudget(std::shared_ptr<detail::CaseState>);
  std::shared_ptr<detail::CaseState> state_;
  friend class CaseBudget;
};

class ChunkIOLease final {
 public:
  ChunkIOLease(const ChunkIOLease&)=delete;
  ChunkIOLease& operator=(const ChunkIOLease&)=delete;
  ChunkIOLease(ChunkIOLease&&) noexcept=default;
  ChunkIOLease& operator=(ChunkIOLease&&)=delete;
  ~ChunkIOLease();
  void requireHealthy() const;
  const char* firstReentryReason() const noexcept;
 private:
  explicit ChunkIOLease(std::shared_ptr<detail::CaseState>);
  std::shared_ptr<detail::CaseState> state_;
  friend class SharedCaseBudget;
};

// These are observed file facts, not a Model/derivative/permission certificate.
struct FileIdentity { std::string path, sha256; Count bytes = 0; };
FileIdentity observePinnedFile(const std::string& path,
                              const std::string& expected_sha256);
struct MemberIdentityObservationV1 {const char* stage="NOT_ATTEMPTED";Count bytes_read=0,attempted_read_bytes=0,device=0,inode=0,size=0;bool physical_eof=false,hash_state_valid=false,hash_valid=false,refused=false;std::string physical_sha256,first_error;};
FileIdentity observePinnedFileWithMemberBudgetV1(SharedCaseBudget,const FileIdentity&,MemberIdentityObservationV1&);
FileIdentity observeCurrentProducerElfWithMemberBudgetV1(SharedCaseBudget,const std::string& expected_sha,Count expected_bytes,MemberIdentityObservationV1&);
FileIdentity observeCurrentProducerElf(const std::string& expected_sha256);
class StaticDomainRanges final {
 public:
  StaticDomainRanges(const StaticDomainRanges&) = default;
  StaticDomainRanges& operator=(const StaticDomainRanges&) = default;
  const JointVector& qLower() const noexcept { return q_lower_; }
  const JointVector& qUpper() const noexcept { return q_upper_; }
  const JointVector& cLower() const noexcept { return c_lower_; }
  const JointVector& cUpper() const noexcept { return c_upper_; }
  const FileIdentity& constantsIdentity() const noexcept { return identity_; }
 private:
  StaticDomainRanges() = default;
  JointVector q_lower_{}, q_upper_{}, c_lower_{}, c_upper_{};
  FileIdentity identity_;
  friend StaticDomainRanges loadPinnedStaticRanges(const std::string&,
                                                   const std::string&);
  friend class LiveActualContext;
};
// Hash and parse only the bounded constants bytes; no SDK/Model metadata query.
StaticDomainRanges loadPinnedStaticRanges(const std::string& path,
                                         const std::string& expected_sha256);
class ReviewedForecastPermission final {
 public:
  ReviewedForecastPermission(const ReviewedForecastPermission&) = delete;
  ReviewedForecastPermission& operator=(const ReviewedForecastPermission&) = delete;
  ReviewedForecastPermission(ReviewedForecastPermission&&) noexcept = default;
 private:
  ReviewedForecastPermission() = default;
  std::shared_ptr<detail::ForecastReleaseState> release_;
  friend struct detail::ForecastFactory; // Defined only in the separately gated target.
};
// No permission factory, Model handle, constructor, metadata or rollout in stage 1.

struct BoundaryId { Count completed_tick = 0, completed_command_sequence = 0; };
struct State30 { JointVector q{}, v{}, C{}, w{}; double s = 0, r = 0; };
struct ObservedActual {
  JointVector q{}, v{}; BoundaryId boundary;
  std::string observation_id, transaction_id;
  double state_age_seconds = 0;
  bool completed = false, current_contact_free = false;
};
struct AcceptedCommandHistory {
  JointVector C{}, w{}, previous_alpha{}; BoundaryId boundary;
  std::string observation_id, transaction_id; bool completed = false;
};
struct ProgressHistory {
  double s = 0, r = 0, previous_b = 0; BoundaryId boundary;
  std::string observation_id, transaction_id; bool completed = false;
};
struct NominalAnchor { State30 point; BoundaryId boundary; };
struct CurrentBoundaryExpectation {
  BoundaryId boundary; std::string observation_id, transaction_id;
  double maximum_age_seconds = macro_dt;
  bool no_command_in_flight = false;
};
class LiveActualContext final {
 public:
  // Copy-only immutable value witness: moving cannot leave a stale valid-looking
  // state paired with empty profile/transaction identities.
  LiveActualContext(const LiveActualContext&) = default;
  LiveActualContext& operator=(const LiveActualContext&) = default;
  const State30& actualInitial() const noexcept { return actual_; }
  const JointVector& previousAlpha() const noexcept { return previous_alpha_; }
  double previousB() const noexcept { return previous_b_; }
  BoundaryId boundary() const noexcept { return boundary_; }
  const std::string& observationId() const noexcept { return observation_id_; }
  const std::string& transactionId() const noexcept { return transaction_id_; }
  const StaticDomainRanges& ranges() const noexcept { return ranges_; }
 private:
  LiveActualContext() = default;
  State30 actual_; JointVector previous_alpha_{}; double previous_b_ = 0;
  BoundaryId boundary_; StaticDomainRanges ranges_;
  std::string observation_id_, transaction_id_;
  friend LiveActualContext validateLiveActual(const ObservedActual&,
    const AcceptedCommandHistory&, const ProgressHistory&, const NominalAnchor&,
    const CurrentBoundaryExpectation&, const StaticDomainRanges&);
};
LiveActualContext validateLiveActual(const ObservedActual&,
  const AcceptedCommandHistory&, const ProgressHistory&, const NominalAnchor&,
  const CurrentBoundaryExpectation&, const StaticDomainRanges&);
enum class ContextInputSourceKindV1 {CallerObserverAssertions};
struct ContextValidationHistoryV1 {
  Count owned_scalar_slots=198,copied_scalar_slots=0,completed_input_groups=0;
  bool attempted=false,inputs_copied=false,validation_started=false,validation_returned=false;
  bool validated_copy_complete=false,complete=false,refused=false,ranges_copied=false,first_error_known=false;
  const char* stage="NOT_ATTEMPTED";std::string first_error;
};
namespace detail {struct ContextSnapshotData;struct ContextSnapshotFactory;}
class CapturedLiveActualContextV1 final {
 public:
  CapturedLiveActualContextV1(const CapturedLiveActualContextV1&)=default;CapturedLiveActualContextV1& operator=(const CapturedLiveActualContextV1&)=default;
  const ObservedActual& observedInput() const;const AcceptedCommandHistory& commandInput() const;const ProgressHistory& progressInput() const;
  const NominalAnchor& nominalInput() const;const CurrentBoundaryExpectation& currentInput() const;const StaticDomainRanges& inputRanges() const;
  const ContextValidationHistoryV1& history() const;ContextInputSourceKindV1 sourceKind() const;
 private:
  explicit CapturedLiveActualContextV1(std::shared_ptr<const detail::ContextSnapshotData>);
  const LiveActualContext& validatedContext() const;
  bool sameSource(const std::shared_ptr<const void>&,const SharedCaseBudget&) const;
  bool sameWitness(const CapturedLiveActualContextV1&) const;
  std::shared_ptr<const detail::ContextSnapshotData> data_;
  friend struct detail::ContextSnapshotFactory;friend struct detail::ForecastFactory;
};
namespace detail {
struct ContextSnapshotFactory {
 private:
  static CapturedLiveActualContextV1 captureAndValidate(SharedCaseBudget,std::shared_ptr<const void>,const ObservedActual&,const AcceptedCommandHistory&,const ProgressHistory&,const NominalAnchor&,const CurrentBoundaryExpectation&,const StaticDomainRanges&);
  friend struct ForecastFactory;
};
}
class AlgebraTestInitial final {
 public:
  const State30& point() const noexcept { return point_; }
 private:
  State30 point_;
  friend AlgebraTestInitial validateAlgebraTestInitial(const State30&);
};
AlgebraTestInitial validateAlgebraTestInitial(const State30&);
struct CommandProposal {
  JointVector C_next{}, w_next{}, alpha{}, implied_alpha{}, command_jerk_if_accepted{};
  double s_next = 0, r_next = 0, b = 0, progress_jerk = 0;
  std::array<double, 2> half_s_reference{}, half_r_reference{};
  BoundaryId from; // Preview only: no issued/accepted sequence or physical q/v.
};
CommandProposal first4msRequest(const LiveActualContext&,
                               const JointVector& candidate_alpha, double candidate_b);
} // namespace phase5_public_live_affine_v2
