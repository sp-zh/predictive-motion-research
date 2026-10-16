#pragma once
#include <Eigen/Core>
#include <Eigen/LU>
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <stdexcept>
#include <string>
#include <vector>
namespace phase5_working_face_basis_v1 {
// Numeric inventory only; vector capacity/strings/Eigen allocator and library
// scratch are not an RSS proof. External native AS4GiB remains mandatory.
constexpr std::uint64_t declared_endpoint_capacity53=16384;
constexpr std::uint64_t conservative_numeric_inventory53=155648+65536+20000+20000+144+288+248832+16384*8;
constexpr std::uint64_t declared_numeric_allowance53=700000;
static_assert(conservative_numeric_inventory53==641520&&conservative_numeric_inventory53<declared_numeric_allowance53,"fresh53 full16384 explicit numeric inventory before stop-trial allocation");

constexpr std::uint64_t declared_stop_boundary_capacity54=4096;
constexpr std::uint64_t conservative_numeric_inventory54=conservative_numeric_inventory53+declared_stop_boundary_capacity54*6;
static_assert(conservative_numeric_inventory54==666096&&conservative_numeric_inventory54<declared_numeric_allowance53,"fresh54 conservatively charges all4096 boundary records, no deduction of previously charged1024; unchanged700K stop precharge");

struct Face {int row=0,side=1;};
struct BasisDiagnostic {int iteration=0,original_count=0,rank=0,blocker_row=-1,blocker_side=1;bool rank_measured=false,span_measured=false,complete=false;double span_error=0;std::string error;std::vector<std::uint64_t> old_encoded;std::vector<int> kept_positions;};
struct EndpointDiagnostic {int iteration=0,row=0;double start=0,travel=0,endpoint=0,lower=0,upper=0,violation=0;};
struct RefinementDiagnostic55 {int iteration=0,step=0,rank=0,dimension=0,reason=0;bool before_available=false,correction_available=false,after_available=false,accepted=false;double before=0,after=0,correction_inf=0,solution_inf=0,correction_cap=0,initial_double_residual=0;};
struct Trace {std::vector<BasisDiagnostic> basis;std::vector<EndpointDiagnostic> endpoints;std::vector<RefinementDiagnostic55> refinements;};
constexpr std::uint64_t maximum_refinement_records55=512*3;
constexpr std::uint64_t conservative_numeric_inventory55=conservative_numeric_inventory54+maximum_refinement_records55*16+1184;
static_assert(conservative_numeric_inventory55==691856&&conservative_numeric_inventory55<declared_numeric_allowance53,"bounded1536 refinements plus3vectors/scalars within unchanged700K stop precharge; AS4GiB still mandatory");
inline BasisDiagnostic reduce(const Eigen::MatrixXd& A,const std::vector<Face>& faces,int iteration,int blocker_row,int blocker_side){
 BasisDiagnostic out;out.iteration=iteration;out.original_count=faces.size();out.blocker_row=blocker_row;out.blocker_side=blocker_side;
 auto need=[](bool b,const char* s){if(!b)throw std::invalid_argument(s);};
 try{const int n=A.cols();need(n>0&&n<=144&&A.rows()>0&&A.rows()<=20000&&faces.size()==static_cast<std::size_t>(n),"bounded fullface basis shapes before allocation");need(A.allFinite()&&blocker_row>=0&&blocker_row<A.rows()&&(blocker_side==1||blocker_side==-1),"finite fullface basis matrix/blocker before allocation");
  for(int j=0;j<n;++j){need(faces[j].row>=0&&faces[j].row<A.rows()&&(faces[j].side==1||faces[j].side==-1),"finite valid fullface indices/sides before allocation");for(int k=0;k<j;++k)need(faces[k].row!=faces[j].row,"unique fullface row IDs before allocation");need(faces[j].row!=blocker_row,"new blocker absent from full working set");}
  out.old_encoded.reserve(n);for(const auto& f:faces)out.old_encoded.push_back(2ULL*f.row+(f.side==1));
  Eigen::MatrixXd WT(n,n);for(int j=0;j<n;++j)WT.col(j)=faces[j].side*A.row(faces[j].row).transpose();
  Eigen::FullPivLU<Eigen::MatrixXd> ranker(WT);out.rank=ranker.rank();out.rank_measured=true;need(out.rank>0&&out.rank<n,"full face cap has no certified numerical redundancy");out.kept_positions.reserve(out.rank);for(int j=0;j<out.rank;++j)out.kept_positions.push_back(ranker.permutationQ().indices()(j));std::sort(out.kept_positions.begin(),out.kept_positions.end());
  Eigen::MatrixXd basis(n,out.rank);for(int j=0;j<out.rank;++j)basis.col(j)=WT.col(out.kept_positions[j]);Eigen::FullPivLU<Eigen::MatrixXd> represent(basis);need(represent.rank()==out.rank,"independent selected numerical face basis");const Eigen::MatrixXd coefficients=represent.solve(WT);need(coefficients.allFinite(),"finite face basis coefficients");out.span_error=(basis*coefficients-WT).cwiseAbs().maxCoeff();out.span_measured=true;need(std::isfinite(out.span_error)&&out.span_error<=1e-12,"numerical active face span reconstruction residual");out.complete=true;
 }catch(const std::exception& e){out.complete=false;out.error=e.what();}return out;
}
inline bool endpointWithinExistingNumericDomain(double endpoint,double lower,double upper){if(!std::isfinite(endpoint)||!std::isfinite(lower)||!std::isfinite(upper)||lower>upper)throw std::invalid_argument("finite ordered numerical fullendpoint bounds");return std::max({0.,lower-endpoint,endpoint-upper})<=1e-12;}
// These are NUMERICAL working-set/hint diagnostics only. Full A/l/u remains;
// no exactrank/removedQPconstraint/physicaldomain certificate. Caller reserves
// bounded logical stores before allocations, retains every failure and checks
// each actual step/final allrows, original native/SI/literal/B/privateC gates.
}
