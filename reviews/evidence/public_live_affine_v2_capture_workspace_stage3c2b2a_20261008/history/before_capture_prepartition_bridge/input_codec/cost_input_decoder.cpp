#include "cost_input_decoder.hpp"
#include <openssl/evp.h>
#include <algorithm>
#include <array>
#include <charconv>
#include <cmath>
#include <cstring>
#include <cerrno>
#include <fcntl.h>
#include <limits>
#include <stdexcept>
#include <system_error>
#include <sys/stat.h>
#include <unistd.h>
namespace phase5_public_live_affine_v2 {
namespace {
void need(bool x,const char* s){if(!x)throw std::invalid_argument(s);}
Count add(Count a,Count b){return checkedAdd(a,b);}Count mul(Count a,Count b){return checkedMultiply(a,b);}
Count bits(double d){static_assert(sizeof(double)==8&&std::numeric_limits<double>::is_iec559,"IEEE754 required");Count n;std::memcpy(&n,&d,8);return n;}
bool digit(int c){return c>='0'&&c<='9';}
bool whitespace(int c){return c==' '||c=='\n'||c=='\r'||c=='\t';}
void utf8(const std::string& s){
  need(!s.empty()&&s.size()<=256&&s.find('\0')==std::string::npos,"bounded nonempty UTF8 name/units required");
  for(std::size_t i=0;i<s.size();){unsigned c=static_cast<unsigned char>(s[i++]);if(c<128)continue;
    unsigned n=0,v=0,min=0;if(c>=0xc2&&c<=0xdf){n=1;v=c&31;min=0x80;}
    else if(c>=0xe0&&c<=0xef){n=2;v=c&15;min=0x800;}else if(c>=0xf0&&c<=0xf4){n=3;v=c&7;min=0x10000;}else need(false,"invalid UTF8 lead");
    need(i+n<=s.size(),"truncated UTF8");while(n--){unsigned q=static_cast<unsigned char>(s[i++]);need((q&0xc0)==0x80,"invalid UTF8 continuation");v=(v<<6)|(q&63);}
    need(v>=min&&v<=0x10ffff&&!(v>=0xd800&&v<=0xdfff),"noncanonical UTF8 scalar");
  }
}
void appendUtf8(std::string& s,unsigned v){
  need(v<=0x10ffff&&!(v>=0xd800&&v<=0xdfff),"invalid JSON unicode scalar");
  if(v<0x80)s.push_back(static_cast<char>(v));else if(v<0x800){s.push_back(static_cast<char>(0xc0|(v>>6)));s.push_back(static_cast<char>(0x80|(v&63)));}
  else if(v<0x10000){s.push_back(static_cast<char>(0xe0|(v>>12)));s.push_back(static_cast<char>(0x80|((v>>6)&63)));s.push_back(static_cast<char>(0x80|(v&63)));}
  else {s.push_back(static_cast<char>(0xf0|(v>>18)));s.push_back(static_cast<char>(0x80|((v>>12)&63)));s.push_back(static_cast<char>(0x80|((v>>6)&63)));s.push_back(static_cast<char>(0x80|(v&63)));}
}
}
namespace detail {
struct CostDecoderState {
  // Shared receipt protects both parsed topology and cache, including after
  // descriptors transfer to the cost anchor and while this observer survives.
  std::shared_ptr<OwnedReservation> input_owner;
  std::unique_ptr<std::array<unsigned char,128>> cache;Count next=0,available=0;
  CostInputRecipe partial;FileIdentity expected;CaseBudget* budget=nullptr;
  Count metadata_cap=0,artifact_cap=0,dy=0,du=0,samples=0;FactorShape shape;
  CostDecodeObservation status;int fd=-1;struct stat original_stat{};
  std::unique_ptr<EVP_MD_CTX,decltype(&EVP_MD_CTX_free)> hash{EVP_MD_CTX_new(),EVP_MD_CTX_free};
  ~CostDecoderState(){if(fd>=0)::close(fd);}
  void fail(const char* why) noexcept{if(status.refused)return;status.refused=true;try{status.failure=why?why:"DECODER_REFUSAL";}catch(...){}}
  std::string digest() const {
    std::unique_ptr<EVP_MD_CTX,decltype(&EVP_MD_CTX_free)> copy(EVP_MD_CTX_new(),EVP_MD_CTX_free);
    need(copy&&EVP_MD_CTX_copy_ex(copy.get(),hash.get())==1,"prefix SHA copy failed");
    std::array<unsigned char,EVP_MAX_MD_SIZE> bytes{};unsigned n=0;
    need(EVP_DigestFinal_ex(copy.get(),bytes.data(),&n)==1&&n==32,"prefix SHA final failed");
    constexpr char h[]="0123456789abcdef";std::string out;for(unsigned i=0;i<n;++i){out.push_back(h[bytes[i]>>4]);out.push_back(h[bytes[i]&15]);}return out;
  }
  void open(){
    status.stage="OPEN_PINNED_ARTIFACT";need(expected.bytes>0&&expected.bytes<=artifact_cap,"cost artifact byte cap");
    need(hash&&EVP_DigestInit_ex(hash.get(),EVP_sha256(),nullptr)==1,"artifact SHA init failed");status.hash_valid=true;
    fd=::open(expected.path.c_str(),O_RDONLY|O_CLOEXEC|O_NOFOLLOW);need(fd>=0,"cost artifact nofollow open failed");
    need(::fstat(fd,&original_stat)==0&&S_ISREG(original_stat.st_mode)&&original_stat.st_size>=0&&
      static_cast<Count>(original_stat.st_size)==expected.bytes,"cost artifact not bounded regular file");
  }
  int peek(){
    if(next==available){
      if(status.physical_bytes_read==expected.bytes)return -1;
      budget->chargeScratchOrCopy(16); // Charge BEFORE each 128-byte cache reuse.
      const Count amount=std::min<Count>(cache->size(),expected.bytes-status.physical_bytes_read);
      ssize_t n;do{n=::read(fd,cache->data(),static_cast<std::size_t>(amount));}while(n<0&&errno==EINTR);
      need(n>0,"truncated/read-error cost artifact");available=static_cast<Count>(n);next=0;
      status.physical_bytes_read=add(status.physical_bytes_read,available);status.hash_valid=false;
      need(EVP_DigestUpdate(hash.get(),cache->data(),static_cast<std::size_t>(n))==1,"artifact SHA update failed");status.hash_valid=true;
    }return (*cache)[static_cast<std::size_t>(next)];
  }
  int get(){const int v=peek();need(v>=0,"truncated cost artifact");++next;status.consumed_bytes=add(status.consumed_bytes,1);
    if(!status.header_complete){status.metadata_bytes=status.consumed_bytes;need(status.metadata_bytes<=metadata_cap,"cost metadata byte cap");}return v;}
  Count u64(){Count n=0;status.pending_u64_bits=0;status.pending_u64_bytes=0;status.pending_u64_start=status.consumed_bytes;
    for(unsigned j=0;j<8;++j){n|=static_cast<Count>(get())<<(8*j);status.pending_u64_bits=n;status.pending_u64_bytes=j+1;}return n;}
  std::int64_t i64(){const Count n=u64();std::int64_t i;static_assert(sizeof(i)==8,"i64 required");std::memcpy(&i,&n,8);return i;}
  double binaryDouble(){status.last_bits_valid=false;Count n=u64();status.last_scalar_bits=n;status.last_bits_valid=true;double d;std::memcpy(&d,&n,8);need(std::isfinite(d),"nonfinite binary cost scalar");return d;}
  std::string binaryString(Count cap){const Count n=u64();need(n>0&&n<=cap,"binary string length cap");std::string s;s.reserve(static_cast<std::size_t>(n));for(Count i=0;i<n;++i)s.push_back(static_cast<char>(get()));return s;}
  void ws(){while(whitespace(peek()))get();}
  void punctuation(int c){ws();need(get()==c,"JSON structure/key-order mismatch");}
  unsigned hex4(){unsigned n=0;for(int i=0;i<4;++i){int c=get();unsigned v=0;if(digit(c))v=c-'0';else if(c>='a'&&c<='f')v=c-'a'+10;else if(c>='A'&&c<='F')v=c-'A'+10;else need(false,"invalid JSON unicode hex");n=(n<<4)|v;}return n;}
  std::string string(Count cap){ws();need(get()=='"',"JSON string required");std::string s;
    while(true){int c=get();if(c=='"')break;need(c>=32,"JSON unescaped control");
      if(c=='\\'){c=get();switch(c){case '"':case '\\':case '/':s.push_back(static_cast<char>(c));break;
        case 'b':s.push_back('\b');break;case 'f':s.push_back('\f');break;case 'n':s.push_back('\n');break;case 'r':s.push_back('\r');break;case 't':s.push_back('\t');break;
        case 'u':{unsigned v=hex4();if(v>=0xd800&&v<=0xdbff){need(get()=='\\'&&get()=='u',"JSON high surrogate requires pair");unsigned low=hex4();need(low>=0xdc00&&low<=0xdfff,"JSON invalid low surrogate");v=0x10000+((v-0xd800)<<10)+(low-0xdc00);}appendUtf8(s,v);break;}
        default:need(false,"JSON escape refused");}}
      else s.push_back(static_cast<char>(c));need(s.size()<=cap,"decoded JSON string cap");
    }return s;
  }
  void key(const char* expected_key,bool first=false){if(!first)punctuation(',');need(string(64)==expected_key,"JSON duplicate/unknown/noncanonical key order");punctuation(':');}
  Count count(){ws();need(digit(peek()),"JSON unsigned canonical integer required");Count n=0;int first=get();n=first-'0';if(first=='0')need(!digit(peek()),"JSON leading-zero count");
    else while(digit(peek()))n=add(mul(n,10),static_cast<Count>(get()-'0'));
    int c=peek();need(c==','||c==']'||c=='}'||whitespace(c),"JSON count token suffix");return n;
  }
  double jsonDouble(){status.last_bits_valid=false;status.numeric_token_prefix.clear();ws();std::array<char,33> token{};std::size_t n=0;
    while(true){int c=peek();if(!(digit(c)||c=='-'||c=='+'||c=='.'||c=='e'||c=='E'))break;
      need(n<32,"JSON f64 token length cap");token[n++]=static_cast<char>(get());status.numeric_token_prefix.push_back(token[n-1]);}
    std::size_t i=0;if(i<n&&token[i]=='-')++i;need(i<n&&digit(token[i]),"JSON number grammar");
    if(token[i]=='0')++i;else while(i<n&&digit(token[i]))++i;
    if(i<n&&token[i]=='.'){++i;const auto start=i;while(i<n&&digit(token[i]))++i;need(i>start,"JSON empty fraction");}
    if(i<n&&(token[i]=='e'||token[i]=='E')){++i;if(i<n&&(token[i]=='+'||token[i]=='-'))++i;const auto start=i;while(i<n&&digit(token[i]))++i;need(i>start,"JSON empty exponent");}
    need(i==n&&n>0,"JSON malformed numeric token");int c=peek();need(c==','||c==']'||c=='}'||whitespace(c),"JSON number suffix/tag/alias");
    double value=0;const auto result=std::from_chars(token.data(),token.data()+n,value,std::chars_format::general);
    need(result.ec==std::errc{}&&result.ptr==token.data()+n&&std::isfinite(value),"JSON f64 range/conversion failure");status.last_scalar_bits=bits(value);status.last_bits_valid=true;return value;
  }
  Count scalarCount() const{return add(add(add(mul(shape.rows,dy),shape.rows),add(mul(shape.terms,dy),shape.terms)),add(shape.addition_coefficients,du));}
  void shapeEqual(const FactorShape& f){need(f.terms==shape.terms&&f.rows==shape.rows&&f.largest_term_rows==shape.largest_term_rows&&
    f.addition_coefficients==shape.addition_coefficients&&f.addition_records==shape.addition_records,"decoded cost shape differs from bound shape");}
  void metadata(CompactAffineAssembly& assembly){
    status.stage="DECODE_COMPLETE_METADATA";ws();const int lead=peek();
    if(lead=='{')status.actual_input=NumericEncoding::FullNumericJson;
    else if(lead=='P'){need(status.consumed_bytes==0,"binary leading whitespace refused");status.actual_input=NumericEncoding::LosslessBinary;}
    else need(false,"unrecognized declared input codec");
    need(*status.actual_input==status.requested_output,"unsupported input/output encoding pair; no fallback");
    const bool binary=*status.actual_input==NumericEncoding::LosslessBinary;
    if(binary){constexpr char magic[]="P5COSTBINARYV001";for(unsigned j=0;j<16;++j)need(get()==magic[j],"wrong binary cost magic/version");
      need(u64()==0x0102030405060708ULL,"wrong cost endian marker");need(binaryString(64)=="PUBLIC_LIVE_AFFINE_V2_COST_INPUT_BINARY_1","binary input schema");}
    else {punctuation('{');key("schema",true);need(string(64)=="PUBLIC_LIVE_AFFINE_V2_COST_INPUT_JSON_1","JSON cost schema");
      key("endian");need(string(16)=="little","JSON endian declaration");}
    auto integer=[&](const char* k){if(!binary)key(k);return binary?u64():count();};
    need(integer("dy")==dy&&integer("du")==du,"decoded DY/DU mismatch");
    if(binary)need(i64()==static_cast<std::int64_t>(assembly.initialKind()),"decoded initial kind mismatch");
    else {key("initial_kind");need(string(32)==(assembly.initialKind()==AssemblyInitialKind::LiveActual?"LiveActual":"AlgebraTest"),"JSON initial kind mismatch");key("chosen_initial");punctuation('[');}
    status.stage="HEADER_CHOSEN_INITIAL";for(Count j=0;j<30;++j){status.last_scalar_byte_offset=status.consumed_bytes;if(!binary&&j)punctuation(',');const double v=binary?binaryDouble():jsonDouble();need(bits(v)==bits(assembly.chosenInitial(j)),"decoded chosen initial bits differ from assembly");++status.header_initial_count;}
    if(!binary){punctuation(']');key("factor_shape");punctuation('{');}
    FactorShape declared;
    if(binary){declared={u64(),u64(),u64(),u64(),u64()};}
    else {key("terms",true);declared.terms=count();key("rows");declared.rows=count();key("largest_term_rows");declared.largest_term_rows=count();
      key("addition_coefficients");declared.addition_coefficients=count();key("addition_records");declared.addition_records=count();punctuation('}');}
    shapeEqual(declared);status.expected_scalars=scalarCount();need(integer("scalar_count")==status.expected_scalars,"scalar count mismatch");
    if(!binary){key("terms");punctuation('[');}partial.terms.reserve(static_cast<std::size_t>(shape.terms));FactorShape actual;actual.terms=shape.terms;
    for(Count k=0;k<shape.terms;++k){status.active_term=k;status.stage="TERM_NAME";if(!binary){if(k)punctuation(',');punctuation('{');key("name",true);}
      partial.terms.emplace_back();auto& t=partial.terms.back();t.name=binary?binaryString(256):string(256);utf8(t.name);
      status.stage="TERM_UNITS";if(!binary)key("units");t.units=binary?binaryString(256):string(256);utf8(t.units);
      status.stage="TERM_ROWS";if(!binary)key("rows");t.rows=binary?u64():count();need(t.rows<=shape.largest_term_rows&&t.rows<=256,"decoded parent row cap");
      actual.rows=add(actual.rows,t.rows);need(actual.rows<=shape.rows,"decoded total rows exceed shape");actual.largest_term_rows=std::max(actual.largest_term_rows,t.rows);
      Count records=0;if(binary)records=u64();else {key("additions");punctuation('[');}
      if(binary)need(records<=shape.addition_records-actual.addition_records,"decoded addition roster cap");
      Count a=0;while(binary?a<records:(ws(),peek()!=']')){
        status.active_addition=a;status.stage="ADDITION_SAMPLE";if(!binary){if(a)punctuation(',');punctuation('{');key("sample_index",true);}
        need(actual.addition_records<shape.addition_records,"decoded addition records exceed shape");t.additions.emplace_back();auto& v=t.additions.back();
        v.sample_index=binary?u64():count();need(v.sample_index<samples,"decoded sample index outside source");
        Count parents=0;if(binary){parents=u64();need(parents>0&&parents<=t.rows,"decoded parent embed rows");v.parent_rows.reserve(static_cast<std::size_t>(parents));}
        else {key("parent_rows");punctuation('[');}
        status.stage="ADDITION_PARENT_ROWS";Count r=0;while(binary?r<parents:(ws(),peek()!=']')){
          status.active_parent=r;if(!binary&&r)punctuation(',');need(r<t.rows&&actual.addition_coefficients<=shape.addition_coefficients&&
            shape.addition_coefficients-actual.addition_coefficients>=30,"decoded coefficient/row cap");
          const Count row=binary?u64():count();need(row<t.rows,"decoded parent row index");v.parent_rows.push_back(row);actual.addition_coefficients=add(actual.addition_coefficients,30);++r;
        }
        need(r>0,"empty addition rows");if(!binary){punctuation(']');punctuation('}');}
        actual.addition_records=add(actual.addition_records,1);status.parsed_additions=actual.addition_records;++a;
      }
      if(!binary){punctuation(']');punctuation('}');}status.parsed_terms=k+1;
    }
    shapeEqual(actual);if(!binary){punctuation(']');key("scalars");punctuation('[');}
    status.header_complete=true;
    if(binary)need(add(status.consumed_bytes,mul(status.expected_scalars,8))==expected.bytes,"binary exact payload length/trailing data");
    status.stage="INGEST_SCALARS";
  }
  double scalar(Count index){try{
    need(status.header_complete&&!status.artifact_closed&&!status.refused&&index==status.delivered_scalars&&index<status.expected_scalars,"scalar replay/skip/outside declared input");
    status.last_scalar_attempted=true;status.last_scalar_delivered=false;status.last_scalar_bits=0;status.last_bits_valid=false;
    status.pending_u64_bits=0;status.pending_u64_bytes=0;status.pending_u64_start=status.consumed_bytes;
    status.numeric_token_prefix.clear();status.last_scalar_byte_offset=status.consumed_bytes;
    if(status.requested_output==NumericEncoding::FullNumericJson&&index)punctuation(',');
    double value=status.requested_output==NumericEncoding::LosslessBinary?binaryDouble():jsonDouble();
    ++status.delivered_scalars;status.last_scalar_delivered=true;return value;
  }catch(const std::exception& e){fail(e.what());throw;}catch(...){fail("NONSTANDARD_SCALAR_FAILURE");throw;}}
  void finish(){try{
    need(!status.refused,"decoder first refusal retained");status.stage="CLOSE_COMPLETE_ARTIFACT";need(status.header_complete&&!status.artifact_closed&&!status.refused&&status.delivered_scalars==status.expected_scalars,"incomplete/replayed decoder closure");
    if(status.requested_output==NumericEncoding::FullNumericJson){punctuation(']');punctuation('}');ws();}
    need(status.consumed_bytes==expected.bytes&&next==available,"trailing/unconsumed cost artifact");
    struct stat now{};need(::fstat(fd,&now)==0&&now.st_dev==original_stat.st_dev&&now.st_ino==original_stat.st_ino&&now.st_size==original_stat.st_size,"cost artifact inode/size changed");
    unsigned char extra=0;ssize_t n;do{n=::read(fd,&extra,1);}while(n<0&&errno==EINTR);need(n==0,"cost artifact physical trailing/read-error");
    status.physical_prefix_sha256=digest();need(status.physical_prefix_sha256==expected.sha256,"complete consumed artifact SHA differs");
    status.artifact_closed=true;status.stage="ARTIFACT_CLOSED";
  }catch(const std::exception& e){fail(e.what());throw;}catch(...){fail("NONSTANDARD_EOF_FAILURE");throw;}}
};
struct CostInputFactory {
  static CostDecodeOutcome construct(AffineAssemblyOutcome&& source,const InitialCostConsumer& consumer){
    CostDecodeOutcome out(std::move(source));try{
      need(out.original_.hasCompleteAssembly(),"complete owned assembly required for cost decode");auto& a=out.original_.assembly();
      out.requested_=a.boundCostInputIdentity();const auto& plan=a.costPlan();auto& budget=a.costBudget();const auto shape=a.boundCostShape();
      auto state=std::make_shared<CostDecoderState>();out.state_=state;state->expected=out.requested_;state->partial.file=out.requested_;
      state->budget=&budget;state->dy=plan.dy();state->du=plan.du();state->shape=shape;state->samples=a.originalNormalization().maps().samples().size();
      state->metadata_cap=plan.metadataCeiling();state->artifact_cap=std::min(plan.outputCeiling(),ResourcePolicyV2::output_bytes);state->status.requested_output=plan.numericEncoding();
      need(state->status.requested_output==NumericEncoding::LosslessBinary||state->status.requested_output==NumericEncoding::FullNumericJson,"unknown requested codec; no fallback");
      const Count topology=add(shape.addition_coefficients/30,mul(shape.addition_records,4));state->partial.admitOwnedInput(budget,topology,16);
      state->input_owner=state->partial.owned_input_;state->cache=std::make_unique<std::array<unsigned char,128>>();state->open();state->metadata(a);
      CostInputRecipe recipe(std::move(state->partial));recipe.read_scalar=[state](Count i){return state->scalar(i);};recipe.finish_read=[state](){state->finish();};
      out.cost_.emplace(buildQuadraticCost(std::move(out.original_),std::move(recipe),consumer));
      if(!out.cost_->hasCompleteCost()){
        const auto reason=out.cost_->refusal();const char* why=reason.empty()?"UPSTREAM_COST_REFUSAL":reason.data();
        state->fail(why);out.refuse(why); // Copied callbacks now refuse before budget/FD access.
      }
    }catch(const std::exception& e){if(out.state_)out.state_->fail(e.what());out.refuse(e.what());}
    catch(...){if(out.state_)out.state_->fail("NONSTANDARD_DECODER_FAILURE");out.refuse("NONSTANDARD_DECODER_FAILURE");}return out;
  }
};
}
CostDecodeOutcome::CostDecodeOutcome(AffineAssemblyOutcome&& a) noexcept:original_(std::move(a)){}
CostDecodeOutcome::CostDecodeOutcome(CostDecodeOutcome&&) noexcept=default;
CostDecodeOutcome& CostDecodeOutcome::operator=(CostDecodeOutcome&&) noexcept=default;
CostDecodeOutcome::~CostDecodeOutcome()=default;
bool CostDecodeOutcome::hasCompleteCost() const noexcept{return !refused_&&state_&&state_->status.artifact_closed&&cost_&&cost_->hasCompleteCost();}
QuadraticCostOutcome& CostDecodeOutcome::costOutcome(){need(static_cast<bool>(cost_),"cost ingest outcome not reached");return *cost_;}
const AffineAssemblyOutcome& CostDecodeOutcome::originalAssembly() const{return cost_?cost_->originalAssembly():original_;}
const std::vector<CostTermLayout>& CostDecodeOutcome::parsedMetadataPrefix() const{
  if(cost_)return cost_->forensicInputRecipe().terms;need(static_cast<bool>(state_),"decoder absent");return state_->partial.terms;
}
CostDecodeObservation CostDecodeOutcome::observation() const{if(!state_)return {};auto out=state_->status;
  if(state_->hash&&state_->status.hash_valid)out.physical_prefix_sha256=state_->digest();return out;}
std::string_view CostDecodeOutcome::refusal() const noexcept{if(cost_&&!cost_->hasCompleteCost())return cost_->refusal();return refused_?(failure_.empty()?std::string_view("DECODER_REFUSAL_UNRECORDED_DETAIL"):std::string_view(failure_)):std::string_view{};}
void CostDecodeOutcome::refuse(const char* why) noexcept{if(refused_)return;refused_=true;try{failure_=why?why:"DECODER_REFUSAL";}catch(...){failure_.clear();}}
CostDecodeOutcome decodeAndBuildCost(AffineAssemblyOutcome&& a,const InitialCostConsumer& c){return detail::CostInputFactory::construct(std::move(a),c);}
}
