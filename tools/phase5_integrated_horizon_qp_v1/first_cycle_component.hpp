#pragma once
#include "integrated_horizon_qp.hpp"
namespace phase5_integrated_horizon_qp_v1 {
struct FirstCycleOutcome {
  std::optional<live::ModelOpenOutcome> original_open;
  std::optional<Outcome> integration;
  CandidateOutcome candidate;
  std::string first_error;
  double component_elapsed_seconds=0;
  bool open_entered=false,forecast_entered=false,integration_entered=false;
};
// Source-only orchestration of exactly one already prepared genuine invocation.
// Permission/observed context/readset/binary freeze belong to external dispatch.
// A failure never triggers a new invocation, shorter mesh or fallback controller.
FirstCycleOutcome runFirstCycle(live::ReviewedForecastPermission&,
  live::OwnedLiveInvocation&&,const Inputs&,const qp::QpOptions&);
}
