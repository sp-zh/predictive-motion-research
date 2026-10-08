#pragma once
#include "model_boundary.hpp"
#include <array>
#include <memory>
#include <string_view>
#include <vector>

namespace phase5_public_live_affine_v2 {
namespace detail { struct RawAnchor; struct NormalizedInventory; struct NormalizationFactory; }
// Native cumulative nominal coefficient view, not a finite-neighborhood or
// execution certificate. Every reference keeps the genuine raw owner alive.
class NormalizedBlockView final {
 public:
  NormalizedBlockView(const NormalizedBlockView&) = delete;
  NormalizedBlockView& operator=(const NormalizedBlockView&) = delete;
  NormalizedBlockView(NormalizedBlockView&&) noexcept = default;
  NormalizedBlockView& operator=(NormalizedBlockView&&) noexcept = default;
  Count cell() const;
  Count cycle() const;
  Count half() const;
  Count physicalTick() const;
  Count sampleIndex() const; // Only meaningful for sample views.
  const Eigen::MatrixXd& A() const;
  const Eigen::MatrixXd& B() const;
  const Eigen::VectorXd& defect() const;
  const phase5_public_coupled_augmented::State& nominalOrigin() const;
  const phase5_public_coupled_augmented::State& nominalEndpoint() const;
  const Eigen::VectorXd& nominalInput() const;
 private:
  NormalizedBlockView(std::shared_ptr<detail::RawAnchor>,bool sample,Count index);
  const phase5_public_coupled_augmented_extension::Map& native() const;
  std::shared_ptr<detail::RawAnchor> anchor_;
  bool sample_ = false;
  Count index_=0; // Remaining3/5 logical topology fields reference/derive from raw.
  friend struct detail::NormalizationFactory;
};
class NormalizedNominalMaps final {
 public:
  NormalizedNominalMaps(const NormalizedNominalMaps&) = delete;
  NormalizedNominalMaps& operator=(const NormalizedNominalMaps&) = delete;
  NormalizedNominalMaps(NormalizedNominalMaps&&) noexcept;
  NormalizedNominalMaps& operator=(NormalizedNominalMaps&&) noexcept;
  ~NormalizedNominalMaps();
  const std::vector<NormalizedBlockView>& cells() const;
  const std::vector<NormalizedBlockView>& samples() const;
  Count cycleCount() const;
  const Eigen::MatrixXd& cycleA(Count) const;
  const Eigen::MatrixXd& cycleB(Count) const;
  const Eigen::VectorXd& cycleDefect(Count) const;
  const phase5_public_coupled_augmented::State& cycleOrigin(Count) const;
  const phase5_public_coupled_augmented::State& cycleEndpoint(Count) const;
  Count cycleCell(Count) const;
  const OwnedPublicForecast& originalForecast() const;
  static const std::array<bool,7>& scopeClaims() noexcept; // Fixed all false.
 private:
  explicit NormalizedNominalMaps(std::unique_ptr<detail::NormalizedInventory>);
  std::unique_ptr<detail::NormalizedInventory> storage_;
  friend struct detail::NormalizationFactory;
};
class NormalizationOutcome final {
 public:
  NormalizationOutcome(const NormalizationOutcome&) = delete;
  NormalizationOutcome& operator=(const NormalizationOutcome&) = delete;
  NormalizationOutcome(NormalizationOutcome&&) noexcept;
  NormalizationOutcome& operator=(NormalizationOutcome&&) noexcept;
  ~NormalizationOutcome();
  bool hasFullNominalMaps() const noexcept;
  const NormalizedNominalMaps& maps() const;
  const OwnedPublicForecast& originalForecast() const;
  std::string_view refusal() const noexcept;
 private:
  explicit NormalizationOutcome(OwnedPublicForecast&&) noexcept;
  void recordRefusal(const char*) noexcept;
  OwnedPublicForecast original_; // Refusal outcome requires no new heap wrapper.
  std::shared_ptr<detail::RawAnchor> anchor_;
  std::unique_ptr<NormalizedNominalMaps> maps_;
  std::string refusal_detail_;bool refused_=false;
  friend struct detail::NormalizationFactory;
};
// Zero extra Model calls. Failed/incomplete/unsupported/overquota outcomes own
// original data and emit no full maps/cost/controller request.
NormalizationOutcome normalizePublic(OwnedPublicForecast&&);
} // namespace phase5_public_live_affine_v2
