// Source-only proposal: not compiled,linked or run in this work unit.
#include "foundation.hpp"
#include "pricing_expected_v1.hpp"
#include <array>
#include <iostream>
#include <stdexcept>
#include <string>
namespace p=phase5_public_live_affine_v2;
namespace {
void require(bool condition,const char* reason) {
  if(!condition) throw std::runtime_error(reason); // Active under NDEBUG.
}
void check(const pricing_expected::Case& c) {
  // BalancedInteger is only a legal <=32cell setup fixture,not another mesh test.
  const p::HorizonSpec horizon{c.n,c.t,p::MeshPolicy::BalancedInteger,{}};
  const auto mesh=p::planMesh(horizon);
  const p::FactorShape factor{c.k,c.rows,c.r,c.coeff,c.records};
  const auto mode=static_cast<p::CaptureMode>(c.mode);
  const auto encoding=static_cast<p::NumericEncoding>(c.encoding);
  if(!c.accept) {
    bool refused=false;
    try { (void)p::planResources(mesh,factor,mode,encoding); }
    catch(const std::invalid_argument& e) {
      refused=true;
      require(std::string(e.what())==c.refusal,"wrong frozen first refusal reason");
    }
    require(refused,"planned refusal returned a ResourcePlan or silently fell back");
    return;
  }
  const auto result=p::planResources(mesh,factor,mode,encoding);
  const std::array<p::Count,11> actual{
    result.dx(),result.du(),result.dy(),result.rawResultShapeSlots(),
    result.sdkPlanningAllowance(),result.liveCeiling(),result.chargeCeiling(),
    result.outputCeiling(),result.metadataCeiling(),
    result.memberCaptureSlots(),result.memberCaptureCharges()};
  for(std::size_t i=0;i<actual.size();++i)
    require(actual[i]==c.getter[i],"public getter disagrees with independent frozen dimensional ledger");
  require(result.captureMode()==mode,"capture mode changed or fell back");
  require(result.numericEncoding()==encoding,"encoding changed or fell back");
}
} // namespace
int main(int argc,char**) {
  if(argc!=1) { std::cerr<<"no arguments allowed\n";return 2; }
  p::Count completed=0;
  for(const auto& c:pricing_expected::cases) {
    try { check(c); }
    catch(const std::exception& e) { std::cerr<<"FAIL "<<c.id<<": "<<e.what()<<'\n';return 1; }
    catch(...) { std::cerr<<"FAIL "<<c.id<<": nonstandard exception\n";return 1; }
    ++completed;std::cout<<"PASS "<<c.id<<'\n';
  }
  if(completed!=pricing_expected::case_count) { std::cerr<<"fixed roster count mismatch\n";return 1; }
  std::cout<<"COMPLETE "<<completed<<" resource pricing groups; no phase acceptance\n";
  return 0;
}
