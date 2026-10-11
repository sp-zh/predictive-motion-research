#include "runtime_observer.hpp"
#include <iostream>
#include <iomanip>
#include <stdexcept>
#include <cstring>
#include <thread>
namespace rt=phase5_active_session_runtime_v1;namespace live=phase5_active_session_v1;
void need(bool c,const char* s){if(!c)throw std::runtime_error(s);}
int main(int argc,char** argv){try{
 need(argc==6,"XML/path SHA bytes and constants path SHA required");
 const auto ranges=live::loadPinnedStaticRanges(argv[4],argv[5]);
 rt::Simulation sim(live::FileIdentity{argv[1],argv[2],std::stoull(argv[3])},"OBSERVER_REGRESSION_V1");
 rt::Snapshot a,b,c;sim.observe(a);auto current_a=sim.current(a,rt::ObservationClock::OfflineFrozenSimulationBoundary);
 live::State30 initial;initial.q=a.actualObservation().q;initial.v=a.actualObservation().v;initial.C=a.acceptedHistory().C;initial.w=a.acceptedHistory().w;initial.s=a.progressHistory().s;initial.r=a.progressHistory().r;
 const auto ctx=live::validateLiveActual(a.actualObservation(),a.acceptedHistory(),a.progressHistory(),live::NominalAnchor{initial,a.actualObservation().boundary},current_a,ranges);
 sim.observe(b);sim.observe(c);
 need(a.completed()&&b.completed()&&c.completed()&&a.simulationTime()==0&&b.simulationTime()==0&&c.simulationTime()==0,"observer advanced simulation");
 need(a.integrationBefore().size()==b.integrationBefore().size()&&b.integrationBefore().size()==c.integrationBefore().size()&&std::memcmp(a.integrationBefore().data(),b.integrationBefore().data(),a.integrationBefore().size()*sizeof(mjtNum))==0&&std::memcmp(b.integrationBefore().data(),c.integrationBefore().data(),b.integrationBefore().size()*sizeof(mjtNum))==0,"repeated observation changed native integration");
 need(a.actualObservation().observation_id!=b.actualObservation().observation_id&&b.actualObservation().observation_id!=c.actualObservation().observation_id&&a.actualObservation().transaction_id==c.actualObservation().transaction_id,"fresh ID/completed history semantics");
 bool stale=false;try{sim.current(a);}catch(const std::invalid_argument&){stale=true;}need(stale,"old snapshot admitted as latest current observer");
 need(sim.ageSeconds(c)>=c.actualObservation().state_age_seconds,"original timestamp shifted or age refreshed");
 need(ctx.actualInitial().q==c.actualObservation().q&&ctx.actualInitial().v==c.actualObservation().v&&c.acceptedHistory().C==ctx.actualInitial().C,"repeated genuine measured/current histories differ");
 std::this_thread::sleep_for(std::chrono::milliseconds(5));
 bool old_age=false;try{sim.current(c,rt::ObservationClock::OnlineWallAge);}catch(const std::invalid_argument&){old_age=true;}need(old_age,"stale original capture admitted as online observation");
 sim.current(c,rt::ObservationClock::OfflineFrozenSimulationBoundary);
 const auto& f=sim.facts();need(f.load_xml==1&&f.make_data==2&&f.reset==1&&f.forward==4&&f.copy==3&&f.get_state==6&&f.observations==3&&f.step==0&&f.commits==0,"native wrapper facts differ from declared test");
 sim.verifyTermination();
 std::cout<<std::setprecision(17)<<"{\"complete\":true,\"scope\":\"actual repeated independent native observation only\",\"load_xml\":1,\"make_data\":2,\"reset\":1,\"forward\":4,\"copy\":3,\"get_state\":6,\"observations\":3,\"steps\":0,\"commits\":0,\"Model_nominal_QP_candidate_calls\":0,\"stored_observer_age\":"<<c.actualObservation().state_age_seconds<<",\"derived_age\":"<<sim.ageSeconds(c)<<",\"q\":[";
 for(int j=0;j<7;++j){if(j)std::cout<<',';std::cout<<c.actualObservation().q[j];}std::cout<<"],\"v\":[";for(int j=0;j<7;++j){if(j)std::cout<<',';std::cout<<c.actualObservation().v[j];}std::cout<<"],\"accepted_C\":[";for(int j=0;j<7;++j){if(j)std::cout<<',';std::cout<<c.acceptedHistory().C[j];}std::cout<<"]}\n";return 0;
 }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
