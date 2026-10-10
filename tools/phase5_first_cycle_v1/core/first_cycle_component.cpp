#include "first_cycle_component.hpp"
#include <exception>
#include <chrono>
#include <stdexcept>
#include <utility>
namespace phase5_integrated_horizon_qp_v1 {
FirstCycleOutcome runFirstCycle(live::ReviewedForecastPermission& permission,
 live::OwnedLiveInvocation&& invocation,const Inputs& inputs,const qp::QpOptions& options){
 FirstCycleOutcome out;
 const auto component_started=std::chrono::steady_clock::now();
 auto recordElapsed=[&](){out.component_elapsed_seconds=std::chrono::duration<double>(std::chrono::steady_clock::now()-component_started).count();};
 try{
  if(inputs.geometry.size()>1600)throw std::invalid_argument("geometry cap before first-cycle calls");
  out.open_entered=true;out.original_open.emplace(live::openPinnedModel(permission,invocation));
  if(!out.original_open->hasModel()){out.first_error=out.original_open->refusal();recordElapsed();return out;}
  out.forecast_entered=true;
  auto forecast=live::forecastPublic(out.original_open->model(),std::move(invocation));
  Inputs bridge_inputs=inputs;
  bridge_inputs.known_upstream_elapsed_seconds+=std::chrono::duration<double>(std::chrono::steady_clock::now()-component_started).count();
  out.integration_entered=true;out.integration.emplace(connect(std::move(forecast),bridge_inputs));
  // Includes open/metadata/forecast and input-copy timing before connection.
  // Caller must separately supply actual observation->preparation elapsed.
  if(!out.integration->complete()){out.first_error=out.integration->trace().first_error;recordElapsed();return out;}
  solveOnce(*out.integration,options,out.candidate);
  out.first_error=out.candidate.stopReason(); // Even solved output still needs independent forward.
 }catch(const std::exception& e){out.first_error=e.what();}
 catch(...){out.first_error="NONSTANDARD_FIRST_CYCLE_FAILURE";}
 recordElapsed();return out;
}
}
