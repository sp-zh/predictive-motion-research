#!/usr/bin/env python3
"""Recorded simulation plots and saved-state geometry; no predictor/run changes."""
import csv,hashlib,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
p=Path('/home/codextransfer/predictive_motion');base=p/'results/phase5/development/public-coupled-v2-development-validation-91013';raw=Path('/mnt/d/CodexTransfer/projects/predictive_motion/phase5/raw/public-coupled-v2-development-validation-91013/raw.csv')
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
report=json.loads((base/'scored/validation_report.json').read_text());execution=json.loads((base/'execution.json').read_text());assert sha(raw)==execution['raw_files']['raw.csv']
rows=list(csv.DictReader(raw.open()));cycles=list(csv.DictReader(raw.with_name('cycles.csv').open()));times=np.array([float(r['time_s']) for r in rows])
data=lambda prefix:np.array([[float(r[prefix+str(j)]) for j in range(7)] for r in rows]);w,alpha,jerk,v=[data(k) for k in ['command_velocity_','command_acceleration_','command_jerk_','v_post_']]
metrics=[m for m in report.get('metrics',[]) if m['scope']=='active'];assert len(metrics)==4
fig,axes=plt.subplots(2,3,figsize=(13,7.2),constrained_layout=True);x=np.arange(4);labels=['2','4','40','800']
for ax,quantity,unit in [(axes[0,0],'q','rad'),(axes[0,1],'v','rad/s')]:
 vals=[m['max_'+quantity+'_error_'+('rad' if quantity=='q' else 'rad_s')] for m in metrics];rmse=[m['rmse_'+quantity+'_'+('rad' if quantity=='q' else 'rad_s')] for m in metrics];limits=[m[quantity+'_limit_'+('rad' if quantity=='q' else 'rad_s')] for m in metrics]
 ax.plot(x,np.maximum(vals,1e-18),'o-',label='Max active error',color='#357d86');ax.plot(x,np.maximum(rmse,1e-18),'s-',label='RMS active error',color='#536f8c');ax.plot(x,limits,'x--',label='Frozen limit',color='#a66b56');ax.set_yscale('log');ax.set_xticks(x,labels);ax.set_xlabel('Conditional forecast horizon (ms)');ax.set_ylabel(unit);ax.set_title('Active '+quantity+' endpoint errors');ax.grid(alpha=.15);ax.legend(fontsize=8)
ax=axes[0,2]
for values,limit,label,color in [(w,.0625,'Accepted |w| / 0.0625','#357d86'),(alpha,1.,'Accepted |alpha| / 1','#536f8c'),(jerk,20.,'Accepted |jerk| / 20','#a66b56')]:ax.plot(times,np.max(abs(values),axis=1)/limit,label=label,color=color,lw=1)
ax.axhline(1,color='#555',ls='--',lw=1);ax.set_title('Recorded command derivatives');ax.set_xlabel('Simulation time (s)');ax.set_ylabel('Maximum joint value / declared limit');ax.legend(fontsize=8);ax.grid(alpha=.15)
ax=axes[1,0];clearance=np.array([float(r['true_clearance_m']) for r in rows])*1000;ax.plot(times,clearance,color='#357d86');ax.axhline(5,color='#a66b56',ls='--',label='Frozen 5 mm guard');ax.set_title('Recorded minimum clearance');ax.set_xlabel('Simulation time (s)');ax.set_ylabel('mm');ax.legend(fontsize=8);ax.grid(alpha=.15)
ax=axes[1,1];ct=np.array([int(r['tick'])*.004 for r in cycles]);wall=np.array([float(r['full_cycle_wall_s']) for r in cycles])*1000;age=np.array([float(r['command_age_s']) for r in cycles])*1000
ax.plot(ct,wall,label='Full cycle wall time',color='#536f8c',lw=.8);ax.plot(ct,age,label='Command age',color='#357d86',lw=.8);ax.axhline(4,color='#a66b56',ls='--',label='4 ms deadline');ax.axhline(50,color='#555',ls=':',label='50 ms age budget');ax.set_title('Measured execution timing (not 250 Hz proof)');ax.set_xlabel('Simulation time (s)');ax.set_ylabel('ms');ax.legend(fontsize=7);ax.grid(alpha=.15)
ax=axes[1,2];ax.axis('off');audit=report['capture_integrity'];text=[report['gate'],f"Seed 91013 | {audit['cycles']} cycles | {len(rows)} physical substeps",f"Complete active windows: {[m['windows'] for m in metrics]}",f"Warmup failures: {sum(m['failed_windows'] for m in report['metrics'] if m['scope']=='warmup')}",f"All native/API attempts: {audit['attempts']}",f"Original-row max SI: {audit['actual_original_row_max_SI_violation']:.3g}",f"4 ms deadline misses: {audit['full4ms_deadline_misses']}",f"Force-QP max KKT: {report['max_force_QP_KKT']:.3g}",f"Terminal max |w|: {abs(w[-1]).max():.3g} rad/s",f"Terminal max physical |v|: {abs(v[-1]).max():.3g} rad/s",'Known curated input; hold-end stop.','No full task, controller, uniform-domain','or Phase5 acceptance.']
ax.text(0,.99,'\n'.join(text),va='top',fontsize=9);fig.suptitle('Recorded seed91013 conditional development validation',fontsize=15);fig.supxlabel('Fixed public_v2 model; measured start once and future accepted targets only. Overlapping windows are not independent trials.',fontsize=9)
chart=base/'phase5_public_validation_91013_actual.png';fig.savefig(chart,dpi=160);plt.close(fig)
ppm=base/'recorded_final_state.ppm';row=rows[-1];fig,ax=plt.subplots(figsize=(12.8,8.0),constrained_layout=True);ax.imshow(Image.open(ppm));ax.axis('off');ax.set_title('FR3 recorded seed91013 final state | shared stop complete',fontsize=15,pad=12)
fig.supxlabel(f"Saved q/v/target geometry at t={float(row['time_s']):.3f} s; clearance={float(row['true_clearance_m'])*1000:.2f} mm; contacts={row['contacts']}\nMuJoCo 3.3.7 OSMesa, mj_forward only. No new physics/control stepping, full-task or Phase5 acceptance.",fontsize=10)
render=base/'phase5_public_validation_91013_recorded_final_state.png';fig.savefig(render,dpi=100);plt.close(fig)
manifest=p/'src/predictive_motion_description/manifests/fr3.sha256'
for line in manifest.read_text().splitlines():
 expected,name=line.split(None,1);assert sha(p/'.vendor/menagerie'/name.strip())==expected
sourcefiles=[raw,raw.with_name('cycles.csv'),base/'execution.json',base/'scored/validation_report.json',ppm,p/'experiments/generated/inspection/scene.xml',p/'experiments/generated/inspection/inspection_fr3.xml',p/'tools/phase5_servo_diagnostics/render_servo_recorded_pose.cpp',p/'build-servo-qp-reconstruct-v1/render_servo_recorded_pose',Path(__file__)]
metadata={'scope':'Actual recorded simulation and conditional model validation; saved-state geometry only; not hardware, new plant run, task success or Phase5 acceptance','seed':91013,'model_length_units':'metres; q radians, v rad/s; plotted clearance mm and timing ms','camera':{'lookat_m':[.49,-.01,.49],'distance_m':1.5,'azimuth_deg':135,'elevation_deg':-23},'source_hashes':{str(f):sha(f) for f in sourcefiles},'upstream_asset_manifest_sha256':sha(manifest),'outputs':{f.name:sha(f) for f in [chart,render]},'recorded_terminal':{'tick':int(row['tick']),'time_s':float(row['time_s']),'q_post_rad':[float(row['q_post_'+str(j)]) for j in range(7)]},'visualization_tools_created_after_run':True,'predictor_frozen_before_run':True,'task_success_video_created':False}
(base/'phase5_public_validation_91013_visuals.json').write_text(json.dumps(metadata,indent=2,allow_nan=False)+'\n');print(json.dumps(metadata,indent=2))
