#!/usr/bin/env python3
"""Frozen public coupled prototype review; 19 fixed TRAIN windows, no fitting."""
import base64
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
SOURCE=Path(__file__).resolve();SOURCE_BYTES=SOURCE.read_bytes()
PACKET=Path('results/phase5-public-coupled-v1-early-review')
REMOTE_BODY=r'''
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
import csv,hashlib,itertools,json,sys,xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
import numpy as np
import pinocchio as pin
sys.path.insert(0,str(out/'packet'))
from public_coupled_servo_v1 import PublicServo
from coupled_friction_box_v1 import solve_box
packet=out/'packet';frozen=json.loads((packet/'frozen.json').read_text());constants=json.loads((packet/'public_constants.json').read_text())
root=Path('/home/codextransfer/predictive_motion')
xml=root/'experiments/generated/inspection/inspection_fr3.xml';scene=xml.with_name('scene.xml')
raw=Path('/mnt/d/CodexTransfer/projects/predictive_motion/phase5/raw/servo-identification-v1-training/raw.csv')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
effective={str(p):sha(p) for p in [xml,scene,raw]}
assert all(h==frozen['files'][p] for p,h in effective.items())
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
assert len(rows)==5380 and all(int(r['tick'])==i//2 and int(r['substep'])==i%2+1 for i,r in enumerate(rows))
assert np.array_equal(c[::2],c[1::2]) and np.array_equal(q[1:],qp[:-1]) and np.array_equal(v[1:],vp[:-1])
starts=[100,500,1250,2400,2500];horizons=[1,2,20,400]
declaration={'start_ticks':starts,'substeps':horizons,'selection':'Declared before forecasting; warmup/excitation/cross-stop/stopping. Tick2500 has only380 remaining substeps so its400-step window is unscorable, not truncated.','scorable_windows':19}
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
result={'scope':'Independent selected TRAIN91011 conditional forecasts only; no fitting, physical rollout, new data, model domain acceptance or Phase5 gate','pinocchio_version':pin.__version__,'numpy_version':np.__version__,'frozen_packet_inputs':inputs,'effective_model_raw_hashes':effective,'transitive_mesh_assets':assets,'scene_includes':includes,'joint_mapping':mapping,'declaration':declaration,'windows':reports,'selected_QPs_enumeration':enumerated,'max_coordinate_solver_KKT':max_res,'max_coordinate_solver_iterations':max_iter,'phase_substeps_evaluated':dict(all_phase_counts),'physical_future_state_resets':False,'static_B_matches_only_current_dampratio_one':True}
(out/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
'''

def main():
    expected=json.loads((PACKET/'ROOT_SOURCE_PACKET_VERIFIED.json').read_text())
    assert all(hashlib.sha256((PACKET/name).read_bytes()).hexdigest()==h for name,h in expected.items())
    remote='/home/codextransfer/clean-audits/public-coupled-training-independent-20261007-v1'
    payload=base64.b64encode(json.dumps({p.name:p.read_text() for p in PACKET.iterdir()}).encode()).decode()
    code="import base64,json,pathlib; out=pathlib.Path("+repr(remote)+"); out.mkdir(exist_ok=False); (out/'packet').mkdir(); packet=json.loads(base64.b64decode("+repr(payload)+")); [(out/'packet'/n).write_text(v) for n,v in packet.items()]; (out/'independent.py').write_text("+repr(REMOTE_BODY)+"); exec(compile((out/'independent.py').read_text(),str(out/'independent.py'),'exec'))"
    run=subprocess.run(['tools/dell-ssh.sh','DellTransfer','source /opt/ros/jazzy/setup.bash && python3 -c '+shlex.quote(code)],capture_output=True,text=True,check=True)
    result=json.loads(run.stdout);result['source_sha256']=hashlib.sha256(SOURCE_BYTES).hexdigest();result['unique_remote']=remote
    assert SOURCE.read_bytes()==SOURCE_BYTES and all(hashlib.sha256((PACKET/name).read_bytes()).hexdigest()==h for name,h in expected.items())
    out=Path('results/phase5-reference/root-public-coupled-training-independent-20261007-v1');out.mkdir(exist_ok=False)
    encoded=json.dumps(result,indent=2)+'\n';(out/'audit.json').write_text(encoded);(out/'SOURCE_SNAPSHOT.py').write_bytes(SOURCE_BYTES);(out/'independent_remote.py').write_text(REMOTE_BODY)
    Path('reviews/evidence/public_coupled_training_v1_math_audit_20261007.json').write_text(encoded)
    ready={'source_sha256':result['source_sha256'],'files':{p.name:{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in out.iterdir()}}
    assert SOURCE.read_bytes()==SOURCE_BYTES
    (out/'READY.json').write_text(json.dumps(ready,indent=2)+'\n')
    complete=[x for x in result['windows'] if x['scorable']];success=[x for x in complete if not x['failed']]
    print(json.dumps({'windows':len(complete),'failed':len(complete)-len(success),'max_q_error':max(x['q_error_rad'] for x in success),'max_v_error':max(x['v_error_rad_s'] for x in success),'max_producer_q_difference':max(x['independent_vs_producer_q_rad'] for x in success),'max_producer_v_difference':max(x['independent_vs_producer_v_rad_s'] for x in success),'max_KKT':result['max_coordinate_solver_KKT'],'source_sha256':result['source_sha256']},indent=2))

if __name__=='__main__':main()
