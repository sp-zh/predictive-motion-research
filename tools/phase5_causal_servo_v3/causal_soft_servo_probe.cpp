#include "causal_soft_servo.hpp"
#include <yaml-cpp/yaml.h>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <string>
using namespace phase5_local_model;
Vector vector(const YAML::Node& x){Vector v(x.size());for(int i=0;i<v.size();++i)v(i)=x[i].as<double>();return v;}
Model model(const YAML::Node& x){Model m;auto p=x["public_parameters"],b=x["local_box"];m.mass=vector(x["mass_effective_kg_m2"]);m.bias=vector(x["bias_Nm"]);m.kp=vector(p["kp_Nm_rad"]);m.damping=vector(p["damping_Nm_s_rad"]);m.friction=vector(p["friction_bound_Nm"]);m.impedance=vector(p["impedance"]);m.decay=vector(p["reference_decay_s_inv"]);m.q_min=vector(b["q_min"]);m.q_max=vector(b["q_max"]);m.error_min=vector(b["target_error_min"]);m.error_max=vector(b["target_error_max"]);m.velocity_abs_max=b["v_abs_max"].as<double>();m.validate();return m;}
void emit(std::ostream& out,const Matrix& a){requireFinite(a,"nonfinite matrix serialization");out<<'[';for(int i=0;i<a.rows();++i){if(i)out<<',';out<<'[';for(int j=0;j<a.cols();++j){if(j)out<<',';out<<a(i,j);}out<<']';}out<<']';}
void emit(std::ostream& out,const Vector& v){requireFinite(v,"nonfinite vector serialization");out<<'[';for(int i=0;i<v.size();++i){if(i)out<<',';out<<v(i);}out<<']';}
template<class T>void emitList(std::ostream& out,const std::vector<T>& v){out<<'[';for(size_t i=0;i<v.size();++i){if(i)out<<',';emit(out,v[i]);}out<<']';}
int main(int argc,char** argv){
 if(argc!=3)return 2;
 try{
  auto input=YAML::LoadFile(argv[1]);std::ofstream out(argv[2]);if(!out)return 2;out<<std::setprecision(17)<<"{\"cases\":[";int index=0;
  for(auto c:input["cases"]){
   if(index++)out<<',';
   auto m=model(c["model"]);auto mesh=c["mesh_s"];int N=mesh.size(),nx=4*m.n()+2,nu=m.n()+1;
   Vector initial=vector(c["initial"]),current=initial;m.domain(initial);
   std::vector<Vector> states{initial},offsets{initial},defects;
   std::vector<Matrix> as,bs,maps{Matrix::Zero(nx,N*nu)},initial_maps{Matrix::Identity(nx,nx)};
   int equalities=0;out<<"{\"name\":\""<<c["name"].as<std::string>()<<"\",\"history\":[";bool first_history=true;double time=0;
   for(int k=0;k<N;++k){int count=periods(mesh[k].as<double>());Vector u=vector(c["controls"][k]);auto t=cell(current,u,count,m);Vector history_state=current;
    for(int j=0;j<count;++j){auto h=cycle(history_state,u,m);history_state=h.state;time+=command_dt;if(!first_history)out<<',';first_history=false;out<<"{\"cell\":"<<k<<",\"time_s\":"<<time<<",\"state\":";emit(out,h.state);out<<",\"branches_2ms\":[";for(int sub=0;sub<2;++sub){if(sub)out<<',';out<<'[';for(int a=0;a<m.n();++a){if(a)out<<',';out<<h.branches[sub][a];}out<<']';}out<<"]}";}
    equalities+=t.clip_equalities;current=t.state;states.push_back(current);as.push_back(t.A);bs.push_back(t.B);defects.push_back(t.defect);
    Vector nextoffset=t.A*offsets.back()+t.defect;requireFinite(nextoffset,"nonfinite horizon offset");offsets.push_back(nextoffset);
    Matrix nextmap=t.A*maps.back();requireFinite(nextmap,"nonfinite horizon control sensitivity product");nextmap.block(0,k*nu,nx,nu)+=t.B;requireFinite(nextmap,"nonfinite horizon control sensitivity");maps.push_back(nextmap);
    Matrix nextinitial=t.A*initial_maps.back();requireFinite(nextinitial,"nonfinite horizon initial sensitivity");initial_maps.push_back(nextinitial);
   }
   out<<"],\"states\":";emitList(out,states);out<<",\"cell_A\":";emitList(out,as);out<<",\"cell_B\":";emitList(out,bs);out<<",\"cell_defect\":";emitList(out,defects);out<<",\"condensed_offsets\":";emitList(out,offsets);out<<",\"control_sensitivities\":";emitList(out,maps);out<<",\"initial_sensitivities\":";emitList(out,initial_maps);out<<",\"clip_equalities\":"<<equalities<<'}';
  }
  out<<"],\"rejections\":[";int i=0;for(auto r:input["rejection_cases"]){if(i++)out<<',';std::string reason="ACCEPTED";try{auto m=model(r["model"]);auto z=vector(r["initial"]),u=vector(r["control"]);auto t=cell(z,u,periods(r["mesh_s"].as<double>()),m);(void)t;}catch(const std::exception& e){reason=e.what();}out<<"{\"name\":\""<<r["name"].as<std::string>()<<"\",\"rejected\":"<<(reason!="ACCEPTED"?"true":"false")<<",\"reason\":\""<<reason<<"\"}";}out<<"]}\n";
 }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 3;}return 0;
}
