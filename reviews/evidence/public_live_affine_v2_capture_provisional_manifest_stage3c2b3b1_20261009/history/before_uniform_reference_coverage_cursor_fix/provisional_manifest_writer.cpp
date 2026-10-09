#include "provisional_manifest_io.hpp"
#include "provisional_manifest_schema.hpp"
#include "../output_chunks/chunk_io.hpp"
#include <charconv>
#include <cerrno>
#include <type_traits>
namespace phase5_public_live_affine_v2::detail {
namespace {
using chunk_detail::need;using chunk_detail::add;
const char* writerType(MetadataKind k){switch(k){case MetadataKind::Utf8:return "utf8";case MetadataKind::U64:return "u64";case MetadataKind::I64:return "i64";case MetadataKind::Boolean:return "bool";case MetadataKind::Ieee64Bits:return "ieee64_bits";case MetadataKind::NumericReference:return "numeric_reference";case MetadataKind::Missing:return "missing";}throw std::invalid_argument("unknown manifest metadata kind");}
void writeFailure(SharedCaseBudget& b,ProvisionalManifestObservation& o,const char* reason) noexcept{if(o.refused)return;o.refused=true;o.fallback_error="MANIFEST_WRITE_FAILURE_DETAIL_NOT_COPIED_SOURCE_RETAINED";try{std::string_view s=reason?reason:"MANIFEST_WRITE_FAILURE";need(s.size()<=512,"write error text cap");b.chargeMetadataBytes(s.size());o.first_error.assign(s);o.fallback_error="";}catch(...){}}
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
  template<class T>void number(T value){out.writer_.last_bits=static_cast<Count>(value);out.writer_.last_kind=std::is_signed<T>::value?MetadataKind::I64:MetadataKind::U64;out.writer_.last_bits_valid=true;budget.chargeScratchOrCopy(4);char token[32]{};const auto r=std::to_chars(token,token+32,value);need(r.ec==std::errc{},"manifest integer format error");text({token,static_cast<std::size_t>(r.ptr-token)});}
  void boolean(bool b){out.writer_.last_kind=MetadataKind::Boolean;out.writer_.last_bits=b?1:0;out.writer_.last_bits_valid=true;text(b?"true":"false");}
  void string(std::string_view s){need(s.size()<=ResourcePolicyV2::metadata_bytes,"manifest string cap before borrow");byte('"');static constexpr char h[]="0123456789abcdef";for(unsigned char c:s){budget.chargeScratchOrCopy(1);if(c=='"'||c=='\\'){byte('\\');byte(c);}else if(c<32){char e[6]={'\\','u','0','0',h[c>>4],h[c&15]};text({e,6});}else byte(c);}byte('"');}
  void key(const char* s,bool first=false){if(!first)byte(',');string(s);byte(':');++out.writer_.field;out.writer_.last_bits_valid=false;}
  void bits(Count v){out.writer_.last_kind=MetadataKind::Ieee64Bits;out.writer_.last_bits=v;out.writer_.last_bits_valid=true;budget.chargeScratchOrCopy(2);char token[16]{};static constexpr char h[]="0123456789abcdef";for(int i=15;i>=0;--i){token[i]=h[v&15];v>>=4;}byte('"');text({token,16});byte('"');}
  void compactString(std::string_view value,std::string_view firstRoot={},std::string_view mainHash={},bool rootRef=false,bool hashRef=false){
    for(Count i=0;i<sizeof(manifest_schema::literals)/sizeof(manifest_schema::literals[0]);++i)if(value==manifest_schema::literals[i]){text("[\"d\",");number(i);byte(']');return;}
    if(rootRef&&value==firstRoot){text("[\"r\",0]");return;}if(hashRef&&!mainHash.empty()&&value==mainHash){text("[\"h\",0]");return;}string(value);
  }
  void observation(const ChunkIOObservation& o,std::string_view hash){text("[[\"stage\",");compactString(o.stage);text("],");number(o.attempted_index);byte(',');number(o.encoded_or_decoded);byte(',');number(o.physical_bytes);byte(',');number(o.consumed_bytes);byte(',');number(o.pending_bytes);byte(',');bits(o.last_scalar_bits);byte(',');boolean(o.last_bits_valid);byte(',');boolean(o.hash_valid);byte(',');boolean(o.refused);byte(',');compactString(o.first_error);byte(',');compactString(o.physical_prefix_sha256,{},hash,false,true);byte(']');}
  void rowObservation(const ChunkIOObservation& o,const BoundLeafAttempt& a,bool read){const auto& r=a.write_.record;
    const bool values=o.attempted_index==(r.count?r.count-1:0)&&o.encoded_or_decoded==r.count&&o.physical_bytes==r.bytes&&o.consumed_bytes==(read?r.bytes:0)&&o.pending_bytes==0&&o.last_bits_valid==(r.count!=0)&&o.hash_valid&&!o.refused&&o.first_error.empty()&&o.physical_prefix_sha256==r.sha256;
    const bool scalar=r.count?(read?a.comparison_attempted_&&o.last_scalar_bits==a.actual_.bits:a.expected_valid_&&o.last_scalar_bits==a.expected_.bits):o.last_scalar_bits==0;
    const bool stage=std::string_view(o.stage)==(read?"EXACT_CHUNK_READBACK":"CLOSED_PROVISIONAL_CHUNK");
    if(values&&scalar&&stage){text(read?"[\"CR1\"]":"[\"CW1\"]");return;}observation(o,r.sha256);
  }
  void attempt(const ManifestAttemptRowView& view){const auto& a=*view.actual_;const auto& r=a.write_.record;byte('[');bool used=false;auto col=[&]{++out.writer_.field;out.writer_.last_bits_valid=false;out.writer_.last_bits=0;if(used)byte(',');used=true;};
#define A_U(v) col();number(v)
#define A_B(v) col();boolean(v)
    A_U(a.attempt_sequence_);A_U(static_cast<Count>(a.role_));A_U(a.primary_);A_U(a.secondary_);A_U(a.generation_);col();number(static_cast<std::int64_t>(a.computed_state_));col();compactString(a.storage_traversal_);col();compactString(a.assignment_traversal_);
    A_B(view.source_matches_);A_B(view.cost_matches_);A_B(view.partition_matches_);A_B(a.original_scope_);A_B(a.canonical_scope_);A_B(a.sample_scope_);A_U(a.sample_cell_);A_U(a.sample_tick_);A_U(a.sample_cycle_);A_U(a.sample_half_);
    col();byte('[');for(Count i=0;i<r.spec.dimensions.size();++i){if(i)byte(',');number(r.spec.dimensions[i]);}byte(']');col();number(static_cast<std::int64_t>(r.spec.kind));col();number(static_cast<std::int64_t>(r.spec.classification));col();number(static_cast<std::int64_t>(r.encoding));
    col();compactString(r.root_path,view.first_root_,{},view.index_>0,false);col();compactString(r.spec.relative_name);col();compactString(r.spec.role);col();compactString(r.sha256);A_U(r.count);A_U(r.bytes);A_U(r.device);A_U(r.inode);A_U(r.directory_device);A_U(r.directory_inode);A_B(r.closed_fsynced);col();rowObservation(a.write_.observation,a,false);
    A_B(a.comparison_attempted_);A_B(a.expected_valid_);A_B(a.mismatch_);A_U(a.mismatch_index_);col();number(static_cast<std::int64_t>(a.expected_.kind));col();number(static_cast<std::int64_t>(a.actual_.kind));
    col();if(a.expected_valid_)bits(a.expected_.bits);else text("[\"missing\",\"EXPECTED_SCALAR_NOT_OBSERVED_VALID\"]");col();if(a.comparison_attempted_)bits(a.actual_.bits);else text("[\"missing\",\"ACTUAL_SCALAR_NOT_OBSERVED\"]");
    col();if(a.readback_){byte('[');boolean(a.readback_->exact_readback);byte(',');compactString(a.readback_->observed_sha256,{},r.sha256,false,true);byte(',');rowObservation(a.readback_->observation,a,true);byte(']');}else text("[\"missing\",\"NO_INDEPENDENT_READBACK_OUTCOME\"]");
#undef A_U
#undef A_B
    byte(']');
  }
  void reference(const ReferenceFact& f){byte('[');bool used=false;auto col=[&]{if(used)byte(',');used=true;++out.writer_.field;out.writer_.last_bits_valid=false;};col();number(static_cast<Count>(f.use));col();number(f.index);col();number(f.part);col();number(static_cast<Count>(f.target.role));col();number(f.target.primary);col();number(f.target.secondary);col();number(static_cast<Count>(f.kind));col();number(f.rank);need(f.rank<=4,"manifest reference rank cap");col();byte('[');for(Count i=0;i<f.rank;++i){if(i)byte(',');number(f.dimensions[i]);}byte(']');
#define WR_U(name) col();number(f.name)
#define WR_B(name) col();boolean(f.name)
    WR_U(count);WR_U(offset);WR_U(source_count);WR_U(destination_offset);WR_B(zero_block);WR_B(empty_concatenation);WR_B(source_valid);WR_B(paired_verified);WR_B(reconstruction_verified);WR_B(requires_original_scope);WR_B(requires_sample_scope);WR_U(cell);WR_U(cycle);WR_U(half);WR_U(tick);
#undef WR_U
#undef WR_B
    byte(']');
  }
  void metadata(const MetadataFact& f){byte('{');key("family",true);string(f.family);key("field");string(f.field);key("index");number(f.index);key("subindex");number(f.subindex);key("type");string(writerType(f.kind));key("value");
    switch(f.kind){case MetadataKind::Utf8:case MetadataKind::Missing:string(f.text);break;case MetadataKind::U64:number(f.unsigned_value);break;case MetadataKind::I64:number(f.signed_value);break;case MetadataKind::Boolean:boolean(f.boolean_value);break;case MetadataKind::Ieee64Bits:bits(f.unsigned_value);break;case MetadataKind::NumericReference:reference(f.reference);break;}byte('}');
  }
  void coverage(const CoverageObligation& o){const auto& f=o.required;byte('[');bool used=false;auto col=[&]{if(used)byte(',');used=true;++out.writer_.field;out.writer_.last_bits_valid=false;};col();number(static_cast<Count>(f.role));col();number(f.primary);col();number(f.secondary);col();number(f.rank);need(f.rank<=4,"manifest requirement rank cap");col();byte('[');for(Count i=0;i<f.rank;++i){if(i)byte(',');number(f.dimensions[i]);}byte(']');col();number(static_cast<Count>(f.availability));col();number(static_cast<Count>(f.classification));col();compactString(f.traversal);col();boolean(f.mandatory);col();number(static_cast<Count>(f.scalar_kind));col();number(static_cast<Count>(f.defined_computed));col();boolean(f.shape_known);col();boolean(f.actual_leaf_bound);col();boolean(f.bytes_captured);col();boolean(f.exact_readback);col();number(static_cast<Count>(o.state));col();number(o.matching_attempts);col();compactString(o.reason);col();boolean(false);col();boolean(false);byte(']');}
  void document(const ManifestEventSource& source){out.writer_.stage="ENCODE_PROVISIONAL_TYPED_EVENTS";byte('{');key("schema",true);string("PUBLIC_LIVE_AFFINE_V2_PROVISIONAL_MANIFEST_COLUMNS_2");key("status");string("PROVISIONAL_UNACCEPTED");key("mode");string(out.mode_==ProvisionalManifestMode::LiveUnacceptedDiagnostics?"LIVE_UNACCEPTED_DIAGNOSTICS":"RETAINED_FAILURE_DIAGNOSTICS");key("references_available");boolean(out.snapshot_.references_available);key("coverage_available");boolean(out.snapshot_.coverage_available);key("references_reason");string(out.snapshot_.references_available?"REFERENCE_DESCRIPTORS_ONLY_RECONSTRUCTION_PENDING":"ACTUAL_REFERENCE_SOURCE_UNAVAILABLE_MANDATORY_MISSING");key("coverage_reason");string(out.snapshot_.coverage_available?"NUMERIC_OBLIGATIONS_ONLY_COMPOUND_CLOSURE_PENDING":"ACTUAL_REQUIREMENT_OWNER_UNAVAILABLE_MANDATORY_MISSING");
    out.writer_.stage="ENCODE_ACTUAL_METADATA_EVENTS";key("metadata");byte('[');Count stored=0;bool marker=false;
    source.metadata([&](const MetadataLeafView& view){const auto& fact=view.fact();const std::string_view family=fact.family;const bool row=family=="attempt"||family=="attempt_write"||family=="attempt_read"||family=="attempt_write_frontier"||family=="attempt_read_frontier";
      out.writer_.event=out.metadata_events_;out.writer_.field=0;
      if(row){bool known=false;for(const auto& definition:manifest_schema::projected_fields){budget.chargeScratchOrCopy(1);if(definition.family==family&&definition.field==fact.field){need((definition.kind_mask&(1U<<static_cast<unsigned>(fact.kind)))!=0,"projected field original scalar type mismatch");known=true;break;}}need(known,"unknown/extra projected attempt field");if(!marker){if(stored++)byte(',');text("[\"ATTEMPT_COLUMN_ROWS\",");number(source.attempt_count);byte(']');marker=true;}}
      else {if(stored++)byte(',');metadata(fact);}++out.metadata_events_;});byte(']');
    key("attempt_rows");byte('[');Count rowCount=0;source.attempts([&](const ManifestAttemptRowView& view){if(rowCount++)byte(',');out.writer_.event=view.index_;out.writer_.field=0;attempt(view);});need(rowCount==source.attempt_count,"private complete attempt row count mismatch");byte(']');
    out.writer_.stage="ENCODE_ACTUAL_REFERENCE_EVENTS";key("references");byte('[');if(out.snapshot_.references_available)source.references([&](const ReferenceLeafView& view){if(out.reference_events_)byte(',');out.writer_.event=out.reference_events_;out.writer_.field=0;reference(view.fact());++out.reference_events_;});byte(']');
    out.writer_.stage="ENCODE_ACTUAL_COVERAGE_OBLIGATIONS";key("coverage");byte('[');if(out.snapshot_.coverage_available)source.coverage([&](const CoverageObligationView& view){if(out.coverage_events_)byte(',');out.writer_.event=out.coverage_events_;out.writer_.field=0;coverage(view.obligation());++out.coverage_events_;});byte(']');
    out.writer_.stage="ENCODE_PROVISIONAL_TRAILER";key("counts");byte('[');number(out.metadata_events_);byte(',');number(out.reference_events_);byte(',');number(out.coverage_events_);byte(']');key("references_reconstructed");boolean(false);key("full_capture_complete");boolean(false);key("full_flow_accepted");boolean(false);key("phase5");string("NOT_ACCEPTED");key("phase6");string("NOT_STARTED");byte('}');flush();
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
