#pragma once
#include "boundary_retention_limits57.hpp"
#include <Eigen/Core>
#include <vector>
#include <cmath>
#include <stdexcept>
namespace phase5_negative_leaving59_v1 {
using Face=phase5_working_face_basis_v1::Face;
struct Event {int iteration=0,row=-1,side=1,position=-1;double selected_multiplier=0,minimum_multiplier=0;};
constexpr std::uint64_t maximum_events=512;
constexpr std::uint64_t conservative_inventory59=phase5_boundary_retention_limits57::conservative_numeric_inventory57+maximum_events*6+128;
static_assert(conservative_inventory59==744208&&conservative_inventory59<phase5_boundary_retention_limits57::declared_numeric_allowance57,"all512 explicit six-field leaving records and local/vector/scalar inventory fit unchanged745000 stop reservation; global1.8B unchanged, externalAS4GiB remains mandatory");
// Current scaled solver A row indices only. These are not original14756SI IDs.
inline int select(const std::vector<Face>& faces,const Eigen::VectorXd& solution,int primal_size,int row_count){
 auto need=[](bool ok,const char*why){if(!ok)throw std::invalid_argument(why);};need(primal_size>0&&primal_size<=144&&row_count>0&&row_count<=20000&&faces.size()<=144&&solution.size()==primal_size+static_cast<int>(faces.size())&&solution.allFinite(),"bounded finite negative leaving inputs");int selected=-1;
 for(std::size_t j=0;j<faces.size();++j){const auto&face=faces[j];need(face.row>=0&&face.row<row_count&&(face.side==1||face.side==-1),"valid current solver face ID/side");for(std::size_t k=0;k<j;++k)need(faces[k].row!=face.row,"unique current solver working face rows");
  if(solution(primal_size+j)<-1e-12&&(selected<0||face.row<faces[selected].row))selected=j;
 }
 return selected;
}
}
