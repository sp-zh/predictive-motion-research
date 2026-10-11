#include "bounded_current_trials.hpp"
#include <iostream>
using phase5_bounded_current_trials_v1::Registry;
void need(bool b){if(!b)throw std::runtime_error("registry invariant");}
template<class F>void no(F f){bool b=false;try{f();}catch(const std::invalid_argument&){b=true;}need(b);}
std::string id(int i){std::string s(64,'a');s[0]='A'+i;return s;}
int main(){Registry r(64,3);no([&]{r.validation(0,id(0));});r.geometry(0,id(0));no([&]{r.validation(0,id(0));});r.geometryComplete(id(0));no([&]{r.geometryComplete(id(0));});no([&]{r.validation(1,id(0));});no([&]{r.validation(0,id(1));});r.validation(0,id(0));no([&]{r.validation(0,id(0));});no([&]{r.geometry(0,id(0));});r.geometry(0,id(1));r.geometryComplete(id(1));r.validation(0,id(1));r.geometry(0,id(2));r.geometryComplete(id(2));r.validation(0,id(2));no([&]{r.geometry(0,id(3));});r.token(id(2));no([&]{r.token(id(2));});no([&]{r.geometry(0,id(4));});r.geometry(1,id(3));no([&]{r.geometry(0,id(4));});need(r.records().size()==4&&r.records()[0].validation_attempted&&!r.records()[0].token_issued&&r.records()[2].token_issued);Registry cap(1,1);cap.geometry(0,id(0));no([&]{cap.geometry(0,id(1));});no([&]{cap.geometry(1,id(1));});std::cout<<"PASS cumulative/freshnonce/no-replay/boundary-monotonicity/perboundary-globalcaps/enteredcompletegeometry/uniquevalidation/tokenblocksnewtrial; pure registry not authentic Model owner proof\n";}
