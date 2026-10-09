#pragma once
#include "capture_leaves.hpp"
namespace phase5_public_live_affine_v2 {
namespace detail {struct MetadataBinding;struct ReferenceBinding;struct ObligationBinding;}
enum class MetadataKind {Utf8,U64,I64,Boolean,Ieee64Bits,NumericReference,Missing};
enum class ReferenceUse {NumericMetadata,NormalizedCell,NormalizedSample,NormalizedCycle,SampleRecipe,InitialSelector,CanonicalConcatenation};
struct LeafKey {RequiredRole role;Count primary=0,secondary=0;};
struct ReferenceFact {
  ReferenceUse use=ReferenceUse::NumericMetadata;Count index=0,part=0;
  LeafKey target{RequiredRole::ProvenanceAndMetadata,0,0};
  ChunkScalarKind kind=ChunkScalarKind::F64;
  Count rank=0,count=0,offset=0,source_count=0,destination_offset=0;
  std::array<Count,4> dimensions{};
  bool zero_block=false,empty_concatenation=false,source_valid=false,paired_verified=false,reconstruction_verified=false;
  bool requires_original_scope=false,requires_sample_scope=false;
  Count cell=0,cycle=0,half=0,tick=0;
};
struct MetadataFact {
  const char* family="";const char* field="";Count index=0,subindex=0;
  MetadataKind kind=MetadataKind::Missing;std::string_view text;
  Count unsigned_value=0;std::int64_t signed_value=0;bool boolean_value=false;
  ReferenceFact reference;
};
class MetadataLeafView final {
 public:
  MetadataLeafView(const MetadataLeafView&)=delete;MetadataLeafView& operator=(const MetadataLeafView&)=delete;
  const MetadataFact& fact() const;
  // Exact UTF8 JSON string bytes only, streamed synchronously. No file writer.
  // Charges actual encoded metadata bytes before each callback, not output bytes.
  void withJsonString(const std::function<void(std::string_view)>&) const;
 private:
  explicit MetadataLeafView(detail::MetadataBinding*);detail::MetadataBinding* binding_;
  friend struct detail::CaptureLeafFactory;
};
class ReferenceLeafView final {
 public:
  ReferenceLeafView(const ReferenceLeafView&)=delete;ReferenceLeafView& operator=(const ReferenceLeafView&)=delete;
  const ReferenceFact& fact() const;
 private:
  explicit ReferenceLeafView(detail::ReferenceBinding*);detail::ReferenceBinding* binding_;
  friend struct detail::CaptureLeafFactory;
};
enum class CoverageState {Missing,AbsentUpstream,UnsupportedCompound,UnknownShape,Unverified,VerifiedPrivateNumeric};
struct CoverageObligation {
  RequiredField required;CoverageState state=CoverageState::Missing;
  Count matching_attempts=0;const char* reason="MISSING_ACTUAL_PAIRED_ATTEMPT";
  bool full_capture_complete=false,full_flow_accepted=false;
};
class CoverageObligationView final {
 public:
  CoverageObligationView(const CoverageObligationView&)=delete;CoverageObligationView& operator=(const CoverageObligationView&)=delete;
  const CoverageObligation& obligation() const;
 private:
  explicit CoverageObligationView(detail::ObligationBinding*);detail::ObligationBinding* binding_;
  friend struct detail::CaptureLeafFactory;
};
using MetadataConsumer=std::function<void(const MetadataLeafView&)>;
using ReferenceConsumer=std::function<void(const ReferenceLeafView&)>;
using CoverageConsumer=std::function<void(const CoverageObligationView&)>;
// Borrowed facts and lossless descriptors do not serialize or prove reconstruction.
}
