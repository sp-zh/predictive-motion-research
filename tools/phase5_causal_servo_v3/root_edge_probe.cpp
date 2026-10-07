#include "causal_soft_servo.hpp"
#include <iostream>
using namespace phase5_local_model;
int main(){Model m;m.mass=Vector::Constant(1,1e-300);m.bias=Vector::Zero(1);m.kp=Vector::Constant(1,1e308);m.damping=Vector::Zero(1);m.friction=Vector::Zero(1);m.impedance=Vector::Constant(1,.9);m.decay=Vector::Constant(1,100);m.q_min=Vector::Constant(1,-.01);m.q_max=Vector::Constant(1,.01);m.error_min=Vector::Constant(1,-.001);m.error_max=Vector::Constant(1,.001);m.velocity_abs_max=.05;Vector z=Vector::Zero(6),u=Vector::Zero(2);z(4)=.2;
bool validated=false;try{m.validate();validated=true;auto t=cycle(z,u,m);std::cout<<"{\"model_validated\":"<<validated<<",\"threw\":false,\"state_finite\":"<<t.state.allFinite()<<",\"A_finite\":"<<t.A.allFinite()<<",\"B_finite\":"<<t.B.allFinite()<<",\"defect_finite\":"<<t.defect.allFinite()<<"}\n";}catch(const std::exception&){std::cout<<"{\"model_validated\":"<<validated<<",\"threw\":true}\n";}}
