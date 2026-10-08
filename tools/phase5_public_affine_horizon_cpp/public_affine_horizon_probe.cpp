#include "public_affine_horizon_internal.hpp"
#include "public_coupled_augmented_extension.hpp"
#include <yaml-cpp/yaml.h>
#include <openssl/evp.h>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <regex>
#include <set>
#include <sstream>
#include <memory>
#include <cctype>
#include <fcntl.h>
#include <unistd.h>

namespace ah=phase5_public_affine_horizon;
using ah::detail::require;using ah::detail::add;using ah::detail::mul;
using ah::Matrix;using ah::Vector;
const std::string CERT="COMMAND_PROGRESS_EXTENSION_JACOBIAN_STRICT_PHYSICAL_V1";
const std::string F1="f1b7e6c7e4219fec2beb310540c725b448dcf021b3a95ddafc2922e8849bf1d6";
const std::regex NUM("-?(0|[1-9][0-9]*)(\\.[0-9]+)?([eE][+-]?[0-9]+)?"), UINT("(0|[1-9][0-9]*)");

// yaml-cpp provides nodes, but a separate strict JSON grammar rejects YAML,
// duplicate decoded keys, aliases, trailing content and excessive nesting.
class JsonGrammar {
 const std::string& s;std::size_t i=0,numeric=0;int depth=0;
 void ws(){while(i<s.size()&&(s[i]==' '||s[i]=='\t'||s[i]=='\r'||s[i]=='\n'))++i;}
 void take(char c){ws();require(i<s.size()&&s[i++]==c,"JSON syntax");}
 std::string string(){ws();auto begin=i;require(i<s.size()&&s[i++]=='"',"JSON string");
  bool end=false;while(i<s.size()){unsigned char c=s[i++];if(c=='"'){end=true;break;}require(c>=32,"JSON string control");
   if(c=='\\'){require(i<s.size(),"JSON escape");char e=s[i++];require(std::string("\"\\/bfnrtu").find(e)!=std::string::npos,"JSON escape");if(e=='u')for(int k=0;k<4;++k){require(i<s.size()&&std::isxdigit(static_cast<unsigned char>(s[i])),"JSON unicode");++i;}}}
  require(end,"unterminated JSON string");return YAML::Load(s.substr(begin,i-begin)).as<std::string>();}
 void value(){ws();require(i<s.size()&&++depth<=64,"JSON depth/content");char c=s[i];
  if(c=='{'){++i;ws();std::set<std::string> keys;if(i<s.size()&&s[i]=='}')++i;else while(true){auto k=string();require(keys.insert(k).second,"duplicate JSON key");take(':');value();ws();require(i<s.size(),"JSON object end");if(s[i]=='}'){++i;break;}take(',');}}
  else if(c=='['){++i;ws();if(i<s.size()&&s[i]==']')++i;else while(true){value();ws();require(i<s.size(),"JSON array end");if(s[i]==']'){++i;break;}take(',');}}
  else if(c=='"'){string();}
  else if(s.compare(i,4,"true")==0)i+=4;
  else if(s.compare(i,5,"false")==0)i+=5;
  else if(s.compare(i,4,"null")==0)i+=4;
  else {auto begin=i;while(i<s.size()&&std::string("-+0123456789.eE").find(s[i])!=std::string::npos)++i;
   require(i>begin&&std::regex_match(s.substr(begin,i-begin),NUM),"JSON number");++numeric;}
  --depth;
 }
 public:explicit JsonGrammar(const std::string& t):s(t){}std::size_t check(){value();ws();require(i==s.size(),"JSON trailing content");return numeric;}
};
bool isString(const YAML::Node& n){return n.IsScalar()&&(n.Tag()=="!"||n.Tag()=="tag:yaml.org,2002:str");}
std::string str(const YAML::Node& n){require(isString(n),"quoted JSON string required");return n.Scalar();}
double number(const YAML::Node& n){require(n.IsScalar()&&!isString(n)&&std::regex_match(n.Scalar(),NUM),"finite JSON number type");double v=std::stod(n.Scalar());require(std::isfinite(v),"nonfinite JSON number");return v;}
std::size_t integer(const YAML::Node& n){require(n.IsScalar()&&!isString(n)&&std::regex_match(n.Scalar(),UINT),"canonical unsigned JSON integer");auto v=std::stoull(n.Scalar());require(v<=SIZE_MAX,"integer overflow");return v;}
bool boolean(const YAML::Node& n){require(n.IsScalar()&&!isString(n)&&(n.Scalar()=="true"||n.Scalar()=="false"),"JSON boolean type");return n.Scalar()=="true";}
void scope(const YAML::Node& n){require(n.IsMap()&&n.size()==7,"scope fields");for(const auto* k:{"connecting_segment","ball","admissibility","execution","safety","uniform_error_bound","controller_readiness"})require(!boolean(n[k]),"true/omitted scope claim refused");}
YAML::Node scopeNode(){YAML::Node n;for(const auto* k:{"connecting_segment","ball","admissibility","execution","safety","uniform_error_bound","controller_readiness"})n[k]=false;return n;}
YAML::Node textNode(const std::string& s){YAML::Node n(s);n.SetTag("tag:yaml.org,2002:str");return n;}
std::string sha(const std::string& bytes){
 std::unique_ptr<EVP_MD_CTX,decltype(&EVP_MD_CTX_free)> ctx(EVP_MD_CTX_new(),EVP_MD_CTX_free);require(bool(ctx),"SHA context");
 require(EVP_DigestInit_ex(ctx.get(),EVP_sha256(),nullptr)==1&&EVP_DigestUpdate(ctx.get(),bytes.data(),bytes.size())==1,"SHA update");
 unsigned char digest[EVP_MAX_MD_SIZE];unsigned int n=0;require(EVP_DigestFinal_ex(ctx.get(),digest,&n)==1&&n==32,"SHA final");std::ostringstream s;for(unsigned int j=0;j<n;++j)s<<std::hex<<std::setw(2)<<std::setfill('0')<<int(digest[j]);return s.str();
}
struct Document {YAML::Node node;std::string digest;};
Document load(const std::filesystem::path& path,const ah::Limits& limits,ah::CliBudget& budget,const std::string& expected=""){
 require(std::filesystem::is_regular_file(path),"source must be regular file");auto len=std::filesystem::file_size(path);require(len<=limits.max_document_bytes,"document byte cap");
 std::ifstream f(path,std::ios::binary);require(bool(f),"source open");std::string bytes(len,'\0');f.read(bytes.data(),len);require(std::size_t(f.gcount())==len,"source short read");
 require(f.peek()==std::char_traits<char>::eof(),"source changed length");auto digest=sha(bytes);require(expected.empty()||digest==expected,"source bytes hash mismatch before parse");auto count=JsonGrammar(bytes).check();auto total=add(budget.charged_numeric_elements,count);require(total<=limits.max_cli_numeric_elements,"parsed numeric CLI cap");budget.charged_numeric_elements=total;
 return {YAML::Load(bytes),digest};
}
void sequence(const YAML::Node& n,std::size_t size,const std::string& e){require(n.IsSequence()&&n.size()==size,e);}
void inspectV(const YAML::Node& n,std::size_t size){sequence(n,size,"preflight vector shape");for(const auto& x:n)number(x);}
void inspectM(const YAML::Node& n,std::size_t rows,std::size_t cols){sequence(n,rows,"preflight matrix rows");for(const auto& row:n)inspectV(row,cols);}
void inspectState(const YAML::Node& n,bool sampled=false){for(const auto* k:{"q","v","C","w"})inspectV(n[k],7);number(n[sampled?"s_reference":"s"]);number(n[sampled?"r_reference":"r"]);}
Vector vector(const YAML::Node& n,std::size_t size,ah::ProblemBudget& b){sequence(n,size,"vector shape");for(const auto& x:n)number(x);auto v=ah::detail::zeros(size,b);for(std::size_t j=0;j<size;++j)v(j)=number(n[j]);return v;}
Matrix matrix(const YAML::Node& n,std::size_t rows,std::size_t cols,ah::ProblemBudget& b){sequence(n,rows,"matrix row shape");for(const auto& row:n){sequence(row,cols,"matrix column shape");for(const auto& x:row)number(x);}auto m=ah::detail::zeros(rows,cols,b);for(std::size_t r=0;r<rows;++r)for(std::size_t c=0;c<cols;++c)m(r,c)=number(n[r][c]);return m;}
Vector state(const YAML::Node& n,ah::ProblemBudget& b,bool sampled=false){
 auto v=ah::detail::zeros(30,b);std::size_t offset=0;for(const auto* k:{"q","v","C","w"}){auto x=vector(n[k],7,b);v.segment(offset,7)=x;offset+=7;}
 v(28)=number(n[sampled?"s_reference":"s"]);v(29)=number(n[sampled?"r_reference":"r"]);return v;
}
Vector input(const YAML::Node& n,ah::ProblemBudget& b){auto u=ah::detail::zeros(8,b);u.head(7)=vector(n["alpha"],7,b);u(7)=number(n["b"]);return u;}
bool same(const Matrix& a,const Matrix& b){return a.rows()==b.rows()&&a.cols()==b.cols()&&(a.array()==b.array()).all();}
void mapCertificate(const YAML::Node& m){require(str(m["certificate_name"])==CERT&&!boolean(m["certifies_two_sided_admissible_neighborhood"]),"public map certificate");}
void index(const YAML::Node& m,std::size_t c,int k,int h){require(integer(m["cell"])==c&&integer(m["cycle"])==std::size_t(k)&&integer(m["half"])==std::size_t(h),"public exact map roster");}
struct Artifact {Document doc;std::string id,binary,archive;};
struct Selected {const Artifact* artifact=nullptr;YAML::Node row;std::string roster,name;};
Selected select(const YAML::Node& src,const std::map<std::string,Artifact>& artifacts){
 auto id=str(src["artifact_id"]);auto found=artifacts.find(id);require(found!=artifacts.end(),"artifact id not pinned");auto roster=str(src["roster"]);require(roster=="complete"||roster=="refused","source roster");auto name=str(src["row_name"]);auto rows=found->second.doc.node[roster];require(rows.IsSequence(),"artifact roster");
 std::set<std::string> names;YAML::Node result;for(std::size_t j=0;j<rows.size();++j){const YAML::Node row=rows[j];auto nm=str(row["name"]);require(names.insert(nm).second,"duplicate source row");if(nm==name)result=row;}
 require(result.IsMap(),"pinned source row missing");return {&found->second,result,roster,name};
}
bool supported(const Selected& s){auto o=s.row["original_output"];return s.roster=="complete"&&boolean(o["value"]["success"])&&boolean(o["value"]["has_final_state"])&&boolean(o["extension_jacobian_success"]);}
ah::SourceIdentity identity(const Selected& s){ah::SourceIdentity id;id.kind="public_saved_json";id.artifact_id=s.artifact->id;id.file_sha256=s.artifact->doc.digest;id.row_name=s.name;id.source_binary_sha256=s.artifact->binary;id.certificate_name=CERT;id.full_nominal_source_certified=true;return id;}
ah::Problem publicProblem(const Selected& sel,const YAML::Node& actual,const ah::Limits& l,ah::ProblemBudget& b){
 require(supported(sel),"public failed/unsupported source refused");auto in=sel.row["original_input"],o=sel.row["original_output"],value=o["value"];
 require(str(in["name"])==sel.name&&str(o["name"])==sel.name,"public descriptor name mismatch");
 require(o["first_uncertified_substep"].IsScalar()&&!isString(o["first_uncertified_substep"])&&o["first_uncertified_substep"].Scalar()=="-1","public first uncertified must be -1");mapCertificate(o);
 ah::Problem p;p.nx=30;p.nu=8;p.source=identity(sel);p.actual_initial=vector(actual,30,b);auto cells=in["cells"];require(cells.IsSequence()&&cells.size()>0&&cells.size()<=l.max_cells,"public cell cap");
 std::size_t total=0;for(const auto& c:cells){auto k=integer(c["cycles"]);require(k>0&&k<=l.max_samples/2,"public positive cycle cap");total=add(total,k);}require(mul(2,total)<=l.max_samples,"public sample cap");
 sequence(o["cell_maps"],cells.size(),"public cell roster length");sequence(o["cycle_maps"],total,"public cycle roster length");sequence(o["substep_maps"],2*total,"public half roster length");sequence(value["cell_end_states"],cells.size(),"public cell value roster");sequence(value["cycle_end_states"],total,"public cycle value roster");sequence(value["substeps"],2*total,"public actual half roster");
 p.cells.reserve(cells.size());p.nominal_cells.reserve(cells.size());p.samples.reserve(2*total);p.nominal_samples.reserve(2*total);auto origin=state(in["state"],b);std::size_t step=0,cycle=0;
 for(std::size_t c=0;c<cells.size();++c){int m=integer(cells[c]["cycles"]);auto u=input(cells[c],b);auto cm=o["cell_maps"][c];index(cm,c,m,2);mapCertificate(cm);
  auto co=state(cm["origin"],b),ce=state(cm["state"],b),cu=vector(cm["input"],8,b);require(ah::detail::exact(co,origin)&&ah::detail::exact(cu,u)&&ah::detail::exact(ce,state(value["cell_end_states"][c],b)),"public literal wholecell mismatch");
  ah::Transition t;t.cycles=m;t.A=matrix(cm["A"],30,30,b);t.B=matrix(cm["B"],30,8,b);t.defect=vector(cm["defect"],30,b);p.cells.push_back(std::move(t));b.reserve(68);p.nominal_cells.push_back({co,u,ce});
  b.reserve(30);auto localOrigin=origin;
  for(int k=1;k<=m;++k){auto cycleMap=o["cycle_maps"][cycle];index(cycleMap,c,k,2);mapCertificate(cycleMap);
   auto cOrigin=state(cycleMap["origin"],b),cState=state(cycleMap["state"],b);require(ah::detail::exact(cOrigin,localOrigin)&&ah::detail::exact(cState,state(value["cycle_end_states"][cycle],b))&&ah::detail::exact(state(cycleMap["cell_origin"],b),origin)&&ah::detail::exact(vector(cycleMap["input"],8,b),u),"public cycle literals");
   ah::detail::residual(matrix(cycleMap["A"],30,30,b),matrix(cycleMap["B"],30,8,b),vector(cycleMap["defect"],30,b),localOrigin,u,cState,l,b);
   ah::detail::residual(matrix(cycleMap["cell_A"],30,30,b),matrix(cycleMap["cell_B"],30,8,b),vector(cycleMap["cell_defect"],30,b),origin,u,cState,l,b);
   for(int h=1;h<=2;++h){auto sm=o["substep_maps"][step],vs=value["substeps"][step];index(sm,c,k,h);index(vs,c,k,h);mapCertificate(sm);
    auto so=state(sm["cell_origin"],b),se=state(sm["state"],b),su=vector(sm["input"],8,b);require(ah::detail::exact(so,origin)&&ah::detail::exact(su,u)&&ah::detail::exact(state(sm["origin"],b),localOrigin)&&ah::detail::exact(se,state(vs,b,true)),"public sample literal mismatch");
    auto time=number(vs["elapsed_s"]);require(std::abs(time-.002*(step+1))<=l.arithmetic_abs+l.arithmetic_rel*std::abs(time),"public sample timestamp");
    ah::detail::residual(matrix(sm["A"],30,30,b),matrix(sm["B"],30,8,b),vector(sm["defect"],30,b),localOrigin,u,se,l,b);
    ah::Sample s;s.cell=c;s.cycle=k;s.half=h;s.A=matrix(sm["cell_A"],30,30,b);s.B=matrix(sm["cell_B"],30,8,b);s.defect=vector(sm["cell_defect"],30,b);p.samples.push_back(std::move(s));p.nominal_samples.push_back({std::move(so),std::move(su),std::move(se)});++step;
   }localOrigin=cState;++cycle;
  }origin=ce;
 }
 require(ah::detail::exact(origin,state(value["final_state"],b)),"public literal final state");return p;
}
phase5_public_coupled_augmented::State nativeState(const YAML::Node& n,ah::ProblemBudget& b,bool sampled=false){
 phase5_public_coupled_augmented::State z;z.q=vector(n["q"],7,b);z.v=vector(n["v"],7,b);z.C=vector(n["C"],7,b);z.w=vector(n["w"],7,b);z.s=number(n[sampled?"s_reference":"s"]);z.r=number(n[sampled?"r_reference":"r"]);return z;
}
phase5_public_coupled_augmented_extension::Map nativeMap(const YAML::Node& n,ah::ProblemBudget& b){
 phase5_public_coupled_augmented_extension::Map m;m.cell=integer(n["cell"]);m.cycle=integer(n["cycle"]);m.half=integer(n["half"]);m.origin=nativeState(n["origin"],b);m.state=nativeState(n["state"],b);m.input=vector(n["input"],8,b);m.A=matrix(n["A"],30,30,b);m.B=matrix(n["B"],30,8,b);m.defect=vector(n["defect"],30,b);m.cell_origin=nativeState(n["cell_origin"],b);m.cell_A=matrix(n["cell_A"],30,30,b);m.cell_B=matrix(n["cell_B"],30,8,b);m.cell_defect=vector(n["cell_defect"],30,b);return m;
}
YAML::Node nativeBridge(const Selected& sel,const ah::Problem& json,const ah::Limits& l,ah::ProblemBudget& b){
 // Reconstruct archived carrier with deliberately DISTINCT local/cumulative
 // fields in multicycle cells. No Model constructor/rollout is available here.
 phase5_public_coupled_augmented_extension::Result r;auto o=sel.row["original_output"],v=o["value"];r.value.success=boolean(v["success"]);r.value.has_final_state=boolean(v["has_final_state"]);r.value.final_state=nativeState(v["final_state"],b);r.extension_jacobian_success=boolean(o["extension_jacobian_success"]);r.first_uncertified_substep=-1;r.value.cell_end_states.reserve(v["cell_end_states"].size());r.value.cycle_end_states.reserve(v["cycle_end_states"].size());r.value.substeps.reserve(v["substeps"].size());r.cycle_maps.reserve(o["cycle_maps"].size());r.substep_maps.reserve(o["substep_maps"].size());r.cell_maps.reserve(json.cells.size());
 for(const auto& z:v["cell_end_states"]){r.value.cell_end_states.push_back(nativeState(z,b));}
 for(const auto& z:v["cycle_end_states"]){r.value.cycle_end_states.push_back(nativeState(z,b));}
 for(const auto& z:v["substeps"]){phase5_public_coupled_augmented::Substep s;s.cell=integer(z["cell"]);s.cycle=integer(z["cycle"]);s.half=integer(z["half"]);s.elapsed_s=number(z["elapsed_s"]);s.s_reference=number(z["s_reference"]);s.r_reference=number(z["r_reference"]);s.q=vector(z["q"],7,b);s.v=vector(z["v"],7,b);s.C=vector(z["C"],7,b);s.w=vector(z["w"],7,b);r.value.substeps.push_back(std::move(s));}
 for(const auto& m:o["cycle_maps"]){r.cycle_maps.push_back(nativeMap(m,b));}
 for(const auto& m:o["substep_maps"]){r.substep_maps.push_back(nativeMap(m,b));}
 std::size_t idx=0;for(std::size_t c=0;c<json.cells.size();++c){idx+=json.cells[c].cycles;auto m=nativeMap(o["cycle_maps"][idx-1],b);auto full=o["cell_maps"][c];
  // Last cycle local fields above stay local. Replace only cumulative fields.
  m.cell_origin=nativeState(full["origin"],b);m.cell_A=matrix(full["A"],30,30,b);m.cell_B=matrix(full["B"],30,8,b);m.cell_defect=vector(full["defect"],30,b);m.state=nativeState(full["state"],b);r.cell_maps.push_back(std::move(m));}
 bool distinct=false;for(const auto& m:r.cell_maps)if(m.cycle>1&&(!same(m.A,m.cell_A)||!same(m.B,m.cell_B)||!ah::detail::exact(m.defect,m.cell_defect)))distinct=true;
 auto native=ah::normalize_public_native(r,json,json.source,l,b);require(native.cells.size()==json.cells.size()&&native.samples.size()==json.samples.size(),"native bridge roster");
 for(std::size_t c=0;c<json.cells.size();++c){require(same(native.cells[c].A,json.cells[c].A)&&same(native.cells[c].B,json.cells[c].B)&&ah::detail::exact(native.cells[c].defect,json.cells[c].defect)&&ah::detail::exact(native.nominal_cells[c].origin,json.nominal_cells[c].origin),"native cumulative wholecell bridge mismatch");}
 for(std::size_t j=0;j<json.samples.size();++j)require(same(native.samples[j].A,json.samples[j].A)&&same(native.samples[j].B,json.samples[j].B)&&ah::detail::exact(native.samples[j].defect,json.samples[j].defect),"native cumulative sample bridge mismatch");
 YAML::Node proof;proof["used_native_normalization"]=true;proof["matched_json_cumulative_fields"]=true;proof["multicycle_local_cumulative_distinct"]=distinct;proof["source_file_sha256"]=textNode(sel.artifact->doc.digest);proof["source_binary_sha256"]=textNode(F1);proof["cell_count"]=json.cells.size();proof["sample_count"]=json.samples.size();return proof;
}
ah::Problem genericProblem(const YAML::Node& src,const YAML::Node& actual,const ah::Limits& l,ah::ProblemBudget& b){
 ah::Problem p;p.source.kind="generic_synthetic";p.nx=integer(src["nx"]);p.nu=integer(src["nu"]);require(p.nx>0&&p.nx<=l.max_nx&&p.nu>0&&p.nu<=l.max_nu,"generic dimension cap");p.actual_initial=vector(actual,p.nx,b);
 auto cells=src["cells"];require(cells.IsSequence()&&cells.size()>0&&cells.size()<=l.max_cells,"generic cell cap");p.cells.reserve(cells.size());for(const auto& c:cells){ah::Transition t;auto k=integer(c["cycles"]);require(k>0&&k<=l.max_samples/2,"generic positive cycles");t.cycles=k;t.A=matrix(c["A"],p.nx,p.nx,b);t.B=matrix(c["B"],p.nx,p.nu,b);t.defect=vector(c["defect"],p.nx,b);p.cells.push_back(std::move(t));}
 auto samples=src["samples"];if(samples){require(samples.IsSequence()&&samples.size()<=l.max_samples,"generic sample cap");p.samples.reserve(samples.size());for(const auto& s:samples){ah::Sample v;v.cell=integer(s["cell"]);auto cy=integer(s["cycle"]),h=integer(s["half"]);require(cy<=l.max_samples/2&&h<=2,"generic sample integer cap");v.cycle=cy;v.half=h;v.A=matrix(s["A"],p.nx,p.nx,b);v.B=matrix(s["B"],p.nx,p.nu,b);v.defect=vector(s["defect"],p.nx,b);p.samples.push_back(std::move(v));}}
 return p;
}
std::vector<ah::FactorTerm> factors(const YAML::Node& n,std::size_t dy,std::size_t nx,const ah::Limits& l,ah::ProblemBudget& b){
 require(n.IsSequence()&&n.size()<=l.max_terms,"term roster cap");std::vector<ah::FactorTerm> out;out.reserve(n.size());std::set<std::string> names;
 for(const auto& term:n){ah::FactorTerm t;t.name=str(term["name"]);t.units=str(term["units"]);require(names.insert(t.name).second,"duplicate term name");auto F=term["F"];require(F.IsSequence()&&F.size()>0&&F.size()<=l.max_factor_rows,"factor row cap");t.F=matrix(F,F.size(),dy,b);t.f0=vector(term["f0"],F.size(),b);t.linear=vector(term["linear"],dy,b);t.constant=number(term["constant"]);
  auto ss=term["sample_additions"];require(ss.IsSequence()&&ss.size()<=l.max_samples,"sample additions roster");t.sample_additions.reserve(ss.size());for(const auto& s:ss){ah::SampleFactor v;v.sample_index=integer(s["sample_index"]);v.coefficient=matrix(s["coefficient"],F.size(),nx,b);t.sample_additions.push_back(std::move(v));}out.push_back(std::move(t));}
 return out;
}
std::size_t plan(const YAML::Node& c,const std::map<std::string,Artifact>& artifacts,const ah::Limits& l){
 scope(c["scope"]);auto src=c["source"];std::size_t nx,nu,N,samples;auto kind=str(src["kind"]);
 if(kind=="public_saved_json"){auto selected=select(src,artifacts);if(!supported(selected))return 0;nx=30;nu=8;auto cells=selected.row["original_input"]["cells"];require(cells.IsSequence(),"source cells");N=cells.size();samples=selected.row["original_output"]["substep_maps"].size();}
 else {require(kind=="generic_synthetic","source kind");nx=integer(src["nx"]);nu=integer(src["nu"]);require(src["cells"].IsSequence(),"generic cells");N=src["cells"].size();samples=src["samples"]?src["samples"].size():0;}
 require(nx>0&&nx<=l.max_nx&&nu>0&&nu<=l.max_nu&&N>0&&N<=l.max_cells&&samples<=l.max_samples,"planned problem caps");
 auto dx=mul(nx,add(N,1)),du=mul(nu,N),dy=add(dx,du);require(mul(dx,dx)<=l.max_matrix_elements,"planned L cap");sequence(c["actual_initial"],nx,"planned initial shape");sequence(c["evaluate_controls"],du,"planned controls shape");inspectV(c["actual_initial"],nx);inspectV(c["evaluate_controls"],du);
 if(kind=="generic_synthetic"){
  for(const auto& cell:src["cells"]){auto cy=integer(cell["cycles"]);require(cy>0&&cy<=l.max_samples/2,"preflight positive cycles");inspectM(cell["A"],nx,nx);inspectM(cell["B"],nx,nu);inspectV(cell["defect"],nx);}
  if(src["samples"])for(const auto& sample:src["samples"]){integer(sample["cell"]);integer(sample["cycle"]);integer(sample["half"]);inspectM(sample["A"],nx,nx);inspectM(sample["B"],nx,nu);inspectV(sample["defect"],nx);}
 }else{
  auto selected=select(src,artifacts);auto in=selected.row["original_input"],out=selected.row["original_output"];inspectState(in["state"]);
  for(const auto& cell:in["cells"]){auto cy=integer(cell["cycles"]);require(cy>0&&cy<=l.max_samples/2,"preflight public cycles");inspectV(cell["alpha"],7);number(cell["b"]);}
  for(const auto* group:{"cell_maps","cycle_maps","substep_maps"}){require(out[group].IsSequence(),"preflight public map group");for(const auto& map:out[group]){
   inspectM(map["A"],30,30);inspectM(map["B"],30,8);inspectV(map["defect"],30);inspectV(map["input"],8);inspectState(map["origin"]);inspectState(map["state"]);
   if(std::string(group)!="cell_maps"){inspectM(map["cell_A"],30,30);inspectM(map["cell_B"],30,8);inspectV(map["cell_defect"],30);inspectState(map["cell_origin"]);}
  }}
  for(const auto& z:out["value"]["substeps"]){inspectState(z,true);}
  for(const auto& z:out["value"]["cycle_end_states"]){inspectState(z);}
  for(const auto& z:out["value"]["cell_end_states"]){inspectState(z);}
  inspectState(out["value"]["final_state"]);
 }
 auto terms=c["terms"];require(terms.IsSequence()&&terms.size()<=l.max_terms,"planned terms cap");std::size_t rows=0,additions=0;for(const auto& t:terms){require(t["F"].IsSequence()&&t["F"].size()>0&&t["F"].size()<=l.max_factor_rows,"planned factor rows");rows=add(rows,t["F"].size());str(t["name"]);str(t["units"]);inspectM(t["F"],t["F"].size(),dy);inspectV(t["f0"],t["F"].size());inspectV(t["linear"],dy);number(t["constant"]);require(t["sample_additions"].IsSequence()&&t["sample_additions"].size()<=l.max_samples,"planned sample additions");additions=add(additions,t["sample_additions"].size());for(const auto& s:t["sample_additions"]){auto index=integer(s["sample_index"]);require(index<samples,"preflight sample addition index");inspectM(s["coefficient"],t["F"].size(),nx);}}
 // Conservative cumulative arithmetic/storage/serialization upper envelope,
 // including native carrier, solver scratch, chained Hessian intermediates.
 std::size_t v=mul(24,mul(dx,dx));v=add(v,mul(16,mul(dx,add(add(du,nx),1))));
 v=add(v,mul(samples,add(add(mul(24,mul(nx,dy)),mul(32,mul(nx,du))),mul(64,mul(nx,nx)))));
 v=add(v,mul(32,mul(rows,dy)));v=add(v,mul(32,mul(add(terms.size(),1),mul(du,dy))));
 v=add(v,mul(24,mul(add(terms.size(),1),mul(du,du))));v=add(v,mul(8,mul(N,mul(nx,du))));
 // Every addition can touch the parent factor's full rows; use max row cap.
 v=add(v,mul(additions,mul(8,mul(l.max_factor_rows,add(dy,nx)))));
 require(v<=l.max_problem_numeric_elements,"planned problem cumulative cap");return v;
}
YAML::Node vNode(const Vector& v,ah::ProblemBudget& b){ah::detail::finite(v);b.reserve(v.size());YAML::Node n(YAML::NodeType::Sequence);for(Eigen::Index j=0;j<v.size();++j)n.push_back(v(j));return n;}
YAML::Node mNode(const Matrix& v,ah::ProblemBudget& b){ah::detail::finite(v);b.reserve(mul(v.rows(),v.cols()));YAML::Node n(YAML::NodeType::Sequence);for(Eigen::Index r=0;r<v.rows();++r){YAML::Node row(YAML::NodeType::Sequence);for(Eigen::Index c=0;c<v.cols();++c)row.push_back(v(r,c));n.push_back(row);}return n;}
YAML::Node viewNode(const ah::AffineView& v,ah::ProblemBudget& b){YAML::Node n;n["offset"]=vNode(v.offset,b);n["control"]=mNode(v.control,b);n["initial"]=mNode(v.initial,b);return n;}
YAML::Node termNode(const ah::CondensedTerm& t,ah::ProblemBudget& b){YAML::Node n;n["name"]=textNode(t.name);n["units"]=textNode(t.units);n["used_F"]=mNode(t.used_F,b);n["used_f0"]=vNode(t.used_f0,b);n["used_linear"]=vNode(t.used_linear,b);n["used_constant"]=t.used_constant;n["factor"]=mNode(t.factor,b);n["offset"]=vNode(t.offset,b);n["H"]=mNode(t.H,b);n["g"]=vNode(t.g,b);n["constant"]=t.constant;return n;}
YAML::Node evalNode(const ah::Assembly& a,const ah::CondensedTerm& t,const Vector& U,const ah::Limits& l,ah::ProblemBudget& b){auto e=ah::evaluate(a,t,U,l,b);YAML::Node n;n["name"]=textNode(t.name);n["lifted_value"]=e.lifted_value;n["condensed_value"]=e.condensed_value;n["lifted_chain_gradient"]=vNode(e.lifted_chain_gradient,b);n["condensed_gradient"]=vNode(e.condensed_gradient,b);n["lifted_chain_hessian"]=mNode(e.lifted_chain_hessian,b);n["condensed_hessian"]=mNode(e.condensed_hessian,b);return n;}
YAML::Node resultNode(const ah::Problem& p,const ah::Assembly& a,const ah::Objective& o,const Vector& U,const ah::Limits& l,ah::ProblemBudget& b){
 YAML::Node r;r["success"]=true;r["error"]=textNode("");r["scope"]=scopeNode();auto id=r["source"];id["kind"]=textNode(p.source.kind);id["artifact_id"]=textNode(p.source.artifact_id);id["file_sha256"]=textNode(p.source.file_sha256);id["row_name"]=textNode(p.source.row_name);id["source_binary_sha256"]=textNode(p.source.source_binary_sha256);id["certificate_name"]=textNode(p.source.certificate_name);id["full_nominal_source_certified"]=p.source.full_nominal_source_certified;id["actual_initial_shifted"]=!p.nominal_cells.empty()&&!ah::detail::exact(p.actual_initial,p.nominal_cells.front().origin);
 auto n=r["assembly"];n["nx"]=p.nx;n["nu"]=p.nu;n["N"]=p.cells.size();n["cycles"]=YAML::Node(YAML::NodeType::Sequence);for(const auto& c:p.cells)n["cycles"].push_back(c.cycles);n["recursive_states"]=YAML::Node(YAML::NodeType::Sequence);for(const auto& v:a.recursive_states)n["recursive_states"].push_back(viewNode(v,b));
 auto lifted=n["lifted"];lifted["L"]=mNode(a.L,b);lifted["E"]=mNode(a.E,b);lifted["f"]=vNode(a.f,b);lifted["initial_selector"]=mNode(a.initial_selector,b);lifted["X_control"]=mNode(a.X_control,b);lifted["X_offset"]=vNode(a.X_offset,b);lifted["X_initial"]=mNode(a.X_initial,b);lifted["T"]=mNode(a.T,b);lifted["t"]=vNode(a.t,b);
 n["samples"]=YAML::Node(YAML::NodeType::Sequence);for(const auto& v:a.samples){YAML::Node s;s["cell"]=v.cell;s["cycle"]=v.cycle;s["half"]=v.half;s["recursive"]=viewNode(v.recursive,b);s["lifted_factor"]=mNode(v.lifted_factor,b);s["lifted_offset"]=vNode(v.lifted_offset,b);s["eliminated"]=viewNode(v.eliminated,b);n["samples"].push_back(s);}n["nominal_cell_defect_residual_max"]=vNode(a.nominal_cell_defect_residual_max,b);n["nominal_sample_defect_residual_max"]=vNode(a.nominal_sample_defect_residual_max,b);
 auto objective=r["objective"];objective["terms"]=YAML::Node(YAML::NodeType::Sequence);for(const auto& t:o.terms)objective["terms"].push_back(termNode(t,b));objective["sum"]=termNode(o.sum,b);
 auto ev=r["evaluation"];ev["controls"]=vNode(U,b);ev["terms"]=YAML::Node(YAML::NodeType::Sequence);for(const auto& t:o.terms)ev["terms"].push_back(evalNode(a,t,U,l,b));ev["sum"]=evalNode(a,o.sum,U,l,b);return r;
}
std::string quoted(const std::string& s){std::ostringstream o;o<<'"';for(unsigned char c:s){if(c=='"'||c=='\\')o<<'\\'<<c;else if(c<32)o<<"\\u"<<std::hex<<std::setw(4)<<std::setfill('0')<<int(c)<<std::dec;else o<<c;}o<<'"';return o.str();}
void emit(std::ostream& o,const YAML::Node& n){
 if(n.IsMap()){o<<'{';bool first=true;for(const auto& x:n){if(!first)o<<',';first=false;o<<quoted(x.first.as<std::string>())<<':';emit(o,x.second);}o<<'}';}
 else if(n.IsSequence()){o<<'[';bool first=true;for(const auto& x:n){if(!first)o<<',';first=false;emit(o,x);}o<<']';}
 else if(n.IsNull())o<<"null";
 else if(isString(n))o<<quoted(n.Scalar());
 else {auto s=n.Scalar();require(s=="true"||s=="false"||std::regex_match(s,NUM),"output scalar type");if(s!="true"&&s!="false")number(n);o<<s;}
}
YAML::Node limitsNode(const ah::Limits& l){YAML::Node n;
#define LFIELD(x) n[#x]=l.x
 LFIELD(max_cases);LFIELD(max_cells);LFIELD(max_samples);LFIELD(max_nx);LFIELD(max_nu);LFIELD(max_terms);LFIELD(max_factor_rows);LFIELD(max_matrix_elements);LFIELD(max_document_bytes);LFIELD(max_problem_numeric_elements);LFIELD(max_cli_numeric_elements);LFIELD(arithmetic_abs);LFIELD(arithmetic_rel);
#undef LFIELD
 return n;}
int main(int argc,char** argv){
 if(argc!=5||std::string(argv[1])!="--policy"){std::cerr<<"--policy POLICY.json INPUT.json FRESH_OUTPUT.json\n";return 2;}
 if(std::filesystem::exists(argv[4])){std::cerr<<"refuse existing output\n";return 2;}
 try {const ah::Limits limits;ah::CliBudget cli;auto policy=load(argv[2],limits,cli);require(integer(policy.node["schema_version"])==1,"policy schema version");scope(policy.node["scope"]);
  auto fixedLimits=limitsNode(limits);require(policy.node["limits"].IsMap()&&policy.node["limits"].size()==fixedLimits.size(),"policy limits roster");for(const auto& x:fixedLimits){auto key=x.first.as<std::string>();if(key=="arithmetic_abs"||key=="arithmetic_rel")require(number(policy.node["limits"][key])==number(x.second),"policy fixed tolerance altered");else require(integer(policy.node["limits"][key])==integer(x.second),"policy canonical integer limit altered");}
  auto artifactsNode=policy.node["artifacts"];require(artifactsNode.IsSequence()&&artifactsNode.size()<=4,"artifact count cap");std::map<std::string,Artifact> artifacts;
  for(const auto& a:artifactsNode){Artifact artifact;artifact.id=str(a["id"]);artifact.binary=str(a["source_binary_sha256"]);artifact.archive=str(a["archive_sha256"]);require(artifact.binary==F1&&str(a["certificate_name"])==CERT,"public pinned policy source");require(std::regex_match(artifact.archive,std::regex("[0-9a-f]{64}")),"archive hash shape");artifact.doc=load(str(a["path"]),limits,cli,str(a["sha256"]));require(artifact.doc.digest==str(a["sha256"]),"public source bytes hash mismatch");require(artifacts.emplace(artifact.id,std::move(artifact)).second,"duplicate artifact id");}
  auto inputDoc=load(argv[3],limits,cli);require(integer(inputDoc.node["schema_version"])==1,"input schema version");auto cases=inputDoc.node["cases"];require(cases.IsSequence()&&cases.size()<=limits.max_cases,"case roster cap");
  std::vector<std::size_t> planned;std::vector<std::string> errors;std::set<std::string> names;std::size_t totalPlan=cli.charged_numeric_elements;
  for(const auto& c:cases){auto name=str(c["name"]);require(!name.empty()&&names.insert(name).second,"unique case name");try {auto estimate=plan(c,artifacts,limits);planned.push_back(estimate);errors.emplace_back();totalPlan=add(totalPlan,estimate);}catch(const std::exception& e){planned.push_back(0);errors.emplace_back(e.what());}}
  require(totalPlan<=limits.max_cli_numeric_elements,"planned aggregate CLI numeric cap");
  YAML::Node out;out["schema_version"]=1;out["metadata"]["namespace"]=textNode("phase5_public_affine_horizon");out["metadata"]["policy_sha256"]=textNode(policy.digest);out["metadata"]["limits"]=fixedLimits;out["metadata"]["scope"]=scopeNode();out["cases"]=YAML::Node(YAML::NodeType::Sequence);
  for(std::size_t j=0;j<cases.size();++j){const auto c=cases[j];ah::ProblemBudget budget{cli,0,limits,planned[j]};YAML::Node r;Selected sel;bool selected=false,nominalSupported=false;YAML::Node bridge;
   try {require(errors[j].empty(),errors[j]);scope(c["scope"]);auto kind=str(c["source"]["kind"]);ah::Problem p;
    if(kind=="public_saved_json"){sel=select(c["source"],artifacts);selected=true;nominalSupported=supported(sel);p=publicProblem(sel,c["actual_initial"],limits,budget);bridge=nativeBridge(sel,p,limits,budget);}
    else {p=genericProblem(c["source"],c["actual_initial"],limits,budget);bridge["used_native_normalization"]=false;bridge["matched_json_cumulative_fields"]=false;bridge["multicycle_local_cumulative_distinct"]=false;bridge["source_file_sha256"]=textNode("");bridge["source_binary_sha256"]=textNode("");bridge["cell_count"]=0;bridge["sample_count"]=0;}
    auto a=ah::assemble(p,limits,budget);auto du=mul(p.nu,p.cells.size()),dy=add(mul(p.nx,add(p.cells.size(),1)),du);auto ts=factors(c["terms"],dy,p.nx,limits,budget);auto objective=ah::substitute(a,ts,limits,budget);auto U=vector(c["evaluate_controls"],du,budget);r=resultNode(p,a,objective,U,limits,budget);r["native_bridge"]=bridge;
    require(budget.charged_numeric_elements<=planned[j],"actual numeric charges exceeded conservative plan");
   }catch(const std::exception& e){r=YAML::Node(YAML::NodeType::Map);r["success"]=false;r["error"]=textNode(e.what());r["refusal_code"]=textNode(selected&&!nominalSupported?"SOURCE_INCOMPLETE_OR_UNSUPPORTED":"INVALID_SOURCE_SHAPE_OR_RESOURCE");r["scope"]=scopeNode();r["source"]=c["source"];if(selected){r["source_diagnostic"]=sel.row["original_output"];}else r["source_diagnostic"]=YAML::Node(YAML::NodeType::Map);}
   r["name"]=textNode(str(c["name"]));out["cases"].push_back(r);
  }
  // Check complete serialization before creating the requested output. Retain
  // numeric nodes already charged by output constructors; no string reparse.
  std::ostringstream serialized;emit(serialized,out);auto bytes=serialized.str();require(bytes.size()<=limits.max_document_bytes,"output byte cap");
  int fd=::open(argv[4],O_WRONLY|O_CREAT|O_EXCL,0644);require(fd>=0,"exclusive output create failed");bytes.push_back('\n');std::size_t offset=0;while(offset<bytes.size()){auto wrote=::write(fd,bytes.data()+offset,bytes.size()-offset);if(wrote<=0){::close(fd);throw std::runtime_error("output write failed; partial file retained");}offset+=wrote;}require(::close(fd)==0,"output close failed");return 0;
 }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
