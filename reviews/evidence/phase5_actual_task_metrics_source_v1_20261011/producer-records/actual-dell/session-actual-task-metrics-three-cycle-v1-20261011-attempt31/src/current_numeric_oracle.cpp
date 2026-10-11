#include "current_numeric_guess.hpp"
#include <fstream>
#include <iostream>
#include <iomanip>
#include <cstdint>
#include <cstring>
std::uint64_t count(std::ifstream& in){std::uint64_t n=0;in.read(reinterpret_cast<char*>(&n),8);if(!in)throw std::runtime_error("truncated bounded pure matrix input");return n;}
Eigen::MatrixXd matrix(std::ifstream& in){auto r=count(in),c=count(in);if(r>20000||c>144||r*c>3000000)throw std::runtime_error("pure matrix shape cap");Eigen::MatrixXd a(r,c);for(auto i=0ULL;i<r;++i)for(auto j=0ULL;j<c;++j){in.read(reinterpret_cast<char*>(&a(i,j)),8);if(!in)throw std::runtime_error("truncated pure matrix");}return a;}
Eigen::VectorXd vector(std::ifstream& in){auto n=count(in);if(n>20000)throw std::runtime_error("pure vector cap");Eigen::VectorXd a(n);in.read(reinterpret_cast<char*>(a.data()),8*n);if(!in)throw std::runtime_error("truncated pure vector");return a;}
int main(int argc,char** argv){try{if(argc!=2)throw std::runtime_error("one fresh immutable pure input path");std::ifstream in(argv[1],std::ios::binary);auto H=matrix(in);auto g=vector(in);auto A=matrix(in);auto l=vector(in);auto u=vector(in);char tail;if(in.get(tail))throw std::runtime_error("unexpected trailing input");auto result=phase5_dynamic_numeric_v1::derive(H,g,A,l,u);std::cout<<std::setprecision(17)<<"complete="<<result.complete<<" error="<<result.error<<" events="<<result.events.size()<<"\n";for(auto& e:result.events)std::cout<<"event,"<<e.iteration<<","<<e.active_count<<","<<e.worst_row<<","<<e.violation<<","<<e.min_multiplier<<","<<e.stationarity<<","<<e.kkt_residual<<"\n";if(!result.complete)return 1;std::cout<<"primal";for(double x:result.primal)std::cout<<","<<x;std::cout<<"\ndual";for(double x:result.dual)std::cout<<","<<x;std::cout<<"\n";return 0;}catch(const std::exception& e){std::cerr<<e.what()<<"\n";return 1;}}
