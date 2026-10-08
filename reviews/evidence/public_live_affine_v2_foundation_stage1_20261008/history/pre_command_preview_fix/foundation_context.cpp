#include "foundation.hpp"
#include <cmath>
#include <stdexcept>

namespace phase5_public_live_affine_v2 {
namespace {
void need(bool condition, const char* reason) {
  if (!condition) throw std::invalid_argument(reason);
}
void finite(const JointVector& vector) {
  for (double value : vector) need(std::isfinite(value), "nonfinite joint vector");
}
void finiteState(const State30& state) {
  finite(state.q); finite(state.v); finite(state.C); finite(state.w);
  need(std::isfinite(state.s) && std::isfinite(state.r), "nonfinite progress state");
}
bool sameBoundary(BoundaryId a, BoundaryId b) {
  return a.completed_tick == b.completed_tick &&
         a.completed_command_sequence == b.completed_command_sequence;
}
void identity(const std::string& value, const char* message) {
  need(!value.empty() && value.size() <= 256, message);
  for (unsigned char c : value) need(c >= 33 && c <= 126, "identity must be bounded printable ASCII");
}
void progress(double s, double r) {
  need(std::isfinite(s) && std::isfinite(r), "nonfinite progress arithmetic");
  need(s >= 0 && s <= 1 && r >= 0 && r <= .2, "progress outside original closed domain");
}
bool sameState(const State30& a, const State30& b) {
  return a.q == b.q && a.v == b.v && a.C == b.C && a.w == b.w &&
         a.s == b.s && a.r == b.r; // Exact numeric equality; no tolerance/reset.
}
}
LiveActualContext validateLiveActual(const ObservedActual& observed,
    const AcceptedCommandHistory& command, const ProgressHistory& virtual_progress,
    const NominalAnchor& nominal, const CurrentBoundaryExpectation& current,
    const StaticDomainRanges& ranges) {
  identity(current.observation_id, "current immutable observation ID required");
  identity(current.transaction_id, "current completed transaction ID required");
  need(current.no_command_in_flight && observed.completed && command.completed &&
       virtual_progress.completed, "in-flight or partial boundary refused");
  need(sameBoundary(observed.boundary, current.boundary) &&
       sameBoundary(command.boundary, current.boundary) &&
       sameBoundary(virtual_progress.boundary, current.boundary) &&
       sameBoundary(nominal.boundary, current.boundary), "completed boundary mismatch");
  need(observed.observation_id == current.observation_id &&
       command.observation_id == current.observation_id &&
       virtual_progress.observation_id == current.observation_id &&
       observed.transaction_id == current.transaction_id &&
       command.transaction_id == current.transaction_id &&
       virtual_progress.transaction_id == current.transaction_id,
       "observation/history/progress transaction binding mismatch");
  need(std::isfinite(current.maximum_age_seconds) && current.maximum_age_seconds >= 0 &&
       current.maximum_age_seconds <= macro_dt, "freshness policy must be within one macro cycle");
  need(std::isfinite(observed.state_age_seconds) && observed.state_age_seconds >= 0 &&
       observed.state_age_seconds <= current.maximum_age_seconds, "stale observation refused");
  need(observed.current_contact_free, "current contact-free observer fact required");
  LiveActualContext out;
  out.actual_.q = observed.q; out.actual_.v = observed.v;
  out.actual_.C = command.C; out.actual_.w = command.w;
  out.actual_.s = virtual_progress.s; out.actual_.r = virtual_progress.r;
  finiteState(out.actual_); finiteState(nominal.point);
  finite(command.previous_alpha);
  need(std::isfinite(virtual_progress.previous_b), "nonfinite accepted progress acceleration history");
  for (std::size_t j = 0; j < 7; ++j) {
    need(observed.q[j] > ranges.qLower()[j] && observed.q[j] < ranges.qUpper()[j],
         "physical q outside strict joint-limit-free domain");
    need(command.C[j] >= ranges.cLower()[j] && command.C[j] <= ranges.cUpper()[j],
         "accepted C outside original closed domain");
    need(std::abs(command.w[j]) <= .0625, "accepted w outside original closed domain");
  }
  progress(virtual_progress.s, virtual_progress.r);
  need(sameState(out.actual_, nominal.point), "nominal anchor must equal current actual initial");
  out.previous_alpha_ = command.previous_alpha; out.previous_b_ = virtual_progress.previous_b;
  out.boundary_ = current.boundary; out.ranges_ = ranges;
  out.observation_id_ = current.observation_id; out.transaction_id_ = current.transaction_id;
  return out;
}
AlgebraTestInitial validateAlgebraTestInitial(const State30& initial) {
  finiteState(initial);
  AlgebraTestInitial out; out.point_ = initial; return out;
  // Finite only, including negative r. This type cannot convert to LiveActualContext.
}
CommandProposal first4msRequest(const LiveActualContext& context,
                               const JointVector& alpha, double b) {
  finite(alpha); need(std::isfinite(b), "finite candidate progress acceleration required");
  CommandProposal out;
  const auto& actual = context.actualInitial(); const auto& ranges = context.ranges();
  out.from = context.boundary(); out.alpha = alpha; out.b = b;
  for (std::size_t j = 0; j < 7; ++j) {
    need(std::abs(alpha[j]) <= 1, "candidate alpha outside original closed domain");
    out.w_next[j] = actual.w[j] + macro_dt * alpha[j];
    out.C_next[j] = actual.C[j] + macro_dt * out.w_next[j];
    need(std::isfinite(out.w_next[j]) && std::isfinite(out.C_next[j]), "nonfinite command preview");
    need(std::abs(out.w_next[j]) <= .0625 && out.C_next[j] >= ranges.cLower()[j] &&
         out.C_next[j] <= ranges.cUpper()[j], "command preview outside closed domain");
    out.command_jerk[j] = (alpha[j] - context.previousAlpha()[j]) / macro_dt;
    need(std::isfinite(out.command_jerk[j]), "nonfinite command jerk preview");
  }
  out.s_next = actual.s + macro_dt * actual.r + .5 * macro_dt * macro_dt * b;
  out.r_next = actual.r + macro_dt * b; progress(out.s_next, out.r_next);
  for (std::size_t half = 0; half < 2; ++half) {
    const double t = physical_dt * static_cast<double>(half + 1);
    out.half_s_reference[half] = actual.s + t * actual.r + .5 * t * t * b;
    out.half_r_reference[half] = actual.r + t * b;
    progress(out.half_s_reference[half], out.half_r_reference[half]);
  }
  out.progress_jerk = (b - context.previousB()) / macro_dt;
  need(std::isfinite(out.progress_jerk), "nonfinite progress jerk preview");
  return out; // No physical step, q/v forecast, command issue or history mutation.
}
} // namespace phase5_public_live_affine_v2
