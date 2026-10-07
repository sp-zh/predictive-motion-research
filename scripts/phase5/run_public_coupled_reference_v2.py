#!/usr/bin/env python3
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
import copy,csv,datetime,hashlib,importlib,json,subprocess,sys
from pathlib import Path
import numpy as np
from public_coupled_servo_v1 import PublicServo as V1
from public_coupled_servo_v2 import PublicServo as V2
from coupled_friction_box_v1 import solve_box

p=Path('/home/codextransfer/predictive_motion');old=p/'results/phase5/development/public-coupled-servo-v1-training';base=p/'results/phase5/development/public-coupled-servo-v2-reference-contract';base.mkdir(exist_ok=False);sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest();oldfreeze=json.loads((old/'frozen.json').read_text());assert all(sha(f)==h for f,h in oldfreeze['files'].items())
constants=json.loads((old/'public_constants.json').read_text());xml=p/'experiments/generated/inspection/inspection_fr3.xml';raw=Path('/mnt/d/CodexTransfer/projects/predictive_motion/phase5/raw/servo-identification-v1-training/raw.csv');assert sha(raw)=='ab9d14efa1a5886c0683db25345f24d5cacd55343e2768eb60536fa180a11dce'
assetclosure=json.loads((old/'post_run_transitive_asset_closure.json').read_text());assets=[Path(x['path']) for x in assetclosure['files']];assert all(sha(x['path'])==x['sha256'] for x in assetclosure['files'])
ref=p/'results/phase5/development/public-coupled-servo-v1-reference';protocol={'status':'FROZEN_REFERENCE_CONTRACT_V2_ONLY','changes':'B=2/(dmax*timeconst), no dampratio multiplier; reject timeconst<2*.002 and nonpositive/nonfinite solref; retain exact inspected FR3 solimp profile only','scope':'Fixed seven-coordinate FR3 public baseline, no contact/limit/equality/unknown forces; no generalized robot/model accuracy claim. Synthetic changed reference metadata is formula testing only, never actual plant parameter changes.','unchanged':'M/bias/armature/payload/force-control clipping/R/implicitfast law/rootboxsolver; no fit/derivatives/C++predictor/mainMPC/physicalvalidation','train_start_ticks':[100,500,1250,2400,2500],'horizons_substeps':[1,2,20,400],'incomplete_window_policy':'Retain tick2500/800ms as incomplete, never shorten it','regression_tolerance':5e-12,'source_identity':'Original v1 andold40freeze left byte-identical','synthetic_ratios':[.5,2.],'unsupported_reference_cases':['timeconst0.003','ratio0','negative_timeconst','nonfinite_ratio','different_solimp_profile']}
(base/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');files=[Path(f) for f in oldfreeze['files']]+assets+[Path(__file__),p/'scripts/phase5/public_coupled_servo_v2.py',p/'scripts/phase5/prepare_public_coupled_servo_v2.py',old/'public_constants.json',base/'protocol.json',ref/'oracle.json',ref/'READY.json']
for module in ['numpy','numpy.linalg._umath_linalg','numpy.core._multiarray_umath']:
 file=Path(importlib.import_module(module).__file__);files.append(file)
 if file.suffix=='.so':
  for line in subprocess.check_output(['ldd',str(file)],text=True).splitlines():
   candidate=next((Path(x) for x in line.split() if x.startswith('/') and Path(x).is_file()),None)
   if candidate:files.append(candidate)
freeze={'before_any_v2_model_prediction_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':{str(f):sha(f) for f in files},'XML_transitive_assets_prelisted':len(assets),'NumPy_BLAS_prelisted':True,'scope':protocol['status'],'complete_entire_Python_environment_claim':False};(base/'frozen.json').write_text(json.dumps(freeze,indent=2)+'\n')
v1,v2=V1(xml,constants),V2(xml,constants);assert np.array_equal(v1.B,v2.B)
oracle=json.loads((ref/'oracle.json').read_text());fixtures=[]
for f in oracle['fixtures']:
 force,info=solve_box(oracle['original_H'],f['ell'],oracle['friction_bounds']);error=float(np.max(abs(force-f['force'])));assert error<5e-10;fixtures.append({'name':f['name'],'force_error':error,**info})
synthetic=[]
for ratio in protocol['synthetic_ratios']:
 changed=copy.deepcopy(constants);npref=np.array(changed['solref']).reshape(7,2);npref[:,1]=ratio;changed['solref']=npref.ravel().tolist();model=V2(xml,changed);assert np.array_equal(model.B,v2.B)
 synthetic.append({'ratio':ratio,'B_s_inv':model.B.tolist(),'matches_standard_and_ratio1':True,'scope':'Algebraic coefficient contract only; no physical/model accuracy evaluation'})
rejections=[]
for name in protocol['unsupported_reference_cases']:
 changed=copy.deepcopy(constants)
 if name=='timeconst0.003':changed['solref'][0]=.003
 elif name=='ratio0':changed['solref'][1]=0
 elif name=='negative_timeconst':changed['solref'][0]=-.02
 elif name=='nonfinite_ratio':changed['solref'][1]=float('nan')
 else:changed['solimp'][0]=.8
 try:V2(xml,changed);raise AssertionError('unsupported reference accepted')
 except ValueError as e:rejections.append({'case':name,'rejected':True,'reason':str(e)})
rows=list(csv.DictReader(raw.open()));windows=[];incomplete=[];max_q_error=max_v_error=max_difference=0.
def vector(row,prefix):return np.array([float(row[prefix+str(j)]) for j in range(7)])
for tick in protocol['train_start_ticks']:
 i=2*tick
 for count in protocol['horizons_substeps']:
  if i+count>len(rows):incomplete.append({'start_tick':tick,'duration_s':count*.002,'available_substeps':len(rows)-i,'scope':'Incomplete original trace tail; never shortened/claimed successful'});continue
  q1=vq=vector(rows[i],'q_before_');w1=vv=vector(rows[i],'v_before_');q1=q1.copy();w1=w1.copy()
  for k in range(count):
   target=vector(rows[i+k],'target_');q1,w1,_=v1.step(q1,w1,target);vq,vv,_=v2.step(vq,vv,target)
  difference=float(max(np.max(abs(q1-vq)),np.max(abs(w1-vv))));eq=float(np.max(abs(vq-vector(rows[i+count-1],'q_post_'))));ev=float(np.max(abs(vv-vector(rows[i+count-1],'v_post_'))));max_difference=max(max_difference,difference);max_q_error=max(max_q_error,eq);max_v_error=max(max_v_error,ev);assert difference<=5e-12
  windows.append({'start_tick':tick,'duration_s':count*.002,'start_phase':rows[i]['phase'],'stop_substeps':sum(r['phase']=='stopping' for r in rows[i:i+count]),'v1_v2_max_difference':difference,'q_error_rad':eq,'v_error_rad_s':ev})
assert len(windows)==19 and len(incomplete)==1 and all(sha(f)==h for f,h in freeze['files'].items()) and all(sha(f)==h for f,h in oldfreeze['files'].items())
report={'gate':'PASS_FIXED_FR3_REFERENCE_CONTRACT_V2','scope':protocol['scope'],'no_actual_parameter_or_plant_changes':True,'no_calibration_or_new_validation':True,'original_v1_all40_inputs_unchanged':True,'pre_recorded_input_count':len(freeze['files']),'root_box_fixtures':fixtures,'synthetic_reference_contracts':synthetic,'unsupported_reference_rejections':rejections,'train_windows':windows,'incomplete_retained':incomplete,'max_v1_v2_difference':max_difference,'selected_TRAIN_max_q_error_rad':max_q_error,'selected_TRAIN_max_v_error_rad_s':max_v_error,'full_TRAIN_v2_rescan_claim':False};(base/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['train_windows','root_box_fixtures']},indent=2))
