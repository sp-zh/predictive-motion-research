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
struct ForecastReleaseState {
  FileIdentity review,protocol,producer,xml,constants,policy,expected_metadata,invocation;
  std::vector<FileIdentity> files,libraries;
  std::string attempt_claim_path;
  Count prepare_attempts=0,open_attempts=0,forecast_attempts=0;
  Count constructor_attempts=0,metadata_attempts=0,rollout_attempts=0;
};
struct InvocationStorage {
  CaseBudget budget;OwnedReservation ticket;ResourcePlan plan;LiveActualContext context;
  CycleMesh mesh;NativeState initial;std::vector<NativeCell> cells;
  std::shared_ptr<ForecastReleaseState> release;
  InvocationStorage(BatchBudget& batch,const ResourcePlan& p,const LiveActualContext& c,const CycleMesh& m,
                    std::shared_ptr<ForecastReleaseState> r)
    :budget(batch,p),ticket(budget.reserve(checkedAdd(128,checkedMultiply(10,m.cycles().size())))),
     plan(p),context(c),mesh(m),release(std::move(r)) {}
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
    need(static_cast<bool>(permission.release_),"missing/moved-from reviewed release");return permission.release_;
  }
  static void recheck(const ForecastReleaseState& r) {
    verify(r.review);verify(r.protocol);observeCurrentProducerElf(r.producer.sha256);
    for(const auto& f:r.files)verify(f);verifyLoadedLibraries(r.libraries);
  }
  static ReviewedForecastPermission permission(const ReviewPins& pins) {
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
    keys(p,{"schema","source_kind","producer_sha256","constructor_attempts","metadata_attempts","rollout_attempts",
      "scope_claims","artifacts","attempt_claim_path"});
    need(text(p["schema"])=="PUBLIC_LIVE_AFFINE_V2_FROZEN_PROTOCOL_1"&&text(p["source_kind"])=="LiveActual"&&
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
    for(const auto& pair:by_role)r->files.push_back(pair.second);
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
      "augmented_extension.hpp","augmented_extension.cpp","augmented_extension_CMakeLists",
      "augmented_value.hpp","augmented_value.cpp","physical_derivative.hpp","physical_derivative.cpp","physical_derivative_CMakeLists",
      "physical_value.hpp","physical_value.cpp","physical_value_CMakeLists","coupled_friction_box.cpp"};
    for(const char* manifest_role:{"source_closure","sdk_manifest"}) {
      auto closure=readDocument(by_role.at(manifest_role));
      if(std::string(manifest_role)=="source_closure")keys(closure,{"schema","files"});
      else keys(closure,{"schema","files","loaded_libraries"});
      need(text(closure["schema"])==(std::string(manifest_role)=="source_closure"?"PUBLIC_LIVE_AFFINE_V2_SOURCE_CLOSURE_1":"PUBLIC_LIVE_AFFINE_V2_SDK_CLOSURE_1"),"closure schema mismatch");
      const auto files=closure["files"];need(files.IsSequence()&&files.size()>0&&files.size()<=4096,"bounded complete closure required");
      std::set<std::string> roles,paths;std::map<std::string,FileIdentity> verified;
      for(const auto& item:files) {auto a=artifact(item);need(roles.insert(a.role).second&&paths.insert(a.identity.path).second,"duplicate closure role/path");
        auto f=verify(a.identity);r->files.push_back(f);verified.emplace(f.path,f);}
      if(std::string(manifest_role)=="source_closure") {
        for(const auto& role:required_sources)need(roles.count(role)==1,"source closure omitted required compiled source/target");
      } else {
        auto libs=closure["loaded_libraries"];need(libs.IsSequence()&&libs.size()>0&&libs.size()<=512,"full loaded SDK library roster required");
        std::set<std::string> unique;
        for(const auto& item:libs) {auto name=text(item);need(unique.insert(name).second&&verified.count(name)==1,"loaded library missing from verified SDK closure");r->libraries.push_back(verified.at(name));}
      }
    }
    auto policy=readDocument(r->policy);
    keys(policy,{"schema","certificate_name","cycle_dt","substep_dt","control_margin","nx","nu","max_cells","max_cycles","max_samples"});
    need(text(policy["schema"])=="PUBLIC_LIVE_AFFINE_V2_DERIVATIVE_POLICY_1"&&text(policy["certificate_name"])==NativeModel::certificate_name&&
      number(policy["cycle_dt"])==macro_dt&&number(policy["substep_dt"])==physical_dt&&number(policy["control_margin"])==NativeModel::control_margin&&
      integer(policy["nx"])==30&&integer(policy["nu"])==8&&integer(policy["max_cells"])==32&&integer(policy["max_cycles"])==375&&integer(policy["max_samples"])==750,
      "unchanged derivative policy/versioned envelope mismatch");
    verifyLoadedLibraries(r->libraries);
    ReviewedForecastPermission out;out.release_=std::move(r);return out;
  }
  static OwnedLiveInvocation prepare(ReviewedForecastPermission& permission,const LiveActualContext& actual,
                                     BatchBudget& batch) {
    auto r=valid(permission);need(r->prepare_attempts==0,"invocation preparation already attempted");
    ++r->prepare_attempts;recheck(*r);
    const auto n=readDocument(r->invocation);
    keys(n,{"schema","source_kind","units","boundary","initial","previous_alpha","previous_b",
            "mesh","controls","factor_shape","capture_mode","encoding"});
    need(text(n["schema"])=="PUBLIC_LIVE_AFFINE_V2_INVOCATION_1"&&text(n["source_kind"])=="LiveActual"&&
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
    const auto capture=text(n["capture_mode"]),encoding=text(n["encoding"]);
    need(capture=="CompactComplete"||capture=="DenseAuditComplete","unknown frozen capture mode");
    need(encoding=="LosslessBinary"||encoding=="FullNumericJson","unknown frozen numeric encoding");
    auto plan=planResources(mesh,fs,capture=="CompactComplete"?CaptureMode::CompactComplete:CaptureMode::DenseAuditComplete,
                           encoding=="LosslessBinary"?NumericEncoding::LosslessBinary:NumericEncoding::FullNumericJson);
    const auto controls=n["controls"];need(controls.IsSequence()&&controls.size()==mesh.cycles().size(),"nominal control roster mismatch");
    auto data=std::make_shared<InvocationStorage>(batch,plan,actual,mesh,r);
    data->initial=nativeState(actual.actualInitial());data->cells.reserve(mesh.cycles().size());
    for(std::size_t k=0;k<controls.size();++k) {
      auto item=controls[k];keys(item,{"alpha","b"});const auto alpha=joints(item["alpha"]);
      NativeCell cell;cell.cycles=static_cast<int>(mesh.cycles()[k]);cell.alpha.resize(7);cell.b=number(item["b"]);
      for(std::size_t j=0;j<7;++j){need(std::abs(alpha[j])<=1,"nominal alpha outside unchanged closed domain");cell.alpha(j)=alpha[j];}
      data->cells.push_back(std::move(cell));
    }
    return OwnedLiveInvocation(std::move(data));
  }
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
      claim(*r); // Must precede actual constructor; failures retain immutable claim.
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
const char* OwnedPublicForecast::normalizationCertificate() const{(void)present(storage_);return NativeModel::certificate_name;}
ReviewedForecastPermission loadReviewedForecastPermission(const ReviewPins& pins){return detail::ForecastFactory::permission(pins);}
OwnedLiveInvocation prepareFrozenLiveInvocation(ReviewedForecastPermission& p,const LiveActualContext& c,BatchBudget& b){return detail::ForecastFactory::prepare(p,c,b);}
ModelOpenOutcome openPinnedModel(ReviewedForecastPermission& p,OwnedLiveInvocation& i){return detail::ForecastFactory::open(p,i);}
OwnedPublicForecast forecastPublic(PinnedModelHandle& h,OwnedLiveInvocation&& i){return detail::ForecastFactory::forecast(h,std::move(i));}
} // namespace phase5_public_live_affine_v2
