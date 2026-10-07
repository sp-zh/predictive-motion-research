#!/usr/bin/env python3
"""Independent selected91013 forecasts; no future plant state or fitting.

Run in a unique Dell root-audit directory. Snapshot frozen public inputs and
use a separate cyclic-coordinate solver with enumerated single-step force QPs.
"""
import argparse,hashlib,json,shutil
from pathlib import Path

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--output',type=Path,required=True)
 parser.add_argument('--declaration',type=Path,required=True)
 parser.add_argument('--expected-raw-sha256',required=True)
 args=parser.parse_args();out=args.output;out.mkdir(parents=True,exist_ok=False);packet=out/'packet';packet.mkdir()
 root=Path('/home/codextransfer/predictive_motion');base=root/'results/phase5/development/public-coupled-validation-91013-protocol-v2'
 sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 assert sha(base/'frozen.json')=='190b05049892a27923778475e8287a7814854455d1fa55d722d14094245b814d'
 freeze=json.loads((base/'frozen.json').read_text());protocol=json.loads((base/'protocol.json').read_text())
 assert sha(base/'protocol.json')=='0325135b001c9f54b1747993eb6af6364e5c05deb3ee9b37f81b434e253a5739'
 inputs={}
 for name,source in [('public_coupled_servo_v2.py',Path(protocol['public_model_source'])),('coupled_friction_box_v1.py',root/'scripts/phase5/coupled_friction_box_v1.py'),('public_constants.json',Path(protocol['public_model_constants']))]:
  assert sha(source)==freeze['files'][str(source)];shutil.copyfile(source,packet/name);inputs[name]=sha(packet/name)
 shutil.copyfile(base/'frozen.json',packet/'frozen.json');inputs['frozen.json']=sha(packet/'frozen.json')
 shutil.copyfile(args.declaration,packet/'PREDECLARED_WINDOWS.json');inputs['PREDECLARED_WINDOWS.json']=sha(packet/'PREDECLARED_WINDOWS.json')
 (packet/'ROOT_SOURCE_PACKET_VERIFIED.json').write_text(json.dumps(inputs,indent=2)+'\n')
 source=Path(__file__);source_bytes=source.read_bytes();(out/'SOURCE_SNAPSHOT.py').write_bytes(source_bytes)
 exec(compile(REMOTE_BODY,str(out/'independent_remote.py'),'exec'),dict(out=out,args=args,REMOTE_BODY=REMOTE_BODY))
 assert source.read_bytes()==source_bytes
 result=json.loads((out/'audit.json').read_text());result['source_sha256']=hashlib.sha256(source_bytes).hexdigest();result['future_accepted_targets_are_conditional_inputs']=True
 (out/'audit.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
 (out/'independent_remote.py').write_text(REMOTE_BODY)
 files={str(p.relative_to(out)):{'sha256':sha(p),'bytes':p.stat().st_size} for p in out.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
 (out/'READY.json').write_text(json.dumps({'scope':result['scope'],'files':files},indent=2)+'\n')
 complete=[x for x in result['windows'] if x['scorable']];success=[x for x in complete if not x['failed']]
 print(json.dumps({'scorable':len(complete),'failed':len(complete)-len(success),'max_q_error_rad':max([x['q_error_rad'] for x in success],default=None),'max_v_error_rad_s':max([x['v_error_rad_s'] for x in success],default=None),'source_sha256':result['source_sha256']},indent=2))

REMOTE_BODY=r'''

import os
os.environ['OPENBLAS_NUM_THREADS']='1'
import csv,hashlib,itertools,json,sys,xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
import numpy as np
import pinocchio as pin
sys.path.insert(0,str(out/'packet'))
from public_coupled_servo_v2 import PublicServo
from coupled_friction_box_v1 import solve_box
packet=out/'packet';frozen=json.loads((packet/'frozen.json').read_text());constants=json.loads((packet/'public_constants.json').read_text())
root=Path('/home/codextransfer/predictive_motion')
xml=root/'experiments/generated/inspection/inspection_fr3.xml';scene=xml.with_name('scene.xml')
raw=Path('/mnt/d/CodexTransfer/projects/predictive_motion/phase5/raw/public-coupled-v2-development-validation-91013/raw.csv')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
effective={str(p):sha(p) for p in [xml,scene,raw]}
assert effective[str(raw)]==args.expected_raw_sha256
assert all(h==frozen['files'][p] for p,h in effective.items() if p!=str(raw))
xml_bytes=xml.read_bytes();(out/'MODEL_XML_SNAPSHOT.xml').write_bytes(xml_bytes)
inputs=json.loads((packet/'ROOT_SOURCE_PACKET_VERIFIED.json').read_text())
assert all(sha(packet/name)==h for name,h in inputs.items())
files=ET.fromstring(xml_bytes);meshdir=Path(files.find('compiler').attrib['meshdir'])
assets=[]
for mesh in files.findall('./asset/mesh'):
 name=mesh.attrib['file'];path=Path(name) if Path(name).is_absolute() else meshdir/name
 assets.append({'path':str(path),'bytes':path.stat().st_size,'sha256':sha(path),'in_producer_frozen_manifest':str(path) in frozen['files']})
includes=[str(scene.parent/e.attrib['file']) for e in ET.parse(scene).findall('include')]
producer=PublicServo(out/'MODEL_XML_SNAPSHOT.xml',constants)
model=pin.buildModelFromMJCF(str(out/'MODEL_XML_SNAPSHOT.xml'));model.gravity.linear=np.array(constants['gravity']);work=model.createData()
assert np.array_equal(model.armature,constants['armature'])
mapping=[{'name':model.names[i+1],'q_index':model.joints[i+1].idx_q,'v_index':model.joints[i+1].idx_v} for i in range(7)]
assert all(x['name']==constants['joint_names'][i] and x['q_index']==x['v_index']==i for i,x in enumerate(mapping))
eta=np.array(constants['friction_bounds']);imp=np.array(constants['solimp']).reshape(7,5);ref=np.array(constants['solref']).reshape(7,2)
R=np.maximum(constants['minimum_value'],(1-imp[:,0])/imp[:,0]*np.array(constants['invweight0']));B=2/(imp[:,1]*ref[:,0])
assert np.array_equal(ref[:,1],np.ones(7)) and np.max(abs(B-producer.B))==0
gain=np.array(constants['gainprm']).reshape(7,10)[:,0];bias=np.array(constants['biasprm']).reshape(7,10);passive=np.array(constants['passive_damping']);D=passive-bias[:,2]
def residual(H,ell,x):
 gradient=H@x+ell
 label=np.where(x<=-eta+1e-13,-1,np.where(x>=eta-1e-13,1,0))
 violation=np.where(label==0,abs(gradient),np.where(label<0,np.maximum(-gradient,0),np.maximum(gradient,0)))
 return float(max(np.max(violation),np.max(abs(x)-eta),0))
def coordinate_box(H,ell):
 # Independent cyclic exact coordinate minimization; no producer active-face logic.
 x=np.zeros(7)
 for iteration in range(1,20001):
  for j in range(7):
   rest=H[j]@x-H[j,j]*x[j];x[j]=np.clip(-(ell[j]+rest)/H[j,j],-eta[j],eta[j])
  error=residual(H,ell,x)
  if error<=1e-12:return x,iteration,error
 raise ArithmeticError('independent coordinate solver did not converge')
def enumerated_box(H,ell):
 candidates=[]
 for state in itertools.product((-1,0,1),repeat=7):
  state=np.array(state);free=np.flatnonzero(state==0);bound=np.flatnonzero(state!=0);x=state*eta
  if free.size:x[free]=np.linalg.solve(H[np.ix_(free,free)],-ell[free]-H[np.ix_(free,bound)]@x[bound])
  g=H@x+ell
  error=max(np.max(abs(x)-eta),np.max(np.where(state==0,abs(g),np.where(state<0,-g,g))),0)
  if error<=1e-10:candidates.append((float(.5*x@H@x+ell@x),x.copy()))
 assert candidates
 return min(candidates,key=lambda item:item[0])[1]
def step(q,v,c):
 c=c.copy();lims=np.array(constants['control_range']).reshape(7,2);flag=np.array(constants['control_limited'],bool);c[flag]=np.clip(c[flag],lims[flag,0],lims[flag,1])
 act=gain*c+bias[:,0]+bias[:,1]*q+bias[:,2]*v
 for r,f in [('actuator_force_range','actuator_force_limited'),('joint_actuator_force_range','joint_actuator_force_limited')]:
  lims=np.array(constants[r]).reshape(7,2);flag=np.array(constants[f],bool);act[flag]=np.clip(act[flag],lims[flag,0],lims[flag,1])
 upper=np.triu(np.array(pin.crba(model,work,q)));M=upper+np.triu(upper,1).T
 rigid=np.array(pin.nonLinearEffects(model,work,q,v)).copy();tau=act-passive*v-rigid
 W=np.linalg.solve(M,np.eye(7));H=W+np.diag(R);ell=W@tau+B*v
 f,nit,res=coordinate_box(H,ell)
 vp=v+.002*np.linalg.solve(M+.002*np.diag(D),tau+f);qp=q+.002*vp
 assert np.isfinite(qp).all() and np.isfinite(vp).all()
 limits=np.array(constants['joint_range']).reshape(7,2);assert np.all(qp>limits[:,0]) and np.all(qp<limits[:,1])
 return qp,vp,(H,ell,f,nit,res)
rows=list(csv.DictReader(raw.open()))
def values(prefix):return np.array([[float(r[prefix+str(j)]) for j in range(7)] for r in rows])
q,v,c,qp,vp=[values(x) for x in ['q_before_','v_before_','target_','q_post_','v_post_']]
assert len(rows)>=1000 and len(rows)%2==0 and all(int(r['tick'])==i//2 and int(r['substep'])==i%2+1 for i,r in enumerate(rows))
assert np.array_equal(c[::2],c[1::2]) and np.array_equal(q[1:],qp[:-1]) and np.array_equal(v[1:],vp[:-1])
declaration=json.loads((packet/'PREDECLARED_WINDOWS.json').read_text());starts=declaration['start_ticks'];horizons=declaration['substeps']
(out/'PREDECLARED_WINDOWS.json').write_text(json.dumps(declaration,indent=2)+'\n')
reports=[];enumerated=[];max_res=max_iter=0;all_phase_counts=Counter()
for tick in starts:
 i=2*tick
 for count in horizons:
  if i+count>len(rows):reports.append({'start_tick':tick,'substeps':count,'scorable':False,'reason':'Incomplete trailing window; retained, no truncation'});continue
  ownq,ownv=q[i].copy(),v[i].copy();pq,pv=ownq.copy(),ownv.copy();counted=Counter()
  try:
   assert not any(int(r['contacts']) for r in rows[i:i+count])
   for k in range(count):
    ownq,ownv,info=step(ownq,ownv,c[i+k]);H,ell,f,nit,res=info;max_res=max(max_res,res);max_iter=max(max_iter,nit)
    pq,pv,_=producer.step(pq,pv,c[i+k]);counted.update([rows[i+k]['phase']])
    if count==1:
     exact=enumerated_box(H,ell);pforce,pinfo=solve_box(H,ell,eta);err=float(np.max(abs(f-exact)));perr=float(np.max(abs(pforce-exact)))
     assert err<1e-10 and perr<1e-10
     enumerated.append({'tick':tick,'substep':1,'H':H.tolist(),'ell':ell.tolist(),'force_independent':f.tolist(),'force_enumerated':exact.tolist(),'force_producer':pforce.tolist(),'independent_force_error':err,'producer_force_error':perr,'original_KKT_independent':res,'original_KKT_producer':pinfo['original_KKT'],'H_eigenvalues':np.linalg.eigvalsh(.5*(H+H.T)).tolist()})
   reports.append({'start_tick':tick,'substeps':count,'duration_s':count*.002,'scorable':True,'start_phase':rows[i]['phase'],'window_phase_substeps':dict(counted),'q_error_rad':float(np.max(abs(ownq-qp[i+count-1]))),'v_error_rad_s':float(np.max(abs(ownv-vp[i+count-1]))),'independent_vs_producer_q_rad':float(np.max(abs(ownq-pq))),'independent_vs_producer_v_rad_s':float(np.max(abs(ownv-pv))),'failed':False});all_phase_counts.update(counted)
  except Exception as e:reports.append({'start_tick':tick,'substeps':count,'scorable':True,'failed':True,'reason':type(e).__name__+': '+str(e)})
assert all(sha(Path(p))==h for p,h in effective.items())
assert all(sha(packet/name)==h for name,h in inputs.items())
result={'scope':'Independent predeclared selected seed91013 conditional forecasts; cyclic-coordinate force solver and enumerated single-step QPs. No fitting, physical rollout, full-window numerical reproduction, model-domain acceptance or Phase5 gate','pinocchio_version':pin.__version__,'numpy_version':np.__version__,'frozen_packet_inputs':inputs,'effective_model_raw_hashes':effective,'transitive_mesh_assets':assets,'scene_includes':includes,'joint_mapping':mapping,'declaration':declaration,'windows':reports,'selected_QPs_enumeration':enumerated,'max_coordinate_solver_KKT':max_res,'max_coordinate_solver_iterations':max_iter,'phase_substeps_evaluated':dict(all_phase_counts),'physical_future_state_resets':False,'static_B_contract':'Standard positive-solref B=2/(dmax*timeconst); actual frozen ratios1' }
(out/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

'''

if __name__=="__main__":main()
