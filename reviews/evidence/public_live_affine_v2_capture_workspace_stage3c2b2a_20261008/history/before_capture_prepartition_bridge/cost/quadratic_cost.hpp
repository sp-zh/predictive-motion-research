#pragma once
#include "affine_assembly.hpp"
#include <functional>
#include <memory>
#include <utility>
#include <string_view>
#include <vector>

namespace phase5_public_live_affine_v2 {
struct SampleAdditionLayout {Count sample_index=0;std::vector<Count> parent_rows;};
struct CostTermLayout {
  std::string name,units;Count rows=0;
  std::vector<SampleAdditionLayout> additions;
};
// Reader contract: bounded scalar access to the reviewed opaque input; no
// retained unbudgeted numerical arrays. Complete codecs belong to SOURCE3C.
// Scalar order is specified in INPUT_CONTRACT.md. Read exactly once on ingest.
namespace detail {struct CostInputFactory;struct CostFactory;struct CaptureInventoryFactory;}
struct CostInputRecipe {
 private:
  std::shared_ptr<OwnedReservation> owned_input_; // Dies after public metadata/cache callbacks.
  CaseBudget* owned_budget_=nullptr;Count owned_topology_=0,owned_cache_=0;
  void admitOwnedInput(CaseBudget&,Count topology,Count byte_cache_slots);
  friend struct detail::CostInputFactory;
  friend struct detail::CostFactory;
 public:
  CostInputRecipe()=default;
  CostInputRecipe(FileIdentity f,std::vector<CostTermLayout> t,std::function<double(Count)> r)
    :file(std::move(f)),terms(std::move(t)),read_scalar(std::move(r)){}
  CostInputRecipe(const CostInputRecipe&)=delete;
  CostInputRecipe& operator=(const CostInputRecipe&)=delete;
  CostInputRecipe(CostInputRecipe&&) noexcept=default;
  CostInputRecipe& operator=(CostInputRecipe&&) noexcept;
  FileIdentity file;std::vector<CostTermLayout> terms;
  std::function<double(Count scalar_index)> read_scalar;
  std::function<void()> finish_read; // Exact decoder EOF/SHA closure before complete cost.
};
namespace detail {struct CostStorage;struct CostAnchor;struct CostFactory;}
class CostEvaluationView final {
 public:
  CostEvaluationView(const CostEvaluationView&)=delete;
  CostEvaluationView& operator=(const CostEvaluationView&)=delete;
  double directValue() const;
  double condensedValue() const;
  double directGradient(Count) const;
  double condensedGradient(Count) const;
  double directHessian(Count,Count) const;
  double condensedHessian(Count,Count) const;
 private:
  std::shared_ptr<const void> captureOriginToken() const;
  bool originalConsumerScope() const;
  std::shared_ptr<const void> captureCostToken() const;
  explicit CostEvaluationView(detail::CostStorage*);
  detail::CostStorage* storage_=nullptr;
  friend struct detail::CostFactory;
  friend class UsedTermView;
  friend struct detail::CaptureInventoryFactory;
};
class UsedTermView final {
 public:
  UsedTermView(const UsedTermView&)=delete;
  UsedTermView& operator=(const UsedTermView&)=delete;
  Count termIndex() const noexcept{return term_;}
  Count rows() const;
  double usedFactor(Count,Count) const;
  double usedOffset(Count) const;
  double usedLinear(Count) const;
  double usedConstant() const;
  double factorControl(Count,Count) const;
  double factorOffset(Count) const;
  double rawH(Count,Count) const;
  double gradientCoefficient(Count) const;
  double constantCoefficient() const;
  const CostEvaluationView& evaluation() const noexcept{return evaluation_;}
 private:
  std::shared_ptr<const void> captureOriginToken() const;
  bool originalConsumerScope() const;
  std::shared_ptr<const void> captureCostToken() const;
  UsedTermView(detail::CostStorage*,Count);
  detail::CostStorage* storage_=nullptr;Count term_=0;CostEvaluationView evaluation_;
  friend struct detail::CostFactory;
  friend struct detail::CaptureInventoryFactory;
};
// Borrow complete fields during their original calculation, with no replay.
// No files/codecs are implemented here. Throwing refuses the whole outcome.
struct InitialCostConsumer {
  std::function<void(const UsedTermView&)> term;
  std::function<void(const CostEvaluationView&)> canonical;
};
class CompleteQuadraticCost final {
 public:
  CompleteQuadraticCost(const CompleteQuadraticCost&)=delete;
  CompleteQuadraticCost& operator=(const CompleteQuadraticCost&)=delete;
  CompleteQuadraticCost(CompleteQuadraticCost&&) noexcept;
  CompleteQuadraticCost& operator=(CompleteQuadraticCost&&) noexcept;
  ~CompleteQuadraticCost();
  bool complete() const noexcept;
  Count termCount() const;
  const std::vector<CostTermLayout>& inputLayouts() const;
  const FileIdentity& inputIdentity() const;
  const std::string& inputSemanticSha256() const;
  double inputFactor(Count term,Count row,Count column) const;
  double inputOffset(Count term,Count row) const;
  double inputLinear(Count term,Count column) const;
  double inputConstant(Count term) const;
  double inputAdditionCoefficient(Count term,Count addition,Count row,Count column) const;
  double evaluationControl(Count column) const;
  double sumRawH(Count,Count) const;
  double sumGradientCoefficient(Count) const;
  double sumConstantCoefficient() const;
  double sumLinear(Count) const;
  double sumInputConstant() const;
  double sumFactorControl(Count row,Count column) const; // Ordered term concatenation.
  double sumFactorOffset(Count row) const;
  // Whole actually computed used factors and every evaluation entry are exposed
  // in bounded callbacks. Sum used factors concatenate withTerm chunks in order.
  void withTerm(Count,const std::function<void(const UsedTermView&)>&);
  void withCanonicalEvaluation(const std::function<void(const CostEvaluationView&)>&);
  std::string_view refusal() const noexcept;
  const AffineAssemblyOutcome& originalAssembly() const;
  static const std::array<bool,7>& scopeClaims() noexcept;
 private:
  explicit CompleteQuadraticCost(std::unique_ptr<detail::CostStorage>);
  std::unique_ptr<detail::CostStorage> storage_;
  friend struct detail::CostFactory;
  friend class QuadraticCostOutcome;
};
class QuadraticCostOutcome final {
 public:
  QuadraticCostOutcome(const QuadraticCostOutcome&)=delete;
  QuadraticCostOutcome& operator=(const QuadraticCostOutcome&)=delete;
  QuadraticCostOutcome(QuadraticCostOutcome&&) noexcept;
  QuadraticCostOutcome& operator=(QuadraticCostOutcome&&) noexcept;
  ~QuadraticCostOutcome();
  bool hasCompleteCost() const noexcept;
  CompleteQuadraticCost& cost();
  const AffineAssemblyOutcome& originalAssembly() const;
  // Authoritative sealed descriptor; read_scalar is deliberately empty.
  // Refuses if construction failed before a snapshot was admitted.
  const CostInputRecipe& originalInputRecipe() const;
  // Forensic moved request, potentially still caller-aliased; never authority.
  const CostInputRecipe& forensicInputRecipe() const;
  std::string_view refusal() const noexcept;
  bool hasRetainedRegions() const noexcept;
  void withRetainedRegions(const RetainedRegionConsumer&) const;
 private:
  std::shared_ptr<const void> captureCostToken() const;
  QuadraticCostOutcome(AffineAssemblyOutcome&&,CostInputRecipe&&) noexcept;
  void recordRefusal(const char*) noexcept;
  AffineAssemblyOutcome original_;CostInputRecipe input_;
  std::shared_ptr<detail::CostAnchor> anchor_;std::unique_ptr<CompleteQuadraticCost> cost_;
  std::unique_ptr<detail::CostStorage> failed_; // Initialized partial data retained for future capture.
  std::string reason_;bool refused_=false;
  friend struct detail::CostFactory;
  friend struct detail::CaptureInventoryFactory;
};
QuadraticCostOutcome buildQuadraticCost(AffineAssemblyOutcome&&,CostInputRecipe&&);
QuadraticCostOutcome buildQuadraticCost(AffineAssemblyOutcome&&,CostInputRecipe&&,
                                      const InitialCostConsumer&);
// No weights selected, no codec/solver/controller/Model/phase permission emitted.
} // namespace phase5_public_live_affine_v2
