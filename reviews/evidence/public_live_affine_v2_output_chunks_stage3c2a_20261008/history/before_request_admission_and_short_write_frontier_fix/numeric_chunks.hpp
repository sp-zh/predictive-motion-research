#pragma once
#include "foundation.hpp"
#include <functional>
#include <optional>
#include <string_view>
namespace phase5_public_live_affine_v2 {
enum class ChunkScalarKind {F64=1,U64=2,I64=3,FailureF64Bits=4};
enum class ChunkClassification {FiniteFields,ForensicDefinedFields};
struct ChunkScalar {
  ChunkScalarKind kind=ChunkScalarKind::U64;Count bits=0;
  static ChunkScalar f64(double);
  static ChunkScalar u64(Count);
  static ChunkScalar i64(std::int64_t);
  static ChunkScalar failureF64Bits(Count);
};
struct NumericChunkSpec {
  std::string relative_name,role;
  ChunkScalarKind kind=ChunkScalarKind::F64;
  ChunkClassification classification=ChunkClassification::FiniteFields;
  std::vector<Count> dimensions; // At most4; empty means one scalar.
};
struct NumericChunkRecord {
  NumericChunkSpec spec;NumericEncoding encoding=NumericEncoding::LosslessBinary;
  Count count=0,bytes=0,device=0,inode=0;std::string sha256;
  bool closed_fsynced=false;
};
struct ChunkIOObservation {
  const char* stage="NOT_OPENED";
  Count attempted_index=0,encoded_or_decoded=0,physical_bytes=0,consumed_bytes=0,pending_bytes=0;
  Count last_scalar_bits=0;bool last_bits_valid=false,hash_valid=false,refused=false;
  std::string first_error,physical_prefix_sha256;
};
struct ChunkWriteOutcome {
  NumericChunkRecord record;ChunkIOObservation observation;
  bool closedChunk() const noexcept{return !observation.refused&&record.closed_fsynced;}
};
struct ChunkReadOutcome {
  ChunkIOObservation observation;std::string observed_sha256;
  bool exact_readback=false;
};
using ChunkScalarSource=std::function<ChunkScalar(Count)>;
using ChunkScalarObserver=std::function<void(Count,const ChunkScalar&)>;
ChunkWriteOutcome writeProvisionalNumericChunk(SharedCaseBudget,const std::string& absolute_root,
                                              const NumericChunkSpec&,const ChunkScalarSource&);
ChunkReadOutcome readbackNumericChunk(SharedCaseBudget,const std::string& absolute_root,
                                     const NumericChunkRecord&,const ChunkScalarObserver& observer={});
// No root CAPTURE_READY, inventory acceptance, controller or Model authority.
}
