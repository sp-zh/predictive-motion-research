#pragma once
#include "normalization.hpp"
#include <functional>
#include <memory>
#include <optional>
#include <string_view>

namespace phase5_public_live_affine_v2 {
enum class AssemblyInitialKind { LiveActual, AlgebraTest };
namespace detail { struct AffineStorage; struct AffineAnchor; struct AffineFactory; }
class SampleAffineView final {
 public:
  SampleAffineView(const SampleAffineView&) = delete;
  SampleAffineView& operator=(const SampleAffineView&) = delete;
  Count cell() const noexcept {return cell_;}
  Count tick() const noexcept {return tick_;}
  Count controlCount() const noexcept {return du_;}
  double offset(Count row) const;
  double actualOffset(Count row) const;
  double control(Count row,Count column) const;
  double initial(Count row,Count column) const;
 private:
  SampleAffineView(Count,Count,Count,const double*);
  Count cell_=0,tick_=0,du_=0;const double* work_=nullptr;
  friend struct detail::AffineFactory;
};
class CompactAffineAssembly final {
 public:
  CompactAffineAssembly(const CompactAffineAssembly&) = delete;
  CompactAffineAssembly& operator=(const CompactAffineAssembly&) = delete;
  CompactAffineAssembly(CompactAffineAssembly&&) noexcept;
  CompactAffineAssembly& operator=(CompactAffineAssembly&&) noexcept;
  ~CompactAffineAssembly();
  bool complete() const noexcept;
  Count cells() const;
  Count dx() const;
  Count du() const;
  Count dy() const;
  AssemblyInitialKind initialKind() const;
  CaptureMode mode() const;
  double chosenInitial(Count coordinate) const;
  double boundaryOffset(Count cell,Count row) const;
  double boundaryControl(Count cell,Count row,Count column) const;
  double boundaryInitial(Count cell,Count row,Count column) const;
  double embeddingControl(Count row,Count column) const;
  double embeddingOffset(Count row) const;
  double embeddingInitial(Count row,Count column) const; // P blocks plus zero U block.
  // Callback-only borrowed view. Reentry, quota and callback failures poison the
  // complete assembly; original normalized/raw provenance remains retained.
  void withSample(Count index,const std::function<void(const SampleAffineView&)>&);
  std::string_view refusal() const noexcept;
  // DenseAudit getters refuse in Compact; no silent reinterpretation/fallback.
  double liftedL(Count row,Count column) const;
  double liftedE(Count row,Count column) const;
  double liftedOffset(Count row) const;
  double liftedInitialSelector(Count row,Count column) const;
  double eliminatedControl(Count row,Count column) const;
  double eliminatedOffset(Count row) const;
  double eliminatedInitial(Count row,Count column) const;
  double sampleDenseSelector(Count sample,Count row,Count column) const;
  double auditSampleControl(bool eliminated,Count sample,Count row,Count column) const;
  double auditSampleOffset(bool eliminated,Count sample,Count row) const;
  double auditSampleInitial(bool eliminated,Count sample,Count row,Count column) const;
  const NormalizationOutcome& originalNormalization() const;
  static const std::array<bool,7>& scopeClaims() noexcept;
 private:
  explicit CompactAffineAssembly(std::unique_ptr<detail::AffineStorage>);
  std::unique_ptr<detail::AffineStorage> storage_;
  friend struct detail::AffineFactory;
};
class AffineAssemblyOutcome final {
 public:
  AffineAssemblyOutcome(const AffineAssemblyOutcome&) = delete;
  AffineAssemblyOutcome& operator=(const AffineAssemblyOutcome&) = delete;
  AffineAssemblyOutcome(AffineAssemblyOutcome&&) noexcept;
  AffineAssemblyOutcome& operator=(AffineAssemblyOutcome&&) noexcept;
  ~AffineAssemblyOutcome();
  bool hasCompleteAssembly() const noexcept;
  CompactAffineAssembly& assembly();
  const NormalizationOutcome& originalNormalization() const;
  CaptureMode requestedMode() const noexcept {return requested_;}
  std::optional<CaptureMode> actualMode() const noexcept;
  AssemblyInitialKind initialKind() const noexcept {return kind_;}
  std::string_view refusal() const noexcept;
 private:
  AffineAssemblyOutcome(NormalizationOutcome&&,CaptureMode,AssemblyInitialKind) noexcept;
  void recordRefusal(const char*) noexcept;
  NormalizationOutcome original_;std::shared_ptr<detail::AffineAnchor> anchor_;
  std::unique_ptr<CompactAffineAssembly> assembly_;
  CaptureMode requested_;AssemblyInitialKind kind_;std::string refusal_detail_;bool refused_=false;
  friend struct detail::AffineFactory;
};
AffineAssemblyOutcome assembleLiveAffine(NormalizationOutcome&&,CaptureMode requested);
AffineAssemblyOutcome assembleAlgebraAffine(NormalizationOutcome&&,const AlgebraTestInitial&,CaptureMode requested);
// No costs, capture/reader, solver, controller request, Model call or phase gate.
} // namespace phase5_public_live_affine_v2
