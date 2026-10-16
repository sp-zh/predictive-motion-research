#include <array>
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
#include <Eigen/Core>
static std::ofstream diagnostic63;
static std::uint64_t diagnostic63_bytes=0,diagnostic63_records=0;
static void diag_u63(std::uint64_t x){if(diagnostic63_bytes+8>8ULL*1024*1024)throw std::runtime_error("8MiB diagnostic prewrite bound");diagnostic63.write(reinterpret_cast<const char*>(&x),8);diagnostic63_bytes+=8;if(!diagnostic63)throw std::runtime_error("diagnostic IO");}
static void diag_d63(double x){std::uint64_t b;std::memcpy(&b,&x,8);diag_u63(b);}
template<class X,class Faces,class D,class Sol>void diag_record63(int it,int generation,const X&x,const Faces&faces,const D&direction,int negative,const Sol&sol,int n,double residual){if(diagnostic63_records>=512||x.size()!=144||faces.size()>144)throw std::runtime_error("bounded512x144 diagnostic");++diagnostic63_records;for(std::int64_t v:{std::int64_t(it),std::int64_t(generation),std::int64_t(n),std::int64_t(faces.size()),std::int64_t(negative)})diag_u63(v);diag_d63(direction.template lpNorm<Eigen::Infinity>());diag_d63(negative>=0?sol(n+negative):0.);diag_d63(residual);for(int i=0;i<n;++i)diag_d63(x(i));for(const auto&f:faces){diag_u63(f.row);diag_u63(f.side);}}
#define P5_SAVED63_DIAGNOSTIC(...) diag_record63(__VA_ARGS__)
#include "current_numeric_guess.hpp"
#include <iostream>
#include <iomanip>
std::uint64_t u(std::ifstream& f){std::uint64_t n;f.read(reinterpret_cast<char*>(&n),8);if(!f)throw std::runtime_error("truncated");return n;}
Eigen::MatrixXd matrix(std::ifstream& f){auto r=u(f),c=u(f);if(r>20000||c>144||r*c>3000000)throw std::runtime_error("shape");Eigen::MatrixXd m(r,c);for(auto i=0ULL;i<r;++i)for(auto j=0ULL;j<c;++j){f.read(reinterpret_cast<char*>(&m(i,j)),8);if(!f)throw std::runtime_error("truncated");}return m;}
Eigen::VectorXd vector(std::ifstream& f){auto n=u(f);if(n>20000)throw std::runtime_error("shape");Eigen::VectorXd x(n);f.read(reinterpret_cast<char*>(x.data()),8*n);if(!f)throw std::runtime_error("truncated");return x;}
int main(int argc,char**argv){try{if(argc!=5)throw std::runtime_error("fixture prefix cycle trial");std::ifstream in(argv[1],std::ios::binary);auto H=matrix(in);auto g=vector(in);auto A=matrix(in);auto lo=vector(in);auto hi=vector(in);auto seed=vector(in);char tail;if(in.get(tail))throw std::runtime_error("trailing fixture");diagnostic63.open(std::string(argv[2])+".snapshots.bin",std::ios::binary);auto r=phase5_dynamic_numeric_v1::derive(H,g,A,lo,hi,seed,true);diagnostic63.close();std::ofstream out(std::string(argv[2])+".finalxy.bin",std::ios::binary);for(const auto*x:{&r.primal,&r.dual}){std::uint64_t n=x->size();out.write(reinterpret_cast<const char*>(&n),8);out.write(reinterpret_cast<const char*>(x->data()),8*n);}out.close();std::ofstream events(std::string(argv[2])+".states.bin",std::ios::binary);for(const auto&e:r.events){for(int x:{e.iteration,e.active_count,e.worst_row}){std::int64_t v=x;events.write(reinterpret_cast<const char*>(&v),8);}for(double x:{e.violation,e.min_multiplier,e.stationarity,e.kkt_residual})events.write(reinterpret_cast<const char*>(&x),8);}events.close();std::cout<<std::setprecision(17)<<"complete="<<r.complete<<" error="<<std::quoted(r.error)<<" events="<<r.events.size()<<" records="<<diagnostic63_records<<" bytes="<<diagnostic63_bytes<<" rank="<<r.rank_events.size()<<" leaving="<<r.negative_leaving.size()<<" final_primal_violation="<<std::max({0.,(lo-A*r.primal).maxCoeff(),(A*r.primal-hi).maxCoeff()})<<"\n";if(diagnostic63_records!=512)throw std::runtime_error("not exact512 recorded failure");return 0;}catch(const std::exception&e){std::cerr<<e.what()<<"\n";return 2;}}
