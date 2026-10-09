#pragma once
#include "numeric_chunks.hpp"
#include <openssl/evp.h>
#include <array>
#include <cstring>
#include <fcntl.h>
#include <limits>
#include <memory>
#include <stdexcept>
#include <sys/stat.h>
#include <unistd.h>
namespace phase5_public_live_affine_v2::chunk_detail {
inline void need(bool b,const char* s){if(!b)throw std::invalid_argument(s);}
inline Count add(Count a,Count b){return checkedAdd(a,b);}
inline Count mul(Count a,Count b){return checkedMultiply(a,b);}
struct FD {
  int value=-1;FD()=default;explicit FD(int n):value(n){}
  FD(const FD&)=delete;FD& operator=(const FD&)=delete;
  ~FD(){if(value>=0)::close(value);}
};
inline bool safeChar(unsigned char c){return(c>='a'&&c<='z')||(c>='A'&&c<='Z')||(c>='0'&&c<='9')||c=='_'||c=='-'||c=='.';}
inline void component(const std::string& s,Count cap){need(!s.empty()&&s.size()<=cap&&s!="."&&s!="..","bounded safe component required");for(unsigned char c:s)need(safeChar(c),"unsafe path/role character");}
inline int directory(const std::string& path){
  need(!path.empty()&&path[0]=='/'&&path.size()<=4096&&path.find('\0')==std::string::npos,"bounded absolute root required");
  FD current(::open("/",O_RDONLY|O_DIRECTORY|O_CLOEXEC));need(current.value>=0,"root directory open failed");
  std::size_t at=1;while(at<path.size()){const auto end=path.find('/',at);const auto part=path.substr(at,end==std::string::npos?path.size()-at:end-at);
    component(part,255);const int next=::openat(current.value,part.c_str(),O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC);
    need(next>=0,"directory component absent/symlink/not directory");::close(current.value);current.value=next;
    if(end==std::string::npos)break;at=end+1;need(at<path.size(),"trailing root slash refused");
  }const int out=current.value;current.value=-1;return out;
}
inline Count sealSpec(NumericChunkSpec& s){
  component(s.relative_name,128);component(s.role,128);
  need(s.relative_name.size()>12&&s.relative_name.compare(s.relative_name.size()-12,12,".provisional")==0,"only provisional numeric names accepted");
  need(s.dimensions.size()<=4,"at most4 chunk axes");Count n=1;for(Count d:s.dimensions)n=mul(n,d);
  need(n<=ResourcePolicyV2::matrix_entries,"chunk element cap");
  need(s.kind==ChunkScalarKind::F64||s.kind==ChunkScalarKind::U64||s.kind==ChunkScalarKind::I64||s.kind==ChunkScalarKind::FailureF64Bits,"unknown chunk scalar type");
  need(s.classification==ChunkClassification::FiniteFields||s.classification==ChunkClassification::ForensicDefinedFields,"unknown chunk classification");
  need(s.kind!=ChunkScalarKind::FailureF64Bits||s.classification==ChunkClassification::ForensicDefinedFields,"failure IEEE bits cannot be finite success fields");return n;
}
inline const char* typeName(ChunkScalarKind k){switch(k){case ChunkScalarKind::F64:return "f64";case ChunkScalarKind::U64:return "u64";case ChunkScalarKind::I64:return "i64";case ChunkScalarKind::FailureF64Bits:return "f64_ieee_bits";}throw std::invalid_argument("unknown scalar type");}
struct SHA {
  std::unique_ptr<EVP_MD_CTX,decltype(&EVP_MD_CTX_free)> data{EVP_MD_CTX_new(),EVP_MD_CTX_free};
  SHA(){need(data&&EVP_DigestInit_ex(data.get(),EVP_sha256(),nullptr)==1,"chunk SHA init");}
  void update(const void* p,std::size_t n){need(EVP_DigestUpdate(data.get(),p,n)==1,"chunk SHA update");}
  std::string digest() const {
    std::unique_ptr<EVP_MD_CTX,decltype(&EVP_MD_CTX_free)> copy(EVP_MD_CTX_new(),EVP_MD_CTX_free);
    need(copy&&EVP_MD_CTX_copy_ex(copy.get(),data.get())==1,"chunk SHA copy");
    std::array<unsigned char,EVP_MAX_MD_SIZE> bytes{};unsigned n=0;need(EVP_DigestFinal_ex(copy.get(),bytes.data(),&n)==1&&n==32,"chunk SHA final");
    constexpr char hex[]="0123456789abcdef";std::string out;for(unsigned i=0;i<n;++i){out.push_back(hex[bytes[i]>>4]);out.push_back(hex[bytes[i]&15]);}return out;
  }
};
inline void reject(ChunkIOObservation& s,const char* error) noexcept{if(s.refused)return;s.refused=true;try{s.first_error=error?error:"CHUNK_IO_REFUSAL";}catch(...){}}
inline double asDouble(Count n){static_assert(sizeof(double)==8&&std::numeric_limits<double>::is_iec559,"IEEE binary64 required");double value;std::memcpy(&value,&n,8);return value;}
inline std::int64_t asSigned(Count n){std::int64_t value;static_assert(sizeof(value)==8,"i64 required");std::memcpy(&value,&n,8);return value;}
}
