#include "foundation.hpp"
#include <openssl/evp.h>
#include <yaml-cpp/yaml.h>
#include <array>
#include <algorithm>
#include <string_view>
#include <cerrno>
#include <cmath>
#include <cstring>
#include <fcntl.h>
#include <limits>
#include <memory>
#include <set>
#include <stdexcept>
#include <sys/stat.h>
#include <unistd.h>
#include <utility>

namespace phase5_public_live_affine_v2 {
namespace {
void need(bool condition, const char* reason) {
  if (!condition) throw std::invalid_argument(reason);
}
void shaSyntax(const std::string& sha) {
  need(sha.size() == 64, "SHA256 must contain64 lowercase hexadecimal characters");
  for (char c : sha) need((c >= '0' && c <= '9') || (c >= 'a' && c <= 'f'),
                         "SHA256 must use lowercase hexadecimal");
}
class File final {
 public:
  File(const std::string& path, bool current_executable) {
    need(!path.empty() && path.size() <= 4096 && path.find('\0') == std::string::npos,
         "bounded file path without embedded NUL required");
    int flags = O_RDONLY | O_CLOEXEC;
    if (!current_executable) flags |= O_NOFOLLOW;
    fd_ = ::open(path.c_str(), flags);
    if (fd_ < 0) throw std::runtime_error("cannot open identity input: " + std::string(std::strerror(errno)));
  }
  File(const File&) = delete;
  File& operator=(const File&) = delete;
  ~File() { if (fd_ >= 0) ::close(fd_); }
  int fd() const noexcept { return fd_; }
 private: int fd_ = -1;
};
struct ReadResult { FileIdentity identity; std::string text; };
ReadResult readPinned(const std::string& path, const std::string& expected,
                      bool text, bool current_executable) {
  shaSyntax(expected);
  File file(path, current_executable);
  struct stat before{}, after{};
  need(::fstat(file.fd(), &before) == 0 && S_ISREG(before.st_mode) && before.st_size >= 0,
       "identity input must be a regular file");
  const Count cap = text ? ResourcePolicyV2::metadata_bytes : 512ULL * 1024 * 1024;
  need(static_cast<Count>(before.st_size) > 0 && static_cast<Count>(before.st_size) <= cap,
       "identity input byte cap exceeded or empty file");
  using DigestPtr = std::unique_ptr<EVP_MD_CTX, decltype(&EVP_MD_CTX_free)>;
  DigestPtr digest(EVP_MD_CTX_new(), EVP_MD_CTX_free);
  need(digest && EVP_DigestInit_ex(digest.get(), EVP_sha256(), nullptr) == 1,
       "SHA256 initialization failed");
  ReadResult out; out.identity.path = path;
  std::array<unsigned char, 65536> buffer{};
  std::array<unsigned char, 4> magic{}; Count count = 0;
  if (text) out.text.reserve(static_cast<std::size_t>(before.st_size));
  for (;;) {
    const ssize_t got = ::read(file.fd(), buffer.data(), buffer.size());
    if (got < 0 && errno == EINTR) continue;
    if (got < 0) throw std::runtime_error("identity input read failed");
    if (got == 0) break;
    const Count next = checkedAdd(count, static_cast<Count>(got));
    need(next <= cap, "identity input grew beyond byte cap");
    for (Count k = count; k < next && k < 4; ++k)
      magic[static_cast<std::size_t>(k)] = buffer[static_cast<std::size_t>(k - count)];
    need(EVP_DigestUpdate(digest.get(), buffer.data(), static_cast<std::size_t>(got)) == 1,
         "SHA256 update failed");
    if (text) out.text.append(reinterpret_cast<const char*>(buffer.data()), static_cast<std::size_t>(got));
    count = next;
  }
  need(::fstat(file.fd(), &after) == 0 && before.st_dev == after.st_dev &&
       before.st_ino == after.st_ino && before.st_size == after.st_size &&
       count == static_cast<Count>(before.st_size), "identity input changed size/inode during read");
  unsigned int length = 0; std::array<unsigned char, EVP_MAX_MD_SIZE> bytes{};
  need(EVP_DigestFinal_ex(digest.get(), bytes.data(), &length) == 1 && length == 32,
       "SHA256 finalization failed");
  constexpr char hex[] = "0123456789abcdef";
  for (unsigned int j = 0; j < length; ++j) {
    out.identity.sha256.push_back(hex[bytes[j] >> 4]);
    out.identity.sha256.push_back(hex[bytes[j] & 15]);
  }
  out.identity.bytes = count;
  need(out.identity.sha256 == expected, "identity input SHA256 mismatch");
  if (current_executable) {
    need(count >= 4 && magic[0] == 0x7f && magic[1] == 'E' && magic[2] == 'L' && magic[3] == 'F',
         "live producer must be the actual current Linux ELF");
    need(expected != "f1b7e6c7e4219fec2beb310540c725b448dcf021b3a95ddafc2922e8849bf1d6",
         "archived f1 producer is not the new live producer");
  }
  return out;
}
YAML::Node list(const YAML::Node& root, const char* key, std::size_t length) {
  const auto value = root[key];
  need(value.IsSequence() && value.size() == length, "static range/list roster mismatch");
  return value;
}
}
namespace {
FileIdentity memberIdentity(SharedCaseBudget budget,const std::string& path,const std::string& expected,Count expected_bytes,bool current,MemberIdentityObservationV1& observation){
  try{need(observation.stage&&!observation.refused&&std::string_view(observation.stage)=="NOT_ATTEMPTED","member identity observation already attempted/refused");shaSyntax(expected);need(expected_bytes>0&&expected_bytes<=512ULL*1024*1024,"member actual file byte envelope");need(!path.empty()&&path.front()=='/'&&path.size()<=4096&&path.find('\0')==std::string::npos,"bounded actual member path");
    auto ticket=budget.reserve(8224); // cache8192,digest8,magic1,stat/cursor/control23.
    observation.stage="OPEN_ACTUAL_MEMBER_FD";File file(path,current);struct stat before{},after{};need(::fstat(file.fd(),&before)==0&&S_ISREG(before.st_mode)&&before.st_size>=0&&static_cast<Count>(before.st_size)==expected_bytes,"member FD nonregular/frozen size mismatch");
    observation.device=before.st_dev;observation.inode=before.st_ino;observation.size=before.st_size;using DigestPtr=std::unique_ptr<EVP_MD_CTX,decltype(&EVP_MD_CTX_free)>;DigestPtr digest(EVP_MD_CTX_new(),EVP_MD_CTX_free);need(digest&&EVP_DigestInit_ex(digest.get(),EVP_sha256(),nullptr)==1,"member hash initialize");observation.hash_state_valid=true;
    std::array<unsigned char,65536> cache;budget.chargeScratchOrCopy(1);std::array<unsigned char,4> magic{};Count count=0;
    while(count<expected_bytes){const Count remaining=expected_bytes-count,request=std::min<Count>(remaining,cache.size());observation.stage="READ_BOUNDED_MEMBER_BYTES";observation.attempted_read_bytes=request;budget.chargeScratchOrCopy(8192);const ssize_t n=::read(file.fd(),cache.data(),request);if(n<0&&errno==EINTR)continue;need(n>0&&static_cast<Count>(n)<=request,"member short/error/truncated read");
      for(Count k=count;k<count+static_cast<Count>(n)&&k<4;++k)magic[k]=cache[k-count];count=checkedAdd(count,n);observation.bytes_read=count;observation.hash_state_valid=false;need(EVP_DigestUpdate(digest.get(),cache.data(),n)==1,"member actual byte hash update");observation.hash_state_valid=true;
    }
    observation.stage="ACTUAL_MEMBER_EOF";observation.attempted_read_bytes=1;budget.chargeScratchOrCopy(1);unsigned char extra=0;ssize_t end;do{budget.chargeScratchOrCopy(1);end=::read(file.fd(),&extra,1);}while(end<0&&errno==EINTR);need(end==0,"member extra/grown/error EOF");observation.physical_eof=true;
    need(::fstat(file.fd(),&after)==0&&before.st_dev==after.st_dev&&before.st_ino==after.st_ino&&before.st_size==after.st_size&&S_ISREG(after.st_mode)&&count==expected_bytes,"member actual FD changed");
    budget.chargeScratchOrCopy(8);unsigned int length=0;std::array<unsigned char,EVP_MAX_MD_SIZE> bytes{};need(EVP_DigestFinal_ex(digest.get(),bytes.data(),&length)==1&&length==32,"member actual hash final");
    budget.chargeMetadataBytes(checkedAdd(path.size(),128));budget.chargeScratchOrCopy(checkedAdd((path.size()+7)/8,16));FileIdentity out;out.path=path;out.bytes=count;out.sha256.reserve(64);constexpr char hex[]="0123456789abcdef";for(unsigned j=0;j<length;++j){out.sha256.push_back(hex[bytes[j]>>4]);out.sha256.push_back(hex[bytes[j]&15]);}observation.physical_sha256=out.sha256;observation.hash_state_valid=false;observation.hash_valid=true;need(out.sha256==expected,"member actual SHA differs");
    if(current){need(path=="/proc/self/exe"&&count>=4&&magic[0]==0x7f&&magic[1]=='E'&&magic[2]=='L'&&magic[3]=='F',"actual Linux member producer ELF required");need(expected!="f1b7e6c7e4219fec2beb310540c725b448dcf021b3a95ddafc2922e8849bf1d6","archived producer forbidden");}
    observation.stage="VERIFIED_ACTUAL_MEMBER";return out;
  }catch(const std::exception& e){observation.refused=true;try{std::string_view why=e.what();need(why.size()<=512,"member error detail cap");budget.chargeMetadataBytes(why.size());observation.first_error.assign(why);}catch(...){}throw;}catch(...){observation.refused=true;observation.stage="NONSTANDARD_MEMBER_IDENTITY_REFUSAL";throw;}
}
}
FileIdentity observePinnedFileWithMemberBudgetV1(SharedCaseBudget budget,const FileIdentity& expected,MemberIdentityObservationV1& observation){return memberIdentity(std::move(budget),expected.path,expected.sha256,expected.bytes,false,observation);}
FileIdentity observeCurrentProducerElfWithMemberBudgetV1(SharedCaseBudget budget,const std::string& expected_sha,Count expected_bytes,MemberIdentityObservationV1& observation){
#if defined(__linux__)
  return memberIdentity(std::move(budget),"/proc/self/exe",expected_sha,expected_bytes,true,observation);
#else
  (void)budget;(void)expected_sha;(void)expected_bytes;observation.refused=true;throw std::invalid_argument("member producer requires actual current Linux ELF");
#endif
}
FileIdentity observePinnedFile(const std::string& path, const std::string& expected) {
  return readPinned(path, expected, false, false).identity;
}
FileIdentity observeCurrentProducerElf(const std::string& expected) {
#if defined(__linux__)
  // Open the kernel's current executable binding, not a caller-selected path.
  return readPinned("/proc/self/exe", expected, false, true).identity;
#else
  (void)expected;
  throw std::invalid_argument("live producer identity requires Linux current ELF; unsupported host");
#endif
}
StaticDomainRanges loadPinnedStaticRanges(const std::string& path, const std::string& expected) {
  auto source = readPinned(path, expected, true, false);
  // Parse EXACTLY the hashed bytes. No second path open, constructor or Model query.
  auto root = YAML::Load(source.text);
  need(root.IsMap(), "static constants must be a keyed object");
  std::set<std::string> names;
  for (const auto& entry : root) {
    need(entry.first.IsScalar(), "static constants key must be scalar");
    need(names.insert(entry.first.as<std::string>()).second, "duplicate static constants key");
  }
  const auto q = list(root, "joint_range", 14), c = list(root, "control_range", 14);
  const auto q_limited = list(root, "joint_limited", 7), c_limited = list(root, "control_limited", 7);
  StaticDomainRanges out; out.identity_ = std::move(source.identity);
  for (std::size_t j = 0; j < 7; ++j) {
    need(q_limited[j].as<int>() == 1 && c_limited[j].as<int>() == 1,
         "fixed bounded FR3 joint and command profile required");
    out.q_lower_[j] = q[2*j].as<double>(); out.q_upper_[j] = q[2*j+1].as<double>();
    out.c_lower_[j] = c[2*j].as<double>(); out.c_upper_[j] = c[2*j+1].as<double>();
    need(std::isfinite(out.q_lower_[j]) && std::isfinite(out.q_upper_[j]) &&
         std::isfinite(out.c_lower_[j]) && std::isfinite(out.c_upper_[j]) &&
         out.q_lower_[j] < out.q_upper_[j] && out.c_lower_[j] < out.c_upper_[j],
         "finite ordered static ranges required");
  }
  return out;
  // This is a constants-file range witness, not a VerifiedModelProfile: actual
  // nq/nv/SDK/masses/XML/runtime/derivative identity remains a stage-2 obligation.
}
} // namespace phase5_public_live_affine_v2
