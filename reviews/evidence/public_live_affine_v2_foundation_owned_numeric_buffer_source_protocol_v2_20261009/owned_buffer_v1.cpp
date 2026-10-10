// Source proposal only. No buffer or production function was executed during preparation.
#include "foundation.hpp"
#include "buffer_expected_v1.hpp"
#include <iostream>
#include <memory>
#include <optional>
#include <stdexcept>
#include <string>
#include <utility>
namespace p=phase5_public_live_affine_v2;
namespace e=buffer_expected;
namespace {
void require(bool ok,const char* reason){if(!ok)throw std::runtime_error(reason);}
p::ResourcePlan smallSetup(){
 const auto mesh=p::planMesh({1,1,p::MeshPolicy::BalancedInteger,{}});
 return p::planResources(mesh,{},p::CaptureMode::CompactComplete,p::NumericEncoding::LosslessBinary);
}
template<class B> void ledger(const B& b,e::Ledger expected){
 require(b.liveSlots()==expected.live&&b.cumulativeCharges()==expected.cumulative,"literal ledger snapshot mismatch");
}
void initialize(p::OwnedNumericBuffer& b){
 require(b.size()<=64,"perbuffer64doublecap");
 if(b.size())require(b.data()!=nullptr,"nonempty null data");
 for(p::Count i=0;i<b.size();++i)b.data()[i]=e::values[static_cast<std::size_t>(i)];
}
void values(const p::OwnedNumericBuffer& b,p::Count size){
 require(b.size()==size&&size<=64,"buffer size changed");
 require(size==0?b.data()==nullptr:b.data()!=nullptr,"buffer null state mismatch");
 // Called only after initialize(),and only while b stillowns its data.
 for(p::Count i=0;i<size;++i)require(b.data()[i]==e::values[static_cast<std::size_t>(i)],"initialized constdata mismatch");
}
void empty(const p::OwnedNumericBuffer& b){require(b.size()==0&&b.data()==nullptr,"moved/zero buffer not empty");}
void zero(){p::BatchBudget b;p::CaseBudget c(b,smallSetup());{p::OwnedNumericBuffer z(c,0);empty(z);const auto& cz=z;require(cz.data()==nullptr,"constzero data");ledger(c,e::zero);ledger(b,e::zero);}ledger(c,e::zero);ledger(b,e::zero);}
void readwrite(){p::BatchBudget b;p::CaseBudget c(b,smallSetup());{
 p::OwnedNumericBuffer x(c,8);initialize(x);values(x,8);double* ptr=x.data();const auto& cx=x;
 require(cx.data()==ptr,"const and mutable data differ");x.data()[3]=4.25;require(cx.data()[3]==4.25,"explicit initialized mutation not visible");x.data()[3]=e::values[3];values(cx,8);ledger(c,e::held8);ledger(b,e::held8);
 }ledger(c,e::released8);ledger(b,e::released8);}
void maximum(){p::BatchBudget b;p::CaseBudget c(b,smallSetup());{p::OwnedNumericBuffer x(c,64);initialize(x);values(x,64);ledger(c,e::held64);ledger(b,e::held64);}ledger(c,e::released64);ledger(b,e::released64);}
void moveCtor(){p::BatchBudget b;p::CaseBudget c(b,smallSetup());{
 p::OwnedNumericBuffer from(c,8);initialize(from);double* ptr=from.data();ledger(c,e::held8);ledger(b,e::held8);p::OwnedNumericBuffer to(std::move(from));
 empty(from);require(to.data()==ptr,"move constructor changed live data pointer");values(to,8);ledger(c,e::held8);ledger(b,e::held8);
 }ledger(c,e::released8);ledger(b,e::released8);}
void sameCaseAssign(){p::BatchBudget b;p::CaseBudget c(b,smallSetup());{
 p::OwnedNumericBuffer to(c,5),from(c,7);initialize(to);initialize(from);double* liveptr=from.data();ledger(c,e::both5and7);ledger(b,e::both5and7);
 to=std::move(from);empty(from);require(to.data()==liveptr,"samecase move pointer changed");values(to,7);ledger(c,e::moved7from12);ledger(b,e::moved7from12);
 }ledger(c,e::released12);ledger(b,e::released12);}
void differentCaseAssign(){p::BatchBudget b;const auto plan=smallSetup();p::CaseBudget a(b,plan),c(b,plan);auto av=a.share(),cv=c.share();{
 p::OwnedNumericBuffer to(a,5),from(c,7);initialize(to);initialize(from);double* liveptr=from.data();ledger(av,e::own5);ledger(cv,e::own7);ledger(b,e::both5and7);
 to=std::move(from);empty(from);require(to.data()==liveptr,"differentcase move pointer changed");values(to,7);ledger(av,e::released5);ledger(cv,e::own7);ledger(b,e::moved7from12);
 }ledger(av,e::released5);ledger(cv,e::released7);ledger(b,e::released12);}
void differentBatchAssign(){p::BatchBudget ba,bb;const auto plan=smallSetup();p::CaseBudget a(ba,plan),b(bb,plan);{
 p::OwnedNumericBuffer to(a,5),from(b,7);initialize(to);initialize(from);double* liveptr=from.data();ledger(ba,e::own5);ledger(bb,e::own7);ledger(a,e::own5);ledger(b,e::own7);
 to=std::move(from);empty(from);require(to.data()==liveptr,"differentbatch move pointer changed");values(to,7);ledger(a,e::released5);ledger(b,e::own7);ledger(ba,e::released5);ledger(bb,e::own7);
 }ledger(a,e::released5);ledger(b,e::released7);ledger(ba,e::released5);ledger(bb,e::released7);}
void selfMove(){p::BatchBudget b;p::CaseBudget c(b,smallSetup());{
 p::OwnedNumericBuffer x(c,64);initialize(x);double* liveptr=x.data();ledger(c,e::held64);ledger(b,e::held64);x=std::move(x);require(x.data()==liveptr,"selfmove changed data pointer");values(x,64);ledger(c,e::held64);ledger(b,e::held64);
 }ledger(c,e::released64);ledger(b,e::released64);}
void zeroIntoOccupied(){p::BatchBudget b;p::CaseBudget c(b,smallSetup());{
 p::OwnedNumericBuffer to(c,4),from(c,0);initialize(to);empty(from);ledger(c,e::held4);ledger(b,e::held4);to=std::move(from);empty(to);empty(from);ledger(c,e::released4);ledger(b,e::released4);
 }ledger(c,e::released4);ledger(b,e::released4);}
void occupiedIntoZero(){p::BatchBudget b;p::CaseBudget c(b,smallSetup());{
 p::OwnedNumericBuffer to(c,0),from(c,4);initialize(from);double* liveptr=from.data();ledger(c,e::held4);ledger(b,e::held4);to=std::move(from);empty(from);require(to.data()==liveptr,"zero destination move pointer changed");values(to,4);ledger(c,e::held4);ledger(b,e::held4);
 }ledger(c,e::released4);ledger(b,e::released4);}
void ownersGone(){std::optional<p::SharedCaseBudget> view;std::unique_ptr<p::OwnedNumericBuffer> retained;{
 p::BatchBudget b;p::CaseBudget c(b,smallSetup());view.emplace(c.share());retained=std::make_unique<p::OwnedNumericBuffer>(c,6);initialize(*retained);ledger(*view,e::held6);
 }values(*retained,6);ledger(*view,e::held6);retained.reset();ledger(*view,e::released6);/* No stale data pointer is read or compared after reset. */}
void overlap128(){p::BatchBudget b;p::CaseBudget c(b,smallSetup());{
 p::OwnedNumericBuffer first(c,64);initialize(first);ledger(c,e::held64);ledger(b,e::held64);{p::OwnedNumericBuffer second(c,64);initialize(second);values(first,64);values(second,64);ledger(c,e::both64);ledger(b,e::both64);}
 values(first,64);ledger(c,e::one64remaining);ledger(b,e::one64remaining);
 }ledger(c,e::released128);ledger(b,e::released128);}
void movedCaseRefusal(){p::BatchBudget b;p::CaseBudget from(b,smallSetup());p::CaseBudget retained(std::move(from));bool caught=false;
 try{p::OwnedNumericBuffer notCreated(from,4);}catch(const std::invalid_argument& ex){caught=true;require(std::string(ex.what())=="moved-from case budget","wrong firstconstructor refusal");}
 require(caught,"constructor accepted movedfrom case");ledger(retained,e::zero);ledger(b,e::zero);}
struct Case {const char* id;void(*run)();};
constexpr Case cases[]={
 {"buffer_zero_null",zero},{"buffer_initialized_mutable_const",readwrite},{"buffer_initialized64",maximum},
 {"buffer_move_constructor",moveCtor},{"buffer_assign_same_case",sameCaseAssign},{"buffer_assign_different_case_same_batch",differentCaseAssign},
 {"buffer_assign_different_batch",differentBatchAssign},{"buffer_self_move",selfMove},{"buffer_assign_zero_into_occupied",zeroIntoOccupied},
 {"buffer_assign_occupied_into_zero",occupiedIntoZero},{"buffer_outlives_case_batch_wrappers",ownersGone},{"buffer_two64_overlap128",overlap128},
 {"buffer_constructor_moved_case_refusal",movedCaseRefusal}};
}
int main(int argc,char**){if(argc!=1){std::cerr<<"no arguments allowed\n";return 2;}p::Count completed=0;
 for(const auto& c:cases){try{c.run();}catch(const std::exception& ex){std::cerr<<"FAIL "<<c.id<<": "<<ex.what()<<'\n';return 1;}catch(...){std::cerr<<"FAIL "<<c.id<<": nonstandard exception\n";return 1;}++completed;std::cout<<"PASS "<<c.id<<'\n';}
 if(completed!=e::case_count){std::cerr<<"fixed roster count mismatch\n";return 1;}std::cout<<"COMPLETE "<<completed<<" owned buffer groups; no phase acceptance\n";return 0;}
