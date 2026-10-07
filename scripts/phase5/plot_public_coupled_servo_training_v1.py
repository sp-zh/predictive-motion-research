#!/usr/bin/env python3
import csv,json,hashlib
from collections import Counter
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=Path('/home/codextransfer/predictive_motion');base=p/'results/phase5/development/public-coupled-servo-v1-training';report=base/'training_report.json';r=json.loads(report.read_text());raw=Path('/mnt/d/CodexTransfer/projects/predictive_motion/phase5/raw/servo-identification-v1-training/raw.csv');rows=list(csv.DictReader(raw.open()));sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest();rosters=[]
for count in [1,2,20,400]:
 starts=[i for i in range(0,len(rows)-count+1,2) if rows[i]['phase']!='warmup'];rosters.append({'duration_s':count*.002,'active_windows':len(starts),'start_phase_counts':dict(Counter(rows[i]['phase'] for i in starts)),'windows_containing_stop':sum(any(rows[j]['phase']=='stopping' for j in range(i,i+count)) for i in starts),'trailing_incomplete_windows_not_constructed':count//2-1 if count>1 else 0})
(base/'window_phase_roster.json').write_text(json.dumps({'raw_sha256':sha(raw),'rosters':rosters,'scope':'All full windows retained; incomplete trace tails cannot form a full horizon; stop-inclusive windows explicitly counted, not removed'},indent=2)+'\n')
metrics=[m for m in r['metrics'] if m['scope']=='active'];x=np.arange(4);qrat=[m['max_q_error_rad']/m['q_limit_rad'] for m in metrics];vrat=[m['max_v_error_rad_s']/m['v_limit_rad_s'] for m in metrics]
fig,ax=plt.subplots(figsize=(9,4.8),constrained_layout=True);ax.bar(x-.18,qrat,.36,label='Maximum q error / original q limit',color='#407b93');ax.bar(x+.18,vrat,.36,label='Maximum v error / original v limit',color='#987253');ax.axhline(1,color='#ae4444',ls='--',label='Original error gate');ax.set_yscale('log');ax.set_ylim(1e-13,2);ax.set_xticks(x,['2 ms\n2190 windows','4 ms\n2190 windows','40 ms\n2181 windows','800 ms\n1991 windows']);ax.set_ylabel('Error / frozen limit (dimensionless, log scale)');ax.legend(fontsize=9,loc='upper left')
ax.set_title('Public coupled baseline: TRAIN91011 conditional prediction only',fontsize=13);fig.supxlabel('Zero calibration; complete stop-inclusive windows. Not holdout, exact-engine or controller acceptance.',fontsize=9)
image=base/'phase5_public_coupled_training_v1.png';fig.savefig(image,dpi=170);plt.close(fig)
(base/'phase5_public_coupled_training_v1.json').write_text(json.dumps({'image_sha256':sha(image),'report_sha256':sha(report),'training_raw_sha256':sha(raw),'source':'scripts/phase5/plot_public_coupled_servo_training_v1.py','units':'Dimensionless error/original-limit ratios; q radians,v radians/s; horizons milliseconds','scope':r['scope'],'zero_q_v_error_claim':False,'geometry_changed':False},indent=2)+'\n');print(json.dumps({'image_sha256':sha(image),'rosters':rosters},indent=2))
