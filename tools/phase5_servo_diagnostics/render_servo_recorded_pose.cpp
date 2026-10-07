#include <GL/osmesa.h>
#include <mujoco/mujoco.h>
#include <yaml-cpp/yaml.h>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <map>
#include <memory>
#include <sstream>
#include <vector>
std::vector<std::string> split(const std::string& line){std::stringstream stream(line);std::string cell;std::vector<std::string> out;while(std::getline(stream,cell,','))out.push_back(cell);return out;}
int main(int argc,char** argv){
 if(argc!=4){std::cerr<<"root recorded_csv fresh_output_ppm\n";return 2;}
 try{
  std::filesystem::path root=argv[1],raw=argv[2],out=argv[3];if(std::filesystem::exists(out))throw std::runtime_error("refuse render overwrite");
  if(std::string(mj_versionString())!="3.3.7")throw std::runtime_error("MuJoCo render version mismatch");
  std::ifstream file(raw);std::string line;std::getline(file,line);auto header=split(line);std::map<std::string,int> cols;for(int j=0;j<int(header.size());++j)cols[header[j]]=j;std::vector<std::string> last;while(std::getline(file,line))if(!line.empty())last=split(line);
  auto names=YAML::LoadFile((root/"experiments/generated/phase4/robot.yaml").string())["joint_names"].as<std::vector<std::string>>();
  char error[2048]={};std::unique_ptr<mjModel,decltype(&mj_deleteModel)> model(mj_loadXML((root/"experiments/generated/inspection/scene.xml").c_str(),nullptr,error,sizeof(error)),mj_deleteModel);if(!model)throw std::runtime_error(error);
  std::unique_ptr<mjData,decltype(&mj_deleteData)> data(mj_makeData(model.get()),mj_deleteData);
  for(int j=0;j<int(names.size());++j){int joint=mj_name2id(model.get(),mjOBJ_JOINT,names[j].c_str());data->qpos[model->jnt_qposadr[joint]]=std::stod(last.at(cols.at("q_post_"+std::to_string(j))));data->qvel[model->jnt_dofadr[joint]]=std::stod(last.at(cols.at("v_post_"+std::to_string(j))));for(int a=0;a<model->nu;++a)if(model->actuator_trntype[a]==mjTRN_JOINT&&model->actuator_trnid[2*a]==joint)data->ctrl[a]=std::stod(last.at(cols.at("target_"+std::to_string(j))));}
  data->time=std::stod(last.at(cols.at("time_s")));mj_forward(model.get(),data.get());
  const int width=1280,height=720;OSMesaContext os=OSMesaCreateContextExt(OSMESA_RGBA,24,8,0,nullptr);if(!os)throw std::runtime_error("OSMesa context unavailable");std::vector<unsigned char> buffer(width*height*4);if(!OSMesaMakeCurrent(os,buffer.data(),GL_UNSIGNED_BYTE,width,height))throw std::runtime_error("OSMesa bind failed");
  model->vis.global.offwidth=width;model->vis.global.offheight=height;
  mjvCamera camera;mjv_defaultCamera(&camera);camera.lookat[0]=.49;camera.lookat[1]=-.01;camera.lookat[2]=.49;camera.distance=1.5;camera.azimuth=135;camera.elevation=-23;
  mjvOption option;mjv_defaultOption(&option);mjvScene scene;mjv_defaultScene(&scene);mjv_makeScene(model.get(),&scene,10000);mjrContext context;mjr_defaultContext(&context);mjr_makeContext(model.get(),&context,mjFONTSCALE_150);mjr_setBuffer(mjFB_OFFSCREEN,&context);
  mjv_updateScene(model.get(),data.get(),&option,nullptr,&camera,mjCAT_ALL,&scene);mjrRect viewport{0,0,width,height};mjr_render(viewport,&scene,&context);
  std::vector<unsigned char> rgb(width*height*3);mjr_readPixels(rgb.data(),nullptr,viewport,&context);
  std::ofstream image(out,std::ios::binary);image<<"P6\n"<<width<<' '<<height<<"\n255\n";for(int row=height-1;row>=0;--row)image.write(reinterpret_cast<const char*>(rgb.data()+row*width*3),width*3);
  image.close();mjr_freeContext(&context);mjv_freeScene(&scene);OSMesaDestroyContext(os);
  std::cout<<"Recorded q/v/target pose rendered at time "<<data->time<<"; forward geometry only; no physics/control stepping\n";return 0;
 }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
