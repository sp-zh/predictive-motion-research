#include "partition_internal.hpp"
#include <algorithm>
#include <initializer_list>
#include <stdexcept>
namespace phase5_public_live_affine_v2 {
namespace {
void need(bool x,const char* why){if(!x)throw std::invalid_argument(why);}
Count add(Count a,Count b){return checkedAdd(a,b);}Count mul(Count a,Count b){return checkedMultiply(a,b);}
Count sum(std::initializer_list<Count> xs){Count n=0;for(Count x:xs)n=add(n,x);return n;}
void sha(const std::string& value){need(value.size()==64,"bounded SHA identity");for(char c:value)need((c>='0'&&c<='9')||(c>='a'&&c<='f'),"lowercase SHA identity");}
void inputIdentity(const FileIdentity& f,const std::string& semantic,const ResourcePlan& p){
  need(!f.path.empty()&&f.path[0]=='/'&&f.path.size()<=4096&&f.path.find('\0')==std::string::npos,"bounded pinned input path before snapshot");sha(f.sha256);sha(semantic);
  need(f.bytes>0&&f.bytes<=p.outputCeiling()&&f.bytes<=ResourcePolicyV2::output_bytes,"capture input byte envelope");
}
Count subtract(Count a,Count b){need(a>=b,"capture partition exceeds actual planned work");return a-b;}
}
namespace detail {
struct CaptureWorkspaceFactory {
  static CaptureWorkspaceGrant prepare(const AffineAssemblyOutcome& source){
    need(source.hasCompleteAssembly(),"genuine complete affine source required for workspace preparation");
    const auto& a=source.assembly();const auto& plan=a.costPlan();const auto& shape=a.boundCostShape();
    inputIdentity(a.boundCostInputIdentity(),a.boundCostSemanticSha256(),plan);
    auto state=std::shared_ptr<CapturePartitionState>(new CapturePartitionState(a.captureOriginToken(),a.costBudget().share(),plan,shape,a.boundCostInputIdentity(),a.boundCostSemanticSha256()));
    try{auto& o=state->status;const Count n=plan.du()/8,t=a.originalNormalization().maps().cycleCount(),s=mul(2,t),du=plan.du(),dy=plan.dy(),r=shape.largest_term_rows;
      // Exact upper of B1 closed requirement keys for a complete metadata roster.
      o.catalogue_role_upper=sum({32,mul(16,n),mul(12,t),mul(23,s),mul(20,shape.terms),mul(3,shape.addition_records),plan.captureMode()==CaptureMode::DenseAuditComplete?sum({7,mul(7,s)}):0});
      // One extra typed leaf per composite alpha/b + integer cycle control.
      o.cell_control_split_extra=n;
      o.receipt_limit=sum({o.catalogue_role_upper,o.ancillary_numeric_limit,o.cell_control_split_extra});
      // Catalogue20 stays live; writerIO20/reader28 are mutually exclusive.
      o.credit_slots=sum({20,std::max<Count>(20,28),mul(4,o.receipt_limit)});
      o.planned_work=sum({mul(4,mul(r,dy)),mul(4,mul(r,du)),mul(4,mul(du,du)),mul(2,mul(dy,du))});
      o.topology_slots=sum({shape.addition_coefficients/30,mul(shape.addition_records,4)});
      o.required_actual_work=sum({du,1,mul(r,dy),mul(2,r),mul(2,dy),mul(r,du),mul(dy,du),mul(2,mul(du,du)),mul(3,du),1});
      o.remaining_actual_work=subtract(o.planned_work,sum({o.topology_slots,16,o.credit_slots}));
      need(o.required_actual_work<=o.remaining_actual_work,"capture prepartition leaves insufficient actual cost workspace");
      need(state->source_origin&&state->budget.numericEncoding()==plan.numericEncoding()&&state->budget.liveCeiling()==plan.liveCeiling()&&state->budget.chargeCeiling()==plan.chargeCeiling()&&state->budget.outputCeiling()==plan.outputCeiling(),"genuine case/plan mismatch");
      o.prepared=true;
    }catch(const std::exception& e){state->reject(e.what());}catch(...){state->reject("NONSTANDARD_CAPTURE_PARTITION_PREPARATION_FAILURE");}
    return CaptureWorkspaceGrant(std::move(state));
  }
};
}
CaptureWorkspaceGrant::CaptureWorkspaceGrant(std::shared_ptr<detail::CapturePartitionState> s):state_(std::move(s)){}
CaptureWorkspaceObservation CaptureWorkspaceGrant::observation() const{need(static_cast<bool>(state_),"moved capture workspace grant");return state_->status;}
CaptureWorkspaceObservation CaptureWorkspaceObserver::observation() const{need(static_cast<bool>(state_),"capture workspace observer absent");return state_->status;}
CaptureWorkspaceObserver CaptureWorkspaceGrant::observer() const{need(static_cast<bool>(state_),"moved capture workspace grant");return CaptureWorkspaceObserver(state_);}
bool CaptureWorkspaceGrant::readyForOneAdmission() const noexcept{return state_&&state_->status.prepared&&!state_->status.attempted&&!state_->status.refused;}
CaptureWorkspaceGrant prepareCaptureWorkspaceV1(const AffineAssemblyOutcome& source){return detail::CaptureWorkspaceFactory::prepare(source);}
}
