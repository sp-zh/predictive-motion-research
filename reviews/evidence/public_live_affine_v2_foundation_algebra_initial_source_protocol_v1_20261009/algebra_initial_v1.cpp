// Source-only proposal. Synthetic finite-coordinate diagnostics; not physical/Model admission.
#include "foundation.hpp"
#include "initial_expected_v1.hpp"
#include <cmath>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <type_traits>
namespace p=phase5_public_live_affine_v2;namespace e=initial_expected;
static_assert(!std::is_convertible_v<p::AlgebraTestInitial,p::LiveActualContext>);
static_assert(!std::is_constructible_v<p::LiveActualContext,p::AlgebraTestInitial>);
static_assert(!std::is_invocable_v<decltype(&p::first4msRequest),const p::AlgebraTestInitial&,const p::JointVector&,double>);
namespace {
std::size_t entries=0;
void require(bool ok,const char* message){if(!ok)throw std::runtime_error(message);}
p::JointVector& field(p::State30& s,std::size_t f){switch(f){case 0:return s.q;case 1:return s.v;case 2:return s.C;case 3:return s.w;default:throw std::runtime_error("bad joint field");}}
const p::JointVector& field(const p::State30& s,std::size_t f){switch(f){case 0:return s.q;case 1:return s.v;case 2:return s.C;case 3:return s.w;default:throw std::runtime_error("bad joint field");}}
void zero(p::State30& s){s.q.fill(0.0);s.v.fill(0.0);s.C.fill(0.0);s.w.fill(0.0);s.s=0.0;s.r=0.0;}
void tuple(p::State30& s){for(std::size_t f=0;f<4;++f)for(std::size_t j=0;j<7;++j)field(s,f)[j]=e::tuple[f*7+j];s.s=e::tuple[28];s.r=e::tuple[29];}
void checkTuple(const p::State30& s,bool shifted=false){for(std::size_t f=0;f<4;++f)for(std::size_t j=0;j<7;++j){const double expected=shifted&&f==0&&j==0?e::shifted_q0:e::tuple[f*7+j];require(field(s,f)[j]==expected,"finite joint copy mismatch");}require(s.s==(shifted?e::shifted_s:e::tuple[28])&&s.r==(shifted?e::shifted_r:e::tuple[29]),"finite progress copy mismatch");}
void checkZero(const p::State30& s,bool alternating){for(std::size_t f=0;f<4;++f)for(std::size_t j=0;j<7;++j){const double x=field(s,f)[j];require(x==0.0&&std::signbit(x)==(alternating?e::negative_zero[f*7+j]:false),"zero joint value/sign mismatch");}require(s.s==0.0&&s.r==0.0&&std::signbit(s.s)==(alternating?e::negative_zero[28]:false)&&std::signbit(s.r)==(alternating?e::negative_zero[29]:false),"zero progress value/sign mismatch");}
p::AlgebraTestInitial invoke(const p::State30& input){require(entries<e::target_entries,"target entry cap exceeded");++entries;return p::validateAlgebraTestInitial(input);}
void invalid(const p::State30& input,const char* expected){bool caught=false;try{const auto unexpected=invoke(input);(void)unexpected;}catch(const std::invalid_argument& x){caught=true;require(std::string(x.what())==expected,"wrong nonfinite category refusal");}require(caught,"required invalid_argument missing");}
double nonfinite(std::size_t kind){const double infinity=std::numeric_limits<double>::infinity();if(kind==0){const double x=std::numeric_limits<double>::quiet_NaN();require(std::isnan(x),"quiet NaN category unavailable");return x;}if(kind==1){require(std::isinf(infinity)&&!std::signbit(infinity),"positive infinity category unavailable");return infinity;}if(kind==2){require(std::isinf(-infinity)&&std::signbit(-infinity),"negative infinity category unavailable");return -infinity;}throw std::runtime_error("bad nonfinite species");}
void zeroCopy(){p::State30 input;zero(input);checkZero(input,false);const auto out=invoke(input);checkZero(out.point(),false);checkZero(input,false);}
void tupleCopy(){p::State30 input;tuple(input);checkTuple(input);const auto out=invoke(input);checkTuple(out.point());checkTuple(input);}
void mutationCopy(){p::State30 input;tuple(input);checkTuple(input);const auto out=invoke(input);checkTuple(out.point());input.q.fill(e::mutation_joint);input.v.fill(e::mutation_joint);input.C.fill(e::mutation_joint);input.w.fill(e::mutation_joint);input.s=e::mutation_s;input.r=e::mutation_r;for(std::size_t f=0;f<4;++f)for(double x:field(input,f))require(x==e::mutation_joint,"source mutation incomplete");require(input.s==e::mutation_s&&input.r==e::mutation_r,"source progress mutation incomplete");checkTuple(out.point());}
void shiftedCopy(){p::State30 input;tuple(input);input.q[0]=e::shifted_q0;input.s=e::shifted_s;input.r=e::shifted_r;checkTuple(input,true);const auto out=invoke(input);checkTuple(out.point(),true);checkTuple(input,true);}
void signedZero(){p::State30 input;zero(input);for(std::size_t f=0;f<4;++f)for(std::size_t j=0;j<7;++j)field(input,f)[j]=((f*7+j)%2)?-0.0:0.0;input.s=0.0;input.r=-0.0;checkZero(input,true);const auto out=invoke(input);checkZero(out.point(),true);checkZero(input,true);}
void jointNonfinite(std::size_t f){for(std::size_t j=0;j<7;++j)for(std::size_t kind=0;kind<3;++kind){p::State30 input;zero(input);checkZero(input,false);field(input,f)[j]=nonfinite(kind);invalid(input,e::joint_reason);}}
void qNonfinite(){jointNonfinite(0);}void vNonfinite(){jointNonfinite(1);}void cNonfinite(){jointNonfinite(2);}void wNonfinite(){jointNonfinite(3);}
void progressNonfinite(){for(std::size_t which=0;which<2;++which)for(std::size_t kind=0;kind<3;++kind){p::State30 input;zero(input);checkZero(input,false);if(which==0)input.s=nonfinite(kind);else input.r=nonfinite(kind);invalid(input,e::progress_reason);}}
void jointPriority(){ {p::State30 input;zero(input);checkZero(input,false);input.q[0]=nonfinite(0);input.s=nonfinite(1);invalid(input,e::joint_reason);} {p::State30 input;zero(input);checkZero(input,false);input.w[6]=nonfinite(2);input.r=nonfinite(0);invalid(input,e::joint_reason);} }
}
int main(int argc,char**){try{require(argc==1,"no arguments allowed");struct Group{const char* id;void(*run)();std::size_t expected_entries;};const Group groups[]={
{"initial_zero_copy",zeroCopy,1},{"initial_literal_tuple_copy",tupleCopy,1},{"initial_source_mutation_independence",mutationCopy,1},{"initial_finite_shift_negative_r",shiftedCopy,1},{"initial_signed_zero_copy",signedZero,1},{"initial_q_nonfinite",qNonfinite,21},{"initial_v_nonfinite",vNonfinite,21},{"initial_C_nonfinite",cNonfinite,21},{"initial_w_nonfinite",wNonfinite,21},{"initial_progress_nonfinite",progressNonfinite,6},{"initial_joint_over_progress_priority",jointPriority,2}};
std::size_t completed=0;for(const auto& g:groups){const auto before=entries;g.run();require(entries-before==g.expected_entries,"group target count mismatch");++completed;std::cout<<"PASS "<<g.id<<'\n';}require(completed==e::groups&&entries==e::target_entries,"fixed count closure mismatch");std::cout<<"COMPLETE 11 algebra initial groups; target entries 97; no phase acceptance\n";return 0;}catch(const std::exception& x){std::cerr<<"FAIL "<<x.what()<<'\n';return 1;}}
