#!/usr/bin/env python3
"""Plot the retained incomplete expanded identification trace; no stop or model acceptance."""
import argparse,csv,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from servo_model_v1 import sha
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--raw',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
rows=[r for r in csv.DictReader(a.raw.open()) if r['phase']!='warmup' and r['substep']=='2']
j=max(range(7),key=lambda k:max(abs(float(r['command_velocity_'+str(k)])) for r in rows))
t=[float(r['time_s'])-2 for r in rows];origin=float(rows[0]['target_'+str(j)])
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
fig,axes=plt.subplots(3,1,figsize=(11,9),sharex=True)
fig.suptitle('Expanded servo validation: command rejected before completion',x=.09,ha='left',fontsize=17,weight='bold')
fig.text(.09,.925,'Same frozen soft model · new 8 mrad waveform · native PRIMAL_INFEASIBLE at next command',fontsize=10,color='#555')
blue,orange='#406b96','#bf6b36'
for prefix,label,color,style in [('target_','Accepted target',orange,'--'),('q_post_','Recorded physical position',blue,'-')]:
 axes[0].plot(t,[1000*(float(r[prefix+str(j)])-origin) for r in rows],color=color,linestyle=style,label=label,linewidth=1.7)
axes[0].set_ylabel(f'Joint {j+1} position [mrad]')
for prefix,label,color,style in [('command_velocity_','Max accepted command speed',orange,'--'),('v_post_','Max recorded physical speed',blue,'-')]:
 axes[1].plot(t,[1000*max(abs(float(r[prefix+str(k)])) for k in range(7)) for r in rows],color=color,linestyle=style,label=label,linewidth=1.7)
axes[1].set_ylabel('Max speed [mrad/s]')
axes[2].plot(t,[1000*float(r['true_clearance_m']) for r in rows],color=blue,label='Recorded clearance',linewidth=1.7)
axes[2].axhline(5,color='#777',linestyle=':',label='Unchanged 5 mm safety threshold')
axes[2].set_ylabel('Clearance [mm]');axes[2].set_xlabel('Time since excitation began [s]')
for ax in axes:
 ax.grid(axis='y',color='#ddd',linewidth=.6);ax.legend(loc='lower left',bbox_to_anchor=(0,1.005),ncol=2,frameon=False,fontsize=9)
 ax.axvline(t[-1],color='#b13c3c',linestyle=':',linewidth=1.2);ax.set_xlim(t[0],t[-1]+.025)
fig.text(.09,.055,'Records end after tick 853 (1.416 s excitation); the next command is rejected. No command is accepted after rejection.\n'
         'No completed bounded-stop record or complete expanded model validation exists. Recorded clearance alone does not explain QP infeasibility.\n'
         'Samples show the final 2 ms substep per 4 ms cycle. The original model and its smaller validated domain remain unchanged.',fontsize=9,color='#555')
fig.subplots_adjust(left=.12,right=.97,top=.845,bottom=.17,hspace=.48)
a.output.mkdir(exist_ok=False);out=a.output/'phase5_servo_expanded_guard_failure.png';fig.savefig(out,dpi=180,facecolor='white')
with (a.output/'phase5_servo_expanded_guard_failure.json').open('x') as f:f.write(json.dumps({'scope':__doc__,'raw_sha256':sha(a.raw),'script_sha256':sha(__file__),'output_sha256':sha(out),'joint_index_zero_based':j,'4ms_samples':len(rows),'completed_stop':False,'expanded_model_accepted':False},indent=2)+'\n')
print(sha(out))
