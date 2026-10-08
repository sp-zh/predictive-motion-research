#!/usr/bin/env python3
"""Independent native caller for corrected C++ v2 transition and force-box API.

Existing development inputs and mathematical fixtures only. No new plant,
parameter fitting, main-controller or derivative validation. Tiny-bound analytic optima and exact-side labels are checked independently.
"""
import argparse,csv,hashlib,json,os,subprocess,sys
from pathlib import Path
import numpy as np
SHA=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

BINARY='fa1a00344e73d8fe2266541ba4e2b34c362351b30a4f21dfa34c04867f585a04'

def dump(p,d):p.write_text(json.dumps(d,indent=2,allow_nan=False)+'\n')
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--oracle',type=Path,required=True);ap.add_argument('--freeze',type=Path,required=True);ap.add_argument('--freeze-sha256',required=True);a=ap.parse_args();out=a.output;out.mkdir(parents=True,exist_ok=False)
 root=Path('/home/codextransfer/predictive_motion');binary=root/'build-public-coupled-cpp-v2/public_coupled_probe_v2';frozen=a.freeze;xml=root/'experiments/generated/inspection/inspection_fr3.xml';constants=root/'results/phase5/development/public-coupled-servo-v1-training/public_constants.json';raw=Path('/mnt/d/CodexTransfer/projects/predictive_motion/phase5/raw/public-coupled-v2-development-validation-91013/raw.csv')
 source=Path(__file__);source_bytes=source.read_bytes();assert SHA(frozen)==a.freeze_sha256 and SHA(binary)==BINARY and SHA(raw)=='ea70d9e8b01bc6e44387e2f4701779243bb1b202020a61aef18312fac1c054e8'
 entries={x['path']:x for x in json.loads(frozen.read_text())['files']}
 inputs=[binary,xml,constants,raw,root/'scripts/phase5/public_coupled_servo_v2.py',root/'scripts/phase5/coupled_friction_box_v1.py']
 inputs += sorted((root/'tools/phase5_public_coupled_cpp_v2').glob('*'))
 for p in inputs:assert SHA(p)==entries[str(p)]['sha256'],p
 sys.path.insert(0,str(root/'scripts/phase5'));from public_coupled_servo_v2 import PublicServo
 model=PublicServo(xml,json.loads(constants.read_text()));oracle=json.loads(a.oracle.read_text())
 with raw.open() as f:rows=list(csv.DictReader(f))
 vector=lambda r,p:[float(r[p+str(j)]) for j in range(7)]
 state=[]
 for tick,count in [(510,1),(710,2),(690,20),(920,400)]:
  i=2*tick;state.append({'name':f'recorded_{tick}_{count}','q':vector(rows[i],'q_before_'),'v':vector(rows[i],'v_before_'),'targets':[vector(r,'target_') for r in rows[i:i+count]],'expected_success':True})
 baseline={'q':vector(rows[1000],'q_before_'),'v':vector(rows[1000],'v_before_'),'targets':[vector(rows[1000],'target_')]}
 state.append(dict(baseline,name='finite_huge_target_clamps',targets=[[1e308]*7],expected_success=True))
 state.append(dict(baseline,name='finite_velocity_overflow',v=[1e308]*7,expected_success=False))
 state.append(dict(baseline,name='q_dimension6',q=baseline['q'][:6],expected_success=False))
 state.append(dict(baseline,name='target_dimension6',targets=[baseline['targets'][0][:6]],expected_success=False))
 state.append(dict(baseline,name='nonfinite_target',targets=[['.nan']+baseline['targets'][0][1:]],expected_success=False))
 c=json.loads(constants.read_text());badq=baseline['q'].copy();badq[0]=c['joint_range'][0];state.append(dict(baseline,name='joint_boundary',q=badq,expected_success=False))
 boxes=[{'name':'oracle_'+f['name'],'H':oracle['original_H'],'ell':f['ell'],'eta':oracle['friction_bounds'],'expected_success':True,'expected_force':f['force']} for f in oracle['fixtures']]
 boxes += [{'name':'zero_bound','H':[[1.]],'ell':[1.],'eta':[0.],'expected_success':True,'expected_force':[0.]},{'name':'tiny_lower','H':[[1.]],'ell':[1.],'eta':[1e-12],'expected_success':True,'expected_force':[-1e-12]},{'name':'negative_eta','H':[[1.]],'ell':[0.],'eta':[-1.],'expected_success':False},{'name':'nonSPD','H':[[-1.]],'ell':[0.],'eta':[1.],'expected_success':False},{'name':'asymmetry','H':[[1.,2.],[0.,1.]],'ell':[0.,0.],'eta':[1.,1.],'expected_success':False},{'name':'nonfinite_H','H':[['.nan']],'ell':[0.],'eta':[1.],'expected_success':False},{'name':'dimension8','H':np.eye(8).tolist(),'ell':[0.]*8,'eta':[1.]*8,'expected_success':False}]
 boxes += [{'name':'tiny_upper','H':[[1.]],'ell':[-1.],'eta':[1e-12],'expected_success':True,'expected_force':[1e-12]}, {'name':'tiny_lower_1e100','H':[[1.]],'ell':[1.],'eta':[1e-100],'expected_success':True,'expected_force':[-1e-100]}]
 cases={'scope':__doc__,'cases':state,'box_cases':boxes};dump(out/'cases.json',cases);(out/'SOURCE_SNAPSHOT.py').write_bytes(source_bytes)
 command=[str(binary),str(xml),str(constants),str(out/'cases.json'),str(out/'native_output.json')]
 run=subprocess.run(command,capture_output=True,text=True);(out/'stdout.log').write_text(run.stdout);(out/'stderr.log').write_text(run.stderr);assert run.returncode==0
 native=json.loads((out/'native_output.json').read_text(),parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)));assert native['model_success'] is True
 meta=native['metadata'];assert meta['nq']==meta['nv']==7 and meta['idx_q']==meta['idx_v']==list(range(7)) and meta['joint_nq']==meta['joint_nv']==[1]*7
 assert abs(meta['masses'][7]-1.077143)<1e-12 and meta['armature']==c['armature']
 assert len(native['cases'])==len(state) and len(native['box_cases'])==len(boxes)
 state_results=[];maxq=maxv=0.
 for item,answer in zip(state,native['cases']):
  assert answer['name']==item['name'] and isinstance(answer['success'],bool) and answer['success']==item['expected_success'],answer
  record={'name':item['name'],'success':answer['success'],'error':answer.get('error')}
  if answer['success']:
   q,v=np.array(item['q']),np.array(item['v']);assert len(answer['trace'])==len(item['targets']);dq=dv=0.
   for target,point in zip(item['targets'],answer['trace']):
    q,v,info=model.step(q,v,np.array(target));cq,cv=np.array(point['q']),np.array(point['v']);assert np.isfinite(cq).all() and np.isfinite(cv).all()
    dq=max(dq,float(np.max(abs(cq-q))));dv=max(dv,float(np.max(abs(cv-v))));assert point['control_clips']==info['control_clips'] and point['force_clips']==info['force_clips']
   assert dq<1e-11 and dv<1e-10;record.update(substeps=len(item['targets']),maximum_q_parity_rad=dq,maximum_v_parity_rad_s=dv);maxq=max(maxq,dq);maxv=max(maxv,dv)
  state_results.append(record)
 box_results=[]
 for item,answer in zip(boxes,native['box_cases']):
  assert answer['name']==item['name'] and isinstance(answer['success'],bool) and answer['success']==item['expected_success'],answer
  record={'name':item['name'],'success':answer['success'],'error':answer.get('error')}
  if answer['success']:
   force=np.array(answer['result']['force']);expected=np.array(item['expected_force']);assert np.isfinite(force).all() and np.max(abs(force-expected))<1e-10
   H,ell,eta=[np.array(item[k],float) for k in ['H','ell','eta']];g=H@force+ell
   lo=force<=-eta;hi=force>=eta;res=np.where(eta==0,0,np.where(lo,np.maximum(-g,0),np.where(hi,np.maximum(g,0),abs(g))));kkt=float(max(np.max(res),np.max(abs(force)-eta),0));assert kkt<=1e-10
   record.update(independent_KKT=kkt,independent_force_difference=float(np.max(abs(force-expected))))
  if item['name'].startswith('tiny_'):
   assert np.array_equal(force,expected);wanted=1 if item['name']=='tiny_upper' else -1;assert answer['result']['branches']==[wanted];record.update(exact_analytic_optimum=True,exact_side_label=wanted)
  box_results.append(record)
 assert SHA(frozen)==a.freeze_sha256 and SHA(binary)==BINARY and source.read_bytes()==source_bytes
 for p in inputs:assert SHA(p)==entries[str(p)]['sha256'],p
 report={'decision':'PASS_V2_NATIVE_TRANSITION_AND_TINY_BOUND_ANALYTIC_REGRESSIONS','scope':__doc__,'source_sha256':hashlib.sha256(source_bytes).hexdigest(),'binary_sha256':BINARY,'freeze_sha256':a.freeze_sha256,'oracle_sha256':SHA(a.oracle),'metadata':meta,'state_cases':state_results,'box_cases':box_results,'maximum_q_parity_rad':maxq,'maximum_v_parity_rad_s':maxv,'tiny_positive_eta_regressions_passed':True,'new_plant_run':False,'phase5_accepted':False}
 dump(out/'audit.json',report);files={p.name:{'sha256':SHA(p),'bytes':p.stat().st_size} for p in out.iterdir() if p.is_file()};dump(out/'READY.json',{'scope':__doc__,'files':files});print(json.dumps({'states':len(state),'boxes':len(boxes),'max_q':maxq,'max_v':maxv,'tiny_eta_exact_optima_passed':True}))
if __name__=='__main__':main()
