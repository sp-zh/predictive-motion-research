#pragma once
#include "negative_leaving59.hpp"
#include <cstring>
namespace phase5_exact_cycle61_v1 {
using Face=phase5_working_face_basis_v1::Face;
constexpr std::size_t maximum_primal=144,maximum_faces=144,maximum_eligibilities=144,summary_scalar_slots=128;
constexpr std::uint64_t additional_inventory=maximum_primal+2*maximum_faces+maximum_eligibilities+summary_scalar_slots;
constexpr std::uint64_t conservative_inventory=phase5_negative_leaving59_v1::conservative_inventory59+additional_inventory;
static_assert(additional_inventory==704&&conservative_inventory==744912&&conservative_inventory<phase5_boundary_retention_limits57::declared_numeric_allowance57,"pending144x+144two-fieldfaces+144existing-leaving-indices+128scalar/vector metadata fit unchanged745000 stop reservation; no extra m-mask or matrix");
struct State {
 Eigen::VectorXd previous_primal;std::vector<Face> previous_faces;int previous_row=-1,previous_side=0,previous_iteration=-3,previous_generation=-1;bool available=false;
 void initialize(int n){if(n<=0||n>144||available||previous_primal.size())throw std::invalid_argument("bounded fresh exact-cycle state");previous_primal.resize(n);previous_faces.reserve(maximum_faces);}
 // Generation covers every actual0->1 mask change: old basis reduction and
 // new cycle eligibility. It is monotone and the mask is never cleared.
 bool consider(const Eigen::VectorXd&x,const std::vector<Face>&faces,int position,int iteration,int&generation,std::vector<unsigned char>&mask,std::vector<std::uint64_t>&indices,std::uint64_t leaving_index,double direction_inf,double chosen_lambda){
  auto need=[](bool ok,const char*why){if(!ok)throw std::invalid_argument(why);};const int n=x.size();need(n>0&&n<=144&&previous_primal.size()==n&&faces.size()<=maximum_faces&&position>=0&&position<static_cast<int>(faces.size())&&iteration>=0&&iteration<512&&generation>=0&&generation<=20000&&mask.size()>0&&mask.size()<=20000&&leaving_index<512&&indices.size()<=static_cast<std::size_t>(n)&&indices.capacity()<=maximum_eligibilities&&x.allFinite()&&std::isfinite(direction_inf)&&direction_inf>=0&&direction_inf<=1e-12&&std::isfinite(chosen_lambda)&&chosen_lambda<-1e-12,"bounded existing negative direction-zero cycle inputs");const auto removed=faces[position];need(removed.row>=0&&removed.row<static_cast<int>(mask.size())&&(removed.side==1||removed.side==-1),"bounded exact-cycle current row/side");bool same_faces=available&&previous_faces.size()==faces.size();if(same_faces)for(std::size_t j=0;j<faces.size();++j)if(previous_faces[j].row!=faces[j].row||previous_faces[j].side!=faces[j].side){same_faces=false;break;}
  const bool same_x=available&&std::memcmp(previous_primal.data(),x.data(),n*sizeof(double))==0;
  const bool repeat=available&&previous_row==removed.row&&previous_side==removed.side&&previous_iteration+2==iteration&&previous_generation==generation&&same_faces&&same_x&&!mask[removed.row];
  if(repeat){need(indices.size()<static_cast<std::size_t>(n)&&indices.size()<maximum_eligibilities,"finite n<=144 exact-cycle eligibility preappend cap");need(indices.empty()||indices.back()<leaving_index,"ordered existing negative-leaving index");indices.push_back(leaving_index);mask[removed.row]=1;++generation;}
  previous_row=removed.row;previous_side=removed.side;previous_iteration=iteration;previous_generation=generation;previous_primal=x;previous_faces.assign(faces.begin(),faces.end());available=true;need(previous_faces.capacity()<=maximum_faces,"bounded pending full ordered-face capacity");return repeat;
 }
};
}
