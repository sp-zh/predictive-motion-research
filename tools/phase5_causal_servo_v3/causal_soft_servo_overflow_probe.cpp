#include "causal_soft_servo.hpp"
#include <iostream>
using namespace phase5_local_model;
Model algebra(double mass,double kp){Model m;m.mass=Vector::Constant(1,mass);m.bias=Vector::Zero(1);m.kp=Vector::Constant(1,kp);m.damping=Vector::Zero(1);m.friction=Vector::Zero(1);m.impedance=Vector::Constant(1,.9);m.decay=Vector::Constant(1,100);m.q_min=Vector::Constant(1,-.01);m.q_max=Vector::Constant(1,.01);m.error_min=Vector::Constant(1,-.001);m.error_max=Vector::Constant(1,.001);m.velocity_abs_max=.05;return m;}
int main(){Vector z=Vector::Zero(6),u=Vector::Zero(2);z(4)=.2;int failures=0;
 std::cout<<"case,entry,model_validated,overflow_rejected,reason\n";
 for(int id=0;id<4;++id){Model m=algebra(id==0?1e-300:id==1?1e-320:id==2?.002:1.797e308,id==2?1e152:id==3?1.:1e308);if(id==3){m.damping(0)=1.797e308;m.decay(0)=.1;}
  bool validated=false;try{m.validate();validated=true;}catch(const std::exception&){++failures;}
  for(int entry=0;entry<2;++entry){
   // Case2 has a finite one-cycle Jacobian but overflows when composing two cycles.
   if(id==2&&entry==0){auto t=cycle(z,u,m);validateTransition(t);std::cout<<"composed,"<<"cycle_finite,"<<validated<<",0,finite_one_cycle_expected\n";continue;}
   bool rejected=false;std::string reason="no_exception";try{if(entry==0)(void)cycle(z,u,m);else (void)cell(z,u,id==2?2:1,m);}catch(const std::overflow_error& e){rejected=true;reason=e.what();}catch(const std::exception& e){reason=e.what();}
   if(!rejected)++failures;
   std::cout<<id<<','<<(entry==0?"cycle":"cell")<<','<<validated<<','<<rejected<<','<<reason<<'\n';
  }
 }
 return failures?1:0;
}
