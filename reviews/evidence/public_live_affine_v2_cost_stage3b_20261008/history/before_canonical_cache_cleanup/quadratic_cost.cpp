#include "quadratic_cost.hpp"
#include <openssl/evp.h>
#include <algorithm>
#include <array>
#include <cmath>
#include <cstring>
#include <initializer_list>
#include <limits>
#include <stdexcept>
#include <utility>

namespace phase5_public_live_affine_v2 {
namespace {
void need(bool b,const char* s){if(!b)throw std::invalid_argument(s);}
Count mul(Count a,Count b){return checkedMultiply(a,b);}Count add(Count a,Count b){return checkedAdd(a,b);}
Count sum(std::initializer_list<Count> v){Count s=0;for(Count x:v)s=add(s,x);return s;}
void finite(double x){need(std::isfinite(x),"nonfinite cost input/product/sum");}
void product(double a,double b,double& value){double p=a*b;finite(p);value+=p;finite(value);}
void near(double a,double b){finite(a);finite(b);double e=std::abs(a-b),g=2e-13+2e-13*std::max(std::abs(a),std::abs(b));finite(e);finite(g);need(e<=g,"direct/condensed cost identity mismatch");}
double halfFirst(double a,double b){const double result=.5*a+.5*b;finite(result);return result;}
void bounds(Count i,Count n){need(i<n,"cost index outside retained shape");}
struct SemanticHash {
  std::unique_ptr<EVP_MD_CTX,decltype(&EVP_MD_CTX_free)> context{EVP_MD_CTX_new(),EVP_MD_CTX_free};
  SemanticHash(){need(context&&EVP_DigestInit_ex(context.get(),EVP_sha256(),nullptr)==1,"semantic SHA init");}
  void bytes(const void* p,std::size_t n){need(EVP_DigestUpdate(context.get(),p,n)==1,"semantic SHA update");}
  void integer(Count n){std::array<unsigned char,8> b{};for(int j=0;j<8;++j)b[j]=static_cast<unsigned char>((n>>(8*j))&255);bytes(b.data(),b.size());}
  void text(const std::string& s){integer(s.size());bytes(s.data(),s.size());}
  void number(double x){static_assert(sizeof(double)==8&&std::numeric_limits<double>::is_iec559,"IEEE754double required");
    finite(x);Count bits=0;std::memcpy(&bits,&x,8);integer(bits);}
  std::string finish(){std::array<unsigned char,EVP_MAX_MD_SIZE> b{};unsigned int n=0;
    need(EVP_DigestFinal_ex(context.get(),b.data(),&n)==1&&n==32,"semantic SHA final");constexpr char h[]="0123456789abcdef";
    std::string s;for(unsigned j=0;j<n;++j){s.push_back(h[b[j]>>4]);s.push_back(h[b[j]&15]);}return s;}
};
void name(const std::string& s){need(!s.empty()&&s.size()<=256&&s.find('\0')==std::string::npos,"bounded cost name/units required");}
struct TermOffsets {Count F=0,f0=0,linear=0,c0=0,row_base=0;std::vector<Count> additions;};
}
namespace detail {
struct CostAnchor {
  AffineAssemblyOutcome assembly;CostInputRecipe recipe;
  CostAnchor(AffineAssemblyOutcome&& a,CostInputRecipe&& r) noexcept:assembly(std::move(a)),recipe(std::move(r)){}
};
struct CostStorage {
  std::shared_ptr<CostAnchor> anchor;CaseBudget* budget;ResourcePlan plan;FactorShape shape;
  Count du,dy,dx,input_slots,capture_slots,work_slots;std::vector<TermOffsets> offsets;
  OwnedNumericBuffer data;std::string semantic,error;bool poisoned=false,callback_active=false,input_complete=false;
  Count input_initialized=0,active_term=0,active_addition=0;
  bool canonical_evaluation=false;double direct_value=0,condensed_value=0;
  CostStorage(std::shared_ptr<CostAnchor> a,CaseBudget& b,const ResourcePlan& p,const FactorShape& f)
    :anchor(std::move(a)),budget(&b),plan(p),shape(f),du(p.du()),dy(p.dy()),dx(p.dx()),
     input_slots(sum({mul(f.rows,dy),f.rows,mul(f.terms,dy),f.terms,f.addition_coefficients,f.addition_coefficients/30,mul(f.addition_records,4)})),
     capture_slots(sum({mul(f.rows,du+1),mul(f.terms,sum({mul(du,du),du,1})),mul(du,du),du,dy,1})),
     work_slots(sum({mul(4,mul(f.largest_term_rows,dy)),mul(4,mul(f.largest_term_rows,du)),mul(4,mul(du,du)),mul(2,mul(dy,du))})),
     data(b,sum({input_slots,capture_slots,work_slots})){}
  double* input(){return data.data();}double* capture(){return data.data()+input_slots;}
  double* work(){return data.data()+input_slots+capture_slots;}
  Count usedFBase() const{return du+1;}
  Count used0Base() const{return add(usedFBase(),mul(shape.largest_term_rows,dy));}
  Count residualBase() const{return add(used0Base(),shape.largest_term_rows);}
  Count yBase() const{return add(residualBase(),shape.largest_term_rows);}
  Count gyBase() const{return add(yBase(),dy);}
  Count directRowBase() const{return add(gyBase(),dy);}
  Count interBase() const{return add(directRowBase(),mul(shape.largest_term_rows,du));}
  Count directHBase() const{return add(interBase(),mul(dy,du));}
  Count sumHBase() const{return add(directHBase(),mul(du,du));}
  Count directGBase() const{return add(sumHBase(),mul(du,du));}
  Count condensedGBase() const{return add(directGBase(),du);}
  Count sumGBase() const{return add(condensedGBase(),du);}
  double& usedF(Count r,Count c){return work()[usedFBase()+mul(r,dy)+c];}
  double& used0(Count r){return work()[used0Base()+r];}
  double& Fc(Count row,Count c){return capture()[mul(row,du)+c];}
  double& fc(Count row){return capture()[mul(shape.rows,du)+row];}
  Count termHBase() const{return mul(shape.rows,du+1);}
  double& H(Count k,Count r,Count c){return capture()[termHBase()+mul(k,mul(du,du))+mul(r,du)+c];}
  Count termGBase() const{return add(termHBase(),mul(shape.terms,mul(du,du)));}
  double& g(Count k,Count c){return capture()[termGBase()+mul(k,du)+c];}
  Count termCBase() const{return add(termGBase(),mul(shape.terms,du));}
  double& constant(Count k){return capture()[termCBase()+k];}
  Count sumBase() const{return add(termCBase(),shape.terms);}
  double& sumH(Count r,Count c){return capture()[sumBase()+mul(r,du)+c];}
  double& sumg(Count c){return capture()[sumBase()+mul(du,du)+c];}
  double& suml(Count c){return capture()[sumBase()+mul(du,du)+du+c];}
  double& sumc(){return capture()[sumBase()+mul(du,du)+du+dy];}
  void reject(const char* why) noexcept{if(poisoned)return;poisoned=true;try{error=why?why:"COST_REFUSAL";}catch(...){error.clear();}}
};
struct CostFactory {
  static FactorShape shape(const CostInputRecipe& input,CompactAffineAssembly& assembly){
    FactorShape f;f.terms=input.terms.size();need(f.terms<=32,"term roster cap");
    for(const auto& t:input.terms){name(t.name);name(t.units);need(t.rows<=256,"parent term row cap");
      f.rows=add(f.rows,t.rows);f.largest_term_rows=std::max(f.largest_term_rows,t.rows);
      for(const auto& a:t.additions){need(a.sample_index<assembly.originalNormalization().maps().samples().size()&&
        !a.parent_rows.empty()&&a.parent_rows.size()<=t.rows,"sample addition parent/embed shape");
        for(Count r:a.parent_rows)bounds(r,t.rows);
        f.addition_records=add(f.addition_records,1);f.addition_coefficients=add(f.addition_coefficients,mul(a.parent_rows.size(),30));}
    }
    const auto& expected=assembly.boundCostShape();
    need(f.terms==expected.terms&&f.rows==expected.rows&&f.largest_term_rows==expected.largest_term_rows&&
      f.addition_coefficients==expected.addition_coefficients&&f.addition_records==expected.addition_records,
      "actual cost shapes differ from frozen bound invocation");
    need(input.file.path==assembly.boundCostInputIdentity().path&&input.file.sha256==assembly.boundCostInputIdentity().sha256&&
      input.file.bytes==assembly.boundCostInputIdentity().bytes,"opaque cost input identity differs from frozen invocation");
    auto observed=observePinnedFile(input.file.path,input.file.sha256);need(observed.bytes==input.file.bytes,"cost input file length mismatch");
    return f;
  }
  static void ingest(CostStorage& p){
    need(static_cast<bool>(p.anchor->recipe.read_scalar),"bounded scalar input reader required");
    auto& assembly=p.anchor->assembly.assembly();SemanticHash hash;
    hash.text("PUBLIC_LIVE_AFFINE_V2_COST_SEMANTIC_1");hash.integer(p.dy);hash.integer(p.du);
    hash.integer(static_cast<Count>(assembly.initialKind()));for(Count j=0;j<30;++j)hash.number(assembly.chosenInitial(j));
    hash.integer(p.shape.terms);Count scalar=0,cursor=0,row_base=0;
    auto copy=[&](){const double x=p.anchor->recipe.read_scalar(scalar++);finite(x);hash.number(x);
      need(cursor<p.input_slots,"cost input numeric storage shape");p.input()[cursor++]=x;p.input_initialized=cursor;};
    p.offsets.reserve(p.shape.terms);
    for(const auto& term:p.anchor->recipe.terms){
      hash.text(term.name);hash.text(term.units);hash.integer(term.rows);TermOffsets o;o.row_base=row_base;
      o.F=cursor;for(Count j=0;j<mul(term.rows,p.dy);++j)copy();
      o.f0=cursor;for(Count j=0;j<term.rows;++j)copy();
      o.linear=cursor;for(Count j=0;j<p.dy;++j)copy();o.c0=cursor;copy();
      hash.integer(term.additions.size());
      for(const auto& addition:term.additions){hash.integer(addition.sample_index);hash.integer(addition.parent_rows.size());
        for(Count row:addition.parent_rows)hash.integer(row);o.additions.push_back(cursor);
        for(Count j=0;j<mul(addition.parent_rows.size(),30);++j)copy();}
      p.offsets.push_back(std::move(o));row_base=add(row_base,term.rows);
    }
    hash.integer(p.du);for(Count j=0;j<p.du;++j){const double x=p.anchor->recipe.read_scalar(scalar++);finite(x);p.work()[j]=x;hash.number(x);}
    p.semantic=hash.finish();need(p.semantic==assembly.boundCostSemanticSha256(),"complete typed cost semantic SHA mismatch");
    auto observed=observePinnedFile(p.anchor->recipe.file.path,p.anchor->recipe.file.sha256);need(observed.bytes==p.anchor->recipe.file.bytes,"cost file changed during ingest");
    p.input_complete=true;
  }
  static void used(CostStorage& p,Count k){
    p.active_term=k;const auto& term=p.anchor->recipe.terms.at(k);const auto& o=p.offsets.at(k);
    p.budget->chargeScratchOrCopy(p.work_slots);
    for(Count row=0;row<term.rows;++row){p.used0(row)=p.input()[o.f0+row];
      for(Count col=0;col<p.dy;++col)p.usedF(row,col)=p.input()[o.F+mul(row,p.dy)+col];}
    const auto& maps=p.anchor->assembly.originalNormalization().maps();
    for(Count a=0;a<term.additions.size();++a){p.active_addition=a;const auto& layout=term.additions[a];const auto& sample=maps.samples().at(layout.sample_index);
      for(Count r=0;r<layout.parent_rows.size();++r){const Count target=layout.parent_rows[r];
        for(Count col=0;col<30;++col){double value=0;for(Count j=0;j<30;++j)product(p.input()[o.additions[a]+mul(r,30)+j],sample.A()(j,col),value);
          p.usedF(target,30*sample.cell()+col)+=value;finite(p.usedF(target,30*sample.cell()+col));}
        for(Count col=0;col<8;++col){double value=0;for(Count j=0;j<30;++j)product(p.input()[o.additions[a]+mul(r,30)+j],sample.B()(j,col),value);
          p.usedF(target,p.dx+8*sample.cell()+col)+=value;finite(p.usedF(target,p.dx+8*sample.cell()+col));}
        double value=0;for(Count j=0;j<30;++j)product(p.input()[o.additions[a]+mul(r,30)+j],sample.defect()(j),value);
        p.used0(target)+=value;finite(p.used0(target));
      }
    }
  }
  static void condense(CostStorage& p,Count k){
    const auto& t=p.anchor->recipe.terms[k];const auto& o=p.offsets[k];auto& a=p.anchor->assembly.assembly();
    for(Count r=0;r<t.rows;++r){double value=p.used0(r);for(Count j=0;j<p.dy;++j)product(p.usedF(r,j),a.embeddingOffset(j),value);p.fc(o.row_base+r)=value;
      for(Count c=0;c<p.du;++c){double f=0;for(Count j=0;j<p.dy;++j)product(p.usedF(r,j),a.embeddingControl(j,c),f);p.Fc(o.row_base+r,c)=f;}}
    for(Count r=0;r<p.du;++r){
      for(Count c=0;c<p.du;++c){double h=0;for(Count j=0;j<t.rows;++j)product(p.Fc(o.row_base+j,r),p.Fc(o.row_base+j,c),h);p.H(k,r,c)=h;}
      double g=0;for(Count j=0;j<t.rows;++j)product(p.Fc(o.row_base+j,r),p.fc(o.row_base+j),g);
      for(Count j=0;j<p.dy;++j)product(a.embeddingControl(j,r),p.input()[o.linear+j],g);p.g(k,r)=g;
    }
    double squares=0;for(Count j=0;j<t.rows;++j)product(p.fc(o.row_base+j),p.fc(o.row_base+j),squares);
    double constant=.5*squares;finite(constant);for(Count j=0;j<p.dy;++j)product(p.input()[o.linear+j],a.embeddingOffset(j),constant);
    constant+=p.input()[o.c0];finite(constant);p.constant(k)=constant;
  }
  static void evaluateTerm(CostStorage& p,Count k){
    const auto& t=p.anchor->recipe.terms[k];const auto& o=p.offsets[k];auto& a=p.anchor->assembly.assembly();
    for(Count j=0;j<p.dy;++j){double y=a.embeddingOffset(j);for(Count c=0;c<p.du;++c)product(a.embeddingControl(j,c),p.work()[c],y);p.work()[p.yBase()+j]=y;}
    double squares=0;
    for(Count r=0;r<t.rows;++r){double residual=p.used0(r);for(Count j=0;j<p.dy;++j)product(p.usedF(r,j),p.work()[p.yBase()+j],residual);
      p.work()[p.residualBase()+r]=residual;product(residual,residual,squares);}
    p.direct_value=.5*squares;finite(p.direct_value);
    for(Count j=0;j<p.dy;++j)product(p.input()[o.linear+j],p.work()[p.yBase()+j],p.direct_value);
    p.direct_value+=p.input()[o.c0];finite(p.direct_value);
    for(Count r=0;r<t.rows;++r)for(Count c=0;c<p.du;++c){double row_control=0;
      for(Count z=0;z<p.dy;++z)product(p.usedF(r,z),a.embeddingControl(z,c),row_control);
      p.work()[p.directRowBase()+mul(r,p.du)+c]=row_control;}
    for(Count j=0;j<p.dy;++j){double g=p.input()[o.linear+j];for(Count r=0;r<t.rows;++r)product(p.usedF(r,j),p.work()[p.residualBase()+r],g);p.work()[p.gyBase()+j]=g;
      for(Count c=0;c<p.du;++c){double value=0;for(Count r=0;r<t.rows;++r)
          product(p.usedF(r,j),p.work()[p.directRowBase()+mul(r,p.du)+c],value);
        p.work()[p.interBase()+mul(j,p.du)+c]=value;}}
    for(Count r=0;r<p.du;++r){double g=0;for(Count j=0;j<p.dy;++j)product(a.embeddingControl(j,r),p.work()[p.gyBase()+j],g);p.work()[p.directGBase()+r]=g;
      for(Count c=0;c<p.du;++c){double h=0;for(Count j=0;j<p.dy;++j)product(a.embeddingControl(j,r),p.work()[p.interBase()+mul(j,p.du)+c],h);p.work()[p.directHBase()+mul(r,p.du)+c]=h;}}
    condensedEvaluation(p,false,k);p.canonical_evaluation=false;
    near(p.direct_value,p.condensed_value);
    for(Count r=0;r<p.du;++r){near(p.work()[p.directGBase()+r],p.work()[p.condensedGBase()+r]);
      for(Count c=0;c<p.du;++c)near(halfFirst(p.work()[p.directHBase()+mul(r,p.du)+c],p.work()[p.directHBase()+mul(c,p.du)+r]),halfFirst(p.H(k,r,c),p.H(k,c,r)));}
  }
  static void condensedEvaluation(CostStorage& p,bool canonical,Count k){
    auto H=[&](Count r,Count c){return canonical?p.sumH(r,c):p.H(k,r,c);};
    auto G=[&](Count c){return canonical?p.sumg(c):p.g(k,c);};
    double quadratic=0,linear=0;
    for(Count r=0;r<p.du;++r){double row_value=0,g=G(r);for(Count c=0;c<p.du;++c){product(H(r,c),p.work()[c],row_value);
        product(halfFirst(H(r,c),H(c,r)),p.work()[c],g);}product(p.work()[r],row_value,quadratic);product(G(r),p.work()[r],linear);p.work()[p.condensedGBase()+r]=g;}
    p.condensed_value=.5*quadratic;finite(p.condensed_value);p.condensed_value+=linear;finite(p.condensed_value);
    p.condensed_value+=canonical?p.sumc():p.constant(k);finite(p.condensed_value);
  }
  static void build(CostStorage& p){
    need(add(p.sumGBase(),p.du)<=p.work_slots,"bounded cost workspace layout exceeded");
    for(Count r=0;r<p.du;++r){p.sumg(r)=0;p.work()[p.sumGBase()+r]=0;for(Count c=0;c<p.du;++c){p.sumH(r,c)=0;p.work()[p.sumHBase()+mul(r,p.du)+c]=0;}}
    for(Count j=0;j<p.dy;++j)p.suml(j)=0;p.sumc()=0;p.work()[p.du]=0;double direct_sum=0;
    for(Count k=0;k<p.shape.terms;++k){used(p,k);condense(p,k);evaluateTerm(p,k);direct_sum+=p.direct_value;finite(direct_sum);
      for(Count r=0;r<p.du;++r){p.sumg(r)+=p.g(k,r);finite(p.sumg(r));p.work()[p.sumGBase()+r]+=p.work()[p.directGBase()+r];finite(p.work()[p.sumGBase()+r]);
        for(Count c=0;c<p.du;++c){p.sumH(r,c)+=p.H(k,r,c);finite(p.sumH(r,c));p.work()[p.sumHBase()+mul(r,p.du)+c]+=p.work()[p.directHBase()+mul(r,p.du)+c];finite(p.work()[p.sumHBase()+mul(r,p.du)+c]);}}
      for(Count j=0;j<p.dy;++j){p.suml(j)+=p.input()[p.offsets[k].linear+j];finite(p.suml(j));}
      p.work()[p.du]+=p.input()[p.offsets[k].c0];finite(p.work()[p.du]);p.sumc()+=p.constant(k);finite(p.sumc());}
    p.budget->chargeScratchOrCopy(p.work_slots);p.direct_value=direct_sum;condensedEvaluation(p,true,0);p.canonical_evaluation=true;
    near(p.direct_value,p.condensed_value);
    for(Count r=0;r<p.du;++r){near(p.work()[p.sumGBase()+r],p.work()[p.condensedGBase()+r]);
      for(Count c=0;c<p.du;++c)near(halfFirst(p.work()[p.sumHBase()+mul(r,p.du)+c],p.work()[p.sumHBase()+mul(c,p.du)+r]),halfFirst(p.sumH(r,c),p.sumH(c,r)));}
  }
  static QuadraticCostOutcome construct(AffineAssemblyOutcome&& assembly,CostInputRecipe&& recipe){
    QuadraticCostOutcome out(std::move(assembly),std::move(recipe));
    std::unique_ptr<CostStorage> data;
    try{need(out.original_.hasCompleteAssembly(),"complete owned affine assembly required");auto& a=out.original_.assembly();
      const auto f=shape(out.input_,a);auto& budget=a.costBudget();const auto& plan=a.costPlan();
      out.anchor_=std::make_shared<CostAnchor>(std::move(out.original_),std::move(out.input_));
      data=std::make_unique<CostStorage>(out.anchor_,budget,plan,f);ingest(*data);build(*data);
      out.cost_.reset(new CompleteQuadraticCost(std::move(data)));
    }catch(const std::exception& e){if(data)data->reject(e.what());out.failed_=std::move(data);out.recordRefusal(e.what());}
    catch(...){if(data)data->reject("NONSTANDARD_COST_INPUT_FAILURE");out.failed_=std::move(data);out.recordRefusal("NONSTANDARD_COST_INPUT_FAILURE");}
    return out;
  }
  static void term(CostStorage& p,Count k,const std::function<void(const UsedTermView&)>& callback){
    need(!p.poisoned&&p.anchor->assembly.hasCompleteAssembly(),"cost/source previously refused");
    try{need(!p.callback_active&&static_cast<bool>(callback),"cost callback reentry/empty callback");bounds(k,p.shape.terms);
      struct Guard{bool& active;explicit Guard(bool& b):active(b){active=true;}~Guard(){active=false;}} guard(p.callback_active);
      used(p,k);evaluateTerm(p,k);const UsedTermView view(&p,k);callback(view);need(!p.poisoned,"nested cost refusal retained");
    }catch(const std::exception& e){p.reject(e.what());throw;}catch(...){p.reject("NONSTANDARD_COST_CALLBACK_FAILURE");throw;}
  }
  static void canonical(CostStorage& p,const std::function<void(const CostEvaluationView&)>& callback){
    need(!p.poisoned&&p.anchor->assembly.hasCompleteAssembly(),"cost/source previously refused");
    try{need(!p.callback_active&&static_cast<bool>(callback),"cost callback reentry/empty callback");
      struct Guard{bool& active;explicit Guard(bool& b):active(b){active=true;}~Guard(){active=false;}} guard(p.callback_active);
      for(Count r=0;r<p.du;++r){p.work()[p.sumGBase()+r]=0;for(Count c=0;c<p.du;++c)p.work()[p.sumHBase()+mul(r,p.du)+c]=0;}double value=0;
      for(Count k=0;k<p.shape.terms;++k){used(p,k);evaluateTerm(p,k);value+=p.direct_value;finite(value);
        for(Count r=0;r<p.du;++r){p.work()[p.sumGBase()+r]+=p.work()[p.directGBase()+r];finite(p.work()[p.sumGBase()+r]);
          for(Count c=0;c<p.du;++c){p.work()[p.sumHBase()+mul(r,p.du)+c]+=p.work()[p.directHBase()+mul(r,p.du)+c];finite(p.work()[p.sumHBase()+mul(r,p.du)+c]);}}}
      p.budget->chargeScratchOrCopy(p.work_slots);p.direct_value=value;condensedEvaluation(p,true,0);p.canonical_evaluation=true;
      const CostEvaluationView view(&p);callback(view);need(!p.poisoned,"nested canonical refusal retained");
    }catch(const std::exception& e){p.reject(e.what());throw;}catch(...){p.reject("NONSTANDARD_COST_CALLBACK_FAILURE");throw;}
  }
};
} // namespace detail
namespace {
detail::CostStorage& present(const std::unique_ptr<detail::CostStorage>& p){need(p&&!p->poisoned&&p->input_complete&&p->anchor->assembly.hasCompleteAssembly(),"cost/source absent/refused/moved");return *p;}
detail::CostStorage& view(detail::CostStorage* p){need(p&&!p->poisoned&&p->callback_active,"cost view outside callback/refused");return *p;}
}
CostEvaluationView::CostEvaluationView(detail::CostStorage* p):storage_(p){}
double CostEvaluationView::directValue() const{return view(storage_).direct_value;}
double CostEvaluationView::condensedValue() const{return view(storage_).condensed_value;}
double CostEvaluationView::directGradient(Count c) const{auto& p=view(storage_);bounds(c,p.du);return p.work()[(p.canonical_evaluation?p.sumGBase():p.directGBase())+c];}
double CostEvaluationView::condensedGradient(Count c) const{auto& p=view(storage_);bounds(c,p.du);return p.work()[p.condensedGBase()+c];}
double CostEvaluationView::directHessian(Count r,Count c) const{auto& p=view(storage_);bounds(r,p.du);bounds(c,p.du);const Count base=p.canonical_evaluation?p.sumHBase():p.directHBase();return halfFirst(p.work()[base+mul(r,p.du)+c],p.work()[base+mul(c,p.du)+r]);}
double CostEvaluationView::condensedHessian(Count r,Count c) const{auto& p=view(storage_);bounds(r,p.du);bounds(c,p.du);return p.canonical_evaluation?halfFirst(p.sumH(r,c),p.sumH(c,r)):halfFirst(p.H(p.active_term,r,c),p.H(p.active_term,c,r));}
UsedTermView::UsedTermView(detail::CostStorage* p,Count k):storage_(p),term_(k),evaluation_(p){}
Count UsedTermView::rows() const{auto& p=view(storage_);return p.anchor->recipe.terms.at(term_).rows;}
double UsedTermView::usedFactor(Count r,Count c) const{auto& p=view(storage_);bounds(r,rows());bounds(c,p.dy);return p.usedF(r,c);}
double UsedTermView::usedOffset(Count r) const{auto& p=view(storage_);bounds(r,rows());return p.used0(r);}
double UsedTermView::usedLinear(Count c) const{auto& p=view(storage_);bounds(c,p.dy);return p.input()[p.offsets.at(term_).linear+c];}
double UsedTermView::usedConstant() const{auto& p=view(storage_);return p.input()[p.offsets.at(term_).c0];}
double UsedTermView::factorControl(Count r,Count c) const{auto& p=view(storage_);bounds(r,rows());bounds(c,p.du);return p.Fc(p.offsets.at(term_).row_base+r,c);}
double UsedTermView::factorOffset(Count r) const{auto& p=view(storage_);bounds(r,rows());return p.fc(p.offsets.at(term_).row_base+r);}
double UsedTermView::rawH(Count r,Count c) const{auto& p=view(storage_);bounds(r,p.du);bounds(c,p.du);return p.H(term_,r,c);}
double UsedTermView::gradientCoefficient(Count c) const{auto& p=view(storage_);bounds(c,p.du);return p.g(term_,c);}
double UsedTermView::constantCoefficient() const{return view(storage_).constant(term_);}
CompleteQuadraticCost::CompleteQuadraticCost(std::unique_ptr<detail::CostStorage> p):storage_(std::move(p)){}
CompleteQuadraticCost::CompleteQuadraticCost(CompleteQuadraticCost&&) noexcept=default;
CompleteQuadraticCost& CompleteQuadraticCost::operator=(CompleteQuadraticCost&&) noexcept=default;
CompleteQuadraticCost::~CompleteQuadraticCost()=default;
bool CompleteQuadraticCost::complete() const noexcept{return storage_&&!storage_->poisoned&&storage_->input_complete&&storage_->anchor->assembly.hasCompleteAssembly();}
Count CompleteQuadraticCost::termCount() const{return present(storage_).shape.terms;}
const std::vector<CostTermLayout>& CompleteQuadraticCost::inputLayouts() const{return present(storage_).anchor->recipe.terms;}
const FileIdentity& CompleteQuadraticCost::inputIdentity() const{return present(storage_).anchor->recipe.file;}
const std::string& CompleteQuadraticCost::inputSemanticSha256() const{return present(storage_).semantic;}
double CompleteQuadraticCost::inputFactor(Count k,Count r,Count c) const{auto& p=present(storage_);bounds(k,p.shape.terms);bounds(r,p.anchor->recipe.terms[k].rows);bounds(c,p.dy);return p.input()[p.offsets[k].F+mul(r,p.dy)+c];}
double CompleteQuadraticCost::inputOffset(Count k,Count r) const{auto& p=present(storage_);bounds(k,p.shape.terms);bounds(r,p.anchor->recipe.terms[k].rows);return p.input()[p.offsets[k].f0+r];}
double CompleteQuadraticCost::inputLinear(Count k,Count c) const{auto& p=present(storage_);bounds(k,p.shape.terms);bounds(c,p.dy);return p.input()[p.offsets[k].linear+c];}
double CompleteQuadraticCost::inputConstant(Count k) const{auto& p=present(storage_);bounds(k,p.shape.terms);return p.input()[p.offsets[k].c0];}
double CompleteQuadraticCost::inputAdditionCoefficient(Count k,Count a,Count r,Count c) const{auto& p=present(storage_);bounds(k,p.shape.terms);bounds(a,p.offsets[k].additions.size());bounds(r,p.anchor->recipe.terms[k].additions[a].parent_rows.size());bounds(c,30);return p.input()[p.offsets[k].additions[a]+mul(r,30)+c];}
double CompleteQuadraticCost::evaluationControl(Count c) const{auto& p=present(storage_);bounds(c,p.du);return p.work()[c];}
double CompleteQuadraticCost::sumRawH(Count r,Count c) const{auto& p=present(storage_);bounds(r,p.du);bounds(c,p.du);return p.sumH(r,c);}
double CompleteQuadraticCost::sumGradientCoefficient(Count c) const{auto& p=present(storage_);bounds(c,p.du);return p.sumg(c);}
double CompleteQuadraticCost::sumConstantCoefficient() const{return present(storage_).sumc();}
double CompleteQuadraticCost::sumLinear(Count c) const{auto& p=present(storage_);bounds(c,p.dy);return p.suml(c);}
double CompleteQuadraticCost::sumInputConstant() const{auto& p=present(storage_);return p.work()[p.du];}
double CompleteQuadraticCost::sumFactorControl(Count r,Count c) const{auto& p=present(storage_);bounds(r,p.shape.rows);bounds(c,p.du);return p.Fc(r,c);}
double CompleteQuadraticCost::sumFactorOffset(Count r) const{auto& p=present(storage_);bounds(r,p.shape.rows);return p.fc(r);}
void CompleteQuadraticCost::withTerm(Count k,const std::function<void(const UsedTermView&)>& callback){detail::CostFactory::term(present(storage_),k,callback);}
void CompleteQuadraticCost::withCanonicalEvaluation(const std::function<void(const CostEvaluationView&)>& callback){detail::CostFactory::canonical(present(storage_),callback);}
std::string_view CompleteQuadraticCost::refusal() const noexcept{
  if(storage_&&storage_->poisoned)return storage_->error.empty()?std::string_view("COST_REFUSAL_UNRECORDED_DETAIL"):std::string_view(storage_->error);
  if(storage_&&!storage_->anchor->assembly.hasCompleteAssembly())return storage_->anchor->assembly.refusal();
  return {};
}
const AffineAssemblyOutcome& CompleteQuadraticCost::originalAssembly() const{need(static_cast<bool>(storage_),"moved cost owner");return storage_->anchor->assembly;}
const std::array<bool,7>& CompleteQuadraticCost::scopeClaims() noexcept{static const std::array<bool,7> flags{};return flags;}
QuadraticCostOutcome::QuadraticCostOutcome(AffineAssemblyOutcome&& a,CostInputRecipe&& i) noexcept:original_(std::move(a)),input_(std::move(i)){}
QuadraticCostOutcome::QuadraticCostOutcome(QuadraticCostOutcome&&) noexcept=default;
QuadraticCostOutcome& QuadraticCostOutcome::operator=(QuadraticCostOutcome&&) noexcept=default;
QuadraticCostOutcome::~QuadraticCostOutcome()=default;
bool QuadraticCostOutcome::hasCompleteCost() const noexcept{return !refused_&&cost_&&cost_->complete();}
CompleteQuadraticCost& QuadraticCostOutcome::cost(){need(hasCompleteCost(),"complete cost refused/moved");return *cost_;}
const AffineAssemblyOutcome& QuadraticCostOutcome::originalAssembly() const{return anchor_?anchor_->assembly:original_;}
const CostInputRecipe& QuadraticCostOutcome::originalInputRecipe() const{return anchor_?anchor_->recipe:input_;}
std::string_view QuadraticCostOutcome::refusal() const noexcept{if(cost_&&!cost_->complete())return cost_->refusal();return refused_?(reason_.empty()?std::string_view("COST_REFUSAL_UNRECORDED_DETAIL"):std::string_view(reason_)):std::string_view{};}
void QuadraticCostOutcome::recordRefusal(const char* e) noexcept{cost_.reset();refused_=true;try{reason_=e?e:"COST_REFUSAL";}catch(...){reason_.clear();}}
QuadraticCostOutcome buildQuadraticCost(AffineAssemblyOutcome&& a,CostInputRecipe&& i){return detail::CostFactory::construct(std::move(a),std::move(i));}
} // namespace phase5_public_live_affine_v2
