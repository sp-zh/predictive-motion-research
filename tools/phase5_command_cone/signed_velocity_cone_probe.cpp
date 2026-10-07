#include "signed_velocity_cone.hpp"
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>
int main(int argc,char** argv) {
  if(argc!=4)return 2;
  std::ifstream input(argv[1]);std::ofstream output(argv[2]),rows(argv[3]);
  if(!input||!output||!rows)return 2;
  output<<std::setprecision(17)<<"case,feasible,lower_acceleration,upper_acceleration,stop_acceleration,stop_velocity\n";
  rows<<std::setprecision(17)<<"case,K,lower,upper\n";
  std::string line;std::getline(input,line);
  while(std::getline(input,line)) {
    std::istringstream stream(line);std::string cell;std::getline(stream,cell,',');int id=std::stoi(cell);
    double v[6];for(auto& x:v){if(!std::getline(stream,cell,','))return 2;x=std::stod(cell);}
    phase5_diagnostic::Limits l{v[2],v[3],v[4],v[5]};
    try{
      auto interval=phase5_diagnostic::accelerationInterval(v[0],v[1],l);
      output<<id<<','<<interval.feasible<<','<<interval.lower<<','<<interval.upper;
      if(interval.feasible){double a=std::clamp(-v[0]/l.dt,interval.lower,interval.upper);output<<','<<a<<','<<v[0]+l.dt*a;}
      else output<<",nan,nan";
      output<<'\n';
      for(auto r:phase5_diagnostic::candidateVelocityRows(v[0],l))rows<<id<<','<<r.coefficient<<','<<r.lower<<','<<r.upper<<'\n';
    }catch(const std::exception& e){std::cerr<<id<<':'<<e.what()<<'\n';return 3;}
  }
  return 0;
}
