#include "integrated_horizon_qp.hpp"
#include <cmath>
#include <iostream>
#include <stdexcept>
#include <type_traits>
namespace live=phase5_active_session_v1;
namespace core=phase5_active_session_qp_v1;
void need(bool x,const char* why){if(!x)throw std::runtime_error(why);}
void near(double a,double b,double e=1e-13){need(std::isfinite(a)&&std::isfinite(b)&&std::abs(a-b)<=e,"numeric invariant mismatch");}
template<class F> void refused(F f){bool fail=false;try{f();}catch(const std::invalid_argument&){fail=true;}need(fail,"invalid boundary unexpectedly accepted");}
int main(int argc,char** argv){try{
 need(argc==3,"constants path and digest required");
 static_assert(!std::is_copy_constructible_v<live::OwnedPublicForecast>);
 static_assert(std::is_nothrow_move_constructible_v<live::OwnedPublicForecast>);
 const auto ranges=live::loadPinnedStaticRanges(argv[1],argv[2]);
 live::ObservedActual o;o.q={0,0,0,-1.57079,0,1.57079,-.7853};o.v.fill(.1);o.boundary={8,4};o.observation_id="REAL_TEST_BOUNDARY";o.transaction_id="COMPLETED_TEST_TRANSACTION";o.completed=true;o.current_contact_free=true;o.state_age_seconds=.001;
 live::AcceptedCommandHistory h;h.C=o.q;h.w.fill(-.001);h.previous_alpha.fill(.04);h.boundary=o.boundary;h.observation_id=o.observation_id;h.transaction_id=o.transaction_id;h.completed=true;
 live::ProgressHistory p;p.s=.3;p.r=.01;p.previous_b=.01;p.boundary=o.boundary;p.observation_id=o.observation_id;p.transaction_id=o.transaction_id;p.completed=true;
 live::State30 x;x.q=o.q;x.v=o.v;x.C=h.C;x.w=h.w;x.s=p.s;x.r=p.r;
 live::CurrentBoundaryExpectation c;c.boundary=o.boundary;c.observation_id=o.observation_id;c.transaction_id=o.transaction_id;c.maximum_age_seconds=.004;c.no_command_in_flight=true;
 live::NominalAnchor a{x,c.boundary};
 auto context=live::validateLiveActual(o,h,p,a,c,ranges);
 live::JointVector alpha;alpha.fill(.05);auto request=live::first4msRequest(context,alpha,.02);
 for(int j=0;j<7;++j){near(request.w_next[j],-.0008);near(request.C_next[j],h.C[j]-.0000032);near(request.command_jerk_if_accepted[j],2.5,1e-11);}
 near(request.s_next,.30004016);near(request.r_next,.01008);near(request.half_s_reference[0],.30002004);near(request.half_r_reference[0],.01004);near(request.progress_jerk,2.5);
 need(h.w[0]==-.001&&p.s==.3&&o.v[0]==.1,"preview mutated accepted history or physical velocity");
 auto bad_o=o;bad_o.state_age_seconds=.004001;refused([&]{live::validateLiveActual(bad_o,h,p,a,c,ranges);});
 auto bad_h=h;bad_h.boundary.completed_tick=9;refused([&]{live::validateLiveActual(o,bad_h,p,a,c,ranges);});
 bad_h=h;bad_h.transaction_id="OTHER";refused([&]{live::validateLiveActual(o,bad_h,p,a,c,ranges);});
 auto bad_c=c;bad_c.no_command_in_flight=false;refused([&]{live::validateLiveActual(o,h,p,a,bad_c,ranges);});
 auto bad_a=a;bad_a.point.q[0]+=.000001;refused([&]{live::validateLiveActual(o,h,p,bad_a,c,ranges);});
 Eigen::VectorXd u(core::NZ);for(int k=0;k<core::N;++k)for(int j=0;j<core::NU;++j)u(k*core::NU+j)=100*k+j;
 // Independent cycle-expanded oracle, including zero tail beyond old horizon.
 std::vector<Eigen::Matrix<double,8,1>> held;for(int k=0;k<core::N;++k)for(live::Count t=0;t<core::lattice[k];++t)held.push_back(u.segment<8>(k*8));
 for(live::Count shift:{0ULL,1ULL,37ULL,199ULL}){auto guess=core::shiftControlGuess(u,shift);live::Count at=shift;for(int k=0;k<core::N;++k){Eigen::Matrix<double,8,1> sum=Eigen::Matrix<double,8,1>::Zero();for(live::Count t=0;t<core::lattice[k];++t,++at)if(at<held.size())sum+=held[at];sum/=core::lattice[k];for(int j=0;j<8;++j)near(guess(k*8+j),sum(j),1e-10);}}
 refused([&]{core::shiftControlGuess(u,200);});
 live::HorizonSpec spec;spec.policy=live::MeshPolicy::ExplicitCycles;spec.explicit_cycles.assign(core::lattice.begin(),core::lattice.end());const auto mesh=live::planMesh(spec);const auto plan=live::planResources(mesh,{},live::CaptureMode::CompactComplete,live::NumericEncoding::LosslessBinary);
 live::BatchBudget batch;{live::CaseBudget one(batch,plan);{auto ticket=one.reserve(16);one.chargeScratchOrCopy(8);need(batch.liveSlots()==16&&batch.cumulativeCharges()==24,"first case ledger");}need(batch.liveSlots()==0&&batch.cumulativeCharges()==24,"charges refunded after release");}
 {live::CaseBudget two(batch,plan);auto ticket=two.reserve(12);need(batch.cumulativeCharges()==36,"session cumulative ledger reset between cases");}need(batch.liveSlots()==0&&batch.cumulativeCharges()==36,"ledger lifetime invariant");
 std::cout<<"PASS: first4ms command/history separation, five stale/mismatched boundary refusals, four independent expanded warm shifts, shared cumulative ledger; Model/nominal/QP/plant calls=0\n";return 0;
 }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
