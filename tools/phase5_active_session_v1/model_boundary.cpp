#include "model_boundary.hpp"
#include <yaml-cpp/yaml.h>
#include <openssl/evp.h>
#include <cmath>
#include <cstring>
#include <sstream>
#include <iomanip>
#include <stdexcept>
#include <utility>
#include <link.h>
#include <set>
#include <filesystem>
#include <sys/stat.h>
#include <sys/sysmacros.h>
#include <type_traits>
#include <fstream>
namespace phase5_active_session_v1 {
namespace {
void need(bool c,const char* s){if(!c)throw std::invalid_argument(s);}
CycleMesh fixedMesh(){HorizonSpec h;h.policy=MeshPolicy::ExplicitCycles;h.explicit_cycles={1,1,2,2,3,3,4,4,5,5,6,6,8,10,12,16,20,24,28,40};return planMesh(h);}
void pin(const FileIdentity& f){const auto got=observePinnedFile(f.path,f.sha256);need(got.bytes==f.bytes,"pinned byte length changed");}
void equalMetadata(const NativeMetadata& m,const FileIdentity& f){
 const auto n=YAML::LoadFile(f.path);
 need(n.IsMap()&&n.size()==16,"exact metadata key roster required");
 need(n["units"].as<std::string>()=="q/C rad,v/w rad/s,s dimensionless,r1/s; alpha rad/s^2,b1/s^2; time seconds; mass kg/armature kg*m^2"&&m.nq==7&&m.nv==7&&m.pinocchio_version=="4.1.0","fixed metadata units/version/domain required");
 need(m.joint_names.size()==7&&m.idx_q.size()==7&&m.idx_v.size()==7&&m.joint_nq.size()==7&&m.joint_nv.size()==7,"fixed joint mapping shape");
 for(int j=0;j<7;++j)need(m.idx_q[j]==j&&m.idx_v[j]==j&&m.joint_nq[j]==1&&m.joint_nv[j]==1,"fixed scalar coordinate mapping");
 need(m.masses.size()==8&&m.armature.size()==7&&m.gravity.size()==3&&m.R.size()==7&&m.B.size()==7&&m.damping.size()==7&&m.masses.allFinite()&&m.armature.allFinite()&&m.gravity.allFinite()&&m.R.allFinite()&&m.B.allFinite()&&m.damping.allFinite()&&(m.masses.array()>=0).all()&&(m.armature.array()>=0).all()&&(m.R.array()>0).all()&&(m.B.array()>0).all()&&(m.damping.array()>=0).all(),"metadata coefficient domain");
 need(n["pinocchio_version"].as<std::string>()==m.pinocchio_version&&n["nq"].as<int>()==m.nq&&n["nv"].as<int>()==m.nv,"metadata version/dimension mismatch");
 auto list=[&](const char* k,const auto& v){const auto a=n[k];need(a.IsSequence()&&a.size()==v.size(),"metadata list shape mismatch");for(std::size_t i=0;i<v.size();++i)need(a[i].template as<typename std::decay_t<decltype(v)>::value_type>()==v[i],"metadata list mismatch");};
 list("joint_names",m.joint_names);list("frame_names",m.frame_names);list("idx_q",m.idx_q);list("idx_v",m.idx_v);list("joint_nq",m.joint_nq);list("joint_nv",m.joint_nv);
 auto vector=[&](const char* k,const Eigen::VectorXd& v){const auto a=n[k];need(a.IsSequence()&&a.size()==static_cast<std::size_t>(v.size()),"metadata vector shape mismatch");for(Eigen::Index i=0;i<v.size();++i){double x=a[i].as<double>();need(std::isfinite(x)&&x==v(i),"metadata scalar mismatch");}};
 vector("masses",m.masses);vector("armature",m.armature);vector("gravity",m.gravity);vector("R",m.R);vector("B",m.B);vector("damping",m.damping);
}
class Digest {
 std::unique_ptr<EVP_MD_CTX,decltype(&EVP_MD_CTX_free)> p{EVP_MD_CTX_new(),EVP_MD_CTX_free};
 public:
 Digest(){need(p&&EVP_DigestInit_ex(p.get(),EVP_sha256(),nullptr)==1,"digest init failed");}
 void bytes(const void* b,std::size_t n){need(EVP_DigestUpdate(p.get(),b,n)==1,"digest update failed");}
 void integer(Count x){unsigned char b[8];for(int i=0;i<8;++i)b[i]=static_cast<unsigned char>(x>>(8*i));bytes(b,8);}
 void number(double x){need(std::isfinite(x),"nonfinite cycle digest");static_assert(sizeof(double)==8);Count u;std::memcpy(&u,&x,8);integer(u);}
 void text(const std::string& s){integer(s.size());bytes(s.data(),s.size());}
 std::string finish(){unsigned char b[32];unsigned int n=0;need(EVP_DigestFinal_ex(p.get(),b,&n)==1&&n==32,"digest final failed");std::ostringstream out;for(unsigned char x:b)out<<std::hex<<std::setw(2)<<std::setfill('0')<<static_cast<unsigned>(x);return out.str();}
};
void loaded(const std::vector<FileIdentity>& expected){
 need(!expected.empty(),"loaded SDK roster required");
 struct Capture {std::set<std::string> paths;bool failed=false;} observed;
 dl_iterate_phdr([](dl_phdr_info* info,std::size_t,void* data){
  auto& c=*static_cast<Capture*>(data);
  if(!info->dlpi_name||!*info->dlpi_name||std::string(info->dlpi_name)=="linux-vdso.so.1")return 0;
  try{c.paths.insert(std::filesystem::canonical(info->dlpi_name).string());}catch(...){c.failed=true;}
  return 0;
 },&observed);
 need(!observed.failed,"loaded object canonicalization failed");
 std::set<std::string> declared;
 for(const auto& x:expected){need(std::filesystem::canonical(x.path).string()==x.path,"loaded SDK pin must be canonical");need(declared.insert(x.path).second,"duplicate loaded SDK pin");pin(x);}
 need(observed.paths==declared,"actual loaded SDK roster differs from pins");
 // Loader roster names alone do not bind inode: verify mapped file backing.
 std::ifstream in("/proc/self/maps");need(bool(in),"Linux mapping inventory unavailable");
 std::string line;std::set<std::string> backed;
 while(std::getline(in,line)){
  std::istringstream row(line);std::string range,perms,offset,device;unsigned long long inode=0;
  if(!(row>>range>>perms>>offset>>device>>inode))throw std::invalid_argument("mapping parse failure");
  std::string name;std::getline(row,name);auto begin=name.find_first_not_of(' ');if(begin==std::string::npos||name[begin]!='/')continue;name=name.substr(begin);
  if(!declared.count(name)) continue;
  struct stat st{};need(::stat(name.c_str(),&st)==0&&S_ISREG(st.st_mode)&&static_cast<unsigned long long>(st.st_ino)==inode,"mapped SDK inode changed");
  const auto colon=device.find(':');need(colon!=std::string::npos&&std::stoull(device.substr(0,colon),nullptr,16)==major(st.st_dev)&&std::stoull(device.substr(colon+1),nullptr,16)==minor(st.st_dev),"mapped SDK device changed");backed.insert(name);
 }
 need(backed==declared,"loaded SDK lacks mapped backing proof");
}

}
namespace detail {
struct SessionStorage {
 SessionPins pins;BatchBudget batch;StaticDomainRanges ranges;
 CycleMesh mesh;ResourcePlan resident_plan;CaseBudget resident_budget;
 OwnedReservation resident_ticket; // Model and metadata are destroyed before this reservation
 std::unique_ptr<phase5_public_coupled_augmented_extension::Model> model;
 NativeMetadata metadata;bool verified=false,terminated=false,termination_passed=false;std::string termination_failure;Count ordinal=0;std::string binding_digest;
 explicit SessionStorage(const SessionPins& p):pins(p),ranges(loadPinnedStaticRanges(p.constants.path,p.constants.sha256)),mesh(fixedMesh()),resident_plan(planResources(mesh,FactorShape{},CaptureMode::CompactComplete,NumericEncoding::LosslessBinary)),resident_budget(batch,resident_plan),resident_ticket(resident_budget.reserve(resident_plan.sdkPlanningAllowance())){
  need(!pins.session_id.empty()&&pins.session_id.size()<=256,"bounded session identity required");
  checkPins();model=std::make_unique<phase5_public_coupled_augmented_extension::Model>(pins.xml.path,pins.constants.path);
  metadata=model->metadata();equalMetadata(metadata,pins.expected_metadata);checkPins();
  Digest d;d.text("ACTIVE_SESSION_MODEL_BINDING_V1");d.text(pins.session_id);
  auto add=[&](const FileIdentity& x){d.text(x.path);d.integer(x.bytes);d.text(x.sha256);};
  for(const auto* x:{&pins.producer,&pins.xml,&pins.constants,&pins.expected_metadata})add(*x);
  d.integer(pins.dependencies.size());for(const auto& x:pins.dependencies)add(x);
  d.integer(pins.loaded_libraries.size());for(const auto& x:pins.loaded_libraries)add(x);
  binding_digest=d.finish();verified=true;
 }
 void checkPins(){auto producer=observeCurrentProducerElf(pins.producer.sha256);need(producer.bytes==pins.producer.bytes&&std::filesystem::canonical("/proc/self/exe").string()==pins.producer.path,"producer size/path changed");pin(pins.producer);pin(pins.xml);pin(pins.constants);pin(pins.expected_metadata);need(!pins.dependencies.empty(),"dependency roster required");for(const auto& x:pins.dependencies)pin(x);loaded(pins.loaded_libraries);}
};
struct ForecastStorage {
 std::shared_ptr<SessionStorage> session;
 CycleMesh mesh;ResourcePlan plan;CaseBudget budget;
 OwnedReservation source_ticket; // context69 + native cells180 + initial30; resident native workspace is Session-owned
 LiveActualContext context;
 std::vector<phase5_public_coupled_augmented::Cell> cells;
 double observer_age;std::string digest,transport,structural;
 OwnedReservation raw_ticket; // raw destroyed before ticket, budget and session
 std::unique_ptr<RawResult> raw;
 ForecastStorage(std::shared_ptr<SessionStorage> s,const LiveActualContext& c,const CycleMesh& m,double age)
 :session(std::move(s)),mesh(m),plan(planResources(mesh,FactorShape{},CaptureMode::CompactComplete,NumericEncoding::LosslessBinary)),budget(session->batch,plan),source_ticket(budget.reserve(279)),context(c),observer_age(age),raw_ticket(budget.reserve(plan.rawResultShapeSlots())){}
};
}
Session::Session(const SessionPins& p):storage_(std::make_shared<detail::SessionStorage>(p)){}
Session::~Session()=default;
const NativeMetadata& Session::verifiedMetadata() const{return storage_->metadata;}
void Session::verifyTermination(){need(!storage_->terminated,"session already terminated");storage_->terminated=true;try{storage_->checkPins();storage_->termination_passed=true;}catch(const std::exception& e){storage_->verified=false;storage_->termination_failure=e.what();throw;}catch(...){storage_->verified=false;storage_->termination_failure="unknown termination verification failure";throw;}}
bool Session::terminationVerified() const{return storage_->terminated&&storage_->termination_passed&&storage_->termination_failure.empty();}
const std::string& Session::terminationFailure() const{return storage_->termination_failure;}
Count Session::cumulativeCharges() const{return storage_->batch.cumulativeCharges();}
OwnedPublicForecast Session::forecast(const ObservedActual& obs,const AcceptedCommandHistory& cmd,const ProgressHistory& prog,const CurrentBoundaryExpectation& current,const std::vector<NominalControl>& controls){
 auto& s=*storage_;need(s.verified&&!s.terminated,"inactive session");s.ordinal=checkedAdd(s.ordinal,1);need(controls.size()==20,"N20 controls required");
 State30 initial;initial.q=obs.q;initial.v=obs.v;initial.C=cmd.C;initial.w=cmd.w;initial.s=prog.s;initial.r=prog.r;
 const auto context=validateLiveActual(obs,cmd,prog,NominalAnchor{initial,current.boundary},current,s.ranges);
 auto f=std::make_unique<detail::ForecastStorage>(storage_,context,s.mesh,obs.state_age_seconds);
 f->cells.reserve(20);Digest d;d.text("ACTIVE_SESSION_CYCLE_V1");d.text(s.binding_digest);d.integer(s.ordinal);d.integer(current.boundary.completed_tick);d.integer(current.boundary.completed_command_sequence);d.text(obs.observation_id);d.text(obs.transaction_id);d.number(obs.state_age_seconds);
 for(const JointVector* v:std::array<const JointVector*,5>{&initial.q,&initial.v,&initial.C,&initial.w,&cmd.previous_alpha}) {
  for(double x:*v) d.number(x);
 }
 d.number(initial.s);d.number(initial.r);d.number(prog.previous_b);
 for(std::size_t k=0;k<controls.size();++k){phase5_public_coupled_augmented::Cell c;c.cycles=static_cast<int>(f->mesh.cycles()[k]);c.alpha.resize(7);for(int j=0;j<7;++j){need(std::isfinite(controls[k].alpha[j])&&std::abs(controls[k].alpha[j])<=1,"nominal alpha outside domain");c.alpha(j)=controls[k].alpha[j];d.number(c.alpha(j));}need(std::isfinite(controls[k].b),"nonfinite nominal progress input");c.b=controls[k].b;d.number(c.b);d.integer(c.cycles);f->cells.push_back(std::move(c));}
 f->digest=d.finish();phase5_public_coupled_augmented::State native;native.q=Eigen::Map<const Eigen::VectorXd>(initial.q.data(),7);native.v=Eigen::Map<const Eigen::VectorXd>(initial.v.data(),7);native.C=Eigen::Map<const Eigen::VectorXd>(initial.C.data(),7);native.w=Eigen::Map<const Eigen::VectorXd>(initial.w.data(),7);native.s=initial.s;native.r=initial.r;
 try{f->raw=std::make_unique<RawResult>(s.model->rollout(native,f->cells));}catch(const std::exception& e){f->transport=e.what();}catch(...){f->transport="unknown model exception";}
 return OwnedPublicForecast(std::move(f));
}
OwnedPublicForecast::OwnedPublicForecast(std::unique_ptr<detail::ForecastStorage> p):storage_(std::move(p)){}
OwnedPublicForecast::OwnedPublicForecast(OwnedPublicForecast&&) noexcept=default;
OwnedPublicForecast& OwnedPublicForecast::operator=(OwnedPublicForecast&&) noexcept=default;
OwnedPublicForecast::~OwnedPublicForecast()=default;
namespace {const detail::ForecastStorage& present(const std::unique_ptr<detail::ForecastStorage>& p){need(bool(p),"moved forecast");return *p;}}
const RawResult* OwnedPublicForecast::originalResult() const{return present(storage_).raw.get();}
const std::string& OwnedPublicForecast::transportFailure() const{return present(storage_).transport;}
const std::string& OwnedPublicForecast::structuralRefusal() const{return present(storage_).structural;}
const LiveActualContext& OwnedPublicForecast::actualContext() const{return present(storage_).context;}
const CycleMesh& OwnedPublicForecast::mesh() const{return present(storage_).mesh;}
const std::vector<phase5_public_coupled_augmented::Cell>& OwnedPublicForecast::nativeCells() const{return present(storage_).cells;}
const std::string& OwnedPublicForecast::invocationSha256() const{return present(storage_).digest;}
const NativeMetadata& OwnedPublicForecast::verifiedMetadata() const{return present(storage_).session->metadata;}
const SessionPins& OwnedPublicForecast::startupPins() const{return present(storage_).session->pins;}
double OwnedPublicForecast::originalObservedAge() const{return present(storage_).observer_age;}
bool OwnedPublicForecast::bindingVerified() const noexcept{return storage_&&storage_->session->verified&&!storage_->digest.empty();}
CaseBudget& OwnedPublicForecast::normalizationBudget(){need(bool(storage_),"moved forecast");return storage_->budget;}
const ResourcePlan& OwnedPublicForecast::normalizationPlan() const{return present(storage_).plan;}
const char* OwnedPublicForecast::normalizationCertificate() const{return phase5_public_coupled_augmented_extension::Model::certificate_name;}
}
