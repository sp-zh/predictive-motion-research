#pragma once
#include "nominal_geometry_selection.hpp"
#include "model_boundary.hpp"
namespace phase5_nominal_geometry_provider_v1 {
namespace live=phase5_active_session_v1;
struct SampleSupport {int sample=-1,cell=-1,cycle=-1,half=-1;double elapsed=0;Eigen::VectorXd nominal_q;double minimum_true=0,minimum_cover=0;std::size_t complete_query_count=0;std::vector<phase5_nominal_geometry_selection_v1::Selected> selected;};
struct Result {bool attempted=false,complete=false;std::string error,nominal_invocation_sha256,geometry_configuration_sha256;std::vector<phase5_active_session_qp_v1::GeometryRow> rows;std::vector<SampleSupport> samples;};
// Data-only genuine nominal gradient assembly; no future native plant truth,
// candidate factory or execution permit. Caller retains frozen Scene/pins.
template<class SceneType> inline void build(const live::OwnedPublicForecast& nominal,predictive_motion::RobotKinematics& robot,const SceneType& scene,const std::string& geometry_sha,Result& out,const std::function<void(live::Count)>& reserve_numeric){
 auto need=[](bool b,const char* s){if(!b)throw std::invalid_argument(s);};need(!out.attempted,"one nominal geometry assembly record");out.attempted=true;try{
 need(geometry_sha.size()==64&&nominal.sessionActive()&&nominal.bindingVerified()&&nominal.transportFailure().empty()&&nominal.structuralRefusal().empty(),"genuine bound nominal/frozen geometry identity");for(char c:geometry_sha)need((c>='0'&&c<='9')||(c>='a'&&c<='f'),"canonical geometry SHA256");const auto* raw=nominal.originalResult();need(raw&&raw->value.success&&raw->extension_jacobian_success&&raw->error.empty()&&raw->value.error.empty()&&raw->substep_maps.size()==400&&raw->value.substeps.size()==400,"complete current nominal 400sample maps");out.nominal_invocation_sha256=nominal.invocationSha256();out.geometry_configuration_sha256=geometry_sha;need(static_cast<bool>(reserve_numeric),"cumulative geometry numeric reservation mandatory");reserve_numeric(200000);out.rows.reserve(1600);out.samples.reserve(400);
 std::size_t expected=0;for(std::size_t a=0;a<scene.objects.size();++a)for(std::size_t b=a+1;b<scene.objects.size();++b)if(!scene.excluded(scene.objects[a],scene.objects[b]))++expected;for(const auto& c:scene.cover){(void)c;for(const auto& o:scene.objects)if(o.category=="fixture"||o.category=="floor")++expected;}need(expected>0&&expected<=20000,"same full configured query roster cap");
 for(int i=0;i<400;++i){const auto& m=raw->substep_maps[i];const auto& v=raw->value.substeps[i];need(m.cell==v.cell&&m.cycle==v.cycle&&m.half==v.half&&m.state.q.size()==7&&m.state.q.allFinite()&&v.q.size()==7&&(m.state.q-v.q).isZero(0)&&std::isfinite(v.elapsed_s)&&std::abs(v.elapsed_s-.002*(i+1))<=1e-10,"actual nominal sample coordinates/time");out.samples.emplace_back();auto& s=out.samples.back();s.sample=i;s.cell=m.cell;s.cycle=m.cycle;s.half=m.half;s.elapsed=v.elapsed_s;s.nominal_q=m.state.q;const auto snapshot=scene.query(robot,s.nominal_q,true,true);need(snapshot.queries.size()==expected,"complete genuine nominal true+cover gradient roster");s.minimum_true=snapshot.minimum_true;s.minimum_cover=snapshot.minimum_cover;s.complete_query_count=snapshot.queries.size();s.selected=phase5_nominal_geometry_selection_v1::select(i,snapshot);for(const auto& selected:s.selected)out.rows.push_back(selected.row);}
 need(out.rows.size()==1600&&out.samples.size()==400,"declared bounded nonempty nominal geometric QP rows");out.complete=true;
 }catch(const std::exception& e){out.complete=false;out.error=e.what();}
}
}
