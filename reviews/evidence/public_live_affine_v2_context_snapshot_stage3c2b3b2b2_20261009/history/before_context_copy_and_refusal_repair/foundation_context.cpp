#include "foundation.hpp"
#include <cmath>
#include <stdexcept>
#include <optional>
#include <string_view>

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
  need(ranges.constantsIdentity().sha256.size() == 64 &&
       !ranges.constantsIdentity().path.empty() && ranges.constantsIdentity().bytes > 0 &&
       ranges.constantsIdentity().bytes <= ResourcePolicyV2::metadata_bytes,
       "hashed static range witness required");
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
    // Feedback acceleration implied by the rounded requested w. This is only
    // conditional on exact acceptance; candidate alpha remains independently
    // recorded and is not relabeled as measured physical acceleration.
    out.implied_alpha[j] = (out.w_next[j] - actual.w[j]) / macro_dt;
    out.command_jerk_if_accepted[j] = (out.implied_alpha[j] - context.previousAlpha()[j]) / macro_dt;
    need(std::isfinite(out.implied_alpha[j]) && std::isfinite(out.command_jerk_if_accepted[j]),
         "nonfinite conditional command acceleration/jerk preview");
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
namespace detail {
struct ContextSnapshotData {
  SharedCaseBudget budget;OwnedReservation ticket;std::shared_ptr<const void> source;
  ObservedActual observed;AcceptedCommandHistory command;ProgressHistory progress;NominalAnchor nominal;CurrentBoundaryExpectation current;
  StaticDomainRanges ranges;std::optional<LiveActualContext> validated;ContextValidationHistoryV1 history;ContextInputSourceKindV1 kind=ContextInputSourceKindV1::CallerObserverAssertions;
  ContextSnapshotData(SharedCaseBudget b,std::shared_ptr<const void> s,const StaticDomainRanges& r):budget(std::move(b)),ticket(budget.reserve(200)),source(std::move(s)),ranges(r){}
};
CapturedLiveActualContextV1 ContextSnapshotFactory::captureAndValidate(SharedCaseBudget budget,std::shared_ptr<const void> source,const ObservedActual& observed,const AcceptedCommandHistory& command,const ProgressHistory& progress,const NominalAnchor& nominal,const CurrentBoundaryExpectation& current,const StaticDomainRanges& ranges){
  need(static_cast<bool>(source),"actual context source token absent");need(ranges.constantsIdentity().path.size()<=4096&&ranges.constantsIdentity().sha256.size()<=64,"snapshot ranges identity cap before copy");budget.chargeMetadataBytes(checkedAdd(ranges.constantsIdentity().path.size(),ranges.constantsIdentity().sha256.size()));budget.chargeScratchOrCopy(checkedAdd(28,(ranges.constantsIdentity().path.size()+ranges.constantsIdentity().sha256.size()+7)/8));auto data=std::make_shared<ContextSnapshotData>(budget,std::move(source),ranges);data->history.attempted=true;data->history.stage="CAPTURE_ORIGINAL_CONTEXT_INPUTS";
  try{auto guard=budget.reserve(80); // Existing validator's actual return/context temporary, not future W.
    auto bounded=[&](const std::string& s){need(s.size()<=256,"context original ID cap before copy");budget.chargeMetadataBytes(s.size());budget.chargeScratchOrCopy((s.size()+7)/8);};
    for(const auto* s:{&observed.observation_id,&observed.transaction_id,&command.observation_id,&command.transaction_id,&progress.observation_id,&progress.transaction_id,&current.observation_id,&current.transaction_id})bounded(*s);
    budget.chargeScratchOrCopy(85);data->observed=observed;data->command=command;data->progress=progress;data->nominal=nominal;data->current=current;data->history.copied_scalar_slots=85;data->history.inputs_copied=true;
    data->history.stage="VALIDATE_SAME_OWNED_ORIGINAL_INPUTS";budget.chargeScratchOrCopy(68);auto actual=validateLiveActual(data->observed,data->command,data->progress,data->nominal,data->current,data->ranges);data->history.validation_returned=true;
    // Same source strings/ranges in immutable snapshot; copy returned legacy
    // context once, with actual scalar/identity copies charged before materialization.
    budget.chargeScratchOrCopy(68);budget.chargeMetadataBytes(checkedAdd(actual.observationId().size(),checkedAdd(actual.transactionId().size(),checkedAdd(actual.ranges().constantsIdentity().path.size(),actual.ranges().constantsIdentity().sha256.size()))));
    data->validated.emplace(actual);data->history.complete=true;data->history.stage="VALIDATED_ORIGINAL_CONTEXT_SNAPSHOT";
  }catch(const std::exception& e){try{const std::string_view why=e.what();need(why.size()<=512,"context error detail cap");budget.chargeMetadataBytes(why.size());data->history.first_error.assign(why);}catch(...){}data->history.refused=true;data->history.complete=false;data->history.stage="CONTEXT_INPUT_OR_VALIDATION_REFUSED";}catch(...){data->history.refused=true;data->history.complete=false;data->history.stage="NONSTANDARD_CONTEXT_SNAPSHOT_REFUSAL";}
  return CapturedLiveActualContextV1(std::move(data)); // Private caller retains failure before refusing public witness.
}
}
CapturedLiveActualContextV1::CapturedLiveActualContextV1(std::shared_ptr<const detail::ContextSnapshotData> d):data_(std::move(d)){}
const ObservedActual& CapturedLiveActualContextV1::observedInput() const{need(data_&&data_->history.inputs_copied,"context original inputs not copied");return data_->observed;}
const AcceptedCommandHistory& CapturedLiveActualContextV1::commandInput() const{need(data_&&data_->history.inputs_copied,"context original command not copied");return data_->command;}
const ProgressHistory& CapturedLiveActualContextV1::progressInput() const{need(data_&&data_->history.inputs_copied,"context progress not copied");return data_->progress;}
const NominalAnchor& CapturedLiveActualContextV1::nominalInput() const{need(data_&&data_->history.inputs_copied,"context original nominal not copied");return data_->nominal;}
const CurrentBoundaryExpectation& CapturedLiveActualContextV1::currentInput() const{need(data_&&data_->history.inputs_copied,"context original current expectation not copied");return data_->current;}
const StaticDomainRanges& CapturedLiveActualContextV1::inputRanges() const{need(static_cast<bool>(data_),"context snapshot moved/absent");return data_->ranges;}
const ContextValidationHistoryV1& CapturedLiveActualContextV1::history() const{need(static_cast<bool>(data_),"context snapshot moved/absent");return data_->history;}
ContextInputSourceKindV1 CapturedLiveActualContextV1::sourceKind() const{need(static_cast<bool>(data_),"context source-kind absent");return data_->kind;}
const LiveActualContext& CapturedLiveActualContextV1::validatedContext() const{need(data_&&data_->history.complete&&!data_->history.refused&&data_->validated,"genuine complete validated context required");return *data_->validated;}
bool CapturedLiveActualContextV1::sameSource(const std::shared_ptr<const void>& source,const SharedCaseBudget& budget) const{return data_&&data_->source==source&&data_->budget.sameCase(budget);}
} // namespace phase5_public_live_affine_v2
