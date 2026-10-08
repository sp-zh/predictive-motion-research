#!/usr/bin/env python3
"""Actual augmented predictions and declared component QA plots."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
import json,hashlib
import numpy as np
ROOT=Path('/home/codextransfer/predictive_motion');BASE=ROOT/'results/phase5/development/public-coupled-augmented-cpp-v1';DEST=ROOT/'figures/phase5';DEST.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
inputs=json.loads((BASE/'inputs/cases.json').read_text());outputs=json.loads((BASE/'parity-attempt1/augmented.json').read_text());report=json.loads((BASE/'parity-attempt1/report.json').read_text());assert report['status']=='PASS_BOUNDED_AUGMENTED_COMPONENT_ONLY'
case=next(x for x in outputs['cases'] if x['name']=='nonuniform_mixed');t=np.array([x['elapsed_s'] for x in case['substeps']])*1000;tr=case['substeps'];z=next(x['state'] for x in inputs['cases'] if x['name']=='nonuniform_mixed')
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.titlesize':12,'axes.spines.top':False,'axes.spines.right':False})
fig,ax=plt.subplots(2,2,figsize=(13,8));fig.subplots_adjust(bottom=.17,top=.85,hspace=.45,wspace=.27)
fig.suptitle('Augmented state: actual 4 ms commands, paired 2 ms physics',fontsize=19,x=.07,ha='left');fig.text(.07,.9,'Nonuniform 4 / 40 / 12 / 8 ms cells • synthetic accepted C ≠ q and w ≠ v • C++ v2 physics frozen',fontsize=11)
ax[0,0].plot(t,[x['C'][0]-z['C'][0] for x in tr],drawstyle='steps-post',label='accepted target C, J1');ax[0,0].plot(t,[x['q'][0]-z['q'][0] for x in tr],label='physical position q, J1');ax[0,0].set(ylabel='change from own initial state (rad)',xlabel='elapsed time (ms)',title='Command history and physical position');ax[0,0].legend()
ax[0,1].plot(t,[x['w'][0] for x in tr],drawstyle='steps-post',label='accepted command velocity w, J1');ax[0,1].plot(t,[x['v'][0] for x in tr],label='physical velocity v, J1');ax[0,1].set(ylabel='rad/s',xlabel='elapsed time (ms)',title='Separate accepted and physical velocities');ax[0,1].legend()
ax[1,0].plot(t,[x['s_reference'] for x in tr],marker='.',label='2 ms reference s');ax[1,0].plot(t[1::2],[x['s'] for x in case['cycle_end_states']],marker='o',fillstyle='none',linestyle='none',label='4 ms completed state');ax[1,0].set(ylabel='dimensionless progress s',xlabel='elapsed time (ms)',title='Progress uses pre-update rate');ax[1,0].legend()
ax[1,1].plot(t,[x['r_reference'] for x in tr],marker='.',color='#558855');ax[1,1].set(ylabel='reference progress rate (1/s)',xlabel='elapsed time (ms)',title='Signed b changes at actual mesh boundaries')
for a in ax.flat:
 for boundary in (4,44,56):a.axvline(boundary,color='gray',alpha=.3,linestyle=':')
 a.grid(alpha=.2)
fig.text(.07,.075,'Component diagnostic only: numerical command/progress domain. No physical safety, jerk, task or runtime acceptance.\nNo plant execution. Recorded tests use prior accepted C/w and actual command acceleration; progress is virtual.',fontsize=10)
paths=[]
p=DEST/'phase5_public_coupled_augmented_cpp_transition.png';fig.savefig(p,dpi=160);plt.close(fig);paths.append(p)
positive=[x for x in report['records'] if x['success']];recorded=[x for x in positive if x['name'].startswith(('train91011','seen91013'))]
fig,ax=plt.subplots(1,2,figsize=(14,7));fig.subplots_adjust(bottom=.30,top=.78,wspace=.3);fig.suptitle('Augmented wrapper: closed-form and frozen-base verification',fontsize=19,x=.07,ha='left')
floor=1e-18
for key,label in [('command','C/w vs rational formula'),('progress','s/r/time vs rational formula'),('paired_q','q vs independent base composition'),('paired_v','v vs independent base composition')]:
 ax[0].plot(range(len(positive)),[max(x['maxima'][key],floor) for x in positive],marker='.',label=label)
ax[0].set(yscale='log',xlabel='predeclared positive case index',ylabel='max absolute difference (SI units)',title=f'{len(positive)} positive cases; display floor 1e-18');ax[0].legend(fontsize=7,loc='lower left',bbox_to_anchor=(0,1.14),ncol=2);ax[0].grid(alpha=.2)
labels=['positive\ncomponent\ncases','native invalid\ninput\nrejections','synthetic output\ncorruptions\nrejected','EOF windows\nretained\nincomplete'];values=[len(positive),sum(not x['success'] for x in report['records']),len(report['synthetic_output_gates']['negative_controls']),len(report['incomplete_retained'])]
bars=ax[1].bar(labels,values,color=['#447799','#bb6644','#8866aa','#888888']);ax[1].bar_label(bars);ax[1].set(ylabel='case count',title='Declared roster and distinct negative controls',ylim=(0,max(values)+8));ax[1].tick_params(axis='x',labelsize=9)
qmax=max(x['maxima']['physical_q'] for x in recorded);vmax=max(x['maxima']['physical_v'] for x in recorded)
fig.text(.07,.09,f'{len(recorded)} complete selected TRAIN91011 / seen91013 windows; physical q error {qmax:.3g} rad, v error {vmax:.3g} rad/s.\nShort/long regression gates unchanged. Synthetic output mutations are QA controls, not native model failures.\nPhase5 NOT_ACCEPTED. No new plant, controller, task completion, generalization or online timing claim.',fontsize=10)
p=DEST/'phase5_public_coupled_augmented_cpp_verification.png';fig.savefig(p,dpi=160);plt.close(fig);paths.append(p)
for p in paths:
 provenance=dict(figure_sha256=sha(p),script_sha256=sha(__file__),report_sha256=sha(BASE/'parity-attempt1/report.json'),output_sha256=sha(BASE/'parity-attempt1/augmented.json'),input_sha256=sha(BASE/'inputs/cases.json'),freeze_sha256=sha(BASE/'frozen_before_predictions.json'),units='rad,rad/s,s dimensionless,r1/s,time ms; verification absolute errors in corresponding SI units',data_source='actual frozen augmented/native outputs; fixed declared synthetic and conditional previously seen raw cases',validation_scope='Bounded numerical component only; Phase5 NOT_ACCEPTED; no task-success video available. No performance ranking.',zero_display_floor=1e-18 if 'verification' in p.name else None)
 p.with_suffix('.json').write_text(json.dumps(provenance,indent=2)+'\n');print(str(p),sha(p))
