#include "jerk_interior67_v1.hpp"
#include "contract_interior66_v1.hpp"
#include "physical_braking_nominal65.hpp"
#include "roundoff_command64.hpp"
#include "bounded_progress_seed.hpp"
#include "progress_interior_guard.hpp"
#include "integrated_horizon_qp.hpp"
#include "fine_timing.hpp"
#include "stop_objective_factors.hpp"
#include "current_alpha_trust.hpp"
static_assert(phase5_roundoff_command64_v1::conservative_inventory+phase5_physical_braking65_v1::baseline_slots+phase5_physical_braking65_v1::additional_hot_cap_slots+phase5_physical_braking65_v1::live_input_flag_copies+phase5_physical_braking65_v1::additional_profile_numbers+4==744998&&744998<745000,"old744994 plus two66/two67 Input flag copies; original745000 unchanged");
static_assert(744998-144*144+64==724326&&724326<745000,"before hint and codec: one local KKT matrix absent, at most64 new sequential scalar slots; old48 retained diagnostics not discounted; not an RSS proof");
#include <openssl/evp.h>
#include <cstring>
#include "linear_box_screen.hpp"
#include <Eigen/Cholesky>
#include <algorithm>
#include <cmath>
#include <chrono>
#include <limits>
#include <set>
#include <stdexcept>
#include <utility>
#include <sstream>
#include <iomanip>

namespace phase5_active_session_qp_v1 {
namespace {
constexpr double h=.004;
constexpr int max_factor_rows=909,max_qp_rows=20000,max_geometry_rows=1600;
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
 for(double v:{w.tracking,w.physical_velocity,w.posture,w.command_acceleration,w.command_jerk,w.progress_acceleration,w.progress_jerk,w.progress_reward,w.terminal_progress,w.command_velocity,w.progress_velocity})
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
  int start=trace.factor_rows_written;need(start+m.rows()<=problem.F.rows()&&problem.F.rows()<=max_factor_rows,"inline factor row cap");
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
  const int factor_rows=inputs.stop_mode?909:741;
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
  if(inputs.reserve_separate_numeric)inputs.reserve_separate_numeric(trace.planned_numeric_slots);
  trace.stage="ALLOCATE_SEPARATE_INLINE_QP";
  auto& p=problem;auto& q=p.original_si;
  q.hessian=Eigen::MatrixXd::Zero(NZ,NZ);q.gradient=Eigen::VectorXd::Zero(NZ);
  q.constraints=Eigen::MatrixXd::Zero(qrows,NZ);q.lower=Eigen::VectorXd::Zero(qrows);q.upper=Eigen::VectorXd::Zero(qrows);
  q.state_age_seconds=inputs.observed_age_seconds;p.F=Eigen::MatrixXd::Zero(factor_rows,NZ);p.f=Eigen::VectorXd::Zero(factor_rows);
  p.seed=Eigen::VectorXd::Zero(NZ);p.rows.reserve(qrows);p.terms.reserve(144);p.retained_task_prefix.reserve(N+1);
  const auto& l=inputs.limits;const auto& w=inputs.weights;const auto& ranges=ctx.ranges();
  trace.stage="ACTUAL_NOMINAL_TASK_AND_OBJECTIVE";
  if(inputs.stop_mode)need(w.progress_reward==0&&w.terminal_progress==0&&w.physical_velocity==100&&w.command_velocity==1000&&w.progress_velocity==1000,"explicit fixed stop objective mode");else need(w.command_velocity==0&&w.progress_velocity==0,"active original741 factors unchanged");
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
   if(inputs.stop_mode){const auto stop_rows=phase5_stop_objective_factors_v1::fromBoundary(z.M,z.c);factor(stop_rows.matrix.topRows(7),stop_rows.offset.head(7),w.command_velocity*duration,"stop/accepted_command_w/node/"+std::to_string(k));factor(stop_rows.matrix.row(7),stop_rows.offset.tail(1),w.progress_velocity*duration,"stop/progress_r/node/"+std::to_string(k));}
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
const Limits& Outcome::retainedLimits() const{need(static_cast<bool>(storage_),"moved integration owner");return storage_->inputs.limits;}
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
  // Structured equality reduction and equivalent positive row/variable scaling; original SI arrays and every
  // final original-row/rounded-history gate stay unchanged. Fresh workspace.
  const auto screened=screenLinearInputBoxes(p);
  candidate.retained_solver_rows_=screened.retained_rows;candidate.screening_environment_={static_cast<unsigned>(screened.rounding_mode),screened.x87_control,screened.mxcsr};candidate.omitted_solver_rows_.reserve(screened.omitted_rows.size());
  for(const auto& row:screened.omitted_rows){candidate.omitted_solver_rows_.push_back(row.original_row);std::ostringstream interval;interval<<std::hexfloat<<std::setprecision(std::numeric_limits<long double>::max_digits10)<<row.lower_bound<<" "<<row.upper_bound;candidate.omitted_solver_intervals_.push_back(interval.str());}
  // Analytic terminal equality elimination in original IEEE coefficients.
  // Mathematical U=p+Z*Y; all floating products/reconstruction are retained,
  // and every original SI row and strict rounded-history gate remains required.
  candidate.reduction_.emplace();auto& transform=*candidate.reduction_;
  constexpr int reduced_n=18*NU;
  transform.offset=Eigen::VectorXd::Zero(NZ);transform.transform=Eigen::MatrixXd::Zero(NZ,reduced_n);transform.transform.topRows(reduced_n).setIdentity();
  transform.equalities=Eigen::MatrixXd::Zero(16,NZ);transform.equality_rhs=Eigen::VectorXd::Zero(16);
  auto find=[&](const std::string& label){int found=-1;for(int r=0;r<static_cast<int>(p.rows.size());++r)if(p.rows[r].label==label){need(found<0,"duplicate terminal equality label");found=r;}need(found>=0,"missing terminal equality");need(p.original_si.lower(found)==p.original_si.upper(found),"terminal row must be original equality");return found;};
  for(int j=0;j<NU;++j){const auto label=j<7?"terminal/alpha/"+std::to_string(j):"terminal/b";const int r=find(label),col=(N-1)*NU+j;need(p.original_si.lower(r)==0,"terminal final input must be exact zero");
   for(int k=0;k<NZ;++k)need(p.original_si.constraints(r,k)==(k==col?1.:0.),"terminal final input exact unit row required");
   transform.eliminated_rows.push_back(r);transform.equalities.row(j)=p.original_si.constraints.row(r);transform.equality_rhs(j)=p.original_si.lower(r);}
  for(int j=0;j<NU;++j){const auto label=j<7?"terminal/command_w/"+std::to_string(j):"terminal/progress_r";const int r=find(label),pivot=(N-2)*NU+j;const auto row=p.original_si.constraints.row(r);
   for(int k=0;k<NZ;++k)need(std::isfinite(row(k))&&(k%NU==j||row(k)==0),"terminal equality must have only its own control channel");
   need(row(pivot)!=0&&std::isfinite(p.original_si.lower(r)),"finite nonzero terminal pivot required");transform.offset(pivot)=p.original_si.lower(r)/row(pivot);
   for(int k=0;k<reduced_n;++k)transform.transform(pivot,k)=-row(k)/row(pivot);
   transform.eliminated_rows.push_back(r);transform.equalities.row(NU+j)=row;transform.equality_rhs(NU+j)=p.original_si.lower(r);}
  need(transform.transform.allFinite()&&transform.offset.allFinite(),"finite analytic equality map/offset");
  transform.equality_origin_error=(transform.equalities*transform.offset-transform.equality_rhs).cwiseAbs().maxCoeff()/std::max(1.,transform.equality_rhs.cwiseAbs().maxCoeff());
  transform.equality_map_error=(transform.equalities*transform.transform).cwiseAbs().maxCoeff()/std::max(1.,transform.equalities.cwiseAbs().maxCoeff());
  need(transform.equality_origin_error<=1e-12&&transform.equality_map_error<=1e-12,"terminal equality numerical reconstruction check");
  std::set<int> eliminated(transform.eliminated_rows.begin(),transform.eliminated_rows.end());need(eliminated.size()==16,"all16 independent structured terminal equalities required");
  std::vector<std::string> labels;
  for(int r:screened.retained_rows)if(!eliminated.count(r)){transform.solver_rows.push_back(r);labels.push_back(p.rows[r].label);}
  candidate.retained_solver_rows_=transform.solver_rows;
  transform.stored_numeric_slots=live::checkedAdd(live::checkedMultiply(transform.solver_rows.size(),reduced_n),live::checkedAdd(live::checkedMultiply(p.F.rows(),reduced_n),live::checkedAdd(NZ*reduced_n+reduced_n*reduced_n+16*NZ, NZ+5*reduced_n+16+2*transform.solver_rows.size())));
  need(transform.stored_numeric_slots<=2000000,"bounded reduction stored numeric payload before dense transformation; temporary storage bounded by external AS");
  transform.stage="STRUCTURE_VALIDATED_BUILD_REDUCED_QP";
  qp::QpProblem reduced;reduced.state_age_seconds=screened.solver_problem.state_age_seconds;reduced.hessian=transform.transform.transpose()*p.original_si.hessian*transform.transform;
  reduced.gradient=transform.transform.transpose()*(p.original_si.gradient+p.original_si.hessian*transform.offset);
  reduced.constraints.resize(transform.solver_rows.size(),reduced_n);reduced.lower.resize(transform.solver_rows.size());reduced.upper.resize(transform.solver_rows.size());
  for(int i=0;i<static_cast<int>(transform.solver_rows.size());++i){int r=transform.solver_rows[i];const double shift=p.original_si.constraints.row(r).dot(transform.offset);reduced.constraints.row(i)=p.original_si.constraints.row(r)*transform.transform;reduced.lower(i)=p.original_si.lower(r)-shift;reduced.upper(i)=p.original_si.upper(r)-shift;}
  transform.lower=reduced.lower;transform.upper=reduced.upper;transform.hessian=reduced.hessian;transform.gradient=reduced.gradient;transform.constraints=reduced.constraints;transform.factor=p.F*transform.transform;transform.seed=p.seed.head(reduced_n);
  transform.constant=p.constant+p.original_si.gradient.dot(transform.offset)+.5*transform.offset.dot(p.original_si.hessian*transform.offset);
  transform.factor_consistency_error=(transform.factor.transpose()*transform.factor-reduced.hessian).cwiseAbs().maxCoeff()/std::max(1.,reduced.hessian.cwiseAbs().maxCoeff());
  need(reduced.hessian.allFinite()&&reduced.gradient.allFinite()&&reduced.constraints.allFinite()&&reduced.lower.allFinite()&&reduced.upper.allFinite()&&transform.factor.allFinite()&&std::isfinite(transform.constant)&&transform.factor_consistency_error<=1e-12,"reduced finite/factor certificate validation");
  Eigen::VectorXd scale(reduced_n);for(int j=0;j<reduced_n;++j){need(std::isfinite(reduced.hessian(j,j))&&reduced.hessian(j,j)>0,"positive reduced diagonal");scale(j)=1/std::sqrt(reduced.hessian(j,j));need(std::isfinite(scale(j))&&scale(j)>0,"finite positive reduced Jacobi scale");}
  transform.variable_scale=scale;
  // Positive bounded row equilibration: normalize large rows downward, never
  // magnify almost-zero cancellation rows after equality elimination. Fresh
  // certified API has no workspace auto row scaling; original SI final gate.
  transform.stored_numeric_slots=live::checkedAdd(transform.stored_numeric_slots,live::checkedAdd(live::checkedMultiply(reduced.constraints.rows(),reduced_n+3),live::checkedAdd(reduced_n*reduced_n+7*reduced_n+transform.solver_rows.size(),live::checkedMultiply(p.F.rows(),reduced_n))));
  need(transform.stored_numeric_slots<=4000000,"scaled stored numeric payload cap before allocation");
  qp::QpProblem scaled=reduced;scaled.hessian=scale.asDiagonal()*reduced.hessian*scale.asDiagonal();scaled.gradient=scale.asDiagonal()*reduced.gradient;scaled.constraints=reduced.constraints*scale.asDiagonal();
  transform.row_scale=Eigen::VectorXd::Ones(scaled.constraints.rows());
  for(int r=0;r<scaled.constraints.rows();++r){const double norm=scaled.constraints.row(r).cwiseAbs().maxCoeff();need(std::isfinite(norm),"finite bounded scale row norm");const double multiplier=1/std::max(1.,norm);need(std::isfinite(multiplier)&&multiplier>0&&multiplier<=1,"positive downward-only row scale");transform.row_scale(r)=multiplier;scaled.constraints.row(r)*=multiplier;scaled.lower(r)*=multiplier;scaled.upper(r)*=multiplier;}
  transform.solver_hessian=scaled.hessian;transform.solver_gradient=scaled.gradient;transform.solver_constraints=scaled.constraints;transform.solver_lower=scaled.lower;transform.solver_upper=scaled.upper;transform.solver_factor=transform.factor*scale.asDiagonal();transform.solver_seed=transform.seed.cwiseQuotient(scale);
  need(transform.stored_numeric_slots<=4000000&&scaled.hessian.allFinite()&&scaled.gradient.allFinite()&&scaled.constraints.allFinite()&&scaled.lower.allFinite()&&scaled.upper.allFinite()&&transform.solver_factor.allFinite()&&transform.solver_seed.allFinite(),"bounded finite explicitly scaled solver problem");
  transform.scaled_factor_consistency_error=(transform.solver_factor.transpose()*transform.solver_factor-scaled.hessian).cwiseAbs().maxCoeff()/std::max(1.,scaled.hessian.cwiseAbs().maxCoeff());
  need(transform.scaled_factor_consistency_error<=1e-12,"scaled factor consistency certificate");
  transform.numerical_validation_passed=true;transform.stage="VALIDATED_REDUCED_AND_BOUNDED_SCALED_QP_BEFORE_SOLVER";
  transform.forensic_iterates.primal=Eigen::VectorXd::Zero(reduced_n);transform.forensic_iterates.dual=Eigen::VectorXd::Zero(transform.solver_rows.size()); // owned placeholder only until present=true
  const Eigen::SparseMatrix<double> certificate=transform.solver_factor.sparseView();
  ++candidate.solver_wrapper_entries_;
  candidate.result_=phase5_active_solver_forensics_v1::solveCertified(scaled,options,transform.solver_seed,certificate,transform.forensic_iterates);
  transform.stage="QP_RETURNED_EXPLICITLY_SCALED_COORDINATES";transform.solver_coordinates=candidate.result_.velocity;
  if(candidate.result_.velocity.size()){need(candidate.result_.velocity.size()==reduced_n&&candidate.result_.velocity.allFinite(),"solver scaled coordinate vector finite144 required");transform.reduced_coordinates=scale.asDiagonal()*transform.solver_coordinates;candidate.result_.velocity=transform.offset+transform.transform*transform.reduced_coordinates;need(candidate.result_.velocity.allFinite(),"finite reconstructed original controls160 required");}
  const int backend_row=candidate.result_.maximum_violation_row;
  if(backend_row>=0){need(backend_row<static_cast<int>(transform.solver_rows.size()),"backend violation row outside reduced roster");candidate.backend_mapped_original_violation_row_=transform.solver_rows[backend_row];}
  candidate.timing_.connection_and_solver_elapsed=std::chrono::duration<double>(std::chrono::steady_clock::now()-s.connection_started).count();
  candidate.timing_.known_wall_age=s.inputs.observed_age_seconds+s.inputs.known_upstream_elapsed_seconds+candidate.timing_.connection_and_solver_elapsed;
  need(candidate.result_.status==qp::QpStatus::Solved,"only SOLVED admits candidate; native status retained");
  const auto& u=candidate.result_.velocity;need(u.size()==NZ&&u.allFinite(),"solver original control vector finite160 required");
  Eigen::VectorXd ax=p.original_si.constraints*u;need(ax.allFinite(),"candidate original SI row evaluation");
  candidate.violations_.reserve(p.rows.size());bool accepted=true;
  for(int r=0;r<ax.size();++r){const double v=std::max({0.,p.original_si.lower(r)-ax(r),ax(r)-p.original_si.upper(r)});finite(v);
   if(v>candidate.full_original_maximum_violation_){candidate.full_original_maximum_violation_=v;candidate.full_original_maximum_violation_row_=r;}
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
namespace {
std::string numericProblemDigest(const qp::QpProblem& p,const Eigen::MatrixXd* factor,const Eigen::VectorXd* offset,const double* constant){
 std::unique_ptr<EVP_MD_CTX,decltype(&EVP_MD_CTX_free)> hash(EVP_MD_CTX_new(),EVP_MD_CTX_free);need(hash&&EVP_DigestInit_ex(hash.get(),EVP_sha256(),nullptr)==1,"numeric binding hash init");
 auto integer=[&](std::uint64_t value){unsigned char b[8];for(int j=0;j<8;++j)b[j]=(value>>(8*j))&255;need(EVP_DigestUpdate(hash.get(),b,8)==1,"numeric binding shape hash");};auto number=[&](double value){std::uint64_t u;static_assert(sizeof(double)==8,"binary64 binding");std::memcpy(&u,&value,8);integer(u);};auto matrix=[&](const Eigen::MatrixXd& m){integer(m.rows());integer(m.cols());for(int r=0;r<m.rows();++r)for(int c=0;c<m.cols();++c)number(m(r,c));};auto vector=[&](const Eigen::VectorXd& v){integer(v.size());for(double x:v)number(x);};
 matrix(p.hessian);vector(p.gradient);matrix(p.constraints);vector(p.lower);vector(p.upper);if(factor){need(offset&&constant,"fulloriginal factor/constant binding");matrix(*factor);vector(*offset);number(*constant);}unsigned char b[32];unsigned n=0;need(EVP_DigestFinal_ex(hash.get(),b,&n)==1&&n==32,"numeric binding hash final");std::string out;const char* hex="0123456789abcdef";for(unsigned char v:b){out.push_back(hex[v>>4]);out.push_back(hex[v&15]);}return out;
}
}
void solveOnceWithNumericGuess(Outcome& out,const qp::QpOptions& options,const NumericOptimizerGuess& guess,CandidateOutcome& candidate){
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
  // Structured equality reduction and equivalent positive row/variable scaling; original SI arrays and every
  // final original-row/rounded-history gate stay unchanged. Fresh workspace.
  const auto screened=screenLinearInputBoxes(p);
  candidate.retained_solver_rows_=screened.retained_rows;candidate.screening_environment_={static_cast<unsigned>(screened.rounding_mode),screened.x87_control,screened.mxcsr};candidate.omitted_solver_rows_.reserve(screened.omitted_rows.size());
  for(const auto& row:screened.omitted_rows){candidate.omitted_solver_rows_.push_back(row.original_row);std::ostringstream interval;interval<<std::hexfloat<<std::setprecision(std::numeric_limits<long double>::max_digits10)<<row.lower_bound<<" "<<row.upper_bound;candidate.omitted_solver_intervals_.push_back(interval.str());}
  // Analytic terminal equality elimination in original IEEE coefficients.
  // Mathematical U=p+Z*Y; all floating products/reconstruction are retained,
  // and every original SI row and strict rounded-history gate remains required.
  candidate.reduction_.emplace();auto& transform=*candidate.reduction_;
  constexpr int reduced_n=18*NU;
  transform.offset=Eigen::VectorXd::Zero(NZ);transform.transform=Eigen::MatrixXd::Zero(NZ,reduced_n);transform.transform.topRows(reduced_n).setIdentity();
  transform.equalities=Eigen::MatrixXd::Zero(16,NZ);transform.equality_rhs=Eigen::VectorXd::Zero(16);
  auto find=[&](const std::string& label){int found=-1;for(int r=0;r<static_cast<int>(p.rows.size());++r)if(p.rows[r].label==label){need(found<0,"duplicate terminal equality label");found=r;}need(found>=0,"missing terminal equality");need(p.original_si.lower(found)==p.original_si.upper(found),"terminal row must be original equality");return found;};
  for(int j=0;j<NU;++j){const auto label=j<7?"terminal/alpha/"+std::to_string(j):"terminal/b";const int r=find(label),col=(N-1)*NU+j;need(p.original_si.lower(r)==0,"terminal final input must be exact zero");
   for(int k=0;k<NZ;++k)need(p.original_si.constraints(r,k)==(k==col?1.:0.),"terminal final input exact unit row required");
   transform.eliminated_rows.push_back(r);transform.equalities.row(j)=p.original_si.constraints.row(r);transform.equality_rhs(j)=p.original_si.lower(r);}
  for(int j=0;j<NU;++j){const auto label=j<7?"terminal/command_w/"+std::to_string(j):"terminal/progress_r";const int r=find(label),pivot=(N-2)*NU+j;const auto row=p.original_si.constraints.row(r);
   for(int k=0;k<NZ;++k)need(std::isfinite(row(k))&&(k%NU==j||row(k)==0),"terminal equality must have only its own control channel");
   need(row(pivot)!=0&&std::isfinite(p.original_si.lower(r)),"finite nonzero terminal pivot required");transform.offset(pivot)=p.original_si.lower(r)/row(pivot);
   for(int k=0;k<reduced_n;++k)transform.transform(pivot,k)=-row(k)/row(pivot);
   transform.eliminated_rows.push_back(r);transform.equalities.row(NU+j)=row;transform.equality_rhs(NU+j)=p.original_si.lower(r);}
  need(transform.transform.allFinite()&&transform.offset.allFinite(),"finite analytic equality map/offset");
  transform.equality_origin_error=(transform.equalities*transform.offset-transform.equality_rhs).cwiseAbs().maxCoeff()/std::max(1.,transform.equality_rhs.cwiseAbs().maxCoeff());
  transform.equality_map_error=(transform.equalities*transform.transform).cwiseAbs().maxCoeff()/std::max(1.,transform.equalities.cwiseAbs().maxCoeff());
  need(transform.equality_origin_error<=1e-12&&transform.equality_map_error<=1e-12,"terminal equality numerical reconstruction check");
  std::set<int> eliminated(transform.eliminated_rows.begin(),transform.eliminated_rows.end());need(eliminated.size()==16,"all16 independent structured terminal equalities required");
  std::vector<std::string> labels;
  for(int r:screened.retained_rows)if(!eliminated.count(r)){transform.solver_rows.push_back(r);labels.push_back(p.rows[r].label);}
  candidate.retained_solver_rows_=transform.solver_rows;
  transform.stored_numeric_slots=live::checkedAdd(live::checkedMultiply(transform.solver_rows.size(),reduced_n),live::checkedAdd(live::checkedMultiply(p.F.rows(),reduced_n),live::checkedAdd(NZ*reduced_n+reduced_n*reduced_n+16*NZ, NZ+5*reduced_n+16+2*transform.solver_rows.size())));
  need(transform.stored_numeric_slots<=2000000,"bounded reduction stored numeric payload before dense transformation; temporary storage bounded by external AS");
  transform.stage="STRUCTURE_VALIDATED_BUILD_REDUCED_QP";
  qp::QpProblem reduced;reduced.state_age_seconds=screened.solver_problem.state_age_seconds;reduced.hessian=transform.transform.transpose()*p.original_si.hessian*transform.transform;
  reduced.gradient=transform.transform.transpose()*(p.original_si.gradient+p.original_si.hessian*transform.offset);
  reduced.constraints.resize(transform.solver_rows.size(),reduced_n);reduced.lower.resize(transform.solver_rows.size());reduced.upper.resize(transform.solver_rows.size());
  for(int i=0;i<static_cast<int>(transform.solver_rows.size());++i){int r=transform.solver_rows[i];const double shift=p.original_si.constraints.row(r).dot(transform.offset);reduced.constraints.row(i)=p.original_si.constraints.row(r)*transform.transform;reduced.lower(i)=p.original_si.lower(r)-shift;reduced.upper(i)=p.original_si.upper(r)-shift;}
  transform.lower=reduced.lower;transform.upper=reduced.upper;transform.hessian=reduced.hessian;transform.gradient=reduced.gradient;transform.constraints=reduced.constraints;transform.factor=p.F*transform.transform;transform.seed=p.seed.head(reduced_n);
  transform.constant=p.constant+p.original_si.gradient.dot(transform.offset)+.5*transform.offset.dot(p.original_si.hessian*transform.offset);
  transform.factor_consistency_error=(transform.factor.transpose()*transform.factor-reduced.hessian).cwiseAbs().maxCoeff()/std::max(1.,reduced.hessian.cwiseAbs().maxCoeff());
  need(reduced.hessian.allFinite()&&reduced.gradient.allFinite()&&reduced.constraints.allFinite()&&reduced.lower.allFinite()&&reduced.upper.allFinite()&&transform.factor.allFinite()&&std::isfinite(transform.constant)&&transform.factor_consistency_error<=1e-12,"reduced finite/factor certificate validation");
  Eigen::VectorXd scale(reduced_n);for(int j=0;j<reduced_n;++j){need(std::isfinite(reduced.hessian(j,j))&&reduced.hessian(j,j)>0,"positive reduced diagonal");scale(j)=1/std::sqrt(reduced.hessian(j,j));need(std::isfinite(scale(j))&&scale(j)>0,"finite positive reduced Jacobi scale");}
  transform.variable_scale=scale;
  // Positive bounded row equilibration: normalize large rows downward, never
  // magnify almost-zero cancellation rows after equality elimination. Fresh
  // certified API has no workspace auto row scaling; original SI final gate.
  transform.stored_numeric_slots=live::checkedAdd(transform.stored_numeric_slots,live::checkedAdd(live::checkedMultiply(reduced.constraints.rows(),reduced_n+3),live::checkedAdd(reduced_n*reduced_n+7*reduced_n+transform.solver_rows.size(),live::checkedMultiply(p.F.rows(),reduced_n))));
  need(transform.stored_numeric_slots<=4000000,"scaled stored numeric payload cap before allocation");
  qp::QpProblem scaled=reduced;scaled.hessian=scale.asDiagonal()*reduced.hessian*scale.asDiagonal();scaled.gradient=scale.asDiagonal()*reduced.gradient;scaled.constraints=reduced.constraints*scale.asDiagonal();
  transform.row_scale=Eigen::VectorXd::Ones(scaled.constraints.rows());
  for(int r=0;r<scaled.constraints.rows();++r){const double norm=scaled.constraints.row(r).cwiseAbs().maxCoeff();need(std::isfinite(norm),"finite bounded scale row norm");const double multiplier=1/std::max(1.,norm);need(std::isfinite(multiplier)&&multiplier>0&&multiplier<=1,"positive downward-only row scale");transform.row_scale(r)=multiplier;scaled.constraints.row(r)*=multiplier;scaled.lower(r)*=multiplier;scaled.upper(r)*=multiplier;}
  transform.solver_hessian=scaled.hessian;transform.solver_gradient=scaled.gradient;transform.solver_constraints=scaled.constraints;transform.solver_lower=scaled.lower;transform.solver_upper=scaled.upper;transform.solver_factor=transform.factor*scale.asDiagonal();transform.solver_seed=transform.seed.cwiseQuotient(scale);
  need(transform.stored_numeric_slots<=4000000&&scaled.hessian.allFinite()&&scaled.gradient.allFinite()&&scaled.constraints.allFinite()&&scaled.lower.allFinite()&&scaled.upper.allFinite()&&transform.solver_factor.allFinite()&&transform.solver_seed.allFinite(),"bounded finite explicitly scaled solver problem");
  transform.scaled_factor_consistency_error=(transform.solver_factor.transpose()*transform.solver_factor-scaled.hessian).cwiseAbs().maxCoeff()/std::max(1.,scaled.hessian.cwiseAbs().maxCoeff());
  need(transform.scaled_factor_consistency_error<=1e-12,"scaled factor consistency certificate");
  need(s.inputs.timing_mode==TimingMode::OfflineFrozenSimulationBoundary,"external optimizer guess is offline development only");
  const auto& ctx=s.original.originalNormalization().originalForecast().actualContext();auto bit=[](double a,double b){return std::memcmp(&a,&b,sizeof(double))==0;};const auto& actual=ctx.actualInitial();
  for(int j=0;j<7;++j){need(bit(actual.q[j],guess.actual_initial.q[j])&&bit(actual.v[j],guess.actual_initial.v[j])&&bit(actual.C[j],guess.actual_initial.C[j])&&bit(actual.w[j],guess.actual_initial.w[j])&&bit(ctx.previousAlpha()[j],guess.previous_alpha[j]),"external guess actual/command history bitwise mismatch");}need(bit(actual.s,guess.actual_initial.s)&&bit(actual.r,guess.actual_initial.r)&&bit(ctx.previousB(),guess.previous_b),"external guess progresshistory mismatch");
  need(guess.original_problem_sha256==numericProblemDigest(p.original_si,&p.F,&p.f,&p.constant)&&guess.transformed_problem_sha256==numericProblemDigest(scaled,nullptr,nullptr,nullptr),"external guess fulloriginal/scaledmatrix bitwise binding mismatch");need(guess.solver_coordinates.size()==reduced_n&&guess.solver_coordinates.allFinite(),"finite144 optimizer-only guess required");transform.solver_seed=guess.solver_coordinates;
  transform.numerical_validation_passed=true;transform.stage="VALIDATED_REDUCED_AND_BOUNDED_SCALED_QP_BEFORE_SOLVER";
  transform.forensic_iterates.primal=Eigen::VectorXd::Zero(reduced_n);transform.forensic_iterates.dual=Eigen::VectorXd::Zero(transform.solver_rows.size()); // owned placeholder only until present=true
  const Eigen::SparseMatrix<double> certificate=transform.solver_factor.sparseView();
  ++candidate.solver_wrapper_entries_;
  candidate.result_=phase5_active_solver_forensics_v1::solveCertified(scaled,options,transform.solver_seed,certificate,transform.forensic_iterates);
  transform.stage="QP_RETURNED_EXPLICITLY_SCALED_COORDINATES";transform.solver_coordinates=candidate.result_.velocity;
  if(candidate.result_.velocity.size()){need(candidate.result_.velocity.size()==reduced_n&&candidate.result_.velocity.allFinite(),"solver scaled coordinate vector finite144 required");transform.reduced_coordinates=scale.asDiagonal()*transform.solver_coordinates;candidate.result_.velocity=transform.offset+transform.transform*transform.reduced_coordinates;need(candidate.result_.velocity.allFinite(),"finite reconstructed original controls160 required");}
  const int backend_row=candidate.result_.maximum_violation_row;
  if(backend_row>=0){need(backend_row<static_cast<int>(transform.solver_rows.size()),"backend violation row outside reduced roster");candidate.backend_mapped_original_violation_row_=transform.solver_rows[backend_row];}
  candidate.timing_.connection_and_solver_elapsed=std::chrono::duration<double>(std::chrono::steady_clock::now()-s.connection_started).count();
  candidate.timing_.known_wall_age=s.inputs.observed_age_seconds+s.inputs.known_upstream_elapsed_seconds+candidate.timing_.connection_and_solver_elapsed;
  need(candidate.result_.status==qp::QpStatus::Solved,"only SOLVED admits candidate; native status retained");
  const auto& u=candidate.result_.velocity;need(u.size()==NZ&&u.allFinite(),"solver original control vector finite160 required");
  Eigen::VectorXd ax=p.original_si.constraints*u;need(ax.allFinite(),"candidate original SI row evaluation");
  candidate.violations_.reserve(p.rows.size());bool accepted=true;
  for(int r=0;r<ax.size();++r){const double v=std::max({0.,p.original_si.lower(r)-ax(r),ax(r)-p.original_si.upper(r)});finite(v);
   if(v>candidate.full_original_maximum_violation_){candidate.full_original_maximum_violation_=v;candidate.full_original_maximum_violation_row_=r;}
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
void solveOnceWithPrimalDualNumericGuess(Outcome& out,const qp::QpOptions& options,const NumericOptimizerGuess& guess,CandidateOutcome& candidate){
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
  // Structured equality reduction and equivalent positive row/variable scaling; original SI arrays and every
  // final original-row/rounded-history gate stay unchanged. Fresh workspace.
  const auto screened=screenLinearInputBoxes(p);
  candidate.retained_solver_rows_=screened.retained_rows;candidate.screening_environment_={static_cast<unsigned>(screened.rounding_mode),screened.x87_control,screened.mxcsr};candidate.omitted_solver_rows_.reserve(screened.omitted_rows.size());
  for(const auto& row:screened.omitted_rows){candidate.omitted_solver_rows_.push_back(row.original_row);std::ostringstream interval;interval<<std::hexfloat<<std::setprecision(std::numeric_limits<long double>::max_digits10)<<row.lower_bound<<" "<<row.upper_bound;candidate.omitted_solver_intervals_.push_back(interval.str());}
  // Analytic terminal equality elimination in original IEEE coefficients.
  // Mathematical U=p+Z*Y; all floating products/reconstruction are retained,
  // and every original SI row and strict rounded-history gate remains required.
  candidate.reduction_.emplace();auto& transform=*candidate.reduction_;
  constexpr int reduced_n=18*NU;
  transform.offset=Eigen::VectorXd::Zero(NZ);transform.transform=Eigen::MatrixXd::Zero(NZ,reduced_n);transform.transform.topRows(reduced_n).setIdentity();
  transform.equalities=Eigen::MatrixXd::Zero(16,NZ);transform.equality_rhs=Eigen::VectorXd::Zero(16);
  auto find=[&](const std::string& label){int found=-1;for(int r=0;r<static_cast<int>(p.rows.size());++r)if(p.rows[r].label==label){need(found<0,"duplicate terminal equality label");found=r;}need(found>=0,"missing terminal equality");need(p.original_si.lower(found)==p.original_si.upper(found),"terminal row must be original equality");return found;};
  for(int j=0;j<NU;++j){const auto label=j<7?"terminal/alpha/"+std::to_string(j):"terminal/b";const int r=find(label),col=(N-1)*NU+j;need(p.original_si.lower(r)==0,"terminal final input must be exact zero");
   for(int k=0;k<NZ;++k)need(p.original_si.constraints(r,k)==(k==col?1.:0.),"terminal final input exact unit row required");
   transform.eliminated_rows.push_back(r);transform.equalities.row(j)=p.original_si.constraints.row(r);transform.equality_rhs(j)=p.original_si.lower(r);}
  for(int j=0;j<NU;++j){const auto label=j<7?"terminal/command_w/"+std::to_string(j):"terminal/progress_r";const int r=find(label),pivot=(N-2)*NU+j;const auto row=p.original_si.constraints.row(r);
   for(int k=0;k<NZ;++k)need(std::isfinite(row(k))&&(k%NU==j||row(k)==0),"terminal equality must have only its own control channel");
   need(row(pivot)!=0&&std::isfinite(p.original_si.lower(r)),"finite nonzero terminal pivot required");transform.offset(pivot)=p.original_si.lower(r)/row(pivot);
   for(int k=0;k<reduced_n;++k)transform.transform(pivot,k)=-row(k)/row(pivot);
   transform.eliminated_rows.push_back(r);transform.equalities.row(NU+j)=row;transform.equality_rhs(NU+j)=p.original_si.lower(r);}
  need(transform.transform.allFinite()&&transform.offset.allFinite(),"finite analytic equality map/offset");
  transform.equality_origin_error=(transform.equalities*transform.offset-transform.equality_rhs).cwiseAbs().maxCoeff()/std::max(1.,transform.equality_rhs.cwiseAbs().maxCoeff());
  transform.equality_map_error=(transform.equalities*transform.transform).cwiseAbs().maxCoeff()/std::max(1.,transform.equalities.cwiseAbs().maxCoeff());
  need(transform.equality_origin_error<=1e-12&&transform.equality_map_error<=1e-12,"terminal equality numerical reconstruction check");
  std::set<int> eliminated(transform.eliminated_rows.begin(),transform.eliminated_rows.end());need(eliminated.size()==16,"all16 independent structured terminal equalities required");
  std::vector<std::string> labels;
  for(int r:screened.retained_rows)if(!eliminated.count(r)){transform.solver_rows.push_back(r);labels.push_back(p.rows[r].label);}
  candidate.retained_solver_rows_=transform.solver_rows;
  transform.stored_numeric_slots=live::checkedAdd(live::checkedMultiply(transform.solver_rows.size(),reduced_n),live::checkedAdd(live::checkedMultiply(p.F.rows(),reduced_n),live::checkedAdd(NZ*reduced_n+reduced_n*reduced_n+16*NZ, NZ+5*reduced_n+16+2*transform.solver_rows.size())));
  need(transform.stored_numeric_slots<=2000000,"bounded reduction stored numeric payload before dense transformation; temporary storage bounded by external AS");
  transform.stage="STRUCTURE_VALIDATED_BUILD_REDUCED_QP";
  qp::QpProblem reduced;reduced.state_age_seconds=screened.solver_problem.state_age_seconds;reduced.hessian=transform.transform.transpose()*p.original_si.hessian*transform.transform;
  reduced.gradient=transform.transform.transpose()*(p.original_si.gradient+p.original_si.hessian*transform.offset);
  reduced.constraints.resize(transform.solver_rows.size(),reduced_n);reduced.lower.resize(transform.solver_rows.size());reduced.upper.resize(transform.solver_rows.size());
  for(int i=0;i<static_cast<int>(transform.solver_rows.size());++i){int r=transform.solver_rows[i];const double shift=p.original_si.constraints.row(r).dot(transform.offset);reduced.constraints.row(i)=p.original_si.constraints.row(r)*transform.transform;reduced.lower(i)=p.original_si.lower(r)-shift;reduced.upper(i)=p.original_si.upper(r)-shift;}
  transform.lower=reduced.lower;transform.upper=reduced.upper;transform.hessian=reduced.hessian;transform.gradient=reduced.gradient;transform.constraints=reduced.constraints;transform.factor=p.F*transform.transform;transform.seed=p.seed.head(reduced_n);
  transform.constant=p.constant+p.original_si.gradient.dot(transform.offset)+.5*transform.offset.dot(p.original_si.hessian*transform.offset);
  transform.factor_consistency_error=(transform.factor.transpose()*transform.factor-reduced.hessian).cwiseAbs().maxCoeff()/std::max(1.,reduced.hessian.cwiseAbs().maxCoeff());
  need(reduced.hessian.allFinite()&&reduced.gradient.allFinite()&&reduced.constraints.allFinite()&&reduced.lower.allFinite()&&reduced.upper.allFinite()&&transform.factor.allFinite()&&std::isfinite(transform.constant)&&transform.factor_consistency_error<=1e-12,"reduced finite/factor certificate validation");
  Eigen::VectorXd scale(reduced_n);for(int j=0;j<reduced_n;++j){need(std::isfinite(reduced.hessian(j,j))&&reduced.hessian(j,j)>0,"positive reduced diagonal");scale(j)=1/std::sqrt(reduced.hessian(j,j));need(std::isfinite(scale(j))&&scale(j)>0,"finite positive reduced Jacobi scale");}
  transform.variable_scale=scale;
  // Positive bounded row equilibration: normalize large rows downward, never
  // magnify almost-zero cancellation rows after equality elimination. Fresh
  // certified API has no workspace auto row scaling; original SI final gate.
  transform.stored_numeric_slots=live::checkedAdd(transform.stored_numeric_slots,live::checkedAdd(live::checkedMultiply(reduced.constraints.rows(),reduced_n+3),live::checkedAdd(reduced_n*reduced_n+7*reduced_n+transform.solver_rows.size(),live::checkedMultiply(p.F.rows(),reduced_n))));
  need(transform.stored_numeric_slots<=4000000,"scaled stored numeric payload cap before allocation");
  qp::QpProblem scaled=reduced;scaled.hessian=scale.asDiagonal()*reduced.hessian*scale.asDiagonal();scaled.gradient=scale.asDiagonal()*reduced.gradient;scaled.constraints=reduced.constraints*scale.asDiagonal();
  transform.row_scale=Eigen::VectorXd::Ones(scaled.constraints.rows());
  for(int r=0;r<scaled.constraints.rows();++r){const double norm=scaled.constraints.row(r).cwiseAbs().maxCoeff();need(std::isfinite(norm),"finite bounded scale row norm");const double multiplier=1/std::max(1.,norm);need(std::isfinite(multiplier)&&multiplier>0&&multiplier<=1,"positive downward-only row scale");transform.row_scale(r)=multiplier;scaled.constraints.row(r)*=multiplier;scaled.lower(r)*=multiplier;scaled.upper(r)*=multiplier;}
  transform.solver_hessian=scaled.hessian;transform.solver_gradient=scaled.gradient;transform.solver_constraints=scaled.constraints;transform.solver_lower=scaled.lower;transform.solver_upper=scaled.upper;transform.solver_factor=transform.factor*scale.asDiagonal();transform.solver_seed=transform.seed.cwiseQuotient(scale);
  need(transform.stored_numeric_slots<=4000000&&scaled.hessian.allFinite()&&scaled.gradient.allFinite()&&scaled.constraints.allFinite()&&scaled.lower.allFinite()&&scaled.upper.allFinite()&&transform.solver_factor.allFinite()&&transform.solver_seed.allFinite(),"bounded finite explicitly scaled solver problem");
  transform.scaled_factor_consistency_error=(transform.solver_factor.transpose()*transform.solver_factor-scaled.hessian).cwiseAbs().maxCoeff()/std::max(1.,scaled.hessian.cwiseAbs().maxCoeff());
  need(transform.scaled_factor_consistency_error<=1e-12,"scaled factor consistency certificate");
  need(s.inputs.timing_mode==TimingMode::OfflineFrozenSimulationBoundary,"external optimizer guess is offline development only");
  const auto& ctx=s.original.originalNormalization().originalForecast().actualContext();auto bit=[](double a,double b){return std::memcmp(&a,&b,sizeof(double))==0;};const auto& actual=ctx.actualInitial();
  for(int j=0;j<7;++j){need(bit(actual.q[j],guess.actual_initial.q[j])&&bit(actual.v[j],guess.actual_initial.v[j])&&bit(actual.C[j],guess.actual_initial.C[j])&&bit(actual.w[j],guess.actual_initial.w[j])&&bit(ctx.previousAlpha()[j],guess.previous_alpha[j]),"external guess actual/command history bitwise mismatch");}need(bit(actual.s,guess.actual_initial.s)&&bit(actual.r,guess.actual_initial.r)&&bit(ctx.previousB(),guess.previous_b),"external guess progresshistory mismatch");
  need(guess.original_problem_sha256==numericProblemDigest(p.original_si,&p.F,&p.f,&p.constant)&&guess.transformed_problem_sha256==numericProblemDigest(scaled,nullptr,nullptr,nullptr),"external guess fulloriginal/scaledmatrix bitwise binding mismatch");need(guess.solver_coordinates.size()==reduced_n&&guess.solver_coordinates.allFinite(),"finite144 optimizer-only guess required");transform.solver_seed=guess.solver_coordinates;need(guess.dual_coordinates.size()==scaled.lower.size()&&guess.dual_coordinates.allFinite(),"finite correctlybound externaldualguess");
  transform.numerical_validation_passed=true;transform.stage="VALIDATED_REDUCED_AND_BOUNDED_SCALED_QP_BEFORE_SOLVER";
  transform.forensic_iterates.primal=Eigen::VectorXd::Zero(reduced_n);transform.forensic_iterates.dual=Eigen::VectorXd::Zero(transform.solver_rows.size()); // owned placeholder only until present=true
  const Eigen::SparseMatrix<double> certificate=transform.solver_factor.sparseView();
  ++candidate.solver_wrapper_entries_;
  candidate.result_=phase5_active_solver_forensics_v1::solveCertifiedPrimalDualGuess(scaled,options,transform.solver_seed,guess.dual_coordinates,certificate,transform.forensic_iterates);
  transform.stage="QP_RETURNED_EXPLICITLY_SCALED_COORDINATES";transform.solver_coordinates=candidate.result_.velocity;
  if(candidate.result_.velocity.size()){need(candidate.result_.velocity.size()==reduced_n&&candidate.result_.velocity.allFinite(),"solver scaled coordinate vector finite144 required");transform.reduced_coordinates=scale.asDiagonal()*transform.solver_coordinates;candidate.result_.velocity=transform.offset+transform.transform*transform.reduced_coordinates;need(candidate.result_.velocity.allFinite(),"finite reconstructed original controls160 required");}
  const int backend_row=candidate.result_.maximum_violation_row;
  if(backend_row>=0){need(backend_row<static_cast<int>(transform.solver_rows.size()),"backend violation row outside reduced roster");candidate.backend_mapped_original_violation_row_=transform.solver_rows[backend_row];}
  candidate.timing_.connection_and_solver_elapsed=std::chrono::duration<double>(std::chrono::steady_clock::now()-s.connection_started).count();
  candidate.timing_.known_wall_age=s.inputs.observed_age_seconds+s.inputs.known_upstream_elapsed_seconds+candidate.timing_.connection_and_solver_elapsed;
  need(candidate.result_.status==qp::QpStatus::Solved,"only SOLVED admits candidate; native status retained");
  const auto& u=candidate.result_.velocity;need(u.size()==NZ&&u.allFinite(),"solver original control vector finite160 required");
  Eigen::VectorXd ax=p.original_si.constraints*u;need(ax.allFinite(),"candidate original SI row evaluation");
  candidate.violations_.reserve(p.rows.size());bool accepted=true;
  for(int r=0;r<ax.size();++r){const double v=std::max({0.,p.original_si.lower(r)-ax(r),ax(r)-p.original_si.upper(r)});finite(v);
   if(v>candidate.full_original_maximum_violation_){candidate.full_original_maximum_violation_=v;candidate.full_original_maximum_violation_row_=r;}
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
void solveOnceStabilizationNumericGuess(Outcome& out,const qp::QpOptions& options,const NumericOptimizerGuess& guess,CandidateOutcome& candidate){
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
  // Structured equality reduction and equivalent positive row/variable scaling; original SI arrays and every
  // final original-row/rounded-history gate stay unchanged. Fresh workspace.
  const auto screened=screenLinearInputBoxes(p);
  candidate.retained_solver_rows_=screened.retained_rows;candidate.screening_environment_={static_cast<unsigned>(screened.rounding_mode),screened.x87_control,screened.mxcsr};candidate.omitted_solver_rows_.reserve(screened.omitted_rows.size());
  for(const auto& row:screened.omitted_rows){candidate.omitted_solver_rows_.push_back(row.original_row);std::ostringstream interval;interval<<std::hexfloat<<std::setprecision(std::numeric_limits<long double>::max_digits10)<<row.lower_bound<<" "<<row.upper_bound;candidate.omitted_solver_intervals_.push_back(interval.str());}
  // Analytic terminal equality elimination in original IEEE coefficients.
  // Mathematical U=p+Z*Y; all floating products/reconstruction are retained,
  // and every original SI row and strict rounded-history gate remains required.
  candidate.reduction_.emplace();auto& transform=*candidate.reduction_;
  constexpr int reduced_n=18*NU;
  transform.offset=Eigen::VectorXd::Zero(NZ);transform.transform=Eigen::MatrixXd::Zero(NZ,reduced_n);transform.transform.topRows(reduced_n).setIdentity();
  transform.equalities=Eigen::MatrixXd::Zero(16,NZ);transform.equality_rhs=Eigen::VectorXd::Zero(16);
  auto find=[&](const std::string& label){int found=-1;for(int r=0;r<static_cast<int>(p.rows.size());++r)if(p.rows[r].label==label){need(found<0,"duplicate terminal equality label");found=r;}need(found>=0,"missing terminal equality");need(p.original_si.lower(found)==p.original_si.upper(found),"terminal row must be original equality");return found;};
  for(int j=0;j<NU;++j){const auto label=j<7?"terminal/alpha/"+std::to_string(j):"terminal/b";const int r=find(label),col=(N-1)*NU+j;need(p.original_si.lower(r)==0,"terminal final input must be exact zero");
   for(int k=0;k<NZ;++k)need(p.original_si.constraints(r,k)==(k==col?1.:0.),"terminal final input exact unit row required");
   transform.eliminated_rows.push_back(r);transform.equalities.row(j)=p.original_si.constraints.row(r);transform.equality_rhs(j)=p.original_si.lower(r);}
  for(int j=0;j<NU;++j){const auto label=j<7?"terminal/command_w/"+std::to_string(j):"terminal/progress_r";const int r=find(label),pivot=(N-2)*NU+j;const auto row=p.original_si.constraints.row(r);
   for(int k=0;k<NZ;++k)need(std::isfinite(row(k))&&(k%NU==j||row(k)==0),"terminal equality must have only its own control channel");
   need(row(pivot)!=0&&std::isfinite(p.original_si.lower(r)),"finite nonzero terminal pivot required");transform.offset(pivot)=p.original_si.lower(r)/row(pivot);
   for(int k=0;k<reduced_n;++k)transform.transform(pivot,k)=-row(k)/row(pivot);
   transform.eliminated_rows.push_back(r);transform.equalities.row(NU+j)=row;transform.equality_rhs(NU+j)=p.original_si.lower(r);}
  need(transform.transform.allFinite()&&transform.offset.allFinite(),"finite analytic equality map/offset");
  transform.equality_origin_error=(transform.equalities*transform.offset-transform.equality_rhs).cwiseAbs().maxCoeff()/std::max(1.,transform.equality_rhs.cwiseAbs().maxCoeff());
  transform.equality_map_error=(transform.equalities*transform.transform).cwiseAbs().maxCoeff()/std::max(1.,transform.equalities.cwiseAbs().maxCoeff());
  need(transform.equality_origin_error<=1e-12&&transform.equality_map_error<=1e-12,"terminal equality numerical reconstruction check");
  std::set<int> eliminated(transform.eliminated_rows.begin(),transform.eliminated_rows.end());need(eliminated.size()==16,"all16 independent structured terminal equalities required");
  std::vector<std::string> labels;
  for(int r:screened.retained_rows)if(!eliminated.count(r)){transform.solver_rows.push_back(r);labels.push_back(p.rows[r].label);}
  candidate.retained_solver_rows_=transform.solver_rows;
  transform.stored_numeric_slots=live::checkedAdd(live::checkedMultiply(transform.solver_rows.size(),reduced_n),live::checkedAdd(live::checkedMultiply(p.F.rows(),reduced_n),live::checkedAdd(NZ*reduced_n+reduced_n*reduced_n+16*NZ, NZ+5*reduced_n+16+2*transform.solver_rows.size())));
  need(transform.stored_numeric_slots<=2000000,"bounded reduction stored numeric payload before dense transformation; temporary storage bounded by external AS");
  transform.stage="STRUCTURE_VALIDATED_BUILD_REDUCED_QP";
  qp::QpProblem reduced;reduced.state_age_seconds=screened.solver_problem.state_age_seconds;reduced.hessian=transform.transform.transpose()*p.original_si.hessian*transform.transform;
  reduced.gradient=transform.transform.transpose()*(p.original_si.gradient+p.original_si.hessian*transform.offset);
  reduced.constraints.resize(transform.solver_rows.size(),reduced_n);reduced.lower.resize(transform.solver_rows.size());reduced.upper.resize(transform.solver_rows.size());
  for(int i=0;i<static_cast<int>(transform.solver_rows.size());++i){int r=transform.solver_rows[i];const double shift=p.original_si.constraints.row(r).dot(transform.offset);reduced.constraints.row(i)=p.original_si.constraints.row(r)*transform.transform;reduced.lower(i)=p.original_si.lower(r)-shift;reduced.upper(i)=p.original_si.upper(r)-shift;}
  transform.lower=reduced.lower;transform.upper=reduced.upper;transform.hessian=reduced.hessian;transform.gradient=reduced.gradient;transform.constraints=reduced.constraints;transform.factor=p.F*transform.transform;transform.seed=p.seed.head(reduced_n);
  transform.constant=p.constant+p.original_si.gradient.dot(transform.offset)+.5*transform.offset.dot(p.original_si.hessian*transform.offset);
  transform.factor_consistency_error=(transform.factor.transpose()*transform.factor-reduced.hessian).cwiseAbs().maxCoeff()/std::max(1.,reduced.hessian.cwiseAbs().maxCoeff());
  need(reduced.hessian.allFinite()&&reduced.gradient.allFinite()&&reduced.constraints.allFinite()&&reduced.lower.allFinite()&&reduced.upper.allFinite()&&transform.factor.allFinite()&&std::isfinite(transform.constant)&&transform.factor_consistency_error<=1e-12,"reduced finite/factor certificate validation");
  Eigen::VectorXd scale(reduced_n);for(int j=0;j<reduced_n;++j){need(std::isfinite(reduced.hessian(j,j))&&reduced.hessian(j,j)>0,"positive reduced diagonal");scale(j)=1/std::sqrt(reduced.hessian(j,j));need(std::isfinite(scale(j))&&scale(j)>0,"finite positive reduced Jacobi scale");}
  transform.variable_scale=scale;
  // Positive bounded row equilibration: normalize large rows downward, never
  // magnify almost-zero cancellation rows after equality elimination. Fresh
  // certified API has no workspace auto row scaling; original SI final gate.
  transform.stored_numeric_slots=live::checkedAdd(transform.stored_numeric_slots,live::checkedAdd(live::checkedMultiply(reduced.constraints.rows(),reduced_n+3),live::checkedAdd(reduced_n*reduced_n+7*reduced_n+transform.solver_rows.size(),live::checkedMultiply(p.F.rows(),reduced_n))));
  need(transform.stored_numeric_slots<=4000000,"scaled stored numeric payload cap before allocation");
  qp::QpProblem scaled=reduced;scaled.hessian=scale.asDiagonal()*reduced.hessian*scale.asDiagonal();scaled.gradient=scale.asDiagonal()*reduced.gradient;scaled.constraints=reduced.constraints*scale.asDiagonal();
  transform.row_scale=Eigen::VectorXd::Ones(scaled.constraints.rows());
  for(int r=0;r<scaled.constraints.rows();++r){const double norm=scaled.constraints.row(r).cwiseAbs().maxCoeff();need(std::isfinite(norm),"finite bounded scale row norm");const double multiplier=1/std::max(1.,norm);need(std::isfinite(multiplier)&&multiplier>0&&multiplier<=1,"positive downward-only row scale");transform.row_scale(r)=multiplier;scaled.constraints.row(r)*=multiplier;scaled.lower(r)*=multiplier;scaled.upper(r)*=multiplier;}
  transform.solver_hessian=scaled.hessian;transform.solver_gradient=scaled.gradient;transform.solver_constraints=scaled.constraints;transform.solver_lower=scaled.lower;transform.solver_upper=scaled.upper;transform.solver_factor=transform.factor*scale.asDiagonal();transform.solver_seed=transform.seed.cwiseQuotient(scale);
  need(transform.stored_numeric_slots<=4000000&&scaled.hessian.allFinite()&&scaled.gradient.allFinite()&&scaled.constraints.allFinite()&&scaled.lower.allFinite()&&scaled.upper.allFinite()&&transform.solver_factor.allFinite()&&transform.solver_seed.allFinite(),"bounded finite explicitly scaled solver problem");
  transform.scaled_factor_consistency_error=(transform.solver_factor.transpose()*transform.solver_factor-scaled.hessian).cwiseAbs().maxCoeff()/std::max(1.,scaled.hessian.cwiseAbs().maxCoeff());
  need(transform.scaled_factor_consistency_error<=1e-12,"scaled factor consistency certificate");
  // Exact planning subset b_all=0. Build the original144 reduction/scales
  // first, then copy its command-only columns; canonical matrix bytes do not
  // depend on a different dense multiplication tiling. Original rows preserved.
  const auto& stabilization_ctx=s.original.originalNormalization().originalForecast().actualContext();need(stabilization_ctx.actualInitial().s==0&&stabilization_ctx.actualInitial().r==0&&stabilization_ctx.previousB()==0,"stabilization originaltaskstart progress0 only");
  constexpr int native_n=18*7;std::array<int,native_n> cols{};for(int k=0;k<18;++k)for(int j=0;j<7;++j)cols[k*7+j]=k*NU+j;
  auto selectCols=[&](const Eigen::MatrixXd& source){Eigen::MatrixXd target(source.rows(),native_n);for(int j=0;j<native_n;++j)target.col(j)=source.col(cols[j]);return target;};auto selectVector=[&](const Eigen::VectorXd& source){Eigen::VectorXd target(native_n);for(int j=0;j<native_n;++j)target(j)=source(cols[j]);return target;};auto selectSquare=[&](const Eigen::MatrixXd& source){Eigen::MatrixXd target(native_n,native_n);for(int j=0;j<native_n;++j)for(int k=0;k<native_n;++k)target(j,k)=source(cols[j],cols[k]);return target;};
  scaled.hessian=selectSquare(scaled.hessian);scaled.gradient=selectVector(scaled.gradient);scaled.constraints=selectCols(scaled.constraints);
  transform.transform=selectCols(transform.transform);transform.hessian=selectSquare(transform.hessian);transform.gradient=selectVector(transform.gradient);transform.constraints=selectCols(transform.constraints);transform.factor=selectCols(transform.factor);transform.seed=selectVector(transform.seed);transform.variable_scale=selectVector(transform.variable_scale);transform.solver_hessian=scaled.hessian;transform.solver_gradient=scaled.gradient;transform.solver_constraints=scaled.constraints;transform.solver_factor=selectCols(transform.solver_factor);transform.solver_seed=selectVector(transform.solver_seed);
  transform.factor_consistency_error=(transform.factor.transpose()*transform.factor-transform.hessian).cwiseAbs().maxCoeff()/std::max(1.,transform.hessian.cwiseAbs().maxCoeff());transform.scaled_factor_consistency_error=(transform.solver_factor.transpose()*transform.solver_factor-scaled.hessian).cwiseAbs().maxCoeff()/std::max(1.,scaled.hessian.cwiseAbs().maxCoeff());need(transform.factor_consistency_error<=1e-12&&transform.scaled_factor_consistency_error<=1e-12,"actual126 stabilization factor consistency");
  for(int k=0;k<N;++k)need(transform.offset(k*NU+7)==0&&transform.transform.row(k*NU+7).isZero(0),"exact b_all0 subset reconstruction");
  transform.equality_map_error=(transform.equalities*transform.transform).cwiseAbs().maxCoeff()/std::max(1.,transform.equalities.cwiseAbs().maxCoeff());need(transform.equality_map_error<=1e-12,"stabilization originalterminal map check");
  need(s.inputs.timing_mode==TimingMode::OfflineFrozenSimulationBoundary,"external optimizer guess is offline development only");
  const auto& ctx=s.original.originalNormalization().originalForecast().actualContext();auto bit=[](double a,double b){return std::memcmp(&a,&b,sizeof(double))==0;};const auto& actual=ctx.actualInitial();
  for(int j=0;j<7;++j){need(bit(actual.q[j],guess.actual_initial.q[j])&&bit(actual.v[j],guess.actual_initial.v[j])&&bit(actual.C[j],guess.actual_initial.C[j])&&bit(actual.w[j],guess.actual_initial.w[j])&&bit(ctx.previousAlpha()[j],guess.previous_alpha[j]),"external guess actual/command history bitwise mismatch");}need(bit(actual.s,guess.actual_initial.s)&&bit(actual.r,guess.actual_initial.r)&&bit(ctx.previousB(),guess.previous_b),"external guess progresshistory mismatch");
  need(guess.original_problem_sha256==numericProblemDigest(p.original_si,&p.F,&p.f,&p.constant)&&guess.transformed_problem_sha256==numericProblemDigest(scaled,nullptr,nullptr,nullptr),"external guess fulloriginal/scaledmatrix bitwise binding mismatch");need(guess.solver_coordinates.size()==native_n&&guess.solver_coordinates.allFinite(),"finite126 stabilization optimizer-only guess required");transform.solver_seed=guess.solver_coordinates;need(guess.dual_coordinates.size()==scaled.lower.size()&&guess.dual_coordinates.allFinite(),"finite correctlybound externaldualguess");
  transform.numerical_validation_passed=true;transform.stage="VALIDATED_REDUCED_AND_BOUNDED_SCALED_QP_BEFORE_SOLVER";
  transform.forensic_iterates.primal=Eigen::VectorXd::Zero(native_n);transform.forensic_iterates.dual=Eigen::VectorXd::Zero(transform.solver_rows.size()); // owned placeholder only until present=true
  const Eigen::SparseMatrix<double> certificate=transform.solver_factor.sparseView();
  ++candidate.solver_wrapper_entries_;
  candidate.result_=phase5_active_solver_forensics_v1::solveCertifiedPrimalDualGuess(scaled,options,transform.solver_seed,guess.dual_coordinates,certificate,transform.forensic_iterates);
  transform.stage="QP_RETURNED_EXPLICITLY_SCALED_COORDINATES";transform.solver_coordinates=candidate.result_.velocity;
  if(candidate.result_.velocity.size()){need(candidate.result_.velocity.size()==native_n&&candidate.result_.velocity.allFinite(),"solver scaled coordinate vector finite126 required");transform.reduced_coordinates=transform.variable_scale.asDiagonal()*transform.solver_coordinates;candidate.result_.velocity=transform.offset+transform.transform*transform.reduced_coordinates;need(candidate.result_.velocity.allFinite(),"finite reconstructed original controls160 required");}
  const int backend_row=candidate.result_.maximum_violation_row;
  if(backend_row>=0){need(backend_row<static_cast<int>(transform.solver_rows.size()),"backend violation row outside reduced roster");candidate.backend_mapped_original_violation_row_=transform.solver_rows[backend_row];}
  candidate.timing_.connection_and_solver_elapsed=std::chrono::duration<double>(std::chrono::steady_clock::now()-s.connection_started).count();
  candidate.timing_.known_wall_age=s.inputs.observed_age_seconds+s.inputs.known_upstream_elapsed_seconds+candidate.timing_.connection_and_solver_elapsed;
  need(candidate.result_.status==qp::QpStatus::Solved,"only SOLVED admits candidate; native status retained");
  const auto& u=candidate.result_.velocity;need(u.size()==NZ&&u.allFinite(),"solver original control vector finite160 required");
  Eigen::VectorXd ax=p.original_si.constraints*u;need(ax.allFinite(),"candidate original SI row evaluation");
  candidate.violations_.reserve(p.rows.size());bool accepted=true;
  for(int r=0;r<ax.size();++r){const double v=std::max({0.,p.original_si.lower(r)-ax(r),ax(r)-p.original_si.upper(r)});finite(v);
   if(v>candidate.full_original_maximum_violation_){candidate.full_original_maximum_violation_=v;candidate.full_original_maximum_violation_row_=r;}
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
void solveOnceStabilizationInputTrustNumericGuess(Outcome& out,const qp::QpOptions& options,const NumericOptimizerGuess& guess,CandidateOutcome& candidate){
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
  // Structured equality reduction and equivalent positive row/variable scaling; original SI arrays and every
  // final original-row/rounded-history gate stay unchanged. Fresh workspace.
  const auto screened=screenLinearInputBoxes(p);
  candidate.retained_solver_rows_=screened.retained_rows;candidate.screening_environment_={static_cast<unsigned>(screened.rounding_mode),screened.x87_control,screened.mxcsr};candidate.omitted_solver_rows_.reserve(screened.omitted_rows.size());
  for(const auto& row:screened.omitted_rows){candidate.omitted_solver_rows_.push_back(row.original_row);std::ostringstream interval;interval<<std::hexfloat<<std::setprecision(std::numeric_limits<long double>::max_digits10)<<row.lower_bound<<" "<<row.upper_bound;candidate.omitted_solver_intervals_.push_back(interval.str());}
  // Analytic terminal equality elimination in original IEEE coefficients.
  // Mathematical U=p+Z*Y; all floating products/reconstruction are retained,
  // and every original SI row and strict rounded-history gate remains required.
  candidate.reduction_.emplace();auto& transform=*candidate.reduction_;
  constexpr int reduced_n=18*NU;
  transform.offset=Eigen::VectorXd::Zero(NZ);transform.transform=Eigen::MatrixXd::Zero(NZ,reduced_n);transform.transform.topRows(reduced_n).setIdentity();
  transform.equalities=Eigen::MatrixXd::Zero(16,NZ);transform.equality_rhs=Eigen::VectorXd::Zero(16);
  auto find=[&](const std::string& label){int found=-1;for(int r=0;r<static_cast<int>(p.rows.size());++r)if(p.rows[r].label==label){need(found<0,"duplicate terminal equality label");found=r;}need(found>=0,"missing terminal equality");need(p.original_si.lower(found)==p.original_si.upper(found),"terminal row must be original equality");return found;};
  for(int j=0;j<NU;++j){const auto label=j<7?"terminal/alpha/"+std::to_string(j):"terminal/b";const int r=find(label),col=(N-1)*NU+j;need(p.original_si.lower(r)==0,"terminal final input must be exact zero");
   for(int k=0;k<NZ;++k)need(p.original_si.constraints(r,k)==(k==col?1.:0.),"terminal final input exact unit row required");
   transform.eliminated_rows.push_back(r);transform.equalities.row(j)=p.original_si.constraints.row(r);transform.equality_rhs(j)=p.original_si.lower(r);}
  for(int j=0;j<NU;++j){const auto label=j<7?"terminal/command_w/"+std::to_string(j):"terminal/progress_r";const int r=find(label),pivot=(N-2)*NU+j;const auto row=p.original_si.constraints.row(r);
   for(int k=0;k<NZ;++k)need(std::isfinite(row(k))&&(k%NU==j||row(k)==0),"terminal equality must have only its own control channel");
   need(row(pivot)!=0&&std::isfinite(p.original_si.lower(r)),"finite nonzero terminal pivot required");transform.offset(pivot)=p.original_si.lower(r)/row(pivot);
   for(int k=0;k<reduced_n;++k)transform.transform(pivot,k)=-row(k)/row(pivot);
   transform.eliminated_rows.push_back(r);transform.equalities.row(NU+j)=row;transform.equality_rhs(NU+j)=p.original_si.lower(r);}
  need(transform.transform.allFinite()&&transform.offset.allFinite(),"finite analytic equality map/offset");
  transform.equality_origin_error=(transform.equalities*transform.offset-transform.equality_rhs).cwiseAbs().maxCoeff()/std::max(1.,transform.equality_rhs.cwiseAbs().maxCoeff());
  transform.equality_map_error=(transform.equalities*transform.transform).cwiseAbs().maxCoeff()/std::max(1.,transform.equalities.cwiseAbs().maxCoeff());
  need(transform.equality_origin_error<=1e-12&&transform.equality_map_error<=1e-12,"terminal equality numerical reconstruction check");
  std::set<int> eliminated(transform.eliminated_rows.begin(),transform.eliminated_rows.end());need(eliminated.size()==16,"all16 independent structured terminal equalities required");
  std::vector<std::string> labels;
  for(int r:screened.retained_rows)if(!eliminated.count(r)){transform.solver_rows.push_back(r);labels.push_back(p.rows[r].label);}
  candidate.retained_solver_rows_=transform.solver_rows;
  transform.stored_numeric_slots=live::checkedAdd(live::checkedMultiply(transform.solver_rows.size(),reduced_n),live::checkedAdd(live::checkedMultiply(p.F.rows(),reduced_n),live::checkedAdd(NZ*reduced_n+reduced_n*reduced_n+16*NZ, NZ+5*reduced_n+16+2*transform.solver_rows.size())));
  need(transform.stored_numeric_slots<=2000000,"bounded reduction stored numeric payload before dense transformation; temporary storage bounded by external AS");
  transform.stage="STRUCTURE_VALIDATED_BUILD_REDUCED_QP";
  qp::QpProblem reduced;reduced.state_age_seconds=screened.solver_problem.state_age_seconds;reduced.hessian=transform.transform.transpose()*p.original_si.hessian*transform.transform;
  reduced.gradient=transform.transform.transpose()*(p.original_si.gradient+p.original_si.hessian*transform.offset);
  reduced.constraints.resize(transform.solver_rows.size(),reduced_n);reduced.lower.resize(transform.solver_rows.size());reduced.upper.resize(transform.solver_rows.size());
  for(int i=0;i<static_cast<int>(transform.solver_rows.size());++i){int r=transform.solver_rows[i];const double shift=p.original_si.constraints.row(r).dot(transform.offset);reduced.constraints.row(i)=p.original_si.constraints.row(r)*transform.transform;reduced.lower(i)=p.original_si.lower(r)-shift;reduced.upper(i)=p.original_si.upper(r)-shift;}
  transform.lower=reduced.lower;transform.upper=reduced.upper;transform.hessian=reduced.hessian;transform.gradient=reduced.gradient;transform.constraints=reduced.constraints;transform.factor=p.F*transform.transform;transform.seed=p.seed.head(reduced_n);
  transform.constant=p.constant+p.original_si.gradient.dot(transform.offset)+.5*transform.offset.dot(p.original_si.hessian*transform.offset);
  transform.factor_consistency_error=(transform.factor.transpose()*transform.factor-reduced.hessian).cwiseAbs().maxCoeff()/std::max(1.,reduced.hessian.cwiseAbs().maxCoeff());
  need(reduced.hessian.allFinite()&&reduced.gradient.allFinite()&&reduced.constraints.allFinite()&&reduced.lower.allFinite()&&reduced.upper.allFinite()&&transform.factor.allFinite()&&std::isfinite(transform.constant)&&transform.factor_consistency_error<=1e-12,"reduced finite/factor certificate validation");
  Eigen::VectorXd scale(reduced_n);for(int j=0;j<reduced_n;++j){need(std::isfinite(reduced.hessian(j,j))&&reduced.hessian(j,j)>0,"positive reduced diagonal");scale(j)=1/std::sqrt(reduced.hessian(j,j));need(std::isfinite(scale(j))&&scale(j)>0,"finite positive reduced Jacobi scale");}
  transform.variable_scale=scale;
  // Positive bounded row equilibration: normalize large rows downward, never
  // magnify almost-zero cancellation rows after equality elimination. Fresh
  // certified API has no workspace auto row scaling; original SI final gate.
  transform.stored_numeric_slots=live::checkedAdd(transform.stored_numeric_slots,live::checkedAdd(live::checkedMultiply(reduced.constraints.rows(),reduced_n+3),live::checkedAdd(reduced_n*reduced_n+7*reduced_n+transform.solver_rows.size(),live::checkedMultiply(p.F.rows(),reduced_n))));
  need(transform.stored_numeric_slots<=4000000,"scaled stored numeric payload cap before allocation");
  qp::QpProblem scaled=reduced;scaled.hessian=scale.asDiagonal()*reduced.hessian*scale.asDiagonal();scaled.gradient=scale.asDiagonal()*reduced.gradient;scaled.constraints=reduced.constraints*scale.asDiagonal();
  transform.row_scale=Eigen::VectorXd::Ones(scaled.constraints.rows());
  for(int r=0;r<scaled.constraints.rows();++r){const double norm=scaled.constraints.row(r).cwiseAbs().maxCoeff();need(std::isfinite(norm),"finite bounded scale row norm");const double multiplier=1/std::max(1.,norm);need(std::isfinite(multiplier)&&multiplier>0&&multiplier<=1,"positive downward-only row scale");transform.row_scale(r)=multiplier;scaled.constraints.row(r)*=multiplier;scaled.lower(r)*=multiplier;scaled.upper(r)*=multiplier;}
  transform.solver_hessian=scaled.hessian;transform.solver_gradient=scaled.gradient;transform.solver_constraints=scaled.constraints;transform.solver_lower=scaled.lower;transform.solver_upper=scaled.upper;transform.solver_factor=transform.factor*scale.asDiagonal();transform.solver_seed=transform.seed.cwiseQuotient(scale);
  need(transform.stored_numeric_slots<=4000000&&scaled.hessian.allFinite()&&scaled.gradient.allFinite()&&scaled.constraints.allFinite()&&scaled.lower.allFinite()&&scaled.upper.allFinite()&&transform.solver_factor.allFinite()&&transform.solver_seed.allFinite(),"bounded finite explicitly scaled solver problem");
  transform.scaled_factor_consistency_error=(transform.solver_factor.transpose()*transform.solver_factor-scaled.hessian).cwiseAbs().maxCoeff()/std::max(1.,scaled.hessian.cwiseAbs().maxCoeff());
  need(transform.scaled_factor_consistency_error<=1e-12,"scaled factor consistency certificate");
  // Exact planning subset b_all=0. Build the original144 reduction/scales
  // first, then copy its command-only columns; canonical matrix bytes do not
  // depend on a different dense multiplication tiling. Original rows preserved.
  const auto& stabilization_ctx=s.original.originalNormalization().originalForecast().actualContext();need(stabilization_ctx.actualInitial().s==0&&stabilization_ctx.actualInitial().r==0&&stabilization_ctx.previousB()==0,"stabilization originaltaskstart progress0 only");
  constexpr int native_n=18*7;std::array<int,native_n> cols{};for(int k=0;k<18;++k)for(int j=0;j<7;++j)cols[k*7+j]=k*NU+j;
  auto selectCols=[&](const Eigen::MatrixXd& source){Eigen::MatrixXd target(source.rows(),native_n);for(int j=0;j<native_n;++j)target.col(j)=source.col(cols[j]);return target;};auto selectVector=[&](const Eigen::VectorXd& source){Eigen::VectorXd target(native_n);for(int j=0;j<native_n;++j)target(j)=source(cols[j]);return target;};auto selectSquare=[&](const Eigen::MatrixXd& source){Eigen::MatrixXd target(native_n,native_n);for(int j=0;j<native_n;++j)for(int k=0;k<native_n;++k)target(j,k)=source(cols[j],cols[k]);return target;};
  scaled.hessian=selectSquare(scaled.hessian);scaled.gradient=selectVector(scaled.gradient);scaled.constraints=selectCols(scaled.constraints);
  transform.transform=selectCols(transform.transform);transform.hessian=selectSquare(transform.hessian);transform.gradient=selectVector(transform.gradient);transform.constraints=selectCols(transform.constraints);transform.factor=selectCols(transform.factor);transform.seed=selectVector(transform.seed);transform.variable_scale=selectVector(transform.variable_scale);transform.solver_hessian=scaled.hessian;transform.solver_gradient=scaled.gradient;transform.solver_constraints=scaled.constraints;transform.solver_factor=selectCols(transform.solver_factor);transform.solver_seed=selectVector(transform.solver_seed);
  transform.factor_consistency_error=(transform.factor.transpose()*transform.factor-transform.hessian).cwiseAbs().maxCoeff()/std::max(1.,transform.hessian.cwiseAbs().maxCoeff());transform.scaled_factor_consistency_error=(transform.solver_factor.transpose()*transform.solver_factor-scaled.hessian).cwiseAbs().maxCoeff()/std::max(1.,scaled.hessian.cwiseAbs().maxCoeff());need(transform.factor_consistency_error<=1e-12&&transform.scaled_factor_consistency_error<=1e-12,"actual126 stabilization factor consistency");
  for(int k=0;k<N;++k)need(transform.offset(k*NU+7)==0&&transform.transform.row(k*NU+7).isZero(0),"exact b_all0 subset reconstruction");
  transform.equality_map_error=(transform.equalities*transform.transform).cwiseAbs().maxCoeff()/std::max(1.,transform.equalities.cwiseAbs().maxCoeff());need(transform.equality_map_error<=1e-12,"stabilization originalterminal map check");
  // NEW explicit optimizer subset, all140 original alpha coordinates:
  // includes dependent cell18 and exact-zero cell19 after terminal elimination.
  // Original full H/g/F/f/c/SI/E are immutable. These are extra guard rows.
  constexpr int guard_n=20*7;constexpr double solver_guard=.000999,strict_guard=.001;
  transform.base_solver_row_count=scaled.constraints.rows();transform.solver_alpha_guard=solver_guard;transform.strict_alpha_guard=strict_guard;
  transform.stored_numeric_slots=live::checkedAdd(transform.stored_numeric_slots,guard_n*(2*native_n+9));need(transform.stored_numeric_slots<=4000000,"extra140inputguard numeric payload cap before allocation");
  const int base=transform.base_solver_row_count;scaled.constraints.conservativeResize(base+guard_n,Eigen::NoChange);scaled.lower.conservativeResize(base+guard_n);scaled.upper.conservativeResize(base+guard_n);transform.constraints.conservativeResize(base+guard_n,Eigen::NoChange);transform.lower.conservativeResize(base+guard_n);transform.upper.conservativeResize(base+guard_n);transform.row_scale.conservativeResize(base+guard_n);transform.internal_guard_row_scale.resize(guard_n);transform.internal_guard_control_columns.reserve(guard_n);
  for(int k=0;k<20;++k)for(int j=0;j<7;++j){const int id=k*7+j,col=k*NU+j,row=base+id;const Eigen::RowVectorXd unscaled=transform.transform.row(col);const Eigen::RowVectorXd values=unscaled*transform.variable_scale.asDiagonal();const double norm=values.cwiseAbs().maxCoeff(),multiplier=1/std::max(1.,norm);need(values.allFinite()&&std::isfinite(multiplier)&&multiplier>0&&multiplier<=1,"finite extra original-alpha guard map/scale");const double lower=-solver_guard-transform.offset(col),upper=solver_guard-transform.offset(col);need(std::isfinite(lower)&&std::isfinite(upper)&&lower<=upper,"finite originalalpha guard offsetbounds");transform.constraints.row(row)=unscaled;transform.lower(row)=lower;transform.upper(row)=upper;scaled.constraints.row(row)=multiplier*values;scaled.lower(row)=multiplier*lower;scaled.upper(row)=multiplier*upper;transform.row_scale(row)=multiplier;transform.internal_guard_row_scale(id)=multiplier;transform.internal_guard_control_columns.push_back(col);transform.solver_rows.push_back(-1);}
  transform.solver_constraints=scaled.constraints;transform.solver_lower=scaled.lower;transform.solver_upper=scaled.upper;need(transform.internal_guard_control_columns.size()==guard_n&&scaled.constraints.allFinite()&&scaled.lower.allFinite()&&scaled.upper.allFinite(),"full140internal originalalpha guard rows including eliminatedcells");
  need(s.inputs.timing_mode==TimingMode::OfflineFrozenSimulationBoundary,"external optimizer guess is offline development only");
  const auto& ctx=s.original.originalNormalization().originalForecast().actualContext();auto bit=[](double a,double b){return std::memcmp(&a,&b,sizeof(double))==0;};const auto& actual=ctx.actualInitial();
  for(int j=0;j<7;++j){need(bit(actual.q[j],guess.actual_initial.q[j])&&bit(actual.v[j],guess.actual_initial.v[j])&&bit(actual.C[j],guess.actual_initial.C[j])&&bit(actual.w[j],guess.actual_initial.w[j])&&bit(ctx.previousAlpha()[j],guess.previous_alpha[j]),"external guess actual/command history bitwise mismatch");}need(bit(actual.s,guess.actual_initial.s)&&bit(actual.r,guess.actual_initial.r)&&bit(ctx.previousB(),guess.previous_b),"external guess progresshistory mismatch");
  need(guess.original_problem_sha256==numericProblemDigest(p.original_si,&p.F,&p.f,&p.constant)&&guess.transformed_problem_sha256==numericProblemDigest(scaled,nullptr,nullptr,nullptr),"external guess fulloriginal/scaledmatrix bitwise binding mismatch");need(guess.solver_coordinates.size()==native_n&&guess.solver_coordinates.allFinite(),"finite126 stabilization optimizer-only guess required");transform.solver_seed=guess.solver_coordinates;need(guess.dual_coordinates.size()==scaled.lower.size()&&guess.dual_coordinates.allFinite(),"finite correctlybound externaldualguess");
  transform.numerical_validation_passed=true;transform.stage="VALIDATED_REDUCED_AND_BOUNDED_SCALED_QP_BEFORE_SOLVER";
  transform.forensic_iterates.primal=Eigen::VectorXd::Zero(native_n);transform.forensic_iterates.dual=Eigen::VectorXd::Zero(transform.solver_rows.size()); // owned placeholder only until present=true
  const Eigen::SparseMatrix<double> certificate=transform.solver_factor.sparseView();
  ++candidate.solver_wrapper_entries_;
  candidate.result_=phase5_active_solver_forensics_v1::solveCertifiedPrimalDualGuess(scaled,options,transform.solver_seed,guess.dual_coordinates,certificate,transform.forensic_iterates);
  transform.stage="QP_RETURNED_EXPLICITLY_SCALED_COORDINATES";transform.solver_coordinates=candidate.result_.velocity;
  if(candidate.result_.velocity.size()){need(candidate.result_.velocity.size()==native_n&&candidate.result_.velocity.allFinite(),"solver scaled coordinate vector finite126 required");transform.reduced_coordinates=transform.variable_scale.asDiagonal()*transform.solver_coordinates;candidate.result_.velocity=transform.offset+transform.transform*transform.reduced_coordinates;need(candidate.result_.velocity.allFinite(),"finite reconstructed original controls160 required");}
  const int backend_row=candidate.result_.maximum_violation_row;
  if(backend_row>=0){need(backend_row<static_cast<int>(transform.solver_rows.size()),"backend violation row outside reduced roster");candidate.backend_mapped_original_violation_row_=transform.solver_rows[backend_row];if(backend_row>=transform.base_solver_row_count){const int id=backend_row-transform.base_solver_row_count;need(id>=0&&id<static_cast<int>(transform.internal_guard_control_columns.size()),"internalguard backend row mapping");const int col=transform.internal_guard_control_columns[id];candidate.backend_internal_guard_label_="internal_alpha_guard/cell/"+std::to_string(col/NU)+"/joint/"+std::to_string(col%NU);need(candidate.backend_mapped_original_violation_row_==-1,"internalguard must never pretend originalSI row");}}
  candidate.timing_.connection_and_solver_elapsed=std::chrono::duration<double>(std::chrono::steady_clock::now()-s.connection_started).count();
  candidate.timing_.known_wall_age=s.inputs.observed_age_seconds+s.inputs.known_upstream_elapsed_seconds+candidate.timing_.connection_and_solver_elapsed;
  need(candidate.result_.status==qp::QpStatus::Solved,"only SOLVED admits candidate; native status retained");
  const auto& u=candidate.result_.velocity;need(u.size()==NZ&&u.allFinite(),"solver original control vector finite160 required");
  Eigen::VectorXd ax=p.original_si.constraints*u;need(ax.allFinite(),"candidate original SI row evaluation");
  candidate.violations_.reserve(p.rows.size());bool accepted=true;
  for(int r=0;r<ax.size();++r){const double v=std::max({0.,p.original_si.lower(r)-ax(r),ax(r)-p.original_si.upper(r)});finite(v);
   if(v>candidate.full_original_maximum_violation_){candidate.full_original_maximum_violation_=v;candidate.full_original_maximum_violation_row_=r;}
   candidate.violations_.push_back(v);if(v>options.acceptance_tolerance)accepted=false;}
  need(accepted,"independent original SI row gate failed; no epsilon change");
  for(int k=0;k<20;++k)for(int j=0;j<7;++j)need(std::abs(u(k*NU+j))<=strict_guard,"strict reconstructed original-alpha inputtrust gate; no clipping");
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
  candidate.stop_reason_="CANDIDATE_FORWARD_REQUIRED_NO_EXECUTION_PERMISSION";candidate.forensic_request_=request;candidate.request_=std::move(request);
 }catch(const std::exception& e){candidate.request_.reset();candidate.stop_reason_=e.what();}catch(...){candidate.request_.reset();candidate.stop_reason_="NONSTANDARD_SOLVER_OR_CANDIDATE_GATE_FAILURE";}
 // No retry/projection/shrink/posthoc clip. Original SI unchanged; explicit guard subset only.
}
void solveCurrentStabilizationInputTrust(Outcome& out,const qp::QpOptions& options,CandidateOutcome& candidate){
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
  // Structured equality reduction and equivalent positive row/variable scaling; original SI arrays and every
  // final original-row/rounded-history gate stay unchanged. Fresh workspace.
  need(static_cast<bool>(s.inputs.reserve_separate_numeric),"explicit cumulative numeric ledger required");s.inputs.reserve_separate_numeric(4000000); // bounded reduction stores reserved before first allocation
  const auto screened=screenLinearInputBoxes(p);
  candidate.retained_solver_rows_=screened.retained_rows;candidate.screening_environment_={static_cast<unsigned>(screened.rounding_mode),screened.x87_control,screened.mxcsr};candidate.omitted_solver_rows_.reserve(screened.omitted_rows.size());
  for(const auto& row:screened.omitted_rows){candidate.omitted_solver_rows_.push_back(row.original_row);std::ostringstream interval;interval<<std::hexfloat<<std::setprecision(std::numeric_limits<long double>::max_digits10)<<row.lower_bound<<" "<<row.upper_bound;candidate.omitted_solver_intervals_.push_back(interval.str());}
  // Analytic terminal equality elimination in original IEEE coefficients.
  // Mathematical U=p+Z*Y; all floating products/reconstruction are retained,
  // and every original SI row and strict rounded-history gate remains required.
  candidate.reduction_.emplace();auto& transform=*candidate.reduction_;
  constexpr int reduced_n=18*NU;
  transform.offset=Eigen::VectorXd::Zero(NZ);transform.transform=Eigen::MatrixXd::Zero(NZ,reduced_n);transform.transform.topRows(reduced_n).setIdentity();
  transform.equalities=Eigen::MatrixXd::Zero(16,NZ);transform.equality_rhs=Eigen::VectorXd::Zero(16);
  auto find=[&](const std::string& label){int found=-1;for(int r=0;r<static_cast<int>(p.rows.size());++r)if(p.rows[r].label==label){need(found<0,"duplicate terminal equality label");found=r;}need(found>=0,"missing terminal equality");need(p.original_si.lower(found)==p.original_si.upper(found),"terminal row must be original equality");return found;};
  for(int j=0;j<NU;++j){const auto label=j<7?"terminal/alpha/"+std::to_string(j):"terminal/b";const int r=find(label),col=(N-1)*NU+j;need(p.original_si.lower(r)==0,"terminal final input must be exact zero");
   for(int k=0;k<NZ;++k)need(p.original_si.constraints(r,k)==(k==col?1.:0.),"terminal final input exact unit row required");
   transform.eliminated_rows.push_back(r);transform.equalities.row(j)=p.original_si.constraints.row(r);transform.equality_rhs(j)=p.original_si.lower(r);}
  for(int j=0;j<NU;++j){const auto label=j<7?"terminal/command_w/"+std::to_string(j):"terminal/progress_r";const int r=find(label),pivot=(N-2)*NU+j;const auto row=p.original_si.constraints.row(r);
   for(int k=0;k<NZ;++k)need(std::isfinite(row(k))&&(k%NU==j||row(k)==0),"terminal equality must have only its own control channel");
   need(row(pivot)!=0&&std::isfinite(p.original_si.lower(r)),"finite nonzero terminal pivot required");transform.offset(pivot)=p.original_si.lower(r)/row(pivot);
   for(int k=0;k<reduced_n;++k)transform.transform(pivot,k)=-row(k)/row(pivot);
   transform.eliminated_rows.push_back(r);transform.equalities.row(NU+j)=row;transform.equality_rhs(NU+j)=p.original_si.lower(r);}
  need(transform.transform.allFinite()&&transform.offset.allFinite(),"finite analytic equality map/offset");
  transform.equality_origin_error=(transform.equalities*transform.offset-transform.equality_rhs).cwiseAbs().maxCoeff()/std::max(1.,transform.equality_rhs.cwiseAbs().maxCoeff());
  transform.equality_map_error=(transform.equalities*transform.transform).cwiseAbs().maxCoeff()/std::max(1.,transform.equalities.cwiseAbs().maxCoeff());
  need(transform.equality_origin_error<=1e-12&&transform.equality_map_error<=1e-12,"terminal equality numerical reconstruction check");
  std::set<int> eliminated(transform.eliminated_rows.begin(),transform.eliminated_rows.end());need(eliminated.size()==16,"all16 independent structured terminal equalities required");
  std::vector<std::string> labels;
  for(int r:screened.retained_rows)if(!eliminated.count(r)){transform.solver_rows.push_back(r);labels.push_back(p.rows[r].label);}
  candidate.retained_solver_rows_=transform.solver_rows;
  transform.stored_numeric_slots=live::checkedAdd(live::checkedMultiply(transform.solver_rows.size(),reduced_n),live::checkedAdd(live::checkedMultiply(p.F.rows(),reduced_n),live::checkedAdd(NZ*reduced_n+reduced_n*reduced_n+16*NZ, NZ+5*reduced_n+16+2*transform.solver_rows.size())));
  need(transform.stored_numeric_slots<=2000000,"bounded reduction stored numeric payload before dense transformation; temporary storage bounded by external AS");
  transform.stage="STRUCTURE_VALIDATED_BUILD_REDUCED_QP";
  qp::QpProblem reduced;reduced.state_age_seconds=screened.solver_problem.state_age_seconds;reduced.hessian=transform.transform.transpose()*p.original_si.hessian*transform.transform;
  reduced.gradient=transform.transform.transpose()*(p.original_si.gradient+p.original_si.hessian*transform.offset);
  reduced.constraints.resize(transform.solver_rows.size(),reduced_n);reduced.lower.resize(transform.solver_rows.size());reduced.upper.resize(transform.solver_rows.size());
  for(int i=0;i<static_cast<int>(transform.solver_rows.size());++i){int r=transform.solver_rows[i];const double shift=p.original_si.constraints.row(r).dot(transform.offset);reduced.constraints.row(i)=p.original_si.constraints.row(r)*transform.transform;reduced.lower(i)=p.original_si.lower(r)-shift;reduced.upper(i)=p.original_si.upper(r)-shift;}
  transform.lower=reduced.lower;transform.upper=reduced.upper;transform.hessian=reduced.hessian;transform.gradient=reduced.gradient;transform.constraints=reduced.constraints;transform.factor=p.F*transform.transform;transform.seed=p.seed.head(reduced_n);
  transform.constant=p.constant+p.original_si.gradient.dot(transform.offset)+.5*transform.offset.dot(p.original_si.hessian*transform.offset);
  transform.factor_consistency_error=(transform.factor.transpose()*transform.factor-reduced.hessian).cwiseAbs().maxCoeff()/std::max(1.,reduced.hessian.cwiseAbs().maxCoeff());
  need(reduced.hessian.allFinite()&&reduced.gradient.allFinite()&&reduced.constraints.allFinite()&&reduced.lower.allFinite()&&reduced.upper.allFinite()&&transform.factor.allFinite()&&std::isfinite(transform.constant)&&transform.factor_consistency_error<=1e-12,"reduced finite/factor certificate validation");
  Eigen::VectorXd scale(reduced_n);for(int j=0;j<reduced_n;++j){need(std::isfinite(reduced.hessian(j,j))&&reduced.hessian(j,j)>0,"positive reduced diagonal");scale(j)=1/std::sqrt(reduced.hessian(j,j));need(std::isfinite(scale(j))&&scale(j)>0,"finite positive reduced Jacobi scale");}
  transform.variable_scale=scale;
  // Positive bounded row equilibration: normalize large rows downward, never
  // magnify almost-zero cancellation rows after equality elimination. Fresh
  // certified API has no workspace auto row scaling; original SI final gate.
  transform.stored_numeric_slots=live::checkedAdd(transform.stored_numeric_slots,live::checkedAdd(live::checkedMultiply(reduced.constraints.rows(),reduced_n+3),live::checkedAdd(reduced_n*reduced_n+7*reduced_n+transform.solver_rows.size(),live::checkedMultiply(p.F.rows(),reduced_n))));
  need(transform.stored_numeric_slots<=4000000,"scaled stored numeric payload cap before allocation");
  qp::QpProblem scaled=reduced;scaled.hessian=scale.asDiagonal()*reduced.hessian*scale.asDiagonal();scaled.gradient=scale.asDiagonal()*reduced.gradient;scaled.constraints=reduced.constraints*scale.asDiagonal();
  transform.row_scale=Eigen::VectorXd::Ones(scaled.constraints.rows());
  for(int r=0;r<scaled.constraints.rows();++r){const double norm=scaled.constraints.row(r).cwiseAbs().maxCoeff();need(std::isfinite(norm),"finite bounded scale row norm");const double multiplier=1/std::max(1.,norm);need(std::isfinite(multiplier)&&multiplier>0&&multiplier<=1,"positive downward-only row scale");transform.row_scale(r)=multiplier;scaled.constraints.row(r)*=multiplier;scaled.lower(r)*=multiplier;scaled.upper(r)*=multiplier;}
  transform.solver_hessian=scaled.hessian;transform.solver_gradient=scaled.gradient;transform.solver_constraints=scaled.constraints;transform.solver_lower=scaled.lower;transform.solver_upper=scaled.upper;transform.solver_factor=transform.factor*scale.asDiagonal();transform.solver_seed=transform.seed.cwiseQuotient(scale);
  need(transform.stored_numeric_slots<=4000000&&scaled.hessian.allFinite()&&scaled.gradient.allFinite()&&scaled.constraints.allFinite()&&scaled.lower.allFinite()&&scaled.upper.allFinite()&&transform.solver_factor.allFinite()&&transform.solver_seed.allFinite(),"bounded finite explicitly scaled solver problem");
  transform.scaled_factor_consistency_error=(transform.solver_factor.transpose()*transform.solver_factor-scaled.hessian).cwiseAbs().maxCoeff()/std::max(1.,scaled.hessian.cwiseAbs().maxCoeff());
  need(transform.scaled_factor_consistency_error<=1e-12,"scaled factor consistency certificate");
  // Exact planning subset b_all=0. Build the original144 reduction/scales
  // first, then copy its command-only columns; canonical matrix bytes do not
  // depend on a different dense multiplication tiling. Original rows preserved.
  const auto& stabilization_ctx=s.original.originalNormalization().originalForecast().actualContext();need(stabilization_ctx.actualInitial().s==0&&stabilization_ctx.actualInitial().r==0&&stabilization_ctx.previousB()==0,"stabilization originaltaskstart progress0 only");
  constexpr int native_n=18*7;std::array<int,native_n> cols{};for(int k=0;k<18;++k)for(int j=0;j<7;++j)cols[k*7+j]=k*NU+j;
  auto selectCols=[&](const Eigen::MatrixXd& source){Eigen::MatrixXd target(source.rows(),native_n);for(int j=0;j<native_n;++j)target.col(j)=source.col(cols[j]);return target;};auto selectVector=[&](const Eigen::VectorXd& source){Eigen::VectorXd target(native_n);for(int j=0;j<native_n;++j)target(j)=source(cols[j]);return target;};auto selectSquare=[&](const Eigen::MatrixXd& source){Eigen::MatrixXd target(native_n,native_n);for(int j=0;j<native_n;++j)for(int k=0;k<native_n;++k)target(j,k)=source(cols[j],cols[k]);return target;};
  scaled.hessian=selectSquare(scaled.hessian);scaled.gradient=selectVector(scaled.gradient);scaled.constraints=selectCols(scaled.constraints);
  transform.transform=selectCols(transform.transform);transform.hessian=selectSquare(transform.hessian);transform.gradient=selectVector(transform.gradient);transform.constraints=selectCols(transform.constraints);transform.factor=selectCols(transform.factor);transform.seed=selectVector(transform.seed);transform.variable_scale=selectVector(transform.variable_scale);transform.solver_hessian=scaled.hessian;transform.solver_gradient=scaled.gradient;transform.solver_constraints=scaled.constraints;transform.solver_factor=selectCols(transform.solver_factor);transform.solver_seed=selectVector(transform.solver_seed);
  transform.factor_consistency_error=(transform.factor.transpose()*transform.factor-transform.hessian).cwiseAbs().maxCoeff()/std::max(1.,transform.hessian.cwiseAbs().maxCoeff());transform.scaled_factor_consistency_error=(transform.solver_factor.transpose()*transform.solver_factor-scaled.hessian).cwiseAbs().maxCoeff()/std::max(1.,scaled.hessian.cwiseAbs().maxCoeff());need(transform.factor_consistency_error<=1e-12&&transform.scaled_factor_consistency_error<=1e-12,"actual126 stabilization factor consistency");
  for(int k=0;k<N;++k)need(transform.offset(k*NU+7)==0&&transform.transform.row(k*NU+7).isZero(0),"exact b_all0 subset reconstruction");
  transform.equality_map_error=(transform.equalities*transform.transform).cwiseAbs().maxCoeff()/std::max(1.,transform.equalities.cwiseAbs().maxCoeff());need(transform.equality_map_error<=1e-12,"stabilization originalterminal map check");
  // NEW explicit optimizer subset, all140 original alpha coordinates:
  // includes dependent cell18 and exact-zero cell19 after terminal elimination.
  // Original full H/g/F/f/c/SI/E are immutable. These are extra guard rows.
  constexpr int guard_n=20*7;constexpr double solver_guard=.000999,strict_guard=.001;
  transform.base_solver_row_count=scaled.constraints.rows();transform.solver_alpha_guard=solver_guard;transform.strict_alpha_guard=strict_guard;
  transform.stored_numeric_slots=live::checkedAdd(transform.stored_numeric_slots,guard_n*(2*native_n+9));need(transform.stored_numeric_slots<=4000000,"extra140inputguard numeric payload cap before allocation");
  const int base=transform.base_solver_row_count;scaled.constraints.conservativeResize(base+guard_n,Eigen::NoChange);scaled.lower.conservativeResize(base+guard_n);scaled.upper.conservativeResize(base+guard_n);transform.constraints.conservativeResize(base+guard_n,Eigen::NoChange);transform.lower.conservativeResize(base+guard_n);transform.upper.conservativeResize(base+guard_n);transform.row_scale.conservativeResize(base+guard_n);transform.internal_guard_row_scale.resize(guard_n);transform.internal_guard_control_columns.reserve(guard_n);
  for(int k=0;k<20;++k)for(int j=0;j<7;++j){const int id=k*7+j,col=k*NU+j,row=base+id;const Eigen::RowVectorXd unscaled=transform.transform.row(col);const Eigen::RowVectorXd values=unscaled*transform.variable_scale.asDiagonal();const double norm=values.cwiseAbs().maxCoeff(),multiplier=1/std::max(1.,norm);need(values.allFinite()&&std::isfinite(multiplier)&&multiplier>0&&multiplier<=1,"finite extra original-alpha guard map/scale");const double lower=-solver_guard-transform.offset(col),upper=solver_guard-transform.offset(col);need(std::isfinite(lower)&&std::isfinite(upper)&&lower<=upper,"finite originalalpha guard offsetbounds");transform.constraints.row(row)=unscaled;transform.lower(row)=lower;transform.upper(row)=upper;scaled.constraints.row(row)=multiplier*values;scaled.lower(row)=multiplier*lower;scaled.upper(row)=multiplier*upper;transform.row_scale(row)=multiplier;transform.internal_guard_row_scale(id)=multiplier;transform.internal_guard_control_columns.push_back(col);transform.solver_rows.push_back(-1);}
  transform.solver_constraints=scaled.constraints;transform.solver_lower=scaled.lower;transform.solver_upper=scaled.upper;need(transform.internal_guard_control_columns.size()==guard_n&&scaled.constraints.allFinite()&&scaled.lower.allFinite()&&scaled.upper.allFinite(),"full140internal originalalpha guard rows including eliminatedcells");
  need(s.inputs.timing_mode==TimingMode::OfflineFrozenSimulationBoundary,"current numeric prototype is offline only");
  // Rebuilt current p/Z/H/g/A/l/u/scales only. Never accept old x/y/context
  // or use a state/map shift. Retain all bounded face-search events on refusal.
  s.inputs.reserve_separate_numeric(2000000); // bounded current dense arrays/KKT/hints; AS covers allocator/native/temp
  {phase5_fine_timing_v1::Span hint_timing(phase5_fine_timing_v1::Part::Hint);candidate.current_numeric_=phase5_dynamic_numeric_v1::derive(scaled.hessian,scaled.gradient,scaled.constraints,scaled.lower,scaled.upper,transform.solver_seed);}
  const auto& hint=*candidate.current_numeric_;need(hint.complete&&hint.error.empty(),hint.error.c_str());
  need(hint.primal.size()==native_n&&hint.dual.size()==scaled.lower.size()&&hint.primal.allFinite()&&hint.dual.allFinite(),"bounded current numeric primal-dual shapes");
  transform.solver_seed=hint.primal;
  transform.numerical_validation_passed=true;transform.stage="VALIDATED_REDUCED_AND_BOUNDED_SCALED_QP_BEFORE_SOLVER";
  transform.forensic_iterates.primal=Eigen::VectorXd::Zero(native_n);transform.forensic_iterates.dual=Eigen::VectorXd::Zero(transform.solver_rows.size()); // owned placeholder only until present=true
  const Eigen::SparseMatrix<double> certificate=transform.solver_factor.sparseView();
  ++candidate.solver_wrapper_entries_;
  {phase5_fine_timing_v1::Span native_timing(phase5_fine_timing_v1::Part::NativeWrapper);candidate.result_=phase5_active_solver_forensics_v1::solveCertifiedPrimalDualGuess(scaled,options,transform.solver_seed,hint.dual,certificate,transform.forensic_iterates);}
  transform.stage="QP_RETURNED_EXPLICITLY_SCALED_COORDINATES";transform.solver_coordinates=candidate.result_.velocity;
  if(candidate.result_.velocity.size()){need(candidate.result_.velocity.size()==native_n&&candidate.result_.velocity.allFinite(),"solver scaled coordinate vector finite126 required");transform.reduced_coordinates=transform.variable_scale.asDiagonal()*transform.solver_coordinates;candidate.result_.velocity=transform.offset+transform.transform*transform.reduced_coordinates;need(candidate.result_.velocity.allFinite(),"finite reconstructed original controls160 required");}
  const int backend_row=candidate.result_.maximum_violation_row;
  if(backend_row>=0){need(backend_row<static_cast<int>(transform.solver_rows.size()),"backend violation row outside reduced roster");candidate.backend_mapped_original_violation_row_=transform.solver_rows[backend_row];if(backend_row>=transform.base_solver_row_count){const int id=backend_row-transform.base_solver_row_count;need(id>=0&&id<static_cast<int>(transform.internal_guard_control_columns.size()),"internalguard backend row mapping");const int col=transform.internal_guard_control_columns[id];candidate.backend_internal_guard_label_="internal_alpha_guard/cell/"+std::to_string(col/NU)+"/joint/"+std::to_string(col%NU);need(candidate.backend_mapped_original_violation_row_==-1,"internalguard must never pretend originalSI row");}}
  candidate.timing_.connection_and_solver_elapsed=std::chrono::duration<double>(std::chrono::steady_clock::now()-s.connection_started).count();
  candidate.timing_.known_wall_age=s.inputs.observed_age_seconds+s.inputs.known_upstream_elapsed_seconds+candidate.timing_.connection_and_solver_elapsed;
  need(candidate.result_.status==qp::QpStatus::Solved,"only SOLVED admits candidate; native status retained");
  const auto& u=candidate.result_.velocity;need(u.size()==NZ&&u.allFinite(),"solver original control vector finite160 required");
  Eigen::VectorXd ax=p.original_si.constraints*u;need(ax.allFinite(),"candidate original SI row evaluation");
  candidate.violations_.reserve(p.rows.size());bool accepted=true;
  for(int r=0;r<ax.size();++r){const double v=std::max({0.,p.original_si.lower(r)-ax(r),ax(r)-p.original_si.upper(r)});finite(v);
   if(v>candidate.full_original_maximum_violation_){candidate.full_original_maximum_violation_=v;candidate.full_original_maximum_violation_row_=r;}
   candidate.violations_.push_back(v);if(v>options.acceptance_tolerance)accepted=false;}
  need(accepted,"independent original SI row gate failed; no epsilon change");
  for(int k=0;k<20;++k)for(int j=0;j<7;++j)need(std::abs(u(k*NU+j))<=strict_guard,"strict reconstructed original-alpha inputtrust gate; no clipping");
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
  candidate.stop_reason_="CANDIDATE_FORWARD_REQUIRED_NO_EXECUTION_PERMISSION";candidate.forensic_request_=request;candidate.request_=std::move(request);
 }catch(const std::exception& e){candidate.request_.reset();candidate.stop_reason_=e.what();}catch(...){candidate.request_.reset();candidate.stop_reason_="NONSTANDARD_SOLVER_OR_CANDIDATE_GATE_FAILURE";}
 // No retry/projection/shrink/posthoc clip. Original SI unchanged; explicit guard subset only.
}
void solveCurrentProgressInputTrust(Outcome& out,const qp::QpOptions& options,CandidateOutcome& candidate,double margin_fraction){
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
  // Structured equality reduction and equivalent positive row/variable scaling; original SI arrays and every
  // final original-row/rounded-history gate stay unchanged. Fresh workspace.
  need(static_cast<bool>(s.inputs.reserve_separate_numeric),"explicit cumulative numeric ledger required");s.inputs.reserve_separate_numeric(4000000); // bounded reduction stores reserved before first allocation
  const auto screened=screenLinearInputBoxes(p);
  candidate.retained_solver_rows_=screened.retained_rows;candidate.screening_environment_={static_cast<unsigned>(screened.rounding_mode),screened.x87_control,screened.mxcsr};candidate.omitted_solver_rows_.reserve(screened.omitted_rows.size());
  for(const auto& row:screened.omitted_rows){candidate.omitted_solver_rows_.push_back(row.original_row);std::ostringstream interval;interval<<std::hexfloat<<std::setprecision(std::numeric_limits<long double>::max_digits10)<<row.lower_bound<<" "<<row.upper_bound;candidate.omitted_solver_intervals_.push_back(interval.str());}
  // Analytic terminal equality elimination in original IEEE coefficients.
  // Mathematical U=p+Z*Y; all floating products/reconstruction are retained,
  // and every original SI row and strict rounded-history gate remains required.
  candidate.reduction_.emplace();auto& transform=*candidate.reduction_;
  constexpr int reduced_n=18*NU;
  transform.offset=Eigen::VectorXd::Zero(NZ);transform.transform=Eigen::MatrixXd::Zero(NZ,reduced_n);transform.transform.topRows(reduced_n).setIdentity();
  transform.equalities=Eigen::MatrixXd::Zero(16,NZ);transform.equality_rhs=Eigen::VectorXd::Zero(16);
  auto find=[&](const std::string& label){int found=-1;for(int r=0;r<static_cast<int>(p.rows.size());++r)if(p.rows[r].label==label){need(found<0,"duplicate terminal equality label");found=r;}need(found>=0,"missing terminal equality");need(p.original_si.lower(found)==p.original_si.upper(found),"terminal row must be original equality");return found;};
  for(int j=0;j<NU;++j){const auto label=j<7?"terminal/alpha/"+std::to_string(j):"terminal/b";const int r=find(label),col=(N-1)*NU+j;need(p.original_si.lower(r)==0,"terminal final input must be exact zero");
   for(int k=0;k<NZ;++k)need(p.original_si.constraints(r,k)==(k==col?1.:0.),"terminal final input exact unit row required");
   transform.eliminated_rows.push_back(r);transform.equalities.row(j)=p.original_si.constraints.row(r);transform.equality_rhs(j)=p.original_si.lower(r);}
  for(int j=0;j<NU;++j){const auto label=j<7?"terminal/command_w/"+std::to_string(j):"terminal/progress_r";const int r=find(label),pivot=(N-2)*NU+j;const auto row=p.original_si.constraints.row(r);
   for(int k=0;k<NZ;++k)need(std::isfinite(row(k))&&(k%NU==j||row(k)==0),"terminal equality must have only its own control channel");
   need(row(pivot)!=0&&std::isfinite(p.original_si.lower(r)),"finite nonzero terminal pivot required");transform.offset(pivot)=p.original_si.lower(r)/row(pivot);
   for(int k=0;k<reduced_n;++k)transform.transform(pivot,k)=-row(k)/row(pivot);
   transform.eliminated_rows.push_back(r);transform.equalities.row(NU+j)=row;transform.equality_rhs(NU+j)=p.original_si.lower(r);}
  // Explicit numerical planning tail, NOT exact equivalence to original E0.
  // Original problem/E/rhs/acceptance and strict progress domain are untouched.
  // Positive1e-13 1/s target stays within original SI tolerance; original E
  // residual and observed nonzero tail remain visible, no stop certificate.
  transform.planning_terminal_progress_r_target=1e-13;
  transform.planning_equality_rhs=transform.equality_rhs;transform.planning_equality_rhs(15)+=transform.planning_terminal_progress_r_target;
  transform.offset((N-2)*NU+7)=transform.planning_equality_rhs(15)/transform.equalities(15,(N-2)*NU+7);
  need(transform.transform.allFinite()&&transform.offset.allFinite(),"finite analytic equality map/offset");
  transform.equality_origin_error=(transform.equalities*transform.offset-transform.equality_rhs).cwiseAbs().maxCoeff()/std::max(1.,transform.equality_rhs.cwiseAbs().maxCoeff());
  transform.equality_map_error=(transform.equalities*transform.transform).cwiseAbs().maxCoeff()/std::max(1.,transform.equalities.cwiseAbs().maxCoeff());
  need(transform.equality_origin_error<=1e-12&&transform.equality_map_error<=1e-12,"original E numerical residual check with disclosed nonzero planning progress tail");
  std::set<int> eliminated(transform.eliminated_rows.begin(),transform.eliminated_rows.end());need(eliminated.size()==16,"all16 independent structured terminal equalities required");
  std::vector<std::string> labels;
  for(int r:screened.retained_rows)if(!eliminated.count(r)){transform.solver_rows.push_back(r);labels.push_back(p.rows[r].label);}
  candidate.retained_solver_rows_=transform.solver_rows;
  transform.stored_numeric_slots=live::checkedAdd(live::checkedMultiply(transform.solver_rows.size(),reduced_n),live::checkedAdd(live::checkedMultiply(p.F.rows(),reduced_n),live::checkedAdd(NZ*reduced_n+reduced_n*reduced_n+16*NZ, NZ+5*reduced_n+16+2*transform.solver_rows.size())));
  need(transform.stored_numeric_slots<=2000000,"bounded reduction stored numeric payload before dense transformation; temporary storage bounded by external AS");
  transform.stage="STRUCTURE_VALIDATED_BUILD_REDUCED_QP";
  qp::QpProblem reduced;reduced.state_age_seconds=screened.solver_problem.state_age_seconds;reduced.hessian=transform.transform.transpose()*p.original_si.hessian*transform.transform;
  reduced.gradient=transform.transform.transpose()*(p.original_si.gradient+p.original_si.hessian*transform.offset);
  reduced.constraints.resize(transform.solver_rows.size(),reduced_n);reduced.lower.resize(transform.solver_rows.size());reduced.upper.resize(transform.solver_rows.size());
  for(int i=0;i<static_cast<int>(transform.solver_rows.size());++i){int r=transform.solver_rows[i];const double shift=p.original_si.constraints.row(r).dot(transform.offset);reduced.constraints.row(i)=p.original_si.constraints.row(r)*transform.transform;reduced.lower(i)=p.original_si.lower(r)-shift;reduced.upper(i)=p.original_si.upper(r)-shift;}
  transform.lower=reduced.lower;transform.upper=reduced.upper;transform.hessian=reduced.hessian;transform.gradient=reduced.gradient;transform.constraints=reduced.constraints;transform.factor=p.F*transform.transform;transform.seed=p.seed.head(reduced_n);
  transform.constant=p.constant+p.original_si.gradient.dot(transform.offset)+.5*transform.offset.dot(p.original_si.hessian*transform.offset);
  transform.factor_consistency_error=(transform.factor.transpose()*transform.factor-reduced.hessian).cwiseAbs().maxCoeff()/std::max(1.,reduced.hessian.cwiseAbs().maxCoeff());
  need(reduced.hessian.allFinite()&&reduced.gradient.allFinite()&&reduced.constraints.allFinite()&&reduced.lower.allFinite()&&reduced.upper.allFinite()&&transform.factor.allFinite()&&std::isfinite(transform.constant)&&transform.factor_consistency_error<=1e-12,"reduced finite/factor certificate validation");
  Eigen::VectorXd scale(reduced_n);for(int j=0;j<reduced_n;++j){need(std::isfinite(reduced.hessian(j,j))&&reduced.hessian(j,j)>0,"positive reduced diagonal");scale(j)=1/std::sqrt(reduced.hessian(j,j));need(std::isfinite(scale(j))&&scale(j)>0,"finite positive reduced Jacobi scale");}
  transform.variable_scale=scale;
  // Positive bounded row equilibration: normalize large rows downward, never
  // magnify almost-zero cancellation rows after equality elimination. Fresh
  // certified API has no workspace auto row scaling; original SI final gate.
  transform.stored_numeric_slots=live::checkedAdd(transform.stored_numeric_slots,live::checkedAdd(live::checkedMultiply(reduced.constraints.rows(),reduced_n+3),live::checkedAdd(reduced_n*reduced_n+7*reduced_n+transform.solver_rows.size(),live::checkedMultiply(p.F.rows(),reduced_n))));
  need(transform.stored_numeric_slots<=4000000,"scaled stored numeric payload cap before allocation");
  qp::QpProblem scaled=reduced;scaled.hessian=scale.asDiagonal()*reduced.hessian*scale.asDiagonal();scaled.gradient=scale.asDiagonal()*reduced.gradient;scaled.constraints=reduced.constraints*scale.asDiagonal();
  transform.row_scale=Eigen::VectorXd::Ones(scaled.constraints.rows());
  for(int r=0;r<scaled.constraints.rows();++r){const double norm=scaled.constraints.row(r).cwiseAbs().maxCoeff();need(std::isfinite(norm),"finite bounded scale row norm");const double multiplier=1/std::max(1.,norm);need(std::isfinite(multiplier)&&multiplier>0&&multiplier<=1,"positive downward-only row scale");transform.row_scale(r)=multiplier;scaled.constraints.row(r)*=multiplier;scaled.lower(r)*=multiplier;scaled.upper(r)*=multiplier;}
  transform.solver_hessian=scaled.hessian;transform.solver_gradient=scaled.gradient;transform.solver_constraints=scaled.constraints;transform.solver_lower=scaled.lower;transform.solver_upper=scaled.upper;transform.solver_factor=transform.factor*scale.asDiagonal();transform.solver_seed=transform.seed.cwiseQuotient(scale);
  need(transform.stored_numeric_slots<=4000000&&scaled.hessian.allFinite()&&scaled.gradient.allFinite()&&scaled.constraints.allFinite()&&scaled.lower.allFinite()&&scaled.upper.allFinite()&&transform.solver_factor.allFinite()&&transform.solver_seed.allFinite(),"bounded finite explicitly scaled solver problem");
  transform.scaled_factor_consistency_error=(transform.solver_factor.transpose()*transform.solver_factor-scaled.hessian).cwiseAbs().maxCoeff()/std::max(1.,scaled.hessian.cwiseAbs().maxCoeff());
  need(transform.scaled_factor_consistency_error<=1e-12,"scaled factor consistency certificate");
  // All144 reduced controls, including18 independent progress inputs. No b=0
  // restriction; reconstruct dependent cell18 and zero cell19 from original E.
  constexpr int native_n=reduced_n;
  const auto& progress_context=s.original.originalNormalization().originalForecast().actualContext();
  // NEW explicit optimizer subset, all140 original alpha coordinates:
  // includes dependent cell18 and exact-zero cell19 after terminal elimination.
  // Original full H/g/F/f/c/SI/E are immutable. These are extra guard rows.
  constexpr int alpha_guard_n=20*7,progress_guard_n=20,guard_n=alpha_guard_n+progress_guard_n;constexpr double solver_progress_guard=4.999,strict_progress_guard=4.9995;
  s.inputs.reserve_separate_numeric(40000); // current outward proof/center+retained diagnostics, before allocations
  const auto current_trust=phase5_current_alpha_trust_v1::derive(p,s.inputs.limits.command_acceleration,margin_fraction);const double solver_guard=current_trust.solver_radius,strict_guard=current_trust.strict_radius;
  transform.alpha_guard_center=current_trust.center;transform.alpha_guard_limiting_original_row=current_trust.limiting_original_row;transform.alpha_guard_trust_rows.reserve(current_trust.rows.size());transform.alpha_guard_trust_proof.resize(current_trust.rows.size(),4);for(int i=0;i<static_cast<int>(current_trust.rows.size());++i){const auto& proof=current_trust.rows[i];transform.alpha_guard_trust_rows.push_back(proof.original_row);transform.alpha_guard_trust_proof.row(i)<<proof.coefficient_L1_upper,proof.seed_lower,proof.seed_upper,proof.margin_lower;}

  transform.base_solver_row_count=scaled.constraints.rows();transform.solver_alpha_guard=solver_guard;transform.strict_alpha_guard=strict_guard;transform.solver_progress_jerk_guard=solver_progress_guard;transform.strict_progress_jerk_guard=strict_progress_guard;transform.progress_guard_previous_b=progress_context.previousB();
  transform.stored_numeric_slots=live::checkedAdd(transform.stored_numeric_slots,guard_n*(2*native_n+9));need(transform.stored_numeric_slots<=4000000,"extra160inputguard numeric payload cap before allocation");
  const int base=transform.base_solver_row_count;scaled.constraints.conservativeResize(base+guard_n,Eigen::NoChange);scaled.lower.conservativeResize(base+guard_n);scaled.upper.conservativeResize(base+guard_n);transform.constraints.conservativeResize(base+guard_n,Eigen::NoChange);transform.lower.conservativeResize(base+guard_n);transform.upper.conservativeResize(base+guard_n);transform.row_scale.conservativeResize(base+guard_n);transform.internal_guard_row_scale.resize(guard_n);transform.internal_guard_control_columns.reserve(guard_n);
  for(int k=0;k<20;++k)for(int j=0;j<7;++j){const int id=k*7+j,col=k*NU+j,row=base+id;const Eigen::RowVectorXd unscaled=transform.transform.row(col);const Eigen::RowVectorXd values=unscaled*transform.variable_scale.asDiagonal();const double norm=values.cwiseAbs().maxCoeff(),multiplier=1/std::max(1.,norm);need(values.allFinite()&&std::isfinite(multiplier)&&multiplier>0&&multiplier<=1,"finite extra original-alpha guard map/scale");double lower=std::max(-s.inputs.limits.command_acceleration,current_trust.center(col)-solver_guard)-transform.offset(col),upper=std::min(s.inputs.limits.command_acceleration,current_trust.center(col)+solver_guard)-transform.offset(col);if(s.inputs.stop_mode&&k==0){need(transform.offset(col)==0.,"first seven free original controls have zero terminal offset");const auto first=phase5_roundoff_command64_v1::firstBounds(progress_context.actualInitial().w[j],current_trust.center(col),lower,upper);lower=first.lower;upper=first.upper;if(s.inputs.first_command_interior66){const auto inside=phase5_contract_interior66_v1::prepare(lower,upper,current_trust.center(col),multiplier,transform.variable_scale(col),options.absolute_tolerance);lower=inside.lower;upper=inside.upper;transform.solver_seed(col)=inside.seed_y;}}need(std::isfinite(lower)&&std::isfinite(upper)&&lower<=upper,"finite originalalpha guard offsetbounds");transform.constraints.row(row)=unscaled;transform.lower(row)=lower;transform.upper(row)=upper;scaled.constraints.row(row)=multiplier*values;scaled.lower(row)=multiplier*lower;scaled.upper(row)=multiplier*upper;transform.row_scale(row)=multiplier;transform.internal_guard_row_scale(id)=multiplier;transform.internal_guard_control_columns.push_back(col);transform.solver_rows.push_back(-1);}
  // Additional20 progress feedback-jerk rows with margin inside unchanged5.
  // First row uses actual accepted previousb; later rows use preceding b cell.
  for(int k=0;k<N;++k){const int id=alpha_guard_n+k,col=k*NU+7,row=base+id;Eigen::RowVectorXd unscaled=transform.transform.row(col)/h;double shift=transform.offset(col)/h;if(k==0)shift-=progress_context.previousB()/h;else{unscaled-=transform.transform.row((k-1)*NU+7)/h;shift-=transform.offset((k-1)*NU+7)/h;}const Eigen::RowVectorXd values=unscaled*transform.variable_scale.asDiagonal();const double multiplier=1/std::max(1.,values.cwiseAbs().maxCoeff());double lower=-solver_progress_guard-shift;const double upper=solver_progress_guard-shift;if(s.inputs.stop_mode&&s.inputs.physical_braking65&&k==0){need(transform.offset(7)==0.,"first free progress input has exact zero terminal offset");lower=phase5_physical_braking65_v1::firstProgressLower(progress_context.actualInitial().r,transform.offset(7),lower);}need(values.allFinite()&&std::isfinite(multiplier)&&multiplier>0&&multiplier<=1&&std::isfinite(lower)&&std::isfinite(upper)&&lower<=upper,"finite current progress feedbackjerk internal guard");transform.constraints.row(row)=unscaled;transform.lower(row)=lower;transform.upper(row)=upper;scaled.constraints.row(row)=multiplier*values;scaled.lower(row)=multiplier*lower;scaled.upper(row)=multiplier*upper;transform.row_scale(row)=multiplier;transform.internal_guard_row_scale(id)=multiplier;transform.internal_guard_control_columns.push_back(col);transform.solver_rows.push_back(-1);}
  transform.solver_constraints=scaled.constraints;transform.solver_lower=scaled.lower;transform.solver_upper=scaled.upper;need(transform.internal_guard_control_columns.size()==guard_n&&scaled.constraints.allFinite()&&scaled.lower.allFinite()&&scaled.upper.allFinite(),"full160internal alpha/progressjerk guard rows including eliminatedcells");
  if(s.inputs.stop_mode){
   // NEW stop-only planning subset. Original p.H/g/A/l/u and all final gates
   // remain unchanged. Reserve before helper outputs/copies/label storage.
   s.inputs.reserve_separate_numeric(250000);
   std::vector<std::string> original_labels;original_labels.reserve(p.rows.size());for(const auto& row:p.rows)original_labels.push_back(row.label);
   const auto interior=phase5_progress_interior_guard_v1::prepare(p.original_si.constraints,p.original_si.lower,p.original_si.upper,original_labels,transform.transform,transform.offset,transform.variable_scale,scaled.constraints.rows());
   constexpr int extra=phase5_progress_interior_guard_v1::halves;
   transform.stored_numeric_slots=live::checkedAdd(transform.stored_numeric_slots,extra*(2*native_n+11));need(transform.stored_numeric_slots<=4000000,"all264 floor retained numeric payload before copy");
   const int floor_base=scaled.constraints.rows();need(floor_base<=20000-extra,"all264 floor total rows before resize");
   scaled.constraints.conservativeResize(floor_base+extra,Eigen::NoChange);scaled.lower.conservativeResize(floor_base+extra);scaled.upper.conservativeResize(floor_base+extra);transform.constraints.conservativeResize(floor_base+extra,Eigen::NoChange);transform.lower.conservativeResize(floor_base+extra);transform.upper.conservativeResize(floor_base+extra);transform.row_scale.conservativeResize(floor_base+extra);transform.progress_floor_row_scale=interior.scale;transform.progress_floor_original_rows.reserve(extra);
   for(int sample=0;sample<extra;++sample){const int row=floor_base+sample,original_row=interior.original_row[sample];const double shift=p.original_si.constraints.row(original_row).dot(transform.offset);transform.constraints.row(row)=p.original_si.constraints.row(original_row)*transform.transform;transform.lower(row)=p.original_si.lower(original_row)+phase5_progress_interior_guard_v1::floor_rate-shift;transform.upper(row)=p.original_si.upper(original_row)-shift;scaled.constraints.row(row)=interior.A.row(sample);scaled.lower(row)=interior.lower(sample);scaled.upper(row)=interior.upper(sample);transform.row_scale(row)=interior.scale(sample);transform.progress_floor_original_rows.push_back(original_row);transform.solver_rows.push_back(-1);}
   need(transform.progress_floor_original_rows.size()==extra&&transform.constraints.allFinite()&&transform.lower.allFinite()&&transform.upper.allFinite()&&scaled.constraints.allFinite()&&scaled.lower.allFinite()&&scaled.upper.allFinite(),"all264 finite complete planning floor copies");
   transform.solver_constraints=scaled.constraints;transform.solver_lower=scaled.lower;transform.solver_upper=scaled.upper;
  }

  if(s.inputs.joint_jerk_interior67){
   need(s.inputs.stop_mode&&s.inputs.physical_braking65&&s.inputs.first_command_interior66,"explicit joint jerk planning interior only with existing physical stop/first7 policies");
   phase5_jerk_interior67_v1::tightenExistingScaledRows(scaled.lower,scaled.upper,base,[&](int i){const int r=transform.solver_rows.at(i);need(r>=0&&r<static_cast<int>(p.rows.size()),"existing base original row identity");return phase5_jerk_interior67_v1::isJointJerkRow(p.rows[r].label,p.rows[r].units);},options.absolute_tolerance);
   // Original unscaled reduction bounds remain; actual numerical solver
   // bounds alone are the explicitly recorded smaller planning subset.
   transform.solver_lower=scaled.lower;transform.solver_upper=scaled.upper;
  }
  need(s.inputs.timing_mode==TimingMode::OfflineFrozenSimulationBoundary,"current numeric prototype is offline only");
  // Rebuilt current p/Z/H/g/A/l/u/scales only. Never accept old x/y/context
  // or use a state/map shift. Retain all bounded face-search events on refusal.
  s.inputs.reserve_separate_numeric(2000000); // bounded current dense arrays/KKT/hints; AS covers allocator/native/temp
  if(s.inputs.first_command_interior66)need(s.inputs.stop_mode&&s.inputs.physical_braking65,"explicit physical stop-only optimizer interior policy");
  if(s.inputs.stop_mode){
   s.inputs.reserve_separate_numeric(250000); // before new initializer outputs/copies; no Model/state/candidate changes
   transform.initializer_attempted=true;
   transform.initializer=phase5_bounded_global_interval_seed_v6::prepare(scaled.constraints,scaled.lower,scaled.upper,transform.solver_seed,transform.variable_scale);
   const auto& combined=transform.initializer;const auto& start=combined.retry;
   const std::uint64_t retained=start.row_direction_bounds.size()+start.seed.size()+start.attempts.size()*3+combined.corrections.size()*(144+32)+combined.global_scans.size()*24+768;
   transform.stored_numeric_slots=live::checkedAdd(transform.stored_numeric_slots,retained);need(transform.stored_numeric_slots<=4000000,"combined initializer retained numeric cap before solver seed copy");
   need(combined.complete&&combined.error.empty(),combined.error.c_str());transform.solver_seed=start.seed;
  }
  if(s.inputs.stop_mode)s.inputs.reserve_separate_numeric(phase5_boundary_retention_limits57::declared_numeric_allowance57); // new bounded working-face/endpoint/retained diagnostic stores before allocations
  {phase5_fine_timing_v1::Span hint_timing(phase5_fine_timing_v1::Part::Hint);candidate.current_numeric_=phase5_dynamic_numeric_v1::derive(scaled.hessian,scaled.gradient,scaled.constraints,scaled.lower,scaled.upper,transform.solver_seed,s.inputs.stop_mode,s.inputs.stop_mode);}
  const auto& hint=*candidate.current_numeric_;need(hint.complete&&hint.error.empty(),hint.error.c_str());
  need(hint.primal.size()==native_n&&hint.dual.size()==scaled.lower.size()&&hint.primal.allFinite()&&hint.dual.allFinite(),"bounded current numeric primal-dual shapes");
  transform.solver_seed=hint.primal;
  transform.numerical_validation_passed=true;transform.stage="VALIDATED_FULL144_NUMERICAL_PROGRESS_TAIL_PLAN_NOT_EXACT_E0_EQUIVALENCE";
  transform.forensic_iterates.primal=Eigen::VectorXd::Zero(native_n);transform.forensic_iterates.dual=Eigen::VectorXd::Zero(transform.solver_rows.size()); // owned placeholder only until present=true
  const Eigen::SparseMatrix<double> certificate=transform.solver_factor.sparseView();
  ++candidate.solver_wrapper_entries_;
  {phase5_fine_timing_v1::Span native_timing(phase5_fine_timing_v1::Part::NativeWrapper);candidate.result_=phase5_active_solver_forensics_v1::solveCertifiedPrimalDualGuess(scaled,options,transform.solver_seed,hint.dual,certificate,transform.forensic_iterates);}
  transform.stage="QP_RETURNED_EXPLICITLY_SCALED_COORDINATES";transform.solver_coordinates=candidate.result_.velocity;
  if(candidate.result_.velocity.size()){need(candidate.result_.velocity.size()==native_n&&candidate.result_.velocity.allFinite(),"solver scaled coordinate vector finite144 required");transform.reduced_coordinates=transform.variable_scale.asDiagonal()*transform.solver_coordinates;candidate.result_.velocity=transform.offset+transform.transform*transform.reduced_coordinates;need(candidate.result_.velocity.allFinite(),"finite reconstructed original controls160 required");}
  const int backend_row=candidate.result_.maximum_violation_row;
  if(backend_row>=0){need(backend_row<static_cast<int>(transform.solver_rows.size()),"backend violation row outside reduced roster");candidate.backend_mapped_original_violation_row_=transform.solver_rows[backend_row];if(backend_row>=transform.base_solver_row_count){const int id=backend_row-transform.base_solver_row_count;need(id>=0&&id<static_cast<int>(transform.internal_guard_control_columns.size()+transform.progress_floor_original_rows.size()),"internalguard backend row mapping");if(id<static_cast<int>(transform.internal_guard_control_columns.size())){const int col=transform.internal_guard_control_columns[id];candidate.backend_internal_guard_label_=id<alpha_guard_n?"internal_alpha_guard/cell/"+std::to_string(col/NU)+"/joint/"+std::to_string(col%NU):"internal_progress_jerk_guard/cell/"+std::to_string(col/NU);}else{const int sample=id-transform.internal_guard_control_columns.size();candidate.backend_internal_guard_label_="internal_progress_interior_floor/half/"+std::to_string(sample);}need(candidate.backend_mapped_original_violation_row_==-1,"internalguard must never pretend originalSI row");}}
  candidate.timing_.connection_and_solver_elapsed=std::chrono::duration<double>(std::chrono::steady_clock::now()-s.connection_started).count();
  candidate.timing_.known_wall_age=s.inputs.observed_age_seconds+s.inputs.known_upstream_elapsed_seconds+candidate.timing_.connection_and_solver_elapsed;
  need(candidate.result_.status==qp::QpStatus::Solved,"only SOLVED admits candidate; native status retained");
  const auto& u=candidate.result_.velocity;need(u.size()==NZ&&u.allFinite(),"solver original control vector finite160 required");
  Eigen::VectorXd ax=p.original_si.constraints*u;need(ax.allFinite(),"candidate original SI row evaluation");
  candidate.violations_.reserve(p.rows.size());bool accepted=true;
  for(int r=0;r<ax.size();++r){const double v=std::max({0.,p.original_si.lower(r)-ax(r),ax(r)-p.original_si.upper(r)});finite(v);
   if(v>candidate.full_original_maximum_violation_){candidate.full_original_maximum_violation_=v;candidate.full_original_maximum_violation_row_=r;}
   candidate.violations_.push_back(v);if(v>options.acceptance_tolerance)accepted=false;}
  need(accepted,"independent original SI row gate failed; no epsilon change");
  for(int k=0;k<20;++k)for(int j=0;j<7;++j)need(std::nextafter(std::abs(u(k*NU+j)-current_trust.center(k*NU+j)),std::numeric_limits<double>::infinity())<=strict_guard,"strict outward current nominal-centered alpha trust gate; no clipping");
  if(s.inputs.stop_mode)for(int j=0;j<7;++j){const auto first=phase5_roundoff_command64_v1::firstBounds(progress_context.actualInitial().w[j],current_trust.center(j),std::max(-s.inputs.limits.command_acceleration,current_trust.center(j)-solver_guard),std::min(s.inputs.limits.command_acceleration,current_trust.center(j)+solver_guard));need(phase5_roundoff_command64_v1::strictFirst(progress_context.actualInitial().w[j],u(j),first),"strict current-history first-command contraction planning gate; no clipping");}
  if(s.inputs.stop_mode&&s.inputs.physical_braking65)need(phase5_physical_braking65_v1::strictFirstProgress(progress_context.actualInitial().r,u(7)),"strict first-progress planning band, no clipping or original safety relaxation");
  double prior_progress_b=progress_context.previousB();for(int k=0;k<N;++k){const double jerk=(u(k*NU+7)-prior_progress_b)/h;need(std::isfinite(jerk)&&std::abs(jerk)<=strict_progress_guard,"strict reconstructed internal progressjerk margin; reject without clip");prior_progress_b=u(k*NU+7);}
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
  candidate.stop_reason_="CANDIDATE_FORWARD_REQUIRED_NO_EXECUTION_PERMISSION";candidate.forensic_request_=request;candidate.request_=std::move(request);
 }catch(const std::exception& e){candidate.request_.reset();candidate.stop_reason_=e.what();}catch(...){candidate.request_.reset();candidate.stop_reason_="NONSTANDARD_SOLVER_OR_CANDIDATE_GATE_FAILURE";}
 // No retry/projection/shrink/posthoc clip. Original SI unchanged; explicit guard subset only.
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
