#pragma once
#include "foundation.hpp"
#include "public_coupled_augmented_extension.hpp"
#include <memory>
#include <string>
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
struct OpenStorage;
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
 private:
  explicit OwnedPublicForecast(std::unique_ptr<detail::ForecastStorage>);
  std::unique_ptr<detail::ForecastStorage> storage_;
  friend struct detail::ForecastFactory;
};

// Hash/parse preflight only. These source functions do NOT release a run; future
// execution also requires the external reviewed protocol/dispatch and new freeze.
ReviewedForecastPermission loadReviewedForecastPermission(const ReviewPins&);
OwnedLiveInvocation prepareFrozenLiveInvocation(ReviewedForecastPermission&,
                                                const LiveActualContext&, BatchBudget&);
// Actual ctor/query/rollout appear only behind a validated, single-use release.
ModelOpenOutcome openPinnedModel(ReviewedForecastPermission&, OwnedLiveInvocation&);
OwnedPublicForecast forecastPublic(PinnedModelHandle&, OwnedLiveInvocation&&);
// No archived/native-carrier or AlgebraTest factory can create these witnesses.
// Normalization and complete capture/readers are deliberately a later stage.
} // namespace phase5_public_live_affine_v2
