#include "chunk_io.hpp"
#include <algorithm>
#include <charconv>
#include <cmath>
#include <cerrno>
namespace phase5_public_live_affine_v2 {
namespace {
using namespace chunk_detail;
struct Writer {
  SharedCaseBudget budget;OwnedReservation ticket;std::unique_ptr<std::array<unsigned char,128>> cache;
  FD root,file;SHA hash;ChunkWriteOutcome& out;const ChunkIOLease& lease;Count pending=0,header_bytes=0;bool metadata=true;
  Writer(SharedCaseBudget b,ChunkWriteOutcome& o,const ChunkIOLease& lock):budget(std::move(b)),ticket(budget.reserve(20)),cache(std::make_unique<std::array<unsigned char,128>>()),out(o),lease(lock){out.observation.hash_valid=true;}
  void flush(){lease.requireHealthy();if(!pending)return;out.observation.stage="WRITE_PROVISIONAL_BYTES";
    budget.chargeScratchOrCopy(16); // Owned cache reuse, before IO.
    const Count projected=add(budget.outputBytes(),pending);need(projected<=budget.outputCeiling()&&projected<=ResourcePolicyV2::output_bytes,"chunk aggregate output quota before write");
    if(metadata)need(add(budget.metadataBytes(),pending)<=ResourcePolicyV2::metadata_bytes,"chunk aggregate metadata quota before write");
    Count offset=0;while(offset<pending){ssize_t n;do{n=::write(file.value,cache->data()+offset,static_cast<std::size_t>(pending-offset));}while(n<0&&errno==EINTR);
      need(n>0,"chunk write error/zero write");const Count actual=static_cast<Count>(n);
      out.record.bytes=add(out.record.bytes,actual);out.observation.physical_bytes=out.record.bytes;
      budget.chargeUniqueOutputBytes(actual);if(metadata)budget.chargeMetadataBytes(actual);
      const Count start=offset;offset=add(offset,actual);out.observation.pending_bytes=pending-offset;
      out.observation.hash_valid=false;hash.update(cache->data()+start,static_cast<std::size_t>(actual));out.observation.hash_valid=true;
    }pending=0;out.observation.pending_bytes=0;
  }
  void byte(unsigned char c){(*cache)[static_cast<std::size_t>(pending++)]=c;out.observation.pending_bytes=pending;if(pending==cache->size())flush();}
  void text(const std::string& s){for(unsigned char c:s)byte(c);}
  void u64le(Count n){for(unsigned j=0;j<8;++j)byte(static_cast<unsigned char>((n>>(8*j))&255));}
  template<class T>void decimal(T value){std::array<char,32> token{};const auto result=std::to_chars(token.data(),token.data()+token.size(),value);
    need(result.ec==std::errc{},"integer chunk format range");for(auto* p=token.data();p<result.ptr;++p)byte(static_cast<unsigned char>(*p));}
  void header(){out.observation.stage="ENCODE_TYPED_HEADER";
    if(out.record.encoding==NumericEncoding::LosslessBinary){text("P5NUMCHUNK000001");u64le(static_cast<Count>(out.record.spec.kind));u64le(0x0102030405060708ULL);u64le(out.record.count);}
    else {text("{\"schema\":\"PUBLIC_LIVE_AFFINE_V2_NUMERIC_CHUNK_JSON_1\",\"type\":\"");text(typeName(out.record.spec.kind));text("\",\"count\":");decimal(out.record.count);text(",\"values\":[");}
    flush();header_bytes=out.record.bytes;metadata=false;
  }
  void scalar(const ChunkScalar& value,Count index){
    need(value.kind==out.record.spec.kind,"chunk source scalar type differs");out.observation.last_scalar_bits=value.bits;out.observation.last_bits_valid=true;
    if(value.kind==ChunkScalarKind::F64)need(std::isfinite(asDouble(value.bits)),"nonfinite finite-field chunk scalar");
    if(out.record.encoding==NumericEncoding::LosslessBinary)u64le(value.bits);
    else {if(index)byte(',');switch(value.kind){
      case ChunkScalarKind::F64:{std::array<char,32> token{};const auto r=std::to_chars(token.data(),token.data()+token.size(),asDouble(value.bits),std::chars_format::general,std::numeric_limits<double>::max_digits10);
        need(r.ec==std::errc{},"f64 numeric JSON format error");for(auto* p=token.data();p<r.ptr;++p)byte(static_cast<unsigned char>(*p));break;}
      case ChunkScalarKind::U64:decimal(value.bits);break;
      case ChunkScalarKind::I64:decimal(asSigned(value.bits));break;
      case ChunkScalarKind::FailureF64Bits:{constexpr char hex[]="0123456789abcdef";byte('"');for(int j=15;j>=0;--j)byte(static_cast<unsigned char>(hex[(value.bits>>(4*j))&15]));byte('"');break;}
    }}
  }
  void finish(){out.observation.stage="CLOSE_TYPED_CHUNK";
    if(out.record.encoding==NumericEncoding::FullNumericJson){byte(']');byte('}');}flush();
    struct stat st{};need(::fstat(file.value,&st)==0&&S_ISREG(st.st_mode)&&st.st_nlink==1&&st.st_size>=0&&static_cast<Count>(st.st_size)==out.record.bytes&&
      static_cast<Count>(st.st_dev)==out.record.device&&static_cast<Count>(st.st_ino)==out.record.inode,"written chunk FD identity/size changed");
    if(out.record.encoding==NumericEncoding::LosslessBinary)need(out.record.bytes==add(40,mul(out.record.count,8)),"binary chunk exact byte shape");
    need(::fsync(file.value)==0,"provisional chunk fsync failed");out.observation.stage="FSYNC_DIRECTORY";need(::fsync(root.value)==0,"provisional root fsync failed");
    out.record.sha256=hash.digest();out.record.closed_fsynced=true;out.observation.physical_prefix_sha256=out.record.sha256;out.observation.stage="CLOSED_PROVISIONAL_CHUNK";
  }
};
}
ChunkScalar ChunkScalar::f64(double d){Count n;static_assert(sizeof(d)==8,"f64 required");std::memcpy(&n,&d,8);return {ChunkScalarKind::F64,n};}
ChunkScalar ChunkScalar::u64(Count n){return {ChunkScalarKind::U64,n};}
ChunkScalar ChunkScalar::i64(std::int64_t n){Count bits;std::memcpy(&bits,&n,8);return {ChunkScalarKind::I64,bits};}
ChunkScalar ChunkScalar::failureF64Bits(Count n){return {ChunkScalarKind::FailureF64Bits,n};}
ChunkWriteOutcome writeProvisionalNumericChunk(SharedCaseBudget budget,const std::string& absolute_root,const NumericChunkSpec& request,const ChunkScalarSource& source){
  ChunkWriteOutcome out;std::optional<ChunkIOLease> lease;std::unique_ptr<Writer> writer;
  try{out.observation.stage="ADMIT_CHUNK_STORAGE";lease.emplace(budget.beginChunkIO());writer=std::make_unique<Writer>(std::move(budget),out,*lease);
    out.record.count=chunk_detail::sealSpec(request);out.record.spec=request;
    need(!absolute_root.empty()&&absolute_root[0]=='/'&&absolute_root.size()<=4096&&absolute_root.find('\0')==std::string::npos,"bounded root path required before copy");out.record.root_path=absolute_root;out.record.encoding=writer->budget.numericEncoding();
    need(out.record.encoding==NumericEncoding::LosslessBinary||out.record.encoding==NumericEncoding::FullNumericJson,"unknown frozen encoding/no fallback");
    const ChunkScalarSource read=source;need(static_cast<bool>(read),"chunk scalar source absent");
    out.observation.stage="OPEN_SAFE_ROOT";writer->root.value=directory(out.record.root_path);struct stat dir{};need(::fstat(writer->root.value,&dir)==0&&S_ISDIR(dir.st_mode),"actual root FD not directory");
    out.record.directory_device=static_cast<Count>(dir.st_dev);out.record.directory_inode=static_cast<Count>(dir.st_ino);
    out.observation.stage="CREATE_FIRST_PROVISIONAL";writer->file.value=::openat(writer->root.value,out.record.spec.relative_name.c_str(),O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC,0600);
    need(writer->file.value>=0,"provisional name exists/unsafe/create failed; no retry");struct stat st{};
    need(::fstat(writer->file.value,&st)==0&&S_ISREG(st.st_mode)&&st.st_nlink==1&&st.st_size==0,"new chunk not empty regular single-link");
    out.record.device=static_cast<Count>(st.st_dev);out.record.inode=static_cast<Count>(st.st_ino);writer->header();
    for(Count i=0;i<out.record.count;++i){out.observation.stage="READ_SOURCE_SCALAR";out.observation.attempted_index=i;out.observation.last_bits_valid=false;out.observation.last_scalar_bits=0;
      lease->requireHealthy();const ChunkScalar value=read(i);lease->requireHealthy();out.observation.stage="ENCODE_SOURCE_SCALAR";writer->scalar(value,i);++out.observation.encoded_or_decoded;}
    writer->finish();
  }catch(const std::exception& e){reject(out.observation,lease&&lease->firstReentryReason()?lease->firstReentryReason():e.what());}catch(...){reject(out.observation,lease&&lease->firstReentryReason()?lease->firstReentryReason():"NONSTANDARD_CHUNK_WRITE_FAILURE");}
  if(writer&&out.observation.hash_valid){try{out.observation.physical_prefix_sha256=writer->hash.digest();}catch(...){out.observation.hash_valid=false;}}
  return out; // Every failed O_EXCL file is retained; no unlink/rename/retry.
}
}
