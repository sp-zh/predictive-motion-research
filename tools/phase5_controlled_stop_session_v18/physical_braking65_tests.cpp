#include "physical_braking_codec65.hpp"
#include <filesystem>
#include <iostream>
#include <limits>
namespace live=phase5_active_session_v1;namespace plan=phase5_physical_braking65_v1;namespace codec=phase5_physical_braking_codec65_v1;namespace ev=phase5_active_evidence_v1;namespace storage=phase5_lossless_stream_storage_v4;
void require(bool b,const char*s){if(!b)throw std::runtime_error(s);}template<class F>void denied(F fn){bool caught=false;try{fn();}catch(const std::exception&){caught=true;}require(caught,"expected finite rejection");}
int main(int argc,char**argv){try{require(argc==2,"fresh bounded pure directory");std::filesystem::path root=argv[1];require(root.is_absolute()&&!std::filesystem::exists(root),"fresh pure root");std::filesystem::create_directory(root);storage::StoredBudget budget(32ULL*1024*1024,2ULL*1024*1024);const auto ranges=live::loadPinnedStaticRanges("/home/codextransfer/predictive_motion/results/phase5/integrated-first-cycle-v1-20261010/runtime-profile-version2/inputs/public_constants.json","d37c9a12539345fd1dbb6718cd273584140359ca2bd9834442bf2228e50f6bdd");
live::ObservedActual ba;live::AcceptedCommandHistory bc;live::ProgressHistory bp;ba.completed=ba.current_contact_free=bc.completed=bp.completed=true;ba.observation_id=bc.observation_id=bp.observation_id="PURE65_SAVED64_BASELINE";ba.transaction_id=bc.transaction_id=bp.transaction_id="NO_MODEL_NATIVE";
ba.q={-1.2457657480319455,0.098664936501871678,1.1540916193226654,-2.7855809586168485,-0.097623555799482356,4.3844260218215902,-1.6281406873307038};
ba.v={-2.8843992076774874e-09,9.6806087560919549e-06,-1.1349399098085768e-07,-3.2891034196009085e-07,1.9718796206861044e-08,-3.2471222261747519e-08,3.1496738564326231e-10};
bc.C={-1.2457657489100911,0.096647806394742825,1.1546321286355201,-2.7819779781855476,-0.097550876236406223,4.3852467036499583,-1.6281268331277312};
bc.w={0,0,0,0,0,0,0};
bc.previous_alpha={0,0,0,0,0,0,0};
bp.s=0;bp.r=0;bp.previous_b=0;const auto base=plan::baseline(ba,bc,bp);
{live::ObservedActual a;live::AcceptedCommandHistory c;live::ProgressHistory p;a.completed=a.current_contact_free=c.completed=p.completed=true;a.observation_id=c.observation_id=p.observation_id="PURE65_SAVED64_CURRENT32";a.transaction_id=c.transaction_id=p.transaction_id="NO_MODEL_NATIVE";a.boundary.completed_tick=c.boundary.completed_tick=p.boundary.completed_tick=32;a.boundary.completed_command_sequence=c.boundary.completed_command_sequence=p.boundary.completed_command_sequence=32;
a.q={-1.2457600081276832,0.098658608182580085,1.1541070549831773,-2.7855677184621679,-0.097636916493101897,4.3844406658671291,-1.6281563244298716};
a.v={0.00013457041211566734,-0.00021559591882220337,0.000457685144098359,0.00039879804889611102,-0.00033314576112092895,0.00044739963914296226,-0.0004435228110003943};
c.C={-1.2457404188297727,0.096540335490075971,1.1547395656639872,-2.7818705072808796,-0.097620032817960611,4.3853541745546236,-1.6282172410413318};
c.w={0.00050532486444307401,-0.0023859501430932321,0.0023823557337940308,0.0023859501430932325,-0.00079289952342208585,0.0023859501430932321,-0.0015854325280717282};
c.previous_alpha={0.0097872144868879594,-0.03641847209714022,0.036110359816061172,0.03641847209714022,0.0109915348176985,0.036418472097140109,-0.0089434948153872575};
p.s=0.0012665643073840355;p.r=0.022134098071926317;p.previous_b=0.17293775393293928;std::vector<live::NominalControl>u(20);const auto beforea=a;const auto beforec=c;const auto beforep=p;
ev::Evidence out((root/"saved64-current32").string(),nullptr,&budget);auto d=codec::emit(out,32,0,true,1,a,c,p,base,ranges,u,"PURE65/stop_w_r_v1");require(d.complete&&d.total_attempts==1057,"saved64 nominal count");
require(d.selected[0]==111&&d.attempted[0]==132,"all132 joint families and bestscore selection");
require(std::abs(d.pulse1[0]-(-0.13441731068826432))<=2e-12&&std::abs(d.pulse2[0]-(-0.00053734974960103078))<=2e-12,"saved independent doublehat coefficients");
require(d.selected[1]==3&&d.attempted[1]==132,"all132 joint families and bestscore selection");
require(std::abs(d.pulse1[1]-(0.12779474542015923))<=2e-12&&std::abs(d.pulse2[1]-(-0.0014180739966812373))<=2e-12,"saved independent doublehat coefficients");
require(d.selected[2]==3&&d.attempted[2]==132,"all132 joint families and bestscore selection");
require(std::abs(d.pulse1[2]-(-0.12712651545287504))<=2e-12&&std::abs(d.pulse2[2]-(0.0013736524827804243))<=2e-12,"saved independent doublehat coefficients");
require(d.selected[3]==3&&d.attempted[3]==132,"all132 joint families and bestscore selection");
require(std::abs(d.pulse1[3]-(-0.12742160746503078))<=2e-12&&std::abs(d.pulse2[3]-(0.0013849061784475963))<=2e-12,"saved independent doublehat coefficients");
require(d.selected[4]==99&&d.attempted[4]==132,"all132 joint families and bestscore selection");
require(std::abs(d.pulse1[4]-(0.060861294662608263))<=2e-12&&std::abs(d.pulse2[4]-(-0.0010134204985628109))<=2e-12,"saved independent doublehat coefficients");
require(d.selected[5]==3&&d.attempted[5]==132,"all132 joint families and bestscore selection");
require(std::abs(d.pulse1[5]-(-0.12737199129494289))<=2e-12&&std::abs(d.pulse2[5]-(0.0013804958522175624))<=2e-12,"saved independent doublehat coefficients");
require(d.selected[6]==90&&d.attempted[6]==132,"all132 joint families and bestscore selection");
require(std::abs(d.pulse1[6]-(0.15139638593500526))<=2e-12&&std::abs(d.pulse2[6]-(-0.00085704737661895238))<=2e-12,"saved independent doublehat coefficients");
require(d.selected[7]==132,"genuine progress first-band family");for(int k=0;k<20;++k){
require(std::isfinite(u[k].alpha[0]),"finite nominal");
require(std::isfinite(u[k].alpha[1]),"finite nominal");
require(std::isfinite(u[k].alpha[2]),"finite nominal");
require(std::isfinite(u[k].alpha[3]),"finite nominal");
require(std::isfinite(u[k].alpha[4]),"finite nominal");
require(std::isfinite(u[k].alpha[5]),"finite nominal");
require(std::isfinite(u[k].alpha[6]),"finite nominal");
require(std::isfinite(u[k].b),"finite nominal");
}require(a.q==beforea.q&&a.v==beforea.v&&c.C==beforec.C&&c.w==beforec.w&&c.previous_alpha==beforec.previous_alpha&&p.s==beforep.s&&p.r==beforep.r&&p.previous_b==beforep.previous_b,"actual/history unchanged");out.finish("SAVED64_SCALAR_DOUBLEHAT_FIRSTPROGRESS_ONLY","No Model/native/SI/B/C/physicalstop",true);
auto bad=a;bad.observation_id="MISMATCH";const auto prior=u;denied([&]{plan::build(bad,c,p,base,ranges,u,[](const auto&){});});for(int k=0;k<20;++k)require(u[k].alpha==prior[k].alpha&&u[k].b==prior[k].b,"identity reject controls unchanged");bad=a;bad.v[0]=std::numeric_limits<double>::quiet_NaN();denied([&]{plan::build(bad,c,p,base,ranges,u,[](const auto&){});});
ev::Evidence none((root/"no-rebuild-32").string(),nullptr,&budget);const auto no=codec::emit(none,32,1,false,1,a,c,p,base,ranges,u,"PURE65/stop_w_r_v1");require(!no.complete&&no.total_attempts==0,"rejected-B next trial no regeneration");none.finish("NO_REBUILD","",true);}
{live::ObservedActual a;live::AcceptedCommandHistory c;live::ProgressHistory p;a.completed=a.current_contact_free=c.completed=p.completed=true;a.observation_id=c.observation_id=p.observation_id="PURE65_SAVED64_CURRENT87";a.transaction_id=c.transaction_id=p.transaction_id="NO_MODEL_NATIVE";a.boundary.completed_tick=c.boundary.completed_tick=p.boundary.completed_tick=87;a.boundary.completed_command_sequence=c.boundary.completed_command_sequence=p.boundary.completed_command_sequence=87;
a.q={-1.2457436766400589,0.098599256580262279,1.1542052018188449,-2.7854780546989408,-0.097684086795070776,4.3845419981625602,-1.6282331533211873};
a.v={3.3039461846370765e-05,-0.00021001147424637594,0.0002242866673447028,0.00023240615527199499,-9.086877445481084e-05,0.00022314781321132915,-0.00013158591494646623};
c.C={-1.2457379471274204,0.096499430390488097,1.1547804020423158,-2.781829453614864,-0.097623847309292799,4.3853950901233603,-1.6282344382180787};
c.w={5.0000000000013815e-07,-5.0000000000000951e-07,5.0000000000012597e-07,4.9999999999991866e-07,-4.9999999999999521e-07,5.0000000000000506e-07,-5.0000000000000707e-07};
c.previous_alpha={2.2472842881840656e-17,-5.0292581243224083e-18,4.1636963313469201e-17,-2.8322664173815668e-17,9.1320739625854255e-18,2.4113969217145863e-17,2.4616895029578104e-18};
p.s=0.0040112274855189202;p.r=9.9999999997196691e-10;p.previous_b=-5.31060726387798e-17;std::vector<live::NominalControl>u(20);const auto beforea=a;const auto beforec=c;const auto beforep=p;
ev::Evidence out((root/"saved64-current87").string(),nullptr,&budget);auto d=codec::emit(out,87,0,true,1,a,c,p,base,ranges,u,"PURE65/stop_w_r_v1");require(d.complete&&d.total_attempts==925,"saved64 nominal count");
require(d.selected[0]==0&&d.attempted[0]==132,"all132 joint families and bestscore selection");
require(std::abs(d.pulse1[0]-(-0.0020221366202620079))<=2e-12&&std::abs(d.pulse2[0]-(7.2705123259824388e-05))<=2e-12,"saved independent doublehat coefficients");
require(d.selected[1]==0&&d.attempted[1]==132,"all132 joint families and bestscore selection");
require(std::abs(d.pulse1[1]-(0.026441310401008451))<=2e-12&&std::abs(d.pulse2[1]-(-0.00098842414003781588))<=2e-12,"saved independent doublehat coefficients");
require(d.selected[2]==0&&d.attempted[2]==132,"all132 joint families and bestscore selection");
require(std::abs(d.pulse1[2]-(-0.011966768973496088))<=2e-12&&std::abs(d.pulse2[2]-(0.00044562883650610218))<=2e-12,"saved independent doublehat coefficients");
require(d.selected[3]==0&&d.attempted[3]==132,"all132 joint families and bestscore selection");
require(std::abs(d.pulse1[3]-(-0.015331283643087485))<=2e-12&&std::abs(d.pulse2[3]-(0.00057179813661578074))<=2e-12,"saved independent doublehat coefficients");
require(d.selected[4]==0&&d.attempted[4]==132,"all132 joint families and bestscore selection");
require(std::abs(d.pulse1[4]-(0.0044081693724354609))<=2e-12&&std::abs(d.pulse2[4]-(-0.00016218135146632971))<=2e-12,"saved independent doublehat coefficients");
require(d.selected[5]==0&&d.attempted[5]==132,"all132 joint families and bestscore selection");
require(std::abs(d.pulse1[5]-(-0.011268044385237356))<=2e-12&&std::abs(d.pulse2[5]-(0.00041942666444640049))<=2e-12,"saved independent doublehat coefficients");
require(d.selected[6]==0&&d.attempted[6]==132,"all132 joint families and bestscore selection");
require(std::abs(d.pulse1[6]-(0.0054738589394185376))<=2e-12&&std::abs(d.pulse2[6]-(-0.00020214471022819502))<=2e-12,"saved independent doublehat coefficients");
require(d.selected[7]==0,"genuine progress first-band family");for(int k=0;k<20;++k){
require(std::isfinite(u[k].alpha[0]),"finite nominal");
require(std::isfinite(u[k].alpha[1]),"finite nominal");
require(std::isfinite(u[k].alpha[2]),"finite nominal");
require(std::isfinite(u[k].alpha[3]),"finite nominal");
require(std::isfinite(u[k].alpha[4]),"finite nominal");
require(std::isfinite(u[k].alpha[5]),"finite nominal");
require(std::isfinite(u[k].alpha[6]),"finite nominal");
require(std::isfinite(u[k].b),"finite nominal");
}require(a.q==beforea.q&&a.v==beforea.v&&c.C==beforec.C&&c.w==beforec.w&&c.previous_alpha==beforec.previous_alpha&&p.s==beforep.s&&p.r==beforep.r&&p.previous_b==beforep.previous_b,"actual/history unchanged");out.finish("SAVED64_SCALAR_DOUBLEHAT_FIRSTPROGRESS_ONLY","No Model/native/SI/B/C/physicalstop",true);
auto bad=a;bad.observation_id="MISMATCH";const auto prior=u;denied([&]{plan::build(bad,c,p,base,ranges,u,[](const auto&){});});for(int k=0;k<20;++k)require(u[k].alpha==prior[k].alpha&&u[k].b==prior[k].b,"identity reject controls unchanged");bad=a;bad.v[0]=std::numeric_limits<double>::quiet_NaN();denied([&]{plan::build(bad,c,p,base,ranges,u,[](const auto&){});});
ev::Evidence none((root/"no-rebuild-87").string(),nullptr,&budget);const auto no=codec::emit(none,87,1,false,1,a,c,p,base,ranges,u,"PURE65/stop_w_r_v1");require(!no.complete&&no.total_attempts==0,"rejected-B next trial no regeneration");none.finish("NO_REBUILD","",true);}
{storage::StoredBudget old(64,16),hot(64,16,48);require(old.cap()==64&&old.physicalCap()==64&&hot.cap()==64&&hot.physicalCap()==48,"original cap preserved, optional hot cap tightens only");hot.reserve(32);denied([&]{hot.reserve(1);});require(hot.charged()==32,"normal hot tail not spent/refunded");hot.beginFinalization();hot.reserve(16);denied([&]{hot.reserve(1);});denied([&]{hot.beginFinalization();});require(hot.charged()==48,"one tail release/same spent");old.reserve(48);old.beginFinalization();old.reserve(16);require(old.charged()==64,"old default exact quota");denied([&]{storage::StoredBudget invalid(64,16,65);});denied([&]{storage::StoredBudget invalid(64,16,16);});}
{ev::Evidence out((root/"max1080").string(),nullptr,&budget);out.write("all.bin","PURE65_1080_SYNTHETIC_STORAGE_NO_MODEL",[&](ev::BinaryFile&file){codec::Output f{file};std::uint64_t records=0;for(std::uint64_t ch=0;ch<8;++ch)for(std::uint64_t id=0;id<(ch==7?149:133);++id)codec::writeAttempt(f,plan::Attempt{ch,id,13,20,0,0,0,0,0,0,0,1,0},records);require(records==1080&&f.charged==256+1080*112,"112B exact all-record precharge");denied([&]{codec::writeAttempt(f,{},records);});require(records==1080,"1081 refused before record");});out.finish("MAX1080_STORAGE_ONLY","",true);}
require(plan::strictFirstProgress(1e-7,0)&&!plan::strictFirstProgress(1e-9,0),"new first-progress strict subset");for(double previous:{-.001,.001}){const double rate=1e-9,oldlower=-4.999-previous/.004;const double lower=plan::firstProgressLower(rate,0.,oldlower);const double firstb=.004*lower;require(lower>=oldlower&&std::abs(rate+.004*firstb-1e-7)<=1e-20,"correct offset-based first-rate lower for nonzero +/- previousb, no duplicate history subtraction");const double wrong=std::max(oldlower,std::nextafter((1e-7-rate)/(.004*.004)-previous/.004,-std::numeric_limits<double>::infinity()));require(std::abs(rate+.004*(.004*wrong)-1e-7)>1e-7,"old wrong formula counterexample retained");}std::cout<<"PASS saved64x2 doublehat all132/bestscore/112B/1080, identityNaN refusal, trial1 no rebuild, original scalar200/400, firstprogress tighter, hotcap defaultcompat/sharedtail/no refund; no Model/native/SI/B/C/physicalstop\n";return 0;}catch(const std::exception&e){std::cerr<<e.what()<<"\n";return 1;}}
