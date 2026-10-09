#include "provisional_manifest_io.hpp"
#include "../output_chunks/chunk_io.hpp"
#include <charconv>
#include <cerrno>
namespace phase5_public_live_affine_v2::detail {
namespace {
using chunk_detail::need;using chunk_detail::add;
const char* writerType(MetadataKind k){switch(k){case MetadataKind::Utf8:return "utf8";case MetadataKind::U64:return "u64";case MetadataKind::I64:return "i64";case MetadataKind::Boolean:return "bool";case MetadataKind::Ieee64Bits:return "ieee64_bits";case MetadataKind::NumericReference:return "numeric_reference";case MetadataKind::Missing:return "missing";}throw std::invalid_argument("unknown manifest metadata kind");}
void writeFailure(SharedCaseBudget& b,ProvisionalManifestObservation& o,const char* reason) noexcept{if(o.refused)return;o.refused=true;try{std::string_view s=reason?reason:"MANIFEST_WRITE_FAILURE";need(s.size()<=512,"write error text cap");b.chargeMetadataBytes(s.size());o.first_error.assign(s);}catch(...){}}
}
struct ManifestWriter {
  SharedCaseBudget budget;OwnedReservation ticket;std::unique_ptr<std::array<unsigned char,128>> buffer;
  chunk_detail::FD root,file;chunk_detail::SHA hash;ProvisionalManifestAttempt& out;const ChunkIOLease& lease;Count pending=0;
  ManifestWriter(SharedCaseBudget b,ProvisionalManifestAttempt& o,const ChunkIOLease& l):budget(std::move(b)),ticket(budget.reserve(96)),buffer(std::make_unique<std::array<unsigned char,128>>()),out(o),lease(l){out.writer_.hash_valid=true;}
  void flush(){lease.requireHealthy();if(!pending)return;need(add(budget.outputBytes(),pending)<=budget.outputCeiling()&&add(budget.outputBytes(),pending)<=ResourcePolicyV2::output_bytes,"manifest output quota before write");need(add(budget.metadataBytes(),pending)<=ResourcePolicyV2::metadata_bytes,"manifest metadata quota before write");Count at=0;
    while(at<pending){ssize_t n;do{n=::write(file.value,buffer->data()+at,static_cast<std::size_t>(pending-at));}while(n<0&&errno==EINTR);need(n>0,"manifest short/zero/error write");const Count actual=n;out.bytes_=add(out.bytes_,actual);out.writer_.physical_bytes=out.bytes_;budget.chargeUniqueOutputBytes(actual);budget.chargeMetadataBytes(actual);out.writer_.pending_bytes=pending-at-actual;out.writer_.hash_valid=false;hash.update(buffer->data()+at,actual);out.writer_.hash_valid=true;at=add(at,actual);
    }pending=0;out.writer_.pending_bytes=0;
  }
  void byte(unsigned char c){lease.requireHealthy();if(!pending)budget.chargeScratchOrCopy(16);(*buffer)[pending++]=c;out.writer_.pending_bytes=pending;if(pending==128)flush();}
  void text(std::string_view s){for(unsigned char c:s)byte(c);}
  template<class T>void number(T value){budget.chargeScratchOrCopy(4);char token[32]{};const auto r=std::to_chars(token,token+32,value);need(r.ec==std::errc{},"manifest integer format error");text({token,static_cast<std::size_t>(r.ptr-token)});}
  void boolean(bool b){text(b?"true":"false");}
  void string(std::string_view s){need(s.size()<=ResourcePolicyV2::metadata_bytes,"manifest string cap before borrow");byte('"');static constexpr char h[]="0123456789abcdef";for(unsigned char c:s){budget.chargeScratchOrCopy(1);if(c=='"'||c=='\\'){byte('\\');byte(c);}else if(c<32){char e[6]={'\\','u','0','0',h[c>>4],h[c&15]};text({e,6});}else byte(c);}byte('"');}
  void key(const char* s,bool first=false){if(!first)byte(',');string(s);byte(':');++out.writer_.field;}
  void bits(Count v){budget.chargeScratchOrCopy(2);char token[16]{};static constexpr char h[]="0123456789abcdef";for(int i=15;i>=0;--i){token[i]=h[v&15];v>>=4;}byte('"');text({token,16});byte('"');}
  void reference(const ReferenceFact& f){byte('{');key("use",true);number(static_cast<Count>(f.use));key("index");number(f.index);key("part");number(f.part);key("role");number(static_cast<Count>(f.target.role));key("primary");number(f.target.primary);key("secondary");number(f.target.secondary);key("kind");number(static_cast<Count>(f.kind));key("rank");number(f.rank);need(f.rank<=4,"manifest reference rank cap");key("dimensions");byte('[');for(Count i=0;i<f.rank;++i){if(i)byte(',');number(f.dimensions[i]);}byte(']');
#define WR_U(name) key(#name);number(f.name)
#define WR_B(name) key(#name);boolean(f.name)
    WR_U(count);WR_U(offset);WR_U(source_count);WR_U(destination_offset);WR_B(zero_block);WR_B(empty_concatenation);WR_B(source_valid);WR_B(paired_verified);WR_B(reconstruction_verified);WR_B(requires_original_scope);WR_B(requires_sample_scope);WR_U(cell);WR_U(cycle);WR_U(half);WR_U(tick);
#undef WR_U
#undef WR_B
    byte('}');
  }
  void metadata(const MetadataFact& f){byte('{');key("family",true);string(f.family);key("field");string(f.field);key("index");number(f.index);key("subindex");number(f.subindex);key("type");string(writerType(f.kind));key("value");
    switch(f.kind){case MetadataKind::Utf8:case MetadataKind::Missing:string(f.text);break;case MetadataKind::U64:number(f.unsigned_value);break;case MetadataKind::I64:number(f.signed_value);break;case MetadataKind::Boolean:boolean(f.boolean_value);break;case MetadataKind::Ieee64Bits:bits(f.unsigned_value);break;case MetadataKind::NumericReference:reference(f.reference);break;}byte('}');
  }
  void coverage(const CoverageObligation& o){const auto& f=o.required;byte('{');key("role",true);number(static_cast<Count>(f.role));key("primary");number(f.primary);key("secondary");number(f.secondary);key("rank");number(f.rank);need(f.rank<=4,"manifest requirement rank cap");key("dimensions");byte('[');for(Count i=0;i<f.rank;++i){if(i)byte(',');number(f.dimensions[i]);}byte(']');key("availability");number(static_cast<Count>(f.availability));key("classification");number(static_cast<Count>(f.classification));key("traversal");string(f.traversal);key("mandatory");boolean(f.mandatory);key("scalar_kind");number(static_cast<Count>(f.scalar_kind));key("defined_computed");number(static_cast<Count>(f.defined_computed));key("shape_known");boolean(f.shape_known);key("actual_leaf_bound");boolean(f.actual_leaf_bound);key("bytes_captured");boolean(f.bytes_captured);key("exact_readback");boolean(f.exact_readback);key("state");number(static_cast<Count>(o.state));key("matching_attempts");number(o.matching_attempts);key("reason");string(o.reason);key("full_capture_complete");boolean(false);key("full_flow_accepted");boolean(false);byte('}');}
  void document(const ManifestEventSource& source){out.writer_.stage="ENCODE_PROVISIONAL_TYPED_EVENTS";byte('{');key("schema",true);string("PUBLIC_LIVE_AFFINE_V2_PROVISIONAL_MANIFEST_1");key("status");string("PROVISIONAL_UNACCEPTED");key("mode");string(out.mode_==ProvisionalManifestMode::LiveUnacceptedDiagnostics?"LIVE_UNACCEPTED_DIAGNOSTICS":"RETAINED_FAILURE_DIAGNOSTICS");key("references_available");boolean(out.snapshot_.references_available);key("coverage_available");boolean(out.snapshot_.coverage_available);key("references_reason");string(out.snapshot_.references_available?"REFERENCE_DESCRIPTORS_ONLY_RECONSTRUCTION_PENDING":"ACTUAL_REFERENCE_SOURCE_UNAVAILABLE_MANDATORY_MISSING");key("coverage_reason");string(out.snapshot_.coverage_available?"NUMERIC_OBLIGATIONS_ONLY_COMPOUND_CLOSURE_PENDING":"ACTUAL_REQUIREMENT_OWNER_UNAVAILABLE_MANDATORY_MISSING");
    key("metadata");byte('[');source.metadata([&](const MetadataLeafView& view){if(out.metadata_events_)byte(',');out.writer_.event=out.metadata_events_;out.writer_.field=0;metadata(view.fact());++out.metadata_events_;});byte(']');
    key("references");byte('[');if(out.snapshot_.references_available)source.references([&](const ReferenceLeafView& view){if(out.reference_events_)byte(',');out.writer_.event=out.reference_events_;out.writer_.field=0;reference(view.fact());++out.reference_events_;});byte(']');
    key("coverage");byte('[');if(out.snapshot_.coverage_available)source.coverage([&](const CoverageObligationView& view){if(out.coverage_events_)byte(',');out.writer_.event=out.coverage_events_;out.writer_.field=0;coverage(view.obligation());++out.coverage_events_;});byte(']');
    key("counts");byte('[');number(out.metadata_events_);byte(',');number(out.reference_events_);byte(',');number(out.coverage_events_);byte(']');key("references_reconstructed");boolean(false);key("full_capture_complete");boolean(false);key("full_flow_accepted");boolean(false);key("phase5");string("NOT_ACCEPTED");key("phase6");string("NOT_STARTED");byte('}');flush();
  }
  void finish(){struct stat st{};need(::fstat(file.value,&st)==0&&S_ISREG(st.st_mode)&&st.st_nlink==1&&st.st_size>=0&&static_cast<Count>(st.st_size)==out.bytes_&&static_cast<Count>(st.st_dev)==out.device_&&static_cast<Count>(st.st_ino)==out.inode_,"manifest FD changed before closure");need(::fsync(file.value)==0,"manifest file fsync failed");need(::fsync(root.value)==0,"manifest directory fsync failed");budget.chargeScratchOrCopy(8);out.sha256_=hash.digest();out.closed_=true;out.writer_.prefix_sha256=out.sha256_;out.writer_.stage="CLOSED_PROVISIONAL_ONLY";}
};
void ProvisionalManifestIO::write(SharedCaseBudget budget,ProvisionalManifestAttempt& out,const ManifestEventSource& source){std::optional<ChunkIOLease> lease;std::unique_ptr<ManifestWriter> w;
  try{out.writer_.stage="ADMIT_PROVISIONAL_WRITER";lease.emplace(budget.beginChunkIO());w=std::make_unique<ManifestWriter>(budget,out,*lease);chunk_detail::component(out.name_,128);need(out.name_.size()>12&&out.name_.compare(out.name_.size()-12,12,".provisional")==0,"manifest only safe provisional name");
    w->root.value=chunk_detail::directory(out.root_);struct stat d{};need(::fstat(w->root.value,&d)==0&&S_ISDIR(d.st_mode),"manifest root not directory");out.directory_device_=d.st_dev;out.directory_inode_=d.st_ino;
    out.writer_.stage="CREATE_PROVISIONAL_O_EXCL";w->file.value=::openat(w->root.value,out.name_.c_str(),O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC,0600);need(w->file.value>=0,"manifest exists/unsafe/create failed; no retry");struct stat st{};need(::fstat(w->file.value,&st)==0&&S_ISREG(st.st_mode)&&st.st_nlink==1&&st.st_size==0,"manifest new FD not empty regular single-link");out.device_=st.st_dev;out.inode_=st.st_ino;w->document(source);lease->requireHealthy();w->finish();
  }catch(const std::exception& e){writeFailure(budget,out.writer_,lease&&lease->firstReentryReason()?lease->firstReentryReason():e.what());}catch(...){writeFailure(budget,out.writer_,"NONSTANDARD_PROVISIONAL_WRITE_FAILURE");}
  if(w&&out.writer_.hash_valid&&!out.closed_)try{budget.chargeScratchOrCopy(8);out.writer_.prefix_sha256=w->hash.digest();}catch(...){out.writer_.hash_valid=false;}
}
}
