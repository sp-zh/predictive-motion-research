// Source proposal only; no lease or production function executed during preparation.
#include "foundation.hpp"
#include "lease_expected_v1.hpp"
#include <iostream>
#include <optional>
#include <stdexcept>
#include <string>
#include <type_traits>
#include <utility>
namespace p=phase5_public_live_affine_v2;namespace e=lease_expected;
static_assert(!std::is_copy_constructible_v<p::ChunkIOLease>);
static_assert(!std::is_copy_assignable_v<p::ChunkIOLease>);
static_assert(std::is_nothrow_move_constructible_v<p::ChunkIOLease>);
static_assert(!std::is_move_assignable_v<p::ChunkIOLease>);
namespace {
void require(bool x,const char* m){if(!x)throw std::runtime_error(m);}
p::ResourcePlan setup(){return p::planResources(p::planMesh({1,1,p::MeshPolicy::BalancedInteger,{}}),{},p::CaptureMode::CompactComplete,p::NumericEncoding::LosslessBinary);}
void zero(const p::SharedCaseBudget& x){require(x.liveSlots()==e::zero&&x.cumulativeCharges()==e::zero&&x.outputBytes()==e::zero&&x.metadataBytes()==e::zero,"public case zero ledger changed");}
void zero(const p::BatchBudget& x){require(x.liveSlots()==e::zero&&x.cumulativeCharges()==e::zero,"public batch zero ledger changed");}
void reason(const p::ChunkIOLease& x,const char* expected){const char* actual=x.firstReentryReason();require(expected?actual&&std::string(actual)==expected:actual==nullptr,"reason content mismatch");}
void healthy(const p::ChunkIOLease& x){x.requireHealthy();reason(x,nullptr);}
template<class F>void refusal(F f,const char* expected){bool caught=false;try{f();}catch(const std::invalid_argument& x){caught=true;require(std::string(x.what())==expected,"wrong first refusal reason");}require(caught,"required invalid_argument missing");}
void reentry(p::SharedCaseBudget& s){refusal([&]{auto unexpected=s.beginChunkIO();(void)unexpected;},e::reentry);}
void poison(const p::ChunkIOLease& x){refusal([&]{x.requireHealthy();},e::poisoned);reason(x,e::reentry);}
void openClose(){p::BatchBudget b;p::CaseBudget c(b,setup());auto s=c.share();zero(s);zero(b);{auto x=s.beginChunkIO();healthy(x);zero(s);zero(b);}zero(s);zero(b);{auto y=s.beginChunkIO();healthy(y);zero(s);zero(b);}zero(s);zero(b);}
void sameAlias(){p::BatchBudget b;p::CaseBudget c(b,setup());auto s=c.share(),a=c.share();require(s.sameCase(a)&&a.sameCase(s)&&s.sameCase(s),"samecase identity");zero(s);zero(a);zero(b);{auto x=s.beginChunkIO();healthy(x);zero(s);zero(a);zero(b);reentry(a);poison(x);zero(s);zero(a);zero(b);}zero(s);zero(a);zero(b);{auto y=a.beginChunkIO();healthy(y);zero(s);zero(a);zero(b);}zero(s);zero(a);zero(b);}
void repeated(){p::BatchBudget b;p::CaseBudget c(b,setup());auto s=c.share();zero(s);zero(b);{auto x=s.beginChunkIO();healthy(x);zero(s);zero(b);reentry(s);poison(x);zero(s);zero(b);reentry(s);poison(x);zero(s);zero(b);}zero(s);zero(b);{auto y=s.beginChunkIO();healthy(y);zero(s);zero(b);}zero(s);zero(b);}
void resetAfterPoison(){p::BatchBudget b;p::CaseBudget c(b,setup());auto s=c.share();zero(s);zero(b);{auto x=s.beginChunkIO();healthy(x);zero(s);zero(b);reentry(s);poison(x);zero(s);zero(b);}zero(s);zero(b);{auto y=s.beginChunkIO();healthy(y);zero(s);zero(b);reentry(s);poison(y);zero(s);zero(b);}zero(s);zero(b);{auto z=s.beginChunkIO();healthy(z);zero(s);zero(b);}zero(s);zero(b);}
void differentCase(){p::BatchBudget b;const auto plan=setup();p::CaseBudget ca(b,plan),cb(b,plan);auto a=ca.share(),c=cb.share();require(!a.sameCase(c)&&!c.sameCase(a),"differentcase identity");zero(a);zero(c);zero(b);{auto x=a.beginChunkIO(),y=c.beginChunkIO();healthy(x);healthy(y);zero(a);zero(c);zero(b);reentry(a);poison(x);healthy(y);zero(a);zero(c);zero(b);}zero(a);zero(c);zero(b);{auto x=a.beginChunkIO(),y=c.beginChunkIO();healthy(x);healthy(y);zero(a);zero(c);zero(b);}zero(a);zero(c);zero(b);}
void differentBatch(){p::BatchBudget ba,bb;const auto plan=setup();p::CaseBudget ca(ba,plan),cb(bb,plan);auto a=ca.share(),c=cb.share();require(!a.sameCase(c)&&!c.sameCase(a),"differentbatch identity");zero(a);zero(c);zero(ba);zero(bb);{auto x=a.beginChunkIO(),y=c.beginChunkIO();healthy(x);healthy(y);zero(a);zero(c);zero(ba);zero(bb);reentry(a);poison(x);healthy(y);zero(a);zero(c);zero(ba);zero(bb);}zero(a);zero(c);zero(ba);zero(bb);}
void moveHealthy(){p::BatchBudget b;p::CaseBudget c(b,setup());auto s=c.share();zero(s);zero(b);{auto from=s.beginChunkIO();healthy(from);zero(s);zero(b);p::ChunkIOLease to(std::move(from));healthy(to);reason(from,nullptr);refusal([&]{from.requireHealthy();},e::moved);zero(s);zero(b);}zero(s);zero(b);{auto next=s.beginChunkIO();healthy(next);zero(s);zero(b);}zero(s);zero(b);}
void movedSourceDiesFirst(){p::BatchBudget b;p::CaseBudget c(b,setup());auto s=c.share();std::optional<p::ChunkIOLease> to;zero(s);zero(b);{auto from=s.beginChunkIO();healthy(from);zero(s);zero(b);to.emplace(std::move(from));healthy(*to);reason(from,nullptr);refusal([&]{from.requireHealthy();},e::moved);zero(s);zero(b);}healthy(*to);zero(s);zero(b);reentry(s);poison(*to);zero(s);zero(b);to.reset();zero(s);zero(b);{auto next=s.beginChunkIO();healthy(next);zero(s);zero(b);}zero(s);zero(b);}
void movePoison(){p::BatchBudget b;p::CaseBudget c(b,setup());auto s=c.share();zero(s);zero(b);{auto from=s.beginChunkIO();healthy(from);zero(s);zero(b);reentry(s);poison(from);zero(s);zero(b);p::ChunkIOLease to(std::move(from));poison(to);reason(from,nullptr);refusal([&]{from.requireHealthy();},e::moved);zero(s);zero(b);}zero(s);zero(b);{auto next=s.beginChunkIO();healthy(next);zero(s);zero(b);}zero(s);zero(b);}
void ownersGone(){std::optional<p::SharedCaseBudget> view;std::optional<p::ChunkIOLease> lease;{p::BatchBudget b;p::CaseBudget c(b,setup());view.emplace(c.share());zero(*view);zero(b);lease.emplace(view->beginChunkIO());healthy(*lease);zero(*view);zero(b);}healthy(*lease);zero(*view);reentry(*view);poison(*lease);zero(*view);lease.reset();zero(*view);{auto next=view->beginChunkIO();healthy(next);zero(*view);}zero(*view);}
}
int main(int argc,char**){try{require(argc==1,"no arguments allowed");struct Group{const char* id;void(*run)();};const Group groups[]={
{"lease_open_close_reopen",openClose},{"lease_shared_alias_reentry",sameAlias},{"lease_repeat_reentry_poison",repeated},{"lease_close_reset_poison",resetAfterPoison},{"lease_different_case_isolation",differentCase},{"lease_different_batch_isolation",differentBatch},{"lease_move_healthy_moved_source",moveHealthy},{"lease_moved_source_dies_first",movedSourceDiesFirst},{"lease_move_poisoned_state",movePoison},{"lease_outlives_case_batch_wrappers",ownersGone}};std::size_t completed=0;for(const auto& g:groups){g.run();++completed;std::cout<<"PASS "<<g.id<<'\n';}require(completed==e::case_count,"group count mismatch");std::cout<<"COMPLETE 10 chunk IO lease groups; no phase acceptance\n";return 0;}catch(const std::exception& x){std::cerr<<"FAIL "<<x.what()<<'\n';return 1;}}
