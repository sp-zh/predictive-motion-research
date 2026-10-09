#include "affine_assembly.hpp"
#include <algorithm>
#include <cmath>
#include <initializer_list>
#include <stdexcept>
#include <utility>

namespace phase5_public_live_affine_v2 {
namespace {
constexpr double arithmetic_abs=2e-13,arithmetic_rel=2e-13;
void need(bool value,const char* reason){if(!value)throw std::invalid_argument(reason);}
Count mul(Count a,Count b){return checkedMultiply(a,b);}
Count add(Count a,Count b){return checkedAdd(a,b);}
Count sum(std::initializer_list<Count> values){Count n=0;for(Count v:values)n=add(n,v);return n;}
void finite(double value){need(std::isfinite(value),"nonfinite affine operation");}
void product(double a,double b,double& total){const double p=a*b;finite(p);total+=p;finite(total);}
void near(double a,double b){finite(a);finite(b);const double e=std::abs(a-b);
  const double gate=arithmetic_abs+arithmetic_rel*std::max(std::abs(a),std::abs(b));finite(e);finite(gate);need(e<=gate,"independent affine audit mismatch");}
double coordinate(const State30& s,Count j){
  if(j<7)return s.q[j];if(j<14)return s.v[j-7];if(j<21)return s.C[j-14];if(j<28)return s.w[j-21];return j==28?s.s:s.r;
}
Count prefixWork(Count du){return sum({mul(4,mul(30,du)),mul(4,900),60});}
Count retainedWorkCapacity(Count planned,Count held,Count du){
  need(planned>=held,"normalization diagnostics exceed affine work plan");const Count remaining=planned-held;
  need(sum({90,mul(30,du),900})<=remaining,"retained diagnostics leave insufficient actual affine workspace");return remaining;
}
Count blockStride(Count du){return sum({30,mul(30,du),900});}
void matrixShape(Count rows,Count cols){need(mul(rows,cols)<=ResourcePolicyV2::matrix_entries,"affine matrix entry cap exceeded");}
}
namespace detail {
struct AffineAnchor {NormalizationOutcome normalization;explicit AffineAnchor(NormalizationOutcome&& n) noexcept:normalization(std::move(n)){} };
struct DenseStorage {
  Count lifted_slots,workspace_slots,solution_slots,selector_slots,sample_slots;
  OwnedNumericBuffer data; // One complete reservation BEFORE any audit allocation.
  DenseStorage(CaseBudget& budget,Count dx,Count du,Count dy,Count count)
    :lifted_slots(sum({mul(dx,dx),mul(dx,du),dx,mul(dx,30)})),
     workspace_slots(add(mul(8,mul(dx,dx)),mul(6,mul(dx,sum({du,30,1}))))),
     solution_slots(mul(dx,sum({du,30,1}))),selector_slots(mul(count,mul(30,dy))),
     sample_slots(mul(2,mul(count,blockStride(du)))),
     data(budget,sum({lifted_slots,workspace_slots,solution_slots,selector_slots,sample_slots})){
    std::fill_n(lifted(),lifted_slots,0.);std::fill_n(workspace(),add(mul(dx,dx),mul(dx,du+31)),0.);
    std::fill_n(solution(),solution_slots,0.);std::fill_n(selectors(),selector_slots,0.);std::fill_n(samples(),sample_slots,0.);
  }
  double* lifted(){return data.data();}
  double* workspace(){return data.data()+lifted_slots;}
  double* solution(){return data.data()+sum({lifted_slots,workspace_slots});}
  double* selectors(){return data.data()+sum({lifted_slots,workspace_slots,solution_slots});}
  double* samples(){return data.data()+sum({lifted_slots,workspace_slots,solution_slots,selector_slots});}
};
struct AffineStorage {
  std::shared_ptr<AffineAnchor> anchor;CaseBudget* budget;ResourcePlan plan;
  Count n,dx,du,dy,sample_count;AssemblyInitialKind kind;CaptureMode mode;
  Count boundary_slots,embedding_slots,work_slots,work_capacity;
  OwnedNumericBuffer data; // Whole Compact schedule reserved before allocation.
  std::unique_ptr<DenseStorage> dense;
  bool poisoned=false,streaming=false;std::string error;MathCaptureTrace trace;
  AffineStorage(std::shared_ptr<AffineAnchor> a,CaseBudget& b,const ResourcePlan& p,
                AssemblyInitialKind k,CaptureMode m)
    :anchor(std::move(a)),budget(&b),plan(p),n(p.du()/8),dx(p.dx()),du(p.du()),dy(p.dy()),
     sample_count(anchor->normalization.maps().samples().size()),kind(k),mode(m),
     boundary_slots(mul(n+1,blockStride(du))),embedding_slots(add(mul(dy,du),dy)),work_slots(prefixWork(du)),
     work_capacity(retainedWorkCapacity(work_slots,anchor->normalization.retainedDiagnosticSlots(),du)),
     data(b,sum({boundary_slots,embedding_slots,work_capacity})){
    std::fill_n(boundaries(),boundary_slots,0.);std::fill_n(embedding(),embedding_slots,0.);
    std::fill_n(work(),90+mul(30,du)+900,0.);trace.stage="DEFINED_PLACEHOLDERS";
  }
  double* boundaries(){return data.data();}
  double* embedding(){return data.data()+boundary_slots;}
  double* work(){return data.data()+add(boundary_slots,embedding_slots);}
  double& o(Count k,Count row){return boundaries()[mul(k,blockStride(du))+row];}
  double& M(Count k,Count row,Count col){return boundaries()[mul(k,blockStride(du))+30+mul(row,du)+col];}
  double& P(Count k,Count row,Count col){return boundaries()[mul(k,blockStride(du))+30+mul(30,du)+mul(row,30)+col];}
  double& T(Count row,Count col){return embedding()[mul(row,du)+col];}
  double& t(Count row){return embedding()[mul(dy,du)+row];}
  double& L(Count row,Count col){return dense->lifted()[mul(row,dx)+col];}
  double& E(Count row,Count col){return dense->lifted()[mul(dx,dx)+mul(row,du)+col];}
  double& f(Count row){return dense->lifted()[mul(dx,dx)+mul(dx,du)+row];}
  double& I(Count row,Count col){return dense->lifted()[sum({mul(dx,dx),mul(dx,du),dx,mul(row,30),col})];}
  double& X(Count row,Count col){return dense->solution()[mul(row,du+31)+col];}
  double& selector(Count sample,Count row,Count col){return dense->selectors()[mul(sample,mul(30,dy))+mul(row,dy)+col];}
  double& so(bool eliminated,Count sample,Count row){
    return dense->samples()[mul(static_cast<Count>(eliminated)*sample_count+sample,blockStride(du))+row];}
  double& sM(bool eliminated,Count sample,Count row,Count col){
    return dense->samples()[mul(static_cast<Count>(eliminated)*sample_count+sample,blockStride(du))+30+mul(row,du)+col];}
  double& sP(bool eliminated,Count sample,Count row,Count col){
    return dense->samples()[mul(static_cast<Count>(eliminated)*sample_count+sample,blockStride(du))+30+mul(30,du)+mul(row,30)+col];}
  void reject(const char* reason) noexcept{if(poisoned)return;poisoned=true;trace.complete=false;try{error=reason?reason:"AFFINE_REFUSAL";}catch(...){error.clear();}}
};
struct AffineFactory {
  static const ResourcePlan& originalPlan(const NormalizationOutcome& n){return n.maps().affinePlan();}
  static SharedCaseBudget originalBudget(const NormalizationOutcome& n){return n.maps().affineBudget().share();}
  static const FactorShape& originalShape(const NormalizationOutcome& n){return n.maps().boundCostShape();}
  static const FactorShape& shape(const NormalizedNominalMaps& m){return m.boundCostShape();}
  static const FileIdentity& identity(const NormalizedNominalMaps& m){return m.boundCostInputIdentity();}
  static const std::string& semantic(const NormalizedNominalMaps& m){return m.boundCostSemanticSha256();}
  static void compact(AffineStorage& p,const State30& initial){
    matrixShape(p.dx,p.du);matrixShape(p.dx,30);matrixShape(p.dy,p.du);
    // Every buffer is reserved before this first materialization. No raw arrays
    // or nominal future states are copied into these actual-coordinate offsets.
    p.trace.stage="CHOSEN_INITIAL";for(Count j=0;j<30;++j){p.trace.column=j;const double x=coordinate(initial,j);finite(x);p.work()[j]=x;++p.trace.written[0];}
    p.trace.stage="BOUNDARY_INITIAL";
    for(Count row=0;row<30;++row){p.trace.row=row;p.o(0,row)=0;++p.trace.written[1];
      for(Count j=0;j<p.du;++j){p.M(0,row,j)=0;++p.trace.written[2];}
      for(Count j=0;j<30;++j){p.P(0,row,j)=row==j?1:0;++p.trace.written[3];}}
    const auto& source=p.anchor->normalization.maps();
    p.trace.stage="BOUNDARY_COMPOSITION";for(Count k=0;k<p.n;++k){p.trace.item=k+1;const auto& cell=source.cells().at(k);
      for(Count row=0;row<30;++row){p.trace.row=row;
        double o=0;for(Count j=0;j<30;++j)product(cell.A()(row,j),p.o(k,j),o);
        o+=cell.defect()(row);finite(o);p.o(k+1,row)=o;++p.trace.written[1];
        for(Count col=0;col<p.du;++col){double value=0;
          for(Count j=0;j<30;++j)product(cell.A()(row,j),p.M(k,j,col),value);
          if(col>=8*k&&col<8*(k+1))value+=cell.B()(row,col-8*k);finite(value);p.M(k+1,row,col)=value;++p.trace.written[2];}
        for(Count col=0;col<30;++col){double value=0;
          for(Count j=0;j<30;++j)product(cell.A()(row,j),p.P(k,j,col),value);p.P(k+1,row,col)=value;++p.trace.written[3];}
      }
    }
    p.trace.stage="EMBEDDING";for(Count row=0;row<p.dy;++row){p.trace.row=row;
      if(row<p.dx){const Count k=row/30,j=row%30;double value=p.o(k,j);
        for(Count col=0;col<30;++col)product(p.P(k,j,col),p.work()[col],value);p.t(row)=value;++p.trace.written[4];
        for(Count col=0;col<p.du;++col){p.T(row,col)=p.M(k,j,col);++p.trace.written[5];}
      }else{p.t(row)=0;++p.trace.written[4];for(Count col=0;col<p.du;++col){p.T(row,col)=row-p.dx==col?1:0;++p.trace.written[5];}}
    }
  }
  static void sample(AffineStorage& p,Count index){
    need(index<p.sample_count,"sample index outside complete assembly");
    p.budget->chargeScratchOrCopy(prefixWork(p.du));
    p.trace.stage="SAMPLE_COMPOSITION";p.trace.item=index;p.trace.memory_item=index;p.trace.memory_stage="SAMPLE_COMPOSITION";
    for(Count j=6;j<=9;++j)p.trace.written[j]=0;
    std::fill_n(p.work()+30,60+mul(30,p.du)+900,0.);
    const auto& view=p.anchor->normalization.maps().samples().at(index);const Count k=view.cell();
    double* work=p.work();
    for(Count row=0;row<30;++row){
      double value=0;for(Count j=0;j<30;++j)product(view.A()(row,j),p.o(k,j),value);
      value+=view.defect()(row);finite(value);work[30+row]=value;++p.trace.written[6];
      for(Count col=0;col<p.du;++col){double m=0;
        for(Count j=0;j<30;++j)product(view.A()(row,j),p.M(k,j,col),m);
        if(col>=8*k&&col<8*(k+1))m+=view.B()(row,col-8*k);finite(m);work[90+mul(row,p.du)+col]=m;++p.trace.written[7];}
      for(Count col=0;col<30;++col){double m=0;
        for(Count j=0;j<30;++j)product(view.A()(row,j),p.P(k,j,col),m);work[90+mul(30,p.du)+mul(row,30)+col]=m;++p.trace.written[8];}
      for(Count col=0;col<30;++col)product(work[90+mul(30,p.du)+mul(row,30)+col],work[col],value);
      work[60+row]=value;++p.trace.written[9];
    }
  }
  static void denseAudit(AffineStorage& p){
    const Count rhs=p.du+31;
    matrixShape(p.dx,p.dx);matrixShape(p.dx,p.du);matrixShape(p.dx,30);matrixShape(30,p.dy);
    // Whole requested audit allocation occurs before matrix writes/factorization.
    p.trace.stage="DENSE_ALLOCATION";p.dense=std::make_unique<DenseStorage>(*p.budget,p.dx,p.du,p.dy,p.sample_count);
    p.trace.stage="DENSE_LIFTED";
    const auto& source=p.anchor->normalization.maps();
    for(Count row=0;row<p.dx;++row){const Count k=row/30,r=row%30;
      for(Count col=0;col<p.dx;++col){double v=row==col?1:0;
        if(k>0&&col/30==k-1)v=-source.cells().at(k-1).A()(r,col%30);p.L(row,col)=v;++p.trace.written[10];}
      for(Count col=0;col<p.du;++col){p.E(row,col)=k>0&&col/8==k-1?source.cells().at(k-1).B()(r,col%8):0;++p.trace.written[11];}
      p.f(row)=k==0?0:source.cells().at(k-1).defect()(r);++p.trace.written[12];
      for(Count col=0;col<30;++col){p.I(row,col)=k==0&&r==col?1:0;++p.trace.written[13];}
    }
    p.trace.stage="DENSE_WORK_COPY";double* LU=p.dense->workspace();double* R=LU+mul(p.dx,p.dx);
    // This is the workspace's first materialization, priced by its owned
    // reservation. Elimination updates it in place; scalar FLOPs are not extra
    // allocations/copies and no Eigen solver/work temporary is used.
    for(Count row=0;row<p.dx;++row){for(Count col=0;col<p.dx;++col){LU[mul(row,p.dx)+col]=p.L(row,col);++p.trace.written[14];}
      for(Count col=0;col<rhs;++col){R[mul(row,rhs)+col]=col<p.du?p.E(row,col):col==p.du?p.f(row):p.I(row,col-p.du-1);++p.trace.written[15];}}
    p.trace.stage="DENSE_ELIMINATION_IN_PLACE";for(Count pivot=0;pivot<p.dx;++pivot){p.trace.item=pivot;p.trace.row=pivot;p.trace.column=pivot;p.trace.stage="DENSE_PIVOT_SELECT";
      Count selected=pivot;double largest=std::abs(LU[mul(pivot,p.dx)+pivot]);finite(largest);
      for(Count row=pivot+1;row<p.dx;++row){p.trace.row=row;const double v=std::abs(LU[mul(row,p.dx)+pivot]);finite(v);
        if(v>largest){largest=v;selected=row;}}
      need(largest>0,"singular independent lifted audit");
      if(selected!=pivot){p.trace.stage="DENSE_SWAP_LU";for(Count col=0;col<p.dx;++col){p.trace.column=col;std::swap(LU[mul(selected,p.dx)+col],LU[mul(pivot,p.dx)+col]);}
        p.trace.stage="DENSE_SWAP_RHS";for(Count col=0;col<rhs;++col){p.trace.column=col;std::swap(R[mul(selected,rhs)+col],R[mul(pivot,rhs)+col]);}}
      const double diagonal=LU[mul(pivot,p.dx)+pivot];finite(diagonal);need(diagonal!=0,"zero pivot in lifted audit");
      for(Count row=pivot+1;row<p.dx;++row){p.trace.row=row;p.trace.column=pivot;p.trace.stage="DENSE_LU_SCALE";const double scale=LU[mul(row,p.dx)+pivot]/diagonal;finite(scale);LU[mul(row,p.dx)+pivot]=scale;
        for(Count col=pivot+1;col<p.dx;++col){p.trace.column=col;p.trace.stage="DENSE_LU_UPDATE";const double q=scale*LU[mul(pivot,p.dx)+col];finite(q);LU[mul(row,p.dx)+col]-=q;finite(LU[mul(row,p.dx)+col]);}
        for(Count col=0;col<rhs;++col){p.trace.column=col;p.trace.stage="DENSE_RHS_UPDATE";const double q=scale*R[mul(pivot,rhs)+col];finite(q);R[mul(row,rhs)+col]-=q;finite(R[mul(row,rhs)+col]);}}
    }
    p.trace.stage="DENSE_BACK_SUBSTITUTION";for(Count col=0;col<rhs;++col)for(Count remaining=p.dx;remaining>0;--remaining){const Count row=remaining-1;p.trace.column=col;p.trace.row=row;
      double v=R[mul(row,rhs)+col];for(Count k=row+1;k<p.dx;++k){p.trace.stage="DENSE_BACKSUB_PRODUCT";p.trace.addition=k;const double q=LU[mul(row,p.dx)+k]*p.X(k,col);finite(q);v-=q;finite(v);}
      p.trace.stage="DENSE_BACKSUB_DIVIDE";v/=LU[mul(row,p.dx)+row];finite(v);p.X(row,col)=v;++p.trace.written[16];}
    p.trace.stage="DENSE_RESIDUAL_AUDIT";for(Count row=0;row<p.dx;++row)for(Count col=0;col<rhs;++col){p.trace.row=row;p.trace.column=col;double residual=0;
      p.trace.stage="DENSE_RESIDUAL_PRODUCT";for(Count k=0;k<p.dx;++k){p.trace.addition=k;product(p.L(row,k),p.X(k,col),residual);}
      p.trace.stage="DENSE_RESIDUAL_COMPARE";
      near(residual,col<p.du?p.E(row,col):col==p.du?p.f(row):p.I(row,col-p.du-1));
      p.trace.stage="DENSE_SOLUTION_COMPARE";near(p.X(row,col),col<p.du?p.M(row/30,row%30,col):col==p.du?p.o(row/30,row%30):p.P(row/30,row%30,col-p.du-1));}
    p.trace.stage="DENSE_SAMPLE_AUDIT";for(Count index=0;index<p.sample_count;++index){p.trace.item=index;const auto& v=source.samples().at(index);const Count cell=v.cell();
      for(Count row=0;row<30;++row){
        for(Count col=0;col<p.dy;++col){double value=0;
          if(col<p.dx&&col/30==cell)value=v.A()(row,col%30);
          if(col>=p.dx&&(col-p.dx)/8==cell)value=v.B()(row,(col-p.dx)%8);p.selector(index,row,col)=value;++p.trace.written[17];}
        for(bool eliminated:{false,true}){
          double o=0;for(Count j=0;j<30;++j)product(v.A()(row,j),eliminated?p.X(30*cell+j,p.du):p.o(cell,j),o);
          o+=v.defect()(row);finite(o);p.so(eliminated,index,row)=o;++p.trace.written[18+static_cast<Count>(eliminated)*3];
          for(Count col=0;col<p.du;++col){double m=0;
            for(Count j=0;j<30;++j)product(v.A()(row,j),eliminated?p.X(30*cell+j,col):p.M(cell,j,col),m);
            if(col>=8*cell&&col<8*(cell+1))m+=v.B()(row,col-8*cell);finite(m);p.sM(eliminated,index,row,col)=m;++p.trace.written[19+static_cast<Count>(eliminated)*3];}
          for(Count col=0;col<30;++col){double value=0;
            for(Count j=0;j<30;++j)product(v.A()(row,j),eliminated?p.X(30*cell+j,p.du+1+col):p.P(cell,j,col),value);
            p.sP(eliminated,index,row,col)=value;++p.trace.written[20+static_cast<Count>(eliminated)*3];}
        }
        near(p.so(false,index,row),p.so(true,index,row));
        for(Count col=0;col<p.du;++col)near(p.sM(false,index,row,col),p.sM(true,index,row,col));
        for(Count col=0;col<30;++col)near(p.sP(false,index,row,col),p.sP(true,index,row,col));
      }
    }
  }
  static AffineAssemblyOutcome assemble(NormalizationOutcome&& source,CaptureMode request,
                                        AssemblyInitialKind kind,const State30* algebra){
    AffineAssemblyOutcome out(std::move(source),request,kind);
    std::unique_ptr<AffineStorage> data;
    try{
      need(out.original_.hasFullNominalMaps(),"full genuine normalization required for affine assembly");
      const auto& maps=out.original_.maps();auto& budget=maps.affineBudget();const auto& plan=maps.affinePlan();
      need((request==CaptureMode::CompactComplete||request==CaptureMode::DenseAuditComplete)&&request==plan.captureMode(),
           "requested mode differs from bound whole-case plan; no fallback");
      matrixShape(plan.dx(),plan.du());matrixShape(plan.dx(),30);matrixShape(plan.dy(),plan.du());
      const State30& initial=algebra?*algebra:maps.originalForecast().actualContext().actualInitial();
      out.anchor_=std::make_shared<AffineAnchor>(std::move(out.original_));
      data=std::make_unique<AffineStorage>(out.anchor_,budget,plan,kind,request);
      compact(*data,initial);
      if(request==CaptureMode::DenseAuditComplete)denseAudit(*data);
      data->trace.stage="COMPLETE_AFFINE";data->trace.complete=true;data->trace.construction_completed=true;out.assembly_.reset(new CompactAffineAssembly(std::move(data)));
    }catch(const std::exception& e){if(data)data->reject(e.what());out.failed_=std::move(data);out.recordRefusal(e.what());}
    catch(...){if(data)data->reject("NONSTANDARD_AFFINE_BUILD_FAILURE");out.failed_=std::move(data);out.recordRefusal("NONSTANDARD_AFFINE_BUILD_FAILURE");}
    return out;
  }
  static void stream(AffineStorage& p,Count index,const std::function<void(const SampleAffineView&)>& callback){
    need(!p.poisoned,"affine assembly previously refused");
    try{
      need(!p.streaming&&static_cast<bool>(callback),"sample stream reentry/empty callback refused");
      struct StreamGuard{bool& active;explicit StreamGuard(bool& a):active(a){active=true;}~StreamGuard(){active=false;}} guard(p.streaming);
      sample(p,index);const auto& v=p.anchor->normalization.maps().samples().at(index);
      const SampleAffineView view(v.cell(),v.physicalTick(),p.du,p.work());callback(view);
      need(!p.poisoned,"nested stream refusal retained");
    }catch(const std::exception& e){p.reject(e.what());throw;}
    catch(...){p.reject("NONSTANDARD_SAMPLE_CALLBACK_FAILURE");throw;}
  }
};
} // namespace detail

namespace {
detail::AffineStorage& present(const std::unique_ptr<detail::AffineStorage>& p){need(p&&!p->poisoned&&p->anchor->normalization.hasFullNominalMaps(),"affine assembly/source missing/refused/moved");return *p;}
detail::AffineStorage& dense(const std::unique_ptr<detail::AffineStorage>& p){auto& s=present(p);need(s.mode==CaptureMode::DenseAuditComplete&&s.dense,"DenseAudit data not requested/completed");return s;}
void row(Count r){need(r<30,"state row outside30");}
void bounds(Count a,Count cap){need(a<cap,"affine index outside declared shape");}
}
SampleAffineView::SampleAffineView(Count cell,Count tick,Count du,const double* work):cell_(cell),tick_(tick),du_(du),work_(work){}
double SampleAffineView::offset(Count r) const{row(r);return work_[30+r];}
double SampleAffineView::actualOffset(Count r) const{row(r);return work_[60+r];}
double SampleAffineView::control(Count r,Count c) const{row(r);bounds(c,du_);return work_[90+mul(r,du_)+c];}
double SampleAffineView::initial(Count r,Count c) const{row(r);bounds(c,30);return work_[90+mul(30,du_)+mul(r,30)+c];}
CompactAffineAssembly::CompactAffineAssembly(std::unique_ptr<detail::AffineStorage> p):storage_(std::move(p)){}
CompactAffineAssembly::CompactAffineAssembly(CompactAffineAssembly&&) noexcept=default;
CompactAffineAssembly& CompactAffineAssembly::operator=(CompactAffineAssembly&&) noexcept=default;
CompactAffineAssembly::~CompactAffineAssembly()=default;
bool CompactAffineAssembly::complete() const noexcept{return storage_&&!storage_->poisoned&&storage_->anchor->normalization.hasFullNominalMaps();}
Count CompactAffineAssembly::cells() const{return present(storage_).n;}
Count CompactAffineAssembly::dx() const{return present(storage_).dx;}
Count CompactAffineAssembly::du() const{return present(storage_).du;}
Count CompactAffineAssembly::dy() const{return present(storage_).dy;}
AssemblyInitialKind CompactAffineAssembly::initialKind() const{return present(storage_).kind;}
CaptureMode CompactAffineAssembly::mode() const{return present(storage_).mode;}
double CompactAffineAssembly::chosenInitial(Count c) const{bounds(c,30);return present(storage_).work()[c];}
double CompactAffineAssembly::boundaryOffset(Count k,Count r) const{auto& s=present(storage_);bounds(k,s.n+1);row(r);return s.o(k,r);}
double CompactAffineAssembly::boundaryControl(Count k,Count r,Count c) const{auto& s=present(storage_);bounds(k,s.n+1);row(r);bounds(c,s.du);return s.M(k,r,c);}
double CompactAffineAssembly::boundaryInitial(Count k,Count r,Count c) const{auto& s=present(storage_);bounds(k,s.n+1);row(r);bounds(c,30);return s.P(k,r,c);}
double CompactAffineAssembly::embeddingControl(Count r,Count c) const{auto& s=present(storage_);bounds(r,s.dy);bounds(c,s.du);return s.T(r,c);}
double CompactAffineAssembly::embeddingOffset(Count r) const{auto& s=present(storage_);bounds(r,s.dy);return s.t(r);}
double CompactAffineAssembly::embeddingInitial(Count r,Count c) const{auto& s=present(storage_);bounds(r,s.dy);bounds(c,30);return r<s.dx?s.P(r/30,r%30,c):0;}
void CompactAffineAssembly::withSample(Count k,const std::function<void(const SampleAffineView&)>& callback){detail::AffineFactory::stream(present(storage_),k,callback);}
std::string_view CompactAffineAssembly::refusal() const noexcept{
  if(storage_&&storage_->poisoned)return storage_->error.empty()?std::string_view("AFFINE_REFUSAL_UNRECORDED_DETAIL"):std::string_view(storage_->error);
  if(storage_&&!storage_->anchor->normalization.hasFullNominalMaps())return storage_->anchor->normalization.refusal();return {};
}
double CompactAffineAssembly::liftedL(Count r,Count c) const{auto& s=dense(storage_);bounds(r,s.dx);bounds(c,s.dx);return s.L(r,c);}
double CompactAffineAssembly::liftedE(Count r,Count c) const{auto& s=dense(storage_);bounds(r,s.dx);bounds(c,s.du);return s.E(r,c);}
double CompactAffineAssembly::liftedOffset(Count r) const{auto& s=dense(storage_);bounds(r,s.dx);return s.f(r);}
double CompactAffineAssembly::liftedInitialSelector(Count r,Count c) const{auto& s=dense(storage_);bounds(r,s.dx);bounds(c,30);return s.I(r,c);}
double CompactAffineAssembly::eliminatedControl(Count r,Count c) const{auto& s=dense(storage_);bounds(r,s.dx);bounds(c,s.du);return s.X(r,c);}
double CompactAffineAssembly::eliminatedOffset(Count r) const{auto& s=dense(storage_);bounds(r,s.dx);return s.X(r,s.du);}
double CompactAffineAssembly::eliminatedInitial(Count r,Count c) const{auto& s=dense(storage_);bounds(r,s.dx);bounds(c,30);return s.X(r,s.du+1+c);}
double CompactAffineAssembly::sampleDenseSelector(Count k,Count r,Count c) const{auto& s=dense(storage_);bounds(k,s.sample_count);row(r);bounds(c,s.dy);return s.selector(k,r,c);}
double CompactAffineAssembly::auditSampleControl(bool e,Count k,Count r,Count c) const{auto& s=dense(storage_);bounds(k,s.sample_count);row(r);bounds(c,s.du);return s.sM(e,k,r,c);}
double CompactAffineAssembly::auditSampleOffset(bool e,Count k,Count r) const{auto& s=dense(storage_);bounds(k,s.sample_count);row(r);return s.so(e,k,r);}
double CompactAffineAssembly::auditSampleInitial(bool e,Count k,Count r,Count c) const{auto& s=dense(storage_);bounds(k,s.sample_count);row(r);bounds(c,30);return s.sP(e,k,r,c);}
const NormalizationOutcome& CompactAffineAssembly::originalNormalization() const{need(static_cast<bool>(storage_),"moved affine owner");return storage_->anchor->normalization;}
std::shared_ptr<const void> CompactAffineAssembly::captureOriginToken() const{return std::static_pointer_cast<const void>(present(storage_).anchor);}
CaseBudget& CompactAffineAssembly::costBudget() const{return *present(storage_).budget;}
const ResourcePlan& CompactAffineAssembly::costPlan() const{return present(storage_).plan;}
const FactorShape& CompactAffineAssembly::boundCostShape() const{return detail::AffineFactory::shape(present(storage_).anchor->normalization.maps());}
const FileIdentity& CompactAffineAssembly::boundCostInputIdentity() const{return detail::AffineFactory::identity(present(storage_).anchor->normalization.maps());}
const std::string& CompactAffineAssembly::boundCostSemanticSha256() const{return detail::AffineFactory::semantic(present(storage_).anchor->normalization.maps());}
const std::array<bool,7>& CompactAffineAssembly::scopeClaims() noexcept{static const std::array<bool,7> flags{};return flags;}
AffineAssemblyOutcome::AffineAssemblyOutcome(NormalizationOutcome&& n,CaptureMode m,AssemblyInitialKind k) noexcept:original_(std::move(n)),requested_(m),kind_(k){}
AffineAssemblyOutcome::AffineAssemblyOutcome(AffineAssemblyOutcome&&) noexcept=default;
AffineAssemblyOutcome& AffineAssemblyOutcome::operator=(AffineAssemblyOutcome&&) noexcept=default;
AffineAssemblyOutcome::~AffineAssemblyOutcome()=default;
bool AffineAssemblyOutcome::hasCompleteAssembly() const noexcept{return !refused_&&assembly_&&assembly_->complete();}
CompactAffineAssembly& AffineAssemblyOutcome::assembly(){need(hasCompleteAssembly(),"complete affine assembly refused/moved");return *assembly_;}
const CompactAffineAssembly& AffineAssemblyOutcome::assembly() const{need(hasCompleteAssembly(),"complete affine assembly refused/moved");return *assembly_;}
std::shared_ptr<const void> AffineAssemblyOutcome::captureOriginToken() const{return std::static_pointer_cast<const void>(anchor_);}
const ResourcePlan& AffineAssemblyOutcome::capturePlan() const{
  if(assembly_&&assembly_->storage_)return assembly_->storage_->plan;if(failed_)return failed_->plan;
  return detail::AffineFactory::originalPlan(originalNormalization());
}
const FactorShape& AffineAssemblyOutcome::captureShape() const{return detail::AffineFactory::originalShape(originalNormalization());}
SharedCaseBudget AffineAssemblyOutcome::captureBudget() const{
  if(assembly_&&assembly_->storage_)return assembly_->storage_->budget->share();if(failed_)return failed_->budget->share();
  return detail::AffineFactory::originalBudget(originalNormalization());
}
const NormalizationOutcome& AffineAssemblyOutcome::originalNormalization() const{return anchor_?anchor_->normalization:original_;}
std::optional<CaptureMode> AffineAssemblyOutcome::actualMode() const noexcept{return hasCompleteAssembly()?std::optional<CaptureMode>(requested_):std::nullopt;}
std::string_view AffineAssemblyOutcome::refusal() const noexcept{if(assembly_&&!assembly_->complete())return assembly_->refusal();
  return refused_?(refusal_detail_.empty()?std::string_view("AFFINE_REFUSAL_UNRECORDED_DETAIL"):std::string_view(refusal_detail_)):std::string_view{};}
bool AffineAssemblyOutcome::hasRetainedRegions() const noexcept{return (assembly_&&assembly_->storage_)||static_cast<bool>(failed_);}
void AffineAssemblyOutcome::withRetainedRegions(const RetainedRegionConsumer& callback) const{
  auto* p=assembly_?assembly_->storage_.get():failed_.get();need(p,"retained affine regions absent");
  if(!callback||p->streaming){p->reject("retained affine callback reentry/empty callback");throw std::invalid_argument("retained affine callback reentry/empty callback");}
  p->trace.complete=!p->poisoned&&p->anchor->normalization.hasFullNominalMaps()&&p->trace.construction_completed;
  struct Guard{bool& active;Guard(bool& b):active(b){active=true;}~Guard(){active=false;}} guard(p->streaming);
  auto emit=[&](const char* role,const double* data,Count n){const RetainedNumericRegionView v(role,data,n,p->trace,p->streaming);callback(v);};
  try{emit("affine.boundary",p->boundaries(),p->boundary_slots);emit("affine.embedding",p->embedding(),p->embedding_slots);
    emit("affine.chosen_initial_and_current_sample",p->work(),90+mul(30,p->du)+900);
    if(p->dense){emit("dense.lifted",p->dense->lifted(),p->dense->lifted_slots);
      emit("dense.active_LU_R",p->dense->workspace(),add(mul(p->dx,p->dx),mul(p->dx,p->du+31)));
      emit("dense.solution",p->dense->solution(),p->dense->solution_slots);emit("dense.selectors",p->dense->selectors(),p->dense->selector_slots);
      emit("dense.sample_maps",p->dense->samples(),p->dense->sample_slots);}
  }catch(const std::exception& e){p->reject(e.what());throw;}catch(...){p->reject("NONSTANDARD_AFFINE_CAPTURE_CALLBACK_FAILURE");throw;}
}
void AffineAssemblyOutcome::recordRefusal(const char* reason) noexcept{assembly_.reset();refused_=true;
  try{refusal_detail_=reason?reason:"AFFINE_REFUSAL";}catch(...){refusal_detail_.clear();}}
AffineAssemblyOutcome assembleLiveAffine(NormalizationOutcome&& n,CaptureMode m){return detail::AffineFactory::assemble(std::move(n),m,AssemblyInitialKind::LiveActual,nullptr);}
AffineAssemblyOutcome assembleAlgebraAffine(NormalizationOutcome&& n,const AlgebraTestInitial& x,CaptureMode m){return detail::AffineFactory::assemble(std::move(n),m,AssemblyInitialKind::AlgebraTest,&x.point());}
} // namespace phase5_public_live_affine_v2
