#include "causal_soft_servo.hpp"
#include <iostream>
#include <functional>
#include <limits>
#include <string>
using namespace phase5_local_model;
Model baseline(){Model m;m.mass=Vector::Constant(1,.2);m.bias=Vector::Constant(1,.01);m.kp=Vector::Constant(1,1000);m.damping=Vector::Constant(1,100);m.friction=Vector::Constant(1,.3);m.impedance=Vector::Constant(1,.9);m.decay=Vector::Constant(1,100);m.q_min=Vector::Constant(1,-.01);m.q_max=Vector::Constant(1,.01);m.error_min=Vector::Constant(1,-.001);m.error_max=Vector::Constant(1,.001);m.velocity_abs_max=.05;return m;}
int main(){
 int failures=0,checks=0;double nan=std::numeric_limits<double>::quiet_NaN(),inf=std::numeric_limits<double>::infinity();
 std::cout<<"case,entry,rejected\n";
 for(int test=0;test<27;++test){
  Model m=baseline();Vector z=Vector::Zero(6),u=Vector::Zero(2);z(2)=-.00001;z(4)=.2;z(5)=.01;std::string name;
  switch(test){
   case 0:name="mass_empty";m.mass.resize(0);break;
   case 1:name="bias_dimension";m.bias.resize(2);break;
   case 2:name="kp_dimension";m.kp.resize(2);break;
   case 3:name="qmin_dimension";m.q_min.resize(2);break;
   case 4:name="error_max_dimension";m.error_max.resize(2);break;
   case 5:name="mass_nan";m.mass(0)=nan;break;
   case 6:name="bias_inf";m.bias(0)=inf;break;
   case 7:name="mass_negative";m.mass(0)=-1;break;
   case 8:name="mass_zero";m.mass(0)=0;break;
   case 9:name="kp_zero";m.kp(0)=0;break;
   case 10:name="damping_negative";m.damping(0)=-1;break;
   case 11:name="friction_negative";m.friction(0)=-1;break;
   case 12:name="impedance_zero";m.impedance(0)=0;break;
   case 13:name="impedance_above_one";m.impedance(0)=1.01;break;
   case 14:name="decay_zero";m.decay(0)=0;break;
   case 15:name="qbox_reversed";m.q_min(0)=.02;break;
   case 16:name="errorbox_reversed";m.error_min(0)=.002;break;
   case 17:name="velocity_limit_zero";m.velocity_abs_max=0;break;
   case 18:name="velocity_limit_inf";m.velocity_abs_max=inf;break;
   case 19:name="state_short";z.resize(5);break;
   case 20:name="state_nan";z(0)=nan;break;
   case 21:name="control_short";u.resize(1);break;
   case 22:name="control_nan";u(0)=nan;break;
   case 23:name="state_long";z.conservativeResize(7);z(6)=0;break;
   case 24:name="control_long";u.conservativeResize(3);u(2)=0;break;
   case 25:name="impedance_nan";m.impedance(0)=nan;break;
   default:name="qbox_nan";m.q_max(0)=nan;break;
  }
  for(int entry=0;entry<3;++entry){
   if(entry==0&&(test==21||test==22||test==24))continue;
   bool rejected=false;try{if(entry==0)m.domain(z);else if(entry==1)(void)cycle(z,u,m);else (void)cell(z,u,1,m);}catch(const std::exception&){rejected=true;}
   ++checks;if(!rejected)++failures;std::cout<<name<<','<<(entry==0?"domain":entry==1?"cycle":"cell")<<','<<rejected<<'\n';
  }
 }
 std::cerr<<checks<<" invalid-entry checks; failures="<<failures<<'\n';return failures?1:0;
}
