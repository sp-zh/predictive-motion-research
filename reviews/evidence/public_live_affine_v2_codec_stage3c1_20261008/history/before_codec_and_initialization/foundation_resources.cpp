#include "foundation.hpp"
#include <algorithm>
#include <initializer_list>
#include <limits>
#include <stdexcept>
#include <utility>

namespace phase5_public_live_affine_v2 {
namespace {
void need(bool condition, const char* reason) {
  if (!condition) throw std::invalid_argument(reason);
}
Count sum(std::initializer_list<Count> values) {
  Count result = 0;
  for (Count value : values) result = checkedAdd(result, value);
  return result;
}
Count mul(Count a, Count b) { return checkedMultiply(a, b); }
Count ceilDiv(Count value, Count divisor) {
  need(divisor != 0, "zero integer divisor");
  return checkedAdd(value / divisor, value % divisor != 0 ? 1 : 0);
}
}
Count checkedAdd(Count a, Count b) {
  if (b > std::numeric_limits<Count>::max() - a)
    throw std::overflow_error("integer shape addition overflow");
  return a + b;
}
Count checkedMultiply(Count a, Count b) {
  if (a != 0 && b > std::numeric_limits<Count>::max() / a)
    throw std::overflow_error("integer shape multiplication overflow");
  return a * b;
}
Count exactDecimalSecondsToCycles(const std::string& text) {
  need(!text.empty() && text.size() <= 32, "bounded decimal seconds required");
  Count numerator = 0, denominator = 1, fractional_digits = 0;
  bool dot = false, digit = false;
  for (char ch : text) {
    if (ch == '.') {
      need(!dot, "multiple decimal points");
      dot = true;
    } else {
      need(ch >= '0' && ch <= '9', "seconds must be unsigned plain decimal");
      digit = true;
      numerator = checkedAdd(mul(numerator, 10), static_cast<Count>(ch - '0'));
      if (dot) { denominator = mul(denominator, 10); ++fractional_digits; }
    }
  }
  need(digit && (!dot || fractional_digits != 0), "incomplete decimal seconds");
  // 1 second is exactly 250 macro cycles; no floating point nearest rounding.
  const Count scaled = mul(numerator, 250);
  need(scaled % denominator == 0, "seconds outside exact 4ms lattice");
  const Count cycles = scaled / denominator;
  need(cycles > 0 && cycles <= ResourcePolicyV2::cycles, "duration outside v2 cycle cap");
  return cycles;
}
CycleMesh planMesh(const HorizonSpec& spec) {
  const Count n = spec.steps, total = spec.total_macro_cycles;
  need(n > 0 && n <= ResourcePolicyV2::cells, "positive bounded cell count required");
  need(total >= n && total <= ResourcePolicyV2::cycles, "positive bounded total cycles required");
  CycleMesh out;
  out.cycles_.reserve(static_cast<std::size_t>(n));
  switch (spec.policy) {
    case MeshPolicy::UniformExact:
      need(spec.explicit_cycles.empty(), "unexpected explicit mesh for uniform policy");
      need(total % n == 0, "uniform duration must divide exactly by N");
      out.cycles_.assign(static_cast<std::size_t>(n), total / n);
      break;
    case MeshPolicy::BalancedInteger:
      need(spec.explicit_cycles.empty(), "unexpected explicit mesh for balanced policy");
      for (Count k = 0; k < n; ++k)
        out.cycles_.push_back(mul(k + 1, total) / n - mul(k, total) / n);
      break;
    case MeshPolicy::ExplicitCycles:
      need(spec.explicit_cycles.size() == n, "explicit mesh roster mismatch");
      out.cycles_ = spec.explicit_cycles;
      break;
    default: throw std::invalid_argument("unknown mesh policy");
  }
  for (Count cycles : out.cycles_) {
    need(cycles > 0 && cycles <= ResourcePolicyV2::cycles, "positive bounded cell cycles required");
    out.total_ = checkedAdd(out.total_, cycles);
  }
  need(out.total_ == total && mul(out.total_, 2) <= ResourcePolicyV2::samples,
       "mesh cycle sum or sample cap mismatch");
  return out;
}

ResourcePlan planResources(const CycleMesh& mesh, const FactorShape& f,
                           CaptureMode mode, NumericEncoding encoding) {
  const Count n = mesh.cycles().size(), t = mesh.total(), s = mul(2, t);
  need(n > 0 && n <= ResourcePolicyV2::cells && t >= n && t <= ResourcePolicyV2::cycles,
       "invalid planned mesh");
  need(f.terms <= ResourcePolicyV2::terms && f.rows <= ResourcePolicyV2::rows &&
       f.largest_term_rows <= ResourcePolicyV2::term_rows &&
       f.rows <= mul(f.terms, f.largest_term_rows), "cost term/row envelope mismatch");
  need(f.largest_term_rows <= f.rows, "largest term cannot exceed total rows");
  need((f.terms != 0) || (f.rows == 0 && f.largest_term_rows == 0 &&
       f.addition_coefficients == 0 && f.addition_records == 0), "nonempty data with zero terms");
  need(f.addition_coefficients <= ResourcePolicyV2::addition_coefficients &&
       f.addition_records <= ResourcePolicyV2::addition_records,
       "addition envelope exceeded");
  // Every addition is C(n,30), n>=1 and n<=parent rows<=256.
  need(f.addition_coefficients % state_dimension == 0, "addition coefficient rows not dimension30");
  const Count addition_rows = f.addition_coefficients / state_dimension;
  need((f.addition_records == 0 && addition_rows == 0) ||
       (f.addition_records > 0 && addition_rows >= f.addition_records &&
        addition_rows <= mul(f.addition_records, f.largest_term_rows)),
       "addition record/coefficient envelope mismatch");
  const Count k = f.terms, r = f.largest_term_rows, rows = f.rows;
  const Count c = f.addition_coefficients, records = f.addition_records;
  ResourcePlan out;
  out.dx_ = mul(30, n + 1); out.du_ = mul(8, n); out.dy_ = checkedAdd(out.dx_, out.du_);
  const Count dx = out.dx_, du = out.du_, dy = out.dy_;
  need(mul(rows, dy) <= ResourcePolicyV2::matrix_entries &&
       mul(dx, dx) <= ResourcePolicyV2::matrix_entries &&
       mul(dy, du) <= ResourcePolicyV2::matrix_entries,
       "individual matrix shape exceeds v2 cap");
  const Count raw_maps = mul(sum({s, t, n}), 2441);
  const Count raw_values = sum({mul(s, 52), mul(sum({t, n, 1}), 30), mul(n, 9)});
  out.raw_ = checkedAdd(raw_maps, raw_values);
  out.sdk_allowance_ = checkedAdd(mul(3, out.raw_), 1000000);
  const Count normalized = checkedAdd(mul(n, 1241), mul(s, 1243));
  const Count boundary = mul(n + 1, sum({30, mul(30, du), 900}));
  const Count embedding = checkedAdd(mul(dy, du), dy);
  const Count inputs = sum({mul(rows, dy), rows, mul(k, dy), k, c,
                           ceilDiv(c, 30), mul(records, 4)});
  const Count factor_work = sum({mul(mul(4, r), dy), mul(mul(4, r), du),
                                mul(4, mul(du, du)), mul(2, mul(dy, du))});
  const Count sample_work = sum({mul(4, mul(30, du)), mul(4, 900), 60});
  const Count condensed = sum({mul(rows, du + 1),
    mul(k, sum({mul(du, du), du, 1})), mul(du, du), du, dy, 1});
  const Count compact = sum({out.sdk_allowance_, normalized, boundary, embedding,
                            inputs, factor_work, sample_work, condensed});
  const Count addition_scratch = checkedAdd(mul(8, c), mul(mul(2, records), 1170));
  const Count cumulative = sum({compact, mul(s, sample_work), mul(k + 1, factor_work),
                               addition_scratch});
  const Count output_slots = sum({out.raw_, normalized, mul(2, boundary), mul(2, mul(rows, dy)),
    mul(2, rows), mul(2, mul(k, dy + 1)), c, ceilDiv(c, 30), mul(records, 4), condensed,
    mul(2, mul(k + 1, sum({mul(du, du), du, 2})))});
  Count dense_extra = 0;
  switch (mode) {
    case CaptureMode::CompactComplete: break;
    case CaptureMode::DenseAuditComplete:
      dense_extra = sum({mul(dx, dx), mul(dx, du), dx, mul(dx, 30),
        mul(8, mul(dx, dx)), mul(6, mul(dx, sum({du, 30, 1}))),
        mul(dx, sum({du, 30, 1})), mul(s, mul(30, dy)),
        mul(2, mul(s, sum({30, mul(30, du), 900})))});
      break;
    default: throw std::invalid_argument("unknown capture mode");
  }
  Count bytes_per_slot = 0;
  switch (encoding) {
    case NumericEncoding::LosslessBinary: bytes_per_slot = 8; break;
    case NumericEncoding::FullNumericJson: bytes_per_slot = 34; break;
    default: throw std::invalid_argument("unknown numeric encoding");
  }
  out.live_ = checkedAdd(compact, dense_extra);
  out.charges_ = checkedAdd(cumulative, dense_extra);
  // Dense capture includes the additional audit arrays in the actual artifact.
  out.output_ = checkedAdd(mul(bytes_per_slot, checkedAdd(output_slots, dense_extra)),
                           ResourcePolicyV2::metadata_bytes);
  out.mode_ = mode;
  need(out.live_ <= ResourcePolicyV2::live_slots, "whole-request live quota exceeded");
  need(out.charges_ <= ResourcePolicyV2::case_charges, "whole-request cumulative quota exceeded");
  need(out.output_ <= ResourcePolicyV2::output_bytes, "whole-request output quota exceeded");
  return out;
}

namespace detail {
struct BatchState { Count live = 0, cumulative = 0; };
struct CaseState {
  std::shared_ptr<BatchState> batch;
  Count live = 0, cumulative = 0, metadata = 0, output = 0;
  Count live_ceiling = 0, charge_ceiling = 0, output_ceiling = 0;
};
}
namespace {
void charge(detail::CaseState& state, Count slots) {
  const Count case_next = checkedAdd(state.cumulative, slots);
  const Count batch_next = checkedAdd(state.batch->cumulative, slots);
  need(case_next <= state.charge_ceiling && case_next <= ResourcePolicyV2::case_charges,
       "case planned cumulative charge exceeded");
  need(batch_next <= ResourcePolicyV2::batch_charges, "batch cumulative charge exceeded");
  state.cumulative = case_next; state.batch->cumulative = batch_next;
}
detail::CaseState& valid(const std::shared_ptr<detail::CaseState>& state) {
  need(static_cast<bool>(state), "moved-from case budget");
  return *state;
}
}
BatchBudget::BatchBudget() : state_(std::make_shared<detail::BatchState>()) {}
Count BatchBudget::liveSlots() const {
  need(static_cast<bool>(state_), "moved-from batch budget"); return state_->live;
}
Count BatchBudget::cumulativeCharges() const {
  need(static_cast<bool>(state_), "moved-from batch budget"); return state_->cumulative;
}
CaseBudget::CaseBudget(BatchBudget& batch, const ResourcePlan& plan)
    : state_(std::make_shared<detail::CaseState>()) {
  need(static_cast<bool>(batch.state_), "moved-from batch budget");
  state_->batch = batch.state_; state_->live_ceiling = plan.liveCeiling();
  state_->charge_ceiling = plan.chargeCeiling(); state_->output_ceiling = plan.outputCeiling();
  // This reservation prices prospective SDK result growth only. It does not
  // instrument SDK allocations; stage 2 must retain its ticket for result lifetime.
}
OwnedReservation CaseBudget::reserve(Count slots) {
  auto& state = valid(state_);
  const Count next = checkedAdd(state.live, slots);
  const Count batch_next = checkedAdd(state.batch->live, slots);
  need(next <= state.live_ceiling && next <= ResourcePolicyV2::live_slots,
       "case planned live storage exceeded");
  need(batch_next <= ResourcePolicyV2::live_slots, "batch simultaneously live storage exceeded");
  charge(state, slots); state.live = next; state.batch->live = batch_next;
  return OwnedReservation(state_, slots);
}
void CaseBudget::chargeScratchOrCopy(Count slots) { charge(valid(state_), slots); }
void CaseBudget::chargeMetadataBytes(Count bytes) {
  auto& state = valid(state_); const Count next = checkedAdd(state.metadata, bytes);
  need(next <= ResourcePolicyV2::metadata_bytes, "actual metadata aggregate exceeded");
  state.metadata = next;
}
void CaseBudget::chargeUniqueOutputBytes(Count bytes) {
  auto& state = valid(state_); const Count next = checkedAdd(state.output, bytes);
  need(next <= state.output_ceiling && next <= ResourcePolicyV2::output_bytes,
       "actual unique output bytes exceeded");
  state.output = next;
}
Count CaseBudget::liveSlots() const { return valid(state_).live; }
Count CaseBudget::cumulativeCharges() const { return valid(state_).cumulative; }
Count CaseBudget::outputBytes() const { return valid(state_).output; }
Count CaseBudget::metadataBytes() const { return valid(state_).metadata; }
OwnedReservation::OwnedReservation(std::shared_ptr<detail::CaseState> state, Count slots)
    : state_(std::move(state)), slots_(slots) {}
OwnedReservation::OwnedReservation(OwnedReservation&& other) noexcept
    : state_(std::move(other.state_)), slots_(std::exchange(other.slots_, 0)) {}
OwnedReservation& OwnedReservation::operator=(OwnedReservation&& other) noexcept {
  if (this != &other) {
    release(); state_ = std::move(other.state_); slots_ = std::exchange(other.slots_, 0);
  }
  return *this;
}
OwnedReservation::~OwnedReservation() { release(); }
void OwnedReservation::release() noexcept {
  if (state_) {
    state_->live -= slots_; state_->batch->live -= slots_; state_.reset();
  }
  slots_ = 0; // Cumulative case and batch charges never decrement.
}
OwnedNumericBuffer::OwnedNumericBuffer(CaseBudget& budget, Count slots)
    : reservation_(budget.reserve(slots)) {
  need(slots <= std::numeric_limits<std::size_t>::max() / sizeof(double),
       "numeric buffer host-size overflow");
  if (slots != 0) data_.reset(new double[static_cast<std::size_t>(slots)]);
  // Allocation failure destroys the ticket/live charge but never refunds the
  // already recorded cumulative case/batch charge. Contents are uninitialized.
}
OwnedNumericBuffer::OwnedNumericBuffer(OwnedNumericBuffer&& other) noexcept
    : reservation_(std::move(other.reservation_)), data_(std::move(other.data_)) {}
OwnedNumericBuffer& OwnedNumericBuffer::operator=(OwnedNumericBuffer&& other) noexcept {
  if (this != &other) {
    data_.reset(); // Release old actual storage before releasing its ticket.
    reservation_ = std::move(other.reservation_); data_ = std::move(other.data_);
  }
  return *this;
}
} // namespace phase5_public_live_affine_v2
