#pragma once
#include <string>
#include <vector>
#include <cstdint>
#include <stdexcept>
namespace phase5_bounded_current_trials_v1 {
struct Record {std::uint64_t boundary=0;std::string nominal;bool geometry_complete=false,validation_attempted=false,token_issued=false;};
class Registry {std::uint64_t boundaries_,per_boundary_,global_;std::vector<Record> records_;static void need(bool b,const char* s){if(!b)throw std::invalid_argument(s);}public:
 Registry(std::uint64_t boundaries,std::uint64_t trials,std::uint64_t global=0):boundaries_(boundaries),per_boundary_(trials),global_(global?global:boundaries*trials){need(boundaries>0&&boundaries<=128&&trials>0&&trials<=3,"finite current trial registry");need(global_>=boundaries_&&global_<=boundaries_*per_boundary_,"finite explicit global trial quota");records_.reserve(global_);}
 void geometry(std::uint64_t boundary,const std::string& nominal){need(boundary<boundaries_&&nominal.size()==64&&records_.size()<global_,"current trial before geometry cumulative cap");std::uint64_t count=0;for(const auto& r:records_){need(r.nominal!=nominal,"genuine invocation cannot replay");if(r.boundary==boundary){++count;need(!r.token_issued,"accepted token prevents another planning trial");}need(r.boundary<=boundary,"current trial boundaries cannot rewind");}need(count<per_boundary_,"finite relinearization per current boundary");records_.push_back({boundary,nominal});}
 void geometryComplete(const std::string& nominal){need(!records_.empty()&&records_.back().nominal==nominal&&!records_.back().geometry_complete,"same entered geometry invocation complete once");records_.back().geometry_complete=true;}
 void validation(std::uint64_t boundary,const std::string& nominal){need(!records_.empty(),"validation needs authentic entered nominal geometry");auto& r=records_.back();need(r.boundary==boundary&&r.nominal==nominal&&r.geometry_complete&&!r.validation_attempted&&!r.token_issued,"one fresh validation for current geometric nominal invocation");r.validation_attempted=true;}
 void token(const std::string& nominal){need(!records_.empty(),"token needs entered trial");auto& r=records_.back();need(r.nominal==nominal&&r.validation_attempted&&!r.token_issued,"one successful private validation token per trial");r.token_issued=true;}
 const std::vector<Record>& records()const{return records_;}
};
}
