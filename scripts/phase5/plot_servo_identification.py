#!/usr/bin/env python3
"""Plot recorded MuJoCo servo training; no fitted-model or research success claim."""
import argparse,csv,hashlib,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=argparse.ArgumentParser(description=__doc__);p.add_argument('raw',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
rows=[r for r in csv.DictReader(a.raw.open()) if r['phase']!='warmup' and r['substep']=='2']
j=max(range(7),key=lambda k:max(abs(float(r['command_velocity_'+str(k)])) for r in rows))
t=[float(r['time_s'])-2 for r in rows];baseline=float(rows[0]['target_'+str(j)])
plt.rcParams.update({'font.size':11,'font.family':'DejaVu Sans','axes.spines.top':False,'axes.spines.right':False})
fig,ax=plt.subplots(3,1,figsize=(10.5,8.6),sharex=True)
fig.suptitle('Phase 5 servo identification training',x=.09,ha='left',fontsize=19,fontweight='bold')
fig.text(.09,.916,'Recorded MuJoCo fixture · seed 91011 · model fit and holdout validation pending',fontsize=10,color='#555555')
blue,orange,gray='#286094','#C46A2C','#545454'
for prefix,label,color,style in [('target_','Accepted target',orange,'--'),('q_post_','Measured position',blue,'-')]:
 ax[0].plot(t,[1000*(float(r[prefix+str(j)])-baseline) for r in rows],label=label,color=color,linestyle=style,linewidth=1.7)
ax[0].set_ylabel(f'Joint {j+1} position [mrad]');ax[0].legend(frameon=False,loc='lower left',bbox_to_anchor=(0,1.01),ncol=2,fontsize=9)
for prefix,label,color,style in [('command_velocity_','Command velocity',orange,'--'),('v_post_','Measured velocity',blue,'-')]:
 ax[1].plot(t,[1000*float(r[prefix+str(j)]) for r in rows],label=label,color=color,linestyle=style,linewidth=1.7)
ax[1].set_ylabel(f'Joint {j+1} speed [mrad/s]');ax[1].legend(frameon=False,loc='lower left',bbox_to_anchor=(0,1.01),ncol=2,fontsize=9)
ax[2].plot(t,[1000*max(abs(float(r['v_post_'+str(k)])) for k in range(7)) for r in rows],color=blue,linewidth=1.6,label='Max physical joint speed')
ax[2].axhline(.1,color=gray,linestyle=':',label='Recorded stop criterion 0.1 mrad/s')
ax[2].set_ylabel('Max joint speed [mrad/s]');ax[2].set_xlabel('Time since excitation began [s]');ax[2].legend(frameon=False,loc='lower left',bbox_to_anchor=(0,1.01),ncol=2,fontsize=9)
for axis in ax:
 axis.grid(axis='y',color='#DADADA',linewidth=.6);axis.set_xlim(t[0],t[-1]);axis.axvspan(8,t[-1],color='#E6E6E6',alpha=.7)
fig.text(.09,.035,'Shaded interval: bounded stopping. Upper two panels select the joint with highest command-speed peak.\nPosition curves share the initial accepted-target origin. Samples are the final 2 ms substep of each 4 ms cycle.\nRecorded training only; no holdout prediction accuracy, predictive-task success, hardware or real-time claim.',fontsize=9,color='#555555')
fig.subplots_adjust(left=.12,right=.97,top=.875,bottom=.16,hspace=.35)
a.output.mkdir(parents=True,exist_ok=False);out=a.output/'phase5_servo_training_v1.png';fig.savefig(out,dpi=180,facecolor='white')
meta={'scope':__doc__,'raw_source':str(a.raw),'raw_sha256':hashlib.sha256(a.raw.read_bytes()).hexdigest(),'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'joint_index_zero_based':j,'active_4ms_samples':len(rows),'position_origin_rad':baseline,'shaded_stop_time_s':8,'output_sha256':hashlib.sha256(out.read_bytes()).hexdigest()}
(a.output/'phase5_servo_training_v1.json').write_text(json.dumps(meta,indent=2)+'\n');print(json.dumps(meta))
