#include "integrated_horizon_qp.hpp"
#include <algorithm>
#include <cmath>
#include <chrono>
#include <limits>
#include <set>
#include <stdexcept>
#include <utility>

namespace phase5_active_session_qp_v1 {
namespace {
constexpr double h=.004;
constexpr int factor_rows=741,max_qp_rows=20000,max_geometry_rows=1600;
constexpr std::uint64_t max_numeric_slots=8000000;
void need(bool v,const char* s){if(!v)throw std::invalid_argument(s);}
void finite(double x){need(std::isfinite(x),"nonfinite integration arithmetic");}
void positive(double x){need(std::isfinite(x)&&x>0,"positive finite integration parameter required");}
Eigen::VectorXd packed(const live::State30& s){Eigen::VectorXd x(NX);
 for(int j=0;j<7;++j){x(j)=s.q[j];x(j+7)=s.v[j];x(j+14)=s.C[j];x(j+21)=s.w[j];}
 x(28)=s.s;x(29)=s.r;need(x.allFinite(),"finite actual30 required");return x;
}
live::State30 nativeState(const phase5_public_coupled_augmented::State& x){
 need(x.q.size()==7&&x.v.size()==7&&x.C.size()==7&&x.w.size()==7,"nominal30 dimension");
 live::State30 s;for(int j=0;j<7;++j){s.q[j]=x.q(j);s.v[j]=x.v(j);s.C[j]=x.C(j);s.w[j]=x.w(j);}s.s=x.s;s.r=x.r;(void)packed(s);return s;
}
void identifier(const std::string& s){need(!s.empty()&&s.size()<=256,"bounded integration identity required");for(unsigned char c:s)need(c>=33&&c<=126,"printable integration identity");}
struct Map {Eigen::MatrixXd M;Eigen::VectorXd c;};
Map boundary(const live::CompactAffineAssembly& a,int node){Map m{Eigen::MatrixXd(NX,NZ),Eigen::VectorXd(NX)};
 for(int r=0;r<NX;++r){m.c(r)=a.boundaryOffset(node,r);
  for(int j=0;j<NX;++j)m.c(r)+=a.boundaryInitial(node,r,j)*a.chosenInitial(j);
  for(int j=0;j<NZ;++j)m.M(r,j)=a.boundaryControl(node,r,j);}
 need(m.M.allFinite()&&m.c.allFinite(),"full boundary composition nonfinite");return m;
}
Map sample(const live::CompactAffineAssembly& a,int index){
 const auto& maps=a.originalNormalization().maps();const auto& prefix=maps.samples().at(index);
 Map base=boundary(a,static_cast<int>(prefix.cell()));
 Map out{prefix.A()*base.M,prefix.A()*base.c+prefix.defect()};
 // NormalizedBlockView exposes genuine CELL-CUMULATIVE prefix A/B/defect,
 // never cycle-local native Map.A/B. Its control is constant in this cell.
 out.M.middleCols(static_cast<int>(prefix.cell())*NU,NU)+=prefix.B();
 need(out.M.allFinite()&&out.c.allFinite(),"full sample prefix composition nonfinite");return out;
}
void parameterChecks(const Inputs& in,const live::LiveActualContext& context){
 const auto& l=in.limits;const auto& w=in.weights;
 for(double v:{l.command_speed,l.command_acceleration,l.command_jerk,l.progress_speed,
     l.progress_acceleration,l.progress_jerk,l.position_margin,l.joint_trust,l.progress_trust,w.rotation_length})positive(v);
 need(l.command_speed<=.0625&&l.command_acceleration<=1&&l.progress_speed<=.2,
      "profile cannot enlarge unchanged command/progress domain");
 need(std::isfinite(in.observed_age_seconds)&&in.observed_age_seconds>=0&&in.observed_age_seconds<=h,
      "original observation already stale");
 need(std::isfinite(in.known_upstream_elapsed_seconds)&&in.known_upstream_elapsed_seconds>=0,"finite actual known upstream elapsed required");
 need(in.timing_mode==TimingMode::OfflineFrozenSimulationBoundary||in.timing_mode==TimingMode::OnlineWallAge,"reviewed timing mode required");
 need(in.timing_mode!=TimingMode::OfflineFrozenSimulationBoundary||in.simulation_boundary_asserted_frozen,"offline component boundary must be asserted frozen by actual source runner");
 identifier(in.objective_source_id);need(static_cast<bool>(in.task),"actual nominal task linearizer required");
 for(double v:{w.tracking,w.physical_velocity,w.posture,w.command_acceleration,w.command_jerk,w.progress_acceleration,w.progress_jerk,w.progress_reward,w.terminal_progress})
  need(std::isfinite(v)&&v>=0,"finite nonnegative explicit objective weights");
 const auto& x=context.actualInitial();const auto& d=context.ranges();
 for(int j=0;j<7;++j){positive(l.physical_speed[j]);finite(w.posture_reference[j]);
  need(d.qLower()[j]+l.position_margin<d.qUpper()[j]-l.position_margin&&
       d.cLower()[j]+l.position_margin<d.cUpper()[j]-l.position_margin,"empty margin bounds");
  need(x.q[j]>=d.qLower()[j]+l.position_margin&&x.q[j]<=d.qUpper()[j]-l.position_margin&&
       std::abs(x.v[j])<=l.physical_speed[j],"initial actual q/v bound refused");
  need(x.C[j]>=d.cLower()[j]+l.position_margin&&x.C[j]<=d.cUpper()[j]-l.position_margin&&
       std::abs(x.w[j])<=l.command_speed&&std::abs(context.previousAlpha()[j])<=l.command_acceleration,
       "initial accepted command/history bound refused");
 }
 need(x.r<=l.progress_speed&&std::abs(context.previousB())<=l.progress_acceleration,"initial progress/history bound refused");
 need(in.geometry.size()<=max_geometry_rows,"separate geometric row cap");
 std::array<int,S> counts{};std::set<std::string> ids;
 for(const auto& g:in.geometry){need(g.sample>=0&&g.sample<S&&g.Jq.allFinite(),"geometry prefix shape");
  identifier(g.id);identifier(g.units);finite(g.nominal_value);finite(g.lower);finite(g.upper);
  need(g.lower<=g.upper&&++counts[g.sample]<=4&&ids.insert(std::to_string(g.sample)+"/"+g.id).second,
       "geometry per-sample count/duplicate/bounds");}
}
} // namespace
struct Outcome::Storage {
 live::AffineAssemblyOutcome original;Inputs inputs;AssemblyTrace trace;Problem problem;
 bool solver_entry_consumed=false;
 std::chrono::steady_clock::time_point connection_started;
 Storage(live::AffineAssemblyOutcome&& a,std::chrono::steady_clock::time_point start):original(std::move(a)),connection_started(start){}
 void stop(const char* e){if(trace.refused)return;trace.refused=true;trace.complete=false;trace.first_error=e?e:"INTEGRATION_REFUSED";}
 void factor(const Eigen::MatrixXd& m,const Eigen::VectorXd& c,double weight,const std::string& name){
  need(m.cols()==NZ&&m.rows()==c.size()&&m.allFinite()&&c.allFinite(),"objective row shape");
  need(std::isfinite(weight)&&weight>=0,"objective weighted duration");const double root=std::sqrt(2*weight);finite(root);
  int start=trace.factor_rows_written;need(start+m.rows()<=factor_rows,"inline factor row cap");
  problem.terms.push_back({name,start,static_cast<int>(m.rows())});
  for(int r=0;r<m.rows();++r){for(int j=0;j<NZ;++j){const double v=root*m(r,j);finite(v);problem.F(start+r,j)=v;}
   const double v=root*c(r);finite(v);problem.f(start+r)=v;++trace.factor_rows_written;}
 }
 void row(const Eigen::RowVectorXd& m,double c,double lo,double hi,const std::string& name,const std::string& units){
  need(m.size()==NZ&&m.allFinite(),"constraint row shape");finite(c);finite(lo);finite(hi);need(lo<=hi,"inverted original SI bounds");
  const double lower=lo-c,upper=hi-c;finite(lower);finite(upper);
  int r=trace.constraint_rows_written;need(r<problem.original_si.constraints.rows(),"separate QP row cap");
  problem.original_si.constraints.row(r)=m;problem.original_si.lower(r)=lower;problem.original_si.upper(r)=upper;
  problem.rows.push_back({name,units});++trace.constraint_rows_written;
 }
 void build(){
  trace.stage="REQUIRE_FULL_GENUINE_LIVE_HORIZON";
  need(original.hasCompleteAssembly()&&original.initialKind()==live::AssemblyInitialKind::LiveActual,
       "failed/incomplete/algebra-only horizon STOP; retain original prefix");
  const auto& a=original.assembly();const auto& maps=a.originalNormalization().maps();const auto& raw=maps.originalForecast();
  need(a.cells()==N&&a.du()==NZ&&a.dx()==630&&a.dy()==790&&maps.samples().size()==S&&maps.cycleCount()==T,
       "complete N20/T200/S400 shape required; no shorter horizon");
  need(raw.mesh().cycles().size()==N&&raw.mesh().total()==T,"bound lattice shape");
  for(int k=0;k<N;++k)need(raw.mesh().cycles()[k]==lattice[k],"explicit nonuniform lattice differs from reviewed profile");
  need(raw.bindingVerified(),"session startup/cycle ownership required");
  const auto& ctx=raw.actualContext();parameterChecks(inputs,ctx);
  trace.timing_mode=inputs.timing_mode;trace.original_observer_age=inputs.observed_age_seconds;
  trace.known_upstream_elapsed=inputs.known_upstream_elapsed_seconds;
  need(raw.originalObservedAge()==inputs.observed_age_seconds,"original observation age cannot be overwritten");
  trace.snapshot_age_bound=true;trace.observation_source="SESSION_BOUND_CALLER_OBSERVER_ASSERTIONS";

  const auto initial=packed(ctx.actualInitial());for(int j=0;j<NX;++j)need(a.chosenInitial(j)==initial(j),"actual30 must remain exact chosen initial");
  const int qrows=13156+static_cast<int>(inputs.geometry.size());need(qrows<=max_qp_rows,"QP row envelope");
  // Separate inline adapter plan. Existing CaseBudget/FactorShape reservations
  // remain untouched. This bounds explicit logical numeric arrays, NOT RSS or
  // the OSQP/native/allocator memory footprint, which future runner must cap.
  trace.planned_numeric_slots=static_cast<std::uint64_t>(qrows)*(NZ+2)+
    static_cast<std::uint64_t>(factor_rows)*(NZ+1)+4*NZ*NZ+20*NX*NZ+64*NZ;
  need(trace.planned_numeric_slots<=max_numeric_slots,"separate inline numeric schedule");
  trace.stage="ALLOCATE_SEPARATE_INLINE_QP";
  auto& p=problem;auto& q=p.original_si;
  q.hessian=Eigen::MatrixXd::Zero(NZ,NZ);q.gradient=Eigen::VectorXd::Zero(NZ);
  q.constraints=Eigen::MatrixXd::Zero(qrows,NZ);q.lower=Eigen::VectorXd::Zero(qrows);q.upper=Eigen::VectorXd::Zero(qrows);
  q.state_age_seconds=inputs.observed_age_seconds;p.F=Eigen::MatrixXd::Zero(factor_rows,NZ);p.f=Eigen::VectorXd::Zero(factor_rows);
  p.seed=Eigen::VectorXd::Zero(NZ);p.rows.reserve(qrows);p.terms.reserve(144);p.retained_task_prefix.reserve(N+1);
  const auto& l=inputs.limits;const auto& w=inputs.weights;const auto& ranges=ctx.ranges();
  trace.stage="ACTUAL_NOMINAL_TASK_AND_OBJECTIVE";
  for(int k=0;k<=N;++k){Map z=boundary(a,k);
   live::State30 nominal=k==0?ctx.actualInitial():nativeState(maps.cells()[k-1].nominalEndpoint());
   TaskLocal task=inputs.task(k,nominal);identifier(task.source_id);
   need(task.residual.allFinite()&&task.Jq.allFinite()&&task.Js.allFinite(),"task local derivative nonfinite");
   p.retained_task_prefix.push_back(task);++trace.task_nodes_returned;
   const auto nominal_x=packed(nominal);
   Eigen::MatrixXd tracking=task.Jq*z.M.topRows(7)+task.Js*z.M.row(28);
   Eigen::VectorXd offset=task.residual+task.Jq*(z.c.head(7)-nominal_x.head(7))+task.Js*(z.c(28)-nominal.s);
   tracking.bottomRows(3)*=w.rotation_length;offset.tail(3)*=w.rotation_length;
   const double duration=.5*h*static_cast<double>((k==0?0:lattice[k-1])+(k==N?0:lattice[k]));
   factor(tracking,offset,w.tracking*duration,"tracking/node/"+std::to_string(k));
   factor(z.M.middleRows(7,7),z.c.segment(7,7),w.physical_velocity*duration,"physical_velocity/node/"+std::to_string(k));
   Eigen::VectorXd posture=z.c.head(7);for(int j=0;j<7;++j)posture(j)-=w.posture_reference[j];
   factor(z.M.topRows(7),posture,w.posture*duration,"posture/node/"+std::to_string(k));
  }
  for(int k=0;k<N;++k){Eigen::MatrixXd u=Eigen::MatrixXd::Zero(NU,NZ),j=u;u.middleCols(k*NU,NU).setIdentity();j=u;
   Eigen::VectorXd jc=Eigen::VectorXd::Zero(NU);if(k==0){for(int d=0;d<7;++d)jc(d)=-ctx.previousAlpha()[d];jc(7)=-ctx.previousB();}
   else j.middleCols((k-1)*NU,NU)-=Eigen::MatrixXd::Identity(NU,NU);
   j/=h;jc/=h; // Changed feedback command boundary, never coarse cell duration.
   factor(u.topRows(7),Eigen::VectorXd::Zero(7),w.command_acceleration*h*lattice[k],"command_alpha/cell/"+std::to_string(k));
   factor(j.topRows(7),jc.head(7),w.command_jerk*h,"command_jerk/cell/"+std::to_string(k));
   factor(u.row(7),Eigen::VectorXd::Zero(1),w.progress_acceleration*h*lattice[k],"progress_b/cell/"+std::to_string(k));
   factor(j.row(7),jc.tail(1),w.progress_jerk*h,"progress_jerk/cell/"+std::to_string(k));
   const auto& native=raw.nativeCells()[k];for(int d=0;d<7;++d)p.seed(k*NU+d)=native.alpha(d);p.seed(k*NU+7)=native.b;
  }
  Map final=boundary(a,N);Eigen::VectorXd terminal(1);terminal(0)=final.c(28)-1;
  factor(final.M.row(28),terminal,w.terminal_progress,"terminal_progress");
  need(trace.factor_rows_written==factor_rows,"all objective factors required");
  trace.stage="INLINE_H_G_CONSTANT_PSD_CERTIFICATE";
  // .5||F U+f||² - progress_reward*s_N. Preserve full linear/constant.
  for(int r=0;r<NZ;++r){for(int c=0;c<NZ;++c){double sum=0;for(int k=0;k<factor_rows;++k){sum+=p.F(k,r)*p.F(k,c);finite(sum);}q.hessian(r,c)=sum;}
   double sum=-w.progress_reward*final.M(28,r);finite(sum);for(int k=0;k<factor_rows;++k){sum+=p.F(k,r)*p.f(k);finite(sum);}q.gradient(r)=sum;}
  p.constant=-w.progress_reward*final.c(28);finite(p.constant);for(int k=0;k<factor_rows;++k){p.constant+=.5*p.f(k)*p.f(k);finite(p.constant);}
  p.psd_factor=p.F.sparseView(); // Solver checks original H against this factor.
  trace.stage="ALL_MACRO_COMMAND_PROGRESS_AND_JERK_ROWS";
  Eigen::MatrixXd C=Eigen::MatrixXd::Zero(7,NZ),W=C;
  Eigen::VectorXd co(7),wo(7);for(int j=0;j<7;++j){co(j)=initial(14+j);wo(j)=initial(21+j);}
  Eigen::RowVectorXd sm=Eigen::RowVectorXd::Zero(NZ),rm=sm;double so=initial(28),ro=initial(29);
  int sample_index=0;
  for(int k=0;k<N;++k){Eigen::RowVectorXd b=Eigen::RowVectorXd::Zero(NZ);b(k*NU+7)=1;
   for(int j=0;j<NU;++j){Eigen::RowVectorXd u=Eigen::RowVectorXd::Zero(NZ);u(k*NU+j)=1;
    const double accel=j<7?l.command_acceleration:l.progress_acceleration;
    row(u,0,-accel,accel,"input/"+std::to_string(k)+"/"+std::to_string(j),j<7?"rad/s^2":"1/s^2");
    Eigen::RowVectorXd jerk=u/h;double prior=0;if(k==0)prior=j<7?ctx.previousAlpha()[j]:ctx.previousB();else jerk((k-1)*NU+j)-=1/h;
    row(jerk,-prior/h,-(j<7?l.command_jerk:l.progress_jerk),j<7?l.command_jerk:l.progress_jerk,
        "feedback_jerk/"+std::to_string(k)+"/"+std::to_string(j),j<7?"rad/s^3":"1/s^3");
   }
   const Eigen::RowVectorXd origin_sm=sm,origin_rm=rm;const double origin_so=so,origin_ro=ro;
   const double duration=h*lattice[k];
   row(origin_sm+.5*duration*origin_rm,origin_so+.5*duration*origin_ro,0,1,
       "progress/bernstein/cell/"+std::to_string(k),"dimensionless");
   for(live::Count cycle=0;cycle<lattice[k];++cycle){
    // Literal accepted-history semi-implicit recursion. Afterk updates its
    // alpha coefficient is .5*k*(k+1)*h², not .5*(k*h)².
    W.middleCols(k*NU,7)+=h*Eigen::MatrixXd::Identity(7,7);C+=h*W;co+=h*wo;
    const auto previous_rm=rm;sm+=h*previous_rm+.5*h*h*b;so+=h*ro;rm+=h*b;
    const std::string tick=std::to_string(sample_index/2+1);
    for(int j=0;j<7;++j){row(C.row(j),co(j),ranges.cLower()[j]+l.position_margin,ranges.cUpper()[j]-l.position_margin,"command/C/tick/"+tick+"/"+std::to_string(j),"rad");
     row(W.row(j),wo(j),-l.command_speed,l.command_speed,"command/w/tick/"+tick+"/"+std::to_string(j),"rad/s");}
    row(sm,so,0,1,"progress/s/tick/"+tick,"dimensionless");row(rm,ro,0,l.progress_speed,"progress/r/tick/"+tick,"1/s");
    for(int half=1;half<=2;++half,++sample_index){const double t=h*cycle+.002*half;
     row(origin_sm+t*origin_rm+.5*t*t*b,origin_so+t*origin_ro,0,1,"progress/s/half/"+std::to_string(sample_index),"dimensionless");
     row(origin_rm+t*b,origin_ro,0,l.progress_speed,"progress/r/half/"+std::to_string(sample_index),"1/s");
    }
   }
  }
  for(int j=0;j<7;++j){row(W.row(j),wo(j),0,0,"terminal/command_w/"+std::to_string(j),"rad/s");Eigen::RowVectorXd u=Eigen::RowVectorXd::Zero(NZ);u((N-1)*NU+j)=1;row(u,0,0,0,"terminal/alpha/"+std::to_string(j),"rad/s^2");}
  row(rm,ro,0,0,"terminal/progress_r","1/s");Eigen::RowVectorXd lastb=Eigen::RowVectorXd::Zero(NZ);lastb((N-1)*NU+7)=1;row(lastb,0,0,0,"terminal/b","1/s^2");
  trace.stage="EVERY_HALF_PHYSICAL_Q_V_TRUST_AND_GEOMETRY_ROWS";
  for(int s=0;s<S;++s){Map z=sample(a,s);const auto nominal=nativeState(maps.samples()[s].nominalEndpoint());
   for(int j=0;j<7;++j){const std::string suffix=std::to_string(s)+"/"+std::to_string(j);
    row(z.M.row(j),z.c(j),ranges.qLower()[j]+l.position_margin,ranges.qUpper()[j]-l.position_margin,"physical/q/half/"+suffix,"rad");
    row(z.M.row(j+7),z.c(j+7),-l.physical_speed[j],l.physical_speed[j],"physical/v/half/"+suffix,"rad/s");
    row(z.M.row(j),z.c(j),nominal.q[j]-l.joint_trust,nominal.q[j]+l.joint_trust,"trust/q/half/"+suffix,"rad");}
   row(z.M.row(28),z.c(28),nominal.s-l.progress_trust,nominal.s+l.progress_trust,"trust/s/half/"+std::to_string(s),"dimensionless");
   for(const auto& g:inputs.geometry)if(g.sample==s){Eigen::VectorXd nominal_q(7);for(int j=0;j<7;++j)nominal_q(j)=nominal.q[j];
    const double c=g.nominal_value+(g.Jq*(z.c.head(7)-nominal_q))(0);row(g.Jq*z.M.topRows(7),c,g.lower,g.upper,"geometry/half/"+std::to_string(s)+"/"+g.id,g.units);}
  }
  need(sample_index==S&&trace.constraint_rows_written==qrows&&trace.task_nodes_returned==21,"complete inline row/task roster required");
  std::set<std::string> labels;for(const auto& r:p.rows)need(labels.insert(r.label).second,"unique SI semantic row labels required");
  trace.connection_elapsed=std::chrono::duration<double>(std::chrono::steady_clock::now()-connection_started).count();
  trace.linear_geometry_present=!inputs.geometry.empty();trace.stage="COMPLETE_INLINE_QP_COMPONENT_ONLY";trace.complete=true;
 }
};
Outcome::Outcome(std::unique_ptr<Storage> p):storage_(std::move(p)){}
Outcome::Outcome(Outcome&&) noexcept=default;Outcome& Outcome::operator=(Outcome&&) noexcept=default;Outcome::~Outcome()=default;
bool Outcome::complete() const noexcept{return storage_&&storage_->trace.complete&&!storage_->trace.refused&&storage_->original.hasCompleteAssembly();}
const AssemblyTrace& Outcome::trace() const{need(static_cast<bool>(storage_),"moved integration owner");return storage_->trace;}
const Problem& Outcome::retainedProblem() const{need(static_cast<bool>(storage_),"moved integration owner");return storage_->problem;}
const live::AffineAssemblyOutcome& Outcome::originalAssembly() const{need(static_cast<bool>(storage_),"moved integration owner");return storage_->original;}
Outcome connect(live::OwnedPublicForecast&& forecast,const Inputs& in){
 // Existing owners retain original full result or failure prefix through moves.
 const auto connection_started=std::chrono::steady_clock::now();
 auto normalized=live::normalizePublic(std::move(forecast));
 auto affine=live::assembleLiveAffine(std::move(normalized),live::CaptureMode::CompactComplete);
 auto p=std::make_unique<Outcome::Storage>(std::move(affine),connection_started);
 try{need(in.geometry.size()<=max_geometry_rows,"geometry cap before copying input");
  identifier(in.objective_source_id);p->inputs=in;p->build();}catch(const std::exception& e){p->stop(e.what());}catch(...){p->stop("NONSTANDARD_INTEGRATION_FAILURE");}
 p->trace.connection_elapsed=std::chrono::duration<double>(std::chrono::steady_clock::now()-connection_started).count();
 return Outcome(std::move(p));
}
namespace {
TerminalTailObservation strictRoundedCommandAndProgress(const live::LiveActualContext& ctx,const Limits& l,const Eigen::VectorXd& u){
 auto x=ctx.actualInitial();live::JointVector previous=ctx.previousAlpha();double prior_b=ctx.previousB();
 for(int k=0;k<N;++k){const auto origin=x;
  for(live::Count t=0;t<lattice[k];++t){for(int j=0;j<7;++j){const double alpha=u(k*NU+j);
    need(std::abs(alpha)<=l.command_acceleration,"candidate alpha strict bound");
    const double nextw=x.w[j]+h*alpha,nextC=x.C[j]+h*nextw;finite(nextw);finite(nextC);
    const double implied=(nextw-x.w[j])/h,jerk=(implied-previous[j])/h;finite(implied);finite(jerk);
    need(std::abs(implied)<=l.command_acceleration&&std::abs(jerk)<=l.command_jerk&&std::abs(nextw)<=l.command_speed,
         "rounded candidate command derivative bound");
    need(nextC>=ctx.ranges().cLower()[j]+l.position_margin&&nextC<=ctx.ranges().cUpper()[j]-l.position_margin,"rounded candidate C bound");
    x.C[j]=nextC;x.w[j]=nextw;previous[j]=implied;
   }
   const double b=u(k*NU+7);need(std::abs(b)<=l.progress_acceleration&&std::abs((b-prior_b)/h)<=l.progress_jerk,"candidate b/feedback jerk strict bound");
   for(int half=1;half<=2;++half){const double local=h*t+.002*half;
    const double s=origin.s+local*origin.r+.5*local*local*b,r=origin.r+local*b;finite(s);finite(r);
    need(s>=0&&s<=1&&r>=0&&r<=l.progress_speed,"candidate half progress strict domain");}
   const double s=x.s+h*x.r+.5*h*h*b,r=x.r+h*b;finite(s);finite(r);
   need(s>=0&&s<=1&&r>=0&&r<=l.progress_speed,"candidate recursive progress strict domain");x.s=s;x.r=r;prior_b=b;
  }
 }
 // Finite original-unit residual acceptance is NOT an exact infinite-time
 // zero-command continuation certificate. No snap-to-zero or projection.
 TerminalTailObservation tail;tail.exact_zero_command_progress_tail=true;
 for(int j=0;j<7;++j){tail.final_w[j]=x.w[j];tail.last_alpha[j]=u((N-1)*NU+j);
  if(tail.final_w[j]!=0||tail.last_alpha[j]!=0)tail.exact_zero_command_progress_tail=false;}
 tail.final_r=x.r;tail.last_b=u((N-1)*NU+7);
 if(tail.final_r!=0||tail.last_b!=0)tail.exact_zero_command_progress_tail=false;
 return tail; // Residuals retained. No infinite-time certificate required for data-only forward request.
}
}
void solveOnce(Outcome& out,const qp::QpOptions& options,CandidateOutcome& candidate){
 candidate.request_.reset(); // A repeated entry never leaves an active request.
 try{need(out.storage_&&candidate.solve_attempts_==0&&!out.storage_->solver_entry_consumed,"REENTRY_STOP_PREVIOUS_DATA_FORENSIC");
  auto& s=*out.storage_;s.solver_entry_consumed=true;++candidate.solve_attempts_;
  need(out.complete(),"incomplete full horizon cannot enter solver");const auto& p=s.problem;
  const double elapsed=std::chrono::duration<double>(std::chrono::steady_clock::now()-s.connection_started).count();
  candidate.timing_.mode=s.inputs.timing_mode;candidate.timing_.original_observer_age=s.inputs.observed_age_seconds;
  candidate.timing_.known_upstream_elapsed=s.inputs.known_upstream_elapsed_seconds;
  candidate.timing_.connection_and_solver_elapsed=elapsed;
  candidate.timing_.known_wall_age=s.inputs.observed_age_seconds+s.inputs.known_upstream_elapsed_seconds+elapsed;
  if(s.inputs.timing_mode==TimingMode::OnlineWallAge){
   need(std::isfinite(options.max_state_age_seconds)&&options.max_state_age_seconds>0&&options.max_state_age_seconds<=h,"online original-age policy within one feedback tick");
   s.problem.original_si.state_age_seconds=candidate.timing_.known_wall_age;
  }else s.problem.original_si.state_age_seconds=s.inputs.observed_age_seconds;
  // Offline keeps original historical age. Real elapsed remains separate;
  // source runner must prove no simulation step/command mutation. No mode retry.
  ++candidate.solver_wrapper_entries_; // C++ QP API entry, NOT OSQP/internal calls.
  candidate.result_=qp::solveQpCertified(p.original_si,options,p.seed,p.psd_factor);
  candidate.timing_.connection_and_solver_elapsed=std::chrono::duration<double>(std::chrono::steady_clock::now()-s.connection_started).count();
  candidate.timing_.known_wall_age=s.inputs.observed_age_seconds+s.inputs.known_upstream_elapsed_seconds+candidate.timing_.connection_and_solver_elapsed;
  need(candidate.result_.status==qp::QpStatus::Solved,"only SOLVED admits candidate; native status retained");
  const auto& u=candidate.result_.velocity;need(u.size()==NZ&&u.allFinite(),"solver original control vector finite160 required");
  Eigen::VectorXd ax=p.original_si.constraints*u;need(ax.allFinite(),"candidate original SI row evaluation");
  candidate.violations_.reserve(p.rows.size());bool accepted=true;
  for(int r=0;r<ax.size();++r){const double v=std::max({0.,p.original_si.lower(r)-ax(r),ax(r)-p.original_si.upper(r)});finite(v);
   candidate.violations_.push_back(v);if(v>options.acceptance_tolerance)accepted=false;}
  need(accepted,"independent original SI row gate failed; no epsilon change");
  candidate.timing_.connection_and_solver_elapsed=std::chrono::duration<double>(std::chrono::steady_clock::now()-s.connection_started).count();
  candidate.timing_.known_wall_age=s.inputs.observed_age_seconds+s.inputs.known_upstream_elapsed_seconds+candidate.timing_.connection_and_solver_elapsed;
  candidate.timing_.known_current_age_within_policy=candidate.timing_.known_wall_age<=options.max_state_age_seconds;
  if(s.inputs.timing_mode==TimingMode::OnlineWallAge)need(candidate.timing_.known_current_age_within_policy,"candidate stale after solve; no timestamp refresh");
  const auto& raw=s.original.originalNormalization().originalForecast();const auto& context=raw.actualContext();
  live::JointVector alpha{};for(int j=0;j<7;++j)alpha[j]=u(j);
  candidate.preview_=live::first4msRequest(context,alpha,u(7)); // Always accepted C/w, never measuredv+ha.
  candidate.tail_=strictRoundedCommandAndProgress(context,s.inputs.limits,u);
  CandidateForwardRequest request;request.actual_initial_at_completed_boundary=context.actualInitial();request.boundary=context.boundary();
  request.observation_id=context.observationId();request.transaction_id=context.transactionId();request.nominal_invocation_sha256=raw.invocationSha256();
  request.candidate_controls.reserve(N);for(int k=0;k<N;++k){live::NominalControl c;for(int j=0;j<7;++j)c.alpha[j]=u(k*NU+j);c.b=u(k*NU+7);request.candidate_controls.push_back(c);}
  candidate.forensic_request_=request;candidate.request_=std::move(request);candidate.stop_reason_="CANDIDATE_FORWARD_REQUIRED_NO_EXECUTION_PERMISSION";
 }catch(const std::exception& e){candidate.stop_reason_=e.what();}catch(...){candidate.stop_reason_="NONSTANDARD_SOLVER_OR_CANDIDATE_GATE_FAILURE";}
 // No retry, projection, shortening, altered rows, new nominal, Model/plant call.
}
Eigen::VectorXd shiftControlGuess(const Eigen::VectorXd& old,live::Count elapsed){
 need(old.size()==NZ&&old.allFinite()&&elapsed<T,"unusable control-only warm guess");
 Eigen::VectorXd guess=Eigen::VectorXd::Zero(NZ);live::Count begin=elapsed;
 for(int k=0;k<N;++k){live::Count end=begin+lattice[k],oldbegin=0;
  for(int j=0;j<N;++j){const live::Count oldend=oldbegin+lattice[j];const auto left=std::max(begin,oldbegin),right=std::min(end,oldend);
   if(right>left)guess.segment(k*NU,NU)+=(static_cast<double>(right-left)/lattice[k])*old.segment(j*NU,NU);oldbegin=oldend;}
  begin=end;
 }
 need(guess.allFinite(),"nonfinite warm control guess");return guess; // Tail guess0; no states/permissions/validation.
}
} // namespace phase5_active_session_qp_v1
