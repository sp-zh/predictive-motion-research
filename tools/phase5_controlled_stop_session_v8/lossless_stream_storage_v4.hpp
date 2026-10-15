#pragma once
#include <zlib.h>
#include <openssl/evp.h>
#include <array>
#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <functional>
#include <limits>
#include <memory>
#include <stdexcept>
#include <string>
#include <cstdlib>
namespace phase5_lossless_stream_storage_v4 {
inline void need(bool b,const char* s){if(!b)throw std::runtime_error(s);}
constexpr std::uint64_t buffer_bytes=65536,allocation_cap=1048576;
constexpr std::uint64_t conservativeBound(std::uint64_t raw){return raw+raw/4+65536;}
class StoredBudget {
 std::uint64_t cap_,spent_=0,tail_=0;bool final_=false;
 public:StoredBudget(std::uint64_t cap,std::uint64_t tail):cap_(cap),tail_(tail){need(cap>0&&cap<=7ULL*1024*1024*1024&&tail<cap,"declared finite storedbyte budget and tail");}
 void reserve(std::uint64_t n){need(spent_<=cap_-tail_&&n<=cap_-tail_-spent_,"storedbyte prewrite budget exhausted, retain failure");spent_+=n;}
 void beginFinalization(){need(!final_,"single stored tail release noreset");final_=true;tail_=0;}
 std::uint64_t charged()const{return spent_;}std::uint64_t cap()const{return cap_;}
};
class Gzip {
 struct Allocation {std::uint64_t live=0,peak=0;};struct alignas(std::max_align_t) Block {std::size_t bytes;};
 Allocation allocation_;z_stream stream_{};bool initialized_=false,failed_=false,finished_=false,raw_hash_valid_=false;
 std::array<unsigned char,buffer_bytes> output_{};
 std::unique_ptr<EVP_MD_CTX,decltype(&EVP_MD_CTX_free)> raw_hash_{EVP_MD_CTX_new(),EVP_MD_CTX_free};
 std::uint64_t raw_=0;std::function<void(const unsigned char*,std::size_t)> emit_;
 static voidpf allocate(voidpf opaque,uInt items,uInt size){auto& a=*static_cast<Allocation*>(opaque);if(size&&items>(allocation_cap-sizeof(Block))/size)return nullptr;const auto n=std::size_t(items)*size+sizeof(Block);if(n>allocation_cap-a.live)return nullptr;auto* b=static_cast<Block*>(std::calloc(1,n));if(!b)return nullptr;b->bytes=n;a.live+=n;a.peak=std::max(a.peak,a.live);return b+1;}
 static void release(voidpf opaque,voidpf address){if(!address)return;auto& a=*static_cast<Allocation*>(opaque);auto* b=static_cast<Block*>(address)-1;a.live-=b->bytes;std::free(b);}
 void output(){const auto n=output_.size()-stream_.avail_out;if(n)emit_(output_.data(),n);}
 public:
 explicit Gzip(std::function<void(const unsigned char*,std::size_t)> emit):emit_(std::move(emit)){
  need(raw_hash_&&EVP_DigestInit_ex(raw_hash_.get(),EVP_sha256(),nullptr)==1,"raw stream SHA init");raw_hash_valid_=true;stream_.zalloc=allocate;stream_.zfree=release;stream_.opaque=&allocation_;
  need(deflateInit2(&stream_,1,Z_DEFLATED,15+16,8,Z_DEFAULT_STRATEGY)==Z_OK,"bounded pinned zlib gzip init");initialized_=true;
  if(deflateBound(&stream_,128ULL*1024*1024)>conservativeBound(128ULL*1024*1024)){deflateEnd(&stream_);initialized_=false;throw std::runtime_error("pinned deflateBound outside conservative tail domain");}
 }
 Gzip(const Gzip&)=delete;Gzip&operator=(const Gzip&)=delete;
 ~Gzip(){if(initialized_)deflateEnd(&stream_);}
 void write(const unsigned char* data,std::size_t n){need(!failed_&&!finished_&&n<=buffer_bytes,"fresh finite gzip input chunk, no retry after failure");need(raw_<=128ULL*1024*1024&&n<=128ULL*1024*1024-raw_,"raw input cap BEFORE compressor consumption");stream_.next_in=const_cast<Bytef*>(data);stream_.avail_in=n;
  try{do{const auto before=stream_.avail_in;const auto* input=stream_.next_in;stream_.next_out=output_.data();stream_.avail_out=output_.size();const int code=deflate(&stream_,Z_NO_FLUSH);if((code==Z_OK||code==Z_BUF_ERROR)&&before==0&&stream_.avail_in==0&&stream_.avail_out==output_.size())break;need(code==Z_OK,"deflate input failure");const auto consumed=before-stream_.avail_in;need(consumed||stream_.avail_out<output_.size(),"deflate must make finite progress");if(consumed){need(raw_<=128ULL*1024*1024&&consumed<=128ULL*1024*1024-raw_,"perfile logicalraw input bounded128MiB");raw_+=consumed;raw_hash_valid_=false;need(EVP_DigestUpdate(raw_hash_.get(),input,consumed)==1,"actual consumed raw SHA update, rawdigest unknown on failure");raw_hash_valid_=true;}output();}while(stream_.avail_in||stream_.avail_out==0);
  }catch(...){failed_=true;throw;}
 }
 void finish(){need(!failed_&&!finished_,"gzip close once, no failed-stream retry");stream_.next_in=nullptr;stream_.avail_in=0;
  try{for(;;){stream_.next_out=output_.data();stream_.avail_out=output_.size();const int code=deflate(&stream_,Z_FINISH);need(code==Z_OK||code==Z_STREAM_END,"deflate finish failure");output();if(code==Z_STREAM_END){finished_=true;break;}need(stream_.avail_out<output_.size(),"deflate finish must make finite progress");}}
  catch(...){failed_=true;throw;}
 }
 std::uint64_t rawBytes()const{return raw_;}bool inputHashValid()const{return raw_hash_valid_;}bool complete()const{return finished_&&!failed_;}std::uint64_t allocationPeak()const{return allocation_.peak;}
 std::string rawSha256()const{need(raw_hash_valid_,"rawinput SHA unavailable after updatefailure");std::unique_ptr<EVP_MD_CTX,decltype(&EVP_MD_CTX_free)> copy(EVP_MD_CTX_new(),EVP_MD_CTX_free);need(copy&&EVP_MD_CTX_copy_ex(copy.get(),raw_hash_.get())==1,"raw SHA clone");unsigned char bytes[32];unsigned n=0;need(EVP_DigestFinal_ex(copy.get(),bytes,&n)==1&&n==32,"raw SHA final");const char* hex="0123456789abcdef";std::string s;for(auto b:bytes){s.push_back(hex[b>>4]);s.push_back(hex[b&15]);}return s;}
};
// Z_NO_FLUSH input chunks then one Z_FINISH gzip closure; no dictionary, file
// names or current-time metadata. Exact storedprefix SHA belongs to sink; raw
// SHA covers consumedcompressor input. On stored/OS failure rawreconstruction
// UNKNOWN until independent inflate; never claim incomplete gzip is complete.
}
