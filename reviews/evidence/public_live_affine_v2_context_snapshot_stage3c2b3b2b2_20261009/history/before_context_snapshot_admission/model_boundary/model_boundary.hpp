#pragma once
#include "foundation.hpp"
#include "public_coupled_augmented_extension.hpp"
#include <memory>
#include <string>
#include <string_view>
#include <vector>

namespace phase5_public_live_affine_v2 {
using RawResult = phase5_public_coupled_augmented_extension::Result;
using NativeMetadata = phase5_public_coupled_v2::ModelMetadata;
// The expected review digest must come from the separately reviewed dispatch.
// A caller-chosen digest is not evidence of human/reviewer authorization.
struct ReviewPins { std::string review_record_path, review_record_sha256; };
struct NominalControl { JointVector alpha{}; double b = 0; };
namespace detail {
struct InvocationStorage; struct HandleStorage; struct ForecastStorage;
struct OpenStorage; struct NormalizationFactory;
}
class OwnedLiveInvocation final {
 public:
  OwnedLiveInvocation(const OwnedLiveInvocation&) = delete;
  OwnedLiveInvocation& operator=(const OwnedLiveInvocation&) = delete;
  OwnedLiveInvocation(OwnedLiveInvocation&&) noexcept;
  OwnedLiveInvocation& operator=(OwnedLiveInvocation&&) noexcept;
  ~OwnedLiveInvocation();
  const LiveActualContext& actualContext() const;
  const CycleMesh& mesh() const;
  const std::vector<phase5_public_coupled_augmented::Cell>& nativeCells() const;
  const std::string& invocationSha256() const;
  const ResourcePlan& resourcePlan() const;
 private:
  explicit OwnedLiveInvocation(std::shared_ptr<detail::InvocationStorage>);
  std::shared_ptr<detail::InvocationStorage> storage_;
  friend struct detail::ForecastFactory;
};
class PinnedModelHandle final {
 public:
  PinnedModelHandle(const PinnedModelHandle&) = delete;
  PinnedModelHandle& operator=(const PinnedModelHandle&) = delete;
  PinnedModelHandle(PinnedModelHandle&&) noexcept;
  PinnedModelHandle& operator=(PinnedModelHandle&&) noexcept;
  ~PinnedModelHandle();
  bool hasLiveModel() const noexcept;
  const NativeMetadata& verifiedMetadata() const;
  const std::vector<FileIdentity>& verifiedFiles() const;
  const FileIdentity& currentProducerIdentity() const;
  const FileIdentity& reviewRecordIdentity() const;
  const FileIdentity& protocolIdentity() const;
 private:
  explicit PinnedModelHandle(std::unique_ptr<detail::HandleStorage>);
  std::unique_ptr<detail::HandleStorage> storage_;
  friend struct detail::ForecastFactory;
};
class ModelOpenOutcome final {
 public:
  ModelOpenOutcome(const ModelOpenOutcome&) = delete;
  ModelOpenOutcome& operator=(const ModelOpenOutcome&) = delete;
  ModelOpenOutcome(ModelOpenOutcome&&) noexcept;
  ModelOpenOutcome& operator=(ModelOpenOutcome&&) noexcept;
  ~ModelOpenOutcome();
  bool hasModel() const;
  PinnedModelHandle& model();
  const std::string& refusal() const;
  bool constructorAttempted() const;
  bool metadataAttempted() const;
  const NativeMetadata* observedMetadata() const; // Complete, including mismatch.
 private:
  explicit ModelOpenOutcome(std::unique_ptr<detail::OpenStorage>);
  std::unique_ptr<detail::OpenStorage> storage_;
  friend struct detail::ForecastFactory;
};
struct ReleaseAttemptFacts {Count prepare=0,open=0,forecast=0,constructor=0,metadata=0,rollout=0;};
enum class VerifiedMemberGroup {Protocol,SourceClosure,SDKClosure,InvocationCost};
struct VerifiedMemberRelation {
  Count file_index=0,parent_index=0,native_ordinal=0,declared_loaded_ordinal=0;
  VerifiedMemberGroup group=VerifiedMemberGroup::Protocol;
  bool parent_is_protocol=false,declared_loaded=false,verified=false;
}; //8 real logical fields; FileIdentity.bytes adds1 per actual file.
enum class MemberIdentityTargetKind {NotCaptured,Review,Protocol,Producer,MemberFile,DeclaredLibrary,CostInput};
struct MemberLoaderObservationV1 {const char* stage="NOT_ATTEMPTED";Count libraries_checked=0,current_library_index=0,lines=0,inode=0,major_id=0,minor_id=0;bool current_library_known=false,parsed=false,mapped=false,refused=false;};
struct MemberCaptureStatus {Count expected_files=0,actual_files=0,declared_libraries=0,verified_loader_checks=0,active_file_index=0,active_native_ordinal=0,active_parent_index=0;VerifiedMemberGroup active_group=VerifiedMemberGroup::Protocol;bool active_member_known=false;MemberIdentityTargetKind identity_target_kind=MemberIdentityTargetKind::NotCaptured;Count identity_target_index=0;bool identity_target_known=false;bool admitted=false,complete=false,refused=false;std::string first_error;};
class OwnedPublicForecast final {
 public:
  OwnedPublicForecast(const OwnedPublicForecast&) = delete;
  OwnedPublicForecast& operator=(const OwnedPublicForecast&) = delete;
  OwnedPublicForecast(OwnedPublicForecast&&) noexcept;
  OwnedPublicForecast& operator=(OwnedPublicForecast&&) noexcept;
  ~OwnedPublicForecast();
  const RawResult* originalResult() const; // Never a fabricated empty success.
  const std::string& transportFailure() const;
  const std::string& structuralRefusal() const;
  const LiveActualContext& actualContext() const;
  const CycleMesh& mesh() const;
  const std::vector<phase5_public_coupled_augmented::Cell>& nativeCells() const;
  const std::string& invocationSha256() const;
  const NativeMetadata& verifiedMetadata() const;
  const std::vector<FileIdentity>& verifiedFiles() const;
  const FileIdentity& currentProducerIdentity() const;
  const FileIdentity& reviewRecordIdentity() const;
  const FileIdentity& protocolIdentity() const;
  std::string_view verifiedArtifactRole(Count index) const;
  bool hasVerifiedMemberCapture() const noexcept;
  const VerifiedMemberRelation& verifiedMemberRelation(Count) const;
  const FileIdentity& verifiedMemberParent(Count) const;
  const MemberCaptureStatus* memberCaptureStatus() const;
  const MemberIdentityObservationV1* memberIdentityObservation() const;
  const MemberLoaderObservationV1* memberLoaderObservation() const;
  Count retainedMemberCount() const;
  std::string_view retainedMemberRole(Count) const;
  const VerifiedMemberRelation& retainedMemberRelation(Count) const;
  const FileIdentity& retainedMemberParent(Count) const;
  const std::vector<FileIdentity>& verifiedLoadedLibraries() const;
  std::string_view reviewedAttemptClaimPath() const;
  ReleaseAttemptFacts releaseAttemptFacts() const;
  std::string_view verifiedUnits() const;
  std::string_view verifiedCertificateName() const;

 private:
  CaseBudget& normalizationBudget();
  const ResourcePlan& normalizationPlan() const;
  const char* normalizationCertificate() const;
  const FactorShape& costShape() const;
  const FileIdentity& costInputIdentity() const;
  const std::string& costSemanticSha256() const;
  explicit OwnedPublicForecast(std::unique_ptr<detail::ForecastStorage>);
  std::unique_ptr<detail::ForecastStorage> storage_;
  friend struct detail::ForecastFactory;
  friend struct detail::NormalizationFactory;
};

// Hash/parse preflight only. These source functions do NOT release a run; future
// execution also requires the external reviewed protocol/dispatch and new freeze.
ReviewedForecastPermission loadReviewedForecastPermission(const ReviewPins&);
ReviewedForecastPermission loadReviewedForecastPermissionWithMemberCaptureV2(const ReviewPins&,BatchBudget&);
OwnedLiveInvocation prepareFrozenLiveInvocation(ReviewedForecastPermission&,
                                                const LiveActualContext&, BatchBudget&);
// Actual ctor/query/rollout appear only behind a validated, single-use release.
ModelOpenOutcome openPinnedModel(ReviewedForecastPermission&, OwnedLiveInvocation&);
OwnedPublicForecast forecastPublic(PinnedModelHandle&, OwnedLiveInvocation&&);
// No archived/native-carrier or AlgebraTest factory can create these witnesses.
// Normalization is a separate target; complete capture/readers remain later.
} // namespace phase5_public_live_affine_v2
