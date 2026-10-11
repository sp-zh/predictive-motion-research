#pragma once
#include "integrated_horizon_qp.hpp"
#include "geometry.hpp"
#include <algorithm>
#include <set>
#include <stdexcept>
namespace phase5_nominal_geometry_selection_v1 {
namespace core=phase5_active_session_qp_v1;
using Query=predictive_motion::geometry::Query;
struct Selected {core::GeometryRow row;Query original_query;};
inline std::string identity(const Query& q){return q.type+"/"+q.a+"/"+q.b+"/cover/"+std::to_string(q.cover_index);}
// Deliberate QP assistance subset: lowest2true+lowest2cover at each genuine
// nominal 2ms sample. Full nonlinear candidate all-pair checks remain required.
inline std::vector<Selected> select(int sample,const predictive_motion::geometry::Snapshot& all){
 auto need=[](bool v,const char* why){if(!v)throw std::invalid_argument(why);};need(sample>=0&&sample<400&&all.queries.size()>0&&all.queries.size()<=20000,"bounded genuine sample/full query roster");need(std::isfinite(all.minimum_true)&&std::isfinite(all.minimum_cover),"both true and cover minima required");std::vector<const Query*> true_rows,cover_rows;std::set<std::string> roster;
 for(const auto& q:all.queries){need((q.type=="true"||q.type=="cover")&&std::isfinite(q.distance)&&q.gradient.size()==7&&q.gradient.allFinite()&&q.normal.allFinite()&&q.witness_a.allFinite()&&q.witness_b.allFinite()&&std::abs(q.normal.norm()-1)<=1e-6&&(q.witness_b-q.witness_a-q.distance*q.normal).norm()<=1e-6,"actual query gradient/witness/normal support");const auto id=identity(q);need(!q.a.empty()&&!q.b.empty()&&id.size()<=256&&roster.insert(id).second,"unique bounded query support identity");for(unsigned char c:id)need(c>=33&&c<=126,"printable query identity");(q.type=="true"?true_rows:cover_rows).push_back(&q);}
 need(true_rows.size()>=2&&cover_rows.size()>=2,"four declared assistance supports require both query families");auto order=[](const Query* a,const Query* b){return a->distance==b->distance?identity(*a)<identity(*b):a->distance<b->distance;};std::sort(true_rows.begin(),true_rows.end(),order);std::sort(cover_rows.begin(),cover_rows.end(),order);need(true_rows[0]->distance==all.minimum_true&&cover_rows[0]->distance==all.minimum_cover,"selected actual minima match full snapshot");std::vector<Selected> out;out.reserve(4);
 for(auto rows:{&true_rows,&cover_rows})for(int k=0;k<2;++k){const auto& q=*(*rows)[k];core::GeometryRow row;row.sample=sample;row.id=identity(q);row.units="m";row.Jq=q.gradient;row.nominal_value=q.distance;row.lower=.005;row.upper=1000000.;out.push_back({row,q});}return out;
}
}
