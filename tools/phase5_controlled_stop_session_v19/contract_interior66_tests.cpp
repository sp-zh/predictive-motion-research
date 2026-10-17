#include "contract_interior66_v1.hpp"
#include "roundoff_command64.hpp"
#include "integrated_horizon_qp.hpp"
#include <iostream>
#include <fstream>
#include <cstring>
namespace ip=phase5_contract_interior66_v1;namespace old=phase5_roundoff_command64_v1;
void require(bool b,const char*s){if(!b)throw std::runtime_error(s);}
template<class F>void refuses(F f){bool caught=false;try{f();}catch(const std::invalid_argument&){caught=true;}require(caught,"invalid/narrow interior must refuse, never fallback");}
std::uint64_t count(std::ifstream&f){std::uint64_t n;f.read(reinterpret_cast<char*>(&n),8);ip::need(bool(f),"bounded immutable fixture count");return n;}
Eigen::MatrixXd matrix(std::ifstream&f){auto r=count(f),c=count(f);ip::need(r<=20000&&c<=144&&r*c<=3000000,"fixture matrix finite shape");Eigen::MatrixXd a(r,c);for(auto i=0ULL;i<r;++i)for(auto j=0ULL;j<c;++j){f.read(reinterpret_cast<char*>(&a(i,j)),8);ip::need(bool(f),"fixture full matrix");}ip::need(a.allFinite(),"finite fixture matrix");return a;}
Eigen::VectorXd vector(std::ifstream&f){auto n=count(f);ip::need(n<=20000,"fixture vector shape");Eigen::VectorXd a(n);f.read(reinterpret_cast<char*>(a.data()),8*n);ip::need(bool(f)&&a.allFinite(),"finite full fixture vector");return a;}
int main(int argc,char**argv){try{
 require(argc==2,"one immutable saved fixture");
 phase5_active_session_qp_v1::Inputs defaults;require(!defaults.first_command_interior66,"new policy defaultfalse");
 const double w=-.0009720758727266975,nom=.0023084839272165167,guard=.0010803541;
 const auto b=old::firstBounds(w,nom,nom-guard,nom+guard);
 require(!old::strictFirst(w,.002308483927128721,b),"preserve actual65 native strict refusal");
 const auto p=ip::prepare(b.lower,b.upper,nom,1./5.744562646538029,5.744562646538029,1e-9);
 require(old::strictFirst(w,p.seed_alpha,b)&&p.lower>b.lower&&p.upper<b.upper,"strict gate unchanged with inward affine optimizer start");
 unsigned cases=0;
 for(double width:{1e-7,1e-5,.001,.25,2.})for(double fraction:{0.,.125,.5,.875,1.})for(double mult:{.001,.2,1.}){
  const double lo=-.5*width,hi=.5*width,c=lo+fraction*width;const auto a=ip::prepare(lo,hi,c,mult,2.,1e-9);
  require(a.lower>lo&&a.upper<hi&&a.lower<a.seed_alpha&&a.seed_alpha<a.upper,"finite representable subset contains analytic optimizer seed");
  require(a.scaled_inset>4e-12&&a.blend>0&&a.blend<=.5,"original hint domain margin or refusal");++cases;
 }
 refuses([&]{ip::prepare(-1e-13,1e-13,0.,1.,1.,1e-9);});
 refuses([&]{ip::prepare(1.,1.,1.,1.,1.,1e-9);});
 refuses([&]{ip::prepare(-1.,1.,2.,1.,1.,1e-9);});
 refuses([&]{ip::prepare(-1.,1.,0.,0.,1.,1e-9);});
 refuses([&]{ip::prepare(-1.,1.,0.,1.,0.,1e-9);});
 refuses([&]{ip::prepare(-1.,1.,0.,1.,1.,1e-8);});
 refuses([&]{ip::prepare(-1.,1.,std::numeric_limits<double>::quiet_NaN(),1.,1.,1e-9);});
 refuses([&]{ip::prepare(-1e308,1e308,0.,1.,1.,1e-9);});

 std::ifstream in(argv[1],std::ios::binary);auto H=matrix(in);auto g=vector(in);auto A=matrix(in);auto lo=vector(in);auto hi=vector(in);auto F=matrix(in);auto D=vector(in);auto nominal=vector(in);auto oldx=vector(in);auto oldy=vector(in);auto W=vector(in);auto centers=vector(in);auto L=vector(in);auto U=vector(in);char tail;
 require(!in.get(tail)&&H.rows()==144&&A.rows()==7337&&A.cols()==144&&D.size()==144,"one exact actual65 saved matrix fixture");
 Eigen::VectorXd seed=nominal.cwiseQuotient(D);const int base=A.rows()-424;
 for(int j=0;j<7;++j){const double mult=1/std::max(1.,D(j));auto a=ip::prepare(L(j),U(j),centers(j),mult,D(j),1e-9);lo(base+j)=mult*a.lower;hi(base+j)=mult*a.upper;seed(j)=a.seed_y;}
 const auto initialized=phase5_bounded_global_interval_seed_v6::prepare(A,lo,hi,seed,D);
 require(initialized.complete&&initialized.error.empty()&&initialized.retry_available&&initialized.retry.seed.size()==144,"actual unchanged V6 initializer succeeds on new seven coordinates");
 for(int j=0;j<144;++j)if(j%8!=7)require(std::memcmp(&initialized.retry.seed(j),&seed(j),8)==0,"all126 nonbeta coordinates bitexact preserved includingfirst7");
 const Eigen::VectorXd vals=A*initialized.retry.seed;double worst=std::max({0.,(lo-vals).maxCoeff(),(vals-hi).maxCoeff()});require(worst<=1e-12&&initialized.retry.row_bounds_written==7337,"V6 checks whole current matrix");
 const auto hint=phase5_dynamic_numeric_v1::derive(H,g,A,lo,hi,initialized.retry.seed,true,true);require(hint.complete&&hint.error.empty(),"unchanged hint after actual initializer");
 for(int j=0;j<7;++j){auto b=old::firstBounds(W(j),centers(j),L(j),U(j));require(old::strictFirst(W(j),D(j)*hint.primal(j),b),"integrated V6 then hint still satisfies original strict7");}
 std::cout<<"V6 initializer all7337 rows checked; all126 nonbeta bits preserved; original hint events="<<hint.events.size()<<" strict7=PASS nativecalls=0\n";
 std::cout<<"PASS defaultfalse, actual65 strict refusal retained, inward seed strictpass, "<<cases<<" signed/interior/boundary/scaling cases, narrow/NaN/overflow/changed-tolerance refuse. No nativeQP/Model/controller66/B/C/physical-stop entry.\n";return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<"\n";return 1;}}
