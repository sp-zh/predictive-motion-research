#!/usr/bin/env python3
"""Small frozen v2 reference-contract regression; no full TRAIN scan or fitting."""
import base64
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
SOURCE=Path(__file__).resolve();SOURCE_BYTES=SOURCE.read_bytes()
V1=Path('results/phase5-public-coupled-v1-early-review')
V2=Path('results/phase5-public-coupled-v2-early-review')
BODY=r'''
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
import copy,csv,hashlib,json,sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(out/'packet'))
from public_coupled_servo_v1 import PublicServo as Servo1
from public_coupled_servo_v2 import PublicServo as Servo2
from coupled_friction_box_v1 import solve_box
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
packet=out/'packet';frozen=json.loads((packet/'frozen_v2.json').read_text());expected=frozen['files']
assert len(expected)==88
identity={name:sha(Path(name)) for name in expected}
assert identity==expected
constants=json.loads((packet/'public_constants.json').read_text());xml=Path('/home/codextransfer/predictive_motion/experiments/generated/inspection/inspection_fr3.xml')
xml_bytes=xml.read_bytes();(out/'MODEL_XML_SNAPSHOT.xml').write_bytes(xml_bytes);xml=out/'MODEL_XML_SNAPSHOT.xml'
original=Servo1(xml,constants);model=Servo2(xml,constants)
assert np.array_equal(original.R,model.R) and np.array_equal(original.B,model.B) and np.array_equal(original.D,model.D)
oracle=json.loads((packet/'root_oracle.json').read_text());fixtures=[]
for c in oracle['fixtures']:
 f,info=solve_box(oracle['original_H'],c['ell'],oracle['friction_bounds'])
 error=float(np.max(abs(f-np.array(c['force']))));assert error<5e-10 and info['original_KKT']<=1e-10
 fixtures.append({'name':c['name'],'force_error':error,'original_KKT':info['original_KKT'],'branches':info['branches']})
assert len(fixtures)==7
ratios=[]
for ratio in (.5,2.):
 c=copy.deepcopy(constants);ref=np.array(c['solref']).reshape(7,2);ref[:,1]=ratio;c['solref']=ref.ravel().tolist();m=Servo2(xml,c)
 standard=2/(np.array(c['solimp']).reshape(7,5)[:,1]*ref[:,0]);assert np.array_equal(m.B,standard) and np.array_equal(m.B,model.B)
 ratios.append({'ratio':ratio,'B_s_inv':m.B.tolist(),'standard_formula_max_error':float(np.max(abs(m.B-standard)))})
negative=[]
for name in ('timeconst0.003','ratio0','negative_timeconst','nonfinite_ratio','different_solimp_profile'):
 c=copy.deepcopy(constants);ref=np.array(c['solref']).reshape(7,2)
 if name=='timeconst0.003':ref[:,0]=.003
 elif name=='ratio0':ref[:,1]=0
 elif name=='negative_timeconst':ref[:,0]=-.02
 elif name=='nonfinite_ratio':ref[:,1]=np.nan
 else:c['solimp'][0]=.89
 c['solref']=ref.ravel().tolist();reason='ACCEPTED'
 try:Servo2(xml,c)
 except ValueError as e:reason=str(e)
 assert reason!='ACCEPTED';negative.append({'name':name,'rejected':True,'reason':reason})
raw=Path('/mnt/d/CodexTransfer/projects/predictive_motion/phase5/raw/servo-identification-v1-training/raw.csv');rows=list(csv.DictReader(raw.open()))
def vals(prefix):return np.array([[float(r[prefix+str(j)]) for j in range(7)] for r in rows])
q,v,c,postq,postv=[vals(k) for k in ['q_before_','v_before_','target_','q_post_','v_post_']]
windows=[]
for tick in (100,500,1250,2400,2500):
 i=2*tick
 for count in (1,2,20,400):
  if i+count>len(rows):windows.append({'start_tick':tick,'substeps':count,'scorable':False,'available_substeps':len(rows)-i});continue
  a,b=q[i].copy(),v[i].copy();x,y=a.copy(),b.copy();stopping=0
  for k in range(count):
   a,b,_=original.step(a,b,c[i+k]);x,y,_=model.step(x,y,c[i+k]);stopping+=rows[i+k]['phase']=='stopping'
  diff=max(float(np.max(abs(a-x))),float(np.max(abs(b-y))));assert diff==0
  windows.append({'start_tick':tick,'substeps':count,'scorable':True,'start_phase':rows[i]['phase'],'stopping_substeps':stopping,'v1_v2_q_difference':float(np.max(abs(a-x))),'v1_v2_v_difference':float(np.max(abs(b-y))),'q_error_rad':float(np.max(abs(x-postq[i+count-1]))),'v_error_rad_s':float(np.max(abs(y-postv[i+count-1])))})
assert sum(w['scorable'] for w in windows)==19
assert all(sha(Path(name))==h for name,h in identity.items())
prior=json.loads((packet/'frozen_v1.json').read_text())['files'];assert all(name in expected and expected[name]==h for name,h in prior.items())
result={'status':'PASS_FIXED_FR3_REFERENCE_CONTRACT_V2_INDEPENDENT','prelisted_input_count':88,'input_hashes_unchanged':True,'checked_input_hashes':identity,'original_v1_freeze_unchanged':True,'root_oracle_sha256':sha(packet/'root_oracle.json'),'root_box_fixtures':fixtures,'synthetic_ratios':ratios,'negative_parameter_cases':negative,'selected_training_windows':windows,'physical_future_state_resets':False,'new_fits_or_plant':False,'limits':['Reference coefficient/rejection and selected old TRAIN compatibility only','Seven-coordinate FR3 prototype, not robot-agnostic library or whole Python environment freeze','Synthetic ratio changes are coefficient tests; no parameter-generalized prediction accuracy','No new holdout, accuracy/domain expansion, main MPC, stopping certificate or Phase5 acceptance']}
(out/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
'''

def main():
    assert hashlib.sha256((V2/'public_coupled_servo_v2.py').read_bytes()).hexdigest()=='89a0ce2122aaa709afe3195d1cca269debca3e70710462cbdbeea37bd48e480a'
    v1names=['public_coupled_servo_v1.py','coupled_friction_box_v1.py','public_constants.json']
    files={n:(V1/n).read_text() for n in v1names};files['frozen_v1.json']=(V1/'frozen.json').read_text();files['frozen_v2.json']=(V2/'frozen.json').read_text();files['public_coupled_servo_v2.py']=(V2/'public_coupled_servo_v2.py').read_text();files['root_oracle.json']=Path('reviews/evidence/coupled_friction_box_root_oracle_20261007.json').read_text()
    packet_bytes=json.dumps(files).encode();remote='/home/codextransfer/clean-audits/public-coupled-reference-v2-independent-20261007-v1'
    payload=base64.b64encode(packet_bytes).decode();setup="import pathlib,base64,json; out=pathlib.Path("+repr(remote)+"); out.mkdir(exist_ok=False); (out/'packet').mkdir(); files=json.loads(base64.b64decode("+repr(payload)+")); [(out/'packet'/n).write_text(v) for n,v in files.items()]; (out/'independent.py').write_text("+repr(BODY)+"); exec(compile((out/'independent.py').read_text(),str(out/'independent.py'),'exec'))"
    run=subprocess.run(['tools/dell-ssh.sh','DellTransfer','source /opt/ros/jazzy/setup.bash && python3 -c '+shlex.quote(setup)],capture_output=True,text=True,check=True)
    result=json.loads(run.stdout);result['source_sha256']=hashlib.sha256(SOURCE_BYTES).hexdigest();result['remote_clean_audit']=remote
    assert SOURCE.read_bytes()==SOURCE_BYTES
    out=Path('results/phase5-reference/root-public-coupled-reference-v2-independent-20261007-v1');out.mkdir(exist_ok=False)
    text=json.dumps(result,indent=2)+'\n';(out/'audit.json').write_text(text);(out/'SOURCE_SNAPSHOT.py').write_bytes(SOURCE_BYTES);(out/'PACKET_SNAPSHOT.json').write_bytes(packet_bytes)
    Path('reviews/evidence/public_coupled_v2_reference_root_review_20261007.json').write_text(text)
    ready={'source_sha256':result['source_sha256'],'files':{p.name:{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in out.iterdir()}}
    assert SOURCE.read_bytes()==SOURCE_BYTES
    (out/'READY.json').write_text(json.dumps(ready,indent=2)+'\n')
    valid=[w for w in result['selected_training_windows'] if w['scorable']]
    print(json.dumps({'status':result['status'],'inputs':88,'fixtures':7,'windows':len(valid),'v1_v2_max_difference':max(max(w['v1_v2_q_difference'],w['v1_v2_v_difference']) for w in valid),'max_q_error_rad':max(w['q_error_rad'] for w in valid),'max_v_error_rad_s':max(w['v_error_rad_s'] for w in valid),'source_sha256':result['source_sha256']},indent=2))

if __name__=='__main__':main()
