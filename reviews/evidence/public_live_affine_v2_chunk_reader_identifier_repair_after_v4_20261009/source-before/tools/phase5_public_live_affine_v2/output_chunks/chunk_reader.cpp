#include "chunk_io.hpp"
#include <algorithm>
#include <charconv>
#include <cmath>
#include <cerrno>
namespace phase5_public_live_affine_v2 {
namespace {
using namespace chunk_detail;
bool digit(int c){return c>='0'&&c<='9';}
bool space(int c){return c==' '||c=='\n'||c=='\r'||c=='\t';}
struct Reader {
  SharedCaseBudget budget;OwnedReservation ticket;std::unique_ptr<std::array<unsigned char,128>> cache;
  FD root,file;SHA hash;ChunkReadOutcome& out;const ChunkIOLease& lease;
  NumericChunkRecord expected;struct stat opened{};Count next=0,available=0;bool metadata=true;
  Reader(SharedCaseBudget b,ChunkReadOutcome& o,const ChunkIOLease& lock):budget(std::move(b)),ticket(budget.reserve(28)),cache(std::make_unique<std::array<unsigned char,128>>()),out(o),lease(lock){out.observation.hash_valid=true;}
  int peek(){lease.requireHealthy();if(next==available){
    if(out.observation.physical_bytes==expected.bytes)return -1;
    budget.chargeScratchOrCopy(16);const Count amount=std::min<Count>(cache->size(),expected.bytes-out.observation.physical_bytes);
    ssize_t n;do{n=::read(file.value,cache->data(),static_cast<std::size_t>(amount));}while(n<0&&errno==EINTR);
    need(n>0,"chunk read error/truncation");next=0;available=static_cast<Count>(n);
    out.observation.physical_bytes=add(out.observation.physical_bytes,available);out.observation.hash_valid=false;
    hash.update(cache->data(),static_cast<std::size_t>(n));out.observation.hash_valid=true;
  }return (*cache)[static_cast<std::size_t>(next)];}
  int get(){const int c=peek();need(c>=0,"chunk EOF before declared element/structure");++next;++out.observation.consumed_bytes;
    if(metadata)budget.chargeMetadataBytes(1);return c;}
  void ws(){while(space(peek()))get();}
  void punctuation(int c){ws();need(get()==c,"numeric JSON structure mismatch");}
  Count littleWord(){Count n=0;for(unsigned j=0;j<8;++j)n|=static_cast<Count>(get())<<(8*j);return n;}
  unsigned hex(){int c=get();if(digit(c))return c-'0';if(c>='a'&&c<='f')return c-'a'+10;need(false,"literal lowerhex digit required");return 0;}
  unsigned escapedHex(){int c=get();if(digit(c))return c-'0';if(c>='a'&&c<='f')return c-'a'+10;if(c>='A'&&c<='F')return c-'A'+10;need(false,"JSON unicode hex required");return 0;}
  std::string headerString(){budget.chargeScratchOrCopy(8);ws();need(get()=='"',"quoted ASCII schema string required");std::string value;
    while(true){int c=get();if(c=='"')break;need(c>=32&&c<128,"raw JSON control/nonASCII schema field");
      if(c=='\\'){c=get();switch(c){case '"':case '\\':case '/':break;case 'b':c='\b';break;case 'f':c='\f';break;case 'n':c='\n';break;case 'r':c='\r';break;case 't':c='\t';break;
        case 'u':{unsigned v=0;for(int j=0;j<4;++j)v=(v<<4)|escapedHex();need(v<128,"nonASCII schema escape");c=static_cast<int>(v);break;}
        default:need(false,"unknown JSON escape");}}
      value.push_back(static_cast<char>(c));need(value.size()<=64,"schema/key token cap");
    }return value;
  }
  void key(const char* name,bool first=false){if(!first)punctuation(',');need(headerString()==name,"duplicate decoded/unknown/out-of-order JSON key");punctuation(':');}
  Count unsignedDecimal(){ws();need(digit(peek()),"canonical unsigned JSON integer required");Count value=static_cast<Count>(get()-'0');
    if(value==0)need(!digit(peek()),"JSON integer leading zeros");else while(digit(peek()))value=add(mul(value,10),static_cast<Count>(get()-'0'));
    const int c=peek();need(c==','||c==']'||c=='}'||space(c),"unsigned JSON integer suffix/type");return value;
  }
  std::string numberToken(){budget.chargeScratchOrCopy(8);ws();std::string value;while(true){int c=peek();if(!(digit(c)||c=='-'||c=='+'||c=='.'||c=='e'||c=='E'))break;
      need(value.size()<32,"numeric JSON token cap");value.push_back(static_cast<char>(get()));}
    const int c=peek();need(c==','||c==']'||c=='}'||space(c),"JSON numeric suffix/tag/alias");return value;
  }
  Count floatBits(){const auto text=numberToken();std::size_t j=0;if(j<text.size()&&text[j]=='-')++j;
    need(j<text.size()&&digit(text[j]),"JSON f64 grammar");if(text[j]=='0')++j;else while(j<text.size()&&digit(text[j]))++j;
    if(j<text.size()&&text[j]=='.'){++j;const auto at=j;while(j<text.size()&&digit(text[j]))++j;need(j>at,"JSON empty fraction");}
    if(j<text.size()&&(text[j]=='e'||text[j]=='E')){++j;if(j<text.size()&&(text[j]=='+'||text[j]=='-'))++j;const auto at=j;while(j<text.size()&&digit(text[j]))++j;need(j>at,"JSON empty exponent");}
    need(j==text.size(),"JSON f64 malformed token");double value=0;const auto result=std::from_chars(text.data(),text.data()+text.size(),value,std::chars_format::general);
    need(result.ec==std::errc{}&&result.ptr==text.data()+text.size()&&std::isfinite(value),"numeric JSON nonfinite/f64 conversion failure");Count bits;std::memcpy(&bits,&value,8);return bits;
  }
  Count signedBits(){const auto text=numberToken();std::size_t at=(!text.empty()&&text[0]=='-')?1:0;
    need(at<text.size()&&digit(text[at]),"canonical signed integer required");need(text[at]!='0'||at+1==text.size(),"signed integer leading zeros");
    for(std::size_t i=at;i<text.size();++i)need(digit(text[i]),"signed integer fraction/exponent/plus refused");
    need(text!="-0","signed integer minus zero refused");std::int64_t value=0;const auto result=std::from_chars(text.data(),text.data()+text.size(),value);
    need(result.ec==std::errc{}&&result.ptr==text.data()+text.size(),"signed integer overflow");Count bits;std::memcpy(&bits,&value,8);return bits;
  }
  void header(){out.observation.stage="READ_TYPED_HEADER";
    if(expected.encoding==NumericEncoding::LosslessBinary){constexpr char magic[]="P5NUMCHUNK000001";
      for(unsigned j=0;j<16;++j)need(get()==magic[j],"wrong binary chunk schema/magic");
      need(littleWord()==static_cast<Count>(expected.spec.kind),"binary chunk scalar type mismatch");need(littleWord()==0x0102030405060708ULL,"binary chunk endian mismatch");
      need(littleWord()==expected.count,"binary chunk count mismatch");need(expected.bytes==add(40,mul(expected.count,8)),"binary chunk exact byte length mismatch");
    }else {punctuation('{');key("schema",true);need(headerString()=="PUBLIC_LIVE_AFFINE_V2_NUMERIC_CHUNK_JSON_1","JSON numeric chunk schema mismatch");
      key("type");need(headerString()==typeName(expected.spec.kind),"JSON scalar type mismatch");key("count");need(unsignedDecimal()==expected.count,"JSON element count mismatch");key("values");punctuation('[');}
    metadata=false;
  }
  ChunkScalar scalar(Count index){out.observation.stage="READ_TYPED_SCALAR";out.observation.attempted_index=index;out.observation.last_bits_valid=false;out.observation.last_scalar_bits=0;
    ChunkScalar value;value.kind=expected.spec.kind;
    if(expected.encoding==NumericEncoding::LosslessBinary)value.bits=littleWord();else {
      if(index)punctuation(',');switch(value.kind){case ChunkScalarKind::F64:value.bits=floatBits();break;
        case ChunkScalarKind::U64:value.bits=unsignedDecimal();break;case ChunkScalarKind::I64:value.bits=signedBits();break;
        case ChunkScalarKind::FailureF64Bits:{punctuation('"');Count n=0;for(int i=0;i<16;++i)n=(n<<4)|hex();need(get()=='"',"IEEE failure JSON must have exactly16 literal hex digits");value.bits=n;break;}}
    }
    out.observation.last_scalar_bits=value.bits;out.observation.last_bits_valid=true;
    if(value.kind==ChunkScalarKind::F64)need(std::isfinite(asDouble(value.bits)),"nonfinite success/finite chunk field");return value;
  }
  void finish(){lease.requireHealthy();out.observation.stage="VERIFY_COMPLETE_CHUNK_CLOSURE";
    if(expected.encoding==NumericEncoding::FullNumericJson){punctuation(']');punctuation('}');ws();}
    need(out.observation.consumed_bytes==expected.bytes&&next==available,"extra/missing/trailing chunk bytes");
    unsigned char extra=0;ssize_t n;do{n=::read(file.value,&extra,1);}while(n<0&&errno==EINTR);need(n==0,"chunk physical EOF/read error");
    struct stat final{};need(::fstat(file.value,&final)==0&&S_ISREG(final.st_mode)&&final.st_nlink==1&&final.st_dev==opened.st_dev&&final.st_ino==opened.st_ino&&final.st_size==opened.st_size,"chunk FD inode/size changed");
    out.observed_sha256=hash.digest();need(out.observed_sha256==expected.sha256,"complete actual chunk SHA mismatch");
    out.observation.physical_prefix_sha256=out.observed_sha256;out.observation.stage="EXACT_CHUNK_READBACK";out.exact_readback=true;
  }
};
}
ChunkReadOutcome readbackNumericChunk(SharedCaseBudget budget,const std::string& absolute_root,const NumericChunkRecord& record,const ChunkScalarObserver& observer){
  ChunkReadOutcome out;std::optional<ChunkIOLease> lease;std::unique_ptr<Reader> reader;
  try{out.observation.stage="ADMIT_READBACK_STORAGE";lease.emplace(budget.beginChunkIO());reader=std::make_unique<Reader>(std::move(budget),out,*lease);
    const Count count=sealSpec(record.spec);
    need(count==record.count&&record.closed_fsynced,"unclosed chunk/shape receipt mismatch");
    need(record.encoding==reader->budget.numericEncoding(),"readback encoding differs from frozen request; no fallback");
    need(record.encoding==NumericEncoding::LosslessBinary||record.encoding==NumericEncoding::FullNumericJson,"unknown frozen encoding");
    need(record.bytes>0&&record.bytes<=reader->budget.outputCeiling()&&record.bytes<=ResourcePolicyV2::output_bytes,"chunk actual byte cap");
    need(record.sha256.size()==64,"chunk SHA size");for(char c:record.sha256)need(digit(c)||(c>='a'&&c<='f'),"lowercase SHA hex required");
    need(!record.root_path.empty()&&record.root_path[0]=='/'&&record.root_path.size()<=4096&&record.root_path.find('\0')==std::string::npos,"bounded root receipt before copying");
    reader->expected.spec=record.spec;reader->expected.count=record.count;reader->expected.closed_fsynced=record.closed_fsynced;
    reader->expected.encoding=record.encoding;reader->expected.bytes=record.bytes;reader->expected.sha256=record.sha256;
    reader->expected.root_path=record.root_path;reader->expected.device=record.device;reader->expected.inode=record.inode;
    reader->expected.directory_device=record.directory_device;reader->expected.directory_inode=record.directory_inode;
    need(absolute_root==reader->expected.root_path,"readback root path differs from sealed writer receipt");
    const ChunkScalarObserver consume=observer;out.observation.stage="OPEN_READBACK_ROOT";reader->root.value=directory(reader->expected.root_path);
    struct stat dir{};need(::fstat(reader->root.value,&dir)==0&&S_ISDIR(dir.st_mode)&&static_cast<Count>(dir.st_dev)==reader->expected.directory_device&&static_cast<Count>(dir.st_ino)==reader->expected.directory_inode,"readback directory FD differs");
    out.observation.stage="OPEN_REGULAR_NONBLOCKING_CHUNK";reader->file.value=::openat(reader->root.value,reader->expected.spec.relative_name.c_str(),O_RDONLY|O_NOFOLLOW|O_NONBLOCK|O_CLOEXEC);
    need(reader->file.value>=0,"numeric chunk absent/symlink/open failure");need(::fstat(reader->file.value,&reader->opened)==0&&S_ISREG(reader->opened.st_mode)&&reader->opened.st_nlink==1&&reader->opened.st_size>=0&&
      static_cast<Count>(reader->opened.st_size)==reader->expected.bytes&&static_cast<Count>(reader->opened.st_dev)==reader->expected.device&&static_cast<Count>(reader->opened.st_ino)==reader->expected.inode,"readback FD not matching regular artifact");
    reader->header();for(Count i=0;i<reader->expected.count;++i){const auto value=reader->scalar(i);++out.observation.encoded_or_decoded;
      if(consume){out.observation.stage="OBSERVE_DECODED_SCALAR";lease->requireHealthy();consume(i,value);lease->requireHealthy();}}
    reader->finish();
  }catch(const std::exception& e){reject(out.observation,lease&&lease->firstReentryReason()?lease->firstReentryReason():e.what());}
  catch(...){reject(out.observation,lease&&lease->firstReentryReason()?lease->firstReentryReason():"NONSTANDARD_CHUNK_READBACK_FAILURE");}
  if(reader&&out.observation.hash_valid){try{out.observation.physical_prefix_sha256=reader->hash.digest();}catch(...){out.observation.hash_valid=false;}}
  return out; // No repair, rewrite, retry, unlink, rename or root READY publication.
}
}
