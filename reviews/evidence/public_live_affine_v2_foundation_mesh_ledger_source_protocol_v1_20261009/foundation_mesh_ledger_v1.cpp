// SOURCE PROPOSAL ONLY: never compiled, linked or run in this work unit.
#include "foundation.hpp"
#include "expected_v1.hpp"
#include <functional>
#include <iostream>
#include <limits>
#include <optional>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace p = phase5_public_live_affine_v2;
using p::Count;
namespace {
struct Failure : std::runtime_error { using std::runtime_error::runtime_error; };
void require(bool condition, const char* reason) {
  if (!condition) throw Failure(reason); // Deliberately independent of assert/NDEBUG.
}
template<class E, class F> void refuses(F&& f) {
  bool caught = false;
  try { f(); } catch (const E&) { caught = true; }
  require(caught, "expected exception not raised");
}
p::HorizonSpec spec(Count n, Count t, p::MeshPolicy policy,
                    std::vector<Count> cells = {}) {
  return {n, t, policy, std::move(cells)};
}
p::ResourcePlan smallPlan() {
  auto mesh = p::planMesh(spec(1, 1, p::MeshPolicy::UniformExact));
  auto plan = p::planResources(mesh, {}, p::CaptureMode::CompactComplete,
                              p::NumericEncoding::LosslessBinary);
  require(plan.liveCeiling() == expected::small_live &&
          plan.chargeCeiling() == expected::small_charge &&
          plan.outputCeiling() == expected::small_output, "small fixture setup mismatch");
  return plan;
}
p::ResourcePlan batchPlan() {
  auto mesh = p::planMesh(spec(20, 375, p::MeshPolicy::BalancedInteger));
  auto plan = p::planResources(mesh, {}, p::CaptureMode::CompactComplete,
                              p::NumericEncoding::LosslessBinary);
  require(plan.liveCeiling() == expected::batch_case_live &&
          plan.chargeCeiling() == expected::batch_case_charge &&
          plan.outputCeiling() == expected::batch_case_output, "batch fixture setup mismatch");
  return plan;
}
Count completed = 0;
void run(const char* id, const std::function<void()>& body) {
  try { body(); }
  catch (const std::exception& e) {
    std::cerr << "FAIL " << id << ": " << e.what() << '\n';
    throw;
  }
  ++completed;
  std::cout << "PASS " << id << '\n';
}
void integerCases() {
  for (const auto& x : expected::integer_success) run(x.id, [&] {
    require((x.multiply ? p::checkedMultiply(x.a, x.b) : p::checkedAdd(x.a, x.b))
            == x.result, "integer literal mismatch");
  });
  for (const auto& x : expected::integer_overflow) run(x.id, [&] {
    refuses<std::overflow_error>([&] {
      if (x.multiply) (void)p::checkedMultiply(x.a, x.b);
      else (void)p::checkedAdd(x.a, x.b);
    });
  });
}
void decimalCases() {
  for (const auto& x : expected::decimal_success) run(x.id, [&] {
    require(p::exactDecimalSecondsToCycles(x.text) == x.cycles, "decimal literal mismatch");
  });
  for (const auto& x : expected::decimal_invalid) run(x.id, [&] {
    refuses<std::invalid_argument>([&] { (void)p::exactDecimalSecondsToCycles(x.text); });
  });
  for (const auto& x : expected::decimal_overflow) run(x.id, [&] {
    refuses<std::overflow_error>([&] { (void)p::exactDecimalSecondsToCycles(x.text); });
  });
}
void meshCases() {
  using M = p::MeshPolicy;
  run("mesh_uniform_20_200", [] {
    const auto m = p::planMesh(spec(20, 200, M::UniformExact));
    require(m.total() == 200 && m.cycles() == std::vector<Count>(20, 10), "uniform order");
  });
  run("mesh_balanced_20_375", [] {
    const auto m = p::planMesh(spec(20, 375, M::BalancedInteger));
    require(m.total() == 375 && m.cycles() == expected::balanced_20_375, "balanced order");
  });
  run("mesh_explicit_4_10", [] {
    const auto m = p::planMesh(spec(4, 10, M::ExplicitCycles, {1,4,2,3}));
    require(m.total() == 10 && m.cycles() == std::vector<Count>({1,4,2,3}), "explicit order");
  });
  run("mesh_explicit_1_375", [] {
    const auto m = p::planMesh(spec(1, 375, M::ExplicitCycles, {375}));
    require(m.total() == 375 && m.cycles() == std::vector<Count>({375}), "explicit single");
  });
  const std::vector<std::pair<const char*, p::HorizonSpec>> bad = {
    {"mesh_zero_n", spec(0,200,M::UniformExact)},
    {"mesh_n_over_cap", spec(33,200,M::BalancedInteger)},
    {"mesh_zero_total", spec(1,0,M::UniformExact)},
    {"mesh_total_below_n", spec(20,19,M::BalancedInteger)},
    {"mesh_total_over_cap", spec(20,376,M::BalancedInteger)},
    {"mesh_uniform_remainder", spec(20,375,M::UniformExact)},
    {"mesh_uniform_extra", spec(1,1,M::UniformExact,{1})},
    {"mesh_balanced_extra", spec(1,1,M::BalancedInteger,{1})},
    {"mesh_explicit_empty", spec(1,1,M::ExplicitCycles)},
    {"mesh_explicit_wrong_size", spec(4,10,M::ExplicitCycles,{1,4,5})},
    {"mesh_explicit_zero", spec(4,10,M::ExplicitCycles,{0,4,2,4})},
    {"mesh_explicit_wrong_sum", spec(4,10,M::ExplicitCycles,{1,4,2,4})},
    {"mesh_explicit_cell_over_cap", spec(1,375,M::ExplicitCycles,{376})},
    {"mesh_bad_enum", spec(1,1,static_cast<M>(99))}
  };
  for (const auto& x : bad) run(x.first, [&] {
    refuses<std::invalid_argument>([&] { (void)p::planMesh(x.second); });
  });
}
void ledgerCases() {
  run("ledger_ticket_move_and_release", [] {
    p::BatchBudget b; p::CaseBudget c(b, smallPlan());
    { auto a = c.reserve(3); auto dest = c.reserve(5);
      auto moved = std::move(a);
      require(a.slots()==0 && moved.slots()==3 && b.liveSlots()==8, "move constructor");
      dest = std::move(moved);
      require(moved.slots()==0 && dest.slots()==3 && c.liveSlots()==3 &&
              b.liveSlots()==3 && c.cumulativeCharges()==8 && b.cumulativeCharges()==8,
              "move assignment releases destination without cumulative refund");
    }
    require(c.liveSlots()==0 && b.liveSlots()==0 && c.cumulativeCharges()==8 &&
            b.cumulativeCharges()==8, "destruction never refunds cumulative");
  });
  run("ledger_owner_lifetime", [] {
    std::optional<p::SharedCaseBudget> view;
    std::optional<p::OwnedReservation> ticket;
    { p::BatchBudget b; p::CaseBudget c(b,smallPlan());
      view.emplace(c.share()); ticket.emplace(c.reserve(7)); }
    require(view->liveSlots()==7 && view->cumulativeCharges()==7, "survives both owners");
    ticket.reset();
    require(view->liveSlots()==0 && view->cumulativeCharges()==7, "surviving ledger release");
  });
  run("ledger_share_and_distinct_case", [] {
    p::BatchBudget b; p::BatchBudget other; const auto plan=smallPlan();
    p::CaseBudget c(b,plan), d(b,plan); auto s=c.share(), s2=c.share(), ds=d.share();
    require(s.sameCase(s2) && !s.sameCase(ds) && c.sameBatch(b) && !c.sameBatch(other),
            "ledger identities");
    { auto a=s.reserve(2); auto z=ds.reserve(3); s2.chargeScratchOrCopy(4);
      require(c.liveSlots()==2 && d.liveSlots()==3 && b.liveSlots()==5 &&
              c.cumulativeCharges()==6 && d.cumulativeCharges()==3 && b.cumulativeCharges()==9,
              "case separation with shared batch"); }
    require(b.liveSlots()==0 && b.cumulativeCharges()==9, "shared release");
  });
  run("ledger_case_live_boundary", [] {
    p::BatchBudget b; p::CaseBudget c(b,smallPlan());
    { auto ticket=c.reserve(expected::small_live);
      refuses<std::invalid_argument>([&] { (void)c.reserve(1); });
      require(c.liveSlots()==expected::small_live && c.cumulativeCharges()==expected::small_live &&
              b.liveSlots()==expected::small_live && b.cumulativeCharges()==expected::small_live,
              "failed live reservation does not mutate"); }
    require(c.liveSlots()==0 && c.cumulativeCharges()==expected::small_live, "release at cap");
  });
  run("ledger_case_cumulative_boundary", [] {
    p::BatchBudget b; p::CaseBudget c(b,smallPlan()); c.chargeScratchOrCopy(expected::small_charge);
    refuses<std::invalid_argument>([&] { c.chargeScratchOrCopy(1); });
    refuses<std::invalid_argument>([&] { (void)c.reserve(1); });
    require(c.liveSlots()==0 && b.liveSlots()==0 && c.cumulativeCharges()==expected::small_charge &&
            b.cumulativeCharges()==expected::small_charge, "failed cumulative reservation atomic");
  });
  run("ledger_batch_live_boundary", [] {
    p::BatchBudget b; const auto plan=batchPlan();
    std::vector<p::CaseBudget> cases; cases.reserve(6);
    std::vector<p::OwnedReservation> tickets; tickets.reserve(6);
    for (int i=0;i<6;++i) cases.emplace_back(b,plan);
    for (int i=0;i<5;++i) tickets.push_back(cases[i].reserve(expected::batch_case_live));
    tickets.push_back(cases[5].reserve(expected::batch_live_remainder));
    require(b.liveSlots()==expected::batch_live_cap && b.cumulativeCharges()==expected::batch_live_cap,
            "shared live exact boundary");
    refuses<std::invalid_argument>([&] { (void)cases[5].reserve(1); });
    require(cases[5].liveSlots()==expected::batch_live_remainder &&
            cases[5].cumulativeCharges()==expected::batch_live_remainder &&
            b.liveSlots()==expected::batch_live_cap && b.cumulativeCharges()==expected::batch_live_cap,
            "batch live refusal atomic");
    tickets.clear();
    require(b.liveSlots()==0 && b.cumulativeCharges()==expected::batch_live_cap, "batch release");
  });
  run("ledger_batch_cumulative_boundary", [] {
    p::BatchBudget b; const auto plan=batchPlan();
    for (int i=0;i<35;++i) { p::CaseBudget c(b,plan); c.chargeScratchOrCopy(expected::batch_case_charge); }
    require(b.liveSlots()==0 && b.cumulativeCharges()==expected::batch_charge_prefix,
            "destroyed cases retain batch charges");
    p::CaseBudget last(b,plan); last.chargeScratchOrCopy(expected::batch_charge_remainder);
    refuses<std::invalid_argument>([&] { last.chargeScratchOrCopy(1); });
    refuses<std::invalid_argument>([&] { (void)last.reserve(1); });
    require(last.liveSlots()==0 && last.cumulativeCharges()==expected::batch_charge_remainder &&
            b.liveSlots()==0 && b.cumulativeCharges()==expected::batch_charge_cap, "batch charge refusal atomic");
  });
  run("ledger_metadata_output_boundary", [] {
    p::BatchBudget b; p::CaseBudget c(b,smallPlan()); auto s=c.share();
    s.chargeMetadataBytes(expected::metadata_cap); c.chargeUniqueOutputBytes(expected::small_output);
    refuses<std::invalid_argument>([&] { c.chargeMetadataBytes(1); });
    refuses<std::invalid_argument>([&] { s.chargeUniqueOutputBytes(1); });
    require(c.metadataBytes()==expected::metadata_cap && s.metadataBytes()==expected::metadata_cap &&
            c.outputBytes()==expected::small_output && s.outputBytes()==expected::small_output &&
            b.liveSlots()==0 && b.cumulativeCharges()==0, "metadata/output aggregate and unchanged slot charges");
  });
  run("ledger_checked_overflow_atomic", [] {
    p::BatchBudget b; p::CaseBudget c(b,smallPlan());
    auto ticket=c.reserve(1); c.chargeMetadataBytes(1); c.chargeUniqueOutputBytes(1);
    refuses<std::overflow_error>([&] { (void)c.reserve(expected::max_count); });
    refuses<std::overflow_error>([&] { c.chargeScratchOrCopy(expected::max_count); });
    refuses<std::overflow_error>([&] { c.chargeMetadataBytes(expected::max_count); });
    refuses<std::overflow_error>([&] { c.chargeUniqueOutputBytes(expected::max_count); });
    require(c.liveSlots()==1 && c.cumulativeCharges()==1 && c.metadataBytes()==1 && c.outputBytes()==1 &&
            b.liveSlots()==1 && b.cumulativeCharges()==1, "overflow no partial mutation");
  });
  run("ledger_moved_from_batch", [] {
    const auto plan=smallPlan(); p::BatchBudget b; p::CaseBudget c(b,plan);
    p::BatchBudget moved=std::move(b);
    refuses<std::invalid_argument>([&] { (void)b.liveSlots(); });
    refuses<std::invalid_argument>([&] { (void)b.cumulativeCharges(); });
    refuses<std::invalid_argument>([&] { p::CaseBudget bad(b,plan); });
    require(c.sameBatch(moved) && !c.sameBatch(b), "batch moved identity");
    auto ticket=c.reserve(2); require(moved.liveSlots()==2 && moved.cumulativeCharges()==2, "moved batch retains ledger");
  });
  run("ledger_moved_from_case", [] {
    p::BatchBudget b; p::CaseBudget c(b,smallPlan()); auto shared=c.share(); p::CaseBudget moved=std::move(c);
    refuses<std::invalid_argument>([&] { (void)c.reserve(0); });
    refuses<std::invalid_argument>([&] { c.chargeScratchOrCopy(0); });
    refuses<std::invalid_argument>([&] { c.chargeMetadataBytes(0); });
    refuses<std::invalid_argument>([&] { c.chargeUniqueOutputBytes(0); });
    refuses<std::invalid_argument>([&] { (void)c.liveSlots(); });
    refuses<std::invalid_argument>([&] { (void)c.cumulativeCharges(); });
    refuses<std::invalid_argument>([&] { (void)c.metadataBytes(); });
    refuses<std::invalid_argument>([&] { (void)c.outputBytes(); });
    refuses<std::invalid_argument>([&] { (void)c.share(); });
    require(!c.sameBatch(b) && moved.share().sameCase(shared), "case moved identity");
  });
  run("ledger_moved_from_shared", [] {
    p::BatchBudget b; p::CaseBudget c(b,smallPlan()); auto s=c.share(); auto moved=std::move(s);
    refuses<std::invalid_argument>([&] { (void)s.reserve(0); });
    refuses<std::invalid_argument>([&] { s.chargeScratchOrCopy(0); });
    refuses<std::invalid_argument>([&] { s.chargeMetadataBytes(0); });
    refuses<std::invalid_argument>([&] { s.chargeUniqueOutputBytes(0); });
    refuses<std::invalid_argument>([&] { (void)s.liveSlots(); });
    refuses<std::invalid_argument>([&] { (void)s.liveCeiling(); });
    refuses<std::invalid_argument>([&] { (void)s.cumulativeCharges(); });
    refuses<std::invalid_argument>([&] { (void)s.chargeCeiling(); });
    refuses<std::invalid_argument>([&] { (void)s.metadataBytes(); });
    refuses<std::invalid_argument>([&] { (void)s.outputBytes(); });
    refuses<std::invalid_argument>([&] { (void)s.outputCeiling(); });
    refuses<std::invalid_argument>([&] { (void)s.numericEncoding(); });
    refuses<std::invalid_argument>([&] { (void)s.beginChunkIO(); });
    require(!s.sameCase(moved) && moved.sameCase(c.share()), "shared moved identity");
  });
  run("ledger_chunk_reentry_poison", [] {
    p::BatchBudget b; p::CaseBudget c(b,smallPlan()), other(b,smallPlan()); auto s=c.share(), duplicate=c.share();
    { auto lease=s.beginChunkIO(); lease.requireHealthy();
      require(lease.firstReentryReason()==nullptr, "initial healthy lease");
      { auto independent=other.share().beginChunkIO(); independent.requireHealthy(); }
      refuses<std::invalid_argument>([&] { (void)duplicate.beginChunkIO(); });
      require(lease.firstReentryReason()!=nullptr &&
              std::string(lease.firstReentryReason())=="CHUNK_IO_REENTRY", "reentry first reason");
      refuses<std::invalid_argument>([&] { lease.requireHealthy(); });
      auto moved=std::move(lease);
      refuses<std::invalid_argument>([&] { lease.requireHealthy(); });
      require(lease.firstReentryReason()==nullptr, "moved lease empty");
      refuses<std::invalid_argument>([&] { moved.requireHealthy(); }); }
    { auto fresh=s.beginChunkIO(); fresh.requireHealthy(); require(fresh.firstReentryReason()==nullptr, "new operation resets poison"); }
    require(b.liveSlots()==0 && b.cumulativeCharges()==0, "pure lease no slot charges");
  });
}
} // namespace
int main(int argc, char**) {
  if (argc != 1) { std::cerr << "no arguments allowed\n"; return 2; }
  try {
    integerCases(); decimalCases(); meshCases(); ledgerCases();
    require(completed == expected::case_count, "fixed roster count mismatch");
    std::cout << "COMPLETE " << completed << " foundation seam cases; no phase acceptance\n";
    return 0;
  } catch (const std::exception&) { return 1; }
    catch (...) { std::cerr << "unexpected nonstandard exception\n"; return 1; }
}
