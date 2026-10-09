#include "model_boundary.hpp"
#include <yaml-cpp/yaml.h>
#include <openssl/evp.h>
#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <exception>
#include <cerrno>
#include <fcntl.h>
#include <fstream>
#include <limits>
#include <locale>
#include <map>
#include <optional>
#include <cstring>
#include <string_view>
#include <set>
#include <regex>
#include <sstream>
#include <stdexcept>
#include <utility>
#include <unistd.h>
#if defined(__linux__)
#include <link.h>
#include <sys/stat.h>
#include <sys/sysmacros.h>
#endif

namespace phase5_public_live_affine_v2 {
namespace {
using NativeModel = phase5_public_coupled_augmented_extension::Model;
using NativeState = phase5_public_coupled_augmented::State;
using NativeCell = phase5_public_coupled_augmented::Cell;
constexpr const char* units = "q/C rad,v/w rad/s,s dimensionless,r1/s; alpha rad/s^2,b1/s^2; time seconds; mass kg/armature kg*m^2";
void need(bool condition, const char* reason) {
  if (!condition) throw std::invalid_argument(reason);
}
Count difference(Count a,Count b) {
  need(a>=b,"integer planning subtraction underflow");return a-b;
}
const std::regex numericGrammar("-?(0|[1-9][0-9]*)(\\.[0-9]+)?([eE][+-]?[0-9]+)?");
bool plainScalar(const YAML::Node& n) { return n.IsScalar()&&n.Tag()=="?"; }
bool stringScalar(const YAML::Node& n) { return n.IsScalar()&&n.Tag()=="!"; }
void bounded(const std::string& s, Count cap, const char* reason) {
  need(!s.empty() && s.size() <= cap && s.find('\0') == std::string::npos, reason);
}
Count integer(const YAML::Node& n) {
  need(plainScalar(n), "untagged literal unsigned integer required");
  const auto text = n.Scalar();
  need(!text.empty() && (text.size() == 1 || text[0] != '0'), "noncanonical integer");
  Count result = 0;
  for (char c : text) {
    need(c >= '0' && c <= '9', "unsigned decimal integer required");
    result = checkedAdd(checkedMultiply(result, 10), static_cast<Count>(c - '0'));
  }
  return result;
}
double number(const YAML::Node& n) {
  need(plainScalar(n)&&std::regex_match(n.Scalar(),numericGrammar),"literal JSON number required");
  std::istringstream parser(n.Scalar());parser.imbue(std::locale::classic());double value=0;
  parser>>value;need(!parser.fail()&&parser.peek()==std::char_traits<char>::eof(),"numeric conversion failed");
  need(std::isfinite(value), "nonfinite frozen scalar"); return value;
}
std::string text(const YAML::Node& n, Count cap = 4096) {
  need(stringScalar(n), "quoted JSON string required"); auto value = n.Scalar();
  bounded(value, cap, "bounded nonempty text required"); return value;
}
void keys(const YAML::Node& n, std::initializer_list<const char*> expected) {
  need(n.IsMap() && n.size() == expected.size(), "exact object key roster required");
  std::set<std::string> actual;
  for (const auto& item : n) need(actual.insert(text(item.first)).second, "duplicate object key");
  for (const char* key : expected) need(actual.count(key) == 1, "missing/unknown object key");
}
class DocumentGrammar final {
  const std::string& bytes_;std::size_t pos_=0;Count depth_=0;
  void whitespace(){while(pos_<bytes_.size()&&(bytes_[pos_]==' '||bytes_[pos_]=='\t'||bytes_[pos_]=='\r'||bytes_[pos_]=='\n'))++pos_;}
  void take(char c){whitespace();need(pos_<bytes_.size()&&bytes_[pos_++]==c,"JSON punctuation required");}
  std::string string(){
    whitespace();const auto begin=pos_;need(pos_<bytes_.size()&&bytes_[pos_++]=='"',"quoted JSON string required");
    bool complete=false;
    while(pos_<bytes_.size()) {
      const unsigned char c=bytes_[pos_++];if(c=='"'){complete=true;break;}need(c>=32,"unescaped string control");
      if(c=='\\') {
        need(pos_<bytes_.size(),"incomplete string escape");const char escape=bytes_[pos_++];
        need(std::string("\"\\/bfnrtu").find(escape)!=std::string::npos,"invalid JSON escape");
        if(escape=='u')for(int k=0;k<4;++k){need(pos_<bytes_.size(),"short unicode escape");const char h=bytes_[pos_++];
          need((h>='0'&&h<='9')||(h>='a'&&h<='f')||(h>='A'&&h<='F'),"nonhex unicode escape");}
      }
    }
    need(complete,"unterminated JSON string");return YAML::Load(bytes_.substr(begin,pos_-begin)).Scalar();
  }
  void value(){
    whitespace();need(pos_<bytes_.size()&&++depth_<=64,"JSON depth/content bound");const char c=bytes_[pos_];
    if(c=='{') {
      ++pos_;whitespace();std::set<std::string> names;
      if(pos_<bytes_.size()&&bytes_[pos_]=='}')++pos_;
      else for(;;){need(names.insert(string()).second,"duplicate decoded JSON key");take(':');value();whitespace();
        need(pos_<bytes_.size(),"unterminated JSON object");if(bytes_[pos_]=='}'){++pos_;break;}take(',');}
    } else if(c=='[') {
      ++pos_;whitespace();if(pos_<bytes_.size()&&bytes_[pos_]==']')++pos_;
      else for(;;){value();whitespace();need(pos_<bytes_.size(),"unterminated JSON array");
        if(bytes_[pos_]==']'){++pos_;break;}take(',');}
    } else if(c=='"')string();
    else if(bytes_.compare(pos_,4,"true")==0)pos_+=4;
    else if(bytes_.compare(pos_,5,"false")==0)pos_+=5;
    else if(bytes_.compare(pos_,4,"null")==0)pos_+=4;
    else {const auto begin=pos_;while(pos_<bytes_.size()&&std::string("-+0123456789.eE").find(bytes_[pos_])!=std::string::npos)++pos_;
      need(pos_>begin&&std::regex_match(bytes_.substr(begin,pos_-begin),numericGrammar),"JSON numeric grammar required");}
    --depth_;
  }
 public:
  explicit DocumentGrammar(const std::string& bytes):bytes_(bytes){}
  void check(){value();whitespace();need(pos_==bytes_.size(),"JSON trailing content refused");}
};
struct Artifact { std::string role; FileIdentity identity; };
Artifact artifact(const YAML::Node& n) {
  keys(n, {"role", "path", "sha256", "bytes"});
  Artifact a{ text(n["role"], 128), {text(n["path"]), text(n["sha256"],64), integer(n["bytes"])} };
  need(a.identity.path.front() == '/' && a.identity.bytes > 0, "absolute nonempty artifact required");
  return a;
}
FileIdentity verify(const FileIdentity& expected) {
  auto observed = observePinnedFile(expected.path, expected.sha256);
  need(observed.bytes == expected.bytes, "artifact byte length mismatch"); return observed;
}
YAML::Node readDocument(const FileIdentity& expected) {
  need(expected.bytes <= ResourcePolicyV2::metadata_bytes, "bounded metadata document required");
  verify(expected);
  std::ifstream input(expected.path, std::ios::binary);
  need(static_cast<bool>(input), "cannot read pinned document");
  std::string bytes(static_cast<std::size_t>(expected.bytes), '\0');
  input.read(&bytes[0], static_cast<std::streamsize>(bytes.size()));
  need(input.gcount() == static_cast<std::streamsize>(bytes.size()) && input.peek() == EOF,
       "pinned document size changed");
  std::array<unsigned char,EVP_MAX_MD_SIZE> digest{};unsigned int length=0;
  need(EVP_Digest(bytes.data(),bytes.size(),digest.data(),&length,EVP_sha256(),nullptr)==1&&length==32,
       "document SHA256 computation failed");
  std::string observed;constexpr char hex[]="0123456789abcdef";
  for(unsigned int j=0;j<length;++j){observed.push_back(hex[digest[j]>>4]);observed.push_back(hex[digest[j]&15]);}
  need(observed==expected.sha256,"actual parsed document bytes differ from reviewed SHA256");
  // Recheck the file after the bounded read. The compiled release additionally
  // requires immutable input files; this is not an adversarial filesystem lock.
  verify(expected);
  DocumentGrammar(bytes).check();return YAML::Load(bytes);
}
Eigen::VectorXd vector(const YAML::Node& n, Count expected) {
  need(n.IsSequence() && n.size() == expected && expected <= 512, "metadata vector roster mismatch");
  Eigen::VectorXd v(static_cast<Eigen::Index>(expected));
  for (Count k = 0; k < expected; ++k) v(static_cast<Eigen::Index>(k)) = number(n[static_cast<std::size_t>(k)]);
  return v;
}
JointVector joints(const YAML::Node& n) {
  need(n.IsSequence() && n.size() == 7, "joint vector dimension7 required");
  JointVector out{}; for (std::size_t j = 0; j < 7; ++j) out[j] = number(n[j]); return out;
}
State30 state(const YAML::Node& n) {
  keys(n, {"q","v","C","w","s","r"});
  return {joints(n["q"]), joints(n["v"]), joints(n["C"]), joints(n["w"]), number(n["s"]), number(n["r"])};
}
bool equalState(const State30& a, const State30& b) {
  return a.q==b.q && a.v==b.v && a.C==b.C && a.w==b.w && a.s==b.s && a.r==b.r;
}
NativeState nativeState(const State30& s) {
  NativeState out; out.q.resize(7); out.v.resize(7); out.C.resize(7); out.w.resize(7);
  for (std::size_t j=0;j<7;++j) { out.q(j)=s.q[j];out.v(j)=s.v[j];out.C(j)=s.C[j];out.w(j)=s.w[j]; }
  out.s=s.s;out.r=s.r;return out;
}
NativeMetadata metadata(const FileIdentity& file) {
  auto n=readDocument(file);
  keys(n,{"pinocchio_version","nq","nv","joint_names","frame_names","idx_q","idx_v",
          "joint_nq","joint_nv","masses","armature","gravity","R","B","damping","units"});
  need(text(n["units"])==units && text(n["pinocchio_version"])=="4.1.0" &&
       integer(n["nq"])==7 && integer(n["nv"])==7,"fixed metadata version/dimensions/declared units");
  NativeMetadata out;out.nq=7;out.nv=7;out.pinocchio_version="4.1.0";
  for (const char* name:{"joint_names","frame_names"}) {
    const auto v=n[name];need(v.IsSequence()&&v.size()>0&&v.size()<=512,"name roster required");
    auto& dest=std::string(name)=="joint_names"?out.joint_names:out.frame_names;
    for (const auto& item:v) dest.push_back(text(item,256));
  }
  need(out.joint_names.size()==7,"fixed7 joint names required");
  for (const char* name:{"idx_q","idx_v","joint_nq","joint_nv"}) {
    const auto v=n[name];need(v.IsSequence()&&v.size()==7,"fixed7 joint index roster required");
    auto* dest=std::string(name)=="idx_q"?&out.idx_q:std::string(name)=="idx_v"?&out.idx_v:
               std::string(name)=="joint_nq"?&out.joint_nq:&out.joint_nv;
    for (std::size_t j=0;j<7;++j) {
      const Count expected=(std::string(name)=="idx_q"||std::string(name)=="idx_v")?j:1;
      need(integer(v[j])==expected,"fixed scalar joint mapping required");dest->push_back(static_cast<int>(expected));
    }
  }
  out.masses=vector(n["masses"],8);out.armature=vector(n["armature"],7);out.gravity=vector(n["gravity"],3);
  out.R=vector(n["R"],7);out.B=vector(n["B"],7);out.damping=vector(n["damping"],7);
  need((out.masses.array()>=0).all()&&(out.armature.array()>=0).all()&&
       (out.R.array()>0).all()&&(out.B.array()>0).all()&&(out.damping.array()>=0).all(),"fixed metadata coefficient domain");
  return out;
}
void compareMetadata(const NativeMetadata& actual,const NativeMetadata& expected) {
  need(actual.pinocchio_version==expected.pinocchio_version&&actual.nq==7&&actual.nv==7&&
    actual.joint_names==expected.joint_names&&actual.frame_names==expected.frame_names&&
    actual.idx_q==expected.idx_q&&actual.idx_v==expected.idx_v&&actual.joint_nq==expected.joint_nq&&
    actual.joint_nv==expected.joint_nv,"actual model metadata identity mismatch");
  const std::array<std::pair<const Eigen::VectorXd*,const Eigen::VectorXd*>,6> pairs={{{&actual.masses,&expected.masses},
    {&actual.armature,&expected.armature},{&actual.gravity,&expected.gravity},{&actual.R,&expected.R},
    {&actual.B,&expected.B},{&actual.damping,&expected.damping}}};
  for (const auto& pair:pairs) need(pair.first->size()==pair.second->size()&&pair.first->allFinite()&&
    (pair.first->array()==pair.second->array()).all(),"actual numeric model metadata mismatch");
}

#if defined(__linux__)
std::string canonical(const std::string& p) {
  std::unique_ptr<char,decltype(&std::free)> value(::realpath(p.c_str(),nullptr),std::free);
  need(static_cast<bool>(value),"loaded library canonical path unavailable");return value.get();
}
struct LoaderNames { std::set<std::string> paths; std::exception_ptr error; };
int loaded(struct dl_phdr_info* info,std::size_t,void* data) {
  auto& result=*static_cast<LoaderNames*>(data);
  try {
    const std::string name=info->dlpi_name?info->dlpi_name:"";
    if (!name.empty()&&name!="linux-vdso.so.1") result.paths.insert(canonical(name));
  } catch (...) { result.error=std::current_exception();return 1; }
  return 0;
}
void mappedIdentity(const std::string& path) {
  struct stat st{};need(::stat(path.c_str(),&st)==0&&S_ISREG(st.st_mode),"loaded library stat failed");
  std::ifstream maps("/proc/self/maps");need(static_cast<bool>(maps),"process map inventory unavailable");
  std::string line;bool found=false;Count lines=0;
  while(std::getline(maps,line)) {
    need(++lines<=262144&&line.size()<=16384,"process map inventory bound exceeded");
    std::istringstream row(line);std::string address,permissions,offset,device,name;Count inode=0;
    if (!(row>>address>>permissions>>offset>>device>>inode)) continue;
    std::getline(row,name);const auto first=name.find_first_not_of(' ');if(first==std::string::npos)continue;name=name.substr(first);
    if(name!=path)continue;
    const auto split=device.find(':');need(split!=std::string::npos,"invalid process map device");
    const auto major_id=std::stoull(device.substr(0,split),nullptr,16),minor_id=std::stoull(device.substr(split+1),nullptr,16);
    need(inode==static_cast<Count>(st.st_ino)&&major_id==major(st.st_dev)&&minor_id==minor(st.st_dev),
         "loaded library file inode/device mismatch");found=true;
  }
  need(found,"reviewed library absent from actual process mappings");
}
// V2-specific bounded loader observation. Legacy helpers above are unchanged.
std::string memberCanonical(const char* path,SharedCaseBudget budget){need(path,"member loaded path absent");const auto length=::strnlen(path,4097);need(length>0&&length<=4096,"member actual loader path cap before copy");auto ticket=budget.reserve(528);budget.chargeScratchOrCopy(513);std::array<char,4097> buffer{};need(::realpath(path,buffer.data()),"member canonical loader path unavailable");const auto bytes=::strnlen(buffer.data(),buffer.size());need(bytes>0&&bytes<=4096,"member canonical result cap");budget.chargeMetadataBytes(bytes);budget.chargeScratchOrCopy((bytes+7)/8);return std::string(buffer.data(),bytes);}
struct MemberLoaderNames {SharedCaseBudget budget;MemberLoaderObservationV1& observation;std::set<std::string> paths;std::exception_ptr error;};
int memberLoaded(struct dl_phdr_info* info,std::size_t,void* data){auto& result=*static_cast<MemberLoaderNames*>(data);try{result.budget.chargeScratchOrCopy(4);const char* name=info->dlpi_name;if(name&&*name){const auto length=::strnlen(name,4097);need(length<=4096,"actual loader path length overflow");if(std::string_view(name,length)!="linux-vdso.so.1"){need(result.paths.size()<512,"member actual loader set cap");auto path=memberCanonical(name,result.budget);result.paths.insert(std::move(path));}}}catch(...){result.observation.refused=true;result.error=std::current_exception();return 1;}return 0;}
void memberMapped(const std::string& path,SharedCaseBudget budget,const MemberIdentityObservationV1& identity,MemberLoaderObservationV1& observation){
  auto ticket=budget.reserve(2088); // line16384=2048/cache128=16/control24.
  struct FD{int value=-1;~FD(){if(value>=0)::close(value);}} fd{::open("/proc/self/maps",O_RDONLY|O_CLOEXEC)};need(fd.value>=0,"actual member process maps unavailable");
  std::array<char,16384> line;std::array<unsigned char,128> cache;Count available=0,next=0,length=0,lines=0;bool found=false;
  auto get=[&](){if(next==available){budget.chargeScratchOrCopy(16);const auto n=::read(fd.value,cache.data(),cache.size());if(n<0&&errno==EINTR)return -2;need(n>=0,"member maps read error");if(n==0)return -1;available=n;next=0;}return static_cast<int>(cache[next++]);};
  auto parse=[&](){budget.chargeScratchOrCopy(24);observation.lines=++lines;need(lines<=262144,"member map line count cap");Count at=0;
    auto token=[&](){while(at<length&&line[at]==' ')++at;const Count start=at;while(at<length&&line[at]!=' ')++at;return std::string_view(line.data()+start,at-start);};
    const auto address=token(),permissions=token(),offset=token(),device=token(),inodeText=token();(void)address;(void)permissions;(void)offset;if(inodeText.empty())return;
    while(at<length&&line[at]==' ')++at;const std::string_view actual_path(line.data()+at,length-at);if(actual_path!=path)return;
    auto integer=[&](std::string_view value,Count base){need(!value.empty()&&value.size()<=20,"member map integer token bound");Count out=0;for(char c:value){Count digit=c>='0'&&c<='9'?c-'0':c>='a'&&c<='f'?c-'a'+10:c>='A'&&c<='F'?c-'A'+10:base;need(digit<base,"member map device/inode token");out=checkedAdd(checkedMultiply(out,base),digit);}return out;};
    const auto colon=device.find(':');need(colon!=std::string_view::npos,"member map device separator");observation.inode=integer(inodeText,10);observation.major_id=integer(device.substr(0,colon),16);observation.minor_id=integer(device.substr(colon+1),16);observation.parsed=true;
    need(observation.inode==identity.inode&&observation.major_id==major(static_cast<dev_t>(identity.device))&&observation.minor_id==minor(static_cast<dev_t>(identity.device)),"actual member mapping inode/device mismatch");found=true;
  };
  observation.stage="READ_ACTUAL_MEMBER_MAPS";budget.chargeScratchOrCopy(2048);for(;;){const int ch=get();if(ch==-2)continue;if(ch<0){if(length)parse();break;}if(ch=='\n'){parse();length=0;budget.chargeScratchOrCopy(2048);}else{need(length<line.size(),"member map line byte cap");line[length++]=static_cast<char>(ch);}}
  need(found,"actual member library absent from process maps");observation.mapped=true;
}
void verifyMemberLoadedLibraries(const std::vector<FileIdentity>& libraries,SharedCaseBudget budget,MemberIdentityObservationV1& identity,MemberLoaderObservationV1& observation,MemberCaptureStatus& status){
  try{budget.chargeScratchOrCopy(16);observation=MemberLoaderObservationV1{};observation.stage="ACTUAL_MEMBER_LOADER_SET";MemberLoaderNames names{budget,observation,{},nullptr};::dl_iterate_phdr(memberLoaded,&names);if(names.error)std::rethrow_exception(names.error);
    std::set<std::string> expected;for(Count index=0;index<libraries.size();++index){budget.chargeScratchOrCopy(12);observation.current_library_index=index;observation.current_library_known=true;observation.lines=0;observation.inode=0;observation.major_id=0;observation.minor_id=0;observation.parsed=false;observation.mapped=false;observation.stage="CANONICAL_CURRENT_DECLARED_LIBRARY";const auto& file=libraries[index];auto canonical_path=memberCanonical(file.path.c_str(),budget);need(canonical_path==file.path&&expected.insert(std::move(canonical_path)).second,"member canonical SDK declaration duplicate/differs");budget.chargeScratchOrCopy(20);identity=MemberIdentityObservationV1{};status.identity_target_kind=MemberIdentityTargetKind::DeclaredLibrary;status.identity_target_index=index;status.identity_target_known=true;status.active_member_known=false;observePinnedFileWithMemberBudgetV1(budget,file,identity);memberMapped(file.path,budget,identity,observation);observation.libraries_checked=index+1;}
    need(names.paths==expected,"actual member loader set differs from complete SDK declaration");observation.libraries_checked=libraries.size();observation.stage="VERIFIED_ACTUAL_MEMBER_LOADER_SET";
  }catch(...){observation.refused=true;throw;}
}
#endif
void verifyLoadedLibraries(const std::vector<FileIdentity>& libraries) {
#if defined(__linux__)
  LoaderNames names;::dl_iterate_phdr(loaded,&names);if(names.error)std::rethrow_exception(names.error);
  std::set<std::string> expected;
  for(const auto& file:libraries) {
    need(canonical(file.path)==file.path&&expected.insert(file.path).second,"canonical unique SDK library path required");
    verify(file);mappedIdentity(file.path);
  }
  need(names.paths==expected,"complete actual loaded DSO inventory differs from reviewed SDK closure");
#else
  (void)libraries;throw std::invalid_argument("live SDK identity requires Linux loader/map inventory");
#endif
}
} // namespace

namespace detail {
struct ClaimCaptureData {
  SharedCaseBudget budget;OwnedReservation ticket;std::shared_ptr<const void> source;
  std::array<unsigned char,324> expected{};std::array<unsigned char,325> readback{};
  ClaimCaptureFactsV1 facts;
  ClaimCaptureData(SharedCaseBudget b,std::shared_ptr<const void> tag):budget(std::move(b)),ticket(budget.reserve(182)),source(std::move(tag)){}
  // Payload/metadata arrays and source die before ticket; no owner cycle.
};
// Private primitives; no output_chunks dependency and no caller IO callback.
#if defined(__linux__)
struct ClaimIOV1 {
  static void attempt(ClaimCaptureData& d,const char* stage,Count extra=0){
    auto& h=d.facts;h.stage=stage;need(h.io_attempts<1024,"claim syscall-attempt cap; retained no retry");
    d.budget.chargeScratchOrCopy(checkedAdd(128,extra));++h.io_attempts;h.last_errno=0;h.last_return=0;
  }
  static std::int64_t result(ClaimCaptureFactsV1& h,std::int64_t n){h.last_return=n;h.last_errno=n<0?errno:0;return n;}
  static void statFacts(ClaimCaptureFactsV1& h,const struct stat& st){
    h.last_stat_device=st.st_dev;h.last_stat_inode=st.st_ino;h.last_stat_size=st.st_size;
    h.last_stat_mode=st.st_mode;h.last_stat_links=st.st_nlink;h.last_stat_known=true;
  }
  static void fdStat(ClaimCaptureData& d,int fd,struct stat& st,ClaimStatTargetV1 target,const char* stage){
    auto& h=d.facts;h.last_stat_target=target;h.last_stat_known=false;attempt(d,stage);
    need(result(h,::fstat(fd,&st))==0,"claim actual FD stat failed");statFacts(h,st);
  }
  static bool regular(const struct stat& st){return S_ISREG(st.st_mode)&&st.st_nlink==1&&st.st_size>=0&&(st.st_mode&07777)==0600;}
  static void digest(ClaimCaptureData& d,EVP_MD_CTX* md,std::array<char,64>& held,bool& known,Count* count=nullptr,Count bytes=0){
    d.budget.chargeScratchOrCopy(72);d.budget.chargeMetadataBytes(64);
    using Ptr=std::unique_ptr<EVP_MD_CTX,decltype(&EVP_MD_CTX_free)>;
    Ptr clone(EVP_MD_CTX_new(),EVP_MD_CTX_free);need(clone&&EVP_MD_CTX_copy_ex(clone.get(),md)==1,"claim actual digest clone failed");
    std::array<unsigned char,32> raw{};unsigned length=0;
    need(EVP_DigestFinal_ex(clone.get(),raw.data(),&length)==1&&length==32,"claim actual prefix digest final failed");
    constexpr char hex[]="0123456789abcdef";for(unsigned i=0;i<32;++i){held[2*i]=hex[raw[i]>>4];held[2*i+1]=hex[raw[i]&15];}
    if(count)*count=bytes;known=true;
  }
};
struct ClaimFDV1 {
  enum class Kind {Other,Writer,Reader,Parent};ClaimCaptureFactsV1& h;int fd=-1;Kind kind=Kind::Other;
  explicit ClaimFDV1(ClaimCaptureFactsV1& status,Kind k=Kind::Other):h(status),kind(k){}
  ClaimFDV1(const ClaimFDV1&)=delete;ClaimFDV1& operator=(const ClaimFDV1&)=delete;
  void flags(bool ok){if(kind==Kind::Writer){h.write_close_attempted=true;h.write_closed=ok;}if(kind==Kind::Reader){h.read_close_attempted=true;h.read_closed=ok;}if(kind==Kind::Parent){h.parent_close_attempted=true;h.parent_closed=ok;}}
  bool closeNow(){if(fd<0)return true;const int value=fd;fd=-1;++h.close_attempts;const int code=::close(value);h.last_close_return=code;flags(code==0);if(code==0)++h.close_successes;else {h.cleanup_close_failed=true;h.cleanup_errno=errno;}return code==0;}
  void closeChecked(ClaimCaptureData& d,const char* stage){ClaimIOV1::attempt(d,stage);need(closeNow(),"claim descriptor close failed; never close-retried");}
  ~ClaimFDV1(){closeNow();} // Cleanup work prepaid64; never retries, unlinks or overwrites.
};
#endif
struct ContextCaptureControl {
  SharedCaseBudget budget;OwnedReservation ticket;
  bool enabled=true,attempted=false;std::shared_ptr<const void> origin;
  std::optional<CapturedLiveActualContextV1> snapshot;
  explicit ContextCaptureControl(SharedCaseBudget b):budget(std::move(b)),ticket(budget.reserve(8)){
    budget.chargeScratchOrCopy(8);struct ActualContextOrigin {};origin=std::make_shared<ActualContextOrigin>();
  }
  // Actual context fields/source/wrapper identities are materialized after ticket.
};
struct MemberCaptureStorage {
  SharedCaseBudget budget;OwnedReservation ticket;ResourcePlan plan;
  std::unique_ptr<CaseBudget> pending_case;FileIdentity planned_invocation;std::vector<VerifiedMemberRelation> relations;
  std::shared_ptr<ContextCaptureControl> context;std::shared_ptr<ClaimCaptureData> claim;
  MemberCaptureStatus status;MemberIdentityObservationV1 latest_identity;MemberLoaderObservationV1 latest_loader;bool copy_scope_active=false;
  MemberCaptureStorage(std::unique_ptr<CaseBudget> c,const ResourcePlan& p,Count slots):budget(c->share()),ticket(budget.reserve(slots)),plan(p),pending_case(std::move(c)){}
  void reject(const char* why) noexcept{if(status.refused)return;status.refused=true;status.complete=false;try{std::string_view s=why?why:"MEMBER_CAPTURE_REFUSAL";need(s.size()<=512,"member refusal detail cap");budget.chargeMetadataBytes(s.size());status.first_error.assign(s);}catch(...){}}
  void rejectClaim(const char* why) noexcept{if(status.refused)return;status.refused=true;status.complete=false;try{std::string_view text=why?why:"ACTUAL_CLAIM_REFUSAL";need(text.size()<=512,"claim member detail cap");budget.chargeMetadataBytes(text.size());budget.chargeScratchOrCopy((text.size()+7)/8);status.first_error.assign(text);}catch(...){}}
};
struct ForecastReleaseState {
  std::shared_ptr<MemberCaptureStorage> members; // Dies AFTER the actual identity/string lists.

  FileIdentity review,protocol,producer,xml,constants,policy,expected_metadata,invocation;
  std::vector<FileIdentity> files,libraries;std::vector<std::string> file_roles;
  std::string attempt_claim_path;
  Count prepare_attempts=0,open_attempts=0,forecast_attempts=0;
  Count constructor_attempts=0,metadata_attempts=0,rollout_attempts=0;
};
struct InvocationStorage {
  CaseBudget budget;OwnedReservation ticket;ResourcePlan plan;LiveActualContext context;
  CycleMesh mesh;NativeState initial;std::vector<NativeCell> cells;
  std::shared_ptr<ForecastReleaseState> release;
  FactorShape factors;FileIdentity cost_input;std::string cost_semantic_sha256;std::optional<CapturedLiveActualContextV1> captured_context;
  InvocationStorage(BatchBudget& batch,const ResourcePlan& p,const LiveActualContext& c,const CycleMesh& m,
                    std::shared_ptr<ForecastReleaseState> r)
    :budget(batch,p),ticket(budget.reserve(checkedAdd(128,checkedMultiply(10,m.cycles().size())))),
     plan(p),context(c),mesh(m),release(std::move(r)) {}
  InvocationStorage(CaseBudget&& existing,const ResourcePlan& p,const LiveActualContext& c,const CycleMesh& m,std::shared_ptr<ForecastReleaseState> r)
    :budget(std::move(existing)),ticket(budget.reserve(checkedAdd(128,checkedMultiply(10,m.cycles().size())))),plan(p),context(c),mesh(m),release(std::move(r)){}
  // Native initial/cells/context are destroyed before ticket (budget survives all).
};
struct ProfileStorage {
  OwnedReservation ticket;std::shared_ptr<ForecastReleaseState> release;
  NativeMetadata expected;std::unique_ptr<NativeMetadata> observed;
  explicit ProfileStorage(InvocationStorage& i):ticket(i.budget.reserve(1000000)),release(i.release){}
};
struct HandleStorage {
  std::shared_ptr<ProfileStorage> profile;std::shared_ptr<InvocationStorage> invocation;
  std::unique_ptr<NativeModel> model; // Destroy model BEFORE shared profile ticket.
};
struct OpenStorage {
  std::shared_ptr<ProfileStorage> profile;std::unique_ptr<PinnedModelHandle> handle;
  std::string refusal;bool constructor_attempted=false,metadata_attempted=false;
};
struct ForecastStorage {
  OwnedReservation result_ticket;std::shared_ptr<ProfileStorage> profile;
  std::shared_ptr<InvocationStorage> invocation;
  std::string transport_failure,structural_refusal;
  std::unique_ptr<RawResult> raw; // Complete raw destroyed BEFORE result ticket.
  explicit ForecastStorage(HandleStorage& h)
    :result_ticket(h.invocation->budget.reserve(difference(checkedMultiply(3,h.invocation->plan.rawResultShapeSlots()),
          h.invocation->ticket.slots()))),profile(h.profile),invocation(h.invocation){}
};

struct ForecastFactory {
  static std::shared_ptr<ForecastReleaseState> valid(ReviewedForecastPermission& permission) {
    need(static_cast<bool>(permission.release_),"missing/moved-from reviewed release");need(!permission.release_->members||!permission.release_->members->status.refused,"member admission first refusal retained");return permission.release_;
  }
  static void recheck(ForecastReleaseState& r){
    if(!r.members){verify(r.review);verify(r.protocol);observeCurrentProducerElf(r.producer.sha256);for(const auto& f:r.files)verify(f);verifyLoadedLibraries(r.libraries);return;}
    auto& m=*r.members;try{auto frame=m.budget.reserve(40);m.budget.chargeScratchOrCopy(40);need(!m.status.refused&&m.status.admitted,"member source not admitted/first refusal retained");
      auto check=[&](const FileIdentity& f,MemberIdentityTargetKind kind,Count index=0){m.budget.chargeScratchOrCopy(20);m.status.identity_target_kind=kind;m.status.identity_target_index=index;m.status.identity_target_known=true;m.status.active_member_known=false;m.latest_identity=MemberIdentityObservationV1{};observePinnedFileWithMemberBudgetV1(m.budget,f,m.latest_identity);};
      check(r.review,MemberIdentityTargetKind::Review);check(r.protocol,MemberIdentityTargetKind::Protocol);{m.budget.chargeScratchOrCopy(20);m.status.identity_target_kind=MemberIdentityTargetKind::Producer;m.status.identity_target_index=0;m.status.identity_target_known=true;m.status.active_member_known=false;m.latest_identity=MemberIdentityObservationV1{};observeCurrentProducerElfWithMemberBudgetV1(m.budget,r.producer.sha256,r.producer.bytes,m.latest_identity);}for(Count i=0;i<r.files.size();++i)check(r.files[i],MemberIdentityTargetKind::MemberFile,i);
      #if defined(__linux__)
      verifyMemberLoadedLibraries(r.libraries,m.budget,m.latest_identity,m.latest_loader,m.status);
#else
      throw std::invalid_argument("member loaded verifier requires Linux");
#endif
      m.budget.chargeScratchOrCopy(1);++m.status.verified_loader_checks;
    }catch(const std::exception& e){m.reject(e.what());throw;}catch(...){m.reject("NONSTANDARD_MEMBER_RECHECK");throw;}
  }
  struct MemberPlanDescriptor {CycleMesh mesh;FactorShape factors;CaptureMode mode;NumericEncoding encoding;ResourcePlan base;};
  static MemberPlanDescriptor memberBasePlan(const YAML::Node& n){
    keys(n,{"schema","source_kind","units","boundary","initial","previous_alpha","previous_b","mesh","controls","factor_shape","capture_mode","encoding","cost_input"});need(text(n["schema"])=="PUBLIC_LIVE_AFFINE_V2_INVOCATION_COST_BOUND_2"&&text(n["source_kind"])=="LiveActual"&&text(n["units"])==units,"wrong actual member invocation");
    auto m=n["mesh"];keys(m,{"steps","total_macro_cycles","policy","explicit_cycles"});HorizonSpec spec;spec.steps=integer(m["steps"]);spec.total_macro_cycles=integer(m["total_macro_cycles"]);const auto policy=text(m["policy"]);if(policy=="UniformExact")spec.policy=MeshPolicy::UniformExact;else if(policy=="BalancedInteger")spec.policy=MeshPolicy::BalancedInteger;else if(policy=="ExplicitCycles")spec.policy=MeshPolicy::ExplicitCycles;else throw std::invalid_argument("member mesh policy");need(m["explicit_cycles"].IsSequence()&&m["explicit_cycles"].size()<=32,"member explicit cycles bound");for(const auto& v:m["explicit_cycles"])spec.explicit_cycles.push_back(integer(v));auto mesh=planMesh(spec);
    auto f=n["factor_shape"];keys(f,{"terms","rows","largest_term_rows","addition_coefficients","addition_records"});FactorShape shape{integer(f["terms"]),integer(f["rows"]),integer(f["largest_term_rows"]),integer(f["addition_coefficients"]),integer(f["addition_records"])};
    const auto mode=text(n["capture_mode"]),encoding=text(n["encoding"]);need(mode=="CompactComplete"||mode=="DenseAuditComplete","member mode");need(encoding=="LosslessBinary"||encoding=="FullNumericJson","member encoding");const auto cm=mode=="CompactComplete"?CaptureMode::CompactComplete:CaptureMode::DenseAuditComplete;const auto enc=encoding=="LosslessBinary"?NumericEncoding::LosslessBinary:NumericEncoding::FullNumericJson;
    return {mesh,shape,cm,enc,planResources(mesh,shape,cm,enc)};
  }
  static ResourcePlan memberPlan(const MemberPlanDescriptor& d,Count slots,Count charges,bool claim=false){return claim?planResourcesWithMemberClaimCaptureV2(d.mesh,d.factors,d.mode,d.encoding,slots,charges):planResourcesWithMemberCaptureV1(d.mesh,d.factors,d.mode,d.encoding,slots,charges);}
  static bool sameBasePlan(const ResourcePlan& base,const ResourcePlan& added,bool claim=false){return base.dx()==added.dx()&&base.du()==added.du()&&base.dy()==added.dy()&&base.captureMode()==added.captureMode()&&base.numericEncoding()==added.numericEncoding()&&base.rawResultShapeSlots()==added.rawResultShapeSlots()&&base.sdkPlanningAllowance()==added.sdkPlanningAllowance()&&checkedAdd(base.liveCeiling(),added.memberCaptureSlots())==added.liveCeiling()&&checkedAdd(base.chargeCeiling(),added.memberCaptureCharges())==added.chargeCeiling()&&checkedAdd(base.outputCeiling(),claim?324:0)==added.outputCeiling();}
  struct MemberFrame {MemberCaptureStorage& m;std::optional<OwnedReservation> ticket;bool acquired=false;MemberFrame(MemberCaptureStorage& state):m(state){need(!m.status.refused,"member first refusal retained");if(!m.copy_scope_active){ticket.emplace(m.budget.reserve(40));m.copy_scope_active=true;acquired=true;}m.budget.chargeScratchOrCopy(40);}~MemberFrame(){if(acquired)m.copy_scope_active=false;}};
  static void memberKeys(const YAML::Node& node,MemberCaptureStorage& m,std::initializer_list<const char*> names){need(node.IsMap()&&node.size()==names.size(),"member exact key count before copies");for(const auto& field:node){need(stringScalar(field.first),"member quoted key");const auto& name=field.first.Scalar();bounded(name,128,"member key before copy");m.budget.chargeMetadataBytes(name.size());m.budget.chargeScratchOrCopy((name.size()+7)/8);}keys(node,names);}
  static Count memberInteger(const YAML::Node& n,MemberCaptureStorage& m){need(plainScalar(n),"member literal unsigned integer");const std::string& value=n.Scalar();need(!value.empty()&&value.size()<=20&&(value.size()==1||value[0]!='0'),"member canonical integer token cap");m.budget.chargeScratchOrCopy(4);Count out=0;for(char c:value){need(c>='0'&&c<='9',"member unsigned token");out=checkedAdd(checkedMultiply(out,10),c-'0');}return out;}
  static std::string memberText(const YAML::Node& n,MemberCaptureStorage& m,Count cap){need(stringScalar(n),"actual member quoted string");const std::string& value=n.Scalar();bounded(value,cap,"member text cap before copy");m.budget.chargeMetadataBytes(value.size());m.budget.chargeScratchOrCopy((value.size()+7)/8);return value;}
  static Artifact memberArtifact(const YAML::Node& n,MemberCaptureStorage& m){MemberFrame frame(m);memberKeys(n,m,{"role","path","sha256","bytes"});Artifact a{memberText(n["role"],m,128),{memberText(n["path"],m,4096),memberText(n["sha256"],m,64),memberInteger(n["bytes"],m)}};need(a.identity.path.front()=='/'&&a.identity.bytes>0&&a.identity.bytes<=512ULL*1024*1024,"actual member artifact envelope");return a;}
  static Count parentIndex(const ForecastReleaseState& r,std::string_view role){need(r.members&&!r.members->status.refused,"member parent unavailable");for(Count i=0;i<r.members->relations.size();++i){const auto& relation=r.members->relations[i];if(relation.group==VerifiedMemberGroup::Protocol&&r.file_roles[i]==role)return i;}throw std::invalid_argument("actual parent not captured");}
  static void appendMember(ForecastReleaseState& r,const std::string& role,const FileIdentity& file,VerifiedMemberGroup group,Count parent,bool protocol_parent,Count ordinal){auto& m=*r.members;try{need(m.status.admitted&&!m.status.refused&&r.files.size()==r.file_roles.size()&&r.files.size()==m.relations.size()&&r.files.size()<m.status.expected_files&&r.files.size()<r.files.capacity()&&r.file_roles.size()<r.file_roles.capacity()&&m.relations.size()<m.relations.capacity(),"member actual append invariant");need(protocol_parent||parent<r.files.size(),"member genuine parent index");bounded(role,128,"member role bound before copy");bounded(file.path,4096,"member path bound before copy");bounded(file.sha256,64,"member SHA before copy");need(file.bytes>0,"member actual nonempty identity");
    MemberFrame frame(m);m.budget.chargeMetadataBytes(checkedAdd(role.size(),checkedAdd(file.path.size(),file.sha256.size())));m.budget.chargeScratchOrCopy(checkedAdd(9,(role.size()+file.path.size()+file.sha256.size()+7)/8));
    const Count index=r.files.size();VerifiedMemberRelation relation{index,parent,ordinal,0,group,protocol_parent,false,true};r.files.push_back(file);r.file_roles.push_back(role);m.relations.push_back(relation);m.status.actual_files=r.files.size();
    }catch(const std::exception& e){m.reject(e.what());throw;}catch(...){m.reject("NONSTANDARD_MEMBER_APPEND");throw;}}
  static ReviewedForecastPermission permission(const ReviewPins& pins,BatchBudget* member_batch=nullptr,bool context=false,bool claim_capture=false) {
    // The external dispatch supplies the trusted review digest. Merely creating
    // a protocol file or choosing a digest does not authorize its execution.
    auto review_id=observePinnedFile(pins.review_record_path,pins.review_record_sha256);
    auto review=readDocument(review_id);
    keys(review,{"schema","decision","scope","protocol","phase5","phase6"});
    need(text(review["schema"])=="PUBLIC_LIVE_AFFINE_V2_RUN_REVIEW_1"&&
      text(review["decision"])=="RELEASED_FOR_ONE_BOUND_COMPONENT_ATTEMPT"&&
      text(review["scope"])=="MODEL_CONSTRUCTOR_METADATA_AND_ONE_LIVE_FORECAST_ONLY"&&
      text(review["phase5"])=="NOT_ACCEPTED"&&text(review["phase6"])=="NOT_STARTED","wrong reviewed release scope");
    auto protocol_artifact=artifact(review["protocol"]);need(protocol_artifact.role=="protocol","protocol role mismatch");
    auto p=readDocument(protocol_artifact.identity);
    if(claim_capture)keys(p,{"schema","source_kind","producer_sha256","constructor_attempts","metadata_attempts","rollout_attempts","scope_claims","artifacts","attempt_claim_path","member_capture_policy","context_capture_policy","claim_capture_policy"});
    else if(context)keys(p,{"schema","source_kind","producer_sha256","constructor_attempts","metadata_attempts","rollout_attempts","scope_claims","artifacts","attempt_claim_path","member_capture_policy","context_capture_policy"});
    else if(member_batch)keys(p,{"schema","source_kind","producer_sha256","constructor_attempts","metadata_attempts","rollout_attempts","scope_claims","artifacts","attempt_claim_path","member_capture_policy"});
    else keys(p,{"schema","source_kind","producer_sha256","constructor_attempts","metadata_attempts","rollout_attempts","scope_claims","artifacts","attempt_claim_path"});
    if(claim_capture)need(context&&member_batch&&text(p["claim_capture_policy"])=="FIRST_NOFOLLOW_INDEPENDENT_READBACK_SAME_CASE_1","wrong actual claim capture policy");
    if(context)need(member_batch&&text(p["context_capture_policy"])=="PREVALIDATION_INPUT_SNAPSHOT_SAME_CASE_1","wrong captured context policy");
    if(member_batch)need(text(p["member_capture_policy"])=="VERIFIED_MEMBER_CAPTURE_SAME_CASE_1","wrong member capture policy");
    need(text(p["schema"])==(claim_capture?"PUBLIC_LIVE_AFFINE_V2_FROZEN_PROTOCOL_MEMBERS_CONTEXT_CLAIM_4":context?"PUBLIC_LIVE_AFFINE_V2_FROZEN_PROTOCOL_MEMBERS_CONTEXT_3":member_batch?"PUBLIC_LIVE_AFFINE_V2_FROZEN_PROTOCOL_MEMBERS_2":"PUBLIC_LIVE_AFFINE_V2_FROZEN_PROTOCOL_1")&&text(p["source_kind"])=="LiveActual"&&
      integer(p["constructor_attempts"])==1&&integer(p["metadata_attempts"])==1&&integer(p["rollout_attempts"])==1,
      "wrong single-attempt live protocol");
    auto claims=p["scope_claims"];
    keys(claims,{"segment","two_sided_ball","admissibility","execution","safety","uniform_accuracy","controller_readiness"});
    for(const auto& item:claims)need(plainScalar(item.second)&&item.second.Scalar()=="false",
                                   "all seven claims require literal false, never strings/tags");
    auto r=std::make_shared<ForecastReleaseState>();r->review=review_id;r->protocol=protocol_artifact.identity;
    r->producer=observeCurrentProducerElf(text(p["producer_sha256"],64));
    r->attempt_claim_path=text(p["attempt_claim_path"]);
    need(r->attempt_claim_path.front()=='/',"absolute reviewed attempt claim path required");
    const auto entries=p["artifacts"];need(entries.IsSequence()&&entries.size()==8,"complete protocol artifact roster required");
    std::map<std::string,FileIdentity> by_role;
    for(const auto& item:entries) {auto a=artifact(item);need(by_role.emplace(a.role,verify(a.identity)).second,"duplicate artifact role");}
    for(const char* role:{"build_manifest","source_closure","xml","constants","sdk_manifest","derivative_policy","expected_metadata","invocation"})
      need(by_role.count(role)==1,"missing complete profile artifact");
    YAML::Node source_node,sdk_node,invocation_node;Count source_count=0,sdk_count=0,loaded_count=0;
    if(member_batch){source_node=readDocument(by_role.at("source_closure"));sdk_node=readDocument(by_role.at("sdk_manifest"));invocation_node=readDocument(by_role.at("invocation"));
      keys(source_node,{"schema","files"});keys(sdk_node,{"schema","files","loaded_libraries"});
      need(text(source_node["schema"])=="PUBLIC_LIVE_AFFINE_V2_SOURCE_CLOSURE_1"&&text(sdk_node["schema"])=="PUBLIC_LIVE_AFFINE_V2_SDK_CLOSURE_1","wrong member parent schema");
      for(const auto& node:{source_node,sdk_node})need(node["files"].IsSequence()&&node["files"].size()>0&&node["files"].size()<=4096,"bounded actual member roster");need(sdk_node["loaded_libraries"].IsSequence()&&sdk_node["loaded_libraries"].size()>0&&sdk_node["loaded_libraries"].size()<=512,"bounded declared loaded roster");
      source_count=source_node["files"].size();sdk_count=sdk_node["files"].size();loaded_count=sdk_node["loaded_libraries"].size();
      auto base=memberBasePlan(invocation_node);const Count total=checkedAdd(9,checkedAdd(source_count,sdk_count));const Count held=checkedAdd(50,checkedAdd(checkedMultiply(9,total),loaded_count));
      Count bytes=checkedAdd(r->review.bytes,checkedAdd(r->protocol.bytes,r->producer.bytes));for(const auto& pair:by_role)bytes=checkedAdd(bytes,pair.second.bytes);
      for(const auto& node:{source_node,sdk_node})for(const auto& item:node["files"]){keys(item,{"role","path","sha256","bytes"});bytes=checkedAdd(bytes,integer(item["bytes"]));}
      const auto cost=artifact(invocation_node["cost_input"]["artifact"]);bytes=checkedAdd(bytes,cost.identity.bytes);
      // Nominal full-refill schedule is not a promise: EVERY short/EINTR/error
      // actual read is charged by helper and may refuse the same planned cap.
      const Count hash_charges=checkedAdd(checkedMultiply(bytes,2),checkedMultiply(checkedAdd(total,loaded_count),262144));
      const Count copies=checkedAdd(checkedMultiply(total,576),checkedMultiply(loaded_count,536));
      const Count added=checkedAdd(checkedAdd(held,8264),checkedAdd(hash_charges,checkedAdd(copies,checkedMultiply(total,64))));
      const Count context_live=context?294:0,context_charges=context?16384:0,claim_live=claim_capture?446:0,claim_charges=claim_capture?524288:0;auto plan=memberPlan(base,checkedAdd(checkedAdd(checkedAdd(held,8264),context_live),claim_live),checkedAdd(checkedAdd(added,context_charges),claim_charges),claim_capture);auto budget=std::make_unique<CaseBudget>(*member_batch,plan);
      r->members=std::make_shared<MemberCaptureStorage>(std::move(budget),plan,held);auto& m=*r->members;m.status.expected_files=total;m.status.declared_libraries=loaded_count;m.status.admitted=true;if(context)m.context=std::make_shared<ContextCaptureControl>(m.budget);if(claim_capture){need(m.context&&m.context->origin,"claim source context absent");m.claim=std::make_shared<ClaimCaptureData>(m.budget,m.context->origin);}m.budget.chargeMetadataBytes(checkedAdd(by_role.at("invocation").path.size(),64));m.budget.chargeScratchOrCopy(checkedAdd(1,(by_role.at("invocation").path.size()+71)/8));m.planned_invocation=by_role.at("invocation");
      // Freeze vector capacities once under the real ownership ticket. No
      // push may grow an admitted vector beyond its exact closed bound.
      try{m.budget.chargeScratchOrCopy(32);r->files.reserve(total);r->file_roles.reserve(total);m.relations.reserve(total);r->libraries.reserve(loaded_count);need(r->files.capacity()==total&&r->file_roles.capacity()==total&&m.relations.capacity()==total&&r->libraries.capacity()==loaded_count,"member allocator capacity differs from exact admitted bound");}catch(const std::exception& e){m.reject(e.what());}catch(...){m.reject("NONSTANDARD_MEMBER_CAPACITY_ADMISSION");}

    }
    try{for(const auto& pair:by_role){if(r->members){Count ordinal=0;for(;ordinal<entries.size();++ordinal){const std::string& parsed_role=entries[ordinal]["role"].Scalar();if(parsed_role==pair.first)break;}need(ordinal<entries.size(),"actual protocol ordinal unavailable");appendMember(*r,pair.first,pair.second,VerifiedMemberGroup::Protocol,0,true,ordinal);}else {need(pair.first.size()<=128,"bounded retained artifact role");r->file_roles.push_back(pair.first);r->files.push_back(pair.second);}}
    if(r->members)for(const char* role:{"xml","constants","derivative_policy","expected_metadata","invocation"}){const auto& f=by_role.at(role);r->members->budget.chargeMetadataBytes(checkedAdd(f.path.size(),f.sha256.size()));r->members->budget.chargeScratchOrCopy(checkedAdd(1,(f.path.size()+f.sha256.size()+7)/8));}
    r->xml=by_role.at("xml");r->constants=by_role.at("constants");r->policy=by_role.at("derivative_policy");
    r->expected_metadata=by_role.at("expected_metadata");r->invocation=by_role.at("invocation");
    auto build=readDocument(by_role.at("build_manifest"));
    keys(build,{"schema","target","producer_sha256","source_closure_sha256","sdk_manifest_sha256"});
    need(text(build["schema"])=="PUBLIC_LIVE_AFFINE_V2_BUILD_BINDING_1"&&text(build["target"])=="public_live_affine_v2_model_boundary"&&
      text(build["producer_sha256"])==r->producer.sha256&&text(build["source_closure_sha256"])==by_role.at("source_closure").sha256&&
      text(build["sdk_manifest_sha256"])==by_role.at("sdk_manifest").sha256,"build/source/SDK binding mismatch");
    const std::set<std::string> required_sources={"foundation.hpp","foundation_context.cpp","foundation_identity.cpp","foundation_resources.cpp",
      "model_boundary.hpp","model_boundary.cpp","model_boundary_CMakeLists","foundation_CMakeLists",
      "normalization.hpp","normalization.cpp","normalization_CMakeLists",
      "affine_assembly.hpp","affine_assembly.cpp","affine_CMakeLists",
      "quadratic_cost.hpp","quadratic_cost.cpp","cost_CMakeLists",
      "capture_state.hpp","cost_input_decoder.hpp","cost_input_decoder.cpp","input_codec_CMakeLists",
      "numeric_chunks.hpp","chunk_io.hpp","chunk_writer.cpp","chunk_reader.cpp","output_chunks_CMakeLists",
      "capture_inventory.hpp","capture_inventory.cpp","capture_inventory_CMakeLists",
      "capture_workspace.hpp","partition_internal.hpp","capture_workspace.cpp","capture_workspace_CMakeLists",
      "capture_leaves.hpp","capture_leaves.cpp","capture_leaves_CMakeLists",
      "remaining_numeric_support_contract","capture_metadata.hpp","capture_metadata_internal.inc","capture_metadata_contract","provisional_manifest.hpp","provisional_manifest_io.hpp","provisional_manifest_internal.inc","provisional_manifest_writer.cpp","provisional_manifest_reader.cpp","provisional_manifest_contract","provisional_manifest_schema.hpp",
      "augmented_extension.hpp","augmented_extension.cpp","augmented_extension_CMakeLists",
      "augmented_value.hpp","augmented_value.cpp","physical_derivative.hpp","physical_derivative.cpp","physical_derivative_CMakeLists",
      "physical_value.hpp","physical_value.cpp","physical_value_CMakeLists","coupled_friction_box.cpp"};
    for(const char* manifest_role:{"source_closure","sdk_manifest"}) {
      auto closure=r->members?(std::string(manifest_role)=="source_closure"?source_node:sdk_node):readDocument(by_role.at(manifest_role));
      if(std::string(manifest_role)=="source_closure")keys(closure,{"schema","files"});
      else keys(closure,{"schema","files","loaded_libraries"});
      need(text(closure["schema"])==(std::string(manifest_role)=="source_closure"?"PUBLIC_LIVE_AFFINE_V2_SOURCE_CLOSURE_1":"PUBLIC_LIVE_AFFINE_V2_SDK_CLOSURE_1"),"closure schema mismatch");
      const auto files=closure["files"];need(files.IsSequence()&&files.size()>0&&files.size()<=4096,"bounded complete closure required");
      std::set<std::string> roles,paths;std::map<std::string,FileIdentity> verified;
      Count ordinal=0;for(const auto& item:files){std::optional<MemberFrame> member_frame;if(r->members)member_frame.emplace(*r->members);auto a=r->members?memberArtifact(item,*r->members):artifact(item);if(r->members){r->members->budget.chargeMetadataBytes(checkedAdd(a.role.size(),a.identity.path.size()));r->members->budget.chargeScratchOrCopy((a.role.size()+a.identity.path.size()+7)/8);}need(roles.insert(a.role).second&&paths.insert(a.identity.path).second,"duplicate closure role/path");
        FileIdentity f;if(r->members){auto& active=r->members->status;r->members->budget.chargeScratchOrCopy(6);active.active_file_index=r->files.size();active.active_native_ordinal=ordinal;active.active_parent_index=parentIndex(*r,manifest_role);active.active_group=std::string(manifest_role)=="source_closure"?VerifiedMemberGroup::SourceClosure:VerifiedMemberGroup::SDKClosure;active.active_member_known=true;active.identity_target_kind=MemberIdentityTargetKind::MemberFile;active.identity_target_index=active.active_file_index;active.identity_target_known=true;r->members->budget.chargeScratchOrCopy(20);r->members->latest_identity=MemberIdentityObservationV1{};f=observePinnedFileWithMemberBudgetV1(r->members->budget,a.identity,r->members->latest_identity);appendMember(*r,a.role,f,std::string(manifest_role)=="source_closure"?VerifiedMemberGroup::SourceClosure:VerifiedMemberGroup::SDKClosure,parentIndex(*r,manifest_role),false,ordinal);}else {f=verify(a.identity);r->files.push_back(f);}if(r->members){r->members->budget.chargeMetadataBytes(checkedAdd(checkedMultiply(2,f.path.size()),f.sha256.size()));r->members->budget.chargeScratchOrCopy(checkedAdd(1,(2*f.path.size()+f.sha256.size()+7)/8));}verified.emplace(f.path,f);++ordinal;}
      if(std::string(manifest_role)=="source_closure") {
        for(const auto& role:required_sources)need(roles.count(role)==1,"source closure omitted required compiled source/target");if(r->members)need(roles.count("member_capture_contract")==1,"versioned member closure omitted actual capture contract");if(context)need(roles.count("context_snapshot_contract")==1,"versioned context closure omitted actual capture contract");if(claim_capture)need(roles.count("claim_capture_contract")==1,"versioned claim closure omitted actual capture contract");
      } else {
        auto libs=closure["loaded_libraries"];need(libs.IsSequence()&&libs.size()>0&&libs.size()<=512,"full loaded SDK library roster required");
        std::set<std::string> unique;
        Count loaded_ordinal=0;for(const auto& item:libs){auto name=r->members?memberText(item,*r->members,4096):text(item);if(r->members){r->members->budget.chargeMetadataBytes(name.size());r->members->budget.chargeScratchOrCopy((name.size()+7)/8);}need(unique.insert(name).second&&verified.count(name)==1,"loaded library missing from verified SDK closure");
          if(r->members){auto& m=*r->members;m.budget.chargeMetadataBytes(checkedAdd(verified.at(name).path.size(),64));m.budget.chargeScratchOrCopy(checkedAdd((verified.at(name).path.size()+71)/8,1));Count linked=0;for(auto& relation:m.relations){m.budget.chargeScratchOrCopy(1);if(relation.group==VerifiedMemberGroup::SDKClosure&&r->files[relation.file_index].path==name){m.budget.chargeScratchOrCopy(2);relation.declared_loaded=true;relation.declared_loaded_ordinal=loaded_ordinal;++linked;}}need(linked==1,"declared SDK loaded member link not unique");}
          if(r->members)need(r->libraries.size()<r->libraries.capacity()&&r->libraries.capacity()==r->members->status.declared_libraries,"declared library capacity exceeded");r->libraries.push_back(verified.at(name));++loaded_ordinal;}
      }
    }
    auto policy=readDocument(r->policy);
    keys(policy,{"schema","certificate_name","cycle_dt","substep_dt","control_margin","nx","nu","max_cells","max_cycles","max_samples"});
    need(text(policy["schema"])=="PUBLIC_LIVE_AFFINE_V2_DERIVATIVE_POLICY_1"&&text(policy["certificate_name"])==NativeModel::certificate_name&&
      number(policy["cycle_dt"])==macro_dt&&number(policy["substep_dt"])==physical_dt&&number(policy["control_margin"])==NativeModel::control_margin&&
      integer(policy["nx"])==30&&integer(policy["nu"])==8&&integer(policy["max_cells"])==32&&integer(policy["max_cycles"])==375&&integer(policy["max_samples"])==750,
      "unchanged derivative policy/versioned envelope mismatch");
    if(r->members){
#if defined(__linux__)
      auto loader_frame=r->members->budget.reserve(40);r->members->budget.chargeScratchOrCopy(40);verifyMemberLoadedLibraries(r->libraries,r->members->budget,r->members->latest_identity,r->members->latest_loader,r->members->status);
#else
      throw std::invalid_argument("member loaded verifier requires Linux");
#endif
    }else verifyLoadedLibraries(r->libraries);if(r->members){r->members->budget.chargeScratchOrCopy(1);++r->members->status.verified_loader_checks;need(r->files.size()==r->file_roles.size()&&r->files.size()==r->members->relations.size(),"complete member vectors mismatch");}
    }catch(const std::exception& e){if(!r->members)throw;r->members->reject(e.what());}catch(...){if(!r->members)throw;r->members->reject("NONSTANDARD_MEMBER_PERMISSION_CAPTURE");}
    ReviewedForecastPermission out;out.release_=std::move(r);return out;
  }
  static CapturedLiveActualContextV1 validateContext(ReviewedForecastPermission& permission,const ObservedActual& observed,const AcceptedCommandHistory& command,const ProgressHistory& progress,const NominalAnchor& nominal,const CurrentBoundaryExpectation& current,const StaticDomainRanges& ranges){
    auto r=valid(permission);need(static_cast<bool>(r->members),"captured context requires member+context protocol");auto& m=*r->members;try{need(m.context&&m.pending_case&&r->prepare_attempts==0,"captured context budget/source absent or preparation consumed");const bool attempted=m.context->attempted;m.context->attempted=true;m.budget.chargeScratchOrCopy(1);need(!attempted,"context validation already attempted; no retry");m.budget.chargeScratchOrCopy(3);
      auto captured=ContextSnapshotFactory::captureAndValidate(m.budget,m.context->origin,observed,command,progress,nominal,current,ranges);m.context->snapshot=captured;
      need(captured.history().complete&&!captured.history().refused,captured.history().first_error.empty()?"CONTEXT_VALIDATION_REFUSED_DETAIL_UNAVAILABLE":captured.history().first_error.c_str());return captured;
    }catch(const std::exception& e){m.reject(e.what());throw;}catch(...){m.reject("NONSTANDARD_CAPTURED_CONTEXT_ENTRY");throw;}
  }
  static OwnedLiveInvocation prepare(ReviewedForecastPermission& permission,const LiveActualContext& actual,
                                     BatchBudget& batch,const CapturedLiveActualContextV1* captured=nullptr) {
    auto r=valid(permission);if(r->members&&r->members->context&&r->prepare_attempts!=0){r->members->reject("CONTEXT_INVOCATION_PREPARATION_REENTRY");throw std::invalid_argument("invocation preparation already attempted");}need(r->prepare_attempts==0,"invocation preparation already attempted");
    ++r->prepare_attempts;try{
    need(!r->members||!r->members->context||captured,"context-enabled permission requires private captured witness");
    need(!captured||(r->members&&r->members->context&&captured->sameSource(r->members->context->origin,r->members->budget)&&r->members->context->snapshot&&captured->sameWitness(*r->members->context->snapshot)),"captured witness foreign source/case/object");
    recheck(*r);
    const auto n=readDocument(r->invocation);
    keys(n,{"schema","source_kind","units","boundary","initial","previous_alpha","previous_b",
            "mesh","controls","factor_shape","capture_mode","encoding","cost_input"});
    need(text(n["schema"])=="PUBLIC_LIVE_AFFINE_V2_INVOCATION_COST_BOUND_2"&&text(n["source_kind"])=="LiveActual"&&
         text(n["units"])==units,"only frozen live actual invocation is supported");
    auto b=n["boundary"];keys(b,{"completed_tick","completed_command_sequence","observation_id","transaction_id"});
    need(integer(b["completed_tick"])==actual.boundary().completed_tick&&
      integer(b["completed_command_sequence"])==actual.boundary().completed_command_sequence&&
      text(b["observation_id"],256)==actual.observationId()&&text(b["transaction_id"],256)==actual.transactionId()&&
      equalState(state(n["initial"]),actual.actualInitial())&&joints(n["previous_alpha"])==actual.previousAlpha()&&
      number(n["previous_b"])==actual.previousB(),"frozen invocation differs from validated actual/history boundary");
    need(actual.ranges().constantsIdentity().path==r->constants.path&&
      actual.ranges().constantsIdentity().sha256==r->constants.sha256&&
      actual.ranges().constantsIdentity().bytes==r->constants.bytes,"current static range identity differs from profile");
    auto m=n["mesh"];keys(m,{"steps","total_macro_cycles","policy","explicit_cycles"});
    HorizonSpec spec;spec.steps=integer(m["steps"]);spec.total_macro_cycles=integer(m["total_macro_cycles"]);
    const auto mp=text(m["policy"]);
    if(mp=="UniformExact")spec.policy=MeshPolicy::UniformExact;
    else if(mp=="BalancedInteger")spec.policy=MeshPolicy::BalancedInteger;
    else if(mp=="ExplicitCycles")spec.policy=MeshPolicy::ExplicitCycles;
    else throw std::invalid_argument("unknown frozen mesh policy");
    need(m["explicit_cycles"].IsSequence()&&m["explicit_cycles"].size()<=32,"bounded explicit mesh list required");
    for(const auto& item:m["explicit_cycles"])spec.explicit_cycles.push_back(integer(item));
    const auto mesh=planMesh(spec);
    auto f=n["factor_shape"];keys(f,{"terms","rows","largest_term_rows","addition_coefficients","addition_records"});
    const FactorShape fs{integer(f["terms"]),integer(f["rows"]),integer(f["largest_term_rows"]),
                         integer(f["addition_coefficients"]),integer(f["addition_records"])};
    const auto binding=n["cost_input"];keys(binding,{"artifact","semantic_sha256"});
    auto cost_artifact=r->members?memberArtifact(binding["artifact"],*r->members):artifact(binding["artifact"]);need(cost_artifact.role=="cost_input","cost input role mismatch");
    FileIdentity cost_identity;if(r->members){r->members->budget.chargeScratchOrCopy(20);r->members->status.identity_target_kind=MemberIdentityTargetKind::CostInput;r->members->status.identity_target_index=0;r->members->status.identity_target_known=true;r->members->status.active_member_known=false;r->members->latest_identity=MemberIdentityObservationV1{};cost_identity=observePinnedFileWithMemberBudgetV1(r->members->budget,cost_artifact.identity,r->members->latest_identity);}else cost_identity=verify(cost_artifact.identity);const auto semantic=r->members?memberText(binding["semantic_sha256"],*r->members,64):text(binding["semantic_sha256"],64);
    need(semantic.size()==64,"cost semantic SHA256 length");
    for(char ch:semantic)need((ch>='0'&&ch<='9')||(ch>='a'&&ch<='f'),"cost semantic SHA256 hex");
    const auto capture=text(n["capture_mode"]),encoding=text(n["encoding"]);
    need(capture=="CompactComplete"||capture=="DenseAuditComplete","unknown frozen capture mode");
    need(encoding=="LosslessBinary"||encoding=="FullNumericJson","unknown frozen numeric encoding");
    auto plan=planResources(mesh,fs,capture=="CompactComplete"?CaptureMode::CompactComplete:CaptureMode::DenseAuditComplete,
                           encoding=="LosslessBinary"?NumericEncoding::LosslessBinary:NumericEncoding::FullNumericJson);
    const auto controls=n["controls"];need(controls.IsSequence()&&controls.size()==mesh.cycles().size(),"nominal control roster mismatch");
    std::shared_ptr<InvocationStorage> data;if(r->members){auto& m=*r->members;need(m.pending_case&&m.pending_case->sameBatch(batch),"member capture uses a different Batch or Case already moved");
      need(m.planned_invocation.path==r->invocation.path&&m.planned_invocation.sha256==r->invocation.sha256&&m.planned_invocation.bytes==r->invocation.bytes&&sameBasePlan(plan,m.plan,static_cast<bool>(m.claim)),"prepared actual invocation identity/plan differs from admission");plan=m.plan;if(m.context){m.budget.chargeScratchOrCopy(69);for(const auto* value:{&actual.observationId(),&actual.transactionId(),&actual.ranges().constantsIdentity().path,&actual.ranges().constantsIdentity().sha256}){m.budget.chargeMetadataBytes(value->size());m.budget.chargeScratchOrCopy((value->size()+7)/8);}}data=std::make_shared<InvocationStorage>(std::move(*m.pending_case),plan,actual,mesh,r);m.pending_case.reset();need(m.budget.sameCase(data->budget.share()),"moved member Case mismatch");}
    else data=std::make_shared<InvocationStorage>(batch,plan,actual,mesh,r);
    if(r->members){r->members->budget.chargeMetadataBytes(checkedAdd(cost_identity.path.size(),checkedAdd(cost_identity.sha256.size(),semantic.size())));r->members->budget.chargeScratchOrCopy(checkedAdd(6,(cost_identity.path.size()+cost_identity.sha256.size()+semantic.size()+7)/8));}
    data->factors=fs;data->cost_input=cost_identity;data->cost_semantic_sha256=semantic;if(r->members){try{appendMember(*r,"cost_input",cost_identity,VerifiedMemberGroup::InvocationCost,parentIndex(*r,"invocation"),false,0);auto& m=*r->members;need(r->files.size()==m.status.expected_files&&r->files.size()==r->file_roles.size()&&r->files.size()==m.relations.size(),"final actual member count mismatch");m.status.complete=true;}catch(const std::exception& e){r->members->reject(e.what());throw;}catch(...){r->members->reject("NONSTANDARD_COST_MEMBER_APPEND");throw;}}else r->files.push_back(cost_identity);
    if(captured){r->members->budget.chargeScratchOrCopy(2);data->captured_context=*captured;}
    data->initial=nativeState(actual.actualInitial());data->cells.reserve(mesh.cycles().size());
    for(std::size_t k=0;k<controls.size();++k) {
      auto item=controls[k];keys(item,{"alpha","b"});const auto alpha=joints(item["alpha"]);
      NativeCell cell;cell.cycles=static_cast<int>(mesh.cycles()[k]);cell.alpha.resize(7);cell.b=number(item["b"]);
      for(std::size_t j=0;j<7;++j){need(std::abs(alpha[j])<=1,"nominal alpha outside unchanged closed domain");cell.alpha(j)=alpha[j];}
      data->cells.push_back(std::move(cell));
    }
    return OwnedLiveInvocation(std::move(data));
    }catch(const std::exception& e){if(r->members)r->members->reject(e.what());throw;}catch(...){if(r->members)r->members->reject("NONSTANDARD_MEMBER_PREPARE_REFUSAL");throw;}
  }
  static OwnedLiveInvocation prepareCaptured(ReviewedForecastPermission& permission,const CapturedLiveActualContextV1& context,BatchBudget& batch){auto r=valid(permission);try{return prepare(permission,context.validatedContext(),batch,&context);}catch(const std::exception& e){if(r->members)r->members->reject(e.what());throw;}catch(...){if(r->members)r->members->reject("NONSTANDARD_CAPTURED_PREPARE_REFUSAL");throw;}}
  static void claim(const ForecastReleaseState& r) {
    // This reviewed output is FIRST-only across process restarts. No deletion,
    // overwrite, retry token or automatic replacement is implemented.
    const std::string record="review_sha256="+r.review.sha256+"\nprotocol_sha256="+r.protocol.sha256+
      "\nproducer_sha256="+r.producer.sha256+"\ninvocation_sha256="+r.invocation.sha256+"\n";
    struct ClaimFd {
      int value=-1;
      ~ClaimFd(){if(value>=0)::close(value);}
    } fd{::open(r.attempt_claim_path.c_str(),O_WRONLY|O_CREAT|O_EXCL|O_CLOEXEC|O_NOFOLLOW,0600)};
    need(fd.value>=0,"attempt claim unavailable/already present; no Model call permitted");
    std::size_t written=0;bool good=true;
    while(written<record.size()) {
      const auto count=::write(fd.value,record.data()+written,record.size()-written);
      if(count<0&&errno==EINTR)continue;
      if(count<=0){good=false;break;}written+=static_cast<std::size_t>(count);
    }
    if(good)good=::fsync(fd.value)==0;
    const int value=fd.value;fd.value=-1;
    if(::close(value)!=0)good=false;
    need(good,"attempt claim incomplete; retained and never retried");
  }
  static void claimCaptured(ForecastReleaseState& r){
    need(r.members&&r.members->claim,"private claim owner absent");auto& m=*r.members;auto& d=*m.claim;auto& h=d.facts;
    const bool attempted=h.attempted;h.attempted=true;
    try{
      need(!attempted&&!h.refused&&!m.status.refused&&m.context&&d.source==m.context->origin&&d.budget.sameCase(m.budget),"claim source/case/refusal/reentry mismatch");
      d.budget.chargeScratchOrCopy(64); // Prepaid cleanup and bounded history transitions.
      auto work=d.budget.reserve(256); // Before component/stat/hash/descriptor workspace.
#if defined(__linux__)
      static_assert(sizeof(struct stat)<=512,"review platform stat workspace exceeds claim schedule");
      static_assert(sizeof(decltype(std::declval<struct stat>().st_dev))<=8&&sizeof(decltype(std::declval<struct stat>().st_ino))<=8&&sizeof(decltype(std::declval<struct stat>().st_size))<=8,"claim native identity wider than retained fields");
      std::array<char,256> component{};struct stat st{},other{};
      ClaimFDV1 parent(h),writer(h,ClaimFDV1::Kind::Writer),reader(h,ClaimFDV1::Kind::Reader);
      using Ptr=std::unique_ptr<EVP_MD_CTX,decltype(&EVP_MD_CTX_free)>;
      h.stage="CAPTURE_PRIVATE_CLAIM_PATH_AND_CONTENT";
      const auto& path=r.attempt_claim_path;
      need(path.size()>1&&path.size()<=4096&&path.front()=='/'&&path.back()!='/'&&path.find('\0')==std::string::npos,"claim requires bounded absolute component path");
      d.budget.chargeMetadataBytes(path.size());d.budget.chargeScratchOrCopy(checkedAdd(checkedMultiply(path.size(),2),(path.size()+7)/8));h.path=path;h.path_copied=true;
      Count components=0;for(std::size_t start=1;start<path.size();){const auto slash=path.find('/',start);const auto end=slash==std::string::npos?path.size():slash;const auto n=end-start;
        need(n>0&&n<=255&&!(n==1&&path[start]=='.')&&!(n==2&&path[start]=='.'&&path[start+1]=='.'),"claim unsafe/empty/dot/oversized component");need(++components<=64,"claim component cap");start=end+1;}
      Count position=0;auto append=[&](std::string_view bytes){need(bytes.size()<=d.expected.size()-position,"claim fixed record overflow");d.budget.chargeScratchOrCopy((bytes.size()+7)/8);for(unsigned char c:bytes)d.expected[position++]=c;};
      d.budget.chargeMetadataBytes(324);for(const auto* sha:{&r.review.sha256,&r.protocol.sha256,&r.producer.sha256,&r.invocation.sha256}){need(sha->size()==64,"claim private SHA length");for(char c:*sha)need((c>='0'&&c<='9')||(c>='a'&&c<='f'),"claim private SHA syntax");}
      append("review_sha256=");append(r.review.sha256);append("\nprotocol_sha256=");append(r.protocol.sha256);append("\nproducer_sha256=");append(r.producer.sha256);append("\ninvocation_sha256=");append(r.invocation.sha256);append("\n");
      need(position==324,"claim fixed private record shape");h.expected_ready=true;
      d.budget.chargeScratchOrCopy(128);Ptr expected_hash(EVP_MD_CTX_new(),EVP_MD_CTX_free);
      need(expected_hash&&EVP_DigestInit_ex(expected_hash.get(),EVP_sha256(),nullptr)==1&&EVP_DigestUpdate(expected_hash.get(),d.expected.data(),324)==1,"claim private expected SHA failed");
      ClaimIOV1::digest(d,expected_hash.get(),h.expected_sha,h.expected_digest_known);expected_hash.reset();
      need(d.budget.outputBytes()<=d.budget.outputCeiling()&&324<=d.budget.outputCeiling()-d.budget.outputBytes(),"claim output quota before creation");
      ClaimIOV1::attempt(d,"OPEN_NOFOLLOW_DIRECTORY_ROOT");parent.fd=static_cast<int>(ClaimIOV1::result(h,::open("/",O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC)));need(parent.fd>=0,"claim root directory open failed");
      for(std::size_t start=1;start<path.size();){const auto slash=path.find('/',start);const auto end=slash==std::string::npos?path.size():slash;const auto n=end-start;
        d.budget.chargeScratchOrCopy((n+8)/8);std::memcpy(component.data(),path.data()+start,n);component[n]='\0';
        if(end==path.size())break;
        ClaimFDV1 next(h);ClaimIOV1::attempt(d,"OPEN_NOFOLLOW_DIRECTORY_COMPONENT");next.fd=static_cast<int>(ClaimIOV1::result(h,::openat(parent.fd,component.data(),O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC)));need(next.fd>=0,"claim nofollow parent component refused");
        parent.closeChecked(d,"CLOSE_PREVIOUS_DIRECTORY");parent.fd=next.fd;next.fd=-1;++h.directory_components;start=end+1;
      }
      parent.kind=ClaimFDV1::Kind::Parent;ClaimIOV1::fdStat(d,parent.fd,st,ClaimStatTargetV1::Parent,"STAT_CLAIM_PARENT");h.parent_device=st.st_dev;h.parent_inode=st.st_ino;h.parent_identity_known=true;need(S_ISDIR(st.st_mode),"claim actual parent is not directory");
      ClaimIOV1::attempt(d,"CREATE_FIRST_NOFOLLOW_CLAIM");++h.create_attempts;writer.fd=static_cast<int>(ClaimIOV1::result(h,::openat(parent.fd,component.data(),O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC,0600)));need(writer.fd>=0,"claim FIRST exists/unsafe/create failed; never retry");h.created=true;
      ClaimIOV1::fdStat(d,writer.fd,st,ClaimStatTargetV1::CreatedWriter,"STAT_CREATED_CLAIM");h.created_device=st.st_dev;h.created_inode=st.st_ino;h.created_size=st.st_size>=0?static_cast<Count>(st.st_size):0;h.created_identity_known=st.st_size>=0;
      need(ClaimIOV1::regular(st)&&st.st_size==0,"created claim must be empty regular single-link0600");
      d.budget.chargeScratchOrCopy(128);Ptr write_hash(EVP_MD_CTX_new(),EVP_MD_CTX_free);need(write_hash&&EVP_DigestInit_ex(write_hash.get(),EVP_sha256(),nullptr)==1,"claim writer SHA init failed");h.writer_hash_state_valid=true;
      while(h.written_bytes<324){const Count remaining=324-h.written_bytes;ClaimIOV1::attempt(d,"WRITE_ACTUAL_CLAIM_PREFIX",(remaining+7)/8);++h.write_attempts;h.attempted_write_bytes=checkedAdd(h.attempted_write_bytes,remaining);
        const auto got=ClaimIOV1::result(h,::write(writer.fd,d.expected.data()+h.written_bytes,static_cast<std::size_t>(remaining)));
        if(got<0&&h.last_errno==EINTR)continue;need(got>0&&static_cast<Count>(got)<=remaining,"claim zero/failed/impossible short write");
        const Count start=h.written_bytes;h.written_bytes=checkedAdd(start,static_cast<Count>(got));h.write_complete=h.written_bytes==324;d.budget.chargeUniqueOutputBytes(static_cast<Count>(got));h.output_charged_bytes=checkedAdd(h.output_charged_bytes,static_cast<Count>(got));
        h.writer_hash_state_valid=false;need(EVP_DigestUpdate(write_hash.get(),d.expected.data()+start,static_cast<std::size_t>(got))==1,"claim writer prefix SHA update failed");h.writer_hash_state_valid=true;
        ClaimIOV1::digest(d,write_hash.get(),h.writer_prefix_sha,h.writer_digest_known,&h.writer_digest_bytes,h.written_bytes);
      }
      h.write_complete=true;ClaimIOV1::fdStat(d,writer.fd,st,ClaimStatTargetV1::FinalWriter,"STAT_FINAL_WRITER_CLAIM");h.writer_final_size=st.st_size>=0?static_cast<Count>(st.st_size):0;h.writer_final_identity_known=st.st_size>=0;
      need(ClaimIOV1::regular(st)&&static_cast<Count>(st.st_dev)==h.created_device&&static_cast<Count>(st.st_ino)==h.created_inode&&st.st_size==324,"claim writer identity/size changed");
      ClaimIOV1::attempt(d,"FSYNC_CLAIM_FILE");h.file_fsync_attempted=true;need(ClaimIOV1::result(h,::fsync(writer.fd))==0,"claim actual file fsync failed");h.file_fsynced=true;
      ClaimIOV1::attempt(d,"FSYNC_CLAIM_DIRECTORY");h.dir_fsync_attempted=true;need(ClaimIOV1::result(h,::fsync(parent.fd))==0,"claim actual directory fsync failed");h.dir_fsynced=true;
      writer.closeChecked(d,"CLOSE_WRITTEN_CLAIM");write_hash.reset();
      ClaimIOV1::attempt(d,"OPEN_INDEPENDENT_NOFOLLOW_READBACK");++h.read_open_attempts;reader.fd=static_cast<int>(ClaimIOV1::result(h,::openat(parent.fd,component.data(),O_RDONLY|O_NONBLOCK|O_NOFOLLOW|O_CLOEXEC)));need(reader.fd>=0,"claim independent reader open failed");h.read_opened=true;
      ClaimIOV1::fdStat(d,reader.fd,st,ClaimStatTargetV1::ReaderInitial,"STAT_INDEPENDENT_CLAIM_READER");h.read_device=st.st_dev;h.read_inode=st.st_ino;h.read_size=st.st_size>=0?static_cast<Count>(st.st_size):0;h.read_identity_known=st.st_size>=0;
      need(ClaimIOV1::regular(st)&&static_cast<Count>(st.st_dev)==h.created_device&&static_cast<Count>(st.st_ino)==h.created_inode&&st.st_size==324,"claim independent read FD identity/size mismatch");
      d.budget.chargeScratchOrCopy(128);Ptr read_hash(EVP_MD_CTX_new(),EVP_MD_CTX_free);need(read_hash&&EVP_DigestInit_ex(read_hash.get(),EVP_sha256(),nullptr)==1,"claim reader SHA init failed");h.reader_hash_state_valid=true;h.comparison_started=true;h.byte_prefix_equal=true;
      for(;;){need(h.read_bytes<=324,"claim read prefix cap");const Count request=h.read_bytes==324?1:324-h.read_bytes;
        ClaimIOV1::attempt(d,"READ_INDEPENDENT_PHYSICAL_CLAIM",(request+7)/8);++h.read_attempts;h.attempted_read_bytes=checkedAdd(h.attempted_read_bytes,request);
        const auto got=ClaimIOV1::result(h,::read(reader.fd,d.readback.data()+h.read_bytes,static_cast<std::size_t>(request)));
        if(got<0&&h.last_errno==EINTR)continue;need(got>=0&&static_cast<Count>(got)<=request,"claim independent read failed/impossible count");if(got==0){h.physical_eof=true;break;}
        const Count start=h.read_bytes;h.read_bytes=checkedAdd(start,static_cast<Count>(got));for(Count i=start;i<h.read_bytes;++i)if(i>=324||d.readback[i]!=d.expected[i])h.byte_prefix_equal=false;
        h.reader_hash_state_valid=false;need(EVP_DigestUpdate(read_hash.get(),d.readback.data()+start,static_cast<std::size_t>(got))==1,"claim physical reader prefix SHA update failed");h.reader_hash_state_valid=true;
        ClaimIOV1::digest(d,read_hash.get(),h.reader_prefix_sha,h.reader_digest_known,&h.reader_digest_bytes,h.read_bytes);
        need(h.read_bytes<=324,"claim grew beyond exact record; actual extra byte retained");
      }
      h.read_complete=h.physical_eof&&h.read_bytes==324;ClaimIOV1::fdStat(d,reader.fd,st,ClaimStatTargetV1::ReaderFinal,"STAT_FINAL_PHYSICAL_CLAIM_READER");h.read_final_size=st.st_size>=0?static_cast<Count>(st.st_size):0;h.read_final_identity_known=st.st_size>=0;
      need(ClaimIOV1::regular(st)&&static_cast<Count>(st.st_dev)==h.created_device&&static_cast<Count>(st.st_ino)==h.created_inode&&st.st_size==324,"claim read FD changed during read");
      h.last_stat_target=ClaimStatTargetV1::NameRecheck;h.last_stat_known=false;ClaimIOV1::attempt(d,"STAT_NOFOLLOW_CLAIM_NAME");need(ClaimIOV1::result(h,::fstatat(parent.fd,component.data(),&other,AT_SYMLINK_NOFOLLOW))==0,"claim name recheck failed");ClaimIOV1::statFacts(h,other);
      need(ClaimIOV1::regular(other)&&static_cast<Count>(other.st_dev)==h.created_device&&static_cast<Count>(other.st_ino)==h.created_inode&&other.st_size==324,"claim name replaced after independent read");h.identity_stable=true;
      h.read_matches_expected=h.read_complete&&h.byte_prefix_equal&&h.expected_digest_known&&h.writer_digest_known&&h.writer_digest_bytes==324&&h.reader_digest_known&&h.reader_digest_bytes==324&&h.expected_sha==h.writer_prefix_sha&&h.expected_sha==h.reader_prefix_sha;
      need(h.read_matches_expected&&h.output_charged_bytes==324,"actual claim bytes/SHA/unique-output mismatch");reader.closeChecked(d,"CLOSE_INDEPENDENT_CLAIM_READER");parent.closeChecked(d,"CLOSE_FINAL_CLAIM_PARENT");
      need(!h.cleanup_close_failed&&h.write_closed&&h.read_closed&&h.parent_closed,"claim close failure retained");h.historical_complete=true;h.complete=true;h.stage="COMPLETE_ACTUAL_FIRST_CLAIM_READBACK";
#else
      throw std::invalid_argument("versioned claim capture requires reviewed Linux descriptor semantics");
#endif
    }catch(const std::exception& e){const bool first=!h.refused;if(first)h.first_refusal_stage=h.stage;h.refused=true;h.complete=false;
      if(first&&!h.first_error_known)try{std::string_view why=e.what();need(why.size()<=512,"claim refusal detail cap");d.budget.chargeMetadataBytes(why.size());d.budget.chargeScratchOrCopy((why.size()+7)/8);h.first_error.assign(why);h.first_error_known=true;}catch(...){}
      m.rejectClaim(e.what());throw;
    }catch(...){if(!h.refused)h.first_refusal_stage=h.stage;h.refused=true;h.complete=false;m.rejectClaim("NONSTANDARD_ACTUAL_CLAIM_REFUSAL");throw;}
  }
  static ModelOpenOutcome open(ReviewedForecastPermission& permission,OwnedLiveInvocation& invocation) {
    auto record=std::make_unique<OpenStorage>();
    try {
      auto r=valid(permission);need(static_cast<bool>(invocation.storage_)&&invocation.storage_->release==r,
        "live invocation/release ownership mismatch");
      need(r->prepare_attempts==1&&r->open_attempts==0&&r->constructor_attempts==0&&r->metadata_attempts==0&&r->rollout_attempts==0,
           "constructor/metadata release already consumed or unprepared");
      ++r->open_attempts; // Hash/quota/metadata-parse failures also latch this entry.
      recheck(*r);
      record->profile=std::make_shared<ProfileStorage>(*invocation.storage_);
      record->profile->expected=metadata(r->expected_metadata); // After planning reservation; still no Model.
      need(!r->members||(r->members->status.complete&&!r->members->status.refused&&r->files.size()==r->file_roles.size()&&r->files.size()==r->members->relations.size()),"complete actual member capture required before Model");
      if(r->members&&r->members->claim)claimCaptured(*r);else claim(*r); // Must precede actual constructor.
      auto handle=std::make_unique<HandleStorage>();handle->profile=record->profile;handle->invocation=invocation.storage_;
      ++r->constructor_attempts;record->constructor_attempted=true;
      handle->model=std::make_unique<NativeModel>(r->xml.path,r->constants.path);
      // Postconstructor hash/loader recheck cannot retroactively authorize the
      // constructor. All identities and reviewed gate were checked BEFORE it.
      recheck(*r);
      ++r->metadata_attempts;record->metadata_attempted=true;
      record->profile->observed=std::make_unique<NativeMetadata>(handle->model->metadata());
      compareMetadata(*record->profile->observed,record->profile->expected);recheck(*r);
      record->handle.reset(new PinnedModelHandle(std::move(handle)));
    } catch(const std::exception& e) {record->refusal=e.what();}
    return ModelOpenOutcome(std::move(record));
  }
  static Count stateSlots(const NativeState& s) {
    return checkedAdd(checkedAdd(static_cast<Count>(s.q.size()),static_cast<Count>(s.v.size())),
      checkedAdd(checkedAdd(static_cast<Count>(s.C.size()),static_cast<Count>(s.w.size())),2));
  }
  static Count mapSlots(const phase5_public_coupled_augmented_extension::Map& m) {
    Count slots=3;
    for(Count n:{stateSlots(m.origin),stateSlots(m.state),stateSlots(m.cell_origin),static_cast<Count>(m.input.size()),
      static_cast<Count>(m.A.size()),static_cast<Count>(m.B.size()),static_cast<Count>(m.cell_A.size()),
      static_cast<Count>(m.cell_B.size()),static_cast<Count>(m.defect.size()),static_cast<Count>(m.cell_defect.size())})
      slots=checkedAdd(slots,n);
    return slots;
  }
  static void rawEnvelope(const RawResult& raw,const InvocationStorage& i,Count reserved) {
    const Count n=i.mesh.cycles().size(),t=i.mesh.total(),s=checkedMultiply(2,t);
    need(raw.value.substeps.size()<=s&&raw.value.cycle_end_states.size()<=t&&raw.value.cell_end_states.size()<=n&&
      raw.substep_maps.size()<=s&&raw.cycle_maps.size()<=t&&raw.cell_maps.size()<=n,"returned raw roster exceeds planned mesh");
    Count slots=checkedAdd(stateSlots(raw.value.final_state),4);
    for(const auto& point:raw.value.substeps) {
      Count sample=6; // Cell/cycle/half, iterations and2clip flags; branch vector below.
      for(Count count:{static_cast<Count>(point.q.size()),static_cast<Count>(point.v.size()),
          static_cast<Count>(point.C.size()),static_cast<Count>(point.w.size()),static_cast<Count>(point.friction.force.size()),
          static_cast<Count>(point.friction.branches.size()),Count{4}}) sample=checkedAdd(sample,count);
      slots=checkedAdd(slots,sample);
    }
    for(const auto* states:{&raw.value.cycle_end_states,&raw.value.cell_end_states})
      for(const auto& point:*states)slots=checkedAdd(slots,stateSlots(point));
    for(const auto* maps:{&raw.substep_maps,&raw.cycle_maps,&raw.cell_maps})
      for(const auto& map:*maps)slots=checkedAdd(slots,mapSlots(map));
    need(slots<=i.plan.rawResultShapeSlots(),"returned raw numeric shape exceeds declared raw envelope; preserve and refuse");
    need(slots<=reserved,"returned raw numeric shape exceeds planning ticket; preserve and refuse");
  }
  static OwnedPublicForecast forecast(PinnedModelHandle& handle,OwnedLiveInvocation&& invocation) {
    need(static_cast<bool>(handle.storage_)&&static_cast<bool>(handle.storage_->model)&&
         static_cast<bool>(invocation.storage_)&&handle.storage_->invocation==invocation.storage_,
         "forecast requires the exact genuine prepared handle/invocation witness");
    auto entry_release=handle.storage_->invocation->release;
    need(entry_release->forecast_attempts==0,"forecast entry already attempted");
    ++entry_release->forecast_attempts; // Failed reservation/allocation is not retried.
    auto data=std::make_unique<ForecastStorage>(*handle.storage_);
    invocation.storage_.reset(); // Public witness consumed; internal lifetime stays shared.
    auto r=data->invocation->release;
    try {
      need(r->constructor_attempts==1&&r->metadata_attempts==1&&r->rollout_attempts==0&&
           static_cast<bool>(data->profile->observed),"forecast release already consumed or metadata unverified");
      recheck(*r);++r->rollout_attempts;
      // Allocate RawResult object storage before evaluating its genuine return.
      // No caller-supplied RawResult or archived carrier enters this constructor.
      data->raw.reset(new RawResult(handle.storage_->model->rollout(data->invocation->initial,data->invocation->cells)));
      try {rawEnvelope(*data->raw,*data->invocation,data->result_ticket.slots());recheck(*r);}
      catch(const std::exception& e){data->structural_refusal=e.what();}
    } catch(const std::exception& e) {data->transport_failure=e.what();}
    // Original value/error/partial maps/force/friction/clip data is never rewritten
    // for unsuccessful nominal or derivative support. No shorter forecast exists.
    return OwnedPublicForecast(std::move(data));
  }
};
} // namespace detail

namespace {
template<class T> T& present(const std::unique_ptr<T>& p) {
  need(static_cast<bool>(p),"moved-from model-boundary witness");return *p;
}
template<class T> T& present(const std::shared_ptr<T>& p) {
  need(static_cast<bool>(p),"moved-from model-boundary witness");return *p;
}
}
OwnedLiveInvocation::OwnedLiveInvocation(std::shared_ptr<detail::InvocationStorage> p):storage_(std::move(p)){}
OwnedLiveInvocation::OwnedLiveInvocation(OwnedLiveInvocation&&) noexcept=default;
OwnedLiveInvocation& OwnedLiveInvocation::operator=(OwnedLiveInvocation&&) noexcept=default;
OwnedLiveInvocation::~OwnedLiveInvocation()=default;
const LiveActualContext& OwnedLiveInvocation::actualContext() const{return present(storage_).context;}
const CycleMesh& OwnedLiveInvocation::mesh() const{return present(storage_).mesh;}
const std::vector<NativeCell>& OwnedLiveInvocation::nativeCells() const{return present(storage_).cells;}
const std::string& OwnedLiveInvocation::invocationSha256() const{return present(storage_).release->invocation.sha256;}
const ResourcePlan& OwnedLiveInvocation::resourcePlan() const{return present(storage_).plan;}
PinnedModelHandle::PinnedModelHandle(std::unique_ptr<detail::HandleStorage> p):storage_(std::move(p)){}
PinnedModelHandle::PinnedModelHandle(PinnedModelHandle&&) noexcept=default;
PinnedModelHandle& PinnedModelHandle::operator=(PinnedModelHandle&&) noexcept=default;
PinnedModelHandle::~PinnedModelHandle()=default;
bool PinnedModelHandle::hasLiveModel() const noexcept{return storage_&&storage_->model&&storage_->profile&&storage_->profile->observed;}
const NativeMetadata& PinnedModelHandle::verifiedMetadata() const{return *present(storage_).profile->observed;}
const std::vector<FileIdentity>& PinnedModelHandle::verifiedFiles() const{return present(storage_).profile->release->files;}
const FileIdentity& PinnedModelHandle::currentProducerIdentity() const{return present(storage_).profile->release->producer;}
const FileIdentity& PinnedModelHandle::reviewRecordIdentity() const{return present(storage_).profile->release->review;}
const FileIdentity& PinnedModelHandle::protocolIdentity() const{return present(storage_).profile->release->protocol;}
ModelOpenOutcome::ModelOpenOutcome(std::unique_ptr<detail::OpenStorage> p):storage_(std::move(p)){}
ModelOpenOutcome::ModelOpenOutcome(ModelOpenOutcome&&) noexcept=default;
ModelOpenOutcome& ModelOpenOutcome::operator=(ModelOpenOutcome&&) noexcept=default;
ModelOpenOutcome::~ModelOpenOutcome()=default;
bool ModelOpenOutcome::hasModel() const{return storage_&&storage_->handle&&storage_->handle->hasLiveModel();}
PinnedModelHandle& ModelOpenOutcome::model(){auto& s=present(storage_);need(s.handle&&s.handle->hasLiveModel(),"model open refused or extracted");return *s.handle;}
const std::string& ModelOpenOutcome::refusal() const{return present(storage_).refusal;}
bool ModelOpenOutcome::constructorAttempted() const{return present(storage_).constructor_attempted;}
bool ModelOpenOutcome::metadataAttempted() const{return present(storage_).metadata_attempted;}
const NativeMetadata* ModelOpenOutcome::observedMetadata() const{auto& s=present(storage_);return s.profile?s.profile->observed.get():nullptr;}
OwnedPublicForecast::OwnedPublicForecast(std::unique_ptr<detail::ForecastStorage> p):storage_(std::move(p)){}
OwnedPublicForecast::OwnedPublicForecast(OwnedPublicForecast&&) noexcept=default;
OwnedPublicForecast& OwnedPublicForecast::operator=(OwnedPublicForecast&&) noexcept=default;
OwnedPublicForecast::~OwnedPublicForecast()=default;
const RawResult* OwnedPublicForecast::originalResult() const{return present(storage_).raw.get();}
const std::string& OwnedPublicForecast::transportFailure() const{return present(storage_).transport_failure;}
const std::string& OwnedPublicForecast::structuralRefusal() const{return present(storage_).structural_refusal;}
const LiveActualContext& OwnedPublicForecast::actualContext() const{return present(storage_).invocation->context;}
const CycleMesh& OwnedPublicForecast::mesh() const{return present(storage_).invocation->mesh;}
const std::vector<NativeCell>& OwnedPublicForecast::nativeCells() const{return present(storage_).invocation->cells;}
const std::string& OwnedPublicForecast::invocationSha256() const{return present(storage_).invocation->release->invocation.sha256;}
const NativeMetadata& OwnedPublicForecast::verifiedMetadata() const{return *present(storage_).profile->observed;}
const std::vector<FileIdentity>& OwnedPublicForecast::verifiedFiles() const{return present(storage_).profile->release->files;}
const FileIdentity& OwnedPublicForecast::currentProducerIdentity() const{return present(storage_).profile->release->producer;}
const FileIdentity& OwnedPublicForecast::reviewRecordIdentity() const{return present(storage_).profile->release->review;}
const FileIdentity& OwnedPublicForecast::protocolIdentity() const{return present(storage_).profile->release->protocol;}
CaseBudget& OwnedPublicForecast::normalizationBudget(){return present(storage_).invocation->budget;}
const ResourcePlan& OwnedPublicForecast::normalizationPlan() const{return present(storage_).invocation->plan;}
bool OwnedPublicForecast::hasVerifiedMemberCapture() const noexcept{return storage_&&storage_->profile&&storage_->profile->release->members&&storage_->profile->release->members->status.complete&&!storage_->profile->release->members->status.refused&&storage_->profile->release->files.size()==storage_->profile->release->file_roles.size()&&storage_->profile->release->files.size()==storage_->profile->release->members->relations.size();}
std::string_view OwnedPublicForecast::verifiedArtifactRole(Count k) const{need(hasVerifiedMemberCapture(),"legacy/incomplete member relationships are missing; no prefix zip");return present(storage_).profile->release->file_roles.at(k);}
const VerifiedMemberRelation& OwnedPublicForecast::verifiedMemberRelation(Count k) const{need(hasVerifiedMemberCapture(),"member relationship source absent/refused");const auto& r=*present(storage_).profile->release;const auto& relation=r.members->relations.at(k);need(relation.file_index==k&&relation.verified&&(relation.parent_is_protocol||relation.parent_index<r.files.size()),"actual relation index/parent invalid");return relation;}
const FileIdentity& OwnedPublicForecast::verifiedMemberParent(Count k) const{const auto& relation=verifiedMemberRelation(k);const auto& r=*present(storage_).profile->release;return relation.parent_is_protocol?r.protocol:r.files.at(relation.parent_index);}
const ClaimCaptureFactsV1* OwnedPublicForecast::capturedClaimFacts() const{const auto& release=*present(storage_).invocation->release;if(!release.members||!release.members->claim)return nullptr;const auto& m=*release.members;need(m.context&&m.claim->source==m.context->origin&&m.claim->budget.sameCase(m.budget),"claim metadata source/Case mismatch");return &m.claim->facts;}
Count OwnedPublicForecast::retainedMemberCount() const{const auto& r=*present(storage_).profile->release;return r.members?r.members->status.actual_files:0;}
const VerifiedMemberRelation& OwnedPublicForecast::retainedMemberRelation(Count k) const{const auto& r=*present(storage_).profile->release;need(r.members&&k<r.members->status.actual_files&&k<r.members->relations.size()&&k<r.files.size()&&k<r.file_roles.size(),"member committed prefix absent");const auto& relation=r.members->relations[k];need(relation.file_index==k&&relation.verified&&(relation.parent_is_protocol||relation.parent_index<k),"member committed identity/parent invalid");return relation;}
std::string_view OwnedPublicForecast::retainedMemberRole(Count k) const{retainedMemberRelation(k);return present(storage_).profile->release->file_roles[k];}
const FileIdentity& OwnedPublicForecast::retainedMemberParent(Count k) const{const auto& relation=retainedMemberRelation(k);const auto& r=*present(storage_).profile->release;return relation.parent_is_protocol?r.protocol:r.files[relation.parent_index];}
const CapturedLiveActualContextV1* OwnedPublicForecast::capturedActualContextInputs() const{const auto& inv=*present(storage_).invocation;return inv.captured_context?&*inv.captured_context:nullptr;}
const MemberLoaderObservationV1* OwnedPublicForecast::memberLoaderObservation() const{const auto& r=*present(storage_).profile->release;return r.members?&r.members->latest_loader:nullptr;}
const MemberIdentityObservationV1* OwnedPublicForecast::memberIdentityObservation() const{const auto& r=*present(storage_).profile->release;return r.members?&r.members->latest_identity:nullptr;}
const MemberCaptureStatus* OwnedPublicForecast::memberCaptureStatus() const{const auto& r=*present(storage_).profile->release;return r.members?&r.members->status:nullptr;}
const std::vector<FileIdentity>& OwnedPublicForecast::verifiedLoadedLibraries() const{return present(storage_).profile->release->libraries;}
std::string_view OwnedPublicForecast::reviewedAttemptClaimPath() const{return present(storage_).profile->release->attempt_claim_path;}
ReleaseAttemptFacts OwnedPublicForecast::releaseAttemptFacts() const{const auto& r=*present(storage_).profile->release;return {r.prepare_attempts,r.open_attempts,r.forecast_attempts,r.constructor_attempts,r.metadata_attempts,r.rollout_attempts};}
std::string_view OwnedPublicForecast::verifiedUnits() const{(void)present(storage_);return units;}
std::string_view OwnedPublicForecast::verifiedCertificateName() const{(void)present(storage_);return NativeModel::certificate_name;}
const char* OwnedPublicForecast::normalizationCertificate() const{(void)present(storage_);return NativeModel::certificate_name;}
const FactorShape& OwnedPublicForecast::costShape() const{return present(storage_).invocation->factors;}
const FileIdentity& OwnedPublicForecast::costInputIdentity() const{return present(storage_).invocation->cost_input;}
const std::string& OwnedPublicForecast::costSemanticSha256() const{return present(storage_).invocation->cost_semantic_sha256;}
ReviewedForecastPermission loadReviewedForecastPermissionWithMemberContextCaptureV3(const ReviewPins& pins,BatchBudget& batch){return detail::ForecastFactory::permission(pins,&batch,true);}
ReviewedForecastPermission loadReviewedForecastPermissionWithMemberContextClaimCaptureV4(const ReviewPins& pins,BatchBudget& batch){return detail::ForecastFactory::permission(pins,&batch,true,true);}
CapturedLiveActualContextV1 validateFrozenLiveActualWithSnapshotV3(ReviewedForecastPermission& permission,const ObservedActual& observed,const AcceptedCommandHistory& command,const ProgressHistory& progress,const NominalAnchor& nominal,const CurrentBoundaryExpectation& current,const StaticDomainRanges& ranges){return detail::ForecastFactory::validateContext(permission,observed,command,progress,nominal,current,ranges);}
OwnedLiveInvocation prepareFrozenLiveInvocationWithContextSnapshotV3(ReviewedForecastPermission& permission,const CapturedLiveActualContextV1& context,BatchBudget& batch){return detail::ForecastFactory::prepareCaptured(permission,context,batch);}
ReviewedForecastPermission loadReviewedForecastPermissionWithMemberCaptureV2(const ReviewPins& pins,BatchBudget& batch){return detail::ForecastFactory::permission(pins,&batch);}
ReviewedForecastPermission loadReviewedForecastPermission(const ReviewPins& pins){return detail::ForecastFactory::permission(pins);}
OwnedLiveInvocation prepareFrozenLiveInvocation(ReviewedForecastPermission& p,const LiveActualContext& c,BatchBudget& b){return detail::ForecastFactory::prepare(p,c,b);}
ModelOpenOutcome openPinnedModel(ReviewedForecastPermission& p,OwnedLiveInvocation& i){return detail::ForecastFactory::open(p,i);}
OwnedPublicForecast forecastPublic(PinnedModelHandle& h,OwnedLiveInvocation&& i){return detail::ForecastFactory::forecast(h,std::move(i));}
} // namespace phase5_public_live_affine_v2
