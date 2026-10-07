#!/usr/bin/env python3
"""Read public model constants and evaluate Pinocchio nominal algebra only.

Never makes mjData, calls mj_forward/mj_step, predicts a plant trajectory,
fits coefficients, or reads a heldout output for model selection.
"""
import base64
import hashlib
import json
from pathlib import Path
import shlex
import subprocess

SOURCE=Path(__file__).resolve()
SOURCE_BYTES=SOURCE.read_bytes()
CPP=r'''#include <mujoco/mujoco.h>
#include <iostream>
#include <iomanip>
void array(const char* name,const mjtNum* x,int n){std::cout<<'"'<<name<<"\":[";for(int i=0;i<n;++i){if(i)std::cout<<',';std::cout<<x[i];}std::cout<<"],";}
int main(int argc,char** argv){if(argc!=2)return 2;char err[2048]{};mjModel* m=mj_loadXML(argv[1],nullptr,err,2048);if(!m){std::cerr<<err;return 3;}
std::cout<<std::setprecision(17)<<"{\"nv\":"<<m->nv<<",\"nu\":"<<m->nu<<",\"integrator\":"<<m->opt.integrator<<",\"solver\":"<<m->opt.solver<<",\"iterations\":"<<m->opt.iterations<<",\"tolerance\":"<<m->opt.tolerance<<",\"disableflags\":"<<m->opt.disableflags<<",\"timestep\":"<<m->opt.timestep<<',';
array("gravity",m->opt.gravity,3);array("body_mass",m->body_mass,m->nbody);array("body_inertia",m->body_inertia,3*m->nbody);array("body_ipos",m->body_ipos,3*m->nbody);array("body_iquat",m->body_iquat,4*m->nbody);array("body_gravcomp",m->body_gravcomp,m->nbody);array("armature",m->dof_armature,m->nv);array("invweight0",m->dof_invweight0,m->nv);array("damping",m->dof_damping,m->nv);array("frictionloss",m->dof_frictionloss,m->nv);array("solref",m->dof_solref,m->nv*mjNREF);array("solimp",m->dof_solimp,m->nv*mjNIMP);array("actuator_gainprm",m->actuator_gainprm,m->nu*mjNGAIN);array("actuator_biasprm",m->actuator_biasprm,m->nu*mjNBIAS);array("actuator_gear",m->actuator_gear,m->nu*6);array("actuator_ctrlrange",m->actuator_ctrlrange,m->nu*2);array("joint_actuatorfrcrange",m->jnt_actfrcrange,m->njnt*2);std::cout<<"\"version\":\""<<mj_versionString()<<"\"}";mj_deleteModel(m);}
'''
REMOTE=r'''
import hashlib,json,pathlib,subprocess
import numpy as np
import pinocchio as p
root=pathlib.Path('/home/codextransfer/predictive_motion')
scene=root/'experiments/generated/inspection/scene.xml'
robot=root/'experiments/generated/inspection/inspection_fr3.xml'
vendor=root/'.vendor/menagerie/franka_fr3/fr3.xml'
urdf=root/'models/fr3/fr3_arm.urdf'
cpp_params=json.loads(subprocess.check_output([str(out/'static_reader'),str(scene)],text=True))
q=np.array([0.,0.,0.,-1.57079,0.,1.57079,-.7853])
v=np.array([.01,-.008,.006,-.004,.003,-.002,.001])
models={}
for name,path in [('inspection_mjcf',robot),('vendor_mjcf',vendor),('arm_urdf',urdf)]:
 m=p.buildModelFromUrdf(str(path)) if name=='arm_urdf' else p.buildModelFromMJCF(str(path))
 d=m.createData();upper=np.array(p.crba(m,d,q));M=np.triu(upper)+np.triu(upper,1).T
 g=np.array(p.computeGeneralizedGravity(m,d,q)).copy();bias=np.array(p.nonLinearEffects(m,d,q,v)).copy()
 models[name]={'nq':m.nq,'nv':m.nv,'names':list(m.names),'masses':[x.mass for x in m.inertias],'armature':m.armature.tolist(),'damping':m.damping.tolist(),'friction':m.friction.tolist(),'M':M.tolist(),'gravity':g.tolist(),'bias':bias.tolist(),'coriolis':(bias-g).tolist(),'M_eigenvalues':np.linalg.eigvalsh(M).tolist(),'max_offdiagonal_M':float(np.max(np.abs(M-np.diag(np.diag(M))))) }
M=np.array(models['inspection_mjcf']['M']);W=np.linalg.inv(M);dimp=np.array(cpp_params['solimp']).reshape(7,5)[:,0];R=(1-dimp)/dimp*np.array(cpp_params['invweight0']);H=W+np.diag(R)
result={'scope':'Public static model and single nominal Pinocchio M/g/bias evaluation only; no model validity or plant prediction claim','pinocchio_version':p.__version__,'pinocchio_MJCF_available':hasattr(p,'buildModelFromMJCF'),'q_nominal':q.tolist(),'v_nominal':v.tolist(),'compiled_mjModel':cpp_params,'pinocchio_models':models,'inspection_minus_arm_max_abs_M':float(np.max(np.abs(M-np.array(models['arm_urdf']['M'])))),'inspection_minus_vendor_max_abs_M':float(np.max(np.abs(M-np.array(models['vendor_mjcf']['M'])))),'friction_QP_H_eigenvalues':np.linalg.eigvalsh(H).tolist(),'inverse_mass_max_offdiagonal':float(np.max(np.abs(W-np.diag(np.diag(W))))),'regularizer_R':R.tolist(),'inputs':{str(x):{'sha256':hashlib.sha256(x.read_bytes()).hexdigest(),'bytes':x.stat().st_size} for x in [scene,robot,vendor,urdf,root/'experiments/generated/phase4/robot.yaml',pathlib.Path('/opt/ros/jazzy/include/pinocchio/src/algorithm/crba.hxx')]}}
(out/'model_algebra.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
'''

def main():
 out=Path('results/phase5-reference/root-public-coupled-servo-design-20261007-v1');out.mkdir(exist_ok=False)
 remote='/home/codextransfer/clean-audits/public-coupled-servo-design-20261007-v1'
 encoded=base64.b64encode(json.dumps({'cpp':CPP,'python':REMOTE}).encode()).decode()
 setup="import pathlib,base64,json,subprocess; out=pathlib.Path("+repr(remote)+"); out.mkdir(exist_ok=False); doc=json.loads(base64.b64decode("+repr(encoded)+")); (out/'static_reader.cpp').write_text(doc['cpp']); (out/'model_algebra.py').write_text('out=__import__(\"pathlib\").Path('+repr(str(out))+')\\n'+doc['python']); vendor='/home/codextransfer/predictive_motion/.vendor/mujoco-3.3.7'; subprocess.run(['c++','-O2','-std=c++17','-I'+vendor+'/include',str(out/'static_reader.cpp'),vendor+'/lib/libmujoco.so.3.3.7','-Wl,-rpath,'+vendor+'/lib','-o',str(out/'static_reader')],check=True); exec(compile((out/'model_algebra.py').read_text(),str(out/'model_algebra.py'),'exec'))"
 proc=subprocess.run(['tools/dell-ssh.sh','DellTransfer','source /opt/ros/jazzy/setup.bash && python3 -c '+shlex.quote(setup)],capture_output=True,text=True,check=True)
 result=json.loads(proc.stdout);result['audit_source_sha256']=hashlib.sha256(SOURCE_BYTES).hexdigest();result['remote_clean_audit']=remote
 assert SOURCE.read_bytes()==SOURCE_BYTES
 (out/'model_algebra.json').write_text(json.dumps(result,indent=2)+'\n');(out/'static_reader.cpp').write_text(CPP);(out/'model_algebra.py').write_text(REMOTE);(out/'SOURCE_SNAPSHOT.py').write_bytes(SOURCE_BYTES)
 print(json.dumps({k:result[k] for k in ['pinocchio_version','inspection_minus_arm_max_abs_M','inspection_minus_vendor_max_abs_M','friction_QP_H_eigenvalues','inverse_mass_max_offdiagonal','regularizer_R']},indent=2))

if __name__=='__main__':main()
