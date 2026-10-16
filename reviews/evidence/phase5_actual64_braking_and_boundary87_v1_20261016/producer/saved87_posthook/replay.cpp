#include <array>
#include <algorithm>
#include <fstream>
#include <stdexcept>
#include <cstdint>
static std::ofstream stream;
static std::uint64_t written=0;
static void capture(const std::array<unsigned char,72>& b){if(written+72>16*1024*1024)throw std::runtime_error("pure regression fullcapture16MiB cap");stream.write(reinterpret_cast<const char*>(b.data()),b.size());if(!stream)throw std::runtime_error("pure regression capture IO");written+=b.size();}
#ifdef STREAM53
#define PHASE5_ENDPOINT_REGRESSION_SINK capture
#endif
#include <cstring>
static std::ofstream boundary64;
static std::uint64_t boundary64_count=0,boundary64_bytes=0;
static void b64u(std::uint64_t x){if(boundary64_bytes+8>2ULL*1024*1024)throw std::runtime_error("boundary diagnostic2MiB prewrite");boundary64.write(reinterpret_cast<const char*>(&x),8);boundary64_bytes+=8;if(!boundary64)throw std::runtime_error("boundary diagnostic IO");}
static void b64d(double x){std::uint64_t bits;std::memcpy(&bits,&x,8);b64u(bits);}
static void boundary_record64(int it,int row,int side,double slack,double travel,double fraction,double endpoint,double lower,double upper){if(boundary64_count>=12288)throw std::runtime_error("only original successfully appended12288 diagnostic records");++boundary64_count;for(std::int64_t x:{std::int64_t(it),std::int64_t(row),std::int64_t(side)})b64u(x);for(double x:{slack,travel,fraction,endpoint,lower,upper,std::max({0.,lower-endpoint,endpoint-upper})})b64d(x);}
#define P5_BOUNDARY64_DIAGNOSTIC(...) boundary_record64(__VA_ARGS__)
#include "current_numeric_guess.hpp"
#include <iostream>
#include <iomanip>
std::uint64_t u(std::ifstream& f){std::uint64_t n;f.read(reinterpret_cast<char*>(&n),8);if(!f)throw std::runtime_error("truncated");return n;}
Eigen::MatrixXd matrix(std::ifstream& f){auto r=u(f),c=u(f);if(r>20000||c>144||r*c>3000000)throw std::runtime_error("shape");Eigen::MatrixXd m(r,c);for(auto i=0ULL;i<r;++i)for(auto j=0ULL;j<c;++j){f.read(reinterpret_cast<char*>(&m(i,j)),8);if(!f)throw std::runtime_error("truncated");}return m;}
Eigen::VectorXd vector(std::ifstream& f){auto n=u(f);if(n>20000)throw std::runtime_error("shape");Eigen::VectorXd x(n);f.read(reinterpret_cast<char*>(x.data()),8*n);if(!f)throw std::runtime_error("truncated");return x;}
int main(int argc,char**argv){try{if(argc!=5)throw std::runtime_error("fixture prefix cycle trial");std::ifstream in(argv[1],std::ios::binary);auto H=matrix(in);auto g=vector(in);auto A=matrix(in);auto lo=vector(in);auto hi=vector(in);auto seed=vector(in);char tail;if(in.get(tail))throw std::runtime_error("trailing fixture");boundary64.open(std::string(argv[2])+".boundary80.bin",std::ios::binary);auto r=phase5_dynamic_numeric_v1::derive(H,g,A,lo,hi,seed,true,true);boundary64.close();std::ofstream out(std::string(argv[2])+".finalxy.bin",std::ios::binary);for(const auto*x:{&r.primal,&r.dual}){std::uint64_t n=x->size();out.write(reinterpret_cast<const char*>(&n),8);out.write(reinterpret_cast<const char*>(x->data()),8*n);}out.close();std::ofstream events(std::string(argv[2])+".states.bin",std::ios::binary);for(const auto&e:r.events){for(int x:{e.iteration,e.active_count,e.worst_row}){std::int64_t v=x;events.write(reinterpret_cast<const char*>(&v),8);}for(double x:{e.violation,e.min_multiplier,e.stationarity,e.kkt_residual})events.write(reinterpret_cast<const char*>(&x),8);}events.close();std::cout<<std::setprecision(17)<<"complete="<<r.complete<<" error="<<std::quoted(r.error)<<" events="<<r.events.size()<<" boundary_records="<<boundary64_count<<" bytes="<<boundary64_bytes<<" rank="<<r.rank_events.size()<<" leaving="<<r.negative_leaving.size()<<" final_primal_violation="<<std::max({0.,(lo-A*r.primal).maxCoeff(),(A*r.primal-hi).maxCoeff()})<<"\n";if(boundary64_count!=12288)throw std::runtime_error("not exact12288 boundary cap");return 0;}catch(const std::exception&e){std::cerr<<e.what()<<"\n";return 2;}}
