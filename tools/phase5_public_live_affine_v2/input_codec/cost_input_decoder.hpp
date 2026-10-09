#pragma once
#include "quadratic_cost.hpp"
#include <memory>
#include <optional>
#include <string_view>
namespace phase5_public_live_affine_v2 {
namespace detail {struct CostDecoderState;struct CostInputFactory;}
struct CostDecodeObservation {
  NumericEncoding requested_output=NumericEncoding::LosslessBinary;
  std::optional<NumericEncoding> actual_input;
  Count physical_bytes_read=0,consumed_bytes=0,metadata_bytes=0;
  Count expected_scalars=0,delivered_scalars=0,parsed_terms=0,parsed_additions=0;
  Count active_term=0,active_addition=0,active_parent=0,header_initial_count=0;
  Count last_scalar_bits=0,last_scalar_byte_offset=0;
  Count pending_u64_bits=0,pending_u64_bytes=0,pending_u64_start=0;
  bool last_scalar_attempted=false,last_scalar_delivered=false,last_bits_valid=false,refused=false;
  bool header_complete=false,artifact_closed=false,hash_valid=false;
  std::string stage="NOT_OPENED",failure,physical_prefix_sha256,numeric_token_prefix;
};
class CostDecodeOutcome final {
 public:
  CostDecodeOutcome(const CostDecodeOutcome&)=delete;
  CostDecodeOutcome& operator=(const CostDecodeOutcome&)=delete;
  CostDecodeOutcome(CostDecodeOutcome&&) noexcept;
  CostDecodeOutcome& operator=(CostDecodeOutcome&&) noexcept;
  ~CostDecodeOutcome();
  bool hasCompleteCost() const noexcept;
  QuadraticCostOutcome& costOutcome();
  const AffineAssemblyOutcome& originalAssembly() const;
  const FileIdentity& requestedArtifact() const noexcept{return requested_;}
  // After transfer, complete/private descriptors live in the cost outcome.
  // Before transfer, this is the retained actually parsed prefix only.
  const std::vector<CostTermLayout>& parsedMetadataPrefix() const;
  CostDecodeObservation observation() const; // Bounded metadata only, no numeric array copy.
  std::string_view refusal() const noexcept;
 private:
  explicit CostDecodeOutcome(AffineAssemblyOutcome&&) noexcept;
  AffineAssemblyOutcome original_;FileIdentity requested_;
  std::shared_ptr<detail::CostDecoderState> state_;
  std::optional<QuadraticCostOutcome> cost_;std::string failure_;bool refused_=false;
  void refuse(const char*) noexcept;
  friend struct detail::CostInputFactory;
};
CostDecodeOutcome decodeAndBuildCost(AffineAssemblyOutcome&&,
                                    const InitialCostConsumer& consumer={});
// No CLI or output publisher. This function is source, not an execution release.
}
