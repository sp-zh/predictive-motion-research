#!/usr/bin/env python3
"""Actual captured stop-QP witnesses and nonzero state after exact past replay."""
import argparse,json
from pathlib import Path
import yaml
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from servo_model_v1 import sha,write_new
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--project',type=Path,required=True);a=p.parse_args()
case=a.project/'results/phase5/development/servo-expanded-failure-stop-replay-v1';report_file=case/'stop_feasibility_analysis.json';summary_file=case/'replay-stop/summary.yaml'
report=json.loads(report_file.read_text());summary=yaml.safe_load(summary_file.read_text());witness=sorted([r for r in report['geometry_rows'] if r['individually_inconsistent_with_command_box']],key=lambda r:r['lower_deficit'],reverse=True)[:3]
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
fig,axes=plt.subplots(1,2,figsize=(12,6.8),gridspec_kw={'width_ratios':[1.6,1]})
fig.suptitle('Matched failure state: shared guarded stop has no admissible command',x=.075,ha='left',fontsize=17,weight='bold')
fig.text(.075,.905,'Full 1,708-record replay matches q / v / accepted targets / timestamps exactly · no stop command accepted',color='#555',fontsize=10)
for y,r in enumerate(witness):
 lo,hi,required=[1000*r[key] for key in ['min_over_command_box','max_over_command_box','lower']]
 axes[0].plot([lo,hi],[y,y],color='#406b96',linewidth=10,solid_capstyle='butt',label='Reachable guard-row range' if y==0 else None)
 axes[0].plot(required,y,'|',color='#bf6b36',markersize=25,markeredgewidth=3,label='Required lower bound' if y==0 else None)
 axes[0].plot([hi,required],[y,y],color='#b13c3c',linestyle=':',linewidth=1.5)
 axes[0].text((hi+required)/2,y+.18,f'{1000*r["lower_deficit"]:.3f} mm/s deficit',ha='center',fontsize=9,color='#b13c3c')
axes[0].set_yticks(range(len(witness)),['Shaft / left · cover '+r['label'].split('/')[-1] for r in witness]);axes[0].set_ylim(-.4,2.65)
axes[0].set_xlabel('Guard row ∇d · next candidate command w [mm/s]');axes[0].grid(axis='x',color='#ddd',linewidth=.6)
axes[0].legend(frameon=False,loc='lower left',bbox_to_anchor=(0,1.02),fontsize=9)
speeds=[1000*summary['final_physical_speed_rad_s'],1000*summary['final_command_speed_rad_s']]
axes[1].bar([0,1],speeds,color=['#406b96','#bf6b36'],width=.5)
axes[1].set_xticks([0,1],['Physical speed','Last accepted\ncommand speed']);axes[1].set_ylabel('Maximum joint speed [mrad/s]');axes[1].grid(axis='y',color='#ddd',linewidth=.6)
for i,speed in enumerate(speeds):axes[1].text(i,speed+1,f'{speed:.2f}',ha='center')
axes[1].set_ylim(0,50);axes[1].axhline(.1,color='#777',linestyle=':',label='Physical observed-stop criterion')
axes[1].legend(frameon=False,loc='lower left',bbox_to_anchor=(0,1.02),fontsize=8)
fig.text(.075,.05,'Blue ranges include all unchanged command position / velocity / acceleration / jerk rows; each orange requirement lies beyond its range.\n'
         'The full captured stop QP is also infeasible under an independent LP formulation. Its softened margin point violates original SI rows and is not a command.\n'
         'Simulation ends at virtual t=3.416 s with nonzero physical speed. No completed stop, expanded model acceptance, task or hardware claim.',fontsize=9,color='#555')
fig.subplots_adjust(left=.17,right=.97,top=.775,bottom=.23,wspace=.38)
out=case/'figures/phase5_servo_no_feasible_stop.png';fig.savefig(out,dpi=180,facecolor='white')
write_new(case/'figures/phase5_servo_no_feasible_stop.json',{'scope':__doc__,'source_hashes':{str(f):sha(f) for f in [report_file,summary_file,Path(__file__)]},'output_sha256':sha(out),'witness_labels':[r['label'] for r in witness],'completed_stop':False})
print(sha(out))
